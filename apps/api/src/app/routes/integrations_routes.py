"""Integrações da plataforma pela tela (Unidades e fontes > Integração Meta), só a TI da LexGroup.

  GET  /sources/integrations/meta        a configuração em uso e de onde vem cada campo (tela, servidor, padrão)
  POST /sources/integrations/meta/test   o ID e a chave do app abrem na Meta? (não grava)
  PUT  /sources/integrations/meta        grava: testa a chave nova antes; a chave vai cifrada para o banco

A chave secreta do app nunca volta em resposta nenhuma: a tela só sabe se ela existe. No PUT, appSecret
ausente (null) mantém a salva, texto vazio apaga e texto troca (depois do teste). Pausar ou retomar a
coleta acorda a coleta na hora.
"""

import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.connection_check import Check, CheckResult
from app.meta_config import (
    KEY,
    AppChecker,
    IntegrationRepo,
    MetaConfig,
    check_app,
    get_integration_repo,
    get_meta_config,
    view,
)
from app.routes.source_connections import (
    Admin,
    RateLimit,
    _db_message,
    _wake_ads,
    get_ads_sync,
    get_rate_limit,
)
from app.secret_box import SecretBox, SecretKeyMissing
from app.source_admin import NotAllowed, RuleBroken

router = APIRouter(prefix="/sources/integrations", tags=["sources"])

APP_ID = r"^\d{5,25}$"
VERSION = r"^v\d{2}\.0$"


class MetaTestIn(BaseModel):
    appId: str = Field(pattern=APP_ID)
    appSecret: str | None = Field(default=None, max_length=128)  # null = a salva
    graphVersion: str = Field(pattern=VERSION)


class MetaIn(BaseModel):
    appId: str | None = Field(default=None, max_length=25)  # null ou "" = sem app
    appSecret: str | None = Field(
        default=None, max_length=128
    )  # null = manter, "" = apagar, texto = trocar
    graphVersion: str = Field(pattern=VERSION)
    syncPaused: bool = False


def get_app_checker() -> AppChecker:
    return check_app


def get_optional_box(settings: Annotated[Settings, Depends(get_settings)]) -> SecretBox | None:
    """A chave que cifra a chave do app (SOURCE_SECRET_KEY); sem ela, None (só gravar chave nova é barrado)."""
    try:
        return SecretBox.from_setting(settings.SOURCE_SECRET_KEY)
    except (SecretKeyMissing, ValueError):
        return None


def _out(result: CheckResult) -> list[dict[str, Any]]:
    return [vars(c) for c in result.checks]


Meta = Annotated[MetaConfig, Depends(get_meta_config)]
Checker = Annotated[AppChecker, Depends(get_app_checker)]


@router.get("/meta")
async def get_meta(
    _: Admin, meta: Meta, settings: Annotated[Settings, Depends(get_settings)]
) -> dict[str, Any]:
    return view(await meta.refresh(force=True), settings)


@router.post("/meta/test")
async def test_meta(
    body: MetaTestIn,
    user: Admin,
    meta: Meta,
    check: Checker,
    rate: Annotated[RateLimit, Depends(get_rate_limit)],
) -> dict[str, Any]:
    """Testa o ID e a chave na Meta. Sem chave no corpo, usa a que está em uso (tela ou .env)."""
    rate.check(user.user_id)
    current = await meta.refresh(force=True)
    secret = (body.appSecret or "").strip() or current.app_secret
    if not secret:
        msg = "Informe a chave secreta do app (Configurações do app > Básico)."
        return {"ok": False, "checks": _out(CheckResult([Check("login", False, msg)])), "app": None}
    result, name = await check(body.appId, secret, body.graphVersion)
    return {"ok": result.ok, "checks": _out(result), "app": name}


@router.put("/meta")
async def save_meta(
    body: MetaIn,
    user: Admin,
    meta: Meta,
    check: Checker,
    repo: Annotated[IntegrationRepo, Depends(get_integration_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
    rate: Annotated[RateLimit, Depends(get_rate_limit)],
    ads_sync: Annotated[Any, Depends(get_ads_sync)],
    box: Annotated[SecretBox | None, Depends(get_optional_box)],
) -> dict[str, Any]:
    """Grava a configuração da Meta. Chave nova (ou ID novo com a chave salva) é testada antes; teste que
    falha não grava nada (saved=false, com as checagens)."""
    app_id = (body.appId or "").strip()
    if app_id and not re.fullmatch(APP_ID, app_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="O ID do app tem só números."
        )
    before = await meta.refresh(force=True)
    new_secret = (body.appSecret or "").strip()
    if body.appSecret is None:
        action = "keep"
    elif new_secret:
        action = "set"
    else:
        action = "clear"
    if not app_id and action != "clear" and before.origin.get("appSecret") == "tela":
        action = "clear"  # sem app, a chave não serve para nada
    if action == "set" and not app_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Informe o ID do app junto com a chave."
        )

    checks: list[dict[str, Any]] = []
    to_test = new_secret if action == "set" else ""
    if action == "keep" and app_id and app_id != before.app_id and before.app_secret:
        to_test = before.app_secret  # ID novo com a chave que já estava: precisa abrir na Meta
    if to_test:
        rate.check(user.user_id)
        result, _ = await check(app_id, to_test, body.graphVersion)
        checks = _out(result)
        if not result.ok:
            return {"saved": False, "checks": checks, "integration": view(before, settings)}

    ciphertext = None
    if action == "set":
        if box is None:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Guardar a chave do app está desligado: falta SOURCE_SECRET_KEY na API",
            )
        ciphertext = box.encrypt(new_secret)

    config: dict[str, Any] = {"graph_version": body.graphVersion, "sync_paused": body.syncPaused}
    if app_id:
        config["app_id"] = app_id
    try:
        await repo.save(user.user_id, KEY, config, ciphertext, action)
    except NotAllowed as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup configura integrações"
        ) from exc
    except RuleBroken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=_db_message(exc)) from exc

    meta.invalidate()
    after = await meta.refresh(force=True)
    if before.sync_paused != after.sync_paused:
        _wake_ads(ads_sync)
    return {"saved": True, "checks": checks, "integration": view(after, settings)}
