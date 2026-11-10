"""Preferências do hub da pessoa numa organização: favoritos e ordem dos cards.

Dividido em duas partes trocáveis:
  * HubPrefsRepo  só lê e grava no banco (PgHubPrefsRepo em produção, um falso nos testes);
  * clean_order   limpa a ordem recebida do front (função pura).
Tudo é por associação (memberships.id): a mesma pessoa tem preferências separadas em cada organização.
"""

from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends

from app.access import get_db_pool

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


def get_hub_prefs_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> HubPrefsRepo:
    return PgHubPrefsRepo(pool)
