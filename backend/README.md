# Backend

Install deps:

```sh
poetry install
```

Run the server (on port 52014):

```sh
poetry run gunicorn app:app -w 4 -b 127.0.0.1:500052014
```