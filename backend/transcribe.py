import os
import whisper
import common
import time


def do_transcribe(model, filename):
    model = whisper.load_model(
        model, download_root=os.path.join(common.get_models_dir(), "whisper")
    )

    print(f"Transcribing: {filename}")

    start_time = time.time()
    result = model.transcribe(filename)
    elapsed_time = time.time() - start_time

    print(f"Transcription finished:\n{result['text']}")
    return {"success": True, "result": result["text"], "time_elapsed": elapsed_time}
