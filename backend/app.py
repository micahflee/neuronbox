import os
from flask import Flask, send_file, jsonify, request
from .transcribe import transcribe

app = Flask(__name__, static_folder="frontend/dist/assets", static_url_path="/assets")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    filename = request.form.get("filename")

    # Make sure file exists
    if not os.path.exists(filename):
        return jsonify({"error": "File does not exist"})
    
    # Check that the file is an audio file (.wav, .mp3, .flac)
    if not filename.endswith(".wav") and not filename.endswith(".mp3") and not filename.endswith(".flac"):
        return jsonify({"error": "File is not an audio file"})
    
    transcription = transcribe(filename)
    return jsonify(transcription)


if __name__ == "__main__":
    app.run()
