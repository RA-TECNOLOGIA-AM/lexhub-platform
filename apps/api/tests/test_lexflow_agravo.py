"""Agravos fora das queries do LexFlow (app/lexflow_agravo.py, regra da v1 de 06/11/2026)."""

import re

import pytest

from app.analyses.common.julgados_agravo import ORIGENS_AGRAVO
from app.lexflow_agravo import excluir_agravos, precisa_filtro, sql_nao_agravo
from app.source_queries import QUERIES

PREDICADO = sql_nao_agravo("numero_processo")


def test_toda_query_do_lexflow_que_le_processo_sai_sem_agravo():
    # Uma query nova do LexFlow entra no filtro sozinha; este teste pega se a injeção não acontecer.
    alvo = [n for n, c in QUERIES.items() if precisa_filtro(n, c)]
    assert len(alvo) >= 20
    for nome in alvo:
        assert "right(regexp_replace" in QUERIES[nome]["query"], nome


def test_agendamentos_e_outros_bancos_ficam_como_estao():
    for nome, cfg in QUERIES.items():
        if nome.startswith("agendamentos_") or cfg["database"] != "lexflow":
            assert "IN ('0000', '9000', '9001', '9002')" not in cfg["query"], nome


def test_mesmas_origens_do_helper_python():
    assert re.findall(r"'(\d{4})'", PREDICADO) == sorted(ORIGENS_AGRAVO)


def test_inner_join_vira_subselect_sem_agravo():
    sql = "SELECT p.id FROM public.processo p JOIN public.fase f ON f.id = p.id_fase WHERE p.id_situacao = 1"
    out = excluir_agravos("x", sql)
    assert f"FROM (SELECT * FROM public.processo WHERE {PREDICADO}) p" in out
    assert out.endswith("WHERE p.id_situacao = 1")


def test_join_sem_public_tambem_filtra():
    out = excluir_agravos("x", "select * from processo p where p.id = 1")
    assert f"from (SELECT * FROM public.processo WHERE {PREDICADO}) p" in out


def test_left_join_poe_o_filtro_no_where_e_mantem_linha_sem_processo():
    sql = "SELECT a.id FROM agendamento a LEFT JOIN public.processo p ON p.id = a.processo_id WHERE a.ativo"
    out = excluir_agravos("x", sql)
    assert "LEFT JOIN public.processo p" in out
    assert f"WHERE {sql_nao_agravo('p.numero_processo')}\n          AND a.ativo" in out


def test_publicacoes_usam_o_numero_proprio_da_publicacao():
    out = QUERIES["publicacoes_NG"]["query"]
    assert sql_nao_agravo("COALESCE(pro.numero_processo, p.numero_processo)") in out


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1 FROM x LEFT JOIN public.processo p ON true WHERE a = 1 OR b = 2",
        "SELECT 1 FROM x LEFT JOIN public.processo p ON true WHERE a = 1 ORDER BY 1",
        "SELECT 1 FROM x LEFT JOIN public.processo p ON true",
    ],
)
def test_left_join_em_formato_inseguro_para_com_erro(sql):
    with pytest.raises(AssertionError):
        excluir_agravos("x", sql)
