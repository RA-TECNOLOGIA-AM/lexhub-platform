"""Execução Estratégico Geral: as 8 chamadas da página da v1 (Condenação e Acordos) e o período anterior."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import execucao_estrategico as m
from app.dashboards.base import DashboardContext, NotReady, Period


def test_mes_anterior_como_a_v1():
    assert m.mes_anterior(date(2026, 8, 20)) == date(2026, 7, 20)
    assert m.mes_anterior(date(2026, 3, 31)) == date(2026, 2, 28)
    assert m.mes_anterior(date(2028, 3, 31)) == date(2028, 2, 29)
    assert m.mes_anterior(date(2026, 1, 15)) == date(2025, 12, 15)


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 17)),
        filters=filters,
        can_see_commission=True,
    )


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("CONSOLIDADO")))


def test_as_8_chamadas_com_os_parametros_da_v1(monkeypatch):
    chamadas = []

    def falso(rota):
        async def handler(from_date=None, to_date=None, **kw):
            chamadas.append((rota, from_date, to_date, kw))
            return SimpleNamespace(model_dump=lambda: {"stats": {}, "extra_nao_usado": 1})

        return handler

    monkeypatch.setitem(v1.HANDLERS, "execucao", falso("execucao"))
    monkeypatch.setitem(v1.HANDLERS, "execucao_acordos_NG", falso("acordos"))
    monkeypatch.setattr(m.generico_v1, "_parametros", lambda h: {})
    ctx = _ctx(
        materia=["ANP"],
        uf=["AM"],
        comarca=["MANAUS"],
        ano_ajuizamento=["2024"],
        funcionario_execucao=["Ana"],
    )
    body = asyncio.run(m.build(ctx))

    assert len(chamadas) == 8
    datas = [(c[0], c[1], c[2]) for c in chamadas]
    assert datas[:3] == [
        ("execucao", date(2026, 11, 1), date(2026, 11, 17)),
        ("execucao", None, None),
        ("execucao", date(2026, 10, 1), date(2026, 10, 17)),
    ]
    cond, acor, cs = chamadas[0][3], chamadas[3][3], chamadas[6][3]
    assert (
        cond["uf"] == ["AM"]
        and cond["comarca"] == ["MANAUS"]
        and cond["ano_ajuizamento_execucao"] == "2024"
    )
    assert acor["ano_ajuizamento_execucao_acordos"] == "2024" and acor["materia"] == ["ANP"]
    # Confecção CS: sem UF e comarca; as 4 atividades por padrão; o funcionário escolhido
    assert "uf" not in cs and "comarca" not in cs
    assert cs["atividade_execucao"] == list(m.ATIVIDADES_CONFECCAO_CS)
    assert cs["funcionario_execucao"] == ["Ana"]
    # só os campos que a página usa
    assert "extra_nao_usado" not in body["condenacao"]["atual"]
    assert set(body["condenacao"]["atual"]["stats"]) == set(m.CAMPOS["condenacao_atual"]["stats"])
    assert body["periodo_anterior"] == {"from": "2026-10-01", "to": "2026-10-17"}


def test_atividade_escolhida_so_na_confeccao(monkeypatch):
    chamadas = []

    async def handler(from_date=None, to_date=None, **kw):
        chamadas.append(kw)
        return SimpleNamespace(model_dump=lambda: {"stats": {}})

    monkeypatch.setitem(v1.HANDLERS, "execucao", handler)
    monkeypatch.setitem(v1.HANDLERS, "execucao_acordos_NG", handler)
    monkeypatch.setattr(m.generico_v1, "_parametros", lambda h: {})
    asyncio.run(m.build(_ctx(atividade_execucao=["Manifestação Cálculo 1"])))
    assert chamadas[6]["atividade_execucao"] == ["Manifestação Cálculo 1"]  # Confecção CS
    assert chamadas[7]["atividade_execucao"] == list(
        m.ATIVIDADES_CONFECCAO_CS
    )  # "Por atividade": sempre as 4


def test_la_usa_as_rotas_do_la_e_devolve_os_nomes_da_ng(monkeypatch):
    chamadas = []

    def falso(rota, resposta):
        async def handler(from_date=None, to_date=None, **kw):
            chamadas.append((rota, kw))
            return SimpleNamespace(model_dump=lambda: resposta)

        return handler

    cond = {
        "stats": {"total_em_execucao_LA": 7},
        "execucao_por_materia_LA": [{"name": "RMC", "value": 7}],
    }
    acor = {"stats": {"total_em_execucao_acordos_LA": 3}}
    monkeypatch.setitem(v1.HANDLERS, "execucao_LA", falso("execucao_LA", cond))
    monkeypatch.setitem(v1.HANDLERS, "execucao_acordos_LA", falso("execucao_acordos_LA", acor))
    monkeypatch.setattr(m.generico_v1, "_parametros", lambda h: {})
    body = asyncio.run(m.build(_ctx("LA")))

    assert [c[0] for c in chamadas] == ["execucao_LA"] * 3 + ["execucao_acordos_LA"] * 3 + [
        "execucao_LA"
    ] * 2
    assert body["condenacao"]["atual"]["stats"]["total_em_execucao"] == 7
    assert body["condenacao"]["atual"]["execucao_por_materia"] == [{"name": "RMC", "value": 7}]
    assert body["acordos"]["historico"]["stats"]["total_em_execucao_acordos_NG"] == 3
    # Confecção CS: a atividade antiga, sem grau, também entra no LA (e no RJ)
    assert chamadas[6][1]["atividade_execucao"][0] == "Elaborar Cumprimento de Sentença"
    assert body["atividades_confeccao"] == list(m.ATIVIDADES_CONFECCAO_CS_POR_UNIDADE["LA"])
