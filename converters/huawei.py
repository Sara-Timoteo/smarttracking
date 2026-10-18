"""Conversor para a exportação do Huawei Health.

Como exportar: Huawei Health -> Eu -> Centro de contas -> Centro de
privacidade -> "Pedir os seus dados" -> escolher Saúde. A Huawei envia uma
ligação para um zip; os dados de saúde vêm em JSON numa pasta do tipo
"Health detail data & description".

Estrutura conhecida (cada ficheiro é uma lista de registos):
    [
      {
        "type": 10006,
        "samplePoints": [
          {"key": "WEIGHT_BODYFAT_BROAD", "startTime": 1700000000000,
           "endTime": 1700000000000, "value": "{\"bodyWeight\": 79.4, ...}"}
        ]
      }
    ]
  - startTime/endTime em milissegundos desde 1970 (UTC);
  - value pode ser um número ou um texto com JSON lá dentro.

ESTADO: não encontrámos documentação pública que diga que "key" corresponde
a passos, frequência cardíaca ou sono. A própria exportação traz ficheiros
XLSX com a descrição dos campos. Por isso este conversor é CONFIGURÁVEL:
  1. corre-se `python convert.py --formato huawei --inspecionar <pasta>`
     para ver as chaves que existem;
  2. preenche-se mappings/huawei.json com as chaves certas;
  3. converte-se normalmente.

Exemplo de mapeamento:
    {
      "keys": {
        "steps":      {"key": "NOME_DA_CHAVE_DOS_PASSOS"},
        "heart_rate": {"key": "NOME_DA_CHAVE_DA_FC", "field": "bpm"},
        "sleep_duration_min": {"key": "NOME_DA_CHAVE_DO_SONO", "duration": true}
      }
    }
  - "field": se o value for JSON, qual o campo a ler;
  - "duration": true -> o valor é (endTime - startTime) em minutos;
  - "multiply": fator de conversão opcional (ex.: horas -> minutos = 60).

Minimização: só as chaves do mapeamento são lidas; o resto é ignorado.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from measurement import ALLOWED_METRIC_TYPES, Measurement

from ._files import iter_files
from .base import CANONICAL_UNITS, ConversionResult, SkippedRow, to_decimal
from .generic_csv import MappingError


@dataclass(frozen=True)
class KeyMapping:
    metric_type: str
    key: str
    field: str | None = None
    duration: bool = False
    multiply: Decimal = Decimal(1)


def load_mapping(path: str | Path) -> list[KeyMapping]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        keys = data["keys"]
    except json.JSONDecodeError as exc:
        raise MappingError(f"O mapeamento não é JSON válido: {exc}")
    except (KeyError, TypeError):
        raise MappingError('O mapeamento da Huawei precisa do campo "keys".')

    out = []
    for metric, spec in keys.items():
        if metric not in ALLOWED_METRIC_TYPES:
            raise MappingError(f"Métrica fora da lista branca: {metric!r}")
        if not spec.get("key"):
            raise MappingError(f'A métrica {metric!r} não indica "key".')
        out.append(
            KeyMapping(
                metric_type=metric,
                key=spec["key"],
                field=spec.get("field"),
                duration=bool(spec.get("duration", False)),
                multiply=Decimal(str(spec.get("multiply", 1))),
            )
        )
    return out


def _from_ms(ms) -> datetime:
    if not isinstance(ms, (int, float)) or isinstance(ms, bool):
        raise ValueError(f"tempo inválido: {ms!r}")
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _records(path: Path):
    for name, f in iter_files(path, "*.json"):
        try:
            blob = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue  # nem todos os JSON da exportação são de saúde
        records = blob if isinstance(blob, list) else [blob]
        for rec in records:
            if isinstance(rec, dict):
                yield Path(name).name, rec


class HuaweiHealthConverter:
    name = "huawei-health"

    def __init__(self, mapping: list[KeyMapping] | None = None):
        self.mapping = mapping or []

    def inspect(self, path: Path) -> dict[str, int]:
        """Conta os samplePoints por (type, key) — é isto que se põe no mapeamento."""
        counts: Counter = Counter()
        for _name, rec in _records(path):
            for sp in rec.get("samplePoints") or []:
                if isinstance(sp, dict):
                    counts[f"type={rec.get('type')}  key={sp.get('key')}"] += 1
        return dict(sorted(counts.items()))

    def _value(self, sp: dict, m: KeyMapping) -> Decimal:
        if m.duration:
            seconds = (sp["endTime"] - sp["startTime"]) / 1000
            return Decimal(str(seconds)) / 60
        raw = sp.get("value")
        if m.field:
            data = json.loads(raw) if isinstance(raw, str) else raw
            raw = data[m.field]
        return to_decimal(raw)

    def convert_path(self, path: Path) -> ConversionResult:
        if not self.mapping:
            raise MappingError(
                "Falta o mapeamento da Huawei (--mapping mappings/huawei.json). "
                "Usa --inspecionar para ver as chaves da tua exportação."
            )
        result = ConversionResult()
        by_key = {m.key: m for m in self.mapping}
        seen = Counter()

        for name, rec in _records(path):
            for i, sp in enumerate(rec.get("samplePoints") or [], start=1):
                if not isinstance(sp, dict) or sp.get("key") not in by_key:
                    continue
                m = by_key[sp["key"]]
                seen[m.key] += 1
                try:
                    value = self._value(sp, m) * m.multiply
                    if m.metric_type == "sleep_duration_min":
                        value = value.quantize(Decimal(1))
                    result.measurements.append(
                        Measurement(
                            m.metric_type,
                            value,
                            _from_ms(sp.get("startTime")),
                            CANONICAL_UNITS[m.metric_type],
                        )
                    )
                except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
                    result.skipped.append(
                        SkippedRow(f"{name}, ponto {i} ({m.key})", f"{type(exc).__name__}: {exc}")
                    )

        for m in self.mapping:
            if seen[m.key] == 0:
                result.notes.append(
                    f"A chave {m.key!r} ({m.metric_type}) não aparece nesta exportação. "
                    "Confirma com --inspecionar."
                )
        return result
