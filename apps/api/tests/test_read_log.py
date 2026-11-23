"""Registro de leituras: quando cada query foi lida do banco (ou falhou), em memória e no Redis.

É o que mantém a hora do hub e da tela de fontes depois de um deploy ou reload: os dados já
sobreviviam no Redis, a hora não.
"""

import asyncio
from typing import Any

from app.read_log import Read, ReadLog


class FakeShared:
    """Redis falso (mesma interface do CacheService): guarda tudo e conta as gravações."""

    def __init__(self):
        self.data: dict[str, Any] = {}
        self.sets: list[tuple[str, int]] = []

    async def get(self, key: str) -> Any | None:
        return self.data.get(key)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        self.data[key] = value
        self.sets.append((key, ttl))

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self.data.pop(k, None)


def run(coro):
    return asyncio.run(coro)


def test_leitura_boa_fica_na_memoria_e_vai_para_o_redis_uma_chave_por_banco():
    shared = FakeShared()
    log = ReadLog(shared)

    run(log.ok("lexflow:setor_recurso_NG", 100.0))
    run(log.ok("lexflow:setor_recurso_NG@27", 200.0))

    assert run(log.of_db("lexflow")) == {
        "setor_recurso_NG": Read(ok_at=100.0),
        "setor_recurso_NG@27": Read(ok_at=200.0),
    }
    assert set(shared.data) == {"reads:lexflow"}
    assert all(ttl == 7 * 86_400 for _, ttl in shared.sets)


def test_depois_do_restart_a_hora_volta_do_redis():
    shared = FakeShared()
    run(ReadLog(shared).ok("ng:actions_NG_2", 500.0))

    novo = ReadLog(shared)  # API reiniciou: memória vazia

    assert run(novo.ok_at("ng:actions_NG_2")) == 500.0
    assert run(novo.ok_at("ng:outra")) is None


def test_falha_guarda_o_tipo_e_mantem_a_ultima_leitura_boa():
    log = ReadLog(FakeShared())
    run(log.ok("ng:q", 100.0))

    run(log.failed("ng:q", 150.0, "TimeoutError"))

    assert run(log.of_db("ng")) == {"q": Read(ok_at=100.0, fail_at=150.0, error="TimeoutError")}

    run(log.ok("ng:q", 200.0))  # leitura boa depois: a falha some
    assert run(log.of_db("ng")) == {"q": Read(ok_at=200.0)}


def test_redis_desligado_funciona_so_em_memoria():
    from app.cache import NullCache

    log = ReadLog(NullCache())
    run(log.ok("lexpre:q", 10.0))

    assert run(log.ok_at("lexpre:q")) == 10.0


def test_esquecer_apaga_a_fonte_da_memoria_e_do_redis():
    shared = FakeShared()
    log = ReadLog(shared)
    run(log.ok("gs_mc_1:aba", 100.0))
    run(log.ok("ng:q", 100.0))

    run(log.forget("gs_mc_1"))

    assert run(log.of_db("gs_mc_1")) == {}
    assert "reads:gs_mc_1" not in shared.data
    assert run(ReadLog(shared).ok_at("gs_mc_1:aba")) is None  # depois do restart também
    assert run(log.ok_at("ng:q")) == 100.0


def test_redis_so_e_lido_uma_vez_por_banco():
    shared = FakeShared()
    calls = []
    original = shared.get

    async def counting_get(key):
        calls.append(key)
        return await original(key)

    shared.get = counting_get
    log = ReadLog(shared)

    for _ in range(3):
        run(log.ok_at("ng:q"))

    assert calls == ["reads:ng"]
