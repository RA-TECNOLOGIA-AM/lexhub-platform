"""Comercial (LexPre): a prévia do que ainda pode ser protocolado (modal "Ritmo da meta")."""

import asyncio
from datetime import date

from app.dashboards import DASHBOARDS, pre_protocolo
from app.dashboards import comercial_lexpre as m
from app.dashboards.base import DashboardContext, Period


class Fonte:
    def __init__(self, linhas):
        self.linhas = linhas

    async def fetch(self, query):
        assert query == "comercial_lexpre_NG"
        return self.linhas


def _ctx():
    return DashboardContext(
        source=Fonte([{"ESCRITORIO_ID": 1}]),
        unit_ref="1",
        period=Period(date(2026, 11, 1), date(2026, 11, 24)),
        filters={},
        can_see_commission=True,
    )


def test_meses_antes_como_o_calendario():
    assert m.meses_antes(date(2026, 11, 24), 3) == date(2026, 8, 24)
    assert m.meses_antes(date(2026, 5, 31), 3) == date(2026, 2, 28)
    assert m.meses_antes(date(2026, 2, 15), 3) == date(2025, 11, 15)


def test_previa_ticket_dos_ultimos_3_meses_vezes_os_represados(monkeypatch):
    janelas = []

    def ticket(rows, de, ate):
        janelas.append((de, ate))
        return 300_000.0

    async def setores(ctx):
        return {
            "pendencias": {"stats": {"pendencias_nao_resolvidas": 9}},
            "org_documentos": {"stats": {"represados": 24}},
            "peticionamento": {"stats": {"represados": 74}},
            "protocolo": {"stats": {"represados": 8}},
        }

    monkeypatch.setattr(
        m, "filter_comercial_lexpre_por_escritorio_ng", lambda rows, escritorio_id: rows
    )
    monkeypatch.setattr(m, "get_ticket_medio_protocolado_lexpre", ticket)
    monkeypatch.setattr(pre_protocolo, "build", setores)
    out = asyncio.run(m.previa_represados(_ctx(), hoje=date(2026, 11, 24)))
    assert janelas == [(date(2026, 8, 24), date(2026, 11, 24))]
    assert out == {
        "de": "2026-08-24",
        "ate": "2026-11-24",
        "ticket_medio": 300_000.0,
        "represados": {"pendencias": 9, "org_documentos": 24, "peticionamento": 74, "protocolo": 8},
        "total_represados": 115,
        "valor": 34_500_000.0,
    }


def test_setor_sem_numero_conta_zero(monkeypatch):
    async def setores(ctx):
        return {"pendencias": {"stats": None}, "protocolo": {"stats": {"represados": 5}}}

    monkeypatch.setattr(
        m, "filter_comercial_lexpre_por_escritorio_ng", lambda rows, escritorio_id: rows
    )
    monkeypatch.setattr(m, "get_ticket_medio_protocolado_lexpre", lambda rows, de, ate: 10.0)
    monkeypatch.setattr(pre_protocolo, "build", setores)
    out = asyncio.run(m.previa_represados(_ctx(), hoje=date(2026, 11, 24)))
    assert out["total_represados"] == 5 and out["valor"] == 50.0


def test_so_o_comercial_traz_a_previa():
    assert DASHBOARDS["comercial-lexpre"].build is m.build_comercial
    assert DASHBOARDS["comissao-lexpre"].build is not m.build_comercial
    assert set(pre_protocolo.MODULE.queries) <= set(DASHBOARDS["comercial-lexpre"].queries)
