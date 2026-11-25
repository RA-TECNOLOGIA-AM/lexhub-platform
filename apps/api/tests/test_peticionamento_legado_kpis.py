import pytest

from app.dashboards.peticionamento_lexpre_legado import (
    acrescentar_kpis_do_legado,
    juntar_peticionados_por_mes,
    kpis_do_legado,
    misturar_legado_no_corpo,
    periodo_sem_peticionados_lexpre,
    pontos_mes_a_mes_do_legado,
)


def test_periodo_sem_peticionados_lexpre():
    assert periodo_sem_peticionados_lexpre({"total_peticionados": {"total": 0}})
    assert not periodo_sem_peticionados_lexpre({"total_peticionados": {"total": 12}})


def test_kpis_do_legado_ng():
    out = kpis_do_legado(
        {
            "total_peticionados": 100,
            "comparativo_peticionados": 10.5,
            "peticionados_manualmente": 40,
            "comparativo_peticionados_manualmente": -2.0,
            "peticionados_automaticamente": 60,
            "comparativo_peticionados_automaticamente": 5.0,
            "valor_causa_confeccionado": 15000.0,
            "comparativo_valor_causa_confeccionado": 1.5,
            "ticket_medio_confeccionado": 150.0,
            "comparativo_ticket_medio_confeccionado": -0.5,
            "media_tempo_peticionado": 2.5,
            "mediana_tempo_peticionado": 1.25,
            "comparativo_tempo_medio_peticionado": 3.0,
            "comparativo_mediana_tempo_pet": 1.0,
        },
        la=False,
        stats_fila={"nao_peticionados": 99, "processos_em_revisao": 12},
    )
    assert out["total_peticionados"] == {"total": 100, "comparativo": 10.5}
    assert out["peticionados_manualmente"]["total"] == 40
    assert out["peticionados_automaticamente"]["total"] == 60
    assert out["valor_causa_confeccionado"]["total"] == 15000.0
    assert out["ticket_medio_confeccionado"]["total"] == 150.0
    assert out["media_tempo_peticionado"] == 2.5
    assert out["comparativo_mediana_tempo_peticionado"] == 1.0
    assert out["represados"] == 99
    assert out["processos_em_revisao"] == 12
    assert "cancelados" not in out


def test_kpis_do_legado_la():
    out = kpis_do_legado(
        {
            "total_confeccionados_LA": 70,
            "confeccionados_manualmente_LA": 20,
            "confeccionados_automaticamente_LA": 50,
            "valor_causa_confeccionado_LA": 9000.0,
            "ticket_medio_confeccionado_LA": 128.5,
            "tempo_medio_confeccao_LA": 1.1,
            "mediana_tempo_confeccao_LA": 0.8,
            "comparativo_confeccionados_LA": 4.0,
            "comparativo_tempo_medio_confeccionado_LA": -1.0,
        },
        la=True,
        stats_fila={"nao_confeccionados_LA": 33},
    )
    assert out["total_peticionados"]["total"] == 70
    assert out["peticionados_manualmente"]["total"] == 20
    assert out["peticionados_automaticamente"]["total"] == 50
    assert out["valor_causa_confeccionado"]["total"] == 9000.0
    assert out["media_tempo_peticionado"] == 1.1
    assert out["comparativo_tempo_medio_peticionado"] == -1.0
    assert out["represados"] == 33
    assert "processos_em_revisao" not in out


def test_junta_mes_a_mes_legado_preenche_e_lexpre_prevalece():
    legado = [
        {"name": "jan 2024", "value": 100},
        {"name": "set 2024", "value": 50},
    ]
    lexpre = [
        {"name": "set 2024", "value": 371},
        {"name": "out 2024", "value": 493},
    ]
    assert juntar_peticionados_por_mes(lexpre, legado) == [
        {"name": "jan 2024", "value": 100},
        {"name": "set 2024", "value": 371},
        {"name": "out 2024", "value": 493},
    ]


def test_pontos_mes_a_mes_do_legado_ng_e_la():
    assert pontos_mes_a_mes_do_legado(
        {"peticionados_por_mes": [{"name": "mar 2023", "value": 12}]}, la=False
    ) == [{"name": "mar 2023", "value": 12}]
    assert pontos_mes_a_mes_do_legado(
        {"confeccionados_por_mes_LA": [{"name": "abr 2023", "value": 7}]}, la=True
    ) == [{"name": "abr 2023", "value": 7}]


def test_acrescentar_kpis_soma_valor_e_volume():
    lexpre = {
        "total_peticionados": {"total": 1113, "comparativo": 75.0},
        "peticionados_manualmente": {"total": 257, "comparativo": 50.0},
        "peticionados_automaticamente": {"total": 856, "comparativo": 80.0},
        "valor_causa_confeccionado": {"total": 22_075_847.09, "comparativo": 73.0},
        "ticket_medio_confeccionado": {"total": 19_834.54, "comparativo": -1.0},
        "media_tempo_peticionado": 1.8,
        "mediana_tempo_peticionado": 0.84,
        "comparativo_tempo_medio_peticionado": -12.0,
        "represados": 50,
        "cancelados": {"total": 100, "comparativo": 66.0},
    }
    legado = {
        "total_peticionados": {"total": 7056, "comparativo": -11.0},
        "peticionados_manualmente": {"total": 3199, "comparativo": -22.0},
        "peticionados_automaticamente": {"total": 3857, "comparativo": 0.0},
        "valor_causa_confeccionado": {"total": 197_380_763.73, "comparativo": -8.0},
        "ticket_medio_confeccionado": {"total": 27_973.46, "comparativo": 2.0},
        "media_tempo_peticionado": 6.5,
        "mediana_tempo_peticionado": 2.0,
        "represados": 9,
    }
    out = acrescentar_kpis_do_legado(lexpre, legado)
    assert out["total_peticionados"]["total"] == 8169
    assert out["valor_causa_confeccionado"]["total"] == pytest.approx(
        22_075_847.09 + 197_380_763.73
    )
    assert out["represados"] == 50  # fila atual do LexPre
    assert out["cancelados"]["total"] == 100
    assert out["ticket_medio_confeccionado"]["total"] == pytest.approx(
        (22_075_847.09 + 197_380_763.73) / 8169
    )


def test_misturar_misto_quando_ambos_tem_periodo():
    corpo = {
        "stats": {
            "total_peticionados": {"total": 10, "comparativo": 1.0},
            "peticionados_manualmente": {"total": 4, "comparativo": 0.0},
            "peticionados_automaticamente": {"total": 6, "comparativo": 0.0},
            "valor_causa_confeccionado": {"total": 1000.0, "comparativo": 0.0},
            "ticket_medio_confeccionado": {"total": 100.0, "comparativo": 0.0},
            "media_tempo_peticionado": 2.0,
            "mediana_tempo_peticionado": 1.0,
            "represados": 3,
        },
        "peticionados_por_mes": [{"name": "jan 2026", "value": 10}],
    }
    legado = {
        "kpis": {
            "total_peticionados": {"total": 20, "comparativo": -1.0},
            "peticionados_manualmente": {"total": 8, "comparativo": 0.0},
            "peticionados_automaticamente": {"total": 12, "comparativo": 0.0},
            "valor_causa_confeccionado": {"total": 4000.0, "comparativo": 0.0},
            "ticket_medio_confeccionado": {"total": 200.0, "comparativo": 0.0},
            "media_tempo_peticionado": 4.0,
            "mediana_tempo_peticionado": 3.0,
            "represados": 1,
        },
        "peticionados_por_mes": [{"name": "jan 2025", "value": 20}],
    }
    assert misturar_legado_no_corpo(corpo, legado) == "misto"
    assert corpo["stats"]["total_peticionados"]["total"] == 30
    assert corpo["stats"]["valor_causa_confeccionado"]["total"] == 5000.0
    assert corpo["stats"]["represados"] == 3
