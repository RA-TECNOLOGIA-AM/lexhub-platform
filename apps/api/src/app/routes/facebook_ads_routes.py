"""Facebook Ads na tela Conectar fonte: as opções da conta, a prévia e a personalização da coleta.

Só a TI da LexGroup (as mesmas regras de app/routes/source_connections.py). O token chega aqui para testar
e ler as opções antes de conectar (como o link da planilha em /sources/sheets/inspect): nada é gravado e
nenhuma resposta o devolve. Depois de conectar, as rotas da fonte usam o token salvo (cifrado).

  POST /sources/facebook-ads/token            token -> quem é, permissões, o que permite e as contas (nomes)
  POST /sources/facebook-ads/inspect          conta + token -> checagens e opções (campanhas, conversões)
  POST /sources/facebook-ads/preview          conta + token + personalização -> últimos 7 dias
  GET  /orgs/{org}/sources/{key}/facebook-ads/token      o que o token salvo permite
  GET  /orgs/{org}/sources/{key}/facebook-ads/options    opções e a personalização atual
  POST /orgs/{org}/sources/{key}/facebook-ads/preview    prévia com o token salvo
  PUT  /orgs/{org}/sources/{key}/facebook-ads/settings   salva a personalização (e avisa a coleta)

Erro da Meta nas opções e na prévia vira 502 com a mensagem para a tela (token recusado, limite...).
"""

from collections.abc import Awaitable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.connection_check import Check
from app.facebook_ads import (
    AdsChecker,
    AdsSettings,
    AdsSettingsIn,
    ClientFactory,
    GraphError,
    GraphUnavailable,
    account_options,
    app_token,
    client_factory,
    normalize_account,
    preview,
    token_info,
)
from app.routes.source_connections import (
    BAD_ACCOUNT,
    Admin,
    KeyPath,
    RateLimit,
    Repo,
    _db_message,
    _managed,
    _wake_ads,
    get_ads_checker,
    get_ads_sync,
    get_rate_limit,
    get_secret_box,
)
from app.secret_box import SecretBox, SecretUnreadable
from app.source_admin import ManagedSource, NotAllowed, RuleBroken, SourceAdminRepo

platform = APIRouter(prefix="/sources/facebook-ads", tags=["sources"])
org = APIRouter(prefix="/orgs/{org_slug}/sources/{key}/facebook-ads", tags=["sources"])


class TokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=1000)


class AccessIn(BaseModel):
    adAccountId: str = Field(min_length=1, max_length=40)
    token: str = Field(min_length=20, max_length=1000)


class PreviewIn(AccessIn):
    settings: AdsSettingsIn = Field(default_factory=AdsSettingsIn)


class SettingsIn(BaseModel):
    settings: AdsSettingsIn


def get_graph_factory(settings: Annotated[Settings, Depends(get_settings)]) -> ClientFactory:
    return client_factory(settings)


def get_app_token(settings: Annotated[Settings, Depends(get_settings)]) -> str | None:
    return app_token(settings)


Graph = Annotated[ClientFactory, Depends(get_graph_factory)]
AppToken = Annotated[str | None, Depends(get_app_token)]
Rate = Annotated[RateLimit, Depends(get_rate_limit)]
Box = Annotated[SecretBox, Depends(get_secret_box)]


async def _meta[T](call: Awaitable[T]) -> T:
    try:
        return await call
    except (GraphError, GraphUnavailable) as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=exc.screen_message) from exc


def _account(raw: str) -> str:
    account = normalize_account(raw)
    if account is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=BAD_ACCOUNT)
    return account


async def _saved(
    repo: SourceAdminRepo, box: SecretBox, org_slug: str, key: str
) -> tuple[ManagedSource, str]:
    """A fonte Facebook Ads e o token salvo, decifrado."""
    source = await _managed(repo, org_slug, key)
    if source.connector != "facebook_ads":
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Só a fonte Facebook Ads tem personalização."
        )
    try:
        return source, box.decrypt(source.secret_ciphertext or "")
    except SecretUnreadable as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="O token salvo não abre com a chave atual da API. Troque o token.",
        ) from exc


# --- Antes de conectar (o token vem na requisição) --------------------------------------------------


@platform.post("/token")
async def read_token(
    body: TokenIn, user: Admin, graph_for: Graph, app: AppToken, rate: Rate
) -> dict[str, Any]:
    """Passo Acesso: quem é o token, as permissões, o que dá para fazer e as contas de anúncios que ele
    acessa (com o nome, para escolher numa lista). Não grava nada."""
    rate.check(user.user_id)
    async with graph_for(body.token.strip()) as graph:
        return await _meta(token_info(graph, app_token=app))


@platform.post("/inspect")
async def inspect_account(
    body: AccessIn,
    user: Admin,
    check_ads: Annotated[AdsChecker, Depends(get_ads_checker)],
    graph_for: Graph,
    rate: Rate,
) -> dict[str, Any]:
    """Passo Acesso: testa a conta e, se passou, devolve as campanhas e as conversões da conta."""
    rate.check(user.user_id)
    empty: dict[str, Any] = {"account": None, "campaigns": [], "conversions": []}
    account = normalize_account(body.adAccountId)
    if account is None:
        return {"ok": False, "checks": [vars(Check("read", False, BAD_ACCOUNT))], **empty}
    token = body.token.strip()
    result, info = await check_ads(account, token)
    out = {"ok": result.ok, "checks": [vars(c) for c in result.checks], **empty}
    if result.ok and info is not None:
        out["account"] = info.to_api()
        async with graph_for(token) as graph:
            out |= await _meta(account_options(graph, account))
    return out


@platform.post("/preview")
async def preview_account(
    body: PreviewIn, user: Admin, graph_for: Graph, rate: Rate
) -> dict[str, Any]:
    """Passo Prévia: os últimos 7 dias com a personalização escolhida. Não grava nada."""
    rate.check(user.user_id)
    account = _account(body.adAccountId)
    async with graph_for(body.token.strip()) as graph:
        return await _meta(preview(graph, account, body.settings.to_settings()))


# --- Depois de conectar (o token salvo) ----------------------------------------------------------------


@org.get("/token")
async def saved_token(
    org_slug: str,
    key: KeyPath,
    user: Admin,
    repo: Repo,
    box: Box,
    graph_for: Graph,
    app: AppToken,
    rate: Rate,
) -> dict[str, Any]:
    """O que o token salvo permite (e se ainda vale)."""
    _, token = await _saved(repo, box, org_slug, key)
    rate.check(user.user_id)
    async with graph_for(token) as graph:
        return await _meta(token_info(graph, app_token=app))


@org.get("/options")
async def saved_options(
    org_slug: str, key: KeyPath, user: Admin, repo: Repo, box: Box, graph_for: Graph, rate: Rate
) -> dict[str, Any]:
    """Personalizar coleta: as opções da conta e a personalização atual."""
    source, token = await _saved(repo, box, org_slug, key)
    rate.check(user.user_id)
    c = source.config
    async with graph_for(token) as graph:
        options = await _meta(account_options(graph, str(c.get("ad_account_id"))))
    account = {
        "id": c.get("ad_account_id"),
        "name": c.get("account_name"),
        "currency": c.get("currency"),
        "timezone": c.get("timezone"),
        "status": None,
    }
    settings = AdsSettings.from_config(c).to_api()
    return {"ok": True, "checks": [], "account": account, **options, "settings": settings}


@org.post("/preview")
async def saved_preview(
    org_slug: str,
    key: KeyPath,
    body: SettingsIn,
    user: Admin,
    repo: Repo,
    box: Box,
    graph_for: Graph,
    rate: Rate,
) -> dict[str, Any]:
    source, token = await _saved(repo, box, org_slug, key)
    rate.check(user.user_id)
    account = str(source.config.get("ad_account_id"))
    async with graph_for(token) as graph:
        return await _meta(preview(graph, account, body.settings.to_settings()))


@org.put("/settings")
async def save_settings(
    org_slug: str,
    key: KeyPath,
    body: SettingsIn,
    user: Admin,
    repo: Repo,
    ads_sync: Annotated[Any, Depends(get_ads_sync)],
) -> dict[str, Any]:
    """Salva a personalização. Métricas, campanhas, detalhamentos ou histórico mudaram: a coleta refaz o
    histórico (recollect=true). Só as conversões mudaram: "resultados" é refeito na hora, sem coletar."""
    source = await _managed(repo, org_slug, key)
    if source.connector != "facebook_ads":
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Só a fonte Facebook Ads tem personalização."
        )
    old = AdsSettings.from_config(source.config)
    wanted = body.settings.to_settings(old.collect_version)
    recollect = old.needs_recollect(wanted)
    new = body.settings.to_settings(old.collect_version + (1 if recollect else 0))
    config = {**source.config, **new.to_config()}
    try:
        item = await repo.set_config(user.user_id, source.id, config, "")
    except NotAllowed as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup gerencia fontes"
        ) from exc
    except RuleBroken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=_db_message(exc)) from exc
    if set(old.conversions) != set(new.conversions):
        await repo.recompute_results(source.id, list(new.conversions))
    _wake_ads(ads_sync)
    return {"source": item, "recollect": recollect, "settings": new.to_api()}
