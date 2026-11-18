import asyncio
import logging

import asyncpg
import pytest

from app.cache_warmer import MIN_PAUSE, pause_after, warm_loop, warm_once, warm_targets
from app.dashboards.base import AltSource, DashboardModule
from app.database import SourceUnavailable
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


def test_vencido_ha_pouco_vai_para_a_tela_na_hora_e_renova_em_segundo_plano():
    cache, clock, origin = make()
    origin.delay = 0.05  # a busca demora: a tela não pode esperar por ela

    async def go():
        first = await cache.get("k", lambda: origin.fetch("q"))
        clock.now += 300
        served = await asyncio.wait_for(cache.get("k", lambda: origin.fetch("q")), 0.01)
        await cache.wait_renewals()
        after = await cache.get("k", lambda: origin.fetch("q"))
        return first, served, after

    first, served, after = run(go())
    assert served is first  # o atual, sem esperar o banco
    assert origin.calls == 2  # renovou uma vez
    assert after.data[0]["busca"] == 2  # quem pede depois já recebe o novo
    assert after.fetched_at == clock.now


def test_vencido_ha_muito_tempo_espera_a_busca():
    cache, clock, origin = make()

    async def go():
        await cache.get("k", lambda: origin.fetch("q"))
        clock.now += 300 + 600  # ttl + stale_while_revalidate
        return await cache.get("k", lambda: origin.fetch("q"))

    entry = run(go())
    assert origin.calls == 2
    assert entry.data[0]["busca"] == 2
    assert entry.fetched_at == clock.now


def test_sem_stale_while_revalidate_vencido_espera_a_busca():
    clock, origin = Clock(), Origin()
    cache = SourceCache(MemoryStore(), ttl=300, clock=clock, stale_while_revalidate=0)

    async def go():
        await cache.get("k", lambda: origin.fetch("q"))
        clock.now += 300
        return await cache.get("k", lambda: origin.fetch("q"))

    assert run(go()).data[0]["busca"] == 2


def test_varias_pessoas_no_vencido_geram_uma_renovacao_so():
    cache, clock, origin = make()
    origin.delay = 0.05

    async def go():
        first = await cache.get("k", lambda: origin.fetch("q"))
        clock.now += 301
        served = await asyncio.gather(
            *(cache.get("k", lambda: origin.fetch("q")) for _ in range(10))
        )
        await cache.wait_renewals()
        return first, served

    first, served = run(go())
    assert all(e is first for e in served)
    assert origin.calls == 2


def test_renovacao_em_segundo_plano_que_falha_mantem_o_dado_e_nao_levanta():
    cache, clock, origin = make()

    async def go():
        first = await cache.get("k", lambda: origin.fetch("q"))
        origin.fail = True
        clock.now += 301
        served = await cache.get("k", lambda: origin.fetch("q"))
        await cache.wait_renewals()
        again = await cache.get("k", lambda: origin.fetch("q"))  # tenta renovar de novo
        await cache.wait_renewals()
        return first, served, again

    first, served, again = run(go())
    assert served is first and again is first
    assert origin.calls == 3


def test_aquecedor_espera_a_renovacao_em_andamento_em_vez_de_buscar_de_novo():
    cache, clock, origin = make()
    origin.delay = 0.05

    async def go():
        await cache.get("k", lambda: origin.fetch("q"))
        clock.now += 301
        await cache.get("k", lambda: origin.fetch("q"))  # dispara a renovação
        return await cache.refresh("k", lambda: origin.fetch("q"))

    entry = run(go())
    assert origin.calls == 2
    assert entry.data[0]["busca"] == 2


def test_requisicao_cancelada_nao_cancela_a_busca_dos_outros():
    cache, _clock, origin = make()
    origin.delay = 0.05

    async def go():
        desistiu = asyncio.create_task(cache.get("k", lambda: origin.fetch("q")))
        await asyncio.sleep(0.01)
        desistiu.cancel()
        entry = await cache.get("k", lambda: origin.fetch("q"))
        return desistiu, entry

    desistiu, entry = run(go())
    assert desistiu.cancelled()
    assert origin.calls == 1
    assert entry.data[0]["busca"] == 1


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


def test_alvos_do_aquecedor_incluem_os_bancos_extras():
    async def build(ctx):
        return {}

    m = DashboardModule(
        "m", "lexpre", "LexPre", build, queries=("log",), extra_queries={"ng": ("setor_protocolo",)}
    )
    assert warm_targets([m]) == [("lexpre", "log"), ("ng", "setor_protocolo")]


def test_alvos_do_aquecedor_incluem_os_bancos_alternativos():
    async def build(ctx):
        return {}

    m = DashboardModule(
        "m",
        "ng",
        "NG",
        build,
        queries=("setor_protocolo",),
        alt_sources={"laadv": AltSource("LA", ("setor_protocolo_LA",))},
    )
    assert warm_targets([m]) == [("ng", "setor_protocolo"), ("laadv", "setor_protocolo_LA")]


def test_planilhas_ficam_fora_do_aquecedor():
    """A planilha do Google só é baixada quando alguém abre o dashboard (não a cada ciclo)."""

    async def build(ctx):
        return {}

    m = DashboardModule(
        "m",
        "sheets_financeiro_ng",
        "Planilha",
        build,
        queries=("REPASSES CLIENTES",),
        extra_queries={"ng": ("setor_protocolo",)},
    )
    assert warm_targets([m]) == [("ng", "setor_protocolo")]


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


def test_aquecedor_registra_fonte_indisponivel_numa_linha_sem_traceback(caplog):
    cache, _clock, _origin = make()

    class Cancelada:
        async def fetch(self, query_name):
            try:
                raise asyncpg.QueryCanceledError("canceling statement due to statement timeout")
            except asyncpg.QueryCanceledError as exc:
                raise SourceUnavailable("lexflow") from exc

    with caplog.at_level(logging.WARNING, logger="app.cache_warmer"):
        ok = run(warm_once(cache, lambda _db: Cancelada(), [("lexflow", "q1")], lambda _db: True))

    assert ok == 0
    linhas = [r for r in caplog.records if r.name == "app.cache_warmer"]
    falha = next(r for r in linhas if "q1" in r.getMessage())
    assert falha.getMessage() == "'lexflow:q1' não renovou: SourceUnavailable (QueryCanceledError)"
    assert falha.exc_info is None  # sem traceback: o motivo já está no log de app.database


def test_intervalo_do_aquecedor_conta_do_inicio_do_ciclo():
    assert pause_after(98, 240) == 142  # próximo ciclo começa 240 s depois do início deste
    assert pause_after(239, 240) == MIN_PAUSE  # ciclo quase do tamanho do intervalo: folga mínima
    assert pause_after(500, 240) == MIN_PAUSE  # ciclo maior que o intervalo: folga mínima


def test_aquecedor_desconta_a_duracao_do_ciclo_da_pausa():
    cache, _clock, _origin = make()
    now = [0.0]
    pauses: list[float] = []

    class Stop(Exception):
        pass

    class SlowOrigin(Origin):
        async def fetch(self, query_name):
            now[0] += 98  # o ciclo leva 98 s
            return await super().fetch(query_name)

    async def fake_sleep(seconds):
        pauses.append(seconds)
        if len(pauses) == 3:
            raise Stop

    with pytest.raises(Stop):
        run(
            warm_loop(
                cache,
                lambda _db: SlowOrigin(),
                [("lexflow", "q")],
                lambda _db: True,
                interval=240,
                initial_delay=30,
                sleep=fake_sleep,
                clock=lambda: now[0],
            )
        )

    assert pauses == [30, 142, 142]  # espera inicial, depois intervalo - duração do ciclo
