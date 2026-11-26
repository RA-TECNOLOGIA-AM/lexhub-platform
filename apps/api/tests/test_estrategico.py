"""Estratégico: as somas da página da v1 (legado + LexPre), as séries por mês/dia e o Jurídico por unidade."""

import asyncio
from datetime import date

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards import estrategico as m
from app.dashboards.base import DashboardContext, DashboardInputError, NotReady, Period


def _ctx(unit="NG", extra=None, refs=None, **filters):
    return DashboardContext(
        source=object(),
        unit_ref=unit,
        period=Period(date(2026, 11, 1), date(2026, 11, 26)),
        filters={k: v for k, v in filters.items()},
        can_see_commission=True,
        extra_sources=extra or {},
        extra_refs=refs or {},
    )


def test_registrado_lexflow_com_os_bancos_extras():
    mod = DASHBOARDS["estrategico"]
    assert mod is m.MODULE and mod.source_db == "lexflow"
    assert set(mod.extra_queries) == {"ng", "laadv", "lexpre"}
    assert "controle_processo_todas_situacoes" in mod.queries
    assert "comercial_geral_LA" in mod.extra_queries["laadv"]


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("jan 2026", "2026-01"),
        ("Março 2025", "2025-03"),
        ("2026-02", "2026-02"),
        ("2026-02-15", "2026-02"),
        ("03/2026", "2026-03"),
        ("2026/04", "2026-04"),
        ("dez 25", "2025-12"),
        ("total", None),
    ],
)
def test_chave_mes_como_a_v1(nome, esperado):
    assert m.chave_mes(nome) == esperado


def test_chave_dia():
    assert m.chave_dia("2026-11-05") == "2026-11-05"
    assert m.chave_dia("05/11/2026") == "2026-11-05"
    assert m.chave_dia("2026/11/05") == "2026-11-05"
    assert m.chave_dia("nov 2026") is None


def test_soma_series_de_formatos_diferentes_pelo_mes():
    legado = [{"name": "jan 2026", "value": 2}, {"name": "fev 2026", "value": 1}]
    lexpre = [{"name": "2026-01", "value": 3}, {"name": "2025-12", "value": 4}]
    assert m.somar_series([legado, lexpre], m.chave_mes) == [
        {"name": "2025-12", "value": 4.0},
        {"name": "2026-01", "value": 5.0},
        {"name": "2026-02", "value": 1.0},
    ]


def _resposta(stats=None, **charts):
    return {"stats": stats or {}, **charts}


def test_soma_legado_e_lexpre():
    c = m.CAMPOS_NG
    legado = {
        "comercial": [_resposta({c["contratos"]: 10, c["contratos_anterior"]: 8, c["acoes"]: 30})],
        "comercial_historico": [
            _resposta(**{c["contratos_por_mes"]: [{"name": "jan 2026", "value": 10}]})
        ],
        "protocolo": [
            _resposta(
                {
                    c["protocolados"]: 4,
                    c["valor_causa"]: 400.0,
                    c["protocolados_anterior"]: 2,
                    c["valor_causa_anterior"]: 100.0,
                    c["ticket_medio"]: 99.0,
                }
            )
        ],
        "protocolo_historico": [_resposta({c["represados_protocolo"]: 5})],
        "org_doc": [_resposta({c["represados_org_doc"]: 1})],
        "pendencias": [_resposta({c["represados_pendencias"]: 2})],
        "peticionamento": [_resposta({c["represados_peticionamento"]: 3})],
    }
    lexpre = {
        "contratos": 5,
        "contratos_anterior": 2,
        "acoes": 7,
        "contratos_por_mes": [{"name": "2026-01", "value": 5}],
        "protocolados": 0,
        "valor_causa": 0.0,
        "represados": 10,
    }
    corpo = m.somar_comercial_protocolo(legado, c, lexpre)
    assert corpo["comercial"]["contratos"] == 15
    assert corpo["comercial"]["contratos_anterior"] == 10
    assert corpo["comercial"]["acoes"] == 37
    assert corpo["comercial"]["contratos_por_mes"] == [{"name": "2026-01", "value": 15.0}]
    p = corpo["protocolo"]
    assert p["represados"] == 1 + 2 + 5 + 3 + 10
    assert p["protocolados"] == 4 and p["valor_causa"] == 400.0
    # Uma resposta do legado e o LexPre sem protocolados: o ticket pronto da rota (como a v1).
    assert p["ticket_medio"] == 99.0
    assert p["ticket_medio_anterior"] == 50.0

    # Com protocolados no LexPre: valor de causa ÷ protocolados das duas bases.
    corpo = m.somar_comercial_protocolo(
        legado, c, {**lexpre, "protocolados": 4, "valor_causa": 400}
    )
    assert corpo["protocolo"]["ticket_medio"] == 100.0


def test_sem_banco_legado_nem_lexpre_zera():
    corpo = m.somar_comercial_protocolo(None, m.CAMPOS_LA, None)
    assert corpo["comercial"]["contratos"] == 0
    assert corpo["protocolo"]["ticket_medio"] == 0.0
    assert corpo["protocolo"]["protocolados_por_mes"] == []


def test_filtros_uf_so_na_ng_e_todas_viram_nenhuma():
    ctx = _ctx(uf_estrategico=["pa", "AM"])
    assert m.filtros_da_pagina(ctx, True)[0] == ["AM", "PA"]
    assert m.filtros_da_pagina(ctx, False)[0] == []
    assert m.filtros_da_pagina(_ctx(uf_estrategico=["AM", "PA", "PB"]), True)[0] == []
    with pytest.raises(DashboardInputError):
        m.filtros_da_pagina(_ctx(uf_estrategico=["SP"]), True)
    with pytest.raises(DashboardInputError):
        m.filtros_da_pagina(_ctx(situacao_estrategico=["fechado"]), True)


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx("MT")))


def test_build_chama_as_rotas_da_unidade(monkeypatch):
    chamadas = []

    async def rota(ctx, copia, nome, de, ate, **filtros):
        chamadas.append((ctx.source_db, nome, de is not None, filtros))
        return {"stats": {}}

    async def sem_lexpre(ctx, ufs):
        return None

    monkeypatch.setattr(m, "_rota", rota)
    monkeypatch.setattr(m, "resumo_lexpre", sem_lexpre)
    ctx = _ctx(
        "NG",
        extra={"ng": object()},
        refs={"ng": "NG"},
        uf_estrategico=["PA", "PB"],
        comarca_estrategico=["MANAUS"],
    )
    corpo = asyncio.run(m.build(ctx))
    assert corpo["unidade"] == "NG" and corpo["tem_uf"] is True
    assert corpo["fontes"] == {"legado": True, "lexpre": False}
    legado = [c for c in chamadas if c[0] == "ng"]
    # 7 chamadas por UF (comercial e protocolo com e sem período; org. doc., pendências e peticionamento sem)
    assert len(legado) == 14
    assert ("ng", "protocolo", True, {"uf_protocolo": ["PA"]}) in legado
    assert ("ng", "comercial", True, {"uf_comercial_ng": "PB"}) in legado
    juridico = [c for c in chamadas if c[1] == "estrategico_geral"]
    assert [c[2] for c in juridico] == [False, True]  # fixo e com período
    assert juridico[0][3] == {
        "escritorio": ["Nicolas Gomes"],
        "comarca": ["MANAUS"],
        "uf": ["PA", "PB"],
        "situacao": None,
    }


def test_build_la_sem_uf_e_com_o_escritorio_do_la(monkeypatch):
    chamadas = []

    async def rota(ctx, copia, nome, de, ate, **filtros):
        chamadas.append((nome, filtros))
        return {"stats": {}}

    async def sem_lexpre(ctx, ufs):
        return None

    monkeypatch.setattr(m, "_rota", rota)
    monkeypatch.setattr(m, "resumo_lexpre", sem_lexpre)
    asyncio.run(m.build(_ctx("LA", extra={"laadv": object()}, uf_estrategico=["AM"])))
    nomes = [n for n, _ in chamadas]
    assert "comercial_LA" in nomes and "protocolo_LA" in nomes and "pendencia_LA" in nomes
    assert all(f == {} for n, f in chamadas if n != "estrategico_geral")
    juridico = [f for n, f in chamadas if n == "estrategico_geral"]
    assert juridico[0]["escritorio"] == ["Luis Albert AM"] and juridico[0]["uf"] is None


def test_comarca_traz_uf_e_valor_de_causa_para_o_mapa():
    # V2 em analyses/GERAL/estrategico_geral.py: a contagem da v1 não muda; ganha a UF mais comum e o valor.
    from app.analyses.GERAL.estrategico_geral import get_processos_juridico_por_comarca_geral

    linha = {"ID_FASE": None, "COMARCA": "MANAUS", "UF": "AM", "VALOR_DE_CAUSA": "1000,50"}
    from app.analyses.GERAL import estrategico_geral as eg

    fase = next(iter(eg._IDS_FASE_JURIDICO_GERAL))
    rows = [
        {**linha, "ID_FASE": fase},
        {**linha, "ID_FASE": fase, "VALOR_DE_CAUSA": 2000},
        {**linha, "ID_FASE": fase, "COMARCA": "BELÉM", "UF": "PA", "VALOR_DE_CAUSA": None},
        {**linha, "ID_FASE": fase, "COMARCA": ""},
    ]
    itens = {i["name"]: i for i in get_processos_juridico_por_comarca_geral(rows)}
    assert itens["MANAUS"]["value"] == 2.0 and itens["MANAUS"]["percent"] == 50.0
    assert itens["MANAUS"]["uf"] == "AM" and itens["MANAUS"]["valor_causa"] == 3000.5
    assert itens["BELÉM"]["uf"] == "PA" and itens["BELÉM"]["valor_causa"] == 0.0
    assert itens["Sem comarca"]["value"] == 1.0
