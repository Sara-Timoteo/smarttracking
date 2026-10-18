"""Conversor genérico para exportações em CSV, configurado por um mapeamento.

Serve para qualquer relógio/app que exporte uma tabela (uma linha por momento,
uma coluna por métrica). Em vez de programar um conversor por marca, escreve-se
um pequeno ficheiro JSON que diz que coluna corresponde a quê. Exemplo:

    {
      "name": "relogio-exemplo",
      "delimiter": ";",
      "decimal": ",",
      "timestamp": {
        "column": "Data",
        "format": "%d/%m/%Y %H:%M",
        "timezone": "Europe/Lisbon"
      },
      "metrics": {
        "steps":              {"column": "Passos"},
        "heart_rate":         {"column": "FC média"},
        "sleep_duration_min": {"column": "Sono (h)", "multiply": 60}
      }
    }

Só as colunas indicadas em "timestamp" e "metrics" são lidas. Todas as outras
colunas da exportação são ignoradas (minimização de dados).
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TextIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from measurement import ALLOWED_METRIC_TYPES, Measurement

from .base import CANONICAL_UNITS, ConversionResult, SkippedRow

class MappingError(ValueError):
    """O ficheiro de mapeamento está mal construído."""


@dataclass(frozen=True)
class MetricMapping:
    metric_type: str
    column: str
    multiply: Decimal = Decimal(1)


@dataclass(frozen=True)
class CsvMapping:
    name: str
    delimiter: str
    decimal: str
    thousands: str
    ts_column: str
    ts_format: str | None  # None = ISO 8601
    timezone: ZoneInfo | None
    metrics: tuple[MetricMapping, ...]

    @classmethod
    def from_dict(cls, data: dict) -> "CsvMapping":
        try:
            ts = data["timestamp"]
            ts_column = ts["column"]
            metrics_raw = data["metrics"]
        except (KeyError, TypeError) as exc:
            raise MappingError(f"Falta o campo obrigatório {exc} no mapeamento.")

        tz = None
        if ts.get("timezone"):
            try:
                tz = ZoneInfo(ts["timezone"])
            except ZoneInfoNotFoundError:
                raise MappingError(
                    f"Fuso horário desconhecido: {ts['timezone']!r} "
                    "(ex.: 'Europe/Lisbon'). No Windows, instala o pacote 'tzdata'."
                )

        if not metrics_raw:
            raise MappingError("O mapeamento não indica nenhuma métrica.")

        metrics = []
        for metric_type, spec in metrics_raw.items():
            if metric_type not in ALLOWED_METRIC_TYPES:
                raise MappingError(
                    f"Métrica fora da lista branca: {metric_type!r}. "
                    f"Permitidas: {sorted(ALLOWED_METRIC_TYPES)}"
                )
            if "column" not in spec:
                raise MappingError(f"A métrica {metric_type!r} não indica 'column'.")
            try:
                multiply = Decimal(str(spec.get("multiply", 1)))
            except InvalidOperation:
                raise MappingError(f"'multiply' inválido em {metric_type!r}.")
            metrics.append(MetricMapping(metric_type, spec["column"], multiply))

        decimal = data.get("decimal", ".")
        return cls(
            name=data.get("name", "csv-generico"),
            delimiter=data.get("delimiter", ","),
            decimal=decimal,
            # Se a vírgula é decimal, o separador de milhares mais provável é o ponto.
            thousands=data.get("thousands", "." if decimal == "," else ","),
            ts_column=ts_column,
            ts_format=ts.get("format"),
            timezone=tz,
            metrics=tuple(metrics),
        )

    @classmethod
    def load(cls, path: str | Path) -> "CsvMapping":
        with open(path, encoding="utf-8") as f:
            try:
                return cls.from_dict(json.load(f))
            except json.JSONDecodeError as exc:
                raise MappingError(f"O mapeamento não é JSON válido: {exc}")


class GenericCsvConverter:
    def __init__(self, mapping: CsvMapping):
        self.mapping = mapping
        self.name = mapping.name

    # --- leitura de valores -------------------------------------------------

    def _number(self, raw: str) -> Decimal:
        text = raw.strip().replace(" ", "")
        if self.mapping.thousands:
            text = text.replace(self.mapping.thousands, "")
        if self.mapping.decimal != ".":
            text = text.replace(self.mapping.decimal, ".")
        try:
            return Decimal(text)
        except InvalidOperation:
            raise ValueError(f"valor não numérico: {raw!r}")

    def _timestamp(self, raw: str) -> datetime:
        text = raw.strip()
        try:
            if self.mapping.ts_format:
                dt = datetime.strptime(text, self.mapping.ts_format)
            else:
                dt = datetime.fromisoformat(text)
        except ValueError:
            fmt = self.mapping.ts_format or "ISO 8601"
            raise ValueError(f"data inválida: {raw!r} (formato esperado: {fmt})")

        if dt.tzinfo is None:
            if self.mapping.timezone is None:
                raise ValueError(
                    f"data sem fuso horário: {raw!r}. "
                    "Indica 'timezone' no mapeamento (ex.: 'Europe/Lisbon')."
                )
            dt = dt.replace(tzinfo=self.mapping.timezone)
        return dt

    # --- conversão ----------------------------------------------------------

    def convert_path(self, path: Path) -> ConversionResult:
        with open(path, encoding="utf-8-sig", newline="") as f:
            return self.convert(f)

    def inspect(self, path: Path) -> dict[str, int]:
        """Lista as colunas da exportação, para ajudar a escrever o mapeamento."""
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter=self.mapping.delimiter)
            header = next(reader, [])
            counts = {h.strip(): 0 for h in header}
            for row in reader:
                for h, v in zip(header, row):
                    if v.strip():
                        counts[h.strip()] += 1
        return counts

    def convert(self, stream: TextIO) -> ConversionResult:
        result = ConversionResult()
        reader = csv.DictReader(stream, delimiter=self.mapping.delimiter)

        header = [h.strip() for h in (reader.fieldnames or [])]
        needed = [self.mapping.ts_column] + [m.column for m in self.mapping.metrics]
        missing = [c for c in needed if c not in header]
        if missing:
            raise MappingError(
                f"Colunas em falta na exportação: {missing}. "
                f"Colunas encontradas: {header}"
            )

        for line_number, row in enumerate(reader, start=2):
            row = {(k or "").strip(): (v or "") for k, v in row.items()}
            try:
                measured_at = self._timestamp(row[self.mapping.ts_column])
            except ValueError as exc:
                result.skipped.append(SkippedRow(f"linha {line_number}", str(exc)))
                continue

            for metric in self.mapping.metrics:
                raw = row.get(metric.column, "").strip()
                if raw == "":
                    continue  # célula vazia = sem medição nesse momento
                try:
                    value = self._number(raw) * metric.multiply
                    result.measurements.append(
                        Measurement(
                            metric_type=metric.metric_type,
                            metric_value=value,
                            measured_at=measured_at,
                            unit=CANONICAL_UNITS.get(metric.metric_type),
                        )
                    )
                except ValueError as exc:
                    result.skipped.append(
                        SkippedRow(f"linha {line_number}, coluna {metric.column!r}", str(exc))
                    )
        return result
