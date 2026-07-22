"""Parser do CSV canónico de importação.

Formato canónico (cabeçalho obrigatório):
    metric_type,metric_value,unit,measured_at

Devolve as medições válidas e um relatório das linhas rejeitadas (número da
linha + motivo), sem abortar o ficheiro por causa de linhas más — política (a).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import TextIO

from measurement import Measurement

EXPECTED_HEADER = ["metric_type", "metric_value", "unit", "measured_at"]


@dataclass(frozen=True)
class RejectedRow:
    """Uma linha do CSV que não passou na validação."""

    line_number: int  # linha no ficheiro (1 = cabeçalho)
    reason: str
    raw: dict[str, str]


@dataclass(frozen=True)
class ParseResult:
    measurements: list[Measurement]
    rejected: list[RejectedRow]

    @property
    def total_rows(self) -> int:
        return len(self.measurements) + len(self.rejected)


class HeaderError(ValueError):
    """O cabeçalho do CSV não corresponde ao formato canónico."""


def _parse_value(raw: str) -> Decimal:
    text = raw.strip()
    try:
        return Decimal(text)
    except InvalidOperation:
        raise ValueError(f"metric_value nao e numerico: {text!r}")


def _parse_measured_at(raw: str) -> datetime:
    text = raw.strip()
    try:
        # fromisoformat aceita offset (ex.: 2026-07-20T08:30:00+01:00).
        return datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f"measured_at nao e ISO 8601 valido: {text!r} "
            "(ex.: 2026-07-20T08:30:00+01:00)"
        )


def parse_csv(stream: TextIO) -> ParseResult:
    """Lê um CSV canónico a partir de um stream de texto."""
    reader = csv.DictReader(stream)

    if reader.fieldnames is None:
        raise HeaderError("Ficheiro vazio ou sem cabeçalho.")
    header = [name.strip() for name in reader.fieldnames]
    if header != EXPECTED_HEADER:
        raise HeaderError(
            "Cabeçalho inesperado.\n"
            f"  esperado: {EXPECTED_HEADER}\n"
            f"  obtido:   {header}"
        )

    measurements: list[Measurement] = []
    rejected: list[RejectedRow] = []

    # enumerate a partir de 2: linha 1 é o cabeçalho.
    for line_number, row in enumerate(reader, start=2):
        try:
            metric_type = (row.get("metric_type") or "").strip()
            unit_raw = (row.get("unit") or "").strip()
            unit = unit_raw or None

            value = _parse_value(row.get("metric_value") or "")
            measured_at = _parse_measured_at(row.get("measured_at") or "")

            measurements.append(
                Measurement(
                    metric_type=metric_type,
                    metric_value=value,
                    measured_at=measured_at,
                    unit=unit,
                )
            )
        except (InvalidOperation, ValueError) as exc:
            rejected.append(RejectedRow(line_number, str(exc), dict(row)))

    return ParseResult(measurements=measurements, rejected=rejected)