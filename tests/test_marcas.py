"""Testes dos conversores por marca (Apple, Samsung, Huawei).

Usam os ficheiros fictícios em exemplos/, construídos a partir da estrutura
documentada de cada exportação. Correr com: python -m pytest tests
"""
import io
import shutil
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from converters import (  # noqa: E402
    AppleHealthConverter,
    HuaweiHealthConverter,
    MappingError,
    SamsungHealthConverter,
    write_canonical_csv,
)
from converters.huawei import load_mapping  # noqa: E402
from parser_csv import parse_csv  # noqa: E402

EX = ROOT / "exemplos"


def as_dict(result):
    return {(m.metric_type, m.measured_at.isoformat()): m.metric_value
            for m in result.measurements}


def canonical_text(result):
    out = io.StringIO()
    write_canonical_csv(result.measurements, out)
    return out.getvalue()


def assert_import_aceita(result):
    parsed = parse_csv(io.StringIO(canonical_text(result)))
    assert parsed.rejected == []
    assert len(parsed.measurements) == len(result.measurements)


# --- Apple -------------------------------------------------------------------

def test_apple_converte_e_soma_sono_sem_contar_cama_nem_acordado():
    result = AppleHealthConverter(source_filter="Watch").convert_path(EX / "apple")
    got = as_dict(result)
    assert got[("steps", "2026-07-20T08:30:00+01:00")] == Decimal("1210")
    assert got[("heart_rate", "2026-07-20T08:31:00+01:00")] == Decimal("72")
    # 3 h (Core) + 4 h (Deep) = 420 min; "InBed" e "Awake" não contam
    assert got[("sleep_duration_min", "2026-07-20T23:00:00+01:00")] == Decimal("420")
    assert_import_aceita(result)


def test_apple_avisa_quando_ha_varias_fontes():
    result = AppleHealthConverter().convert_path(EX / "apple")
    assert any("várias fontes" in n for n in result.notes)


def test_apple_ignora_peso_e_rotas_de_treino():
    result = AppleHealthConverter().convert_path(EX / "apple")
    assert {m.metric_type for m in result.measurements} <= {
        "steps", "heart_rate", "sleep_duration_min"}
    assert Decimal("70") not in {m.metric_value for m in result.measurements}  # peso
    text = canonical_text(result)
    assert "gpx" not in text and "route" not in text


def test_apple_aceita_o_export_zip(tmp_path):
    pasta = tmp_path / "apple_health_export"
    pasta.mkdir()
    shutil.copy(EX / "apple" / "export.xml", pasta / "export.xml")
    zip_path = shutil.make_archive(str(tmp_path / "export"), "zip", tmp_path, "apple_health_export")
    result = AppleHealthConverter(source_filter="Watch").convert_path(Path(zip_path))
    assert len(result.measurements) == 3


# --- Samsung -----------------------------------------------------------------

def test_samsung_aplica_time_offset_e_calcula_sono():
    result = SamsungHealthConverter().convert_path(EX / "samsung")
    got = as_dict(result)
    # 07:30 UTC com UTC+0100 -> 08:30 hora local
    assert got[("steps", "2026-07-20T08:30:00+01:00")] == Decimal("1234")
    assert got[("heart_rate", "2026-07-20T08:31:00+01:00")] == Decimal("72")
    # 22:00 -> 05:30 = 7 h 30 = 450 min
    assert got[("sleep_duration_min", "2026-07-20T23:00:00+01:00")] == Decimal("450")
    assert_import_aceita(result)


def test_samsung_reporta_valor_mau_com_ficheiro_e_linha():
    result = SamsungHealthConverter().convert_path(EX / "samsung")
    assert len(result.skipped) == 1
    assert "heart_rate" in result.skipped[0].location
    assert "linha 4" in result.skipped[0].location


def test_samsung_nao_abre_ficheiros_de_exercicio_com_localizacao():
    text = canonical_text(SamsungHealthConverter().convert_path(EX / "samsung"))
    assert "38.9551" not in text and "-8.9894" not in text


# --- Huawei ------------------------------------------------------------------

def test_huawei_com_mapeamento_converte_numero_json_e_duracao():
    conv = HuaweiHealthConverter(load_mapping(ROOT / "mappings" / "huawei-exemplo.json"))
    result = conv.convert_path(EX / "huawei")
    got = as_dict(result)
    assert got[("steps", "2026-07-20T07:30:00+00:00")] == Decimal("1234")
    assert got[("heart_rate", "2026-07-20T07:31:00+00:00")] == Decimal("72")  # campo "bpm" do JSON
    assert got[("sleep_duration_min", "2026-07-20T22:00:00+00:00")] == Decimal("450")
    assert_import_aceita(result)


def test_huawei_ignora_chaves_fora_do_mapeamento():
    conv = HuaweiHealthConverter(load_mapping(ROOT / "mappings" / "huawei-exemplo.json"))
    text = canonical_text(conv.convert_path(EX / "huawei"))
    assert "38.9551" not in text


def test_huawei_inspecionar_lista_as_chaves():
    keys = HuaweiHealthConverter().inspect(EX / "huawei")
    assert "type=900  key=EXEMPLO_PASSOS" in keys


def test_huawei_modelo_por_preencher_avisa_e_nao_inventa():
    conv = HuaweiHealthConverter(load_mapping(ROOT / "mappings" / "huawei.json"))
    result = conv.convert_path(EX / "huawei")
    assert result.measurements == []
    assert len(result.notes) == 3


def test_huawei_sem_mapeamento_da_erro_claro():
    with pytest.raises(MappingError, match="--inspecionar"):
        HuaweiHealthConverter().convert_path(EX / "huawei")
