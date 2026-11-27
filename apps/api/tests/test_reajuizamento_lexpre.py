"""Reajuizamento do LexPre: fora de todo total e comissão, visível em cards próprios dos setores.

As linhas de reajuizamento chegam pela query própria (log_setor_demanda_lexpre_reajuizamento_NG); a principal
(log_setor_demanda_lexpre_NG) já vem sem elas do banco. Ver app/dashboards/reajuizamento_lexpre.py.
"""

from datetime import datetime

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards.reajuizamento_lexpre import QUERY_REAJUIZAMENTO
from app.source_queries import QUERIES
from conftest import USER_ID


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def log_row(**overrides):
    row = {
        "ESCRITORIO_ID": 1,
        "ID_DEMANDA": 1,
        "MATERIA": "MORA",
        "UF": "AM",
        "AREA_ATUACAO_ID": 3,
        "AREA_ATUACAO_NOME": "CONSUMIDOR",
        "FUNCIONARIO": "Ana Souza",
        "STATUS_DEMANDA_ID": 13,  # Aguardando Despacho Inicial = protocolada
        "SETOR_ATUAL_ID": 99,
        "VALOR_CAUSA": 1000,
        "REAJUIZAMENTO": False,
    }
    return {**row, **overrides}


def protocolada(demanda, *, reaj=False):
    """Demanda que entrou e saiu do Protocolo (setor 5) em novembro."""
    return [
        log_row(
            TIPO="entrada",
            SETOR_ID=5,
            MOVIMENTACAO_ID=demanda * 10,
            ID_DEMANDA=demanda,
            DATA=datetime(2026, 11, 2, 9),
            REAJUIZAMENTO=reaj,
        ),
        log_row(
            TIPO="saida",
            SETOR_ID=5,
            MOVIMENTACAO_ID=demanda * 10 + 1,
            ID_DEMANDA=demanda,
            DATA=datetime(2026, 11, 5, 15),
            REAJUIZAMENTO=reaj,
        ),
    ]


def represada(demanda, *, reaj=False):
    """Demanda parada no Protocolo agora."""
    return [
        log_row(
            TIPO="entrada",
            SETOR_ID=5,
            SETOR_ATUAL_ID=5,
            STATUS_DEMANDA_ID=1,
            MOVIMENTACAO_ID=demanda * 10,
            ID_DEMANDA=demanda,
            DATA=datetime(2026, 11, 3, 9),
            REAJUIZAMENTO=reaj,
        ),
    ]


@pytest.fixture
def protocolo(repo, sources):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    repo.commission.add(USER_ID)
    # 2 normais protocoladas + 1 normal represada; 1 reajuizamento protocolado + 2 represados
    sources.data["log_setor_demanda_lexpre_NG"] = [*protocolada(1), *protocolada(2), *represada(3)]
    sources.data[QUERY_REAJUIZAMENTO] = [
        *protocolada(101, reaj=True),
        *represada(102, reaj=True),
        *represada(103, reaj=True),
    ]


URL = "/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre?from=2026-11-01&to=2026-11-30"


def test_protocolo_reajuizamento_em_cards_proprios(client, signer, protocolo):
    body = client.get(URL, headers=auth(signer)).json()
    s = body["stats"]
    # totais só com as normais
    assert s["protocolados_total"]["total"] == 2
    assert s["represados"] == 1
    assert s["valor_causa_protocolado"]["total"] == 2000
    # reajuizamento visível, à parte
    assert s["protocolados_de_reajuizamento"] == 1
    assert s["represados_de_reajuizamento"] == 2


def test_protocolo_comissao_sem_reajuizamento(client, signer, protocolo):
    body = client.get(URL, headers=auth(signer)).json()
    linhas = body["comissionamento_por_funcionario"]
    assert sum(r["qtd_protocolados"] for r in linhas) == 2  # o reajuizamento protocolado não conta


def test_sem_reajuizamento_os_cards_ficam_zerados(client, signer, protocolo, sources):
    sources.data[QUERY_REAJUIZAMENTO] = []
    s = client.get(URL, headers=auth(signer)).json()["stats"]
    assert (s["protocolados_de_reajuizamento"], s["represados_de_reajuizamento"]) == (0, 0)
    assert s["protocolados_total"]["total"] == 2


@pytest.mark.parametrize(
    "key,campos",
    [
        ("protocolo-lexpre", ("protocolados_de_reajuizamento", "represados_de_reajuizamento")),
        ("peticionamento-lexpre", ("peticionados_de_reajuizamento", "represados_de_reajuizamento")),
        ("org-documentos-lexpre", ("resolvidos_de_reajuizamento", "represados_de_reajuizamento")),
        (
            "pendencias-lexpre",
            ("pendencias_nao_resolvidas_reajuizamento", "pendencias_resolvidas_reajuizamento"),
        ),
    ],
)
def test_todo_setor_lexpre_traz_os_cards_de_reajuizamento(
    client, signer, repo, sources, key, campos
):
    repo.grant(USER_ID, "NG", key, "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    for q in DASHBOARDS[key].queries:
        sources.data[q] = []
    assert QUERY_REAJUIZAMENTO in DASHBOARDS[key].queries
    r = client.get(f"/orgs/lexgroup/units/NG/dashboards/{key}", headers=auth(signer))
    assert r.status_code == 200, r.text
    for campo in campos:
        assert r.json()["stats"][campo] == 0


def test_sql_separa_reajuizamento():
    """A principal exclui, a de reajuizamento só tem eles; Comercial e cancelamentos também excluem."""
    principal = QUERIES["log_setor_demanda_lexpre_NG"]["query"]
    reaj = QUERIES[QUERY_REAJUIZAMENTO]["query"]
    assert "WHERE NOT coalesce(d.reajuizamento, false)" in principal
    assert "WHERE d.reajuizamento" in reaj and "WHERE NOT" not in reaj
    assert reaj.replace("WHERE d.reajuizamento", "") == principal.replace(
        "WHERE NOT coalesce(d.reajuizamento, false)", ""
    )
    assert "AND NOT coalesce(d.reajuizamento, false)" in QUERIES["comercial_lexpre_NG"]["query"]
    assert (
        "AND NOT coalesce(d.reajuizamento, false)"
        in QUERIES["audit_log_demandas_canceladas_lexpre_NG"]["query"]
    )
