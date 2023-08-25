# NeuronBox

## Getting started:

You need:

- Python3
- Poetry
- Node.js

Install and build the web app:

```sh
# Install backend deps
poetry install

# Install frontend deps and build
cd neuronbox/frontend
npm install
npm run build -m development
cd ../..
```

Start the server:

```sh
poetry run start-neuronbox
```

View the app at http://127.0.0.1:5000.