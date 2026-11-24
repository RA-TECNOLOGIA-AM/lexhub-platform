"""Modo suporte "ver como": com X-Support-Session, a API responde como o membro, só leitura, auditado."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from app.catalog import DashboardUnitRow
from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardModule
from app.support import SupportSession
from conftest import USER_ID

MEMBER = "00000000-0000-0000-0000-0000000000b2"
THIRD = "00000000-0000-0000-0000-0000000000c3"
DASH = "/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre"


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def as_member(signer, session_id: str) -> dict:
    return {**auth(signer), "X-Support-Session": session_id}


def actions(repo, name):
    return [a for a in repo.audits if a.action == name]


@pytest.fixture
def session(client, signer, repo, support_repo):
    """Dev (USER_ID) em suporte como MEMBER, na lexgroup; devolve o id da sessão."""
    repo.join(USER_ID)
    repo.join(MEMBER)
    support_repo.allowed.add(USER_ID)
    membership_id = support_repo.add_member(repo.org_id, MEMBER)
    r = client.post(
        "/orgs/lexgroup/support/sessions",
        json={"membership_id": membership_id, "reason": "Cliente não vê o dashboard"},
        headers=auth(signer),
    )
    assert r.status_code == 201
    repo.audits.clear()  # só interessa o que vem depois do início
    return r.json()["session_id"]


@pytest.fixture
def clock(client):
    """Relógio da API trocável: `clock.now` é o 'agora' de cada pedido."""
    from app.clock import get_now

    class Clock:
        now = datetime.now(UTC)

    holder = Clock()
    client.app.dependency_overrides[get_now] = lambda: holder.now
    return holder


@pytest.fixture
def module(monkeypatch):
    """Protocolo falso, com comissão por funcionário (para conferir de quem é o recorte)."""

    async def build(ctx):
        return {
            "stats": {"total": 2},
            "comissionamento_por_funcionario": [
                {"funcionario": "Ana", "valor_comissao": 10.0},
                {"funcionario": "Bruno", "valor_comissao": 30.0},
            ],
        }

    fake = DashboardModule(
        key="protocolo-lexpre",
        source_db="lexpre",
        source_label="LexPre",
        build=build,
        filters={},
        commission_fields=("comissionamento_por_funcionario",),
    )
    monkeypatch.setitem(DASHBOARDS, "protocolo-lexpre", fake)


@pytest.fixture
def ng(repo):
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")] = "1"


def card(key, unit="NG", **kw):
    base = {
        "title": key,
        "area": "Operação jurídica",
        "desc": "",
        "source": "LexPre",
        "max_delay_min": 60,
        "can_export": True,
        "can_see_commission": True,
    }
    return DashboardUnitRow(key=key, unit_code=unit, **{**base, **kw})


# --- O usuário efetivo é o membro ----------------------------------------------


def test_catalogo_e_do_membro(client, signer, repo, catalog_repo, session):
    catalog_repo.add(USER_ID, repo.org_id, card("so-do-dev", can_toggle=True))
    catalog_repo.add(MEMBER, repo.org_id, card("do-membro", can_toggle=True))
    catalog_repo.add(MEMBER, repo.org_id, card("do-membro", unit="LA", enabled=False))

    r = client.get("/orgs/lexgroup/dashboards", headers=as_member(signer, session))

    assert r.status_code == 200
    (only,) = r.json()["available"]
    assert only["key"] == "do-membro"
    assert only["units"] == ["NG", "LA"]
    assert only["can_export"] is False
    assert only["can_toggle"] is False
    assert only["disabled_units"] == []


def test_dashboard_usa_escopo_do_membro(client, signer, repo, sources, module, ng, session):
    repo.grant(MEMBER, "NG", "protocolo-lexpre", "all")
    repo.commission.add(USER_ID)  # o Dev veria a comissão de todos; o membro, não
    repo.exporters.add(MEMBER)
    sources.members[(MEMBER, repo.org_id, "lexpre")] = "Bruno"

    r = client.get(DASH, headers=as_member(signer, session))

    assert r.status_code == 200
    body = r.json()
    assert body["comissionamento_por_funcionario"] == [
        {"funcionario": "Bruno", "valor_comissao": 30.0}
    ]
    assert body["meta"].get("can_export", False) is False


def test_rota_access_responde_pelo_membro(client, signer, repo, session):
    repo.grant(MEMBER, "NG", "protocolo-lexpre", "all")

    r = client.get(f"{DASH}/access", headers=as_member(signer, session))

    assert r.status_code == 200
    assert r.json()["scope"] == "all"


@pytest.mark.parametrize("reason", ["sem_escopo", "own"])
def test_negacao_em_suporte_nao_audita_access_denied(
    client, signer, repo, module, ng, session, reason
):
    if reason == "own":
        repo.grant(MEMBER, "NG", "protocolo-lexpre", "own")  # 'own' sem vínculo = 403 em _prepare
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")  # o Dev veria; o membro, não

    r = client.get(DASH, headers=as_member(signer, session))

    assert r.status_code == 403
    assert r.json()["detail"] == "Sem acesso"
    assert actions(repo, "dashboard.access_denied") == []


# --- Só leitura ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/orgs/lexgroup/favorites/protocolo-lexpre", None),
        ("DELETE", "/orgs/lexgroup/favorites/protocolo-lexpre", None),
        ("PUT", "/orgs/lexgroup/hub-order", ["protocolo-lexpre"]),
        ("GET", f"{DASH}/export", None),
        ("PUT", f"{DASH}/enabled", {"enabled": False}),
        ("POST", "/orgs/lexgroup/support/sessions", {"membership_id": str(uuid.uuid4())}),
        ("GET", "/sources/failing", None),
    ],
)
def test_rotas_de_escrita_403_read_only(
    client, signer, repo, hub_repo, catalog_repo, session, method, path, body
):
    hub_repo.visible.add("protocolo-lexpre")
    hub_repo.favorites[(MEMBER, repo.org_id)] = ["protocolo-lexpre"]

    r = client.request(method, path, json=body, headers=as_member(signer, session))

    assert r.status_code == 403
    assert r.json() == {"detail": "support_read_only"}
    assert hub_repo.favorites == {(MEMBER, repo.org_id): ["protocolo-lexpre"]}
    assert hub_repo.orders == {}
    assert catalog_repo.switched == []
    assert actions(repo, "dashboard.export") == []


def test_rotas_de_leitura_da_lista_passam(client, signer, repo, hub_repo, session):
    hub_repo.favorites[(MEMBER, repo.org_id)] = ["protocolo-lexpre"]
    hub_repo.favorites[(USER_ID, repo.org_id)] = ["outro"]
    headers = as_member(signer, session)

    assert client.get("/health", headers=headers).status_code == 200
    r = client.get("/orgs/lexgroup/favorites", headers=headers)
    assert r.status_code == 200
    assert r.json() == ["protocolo-lexpre"]  # os favoritos do membro
    assert client.get("/orgs/lexgroup/hub-order", headers=headers).status_code == 200
    r = client.get("/orgs/lexgroup/sources/freshness", headers=headers)
    assert r.status_code == 200


def test_sem_cabecalho_nada_muda(client, signer, repo, hub_repo, support_repo):
    repo.join(USER_ID)
    hub_repo.visible.add("protocolo-lexpre")

    r = client.post("/orgs/lexgroup/favorites/protocolo-lexpre", headers=auth(signer))

    assert r.status_code == 204
    assert hub_repo.favorites == {(USER_ID, repo.org_id): ["protocolo-lexpre"]}


def test_sair_com_o_cabecalho_encerra_a_sessao(client, signer, repo, support_repo, session):
    r = client.delete(
        f"/orgs/lexgroup/support/sessions/{session}", headers=as_member(signer, session)
    )

    assert r.status_code == 204
    assert support_repo.ended[session] == "exit"
    (ended,) = actions(repo, "support.ended")
    assert ended.actor_user_id == USER_ID
    assert ended.metadata == {"session": session, "end_reason": "exit"}


# --- Sessão inválida -----------------------------------------------------------


def test_sessao_vencida_409_e_audita_uma_vez(client, signer, repo, support_repo, session):
    s = support_repo.sessions[session]
    support_repo.sessions[session] = replace(s, expires_at=datetime.now(UTC) - timedelta(minutes=1))

    for _ in range(2):
        r = client.get("/orgs/lexgroup/favorites", headers=as_member(signer, session))
        assert r.status_code == 409
        assert r.json() == {"detail": "support_expired"}

    (ended,) = actions(repo, "support.ended")
    assert ended.actor_user_id == USER_ID
    assert ended.org_id == repo.org_id
    assert ended.target_type == "membership"
    assert ended.target_id == s.target_membership_id
    assert ended.metadata == {"session": session, "end_reason": "expired"}


def test_vencimento_pelo_relogio_da_api(client, signer, repo, support_repo, session, clock):
    clock.now = support_repo.sessions[session].expires_at  # expires_at <= agora

    r = client.get("/orgs/lexgroup/favorites", headers=as_member(signer, session))

    assert r.status_code == 409
    assert support_repo.ended[session] == "expired"


def test_sessao_encerrada_409(client, signer, repo, support_repo, session):
    client.delete(f"/orgs/lexgroup/support/sessions/{session}", headers=auth(signer))
    repo.audits.clear()

    r = client.get(DASH + "/access", headers=as_member(signer, session))

    assert r.status_code == 409
    assert r.json() == {"detail": "support_expired"}
    assert actions(repo, "support.ended") == []  # já tinha sido auditada ao sair


def _alheia(support_repo, **kw) -> str:
    base = {
        "id": str(uuid.uuid4()),
        "org_id": str(uuid.uuid4()),
        "actor_user_id": USER_ID,
        "target_user_id": MEMBER,
        "target_membership_id": str(uuid.uuid4()),
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "ended_at": None,
    }
    s = SupportSession(**{**base, **kw})
    support_repo.sessions[s.id] = s
    return s.id


@pytest.mark.parametrize("which", ["de_outro", "de_outra_org", "inexistente", "invalida"])
def test_sessao_de_outro_403(client, signer, repo, support_repo, which):
    repo.join(USER_ID)
    repo.join(MEMBER)
    support_repo.allowed.add(USER_ID)
    session_id = {
        "de_outro": lambda: _alheia(support_repo, org_id=repo.org_id, actor_user_id=THIRD),
        "de_outra_org": lambda: _alheia(support_repo),
        "inexistente": lambda: str(uuid.uuid4()),
        "invalida": lambda: "nao-e-uuid",
    }[which]()

    for path in ("/orgs/lexgroup/favorites", f"{DASH}/access"):
        r = client.get(path, headers=as_member(signer, session_id))
        assert r.status_code == 403
        assert r.json() == {"detail": "Sem acesso"}
    assert support_repo.ended == {}
    assert actions(repo, "support.ended") == []


def test_dev_rebaixado_403_encerra(client, signer, repo, support_repo, session):
    support_repo.allowed.discard(USER_ID)

    r = client.get("/orgs/lexgroup/favorites", headers=as_member(signer, session))

    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    assert support_repo.ended[session] == "exit"
    (ended,) = actions(repo, "support.ended")
    assert ended.actor_user_id == USER_ID
    assert ended.metadata == {"session": session, "end_reason": "exit"}


def test_membro_desativado_409(client, signer, repo, support_repo, session):
    repo.members.discard((MEMBER, "lexgroup"))

    for path in ("/orgs/lexgroup/favorites", f"{DASH}/access"):
        r = client.get(path, headers=as_member(signer, session))
        assert r.status_code == 409
        assert r.json() == {"detail": "support_expired"}
    assert support_repo.ended[session] == "expired"
    (ended,) = actions(repo, "support.ended")
    assert ended.metadata == {"session": session, "end_reason": "expired"}


# --- support.viewed ------------------------------------------------------------


def test_viewed_uma_vez_em_5_min(client, signer, repo, support_repo, module, ng, session, clock):
    repo.grant(MEMBER, "NG", "protocolo-lexpre", "all")
    headers = as_member(signer, session)
    t0 = clock.now

    for minutes in (0, 1, 4, 6):
        clock.now = t0 + timedelta(minutes=minutes)
        assert client.get(DASH, headers=headers).status_code == 200

    viewed = actions(repo, "support.viewed")
    assert len(viewed) == 2  # 0 e 6 min; 1 e 4 ficam dentro da janela
    first = viewed[0]
    assert first.actor_user_id == USER_ID
    assert first.org_id == repo.org_id
    assert first.target_type == "membership"
    assert first.target_id == support_repo.sessions[session].target_membership_id
    assert first.metadata == {"session": session, "unit": "NG", "dashboard": "protocolo-lexpre"}


def test_sem_cabecalho_nao_grava_viewed(client, signer, repo, module, ng):
    repo.join(USER_ID)
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")

    assert client.get(DASH, headers=auth(signer)).status_code == 200
    assert actions(repo, "support.viewed") == []


def test_dedup_do_viewed_nao_cresce_para_sempre():
    from app.support import ViewedLog

    log = ViewedLog(window=timedelta(minutes=5), max_entries=3)
    t0 = datetime(2026, 11, 24, tzinfo=UTC)

    assert log.first_in_window(("s", "NG", "a"), t0)
    assert not log.first_in_window(("s", "NG", "a"), t0 + timedelta(minutes=4))
    for i, key in enumerate("bcde"):
        assert log.first_in_window(("s", "NG", key), t0 + timedelta(minutes=i))
    assert len(log) <= 3
    # Depois da janela, as antigas somem sozinhas.
    assert log.first_in_window(("s", "NG", "z"), t0 + timedelta(hours=1))
    assert len(log) == 1
