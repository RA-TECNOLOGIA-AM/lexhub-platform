"""Modo suporte é só leitura: com X-Support-Session, só as rotas desta lista respondem.

Fica no nível da app (create_app), então vale também para as rotas que vierem depois: rota nova
nasce bloqueada em suporte até alguém pô-la aqui. A lista é de (método, path do template da rota),
nunca da URL pedida, para um id na URL não escapar da regra.

Quem valida a sessão e troca o usuário pelo membro é app/access.py (resolve_support).
"""

from fastapi import HTTPException, Request, status

from app.access import SUPPORT_HEADER

_ORG = "/orgs/{org_slug}"
_DASHBOARD = f"{_ORG}/units/{{unit_code}}/dashboards/{{dashboard_key}}"
_SESSION = f"{_ORG}/support/sessions/{{session_id}}"

SUPPORT_ALLOWED: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/me"),
        ("GET", f"{_ORG}/dashboards"),
        ("GET", f"{_ORG}/favorites"),
        ("GET", f"{_ORG}/hub-order"),
        ("GET", _DASHBOARD),
        ("GET", f"{_DASHBOARD}/access"),
        ("GET", f"{_ORG}/sources/freshness"),
        ("DELETE", _SESSION),  # sair do modo suporte
        ("GET", f"{_SESSION}/hidden"),
    }
)


def allowed_in_support(method: str, path: str) -> bool:
    return (method, path) in SUPPORT_ALLOWED or (
        method == "GET" and (path == "/health" or path.startswith("/health/"))
    )


async def support_guard(request: Request) -> None:
    """Dependency da app inteira: com o cabeçalho e rota fora da lista, 403 support_read_only.
    Sem o cabeçalho, não faz nada."""
    if SUPPORT_HEADER not in request.headers:
        return
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path is None or not allowed_in_support(request.method, path):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="support_read_only")
