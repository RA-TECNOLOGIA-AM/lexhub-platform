import asyncio
import logging

import asyncpg
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.platform_db import (
    MAX_INACTIVE_CONNECTION_LIFETIME,
    PLATFORM_DB_ATTEMPTS,
    keep_warm,
    open_platform_pool,
    ping_connections,
)

BASE = {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "pk"}
URL = "postgresql://u:p@pooler.invalid:6543/postgres"


def settings(**env) -> Settings:
    return Settings(_env_file=None, **BASE, **env)


async def _no_wait(_seconds: float) -> None:
    return None


# --- Abertura do pool ---------------------------------------------------------------------


def test_pool_da_plataforma_tem_tempo_limite_proprio_e_conexoes_minimas():
    seen: dict = {}

    async def create_pool(dsn, **kwargs):
        seen.update(kwargs, dsn=dsn)
        return "pool"

    assert asyncio.run(open_platform_pool(settings(DATABASE_URL=URL), create_pool=create_pool))
    assert seen["dsn"] == URL
    # 30 s para abrir conexão (antes, os 10 s dos bancos de origem davam 500 com o pooler lento).
    assert seen["timeout"] == 30.0
    assert (seen["min_size"], seen["max_size"]) == (2, 10)
    # Abaixo dos 350 s em que o balanceador da AWS corta conexão TCP ociosa.
    assert seen["max_inactive_connection_lifetime"] == MAX_INACTIVE_CONNECTION_LIFETIME < 350
    assert seen["statement_cache_size"] == 0  # pooler em modo transaction


def test_sem_database_url_nao_abre_pool():
    async def create_pool(*_args, **_kwargs):
        raise AssertionError("não devia conectar")

    assert asyncio.run(open_platform_pool(settings(), create_pool=create_pool)) is None


def test_banco_da_plataforma_fora_impede_a_subida_com_mensagem_clara():
    tentativas = {"n": 0}

    async def recusa(*_args, **_kwargs):
        tentativas["n"] += 1
        raise ConnectionRefusedError("recusado")

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        asyncio.run(
            open_platform_pool(settings(DATABASE_URL=URL), create_pool=recusa, sleep=_no_wait)
        )
    assert tentativas["n"] == PLATFORM_DB_ATTEMPTS


def test_minimo_maior_que_maximo_e_erro_de_configuracao():
    with pytest.raises(ValidationError, match="PLATFORM_DB_POOL_MIN_SIZE"):
        settings(PLATFORM_DB_POOL_MIN_SIZE=5, PLATFORM_DB_POOL_MAX_SIZE=3)


# --- Conexões quentes ---------------------------------------------------------------------


class FakeConn:
    def __init__(self, fail: Exception | None = None):
        self.fail = fail
        self.pings = 0

    async def fetchval(self, query, timeout=None):
        assert query == "select 1"
        self.pings += 1
        if self.fail is not None:
            raise self.fail
        return 1


class FakePool:
    """Entrega uma conexão diferente a cada acquire simultâneo, como o pool do asyncpg."""

    def __init__(self, conns: list[FakeConn]):
        self.free = list(conns)
        self.acquired = 0
        self.timeouts: list[float] = []

    def acquire(self, timeout=None):
        pool = self
        pool.timeouts.append(timeout)

        class _Ctx:
            async def __aenter__(self):
                pool.acquired += 1
                conn = pool.free.pop()
                self.conn = conn
                await asyncio.sleep(0)  # deixa os outros acquires simultâneos acontecerem
                return conn

            async def __aexit__(self, *exc):
                pool.free.append(self.conn)
                return False

        return _Ctx()


def test_teste_das_conexoes_usa_cada_conexao_minima_uma_vez():
    conns = [FakeConn(), FakeConn()]
    pool = FakePool(conns)
    assert asyncio.run(ping_connections(pool, 2, timeout=30)) == 2
    assert [c.pings for c in conns] == [1, 1]  # as duas, não a mesma duas vezes
    assert pool.timeouts == [30, 30]


def test_conexao_morta_no_teste_e_avisada_numa_linha(caplog):
    morta = FakeConn(fail=asyncpg.ConnectionDoesNotExistError("caiu"))
    pool = FakePool([FakeConn(), morta])
    with caplog.at_level(logging.WARNING, logger="app.platform_db"):
        assert asyncio.run(ping_connections(pool, 2, timeout=30)) == 1
    [aviso] = [r for r in caplog.records if r.name == "app.platform_db"]
    assert "1 de 2 conexões não responderam" in aviso.getMessage()
    assert aviso.exc_info is None


def test_keep_warm_repete_e_sobrevive_a_falhas():
    pool = FakePool([FakeConn(fail=OSError("rede")), FakeConn()])
    ciclos = {"n": 0}

    async def sleep(_interval):
        ciclos["n"] += 1
        if ciclos["n"] > 3:
            raise asyncio.CancelledError  # para o laço depois de 3 ciclos

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(keep_warm(pool, 2, interval=60, timeout=30, sleep=sleep))
    assert pool.acquired == 6  # 3 ciclos x 2 conexões, mesmo com uma falhando sempre


# --- 503 em vez de 500 --------------------------------------------------------------------


@pytest.mark.parametrize(
    "erro",
    [
        TimeoutError(),
        ConnectionRefusedError("recusado"),
        asyncpg.ConnectionDoesNotExistError("caiu"),
    ],
)
def test_sem_conexao_com_o_banco_vira_503(client, erro):
    async def rota():
        raise erro

    client.app.add_api_route("/_teste_banco", rota)
    r = client.get("/_teste_banco")
    assert r.status_code == 503
    assert r.json() == {
        "detail": "Banco de dados indisponível no momento. Tente de novo em instantes."
    }
    assert r.headers["retry-after"] == "5"
