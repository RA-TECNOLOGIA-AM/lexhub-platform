"""Sobrevivência Processual: a coorte do estudo (query copiada da v1) no formato colunar da v1, só na NG."""

import asyncio
from datetime import date

import pytest

from app.dashboards import sobrevivencia_processual as m
from app.dashboards.base import DashboardContext, NotReady, Period
from app.source_queries import QUERIES


class Fonte:
    def __init__(self, rows):
        self.rows = rows
        self.pedidas = []

    async def fetch(self, name):
        self.pedidas.append(name)
        return self.rows


def _ctx(fonte, unit_ref="NG"):
    return DashboardContext(
        source=fonte,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters={},
        can_see_commission=True,
    )


def test_query_da_v1_no_lexflow():
    assert QUERIES[m.QUERY]["database"] == "lexflow"


def test_so_ng_e_la():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx(Fonte([]), "RJ")))


def test_cada_unidade_ve_so_o_proprio_escritorio():
    base = {"duracao_dias_e1": 10, "tipo_evento_e1": "CENSURADO"}
    fonte = Fonte(
        [{**base, "id_escritorio_assinante": 20}, {**base, "id_escritorio_assinante": 21}]
    )
    ng = asyncio.run(m.build(_ctx(fonte, "NG")))
    la = asyncio.run(m.build(_ctx(fonte, "LA")))
    assert ng["escritorio_dict"] == ["NG"] and len(ng["registros"]["duracao_e1"]) == 1
    assert la["escritorio_dict"] == ["LA"] and len(la["registros"]["duracao_e1"]) == 1


def test_monta_o_payload_colunar_da_v1():
    linha = {
        "id_escritorio_assinante": 21,
        "duracao_dias_e1": 120,
        "tipo_evento_e1": "ACORDO",
        "tipo_acordo": "PRE_SENTENCA",
        "duracao_dias_acordo": 110,
        "materia": "CESTA",
        "tipo_evento_e2": "PAGO",
        "duracao_dias_e2": 30,
        "tipo_evento_sentenca": "CENSURADO",
        "tipo_evento_acordao": "CENSURADO",
    }
    fonte = Fonte([linha])
    p = asyncio.run(m.build(_ctx(fonte, "LA")))
    assert fonte.pedidas == [m.QUERY]
    assert p["escritorio_dict"] == ["LA"]
    r = p["registros"]
    assert r["duracao_e1"] == [120] and r["evento_e1"] == [1]
    assert r["tipo_evento_e1"] == [p["tipo_evento_e1_dict"].index("ACORDO")]
    assert r["materia"] == [0] and p["materia_dict"] == ["CESTA"]
    assert r["evento_sentenca"] == [0] and r["duracao_acordo"] == [110]
