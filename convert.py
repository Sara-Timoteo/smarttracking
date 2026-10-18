"""Converte uma exportação de wearable para o CSV canónico do SmartTracking.

Corre no PC do utilizador, sem internet: a exportação em bruto nunca sai do
dispositivo. Só as métricas da lista branca passam para o ficheiro final,
que depois se envia pelo POST /import.

Uso:
    python convert.py --mapping mappings/exemplo-relogio.json exportacao.csv
    python convert.py --mapping mappings/exemplo-relogio.json exportacao.csv -o canonico.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from converters import CsvMapping, GenericCsvConverter, MappingError, write_canonical_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converte uma exportação de wearable para o CSV canónico."
    )
    parser.add_argument("export", help="ficheiro exportado pelo relógio/app")
    parser.add_argument(
        "--mapping", required=True, help="ficheiro JSON de mapeamento (pasta mappings/)"
    )
    parser.add_argument(
        "-o", "--output", help="ficheiro de saída (por omissão: <export>_canonico.csv)"
    )
    args = parser.parse_args(argv)

    export_path = Path(args.export)
    out_path = Path(args.output) if args.output else export_path.with_name(
        export_path.stem + "_canonico.csv"
    )

    try:
        converter = GenericCsvConverter(CsvMapping.load(args.mapping))
        # utf-8-sig tolera o BOM que o Excel costuma pôr no início do ficheiro.
        with open(export_path, encoding="utf-8-sig", newline="") as f:
            result = converter.convert(f)
    except (MappingError, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        write_canonical_csv(result.measurements, f)

    print(f"Conversor: {converter.name}")
    print(f"Medições convertidas: {len(result.measurements)}")
    print(f"Ignoradas por erro:   {len(result.skipped)}")
    for s in result.skipped:
        print(f"  - {s.location}: {s.reason}")
    print(f"Ficheiro criado: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
