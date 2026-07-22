"""Núcleo de importação: medições validadas -> linhas prontas para a tabela
`measurements`, com hash de idempotência e resolução do dono via token PII-free.

O user_id NUNCA vem do CSV. Vem da resolução de um token opaco (protocolo da
Secção 5): resolve_user_id(token) -> granter_id. Aqui isolamos essa fronteira
atrás de um Resolver, para o núcleo ficar testável antes de a RPC real existir.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

from measurement import Measurement

SOURCE_MANUAL_IMPORT = "manual_import"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def measurement_hash(m: Measurement) -> str:
    """Hash de idempotência sobre os campos canónicos da medição.

    Deliberadamente sobre os campos normalizados (nao a linha crua do CSV),
    para que reexportar o mesmo dado com espacos/ordem diferentes conte como
    a mesma medicao. Alimenta a UNIQUE(user_id, metric_type, measured_at,
    raw_payload_hash) da tabela measurements.
    """
    canonical = "|".join(
        [
            m.metric_type,
            format(m.metric_value.normalize(), "f"),
            m.unit or "",
            m.measured_at.isoformat(),
        ]
    )
    return sha256_hex(canonical)


class UserIdResolver(Protocol):
    """Fronteira: dado um token opaco, devolve o user_id (granter_id) dono.

    A implementacao real chama uma RPC SECURITY DEFINER no Supabase que valida
    o token (hash, nao-revogado, nao-expirado) e devolve o granter_id. Aqui e
    um Protocol para o nucleo nao depender dessa RPC para ser testado.
    """

    def resolve_user_id(self, token: str) -> str: ...


@dataclass(frozen=True)
class MeasurementRow:
    """Uma linha pronta a inserir em `measurements` (via upsert on_conflict)."""

    user_id: str
    source: str
    metric_type: str
    metric_value: str  # string decimal, para o cliente Supabase/JSON
    unit: str | None
    measured_at: str  # ISO 8601
    raw_payload_hash: str

    def as_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "source": self.source,
            "metric_type": self.metric_type,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "measured_at": self.measured_at,
            "raw_payload_hash": self.raw_payload_hash,
        }


def build_rows(
    measurements: list[Measurement],
    token: str,
    resolver: UserIdResolver,
) -> list[MeasurementRow]:
    """Resolve o dono uma vez e constroi as linhas prontas a inserir."""
    user_id = resolver.resolve_user_id(token)

    rows: list[MeasurementRow] = []
    for m in measurements:
        rows.append(
            MeasurementRow(
                user_id=user_id,
                source=SOURCE_MANUAL_IMPORT,
                metric_type=m.metric_type,
                metric_value=format(m.metric_value.normalize(), "f"),
                unit=m.unit,
                measured_at=m.measured_at.isoformat(),
                raw_payload_hash=measurement_hash(m),
            )
        )
    return rows