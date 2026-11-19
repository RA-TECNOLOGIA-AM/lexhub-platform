"""Emendas e Manifestações: as rotas da v1 (NG e LA), os filtros (UF só no NG) e a exportação."""

import asyncio
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

import pytest

import app.dashboards  # noqa: F401  (a casca antes da cópia da v1: evita o import circular rodando sozinho)
from app.analyses import v1_dashboard_emendas as v1
from app.dashboards import DASHBOARDS
from app.dashboards import emendas_manifestacoes as m
from app.dashboards.base import DashboardContext, NotReady, Period


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 19)),
        filters=filters,
        can_see_commission=True,
    )


def test_registrado_com_as_queries_da_v1():
    assert DASHBOARDS["emendas-manifestacoes"] is m.MODULE
    assert set(m.MODULE.queries) == {
        "agendamentos_setor_emendas_manifestacoes_NG",
        "agendamentos_setor_emendas_manifestacoes_LA",
        "agendamentos_setor_emendas_manifestacoes_RJ",
    }


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("SP")))


def test_rj_usa_a_rota_do_ng_com_a_query_do_rj(monkeypatch):
    """O RJ não tem a página na v1: o cálculo do NG (com UF), lendo a query do RJ (escritório 27)."""
    from app.source_queries import QUERIES

    for ng, rj in m.QUERIES_RJ.items():
        assert QUERIES[rj]["query"].replace("= 27", "= 20") == QUERIES[ng]["query"]
    chamadas = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        linhas = await ctx.source.fetch("agendamentos_setor_emendas_manifestacoes_NG")
        chamadas.append((fn.__name__, kw.get("uf_emendas_manifestacoes"), linhas))
        return SimpleNamespace(
            model_dump=lambda: {"stats": {"total_atividades_emendas_manifestacoes_NG": 4}}
        )

    class Fonte:
        async def fetch(self, name):
            return [name]

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    ctx = replace(_ctx("RJ", uf_emendas_manifestacoes=["RJ"]), source=Fonte())
    corpo = asyncio.run(m.build(ctx))
    assert corpo["unidade"] == "RJ"
    assert corpo["stats"]["total_atividades_emendas_manifestacoes_NG"] == 4
    rota = "get_emendas_manifestacoes_NG_dashboard"
    query_rj = ["agendamentos_setor_emendas_manifestacoes_RJ"]
    assert chamadas == [(rota, ["RJ"], query_rj), (rota, None, query_rj)]


def test_uf_so_vai_para_a_rota_do_ng():
    filtros = {
        "funcionario_emendas_manifestacoes": [" Ana "],
        "uf_emendas_manifestacoes": ["PA"],
    }
    assert m.filtros_da_rota(_ctx("NG", **filtros)) == {
        "funcionario_emendas_manifestacoes": ["Ana"],
        "atividade_emendas_manifestacoes": None,
        "uf_emendas_manifestacoes": ["PA"],
    }
    assert m.filtros_da_rota(_ctx("LA", **filtros)) == {
        "funcionario_emendas_manifestacoes": ["Ana"],
        "atividade_emendas_manifestacoes": None,
    }


@pytest.mark.parametrize("unidade", ["NG", "LA"])
def test_periodo_com_filtros_e_historico_sem(monkeypatch, unidade):
    chamadas = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        chamadas.append((from_date, to_date, kw.get("funcionario_emendas_manifestacoes")))
        return SimpleNamespace(
            model_dump=lambda: {
                "stats": {f"total_atividades_emendas_manifestacoes_{unidade}": 3},
                f"emendas_manifestacoes_comissionamento_por_funcionario_{unidade}": [
                    {"funcionario": "Ana", "valor_comissao": 2.0, "faixa": None}
                ],
            }
        )

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    corpo = asyncio.run(m.build(_ctx(unidade, funcionario_emendas_manifestacoes=["Ana"])))
    assert chamadas == [(date(2026, 11, 1), date(2026, 11, 19), ["Ana"]), (None, None, None)]
    assert corpo["unidade"] == unidade
    assert corpo["stats"]["total_atividades_emendas_manifestacoes_NG"] == 3
    assert corpo["emendas_manifestacoes_comissionamento_por_funcionario_NG"] == [
        {"funcionario": "Ana", "valor_comissao": 2.0}
    ]


def test_exportacao_com_as_colunas_e_a_visao_da_v1(monkeypatch):
    linha = v1.RecursalAtividadeTarefaRow(
        id=7,
        status="Encerrado Cumprido",
        descricao="X",
        pessoa_setor="MANIFESTAÇÃO - ELABORAR DILAÇÃO",
        funcionario="Ana",
        atividade="ELABORAR DILAÇÃO",
        numero_processo="123",
        concluida=True,
    )

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        assert kw["uf_emendas_manifestacoes"] == ["AM"]
        return SimpleNamespace(
            emendas_manifestacoes_por_prazo_lista_NG=[],
            emendas_manifestacoes_atividades_lista_NG=[linha],
        )

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    ctx = replace(
        _ctx("NG", uf_emendas_manifestacoes=["AM"]), export_options={"visao": "concluidas"}
    )
    linhas = asyncio.run(m.EXPORT.rows(ctx))
    assert linhas[0]["numero_processo"] == "123" and linhas[0]["concluida"] == "Sim"
    assert list(linhas[0]) == list(m.EXPORT.fields)
    assert list(m.EXPORT.labels.values()) == v1._HEADERS_EXPORT_EMENDAS_MANIFESTACOES


def test_campos_da_exportacao_iguais_no_front():
    import re
    from pathlib import Path

    arquivo = (
        Path(__file__).resolve().parents[2]
        / "web/src/pages/dashboards/emendas-manifestacoes/exportFields.ts"
    )
    if not arquivo.exists():
        pytest.skip("front fora do checkout")
    texto = arquivo.read_text(encoding="utf-8")
    assert dict(re.findall(r"slug: '([a-z_]+)', label: '([^']+)'", texto)) == m.EXPORT.labels


def test_no_rj_manifestar_dilacao_de_prazo_conta_como_dilacao(monkeypatch):
    """Decisão de 19/11/2026: no RJ, "MANIFESTAR DILAÇÃO DE PRAZO" é dilação (R$ 0,50); no NG segue a v1."""
    from app.analyses.NG import emendas_manifestacoes_NG as ng

    vistos = {}

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        vistos[ctx.unit_ref] = (
            ng._is_atividade_dilacao("MANIFESTAR DILAÇÃO DE PRAZO"),
            ng._is_atividade_manifestacao("MANIFESTAR DILAÇÃO DE PRAZO"),
            ng._is_atividade_dilacao("ELABORAR DILAÇÃO"),
        )
        return SimpleNamespace(model_dump=lambda: {"stats": {}})

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    asyncio.run(m.build(_ctx("RJ")))
    asyncio.run(m.build(_ctx("NG")))
    assert vistos == {"RJ": (True, False, True), "NG": (False, True, True)}
    # fora da chamada, o padrão volta a ser o da v1
    assert ng._is_atividade_manifestacao("MANIFESTAR DILAÇÃO DE PRAZO")
