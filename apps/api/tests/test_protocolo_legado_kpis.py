import pytest

from app.dashboards.protocolo_lexpre_legado import (
    _kwargs_handler_legado,
    acrescentar_kpis_do_legado,
    juntar_protocolados_por_mes,
    kpis_do_legado,
    misturar_legado_no_corpo,
    periodo_sem_protocolados_lexpre,
    pontos_mes_a_mes_do_legado,
)


def test_kwargs_handler_legado_zera_sistema():
    """Protocolo v1 tem `sistema=Query(...)`; sem override explícito a base zera."""

    def handler(
        from_date=None,
        to_date=None,
        materia=None,
        funcionario=None,
        sistema=None,
        uf_protocolo=None,
        area_atuacao_id=None,
    ):
        return None

    kwargs = _kwargs_handler_legado(
        handler,
        materia=["ANP"],
        funcionario=None,
        area=None,
        uf=["AM"],
        param_uf="uf_protocolo",
    )
    assert kwargs["sistema"] is None
    assert kwargs["materia"] == ["ANP"]
    assert kwargs["uf_protocolo"] == ["AM"]
    assert kwargs["funcionario"] is None
    assert "from_date" not in kwargs
    assert "to_date" not in kwargs


def test_periodo_sem_protocolados_lexpre():
    assert periodo_sem_protocolados_lexpre({"protocolados_total": {"total": 0}})
    assert not periodo_sem_protocolados_lexpre({"protocolados_total": {"total": 12}})


def test_kpis_do_legado_ng():
    out = kpis_do_legado(
        {
            "protocolos_resolvidos": 100,
            "comparativo_protocolos_resolvidos": 10.5,
            "valor_causa_protocolo_novo": 15000.0,
            "comparativo_valor_causa_protocolo": 1.5,
            "media_tempo_protocolado": 2.5,
            "mediana_tempo_protocolado": 1.25,
            "comparativo_tempo_medio_protocolos_resolvidos": 3.0,
            "protocolados_de_reajuizamento": 4,
        },
        la=False,
        stats_fila={"nao_protocolados": 99, "nao_protocolados_de_reajuizamento": 2},
    )
    assert out["protocolados_total"] == {"total": 100, "comparativo": 10.5}
    assert out["valor_causa_protocolado"]["total"] == 15000.0
    assert out["ticket_medio_protocolado"]["total"] == 150.0
    assert out["media_tempo_protocolado"] == 2.5
    assert out["represados"] == 99
    assert out["protocolados_de_reajuizamento"] == 4
    assert out["represados_de_reajuizamento"] == 2


def test_kpis_do_legado_la():
    out = kpis_do_legado(
        {
            "protocolos_resolvidos_LA": 70,
            "valor_causa_protocolado_LA": 9000.0,
            "ticket_medio_protocolos_resolvidos_LA": 128.5,
            "media_tempo_protocolo_LA": 1.1,
            "mediana_tempo_protocolo_LA": 0.8,
            "comparativo_protocolos_resolvidos_LA": 4.0,
        },
        la=True,
        stats_fila={"protocolos_represados_LA": 33},
    )
    assert out["protocolados_total"]["total"] == 70
    assert out["valor_causa_protocolado"]["total"] == 9000.0
    assert out["ticket_medio_protocolado"]["total"] == 128.5
    assert out["media_tempo_protocolado"] == 1.1
    assert out["represados"] == 33
    assert "protocolados_de_reajuizamento" not in out


def test_junta_mes_a_mes_legado_preenche_e_lexpre_prevalece():
    legado = [
        {"name": "jan 2024", "value": 100},
        {"name": "set 2024", "value": 50},
    ]
    lexpre = [
        {"name": "set 2024", "value": 371},
        {"name": "out 2024", "value": 493},
    ]
    assert juntar_protocolados_por_mes(lexpre, legado) == [
        {"name": "jan 2024", "value": 100},
        {"name": "set 2024", "value": 371},
        {"name": "out 2024", "value": 493},
    ]


def test_pontos_mes_a_mes_do_legado_ng_e_la():
    assert pontos_mes_a_mes_do_legado(
        {"protocolados_por_mes": [{"name": "mar 2023", "value": 12}]}, la=False
    ) == [{"name": "mar 2023", "value": 12}]
    assert pontos_mes_a_mes_do_legado(
        {"protocolados_por_mes_LA": [{"name": "abr 2023", "value": 7}]}, la=True
    ) == [{"name": "abr 2023", "value": 7}]


def test_acrescentar_kpis_soma_valor_e_volume():
    lexpre = {
        "protocolados_total": {"total": 100, "comparativo": 75.0},
        "valor_causa_protocolado": {"total": 1_000_000.0, "comparativo": 73.0},
        "ticket_medio_protocolado": {"total": 10_000.0, "comparativo": -1.0},
        "media_tempo_protocolado": 1.8,
        "mediana_tempo_protocolado": 0.84,
        "comparativo_tempo_medio_protocolado": -12.0,
        "represados": 50,
    }
    legado = {
        "protocolados_total": {"total": 200, "comparativo": -11.0},
        "valor_causa_protocolado": {"total": 4_000_000.0, "comparativo": -8.0},
        "ticket_medio_protocolado": {"total": 20_000.0, "comparativo": 2.0},
        "media_tempo_protocolado": 6.5,
        "mediana_tempo_protocolado": 2.0,
        "represados": 9,
        "protocolados_de_reajuizamento": 3,
    }
    out = acrescentar_kpis_do_legado(lexpre, legado)
    assert out["protocolados_total"]["total"] == 300
    assert out["valor_causa_protocolado"]["total"] == pytest.approx(5_000_000.0)
    assert out["ticket_medio_protocolado"]["total"] == pytest.approx(5_000_000.0 / 300)
    assert out["represados"] == 50
    assert out["protocolados_de_reajuizamento"] == 3


def test_misturar_misto_quando_ambos_tem_periodo():
    corpo = {
        "stats": {
            "protocolados_total": {"total": 10, "comparativo": 1.0},
            "valor_causa_protocolado": {"total": 1000.0, "comparativo": 0.0},
            "ticket_medio_protocolado": {"total": 100.0, "comparativo": 0.0},
            "media_tempo_protocolado": 2.0,
            "mediana_tempo_protocolado": 1.0,
            "represados": 3,
        },
        "protocolados_por_mes": [{"name": "jan 2026", "value": 10}],
    }
    legado = {
        "kpis": {
            "protocolados_total": {"total": 20, "comparativo": -1.0},
            "valor_causa_protocolado": {"total": 4000.0, "comparativo": 0.0},
            "ticket_medio_protocolado": {"total": 200.0, "comparativo": 0.0},
            "media_tempo_protocolado": 4.0,
            "mediana_tempo_protocolado": 3.0,
            "represados": 1,
        },
        "protocolados_por_mes": [{"name": "jan 2025", "value": 20}],
    }
    assert misturar_legado_no_corpo(corpo, legado) == "misto"
    assert corpo["stats"]["protocolados_total"]["total"] == 30
    assert corpo["stats"]["valor_causa_protocolado"]["total"] == 5000.0
    assert corpo["stats"]["represados"] == 3
