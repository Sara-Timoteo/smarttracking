"""Conversor para a exportação do Samsung Health (Galaxy Watch / telemóvel).

Como exportar: Samsung Health -> Definições -> "Transferir dados pessoais".
Sai uma pasta (ou zip) com um CSV por tipo de dado, por exemplo:
    com.samsung.shealth.tracker.heart_rate.<data>.csv
    com.samsung.shealth.tracker.pedometer_step_count.<data>.csv
    com.samsung.shealth.sleep.<data>.csv

Particularidades do formato:
  - a 1.ª linha é de metadados (ex.: "com.samsung.shealth.tracker.heart_rate,6315006,3");
    o cabeçalho verdadeiro vem a seguir;
  - os nomes das colunas têm prefixo (ex.: "com.samsung.health.heart_rate.start_time"),
    por isso aqui procura-se cada coluna pelo FIM do nome ("start_time");
  - as horas estão em UTC e o fuso vem numa coluna à parte ("time_offset",
    no formato "UTC+0100");
  - as linhas costumam acabar com uma vírgula a mais.

ESTADO: construído a partir de documentação pública e de projetos que leem
este formato. Não foi ainda validado com uma exportação real.

Minimização: a exportação traz dezenas de ficheiros (localização de treinos,
peso, alimentação, stress...). Só os três ficheiros acima são abertos.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from measurement import Measurement

from ._files import as_text, iter_files
from .base import CANONICAL_UNITS, ConversionResult, SkippedRow, to_decimal

# Ficheiro -> (métrica, coluna do valor). Para o sono, o valor é calculado.
FILES = {
    "com.samsung.shealth.tracker.heart_rate.*.csv": ("heart_rate", "heart_rate"),
    "com.samsung.shealth.tracker.pedometer_step_count.*.csv": ("steps", "count"),
    "com.samsung.shealth.sleep.*.csv": ("sleep_duration_min", None),
}

OFFSET_RE = re.compile(r"^UTC([+-])(\d{2}):?(\d{2})$")


def _offset(text: str) -> timezone:
    m = OFFSET_RE.match(text.strip())
    if not m:
        raise ValueError(f"time_offset inválido: {text!r} (esperado ex.: UTC+0100)")
    sign = 1 if m.group(1) == "+" else -1
    return timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))


def _utc(text: str) -> datetime:
    text = text.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    raise ValueError(f"data inválida: {text!r}")


def _rows(f):
    """Salta a linha de metadados e devolve linhas com colunas pelo nome curto."""
    reader = csv.reader(as_text(f))
    header = None
    for line_number, row in enumerate(reader, start=1):
        if header is None:
            # O cabeçalho é a primeira linha que tem uma coluna "...start_time".
            if any(c.strip().endswith("start_time") for c in row):
                header = [c.strip().rsplit(".", 1)[-1] for c in row]
            continue
        if not any(v.strip() for v in row):
            continue
        yield line_number, dict(zip(header, row))
    if header is None:
        raise ValueError("não encontrei o cabeçalho (coluna start_time)")


class SamsungHealthConverter:
    name = "samsung-health"

    def inspect(self, path: Path) -> dict[str, int]:
        """Conta quantos ficheiros de cada tipo há na exportação."""
        counts: Counter = Counter()
        for name, _f in iter_files(path, "*.csv"):
            base = Path(name).name
            kind = re.sub(r"\.\d{12,}\.csv$|\.csv$", "", base)
            counts[kind] += 1
        return dict(sorted(counts.items()))

    def convert_path(self, path: Path) -> ConversionResult:
        result = ConversionResult()
        found = set()

        for pattern, (metric, value_col) in FILES.items():
            for name, f in iter_files(path, pattern):
                found.add(metric)
                short = Path(name).name
                try:
                    rows = list(_rows(f))
                except ValueError as exc:
                    result.skipped.append(SkippedRow(short, str(exc)))
                    continue

                for line_number, row in rows:
                    where = f"{short}, linha {line_number}"
                    try:
                        tz = _offset(row.get("time_offset", ""))
                        start = _utc(row.get("start_time", "")).astimezone(tz)
                        if metric == "sleep_duration_min":
                            end = _utc(row.get("end_time", "")).astimezone(tz)
                            value = Decimal(int((end - start).total_seconds() // 60))
                            if value <= 0:
                                raise ValueError("fim do sono antes do início")
                        else:
                            raw = (row.get(value_col) or "").strip()
                            if raw == "":
                                continue
                            value = to_decimal(raw)
                        result.measurements.append(
                            Measurement(metric, value, start, CANONICAL_UNITS[metric])
                        )
                    except (ValueError, InvalidOperation) as exc:
                        result.skipped.append(SkippedRow(where, str(exc)))

        if not found:
            result.notes.append(
                "Não encontrei nenhum dos ficheiros esperados (heart_rate, "
                "pedometer_step_count, sleep). Usa --inspecionar para ver o que há."
            )
        return result
