"""Microserviço Flask — importação manual de telemetria de wearable."""
from flask import Flask, jsonify

from config import Config


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.FLASK_ENV == "development",
    )
