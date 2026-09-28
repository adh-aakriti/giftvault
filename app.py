import os
from flask import Flask
from db import init_db

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return "hello"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)