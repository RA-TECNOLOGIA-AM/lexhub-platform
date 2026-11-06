import asyncio
import time

import jwt
import pytest

from conftest import USER_ID, Signer

URL = "/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre/access"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- 401: sem login ou token inválido ----------


def test_sem_token_401(client):
    r = client.get(URL)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_esquema_errado_401(client, signer):
    r = client.get(URL, headers={"Authorization": f"Basic {signer.token()}"})
    assert r.status_code == 401


def test_token_lixo_401(client):
    assert client.get(URL, headers=auth("nao-e-um-jwt")).status_code == 401


def test_assinatura_de_outra_chave_401(client):
    intruso = Signer(kid="kid-1")  # mesmo kid, chave diferente
    assert client.get(URL, headers=auth(intruso.token())).status_code == 401


def test_token_expirado_401(client, signer):
    passado = int(time.time()) - 7200
    token = signer.token(iat=passado, exp=passado + 60)
    assert client.get(URL, headers=auth(token)).status_code == 401


def test_audience_errada_401(client, signer):
    assert client.get(URL, headers=auth(signer.token(aud="anon"))).status_code == 401


def test_issuer_de_outro_projeto_401(client, signer):
    token = signer.token(iss="https://outro.supabase.co/auth/v1")
    assert client.get(URL, headers=auth(token)).status_code == 401


def test_sem_sub_401(client, signer):
    assert client.get(URL, headers=auth(signer.token(sub=None))).status_code == 401


def test_alg_none_401(client):
    token = jwt.encode(
        {"sub": USER_ID, "aud": "authenticated", "exp": int(time.time()) + 60},
        key=None,
        algorithm="none",
    )
    assert client.get(URL, headers=auth(token)).status_code == 401


def test_detalhe_do_erro_nao_vaza(client):
    r = client.get(URL, headers=auth("nao-e-um-jwt"))
    assert r.json() == {"detail": "Não autenticado"}


# ---------- JWKS ----------


def test_rotacao_de_chave_rebusca_jwks():
    from app.auth import TokenVerifier
    from app.config import Settings

    antiga, nova = Signer(kid="old"), Signer(kid="new")
    publicadas = [antiga.jwks, nova.jwks]
    chamadas = []

    async def loader():
        chamadas.append(1)
        return publicadas[min(len(chamadas) - 1, 1)]

    s = Settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_PUBLISHABLE_KEY="pk")
    v = TokenVerifier(s, jwks_loader=loader)

    assert asyncio.run(v.verify(antiga.token())).user_id == USER_ID
    assert asyncio.run(v.verify(nova.token())).user_id == USER_ID  # kid novo -> rebusca
    assert len(chamadas) == 2
    asyncio.run(v.verify(nova.token()))
    assert len(chamadas) == 2  # já em cache


def test_kid_desconhecido_nao_rebusca_em_loop():
    from app.auth import InvalidToken, TokenVerifier
    from app.config import Settings

    chamadas = []

    async def loader():
        chamadas.append(1)
        return Signer(kid="publicada").jwks

    s = Settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_PUBLISHABLE_KEY="pk")
    v = TokenVerifier(s, jwks_loader=loader)
    for _ in range(5):
        with pytest.raises(InvalidToken):
            asyncio.run(v.verify(Signer(kid="inexistente").token()))
    assert len(chamadas) <= 2


def test_hs256_legado_com_segredo():
    from app.auth import TokenVerifier
    from app.config import Settings

    segredo = "segredo-legado-de-teste-com-32-bytes!!"
    s = Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_PUBLISHABLE_KEY="pk",
        SUPABASE_JWT_SECRET=segredo,
    )

    async def loader():
        return {"keys": []}

    v = TokenVerifier(s, jwks_loader=loader)
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": USER_ID,
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "exp": now + 60,
        },
        segredo,
        algorithm="HS256",
    )
    assert asyncio.run(v.verify(token)).user_id == USER_ID


def test_hs256_rejeitado_sem_segredo(signer):
    from app.auth import InvalidToken, TokenVerifier
    from app.config import Settings

    s = Settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_PUBLISHABLE_KEY="pk")
    v = TokenVerifier(s, jwks_loader=lambda: _jwks(signer))
    token = jwt.encode(
        {"sub": USER_ID, "aud": "authenticated", "exp": int(time.time()) + 60},
        "qualquer-segredo-com-32-bytes-ou-mais!!",
        algorithm="HS256",
    )
    with pytest.raises(InvalidToken):
        asyncio.run(v.verify(token))


async def _jwks(signer):
    return signer.jwks
