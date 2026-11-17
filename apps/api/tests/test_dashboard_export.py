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


def _linha_comercial(id_action, assinatura, **extra):
    return {
        "ESCRITORIO_ID": 1,
        "ID_ACTION": id_action,
        "ID_DEMANDA": id_action,
        "CLIENTE": f"Cliente {id_action}",
        "ATENDENTE": "Ana Souza",
        "STATUS_ID": 6,  # assinado
        "DATA_ASSINATURA": assinatura,
        "RUBRICA": "MORA",
        "VALOR_AM": 120.0,
        **extra,
    }


def test_comercial_lexpre_exporta_as_colunas_da_query_como_a_v1(client, signer, repo, sources):
    """Assinadas no período, rubrica reunida vira uma linha por componente (com o valor dele)."""
    repo.grant(USER_ID, "NG", "comercial-lexpre", "all")
    repo.exporters.add(USER_ID)
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    sources.data["comercial_lexpre_NG"] = [
        _linha_comercial(1, date(2026, 10, 5)),
        _linha_comercial(2, date(2026, 10, 6), RUBRICA="RUBRICAS_BRADESCO", RUBRICA_REUNIDA=True),
        _linha_comercial(3, date(2026, 9, 30)),  # fora do período
        _linha_comercial(4, date(2026, 10, 7), STATUS_ID=1),  # não assinou
        _linha_comercial(5, date(2026, 10, 8), ESCRITORIO_ID=2),  # outro escritório
    ]
    sources.data["demanda_rubrica_reunida_lexpre_NG"] = [
        {"DEMANDA_ID": 2, "RUBRICA_ASSOCIADA_NOME": "SEGURO", "RUBRICA_ASSOCIADA_VALOR_AM": 50.0},
        {"DEMANDA_ID": 2, "RUBRICA_ASSOCIADA_NOME": "CESTA", "RUBRICA_ASSOCIADA_VALOR_AM": 30.0},
    ]
    url = "/orgs/lexgroup/units/NG/dashboards/comercial-lexpre/export"
    r = client.get(
        f"{url}?from=2026-10-01&to=2026-10-31&campos=id_action&campos=rubrica&campos=valor_am",
        headers=auth(signer),
    )
    assert r.status_code == 200
    linhas = read_csv(r)
    assert linhas[0] == ["ID do Atendimento", "Rubrica", "Valor (R$)"]
    assert sorted(linhas[1:]) == sorted(
        [["1", "MORA", "120.0"], ["2", "SEGURO", "50.0"], ["2", "CESTA", "30.0"]]
    ), linhas


def test_comissao_lexpre_exporta_so_as_proprias_linhas_para_quem_nao_gere(
    client, signer, repo, sources
):
    """Como a v1 (export com escopo_proprio): o colaborador só exporta os próprios contratos."""
    repo.grant(USER_ID, "NG", "comissao-lexpre", "all")
    repo.exporters.add(USER_ID)
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    sources.members[(USER_ID, repo.org_id, "lexpre")] = "Ana Souza"
    sources.data["comercial_lexpre_NG"] = [
        _linha_comercial(1, date(2026, 10, 5)),
        _linha_comercial(2, date(2026, 10, 6), ATENDENTE="Bruno Lima"),
    ]
    url = "/orgs/lexgroup/units/NG/dashboards/comissao-lexpre/export"
    r = client.get(f"{url}?from=2026-10-01&to=2026-10-31&campos=id_action", headers=auth(signer))
    assert r.status_code == 200
    assert read_csv(r) == [["ID do Atendimento"], ["1"]]

    # Quem gere a unidade exporta todo mundo.
    repo.commission.add(USER_ID)
    r = client.get(f"{url}?from=2026-10-01&to=2026-10-31&campos=id_action", headers=auth(signer))
    assert sorted(read_csv(r)[1:]) == [["1"], ["2"]]


# --- Relatórios a mais e opções da janela (Execução Condenação e Execução Acordos, como na v1) ---


@pytest.fixture
def module_opcoes(monkeypatch):
    """Módulo falso com um recorte (como o ?criterio= da Execução) e um segundo relatório."""
    from app.dashboards.base import ExportOption

    seen = {}

    async def rows(ctx):
        seen.setdefault("opcoes", []).append(dict(ctx.export_options))
        return ROWS

    async def build(ctx):
        return {}

    recorte = ExportOption(
        key="criterio", label="Recorte", choices={"entrada": "Entradas", "saida": "Saídas"}
    )
    visao = ExportOption(
        key="view", label="Visão", choices={"concluidas": "Concluídas", "por_prazo": "Por prazo"}
    )
    fake = DashboardModule(
        key="protocolo-lexpre",
        source_db="lexpre",
        source_label="LexPre",
        build=build,
        export=ExportSpec(
            fields=FIELDS, labels=LABELS, sheet_name="Processos", rows=rows, options=(recorte,)
        ),
        export_reports={
            "atividades": ExportSpec(
                fields={"materia": "MATERIA"},
                labels={"materia": "Matéria"},
                sheet_name="Atividades",
                rows=rows,
                options=(visao,),
            )
        },
    )
    monkeypatch.setitem(DASHBOARDS, "protocolo-lexpre", fake)
    return seen


def test_opcao_chega_ao_calculo_e_vai_no_nome_do_arquivo(client, signer, module_opcoes, ready):
    r = client.get(URL, params={"criterio": "saida"}, headers=auth(signer))
    assert r.status_code == 200, r.text
    assert module_opcoes["opcoes"] == [{"criterio": "saida"}]
    assert 'filename="protocolo_lexpre_NG_saida_relatorio.csv"' in r.headers["content-disposition"]


def test_sem_opcao_usa_a_primeira(client, signer, module_opcoes, ready):
    assert client.get(URL, headers=auth(signer)).status_code == 200
    assert module_opcoes["opcoes"] == [{"criterio": "entrada"}]


def test_opcao_desconhecida_400(client, signer, module_opcoes, ready):
    r = client.get(URL, params={"criterio": "ontem"}, headers=auth(signer))
    assert r.status_code == 400
    assert "Recorte inválido" in r.json()["detail"]


def test_outro_relatorio_com_as_suas_opcoes(client, signer, module_opcoes, ready):
    r = client.get(
        URL, params={"relatorio": "atividades", "view": "por_prazo"}, headers=auth(signer)
    )
    assert r.status_code == 200, r.text
    assert read_csv(r)[0] == ["Matéria"]
    assert module_opcoes["opcoes"] == [{"view": "por_prazo"}]
    assert (
        'filename="protocolo_lexpre_NG_atividades_por_prazo_relatorio.csv"'
        in r.headers["content-disposition"]
    )


def test_relatorio_desconhecido_404(client, signer, module_opcoes, ready):
    assert (
        client.get(URL, params={"relatorio": "nao_existe"}, headers=auth(signer)).status_code == 404
    )


def test_execucao_e_acordos_exportam_os_campos_da_v1():
    """Campos, rótulos e recortes da v1 (_CAMPOS_EXPORT_EXECUCAO_*_NG); o front oferece os mesmos (exportFields.ts)."""
    execucao = DASHBOARDS["execucao"].export
    acordos = DASHBOARDS["acordos"]
    atividades = acordos.export_reports["atividades"]
    for spec in (execucao, acordos.export, atividades):
        assert list(spec.fields) == list(spec.labels)
    assert [o.key for o in execucao.options] == ["criterio"]
    assert list(execucao.options[0].choices) == ["entrada", "saida", "total"]
    assert [o.key for o in atividades.options] == ["view"]
    assert (
        "valor_saida_periodo" in execucao.fields and "valor_alcada_final" in acordos.export.fields
    )
    assert execucao.sheet_name == "Execução" and acordos.export.sheet_name == "Execução Acordos"


def test_execucao_fora_da_ng_ainda_nao_exporta(client, signer, repo, sources):
    """A v1 tem exportações próprias de LA e RJ (outras rotas): por enquanto só a da NG (501, sem quebrar).
    O que decide é a unidade no LexFlow: aqui, a unidade de teste ligada ao escritório "LA"."""
    repo.grant(USER_ID, "NG", "execucao", "all")
    repo.exporters.add(USER_ID)
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexflow")] = "LA"
    r = client.get("/orgs/lexgroup/units/NG/dashboards/execucao/export", headers=auth(signer))
    assert r.status_code == 501
    assert "só a da NG" in r.json()["detail"]


def test_campos_da_execucao_e_acordos_iguais_no_front():
    """O front (pages/dashboards/*/exportFields.ts) oferece os mesmos campos, com os mesmos rótulos, que a API
    aceita. A ordem das colunas é a dos grupos da janela (como a v1 mandava), não a da lista do servidor."""
    import re
    from pathlib import Path

    web = Path(__file__).resolve().parents[2] / "web" / "src" / "pages" / "dashboards"
    if not web.exists():
        pytest.skip("front fora do checkout")

    def campos(arquivo: str, constante: str) -> dict[str, str]:
        texto = (web / arquivo).read_text(encoding="utf-8")
        bloco = texto[texto.index(f"const {constante}") :]
        bloco = bloco[: bloco.index("\n]\n")]
        return dict(re.findall(r"slug: '([a-z_0-9]+)', label: '([^']+)'", bloco))

    acordos = DASHBOARDS["acordos"]
    for arquivo, constante, spec in (
        ("execucao/exportFields.ts", "camposExecucao", DASHBOARDS["execucao"].export),
        ("acordos/exportFields.ts", "camposProcessos", acordos.export),
        ("acordos/exportFields.ts", "camposAtividades", acordos.export_reports["atividades"]),
    ):
        assert campos(arquivo, constante) == spec.labels, constante
