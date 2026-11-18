"""Leva os links das planilhas antigas do `.env` (GOOGLE_SHEETS_URL_*) para o banco, cifrados (PR 3).

Roda uma vez, pelo script scripts/migrar_planilhas_env.py, ANTES do deploy que tira as variáveis do `.env`.
Seguro de repetir: só grava na planilha que ainda não tem link no banco (não sobrescreve). A chave das
fontes não muda (sheets_financeiro_ng/la): os dashboards Financeiro estratégico e Meta anual seguem iguais.

  * LegacySheetsRepo  as planilhas antigas sem link e a gravação (banco da plataforma);
  * migrate           confere cada link, baixa para guardar as abas/colunas (detalhe técnico) e cifra.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

import asyncpg

from app.database import SourceUnavailable
from app.secret_box import SecretBox
from app.sheets import InvalidSheetLink, TabInfo, sheet_download_url

# Fonte antiga -> a variável do .env que tinha o link.
LEGACY_SHEETS: dict[str, str] = {
    "sheets_financeiro_ng": "GOOGLE_SHEETS_URL_FINANCEIRO_NG",
    "sheets_financeiro_la": "GOOGLE_SHEETS_URL_FINANCEIRO_LA",
}

SheetReader = Callable[[str], Awaitable[dict[str, TabInfo]]]


class LegacySheetsRepo(Protocol):
    async def without_link(self, keys: list[str]) -> set[str]: ...

    async def save(self, key: str, ciphertext: str, schema: dict | None) -> bool: ...


_WITHOUT_LINK_SQL = """
select key from app.data_sources
 where key = any($1::text[]) and connector = 'sheets' and config = '{}'::jsonb and secret_ciphertext is null
"""

# "and secret_ciphertext is null": outra execução (ou a tela) já gravou = não sobrescreve.
_SAVE_SQL = """
update app.data_sources
   set secret_ciphertext = $2, schema_cache = coalesce($3::jsonb, schema_cache),
       config_version = config_version + 1, updated_at = now()
 where key = $1 and connector = 'sheets' and config = '{}'::jsonb and secret_ciphertext is null
"""


class PgLegacySheetsRepo:
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def without_link(self, keys: list[str]) -> set[str]:
        return {r["key"] for r in await self._conn.fetch(_WITHOUT_LINK_SQL, keys)}

    async def save(self, key: str, ciphertext: str, schema: dict | None) -> bool:
        status = await self._conn.execute(
            _SAVE_SQL, key, ciphertext, json.dumps(schema) if schema is not None else None
        )
        return status.endswith(" 1")


@dataclass(frozen=True)
class Outcome:
    key: str
    result: str  # 'gravada' | 'já estava no banco' | 'sem link no .env' | 'link inválido' | ...
    saved: bool = False


async def migrate(
    repo: LegacySheetsRepo,
    box: SecretBox,
    links: dict[str, str],
    read: SheetReader | None,
) -> list[Outcome]:
    """links: {fonte: link do .env}. read None = não baixa (grava sem as abas/colunas)."""
    pending = await repo.without_link(list(LEGACY_SHEETS))
    out: list[Outcome] = []
    for key in LEGACY_SHEETS:
        link = links.get(key, "").strip()
        if key not in pending:
            out.append(Outcome(key, "já estava no banco (não mexi)"))
            continue
        if not link:
            out.append(Outcome(key, "sem link no .env"))
            continue
        try:
            sheet_download_url(link)
        except InvalidSheetLink:
            out.append(Outcome(key, "link inválido (não é de planilha do Google)"))
            continue
        schema = None
        note = ""
        if read is not None:
            try:
                tabs = await read(link)
                schema = {n: [[c, ""] for c in t.columns] for n, t in tabs.items()} or None
                note = f" ({len(tabs)} abas)"
            except SourceUnavailable:
                note = " (não baixou agora: gravei mesmo assim, sem as abas)"
        saved = await repo.save(key, box.encrypt(link), schema)
        out.append(
            Outcome(key, f"gravada{note}" if saved else "já estava no banco (não mexi)", saved)
        )
    return out
