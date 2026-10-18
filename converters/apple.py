"""Conversor para a exportação do Apple Health (iPhone / Apple Watch).

Como exportar: app Saúde -> foto de perfil -> "Exportar todos os dados de
saúde". Sai um export.zip com apple_health_export/export.xml lá dentro.
Este conversor aceita o export.zip, a pasta descompactada ou o export.xml.

Estrutura (cada medição é um elemento <Record>):
    <Record type="HKQuantityTypeIdentifierStepCount" sourceName="iPhone"
            unit="count" startDate="2026-07-20 08:30:00 +0100"
            endDate="2026-07-20 08:45:00 +0100" value="1234"/>

Tipos usados:
    HKQuantityTypeIdentifierStepCount        -> steps
    HKQuantityTypeIdentifierHeartRate        -> heart_rate (unidade count/min)
    HKCategoryTypeIdentifierSleepAnalysis    -> sleep_duration_min
        (soma dos períodos "a dormir" de cada noite; "na cama" e "acordado"
         não contam)

Duplicados: o iPhone e o Apple Watch contam passos ao mesmo tempo. Usa a
opção de fonte (ex.: só "Watch") para não somar o mesmo passo duas vezes.

Minimização: o export.xml traz centenas de tipos (treinos com GPS, ECG,
ciclos menstruais, medicação...). Só os três tipos acima são lidos.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from measurement import Measurement

from ._files import iter_files
from .base import CANONICAL_UNITS, ConversionResult, SkippedRow, to_decimal

STEPS = "HKQuantityTypeIdentifierStepCount"
HEART_RATE = "HKQuantityTypeIdentifierHeartRate"
SLEEP = "HKCategoryTypeIdentifierSleepAnalysis"

# Valores de sono que contam como "a dormir". Versões antigas do iOS usam
# só "Asleep"; a partir do iOS 16 há fases (Core, Deep, REM) e "Unspecified".
ASLEEP_VALUES = {
    "HKCategoryValueSleepAnalysisAsleep",
    "HKCategoryValueSleepAnalysisAsleepUnspecified",
    "HKCategoryValueSleepAnalysisAsleepCore",
    "HKCategoryValueSleepAnalysisAsleepDeep",
    "HKCategoryValueSleepAnalysisAsleepREM",
}

DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"  # ex.: 2026-07-20 08:30:00 +0100


def _parse_date(text: str) -> datetime:
    return datetime.strptime(text.strip(), DATE_FORMAT)


class AppleHealthConverter:
    name = "apple-health"

    def __init__(self, source_filter: str | None = None):
        # Se indicado, só aceita registos cuja fonte contenha este texto.
        self.source_filter = source_filter.lower() if source_filter else None

    def _records(self, path: Path):
        found = False
        for _name, f in iter_files(path, "export.xml"):
            found = True
            # iterparse lê aos bocados: o export.xml pode ter centenas de MB.
            for _event, elem in ET.iterparse(f, events=("end",)):
                if elem.tag == "Record":
                    yield elem
                elem.clear()
        if not found:
            raise FileNotFoundError(
                "Não encontrei o export.xml. Indica o export.zip, a pasta "
                "apple_health_export ou o próprio export.xml."
            )

    def _accept_source(self, elem) -> bool:
        if self.source_filter is None:
            return True
        return self.source_filter in elem.get("sourceName", "").lower()

    def inspect(self, path: Path) -> dict[str, int]:
        """Conta registos por tipo e fonte (só dos tipos que nos interessam)."""
        counts: Counter = Counter()
        for elem in self._records(path):
            t = elem.get("type")
            if t in (STEPS, HEART_RATE, SLEEP):
                counts[f"{t}  [fonte: {elem.get('sourceName', '?')}]"] += 1
        return dict(sorted(counts.items()))

    def convert_path(self, path: Path) -> ConversionResult:
        result = ConversionResult()
        # Sono: soma de minutos a dormir por (fonte, noite)
        sleep: dict[tuple[str, date], tuple[Decimal, datetime]] = {}
        sources: dict[str, set[str]] = defaultdict(set)

        for n, elem in enumerate(self._records(path), start=1):
            t = elem.get("type")
            if t not in (STEPS, HEART_RATE, SLEEP) or not self._accept_source(elem):
                continue
            source = elem.get("sourceName", "?")
            try:
                start = _parse_date(elem.get("startDate", ""))
                if t == SLEEP:
                    if elem.get("value") not in ASLEEP_VALUES:
                        continue
                    end = _parse_date(elem.get("endDate", ""))
                    minutes = Decimal((end - start).total_seconds()) / 60
                    # A "noite" é identificada pelo dia em que se acorda.
                    key = (source, end.date())
                    total, first = sleep.get(key, (Decimal(0), start))
                    sleep[key] = (total + minutes, min(first, start))
                    sources["sleep_duration_min"].add(source)
                    continue

                metric = "steps" if t == STEPS else "heart_rate"
                value = to_decimal(elem.get("value", ""))
                result.measurements.append(
                    Measurement(metric, value, start, CANONICAL_UNITS[metric])
                )
                sources[metric].add(source)
            except (ValueError, InvalidOperation) as exc:
                result.skipped.append(SkippedRow(f"registo {n} ({t})", str(exc)))

        for (_source, _night), (minutes, first_start) in sorted(sleep.items()):
            result.measurements.append(
                Measurement(
                    "sleep_duration_min",
                    minutes.quantize(Decimal(1)),
                    first_start,  # medição registada no início do sono
                    CANONICAL_UNITS["sleep_duration_min"],
                )
            )

        for metric, srcs in sorted(sources.items()):
            if len(srcs) > 1:
                result.notes.append(
                    f"{metric}: há várias fontes ({', '.join(sorted(srcs))}). "
                    "Os valores podem estar repetidos; usa --fonte para escolher uma."
                )
        return result
