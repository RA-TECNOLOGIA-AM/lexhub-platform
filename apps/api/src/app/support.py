"""Modo suporte "ver como": começar e encerrar a sessão em que Owner/Dev navega como um membro.

Dividido em partes trocáveis:
  * SupportRepo   lê e grava app.support_sessions (PgSupportRepo em produção, um falso nos testes);
  * modelos       o que a rota recebe e devolve;
  * ViewedLog     lembra, na memória do processo, o que já foi auditado como support.viewed.
Quem pode (org.dashboards.all) e se o membro serve (mesma organização, ativo, outra pessoa) é
decidido na rota; o banco só garante uma sessão aberta por pessoa e o vencimento de 1 hora.
Durante a sessão, quem troca o usuário pelo membro é app/access.py; o "só leitura" é
app/support_guard.py.
"""

import json
from collections.abc import Hashable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated, Protocol
from uuid import UUID

import asyncpg
from fastapi import Depends, Request
from pydantic import BaseModel, Field, field_validator

from app.me import SEE_ALL_ORG, MembershipRow, UnitOut, _unit, role_label
from app.platform_db import get_db_pool

REASON_MIN = 5
REASON_MAX = 500
VIEWED_WINDOW = timedelta(minutes=5)  # um support.viewed por sessão + unidade + dashboard
VIEWED_MAX_ENTRIES = 10_000


# --- O que o banco devolve -------------------------------------------------


@dataclass(frozen=True)
class HiddenRow:
    """Um dashboard que o membro não vê na unidade, e por quê (no_unit_role, no_sector_rule, ...)."""

    key: str
    title: str
    area: str
    reason: str


@dataclass(frozen=True)
class SupportSession:
    id: str
    org_id: str
    actor_user_id: str
    target_user_id: str
    target_membership_id: str
    expires_at: datetime
    ended_at: datetime | None
    end_reason: str | None = None  # 'exit' | 'expired' quando ended_at existe
    # Só em start(): a sessão aberta que o start encerrou ('exit') para abrir esta; senão None.
    replaced: "SupportSession | None" = None


class SupportRepo(Protocol):
    # O cargo de quem pede, nesta organização, tem org.dashboards.all (Owner/Dev).
    async def can_support(self, user_id: str, org_id: str) -> bool: ...

    # Membro ATIVO desta organização: {membership_id, user_id, name, avatar_path, role_label,
    # units:[{code,name}]}; None se não for desta organização ou estiver inativo.
    async def member(self, org_id: str, membership_id: str) -> dict | None: ...

    # Encerra a aberta anterior de quem pede (vai em .replaced, com o end_reason aplicado: 'exit', ou
    # 'expired' se já tinha vencido e o cron ainda não passou) e cria a nova. O vencimento
    # (1 hora) vem do banco, nunca do cliente. `reason` já chega sem espaços nas pontas.
    async def start(self, org_id: str, actor: str, member: dict, reason: str) -> SupportSession: ...

    async def get(self, session_id: str) -> SupportSession | None: ...

    # O end_reason aplicado ('expired' se já tinha vencido, senão o pedido) ou None se já estava
    # encerrada (não sobrescreve o motivo de quem encerrou antes).
    async def end(self, session_id: str, end_reason: str) -> str | None: ...

    # Dashboards da unidade (ativos no catálogo, ligados ou não) que o membro NÃO vê, com o motivo
    # de app_private.dashboard_access_explain (a mesma regra do acesso de verdade). Ordem do catálogo.
    async def hidden(self, org_id: str, unit_code: str, member_user_id: str) -> list[HiddenRow]: ...


# --- Entrada e resposta ----------------------------------------------------


class SupportStartIn(BaseModel):
    membership_id: UUID
    reason: str = Field(min_length=REASON_MIN, max_length=REASON_MAX)

    @field_validator("reason", mode="before")
    @classmethod
    def _strip(cls, v: object) -> object:
        return v.strip() if isinstance(v, str) else v


class SupportMemberOut(BaseModel):
    membership_id: str
    name: str
    avatar_path: str | None
    role_label: str
    units: list[UnitOut]


class SupportSessionOut(BaseModel):
    session_id: str
    expires_at: datetime
    member: SupportMemberOut


# --- Banco -----------------------------------------------------------------

# Mesma regra do 'support' do menu (migration 20261126100000), mas por id de usuário: a API não
# tem auth.uid(). app_private.has_permission (migration 20261105170000) também exige a
# organização ativa.
_CAN_SUPPORT_SQL = "select app_private.has_permission($1::uuid, $2::uuid, $3)"

# Mesmos dados do /me (app/me.py), de um membro só: papel, permissões e unidades ativas em que
# tem cargo (ou todas, se o papel da organização vê tudo).
_MEMBER_SQL = """
select m.id::text as membership_id,
       m.user_id::text as user_id,
       m.full_name,
       r.name as role_name,
       array(select rp.permission from app.role_permissions rp
              where rp.role_key = m.role_key) as permissions,
       coalesce((
           select json_agg(json_build_object(
                      'code', u.code,
                      'name', u.name,
                      'role_name', ur.name,
                      'permissions', array(select rp.permission from app.role_permissions rp
                                            where rp.role_key = mu.role_key))
                  order by u.name)
             from app.units u
             left join app.membership_units mu on mu.unit_id = u.id and mu.membership_id = m.id
             left join app.roles ur            on ur.key = mu.role_key
            where u.org_id = m.org_id and u.active
              and (mu.membership_id is not null
                   or exists (select 1 from app.role_permissions rp
                               where rp.role_key = m.role_key and rp.permission = $3))
       ), '[]') as units,
       p.avatar_path
  from app.memberships m
  join app.roles r         on r.key = m.role_key
  left join app.profiles p on p.user_id = m.user_id
 where m.id = $2::uuid and m.org_id = $1::uuid and m.status = 'active'
"""

_COLUMNS = (
    "id::text, org_id::text, actor_user_id::text, target_user_id::text,"
    " target_membership_id::text, expires_at, ended_at, end_reason"
)

# Fecha a aberta de quem pede; devolve a que fechou (para a auditoria do support.ended).
_CLOSE_OPEN_SQL = f"""
update app.support_sessions
   set ended_at = least(now(), expires_at),
       end_reason = case when expires_at <= now() then 'expired' else 'exit' end
 where actor_user_id = $1::uuid and ended_at is null
returning {_COLUMNS}
"""

# expires_at fica de fora de propósito: o padrão do banco (agora + 1 hora) é quem decide.
_INSERT_SQL = f"""
insert into app.support_sessions
    (org_id, actor_user_id, target_user_id, target_membership_id, reason)
values ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5)
returning {_COLUMNS}
"""

_GET_SQL = f"select {_COLUMNS} from app.support_sessions where id = $1::uuid"

_END_SQL = """
update app.support_sessions
   set ended_at = least(now(), expires_at),
       end_reason = case when expires_at <= now() then 'expired' else $2::text end
 where id = $1::uuid and ended_at is null
returning end_reason
"""


def _session(row: asyncpg.Record, replaced: SupportSession | None = None) -> SupportSession:
    return SupportSession(
        id=row["id"],
        org_id=row["org_id"],
        actor_user_id=row["actor_user_id"],
        target_user_id=row["target_user_id"],
        target_membership_id=row["target_membership_id"],
        expires_at=row["expires_at"],
        ended_at=row["ended_at"],
        end_reason=row["end_reason"],
        replaced=replaced,
    )


_HIDDEN_SQL = """
select d.key, d.name as title, d.area, e.reason
  from app.units u
  join app.org_dashboards od   on od.org_id = u.org_id and od.unit_id = u.id
  join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
  cross join lateral app_private.dashboard_access_explain($3::uuid, u.id, d.key) e
 where u.org_id = $1::uuid and u.code = $2 and u.active and e.scope is null
 order by d.area, d.name
"""


class PgSupportRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def can_support(self, user_id, org_id):
        return bool(await self._pool.fetchval(_CAN_SUPPORT_SQL, user_id, org_id, SEE_ALL_ORG))

    async def member(self, org_id, membership_id):
        row = await self._pool.fetchrow(_MEMBER_SQL, org_id, membership_id, SEE_ALL_ORG)
        if row is None:
            return None
        m = MembershipRow(
            full_name=row["full_name"],
            role_name=row["role_name"],
            permissions=frozenset(row["permissions"]),
            units=tuple(_unit(u) for u in json.loads(row["units"])),
        )
        return {
            "membership_id": row["membership_id"],
            "user_id": row["user_id"],
            "name": row["full_name"],
            "avatar_path": row["avatar_path"],
            "role_label": role_label(m),
            "units": [{"code": u.code, "name": u.name} for u in m.units],
        }

    async def start(self, org_id, actor, member, reason):
        async with self._pool.acquire() as conn, conn.transaction():
            # Dois "iniciar" juntos da mesma pessoa esbarrariam no índice único: serializa por ela.
            await conn.execute("select pg_advisory_xact_lock(hashtext($1))", f"support:{actor}")
            closed = await conn.fetchrow(_CLOSE_OPEN_SQL, actor)
            row = await conn.fetchrow(
                _INSERT_SQL, org_id, actor, member["user_id"], member["membership_id"], reason
            )
        return _session(row, _session(closed) if closed else None)

    async def get(self, session_id):
        row = await self._pool.fetchrow(_GET_SQL, session_id)
        return _session(row) if row else None

    async def end(self, session_id, end_reason):
        return await self._pool.fetchval(_END_SQL, session_id, end_reason)

    async def hidden(self, org_id, unit_code, member_user_id):
        rows = await self._pool.fetch(_HIDDEN_SQL, org_id, unit_code, member_user_id)
        return [HiddenRow(r["key"], r["title"], r["area"], r["reason"]) for r in rows]


def get_support_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> SupportRepo:
    return PgSupportRepo(pool)


# --- Dedup do support.viewed -------------------------------------------------


class ViewedLog:
    """Chave -> quando foi auditada. Na memória do processo (a API roda com um worker), como o
    result_memo: reiniciar a API só faz auditar de novo, nunca deixa de auditar.

    As entradas entram em ordem de hora; as vencidas saem pela frente a cada chamada, e passar de
    `max_entries` descarta as mais antigas. Não cresce para sempre.
    """

    def __init__(self, window: timedelta = VIEWED_WINDOW, max_entries: int = VIEWED_MAX_ENTRIES):
        self._window = window
        self._max = max_entries
        self._seen: dict[Hashable, datetime] = {}

    def __len__(self) -> int:
        return len(self._seen)

    def first_in_window(self, key: Hashable, now: datetime) -> bool:
        """True (e marca) se a chave não foi auditada nos últimos `window`; senão False."""
        self._prune(now)
        at = self._seen.get(key)
        if at is not None and now - at < self._window:
            return False
        self._seen.pop(key, None)  # volta para o fim: a ordem segue a hora
        self._seen[key] = now
        while len(self._seen) > self._max:
            del self._seen[next(iter(self._seen))]
        return True

    def _prune(self, now: datetime) -> None:
        while self._seen:
            key, at = next(iter(self._seen.items()))
            if now - at < self._window:
                return
            del self._seen[key]


def get_viewed_log(request: Request) -> ViewedLog:
    """Dependency: o ViewedLog da app (criado em create_app; um por processo)."""
    return request.app.state.support_viewed
