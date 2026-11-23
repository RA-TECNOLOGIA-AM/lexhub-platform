"""Unidades e fontes e o card do hub: a hora vem do registro de leituras (memória + Redis).

A rota só lê esse registro: nenhuma consulta a banco, nada muda no aquecedor nem no TTL.
"""

import asyncio

import pytest

from app.dashboards.base import DashboardModule  # noqa: F401 (carrega antes do cache: import circular)
from app.read_log import ReadLog
from app.source_cache import MemoryStore, SourceCache
from conftest import USER_ID
from test_read_log import FakeShared


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


class Clock:
    def __init__(self, now: float = 1_000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def run(coro):
    return asyncio.run(coro)


async def _ok():
    return [{"a": 1}]


async def _falha():
    raise TimeoutError("host=10.0.0.1 user=leitor")  # a mensagem nunca sai daqui


# --- SourceCache grava no registro ------------------------------------------------------------------


def test_busca_no_banco_grava_a_hora_e_ela_sobrevive_ao_restart():
    shared = FakeShared()
    clock = Clock(1_000.0)
    run(SourceCache(MemoryStore(), clock=clock, shared=shared).refresh("ng:q", _ok))

    depois = SourceCache(MemoryStore(), clock=clock, shared=shared)  # deploy: memória vazia

    assert depois.fetched_at("ng:q") is None
    assert run(depois.last_read("ng:q")) == 1_000.0


def test_falha_no_banco_grava_so_o_tipo_do_erro():
    cache = SourceCache(MemoryStore(), clock=Clock(1_000.0))

    with pytest.raises(TimeoutError):
        run(cache.refresh("ng:q", _falha))

    read = run(cache.reads.of_db("ng"))["q"]
    assert (read.ok_at, read.fail_at, read.error) == (None, 1_000.0, "TimeoutError")


# --- GET /orgs/{org}/sources/freshness ---------------------------------------------------------------


def _reads(client) -> ReadLog:
    return client.app.state.source_cache.reads


def test_sem_login_401(client):
    assert client.get("/orgs/lexgroup/sources/freshness?keys=lexflow").status_code == 401


def test_quem_nao_e_da_organizacao_403(client, signer):
    r = client.get("/orgs/lexgroup/sources/freshness?keys=lexflow", headers=auth(signer))
    assert r.status_code == 403


def test_hora_da_fonte_e_a_leitura_mais_recente_de_qualquer_query_dela(client, signer, repo):
    repo.join(USER_ID)
    run(_reads(client).ok("lexflow:setor_recurso_NG", 1_762_866_000.0))  # 13:00 UTC
    run(_reads(client).ok("lexflow:setor_recurso_NG@27", 1_762_869_600.0))  # 14:00 UTC
    run(_reads(client).ok("lexpre:log", 1_762_880_000.0))  # outra fonte não conta

    r = client.get(
        "/orgs/lexgroup/sources/freshness?keys=lexflow,sheets_financeiro_ng", headers=auth(signer)
    )

    assert r.status_code == 200
    body = r.json()["sources"]
    assert body["lexflow"]["fetched_at"] == "2025-11-11T14:00:00Z"
    assert body["lexflow"]["error"] is None
    assert isinstance(body["lexflow"]["ttl_min"], int)
    assert body["sheets_financeiro_ng"] == {
        "fetched_at": None,
        "ttl_min": body["sheets_financeiro_ng"]["ttl_min"],
        "error": None,
        "error_at": None,
    }


def test_a_fonte_falha_quando_a_tentativa_mais_recente_falhou(client, signer, repo):
    repo.join(USER_ID)
    run(_reads(client).ok("ng:a", 1_762_869_600.0))  # 14:00
    run(_reads(client).failed("ng:b", 1_762_873_200.0, "TimeoutError"))  # 15:00

    ng = client.get("/orgs/lexgroup/sources/freshness?keys=ng", headers=auth(signer)).json()

    assert ng["sources"]["ng"]["fetched_at"] == "2025-11-11T14:00:00Z"
    assert ng["sources"]["ng"]["error"] == "TimeoutError"
    assert ng["sources"]["ng"]["error_at"] == "2025-11-11T15:00:00Z"

    run(_reads(client).ok("ng:a", 1_762_876_800.0))  # 16:00: leitura boa depois da falha
    ng = client.get("/orgs/lexgroup/sources/freshness?keys=ng", headers=auth(signer)).json()
    assert ng["sources"]["ng"]["error"] is None


def test_card_do_hub_usa_a_mesma_hora_mesmo_sem_o_dado_na_memoria(
    client, signer, repo, catalog_repo
):
    """Depois de um deploy, o dado está no Redis e a hora no registro: o card não volta a "Atualiza
    ao abrir"."""
    from test_catalog import row

    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row())  # protocolo-lexpre
    run(_reads(client).ok("lexpre:log_setor_demanda_lexpre_NG", 1_762_869_600.0))

    cards = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"]

    assert cards[0]["synced_at"] == "2025-11-11T14:00:00Z"


def test_deploy_com_redis_mantem_a_hora_no_hub_e_nas_fontes(client, signer, repo, catalog_repo):
    """Ponta a ponta com o RedisCache de produção (cliente falso que guarda bytes em pickle): a API lê
    o banco, sobe de novo com a memória vazia, e as rotas reais do hub e das fontes mantêm a hora."""
    from test_cache import make_redis
    from test_catalog import row

    repo.join(USER_ID)
    catalog_repo.add(
        USER_ID, repo.org_id, row()
    )  # protocolo-lexpre: lê log_setor_demanda_lexpre_NG
    redis_cache, fake, _ = make_redis()
    clock = Clock(1_762_869_600.0)  # 11/11/2025 14:00 UTC

    antes = SourceCache(MemoryStore(), clock=clock, shared=redis_cache)
    run(antes.refresh("lexpre:log_setor_demanda_lexpre_NG", _ok))
    clock.now += 600  # 14:10
    with pytest.raises(TimeoutError):
        run(antes.refresh("ng:actions_NG_2", _falha))
    assert {"t:reads:lexpre", "t:reads:ng"} <= set(fake.data)  # foi para o Redis, em bytes

    # Deploy/reload: processo novo, memória vazia; o Redis continua.
    client.app.state.source_cache = SourceCache(MemoryStore(), clock=clock, shared=redis_cache)

    cards = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"]
    fontes = client.get(
        "/orgs/lexgroup/sources/freshness?keys=lexpre,ng,lexflow", headers=auth(signer)
    ).json()["sources"]

    assert cards[0]["synced_at"] == "2025-11-11T14:00:00Z"  # não voltou a "Atualiza ao abrir"
    assert fontes["lexpre"]["fetched_at"] == "2025-11-11T14:00:00Z"
    assert fontes["lexpre"]["error"] is None
    assert fontes["ng"]["error"] == "TimeoutError"  # a falha também sobreviveu
    assert fontes["ng"]["error_at"] == "2025-11-11T14:10:00Z"
    assert fontes["lexflow"]["fetched_at"] is None  # nunca lida: "Aguardando leitura"


def test_redis_fora_do_ar_nao_derruba_nada_e_fica_so_em_memoria():
    from test_cache import make_redis

    redis_cache, fake, _ = make_redis()
    fake.down = True
    cache = SourceCache(MemoryStore(), clock=Clock(1_000.0), shared=redis_cache)

    entry = run(cache.refresh("ng:q", _ok))

    assert entry.data == [{"a": 1}]
    assert run(cache.last_read("ng:q")) == 1_000.0


def test_chave_repetida_vem_uma_vez_e_sem_chaves_vem_vazio(client, signer, repo):
    repo.join(USER_ID)

    one = client.get("/orgs/lexgroup/sources/freshness?keys=ng,ng", headers=auth(signer)).json()
    empty = client.get("/orgs/lexgroup/sources/freshness", headers=auth(signer)).json()

    assert list(one["sources"]) == ["ng"]
    assert empty == {"sources": {}}


@pytest.mark.parametrize("keys", ["NG", "ng;drop", ",".join(f"f{i:02d}" for i in range(51))])
def test_chave_invalida_ou_demais_422(client, signer, repo, keys):
    repo.join(USER_ID)

    r = client.get(f"/orgs/lexgroup/sources/freshness?keys={keys}", headers=auth(signer))

    assert r.status_code == 422
