import asyncio

import pytest

from app.cache_warmer import warm_once, warm_targets
from app.dashboards.base import DashboardModule
from app.source_cache import CachedSourceFetcher, Entry, MemoryStore, SourceCache


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


class Origin:
    """Banco de origem falso: conta as buscas; pode falhar ou demorar."""

    def __init__(self):
        self.calls = 0
        self.fail = False
        self.delay = 0.0

    async def fetch(self, query_name):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise ConnectionError("origem fora do ar")
        return [{"query": query_name, "busca": self.calls}]

    def synced_at(self):
        return None


def make(ttl=300, stale=3600):
    clock = Clock()
    return SourceCache(MemoryStore(), ttl=ttl, stale_max_age=stale, clock=clock), clock, Origin()


def run(coro):
    return asyncio.run(coro)


def test_dentro_dos_5_min_nao_vai_ao_banco():
    cache, clock, origin = make()

    async def go():
        a = await cache.get("lexpre:q", lambda: origin.fetch("q"))
        clock.now += 299
        b = await cache.get("lexpre:q", lambda: origin.fetch("q"))
        return a, b

    a, b = run(go())
    assert origin.calls == 1
    assert b is a


def test_vencido_busca_de_novo():
    cache, clock, origin = make()

    async def go():
        await cache.get("k", lambda: origin.fetch("q"))
        clock.now += 300
        return await cache.get("k", lambda: origin.fetch("q"))

    entry = run(go())
    assert origin.calls == 2
    assert entry.data[0]["busca"] == 2
    assert entry.fetched_at == clock.now


def test_varias_pessoas_juntas_geram_uma_busca_so():
    cache, _clock, origin = make()
    origin.delay = 0.05

    async def go():
        return await asyncio.gather(*(cache.get("k", lambda: origin.fetch("q")) for _ in range(10)))

    entries = run(go())
    assert origin.calls == 1
    assert all(e is entries[0] for e in entries)


def test_banco_fora_do_ar_serve_o_ultimo_dado_bom_por_ate_1h():
    cache, clock, origin = make()

    async def go():
        first = await cache.get("k", lambda: origin.fetch("q"))
        origin.fail = True
        clock.now += 3600
        return first, await cache.get("k", lambda: origin.fetch("q"))

    first, again = run(go())
    assert again is first


def test_depois_de_1h_o_erro_aparece():
    cache, clock, origin = make()

    async def go():
        await cache.get("k", lambda: origin.fetch("q"))
        origin.fail = True
        clock.now += 3601
        await cache.get("k", lambda: origin.fetch("q"))

    with pytest.raises(ConnectionError):
        run(go())


def test_sem_dado_anterior_o_erro_aparece():
    cache, _clock, origin = make()
    origin.fail = True
    with pytest.raises(ConnectionError):
        run(cache.get("k", lambda: origin.fetch("q")))


def test_aquecedor_renova_mesmo_fresco():
    cache, _clock, origin = make()

    async def go():
        await cache.get("k", lambda: origin.fetch("q"))
        await cache.refresh("k", lambda: origin.fetch("q"))
        return await cache.get("k", lambda: origin.fetch("q"))

    entry = run(go())
    assert origin.calls == 2
    assert entry.data[0]["busca"] == 2


def test_memoria_tem_limite_e_sai_a_mais_antiga():
    store = MemoryStore(max_entries=2)
    store.set("a", Entry([], 1))
    store.set("b", Entry([], 2))
    store.set("c", Entry([], 3))
    assert store.get("a") is None
    assert store.get("b") is not None and store.get("c") is not None


def test_fetcher_com_cache_informa_quando_o_dado_veio_do_banco():
    cache, clock, origin = make()

    async def go():
        fetcher = CachedSourceFetcher(cache, origin, "lexpre")
        assert fetcher.synced_at() is None
        await fetcher.fetch("q1")
        clock.now += 100
        await fetcher.fetch("q2")
        return fetcher

    fetcher = run(go())
    assert fetcher.synced_at() == 1000.0  # o mais antigo dos dados usados


def test_alvos_do_aquecedor_sem_repetir():
    async def build(ctx):
        return {}

    a = DashboardModule("a", "lexpre", "LexPre", build, queries=("log",))
    b = DashboardModule("b", "lexpre", "LexPre", build, queries=("log", "outra"))
    c = DashboardModule("c", "lexflow", "LexFlow", build, queries=("log",))
    assert warm_targets([a, b, c]) == [("lexpre", "log"), ("lexpre", "outra"), ("lexflow", "log")]


def test_aquecedor_pula_banco_fora_e_segue_apos_falha():
    cache, _clock, origin = make()
    broken = Origin()
    broken.fail = True
    fetchers = {"lexpre": broken, "lexflow": origin}
    targets = [("lexpre", "q1"), ("ng", "q2"), ("lexflow", "q3")]

    ok = run(warm_once(cache, fetchers.__getitem__, targets, lambda db: db != "ng"))

    assert ok == 1  # lexpre falhou, ng está fora, lexflow renovou
    assert origin.calls == 1
    assert cache._store.get("lexflow:q3") is not None
