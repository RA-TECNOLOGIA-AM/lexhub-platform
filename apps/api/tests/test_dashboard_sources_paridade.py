"""Paridade: toda fonte que um dashboard da API lê está em app.dashboard_sources.

A tela Unidades e fontes decide "Aguardando dashboards" por essa tabela; a API decide o que lê pelos
módulos (app/dashboards). Duas listas da mesma coisa: este teste não deixa a tabela ficar para trás.
Dashboard novo que lê uma fonte sem o vínculo = falha aqui, com o insert que falta na mensagem.

Roda só com TEST_DATABASE_URL (CI: Postgres com todas as migrations), como tests/test_pg_repo.py.
"""

import asyncio
import os

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardModule

DSN = os.environ.get("TEST_DATABASE_URL", "")
needs_db = pytest.mark.skipif(not DSN, reason="TEST_DATABASE_URL não definida")


def sources_read_by(module: DashboardModule) -> set[str]:
    """Os bancos/planilhas que o módulo pode ler: o seu, os alternativos e os extras."""
    return {module.source_db, *module.alt_sources, *module.extra_queries}


def expected_pairs() -> set[tuple[str, str]]:
    return {(key, src) for key, m in DASHBOARDS.items() for src in sources_read_by(m)}


async def _db_state() -> tuple[set[str], set[tuple[str, str]]]:
    import asyncpg

    conn = await asyncpg.connect(DSN)
    try:
        catalog = {r["key"] for r in await conn.fetch("select key from app.dashboard_catalog")}
        pairs = {
            (r["dashboard_key"], r["source_key"])
            for r in await conn.fetch("select dashboard_key, source_key from app.dashboard_sources")
        }
    finally:
        await conn.close()
    return catalog, pairs


def test_sources_read_by_inclui_alternativos_e_extras():
    module = DASHBOARDS["comercial-lexpre"]
    assert sources_read_by(module) >= {"lexpre", "ng"}


@needs_db
def test_toda_fonte_lida_pela_api_esta_vinculada_ao_dashboard():
    catalog, pairs = asyncio.run(_db_state())
    # Só os dashboards que existem no catálogo (a FK de dashboard_sources exige).
    missing = sorted(p for p in expected_pairs() if p[0] in catalog and p not in pairs)
    values = ",\n".join(f"    ('{d}', '{s}')" for d, s in missing)
    assert not missing, (
        "Dashboards que leem fontes sem vínculo em app.dashboard_sources (a tela de fontes mostraria "
        "'Aguardando dashboards'). Crie uma migration com:\n"
        f"insert into app.dashboard_sources (dashboard_key, source_key) values\n{values}\n"
        "on conflict do nothing;"
    )
