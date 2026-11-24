import uuid
from datetime import UTC, datetime, timedelta

from app.support import SupportSession
from conftest import USER_ID

OTHER = "00000000-0000-0000-0000-0000000000b2"


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def setup(repo, support_repo, *, allowed=True):
    """Quem pede é membro (e, por padrão, Owner/Dev); devolve o id da associação do alvo."""
    repo.join(USER_ID)
    if allowed:
        support_repo.allowed.add(USER_ID)
    return support_repo.add_member(repo.org_id, OTHER)


def start(client, signer, membership_id, reason="Cliente não vê o dashboard"):
    return client.post(
        "/orgs/lexgroup/support/sessions",
        json={"membership_id": membership_id, "reason": reason},
        headers=auth(signer),
    )


def actions(repo, name):
    return [a for a in repo.audits if a.action == name]


def test_inicia_sessao_201_e_audita(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)

    r = start(client, signer, membership_id, "  Cliente não vê o dashboard  ")

    assert r.status_code == 201
    body = r.json()
    assert body["member"] == {
        "membership_id": membership_id,
        "name": "Ana Souza",
        "avatar_path": None,
        "role_label": "Gestor",
        "units": [{"code": "NG", "name": "Núcleo de Gestão"}],
    }
    assert body["expires_at"]
    (started,) = actions(repo, "support.started")
    assert started.actor_user_id == USER_ID
    assert started.org_id == repo.org_id
    assert started.target_type == "membership"
    assert started.target_id == membership_id
    assert started.metadata == {
        "session": body["session_id"],
        "reason": "Cliente não vê o dashboard",  # guardado sem os espaços das pontas
    }
    assert support_repo.reasons[body["session_id"]] == "Cliente não vê o dashboard"
    assert actions(repo, "support.ended") == []


def test_nao_owner_dev_403(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo, allowed=False)

    r = start(client, signer, membership_id)

    assert r.status_code == 403
    assert r.json()["detail"] == "Só Owner e Desenvolvedor usam o modo suporte."
    assert support_repo.sessions == {}
    assert actions(repo, "support.started") == []


def test_membro_de_outra_org_404(client, signer, repo, support_repo):
    setup(repo, support_repo)
    de_fora = support_repo.add_member(str(uuid.uuid4()), OTHER)

    r = start(client, signer, de_fora)

    assert r.status_code == 404
    assert r.json()["detail"] == "Membro não encontrado nesta organização."
    assert actions(repo, "support.started") == []


def test_ver_a_si_mesmo_404(client, signer, repo, support_repo):
    setup(repo, support_repo)
    eu = support_repo.add_member(repo.org_id, USER_ID, "Piloto")

    r = start(client, signer, eu)

    assert r.status_code == 404
    assert support_repo.sessions == {}


def test_motivo_curto_422(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)

    assert start(client, signer, membership_id, "abc").status_code == 422
    assert start(client, signer, membership_id, "   abcd  ").status_code == 422
    assert support_repo.sessions == {}


def test_iniciar_de_novo_encerra_a_anterior(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)
    primeira = start(client, signer, membership_id).json()["session_id"]

    segunda = start(client, signer, membership_id).json()["session_id"]

    assert primeira != segunda
    assert len(actions(repo, "support.started")) == 2
    (ended,) = actions(repo, "support.ended")
    assert ended.metadata == {"session": primeira, "end_reason": "exit"}
    assert ended.target_id == membership_id
    assert support_repo.ended == {primeira: "exit"}


def test_encerra_204_e_audita(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)
    session_id = start(client, signer, membership_id).json()["session_id"]

    r = client.delete(f"/orgs/lexgroup/support/sessions/{session_id}", headers=auth(signer))

    assert r.status_code == 204
    assert r.content == b""
    (ended,) = actions(repo, "support.ended")
    assert ended.actor_user_id == USER_ID
    assert ended.target_type == "membership"
    assert ended.target_id == membership_id
    assert ended.metadata == {"session": session_id, "end_reason": "exit"}


def test_encerrar_duas_vezes_audita_uma(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)
    session_id = start(client, signer, membership_id).json()["session_id"]
    url = f"/orgs/lexgroup/support/sessions/{session_id}"

    assert client.delete(url, headers=auth(signer)).status_code == 204
    assert client.delete(url, headers=auth(signer)).status_code == 204

    assert len(actions(repo, "support.ended")) == 1


def test_encerrar_sessao_de_outro_404(client, signer, repo, support_repo):
    setup(repo, support_repo)
    alheia = SupportSession(
        id=str(uuid.uuid4()),
        org_id=repo.org_id,
        actor_user_id=OTHER,
        target_user_id=USER_ID,
        target_membership_id=str(uuid.uuid4()),
        expires_at=datetime.now(UTC),
        ended_at=None,
    )
    support_repo.sessions[alheia.id] = alheia

    r = client.delete(f"/orgs/lexgroup/support/sessions/{alheia.id}", headers=auth(signer))

    assert r.status_code == 404
    assert support_repo.sessions[alheia.id].ended_at is None
    assert actions(repo, "support.ended") == []


def abrir_vencida(support_repo, repo, membership_id):
    """Sessão do USER_ID aberta, mas com o prazo de 1 hora já estourado (cron ainda não passou)."""
    vencida = SupportSession(
        id=str(uuid.uuid4()),
        org_id=repo.org_id,
        actor_user_id=USER_ID,
        target_user_id=OTHER,
        target_membership_id=membership_id,
        expires_at=datetime.now(UTC) - timedelta(minutes=5),
        ended_at=None,
    )
    support_repo.sessions[vencida.id] = vencida
    return vencida


def test_iniciar_sobre_sessao_vencida_audita_expired(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)
    vencida = abrir_vencida(support_repo, repo, membership_id)

    assert start(client, signer, membership_id).status_code == 201

    (ended,) = actions(repo, "support.ended")
    assert ended.metadata == {"session": vencida.id, "end_reason": "expired"}


def test_encerrar_sessao_vencida_audita_expired(client, signer, repo, support_repo):
    membership_id = setup(repo, support_repo)
    vencida = abrir_vencida(support_repo, repo, membership_id)

    r = client.delete(f"/orgs/lexgroup/support/sessions/{vencida.id}", headers=auth(signer))

    assert r.status_code == 204
    (ended,) = actions(repo, "support.ended")
    assert ended.metadata == {"session": vencida.id, "end_reason": "expired"}
