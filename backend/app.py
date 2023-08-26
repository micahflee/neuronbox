import os
import time
import traceback

import requests
from flask import Flask, jsonify, request, stream_with_context
from flask_cors import CORS
from tqdm import tqdm

import common
from transcribe import do_transcribe, whisper

app = Flask(__name__)
CORS(app)  # TODO: restrict origins to just localhost


@app.errorhandler(Exception)
def handle_exception(e):
    # Capture the stack trace
    trace = traceback.format_exc()
    # Log it, send it to an external service, etc.
    app.logger.error(trace)
    return str(e), 500


# Models


@app.route("/models")
def models():
    whisper_dir = os.path.join(common.get_models_dir(), "whisper")
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
                        "description": "Medium, requires ~5GB RAM (recommended)",
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
    common.create_status_file(key)

    if feature not in ["transcribe"]:
        return jsonify({"success": False, "error": f"Invalid feature: {feature}"})

    if feature == "transcribe":
        if model not in ["small", "medium", "large"]:
            return jsonify({"success": False, "error": f"Invalid model: {model}"})

        download_url = whisper._MODELS[model]
        filename = os.path.join(common.get_models_dir(), "whisper", f"{model}.pt")
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
                        common.update_status_file(key, (progress.n / total_size) * 100)

                        # Canceled early?
                        if not common.read_status_file(key):
                            print("Canceled download detected, deleting partial model")
                            canceled_early = True
                            try:
                                os.remove(filename)
                            except FileNotFoundError:
                                pass
                            break

                progress.close()

                common.delete_status_file(key)

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
            common.delete_status_file(key)

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
            progress = common.read_status_file(key)
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

    if common.read_status_file(key) is not None:
        common.delete_status_file(key)
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

        filename = os.path.join(common.get_models_dir(), "whisper", f"{model}.pt")
        print(f"Deleting {filename}")

        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

        return jsonify({"success": True}), 200


# Transcribe


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

    transcription = do_transcribe(model, filename)
    return jsonify(transcription)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=52014)
