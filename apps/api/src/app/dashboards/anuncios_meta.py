"""Facebook Ads das contas da Meta conectadas na unidade, no lugar do metrics_ads.facebook_ads (banco ng).

A coleta (app/facebook_ads_sync.py) guarda cada conta no próprio LexHub; a fonte da conta responde a query
`facebook_ads` com as mesmas colunas do banco ng (app/registered_sources.py), então o cálculo da v1 não muda.
Cada conta é ligada a uma unidade na tela (app.unit_source_refs, key 'fb_...'): a NG lê as contas dela, a LA
as dela. Unidade sem conta conectada segue no banco ng, como antes.

A troca é por unidade e tudo-ou-nada (a casca, app/routes/dashboards.py, com SourceRefsRepo.ads_ready): só
quando todas as contas ligadas da unidade já têm o histórico completo. Uma conta ainda carregando deixaria o
gasto pela metade, então enquanto isso a unidade segue no banco ng. Conta desligada na tela fica de fora; a
que falhar na leitura também (com aviso no log), como o banco ng fora do ar já deixava os anúncios zerados:
o resto do dashboard continua.
"""

import logging
from typing import Any

from app.dashboards.base import DashboardContext, SourceFetcher
from app.database import SourceUnavailable
from app.registered_sources import ADS_QUERY

logger = logging.getLogger(__name__)

# connect_source (supabase/migrations/20261127110000_fonte_facebook_ads.sql): a key da conta de anúncios
# começa com 'fb_' (e só ela).
ADS_KEY_PREFIX = "fb_"


def ads_keys(source_refs: dict[str, str]) -> list[str]:
    """As contas de anúncios ligadas à unidade, em ordem estável (a ordem das linhas e da memória)."""
    return sorted(k for k in source_refs if k.startswith(ADS_KEY_PREFIX))


async def linhas_da_unidade(ctx: DashboardContext) -> list[dict[str, Any]] | None:
    """As linhas do Facebook Ads de todas as contas da unidade; None = a unidade não tem conta conectada."""
    if not ctx.ads_sources:
        return None
    rows: list[dict[str, Any]] = []
    for key, fonte in ctx.ads_sources.items():
        try:
            rows += await fonte.fetch(ADS_QUERY)
        except SourceUnavailable as exc:  # inclui SourceDisabled (desligada na tela)
            logger.warning("Facebook Ads '%s' fora do Marketing: %s", key, type(exc).__name__)
    return rows


class ComAnunciosDaMeta:
    """A fonte do dashboard com a query `facebook_ads` respondida pelas contas da Meta da unidade (o cálculo
    da v1 do Marketing NG pede tudo à mesma fonte)."""

    def __init__(self, inner: SourceFetcher, ctx: DashboardContext):
        self._inner, self._ctx = inner, ctx

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        if query_name == ADS_QUERY:
            rows = await linhas_da_unidade(self._ctx)
            if rows is not None:
                return rows
        return await self._inner.fetch(query_name)

    def synced_at(self) -> float | None:
        return self._inner.synced_at()


def com_anuncios_da_meta(ctx: DashboardContext) -> SourceFetcher:
    """A fonte do contexto, trocando o Facebook Ads do banco ng pelas contas da unidade (se houver)."""
    return ComAnunciosDaMeta(ctx.source, ctx) if ctx.ads_sources else ctx.source
