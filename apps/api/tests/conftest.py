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
    """Banco em memória: (slug, code) -> unit; (user, unit, dashboard) -> escopo; membros por org."""

    def __init__(self):
        self.org_id = str(uuid.uuid4())
        self.units = {("lexgroup", "NG"): str(uuid.uuid4())}
        self.scopes: dict[tuple[str, str, str], str] = {}
        self.members: set[tuple[str, str]] = set()  # (user_id, org_slug)
        self.audits: list[dict] = []

    def join(self, user_id: str, org_slug: str = "lexgroup") -> None:
        self.members.add((user_id, org_slug))

    async def resolve_org(self, user_id, org_slug):
        return self.org_id if (user_id, org_slug) in self.members else None

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


class FakeMeRepo:
    """Banco em memória do /me: user_id -> organizações e a associação em cada uma."""

    def __init__(self):
        self.orgs: dict[str, list] = {}
        self.memberships: dict[tuple[str, str], object] = {}

    def add(self, user_id: str, org, membership) -> None:
        self.orgs.setdefault(user_id, []).append(org)
        self.memberships[(user_id, org.id)] = membership

    async def list_orgs(self, user_id):
        return list(self.orgs.get(user_id, []))

    async def membership(self, user_id, org_id):
        return self.memberships.get((user_id, org_id))


@pytest.fixture
def me_repo() -> FakeMeRepo:
    return FakeMeRepo()


class FakeCatalogRepo:
    """Banco em memória do catálogo: (user_id, org_id) -> linhas dashboard x unidade."""

    def __init__(self):
        self.rows: dict[tuple[str, str], list] = {}
        self.upcoming: list = []

    def add(self, user_id: str, org_id: str, row) -> None:
        self.rows.setdefault((user_id, org_id), []).append(row)

    async def list_available(self, user_id, org_id):
        return list(self.rows.get((user_id, org_id), []))

    async def list_upcoming(self):
        return list(self.upcoming)


@pytest.fixture
def catalog_repo() -> FakeCatalogRepo:
    return FakeCatalogRepo()


@pytest.fixture
def client(signer, repo, me_repo, catalog_repo):
    from app.access import get_repo
    from app.auth import TokenVerifier, get_verifier
    from app.catalog import get_catalog_repo
    from app.config import get_settings
    from app.main import create_app
    from app.me import get_me_repo

    get_settings.cache_clear()
    app = create_app()
    verifier = TokenVerifier(get_settings(), jwks_loader=lambda: _async(signer.jwks))
    app.dependency_overrides[get_verifier] = lambda: verifier
    app.dependency_overrides[get_repo] = lambda: repo
    app.dependency_overrides[get_me_repo] = lambda: me_repo
    app.dependency_overrides[get_catalog_repo] = lambda: catalog_repo
    with TestClient(app) as c:
        yield c


async def _async(value):
    return value
