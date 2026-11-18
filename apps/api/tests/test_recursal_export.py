"""Exportação do Recursal: os filtros que a janela da v1 mandava, as linhas e os valores da cópia da v1."""

import asyncio
from datetime import date

import pytest

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import DASHBOARDS
from app.dashboards import recursal_export as m
from app.dashboards.base import DashboardContext, NotReady, Period


def _ctx(unit_ref="LA", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters=filters,
        can_see_commission=True,
    )


def test_o_recursal_exporta_os_campos_da_v1():
    spec = DASHBOARDS["recursal"].export
    assert list(spec.fields) == list(v1._CAMPOS_EXPORT_RECURSAL_NG)
    assert spec.labels == v1._LABELS_EXPORT_RECURSAL_NG


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m._linhas(_ctx("SP")))


def test_filtros_como_a_janela_da_v1(monkeypatch):
    pedidos = {}

    def parse(**kw):
        pedidos.update(kw)
        return "F", "A"

    async def fetch():
        return [{"x": 1}]

    async def linhas(rows, filtros, atividades, de, ate):
        assert (filtros, atividades, de, ate) == ("F", "A", None, None)  # sem período, como a v1
        return rows

    monkeypatch.setattr(v1, "_parse_recursal_la_filtros_completos", parse)
    monkeypatch.setattr(v1, "fetch_recursal_LA", fetch)
    monkeypatch.setattr(v1, "_rows_recursal_la_filtradas", linhas)
    monkeypatch.setattr(v1, "_enriquecer_numero_processo_export_la", lambda rows: rows)
    monkeypatch.setattr(v1, "_valor_campo_export_recursal_la", lambda row, slug: f"{slug}!")
    out = asyncio.run(
        m._linhas(
            _ctx(
                id_1g_recursal=["19"],
                juiz_recursal=["Ana"],
                extinto_2g_recursal=["com_merito"],
                funcionario_recursos=["Bia"],
                atividade_recursos=["CONTRARRAZÕES"],
            )
        )
    )
    assert pedidos["id_1g"] == [19] and pedidos["juiz"] == ["Ana"]
    assert pedidos["atividade_recursos"] == ["CONTRARRAZÕES"]
    # a v1 não mandava Extintos 2º grau, funcionário nem situação na exportação
    assert "extinto_2g" not in pedidos and "funcionario_recursos" not in pedidos
    assert out == [{s: f"{s}!" for s in v1._CAMPOS_EXPORT_RECURSAL_NG}]


def test_comissao_so_na_ng():
    assert asyncio.run(m.comissao(_ctx("LA"))) is None
