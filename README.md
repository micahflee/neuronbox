# NeuronBox

## Getting started

This app is developed in three components, all unfortunately in different languages:

- The desktop app, in `src-tauri`, is using [Tauri](https://tauri.app/) and is implemented in Rust.
- The frontend, in `frontend`, is using [Vue.js](https://vuejs.org/) and is implemented in JavaScript. This is the UI that gets loaded in the native app.
- The backend, in `backend.py`, is a [Flask](https://flask.palletsprojects.com/) app, implemented in Python. This hosts an API that does all the AI magic.

### Backend

The backend needs Python 3 and `ffmpeg` installed (TODO: packaging).

Create a virtual environment and install deps:

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Run the server (on port 52014):

```sh
python backend.py
```

### Frontend

You need Node.js to build this component.

Install dependencies:

```sh
npm install
```

Build the frontend:

```sh
npm run build
```

You generally won't have to build this yourself -- Tauri will do this for you when running the desktop app.

### Desktop app

You need Rust installed. Tauri handles building the frontend for you.

Start the app:

```sh
cargo tauri dev
```

Recommended IDE setup:

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)
