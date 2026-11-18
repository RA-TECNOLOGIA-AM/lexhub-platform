"""Publicações: a chamada do período com os filtros da v1, os leitores do histórico todo e a comissão."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import publicacoes as m
from app.dashboards.base import DashboardContext, NotReady, Period


def _ctx(unit_ref="NG", can_see_commission=True, **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters=filters,
        can_see_commission=can_see_commission,
    )


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("SP")))


def test_filtros_da_v1():
    f = m.filtros_v1(
        _ctx(
            leitor_publicacoes=["ANA", "BIA"],
            documento_publicacoes=["SENTENÇA"],
            materia_publicacoes=[],
        )
    )
    assert f["leitor"] == ["ANA", "BIA"] and f["documento"] == "SENTENÇA"
    assert f["materia"] is None and f["tribunal"] is None


def _falso(monkeypatch, u):
    chamadas = []

    async def handler(from_date=None, to_date=None, **kw):
        chamadas.append((from_date, kw))
        resposta = {
            "stats": {f"publicacoes_pendentes_{u}": 7},
            f"publicacoes_cumprido_por_leitor_{u}": [{"name": "ANA", "value": 1, "uf": None}],
            f"publicacoes_pendentes_por_leitor_{u}": [{"name": "BIA", "value": 2}, {"name": ""}],
            f"comissionamento_publicacoes_{u}_por_funcionario": [
                {"funcionario": "ANA", "comissao": 0.2}
            ],
        }
        return SimpleNamespace(model_dump=lambda: resposta)

    monkeypatch.setitem(v1.HANDLERS, f"publicacoes_{u}", handler)
    monkeypatch.setattr(m.generico_v1, "_parametros", lambda h: {})
    return chamadas


def test_periodo_com_filtros_e_leitores_do_historico_sem_filtro(monkeypatch):
    chamadas = _falso(monkeypatch, "LA")
    body = asyncio.run(m.build(_ctx("LA", tribunal_publicacoes=["TJAM"])))
    (de, kw), (de2, kw2) = chamadas
    assert de == date(2026, 11, 1) and kw["tribunal"] == "TJAM"
    assert de2 is None and kw2 == {}
    assert body["stats"]["publicacoes_pendentes_NG"] == 7
    assert body["publicacoes_cumprido_por_leitor_NG"] == [{"name": "ANA", "value": 1}]
    assert body["leitores"] == ["ANA", "BIA"]
    assert body["comissao"] == [{"funcionario": "ANA", "comissao": 0.2}]


def test_comissao_so_para_quem_ve_a_comissao(monkeypatch):
    _falso(monkeypatch, "NG")
    assert asyncio.run(m.build(_ctx(can_see_commission=False)))["comissao"] is None
