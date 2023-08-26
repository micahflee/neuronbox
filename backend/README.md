# Backend

You need Python 3. You also need `ffmpeg` installed (TODO: packaging).

Create a virtual environment and install deps:

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Run the server (on port 52014):

```sh
python app.py
```