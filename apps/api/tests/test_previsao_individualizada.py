"""Previsão Individualizada: o bundle estático do TCC (JSON da v1), recortado ao escritório da unidade."""

import asyncio
from datetime import date

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards import previsao_individualizada as m
from app.dashboards.base import DashboardContext, NotReady, Period


class SemFonte:
    async def fetch(self, name):  # o dashboard é estático: não pode consultar o banco
        raise AssertionError(f"consultou {name}")


def _ctx(unit_ref):
    return DashboardContext(
        source=SemFonte(),
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters={},
        can_see_commission=True,
    )


def test_registrado_sem_queries():
    assert DASHBOARDS["previsao-individualizada"] is m.MODULE
    assert m.MODULE.queries == ()


def test_so_ng_e_la():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("RJ")))


@pytest.mark.parametrize("sigla", ["NG", "LA"])
def test_cada_unidade_ve_so_o_proprio_escritorio(sigla):
    p = asyncio.run(m.build(_ctx(sigla)))
    assert p["opcoes"]["escritorios"] == [sigla]
    assert list(p["referencia_acordo_pre"]) == [sigla]
    for nome in m.TABELAS_POR_COMBINACAO:
        assert p[nome], nome
        assert {k.split("|")[m.POS_ESCRITORIO] for k in p[nome]} == {sigla}, nome
    # as métricas do modelo são do estudo inteiro
    assert p["metricas"]["cindex"] and p["km_materia"]


def test_recorte_nao_muda_o_cache():
    asyncio.run(m.build(_ctx("NG")))
    la = asyncio.run(m.build(_ctx("LA")))
    inteiro = m.montar_payload_tcc_previsao_individual()
    assert inteiro["opcoes"]["escritorios"] == ["NG", "LA"]
    assert len(inteiro["previsoes"]) > len(la["previsoes"])


def test_recortar_chaves():
    payload = {
        "previsoes": {"T|M|C|K|NG|F": [1], "T|M|C|K|LA|F": [2]},
        "opcoes": {"escritorios": ["NG", "LA"], "materias": ["M"]},
        "referencia_acordo_pre": {"NG": 1, "LA": 2},
        "metricas": {"x": 1},
    }
    out = m.recortar(payload, "LA")
    assert out["previsoes"] == {"T|M|C|K|LA|F": [2]}
    assert out["opcoes"] == {"escritorios": ["LA"], "materias": ["M"]}
    assert out["referencia_acordo_pre"] == {"LA": 2}
    assert out["metricas"] == {"x": 1}
