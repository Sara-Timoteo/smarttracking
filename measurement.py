"""Registo normalizado de uma medição — o contrato entre parser e insert.

O parser produz objetos Measurement a partir do CSV canónico; o passo de
importação consome-os para escrever na tabela `measurements` do Supabase.

De propósito, NÃO inclui:
  - user_id  -> atribuído no acto da importação (pseudonimização)
  - source   -> preenchido pelo importador ('manual_import')
  - raw_payload_hash -> calculado pelo importador (idempotência)
  - id, imported_at  -> tratados pela base de dados (defaults)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


# Lista branca de metric_type aceites. Fonte: comentário do CREATE TABLE
# (011_measurements.sql). Ampliar aqui à medida que novos tipos forem precisos.
ALLOWED_METRIC_TYPES: frozenset[str] = frozenset(
    {
        "steps",
        "heart_rate",
        "sleep_duration_min",
    }
)


@dataclass(frozen=True)
class Measurement:
    """Uma medição validada, pronta a inserir (sem user_id/source/hash)."""

    metric_type: str
    metric_value: Decimal
    measured_at: datetime
    unit: str | None = None

    def __post_init__(self) -> None:
        if self.metric_type not in ALLOWED_METRIC_TYPES:
            raise ValueError(
                f"metric_type nao permitido: {self.metric_type!r}. "
                f"Permitidos: {sorted(ALLOWED_METRIC_TYPES)}"
            )
        if self.measured_at.tzinfo is None:
            raise ValueError(
                f"measured_at sem fuso horario: {self.measured_at!r}. "
                "Exige-se ISO 8601 com offset (ex.: 2026-07-20T08:30:00+01:00)."
            )