"""Microserviço Flask - importação manual de telemetria de wearable."""
import truststore

# Faz o Python confiar no armazém de certificados do sistema operativo (Windows),
# que já inclui o CA interno da rede da CMVFX. Necessário porque a rede faz
# inspeção de TLS. Tem de correr antes de qualquer ligação HTTPS.
truststore.inject_into_ssl()

import io  # noqa: E402

from flask import Flask, jsonify, request  # noqa: E402

from config import Config  # noqa: E402
from supabase_client import get_client  # noqa: E402
from parser_csv import parse_csv, HeaderError  # noqa: E402
from importer import build_rows  # noqa: E402
from supabase_import import (  # noqa: E402
    SupabaseResolver,
    upsert_measurements,
    TokenResolutionError,
)

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

    @app.post("/import")
    def import_measurements():
        token = (request.form.get("token") or "").strip()
        if not token:
            return jsonify(status="error", detail="Falta o campo 'token'."), 400

        file = request.files.get("file")
        if file is None:
            return jsonify(
                status="error", detail="Falta o ficheiro CSV (campo 'file')."
            ), 400

        # utf-8-sig tolera o BOM que o Excel costuma pôr no início do ficheiro.
        text = file.stream.read().decode("utf-8-sig")

        try:
            result = parse_csv(io.StringIO(text))
        except HeaderError as exc:
            return jsonify(status="error", detail=str(exc)), 400

        client = get_client()
        resolver = SupabaseResolver(client)
        try:
            rows = build_rows(result.measurements, token=token, resolver=resolver)
        except TokenResolutionError as exc:
            return jsonify(status="error", detail=str(exc)), 403

        inserted = upsert_measurements(client, rows)

        return jsonify(
            status="ok",
            accepted=len(result.measurements),
            inserted=inserted,
            rejected=[
                {"line": r.line_number, "reason": r.reason} for r in result.rejected
            ],
        ), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.FLASK_ENV == "development",
    )