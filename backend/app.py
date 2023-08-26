import os
from flask import Flask, send_file, jsonify, request

from transcribe import transcribe

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '')
    if origin.startswith('http://127.0.0.1:'):
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@app.route("/transcribe", methods=["POST"])
def transcribe():
    filename = request.form.get("filename")

    try:
        # Make sure file exists
        if not os.path.exists(filename):
            return jsonify({"error": "File does not exist"})
        
        # Check that the file is an audio file (.wav, .mp3, .flac)
        if not filename.endswith(".wav") and not filename.endswith(".mp3") and not filename.endswith(".flac"):
            return jsonify({"error": "File is not an audio file"})
    except:
        return jsonify({"error": "Invalid file"})
    
    transcription = transcribe(filename)
    return jsonify(transcription)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=52014)
