"""Converte uma exportação de wearable para o CSV canónico do SmartTracking.

Corre no PC do utilizador, sem internet: a exportação em bruto nunca sai do
dispositivo. Só as métricas da lista branca passam para o ficheiro final,
que depois se envia pelo POST /import.

Exemplos:
    # CSV de qualquer relógio, com mapeamento
    python convert.py --formato csv --mapping mappings/exemplo-relogio.json exportacao.csv

    # Apple Health (aceita o export.zip diretamente); só dados do relógio
    python convert.py --formato apple --fonte Watch export.zip

    # Samsung Health (pasta ou zip da exportação)
    python convert.py --formato samsung samsunghealth_xxx

    # Huawei: primeiro ver as chaves, depois converter com o mapeamento
    python convert.py --formato huawei --inspecionar pasta_huawei
    python convert.py --formato huawei --mapping mappings/huawei.json pasta_huawei
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from converters import (
    FORMATS,
    AppleHealthConverter,
    CsvMapping,
    GenericCsvConverter,
    HuaweiHealthConverter,
    MappingError,
    SamsungHealthConverter,
    write_canonical_csv,
)
from converters.huawei import load_mapping as load_huawei_mapping


def build_converter(args):
    if args.formato == "csv":
        if not args.mapping:
            raise MappingError("O formato csv precisa de --mapping.")
        return GenericCsvConverter(CsvMapping.load(args.mapping))
    if args.formato == "apple":
        return AppleHealthConverter(source_filter=args.fonte)
    if args.formato == "samsung":
        return SamsungHealthConverter()
    if args.formato == "huawei":
        mapping = load_huawei_mapping(args.mapping) if args.mapping else None
        return HuaweiHealthConverter(mapping)
    raise MappingError(f"Formato desconhecido: {args.formato}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Converte uma exportação de wearable para o CSV canónico."
    )
    parser.add_argument("export", help="ficheiro, pasta ou .zip exportado pelo relógio/app")
    parser.add_argument("--formato", choices=FORMATS, default="csv",
                        help="marca/formato da exportação (por omissão: csv)")
    parser.add_argument("--mapping", help="ficheiro JSON de mapeamento (csv e huawei)")
    parser.add_argument("--fonte", help="apple: só registos desta fonte (ex.: Watch)")
    parser.add_argument("--inspecionar", action="store_true",
                        help="mostra o que existe na exportação, sem converter")
    parser.add_argument("-o", "--output",
                        help="ficheiro de saída (por omissão: <export>_canonico.csv)")
    args = parser.parse_args(argv)

    export_path = Path(args.export)
    try:
        converter = build_converter(args)
        if args.inspecionar:
            counts = converter.inspect(export_path)
            print(f"Conversor: {converter.name} — conteúdo de {export_path}")
            if not counts:
                print("  (nada encontrado)")
            for what, n in counts.items():
                print(f"  {n:>8}  {what}")
            return 0
        result = converter.convert_path(export_path)
    except (MappingError, OSError, ValueError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.output) if args.output else export_path.with_name(
        export_path.stem + "_canonico.csv"
    )
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        write_canonical_csv(result.measurements, f)

    print(f"Conversor: {converter.name}")
    print(f"Medições convertidas: {len(result.measurements)}")
    print(f"Ignoradas por erro:   {len(result.skipped)}")
    for s in result.skipped[:20]:
        print(f"  - {s.location}: {s.reason}")
    if len(result.skipped) > 20:
        print(f"  ... e mais {len(result.skipped) - 20}")
    for note in result.notes:
        print(f"AVISO: {note}")
    print(f"Ficheiro criado: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
