"""Tela Clientes (plataforma): as fontes com falha de cada organização.

A mesma regra da tela Unidades e fontes (app/read_log.py, `summarize`): falha = a tentativa de leitura
mais recente da fonte falhou. Tempo parado não conta (a API só lê a fonte quando alguém abre um
dashboard). Antes, app_private.failing_sources_of contava como "atrasada" toda fonte cujo último teste
manual passara de 20 min, e as planilhas saudáveis apareciam como atrasadas.

Peças:
  * MonitoredRepo   banco da plataforma: quem é TI da LexGroup e as fontes que contam (ativas, ligadas e
                    com algum dashboard ligado que as usa; "Aguardando dashboards" e "Desligada" ficam
                    de fora);
  * failing_by_org  junta essa lista com o registro de leituras (memória + Redis; nada vai aos bancos
                    de origem).
"""

from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends

from app.access import get_db_pool
from app.read_log import ReadLog, summarize


class MonitoredRepo(Protocol):
    async def is_source_admin(self, user_id: str) -> bool: ...

    async def monitored(self) -> list[tuple[str, str]]:
        """(slug da organização, chave da fonte) das fontes que entram na conta."""
        ...


_IS_ADMIN_SQL = "select app_private.is_source_admin($1::uuid)"

# Ativa, ligada e usada por algum dashboard ligado na organização (o mesmo vínculo da tela de fontes:
# app.dashboard_sources). Organização inativa não aparece na tela Clientes.
_MONITORED_SQL = """
select o.slug, ds.key
  from app.data_sources ds
  join app.organizations o on o.id = ds.org_id and o.active
 where ds.active
   and ds.enabled
   and exists (
       select 1
         from app.dashboard_sources dsrc
         join app.dashboard_catalog c on c.key = dsrc.dashboard_key and c.active
         join app.org_dashboards od  on od.dashboard_key = c.key and od.org_id = ds.org_id and od.enabled
        where dsrc.source_key = ds.key)
 order by o.slug, ds.key
"""


class PgMonitoredRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def is_source_admin(self, user_id: str) -> bool:
        return bool(await self._pool.fetchval(_IS_ADMIN_SQL, user_id))

    async def monitored(self) -> list[tuple[str, str]]:
        return [(r["slug"], r["key"]) for r in await self._pool.fetch(_MONITORED_SQL)]


def get_monitored_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> MonitoredRepo:
    return PgMonitoredRepo(pool)


async def failing_by_org(reads: ReadLog, monitored: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Organização -> chaves das fontes cuja tentativa mais recente falhou (lista vazia = nenhuma)."""
    out: dict[str, list[str]] = {}
    for slug, key in monitored:
        failing = out.setdefault(slug, [])
        _, fail_at, _ = summarize((await reads.of_db(key)).values())
        if fail_at is not None:
            failing.append(key)
    return out
