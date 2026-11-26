"""Marketing (banco NG): o relatório de Leads (banco NG + LexPre) e o do Facebook Ads (o do Marketing LexPre)."""

import asyncio
from datetime import date, datetime

import pytest

from app.dashboards import marketing as m
from app.dashboards import marketing_lexpre
from app.dashboards.base import DashboardContext, DashboardInputError, Period


def test_spec_dos_relatorios():
    assert list(m.MODULE.export.fields) == [
        "base",
        *marketing_lexpre.CAMPOS_EXPORT_MARKETING_LEXPRE,
    ]
    fb = m.MODULE.export_reports["facebook"]
    assert fb.fields == marketing_lexpre.MODULE.export_reports["facebook"].fields
    assert fb.rows is m.export_facebook


LEADS = [
    {
        "ID_ACTION": 1,
        "ENTRADA": datetime(2026, 9, 2, 10),
        "CLIENTE": "Ana",
        "ATENDENTE": "Bia",
        "UF": "AM",
        "CAMPANHA": "C1",
        "CANAL_ATUAL": "ANUNCIO_NG",
        "TIPO_TRAFEGO": "PAGO",
        "PROSPECCAO": "ATIVA",
        "ASSINADO_EM": datetime(2026, 9, 5),
        "MOTIVO_ENCERRAMENTO": 11,
    },
    {"ID_ACTION": 1, "ENTRADA": datetime(2026, 9, 2)},  # duplicada (join): sai uma vez
    {
        "ID_ACTION": 2,
        "ENTRADA": datetime(2026, 9, 3),
        "CLIENTE": "Caio",
        "CANAL_ATUAL": "INDICACAO",
        "data_encerramento": datetime(2026, 9, 4),
    },
]
PERFIS = [
    {
        "ID_ACTION": 1,
        "DATA_NASCIMENTO": date(1990, 1, 1),
        "GENERO": "FEMININO",
        "RESP_TRIAGEM?": True,
        "PLATAFORMA": "instagram",
    }
]
ANALISE = [
    {
        "ID_ACTION": 1,
        "ID_PROCESSO": 10,
        "RUBRICA": "ANP",
        "DANO_MORAL": "1000",
        "STATUS_PROTOCOLO": "PROTOCOLADO",
    },
    {
        "ID_ACTION": 1,
        "ID_PROCESSO": 11,
        "RUBRICA": "MORA",
        "VALOR_DA_CAUSA": 500,
        "STATUS_PROTOCOLO": "PENDENTE",
    },
]


def test_leads_do_banco_ng():
    linhas = m.linhas_leads_ng(LEADS, PERFIS, ANALISE, [])
    assert [r["id_action"] for r in linhas] == [1, 2]
    ana, caio = linhas
    assert ana["base"] == "Banco NG" and ana["assinado"] == "Sim" and ana["status"] == "Assinado"
    assert ana["data_entrada"] == date(2026, 9, 2) and ana["data_assinatura"] == date(2026, 9, 5)
    assert ana["canal_aquisicao"] == "ANUNCIO_NG" and ana["genero"] == "FEMININO"
    assert ana["triado"] == "Sim" and ana["faixa_etaria"] is not None
    assert ana["qtd_demandas"] == 2 and ana["rubricas"] == "ANP, MORA"
    assert ana["qtd_protocolados"] == 1 and ana["valor_causa_protocolado"] == 1000
    assert caio["assinado"] == "Não" and caio["status"] == "Encerrado" and caio["triado"] is None
    assert set(ana) == set(m.CAMPOS_LEADS)


def test_leads_seguem_os_filtros_da_pagina():
    so_indicacao = m.linhas_leads_ng(LEADS, PERFIS, ANALISE, [("canal_aquisicao", "INDICACAO")])
    assert [r["id_action"] for r in so_indicacao] == [2]
    por_rubrica = m.linhas_leads_ng(LEADS, PERFIS, ANALISE, [("rubrica", "MORA")])
    assert [r["id_action"] for r in por_rubrica] == [1]


def _ctx(**kw):
    return DashboardContext(
        source=object(),
        unit_ref="NG",
        period=Period(date(2026, 9, 1), date(2026, 9, 30)),
        filters={},
        can_see_commission=True,
        **kw,
    )


def test_facebook_sem_lexpre_avisa():
    with pytest.raises(DashboardInputError):
        asyncio.run(m.export_facebook(_ctx()))
