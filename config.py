"""Configuração central — carrega o .env da raiz do projeto."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega o .env que está na mesma pasta (a raiz do repo).
load_dotenv(Path(__file__).resolve().parent / ".env")


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("PORT", "5000"))


def require_service_role() -> None:
    """Garante que temos o mínimo para falar com o Supabase pelo lado servidor.

    Chamada só quando o cliente Supabase é criado — assim a rota /health
    corre mesmo sem chaves configuradas.
    """
    missing = [
        name
        for name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")
        if not getattr(Config, name)
    ]
    if missing:
        raise RuntimeError(
            "Faltam variáveis de ambiente: "
            + ", ".join(missing)
            + ". Preenche o .env (ver .env.example)."
        )
