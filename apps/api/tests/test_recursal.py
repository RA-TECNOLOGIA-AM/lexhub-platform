"""Recursal: as chamadas da página da v1 numa resposta só (cada gráfico sem o filtro da própria dimensão), os nomes
da NG para todas as unidades e os Extintos do controle de processo (NG/LA) ou do próprio Recursal (RJ)."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import recursal as m
from app.dashboards.base import DashboardContext, DashboardInputError, NotReady, Period


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters=filters,
        can_see_commission=True,
    )


def _falsos(monkeypatch, u, resposta=lambda nome: {"stats": {}}):
    chamadas = []

    def falso(nome):
        async def handler(from_date=None, to_date=None, **kw):
            chamadas.append((nome, from_date, to_date, kw))
            return SimpleNamespace(model_dump=lambda: resposta(nome))

        return handler

    monkeypatch.setattr(m.generico_v1, "_parametros", lambda h: {})
    monkeypatch.setitem(v1.HANDLERS, f"recursal_{u}", falso("principal"))
    if u != "RJ":
        monkeypatch.setitem(v1.HANDLERS, f"controle_processo_{u}", falso("controle"))
    for s in (
        "por_subfase",
        "por_materia",
        "por_competencia",
        "por_vara",
        "decisoes",
        "status_1g",
        "status_2g",
        "ranking_juizes",
        "ranking_relatores",
    ):
        monkeypatch.setattr(v1, f"get_recursal_{u}_{s}", falso(s))

    async def opcoes():
        return {"status_1g": [{"id": 19, "label": "IMPROCEDENTE"}], "fases": ["RECURSAL"]}

    monkeypatch.setattr(v1, f"get_recursal_{u}_filtros_opcoes", opcoes)

    async def comissao(ctx):
        return {"linhas": [], "unidade": ctx.unit_ref}

    monkeypatch.setattr(m.recursal_export, "comissao", comissao)
    return chamadas


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("SP")))


def test_ids_de_status_precisam_ser_numeros():
    with pytest.raises(DashboardInputError):
        asyncio.run(m.build(_ctx(id_1g_recursal=["x"])))


def test_cada_grafico_sem_o_filtro_da_propria_dimensao(monkeypatch):
    chamadas = _falsos(monkeypatch, "NG")
    body = asyncio.run(
        m.build(
            _ctx(
                juiz_recursal=["Ana"],
                subfase_recursal=["AG. JULGAMENTO"],
                id_1g_recursal=["19"],
                funcionario_recursos=["Bia"],
            )
        )
    )
    por = {}
    for nome, de, ate, kw in chamadas:
        por.setdefault(nome, []).append((de, ate, kw))
    # principal: período (com filtros), histórico (com filtros) e a produção (sem filtro nenhum)
    (p_de, _, p_kw), (h_de, _, h_kw), (_, _, prod_kw) = por["principal"]
    assert p_de == date(2026, 11, 1) and h_de is None and h_kw["juiz"] == ["Ana"]
    assert (
        p_kw["juiz"] == ["Ana"]
        and p_kw["id_1g"] == [19]
        and p_kw["funcionario_recursos"] == ["Bia"]
    )
    assert prod_kw == {}
    # subfase: estoque (sem data) e entrada (período), sem o filtro de subfase, com os outros
    (e_de, _, e_kw), (n_de, _, n_kw) = por["por_subfase"]
    assert e_de is None and e_kw["base"] == "estoque" and e_kw["subfase"] is None
    assert n_de == date(2026, 11, 1) and n_kw["base"] == "entrada" and n_kw["juiz"] == ["Ana"]
    assert por["ranking_juizes"][0][2]["juiz"] is None
    assert por["status_1g"][0][2]["id_1g"] is None and por["status_2g"][0][2]["id_1g"] == [19]
    # Extintos: do controle de processo, sem os filtros da página
    assert por["controle"][0][2] == {}
    # opções: só as listas que a página usa
    assert body["opcoes"]["status_1g"] == [{"id": 19, "label": "IMPROCEDENTE"}]
    assert "fases" not in body["opcoes"]


def test_rj_le_os_nomes_do_rj_e_os_extintos_do_proprio_recursal(monkeypatch):
    def resposta(nome):
        if nome == "principal":
            return {
                "stats": {
                    "total_recursal_RJ": 7,
                    "controle_processo_taxa_provimento_2g_recursal_RJ": 50.0,
                },
                "recursal_atividades_lista_RJ": [
                    {"id": 1, "numero_processo": None, "status": "Recebido"}
                ],
            }
        if nome == "por_subfase":
            return {"stats": {}, "recursal_por_subfase_RJ": [{"name": "X", "value": 1, "uf": None}]}
        return {"stats": {}}

    chamadas = _falsos(monkeypatch, "RJ", resposta)
    body = asyncio.run(m.build(_ctx("RJ")))
    assert "controle" not in {c[0] for c in chamadas}
    assert body["historico"]["stats"]["total_recursal_NG"] == 7
    assert body["controle"]["stats"]["controle_processo_taxa_provimento_2g_recursal_NG"] == 50.0
    # sem os campos vazios das linhas
    assert body["periodo"]["recursal_atividades_lista_NG"] == [{"id": 1, "status": "Recebido"}]
    assert body["subfase"]["estoque"]["recursal_por_subfase_NG"] == [{"name": "X", "value": 1}]
    assert body["unidade"] == "RJ"


def test_comissao_so_para_quem_ve_a_comissao(monkeypatch):
    _falsos(monkeypatch, "NG")
    assert asyncio.run(m.build(_ctx()))["comissao"] == {"linhas": [], "unidade": "NG"}
    ctx = _ctx()
    sem = DashboardContext(
        source=None, unit_ref="NG", period=ctx.period, filters={}, can_see_commission=False
    )
    assert asyncio.run(m.build(sem))["comissao"] is None
