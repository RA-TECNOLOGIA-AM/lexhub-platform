"""Liga/desliga das fontes (app.data_sources.enabled), checado ANTES do cache.

Fonte desligada não é lida, nem do cache: o SourceCache serve o último dado bom quando a fonte falha
(até 1 h), então a trava fica por fora dele (GuardedSourceFetcher embrulha o CachedSourceFetcher).

  * DisabledRepo      as keys desligadas, do banco da plataforma;
  * SourceSwitch      guarda essa lista por `ttl` (30 s). Ligar/desligar pela API limpa na hora nesta
                      réplica (invalidate); nas outras, vale em até `ttl`;
  * GuardedSourceFetcher  o SourceFetcher que levanta SourceDisabled para fonte desligada.
Os bancos do .env (LexPre, LexFlow, NG, LAADV) não são desligáveis pela tela e nem passam aqui.
"""

import logging
import time
from collections.abc import Callable
from typing import Any, Protocol

import asyncpg

from app.dashboards.base import SourceFetcher
from app.database import SourceDisabled, SourceUnavailable

logger = logging.getLogger(__name__)


class DisabledRepo(Protocol):
    async def disabled_keys(self) -> set[str]: ...


_DISABLED_SQL = "select key from app.data_sources where active and not enabled"


class PgDisabledRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def disabled_keys(self) -> set[str]:
        return {r["key"] for r in await self._pool.fetch(_DISABLED_SQL)}


class SourceSwitch:
    def __init__(
        self, repo: DisabledRepo, *, ttl: float = 30, clock: Callable[[], float] = time.monotonic
    ):
        self._repo = repo
        self._ttl = ttl
        self._clock = clock
        self._keys: set[str] | None = None
        self._loaded_at = 0.0

    async def is_disabled(self, key: str) -> bool:
        """Sem conseguir ler a lista = SourceUnavailable (não arrisca ler uma fonte desligada)."""
        if self._keys is None or self._clock() - self._loaded_at >= self._ttl:
            try:
                self._keys = await self._repo.disabled_keys()
            except Exception as exc:
                logger.warning("Não leu as fontes desligadas (%s)", type(exc).__name__)
                raise SourceUnavailable(key) from exc
            self._loaded_at = self._clock()
        return key in self._keys

    def invalidate(self) -> None:
        """Alguém ligou ou desligou uma fonte: a próxima leitura busca a lista de novo."""
        self._keys = None


class GuardedSourceFetcher:
    """SourceFetcher que recusa fonte desligada antes de ir ao cache ou à fonte."""

    def __init__(self, switch: SourceSwitch, inner: SourceFetcher, db_name: str):
        self._switch = switch
        self._inner = inner
        self._db = db_name

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        if await self._switch.is_disabled(self._db):
            raise SourceDisabled(self._db)
        return await self._inner.fetch(query_name)

    def synced_at(self) -> float | None:
        return self._inner.synced_at()
