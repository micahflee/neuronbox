# NeuronBox

## Getting started

This app is developed in three components, all unfortunately in different languages:

- `native` is the native desktop app using [Tauri](https://tauri.app/), implemented in Rust.
- `frontend` is the frontend using [Vue.js](https://vuejs.org/), implemented in JavaScript. This is the UI that gets loaded in the native app.
- `backend` is the backend a [Flask](https://flask.palletsprojects.com/) app, implemented in Python. This hosts an API that does all the AI magic.

Each component has its own `README.md` file with instructions on getting started.
