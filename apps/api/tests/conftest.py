import os
import time
import uuid
from dataclasses import dataclass, field

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

# Valores fixos para os testes não dependerem do .env local.
os.environ.update(
    SUPABASE_URL="https://example.supabase.co",
    SUPABASE_PUBLISHABLE_KEY="sb_publishable_test",
    SUPABASE_SECRET_KEY="",
    SUPABASE_SERVICE_ROLE_KEY="",
    SUPABASE_JWT_SECRET="",
    DATABASE_URL="",
)
# Bancos de origem desligados: os testes nunca podem conectar nos bancos reais do .env.
for _db in ("NG", "LAADV", "LEXFLOW", "LEXPRE"):
    os.environ[f"DB_{_db}_URL"] = ""
    os.environ[f"DB_{_db}_HOST"] = ""

ISSUER = "https://example.supabase.co/auth/v1"
USER_ID = "00000000-0000-0000-0000-0000000000a1"


def _jwk_for(private_key, kid: str) -> dict:
    jwk = jwt.algorithms.ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    return {**jwk, "kid": kid, "alg": "ES256", "use": "sig"}


@dataclass
class Signer:
    """Chave EC (ES256) que imita as chaves assimétricas do Supabase Auth."""

    kid: str = "kid-1"
    key: ec.EllipticCurvePrivateKey = field(
        default_factory=lambda: ec.generate_private_key(ec.SECP256R1())
    )

    @property
    def jwks(self) -> dict:
        return {"keys": [_jwk_for(self.key, self.kid)]}

    def token(self, **overrides) -> str:
        now = int(time.time())
        claims = {
            "sub": USER_ID,
            "aud": "authenticated",
            "iss": ISSUER,
            "role": "authenticated",
            "email": "piloto@lexgroup.test",
            "iat": now,
            "exp": now + 3600,
        }
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, self.key, algorithm="ES256", headers={"kid": self.kid})


@pytest.fixture
def signer() -> Signer:
    return Signer()


class FakeRepo:
    """Banco em memória: (slug, code) -> unit; (user, unit, dashboard) -> escopo."""

    def __init__(self):
        self.org_id = str(uuid.uuid4())
        self.units = {("lexgroup", "NG"): str(uuid.uuid4())}
        self.scopes: dict[tuple[str, str, str], str] = {}
        self.audits: list[dict] = []

    def grant(self, user_id: str, unit_code: str, dashboard_key: str, scope: str) -> None:
        unit_id = self.units[("lexgroup", unit_code)]
        self.scopes[(user_id, unit_id, dashboard_key)] = scope

    async def resolve_access(self, user_id, org_slug, unit_code, dashboard_key):
        from app.access import ResolvedAccess

        unit_id = self.units.get((org_slug, unit_code))
        if unit_id is None:
            return None
        return ResolvedAccess(
            org_id=self.org_id,
            unit_id=unit_id,
            scope=self.scopes.get((user_id, unit_id, dashboard_key)),
        )

    async def insert_audit(self, entry):
        self.audits.append(entry)


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def client(signer, repo):
    from app.access import get_repo
    from app.auth import TokenVerifier, get_verifier
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()
    verifier = TokenVerifier(get_settings(), jwks_loader=lambda: _async(signer.jwks))
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_repo] = lambda: repo
    with TestClient(app) as c:
        yield c


async def _async(value):
    return value
