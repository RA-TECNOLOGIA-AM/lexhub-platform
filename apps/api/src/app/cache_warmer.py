"""Aquecedor do cache: renova as queries dos dashboards antes de vencerem (padrão da v1).

Assim o usuário quase nunca paga a query pesada. Uma query por vez (não sobrecarrega a origem),
pulando bancos desligados ou fora do ar; falha de uma não interrompe as outras.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Iterable

from app.dashboards.base import DashboardModule, SourceFetcher
from app.database import SourceUnavailable
from app.logs import seconds
from app.source_cache import SourceCache, error_name

logger = logging.getLogger(__name__)

Target = tuple[str, str]  # (banco, query)


def warm_targets(modules: Iterable[DashboardModule]) -> list[Target]:
    """As queries que os dashboards declaram, sem repetir (Protocolo e Pendências usam a mesma).

    Planilhas do Google (app/sheets.py) ficam de fora: o download do XLSX inteiro a cada ciclo pesaria sem
    ninguém ver; elas só entram no cache (5 min) quando alguém abre o dashboard.
    """
    from app.sheets import is_sheet  # aqui: app.sheets é carregado depois dos módulos de dashboard

    modules = list(modules)
    proprias = ((m.source_db, q) for m in modules for q in m.queries)
    extras = ((db, q) for m in modules for db, qs in m.extra_queries.items() for q in qs)
    alternativas = ((db, q) for m in modules for db, a in m.alt_sources.items() for q in a.queries)
    alvos = dict.fromkeys([*proprias, *extras, *alternativas])
    return [(db, q) for db, q in alvos if not is_sheet(db)]


async def warm_once(
    cache: SourceCache,
    fetcher_for: Callable[[str], SourceFetcher],
    targets: list[Target],
    is_up: Callable[[str], bool],
) -> int:
    """Um ciclo. Devolve quantas queries foram renovadas."""
    ok = failed = skipped = 0
    started = time.perf_counter()
    for db, query in targets:
        if not is_up(db):
            skipped += 1
            continue
        try:
            await cache.refresh(
                f"{db}:{query}", lambda db=db, query=query: fetcher_for(db).fetch(query)
            )
            ok += 1
        except SourceUnavailable as exc:
            # Esperado (banco fora, lento ou que cancelou a consulta): uma linha basta, o motivo
            # já foi registrado por app/database.py. Quem abrir o dashboard vê o último dado bom.
            failed += 1
            logger.warning("'%s:%s' não renovou: %s", db, query, error_name(exc))
        except Exception:
            failed += 1
            logger.exception("falha ao renovar '%s:%s'", db, query)
    logger.log(
        logging.WARNING if failed else logging.INFO,
        "ciclo terminado em %s: %d renovadas, %d com falha, %d puladas (banco fora/desligado)",
        seconds(time.perf_counter() - started),
        ok,
        failed,
        skipped,
    )
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
    logger.info(
        "ligado: %d queries, a cada %s; primeiro ciclo em %s",
        len(targets),
        seconds(interval),
        seconds(initial_delay),
    )
    await asyncio.sleep(initial_delay)
    while True:
        await warm_once(cache, fetcher_for, targets, is_up)
        await asyncio.sleep(interval)
