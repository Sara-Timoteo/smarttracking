"""Microserviço Flask - importação manual de telemetria de wearable."""
from flask import Flask, jsonify

from config import Config
from supabase_client import get_client

# Tabela usada apenas para o healthcheck de ligação à base de dados.
# Se a tua tabela de teste tiver outro nome, troca aqui.
HEALTHCHECK_TABLE = "profiles"


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.get("/health/db")
    def health_db():
        try:
            client = get_client()
            client.table(HEALTHCHECK_TABLE).select("*").limit(1).execute()
            return jsonify(status="ok", database="reachable"), 200
        except Exception as exc:
            return jsonify(status="error", detail=str(exc)), 503

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.FLASK_ENV == "development",
    )
