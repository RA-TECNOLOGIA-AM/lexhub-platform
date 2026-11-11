from datetime import date

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardInputError, DashboardModule, parse_filters, resolve_period
from app.sources import SourceUnavailable
from conftest import USER_ID

URL = "/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre"


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
    sources.refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"
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
    repo.grant(USER_ID, "NG", "pendencias", "all")
    r = client.get("/orgs/lexgroup/units/NG/dashboards/pendencias", headers=auth(signer))
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


def test_protocolo_de_verdade_ainda_nao_ligado_501(client, signer, ready):
    """Sem o código da v1 colado, responde 501 com a explicação (nunca números falsos)."""
    r = client.get(URL, headers=auth(signer))
    assert r.status_code == 501
    assert "aguardando a cópia da v1" in r.json()["detail"]


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
