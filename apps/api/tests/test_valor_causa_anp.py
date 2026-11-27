"""Regra de todo valor de causa: matéria ANP soma o DANO_MORAL, não o VALOR_CAUSA.

Cada caso tem uma demanda ANP (valor da causa 10.000, dano moral 3.000) e uma comum (1.000):
o certo é 4.000. Antes destes testes, os cálculos abaixo somavam 11.000.
"""

from datetime import date

from app.analyses.LA import protocolo_LA
from app.analyses.NG import (
    comercial_lexpre,
    comissao_lexpre,
    marketing_lexpre,
    protocolo,
    protocolo_lexpre,
)

# LexPre (query comercial_lexpre_NG: a matéria vem em RUBRICA)
_LEXPRE = {
    "STATUS_ID": protocolo_lexpre.STATUS_ASSINADO_ID,
    "DATA_ASSINATURA": date(2026, 3, 1),
    "STATUS_DEMANDA_ID": protocolo_lexpre.STATUS_AG_DESPACHO_INICIAL_ID,
    "DATA_PROTOCOLO": date(2026, 3, 10),
    "ATENDENTE": "Ana Souza",
    "UF": "PB",
}
LEXPRE = [
    {**_LEXPRE, "ID_DEMANDA": 1, "RUBRICA": "ANP", "VALOR_CAUSA": 10_000, "DANO_MORAL": 3_000},
    {**_LEXPRE, "ID_DEMANDA": 2, "RUBRICA": "MORA", "VALOR_CAUSA": 1_000, "DANO_MORAL": 500},
]

# Legado (banco ng / laadv: a matéria vem em MATERIA)
LEGADO_NG = [
    {
        "STATUS": "NÃO PROTOCOLADO",
        "REAJUIZAMENTO": False,
        "ATENDENTE": "Ana Souza",
        "MATERIA": "ANP",
        "VALOR_DA_CAUSA": 10_000,
        "DANO_MORAL": 3_000,
    },
    {
        "STATUS": "NÃO PROTOCOLADO",
        "REAJUIZAMENTO": False,
        "ATENDENTE": "Ana Souza",
        "MATERIA": "MORA",
        "VALOR_DA_CAUSA": 1_000,
        "DANO_MORAL": 500,
    },
]
LEGADO_LA = [{**p, "STATUS": "PROTOCOLO"} for p in LEGADO_NG]


def test_comercial_meta_anual():
    assert comercial_lexpre.get_valor_causa_protocolado(LEXPRE, ano=2026) == 4_000
    # mesma base do card do Protocolo LexPre
    assert (
        protocolo_lexpre.get_valor_causa_protocolado(LEXPRE, date(2026, 1, 1), date(2026, 12, 31))
        == 4_000
    )


def test_lexpre_por_atendente_protocolado_e_nao_protocolado():
    assert protocolo_lexpre.get_valor_causa_protocolado_por_atendente(LEXPRE) == {"Ana": 4_000}
    represados = [
        {**r, "DATA_PROTOCOLO": None, "SETOR_ID": next(iter(protocolo_lexpre.SETOR_PROTOCOLO_IDS))}
        for r in LEXPRE
    ]
    (linha,) = protocolo_lexpre.get_valor_causa_por_atendente(represados)
    assert linha["nao_protocolado"] == 4_000


def test_comissao_valor_por_estado():
    assert comissao_lexpre._get_valor_por_estado(LEXPRE, {"PB"}) == 4_000


def test_marketing_valor_protocolado():
    assert marketing_lexpre._valor_causa_protocolado(LEXPRE, None, None) == 4_000


def test_legado_ng_nao_protocolado():
    assert protocolo.get_valor_causa_protocolo_nao_protocolado(LEGADO_NG) == 4_000
    assert protocolo.get_valor_causa_protocolo_nao_protocolado_por_atendente(LEGADO_NG) == {
        "Ana": 4_000
    }


def test_legado_la_nao_protocolado_por_atendente():
    assert protocolo_LA.get_valor_causa_nao_protocolado_por_atendente_LA(LEGADO_LA) == {
        "ANA": 4_000
    }
