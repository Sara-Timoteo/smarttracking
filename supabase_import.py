"""Camada que liga o núcleo de importação ao Supabase real.

- SupabaseResolver: resolve token -> user_id via RPC SECURITY DEFINER. O token
  em claro NUNCA sai do cliente; viaja apenas o seu hash SHA-256.
- upsert_measurements: escreve em `measurements` com upsert on_conflict na
  UNIQUE, garantindo idempotência (reimportar não duplica).
"""
from __future__ import annotations

from importer import MeasurementRow, sha256_hex

RESOLVE_RPC = "resolve_import_user_id"
MEASUREMENTS_TABLE = "measurements"
ON_CONFLICT = "user_id,metric_type,measured_at,raw_payload_hash"


class TokenResolutionError(RuntimeError):
    """O token não resolveu para um dono (inválido, expirado ou revogado)."""


class SupabaseResolver:
    """Implementa o UserIdResolver contra o Supabase real."""

    def __init__(self, client):
        self._client = client

    def resolve_user_id(self, token: str) -> str:
        token_hash = sha256_hex(token)
        resp = self._client.rpc(RESOLVE_RPC, {"p_token_hash": token_hash}).execute()
        user_id = resp.data
        if not user_id:
            raise TokenResolutionError(
                "Token invalido, expirado ou revogado (nao resolveu para um dono)."
            )
        return user_id


def upsert_measurements(client, rows: list[MeasurementRow]) -> int:
    """Faz upsert das linhas em `measurements`. Devolve o nº de linhas enviadas."""
    if not rows:
        return 0
    payload = [r.as_dict() for r in rows]
    client.table(MEASUREMENTS_TABLE).upsert(
        payload, on_conflict=ON_CONFLICT
    ).execute()
    return len(payload)