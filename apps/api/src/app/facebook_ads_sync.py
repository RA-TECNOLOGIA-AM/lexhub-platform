"""Coleta do Facebook Ads: baixa o que a fonte pede (AdsSettings, na config) e guarda no Supabase do LexHub.

Ligada por FACEBOOK_ADS_SYNC_ENABLED, desligada por padrão: uma API local apontando para o banco de
produção não coleta sozinha. Deve rodar em uma réplica só (o stack de produção tem uma); duas coletando
ao mesmo tempo só repetem chamadas à Meta, porque cada período é trocado inteiro numa transação.

Conjuntos de dados (app.facebook_ads_sync_state guarda até onde cada um chegou):
  ads          por anúncio e dia (app.facebook_ads_daily), sempre;
  age_gender, platform, region, device
               por campanha, dia e segmento (app.facebook_ads_breakdowns), os escolhidos na fonte.
Para cada um, a cada intervalo da tela (Integração Meta; 10 min sem nada salvo, o mesmo número que o banco
usa para marcar a fonte como atrasada: app_private.ads_sync_every_min) e logo depois de conectar ou
personalizar:
  * histórico: na primeira vez e quando a personalização muda o que é coletado (collect_version), os
    últimos `backfill_days` (a Meta guarda 37 meses), em blocos de 31 dias, do mais antigo para o mais
    novo. Cada bloco é gravado na hora: se a coleta cair no meio, a próxima continua de onde parou;
  * depois: ontem e hoje, no fuso da conta. Uma vez por dia (e na subida da API), os últimos 28 dias,
    porque a Meta ainda recalcula as conversões (atribuição de até 28 dias depois do clique);
  * se a coleta ficou parada (API fora, fonte desligada), o buraco entra junto.
Cada período é trocado inteiro (apaga e grava): o que saiu do relatório sai daqui também.
Campanhas, conjuntos e anúncios (com o criativo, se escolhido) são atualizados uma vez por dia e quando a
personalização muda (app.facebook_ads_entities).
Cada coleta de cada fonte vai para o log da fonte (app_private.record_source_sync): linhas ou o erro.
"""

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import asyncpg

from app.facebook_ads import (
    BREAKDOWNS,
    REACH_BREAKDOWN_DAYS,
    AdsSettings,
    ClientFactory,
    GraphClient,
    GraphError,
    GraphUnavailable,
    parse_breakdown_row,
    parse_entity,
    parse_row,
)
from app.logs import seconds
from app.secret_box import SecretBox, SecretUnreadable

logger = logging.getLogger(__name__)

RECENT_DAYS = 2  # ontem e hoje
DEEP_DAYS = 28  # a janela que a Meta ainda recalcula
DEEP_EVERY = 24 * 3600.0
CHUNK_DAYS = 31
ADS = "ads"

Window = tuple[date, date]


@dataclass(frozen=True)
class AdsSource:
    id: str
    key: str
    config: dict[str, Any]
    secret_ciphertext: str

    @property
    def account_id(self) -> str:
        return str(self.config.get("ad_account_id", ""))

    @property
    def timezone(self) -> str:
        return str(self.config.get("timezone", ""))

    @property
    def settings(self) -> AdsSettings:
        return AdsSettings.from_config(self.config)


@dataclass(frozen=True)
class SyncState:
    collect_version: int
    backfill_done: bool
    covered_until: date | None


class AdsRepo(Protocol):
    async def sources(self) -> list[AdsSource]: ...

    async def states(self, source_id: str) -> dict[str, SyncState]: ...

    async def replace(
        self, source_id: str, dataset: str, window: Window, rows: list[dict[str, Any]]
    ) -> int: ...

    async def set_state(self, source_id: str, dataset: str, state: SyncState) -> None: ...

    async def upsert_entities(self, source_id: str, rows: list[dict[str, Any]]) -> int: ...

    async def record(
        self, source_id: str, ok: bool, rows: int, ms: int, error: str | None
    ) -> None: ...


# --- Quais dias buscar --------------------------------------------------------------------------------


def plan(
    today: date,
    state: SyncState | None,
    *,
    collect_version: int,
    backfill_days: int,
    deep: bool,
) -> tuple[list[Window], bool]:
    """Os blocos de dias desta coleta (do mais antigo para o mais novo) e se é histórico."""
    oldest = today - timedelta(days=backfill_days - 1)
    if state is None or state.collect_version != collect_version:
        return chunks(oldest, today), True
    if not state.backfill_done:  # histórico interrompido: continua do último dia gravado
        start = max(oldest, state.covered_until or oldest)
        return chunks(start, today), True
    window = DEEP_DAYS if deep else RECENT_DAYS
    start = min(today - timedelta(days=window - 1), state.covered_until or today)
    return chunks(max(start, oldest), today), False


def chunks(since: date, until: date, size: int = CHUNK_DAYS) -> list[Window]:
    out: list[Window] = []
    start = since
    while start <= until:
        end = min(start + timedelta(days=size - 1), until)
        out.append((start, end))
        start = end + timedelta(days=1)
    return out


def zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name) if name else ZoneInfo("UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


async def fetch_dataset(
    graph: GraphClient,
    account_id: str,
    dataset: str,
    window: Window,
    settings: AdsSettings,
    today: date,
) -> list[dict[str, Any]]:
    """Um bloco de dias de um conjunto de dados, já no formato da tabela."""
    since, until = window
    if dataset == ADS:
        raw = await graph.report(
            account_id,
            level="ad",
            fields=settings.ad_fields(),
            since=since,
            until=until,
            daily=True,
            campaigns=settings.campaigns,
        )
        return [p for p in (parse_row(r, settings) for r in raw) if p is not None]
    # Alcance com detalhamento: só nos últimos 13 meses (antes disso a Meta recusa).
    with_reach = since >= today - timedelta(days=REACH_BREAKDOWN_DAYS)
    raw = await graph.report(
        account_id,
        level="campaign",
        fields=settings.breakdown_fields(with_reach),
        since=since,
        until=until,
        daily=True,
        breakdowns=BREAKDOWNS[dataset],
        campaigns=settings.campaigns,
    )
    return [p for p in (parse_breakdown_row(r, dataset, settings) for r in raw) if p is not None]


# --- A coleta ---------------------------------------------------------------------------------------


class AdsSync:
    def __init__(
        self,
        repo: AdsRepo,
        box: SecretBox,
        client_for: ClientFactory,
        *,
        interval: float | Callable[[], float],  # segundos; função = lido a cada rodada (a tela)
        now: Callable[[], datetime] = lambda: datetime.now(tz=ZoneInfo("UTC")),
        clock: Callable[[], float] = time.monotonic,
        before_run: Callable[[], Awaitable[object]] | None = None,
        paused: Callable[[], bool] | None = None,
    ):
        self._repo, self._box, self._client_for = repo, box, client_for
        self._interval = interval
        # A configuração da Meta (tela ou .env): lida antes de cada rodada; a tela pode pausar a coleta.
        self._before_run, self._paused = before_run, paused
        self._now, self._clock = now, clock
        self._last_deep: dict[str, float] = {}
        self._entities_for: dict[str, tuple] = {}  # fonte -> a personalização da última atualização
        self._wake = asyncio.Event()

    def interval(self) -> float:
        """Segundos até a próxima rodada (o da tela, lido de novo a cada vez)."""
        return self._interval() if callable(self._interval) else self._interval

    def wake(self) -> None:
        """Coletar já (uma conta foi conectada, personalizada, religada ou teve o token trocado)."""
        self._wake.set()

    async def run_once(self) -> int:
        """Uma rodada em todas as fontes ligadas. Devolve as linhas gravadas."""
        if self._before_run is not None:
            await self._before_run()
        if self._paused is not None and self._paused():
            logger.info(
                "Facebook Ads: coleta pausada na tela (Unidades e fontes > Integração Meta)"
            )
            return 0
        total = 0
        for source in await self._repo.sources():
            total += await self.sync_source(source)
        return total

    async def sync_source(self, source: AdsSource) -> int:
        started = self._clock()
        settings = source.settings
        today = self._now().astimezone(zone(source.timezone)).date()
        deep = self._clock() - self._last_deep.get(source.id, -DEEP_EVERY) >= DEEP_EVERY
        rows = 0
        error: str | None = None
        try:
            token = self._box.decrypt(source.secret_ciphertext)
            states = await self._repo.states(source.id)
            async with self._client_for(token) as graph:
                for dataset in (ADS, *settings.breakdowns):
                    rows += await self._dataset(
                        graph, source, settings, dataset, states, today, deep
                    )
                key = (settings.collect_version, settings.creatives, settings.campaigns)
                if deep or self._entities_for.get(source.id) != key:
                    await self._entities(graph, source, settings)
                    self._entities_for[source.id] = key
        except SecretUnreadable:
            error = "O token salvo não abre com a chave atual da API. Troque o token."
        except (GraphUnavailable, GraphError) as exc:
            error = exc.screen_message
        except Exception:
            logger.exception("Facebook Ads '%s': falha inesperada na coleta", source.key)
            error = "Falha inesperada na coleta (veja o log da API)."
        ms = int((self._clock() - started) * 1000)
        await self._repo.record(source.id, error is None, rows, ms, error)
        if error is None:
            if deep:
                self._last_deep[source.id] = self._clock()
            logger.info(
                "Facebook Ads '%s': %d linhas até %s em %s",
                source.key,
                rows,
                today,
                seconds(ms / 1000),
            )
        else:
            logger.warning("Facebook Ads '%s': coleta falhou: %s", source.key, error)
        return rows

    async def _dataset(
        self,
        graph: GraphClient,
        source: AdsSource,
        settings: AdsSettings,
        dataset: str,
        states: dict[str, SyncState],
        today: date,
        deep: bool,
    ) -> int:
        windows, backfill = plan(
            today,
            states.get(dataset),
            collect_version=settings.collect_version,
            backfill_days=settings.backfill_days,
            deep=deep,
        )
        rows = 0
        for i, window in enumerate(windows):
            parsed = await fetch_dataset(graph, source.account_id, dataset, window, settings, today)
            rows += await self._repo.replace(source.id, dataset, window, parsed)
            done = not backfill or i == len(windows) - 1
            state = SyncState(settings.collect_version, done, window[1])
            await self._repo.set_state(source.id, dataset, state)
        return rows

    async def _entities(self, graph: GraphClient, source: AdsSource, settings: AdsSettings) -> None:
        found: list[dict[str, Any]] = []
        for level in ("campaign", "adset", "ad"):
            raw = await graph.entities(
                source.account_id,
                level,
                creatives=settings.creatives,
                campaigns=settings.campaigns,
            )
            found += [p for p in (parse_entity(level, r) for r in raw) if p is not None]
        await self._repo.upsert_entities(source.id, found)

    async def loop(
        self,
        initial_delay: float = 20,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        """Tarefa de fundo: uma rodada a cada `interval` segundos, ou antes se alguém chamar wake()."""
        logger.info("Coleta do Facebook Ads ligada (o intervalo vem da Integração Meta)")
        await sleep(initial_delay)
        while True:
            self._wake.clear()
            try:
                await self.run_once()
            except Exception:
                logger.exception("Facebook Ads: rodada da coleta falhou")
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=self.interval())
            except TimeoutError:
                pass


# --- Banco da plataforma ------------------------------------------------------------------------------

_SOURCES_SQL = """
select ds.id::text, ds.key, ds.config::text, ds.secret_ciphertext
  from app.data_sources ds
  join app.organizations o on o.id = ds.org_id and o.active
 where ds.connector = 'facebook_ads' and ds.active and ds.enabled and ds.secret_ciphertext is not null
 order by ds.created_at
"""

_STATES_SQL = """
select dataset, collect_version, backfill_done, covered_until
  from app.facebook_ads_sync_state where source_id = $1::uuid
"""

_SET_STATE_SQL = """
insert into app.facebook_ads_sync_state (source_id, dataset, collect_version, backfill_done, covered_until)
values ($1::uuid, $2, $3, $4, $5)
on conflict (source_id, dataset) do update set
    collect_version = excluded.collect_version, backfill_done = excluded.backfill_done,
    covered_until = excluded.covered_until, updated_at = now()
"""

_COMMON = (
    "day",
    "campaign_id",
    "campaign_name",
    "spend",
    "impressions",
    "clicks",
    "link_clicks",
    "landing_page_views",
    "leads",
    "conversations",
    "results",
    "reach",
)
_DAILY = (
    *_COMMON,
    "ad_id",
    "ad_name",
    "adset_id",
    "adset_name",
    "account_id",
    "currency",
    "outbound_clicks",
    "frequency",
    "video_plays",
    "video_thruplays",
    "video_p25",
    "video_p50",
    "video_p75",
    "video_p100",
    "quality_ranking",
    "engagement_ranking",
    "conversion_ranking",
)
_DAILY_JSON = ("actions", "action_values")
_BREAKDOWN = (*_COMMON, "breakdown", "dim1", "dim2")
_BREAKDOWN_JSON = ("actions",)
_ENTITY = (
    "level",
    "id",
    "name",
    "campaign_id",
    "adset_id",
    "status",
    "effective_status",
    "objective",
    "optimization_goal",
    "daily_budget",
    "lifetime_budget",
    "start_time",
    "stop_time",
    "created_time",
)
_ENTITY_JSON = ("creative",)


def _upsert_sql(
    table: str, columns: tuple[str, ...], json_columns: tuple[str, ...], key: str
) -> str:
    """insert ... on conflict (key) do update de todas as colunas (as jsonb chegam como texto)."""
    names = ("source_id", *columns, *json_columns)
    values = ["$1::uuid"]
    values += [f"${i + 2}" for i in range(len(columns))]
    values += [f"${len(columns) + i + 2}::jsonb" for i in range(len(json_columns))]
    keys = {k.strip() for k in key.split(",")}
    updates = [f"{c} = excluded.{c}" for c in (*columns, *json_columns) if c not in keys]
    return (
        f"insert into {table} ({', '.join(names)}) values ({', '.join(values)}) "
        f"on conflict ({key}) do update set {', '.join(updates)}, fetched_at = now()"
    )


_DAILY_SQL = _upsert_sql("app.facebook_ads_daily", _DAILY, _DAILY_JSON, "source_id, day, ad_id")
_BREAKDOWN_SQL = _upsert_sql(
    "app.facebook_ads_breakdowns",
    _BREAKDOWN,
    _BREAKDOWN_JSON,
    "source_id, day, breakdown, campaign_id, dim1, dim2",
)
_ENTITY_SQL = _upsert_sql(
    "app.facebook_ads_entities", _ENTITY, _ENTITY_JSON, "source_id, level, id"
)


def _args(source_id: str, row: dict[str, Any], columns: tuple, json_columns: tuple) -> tuple:
    return (
        source_id,
        *(row.get(c) for c in columns),
        *(None if row.get(c) is None else json.dumps(row[c]) for c in json_columns),
    )


class PgAdsRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def sources(self) -> list[AdsSource]:
        return [
            AdsSource(
                id=r["id"],
                key=r["key"],
                config=json.loads(r["config"]),
                secret_ciphertext=r["secret_ciphertext"],
            )
            for r in await self._pool.fetch(_SOURCES_SQL)
        ]

    async def states(self, source_id: str) -> dict[str, SyncState]:
        return {
            r["dataset"]: SyncState(r["collect_version"], r["backfill_done"], r["covered_until"])
            for r in await self._pool.fetch(_STATES_SQL, source_id)
        }

    async def replace(
        self, source_id: str, dataset: str, window: Window, rows: list[dict[str, Any]]
    ) -> int:
        async with self._pool.acquire() as conn, conn.transaction():
            if dataset == ADS:
                await conn.execute(
                    "delete from app.facebook_ads_daily"
                    " where source_id = $1::uuid and day between $2 and $3",
                    source_id,
                    *window,
                )
                sql, cols, js = _DAILY_SQL, _DAILY, _DAILY_JSON
            else:
                await conn.execute(
                    "delete from app.facebook_ads_breakdowns"
                    " where source_id = $1::uuid and breakdown = $2 and day between $3 and $4",
                    source_id,
                    dataset,
                    *window,
                )
                sql, cols, js = _BREAKDOWN_SQL, _BREAKDOWN, _BREAKDOWN_JSON
            if rows:
                await conn.executemany(sql, [_args(source_id, r, cols, js) for r in rows])
        return len(rows)

    async def set_state(self, source_id: str, dataset: str, state: SyncState) -> None:
        await self._pool.execute(
            _SET_STATE_SQL,
            source_id,
            dataset,
            state.collect_version,
            state.backfill_done,
            state.covered_until,
        )

    async def upsert_entities(self, source_id: str, rows: list[dict[str, Any]]) -> int:
        if rows:
            async with self._pool.acquire() as conn, conn.transaction():
                await conn.executemany(
                    _ENTITY_SQL, [_args(source_id, r, _ENTITY, _ENTITY_JSON) for r in rows]
                )
        return len(rows)

    async def record(self, source_id: str, ok: bool, rows: int, ms: int, error: str | None) -> None:
        await self._pool.execute(
            "select app_private.record_source_sync($1::uuid, $2, $3, $4, $5)",
            source_id,
            ok,
            rows,
            ms,
            error,
        )
