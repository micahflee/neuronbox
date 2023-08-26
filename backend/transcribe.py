import whisper

def do_transcribe(model, filename):
    print("before load_model")
    model = whisper.load_model(model)
    print("before transcribe")
    result = model.transcribe(filename)
    print(result)
    return {"result": result}