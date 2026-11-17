from types import SimpleNamespace

import pytest

from app.config import Settings, get_settings
from app.device_auth import digest_device_value
from app.routes.device_auth import get_device_auth_repository
from app.supabase_client import get_supabase_admin, get_supabase_auth
from conftest import USER_ID


class FakeDeviceAuthRepository:
    def __init__(self):
        self.allow_calls: dict[str, int] = {}
        self.created: list[tuple[str, str, str]] = []
        self.approved: tuple[str, str] | None = None
        self.claim_result: dict | None = {"result": "authorization_pending", "user_id": None}
        self.finished: list[tuple[str, str, bool]] = []

    async def allow_request(self, bucket_key: str, limit: int, window_seconds: int) -> bool:
        count = self.allow_calls.get(bucket_key, 0) + 1
        self.allow_calls[bucket_key] = count
        return count <= limit

    async def cleanup_expired(self, now) -> None:
        return None

    async def create_session(self, device_code: str, user_code: str, expires_at) -> bool:
        self.created.append((device_code, user_code, expires_at))
        return True

    async def approve(self, user_code: str, user_id: str) -> str:
        self.approved = (user_code, user_id)
        return "approved"

    async def claim(self, device_code: str, claim_id: str) -> dict | None:
        return self.claim_result

    async def finish(self, device_code: str, claim_id: str, consume: bool) -> bool:
        self.finished.append((device_code, claim_id, consume))
        return True


class FakeSupabaseAuth:
    def __init__(self):
        self.user_token: str | None = None

        async def get_user(token: str):
            self.user_token = token
            return SimpleNamespace(user=SimpleNamespace(id=USER_ID, email="user@example.com"))

        async def generate_link(options: dict):
            assert options == {"type": "magiclink", "email": "user@example.com"}
            return SimpleNamespace(properties=SimpleNamespace(hashed_token="hashed-link"))

        self.get_user = get_user
        self.admin = SimpleNamespace(
            get_user_by_id=lambda user_id: _user_by_id(user_id),
            generate_link=generate_link,
        )


class FakeOtpAuth:
    async def verify_otp(self, options: dict):
        assert options == {"token_hash": "hashed-link", "type": "magiclink"}
        session = SimpleNamespace(access_token="access", refresh_token="refresh", expires_in=3600)
        return SimpleNamespace(session=session)


async def _user_by_id(user_id: str):
    assert user_id == USER_ID
    return SimpleNamespace(user=SimpleNamespace(email="user@example.com"))


@pytest.fixture
def device_auth(client, me_repo):
    # Quem aprova a TV é membro de uma organização (o caso normal).
    me_repo.add(USER_ID, SimpleNamespace(slug="lexgroup"), SimpleNamespace())
    repository = FakeDeviceAuthRepository()
    auth = FakeSupabaseAuth()
    otp_auth = FakeOtpAuth()
    settings = Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_PUBLISHABLE_KEY="sb_publishable_test",
        SUPABASE_SECRET_KEY="test-secret",
        WEB_BASE_URL="https://lexhub.example",
    )
    client.app.dependency_overrides[get_device_auth_repository] = lambda: repository
    client.app.dependency_overrides[get_supabase_admin] = lambda: SimpleNamespace(auth=auth)
    client.app.dependency_overrides[get_supabase_auth] = lambda: otp_auth
    client.app.dependency_overrides[get_settings] = lambda: settings
    return client, repository, auth, otp_auth, settings


def test_create_device_code_returns_short_code_and_activation_uri(device_auth):
    client, repository, _, _, settings = device_auth

    response = client.post("/auth/device/code")

    assert response.status_code == 200
    result = response.json()
    assert result["verification_uri"] == f"https://lexhub.example/ativar?code={result['user_code']}"
    assert result["interval"] == 5
    assert result["expires_in"] == 600
    assert len(result["user_code"]) == 9
    assert result["user_code"][4] == "-"
    assert not set(result["user_code"]) & set("01IO")
    assert repository.created[0][0] == digest_device_value(
        settings.supabase_secret_key, "device", result["device_code"]
    )
    assert repository.created[0][1] == digest_device_value(
        settings.supabase_secret_key, "user", result["user_code"]
    )


def test_create_device_code_is_rate_limited(device_auth):
    client, _, _, _, _ = device_auth

    for _ in range(10):
        assert client.post("/auth/device/code").status_code == 200

    response = client.post("/auth/device/code")

    assert response.status_code == 429
    assert response.json()["detail"]


def test_device_auth_refuses_to_use_publishable_key_as_admin(client):
    response = client.post("/auth/device/code")

    assert response.status_code == 503


def test_authorize_requires_validated_bearer_and_approves_code(device_auth):
    client, repository, auth, _, settings = device_auth
    user_code = "ABCD-EFGH"

    response = client.post("/auth/device/authorize", json={"user_code": user_code})
    assert response.status_code == 401
    assert auth.user_token is None

    response = client.post(
        "/auth/device/authorize",
        headers={"Authorization": "Bearer mobile-token"},
        json={"user_code": user_code},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "approved"}
    assert auth.user_token == "mobile-token"
    assert repository.approved == (
        digest_device_value(settings.supabase_secret_key, "user", user_code),
        USER_ID,
    )


def test_authorize_refuses_account_without_lexhub_access(device_auth, me_repo):
    """Conta Google sem organização (ex.: pediu acesso e ainda não foi aprovada) não liga TV."""
    client, repository, _, _, _ = device_auth
    me_repo.memberships.clear()

    response = client.post(
        "/auth/device/authorize",
        headers={"Authorization": "Bearer mobile-token"},
        json={"user_code": "ABCD-EFGH"},
    )

    assert response.status_code == 403
    assert "acesso" in response.json()["detail"]
    assert repository.approved is None


def test_authorize_rate_limit_restricts_user_code_guessing(device_auth):
    client, repository, _, _, _ = device_auth
    headers = {"Authorization": "Bearer mobile-token"}

    for _ in range(10):
        response = client.post(
            "/auth/device/authorize",
            headers=headers,
            json={"user_code": "AAAA-0000"},
        )
        assert response.status_code == 400

    response = client.post(
        "/auth/device/authorize",
        headers=headers,
        json={"user_code": "AAAA-0000"},
    )

    assert response.status_code == 429
    assert repository.approved is None


@pytest.mark.parametrize(
    ("claim_result", "expected_error"),
    [
        ({"result": "authorization_pending", "user_id": None}, "authorization_pending"),
        ({"result": "slow_down", "user_id": None}, "slow_down"),
        ({"result": "expired", "user_id": None}, "expired_token"),
    ],
)
def test_poll_returns_oauth_statuses(device_auth, claim_result, expected_error):
    client, repository, _, _, _ = device_auth
    repository.claim_result = claim_result

    response = client.get("/auth/device/token", params={"device_code": "d" * 43})

    assert response.status_code == 400
    assert response.json()["error"] == expected_error


def test_poll_issues_and_consumes_single_use_supabase_session(device_auth):
    client, repository, admin_auth, otp_auth, settings = device_auth
    repository.claim_result = {"result": "approved", "user_id": USER_ID}
    device_code = "d" * 43

    response = client.get("/auth/device/token", params={"device_code": device_code})

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"
    assert response.json()["refresh_token"] == "refresh"
    assert response.headers["cache-control"] == "no-store"
    assert not hasattr(admin_auth, "verify_otp")
    assert isinstance(otp_auth, FakeOtpAuth)
    assert repository.finished[0][0] == digest_device_value(
        settings.supabase_secret_key, "device", device_code
    )
    assert repository.finished[0][2] is True
