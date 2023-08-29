import os
import sys
import time
import traceback
import shutil

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

# Mapping of language codes to names for Helsinki NLP models, for popular languages:
# https://huggingface.co/Helsinki-NLP
language_codes = {
    "bg": "Bulgarian",
    "zh": "Chinese",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "de": "German",
    "el": "Greek",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "jap": "Japanese",
    # "ko": "Korean",  #
    "lv": "Latvian",
    "lt": "Lithuanian",
    # "nb": "Norwegian (bokmål)",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "es": "Spanish",
    "sv": "Swedish",
    "tr": "Turkish",
    "uk": "Ukrainian",
}

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


# Helpers


def get_config_dir():
    return appdirs.user_config_dir("neuronbox")


def get_models_dir():
    return os.path.join(get_config_dir(), "models")


def get_download_status_dir():
    return os.path.join(get_config_dir(), "download_status")


class DownloadStatus:
    def __init__(self, key):
        self.key = key.replace("/", "_")
        self.progress = 0
        self.status_filename = os.path.join(
            get_download_status_dir(), f"{self.key}.status"
        )
        self.cancel_filename = os.path.join(
            get_download_status_dir(), f"{self.key}.cancel"
        )

        self._load_status()
        self.update(self.progress)

    def _load_status(self):
        if os.path.exists(self.status_filename):
            with open(self.status_filename, "r") as f:
                try:
                    self.progress = float(f.read())
                except ValueError:
                    self.progerss = 0

        self.canceled = os.path.exists(self.cancel_filename)

    def update(self, progress):
        self.progress = progress
        with open(self.status_filename, "w") as f:
            f.write(str(progress))

    def cancel(self):
        self.canceled = True
        with open(self.cancel_filename, "w") as f:
            f.write("canceled")

    def is_canceled(self):
        self._load_status()
        return self.canceled

    def clean(self):
        if os.path.exists(self.status_filename):
            os.remove(self.status_filename)
        if os.path.exists(self.cancel_filename):
            os.remove(self.cancel_filename)


# Create folders if they don't exist

if not os.path.exists(get_models_dir()):
    os.makedirs(get_models_dir())

if not os.path.exists(get_download_status_dir()):
    os.makedirs(get_download_status_dir())

# Delete download status files left over from last time
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


def download(download_url, filename, key, model):
    canceled_early = False
    status = DownloadStatus(key)

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
                    status.update((progress.n / total_size) * 100)

                    # Canceled early?
                    if status.is_canceled():
                        print("Canceled download detected, deleting partial model")
                        canceled_early = True
                        try:
                            os.remove(filename)
                        except FileNotFoundError:
                            pass
                        break

            progress.close()

            status.clean()

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
        status.clean()

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


@app.route("/models")
def models():
    # Transcribe models
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

    # Translate models
    # (start with only target language English)
    helsinki_dir = os.path.join(get_models_dir(), "Helsinki-NLP")
    if not os.path.exists(helsinki_dir):
        os.makedirs(helsinki_dir)

    translate_models = []
    for language_code in language_codes:
        # Skip English, since we don't translate from English to English
        if language_code == "en":
            continue

        language_name = language_codes[language_code]

        model_path = os.path.join(helsinki_dir, f"opus-mt-{language_code}-en")
        is_downloaded = os.path.isdir(model_path)
        if is_downloaded:
            size = sum(
                os.path.getsize(os.path.join(model_path, f))
                for f in os.listdir(model_path)
                if os.path.isfile(os.path.join(model_path, f))
            )
        else:
            size = 0

        translate_models.append(
            {
                "name": f"opus-mt-{language_code}-en",
                "description": f"{language_name} to English",
                "downloaded": is_downloaded,
                "size": size,
            }
        )

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
                ],
                "translate": translate_models,
            }
        }
    )


@app.route("/models/download", methods=["POST"])
def models_download():
    feature = request.json.get("feature")
    model = request.json.get("model")
    key = f"{feature}_{model}"
    print(f"Starting download: {key}")

    DownloadStatus(key)

    if feature not in ["transcribe", "translate"]:
        return jsonify({"success": False, "error": f"Invalid feature: {feature}"})

    if feature == "transcribe":
        if model not in ["small", "medium", "large"]:
            return jsonify({"success": False, "error": f"Invalid model: {model}"})

        download_url = whisper._MODELS[model]
        filename = os.path.join(get_models_dir(), "whisper", f"{model}.pt")
        print(f"Key: {key}: Downloading {download_url} to {filename}")

        ret = download(download_url, filename, key, model)
        if ret != None:
            return ret

    elif feature == "translate":
        valid_model_names = []
        for language_code in language_codes:
            if language_code != "en":
                valid_model_names.append(f"opus-mt-{language_code}-en")
        if model not in valid_model_names:
            return jsonify({"success": False, "error": f"Invalid model: {model}"})

        local_dir = os.path.join(get_models_dir(), "Helsinki-NLP", model)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        base_url = f"https://huggingface.co/Helsinki-NLP/{model}/resolve/main"
        filenames = [
            # tokenizer
            "tokenizer_config.json",
            "config.json",
            "source.spm",
            "target.spm",
            "vocab.json",
            # model
            "pytorch_model.bin",
            "generation_config.json",
        ]
        for filename in filenames:
            download_url = f"{base_url}/{filename}"
            local_filename = os.path.join(local_dir, filename)

            print(f"Key: {key}: Downloading {download_url} to {local_filename}")
            ret = download(download_url, local_filename, key, model)
            if ret != None:
                return ret

    return jsonify({"success": True})


@app.route("/download-progress/<feature>/<model>")
def download_progress_route(feature, model):
    def generate():
        key = f"{feature}_{model}"
        while True:
            status = DownloadStatus(key)
            yield f"data:{status.progress}\n\n"
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
    print(f"Canceling download: {key}")

    status = DownloadStatus(key)
    status.cancel()

    return jsonify({"success": True}), 200


@app.route("/models/delete", methods=["POST"])
def models_delete():
    feature = request.json.get("feature")
    model = request.json.get("model")
    print(f"Deleting model: {feature} {model}")

    if feature not in ["transcribe", "translate"]:
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

    if feature == "translate":
        valid_model_names = []
        for language_code in language_codes:
            if language_code != "en":
                valid_model_names.append(f"opus-mt-{language_code}-en")
        if model not in valid_model_names:
            return jsonify({"success": False, "error": f"Invalid model: {model}"})

        model_path = os.path.join(get_models_dir(), "Helsinki-NLP", model)
        shutil.rmtree(model_path, ignore_errors=True)
        return jsonify({"success": True}), 200

    return jsonify({"success": False, "error": f"Invalid feature: {feature}"})


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
    print(f"Transcribing: {filename} with {model}")

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


# Translate


@app.route("/languages")
def languages():
    return jsonify(language_codes)


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
        "workers": 4,  # multiprocessing.cpu_count() + 1,
        "timeout": 1200,
        "worker_class": "gevent",
        "errorlog": os.path.join(get_config_dir(), "error.log"),
        "capture_output": True,
        "loglevel": "debug",
    }

    CustomWSGIApplication(app, options).run()


if __name__ == "__main__":
    # run_gunicorn_server()

    app.run(debug=True, host="127.0.0.1", port=52014)
