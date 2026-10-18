"""Testes dos conversores (correr com: python -m pytest tests)."""
import io
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from converters import (  # noqa: E402
    CsvMapping,
    GenericCsvConverter,
    MappingError,
    write_canonical_csv,
)
from parser_csv import parse_csv  # noqa: E402

MAPPING = ROOT / "mappings" / "exemplo-relogio.json"
EXPORT = ROOT / "exemplos" / "exportacao-exemplo.csv"


def convert_example():
    converter = GenericCsvConverter(CsvMapping.load(MAPPING))
    with open(EXPORT, encoding="utf-8-sig", newline="") as f:
        return converter.convert(f)


def test_converte_valores_e_unidades():
    result = convert_example()
    got = {(m.metric_type, m.measured_at.isoformat()): (m.metric_value, m.unit)
           for m in result.measurements}

    # "1.234" com ponto de milhares -> 1234 passos
    assert got[("steps", "2026-07-20T08:30:00+01:00")] == (Decimal("1234"), "steps")
    # vírgula decimal
    assert got[("heart_rate", "2026-07-20T23:00:00+01:00")] == (Decimal("61.5"), "bpm")
    # 7,5 horas -> 450 minutos (multiply: 60)
    assert got[("sleep_duration_min", "2026-07-20T23:00:00+01:00")] == (Decimal("450.0"), "min")


def test_aplica_fuso_horario_com_hora_de_inverno():
    data = "Data;Passos\n15/01/2026 10:00;100\n"
    mapping = CsvMapping.from_dict({
        "delimiter": ";",
        "timestamp": {"column": "Data", "format": "%d/%m/%Y %H:%M",
                      "timezone": "Europe/Lisbon"},
        "metrics": {"steps": {"column": "Passos"}},
    })
    result = GenericCsvConverter(mapping).convert(io.StringIO(data))
    # Em janeiro, Lisboa está em UTC+00:00
    assert result.measurements[0].measured_at.isoformat() == "2026-01-15T10:00:00+00:00"


def test_celulas_vazias_nao_sao_erro_e_valores_maus_sao_reportados():
    result = convert_example()
    locations = [s.location for s in result.skipped]
    assert "linha 4, coluna 'FC média'" in locations   # "abc"
    assert "linha 5" in locations                       # data 32/07
    assert len(result.skipped) == 2
    # linha 2: passos + FC; linha 3: FC + sono; linha 4: passos (FC "abc" falha)
    assert len(result.measurements) == 5


def test_descarta_colunas_fora_do_mapeamento():
    """Minimização: latitude, longitude e notas nunca chegam ao CSV canónico."""
    result = convert_example()
    out = io.StringIO()
    write_canonical_csv(result.measurements, out)
    text = out.getvalue()
    for proibido in ("38.9551", "38,9551", "-8,9894", "treino"):
        assert proibido not in text


def test_saida_e_aceite_pelo_parser_do_import():
    """O CSV produzido entra no POST /import sem rejeições."""
    result = convert_example()
    out = io.StringIO()
    write_canonical_csv(result.measurements, out)
    parsed = parse_csv(io.StringIO(out.getvalue()))
    assert parsed.rejected == []
    assert len(parsed.measurements) == len(result.measurements)


def test_recusa_metrica_fora_da_lista_branca():
    with pytest.raises(MappingError, match="lista branca"):
        CsvMapping.from_dict({
            "timestamp": {"column": "Data"},
            "metrics": {"gps_location": {"column": "Lat"}},
        })


def test_avisa_quando_falta_coluna_na_exportacao():
    mapping = CsvMapping.load(MAPPING)
    with pytest.raises(MappingError, match="Colunas em falta"):
        GenericCsvConverter(mapping).convert(io.StringIO("Data;Passos\n"))


def test_data_sem_fuso_e_sem_timezone_no_mapeamento_e_rejeitada():
    mapping = CsvMapping.from_dict({
        "timestamp": {"column": "Data"},
        "metrics": {"steps": {"column": "Passos"}},
    })
    result = GenericCsvConverter(mapping).convert(
        io.StringIO("Data,Passos\n2026-07-20T08:30:00,10\n")
    )
    assert result.measurements == []
    assert "sem fuso horário" in result.skipped[0].reason
