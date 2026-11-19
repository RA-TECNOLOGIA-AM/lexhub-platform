"""Controle de Processos (NG): as chamadas da v1 (LexFlow, banco NG legado e LexPre) numa resposta só."""

import asyncio
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

import pytest

import app.dashboards  # noqa: F401  (a casca antes da cópia da v1: evita o import circular rodando sozinho)
from app.dashboards import DASHBOARDS
from app.dashboards import controle_processos as m
from app.dashboards.base import DashboardContext, DashboardInputError, NotReady, Period


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source="lexflow",
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 19)),
        filters=filters,
        can_see_commission=True,
        extra_sources={"ng": "ng", "lexpre": "lexpre"},
        extra_refs={"ng": "NG", "lexpre": "1"},
    )


def test_registrado_com_as_fontes_dos_tres_bancos():
    mod = DASHBOARDS["controle-processos"]
    assert mod is m.MODULE
    assert "controle_processo" in mod.queries and "execucao_LA" in mod.queries
    assert mod.extra_queries == {
        "ng": ("setor_protocolo", "comercial_geral_NG"),
        "lexpre": ("log_setor_demanda_lexpre_NG",),
    }
    assert mod.export is None


def test_so_ng_por_enquanto():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("LA")))


def test_filtros_da_pagina():
    assert m.filtros_da_pagina(_ctx()) == (None, None, None)
    ctx = _ctx(situacao_controle=["Ativo"], uf_controle=["am", " pa "], fase_controle=["INICIAL"])
    assert m.filtros_da_pagina(ctx) == ("ativo", ["AM", "PA"], "INICIAL")
    with pytest.raises(DashboardInputError):
        m.filtros_da_pagina(_ctx(situacao_controle=["arquivado"]))


def test_as_chamadas_da_v1(monkeypatch):
    chamadas = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        chamadas.append((fn.__name__, ctx.source, from_date, kw))
        return SimpleNamespace(
            model_dump=lambda: {
                "stats": {
                    "total_controle_processo_NG": 7,
                    "protocolos_resolvidos": 2,
                    "total_em_execucao": 3,
                },
                "controle_processo_por_fase_NG": [{"name": "INICIAL", "value": 7, "percent": None}],
            }
        )

    async def lexpre(sub):
        assert (sub.source, sub.unit_ref, sub.filters["uf"]) == ("lexpre", "1", ["AM"])
        return {
            "stats": {
                "protocolados_total": {"total": 9},
                "valor_causa_protocolado": {"total": 90},
                "media_tempo_protocolado": 0.33,
                "mediana_tempo_protocolado": 0.06,
            }
        }

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    monkeypatch.setattr(m.protocolo_lexpre, "build", lexpre)
    corpo = asyncio.run(
        m.build(_ctx(situacao_controle=["ativo"], uf_controle=["AM"], fase_controle=["INICIAL"]))
    )

    rotas = [(nome, fonte, de is not None) for nome, fonte, de, _ in chamadas]
    assert rotas == [
        ("get_controle_processo_NG_dashboard", "lexflow", True),  # período
        ("get_controle_processo_NG_dashboard", "lexflow", False),  # histórico
        ("get_controle_processo_NG_dashboard", "lexflow", False),  # fase
        ("get_protocolo_dashboard", "ng", True),  # banco NG legado
        ("get_execucao_dashboard", "lexflow", True),
        ("get_execucao_acordos_ng_dashboard", "lexflow", True),
        ("get_execucao_dashboard", "lexflow", False),
        ("get_execucao_acordos_ng_dashboard", "lexflow", False),
    ]
    kws = [kw for *_, kw in chamadas]
    assert kws[0]["situacao"] == "ativo" and kws[0]["uf"] == ["AM"] and kws[0]["fase"] is None
    assert kws[2]["fase"] == "INICIAL"
    assert kws[3]["uf_protocolo"] == ["AM"] and "situacao" not in kws[3]
    assert all(k["uf"] == ["AM"] for k in kws[4:])
    assert corpo["historico"]["controle_processo_por_fase_NG"] == [{"name": "INICIAL", "value": 7}]
    assert corpo["lexpre"] == {
        "protocolados_total": 9,
        "valor_causa_protocolado": 90,
        "media_tempo_protocolado": 0.33,
        "mediana_tempo_protocolado": 0.06,
        "comparativo_tempo_medio_protocolado": None,
        "comparativo_mediana_tempo_protocolado": None,
    }
    assert corpo["protocolo"]["protocolos_resolvidos"] == 2
    assert corpo["execucao"]["total_em_execucao"] == 3


def test_sem_fase_nao_busca_subfases_e_sem_lexpre_soma_so_o_legado(monkeypatch):
    nomes = []

    async def chamar_v1(ctx, copia, fn, from_date, to_date, **kw):
        nomes.append(kw.get("fase"))
        return SimpleNamespace(model_dump=lambda: {"stats": {}})

    monkeypatch.setattr(m.generico_v1, "chamar_v1", chamar_v1)
    corpo = asyncio.run(
        m.build(replace(_ctx(), extra_sources={"ng": "ng"}, extra_refs={"ng": "NG"}))
    )
    assert corpo["fase"] is None and corpo["lexpre"] is None
    assert "INICIAL" not in nomes
