"""Aquecedor do cache: renova as queries dos dashboards em uso antes de vencerem (padrão da v1).

Assim o usuário quase nunca paga a query pesada. Uma query por vez (não sobrecarrega a origem),
pulando bancos desligados ou fora do ar; falha de uma não interrompe as outras.

Só renova a query que algum pedido leu há pouco (`in_use`, SOURCE_CACHE_WARM_IDLE). Renovar todas,
o dia inteiro, trazia as tabelas inteiras do LexFlow a cada 4 min, inclusive de madrugada: em
19/11/2026 o LexFlow teve 228 GB de egress pelo pooler do Supabase (cobrado), e as queries que mais
devolviam linhas eram as destes dashboards.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Iterable

from app.dashboards.base import DashboardModule, SourceFetcher
from app.database import SourceUnavailable
from app.logs import seconds
from app.source_cache import SourceCache, error_name

logger = logging.getLogger(__name__)

Target = tuple[str, str]  # (banco, query)


def warm_targets(modules: Iterable[DashboardModule], skip_dbs: Iterable[str] = ()) -> list[Target]:
    """As queries que os dashboards declaram, sem repetir (Protocolo e Pendências usam a mesma).

    Planilhas do Google (app/sheets.py) ficam de fora: o download do XLSX inteiro a cada ciclo pesaria sem
    ninguém ver; elas só entram no cache (5 min) quando alguém abre o dashboard.
    `skip_dbs` (SOURCE_CACHE_WARM_SKIP) também: o LexFlow responde em ~1 s, então o aquecedor não
    poupa espera a ninguém, e cada renovação dele era egress cobrado pelo Supabase. Lá o dado vencido
    vai para a tela na hora e é renovado em segundo plano só quando alguém lê.
    """
    from app.sheets import is_sheet  # aqui: app.sheets é carregado depois dos módulos de dashboard

    modules = list(modules)
    skip = frozenset(skip_dbs)
    proprias = ((m.source_db, q) for m in modules for q in m.queries)
    extras = ((db, q) for m in modules for db, qs in m.extra_queries.items() for q in qs)
    alternativas = ((db, q) for m in modules for db, a in m.alt_sources.items() for q in a.queries)
    alvos = dict.fromkeys([*proprias, *extras, *alternativas])
    return [(db, q) for db, q in alvos if not is_sheet(db) and db not in skip]


async def warm_once(
    cache: SourceCache,
    fetcher_for: Callable[[str], SourceFetcher],
    targets: list[Target],
    is_up: Callable[[str], bool],
    in_use: Callable[[str], bool],
) -> int:
    """Um ciclo. Devolve quantas queries foram renovadas.

    `in_use(chave)`: algum pedido leu a chave 'banco:query' há pouco; as outras ficam como estão.
    """
    ok = failed = skipped = unused = 0
    started = time.perf_counter()
    for db, query in targets:
        if not is_up(db):
            skipped += 1
            continue
        key = f"{db}:{query}"
        if not in_use(key):
            unused += 1
            continue
        try:
            fetcher = fetcher_for(db)
            if_changed = getattr(fetcher, "fetch_if_changed", None)
            await cache.refresh(
                key,
                lambda fetcher=fetcher, query=query: fetcher.fetch(query),
                (lambda known, f=if_changed, query=query: f(query, known))
                if callable(if_changed)
                else None,
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
        "ciclo terminado em %s: %d renovadas, %d com falha, %d puladas (banco fora/desligado), "
        "%d sem leitura recente",
        seconds(time.perf_counter() - started),
        ok,
        failed,
        skipped,
        unused,
    )
    return ok


# Pausa mínima entre dois ciclos, quando um ciclo demora mais que o intervalo: a origem respira.
MIN_PAUSE = 30.0


def pause_after(cycle: float, interval: float) -> float:
    """Quanto esperar depois de um ciclo que durou `cycle` s para o próximo começar `interval` s depois
    do início deste.

    Antes a pausa era o intervalo inteiro, depois do ciclo: com ciclo de 1 min 38 s e intervalo de 4 min,
    cada query era renovada a cada ~5 min 40 s e ficava ~40 s vencida (TTL de 5 min).
    """
    return max(MIN_PAUSE, interval - cycle)


async def warm_loop(
    cache: SourceCache,
    fetcher_for: Callable[[str], SourceFetcher],
    targets: list[Target],
    is_up: Callable[[str], bool],
    in_use: Callable[[str], bool],
    interval: float,
    initial_delay: float = 30,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Tarefa de fundo: espera a API subir, aquece e começa um ciclo a cada `interval` segundos."""
    if not targets:
        return
    logger.info(
        "ligado: %d queries, a cada %s; primeiro ciclo em %s",
        len(targets),
        seconds(interval),
        seconds(initial_delay),
    )
    await sleep(initial_delay)
    while True:
        started = clock()
        await warm_once(cache, fetcher_for, targets, is_up, in_use)
        await sleep(pause_after(clock() - started, interval))
