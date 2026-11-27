"""Facebook Ads (Marketing API da Meta): testar a conta, ler as opções dela, montar a prévia e baixar as
métricas, os detalhamentos, as campanhas e os criativos.

O token é o do usuário do sistema do Gerenciador de Negócios, com a permissão ads_read (só leitura de
relatórios). Ele vai no cabeçalho Authorization, nunca na URL: URL aparece em log e em mensagem de erro.
Com a chave secreta do app (Unidades e fontes > Integração Meta; app/meta_config.py), cada chamada leva o
appsecret_proof (obrigatório se o app exigir "Require App Secret" nas configurações avançadas).

O teste de conexão (o "Testar e salvar" da tela) tem quatro checagens, nesta ordem; a primeira que falha
para o resto (as seguintes voltam `skipped`), como em app/connection_check.py:
  network   a API alcança graph.facebook.com;
  login     a Meta aceita o token;
  read      a conta existe, o token lê a conta e os relatórios (/insights dos últimos 7 dias);
  account   a conta está ativa. Se não estiver, é aviso (warn): dá para salvar e guardar o histórico.
As mensagens vão para a tela; do erro da Meta só aproveitamos o código, nunca o texto (pode trazer ids).

A personalização (AdsSettings) fica na config da fonte: grupos de métricas, conversões que somam em
"resultados", campanhas coletadas, detalhamentos, histórico e criativos.
"""

import hashlib
import hmac
import json
import re
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal, Protocol, Self

import httpx
from pydantic import BaseModel, Field

from app.connection_check import Check, CheckResult

GRAPH_URL = "https://graph.facebook.com"

# account_status da Meta (https://developers.facebook.com/docs/marketing-api/reference/ad-account/).
ACCOUNT_STATUS = {
    1: "ativa",
    2: "desativada",
    3: "com pagamento pendente",
    7: "em análise de risco",
    8: "aguardando acerto de pagamento",
    9: "em período de carência",
    100: "aguardando encerramento",
    101: "encerrada",
}

_ACCOUNT_RE = re.compile(r"^(?:act_)?(\d{1,20})$")

# Códigos de erro da Graph API (https://developers.facebook.com/docs/graph-api/guides/error-handling/).
_TOKEN_CODES = {102, 190}
_PERMISSION_CODES = {3, 10} | set(range(200, 300))
_THROTTLE_CODES = {4, 17, 32, 613} | set(range(80000, 80015))

# --- O que dá para personalizar ---------------------------------------------------------------------

MetricGroup = Literal["reach", "video", "quality"]
Breakdown = Literal["age_gender", "platform", "region", "device"]

# Campos da Meta de cada grupo opcional (o básico vem sempre: gasto, impressões, cliques e ações).
GROUP_FIELDS: dict[str, tuple[str, ...]] = {
    "reach": ("reach", "frequency"),
    "video": (
        "video_play_actions",
        "video_thruplay_watched_actions",
        "video_p25_watched_actions",
        "video_p50_watched_actions",
        "video_p75_watched_actions",
        "video_p100_watched_actions",
    ),
    "quality": ("quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"),
}

# Detalhamento -> os breakdowns da Meta (dim1, dim2 na tabela).
BREAKDOWNS: dict[str, tuple[str, ...]] = {
    "age_gender": ("age", "gender"),
    "platform": ("publisher_platform", "platform_position"),
    "region": ("region",),
    "device": ("impression_device",),
}

# Alcance com detalhamento só existe para os últimos 13 meses (Meta, desde 10/06/2025).
REACH_BREAKDOWN_DAYS = 394

BASE_AD_FIELDS = (
    "date_start",
    "account_id",
    "account_currency",
    "campaign_id",
    "campaign_name",
    "adset_id",
    "adset_name",
    "ad_id",
    "ad_name",
    "spend",
    "impressions",
    "clicks",
    "inline_link_clicks",
    "outbound_clicks",
    "actions",
    "action_values",
)
BASE_BREAKDOWN_FIELDS = (
    "date_start",
    "campaign_id",
    "campaign_name",
    "spend",
    "impressions",
    "clicks",
    "inline_link_clicks",
    "actions",
)

LEAD_TYPES = ("onsite_conversion.lead_grouped", "offsite_conversion.fb_pixel_lead")
CONVERSATION_TYPE = "onsite_conversion.messaging_conversation_started_7d"

# Nomes das ações da Meta na tela (as que não estão aqui aparecem com o código).
ACTION_LABELS = {
    "lead": "Leads (formulário + site)",
    "onsite_conversion.lead_grouped": "Leads de formulário da Meta",
    "offsite_conversion.fb_pixel_lead": "Leads no site (pixel)",
    CONVERSATION_TYPE: "Conversas iniciadas (WhatsApp, Messenger, Direct)",
    "onsite_conversion.messaging_first_reply": "Primeira resposta em conversa",
    "onsite_conversion.messaging_block": "Conversas bloqueadas",
    "link_click": "Cliques no link",
    "landing_page_view": "Visualizações da página de destino",
    "omni_landing_page_view": "Visualizações da página de destino (todas)",
    "outbound_click": "Cliques de saída",
    "post_engagement": "Engajamento com a publicação",
    "page_engagement": "Engajamento com a página",
    "post_reaction": "Reações",
    "comment": "Comentários",
    "onsite_conversion.post_save": "Publicações salvas",
    "post": "Compartilhamentos",
    "like": "Curtidas na página",
    "video_view": "Visualizações de vídeo (3 s)",
    "complete_registration": "Cadastros concluídos",
    "offsite_conversion.fb_pixel_complete_registration": "Cadastros concluídos no site (pixel)",
    "contact": "Contatos",
    "offsite_conversion.fb_pixel_contact": "Contatos no site (pixel)",
    "schedule": "Agendamentos",
    "submit_application": "Inscrições enviadas",
    "purchase": "Compras",
    "offsite_conversion.fb_pixel_purchase": "Compras no site (pixel)",
}
# Sempre na lista de conversões, mesmo sem ocorrência nos últimos 30 dias.
ALWAYS_OFFERED = ("lead", CONVERSATION_TYPE, "landing_page_view", "link_click")


def action_label(action_type: str) -> str:
    return ACTION_LABELS.get(action_type, action_type)


@dataclass(frozen=True)
class AdsSettings:
    """A personalização da coleta, guardada em app.data_sources.config (chaves em snake_case)."""

    metrics: tuple[str, ...] = ("reach",)
    conversions: tuple[str, ...] = ("lead", CONVERSATION_TYPE)
    campaigns: tuple[str, ...] | None = None  # None = todas
    breakdowns: tuple[str, ...] = ()
    backfill_days: int = 1095
    creatives: bool = True
    collect_version: int = 1  # sobe quando a coleta precisa refazer o histórico

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "AdsSettings":
        d = cls()
        campaigns = config.get("campaigns")
        return cls(
            metrics=tuple(m for m in config.get("metrics", d.metrics) if m in GROUP_FIELDS),
            conversions=tuple(config.get("conversions") or d.conversions),
            campaigns=tuple(str(c) for c in campaigns) if campaigns else None,
            breakdowns=tuple(b for b in config.get("breakdowns", ()) if b in BREAKDOWNS),
            backfill_days=int(config.get("backfill_days") or d.backfill_days),
            creatives=bool(config.get("creatives", d.creatives)),
            collect_version=int(config.get("collect_version") or 1),
        )

    def to_config(self) -> dict[str, Any]:
        return {
            "metrics": list(self.metrics),
            "conversions": list(self.conversions),
            "campaigns": list(self.campaigns) if self.campaigns is not None else None,
            "breakdowns": list(self.breakdowns),
            "backfill_days": self.backfill_days,
            "creatives": self.creatives,
            "collect_version": self.collect_version,
        }

    def to_api(self) -> dict[str, Any]:
        """O formato da tela (camelCase), sem a versão interna."""
        return {
            "metrics": list(self.metrics),
            "conversions": list(self.conversions),
            "campaigns": list(self.campaigns) if self.campaigns is not None else None,
            "breakdowns": list(self.breakdowns),
            "backfillDays": self.backfill_days,
            "creatives": self.creatives,
        }

    def needs_recollect(self, new: "AdsSettings") -> bool:
        """Métricas, campanhas, detalhamentos ou histórico mudaram: a coleta refaz o histórico.
        Só as conversões (ou os criativos) mudarem não pede: "resultados" sai das ações guardadas."""
        return (
            set(self.metrics) != set(new.metrics)
            or (set(self.campaigns) if self.campaigns else None)
            != (set(new.campaigns) if new.campaigns else None)
            or set(self.breakdowns) != set(new.breakdowns)
            or self.backfill_days != new.backfill_days
        )

    def ad_fields(self) -> str:
        extra = [f for g in self.metrics for f in GROUP_FIELDS.get(g, ())]
        return ",".join((*BASE_AD_FIELDS, *extra))

    def breakdown_fields(self, with_reach: bool) -> str:
        extra = ("reach",) if with_reach and "reach" in self.metrics else ()
        return ",".join((*BASE_BREAKDOWN_FIELDS, *extra))


ActionType = Annotated[str, Field(pattern=r"^[a-z0-9_.]{1,80}$")]
CampaignId = Annotated[str, Field(pattern=r"^\d{1,30}$")]


class AdsSettingsIn(BaseModel):
    """A personalização que a tela manda (Conectar e Personalizar coleta)."""

    metrics: list[MetricGroup] = Field(default_factory=lambda: ["reach"], max_length=3)
    conversions: list[ActionType] = Field(
        default_factory=lambda: ["lead", CONVERSATION_TYPE], min_length=1, max_length=20
    )
    campaigns: list[CampaignId] | None = Field(default=None, min_length=1, max_length=500)
    breakdowns: list[Breakdown] = Field(default_factory=list, max_length=4)
    backfillDays: Literal[90, 365, 1095] = 1095
    creatives: bool = True

    def to_settings(self, collect_version: int = 1) -> AdsSettings:
        return AdsSettings(
            metrics=tuple(sorted(set(self.metrics))),
            conversions=tuple(dict.fromkeys(self.conversions)),
            campaigns=tuple(dict.fromkeys(self.campaigns)) if self.campaigns else None,
            breakdowns=tuple(b for b in BREAKDOWNS if b in self.breakdowns),
            backfill_days=self.backfillDays,
            creatives=self.creatives,
            collect_version=collect_version,
        )


# A estrutura das tabelas, para o analista (detalhe técnico da fonte).
SCHEMA_CACHE = {
    "app.facebook_ads_daily": [
        [c, t]
        for c, t in (
            ("day", "date"),
            ("ad_id", "text"),
            ("ad_name", "text"),
            ("adset_id", "text"),
            ("adset_name", "text"),
            ("campaign_id", "text"),
            ("campaign_name", "text"),
            ("currency", "text"),
            ("spend", "numeric"),
            ("impressions", "bigint"),
            ("clicks", "bigint"),
            ("link_clicks", "bigint"),
            ("outbound_clicks", "bigint"),
            ("landing_page_views", "bigint"),
            ("leads", "bigint"),
            ("conversations", "bigint"),
            ("results", "numeric"),
            ("reach", "bigint"),
            ("frequency", "numeric"),
            ("video_plays", "bigint"),
            ("video_thruplays", "bigint"),
            ("video_p25", "bigint"),
            ("video_p50", "bigint"),
            ("video_p75", "bigint"),
            ("video_p100", "bigint"),
            ("quality_ranking", "text"),
            ("engagement_ranking", "text"),
            ("conversion_ranking", "text"),
            ("actions", "jsonb"),
            ("action_values", "jsonb"),
        )
    ],
    "app.facebook_ads_breakdowns": [
        [c, t]
        for c, t in (
            ("day", "date"),
            ("breakdown", "text"),
            ("campaign_id", "text"),
            ("campaign_name", "text"),
            ("dim1", "text"),
            ("dim2", "text"),
            ("spend", "numeric"),
            ("impressions", "bigint"),
            ("clicks", "bigint"),
            ("link_clicks", "bigint"),
            ("landing_page_views", "bigint"),
            ("leads", "bigint"),
            ("conversations", "bigint"),
            ("results", "numeric"),
            ("reach", "bigint"),
            ("actions", "jsonb"),
        )
    ],
    "app.facebook_ads_entities": [
        [c, t]
        for c, t in (
            ("level", "text"),
            ("id", "text"),
            ("name", "text"),
            ("campaign_id", "text"),
            ("adset_id", "text"),
            ("status", "text"),
            ("effective_status", "text"),
            ("objective", "text"),
            ("optimization_goal", "text"),
            ("daily_budget", "numeric"),
            ("lifetime_budget", "numeric"),
            ("start_time", "timestamptz"),
            ("stop_time", "timestamptz"),
            ("creative", "jsonb"),
        )
    ],
}

# Campos das campanhas, conjuntos e anúncios (o anúncio leva o criativo quando config.creatives).
ENTITY_FIELDS = {
    "campaign": "id,name,status,effective_status,objective,daily_budget,lifetime_budget,start_time,"
    "stop_time,created_time",
    "adset": "id,name,campaign_id,status,effective_status,optimization_goal,daily_budget,"
    "lifetime_budget,start_time,end_time,created_time",
    "ad": "id,name,campaign_id,adset_id,status,effective_status,created_time",
}
CREATIVE_FIELDS = (
    "creative{id,title,body,image_url,thumbnail_url,link_url,call_to_action_type,object_type,"
    "object_story_spec}"
)
ENTITY_PATH = {"campaign": "campaigns", "adset": "adsets", "ad": "ads"}


def normalize_account(raw: str) -> str | None:
    """'act_123', '123' ou ' act_123 ' -> 'act_123'. Fora disso, None."""
    m = _ACCOUNT_RE.match(re.sub(r"\s+", "", raw or ""))
    return f"act_{m.group(1)}" if m else None


class GraphUnavailable(Exception):
    """A API não alcançou graph.facebook.com (rede, DNS, tempo esgotado)."""

    screen_message = "A API não alcançou graph.facebook.com."


class GraphError(Exception):
    """A Meta respondeu com erro. `kind`: token, permission, not_found, throttle, too_much ou other."""

    def __init__(self, status: int, code: int | None, subcode: int | None, message: str):
        self.status, self.code, self.subcode = status, code, subcode
        self.kind = _kind(status, code, message)
        super().__init__(f"Graph API {status}, código {code}/{subcode}")

    @property
    def screen_message(self) -> str:
        return {
            "token": "A Meta recusou o token (inválido, expirado ou revogado). Gere um novo token do "
            "usuário do sistema.",
            "permission": "O token não lê esta conta. No Gerenciador de Negócios, dê ao usuário do "
            "sistema acesso à conta de anúncios e gere o token com a permissão ads_read.",
            "not_found": "A Meta não achou essa conta de anúncios (ou o token não tem acesso a ela). "
            "Confira o ID em Configurações da conta do Gerenciador de Anúncios.",
            "throttle": "A Meta limitou as chamadas deste app agora. Tente de novo em alguns minutos.",
            "too_much": "A Meta pediu para buscar menos dados por vez.",
        }.get(self.kind, f"A Meta respondeu com erro (código {self.code or self.status}).")


def _kind(status: int, code: int | None, message: str) -> str:
    if code in _TOKEN_CODES:
        return "token"
    if code in _THROTTLE_CODES:
        return "throttle"
    if code in _PERMISSION_CODES:
        return "permission"
    if code == 100:
        return "not_found"
    if code == 1 or "reduce the amount of data" in message.lower():
        return "too_much"
    if status == 401:
        return "token"
    if status == 403:
        return "permission"
    return "other"


@dataclass(frozen=True)
class AccountInfo:
    id: str  # act_123
    name: str
    currency: str
    timezone: str
    status: int | None

    def to_api(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "currency": self.currency,
            "timezone": self.timezone,
            "status": ACCOUNT_STATUS.get(self.status) if self.status is not None else None,
        }


def _filter_campaigns(path_field: str, campaigns: Iterable[str] | None) -> dict[str, str]:
    if not campaigns:
        return {}
    flt = [{"field": path_field, "operator": "IN", "value": list(campaigns)}]
    return {"filtering": json.dumps(flt)}


class GraphClient:
    """Chamadas GET à Graph API com o token no cabeçalho. `transport`: os testes passam um falso."""

    def __init__(
        self,
        token: str,
        *,
        version: str = "v26.0",
        app_secret: str = "",
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._proof = (
            hmac.new(app_secret.encode(), token.encode(), hashlib.sha256).hexdigest()
            if app_secret
            else None
        )
        self._token = token
        self._http = httpx.AsyncClient(
            base_url=f"{GRAPH_URL}/{version}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
            transport=transport,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._http.aclose()

    async def get(
        self, path: str, params: dict[str, Any] | None = None, *, auth: str | None = None
    ) -> dict[str, Any]:
        """GET com o token do cliente (ou `auth`, outro token, sem appsecret_proof) no cabeçalho."""
        query = dict(params or {})
        if self._proof and auth is None:
            query["appsecret_proof"] = self._proof
        headers = {"Authorization": f"Bearer {auth}"} if auth else None
        try:
            resp = await self._http.get(path, params=query, headers=headers)
        except httpx.TransportError as exc:
            raise GraphUnavailable(type(exc).__name__) from exc
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if resp.status_code >= 400 or (isinstance(body, dict) and "error" in body):
            err = body.get("error", {}) if isinstance(body, dict) else {}
            raise GraphError(
                resp.status_code,
                _int(err.get("code")),
                _int(err.get("error_subcode")),
                str(err.get("message", "")),
            )
        return body if isinstance(body, dict) else {}

    async def pages(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Todas as páginas de uma lista, pelo cursor `after` (o link `next` não é seguido)."""
        rows: list[dict] = []
        params = {"limit": 500, **params}
        while True:
            body = await self.get(path, params)
            rows.extend(r for r in body.get("data") or [] if isinstance(r, dict))
            paging = body.get("paging") or {}
            after = (paging.get("cursors") or {}).get("after")
            if not paging.get("next") or not after:
                return rows
            params = {**params, "after": after}

    async def me(self) -> dict[str, Any]:
        return await self.get("/me", {"fields": "id,name"})

    async def debug_token(self, app_token: str) -> dict[str, Any]:
        """Tipo, app, validade e permissões do próprio token (/debug_token, com o token do app).
        A Meta só aceita o token inspecionado em input_token (na URL, por HTTPS); nenhum log nosso
        guarda URL nem a mensagem de erro da Meta."""
        body = await self.get("/debug_token", {"input_token": self._token}, auth=app_token)
        data = body.get("data")
        return data if isinstance(data, dict) else {}

    async def account(self, account_id: str) -> AccountInfo:
        a = await self.get(
            f"/{account_id}", {"fields": "name,currency,timezone_name,account_status"}
        )
        return AccountInfo(
            id=account_id,
            name=str(a.get("name") or account_id),
            currency=str(a.get("currency") or ""),
            timezone=str(a.get("timezone_name") or ""),
            status=_int(a.get("account_status")),
        )

    async def last_7_days(self, account_id: str) -> dict[str, Any]:
        """Totais da conta nos últimos 7 dias (testa a leitura de relatórios)."""
        body = await self.get(
            f"/{account_id}/insights",
            {"level": "account", "date_preset": "last_7d", "fields": "spend,impressions"},
        )
        data = body.get("data") or []
        return data[0] if data else {}

    async def report(
        self,
        account_id: str,
        *,
        level: str,
        fields: str,
        preset: str | None = None,
        since: date | None = None,
        until: date | None = None,
        daily: bool = False,
        breakdowns: Iterable[str] = (),
        campaigns: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        """/insights de um período (`preset` ou `since`..`until`), todas as páginas.

        Se a Meta pedir menos dados por vez, divide o período ao meio (até um dia por chamada).
        """
        params: dict[str, Any] = {"level": level, "fields": fields}
        if preset:
            params["date_preset"] = preset
        else:
            assert since is not None and until is not None
            span = {"since": since.isoformat(), "until": until.isoformat()}
            params["time_range"] = json.dumps(span)
        if daily:
            params["time_increment"] = 1
        if breakdowns:
            params["breakdowns"] = ",".join(breakdowns)
        params |= _filter_campaigns("campaign.id", campaigns)
        try:
            return await self.pages(f"/{account_id}/insights", params)
        except GraphError as exc:
            if exc.kind != "too_much" or preset or since is None or until is None or since >= until:
                raise
        middle = since + timedelta(days=(until - since).days // 2)
        kwargs = {
            "level": level,
            "fields": fields,
            "daily": daily,
            "breakdowns": breakdowns,
            "campaigns": campaigns,
        }
        first = await self.report(account_id, since=since, until=middle, **kwargs)
        rest = await self.report(
            account_id, since=middle + timedelta(days=1), until=until, **kwargs
        )
        return first + rest

    async def entities(
        self,
        account_id: str,
        level: str,
        *,
        creatives: bool = False,
        campaigns: Iterable[str] | None = None,
        ids: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Campanhas, conjuntos ou anúncios da conta (o anúncio com o criativo, se pedido)."""
        fields = ENTITY_FIELDS[level] + (
            f",{CREATIVE_FIELDS}" if level == "ad" and creatives else ""
        )
        params: dict[str, Any] = {"fields": fields}
        if ids:
            params |= _filter_campaigns(f"{level}.id" if level != "campaign" else "id", ids)
        elif campaigns:
            params |= _filter_campaigns("id" if level == "campaign" else "campaign.id", campaigns)
        return await self.pages(f"/{account_id}/{ENTITY_PATH[level]}", params)


ClientFactory = Callable[[str], GraphClient]  # token -> cliente
AdsChecker = Callable[[str, str], Awaitable[tuple[CheckResult, AccountInfo | None]]]


class _MetaSource(Protocol):
    @property
    def current(self) -> Any: ...  # MetaSettings (app/meta_config.py)


def client_factory(meta: _MetaSource, timeout: float) -> ClientFactory:
    """token -> cliente da Graph API com a versão e a chave do app em uso (tela ou .env, app/meta_config.py),
    lidas na hora de cada cliente: mudou na tela, a próxima chamada já usa."""
    return lambda token: GraphClient(
        token,
        version=meta.current.graph_version,
        app_secret=meta.current.app_secret,
        timeout=timeout,
    )


# --- Linhas da Meta -> linhas das tabelas ------------------------------------------------------------


@dataclass
class _Actions:
    items: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def of(cls, value: Any) -> "_Actions":
        return cls([a for a in value or [] if isinstance(a, dict)])

    def sum(self, *types: str) -> int:
        return sum(_whole(a.get("value")) for a in self.items if a.get("action_type") in types)

    def total(self, types: Iterable[str]) -> Decimal:
        wanted = set(types)
        return sum(
            (_number(a.get("value")) for a in self.items if a.get("action_type") in wanted),
            Decimal(0),
        )


def _common(r: dict[str, Any], settings: AdsSettings) -> dict[str, Any] | None:
    """O que a linha de anúncio e a de detalhamento têm em comum. Sem dia válido: None."""
    try:
        day = date.fromisoformat(str(r.get("date_start")))
    except ValueError:
        return None
    actions = _Actions.of(r.get("actions"))
    return {
        "day": day,
        "campaign_id": r.get("campaign_id"),
        "campaign_name": r.get("campaign_name"),
        "spend": _money(r.get("spend")),
        "impressions": _whole(r.get("impressions")),
        "clicks": _whole(r.get("clicks")),
        "link_clicks": _whole(r.get("inline_link_clicks")),
        "landing_page_views": actions.sum("landing_page_view")
        or actions.sum("omni_landing_page_view"),
        # 'lead' é o número do Gerenciador de Anúncios (formulário + pixel); sem ele, a soma dos dois.
        "leads": actions.sum("lead") or actions.sum(*LEAD_TYPES),
        "conversations": actions.sum(CONVERSATION_TYPE),
        "results": actions.total(settings.conversions),
        "reach": _optional(r.get("reach")),
        "actions": actions.items,
    }


def parse_row(r: dict[str, Any], settings: AdsSettings | None = None) -> dict[str, Any] | None:
    """Uma linha de /insights (level=ad, time_increment=1) no formato de app.facebook_ads_daily.
    Sem anúncio ou dia válido: None. Grupo não coletado: as colunas dele ficam None."""
    settings = settings or AdsSettings()
    ad_id = str(r.get("ad_id") or "")
    base = _common(r, settings) if ad_id.isdigit() else None
    if base is None:
        return None
    video = "video" in settings.metrics
    quality = "quality" in settings.metrics
    return base | {
        "ad_id": ad_id,
        "ad_name": r.get("ad_name"),
        "adset_id": r.get("adset_id"),
        "adset_name": r.get("adset_name"),
        "account_id": str(r.get("account_id") or ""),
        "currency": r.get("account_currency"),
        "outbound_clicks": _Actions.of(r.get("outbound_clicks")).sum("outbound_click"),
        "frequency": _ratio(r.get("frequency")) if "reach" in settings.metrics else None,
        "video_plays": _video(r, "video_play_actions") if video else None,
        "video_thruplays": _video(r, "video_thruplay_watched_actions") if video else None,
        "video_p25": _video(r, "video_p25_watched_actions") if video else None,
        "video_p50": _video(r, "video_p50_watched_actions") if video else None,
        "video_p75": _video(r, "video_p75_watched_actions") if video else None,
        "video_p100": _video(r, "video_p100_watched_actions") if video else None,
        "quality_ranking": _rank(r.get("quality_ranking")) if quality else None,
        "engagement_ranking": _rank(r.get("engagement_rate_ranking")) if quality else None,
        "conversion_ranking": _rank(r.get("conversion_rate_ranking")) if quality else None,
        "action_values": _Actions.of(r.get("action_values")).items,
    }


def parse_breakdown_row(
    r: dict[str, Any], breakdown: str, settings: AdsSettings
) -> dict[str, Any] | None:
    """Uma linha de /insights (level=campaign, com breakdowns) no formato de app.facebook_ads_breakdowns."""
    keys = BREAKDOWNS[breakdown]
    campaign = str(r.get("campaign_id") or "")
    base = _common(r, settings) if campaign.isdigit() else None
    if base is None:
        return None
    return base | {
        "breakdown": breakdown,
        "dim1": str(r.get(keys[0]) or ""),
        "dim2": str(r.get(keys[1]) or "") if len(keys) > 1 else "",
    }


def parse_creative(c: Any) -> dict[str, Any] | None:
    """O criativo de um anúncio: título, texto, imagem, link e chamada (o que existir)."""
    if not isinstance(c, dict):
        return None
    spec = c.get("object_story_spec") or {}
    link = spec.get("link_data") or {}
    video = spec.get("video_data") or {}
    cta = link.get("call_to_action") or video.get("call_to_action") or {}
    out = {
        "id": c.get("id"),
        "title": c.get("title") or link.get("name") or video.get("title"),
        "body": c.get("body") or link.get("message") or video.get("message"),
        "imageUrl": c.get("image_url")
        or link.get("picture")
        or video.get("image_url")
        or c.get("thumbnail_url"),
        "thumbnailUrl": c.get("thumbnail_url"),
        "linkUrl": c.get("link_url") or link.get("link") or (cta.get("value") or {}).get("link"),
        "callToAction": c.get("call_to_action_type") or cta.get("type"),
        "type": c.get("object_type"),
    }
    return {k: v for k, v in out.items() if v} or None


def parse_entity(level: str, r: dict[str, Any]) -> dict[str, Any] | None:
    """Campanha, conjunto ou anúncio no formato de app.facebook_ads_entities."""
    ident = str(r.get("id") or "")
    if not ident.isdigit():
        return None
    return {
        "level": level,
        "id": ident,
        "name": r.get("name"),
        "campaign_id": r.get("campaign_id") if level != "campaign" else ident,
        "adset_id": r.get("adset_id") if level == "ad" else (ident if level == "adset" else None),
        "status": r.get("status"),
        "effective_status": r.get("effective_status"),
        "objective": r.get("objective"),
        "optimization_goal": r.get("optimization_goal"),
        "daily_budget": _budget(r.get("daily_budget")),
        "lifetime_budget": _budget(r.get("lifetime_budget")),
        "start_time": _when(r.get("start_time")),
        "stop_time": _when(r.get("stop_time") or r.get("end_time")),
        "created_time": _when(r.get("created_time")),
        "creative": parse_creative(r.get("creative")) if level == "ad" else None,
    }


# --- Teste de conexão ---------------------------------------------------------------------------------


async def check_account(
    client_for: ClientFactory, account_id: str, token: str
) -> tuple[CheckResult, AccountInfo | None]:
    """As quatro checagens da tela, para a conta `account_id` ('act_123') com `token`."""
    started = time.perf_counter()
    checks: list[Check] = []

    def ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    def done(info: AccountInfo | None = None) -> tuple[CheckResult, AccountInfo | None]:
        keys = ("network", "login", "read", "account")
        for key in keys[len(checks) :]:
            checks.append(Check(key, False, "", ms(), skipped=True))  # type: ignore[arg-type]
        schema = SCHEMA_CACHE if info is not None else None
        return CheckResult(checks, schema_cache=schema, ms=ms()), info

    async with client_for(token) as graph:
        try:
            me = await graph.me()
        except GraphUnavailable:
            checks.append(Check("network", False, "A API não alcançou graph.facebook.com.", ms()))
            return done()
        except GraphError as exc:
            checks.append(Check("network", True, "A API alcançou graph.facebook.com", ms()))
            checks.append(Check("login", False, exc.screen_message, ms()))
            return done()
        checks.append(Check("network", True, "A API alcançou graph.facebook.com", ms()))
        who = f" (usuário {me['name']})" if me.get("name") else ""
        checks.append(Check("login", True, f"Token aceito pela Meta{who}", ms()))

        try:
            info = await graph.account(account_id)
            week = await graph.last_7_days(account_id)
        except GraphUnavailable:
            checks.append(Check("read", False, "A conexão com a Meta caiu no meio do teste.", ms()))
            return done()
        except GraphError as exc:
            checks.append(Check("read", False, exc.screen_message, ms()))
            return done()

    spend = _money(week.get("spend"))
    impressions = _whole(week.get("impressions"))
    currency = f"{info.currency} " if info.currency else ""
    checks.append(
        Check(
            "read",
            True,
            f"Conta {info.name}: {currency}{_br(spend, 2)} gastos e {_br(impressions)} impressões "
            "nos últimos 7 dias",
            ms(),
        )
    )
    if info.status in (1, None):
        checks.append(Check("account", True, "Conta de anúncios ativa", ms()))
    else:
        state = ACCOUNT_STATUS.get(info.status, f"com status {info.status}")
        checks.append(
            Check(
                "account",
                False,
                f"A conta está {state}: a coleta traz o histórico, mas não há anúncios novos.",
                ms(),
                severity="warn",
            )
        )
    return done(info)


# --- O que o token permite (o passo Acesso) --------------------------------------------------------------

# Permissões da Meta na tela (https://developers.facebook.com/docs/permissions).
PERMISSION_LABELS = {
    "ads_read": "Ler relatórios de anúncios",
    "ads_management": "Gerenciar anúncios",
    "business_management": "Gerenciar negócios",
    "leads_retrieval": "Baixar leads de formulário",
    "pages_manage_ads": "Anúncios das páginas",
    "pages_show_list": "Listar páginas",
    "pages_read_engagement": "Ler engajamento das páginas",
    "pages_manage_metadata": "Configurar páginas (webhooks)",
    "read_insights": "Insights das páginas",
    "instagram_basic": "Perfil do Instagram",
    "instagram_manage_insights": "Insights do Instagram",
    "catalog_management": "Catálogos de produtos",
    "public_profile": "Perfil público",
    "email": "E-mail",
}

TOKEN_TYPES = {
    "SYSTEM_USER": "Usuário do sistema",
    "USER": "Usuário",
    "PAGE": "Página",
    "APP": "App",
}


def capabilities(granted: set[str], accounts: int, businesses: int) -> list[dict[str, str]]:
    """O que dá para fazer com o token. status: used (o LexHub coleta), available (o token permite, o
    LexHub ainda não coleta), warn (permite mais que o necessário), missing (falta permissão)."""
    reads = bool(granted & {"ads_read", "ads_management"})
    pages = bool(granted & {"pages_show_list", "pages_read_engagement", "read_insights"})
    instagram = bool(granted & {"instagram_basic", "instagram_manage_insights"})
    out = [
        {
            "key": "insights",
            "label": "Relatórios de anúncios",
            "status": "used" if reads else "missing",
            "detail": (
                f"Métricas, detalhamentos, campanhas e criativos de {accounts} conta(s) de anúncios"
                if reads
                else "Falta a permissão ads_read (é a única que o LexHub precisa)"
            ),
        },
        {
            "key": "manage",
            "label": "Criar e alterar anúncios",
            "status": "warn" if "ads_management" in granted else "missing",
            "detail": (
                "O token pode alterar anúncios. O LexHub só lê: para menos risco, gere o token só com ads_read"
                if "ads_management" in granted
                else "Não pode (melhor assim: o LexHub só lê)"
            ),
        },
        {
            "key": "business",
            "label": "Gerenciadores de Negócios",
            "status": "available" if "business_management" in granted else "missing",
            "detail": (
                f"Vê {businesses} negócio(s); o LexHub mostra o negócio de cada conta"
                if "business_management" in granted
                else "Opcional: com business_management, a tela mostra o negócio de cada conta"
            ),
        },
        {
            "key": "leads",
            "label": "Dados dos leads de formulário",
            "status": "available" if "leads_retrieval" in granted else "missing",
            "detail": (
                "O token permite baixar nome, telefone e e-mail dos formulários; o LexHub ainda não coleta"
                if "leads_retrieval" in granted
                else "Precisa de leads_retrieval e pages_manage_ads, com revisão do app pela Meta"
            ),
        },
        {
            "key": "pages",
            "label": "Páginas do Facebook",
            "status": "available" if pages else "missing",
            "detail": (
                "O token lê as páginas (seguidores, alcance orgânico); o LexHub ainda não coleta"
                if pages
                else "Opcional: pages_show_list e pages_read_engagement"
            ),
        },
        {
            "key": "instagram",
            "label": "Contas do Instagram",
            "status": "available" if instagram else "missing",
            "detail": (
                "O token lê o perfil e os insights do Instagram; o LexHub ainda não coleta"
                if instagram
                else "Opcional: instagram_basic e instagram_manage_insights"
            ),
        },
    ]
    return out


ACCOUNT_FIELDS = (
    "id,account_id,name,currency,timezone_name,account_status,amount_spent,business{id,name}"
)
# Até quantos negócios a leitura do token abre para achar contas não atribuídas (cada um = 2 chamadas).
MAX_BUSINESSES = 10


def _account_item(
    a: dict[str, Any], *, assigned: bool = True, business: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Uma conta de anúncios na lista do token. assigned=False: o negócio tem a conta, mas ela não foi
    atribuída ao usuário do token (os relatórios dela não abrem com este token)."""
    account = normalize_account(str(a.get("id") or a.get("account_id") or ""))
    if account is None:
        return None
    status = _int(a.get("account_status"))
    owner = a.get("business") if isinstance(a.get("business"), dict) else (business or {})
    return {
        "id": account,
        "name": a.get("name") or account,
        "currency": a.get("currency") or "",
        "timezone": a.get("timezone_name") or "",
        "status": ACCOUNT_STATUS.get(status) if status is not None else None,
        "active": status in (1, None),
        "business": owner.get("name"),
        "businessId": str(owner["id"]) if owner.get("id") else None,
        "spent": float(_budget(a.get("amount_spent")) or 0),  # total gasto na vida da conta
        "assigned": assigned,
    }


async def _business_accounts(
    graph: GraphClient, businesses: list[dict[str, Any]], known: set[str]
) -> list[dict[str, Any]]:
    """As contas dos negócios (próprias e de clientes) que não estão em /me/adaccounts: o token vê o
    negócio, mas a conta não foi atribuída ao usuário. Negócio que não abre (sem papel de admin) é pulado."""
    found: list[dict[str, Any]] = []
    for b in businesses[:MAX_BUSINESSES]:
        for edge in ("owned_ad_accounts", "client_ad_accounts"):
            try:
                raw = await graph.pages(f"/{b['id']}/{edge}", {"fields": ACCOUNT_FIELDS})
            except GraphError:
                continue
            for r in raw:
                item = _account_item(r, assigned=False, business=b)
                if item is not None and item["id"] not in known:
                    known.add(item["id"])
                    found.append(item)
    return found


async def token_info(graph: GraphClient, *, app_token: str | None = None) -> dict[str, Any]:
    """Quem é o token, o que ele permite e as contas de anúncios que ele acessa (com o nome).

    /me e /me/permissions sempre; /me/adaccounts se puder ler anúncios; /me/businesses com
    business_management; tipo e validade só com o token do app (ID + chave, Integração Meta).
    """
    started = time.perf_counter()

    def ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    empty: dict[str, Any] = {
        "user": None,
        "tokenType": None,
        "expiresAt": None,
        "neverExpires": None,
        "app": None,
        "permissions": [],
        "capabilities": [],
        "accounts": [],
        "businesses": [],
    }
    try:
        me = await graph.me()
    except GraphUnavailable:
        check = Check("network", False, "A API não alcançou graph.facebook.com.", ms())
        return {"ok": False, "checks": [vars(check)], **empty}
    except GraphError as exc:
        checks = [
            Check("network", True, "A API alcançou graph.facebook.com", ms()),
            Check("login", False, exc.screen_message, ms()),
        ]
        return {"ok": False, "checks": [vars(c) for c in checks], **empty}

    perms = await graph.pages("/me/permissions", {})
    granted = {str(p.get("permission")) for p in perms if p.get("status") == "granted"}
    permissions = sorted(
        (
            {
                "name": str(p.get("permission")),
                "label": PERMISSION_LABELS.get(str(p.get("permission")), str(p.get("permission"))),
                "granted": p.get("status") == "granted",
            }
            for p in perms
            if p.get("permission")
        ),
        key=lambda p: (not p["granted"], p["label"]),
    )
    accounts: list[dict[str, Any]] = []
    if granted & {"ads_read", "ads_management"}:
        raw = await graph.pages("/me/adaccounts", {"fields": ACCOUNT_FIELDS, "limit": 200})
        accounts = [a for a in (_account_item(r) for r in raw) if a is not None]
    # Os negócios: os do usuário (/me/businesses, com business_management) e os donos das contas.
    by_id: dict[str, dict[str, Any]] = {}
    if "business_management" in granted:
        try:
            for b in await graph.pages("/me/businesses", {"fields": "id,name"}):
                if b.get("id"):
                    by_id[str(b["id"])] = {"id": str(b["id"]), "name": b.get("name")}
        except GraphError:
            pass
    for a in accounts:
        if a["businessId"]:
            by_id.setdefault(a["businessId"], {"id": a["businessId"], "name": a["business"]})
    businesses = list(by_id.values())
    if "business_management" in granted and businesses:
        known = {a["id"] for a in accounts}
        accounts += await _business_accounts(graph, businesses, known)
    # As que o token lê primeiro; depois as ativas; depois pelo nome.
    accounts.sort(key=lambda a: (not a["assigned"], not a["active"], str(a["name"]).lower()))
    readable = [a for a in accounts if a["assigned"]]
    debug: dict[str, Any] = {}
    if app_token:
        try:
            debug = await graph.debug_token(app_token)
        except (GraphError, GraphUnavailable):
            debug = {}
    expires = _int(debug.get("expires_at")) if debug else None
    who = f" (usuário {me['name']})" if me.get("name") else ""
    checks = [
        Check("network", True, "A API alcançou graph.facebook.com", ms()),
        Check("login", True, f"Token aceito pela Meta{who}", ms()),
    ]
    hidden = len(accounts) - len(readable)
    if not readable:
        detail = (
            "O token não acessa nenhuma conta de anúncios. No Gerenciador de Negócios, atribua a conta "
            "ao usuário do sistema."
            if granted & {"ads_read", "ads_management"}
            else "O token não tem a permissão ads_read: gere de novo marcando ads_read."
        )
        checks.append(Check("read", False, detail, ms()))
    else:
        extra = f"; {hidden} do negócio sem acesso aos relatórios" if hidden else ""
        message = f"{len(readable)} conta(s) de anúncios com acesso{extra}"
        checks.append(Check("read", True, message, ms()))
    return {
        "ok": bool(readable),
        "checks": [vars(c) for c in checks],
        "user": {"id": str(me.get("id") or ""), "name": me.get("name")},
        "tokenType": TOKEN_TYPES.get(str(debug.get("type")), debug.get("type")) if debug else None,
        "expiresAt": (
            datetime.fromtimestamp(expires).astimezone().isoformat() if expires else None
        ),
        "neverExpires": (expires == 0) if debug else None,
        "app": debug.get("application") if debug else None,
        "permissions": permissions,
        "capabilities": capabilities(granted, len(readable), len(businesses)),
        "accounts": accounts,
        "businesses": businesses,
    }


# --- Opções da conta (o passo Personalizar) ------------------------------------------------------------


async def account_options(graph: GraphClient, account_id: str) -> dict[str, Any]:
    """As campanhas (com o gasto dos últimos 30 dias) e as conversões que a conta teve nos últimos 30 dias."""
    campaigns = await graph.entities(account_id, "campaign")
    by_campaign = await graph.report(
        account_id, level="campaign", fields="campaign_id,spend", preset="last_30d"
    )
    totals = await graph.report(account_id, level="account", fields="actions", preset="last_30d")
    spend30 = {str(r.get("campaign_id")): float(_money(r.get("spend"))) for r in by_campaign}
    counts: dict[str, int] = {t: 0 for t in ALWAYS_OFFERED}
    for row in totals:
        for a in _Actions.of(row.get("actions")).items:
            t = str(a.get("action_type") or "")
            if t:
                counts[t] = counts.get(t, 0) + _whole(a.get("value"))
    out_campaigns = [
        {
            "id": str(c.get("id")),
            "name": c.get("name") or str(c.get("id")),
            "status": c.get("effective_status") or c.get("status"),
            "objective": c.get("objective"),
            "spend30": spend30.get(str(c.get("id")), 0.0),
        }
        for c in campaigns
        if str(c.get("id") or "").isdigit()
    ]
    out_campaigns.sort(key=lambda c: (-c["spend30"], str(c["name"]).lower()))
    conversions = [
        {"type": t, "label": action_label(t), "count30": n}
        for t, n in sorted(counts.items(), key=lambda kv: (-kv[1], action_label(kv[0])))
    ]
    return {"campaigns": out_campaigns, "conversions": conversions}


# --- Prévia (o passo Prévia) ---------------------------------------------------------------------------


def _totals(rows: list[dict[str, Any]], settings: AdsSettings) -> dict[str, Any]:
    acts = [_Actions.of(r.get("actions")) for r in rows]
    reach = [r.get("reach") for r in rows if r.get("reach") not in (None, "")]
    video = [_video(r, "video_thruplay_watched_actions") for r in rows]
    return {
        "spend": float(sum((_money(r.get("spend")) for r in rows), Decimal(0))),
        "impressions": sum(_whole(r.get("impressions")) for r in rows),
        "clicks": sum(_whole(r.get("clicks")) for r in rows),
        "linkClicks": sum(_whole(r.get("inline_link_clicks")) for r in rows),
        "leads": sum(a.sum("lead") or a.sum(*LEAD_TYPES) for a in acts),
        "conversations": sum(a.sum(CONVERSATION_TYPE) for a in acts),
        "results": float(sum((a.total(settings.conversions) for a in acts), Decimal(0))),
        "reach": sum(_whole(v) for v in reach) if "reach" in settings.metrics and reach else None,
        "thruplays": sum(video) if "video" in settings.metrics else None,
    }


async def preview(graph: GraphClient, account_id: str, settings: AdsSettings) -> dict[str, Any]:
    """Os últimos 7 dias com a personalização: totais, campanhas, detalhamentos e os anúncios que mais
    gastaram (com o criativo, se escolhido)."""
    extra = (",reach" if "reach" in settings.metrics else "") + (
        ",video_thruplay_watched_actions" if "video" in settings.metrics else ""
    )
    base = "spend,impressions,clicks,inline_link_clicks,actions"
    common = {"preset": "last_7d", "campaigns": settings.campaigns}
    account_rows = await graph.report(
        account_id, level="account", fields=f"date_start,date_stop,{base}{extra}", **common
    )
    campaign_rows = await graph.report(
        account_id, level="campaign", fields=f"campaign_id,campaign_name,{base}{extra}", **common
    )
    campaigns = sorted(
        (
            {"id": str(r.get("campaign_id")), "name": r.get("campaign_name")}
            | _totals([r], settings)
            for r in campaign_rows
        ),
        key=lambda c: -c["spend"],
    )
    breakdowns = []
    for key in settings.breakdowns:
        rows = await graph.report(
            account_id,
            level="account",
            fields=base + (",reach" if "reach" in settings.metrics else ""),
            breakdowns=BREAKDOWNS[key],
            **common,
        )
        segments = sorted(
            (
                {"segment": [str(r.get(k) or "") for k in BREAKDOWNS[key]]} | _totals([r], settings)
                for r in rows
            ),
            key=lambda s: -s["spend"],
        )
        breakdowns.append({"key": key, "rows": segments[:10]})
    ads: list[dict[str, Any]] = []
    if settings.creatives:
        ad_rows = await graph.report(
            account_id,
            level="ad",
            fields=f"ad_id,ad_name,campaign_name,{base}",
            **common,
        )
        top = sorted(ad_rows, key=lambda r: -_money(r.get("spend")))[:4]
        ids = [str(r.get("ad_id")) for r in top if str(r.get("ad_id") or "").isdigit()]
        found = await graph.entities(account_id, "ad", creatives=True, ids=ids) if ids else []
        creative = {str(e.get("id")): parse_creative(e.get("creative")) for e in found}
        ads = [
            {
                "id": str(r.get("ad_id")),
                "name": r.get("ad_name"),
                "campaignName": r.get("campaign_name"),
                "creative": creative.get(str(r.get("ad_id"))),
            }
            | _totals([r], settings)
            for r in top
        ]
    first = account_rows[0] if account_rows else {}
    return {
        "since": first.get("date_start"),
        "until": first.get("date_stop"),
        "totals": _totals(account_rows, settings),
        "campaigns": campaigns,
        "breakdowns": breakdowns,
        "ads": ads,
    }


# --- Auxiliares -------------------------------------------------------------------------------------


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> Decimal:
    try:
        return max(Decimal(str(value)), Decimal(0))
    except (InvalidOperation, ValueError):
        return Decimal(0)


def _whole(value: Any) -> int:
    """'1234' -> 1234; vazio ou estranho -> 0 (a Meta manda número como texto)."""
    return int(_number(value))


def _optional(value: Any) -> int | None:
    return None if value in (None, "") else _whole(value)


def _money(value: Any) -> Decimal:
    return _number(value).quantize(Decimal("0.01"))


def _ratio(value: Any) -> Decimal | None:
    return None if value in (None, "") else _number(value).quantize(Decimal("0.0001"))


def _video(r: dict[str, Any], key: str) -> int:
    return _Actions.of(r.get(key)).sum("video_view")


def _rank(value: Any) -> str | None:
    text = str(value or "")
    return text if text and text != "UNKNOWN" else None


def _budget(value: Any) -> Decimal | None:
    """Orçamento da Meta vem em centavos ('5000' = 50,00)."""
    return None if value in (None, "", "0") else (_number(value) / 100).quantize(Decimal("0.01"))


def _when(value: Any) -> datetime | None:
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%S%z")
    except (TypeError, ValueError):
        return None


def _br(value: Decimal | int, decimals: int = 0) -> str:
    """1234.5 -> '1.234,50' (com decimals=2)."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")
