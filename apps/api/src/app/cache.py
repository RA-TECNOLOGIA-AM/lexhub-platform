"""Cache compartilhado (L2) no Redis, no padrão da v1 (api_dashboards/src/app/cache.py).

Mesmas regras da v1:
  * desligado por padrão (CACHE_ENABLED); ligado, conecta na primeira chamada (lazy) com `ping`;
  * valores em pickle (preserva Decimal, date, datetime das linhas do asyncpg, que o JSON perderia);
  * chaves com prefixo da aplicação (v1: "api_dashboards:", aqui CACHE_KEY_PREFIX);
  * TTL por chave, definido por quem grava (v1: CACHE_TTL_HEAVY 600 s / CACHE_TTL_DEFAULT 300 s);
  * Redis fora do ar NUNCA derruba a requisição: loga e responde "não tenho" (cai no banco).

Melhorias sobre a v1:
  * depois de uma falha, só tenta reconectar após `retry_after` s (a v1 tentava a cada chamada e
    cada requisição pagava os 2 s de timeout de conexão);
  * o log mostra só host/porta/banco, nunca a senha que pode vir na REDIS_URL;
  * `delete` para invalidar chaves nas escritas (a v1 só lia e gravava).

Peças trocáveis (mesma interface `CacheService`):
  * RedisCache  produção;
  * NullCache   cache desligado (e nos testes): nunca guarda nada.
"""

import logging
import pickle
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol
from urllib.parse import urlsplit

from fastapi import Request

from app.config import Settings

logger = logging.getLogger(__name__)

Clock = Callable[[], float]
ClientFactory = Callable[[], Any]  # devolve um cliente redis.asyncio (ou um falso nos testes)


class CacheService(Protocol):
    async def get(self, key: str) -> Any | None:
        """Valor guardado; None = ausente, expirado ou cache indisponível."""
        ...

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Guarda por `ttl` segundos. Silencioso em caso de falha."""
        ...

    async def delete(self, *keys: str) -> None:
        """Invalida as chaves. Silencioso em caso de falha."""
        ...

    async def status(self) -> str:
        """'up', 'down' ou 'off' (desligado)."""
        ...

    async def close(self) -> None: ...


class NullCache:
    """Cache desligado: tudo é miss e nada é guardado."""

    async def get(self, key: str) -> Any | None:
        return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        return None

    async def delete(self, *keys: str) -> None:
        return None

    async def status(self) -> str:
        return "off"

    async def close(self) -> None:
        return None


def safe_redis_target(url: str) -> str:
    """host:porta/banco da REDIS_URL, sem usuário nem senha (para log)."""
    parts = urlsplit(url)
    db = parts.path.lstrip("/") or "0"
    return f"{parts.hostname or '?'}:{parts.port or 6379}/{db}"


class RedisCache:
    def __init__(
        self,
        url: str,
        prefix: str = "lexhub_platform:",
        timeout: float = 2.0,
        retry_after: float = 30.0,
        client_factory: ClientFactory | None = None,
        clock: Clock = time.monotonic,
    ):
        self._url = url
        self._prefix = prefix
        self._timeout = timeout
        self._retry_after = retry_after
        self._factory = client_factory or self._default_factory
        self._clock = clock
        self._client: Any = None
        self._next_try = 0.0  # antes disso, nem tenta conectar (Redis caiu há pouco)

    def _default_factory(self) -> Any:
        # Importação lazy, como na v1: sem o pacote instalado, só o Redis fica desligado.
        import redis.asyncio as aioredis

        return aioredis.from_url(
            self._url,
            decode_responses=False,
            socket_connect_timeout=self._timeout,
            socket_timeout=self._timeout,
            retry_on_timeout=False,
        )

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if self._clock() < self._next_try:
            return None
        client = None
        try:
            client = self._factory()
            await client.ping()
        except Exception as exc:  # noqa: BLE001 (Redis nunca derruba a requisição)
            self._next_try = self._clock() + self._retry_after
            logger.warning(
                "Redis indisponível em %s (%s); seguindo só com o cache em memória, "
                "nova tentativa em %.0f s",
                safe_redis_target(self._url),
                type(exc).__name__,
                self._retry_after,
            )
            await _close_quietly(client)
            return None
        self._client = client
        logger.info("Redis conectado em %s", safe_redis_target(self._url))
        return client

    async def _failed(self, op: str, key: str, exc: Exception) -> None:
        """Falha no meio de uma operação: solta o cliente e espera `retry_after` para tentar de novo."""
        logger.warning(
            "Redis %s falhou para '%s' (%s); caindo no banco", op, key, type(exc).__name__
        )
        client, self._client = self._client, None
        self._next_try = self._clock() + self._retry_after
        await _close_quietly(client)

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        if client is None:
            return None
        try:
            raw = await client.get(self._key(key))
        except Exception as exc:  # noqa: BLE001 (Redis nunca derruba a requisição)
            await self._failed("GET", key, exc)
            return None
        if raw is None:
            return None
        try:
            return pickle.loads(raw)
        except Exception as exc:  # noqa: BLE001 (Redis nunca derruba a requisição)
            # Formato antigo/corrompido (ex.: classe renomeada): trata como miss.
            logger.warning("Redis: valor ilegível em '%s' (%s); ignorado", key, type(exc).__name__)
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        client = await self._get_client()
        if client is None or ttl <= 0:
            return
        try:
            raw = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            await client.setex(self._key(key), ttl, raw)
        except Exception as exc:  # noqa: BLE001 (Redis nunca derruba a requisição)
            await self._failed("SET", key, exc)

    async def delete(self, *keys: str) -> None:
        if not keys:
            return
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.delete(*(self._key(k) for k in keys))
        except Exception as exc:  # noqa: BLE001 (Redis nunca derruba a requisição)
            await self._failed("DEL", ",".join(keys), exc)

    async def status(self) -> str:
        client = await self._get_client()
        if client is None:
            return "down"
        try:
            await client.ping()
        except Exception as exc:  # noqa: BLE001 (Redis nunca derruba a requisição)
            await self._failed("PING", "-", exc)
            return "down"
        return "up"

    async def close(self) -> None:
        client, self._client = self._client, None
        await _close_quietly(client)


async def _close_quietly(client: Any) -> None:
    if client is None:
        return
    try:
        await client.aclose()
    except Exception:
        logger.debug("Redis: falha ao fechar o cliente", exc_info=True)


async def get_or_load(
    cache: CacheService, key: str, ttl: int, load: Callable[[], Awaitable[Any]]
) -> Any:
    """Cache-aside: do cache se houver; senão carrega da origem e guarda por `ttl` segundos."""
    cached = await cache.get(key)
    if cached is not None:
        return cached
    value = await load()
    await cache.set(key, value, ttl)
    return value


def get_cache(request: Request) -> CacheService:
    """Dependência FastAPI: o cache criado no lifespan (NullCache se a app subiu sem ele)."""
    return getattr(request.app.state, "cache", None) or NullCache()


def build_cache(settings: Settings) -> CacheService:
    if not settings.CACHE_ENABLED:
        return NullCache()
    return RedisCache(
        settings.REDIS_URL,
        prefix=settings.CACHE_KEY_PREFIX,
        timeout=settings.REDIS_SOCKET_TIMEOUT,
        retry_after=settings.REDIS_RETRY_AFTER,
    )
