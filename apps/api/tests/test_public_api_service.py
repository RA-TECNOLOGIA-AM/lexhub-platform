import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.public_api.service import KeyCache, RefreshRejected, authenticate, issue_pair, rotate
from app.public_api.tokens import InvalidAccessToken
from public_api_fakes import FakeApiKeyRepo, sync

NOW = datetime(2026, 11, 26, 12, 0, 0, 500000, tzinfo=UTC)
SETTINGS = SimpleNamespace(
    PUBLIC_API_JWT_SECRET="s" * 32,
    PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS=604800,
    PUBLIC_API_REFRESH_TOKEN_TTL_DAYS=30,
)


def _repo():
    repo = FakeApiKeyRepo()
    repo.add_key()
    return repo


@sync
async def test_issue_pair_e_authenticate():
    repo = _repo()
    pair = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    assert pair.refresh_token.startswith("lxr_")
    assert pair.access_expires_at == NOW + timedelta(seconds=604800)
    assert pair.refresh_expires_at == NOW + timedelta(days=30)
    key = await authenticate(repo, pair.access_token, SETTINGS, NOW, KeyCache())
    assert key.id == "k1"


@sync
async def test_rotate_troca_e_invalida_o_anterior():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    p2 = await rotate(repo, p1.refresh_token, SETTINGS, NOW)
    assert p2.refresh_token != p1.refresh_token
    assert len(repo.replaced) == 1
    with pytest.raises(RefreshRejected) as exc:
        await rotate(repo, p1.refresh_token, SETTINGS, NOW)
    assert exc.value.reason == "reuso"


@sync
async def test_reuso_revoga_tudo():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    p2 = await rotate(repo, p1.refresh_token, SETTINGS, NOW)
    later = NOW + timedelta(seconds=5)
    with pytest.raises(RefreshRejected):
        await rotate(repo, p1.refresh_token, SETTINGS, later)
    with pytest.raises(RefreshRejected):
        await rotate(repo, p2.refresh_token, SETTINGS, later)
    with pytest.raises(InvalidAccessToken):
        await authenticate(repo, p2.access_token, SETTINGS, later, KeyCache())


@sync
async def test_concorrencia_so_um_consome():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    results = await asyncio.gather(
        rotate(repo, p1.refresh_token, SETTINGS, NOW),
        rotate(repo, p1.refresh_token, SETTINGS, NOW),
        return_exceptions=True,
    )
    assert sum(isinstance(r, RefreshRejected) for r in results) == 1
    assert sum(not isinstance(r, Exception) for r in results) == 1


@sync
async def test_refresh_vencido():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    with pytest.raises(RefreshRejected) as exc:
        await rotate(repo, p1.refresh_token, SETTINGS, NOW + timedelta(days=30, seconds=1))
    assert exc.value.reason == "vencido"


@sync
async def test_refresh_desconhecido():
    with pytest.raises(RefreshRejected) as exc:
        await rotate(_repo(), "lxr_nao_existe", SETTINGS, NOW)
    assert exc.value.reason == "invalido"


@sync
async def test_refresh_de_chave_revogada():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    repo.add_key(status="revoked", tvs=repo.keys["k1"].tokens_valid_since)
    with pytest.raises(RefreshRejected) as exc:
        await rotate(repo, p1.refresh_token, SETTINGS, NOW)
    assert exc.value.reason == "chave_inativa"


@sync
async def test_issue_pair_invalida_tokens_antigos():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    later = NOW + timedelta(seconds=2)
    p2 = await issue_pair(repo, repo.keys["k1"], SETTINGS, later)
    with pytest.raises(InvalidAccessToken):
        await authenticate(repo, p1.access_token, SETTINGS, later, KeyCache())
    assert (await authenticate(repo, p2.access_token, SETTINGS, later, KeyCache())).id == "k1"
    with pytest.raises(RefreshRejected):
        await rotate(repo, p1.refresh_token, SETTINGS, later)


@sync
async def test_chave_revogada_recusa_access():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    repo.add_key(status="revoked", tvs=repo.keys["k1"].tokens_valid_since)
    with pytest.raises(InvalidAccessToken):
        await authenticate(repo, p1.access_token, SETTINGS, NOW, KeyCache())


@sync
async def test_cache_de_60_segundos():
    repo = _repo()
    p1 = await issue_pair(repo, repo.keys["k1"], SETTINGS, NOW)
    clock = [100.0]
    cache = KeyCache(ttl_s=60, monotonic=lambda: clock[0])
    await authenticate(repo, p1.access_token, SETTINGS, NOW, cache)
    await authenticate(repo, p1.access_token, SETTINGS, NOW, cache)
    assert repo.calls.count("get_key") == 1
    clock[0] += 61
    await authenticate(repo, p1.access_token, SETTINGS, NOW, cache)
    assert repo.calls.count("get_key") == 2


@sync
async def test_sem_segredo_nao_emite():
    repo = _repo()
    with pytest.raises(RuntimeError):
        await issue_pair(
            repo,
            repo.keys["k1"],
            SimpleNamespace(**{**vars(SETTINGS), "PUBLIC_API_JWT_SECRET": ""}),
            NOW,
        )
