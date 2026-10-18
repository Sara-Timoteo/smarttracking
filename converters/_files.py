"""Ajuda a ler exportações que vêm como pasta ou como .zip.

As exportações das marcas raramente são um único ficheiro: a Samsung entrega
uma pasta com dezenas de CSVs, a Huawei um zip com JSONs, a Apple um zip com
um export.xml. Estas funções escondem essa diferença dos conversores.
"""
from __future__ import annotations

import fnmatch
import io
import zipfile
from pathlib import Path
from typing import IO, Iterator


def iter_files(path: Path, pattern: str) -> Iterator[tuple[str, IO[bytes]]]:
    """Percorre os ficheiros cujo nome bate com `pattern` (ex.: '*.json').

    `path` pode ser um ficheiro, uma pasta (percorrida recursivamente) ou um
    .zip. Devolve pares (nome, ficheiro aberto em modo binário).
    """
    if path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.is_file() and fnmatch.fnmatch(p.name, pattern):
                with open(p, "rb") as f:
                    yield str(p.relative_to(path)), f
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for info in sorted(z.infolist(), key=lambda i: i.filename):
                name = Path(info.filename).name
                if info.is_dir() or not fnmatch.fnmatch(name, pattern):
                    continue
                if info.flag_bits & 0x1:
                    raise ValueError(
                        f"O zip está protegido por password ({info.filename}). "
                        "Descompacta-o primeiro e indica a pasta."
                    )
                with z.open(info) as f:
                    yield info.filename, f
    elif path.is_file():
        if fnmatch.fnmatch(path.name, pattern):
            with open(path, "rb") as f:
                yield path.name, f
    else:
        raise FileNotFoundError(f"Não encontro: {path}")


def as_text(f: IO[bytes]) -> io.TextIOWrapper:
    """Abre um ficheiro binário como texto UTF-8 (tolera o BOM do Excel)."""
    return io.TextIOWrapper(f, encoding="utf-8-sig", newline="")
