import asyncio

import asyncpg
import pytest

from app.config import Settings
from app.database import DatabaseManager, run_with_connection_retry

BASE = {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "pk"}
# Porta 1 no localhost: conexão recusada na hora.
DOWN = "postgresql://u:p@127.0.0.1:1/db"


def settings(**env) -> Settings:
    return Settings(_env_file=None, **BASE, **env)


async def _no_wait(_seconds: float) -> None:
    return None


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr("app.database.asyncio.sleep", _no_wait)  # sem esperar entre tentativas


def test_sem_variaveis_todos_desligados():
    manager = DatabaseManager(settings())
    asyncio.run(manager.initialize())
    assert manager.status() == {"ng": "off", "laadv": "off", "lexflow": "off", "lexpre": "off"}


def test_obrigatorio_fora_do_ar_impede_a_subida_como_na_v1():
    manager = DatabaseManager(settings(DB_NG_URL=DOWN))
    with pytest.raises(RuntimeError, match="'ng'"):
        asyncio.run(manager.initialize())
    assert manager.status()["ng"] == "down"


def test_obrigatorio_fora_do_ar_nao_impede_os_outros_de_tentar():
    # NG obrigatório cai; LEXPRE (opcional) também; os dois são tentados e marcados antes do erro.
    manager = DatabaseManager(settings(DB_NG_URL=DOWN, DB_LEXPRE_URL=DOWN))
    with pytest.raises(RuntimeError, match="'ng'"):
        asyncio.run(manager.initialize())
    assert manager.status() == {"ng": "down", "laadv": "off", "lexflow": "off", "lexpre": "down"}


def test_lexpre_e_opcional_como_na_v1():
    manager = DatabaseManager(settings(DB_LEXPRE_URL=DOWN))
    asyncio.run(manager.initialize())
    assert manager.status()["lexpre"] == "down"


def test_get_pool_de_banco_nao_aberto_da_erro():
    with pytest.raises(ValueError, match="'laadv'"):
        DatabaseManager(settings()).get_pool("laadv")


class FakePool:
    def __init__(self):
        self.expired = 0

    async def expire_connections(self):
        self.expired += 1


class FakeManager:
    """Gerenciador de mentira: entrega uma 'conexão' e conta as expirações do pool."""

    def __init__(self):
        self.pool = FakePool()

    def get_pool(self, _name):
        return self.pool

    def get_connection(self, _name):
        manager = self

        class _Ctx:
            async def __aenter__(self):
                return manager

            async def __aexit__(self, *exc):
                return False

        return _Ctx()


def test_retry_refaz_em_falha_transitoria_e_expira_o_pool():
    manager = FakeManager()
    calls = {"n": 0}

    async def operation(_conn):
        calls["n"] += 1
        if calls["n"] < 3:
            raise asyncpg.PostgresConnectionError("caiu")
        return "ok"

    assert asyncio.run(run_with_connection_retry(manager, "ng", operation)) == "ok"
    assert calls["n"] == 3
    assert manager.pool.expired == 2


def test_retry_desiste_depois_do_limite():
    manager = FakeManager()

    async def operation(_conn):
        raise asyncpg.PostgresConnectionError("caiu")

    with pytest.raises(asyncpg.PostgresConnectionError):
        asyncio.run(run_with_connection_retry(manager, "ng", operation, max_retries=2))


def test_health_sources_sem_bancos_configurados(client):
    r = client.get("/health/sources")
    assert r.status_code == 200
    assert r.json() == {
        "status": "ok",
        "databases": {"ng": "off", "laadv": "off", "lexflow": "off", "lexpre": "off"},
    }
