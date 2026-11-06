"""SQL real da API contra um Postgres com as migrations (stub do Supabase + supabase/migrations).

Roda só com TEST_DATABASE_URL definida (CI ou cluster local). Usa os dados de teste do
supabase/tests/app_core_smoke.sql dentro de uma transação e desfaz tudo no final.
"""

import asyncio
import os
import re
from pathlib import Path

import pytest

from app.access import AuditEntry, PgAccessRepo

DSN = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL não definida")

SMOKE = Path(__file__).resolve().parents[3] / "supabase" / "tests" / "app_core_smoke.sql"

ADMIN_A = "00000000-0000-0000-0000-0000000000a1"
GESTOR_NG = "00000000-0000-0000-0000-0000000000a2"
PROTOCOLO_NG = "00000000-0000-0000-0000-0000000000a3"
SEM_ACESSO = "00000000-0000-0000-0000-0000000000a4"
INATIVO = "00000000-0000-0000-0000-0000000000a5"
LEITOR_NG = "00000000-0000-0000-0000-0000000000a6"
ADMIN_B = "00000000-0000-0000-0000-0000000000b1"
ORG_A = "10000000-0000-0000-0000-00000000000a"


def _fixtures_sql() -> str:
    text = SMOKE.read_text(encoding="utf-8")
    m = re.search(r"-- -+ dados de teste -+\n(.*?)\n-- -+ integridade", text, re.DOTALL)
    assert m, "bloco de dados de teste não encontrado no smoke"
    return m.group(1)


def _run(coro):
    return asyncio.run(coro)


async def _with_fixtures(check):
    import asyncpg

    conn = await asyncpg.connect(DSN, statement_cache_size=0)
    tx = conn.transaction()
    await tx.start()
    try:
        await conn.execute(_fixtures_sql())
        await check(PgAccessRepo(conn), conn)
    finally:
        await tx.rollback()
        await conn.close()


@pytest.mark.parametrize(
    ("user", "org", "unit", "key", "expected"),
    [
        (ADMIN_A, "org-a", "LA", "protocolo-lexpre", "all"),
        (GESTOR_NG, "org-a", "NG", "pendencias", "all"),
        (PROTOCOLO_NG, "org-a", "NG", "protocolo-lexpre", "all"),
        (LEITOR_NG, "org-a", "NG", "pendencias", "own"),
        (GESTOR_NG, "org-a", "LA", "protocolo-lexpre", None),
        (PROTOCOLO_NG, "org-a", "NG", "pendencias", None),
        (SEM_ACESSO, "org-a", "NG", "protocolo-lexpre", None),
        (INATIVO, "org-a", "NG", "protocolo-lexpre", None),
        (ADMIN_A, "org-b", "XX", "protocolo-lexpre", None),
        (ADMIN_B, "org-a", "NG", "protocolo-lexpre", None),
    ],
)
def test_resolve_access_usa_a_regra_do_banco(user, org, unit, key, expected):
    async def check(repo, _conn):
        r = await repo.resolve_access(user, org, unit, key)
        assert r is not None
        assert r.scope == expected

    _run(_with_fixtures(check))


def test_org_ou_unidade_inexistente_retorna_none():
    async def check(repo, _conn):
        assert await repo.resolve_access(ADMIN_A, "nao-existe", "NG", "protocolo-lexpre") is None
        assert await repo.resolve_access(ADMIN_A, "org-a", "ZZ", "protocolo-lexpre") is None

    _run(_with_fixtures(check))


def test_unidade_inativa_retorna_none():
    async def check(repo, conn):
        await conn.execute("update app.units set active = false where code = 'NG'")
        assert await repo.resolve_access(ADMIN_A, "org-a", "NG", "protocolo-lexpre") is None

    _run(_with_fixtures(check))


def test_insert_audit_grava_a_linha():
    async def check(repo, conn):
        await repo.insert_audit(
            AuditEntry(
                action="dashboard.access_denied",
                actor_user_id=SEM_ACESSO,
                org_id=ORG_A,
                target_type="dashboard",
                target_id="protocolo-lexpre",
                metadata={"org": "org-a", "unit": "NG"},
                ip="127.0.0.1",
                user_agent="pytest",
            )
        )
        row = await conn.fetchrow(
            "select org_id::text, actor_user_id::text, action, target_id, metadata::text,"
            " host(ip) as ip, user_agent from app.audit_log order by id desc limit 1"
        )
        assert dict(row) == {
            "org_id": ORG_A,
            "actor_user_id": SEM_ACESSO,
            "action": "dashboard.access_denied",
            "target_id": "protocolo-lexpre",
            "metadata": '{"org": "org-a", "unit": "NG"}',
            "ip": "127.0.0.1",
            "user_agent": "pytest",
        }

    _run(_with_fixtures(check))


def test_insert_audit_sem_org_e_sem_ip():
    async def check(repo, conn):
        await repo.insert_audit(AuditEntry(action="dashboard.access_denied", actor_user_id=None))
        n = await conn.fetchval("select count(*) from app.audit_log where org_id is null")
        assert n == 1

    _run(_with_fixtures(check))
