"""Tickets (banco NG): os filtros da V2 viram os pares selection_dim/selection_value da rota da v1."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from app.dashboards import tickets as m
from app.dashboards.base import DashboardContext, NotReady, Period


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters=filters,
        can_see_commission=True,
    )


def test_selecao_na_ordem_da_v1_um_valor_por_dimensao():
    assert m.selecao({}) == (None, None)
    dims, valores = m.selecao(
        {"ticket_servidor": ["LA-AM"], "ticket_categoria": ["bug", "acesso"], "ticket_status": []}
    )
    assert dims == ["categoria", "servidor"]
    assert valores == ["bug", "LA-AM"]


def test_so_na_ng():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("LA")))


def test_chama_a_rota_da_v1_com_o_periodo_e_a_selecao(monkeypatch):
    chamadas = []

    async def handler(**kw):
        chamadas.append(kw)
        return SimpleNamespace(
            model_dump=lambda: {"dashboard": "tickets", "stats": {"total_tickets": 3}}
        )

    monkeypatch.setitem(m.copia.HANDLERS, "tickets", handler)
    body = asyncio.run(m.build(_ctx(ticket_subcategoria=["Outros"])))
    assert body["stats"]["total_tickets"] == 3
    assert chamadas == [
        {
            "from_date": date(2026, 11, 1),
            "to_date": date(2026, 11, 18),
            "selection_dim": ["sub_categoria"],
            "selection_value": ["Outros"],
        }
    ]
