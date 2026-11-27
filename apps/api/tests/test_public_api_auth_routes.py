from datetime import UTC, datetime

import pytest

from app.clock import get_now
from app.config import get_settings
from app.public_api.service import KeyCache
from app.public_api.store import get_api_key_repo
from app.routes.public_auth import get_key_cache
from conftest import USER_ID
from public_api_fakes import FakeApiKeyRepo

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
TOKENS = "/orgs/lexgroup/api-key/tokens"
RENEW = "/v1/auth/token"


@pytest.fixture
def keys() -> FakeApiKeyRepo:
    return FakeApiKeyRepo()


@pytest.fixture
def api(client, keys):
    settings = get_settings().model_copy(update={"PUBLIC_API_JWT_SECRET": "s" * 32})
    cache = KeyCache()
    ov = client.app.dependency_overrides
    ov[get_api_key_repo] = lambda: keys
    ov[get_settings] = lambda: settings
    ov[get_now] = lambda: NOW
    ov[get_key_cache] = lambda: cache
    return client


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def test_tokens_sem_login_401(api):
    assert api.post(TOKENS).status_code == 401


def test_tokens_sem_chave_ativa_404(api, signer, keys):
    keys.add_key(user_id=USER_ID, status="pending")
    r = api.post(TOKENS, headers=auth(signer))
    assert r.status_code == 404


def test_tokens_emite_par_e_audita(api, signer, keys, repo):
    keys.add_key(user_id=USER_ID)
    r = api.post(TOKENS, headers=auth(signer))
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "Bearer"
    assert body["refresh_token"].startswith("lxr_")
    assert {"access_token", "access_expires_at", "refresh_expires_at"} <= body.keys()
    assert [a.action for a in repo.audits] == ["api_key.tokens_issued"]
    assert repo.audits[0].actor_user_id == USER_ID


def test_tokens_sem_segredo_503(api, signer, keys):
    keys.add_key(user_id=USER_ID)
    api.app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"PUBLIC_API_JWT_SECRET": ""}
    )
    assert api.post(TOKENS, headers=auth(signer)).status_code == 503


def test_auth_token_rotaciona(api, signer, keys):
    keys.add_key(user_id=USER_ID)
    first = api.post(TOKENS, headers=auth(signer)).json()
    r = api.post(RENEW, json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["refresh_token"] != first["refresh_token"]


def test_auth_token_reuso_401_e_revoga(api, signer, keys, repo):
    keys.add_key(user_id=USER_ID)
    first = api.post(TOKENS, headers=auth(signer)).json()
    second = api.post(RENEW, json={"refresh_token": first["refresh_token"]}).json()
    r = api.post(RENEW, json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 401
    assert "revogados" in r.json()["detail"]
    assert api.post(RENEW, json={"refresh_token": second["refresh_token"]}).status_code == 401
    assert "api_key.refresh_reuse" in [a.action for a in repo.audits]


def test_auth_token_desconhecido_401(api):
    r = api.post(RENEW, json={"refresh_token": "lxr_x"})
    assert r.status_code == 401


def test_auth_token_corpo_invalido_422(api):
    assert api.post(RENEW, json={}).status_code == 422
