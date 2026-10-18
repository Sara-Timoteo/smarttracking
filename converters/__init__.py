"""Conversores: exportações de wearables -> medições canónicas.

Formatos disponíveis:
    csv      -> qualquer relógio/app que exporte CSV (configurado em mappings/)
    apple    -> Apple Health (export.zip / export.xml)
    samsung  -> Samsung Health ("Transferir dados pessoais")
    huawei   -> Huawei Health (Centro de privacidade; configurado em mappings/)

Para acrescentar uma marca nova:
  - se exporta CSV, basta um ficheiro de mapeamento em mappings/ (sem código);
  - se usa outro formato, cria-se um módulo aqui com uma classe que tenha
    `name`, `convert_path(path)` e `inspect(path)` (ver base.py).
"""
from .apple import AppleHealthConverter
from .base import (
    CANONICAL_UNITS,
    ConversionResult,
    Converter,
    SkippedRow,
    write_canonical_csv,
)
from .generic_csv import CsvMapping, GenericCsvConverter, MappingError
from .huawei import HuaweiHealthConverter
from .samsung import SamsungHealthConverter

FORMATS = ("csv", "apple", "samsung", "huawei")

__all__ = [
    "AppleHealthConverter",
    "CANONICAL_UNITS",
    "ConversionResult",
    "Converter",
    "CsvMapping",
    "FORMATS",
    "GenericCsvConverter",
    "HuaweiHealthConverter",
    "MappingError",
    "SamsungHealthConverter",
    "SkippedRow",
    "write_canonical_csv",
]
