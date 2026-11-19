"""Réplicas: as rotas da v1 (NG e LA), os filtros com o mesmo nome nas duas e a taxa de procedência."""

import asyncio
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

import pytest

import app.dashboards  # noqa: F401  (a casca antes da cópia da v1: evita o import circular rodando sozinho)
from app.analyses import v1_dashboard_replicas as v1
from app.dashboards import DASHBOARDS
from app.dashboards import replicas as m
from app.dashboards.base import DashboardContext, NotReady, Period


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 19)),
        filters=filters,
        can_see_commission=True,
    )


def test_registrado_com_as_queries_da_v1_e_sem_exportacao():
    assert DASHBOARDS["replicas"] is m.MODULE
    assert set(m.MODULE.queries) == {
        "agendamentos_setor_replicas_NG",
        "processos_status_1g_replicas_NG",
        "agendamentos_setor_replicas_LA",
        "processos_status_1g_replicas_LA",
        "agendamentos_setor_replicas_RJ",
        "processos_status_1g_replicas_RJ",
    }
    assert m.MODULE.export is None  # a v1 não exporta Réplicas


def test_cada_unidade_com_a_propria_rota_da_v1():
    """Na v1 a rota do NG tinha o nome da do LA; a cópia renomeia (V2) para o NG não cair no cálculo do LA."""
    assert v1.HANDLERS["replicas_NG"] is v1.get_replicas_NG_dashboard
    assert v1.HANDLERS["replicas_LA"] is v1.get_replicas_LA_dashboard
    assert "funcionario_replicas_ng" in v1.get_replicas_NG_dashboard.__code__.co_varnames
    assert "funcionario_replicas" in v1.get_replicas_LA_dashboard.__code__.co_varnames


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("SP")))


def test_rj_usa_a_rota_do_ng_com_as_queries_do_rj(monkeypatch):
    """O RJ não tem a página na v1: o cálculo do NG, lendo as queries do RJ (escritório 27)."""
    from app.source_queries import QUERIES

    for ng, rj in m.QUERIES_RJ.items():
        assert QUERIES[rj]["query"].replace("= 27", "= 20") == QUERIES[ng]["query"]
    chamadas = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        linhas = await ctx.source.fetch("processos_status_1g_replicas_NG")
        chamadas.append((fn.__name__, kw.get("funcionario_replicas_ng"), linhas))
        return SimpleNamespace(model_dump=lambda: {"stats": {"replicas_taxa_procedencia_NG": 33.3}})

    class Fonte:
        async def fetch(self, name):
            return [name]

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    ctx = replace(_ctx("RJ", funcionario_replicas=["Ana"]), source=Fonte())
    corpo = asyncio.run(m.build(ctx))
    assert corpo["unidade"] == "RJ"
    assert corpo["stats"]["replicas_taxa_procedencia_NG"] == 33.3
    rota = "get_replicas_NG_dashboard"
    q_rj = ["processos_status_1g_replicas_RJ"]
    assert chamadas == [(rota, ["Ana"], q_rj), (rota, None, q_rj)]


def test_filtros_no_parametro_da_rota_de_cada_unidade():
    ctx = _ctx(funcionario_replicas=[" Ana "])
    assert m.filtros_da_rota(ctx) == {
        "funcionario_replicas_ng": ["Ana"],
        "atividade_replicas_ng": None,
    }
    assert m.filtros_da_rota(replace(ctx, unit_ref="LA")) == {
        "funcionario_replicas": ["Ana"],
        "atividade_replicas": None,
    }


@pytest.mark.parametrize("unidade", ["NG", "LA"])
def test_periodo_com_filtros_e_historico_sem(monkeypatch, unidade):
    chamadas = []
    sufixo = "_ng" if unidade == "NG" else ""

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        chamadas.append((fn.__name__, from_date, kw.get(f"funcionario_replicas{sufixo}")))
        return SimpleNamespace(
            model_dump=lambda: {
                "stats": {f"replicas_taxa_procedencia_{unidade}": 16.7},
                f"media_replicas_concluidas_por_funcionario_{unidade}": [
                    {"name": "Ana", "value": 2.0, "uf": None}
                ],
            }
        )

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    corpo = asyncio.run(m.build(_ctx(unidade, funcionario_replicas=["Ana"])))
    rota = f"get_replicas_{unidade}_dashboard"
    assert chamadas == [(rota, date(2026, 11, 1), ["Ana"]), (rota, None, None)]
    assert corpo["unidade"] == unidade
    assert corpo["stats"]["replicas_taxa_procedencia_NG"] == 16.7
    assert corpo["media_replicas_concluidas_por_funcionario_NG"] == [{"name": "Ana", "value": 2.0}]


def test_taxa_do_ng_conta_as_atividades_de_replica_atuais():
    """Decisão de 19/11/2026: no NG a réplica virou ELABORAR RÉPLICA SIMPLES / ESPECÍFICA; as três contam."""
    from app.analyses.NG import replicas_NG as ng

    def ag(pid, atividade):
        return {
            "processo_id": pid,
            "ATIVIDADE": atividade,
            "DATA_HORA_CRIACAO": "2026-11-05 10:00:00",
        }

    agendamentos = [
        ag(1, "ELABORAR RÉPLICA SIMPLES"),
        ag(2, "ELABORAR RÉPLICA ESPECÍFICA"),
        ag(3, "ELABORAR RÉPLICA"),
        ag(4, "ANÁLISE DE VIABILIDADE - RÉPLICA"),
        ag(5, "RÉPLICA CANCELADA"),
    ]
    status = [{"processo_id": p, "ID_1G": 20} for p in (1, 2, 3, 4, 5)]
    r = ng.get_replicas_taxa_procedencia_NG(
        agendamentos, status, date(2026, 11, 1), date(2026, 11, 19)
    )
    assert r["replicas_procedencia_total_processos_NG"] == 3
    assert r["replicas_taxa_procedencia_NG"] == 100.0
