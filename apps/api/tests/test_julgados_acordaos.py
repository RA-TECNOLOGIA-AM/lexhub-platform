"""Julgados Acórdãos (LexFlow): o cálculo da v1 na casca da V2, por unidade, e a exportação."""

import csv
import io
from datetime import date

import pytest

from app.analyses.common import matriz_julgamento as mj
from app.dashboards import DASHBOARDS
from conftest import USER_ID

KEY = "julgados-acordaos"
URL = f"/orgs/lexgroup/units/NG/dashboards/{KEY}"
PERIODO = "from=2026-11-01&to=2026-11-30"
ESCRITORIO = {"NG": 20, "LA": 21, "RJ": 27}


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def acordao(escritorio: int, numero: str, merito: int, data: date, **extra) -> dict:
    """Uma linha da query `julgados` com o que o cálculo de acórdãos lê."""
    return {
        "ID_ESCRITORIO": escritorio,
        "ID_SITUACAO": 1,
        "NUMERO_PROCESSO": numero,
        "ID_ACORDAO_MERITO_2G": merito,
        "DATA_ACORDAO": data,
        "DATA_AJUIZAMENTO": date(2024, 3, 10),
        "RELATOR_2G": "Des. Fulano de Tal",
        "MATERIA": "ANP",
        "COMPETENCIA": "Cível",
        "COMARCA": "Manaus",
        "UF": "AM",
        "VALOR_ACORDAO": 1234.5,
        "VALOR_CAUSA_ACORDO": 1234.5,
        **extra,
    }


def ligar(repo, sources, unidade: str = "NG", linhas: list | None = None, exportar: bool = False):
    """A unidade NG do repo falso, ligada no LexFlow como `unidade` (NG, LA ou RJ)."""
    repo.grant(USER_ID, "NG", KEY, "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexflow")] = unidade
    sources.data["julgados"] = linhas or []
    if exportar:
        repo.exporters.add(USER_ID)


def test_modulo_le_so_a_query_julgados_e_exporta():
    module = DASHBOARDS[KEY]
    assert module.source_db == "lexflow"
    assert module.queries == ("julgados",)
    assert module.export is not None
    assert list(module.export.fields) == list(module.export.labels)
    # Filtros da rota da v1 (listas de texto) + situação do processo.
    assert module.filters["materia_julgados"] is str
    assert module.filters["resultado_embargos_julgados"] is str
    assert "situacao_processo" in module.filters


@pytest.mark.parametrize("unidade", ["NG", "LA", "RJ"])
def test_cada_unidade_roda_a_rota_da_v1_dela(client, signer, repo, sources, unidade):
    ligar(repo, sources, unidade)
    r = client.get(f"{URL}?{PERIODO}", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == "LexFlow"
    assert body["dashboard"] == f"julgados_acordaos_{unidade}"
    assert f"julgados_acordao_total_{unidade}" in body["stats"]
    assert sources.last.db_name == "lexflow"


def test_conta_so_os_acordaos_do_escritorio_no_periodo(client, signer, repo, sources):
    linhas = [
        acordao(20, "0001", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 11, 5)),
        acordao(20, "0002", mj.ID_MERITO_IMPROCEDENTE, date(2026, 11, 20)),
        acordao(20, "0003", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 9, 1)),  # fora do período
        acordao(21, "0004", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 11, 6)),  # LA
    ]
    ligar(repo, sources, "NG", linhas)
    stats = client.get(f"{URL}?{PERIODO}", headers=auth(signer)).json()["stats"]
    assert stats["julgados_acordao_total_NG"] == 2
    assert stats["julgados_acordao_procedentes_NG"] == 1
    assert stats["julgados_acordao_improcedentes_NG"] == 1


def test_mes_a_mes_vem_do_historico_e_materia_das_duas_chamadas(client, signer, repo, sources):
    """Como a página da v1, que buscava a rota de novo sem período."""
    linhas = [
        acordao(20, "0001", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 11, 5)),
        acordao(20, "0003", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2025, 2, 1), MATERIA="MORA"),
    ]
    ligar(repo, sources, "NG", linhas)
    body = client.get(f"{URL}?{PERIODO}", headers=auth(signer)).json()
    por_mes = body["julgados_acordao_procedentes_por_mes_NG"]
    assert sum(p["value"] for p in por_mes) == 2  # o acórdão de 2025 também conta
    periodo = {p["name"] for p in body["julgados_acordao_por_materia_NG"]}
    historico = {p["name"] for p in body["historico_julgados_acordao_por_materia_NG"]}
    assert periodo == {"ANP"}
    assert historico == {"ANP", "MORA"}


def test_unidade_sem_versao_na_v1_501(client, signer, repo, sources):
    ligar(repo, sources, "XX")
    assert client.get(URL, headers=auth(signer)).status_code == 501


def test_situacao_invalida_422(client, signer, repo, sources):
    ligar(repo, sources)
    r = client.get(f"{URL}?situacao_processo=XYZ", headers=auth(signer))
    assert r.status_code == 422


# --- Exportação ------------------------------------------------------------------------------


def read_csv(r) -> list[list[str]]:
    return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))


@pytest.mark.parametrize("unidade", ["NG", "LA", "RJ"])
def test_exporta_os_acordaos_do_periodo_como_a_v1(client, signer, repo, sources, unidade):
    linhas = [
        acordao(ESCRITORIO[unidade], "0001", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 11, 5)),
        acordao(ESCRITORIO[unidade], "0002", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 9, 1)),
    ]
    ligar(repo, sources, unidade, linhas, exportar=True)
    campos = "campos=numero_processo&campos=data_acordao&campos=valor_acordao"
    r = client.get(f"{URL}/export?{PERIODO}&{campos}", headers=auth(signer))
    assert r.status_code == 200, r.text
    assert read_csv(r) == [
        ["Número do Processo", "Data do Acórdão", "Valor do Acórdão"],
        ["0001", "05/11/2026", "R$ 1.234,50"],
    ]


def test_exportacao_respeita_os_filtros_da_pagina(client, signer, repo, sources):
    linhas = [
        acordao(20, "0001", mj.ID_MERITO_PROCEDENTE_COM_PE, date(2026, 11, 5)),
        acordao(20, "0002", mj.ID_MERITO_IMPROCEDENTE, date(2026, 11, 6)),
    ]
    ligar(repo, sources, "NG", linhas, exportar=True)
    url = f"{URL}/export?{PERIODO}&campos=numero_processo&categoria_julgados=improcedente"
    assert read_csv(client.get(url, headers=auth(signer))) == [["Número do Processo"], ["0002"]]
