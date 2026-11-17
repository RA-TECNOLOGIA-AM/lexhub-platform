"""Planilhas do Google publicadas como XLSX, como fonte de dados (como na v1: api_dashboards/src/app/sheets.py).

A URL fica só no `.env` (GOOGLE_SHEETS_URL_*). Cada planilha é uma fonte da V2 com a mesma chave de
app.data_sources / app.unit_source_refs (ex.: `sheets_financeiro_ng`): o "nome da query" é a aba
("REPASSES CLIENTES"). O download e a leitura são os da v1, sem mudança (_download_and_parse, _parse_xlsx...).
O cache é o mesmo dos bancos (CachedSourceFetcher: memória + Redis), no lugar do cache próprio da v1; fora do
aquecedor (baixar o XLSX inteiro a cada ciclo pesaria): a planilha só é baixada quando alguém abre o dashboard.

Para o cálculo copiado da v1 (app/analyses/sheets/*), `fetch_sheet(nome_v1)` lê a fonte que o módulo do
dashboard entrega em `usar_fonte(ctx.source)`, como os fetch_* das cópias genéricas.
"""

from __future__ import annotations

import asyncio
import io
import logging
import re
import time
import warnings
from collections.abc import Awaitable, Callable
from contextvars import ContextVar, Token
from datetime import date, datetime, timedelta
from datetime import time as dtime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import httpx
from openpyxl import load_workbook

from app.config import get_settings
from app.database import SourceUnavailable

if TYPE_CHECKING:
    from app.dashboards.base import SourceFetcher

logger = logging.getLogger(__name__)

Row = dict[str, Any]

# Fonte da V2 -> variável da URL no .env e o nome da planilha na v1 (o que o cálculo copiado pede).
SHEETS: dict[str, dict[str, str]] = {
    "sheets_financeiro_ng": {
        "url_setting": "GOOGLE_SHEETS_URL_FINANCEIRO_NG",
        "v1_name": "financeiro_NG",
        "default_sheet": "REPASSES CLIENTES",
    },
    "sheets_financeiro_la": {
        "url_setting": "GOOGLE_SHEETS_URL_FINANCEIRO_LA",
        "v1_name": "financeiro_LA",
        "default_sheet": "REPASSES CLIENTES",
    },
}

# Nome da v1 -> aba padrão (o `fetch_sheet(SHEET_NAME)` do cálculo copiado).
_ABA_PADRAO_V1 = {e["v1_name"]: e["default_sheet"] for e in SHEETS.values()}


def is_sheet(db_name: str) -> bool:
    return db_name in SHEETS


class SheetSourceFetcher:
    """SourceFetcher de uma planilha: `fetch(aba)` devolve as linhas da aba (dicts cabeçalho -> valor).

    url_loader: de onde vem o link (planilha conectada pela tela: o link decifrado do banco). Sem ele,
    o link vem do .env (as planilhas registradas em SHEETS)."""

    def __init__(self, db_name: str, url_loader: Callable[[], Awaitable[str]] | None = None):
        self._db = db_name
        self._url_loader = url_loader
        self._fetched: list[float] = []

    async def fetch(self, query_name: str) -> list[Row]:
        url = await self._url_loader() if self._url_loader else None
        all_sheets = await _download_and_parse(self._db, url)
        if query_name not in all_sheets:
            available = ", ".join(all_sheets) or "(nenhuma)"
            raise KeyError(
                f"Aba '{query_name}' não encontrada na planilha '{self._db}'. Disponíveis: {available}"
            )
        self._fetched.append(time.time())
        return all_sheets[query_name]

    def synced_at(self) -> float | None:
        return min(self._fetched) if self._fetched else None


# --- Ponte para o cálculo copiado da v1 -------------------------------------------------------------

_fonte_ctx: ContextVar[SourceFetcher | None] = ContextVar("fonte_sheets", default=None)


def usar_fonte(fonte: SourceFetcher) -> Token:
    """O módulo do dashboard entrega a fonte (já com cache) antes de chamar o cálculo da v1."""
    return _fonte_ctx.set(fonte)


def soltar_fonte(token: Token) -> None:
    _fonte_ctx.reset(token)


async def fetch_sheet(name: str, sheet: str | None = None) -> list[Row]:
    """Como na v1: as linhas de uma aba da planilha `name` (padrão: a aba principal)."""
    fonte = _fonte_ctx.get()
    if fonte is None:
        raise RuntimeError("fetch_sheet chamado fora de um dashboard (sem usar_fonte)")
    aba = sheet or _ABA_PADRAO_V1.get(name)
    if not aba:
        raise RuntimeError(f"Planilha '{name}' não tem aba padrão; informe o parâmetro `sheet`.")
    return await fonte.fetch(aba)


# --- Conectar planilha pela tela: o link colado vira o link de download em XLSX --------------------------

_PUBLISHED = re.compile(r"^/spreadsheets/d/e/([A-Za-z0-9_-]{20,})/pub(?:html)?$")
_SHARED = re.compile(r"^/spreadsheets/d/([A-Za-z0-9_-]{20,})(?:/.*)?$")


class InvalidSheetLink(ValueError):
    """Não é um link de planilha do Google que a API sabe baixar."""


def sheet_download_url(link: str) -> str:
    """Link colado -> link de download em XLSX. Aceita o "Publicar na Web" (/d/e/.../pub) e o link de
    compartilhamento (/d/<id>/edit, que precisa estar aberto a quem tiver o link). Só docs.google.com."""
    parsed = urlsplit(link.strip())
    if parsed.scheme != "https" or parsed.hostname != "docs.google.com":
        raise InvalidSheetLink(link)
    if m := _PUBLISHED.match(parsed.path):
        return f"https://docs.google.com/spreadsheets/d/e/{m.group(1)}/pub?output=xlsx"
    if m := _SHARED.match(parsed.path):
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=xlsx"
    raise InvalidSheetLink(link)


async def sheet_tabs(link: str) -> dict[str, int]:
    """Baixa a planilha do link e devolve {aba: linhas}. Link inválido = InvalidSheetLink;
    planilha que não baixa (não publicada, sem acesso, fora do ar) = SourceUnavailable."""
    sheets = await _download_and_parse("nova planilha", sheet_download_url(link))
    return {name: len(rows) for name, rows in sheets.items()}


def _indisponivel(msg: str) -> Exception:
    """Planilha sem URL ou que não baixou: SourceUnavailable (503 na casca, como banco fora do ar)."""
    return SourceUnavailable(msg)


# --- Download e leitura: os da v1, sem mudança (só a URL vem do Settings da V2) -----------------------

_RETRYABLE_SHEET_HTTP_ERRORS: tuple[type[Exception], ...] = (
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.ConnectError,
    httpx.PoolTimeout,
    httpx.NetworkError,
)


def _http_timeout() -> httpx.Timeout:
    settings = get_settings()
    return httpx.Timeout(
        connect=settings.SHEETS_HTTP_TIMEOUT,
        read=settings.SHEETS_HTTP_READ_TIMEOUT,
        write=30.0,
        pool=30.0,
    )


def _resolve_url(db_name: str) -> str:
    entry = SHEETS.get(db_name)
    if entry is None:
        raise KeyError(f"Planilha '{db_name}' não está registrada em SHEETS")
    url = getattr(get_settings(), entry["url_setting"], "")
    if not url:
        raise _indisponivel(
            f"A variável de ambiente '{entry['url_setting']}' não está definida: configure-a no `.env` "
            f"para usar a planilha '{db_name}'."
        )
    return url


async def _download_and_parse(db_name: str, url: str | None = None) -> dict[str, list[Row]]:
    """Baixa a planilha e devolve `{nome_aba: linhas}` (url None = a do .env)."""
    url = url or _resolve_url(db_name)
    logger.info("Baixando planilha '%s' do Google Sheets", db_name)
    timeout = _http_timeout()
    max_retries = get_settings().SHEETS_HTTP_MAX_RETRIES

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return _parse_xlsx(response.content)
        except _RETRYABLE_SHEET_HTTP_ERRORS as exc:
            logger.warning(
                "Falha transitória ao baixar planilha '%s' (tentativa %d/%d): %s",
                db_name,
                attempt,
                max_retries,
                exc,
            )
            if attempt >= max_retries:
                raise _indisponivel(
                    f"Não foi possível baixar a planilha '{db_name}': {exc}"
                ) from exc
            await asyncio.sleep(min(2.0, 0.5 * (2 ** (attempt - 1))))
        except httpx.HTTPError as exc:
            raise _indisponivel(f"Erro ao baixar a planilha '{db_name}': {exc}") from exc
    raise _indisponivel(f"Não foi possível baixar a planilha '{db_name}'")


def _parse_xlsx(content: bytes) -> dict[str, list[Row]]:
    """Parseia um XLSX em `{nome_aba: linhas}` (linhas são dicts header→valor)."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Cell .* is marked as a date but the serial value .* is outside the limits",
            category=UserWarning,
            module=r"openpyxl\..*",
        )
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        result: dict[str, list[Row]] = {}
        for sheet_name in workbook.sheetnames:
            worksheet = workbook[sheet_name]
            rows_iter = worksheet.iter_rows(values_only=True)
            try:
                header_row = next(rows_iter)
            except StopIteration:
                result[sheet_name] = []
                continue

            headers = _normalize_headers(header_row)
            if not headers:
                result[sheet_name] = []
                continue

            rows: list[Row] = []
            for raw_row in rows_iter:
                if raw_row is None:
                    continue
                if all(cell is None or cell == "" for cell in raw_row):
                    continue
                row: Row = {}
                for idx, header in enumerate(headers):
                    if header is None:
                        continue
                    value = raw_row[idx] if idx < len(raw_row) else None
                    row[header] = _normalize_value(value)
                rows.append(row)

            result[sheet_name] = rows
        return result
    finally:
        workbook.close()


def _normalize_headers(header_row: tuple[Any, ...]) -> list[str | None]:
    """Limpa e desduplica os cabeçalhos. Posições vazias viram None (ignoradas)."""
    seen: dict[str, int] = {}
    headers: list[str | None] = []
    for cell in header_row:
        if cell is None:
            headers.append(None)
            continue
        name = str(cell).strip()
        if not name:
            headers.append(None)
            continue
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        headers.append(name)
    return headers


def _normalize_value(value: Any) -> Any:
    """Converte tipos do openpyxl em valores serializáveis em JSON."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dtime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, str):
        return value.strip()
    return value
