import hashlib
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import Settings
from app.public_api.tokens import (
    REFRESH_PREFIX,
    InvalidAccessToken,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
    verify_access_token,
)

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
SECRET = "s" * 32


def test_access_token_ida_e_volta():
    tok, exp = issue_access_token("k1", SECRET, 604800, NOW)
    claims = verify_access_token(tok, SECRET, NOW)
    assert claims.key_id == "k1"
    assert claims.issued_at == NOW
    assert exp == claims.expires_at == NOW + timedelta(seconds=604800)


def test_access_token_vencido():
    tok, _ = issue_access_token("k1", SECRET, 60, NOW)
    with pytest.raises(InvalidAccessToken):
        verify_access_token(tok, SECRET, NOW + timedelta(seconds=61))


def test_access_token_outro_segredo_ou_typ():
    tok, _ = issue_access_token("k1", SECRET, 60, NOW)
    with pytest.raises(InvalidAccessToken):
        verify_access_token(tok, "x" * 32, NOW)
    parecido = jwt.encode(
        {"sub": "k1", "iat": NOW, "exp": NOW + timedelta(seconds=60)}, SECRET, "HS256"
    )
    with pytest.raises(InvalidAccessToken):
        verify_access_token(parecido, SECRET, NOW)


def test_access_token_lixo():
    with pytest.raises(InvalidAccessToken):
        verify_access_token("nao-e-jwt", SECRET, NOW)


def test_refresh_token_formato_e_hash():
    t = new_refresh_token()
    assert t.startswith(REFRESH_PREFIX) and REFRESH_PREFIX == "lxr_" and len(t) >= 40
    assert hash_refresh_token(t) == hashlib.sha256(t.encode()).hexdigest()
    assert new_refresh_token() != t


def test_config_padroes():
    s = Settings()
    assert s.PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS == 604800
    assert s.PUBLIC_API_REFRESH_TOKEN_TTL_DAYS == 30
    assert s.PUBLIC_API_JWT_SECRET == ""
