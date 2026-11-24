from app.dashboards.org_documentos_lexpre_legado import (
    juntar_resolvidos_por_mes,
    kpis_do_legado,
    periodo_sem_resolvidos_lexpre,
    pontos_mes_a_mes_do_legado,
)


def test_periodo_sem_resolvidos_lexpre():
    assert periodo_sem_resolvidos_lexpre({"resolvidos_total": {"total": 0}})
    assert not periodo_sem_resolvidos_lexpre({"resolvidos_total": {"total": 12}})


def test_kpis_do_legado_ng():
    out = kpis_do_legado(
        {
            "resolvidos_total": 100,
            "comparativo_resolvidos_total": 10.5,
            "organizados_manualmente": 40,
            "comparativo_organizados_manualmente": -2.0,
            "organizados_e_peticionados_automaticamente": 60,
            "comparativo_organizados_e_peticionados_automaticamente": 5.0,
            "cancelados": 8,
            "comparativo_cancelados": -1.0,
            "media_tempo_resolvidos": 2.5,
            "mediana_tempo_resolvidos": 1.25,
            "comparativo_tempo_medio_resolvidos_org_doc": 3.0,
            "nao_organizados": 99,
            "retorno_pendencia": 50,
        },
        la=False,
    )
    assert out["resolvidos_total"] == {"total": 100, "comparativo": 10.5}
    assert out["organizados_manualmente"]["total"] == 40
    assert out["organizados_e_peticionados_automaticamente"]["total"] == 60
    assert out["cancelados"] == {"total": 8, "comparativo": -1.0}
    assert out["media_tempo_resolvidos"] == 2.5
    assert out["mediana_tempo_resolvidos"] == 1.25
    assert out["comparativo_tempo_medio_resolvidos"] == 3.0
    assert "represados" not in out
    assert "devolvido_pendencia" not in out


def test_kpis_do_legado_la():
    out = kpis_do_legado(
        {
            "total_organizados_LA": 70,
            "total_organizados_manualmente_LA": 20,
            "total_organizados_automaticamente_LA": 50,
            "cancelados_LA": 3,
            "media_tempo_resolvidos_LA": 1.1,
            "mediana_tempo_resolvidos_LA": 0.8,
        },
        la=True,
    )
    assert out["resolvidos_total"]["total"] == 70
    assert out["organizados_manualmente"]["total"] == 20
    assert out["organizados_e_peticionados_automaticamente"]["total"] == 50
    assert out["cancelados"]["total"] == 3
    assert out["media_tempo_resolvidos"] == 1.1
    assert out["mediana_tempo_resolvidos"] == 0.8


def test_junta_mes_a_mes_legado_preenche_e_lexpre_prevalece():
    legado = [
        {"name": "jan 2024", "value": 100},
        {"name": "set 2024", "value": 50},
    ]
    lexpre = [
        {"name": "set 2024", "value": 371},
        {"name": "out 2024", "value": 493},
    ]
    assert juntar_resolvidos_por_mes(lexpre, legado) == [
        {"name": "jan 2024", "value": 100},
        {"name": "set 2024", "value": 371},
        {"name": "out 2024", "value": 493},
    ]


def test_pontos_mes_a_mes_do_legado_ng_e_la():
    assert pontos_mes_a_mes_do_legado(
        {"resolvidos_total_por_mes": [{"name": "mar 2023", "value": 12}]}, la=False
    ) == [{"name": "mar 2023", "value": 12}]
    assert pontos_mes_a_mes_do_legado(
        {"resolvidos_total_por_mes_LA": [{"name": "abr 2023", "value": 7}]}, la=True
    ) == [{"name": "abr 2023", "value": 7}]
