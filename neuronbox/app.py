from flask import Flask, send_file

app = Flask(__name__, static_folder="frontend/dist/assets", static_url_path="/assets")


@app.route("/")
def index():
    return send_file("frontend/dist/index.html")


if __name__ == "__main__":
    app.run()
