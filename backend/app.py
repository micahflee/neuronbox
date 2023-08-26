import os
from flask import Flask, jsonify, request

from transcribe import do_transcribe

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
    filename = request.json.get("filename")
    model = request.json.get("model")

    # Validate filename
    try:
        if not os.path.exists(filename):
            return jsonify({"error": "File does not exist"})
        
        if not filename.endswith(".wav") and not filename.endswith(".mp3") and not filename.endswith(".flac") and not filename.endswith(".m4a"):
            basename = os.path.basename(filename)
            return jsonify({"error": f"{basename} is not an audio file"})
    except Exception as e:
        return jsonify({"error": f"Invalid file: {e}"})
    
    # Validate model, it should be either "small", "medium", or "large"
    if model not in ["small", "medium", "large"]:
        return jsonify({"error": f"Invalid model: {model}"})

    transcription = do_transcribe(model, filename)
    return jsonify(transcription)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=52014)
