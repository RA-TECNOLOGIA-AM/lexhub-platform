import csv
import io
from datetime import date

import pytest
from openpyxl import load_workbook

from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardModule, ExportSpec
from app.dashboards.export import format_value
from conftest import USER_ID

URL = "/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre/export"

FIELDS = {"id_demanda": "ID_DEMANDA", "materia": "MATERIA", "data_entrada": "DATA_ENTRADA"}
LABELS = {"id_demanda": "ID da Demanda", "materia": "Matéria", "data_entrada": "Data de Entrada"}
ROWS = [
    {"ID_DEMANDA": 10, "MATERIA": "ANP", "DATA_ENTRADA": date(2026, 11, 3)},
    {"ID_DEMANDA": 11, "MATERIA": "MORA", "DATA_ENTRADA": None},
]


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


@pytest.fixture
def module(monkeypatch):
    """Módulo falso com exportação: devolve ROWS e guarda o contexto recebido."""
    seen = {}

    async def rows(ctx):
        seen["ctx"] = ctx
        return ROWS

    async def build(ctx):
        return {}

    fake = DashboardModule(
        key="protocolo-lexpre",
        source_db="lexpre",
        source_label="LexPre",
        build=build,
        filters={"materia": str},
        export=ExportSpec(fields=FIELDS, labels=LABELS, sheet_name="Protocolo (LexPre)", rows=rows),
    )
    monkeypatch.setitem(DASHBOARDS, "protocolo-lexpre", fake)
    return seen


@pytest.fixture
def ready(repo, sources):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")
    repo.exporters.add(USER_ID)
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"


def read_csv(r) -> list[list[str]]:
    return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))


def test_csv_com_os_cabecalhos_e_valores_da_v1(client, signer, module, ready):
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert (
        r.headers["content-disposition"]
        == 'attachment; filename="protocolo_lexpre_NG_relatorio.csv"'
    )
    assert r.content.startswith(b"\xef\xbb\xbf")  # BOM: o Excel abre com acento certo
    assert read_csv(r) == [
        ["ID da Demanda", "Matéria", "Data de Entrada"],
        ["10", "ANP", "03/11/2026"],
        ["11", "MORA", ""],
    ]


def test_campos_na_ordem_pedida(client, signer, module, ready):
    r = client.get(URL + "?campos=materia&campos=id_demanda", headers=auth(signer))
    assert read_csv(r)[0] == ["Matéria", "ID da Demanda"]


def test_xlsx(client, signer, module, ready):
    r = client.get(URL + "?format=xlsx", headers=auth(signer))
    assert r.status_code == 200
    assert r.headers["content-disposition"].endswith('protocolo_lexpre_NG_relatorio.xlsx"')
    ws = load_workbook(io.BytesIO(r.content)).active
    assert ws.title == "Protocolo (LexPre)"
    assert [c.value for c in ws[1]] == ["ID da Demanda", "Matéria", "Data de Entrada"]
    assert [c.value for c in ws[2]] == ["10", "ANP", "03/11/2026"]


def test_periodo_e_filtros_chegam_ao_modulo(client, signer, module, ready):
    client.get(URL + "?from=2026-10-01&to=2026-10-31&materia=ANP", headers=auth(signer))
    ctx = module["ctx"]
    assert (ctx.period.start, ctx.period.end) == (date(2026, 10, 1), date(2026, 10, 31))
    assert ctx.filters == {"materia": ["ANP"]}


def test_toda_exportacao_vai_para_a_auditoria(client, signer, module, ready, repo):
    client.get(
        URL + "?format=xlsx&campos=id_demanda&materia=ANP",
        headers={**auth(signer), "User-Agent": "pytest"},
    )
    a = repo.audits[0]
    assert a.action == "dashboard.export"
    assert a.actor_user_id == USER_ID
    assert a.target_id == "protocolo-lexpre"
    assert a.metadata == {
        "org": "lexgroup",
        "unit": "NG",
        "from": "2026-11-01",
        "to": "2026-11-11",
        "filters": {"materia": ["ANP"]},
        "campos": ["id_demanda"],
        "format": "xlsx",
        "rows": 2,
    }


def test_sem_permissao_de_exportar_403_auditado(client, signer, module, ready, repo):
    repo.exporters.clear()
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem permissão para exportar"}
    assert repo.audits[0].metadata["reason"] == "sem_permissao_exportar"
    assert "ctx" not in module  # nem chega a buscar os dados


def test_formato_desconhecido_400(client, signer, module, ready):
    r = client.get(URL + "?format=pdf", headers=auth(signer))
    assert r.status_code == 400
    assert r.json() == {"detail": "Formato inválido. Use csv ou xlsx."}


def test_campo_desconhecido_400(client, signer, module, ready):
    r = client.get(URL + "?campos=id_demanda&campos=senha", headers=auth(signer))
    assert r.status_code == 400
    assert r.json() == {"detail": "Campo desconhecido: senha"}


def test_sem_acesso_a_unidade_403(client, signer, module, repo):
    repo.exporters.add(USER_ID)
    assert client.get(URL, headers=auth(signer)).status_code == 403


def test_escopo_own_403(client, signer, module, ready, repo):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "own")
    assert client.get(URL, headers=auth(signer)).status_code == 403


def test_protocolo_real_exporta_as_linhas_da_v1(client, signer, ready, sources):
    from test_dashboard_data import LOG_ROWS

    sources.data["log_setor_demanda_lexpre_NG"] = LOG_ROWS
    r = client.get(URL + "?campos=id_demanda&campos=materia", headers=auth(signer))
    assert r.status_code == 200
    assert read_csv(r) == [["ID da Demanda", "Matéria"], ["1", "ANP"]]


def test_formatacao_igual_a_v1():
    assert format_value(None) == ""
    assert format_value(True) == "Sim"
    assert format_value(False) == "Não"
    assert format_value(date(2026, 1, 2)) == "02/01/2026"
    assert format_value(1234.5) == "1234.5"


# --- Pendências (LexPre) ---------------------------------------------------


def test_pendencias_lexpre_ligada_ao_calculo_da_v1(client, signer, repo, sources):
    repo.grant(USER_ID, "NG", "pendencias-lexpre", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    sources.data["log_setor_demanda_lexpre_NG"] = []
    sources.data["setor_func_lexpre_NG"] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/pendencias-lexpre", headers=auth(signer))
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["pendencias_total"] == 0
    assert set(body["opcoes_filtro"]) == {"funcionarios", "ufs", "areas"}  # v1 sem matéria


def test_mapas_de_exportacao_iguais_ao_front():
    """Os slugs do servidor são os mesmos que o front oferece (pages/dashboards/*/exportFields.ts)."""
    protocolo = DASHBOARDS["protocolo-lexpre"].export
    pendencias = DASHBOARDS["pendencias-lexpre"].export
    assert list(protocolo.fields) == list(protocolo.labels)
    assert list(pendencias.fields) == list(pendencias.labels)
    assert set(pendencias.fields) - set(protocolo.fields) == {"origem"}
