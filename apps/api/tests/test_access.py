from conftest import USER_ID


def url(org="lexgroup", unit="NG", dashboard="protocolo-lexpre") -> str:
    return f"/orgs/{org}/units/{unit}/dashboards/{dashboard}/access"


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def test_acesso_liberado_200(client, signer, repo):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")
    r = client.get(url(), headers=auth(signer))
    assert r.status_code == 200
    assert r.json() == {
        "org": "lexgroup",
        "unit": "NG",
        "dashboard": "protocolo-lexpre",
        "scope": "all",
    }


def test_escopo_own(client, signer, repo):
    repo.grant(USER_ID, "NG", "pendencias", "own")
    r = client.get(url(dashboard="pendencias"), headers=auth(signer))
    assert r.status_code == 200
    assert r.json()["scope"] == "own"


def test_sem_regra_403(client, signer, repo):
    r = client.get(url(), headers=auth(signer))
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}


def test_outra_organizacao_403(client, signer, repo):
    repo.units[("outra-org", "NG")] = "unit-de-outra-org"
    r = client.get(url(org="outra-org"), headers=auth(signer))
    assert r.status_code == 403


def test_organizacao_inexistente_403_igual(client, signer):
    """Não revela se a organização existe: mesma resposta de 'sem acesso'."""
    r = client.get(url(org="nao-existe"), headers=auth(signer))
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}


def test_negacao_vai_para_auditoria(client, signer, repo):
    client.get(url(), headers={**auth(signer), "User-Agent": "pytest"})
    assert len(repo.audits) == 1
    a = repo.audits[0]
    assert a.action == "dashboard.access_denied"
    assert a.actor_user_id == USER_ID
    assert a.org_id == repo.org_id
    assert a.target_type == "dashboard"
    assert a.target_id == "protocolo-lexpre"
    assert a.metadata == {"org": "lexgroup", "unit": "NG"}
    assert a.user_agent == "pytest"


def test_negacao_em_org_inexistente_audita_sem_org(client, signer, repo):
    client.get(url(org="nao-existe"), headers=auth(signer))
    assert repo.audits[0].org_id is None


def test_acesso_liberado_nao_audita(client, signer, repo):
    repo.grant(USER_ID, "NG", "protocolo-lexpre", "all")
    client.get(url(), headers=auth(signer))
    assert repo.audits == []


def test_sem_login_nao_consulta_banco(client, repo):
    assert client.get(url()).status_code == 401
    assert repo.audits == []


def test_parametros_invalidos_422(client, signer):
    r = client.get(url(unit="ng minúsculo"), headers=auth(signer))
    assert r.status_code == 422


def test_sem_banco_configurado_503(signer):
    from fastapi.testclient import TestClient

    from app.auth import TokenVerifier, get_verifier
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()

    async def jwks():
        return signer.jwks

    app.dependency_overrides[get_verifier] = lambda: TokenVerifier(get_settings(), jwks)
    with TestClient(app) as c:
        r = c.get(url(), headers=auth(signer))
    assert r.status_code == 503
    assert r.json() == {"detail": "Banco indisponível"}
