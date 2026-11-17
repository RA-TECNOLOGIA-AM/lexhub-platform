"""Conectar fonte: banco próprio da operação (Postgres, MySQL) e planilha publicada do Google.

Só a TI da LexGroup (app_private.is_source_admin), em qualquer organização: as rotas não pedem que a
pessoa seja membro da organização (o banco confere quem é TI). O segredo (senha ou link) chega aqui,
é testado, cifrado (app/secret_box.py) e só o cifrado vai para o banco; nenhuma resposta o devolve.

Resultado de teste nunca é erro HTTP: `saved`/`ok` + as checagens. Erro HTTP é só o que impede tentar
(403 quem não é TI, 404 unidade/fonte, 409 regra do banco, 422 campos, 429 testes demais, 503 sem chave).
"""

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.connection_check import Check, CheckResult, DbTarget, check_database
from app.database import SourceUnavailable
from app.secret_box import SecretBox, SecretKeyMissing, SecretUnreadable
from app.sheets import InvalidSheetLink, sheet_tabs
from app.source_admin import (
    ManagedSource,
    NotAllowed,
    RuleBroken,
    SourceAdminRepo,
    get_source_admin_repo,
)
from app.sources import get_registered_sources

DEFAULT_PORT = {"postgres": 5432, "mysql": 3306}
LABEL = {"postgres": "Postgres", "mysql": "MySQL"}
KeyPath = Annotated[str, Path(pattern=r"^[a-z][a-z0-9_]{1,31}$")]

platform = APIRouter(prefix="/sources", tags=["sources"])
org = APIRouter(prefix="/orgs/{org_slug}", tags=["sources"])


# --- Entrada e saída --------------------------------------------------------------------------------


class DatabaseIn(BaseModel):
    connector: Literal["postgres", "mysql"]
    name: str = Field(min_length=1, max_length=80)
    host: str = Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9.\-:\[\]]+$")
    port: int | None = Field(default=None, ge=1, le=65535)
    database: str = Field(min_length=1, max_length=128)
    user: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=512)
    ssl: bool = True
    writerAck: bool = False

    def target(self) -> DbTarget:
        return DbTarget(
            connector=self.connector,
            host=self.host.strip(),
            port=self.port or DEFAULT_PORT[self.connector],
            database=self.database.strip(),
            user=self.user.strip(),
            password=self.password,
            ssl=self.ssl,
        )


class SheetIn(BaseModel):
    connector: Literal["sheets"]
    name: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=10, max_length=2000)
    tab: str = Field(min_length=1, max_length=120)


ConnectIn = Annotated[DatabaseIn | SheetIn, Field(discriminator="connector")]


class SecretIn(BaseModel):
    password: str | None = Field(default=None, min_length=1, max_length=512)  # banco
    url: str | None = Field(default=None, min_length=10, max_length=2000)  # planilha
    writerAck: bool = False


class InspectIn(BaseModel):
    url: str = Field(min_length=10, max_length=2000)


class CheckOut(BaseModel):
    key: str
    ok: bool
    message: str
    ms: int
    severity: str
    skipped: bool


class ConnectOut(BaseModel):
    saved: bool
    needsWriterAck: bool = False
    checks: list[CheckOut]
    source: dict[str, Any] | None = None


class TestOut(BaseModel):
    ok: bool
    checks: list[CheckOut]


class TabOut(BaseModel):
    name: str
    rows: int


class InspectOut(BaseModel):
    tabs: list[TabOut]


class ConnectInfoOut(BaseModel):
    ready: bool  # a API tem a chave para cifrar (sem ela, só LexPre/LexFlow)
    egressIp: str | None  # o IP que a operação libera no firewall do banco


def _checks(result: CheckResult) -> list[CheckOut]:
    return [CheckOut(**vars(c)) for c in result.checks]


# --- Peças trocáveis (os testes passam falsas) ----------------------------------------------------

DbChecker = Callable[[DbTarget], Awaitable[CheckResult]]
SheetReader = Callable[[str], Awaitable[dict[str, int]]]


def get_db_checker(settings: Annotated[Settings, Depends(get_settings)]) -> DbChecker:
    return lambda target: check_database(
        target,
        timeout=settings.SOURCE_TEST_TIMEOUT,
        allow_private=settings.SOURCE_ALLOW_PRIVATE_HOSTS,
    )


def get_sheet_reader() -> SheetReader:
    return sheet_tabs


def get_secret_box(settings: Annotated[Settings, Depends(get_settings)]) -> SecretBox:
    try:
        return SecretBox.from_setting(settings.SOURCE_SECRET_KEY)
    except (SecretKeyMissing, ValueError) as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Conectar banco e planilha está desligado: falta SOURCE_SECRET_KEY na API",
        ) from exc


class RateLimit:
    """Até `limit` testes por `window` segundos por pessoa (nesta réplica)."""

    def __init__(
        self, limit: int = 10, window: float = 60, clock: Callable[[], float] = time.monotonic
    ):
        self._limit, self._window, self._clock = limit, window, clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, user_id: str) -> None:
        now = self._clock()
        hits = self._hits[user_id]
        while hits and now - hits[0] > self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitos testes seguidos. Espere um minuto.",
            )
        hits.append(now)


_rate = RateLimit()


def get_rate_limit() -> RateLimit:
    return _rate


async def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[SourceAdminRepo, Depends(get_source_admin_repo)],
) -> CurrentUser:
    if not await repo.is_source_admin(user.user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup conecta fontes")
    return user


Admin = Annotated[CurrentUser, Depends(require_admin)]
Repo = Annotated[SourceAdminRepo, Depends(get_source_admin_repo)]


# --- Planilha: as checagens no mesmo formato do banco ----------------------------------------------


async def check_sheet(
    read: SheetReader, link: str, tab: str | None
) -> tuple[CheckResult, dict[str, int]]:
    started = time.perf_counter()

    def ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        tabs = await read(link)
    except InvalidSheetLink:
        msg = 'Link inválido. Use o link de "Publicar na Web" (ou de compartilhamento) da planilha.'
        return CheckResult([Check("network", False, msg, ms())]), {}
    except SourceUnavailable:
        msg = (
            "A planilha não baixou. Confira se ela está publicada na Web (Arquivo > Compartilhar > "
            "Publicar na Web) ou aberta a quem tiver o link."
        )
        return CheckResult([Check("network", False, msg, ms())]), {}
    checks = [Check("network", True, f"Planilha baixada: {len(tabs)} abas", ms())]
    if tab is not None:
        if tab not in tabs:
            checks.append(Check("read", False, f"A aba {tab} não existe nessa planilha.", ms()))
        else:
            checks.append(Check("read", True, f"Aba {tab}: {tabs[tab]} linhas", ms()))
    return CheckResult(checks, ms=ms()), tabs


# --- Rotas da plataforma ------------------------------------------------------------------------------


@platform.get("/connect-info", response_model=ConnectInfoOut)
async def connect_info(
    _: Admin, settings: Annotated[Settings, Depends(get_settings)]
) -> ConnectInfoOut:
    """O que a tela Conectar fonte precisa saber da API: se cifra está ligada e o IP de saída."""
    return ConnectInfoOut(
        ready=bool(settings.SOURCE_SECRET_KEY.strip()), egressIp=settings.SOURCE_EGRESS_IP or None
    )


@platform.post("/sheets/inspect", response_model=InspectOut)
async def inspect_sheet(
    body: InspectIn,
    user: Admin,
    read: Annotated[SheetReader, Depends(get_sheet_reader)],
    rate: Annotated[RateLimit, Depends(get_rate_limit)],
) -> InspectOut:
    """Link colado -> as abas da planilha (para o dropdown). Não grava nada."""
    rate.check(user.user_id)
    result, tabs = await check_sheet(read, body.url, None)
    if not result.ok:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=result.error)
    return InspectOut(tabs=[TabOut(name=n, rows=r) for n, r in tabs.items()])


# --- Rotas da organização ---------------------------------------------------------------------------


@org.post("/units/{unit_code}/sources", response_model=ConnectOut)
async def connect_source(
    org_slug: str,
    unit_code: str,
    body: ConnectIn,
    user: Admin,
    repo: Repo,
    box: Annotated[SecretBox, Depends(get_secret_box)],
    check_db: Annotated[DbChecker, Depends(get_db_checker)],
    read_sheet: Annotated[SheetReader, Depends(get_sheet_reader)],
    rate: Annotated[RateLimit, Depends(get_rate_limit)],
) -> ConnectOut:
    """Testar e salvar. Teste falhou = nada gravado (saved=false). Usuário que escreve sem writerAck =
    needsWriterAck (a tela mostra "Salvar mesmo assim")."""
    unit_id = await repo.unit_id(org_slug, unit_code)
    if unit_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada")
    rate.check(user.user_id)

    if isinstance(body, SheetIn):
        result, _ = await check_sheet(read_sheet, body.url, body.tab)
        if not result.ok:
            return ConnectOut(saved=False, checks=_checks(result))
        secret, config, writer_ack = body.url.strip(), {"tab": body.tab}, False
        detail, schema = f"Google Planilhas · aba {body.tab}", None
    else:
        target = body.target()
        result = await check_db(target)
        if not result.ok:
            return ConnectOut(saved=False, checks=_checks(result))
        if result.can_write and not body.writerAck:
            return ConnectOut(saved=False, needsWriterAck=True, checks=_checks(result))
        secret, config, writer_ack = target.password, target.config(), result.can_write
        detail = f"{LABEL[target.connector]} · {target.host}/{target.database}"
        schema = result.schema_cache

    try:
        source = await repo.connect(
            user.user_id,
            unit_id,
            body.connector,
            body.name.strip(),
            detail,
            config,
            box.encrypt(secret),
            writer_ack,
            schema,
        )
    except NotAllowed as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup conecta fontes"
        ) from exc
    except RuleBroken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=_db_message(exc)) from exc
    managed = await repo.source(org_slug, source["id"])
    if managed is not None:
        await repo.record_run(
            managed.id, "test", True, [vars(c) for c in result.checks], result.ms, None
        )
    return ConnectOut(saved=True, checks=_checks(result), source=source)


async def _managed(repo: SourceAdminRepo, org_slug: str, key: str) -> ManagedSource:
    source = await repo.source(org_slug, key)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Fonte não encontrada")
    if source.secret_ciphertext is None or source.connector not in ("postgres", "mysql", "sheets"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Esta fonte não é gerenciada pela tela (produto Lex, banco interno ou planilha antiga).",
        )
    return source


def _db_target(source: ManagedSource, password: str) -> DbTarget:
    c = source.config
    return DbTarget(
        connector=source.connector,  # type: ignore[arg-type]
        host=c["host"],
        port=int(c["port"]),
        database=c["database"],
        user=c["user"],
        password=password,
        ssl=bool(c.get("ssl")),
    )


async def _run_check(
    source: ManagedSource,
    secret: str,
    check_db: DbChecker,
    read_sheet: SheetReader,
) -> CheckResult:
    if source.connector == "sheets":
        result, _ = await check_sheet(read_sheet, secret, source.config.get("tab"))
        return result
    return await check_db(_db_target(source, secret))


@org.post("/sources/{key}/test", response_model=TestOut)
async def retest_source(
    org_slug: str,
    key: KeyPath,
    user: Admin,
    repo: Repo,
    box: Annotated[SecretBox, Depends(get_secret_box)],
    check_db: Annotated[DbChecker, Depends(get_db_checker)],
    read_sheet: Annotated[SheetReader, Depends(get_sheet_reader)],
    rate: Annotated[RateLimit, Depends(get_rate_limit)],
) -> TestOut:
    """Testar de novo com o segredo salvo. O resultado vai para o log da fonte."""
    source = await _managed(repo, org_slug, key)
    rate.check(user.user_id)
    try:
        secret = box.decrypt(source.secret_ciphertext or "")
    except SecretUnreadable:
        result = CheckResult(
            [
                Check(
                    "login",
                    False,
                    "O segredo salvo não abre com a chave atual da API. Troque a senha.",
                )
            ]
        )
    else:
        result = await _run_check(source, secret, check_db, read_sheet)
    await repo.record_run(
        source.id, "test", result.ok, [vars(c) for c in result.checks], result.ms, result.error
    )
    return TestOut(ok=result.ok, checks=_checks(result))


@org.put("/sources/{key}/secret", response_model=ConnectOut)
async def change_secret(
    org_slug: str,
    key: KeyPath,
    body: SecretIn,
    user: Admin,
    repo: Repo,
    box: Annotated[SecretBox, Depends(get_secret_box)],
    check_db: Annotated[DbChecker, Depends(get_db_checker)],
    read_sheet: Annotated[SheetReader, Depends(get_sheet_reader)],
    rate: Annotated[RateLimit, Depends(get_rate_limit)],
    registered: Annotated[Any, Depends(get_registered_sources)],
) -> ConnectOut:
    """Trocar a senha (banco) ou o link (planilha): testa com o novo e só então substitui."""
    source = await _managed(repo, org_slug, key)
    secret = body.url if source.connector == "sheets" else body.password
    if not secret:
        field = "url" if source.connector == "sheets" else "password"
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"Informe o campo {field}"
        )
    rate.check(user.user_id)
    result = await _run_check(
        source, secret.strip() if source.connector == "sheets" else secret, check_db, read_sheet
    )
    if not result.ok:
        return ConnectOut(saved=False, checks=_checks(result))
    if result.can_write and not body.writerAck:
        return ConnectOut(saved=False, needsWriterAck=True, checks=_checks(result))
    try:
        item = await repo.set_secret(
            user.user_id, source.id, box.encrypt(secret), result.can_write, result.schema_cache
        )
    except NotAllowed as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup gerencia fontes"
        ) from exc
    except RuleBroken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=_db_message(exc)) from exc
    await repo.record_run(
        source.id, "test", True, [vars(c) for c in result.checks], result.ms, None
    )
    if registered is not None:
        await registered.invalidate(source.key)
    return ConnectOut(saved=True, checks=_checks(result), source=item)


@org.delete("/sources/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_source(
    org_slug: str,
    key: KeyPath,
    user: Admin,
    repo: Repo,
    registered: Annotated[Any, Depends(get_registered_sources)],
) -> Response:
    """Desconectar: some a fonte, as ligações, o log e o segredo. A key não volta a ser usada."""
    source = await _managed(repo, org_slug, key)
    try:
        await repo.disconnect(user.user_id, source.id)
    except NotAllowed as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup gerencia fontes"
        ) from exc
    except RuleBroken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=_db_message(exc)) from exc
    if registered is not None:
        await registered.invalidate(source.key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _db_message(exc: Exception) -> str:
    """Mensagem de RAISE do banco (P0001), sem o resto do texto do driver."""
    return str(exc).split("\n", 1)[0] or "Não foi possível gravar a fonte."
