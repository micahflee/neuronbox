# NeuronBox

## Getting started

This app is developed in three components, all unfortunately in different languages:

- `native` is the native desktop app using [Tauri](https://tauri.app/), implemented in Rust.
- `frontend` is the frontend using [Vue.js](https://vuejs.org/), implemented in JavaScript. This is the UI that gets loaded in the native app.
- `backend` is the backend a [Flask](https://flask.palletsprojects.com/) app, implemented in Python. This hosts an API that does all the AI magic.

## Dependencies

- Install Rust, Python, and Node.js
- Install Poetry (`python3 -m pip install poetry`)

Install and build the web app:

```sh
# Install backend deps
poetry install

# Install frontend deps and build
poetry run build-frontend
```

Start the server:

```sh
poetry run start-server
```

View the app at http://127.0.0.1:5000.