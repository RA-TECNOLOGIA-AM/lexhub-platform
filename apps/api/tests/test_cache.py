import asyncio
from datetime import date
from decimal import Decimal

from tests.conftest import FakeHubPrefsRepo

# Carrega os dashboards antes do source_cache (ciclo antigo dashboards <-> sources <-> source_cache).
import app.dashboards  # noqa: F401
from app.cache import NullCache, RedisCache, get_or_load, safe_redis_target
from app.hub_prefs import CachedHubPrefsRepo
from app.source_cache import Entry, MemoryStore, SourceCache, ttl_by_query


def run(coro):
    return asyncio.run(coro)


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


class FakeRedis:
    """Cliente redis.asyncio falso: guarda bytes, conta chamadas e pode cair."""

    def __init__(self):
        self.data: dict[str, bytes] = {}
        self.ttls: dict[str, int] = {}
        self.down = False
        self.calls = 0

    def _check(self):
        self.calls += 1
        if self.down:
            raise ConnectionError("redis fora do ar")

    async def ping(self):
        self._check()
        return True

    async def get(self, key):
        self._check()
        return self.data.get(key)

    async def setex(self, key, ttl, value):
        self._check()
        self.data[key] = value
        self.ttls[key] = ttl

    async def delete(self, *keys):
        self._check()
        for k in keys:
            self.data.pop(k, None)

    async def aclose(self):
        pass


def make_redis(retry_after=30.0):
    fake, clock = FakeRedis(), Clock()
    cache = RedisCache(
        "redis://:segredo@redis:6379/0",
        prefix="t:",
        retry_after=retry_after,
        client_factory=lambda: fake,
        clock=clock,
    )
    return cache, fake, clock


# --- RedisCache ------------------------------------------------------------------------


def test_grava_e_le_com_prefixo_ttl_e_tipos_do_banco():
    cache, fake, _ = make_redis()
    rows = [{"valor": Decimal("10.50"), "dia": date(2026, 11, 16)}]

    async def go():
        await cache.set("lexpre:q", rows, 300)
        return await cache.get("lexpre:q")

    assert run(go()) == rows  # pickle preserva Decimal e date (JSON não)
    assert list(fake.data) == ["t:lexpre:q"]
    assert fake.ttls["t:lexpre:q"] == 300


def test_delete_invalida():
    cache, _, _ = make_redis()

    async def go():
        await cache.set("a", 1, 60)
        await cache.delete("a")
        return await cache.get("a")

    assert run(go()) is None


def test_redis_fora_na_conexao_nao_quebra_e_espera_para_tentar_de_novo():
    cache, fake, clock = make_redis(retry_after=30)
    fake.down = True

    async def go():
        assert await cache.get("k") is None
        await cache.set("k", 1, 60)  # silencioso
        await cache.delete("k")
        first = fake.calls
        clock.now += 29
        await cache.get("k")
        assert fake.calls == first  # dentro da espera: nem tenta (sem pagar timeout)
        fake.down = False
        clock.now += 2
        await cache.set("k", 1, 60)
        return await cache.get("k")

    assert run(go()) == 1


def test_falha_no_meio_da_operacao_vira_miss():
    cache, fake, _ = make_redis()

    async def go():
        await cache.set("k", 1, 60)
        fake.down = True
        assert await cache.get("k") is None
        assert await cache.status() == "down"

    run(go())


def test_valor_ilegivel_vira_miss():
    cache, fake, _ = make_redis()

    async def go():
        await cache.set("k", 1, 60)
        fake.data["t:k"] = b"nao-e-pickle"
        return await cache.get("k")

    assert run(go()) is None


def test_redis_real_inalcancavel_nao_levanta():
    cache = RedisCache("redis://127.0.0.1:1/0", timeout=0.3)

    async def go():
        assert await cache.get("k") is None
        await cache.set("k", 1, 60)
        assert await cache.status() == "down"
        await cache.close()

    run(go())


def test_log_nao_mostra_senha():
    assert safe_redis_target("redis://user:segredo@redis:6380/2") == "redis:6380/2"


def test_cache_desligado():
    cache = NullCache()

    async def go():
        await cache.set("k", 1, 60)
        return await cache.get("k"), await cache.status()

    assert run(go()) == (None, "off")


def test_get_or_load_so_carrega_no_miss():
    cache, _, _ = make_redis()
    loads = []

    async def load():
        loads.append(1)
        return ["x"]

    async def go():
        a = await get_or_load(cache, "k", 60, load)
        b = await get_or_load(cache, "k", 60, load)
        return a, b

    assert run(go()) == (["x"], ["x"])
    assert len(loads) == 1


# --- SourceCache com Redis (L2) --------------------------------------------------------


class Origin:
    def __init__(self):
        self.calls = 0
        self.fail = False

    async def fetch(self):
        self.calls += 1
        if self.fail:
            raise ConnectionError("origem fora do ar")
        return [{"busca": self.calls}]


def make_source(redis_cache, clock):
    return SourceCache(
        MemoryStore(),
        ttl=300,
        stale_max_age=3600,
        clock=clock,
        shared=redis_cache,
        shared_ttl=ttl_by_query(600, 300),
    )


def test_restart_usa_o_redis_sem_ir_ao_banco():
    redis_cache, _, _ = make_redis()
    clock, origin = Clock(), Origin()

    async def go():
        await make_source(redis_cache, clock).get("lexpre:q", origin.fetch)
        clock.now += 100
        nova_replica = make_source(redis_cache, clock)  # memória vazia (deploy/restart)
        return await nova_replica.get("lexpre:q", origin.fetch)

    entry = run(go())
    assert origin.calls == 1
    assert entry.fetched_at == 1000.0  # mantém a hora real da busca (meta.synced_at)


def test_dado_vencido_no_redis_vai_para_a_tela_e_e_renovado():
    redis_cache, _, _ = make_redis()
    clock, origin = Clock(), Origin()

    async def go():
        await make_source(redis_cache, clock).get("ng:q", origin.fetch)
        clock.now += 301
        nova_replica = make_source(redis_cache, clock)
        served = await nova_replica.get("ng:q", origin.fetch)
        await nova_replica.wait_renewals()
        return served, await nova_replica.get("ng:q", origin.fetch)

    served, after = run(go())
    assert served.data == [{"busca": 1}]  # na hora, sem esperar o banco
    assert origin.calls == 2  # vencido não conta como fresco: renovou
    assert after.data == [{"busca": 2}]


def test_dado_vencido_ha_muito_tempo_no_redis_espera_a_busca():
    redis_cache, _, _ = make_redis()
    clock, origin = Clock(), Origin()

    async def go():
        await make_source(redis_cache, clock).get("ng:q", origin.fetch)
        clock.now += 1000  # passou de ttl + stale_while_revalidate
        return await make_source(redis_cache, clock).get("ng:q", origin.fetch)

    assert run(go()).data == [{"busca": 2}]


def test_banco_fora_usa_o_ultimo_dado_bom_do_redis():
    redis_cache, _, _ = make_redis()
    clock, origin = Clock(), Origin()

    async def go():
        await make_source(redis_cache, clock).get("ng:q", origin.fetch)
        clock.now += 1000
        origin.fail = True
        return await make_source(redis_cache, clock).get("ng:q", origin.fetch)

    assert run(go()).data == [{"busca": 1}]


def test_redis_fora_cai_no_banco():
    redis_cache, fake, _ = make_redis()
    fake.down = True
    clock, origin = Clock(), Origin()
    entry = run(make_source(redis_cache, clock).get("ng:q", origin.fetch))
    assert entry.data == [{"busca": 1}]


def test_ttl_no_redis_maior_para_queries_pesadas():
    redis_cache, fake, _ = make_redis()
    clock, origin = Clock(), Origin()

    async def go():
        cache = make_source(redis_cache, clock)
        await cache.get("ng:comercial_geral_NG", origin.fetch)
        await cache.get("ng:outra", origin.fetch)

    run(go())
    assert fake.ttls == {"t:ng:comercial_geral_NG": 600, "t:ng:outra": 300}


def test_valor_estranho_no_redis_e_ignorado():
    redis_cache, _, _ = make_redis()
    clock, origin = Clock(), Origin()

    async def go():
        await redis_cache.set("ng:q", {"nao": "e Entry"}, 60)
        return await make_source(redis_cache, clock).get("ng:q", origin.fetch)

    assert isinstance(run(go()), Entry)
    assert origin.calls == 1


# --- Favoritos e ordem (cache-aside com invalidação) -----------------------------------


class CountingRepo(FakeHubPrefsRepo):
    def __init__(self):
        super().__init__()
        self.reads = 0

    async def list_favorites(self, user_id, org_id):
        self.reads += 1
        return await super().list_favorites(user_id, org_id)

    async def get_order(self, user_id, org_id):
        self.reads += 1
        return await super().get_order(user_id, org_id)


def test_favoritos_leem_do_cache_e_escrita_invalida():
    redis_cache, _, _ = make_redis()
    inner = CountingRepo()
    inner.visible = {"protocolo", "execucao"}
    repo = CachedHubPrefsRepo(inner, redis_cache, ttl=300)

    async def go():
        assert await repo.list_favorites("u", "o") == []
        assert await repo.list_favorites("u", "o") == []
        assert inner.reads == 1  # segunda leitura veio do cache
        assert await repo.add_favorite("u", "o", "protocolo")
        assert await repo.list_favorites("u", "o") == ["protocolo"]
        await repo.remove_favorite("u", "o", "protocolo")
        assert await repo.list_favorites("u", "o") == []
        assert await repo.list_favorites("u", "outra-org") == []  # chave separada por org

    run(go())


def test_ordem_le_do_cache_e_escrita_invalida():
    redis_cache, _, _ = make_redis()
    inner = CountingRepo()
    repo = CachedHubPrefsRepo(inner, redis_cache, ttl=300)

    async def go():
        await repo.get_order("u", "o")
        await repo.get_order("u", "o")
        assert inner.reads == 1
        await repo.set_order("u", "o", ["b", "a"])
        return await repo.get_order("u", "o")

    assert run(go()) == ["b", "a"]


def test_favoritos_com_redis_fora_vao_ao_banco():
    redis_cache, fake, _ = make_redis()
    fake.down = True
    inner = CountingRepo()
    inner.visible = {"protocolo"}
    repo = CachedHubPrefsRepo(inner, redis_cache, ttl=300)

    async def go():
        assert await repo.add_favorite("u", "o", "protocolo")
        return await repo.list_favorites("u", "o")

    assert run(go()) == ["protocolo"]


def test_health_cache_desligado(client):
    r = client.get("/health/cache")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "cache": "off"}
