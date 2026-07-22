"""Microserviço Flask - importação manual de telemetria de wearable."""
import truststore

# Faz o Python confiar no armazém de certificados do sistema operativo (Windows),
# que já inclui o CA interno da rede da CMVFX. Necessário porque a rede faz
# inspeção de TLS. Tem de correr antes de qualquer ligação HTTPS.
truststore.inject_into_ssl()

from flask import Flask, jsonify  # noqa: E402

from config import Config  # noqa: E402
from supabase_client import get_client  # noqa: E402

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
