"""Execução Estratégico Geral: o "Relatório" da página da v1 (Condenação, Acordos ou os dois num arquivo só)."""

import csv
import io
import zipfile

import pytest
from openpyxl import load_workbook

from app.dashboards import DASHBOARDS
from app.dashboards import execucao_export as linhas
from conftest import USER_ID

URL = "/orgs/lexgroup/units/NG/dashboards/execucao-estrategico/export"
PERIODO = {"from": "2026-11-01", "to": "2026-11-17"}
FILTROS = {
    "materia": "ANP",
    "uf": "AM",
    "comarca": "MANAUS",
    "ano_ajuizamento": "2024",
    "subfase": "S1",
}


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


@pytest.fixture
def chamadas(repo, monkeypatch):
    """A unidade NG ligada no LexFlow, quem exporta, e as funções de linhas da v1 trocadas por falsas."""
    feitas: dict[str, list] = {"condenacao": [], "acordos": []}

    async def condenacao(*args, **kwargs):
        feitas["condenacao"].append((args, kwargs))
        return [{"NUMERO_PROCESSO": "C1", "UF": "AM"}]

    async def acordos(*args, **kwargs):
        feitas["acordos"].append((args, kwargs))
        return [{"NUMERO_PROCESSO": "A1"}, {"NUMERO_PROCESSO": "A2"}]

    monkeypatch.setitem(linhas.LINHAS_EXECUCAO, "NG", condenacao)
    monkeypatch.setitem(linhas.LINHAS_ACORDOS, "NG", acordos)
    repo.grant(USER_ID, "NG", "execucao-estrategico", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexflow")] = "NG"
    repo.exporters.add(USER_ID)
    return feitas


def test_tres_relatorios_com_origem_e_recorte():
    m = DASHBOARDS["execucao-estrategico"]
    assert m.export.title == "Condenação"
    assert set(m.export_reports) == {"acordos", "ambos"}
    for spec in (m.export, *m.export_reports.values()):
        assert [o.key for o in spec.options] == ["origem", "criterio"]
        assert list(spec.options[0].choices) == ["pagina", "personalizado"]
    # Os mesmos campos e rótulos da Execução Condenação e da Execução Acordos.
    assert m.export.labels == DASHBOARDS["execucao"].export.labels
    assert m.export_reports["acordos"].labels == DASHBOARDS["acordos"].export.labels
    ambos = m.export_reports["ambos"]
    assert [p.prefix for p in ambos.parts] == ["condenacao", "acordos"]
    assert ambos.labels["condenacao.numero_processo"] == m.export.labels["numero_processo"]


def test_condenacao_com_os_filtros_da_pagina(client, signer, chamadas):
    params = {**PERIODO, **FILTROS, "criterio": "saida", "campos": ["numero_processo"]}
    r = client.get(URL, params=params, headers=auth(signer))
    assert r.status_code == 200, r.text
    args, kwargs = chamadas["condenacao"][0]
    # materia, subfase, ano (como export_execucao da v1), o recorte, UF e comarca
    assert args[2:] == (["ANP"], ["S1"], "2024")
    assert kwargs == {"criterio": "saida", "uf": ["AM"], "comarca": ["MANAUS"]}
    assert list(csv.reader(io.StringIO(r.content.decode("utf-8-sig")))) == [
        ["Número do Processo"],
        ["C1"],
    ]
    assert "execucao_estrategico_NG_pagina_saida_relatorio.csv" in r.headers["content-disposition"]


def test_personalizado_ignora_os_filtros_da_pagina(client, signer, chamadas):
    params = {**PERIODO, **FILTROS, "origem": "personalizado", "relatorio": "acordos"}
    assert client.get(URL, params=params, headers=auth(signer)).status_code == 200
    args, kwargs = chamadas["acordos"][0]
    assert args[2:] == (None, None, None, None)  # matéria, subfase, tipo de ação, UF
    assert kwargs == {
        "criterio": "entrada",
        "comarca": None,
        "ano_ajuizamento_execucao_acordos": None,
    }


def test_os_dois_juntos_em_xlsx_uma_aba_de_cada(client, signer, chamadas):
    campos = ["condenacao.numero_processo", "condenacao.uf", "acordos.numero_processo"]
    params = {**PERIODO, "relatorio": "ambos", "format": "xlsx", "campos": campos}
    r = client.get(URL, params=params, headers=auth(signer))
    assert r.status_code == 200, r.text
    wb = load_workbook(io.BytesIO(r.content))
    assert wb.sheetnames == ["Execução Condenação", "Execução Acordos"]
    assert [[c.value for c in row] for row in wb["Execução Condenação"].iter_rows()] == [
        ["Número do Processo", "UF"],
        ["C1", "AM"],
    ]
    assert [row[0].value for row in wb["Execução Acordos"].iter_rows()] == [
        "Número do Processo",
        "A1",
        "A2",
    ]


def test_os_dois_juntos_em_csv_num_zip(client, signer, chamadas):
    params = {**PERIODO, "relatorio": "ambos", "format": "csv"}
    r = client.get(URL, params=params, headers=auth(signer))
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    assert (
        "execucao_estrategico_NG_ambos_pagina_entrada_relatorio.zip"
        in r.headers["content-disposition"]
    )
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.namelist() == ["execucao_condenacao.csv", "execucao_acordos.csv"]


def test_lado_sem_campo_fica_de_fora(client, signer, chamadas):
    params = {
        **PERIODO,
        "relatorio": "ambos",
        "format": "xlsx",
        "campos": ["acordos.numero_processo"],
    }
    r = client.get(URL, params=params, headers=auth(signer))
    assert r.status_code == 200, r.text
    assert load_workbook(io.BytesIO(r.content)).sheetnames == ["Execução Acordos"]
    assert chamadas["condenacao"] == []  # nem busca a Condenação


def test_campo_sem_prefixo_no_relatorio_dos_dois_400(client, signer, chamadas):
    params = {**PERIODO, "relatorio": "ambos", "campos": ["numero_processo"]}
    assert client.get(URL, params=params, headers=auth(signer)).status_code == 400
