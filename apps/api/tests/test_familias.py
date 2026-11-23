"""Famílias unificadas (app/analyses/familias): cada unidade chama o código único com os próprios valores."""

import asyncio

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.common import memo
from app.analyses.LA import julgados_sentenca_LA as la
from app.analyses.NG import julgados_sentenca as ng
from app.analyses.RJ import julgados_sentenca_RJ as rj

LINHAS = [
    {"ID_ESCRITORIO": 20, "NUMERO_PROCESSO": "0001234-11.2025.8.04.0001"},
    {"ID_ESCRITORIO": 21, "NUMERO_PROCESSO": "0001235-11.2025.8.04.0001"},
    {"ID_ESCRITORIO": 27, "NUMERO_PROCESSO": "0001236-11.2025.8.04.0001"},
]


def test_cada_unidade_usa_o_proprio_escritorio():
    assert ng._base_julgados_NG(LINHAS) == [LINHAS[0]]
    assert la._base_julgados_LA(LINHAS) == [LINHAS[1]]
    assert rj._base_julgados_RJ(LINHAS) == [LINHAS[2]]
    # fora da chamada de uma unidade, a família volta ao padrão (NG)
    assert ng._base_julgados_NG(LINHAS) == [LINHAS[0]]


def test_cache_por_pedido_separa_as_unidades():
    async def pedido():
        return (
            la._base_julgados_LA(LINHAS),
            ng._base_julgados_NG(LINHAS),
            la._base_julgados_LA(LINHAS),
        )

    a, b, c = asyncio.run(memo.no_pedido(pedido()))
    assert a == c == [LINHAS[1]]
    assert b == [LINHAS[0]]


def test_nomes_de_hoje_continuam_existindo():
    assert callable(la.get_kpis_sentenca_julgados_LA)
    assert la.JulgadosSentencaFiltrosLA is ng.JulgadosSentencaFiltros


def test_catalogo_do_recursal_e_de_cada_unidade():
    from app.analyses.LA import recurso_LA as rla
    from app.analyses.NG import recurso_NG as rng_

    try:
        rng_.set_atividades_recursos_NG_catalogo([{"id_atividade": 1, "ATIVIDADE": "SÓ NA NG"}])
        rla.set_atividades_recursos_LA_catalogo([{"id_atividade": 2, "ATIVIDADE": "SÓ NA LA"}])
        assert rng_._agendamento_atividade_recursos_valida({"ATIVIDADE": "SÓ NA NG"})
        assert not rng_._agendamento_atividade_recursos_valida({"ATIVIDADE": "SÓ NA LA"})
        assert rla._agendamento_atividade_recursos_valida({"ATIVIDADE": "SÓ NA LA"})
        assert not rla._agendamento_atividade_recursos_valida({"ATIVIDADE": "SÓ NA NG"})
    finally:
        rng_.set_atividades_recursos_NG_catalogo([])
        rla.set_atividades_recursos_LA_catalogo([])
