"""Pendências Intermediárias: as rotas da v1 (NG e LA), os filtros com o mesmo nome nas duas e a exportação."""

import asyncio
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

import pytest

import app.dashboards  # noqa: F401  (a casca antes da cópia da v1: evita o import circular rodando sozinho)
from app.analyses import v1_dashboard_intermediarias as v1
from app.dashboards import DASHBOARDS
from app.dashboards import pendencias_intermediarias as m
from app.dashboards.base import DashboardContext, NotReady, Period


class Fonte:
    def __init__(self, rows=None):
        self.rows = rows or {}

    async def fetch(self, name):
        return self.rows.get(name, [])


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=Fonte(),
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 19)),
        filters=filters,
        can_see_commission=True,
    )


def test_registrado_com_as_queries_da_v1():
    assert DASHBOARDS["pendencias-intermediarias"] is m.MODULE
    assert set(m.MODULE.queries) == {
        "agendamentos_setor_intermediarias_NG",
        "agendamentos_dilacao_prazo_intermediarias_NG",
        "agendamentos_setor_intermediarias_LA",
        "agendamentos_dilacao_prazo_intermediarias_LA",
        "agendamentos_setor_intermediarias_RJ",
        "agendamentos_dilacao_prazo_intermediarias_RJ",
    }


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("SP")))


def test_rj_usa_a_rota_do_ng_com_as_queries_do_rj():
    """O RJ não tem a página na v1: o cálculo do NG, lendo as queries do RJ (escritório 27)."""
    from app.source_queries import QUERIES

    setor_ng, setor_rj = (
        "agendamentos_setor_intermediarias_NG",
        m.QUERIES_RJ["agendamentos_setor_intermediarias_NG"],
    )
    assert QUERIES[setor_rj]["query"].replace("= 27", "= 20") == QUERIES[setor_ng]["query"]
    # dilação do RJ (decisão de 19/11/2026): ELABORAR DILAÇÃO, como o NG, e também MANIFESTAR DILAÇÃO DE PRAZO
    dilacao_rj = QUERIES[m.QUERIES_RJ["agendamentos_dilacao_prazo_intermediarias_NG"]]["query"]
    assert "id_escritorio_assinante = 27" in dilacao_rj
    assert "'MANIFESTAÇÃO - ELABORAR DILAÇÃO'" in dilacao_rj
    assert "'MANIFESTAÇÃO - MANIFESTAR DILAÇÃO DE PRAZO'" in dilacao_rj
    fonte = Fonte({"agendamentos_setor_intermediarias_RJ": [{"x": 1}]})
    ctx, rota = m._na_rota(replace(_ctx("RJ"), source=fonte))
    assert rota == "NG"
    assert asyncio.run(ctx.source.fetch("agendamentos_setor_intermediarias_NG")) == [{"x": 1}]
    assert m.filtros_da_rota(_ctx("RJ", funcionario_intermediarias=["Ana"])) == {
        "funcionario_intermediarias_ng": ["Ana"],
        "atividade_intermediarias_ng": None,
    }


def test_rj_responde_com_a_propria_unidade(monkeypatch):
    rotas = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        rotas.append((fn.__name__, type(ctx.source).__name__))
        return SimpleNamespace(
            model_dump=lambda: {"stats": {"total_atividades_intermediarias_NG": 5}}
        )

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    corpo = asyncio.run(m.build(_ctx("RJ")))
    assert corpo["unidade"] == "RJ"
    assert corpo["stats"]["total_atividades_intermediarias_NG"] == 5
    assert rotas == [("get_pendencias_intermediarias_NG_dashboard", "_FonteRJ")] * 2


def test_filtros_no_parametro_da_rota_de_cada_unidade():
    ctx = _ctx(funcionario_intermediarias=[" Ana "], atividade_intermediarias=[])
    assert m.filtros_da_rota(ctx) == {
        "funcionario_intermediarias_ng": ["Ana"],
        "atividade_intermediarias_ng": None,
    }
    assert m.filtros_da_rota(replace(ctx, unit_ref="LA")) == {
        "funcionario_intermediarias": ["Ana"],
        "atividade_intermediarias": None,
    }
    for u in m.UNIDADES:
        params = v1.HANDLERS[f"pendencias_intermediarias_{m.ROTA[u]}"].__code__.co_varnames
        assert set(m.filtros_da_rota(replace(ctx, unit_ref=u))) <= set(params)


@pytest.mark.parametrize("unidade", ["NG", "LA"])
def test_periodo_com_filtros_e_historico_sem(monkeypatch, unidade):
    chamadas = []
    sufixo = "_ng" if unidade == "NG" else ""

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        chamadas.append((from_date, to_date, kw.get(f"funcionario_intermediarias{sufixo}")))

        class R:
            def model_dump(self):
                return {
                    "stats": {f"total_atividades_intermediarias_{unidade}": 3},
                    f"intermediarias_demandas_por_funcionario_{unidade}": [
                        {"name": "Ana", "total": 1, "percent": None}
                    ],
                    f"intermediarias_concluidas_por_dia_por_funcionario_{unidade}": {
                        "Ana": [{"name": "2026-11-03", "value": 1.0, "uf": None}]
                    },
                }

        return R()

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    corpo = asyncio.run(m.build(_ctx(unidade, funcionario_intermediarias=["Ana"])))
    assert chamadas == [(date(2026, 11, 1), date(2026, 11, 19), ["Ana"]), (None, None, None)]
    # nomes da NG nas duas unidades, sem as chaves nulas
    assert corpo["stats"]["total_atividades_intermediarias_NG"] == 3
    assert corpo["intermediarias_demandas_por_funcionario_NG"] == [{"name": "Ana", "total": 1}]
    assert corpo["intermediarias_concluidas_por_dia_por_funcionario_NG"] == {
        "Ana": [{"name": "2026-11-03", "value": 1.0}]
    }
    assert corpo["unidade"] == unidade


def test_exportacao_com_as_colunas_e_a_visao_da_v1(monkeypatch):
    linha = v1.RecursalAtividadeTarefaRow(
        id=7,
        status="Encerrado Cumprido",
        descricao="X",
        pessoa_setor="PENDÊNCIAS - SOLICITAR DOCS DO CLIENTE",
        funcionario="Ana",
        atividade="SOLICITAR DOCS DO CLIENTE",
        concluida=True,
    )
    pedidas = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        pedidas.append(kw.get("atividade_intermediarias"))
        return SimpleNamespace(
            intermediarias_por_prazo_lista_LA=[linha], intermediarias_atividades_lista_LA=[]
        )

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    ctx = replace(_ctx("LA", atividade_intermediarias=["SOLICITAR DOCS DO CLIENTE"]))
    por_prazo = asyncio.run(m.EXPORT.rows(replace(ctx, export_options={"visao": "por_prazo"})))
    concluidas = asyncio.run(m.EXPORT.rows(replace(ctx, export_options={"visao": "concluidas"})))
    assert pedidas == [["SOLICITAR DOCS DO CLIENTE"]] * 2
    assert concluidas == []
    assert por_prazo[0]["id"] == 7 and por_prazo[0]["concluida"] == "Sim"
    assert list(por_prazo[0]) == list(m.EXPORT.fields)
    assert list(m.EXPORT.labels.values()) == v1._HEADERS_EXPORT_INTERMEDIARIAS
    assert [o.key for o in m.EXPORT.options] == ["visao"]


def test_campos_da_exportacao_iguais_no_front():
    """O front (pages/dashboards/pendencias-intermediarias/exportFields.ts) oferece as colunas da API."""
    import re
    from pathlib import Path

    arquivo = (
        Path(__file__).resolve().parents[2]
        / "web/src/pages/dashboards/pendencias-intermediarias/exportFields.ts"
    )
    if not arquivo.exists():
        pytest.skip("front fora do checkout")
    texto = arquivo.read_text(encoding="utf-8")
    assert dict(re.findall(r"slug: '([a-z_]+)', label: '([^']+)'", texto)) == m.EXPORT.labels
    assert re.findall(r"value: '([a-z_]+)'", texto) == list(m.VISAO.choices)
