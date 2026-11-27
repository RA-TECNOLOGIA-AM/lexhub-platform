from datetime import UTC, date, datetime

import pytest

from app.clock import get_now
from app.config import get_settings
from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardModule, ExportSpec
from app.public_api.rate_limit import RateLimiter
from app.public_api.service import KeyCache, issue_pair
from app.public_api.store import KeyAccess, Reachable, get_api_key_repo
from app.routes.public_auth import get_key_cache
from app.routes.public_data import get_rate_limiter
from public_api_fakes import FakeApiKeyRepo

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
URL = "/v1/orgs/lexgroup/units/NG/dashboards/protocolo-lexpre"
PERIOD = {"from": "2026-11-01", "to": "2026-11-26"}
FIELDS = {"id_demanda": "ID_DEMANDA", "materia": "MATERIA", "data_entrada": "DATA_ENTRADA"}
LABELS = {"id_demanda": "ID da Demanda", "materia": "Matéria", "data_entrada": "Data de Entrada"}
ROWS = [
    {"ID_DEMANDA": i, "MATERIA": "ANP" if i % 2 else "MORA", "DATA_ENTRADA": date(2026, 11, 3)}
    for i in range(1, 6)
]


@pytest.fixture
def module(monkeypatch):
    async def rows(ctx):
        return ROWS

    async def build(ctx):
        return {}

    fake = DashboardModule(
        key="protocolo-lexpre",
        source_db="lexpre",
        source_label="LexPre",
        build=build,
        export=ExportSpec(fields=FIELDS, labels=LABELS, sheet_name="Protocolo", rows=rows),
    )
    monkeypatch.setitem(DASHBOARDS, "protocolo-lexpre", fake)
    sem_export = DashboardModule(
        key="sem-export", source_db="lexpre", source_label="LexPre", build=build
    )
    monkeypatch.setitem(DASHBOARDS, "sem-export", sem_export)
    return fake


@pytest.fixture
def keys() -> FakeApiKeyRepo:
    k = FakeApiKeyRepo()
    k.add_key(user_id="gestor-1")
    access = KeyAccess(
        org_id="o1",
        unit_id="u-ng",
        scope="all",
        can_see_commission=True,
        source_refs={"lexpre": "1"},
    )
    k.access[("k1", "lexgroup", "NG", "protocolo-lexpre")] = access
    k.access[("k1", "lexgroup", "NG", "sem-export")] = access
    k.access[("k1", "lexgroup", "NG", "pendencias")] = KeyAccess(
        org_id="o1", unit_id="u-ng", scope=None
    )
    k.reach["k1"] = [Reachable("lexgroup", "NG", "u-ng", "protocolo-lexpre")]
    return k


@pytest.fixture
def limiter() -> RateLimiter:
    return RateLimiter(limit=60, window_s=60, monotonic=lambda: 0.0)


@pytest.fixture
def token(client, keys, limiter, module):
    settings = get_settings().model_copy(update={"PUBLIC_API_JWT_SECRET": "s" * 32})
    cache = KeyCache()
    ov = client.app.dependency_overrides
    ov[get_api_key_repo] = lambda: keys
    ov[get_settings] = lambda: settings
    ov[get_now] = lambda: NOW
    ov[get_key_cache] = lambda: cache
    ov[get_rate_limiter] = lambda: limiter
    import asyncio

    pair = asyncio.run(issue_pair(keys, keys.keys["k1"], settings, NOW))
    return {"Authorization": f"Bearer {pair.access_token}"}


def test_sem_token_401(client, token):
    assert client.get(URL, params=PERIOD).status_code == 401


def test_dados_pagina_1_e_total(client, token, keys, repo):
    r = client.get(URL, params={**PERIOD, "tamanho_pagina": 2}, headers=token)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["paginacao"] == {"pagina": 1, "tamanho_pagina": 2, "total": 5, "total_paginas": 3}
    assert body["campos"] == ["id_demanda", "materia", "data_entrada"]
    assert body["periodo"] == {"from": "2026-11-01", "to": "2026-11-26"}
    assert body["dados"] == [
        {"id_demanda": 1, "materia": "ANP", "data_entrada": "2026-11-03"},
        {"id_demanda": 2, "materia": "MORA", "data_entrada": "2026-11-03"},
    ]
    assert keys.last_used["k1"] == NOW
    assert keys.last_ip["k1"] == "testclient"  # request.client.host do TestClient


def test_pagina_alem_do_total_vem_vazia(client, token):
    r = client.get(URL, params={**PERIOD, "pagina": 9}, headers=token)
    assert r.status_code == 200
    assert r.json()["dados"] == []
    assert r.json()["paginacao"]["total"] == 5


def test_campos_por_virgula_e_repetidos_sao_iguais(client, token):
    a = client.get(URL, params={**PERIOD, "campos": "materia,id_demanda"}, headers=token).json()
    b = client.get(
        URL,
        params=[*PERIOD.items(), ("campos", "materia"), ("campos", "id_demanda")],
        headers=token,
    ).json()
    assert a["campos"] == b["campos"] == ["materia", "id_demanda"]
    assert a["dados"] == b["dados"]
    assert a["dados"][0] == {"materia": "ANP", "id_demanda": 1}


def test_campo_desconhecido_400(client, token):
    r = client.get(URL, params={**PERIOD, "campos": "xyz"}, headers=token)
    assert r.status_code == 400


def test_sem_scope_403_e_audita(client, token, repo):
    url = "/v1/orgs/lexgroup/units/NG/dashboards/pendencias"
    r = client.get(url, params=PERIOD, headers=token)
    assert r.status_code == 403
    assert repo.audits[-1].action == "api.access_denied"
    assert repo.audits[-1].actor_user_id == "gestor-1"


def test_unidade_desconhecida_403(client, token):
    url = "/v1/orgs/lexgroup/units/XX/dashboards/protocolo-lexpre"
    assert client.get(url, params=PERIOD, headers=token).status_code == 403


def test_dashboard_sem_export_404(client, token):
    url = "/v1/orgs/lexgroup/units/NG/dashboards/sem-export"
    assert client.get(url, params=PERIOD, headers=token).status_code == 404


def test_periodo_maior_que_366_dias_422(client, token):
    r = client.get(URL, params={"from": "2025-01-01", "to": "2026-01-03"}, headers=token)
    assert r.status_code == 422


def test_periodo_invertido_ou_faltando_422(client, token):
    assert (
        client.get(
            URL, params={"from": "2026-11-26", "to": "2026-11-01"}, headers=token
        ).status_code
        == 422
    )
    assert client.get(URL, params={"from": "2026-11-26"}, headers=token).status_code == 422


def test_tamanho_pagina_5001_422(client, token):
    r = client.get(URL, params={**PERIOD, "tamanho_pagina": 5001}, headers=token)
    assert r.status_code == 422


def test_rate_limit_61a_chamada_429(client, token):
    for _ in range(60):
        assert client.get(URL, params=PERIOD, headers=token).status_code == 200
    r = client.get(URL, params=PERIOD, headers=token)
    assert r.status_code == 429


def test_audita_api_read_com_dono_da_chave(client, token, repo):
    client.get(URL, params=PERIOD, headers=token)
    entry = repo.audits[-1]
    assert entry.action == "api.read"
    assert entry.actor_user_id == "gestor-1"
    assert entry.target_id == "protocolo-lexpre"
    assert entry.metadata["key_id"] == "k1"
    assert entry.metadata["total"] == 5


def test_catalogo_lista_so_o_alcancavel(client, token):
    r = client.get("/v1/catalogo", headers=token)
    assert r.status_code == 200
    assert r.json() == {
        "acesso": [
            {
                "org": "lexgroup",
                "unidade": "NG",
                "dashboard": "protocolo-lexpre",
                "relatorios": [{"chave": "", "titulo": "", "campos": list(FIELDS)}],
            }
        ]
    }


def test_rate_limiter_janela_deslizante():
    clock = [0.0]
    rl = RateLimiter(limit=2, window_s=60, monotonic=lambda: clock[0])
    assert rl.hit("k") and rl.hit("k") and not rl.hit("k")
    assert rl.hit("outra")
    clock[0] = 61
    assert rl.hit("k")
