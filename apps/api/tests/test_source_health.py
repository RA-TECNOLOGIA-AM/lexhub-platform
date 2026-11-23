"""Tela Clientes: fontes com falha por organização, pela mesma regra da tela Unidades e fontes.

Conta só a fonte ligada, com algum dashboard ligado que a usa, cuja tentativa de leitura mais recente
falhou (registro de leituras, app/read_log.py). Tempo parado não conta; "Aguardando dashboards" e
"Desligada" ficam de fora (quem decide isso é a consulta do repo, no banco da plataforma).
"""

import asyncio

import pytest

from app.read_log import Read, summarize
from conftest import USER_ID


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def run(coro):
    return asyncio.run(coro)


class FakeMonitored:
    def __init__(self, admins: set[str], pairs: list[tuple[str, str]]):
        self.admins = admins
        self.pairs = pairs

    async def is_source_admin(self, user_id: str) -> bool:
        return user_id in self.admins

    async def monitored(self) -> list[tuple[str, str]]:
        return self.pairs


@pytest.fixture
def monitored(client):
    from app.source_health import get_monitored_repo

    fake = FakeMonitored(
        {USER_ID},
        [
            ("lexgroup", "sheets_financeiro_ng"),
            ("lexgroup", "sheets_financeiro_la"),
            ("lexgroup", "ng"),
            ("cliente", "gs_mc_1"),
        ],
    )
    client.app.dependency_overrides[get_monitored_repo] = lambda: fake
    return fake


# --- summarize: a regra de uma fonte (a mesma da tela de fontes) ------------------------------------


def test_resumo_da_fonte_falha_so_se_a_tentativa_mais_recente_falhou():
    assert summarize([]) == (None, None, None)
    assert summarize([Read(ok_at=100.0), Read(ok_at=300.0)]) == (300.0, None, None)
    # Falha numa query, mas outra leu bem depois: a fonte respondeu por último.
    assert summarize([Read(ok_at=300.0), Read(ok_at=None, fail_at=200.0, error="X")]) == (
        300.0,
        None,
        None,
    )
    assert summarize(
        [Read(ok_at=100.0), Read(ok_at=None, fail_at=200.0, error="TimeoutError")]
    ) == (
        100.0,
        200.0,
        "TimeoutError",
    )


# --- GET /sources/failing ---------------------------------------------------------------------------


def test_sem_login_401(client):
    assert client.get("/sources/failing").status_code == 401


def test_so_a_ti_da_lexgroup_ve(client, signer, monitored):
    monitored.admins.clear()
    assert client.get("/sources/failing", headers=auth(signer)).status_code == 403


def test_tempo_parado_nao_e_falha_so_a_ultima_tentativa_falha(client, signer, monitored):
    reads = client.app.state.source_cache.reads
    run(reads.ok("sheets_financeiro_ng:aba", 1_000.0))  # lida há muito tempo: saudável
    run(reads.ok("sheets_financeiro_la:aba", 1_000.0))
    run(reads.failed("sheets_financeiro_la:aba", 2_000.0, "TimeoutError"))  # falhou por último
    run(reads.failed("gs_mc_1:aba", 2_000.0, "InvalidSheetLink"))
    run(reads.failed("gs_fora:aba", 2_000.0, "X"))  # fora da lista (desligada ou sem dashboard)

    r = client.get("/sources/failing", headers=auth(signer))

    assert r.status_code == 200
    assert r.json() == {"orgs": {"lexgroup": ["sheets_financeiro_la"], "cliente": ["gs_mc_1"]}}


def test_organizacao_sem_falha_vem_com_lista_vazia(client, signer, monitored):
    r = client.get("/sources/failing", headers=auth(signer)).json()

    assert r == {"orgs": {"lexgroup": [], "cliente": []}}
