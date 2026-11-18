from datetime import date, datetime

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardInputError, DashboardModule, parse_filters, resolve_period
from app.database import SourceUnavailable
from conftest import USER_ID

URL = "/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre"


def log_row(**overrides):
    """Uma linha no formato da query log_setor_demanda_lexpre_NG (só as colunas que o cálculo usa)."""
    row = {
        "ESCRITORIO_ID": 1,
        "SETOR_ID": 5,
        "ID_DEMANDA": 1,
        "MATERIA": "ANP",
        "UF": "am",
        "AREA_ATUACAO_ID": 3,
        "AREA_ATUACAO_NOME": "CONSUMIDOR",
        "FUNCIONARIO": "Ana Souza",
        "STATUS_DEMANDA_ID": 13,  # Aguardando Despacho Inicial = protocolada
        "SETOR_ATUAL_ID": 99,
    }
    return {**row, **overrides}


LOG_ROWS = [
    log_row(TIPO="entrada", MOVIMENTACAO_ID=10, DATA=datetime(2026, 11, 2, 9)),
    log_row(TIPO="saida", MOVIMENTACAO_ID=11, DATA=datetime(2026, 11, 5, 15)),
    # outro escritório (LA): não entra na NG
    log_row(
        TIPO="entrada",
        MOVIMENTACAO_ID=20,
        DATA=datetime(2026, 11, 3, 9),
        ESCRITORIO_ID=2,
        ID_DEMANDA=2,
        MATERIA="MORA",
        UF="RJ",
    ),
]


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


@pytest.fixture
def module(monkeypatch):
    """Troca o módulo do Protocolo por um falso, que devolve o que recebeu (para conferir a casca)."""
    seen = {}

    async def build(ctx):
        seen["ctx"] = ctx
        rows = await ctx.source.fetch("log_setor_demanda_lexpre_NG")
        return {
            "stats": {"protocolados_total": {"total": len(rows), "comparativo": 0.0}},
            "comissionamento_por_funcionario": [
                {"funcionario": "Ana", "qtd_protocolados": 1, "valor_comissao": 10.0},
                {"funcionario": "Bruno", "qtd_protocolados": 3, "valor_comissao": 30.0},
            ],
            "opcoes_filtro": {
                "materias": ["ANP"],
                "funcionarios": ["Ana"],
                "ufs": ["AM"],
                "areas": [],
            },
        }

    fake = DashboardModule(
        key="protocolo-lexpre",
        source_db="lexpre",
        source_label="LexPre",
        build=build,
        filters={"materia": str, "funcionario": str, "area_atuacao_id": int, "uf": str},
        commission_fields=("comissionamento_por_funcionario",),
        v2_only_fields=("protocolados_no_prazo", "metas", "pendencias_mais_antigas"),
    )
    monkeypatch.setitem(DASHBOARDS, "protocolo-lexpre", fake)
    return seen


@pytest.fixture
def ready(repo, sources):
    """Pessoa com acesso 'all' ao Protocolo na NG, e a NG ligada ao escritório 1 do LexPre."""
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    sources.data["log_setor_demanda_lexpre_NG"] = [{"ID_DEMANDA": 1}, {"ID_DEMANDA": 2}]


# --- Casca: resposta, período, filtros -----------------------------------


def test_resposta_com_meta_e_dados(client, signer, module, ready, repo):
    repo.commission.add(USER_ID)
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 200
    body = r.json()
    assert body["meta"] == {
        "unit": "NG",
        "from": "2026-11-01",
        "to": "2026-11-11",
        "source": "LexPre",
        "synced_at": None,
        "timezone": "America/Manaus",
    }
    assert body["stats"]["protocolados_total"]["total"] == 2
    assert body["comissionamento_por_funcionario"][0]["funcionario"] == "Ana"
    assert body["opcoes_filtro"]["materias"] == ["ANP"]


def test_quem_desistiu_nao_ocupa_o_worker_com_o_calculo(client, signer, module, ready, monkeypatch):
    """O front cancelou a busca (filtro trocado de novo): a API não roda o cálculo."""
    from starlette.requests import Request

    async def desconectado(self):
        return True

    monkeypatch.setattr(Request, "is_disconnected", desconectado)
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 499
    assert "ctx" not in module  # build não rodou


def test_campos_da_v2_sem_regra_vem_null(client, signer, module, ready):
    body = client.get(URL, headers=auth(signer)).json()
    assert body["protocolados_no_prazo"] is None
    assert body["metas"] is None
    assert body["pendencias_mais_antigas"] is None


def test_quem_gere_ve_a_comissao_de_todos(client, signer, module, ready, repo):
    repo.commission.add(USER_ID)
    rows = client.get(URL, headers=auth(signer)).json()["comissionamento_por_funcionario"]
    assert [r["funcionario"] for r in rows] == ["Ana", "Bruno"]


def test_colaborador_ve_so_a_propria_comissao(client, signer, module, ready, repo, sources):
    sources.members[(USER_ID, repo.org_id, "lexpre")] = "Bruno"
    rows = client.get(URL, headers=auth(signer)).json()["comissionamento_por_funcionario"]
    assert rows == [{"funcionario": "Bruno", "qtd_protocolados": 3, "valor_comissao": 30.0}]


def test_colaborador_sem_vinculo_nao_ve_comissao_nenhuma(client, signer, module, ready):
    body = client.get(URL, headers=auth(signer)).json()
    assert body["comissionamento_por_funcionario"] == []


def test_modulo_recebe_unidade_periodo_e_filtros(client, signer, module, ready, sources):
    q = "?from=2026-10-01&to=2026-10-31&materia=ANP&materia=MORA&area_atuacao_id=3&uf=AM"
    body = client.get(URL + q, headers=auth(signer)).json()
    ctx = module["ctx"]
    assert ctx.unit_ref == "1"
    assert (ctx.period.start, ctx.period.end) == (date(2026, 10, 1), date(2026, 10, 31))
    assert ctx.filters == {
        "materia": ["ANP", "MORA"],
        "funcionario": [],
        "area_atuacao_id": [3],
        "uf": ["AM"],
    }
    assert ctx.can_see_commission is False
    assert sources.last.db_name == "lexpre"
    assert sources.last.fetched == ["log_setor_demanda_lexpre_NG"]
    assert (body["meta"]["from"], body["meta"]["to"]) == ("2026-10-01", "2026-10-31")


def test_filtro_que_o_modulo_nao_declara_e_ignorado(client, signer, module, ready):
    client.get(URL + "?cor=azul", headers=auth(signer))
    assert "cor" not in module["ctx"].filters


def test_so_uma_data_422(client, signer, module, ready):
    r = client.get(URL + "?from=2026-10-01", headers=auth(signer))
    assert r.status_code == 422
    assert r.json() == {"detail": "Informe as duas datas do período (from e to)"}


def test_periodo_invertido_422(client, signer, module, ready):
    r = client.get(URL + "?from=2026-10-31&to=2026-10-01", headers=auth(signer))
    assert r.status_code == 422


def test_data_invalida_422(client, signer, module, ready):
    assert client.get(URL + "?from=ontem&to=hoje", headers=auth(signer)).status_code == 422


def test_area_que_nao_e_numero_422(client, signer, module, ready):
    r = client.get(URL + "?area_atuacao_id=abc", headers=auth(signer))
    assert r.status_code == 422
    assert r.json() == {"detail": "Filtro area_atuacao_id inválido"}


# --- Casca: acesso e erros -------------------------------------------------


def test_sem_login_401(client):
    assert client.get(URL).status_code == 401


def test_sem_acesso_403(client, signer, module, repo):
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 403
    assert repo.audits[0].action == "dashboard.access_denied"


def test_escopo_own_403_auditado_ate_ter_vinculo(client, signer, module, ready, repo):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "own")
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    assert repo.audits[0].metadata == {"org": "lexgroup", "unit": "NG", "reason": "own_sem_vinculo"}
    assert "ctx" not in module  # o módulo nem roda


def test_dashboard_sem_modulo_404(client, signer, repo):
    repo.grant(USER_ID, "NG", "despesas", "all")
    r = client.get("/orgs/lexgroup/units/NG/dashboards/despesas", headers=auth(signer))
    assert r.status_code == 404
    assert r.json() == {"detail": "Este dashboard ainda não tem dados na V2"}


def test_unidade_sem_ligacao_com_a_fonte_503(client, signer, module, repo):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 503
    assert r.json() == {"detail": "A unidade NG ainda não está ligada à fonte LexPre"}


def test_fonte_fora_do_ar_503(client, signer, ready, monkeypatch):
    async def build(ctx):
        raise SourceUnavailable("lexpre")

    monkeypatch.setitem(
        DASHBOARDS,
        "protocolo-lexpre",
        DashboardModule("protocolo-lexpre", "lexpre", "LexPre", build),
    )
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 503
    assert r.json() == {"detail": "A fonte LexPre está indisponível no momento"}


def test_fonte_desligada_423_e_nao_503(client, signer, ready, monkeypatch):
    from app.database import SourceDisabled

    async def build(ctx):
        raise SourceDisabled("lexpre")

    monkeypatch.setitem(
        DASHBOARDS,
        "protocolo-lexpre",
        DashboardModule("protocolo-lexpre", "lexpre", "LexPre", build),
    )
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 423
    assert r.json() == {"detail": "A fonte LexPre está desligada"}


def test_protocolo_real_com_linhas_do_log(client, signer, ready, sources, repo):
    """O cálculo copiado da v1 roda na casca: 1 protocolada na NG; a demanda do escritório 2 fica fora."""
    repo.commission.add(USER_ID)
    sources.data["log_setor_demanda_lexpre_NG"] = LOG_ROWS
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 200
    body = r.json()
    assert body["stats"]["protocolados_total"]["total"] == 1
    assert [p["name"] for p in body["protocolados_por_materia"]] == ["ANP"]
    assert body["opcoes_filtro"] == {
        "materias": ["ANP"],
        "funcionarios": ["Ana Souza"],
        "ufs": ["AM"],
        "areas": [{"id": 3, "nome": "CONSUMIDOR"}],
    }
    assert body["protocolados_no_prazo"] is None  # novo da V2, sem regra ainda


def test_protocolo_real_filtro_que_nao_bate_zera_e_mantem_as_opcoes(client, signer, ready, sources):
    sources.data["log_setor_demanda_lexpre_NG"] = LOG_ROWS
    body = client.get(URL + "?materia=MORA", headers=auth(signer)).json()
    assert body["stats"]["protocolados_total"]["total"] == 0
    assert body["opcoes_filtro"]["materias"] == ["ANP"]  # opções calculadas antes dos filtros


@pytest.mark.parametrize(
    ("key", "lista_funcionarios"),
    [
        ("org-documentos-lexpre", "funcionarios_org_doc"),
        ("peticionamento-lexpre", "funcionarios_peticionamento"),
        ("pendencias-lexpre", "funcionarios_pendencias"),
    ],
)
def test_setores_lexpre_rodam_o_calculo_da_v1(
    client, signer, repo, sources, key, lista_funcionarios
):
    """Org. Doc, Peticionamento e Pendências (LexPre): cálculo da v1 roda na casca, só a NG (escritório 1)."""
    repo.grant(USER_ID, "NG", key, "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    sources.data["log_setor_demanda_lexpre_NG"] = LOG_ROWS
    sources.data["setor_func_lexpre_NG"] = []
    r = client.get(f"/orgs/lexgroup/units/NG/dashboards/{key}", headers=auth(signer))
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["source"] == "LexPre"
    assert lista_funcionarios in body
    assert body["opcoes_filtro"]["ufs"] == ["AM"]  # a linha do RJ (escritório 2) fica fora


def test_pre_protocolo_traz_stats_e_producao_diaria_de_cada_setor(client, signer, repo, sources):
    """Pré-protocolo (LexPre): os 4 setores, cada um com o stats e a produção diária (total e por funcionário)."""
    repo.grant(USER_ID, "NG", "pre-protocolo", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    sources.data["log_setor_demanda_lexpre_NG"] = LOG_ROWS
    sources.data["setor_func_lexpre_NG"] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/pre-protocolo", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    for setor in ("pendencias", "org_documentos", "peticionamento", "protocolo"):
        assert body[setor]["stats"] is not None
        assert isinstance(body[setor]["por_dia"], list)
        assert isinstance(body[setor]["por_dia_por_funcionario"], dict)
    # A saída do Protocolo em 05/11 (LOG_ROWS) está na série diária do setor.
    assert [p["name"] for p in body["protocolo"]["por_dia"]] == ["2026-11-05"]


@pytest.mark.parametrize("key", ["org-documentos-lexpre", "peticionamento-lexpre"])
def test_rubricas_reunidas_na_resposta(client, signer, repo, sources, key):
    """Org. Doc e Peticionamento: o pacote (rubrica reunida) na fila vem com as rubricas da demanda."""
    repo.grant(USER_ID, "NG", key, "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    setor_atual = 3 if key == "org-documentos-lexpre" else 4  # Org. Doc / Peticionamento
    sources.data["log_setor_demanda_lexpre_NG"] = LOG_ROWS + [
        log_row(
            TIPO="entrada",
            MOVIMENTACAO_ID=30,
            DATA=datetime(2026, 11, 4, 9),
            ID_DEMANDA=4204,
            MATERIA="RUBRICAS_REUNIDAS",
            RUBRICA_REUNIDA=True,
            CLIENTE_NOME="CIVAL OLIVEIRA",
            SETOR_ID=setor_atual,
            SETOR_ATUAL_ID=setor_atual,
            STATUS_DEMANDA_ID=1,
        )
    ]
    sources.data["setor_func_lexpre_NG"] = []
    sources.data["demanda_rubrica_reunida_lexpre_NG"] = [
        {"DEMANDA_ID": 4204, "RUBRICA_ASSOCIADA_NOME": "OP_VENCIDAS"},
        {"DEMANDA_ID": 4204, "RUBRICA_ASSOCIADA_NOME": "CESTA"},
    ]
    body = client.get(f"/orgs/lexgroup/units/NG/dashboards/{key}", headers=auth(signer)).json()
    assert body["rubricas_reunidas"] == [
        {
            "materia": "RUBRICAS_REUNIDAS",
            "demandas": [
                {
                    "id_demanda": 4204,
                    "cliente": "CIVAL OLIVEIRA",
                    "situacao": "represado",
                    "protocolado": False,
                    "rubricas": ["OP_VENCIDAS", "CESTA"],
                }
            ],
        }
    ]


def _own_rows_module(monkeypatch):
    """Módulo falso com own_rows_only (como a Comissão Comercial): devolve o que a casca passou."""

    async def build(ctx):
        return {"own_ref": ctx.own_ref, "gere": ctx.can_see_commission}

    fake = DashboardModule(
        key="protocolo-lexpre",
        source_db="lexpre",
        source_label="LexPre",
        build=build,
        own_rows_only=True,
    )
    monkeypatch.setitem(DASHBOARDS, "protocolo-lexpre", fake)


def test_own_rows_only_colaborador_recebe_o_proprio_vinculo(
    client, signer, ready, sources, repo, monkeypatch
):
    _own_rows_module(monkeypatch)
    sources.members[(USER_ID, repo.org_id, "lexpre")] = "Ana Souza"
    body = client.get(URL, headers=auth(signer)).json()
    assert body["own_ref"] == "Ana Souza"
    assert body["gere"] is False


def test_own_rows_only_quem_gere_nao_e_recortado(client, signer, ready, sources, repo, monkeypatch):
    _own_rows_module(monkeypatch)
    repo.commission.add(USER_ID)
    body = client.get(URL, headers=auth(signer)).json()
    assert body["own_ref"] is None
    assert body["gere"] is True


def test_comercial_e_comissao_lexpre_rodam_o_calculo_da_v1(client, signer, repo, sources):
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    for q in DASHBOARDS["comercial-lexpre"].queries:
        sources.data[q] = []
    for key in ("comercial-lexpre", "comissao-lexpre"):
        repo.grant(USER_ID, "NG", key, "all")
        r = client.get(f"/orgs/lexgroup/units/NG/dashboards/{key}", headers=auth(signer))
        assert r.status_code == 200, key
        assert r.json()["stats"]["comissao_base"] == 0.0
        assert set(r.json()["opcoes_filtro"]) == {"atendentes", "areas", "ufs", "segmentos"}
        # Meta Inteligente: só no Comercial (a Comissão é o escopo da própria pessoa), nas três janelas.
        meta = r.json().get("meta_inteligente")
        if key == "comercial-lexpre":
            assert set(meta) == {"3", "6", "12"}
            assert meta["6"]["meses_considerados"] == 6 and meta["6"]["atendentes"] == []
        else:
            assert meta is None
            assert "valor_causa_protocolado_legado" not in r.json()


def _protocolo_legado(saida, valor, atendente="Ana Souza", status="PROTOCOLADO", uf="AM"):
    return {
        "UF": uf,
        "SAIDA": saida,
        "STATUS": status,
        "REAJUIZAMENTO": False,
        "MATERIA": "MORA",
        "VALOR_CAUSA": valor,
        "ATENDENTE": atendente,
    }


def _comercial_ng(repo, sources, ng_ref="NG"):
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
    if ng_ref:
        repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = ng_ref
    for q in DASHBOARDS["comercial-lexpre"].queries:
        sources.data[q] = []
    repo.grant(USER_ID, "NG", "comercial-lexpre", "all")


def test_comercial_lexpre_soma_o_protocolado_do_banco_legado(client, signer, repo, sources):
    """Meta anual: o ano todo de 2026 no legado (sem período); Meta por Atendente: só o período."""
    _comercial_ng(repo, sources)
    sources.data["setor_protocolo"] = [
        _protocolo_legado("2026-10-15", 1000.0),
        _protocolo_legado("2026-02-01", 500.0, atendente="Bruno Lima"),
        _protocolo_legado("2025-12-30", 9999.0),  # outro ano
        _protocolo_legado("2026-10-20", 7777.0, status="EM ANDAMENTO"),  # não protocolado
        _protocolo_legado("2026-10-21", 300.0, atendente="Wellison Rocha", uf="RJ"),  # do RJ
    ]
    r = client.get(
        "/orgs/lexgroup/units/NG/dashboards/comercial-lexpre?from=2026-10-01&to=2026-12-31",
        headers=auth(signer),
    )
    assert r.status_code == 200
    body = r.json()
    # Meta anual: o banco legado inteiro, como na v1; Meta por Atendente: sem quem é do RJ.
    assert body["valor_causa_protocolado_legado"] == 1800.0
    assert body["valor_causa_protocolado_por_atendente_legado"] == {"Ana": 1000.0}


def test_comercial_lexpre_sem_legado_ligado_ou_fora_do_ar(
    client, signer, repo, sources, monkeypatch
):
    # RJ (ref do banco ng diferente de NG) não somava na v1.
    _comercial_ng(repo, sources, ng_ref="RJ")
    url = "/orgs/lexgroup/units/NG/dashboards/comercial-lexpre"
    body = client.get(url, headers=auth(signer)).json()
    assert body["valor_causa_protocolado_legado"] is None
    assert body["valor_causa_protocolado_por_atendente_legado"] == {}

    # Legado fora do ar: a página continua só com o LexPre.
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = "NG"
    original = sources.factory

    def factory(db_name):
        fonte = original(db_name)
        if db_name == "ng":

            async def fora(query_name):
                raise SourceUnavailable(query_name)

            fonte.fetch = fora
        return fonte

    monkeypatch.setattr(sources, "factory", factory)
    r = client.get(url, headers=auth(signer))
    assert r.status_code == 200
    assert r.json()["valor_causa_protocolado_legado"] is None


def _lexflow(repo, sources, key, unidade="NG"):
    repo.grant(USER_ID, unidade, key, "all")
    repo.unit_refs[(repo.units[("lexgroup", unidade)], "lexflow")] = unidade
    for q in DASHBOARDS[key].queries:
        sources.data[q] = []


@pytest.mark.parametrize("key", ["execucao", "acordos", "recursal"])
def test_lexflow_roda_o_calculo_da_v1(client, signer, repo, sources, key):
    """Execução, Acordos e Recursal: o handler da v1 roda na casca, com a fonte LexFlow da V2."""
    _lexflow(repo, sources, key)
    r = client.get(f"/orgs/lexgroup/units/NG/dashboards/{key}", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == "LexFlow"
    # O Recursal junta as chamadas da página da v1 (blocos periodo, historico...); os outros, a resposta da rota.
    assert ("periodo" if key == "recursal" else "stats") in body
    assert sources.last.db_name == "lexflow"


def test_lexflow_situacao_invalida_422(client, signer, repo, sources):
    _lexflow(repo, sources, "recursal")
    r = client.get(
        "/orgs/lexgroup/units/NG/dashboards/recursal?situacao_processo=XYZ", headers=auth(signer)
    )
    assert r.status_code == 422
    assert "Situação do processo inválida" in r.json()["detail"]


def test_recursal_sem_versao_na_v1_para_a_unidade_501(client, signer, repo, sources):
    """A v1 tem Recursal na NG, no LA e no RJ: outra ref no LexFlow tem o módulo, mas não o cálculo."""
    repo.grant(USER_ID, "NG", "recursal", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexflow")] = "SP"
    r = client.get("/orgs/lexgroup/units/NG/dashboards/recursal", headers=auth(signer))
    assert r.status_code == 501


def test_lexflow_filtros_seguem_a_rota_da_v1():
    """Lista ou um valor, e int onde a rota da v1 recebe números (id_1g do Recursal)."""
    assert DASHBOARDS["recursal"].filters["id_1g_recursal"] is int
    assert DASHBOARDS["execucao"].filters["ano_ajuizamento_execucao"] is str
    assert "situacao_processo" in DASHBOARDS["acordos"].filters


@pytest.mark.parametrize(
    ("banco", "ref", "fonte", "campo"),
    [
        ("ng", "NG", "NG", "protocolos_resolvidos"),
        ("laadv", "LA", "LA", "protocolos_resolvidos_LA"),
    ],
)
def test_protocolo_legado_sai_do_banco_da_unidade(
    client, signer, repo, sources, banco, ref, fonte, campo
):
    """Protocolo (legado): NG e RJ pelo banco ng (rotas /protocolo e /protocolo_RJ da v1); a LA, sem o ng,
    pelo laadv (rota /protocolo_LA). A resposta é a da rota da v1 de cada uma."""
    repo.grant(USER_ID, "NG", "protocolo", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], banco)] = ref  # unidade ligada só a esse banco
    module = DASHBOARDS["protocolo"]
    for q in (*module.queries, *module.alt_sources["laadv"].queries):
        sources.data[q] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/protocolo", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == fonte
    assert campo in body["stats"]
    assert sources.last.db_name == banco


def test_protocolo_legado_mes_a_mes_vem_do_historico_todo(client, signer, repo, sources):
    """Protocolados no período (novembro) só contam o do mês; o "mês a mês" traz o histórico todo."""
    repo.grant(USER_ID, "NG", "protocolo", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = "NG"
    linha = {"STATUS": "PROTOCOLADO", "REAJUIZAMENTO": False, "UF": "AM", "MATERIA": "ANP"}
    sources.data["setor_protocolo"] = [
        {**linha, "ENTRADA": datetime(2025, 3, 1, 9), "SAIDA": datetime(2025, 3, 10, 9)},
        {**linha, "ENTRADA": datetime(2026, 11, 2, 9), "SAIDA": datetime(2026, 11, 5, 9)},
    ]
    sources.data["comercial_geral_NG"] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/protocolo", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["stats"]["protocolos_resolvidos"] == 1
    assert sum(p["value"] for p in body["protocolados_por_mes"]) == 2


def test_peticionamento_legado_revisao_e_mes_a_mes_sem_periodo(client, signer, repo, sources):
    """Peticionamento (legado): os peticionados contam só o período; o "mês a mês" e a fila de revisão vêm
    do histórico todo, como a página da v1 (chamada sem data)."""
    repo.grant(USER_ID, "NG", "peticionamento", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = "NG"
    linha = {"REAJUIZAMENTO": False, "UF": "AM", "MATERIA": "ANP"}
    # data da confecção = DATA_CONFECCAO; o "mês a mês" da v1 agrupa por DATA_CONTRATACAO
    sources.data["setor_confeccao"] = [
        {
            **linha,
            "STATUS": "PROTOCOLAR",
            "DATA_CONFECCAO": datetime(2025, 3, 10),
            "DATA_CONTRATACAO": datetime(2025, 3, 1),
        },
        {
            **linha,
            "STATUS": "PROTOCOLAR",
            "DATA_CONFECCAO": datetime(2026, 11, 5),
            "DATA_CONTRATACAO": datetime(2026, 11, 2),
        },
        {
            **linha,
            "STATUS": "REVISÃO",
            "DATA_CONFECCAO": datetime(2025, 6, 2),
            "DATA_CONTRATACAO": datetime(2025, 6, 1),
        },
    ]
    r = client.get("/orgs/lexgroup/units/NG/dashboards/peticionamento", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["stats"]["total_peticionados"] == 1
    assert body["stats"]["processos_em_revisao"] == 1
    assert sum(p["value"] for p in body["peticionados_por_mes"]) == 2


@pytest.mark.parametrize(
    ("banco", "ref", "fonte", "campo"),
    [
        ("ng", "NG", "NG", "total_peticionados"),
        ("laadv", "LA", "LA", "total_confeccionados_LA"),
    ],
)
def test_peticionamento_legado_sai_do_banco_da_unidade(
    client, signer, repo, sources, banco, ref, fonte, campo
):
    """Peticionamento (legado): NG e RJ pelo banco ng; a LA, sem o ng, pelo laadv (rota /peticionamento_LA)."""
    repo.grant(USER_ID, "NG", "peticionamento", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], banco)] = ref  # unidade ligada só a esse banco
    module = DASHBOARDS["peticionamento"]
    for q in (*module.queries, *module.alt_sources["laadv"].queries):
        sources.data[q] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/peticionamento", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == fonte
    assert campo in body["stats"]
    assert sources.last.db_name == banco


@pytest.mark.parametrize(
    ("banco", "ref", "fonte", "campo"),
    [
        ("ng", "NG", "NG", "resolvidos_total"),
        ("laadv", "LA", "LA", "total_organizados_LA"),
    ],
)
def test_org_documentos_legado_sai_do_banco_da_unidade(
    client, signer, repo, sources, banco, ref, fonte, campo
):
    """Org. de Documentos (legado): NG e RJ pelo banco ng; a LA, sem o ng, pelo laadv (rota /org_doc_LA)."""
    repo.grant(USER_ID, "NG", "org-documentos", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], banco)] = ref  # unidade ligada só a esse banco
    module = DASHBOARDS["org-documentos"]
    for q in (*module.queries, *module.alt_sources["laadv"].queries):
        sources.data[q] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/org-documentos", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == fonte
    assert campo in body["stats"]
    assert sources.last.db_name == banco


@pytest.mark.parametrize(
    ("banco", "ref", "fonte", "campo"),
    [
        ("ng", "NG", "NG", "pendencias_total"),
        ("laadv", "LA", "LA", "pendencias_total_LA"),
    ],
)
def test_pendencias_legado_sai_do_banco_da_unidade(
    client, signer, repo, sources, banco, ref, fonte, campo
):
    """Pendências (legado): NG e RJ pelo banco ng; a LA, sem o ng, pelo laadv (rota /pendencia_LA)."""
    repo.grant(USER_ID, "NG", "pendencias", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], banco)] = ref  # unidade ligada só a esse banco
    module = DASHBOARDS["pendencias"]
    for q in (*module.queries, *module.alt_sources["laadv"].queries):
        sources.data[q] = []
    r = client.get("/orgs/lexgroup/units/NG/dashboards/pendencias", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == fonte
    assert campo in body["stats"]
    assert sources.last.db_name == banco


def test_protocolo_legado_unidade_sem_banco_503(client, signer, repo):
    repo.grant(USER_ID, "NG", "protocolo", "all")
    r = client.get("/orgs/lexgroup/units/NG/dashboards/protocolo", headers=auth(signer))
    assert r.status_code == 503


def test_protocolo_legado_filtros_e_queries_das_duas_copias():
    module = DASHBOARDS["protocolo"]
    assert {"materia", "funcionario", "sistema", "area_atuacao_id"} <= set(module.filters)
    assert "uf_protocolo" in module.filters  # só a rota do NG tem; a da LA ignora
    assert "setor_protocolo" in module.queries
    assert "setor_protocolo_LA" in module.alt_sources["laadv"].queries


# --- Funções puras -----------------------------------------------------------


def test_periodo_padrao_e_o_mes_atual():
    p = resolve_period(None, None, date(2026, 11, 11))
    assert (p.start, p.end) == (date(2026, 11, 1), date(2026, 11, 11))


def test_periodo_pedido():
    p = resolve_period(date(2026, 1, 1), date(2026, 1, 31), date(2026, 11, 11))
    assert (p.start, p.end) == (date(2026, 1, 1), date(2026, 1, 31))


def test_parse_filters_ignora_vazios():
    assert parse_filters({"uf": str}, {"uf": ["", "AM"]}) == {"uf": ["AM"]}
    with pytest.raises(DashboardInputError):
        parse_filters({"area_atuacao_id": int}, {"area_atuacao_id": ["x"]})
