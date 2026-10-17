import os

from flask import Flask, jsonify
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        message="Hello Pod",
        pod_name=os.getenv("POD_NAME", "local"),
        pod_namespace=os.getenv("POD_NAMESPACE", "local"),
        pod_ip=os.getenv("POD_IP", "unassigned"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
