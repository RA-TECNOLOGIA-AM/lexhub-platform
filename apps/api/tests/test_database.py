import asyncio

import asyncpg
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import (
    DatabaseManager,
    SourceUnavailable,
    fetch_read_only,
    get_databases,
    reconnect_delay,
    run_with_connection_retry,
)
from app.sources import PgSourceFetcher

BASE = {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "pk"}
# Porta 1 no localhost: conexão recusada na hora.
DOWN = "postgresql://u:p@127.0.0.1:1/db"


def settings(**env) -> Settings:
    return Settings(_env_file=None, **BASE, **env)


async def _no_wait(_seconds: float) -> None:
    return None


@pytest.fixture
def sem_espera(monkeypatch):
    """Tentativas de uma consulta sem esperar entre elas (só nos testes sem tarefa de fundo)."""
    monkeypatch.setattr("app.database.asyncio.sleep", _no_wait)


async def wait_for(condition, timeout: float = 5.0) -> None:
    """Espera as tarefas de fundo chegarem num estado (falha o teste se demorar)."""

    async def loop():
        while not condition():
            await asyncio.sleep(0.01)

    await asyncio.wait_for(loop(), timeout)


# --- Peças de mentira: pool, conexão e "create_pool" ---------------------------------------


class FakeConn:
    """Conexão de mentira: registra a ordem das chamadas (transação, consulta, fim).

    Imita o proxy do pool do asyncpg: depois de devolvida (`released`), recusa chamadas.
    """

    def __init__(self, rows=None, closed: bool = False):
        self.calls: list[str] = []
        self._rows = rows or []
        self.closed = closed
        self.released = False

    def is_closed(self) -> bool:
        if self.released:
            raise asyncpg.InterfaceError(
                "cannot call Connection.is_closed(): connection has been released back to the pool"
            )
        return self.closed

    def transaction(self, **kwargs):
        conn = self

        class _Tx:
            async def __aenter__(self):
                conn.calls.append(f"begin readonly={kwargs.get('readonly')}")

            async def __aexit__(self, *exc):
                conn.calls.append("end")
                return False

        return _Tx()

    async def fetch(self, query):
        self.calls.append(f"fetch {query}")
        return self._rows

    async def fetchval(self, query, timeout=None):
        self.calls.append(f"fetchval {query}")
        return 1


class _Acquire:
    """Imita o pool.acquire() do asyncpg: serve com `await` e com `async with`."""

    def __init__(self, pool):
        self._pool = pool

    async def _get(self):
        if self._pool.fail_acquire is not None:
            raise self._pool.fail_acquire
        return self._pool.conn

    def __await__(self):
        return self._get().__await__()

    async def __aenter__(self):
        return await self._get()

    async def __aexit__(self, *exc):
        return False


class FakePool:
    def __init__(self, fail_acquire: Exception | None = None):
        self.conn = FakeConn()
        self.fail_acquire = fail_acquire
        self.expired = 0
        self.released = 0
        self.closed = False

    def acquire(self, timeout=None):
        return _Acquire(self)

    async def release(self, conn):
        self.released += 1

    async def expire_connections(self):
        self.expired += 1

    async def close(self):
        self.closed = True

    def terminate(self):
        self.closed = True


class PoolFactory:
    """No lugar do asyncpg.create_pool: recusa as `failures` primeiras tentativas."""

    def __init__(self, failures: int = 0, pool: FakePool | None = None):
        self.failures = failures
        self.pool = pool or FakePool()
        self.calls = 0
        self.kwargs: dict = {}

    async def __call__(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        if self.calls <= self.failures:
            raise ConnectionRefusedError("recusado")
        return self.pool


# --- Subida e reconexão ---------------------------------------------------------------------


def test_sem_variaveis_todos_desligados():
    async def run():
        manager = DatabaseManager(settings())
        manager.start()
        assert manager.status() == {"ng": "off", "laadv": "off", "lexflow": "off", "lexpre": "off"}
        await manager.close()

    asyncio.run(run())


def test_banco_fora_do_ar_nao_segura_a_subida_e_fica_down():
    async def run():
        manager = DatabaseManager(settings(DB_NG_URL=DOWN), delay=lambda _n: 3600)
        manager.start()  # volta na hora, sem esperar o banco
        assert manager.status()["ng"] == "connecting"
        await wait_for(lambda: manager.status()["ng"] == "down")
        with pytest.raises(SourceUnavailable):
            manager.get_pool("ng")
        await manager.close()  # cancela a reconexão (que esperaria 1 h)

    asyncio.run(run())


def test_reconecta_sozinho_quando_o_banco_volta():
    async def run():
        factory = PoolFactory(failures=2)
        manager = DatabaseManager(settings(DB_NG_URL=DOWN), create_pool=factory, delay=lambda _n: 0)
        manager.start()
        await wait_for(lambda: manager.is_up("ng"))
        assert factory.calls == 3
        assert manager.get_pool("ng") is factory.pool
        # Cada conexão nova tem o tempo limite curto (DB_CONNECT_TIMEOUT), não os 120 s da v1.
        assert factory.kwargs["timeout"] == 10.0
        await manager.close()
        assert factory.pool.closed

    asyncio.run(run())


def test_banco_que_cai_depois_de_conectado_fica_down_e_volta_sozinho():
    async def run():
        pool = FakePool()
        manager = DatabaseManager(
            settings(DB_NG_URL=DOWN), create_pool=PoolFactory(pool=pool), delay=lambda _n: 0
        )
        manager.start()
        await wait_for(lambda: manager.is_up("ng"))

        pool.fail_acquire = ConnectionResetError("caiu")
        with pytest.raises(SourceUnavailable):
            async with manager.get_connection("ng"):
                pass
        assert manager.status()["ng"] == "down"
        # Fora do ar: a próxima consulta falha na hora, sem tentar conectar de novo.
        with pytest.raises(SourceUnavailable):
            manager.get_pool("ng")

        pool.fail_acquire = None  # o banco voltou
        await wait_for(lambda: manager.is_up("ng"))
        assert pool.expired >= 1  # trocou as conexões antigas antes de conferir
        assert "fetchval select 1" in pool.conn.calls
        await manager.close()

    asyncio.run(run())


def test_get_connection_devolve_a_conexao_ao_pool():
    async def run():
        pool = FakePool()
        manager = DatabaseManager(settings(DB_NG_URL=DOWN), create_pool=PoolFactory(pool=pool))
        manager.start()
        await wait_for(lambda: manager.is_up("ng"))
        async with manager.get_connection("ng") as conn:
            assert conn is pool.conn
        assert pool.released == 1
        await manager.close()

    asyncio.run(run())


def test_get_pool_de_banco_desligado_da_source_unavailable():
    with pytest.raises(SourceUnavailable, match="laadv"):
        DatabaseManager(settings()).get_pool("laadv")


def test_espera_de_reconexao_cresce_ate_1_minuto():
    assert 0.8 <= reconnect_delay(1) <= 1.2
    assert 3.2 <= reconnect_delay(3) <= 4.8
    assert 48 <= reconnect_delay(30) <= 72


# --- Tentativas de uma consulta -------------------------------------------------------------


class FakeManager:
    """Gerenciador de mentira: entrega a 'conexão', conta renovações e quedas informadas."""

    def __init__(self, conn=None):
        self.conn = conn
        self.expired = 0
        self.failures: list[tuple[str, str]] = []

    async def expire_connections(self, _name):
        self.expired += 1

    def report_failure(self, name, exc):
        self.failures.append((name, type(exc).__name__))

    def get_connection(self, _name):
        conn = self.conn

        class _Ctx:
            async def __aenter__(self):
                if conn is not None:
                    conn.released = False
                return conn

            async def __aexit__(self, *exc):
                if conn is not None:
                    conn.released = True  # como o pool: devolvida, a conexão recusa chamadas
                return False

        return _Ctx()


def test_retry_refaz_em_falha_transitoria_e_renova_as_conexoes(sem_espera):
    manager = FakeManager()
    calls = {"n": 0}

    async def operation(_conn):
        calls["n"] += 1
        if calls["n"] < 3:
            raise asyncpg.PostgresConnectionError("caiu")
        return "ok"

    assert asyncio.run(run_with_connection_retry(manager, "ng", operation)) == "ok"
    assert calls["n"] == 3
    assert manager.expired == 2
    assert manager.failures == []


def test_retry_sem_conexao_ate_o_limite_marca_o_banco_fora(sem_espera):
    manager = FakeManager()

    async def operation(_conn):
        raise asyncpg.PostgresConnectionError("caiu")

    with pytest.raises(SourceUnavailable):
        asyncio.run(run_with_connection_retry(manager, "ng", operation, max_retries=2))
    assert manager.failures == [("ng", "PostgresConnectionError")]


def test_consulta_cancelada_pelo_banco_vira_source_unavailable_sem_derrubar(sem_espera):
    # Visto no LexFlow: o statement_timeout do servidor cancelou execucao_LA após 3 min.
    manager = FakeManager()
    calls = {"n": 0}

    async def operation(_conn):
        calls["n"] += 1
        raise asyncpg.QueryCanceledError("canceling statement due to statement timeout")

    with pytest.raises(SourceUnavailable) as caught:
        asyncio.run(run_with_connection_retry(manager, "lexflow", operation))
    assert isinstance(caught.value.__cause__, asyncpg.QueryCanceledError)
    assert calls["n"] == 1  # repetir só esperaria o mesmo limite de novo
    assert manager.failures == []


# Visto no LexFlow: a conexão caiu no meio e o erro original ficou escondido atrás deste.
CLOSED = "cannot call Transaction.__aexit__(): the underlying connection is closed"


def test_interface_error_com_conexao_fechada_tenta_de_novo(sem_espera):
    manager = FakeManager(FakeConn(closed=True))
    calls = {"n": 0}

    async def operation(_conn):
        calls["n"] += 1
        if calls["n"] == 1:
            raise asyncpg.InterfaceError(CLOSED)
        return "ok"

    assert asyncio.run(run_with_connection_retry(manager, "lexflow", operation)) == "ok"
    assert calls["n"] == 2
    assert manager.expired == 1  # pegou conexões novas antes de tentar de novo
    assert manager.failures == []


def test_interface_error_com_conexao_aberta_nao_e_repetido(sem_espera):
    manager = FakeManager(FakeConn(closed=False))
    calls = {"n": 0}

    async def operation(_conn):
        calls["n"] += 1
        raise asyncpg.InterfaceError("erro de uso da conexão")

    with pytest.raises(asyncpg.InterfaceError):
        asyncio.run(run_with_connection_retry(manager, "lexflow", operation))
    assert calls["n"] == 1  # é bug, não falha transitória
    assert manager.expired == 0
    assert manager.failures == []


def test_conexao_fechada_ate_o_limite_marca_o_banco_fora(sem_espera):
    manager = FakeManager(FakeConn(closed=True))

    async def operation(_conn):
        raise asyncpg.InterfaceError(CLOSED)

    with pytest.raises(SourceUnavailable) as caught:
        asyncio.run(run_with_connection_retry(manager, "lexflow", operation, max_retries=2))
    assert manager.failures == [("lexflow", "ConnectionLost")]
    # A cadeia guarda o erro original do asyncpg para o log.
    assert isinstance(caught.value.__cause__.__cause__, asyncpg.InterfaceError)


def test_retry_cache_de_statement_velho_esgota_sem_marcar_o_banco_fora(sem_espera):
    manager = FakeManager()

    async def operation(_conn):
        raise asyncpg.InvalidCachedStatementError("plano velho")

    with pytest.raises(asyncpg.InvalidCachedStatementError):
        asyncio.run(run_with_connection_retry(manager, "ng", operation, max_retries=2))
    assert manager.failures == []


def test_consulta_lenta_vira_source_unavailable_sem_derrubar_o_banco(sem_espera):
    manager = FakeManager()
    calls = {"n": 0}

    async def operation(_conn):
        calls["n"] += 1
        raise TimeoutError

    with pytest.raises(SourceUnavailable):
        asyncio.run(run_with_connection_retry(manager, "ng", operation))
    assert calls["n"] == 1  # lentidão não se repete: o cache serve o último dado bom
    assert manager.failures == []


def test_fetch_read_only_roda_a_consulta_dentro_de_transacao_so_leitura():
    # SET de sessão se perde atrás de PgBouncer em modo transação; BEGIN READ ONLY não.
    conn = FakeConn(rows=[{"id": 1}])
    rows = asyncio.run(fetch_read_only(conn, "select 1"))
    assert rows == [{"id": 1}]
    assert conn.calls == ["begin readonly=True", "fetch select 1", "end"]


def test_pg_source_fetcher_busca_em_transacao_so_leitura():
    conn = FakeConn(rows=[{"x": 1}])
    queries = {"q": {"database": "ng", "query": "select x from t"}}
    fetcher = PgSourceFetcher(FakeManager(conn), "ng", queries)
    assert asyncio.run(fetcher.fetch("q")) == [{"x": 1}]
    assert conn.calls == ["begin readonly=True", "fetch select x from t", "end"]


def test_pg_source_fetcher_de_banco_desligado_da_source_unavailable():
    queries = {"q": {"database": "ng", "query": "select 1"}}
    fetcher = PgSourceFetcher(DatabaseManager(settings()), "ng", queries)
    with pytest.raises(SourceUnavailable):
        asyncio.run(fetcher.fetch("q"))


# --- A API com bancos fora do ar ------------------------------------------------------------


def test_api_sobe_e_responde_com_banco_de_origem_fora_do_ar(monkeypatch):
    monkeypatch.setenv("DB_NG_URL", DOWN)
    get_settings.cache_clear()
    from app.main import create_app

    try:
        with TestClient(create_app()) as c:
            assert c.get("/health").status_code == 200
            r = c.get("/health/sources")
            assert r.status_code == 503
            assert r.json()["databases"]["ng"] in ("connecting", "down")
            assert r.json()["databases"]["laadv"] == "off"
    finally:
        get_settings.cache_clear()


def test_health_sources_sem_bancos_configurados(client):
    r = client.get("/health/sources")
    assert r.status_code == 200
    assert r.json() == {
        "status": "ok",
        "databases": {"ng": "off", "laadv": "off", "lexflow": "off", "lexpre": "off"},
    }


def test_health_sources_503_se_algum_configurado_nao_esta_no_ar(client):
    class Manager:
        def status(self):
            return {"ng": "down", "laadv": "up", "lexflow": "connecting", "lexpre": "off"}

    client.app.dependency_overrides[get_databases] = Manager
    r = client.get("/health/sources")
    assert r.status_code == 503
    assert r.json() == {"status": "error", "databases": Manager().status()}


def test_banco_da_plataforma_fora_impede_a_subida_com_mensagem_clara(monkeypatch):
    from app import main

    tentativas = {"n": 0}

    async def recusa(*_args, **_kwargs):
        tentativas["n"] += 1
        raise ConnectionRefusedError("recusado")

    monkeypatch.setattr(main.asyncpg, "create_pool", recusa)
    monkeypatch.setattr(main.asyncio, "sleep", _no_wait)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        asyncio.run(main._open_platform_db(settings(DATABASE_URL=DOWN)))
    assert tentativas["n"] == main.PLATFORM_DB_ATTEMPTS
