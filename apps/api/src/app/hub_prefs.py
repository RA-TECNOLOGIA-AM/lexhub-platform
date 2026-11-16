"""Preferências do hub da pessoa numa organização: favoritos e ordem dos cards.

Dividido em partes trocáveis:
  * HubPrefsRepo        só lê e grava no banco (PgHubPrefsRepo em produção, um falso nos testes);
  * CachedHubPrefsRepo  o mesmo repo com cache-aside no Redis (lê do cache; toda escrita invalida);
  * clean_order         limpa a ordem recebida do front (função pura).
Tudo é por associação (memberships.id): a mesma pessoa tem preferências separadas em cada organização.
"""

from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends

from app.access import get_db_pool
from app.cache import CacheService, get_cache, get_or_load
from app.config import Settings, get_settings

MAX_ORDER = 200  # mesmo limite do banco (app.hub_orders.keys)


class HubPrefsRepo(Protocol):
    async def list_favorites(self, user_id: str, org_id: str) -> list[str]: ...

    # False = a pessoa não pode ver esse dashboard (inexistente, "em breve" ou sem acesso).
    async def add_favorite(self, user_id: str, org_id: str, dashboard_key: str) -> bool: ...

    async def remove_favorite(self, user_id: str, org_id: str, dashboard_key: str) -> None: ...

    async def get_order(self, user_id: str, org_id: str) -> list[str]: ...

    async def set_order(self, user_id: str, org_id: str, keys: list[str]) -> None: ...


def clean_order(keys: list[str]) -> list[str]:
    """Tira repetidos mantendo a primeira posição ('a','b','a' -> 'a','b')."""
    return list(dict.fromkeys(keys))


# --- Banco -----------------------------------------------------------------

# A associação ativa da pessoa na organização (já conferida pelo require_org).
_MEMBERSHIP = """
select m.id from app.memberships m
 where m.user_id = $1::uuid and m.org_id = $2::uuid and m.status = 'active'
"""

_LIST_FAVORITES_SQL = f"""
select f.dashboard_key
  from app.dashboard_favorites f
 where f.membership_id = ({_MEMBERSHIP})
 order by f.created_at, f.dashboard_key
"""

# Só favorita o que a pessoa pode abrir em alguma unidade (a mesma regra do catálogo).
# Devolve se podia; repetir o mesmo favorito não é erro.
_ADD_FAVORITE_SQL = f"""
with allowed as (
    select ({_MEMBERSHIP}) as membership_id
     where exists (
         select 1
           from app.org_dashboards od
           join app.units u             on u.id = od.unit_id and u.active
           join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
                                       and d.status = 'available'
          where od.org_id = $2::uuid and od.enabled and od.dashboard_key = $3
            and app_private.dashboard_scope($1::uuid, u.id, $3) is not null)
), saved as (
    insert into app.dashboard_favorites (membership_id, dashboard_key)
    select membership_id, $3 from allowed where membership_id is not null
    on conflict do nothing
)
select exists (select 1 from allowed where membership_id is not null)
"""

_REMOVE_FAVORITE_SQL = f"""
delete from app.dashboard_favorites
 where membership_id = ({_MEMBERSHIP}) and dashboard_key = $3
"""

_GET_ORDER_SQL = f"""
select o.keys from app.hub_orders o where o.membership_id = ({_MEMBERSHIP})
"""

_SET_ORDER_SQL = f"""
insert into app.hub_orders (membership_id, keys)
select ({_MEMBERSHIP}), $3::text[]
on conflict (membership_id) do update set keys = excluded.keys
"""


class PgHubPrefsRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def list_favorites(self, user_id: str, org_id: str) -> list[str]:
        return [
            r["dashboard_key"] for r in await self._pool.fetch(_LIST_FAVORITES_SQL, user_id, org_id)
        ]

    async def add_favorite(self, user_id: str, org_id: str, dashboard_key: str) -> bool:
        return await self._pool.fetchval(_ADD_FAVORITE_SQL, user_id, org_id, dashboard_key)

    async def remove_favorite(self, user_id: str, org_id: str, dashboard_key: str) -> None:
        await self._pool.execute(_REMOVE_FAVORITE_SQL, user_id, org_id, dashboard_key)

    async def get_order(self, user_id: str, org_id: str) -> list[str]:
        return list(await self._pool.fetchval(_GET_ORDER_SQL, user_id, org_id) or [])

    async def set_order(self, user_id: str, org_id: str, keys: list[str]) -> None:
        await self._pool.execute(_SET_ORDER_SQL, user_id, org_id, keys)


class CachedHubPrefsRepo:
    """HubPrefsRepo com cache-aside. Chaves por organização e pessoa:

    hub:favorites:<org_id>:<user_id>  e  hub:order:<org_id>:<user_id>  (+ CACHE_KEY_PREFIX).
    Escrita vai primeiro ao banco e depois apaga a chave; a próxima leitura recarrega.
    """

    def __init__(self, inner: HubPrefsRepo, cache: CacheService, ttl: int):
        self._inner = inner
        self._cache = cache
        self._ttl = ttl

    @staticmethod
    def favorites_key(user_id: str, org_id: str) -> str:
        return f"hub:favorites:{org_id}:{user_id}"

    @staticmethod
    def order_key(user_id: str, org_id: str) -> str:
        return f"hub:order:{org_id}:{user_id}"

    async def list_favorites(self, user_id: str, org_id: str) -> list[str]:
        key = self.favorites_key(user_id, org_id)
        return list(
            await get_or_load(
                self._cache, key, self._ttl, lambda: self._inner.list_favorites(user_id, org_id)
            )
        )

    async def add_favorite(self, user_id: str, org_id: str, dashboard_key: str) -> bool:
        saved = await self._inner.add_favorite(user_id, org_id, dashboard_key)
        if saved:
            await self._cache.delete(self.favorites_key(user_id, org_id))
        return saved

    async def remove_favorite(self, user_id: str, org_id: str, dashboard_key: str) -> None:
        await self._inner.remove_favorite(user_id, org_id, dashboard_key)
        await self._cache.delete(self.favorites_key(user_id, org_id))

    async def get_order(self, user_id: str, org_id: str) -> list[str]:
        key = self.order_key(user_id, org_id)
        return list(
            await get_or_load(
                self._cache, key, self._ttl, lambda: self._inner.get_order(user_id, org_id)
            )
        )

    async def set_order(self, user_id: str, org_id: str, keys: list[str]) -> None:
        await self._inner.set_order(user_id, org_id, keys)
        await self._cache.delete(self.order_key(user_id, org_id))


def get_hub_prefs_repo(
    pool: Annotated[asyncpg.Pool, Depends(get_db_pool)],
    cache: Annotated[CacheService, Depends(get_cache)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HubPrefsRepo:
    return CachedHubPrefsRepo(PgHubPrefsRepo(pool), cache, settings.CACHE_TTL_DEFAULT)
