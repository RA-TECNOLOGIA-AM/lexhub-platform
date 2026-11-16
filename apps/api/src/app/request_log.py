"""Uma linha por requisição, dizendo o que a tela pediu, quem pediu, o status e quanto demorou.

    200  GET   dashboard protocolo · NG (01/11 a 16/11)        1,42s  piloto@lexgroup.com.br
    401  GET   sessão (login)                                   0,00s  sem login

Dados de dashboard e exportação ganham também uma linha "carregando ..." na entrada, porque são as
requisições lentas (query no banco de origem) e assim dá para ver a página carregando.
Health checks e preflight (OPTIONS) só aparecem em DEBUG.
"""

import logging
import sys
import time
from datetime import date
from urllib.parse import parse_qs

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.logs import BOLD, CYAN, DIM, GREEN, RED, YELLOW, Paint, seconds, wants_color

logger = logging.getLogger("app.requests")

SLOW_SECONDS = 3.0
_QUIET_PREFIXES = ("/health", "/docs", "/openapi.json", "/favicon.ico")


def _short_date(value: str | None) -> str | None:
    try:
        return date.fromisoformat(value).strftime("%d/%m") if value else None
    except ValueError:
        return value


def _query(scope: Scope) -> dict[str, list[str]]:
    return parse_qs(scope.get("query_string", b"").decode("latin-1"))


def describe(scope: Scope) -> str:
    """O que é a requisição, em português (depois do roteamento, com a rota já conhecida)."""
    route = scope.get("route")
    template = getattr(route, "path", None)
    params = scope.get("path_params") or {}
    key = params.get("dashboard_key")
    unit = params.get("unit_code")
    where = f"{key} · {unit}" if unit else str(key)
    query = _query(scope)

    if template is None:
        return f"{scope.get('path', '?')} (rota inexistente)"
    if template == "/me":
        return "sessão (login)"
    if template == "/orgs/{org_slug}/dashboards":
        return f"catálogo de dashboards · {params.get('org_slug')}"
    if template.endswith("/dashboards/{dashboard_key}"):
        start = _short_date((query.get("from") or [None])[0])
        end = _short_date((query.get("to") or [None])[0])
        period = f" ({start or 'início'} a {end or 'hoje'})" if start or end else ""
        return f"dashboard {where}{period}"
    if template.endswith("/dashboards/{dashboard_key}/access"):
        return f"acesso ao dashboard {where}"
    if template.endswith("/dashboards/{dashboard_key}/export"):
        fmt = (query.get("format") or ["csv"])[0]
        return f"exportação {where} ({fmt})"
    if "/favorites" in template:
        return f"favoritos{f' · {key}' if key else ''}"
    if template.endswith("/hub-order"):
        return "ordem do hub"
    return template


def _who(scope: Scope) -> str:
    state = scope.get("state") or {}
    return state.get("user_email") or state.get("user_id") or "sem login"


class RequestLogMiddleware:
    """Middleware ASGI puro (não atrapalha streaming): mede, descreve e loga cada requisição."""

    def __init__(self, app: ASGIApp, color: bool | None = None):
        self.app = app
        self.paint = Paint(wants_color(sys.stderr) if color is None else color)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status_code = 500
        quiet = scope["method"] == "OPTIONS" or scope["path"].startswith(_QUIET_PREFIXES)

        async def capture(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        # A rota só é conhecida depois do roteamento; para a linha "carregando", olha antes.
        heavy_hint = "/dashboards/" in scope["path"] and "/units/" in scope["path"]
        if heavy_hint and not scope["path"].endswith("/access") and not quiet:
            logger.info(
                "%s", self.paint(f"…    {scope['method']:<5} carregando {_preview(scope)}", DIM)
            )

        try:
            await self.app(scope, receive, capture)
        except Exception:
            status_code = 500
            raise
        finally:
            self._log(scope, status_code, time.perf_counter() - started, quiet)

    def _log(self, scope: Scope, status_code: int, elapsed: float, quiet: bool) -> None:
        p = self.paint
        what = describe(scope)
        if status_code >= 500:
            level, color = logging.ERROR, RED
        elif status_code >= 400:
            level, color = logging.WARNING, YELLOW
        else:
            level, color = logging.INFO, GREEN
        if quiet and status_code < 500:
            level = logging.DEBUG
        took = seconds(elapsed)
        if elapsed >= SLOW_SECONDS:
            took = p(f"{took} (lento)", YELLOW, BOLD)
            level = max(level, logging.WARNING)
        line = (
            f"{p(str(status_code), color, BOLD)}  {scope['method']:<5} {what}  "
            f"{p(took, CYAN)}  {p(_who(scope), DIM)}"
        )
        logger.log(level, "%s", line)


def _preview(scope: Scope) -> str:
    """Descrição antes do roteamento: tira dashboard e unidade direto do caminho."""
    parts = scope["path"].strip("/").split("/")
    # /orgs/{org}/units/{unit}/dashboards/{key}[/export]
    try:
        unit = parts[parts.index("units") + 1]
        key = parts[parts.index("dashboards") + 1]
    except (ValueError, IndexError):
        return scope["path"]
    kind = "exportação" if parts[-1] == "export" else "dashboard"
    return f"{kind} {key} · {unit}"
