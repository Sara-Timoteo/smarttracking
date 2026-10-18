"""Conversores: exportações de wearables -> medições canónicas.

Para acrescentar uma marca nova:
  - se exporta CSV, basta um ficheiro de mapeamento em mappings/ (sem código);
  - se usa outro formato (XML, JSON...), cria-se um módulo aqui com uma classe
    que tenha `name` e `convert(stream) -> ConversionResult` (ver base.py).
"""
from .base import ConversionResult, Converter, SkippedRow, write_canonical_csv
from .generic_csv import CsvMapping, GenericCsvConverter, MappingError

__all__ = [
    "ConversionResult",
    "Converter",
    "CsvMapping",
    "GenericCsvConverter",
    "MappingError",
    "SkippedRow",
    "write_canonical_csv",
]
