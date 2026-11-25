"""Pendências LexPre + legado: o que o legado da unidade soma nos cards, na origem e no mês a mês."""

from datetime import datetime

from app.dashboards import DASHBOARDS
from app.dashboards.pendencias_lexpre_legado import (
    kpis_do_legado,
    misturar_legado_no_corpo,
    somar_kpis,
    somar_por_mes,
    somar_por_origem,
)
from conftest import USER_ID


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def test_kpis_do_legado_ng_le_periodo_e_fila():
    periodo = {
        "pendencias_total": 1195,
        "pendencias_resolvidas": 1109,
        "pendencias_canceladas": 86,
        "pendencias_triagem": 0,
        "pendencias_taxa_resolvidos": 92.8,
        "media_tempo_resolvidos_pendencia": 739000.0,
        "pendencias_nao_resolvidas_reajuizamento": 156,
        "pendencias_resolvidas_reajuizamento": 36,
        "comparativo_pendencias_resolvidas": -9.4,
        "comparativo_tempo_medio_pendencias_resolvidas": 3.38,
        "pendencias_nao_resolvidas": 0,  # do período: não é o que o card mostra
    }
    hist = {"pendencias_nao_resolvidas": 3, "pendencias_nao_resolvidas_com_atraso": 3}
    k = kpis_do_legado(periodo, hist, la=False)
    assert k["pendencias_total"] == 1195
    assert k["pendencias_nao_resolvidas"] == 3  # fila de agora, do histórico
    assert k["pendencias_nao_resolvidas_com_atraso"] == 3
    assert k["pendencias_nao_resolvidas_reajuizamento"] == 156
    assert k["comparativo_tempo_medio_resolvidos_pendencia"] == 3.38


def test_kpis_do_legado_la_usa_sufixo_e_nao_tem_reajuizamento():
    k = kpis_do_legado(
        {"pendencias_total_LA": 10, "pendencias_resolvidas_LA": 8},
        {"pendencias_nao_resolvidas_LA": 2},
        la=True,
    )
    assert (k["pendencias_total"], k["pendencias_resolvidas"], k["pendencias_nao_resolvidas"]) == (10, 8, 2)
    assert "pendencias_resolvidas_reajuizamento" not in k
    assert "comparativo_pendencias_resolvidas" not in k


def test_somar_kpis_soma_contagens_e_pondera_taxas_e_tempos():
    lexpre = {
        "pendencias_total": 100,
        "pendencias_resolvidas": 50,
        "pendencias_nao_resolvidas": 11,
        "pendencias_taxa_resolvidos": 50.0,
        "media_tempo_resolvidos_pendencia": 10.0,
        "pendencias_resolvidas_reajuizamento": 0,
        "comparativo_pendencias_resolvidas": 74.73,
    }
    legado = {
        "pendencias_total": 300,
        "pendencias_resolvidas": 150,
        "pendencias_nao_resolvidas": 3,
        "pendencias_taxa_resolvidos": 90.0,
        "media_tempo_resolvidos_pendencia": 30.0,
        "pendencias_resolvidas_reajuizamento": 36,
        "comparativo_pendencias_resolvidas": -9.4,
    }
    s = somar_kpis(lexpre, legado)
    assert s["pendencias_total"] == 400
    assert s["pendencias_nao_resolvidas"] == 14
    assert s["pendencias_resolvidas_reajuizamento"] == 36
    assert s["pendencias_taxa_resolvidos"] == 80.0  # (50*100 + 90*300) / 400
    assert s["media_tempo_resolvidos_pendencia"] == 25.0  # (10*50 + 30*150) / 200
    assert s["comparativo_pendencias_resolvidas"] == 74.73  # comparativo fica do LexPre


def test_somar_kpis_sem_lexpre_no_periodo_usa_comparativo_do_legado():
    s = somar_kpis(
        {"pendencias_total": 0, "comparativo_pendencias_resolvidas": 0.0},
        {"pendencias_total": 5, "comparativo_pendencias_resolvidas": -9.4},
    )
    assert s["comparativo_pendencias_resolvidas"] == -9.4


def test_somar_por_mes_soma_mes_em_comum():
    lexpre = [{"name": "set 2026", "value": 276}, {"name": "nov 2026", "value": 217}]
    legado = [{"name": "dez 2025", "value": 130}, {"name": "set 2026", "value": 29}]
    assert somar_por_mes(lexpre, legado) == [
        {"name": "dez 2025", "value": 130},
        {"name": "set 2026", "value": 305},
        {"name": "nov 2026", "value": 217},
    ]


def test_somar_por_origem_maior_primeiro():
    assert somar_por_origem(
        [{"name": "Peticionamento", "value": 5}, {"name": "Organização de Documentos", "value": 6}],
        [{"name": "RETORNO COMERCIAL", "value": 3}, {"name": "Peticionamento", "value": 2}],
    ) == [
        {"name": "Peticionamento", "value": 7},
        {"name": "Organização de Documentos", "value": 6},
        {"name": "RETORNO COMERCIAL", "value": 3},
    ]


def test_misturar_sem_legado_nao_mexe():
    corpo = {"stats": {"pendencias_total": 4}, "pendencias_resolvidas_por_mes": []}
    vazio = {"kpis": {"pendencias_total": 0, "pendencias_nao_resolvidas": 0}, "por_origem": [], "por_mes": []}
    assert misturar_legado_no_corpo(corpo, vazio) == "lexpre"
    assert corpo["stats"] == {"pendencias_total": 4}


def test_misturar_so_legado():
    corpo = {"stats": {"pendencias_total": 0, "pendencias_nao_resolvidas": 0}}
    legado = {
        "kpis": {"pendencias_total": 7, "pendencias_nao_resolvidas": 1},
        "por_origem": [{"name": "X", "value": 1}],
        "por_mes": [{"name": "jan 2026", "value": 6}],
    }
    assert misturar_legado_no_corpo(corpo, legado) == "legado"
    assert corpo["stats"]["pendencias_total"] == 7
    assert corpo["pendencias_resolvidas_por_mes"] == [{"name": "jan 2026", "value": 6}]


# --- pela rota: o cálculo da v1 do legado de verdade, com linhas no banco ng ---

_LINHA = {"REAJUIZAMENTO": False, "UF": "AM", "ATENDENTE": "Ana", "FUNCIONARIO": "Ana"}


def test_pendencias_lexpre_soma_o_legado_da_unidade(client, signer, repo, sources):
    repo.grant(USER_ID, "NG", "pendencias-lexpre", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = "NG"
    for q in DASHBOARDS["pendencias-lexpre"].queries:
        sources.data[q] = []
    sources.data["setor_pendencias"] = [
        # período (novembro): 2 resolvidas
        {**_LINHA, "STATUS": "RESOLVIDO", "ENTRADA": datetime(2026, 11, 2, 9), "SAIDA": datetime(2026, 11, 3, 9)},
        {**_LINHA, "STATUS": "RESOLVIDO", "ENTRADA": datetime(2026, 11, 4, 9), "SAIDA": datetime(2026, 11, 6, 9)},
        # fora do período: só entra no mês a mês
        {**_LINHA, "STATUS": "RESOLVIDO", "ENTRADA": datetime(2025, 3, 1, 9), "SAIDA": datetime(2025, 3, 2, 9)},
        # em aberto desde antes do período: fila de agora e origem
        {**_LINHA, "STATUS": "PENDÊNCIA", "ORIGEM": "RETORNO COMERCIAL", "ENTRADA": datetime(2026, 1, 5, 9)},
    ]
    r = client.get(
        "/orgs/lexgroup/units/NG/dashboards/pendencias-lexpre?from=2026-11-01&to=2026-11-30",
        headers=auth(signer),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fonte_indicadores"] == "legado"
    assert body["stats"]["pendencias_resolvidas"] == 2
    assert body["stats"]["pendencias_nao_resolvidas"] == 1
    assert body["pendencias_nao_resolvidas_por_origem"] == [{"name": "RETORNO COMERCIAL", "value": 1}]
    assert sum(p["value"] for p in body["pendencias_resolvidas_por_mes"]) == 3


def test_pendencias_lexpre_sem_legado_ligado(client, signer, repo, sources):
    repo.grant(USER_ID, "NG", "pendencias-lexpre", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    for q in DASHBOARDS["pendencias-lexpre"].queries:
        sources.data[q] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/pendencias-lexpre", headers=auth(signer))
    assert r.status_code == 200, r.text
    assert r.json()["fonte_indicadores"] == "lexpre"


def test_pendencias_lexpre_filtro_de_uf_chega_no_legado(client, signer, repo, sources):
    """A casca manda `uf` como lista; a rota da v1 espera uma UF (texto)."""
    repo.grant(USER_ID, "NG", "pendencias-lexpre", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = "NG"
    for q in DASHBOARDS["pendencias-lexpre"].queries:
        sources.data[q] = []
    resolvida = {**_LINHA, "STATUS": "RESOLVIDO", "ENTRADA": datetime(2026, 11, 2, 9), "SAIDA": datetime(2026, 11, 3, 9)}
    sources.data["setor_pendencias"] = [resolvida, {**resolvida, "UF": "PA"}]
    r = client.get(
        "/orgs/lexgroup/units/NG/dashboards/pendencias-lexpre?from=2026-11-01&to=2026-11-30&uf=AM",
        headers=auth(signer),
    )
    assert r.status_code == 200, r.text
    assert r.json()["stats"]["pendencias_resolvidas"] == 1
