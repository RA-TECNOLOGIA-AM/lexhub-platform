"""Cache das fontes contra o egress do LexFlow: validade por banco, aquecedor sem o LexFlow e
"só baixa se mudou" (impressão digital do resultado antes das linhas)."""

import asyncio
import pickle

from app.cache_warmer import warm_once, warm_targets
from app.config import Settings
from app.dashboards.base import DashboardModule
from app.database import fetch_read_only_if_changed, fingerprint_query
from app.source_cache import (
    CachedSourceFetcher,
    Entry,
    MemoryStore,
    SourceCache,
    shared_ttl_covering,
    ttl_by_query,
)


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


class Origin:
    """Banco de origem falso com busca condicional: conta downloads e conferências.

    `version` é o estado do banco; a impressão digital é 'fp<version>'.
    """

    def __init__(self):
        self.version = 1
        self.downloads = 0
        self.probes = 0
        self.fail = False

    def _rows(self, query_name):
        return [{"query": query_name, "versao": self.version}]

    async def fetch(self, query_name):
        if self.fail:
            raise ConnectionError("origem fora do ar")
        self.downloads += 1
        return self._rows(query_name)

    async def fetch_if_changed(self, query_name, known):
        if self.fail:
            raise ConnectionError("origem fora do ar")
        self.probes += 1
        fingerprint = f"fp{self.version}"
        if known is not None and known == fingerprint:
            return None, fingerprint
        self.downloads += 1
        return self._rows(query_name), fingerprint

    def synced_at(self):
        return None


def make(probe_dbs=("lexflow",), ttl_by_db=None, swr=600):
    clock = Clock()
    cache = SourceCache(
        MemoryStore(),
        ttl=300,
        clock=clock,
        ttl_by_db=ttl_by_db,
        probe_dbs=probe_dbs,
        stale_while_revalidate=swr,
    )
    return cache, clock, Origin()


def run(coro):
    return asyncio.run(coro)


async def ler(cache, origin, key="lexflow:q"):
    fetcher = CachedSourceFetcher(cache, origin, key.split(":")[0])
    return await fetcher._read(key.split(":", 1)[1])


# --- validade por banco ------------------------------------------------------------------------


def test_lexflow_vale_15_min_e_os_outros_bancos_seguem_com_5():
    cache, clock, origin = make(probe_dbs=(), ttl_by_db={"lexflow": 900})

    async def go():
        await cache.get("lexflow:q", lambda: origin.fetch("q"))
        await cache.get("lexpre:q", lambda: origin.fetch("q"))
        clock.now += 600
        await cache.get("lexflow:q", lambda: origin.fetch("q"))  # ainda fresco
        await cache.get("lexpre:q", lambda: origin.fetch("q"))  # vencido: renova em segundo plano
        await cache.wait_renewals()

    run(go())
    assert origin.downloads == 3  # lexflow 1x, lexpre 2x
    assert cache.ttl_of("lexflow:q") == 900
    assert cache.ttl_of("lexpre:q") == 300


def test_redis_guarda_o_lexflow_pelo_menos_a_validade_mais_o_stale_while_revalidate():
    ttl = shared_ttl_covering(ttl_by_query(600, 300), {"lexflow": 900}, 600)
    assert ttl("lexflow:execucao_LA") == 1500
    assert ttl("lexpre:qualquer") == 300
    assert ttl("ng:comercial_geral_NG") == 600  # as pesadas seguem com o TTL delas


# --- só baixa se mudou ---------------------------------------------------------------------------


def test_primeira_leitura_baixa_e_guarda_a_impressao_digital():
    cache, _clock, origin = make()
    entry = run(ler(cache, origin))
    assert origin.downloads == 1
    assert entry.fingerprint == "fp1"
    assert entry.data == [{"query": "q", "versao": 1}]


def test_renovacao_sem_mudanca_nao_baixa_e_mantem_o_mesmo_dado_e_a_versao():
    cache, clock, origin = make()

    async def go():
        first = await ler(cache, origin)
        clock.now += 300  # venceu: vai para a tela e renova em segundo plano
        await ler(cache, origin)
        await cache.wait_renewals()
        return first, await ler(cache, origin)

    first, after = run(go())
    assert origin.downloads == 1  # só a primeira
    assert origin.probes == 2
    assert after.data is first.data  # o mesmo dado, sem baixar de novo
    assert after.fetched_at == clock.now  # conferido agora: a tela mostra a hora da conferência
    assert after.data_version == first.fetched_at  # mesma versão: os cálculos guardados valem


def test_renovacao_com_mudanca_baixa_o_dado_novo():
    cache, clock, origin = make()

    async def go():
        await ler(cache, origin)
        origin.version = 2
        clock.now += 300
        await ler(cache, origin)
        await cache.wait_renewals()
        return await ler(cache, origin)

    after = run(go())
    assert origin.downloads == 2
    assert after.data == [{"query": "q", "versao": 2}]
    assert after.fingerprint == "fp2"
    assert after.data_version == after.fetched_at


def test_vencido_ha_muito_tempo_confere_em_vez_de_baixar_tudo():
    cache, clock, origin = make()

    async def go():
        first = await ler(cache, origin)
        clock.now += 300 + 600 + 1  # passou da validade + stale-while-revalidate: espera a busca
        return first, await ler(cache, origin)

    first, after = run(go())
    assert origin.downloads == 1  # o banco confirmou que nada mudou
    assert after.data is first.data
    assert after.fetched_at == clock.now


def test_banco_sem_conferencia_baixa_como_sempre():
    cache, clock, origin = make(probe_dbs=())  # nenhum banco com "só baixa se mudou"

    async def go():
        await ler(cache, origin, "lexpre:q")
        clock.now += 300 + 600 + 1
        await ler(cache, origin, "lexpre:q")

    run(go())
    assert origin.probes == 0
    assert origin.downloads == 2


def test_so_os_bancos_configurados_conferem():
    cache, clock, origin = make(probe_dbs=("lexflow",))

    async def go():
        await ler(cache, origin, "lexpre:q")
        clock.now += 300 + 600 + 1
        await ler(cache, origin, "lexpre:q")

    run(go())
    assert origin.probes == 0
    assert origin.downloads == 2


def test_dado_antigo_sem_impressao_digital_baixa_tudo_uma_vez():
    """Dado guardado antes da mudança (sem impressão digital): baixa uma vez e passa a conferir."""
    cache, clock, origin = make()
    cache._store.set("lexflow:q", Entry(data=[{"velho": True}], fetched_at=clock.now))

    async def go():
        clock.now += 300 + 600 + 1
        first = await ler(cache, origin)
        clock.now += 300 + 600 + 1
        return first, await ler(cache, origin)

    first, after = run(go())
    assert first.data == [{"query": "q", "versao": 1}]
    assert origin.downloads == 1
    assert after.data is first.data


def test_conferencia_que_nao_devolve_linhas_sem_base_baixa_tudo():
    """Defesa: uma fonte que responde "igual" sem ter com o que comparar não deixa o cache sem dado."""
    cache, _clock, origin = make()

    async def maluca(_known):
        return None, "fp?"

    entry = run(cache.get("lexflow:q", lambda: origin.fetch("q"), maluca))
    assert entry.data == [{"query": "q", "versao": 1}]
    assert entry.fingerprint is None


def test_banco_fora_do_ar_na_conferencia_serve_o_ultimo_dado_bom():
    cache, clock, origin = make()

    async def go():
        first = await ler(cache, origin)
        origin.fail = True
        clock.now += 300 + 600 + 1
        return first, await ler(cache, origin)

    first, after = run(go())
    assert after is first


def test_redis_antigo_sem_os_campos_novos_continua_valendo():
    """Entry gravado no Redis antes desta versão (sem fingerprint/version) é lido sem erro."""
    old = Entry(data=[{"a": 1}], fetched_at=10.0)
    state = dict(old.__dict__)
    del state["fingerprint"], state["version"]
    restored = Entry.__new__(Entry)
    restored.__dict__.update(state)  # o que o pickle faz com o objeto gravado pela versão antiga
    restored = pickle.loads(pickle.dumps(restored))
    assert restored.fingerprint is None
    assert restored.data_version == 10.0


def test_memoria_dos_calculos_ve_a_versao_do_dado_e_nao_a_hora_da_conferencia():
    cache, clock, origin = make()

    async def go():
        fetcher = CachedSourceFetcher(cache, origin, "lexflow")
        v1 = await fetcher.version("q")
        clock.now += 300 + 600 + 1
        v2 = await fetcher.version("q")  # conferido, sem mudança
        origin.version = 2
        clock.now += 300 + 600 + 1
        v3 = await fetcher.version("q")  # mudou: versão nova
        return fetcher, v1, v2, v3

    fetcher, v1, v2, v3 = run(go())
    assert v1 == v2 == 1000.0
    assert v3 == clock.now
    assert [v for _, v in fetcher.reads] == [v1, v2, v3]
    assert fetcher.synced_at() == 1000.0


# --- aquecedor -----------------------------------------------------------------------------------


def _modulo(db, *queries):
    async def build(ctx):
        return {}

    return DashboardModule(key=db, source_db=db, source_label=db, build=build, queries=queries)


def test_aquecedor_nao_renova_os_bancos_de_fora():
    modulos = [_modulo("lexpre", "a"), _modulo("lexflow", "b"), _modulo("ng", "c")]
    assert warm_targets(modulos, {"lexflow"}) == [("lexpre", "a"), ("ng", "c")]
    assert warm_targets(modulos) == [("lexpre", "a"), ("lexflow", "b"), ("ng", "c")]


def test_aquecedor_tambem_so_baixa_se_mudou():
    cache, _clock, origin = make()
    run(ler(cache, origin))  # alguém leu
    ok = run(
        warm_once(cache, lambda _db: origin, [("lexflow", "q")], lambda _db: True, lambda _k: True)
    )
    assert ok == 1
    assert origin.probes == 2
    assert origin.downloads == 1


# --- banco: impressão digital e busca condicional ------------------------------------------------


def test_impressao_digital_leva_o_hash_do_sql_e_aceita_ponto_e_virgula_no_fim():
    a = fingerprint_query("select 1 as x")
    b = fingerprint_query("select 1 as x;\n")
    c = fingerprint_query("select 1 as y")
    assert a == b
    assert a != c  # coluna renomeada: outra impressão digital, nunca reaproveita o dado antigo
    assert "hashtextextended(q::text, 0)" in a
    assert a.rstrip().endswith("select 1 as x\n) q")


class FakeConn:
    def __init__(self, fingerprint, rows):
        self.calls = []
        self._fingerprint = fingerprint
        self._rows = rows

    def transaction(self, **kwargs):
        conn = self

        class _Tx:
            async def __aenter__(self):
                conn.calls.append(("begin", kwargs))

            async def __aexit__(self, *exc):
                conn.calls.append(("end", {}))
                return False

        return _Tx()

    async def fetchval(self, query):
        self.calls.append(("fetchval", query))
        return self._fingerprint

    async def fetch(self, query):
        self.calls.append(("fetch", query))
        return self._rows


def test_busca_condicional_igual_nao_baixa_e_usa_a_mesma_foto_do_banco():
    conn = FakeConn("h:1:2", [{"a": 1}])
    rows, fp = run(fetch_read_only_if_changed(conn, "select a from t", "h:1:2"))
    assert rows is None and fp == "h:1:2"
    assert [c[0] for c in conn.calls] == ["begin", "fetchval", "end"]
    assert conn.calls[0][1] == {"readonly": True, "isolation": "repeatable_read"}


def test_busca_condicional_diferente_ou_sem_base_baixa_na_mesma_transacao():
    for known in (None, "outra"):
        conn = FakeConn("h:1:2", [{"a": 1}])
        rows, fp = run(fetch_read_only_if_changed(conn, "select a from t", known))
        assert rows == [{"a": 1}] and fp == "h:1:2"
        assert [c[0] for c in conn.calls] == ["begin", "fetchval", "fetch", "end"]
        assert conn.calls[2] == ("fetch", "select a from t")


# --- configuração --------------------------------------------------------------------------------


def test_padroes_contra_o_egress_do_lexflow():
    s = Settings(_env_file=None)
    assert s.source_cache_ttl_by_db == {"lexflow": 900}
    assert s.source_cache_probe_dbs == {"lexflow"}
    assert s.source_cache_warm_skip == {"lexflow"}


def test_listas_vazias_desligam():
    s = Settings(_env_file=None, SOURCE_CACHE_PROBE="", SOURCE_CACHE_WARM_SKIP=" ")
    assert s.source_cache_probe_dbs == frozenset()
    assert s.source_cache_warm_skip == frozenset()
    s = Settings(_env_file=None, SOURCE_CACHE_PROBE=" LexFlow , ng ")
    assert s.source_cache_probe_dbs == {"lexflow", "ng"}
