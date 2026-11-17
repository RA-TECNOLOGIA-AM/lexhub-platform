"""Financeiro Estratégico (Financeiro): o cálculo da v1 sobre a planilha do financeiro + o valor ajuizado do
LexFlow, numa resposta só (reflexo, conversão, previsão e clientes pendentes)."""

from datetime import date

from conftest import USER_ID

URL = "/orgs/lexgroup/units/NG/dashboards/financeiro-estrategico"


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def repasse(ted: str, ajuizamento: str | None, hono: float, **extra) -> dict:
    """Uma linha da aba REPASSES CLIENTES (as colunas que o cálculo usa)."""
    return {
        "DATA DO TED": ted,
        "DATA AJUIZAMENTO": ajuizamento,
        "HONO": hono,
        "SUCUMBÊNCIA": 0,
        "MATÉRIA": "CESTA",
        "ORIGEM": "CONDENAÇÃO",
        "STATUS": "PAGO",
        "REPASSE DE CLIENTE": 0,
        "VALOR DA CAUSA": 10_000,
        **extra,
    }


def _pronto(repo, sources):
    repo.grant(USER_ID, "NG", "financeiro-estrategico", "all")
    unidade = repo.units[("lexgroup", "NG")]
    repo.unit_refs[(unidade, "sheets_financeiro_ng")] = "NG"
    repo.unit_refs[(unidade, "lexflow")] = "NG"
    sources.data["REPASSES CLIENTES"] = [
        repasse("2026-11-05", "2025-03-10", 1_000),  # no período (novembro), ajuizado em 2025
        repasse("2026-10-05", "2024-06-01", 500),  # outubro: o mês anterior
        repasse(
            "2025-02-01", "2024-01-01", 300, STATUS="SEM CONTATO", **{"REPASSE DE CLIENTE": 700}
        ),
    ]
    sources.data["valor_causa_ajuizado_lexflow_NG"] = [
        {
            "DATA_AJUIZAMENTO": date(2026, 11, 3),
            "MATERIA": "CESTA",
            "QUANTIDADE": 2,
            "VALOR_CAUSA": 50_000,
        },
        {
            "DATA_AJUIZAMENTO": date(2025, 3, 10),
            "MATERIA": "MORA",
            "QUANTIDADE": 4,
            "VALOR_CAUSA": 100_000,
        },
    ]


def test_le_a_planilha_e_o_lexflow_e_monta_as_quatro_partes(client, signer, repo, sources):
    _pronto(repo, sources)
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == "Planilha do financeiro + LexFlow"
    assert body["escritorio"] == "NG"
    reflexo = body["reflexo_financeiro"]
    assert (
        reflexo["total_entradas"]["valor"] == 1
    )  # só o TED de novembro (período padrão: 01 a 11/11)
    assert reflexo["valor_receita"]["valor"] == 1_000
    # LexFlow: só o distribuído no período (03/11), não muda com os filtros da planilha
    assert reflexo["valor_protocolado"]["valor"] == 50_000
    assert reflexo["valor_protocolado"]["quantidade"] == 2
    assert reflexo["clientes_pendentes"]["valor"] == 700  # status pendente, sem o período
    assert body["conversao"]["receita"] == 1_800  # todas as linhas (sem ano marcado)
    assert body["conversao"]["valor_causa_ajuizado"]["valor"] == 150_000
    assert "cenarios" in body["previsao"]
    assert body["clientes_pendentes"]["valor_fixo"] == 700


def test_conversao_usa_os_proprios_seletores_de_ano(client, signer, repo, sources):
    _pronto(repo, sources)
    r = client.get(URL + "?conv_ano_ajuizamento=2025", headers=auth(signer))
    assert r.status_code == 200, r.text
    conv = r.json()["conversao"]
    assert conv["receita"] == 1_000  # só a linha ajuizada em 2025
    assert conv["valor_causa_ajuizado"]["valor"] == 100_000  # LexFlow de 2025
    assert conv["percentual_conversao"] == 1.0
    # o seletor da Conversão não mexe no reflexo da página
    assert r.json()["reflexo_financeiro"]["valor_receita"]["valor"] == 1_000


def test_sem_lexflow_ligado_503(client, signer, repo, sources):
    _pronto(repo, sources)
    del repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexflow")]
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 503
