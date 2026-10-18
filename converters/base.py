"""Molde comum para conversores de exportações de wearables.

Cada marca (Garmin, Huawei, Apple, Fitbit...) exporta os dados num formato
diferente. Um conversor transforma essa exportação em objetos Measurement —
o mesmo contrato que o parser do CSV canónico já produz. A partir daí, tudo
o resto (token, hash, upsert, RLS) é igual, venha a medição de onde vier.

Minimização de dados (RGPD, art. 5.º, n.º 1, al. c)):
os conversores correm no dispositivo do utilizador e só extraem as métricas
da lista branca (ALLOWED_METRIC_TYPES). Tudo o resto que vem na exportação
(GPS, contactos, notas, etc.) é descartado ANTES de qualquer envio.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol, TextIO

from measurement import Measurement
from parser_csv import EXPECTED_HEADER


@dataclass(frozen=True)
class SkippedRow:
    """Uma linha/registo da exportação que não pôde ser convertido."""

    location: str  # ex.: "linha 7" ou "registo 12"
    reason: str


@dataclass
class ConversionResult:
    measurements: list[Measurement] = field(default_factory=list)
    skipped: list[SkippedRow] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # avisos para quem converte


# Unidade canónica de cada métrica: todos os conversores entregam nestas.
CANONICAL_UNITS: dict[str, str] = {
    "steps": "steps",
    "heart_rate": "bpm",
    "sleep_duration_min": "min",
}


def to_decimal(raw) -> Decimal:
    """Converte um valor para Decimal, com uma mensagem de erro legível."""
    try:
        return Decimal(str(raw).strip())
    except InvalidOperation:
        raise ValueError(f"valor não numérico: {raw!r}")


class Converter(Protocol):
    """O que qualquer conversor tem de saber fazer.

    `path` pode ser um ficheiro, uma pasta ou um .zip, conforme a marca.
    """

    name: str

    def convert_path(self, path: Path) -> ConversionResult: ...

    def inspect(self, path: Path) -> dict[str, int]:
        """Conta o que existe na exportação (tipos, chaves, fontes...),
        para ajudar a configurar o conversor sem abrir os ficheiros à mão."""
        ...


def write_canonical_csv(measurements: list[Measurement], out: TextIO) -> None:
    """Escreve medições no CSV canónico aceite pelo POST /import."""
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(EXPECTED_HEADER)
    for m in sorted(measurements, key=lambda x: (x.measured_at, x.metric_type)):
        writer.writerow(
            [
                m.metric_type,
                format(m.metric_value.normalize(), "f"),
                m.unit or "",
                m.measured_at.isoformat(),
            ]
        )
