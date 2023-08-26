# Backend

You need Python 3.

Create a virtual environment and install deps:

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Run the server (on port 52014):

```sh
gunicorn app:app -w 4 -b 127.0.0.1:500052014
```