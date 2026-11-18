import asyncio

import pytest

from app.database import SourceDisabled, SourceUnavailable
from app.source_cache import CachedSourceFetcher, MemoryStore, SourceCache
from app.source_switch import GuardedSourceFetcher, SourceSwitch
from app.sources import build_source_factory


class FakeRepo:
    def __init__(self, keys=()):
        self.keys = set(keys)
        self.loads = 0
        self.fail = False

    async def disabled_keys(self):
        self.loads += 1
        if self.fail:
            raise OSError("sem banco")
        return set(self.keys)


class Inner:
    def __init__(self):
        self.calls = 0
        self.fail = False

    async def fetch(self, query_name):
        self.calls += 1
        if self.fail:
            raise SourceUnavailable("gs_x")
        return [{"q": query_name}]

    def synced_at(self):
        return 1.0


def test_lista_de_desligadas_vale_por_30s_e_invalida_na_hora():
    now = {"t": 0.0}
    repo = FakeRepo({"gs_x"})
    switch = SourceSwitch(repo, ttl=30, clock=lambda: now["t"])
    assert asyncio.run(switch.is_disabled("gs_x")) and not asyncio.run(switch.is_disabled("pg_y"))
    now["t"] = 29
    asyncio.run(switch.is_disabled("gs_x"))
    assert repo.loads == 1
    repo.keys.clear()  # religou
    switch.invalidate()
    assert not asyncio.run(switch.is_disabled("gs_x")) and repo.loads == 2


def test_sem_ler_a_lista_nao_arrisca_ler_a_fonte():
    repo = FakeRepo()
    repo.fail = True
    with pytest.raises(SourceUnavailable):
        asyncio.run(SourceSwitch(repo).is_disabled("gs_x"))


def test_desligada_nao_serve_nem_o_ultimo_dado_bom_do_cache():
    """O cache serve o último dado bom quando a fonte falha; a trava fica por fora dele."""
    repo = FakeRepo()
    switch = SourceSwitch(repo)
    cache = SourceCache(MemoryStore(), ttl=0, stale_max_age=3600)  # tudo vencido, mas "bom"
    inner = Inner()
    factory = build_source_factory(None, cache, None, switch)
    guarded = GuardedSourceFetcher(switch, CachedSourceFetcher(cache, inner, "gs_x"), "gs_x")
    assert asyncio.run(guarded.fetch("A")) == [{"q": "A"}]
    inner.fail = True
    assert asyncio.run(guarded.fetch("A")) == [{"q": "A"}]  # fora do ar: último dado bom

    repo.keys.add("gs_x")  # desligou
    switch.invalidate()
    calls = inner.calls
    with pytest.raises(SourceDisabled):
        asyncio.run(guarded.fetch("A"))
    assert inner.calls == calls  # nem foi ao cache nem à fonte

    # Bancos do .env não passam pelo liga/desliga (não são desligáveis pela tela).
    assert not isinstance(factory("ng"), GuardedSourceFetcher)
    assert isinstance(factory("gs_x"), GuardedSourceFetcher)


def test_religada_volta_sem_pedir_nada():
    repo = FakeRepo({"gs_x"})
    switch = SourceSwitch(repo)
    guarded = GuardedSourceFetcher(switch, Inner(), "gs_x")
    with pytest.raises(SourceDisabled):
        asyncio.run(guarded.fetch("A"))
    repo.keys.clear()
    switch.invalidate()
    assert asyncio.run(guarded.fetch("A")) == [{"q": "A"}]
    assert guarded.synced_at() == 1.0
