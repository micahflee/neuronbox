import os
import sys
import time
import traceback

import requests
from flask import Flask, jsonify, request, stream_with_context
from flask_cors import CORS
from tqdm import tqdm
import appdirs

from gunicorn.app.base import BaseApplication
import multiprocessing

import whisper
import whisper.audio
import torch
import numpy as np
from functools import lru_cache


# Monkeypatch whisper to work when frozen with PyInstaller. Otherwise, we end up with an error like this:
# Traceback (most recent call last):
#   File "flask/app.py", line 1484, in full_dispatch_request
#   File "flask/app.py", line 1469, in dispatch_request
#   File "backend.py", line 343, in transcribe
#   File "backend.py", line 300, in do_transcribe
#   File "whisper/transcribe.py", line 121, in transcribe
#   File "whisper/audio.py", line 141, in log_mel_spectrogram
#   File "whisper/audio.py", line 94, in mel_filters
#   File "numpy/lib/npyio.py", line 405, in load
# FileNotFoundError: [Errno 2] No such file or directory: '/var/folders/91/mf1m_byx43d8v058f2yb4nlm0000gn/T/_MEIz3Pn83/whisper/assets/mel_filters.npz'
if getattr(sys, "frozen", False):

    @lru_cache(maxsize=None)
    def my_mel_filters(device, n_mels: int = whisper.audio.N_MELS) -> torch.Tensor:
        """
        Modified version of mel_filters function
        """
        assert n_mels == 80, f"Unsupported n_mels: {n_mels}"
        base_path = os.path.dirname(os.path.abspath(__file__))
        mel_filters_path = os.path.join(base_path, "whisper/assets/mel_filters.npz")
        with np.load(mel_filters_path) as f:
            return torch.from_numpy(f[f"mel_{n_mels}"]).to(device)

    whisper.audio.mel_filters = my_mel_filters


# Helper functions


def get_config_dir():
    return appdirs.user_config_dir("neuronbox")


def get_models_dir():
    return os.path.join(get_config_dir(), "models")


def get_download_status_dir():
    return os.path.join(get_config_dir(), "download_status")


def create_status_file(key):
    with open(os.path.join(get_download_status_dir(), f"{key}.status"), "w") as f:
        f.write("0")  # Initially, progress is 0%


def update_status_file(key, progress):
    with open(os.path.join(get_download_status_dir(), f"{key}.status"), "w") as f:
        f.write(str(progress))


def read_status_file(key):
    try:
        with open(os.path.join(get_download_status_dir(), f"{key}.status"), "r") as f:
            return float(f.read().strip())
    except FileNotFoundError:
        return None
    except ValueError:
        return 0


def delete_status_file(key):
    try:
        os.remove(os.path.join(get_download_status_dir(), f"{key}.status"))
    except FileNotFoundError:
        pass


# Create folders if they don't exist

if not os.path.exists(get_models_dir()):
    os.makedirs(get_models_dir())

if not os.path.exists(get_download_status_dir()):
    os.makedirs(get_download_status_dir())
    # Delete any files left over from last time
    for filename in os.listdir(get_download_status_dir()):
        os.remove(os.path.join(get_download_status_dir(), filename))


# Create the flask app

app = Flask(__name__)
CORS(app)  # TODO: restrict origins to just localhost


@app.errorhandler(Exception)
def handle_exception(e):
    # Capture the stack trace
    trace = traceback.format_exc()
    # Log it, send it to an external service, etc.
    app.logger.error(trace)
    return str(e), 500


# Health check
@app.route("/health")
def health():
    return "OK"


# Models


@app.route("/models")
def models():
    whisper_dir = os.path.join(get_models_dir(), "whisper")
    if not os.path.exists(whisper_dir):
        os.makedirs(whisper_dir)

    whispers_small_downloaded = os.path.exists(os.path.join(whisper_dir, "small.pt"))
    whispers_medium_downloaded = os.path.exists(os.path.join(whisper_dir, "medium.pt"))
    whispers_large_downloaded = os.path.exists(os.path.join(whisper_dir, "large.pt"))

    if whispers_small_downloaded:
        whispers_small_size = os.path.getsize(os.path.join(whisper_dir, "small.pt"))
    else:
        whispers_small_size = 0

    if whispers_medium_downloaded:
        whispers_medium_size = os.path.getsize(os.path.join(whisper_dir, "medium.pt"))
    else:
        whispers_medium_size = 0

    if whispers_large_downloaded:
        whispers_large_size = os.path.getsize(os.path.join(whisper_dir, "large.pt"))
    else:
        whispers_large_size = 0

    return jsonify(
        {
            "models": {
                "transcribe": [
                    {
                        "name": "small",
                        "description": "Small, requires ~2GB RAM",
                        "downloaded": whispers_small_downloaded,
                        "size": whispers_small_size,
                    },
                    {
                        "name": "medium",
                        "description": "Medium, requires ~5GB RAM",
                        "downloaded": whispers_medium_downloaded,
                        "size": whispers_medium_size,
                    },
                    {
                        "name": "large",
                        "description": "Large, requires ~10GB RAM",
                        "downloaded": whispers_large_downloaded,
                        "size": whispers_large_size,
                    },
                ]
            }
        }
    )


@app.route("/models/download", methods=["POST"])
def models_download():
    feature = request.json.get("feature")
    model = request.json.get("model")
    key = f"{feature}_{model}"

    print(f"Starting download: {key}")
    create_status_file(key)

    if feature not in ["transcribe"]:
        return jsonify({"success": False, "error": f"Invalid feature: {feature}"})

    if feature == "transcribe":
        if model not in ["small", "medium", "large"]:
            return jsonify({"success": False, "error": f"Invalid model: {model}"})

        download_url = whisper._MODELS[model]
        filename = os.path.join(get_models_dir(), "whisper", f"{model}.pt")
        print(f"Key: {key}: Downloading {download_url} to {filename}")

        canceled_early = False

        try:
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                block_size = 1024  # 1 Kbyte
                progress = tqdm(total=total_size, unit="B", unit_scale=True, desc=model)
                with open(filename, "wb") as f:
                    for data in r.iter_content(block_size):
                        f.write(data)
                        progress.update(len(data))
                        update_status_file(key, (progress.n / total_size) * 100)

                        # Canceled early?
                        if not read_status_file(key):
                            print("Canceled download detected, deleting partial model")
                            canceled_early = True
                            try:
                                os.remove(filename)
                            except FileNotFoundError:
                                pass
                            break

                progress.close()

                delete_status_file(key)

                if not canceled_early and total_size != 0 and progress.n != total_size:
                    error_message = "Downloaded data size does not match expected size"
                    print(f"Error: {error_message}")
                    return jsonify(
                        {
                            "success": False,
                            "error": error_message,
                        }
                    )

        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            delete_status_file(key)

            # Delete the model if the download has started
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass

            # Specific error handling for each exception type
            if isinstance(e, requests.ConnectionError):
                error_message = "Failed to establish a connection. Please check your internet connection."
            elif isinstance(e, requests.Timeout):
                error_message = "The request timed out. Please try again later."
            else:
                error_message = f"An error occurred while downloading: {str(e)}"

            print(f"Error: {error_message}")
            return jsonify(
                {
                    "success": False,
                    "error": error_message,
                }
            )

    return jsonify({"success": True})


@app.route("/download-progress/<feature>/<model>")
def download_progress_route(feature, model):
    def generate():
        key = f"{feature}_{model}"
        while True:
            progress = read_status_file(key)
            if progress is not None:
                yield f"data:{progress}\n\n"
            time.sleep(1)

    response = app.response_class(
        stream_with_context(generate()), mimetype="text/event-stream"
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response


@app.route("/models/cancel-download", methods=["POST"])
def cancel_download():
    feature = request.json.get("feature")
    model = request.json.get("model")
    key = f"{feature}_{model}"

    if read_status_file(key) is not None:
        delete_status_file(key)
        return jsonify({"success": True}), 200
    else:
        return (
            jsonify({"success": False, "error": f"Download {key} is not active"}),
            200,
        )


@app.route("/models/delete", methods=["POST"])
def models_delete():
    feature = request.json.get("feature")
    model = request.json.get("model")

    if feature not in ["transcribe"]:
        return jsonify({"success": False, "error": f"Invalid feature: {feature}"})

    if feature == "transcribe":
        if model not in ["small", "medium", "large"]:
            return jsonify({"success": False, "error": f"Invalid model: {model}"})

        filename = os.path.join(get_models_dir(), "whisper", f"{model}.pt")
        print(f"Deleting {filename}")

        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

        return jsonify({"success": True}), 200


# Transcribe


def do_transcribe(model, filename):
    model = whisper.load_model(
        model, download_root=os.path.join(get_models_dir(), "whisper")
    )

    print(f"Transcribing: {filename}")

    start_time = time.time()
    result = model.transcribe(filename)
    elapsed_time = time.time() - start_time

    print(f"Transcription finished:\n{result['text']}")
    return {"success": True, "result": result["text"], "time_elapsed": elapsed_time}


@app.route("/transcribe", methods=["POST"])
def transcribe():
    filename = request.json.get("filename")
    model = request.json.get("model")

    # Validate filename
    try:
        if not os.path.exists(filename):
            return jsonify({"success": False, "error": "File does not exist"})

        if (
            not filename.endswith(".wav")
            and not filename.endswith(".mp3")
            and not filename.endswith(".flac")
            and not filename.endswith(".m4a")
        ):
            basename = os.path.basename(filename)
            return jsonify(
                {"success": False, "error": f"{basename} is not an audio file"}
            )
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid file: {e}"})

    # Validate model, it should be either "small", "medium", or "large"
    if model not in ["small", "medium", "large"]:
        return jsonify({"success": False, "error": f"Invalid model: {model}"})

    # Make sure the model is actually downloaded
    if not os.path.exists(os.path.join(get_models_dir(), "whisper", f"{model}.pt")):
        return jsonify(
            {
                "success": False,
                "error": f'You must download the model "{model}" before you can use it',
            }
        )

    transcription = do_transcribe(model, filename)
    return jsonify(transcription)


# gunicorn web server stuff


class CustomWSGIApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.application = app
        self.options = options or {}
        super(CustomWSGIApplication, self).__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def run_gunicorn_server():
    options = {
        "bind": "127.0.0.1:52014",
        "workers": multiprocessing.cpu_count() + 1,
        "timeout": 1200,
        "worker_class": "gevent",
    }

    CustomWSGIApplication(app, options).run()


if __name__ == "__main__":
    run_gunicorn_server()
