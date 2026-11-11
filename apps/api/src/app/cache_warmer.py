"""Aquecedor do cache: renova as queries dos dashboards antes de vencerem (padrão da v1).

Assim o usuário quase nunca paga a query pesada. Uma query por vez (não sobrecarrega a origem),
pulando bancos desligados ou fora do ar; falha de uma não interrompe as outras.
"""

import asyncio
import logging
from collections.abc import Callable, Iterable

from app.dashboards.base import DashboardModule, SourceFetcher
from app.source_cache import SourceCache

logger = logging.getLogger(__name__)

Target = tuple[str, str]  # (banco, query)


def warm_targets(modules: Iterable[DashboardModule]) -> list[Target]:
    """As queries que os dashboards declaram, sem repetir (Protocolo e Pendências usam a mesma)."""
    return list(dict.fromkeys((m.source_db, q) for m in modules for q in m.queries))


async def warm_once(
    cache: SourceCache,
    fetcher_for: Callable[[str], SourceFetcher],
    targets: list[Target],
    is_up: Callable[[str], bool],
) -> int:
    """Um ciclo. Devolve quantas queries foram renovadas."""
    ok = 0
    for db, query in targets:
        if not is_up(db):
            continue
        try:
            await cache.refresh(
                f"{db}:{query}", lambda db=db, query=query: fetcher_for(db).fetch(query)
            )
            ok += 1
        except Exception:
            logger.exception("[warm] falha em '%s:%s'", db, query)
    return ok


async def warm_loop(
    cache: SourceCache,
    fetcher_for: Callable[[str], SourceFetcher],
    targets: list[Target],
    is_up: Callable[[str], bool],
    interval: float,
    initial_delay: float = 30,
) -> None:
    """Tarefa de fundo: espera a API subir, aquece e repete a cada `interval` segundos."""
    if not targets:
        return
    logger.info("[warm] iniciado: %d queries, a cada %ds", len(targets), interval)
    await asyncio.sleep(initial_delay)
    while True:
        await warm_once(cache, fetcher_for, targets, is_up)
        await asyncio.sleep(interval)
