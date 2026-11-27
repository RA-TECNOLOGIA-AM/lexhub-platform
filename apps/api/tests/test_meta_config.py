import asyncio
import os
from datetime import UTC, datetime

import asyncpg
import pytest

from app.config import get_settings
from app.connection_check import Check, CheckResult
from app.meta_config import MetaConfig, StoredIntegration, resolve
from app.secret_box import SecretBox
from conftest import USER_ID

BOX = SecretBox(os.urandom(32))
SECRET = "a" * 32


def stored(config=None, secret=None):
    return StoredIntegration(
        config=config or {},
        secret_ciphertext=BOX.encrypt(secret) if secret else None,
        updated_at=datetime(2026, 11, 27, tzinfo=UTC),
        updated_by="TI",
    )


def env(**over):
    return get_settings().model_copy(update=over)


def test_resolve_tela_tem_prioridade_sobre_o_servidor():
    settings = env(
        FACEBOOK_APP_ID="999", FACEBOOK_APP_SECRET="b" * 32, FACEBOOK_GRAPH_VERSION="v25.0"
    )
    only_env = resolve(None, settings, BOX)
    assert (only_env.app_id, only_env.graph_version) == ("999", "v25.0")
    assert only_env.origin == {
        "appId": "servidor",
        "appSecret": "servidor",
        "graphVersion": "servidor",
        "syncInterval": "padrão",
    }
    assert only_env.app_token == f"999|{'b' * 32}"

    screen = resolve(stored({"app_id": "123", "graph_version": "v26.0"}, SECRET), settings, BOX)
    assert (screen.app_id, screen.app_secret, screen.graph_version) == ("123", SECRET, "v26.0")
    assert (
        screen.origin["appId"]
        == screen.origin["appSecret"]
        == screen.origin["graphVersion"]
        == "tela"
    )
    assert screen.sync_interval_min == 10 and screen.origin["syncInterval"] == "padrão"

    nothing = resolve(None, env(FACEBOOK_APP_ID="", FACEBOOK_APP_SECRET=""), BOX)
    assert nothing.app_token is None and nothing.graph_version == "v26.0"
    assert nothing.origin == {
        "appId": "nenhum",
        "appSecret": "nenhum",
        "graphVersion": "padrão",
        "syncInterval": "padrão",
    }


def test_resolve_intervalo_da_tela_e_valor_estranho_cai_no_padrao():
    s = resolve(stored({"sync_interval_min": 30}), env(), BOX)
    assert s.sync_interval_min == 30 and s.origin["syncInterval"] == "tela"
    odd = resolve(stored({"sync_interval_min": 7}), env(), BOX)
    assert odd.sync_interval_min == 10 and odd.origin["syncInterval"] == "padrão"


def test_resolve_chave_que_nao_abre_cai_no_servidor_e_avisa():
    other = SecretBox(os.urandom(32))
    s = resolve(stored({"app_id": "123"}, SECRET), env(FACEBOOK_APP_SECRET=""), other)
    assert s.secret_unreadable and s.app_secret == "" and s.origin["appSecret"] == "nenhum"


class FakeIntegrationRepo:
    def __init__(self, value=None, fail=None):
        self.value, self.fail = value, fail
        self.loads = 0
        self.saved: list[tuple] = []

    async def load(self, key):
        self.loads += 1
        if self.fail:
            raise self.fail
        return self.value

    async def save(self, user_id, key, config, ciphertext, action):
        self.saved.append((key, config, ciphertext, action))
        current = self.value.secret_ciphertext if self.value else None
        secret = {"keep": current, "set": ciphertext, "clear": None}[action]
        self.value = StoredIntegration(config, secret, datetime.now(tz=UTC), "TI")


def test_meta_config_guarda_por_ttl_e_segue_com_banco_fora():
    clock = [0.0]
    repo = FakeIntegrationRepo(stored({"app_id": "123", "sync_paused": True}, SECRET))
    meta = MetaConfig(repo, env(), BOX, ttl=60, clock=lambda: clock[0])

    async def go():
        await meta.refresh()
        await meta.refresh()
        assert repo.loads == 1 and meta.current.sync_paused
        clock[0] = 61
        await meta.refresh()
        assert repo.loads == 2
        repo.fail = asyncpg.UndefinedTableError("relation does not exist")
        meta.invalidate()
        await meta.refresh()  # banco recusou: fica o que já tinha
        assert meta.current.app_id == "123"

    asyncio.run(go())


# --- Rotas (app/routes/integrations_routes.py) ---------------------------------------------------------


class AdminRepo:
    def __init__(self):
        self.admins: set[str] = set()

    async def is_source_admin(self, user_id):
        return user_id in self.admins


class Fx:
    def __init__(self):
        self.admin = AdminRepo()
        self.repo = FakeIntegrationRepo()
        self.meta = MetaConfig(self.repo, env(FACEBOOK_APP_ID="", FACEBOOK_APP_SECRET=""), BOX)
        self.app_ok = True
        self.tested: list[tuple] = []
        self.woke = 0

    async def check(self, app_id, secret, version):
        self.tested.append((app_id, secret, version))
        checks = [Check("network", True, "ok"), Check("login", self.app_ok, "App")]
        return CheckResult(checks), "LexHub Ads" if self.app_ok else None

    def wake(self):
        self.woke += 1


@pytest.fixture
def fx(client):
    from app.meta_config import get_integration_repo, get_meta_config
    from app.routes import integrations_routes as ir
    from app.routes import source_connections as sc
    from app.source_admin import get_source_admin_repo

    f = Fx()

    async def meta():
        await f.meta.refresh()
        return f.meta

    o = client.app.dependency_overrides
    o[get_source_admin_repo] = lambda: f.admin
    o[get_integration_repo] = lambda: f.repo
    o[get_meta_config] = meta
    o[ir.get_app_checker] = lambda: f.check
    o[ir.get_optional_box] = lambda: BOX
    o[sc.get_ads_sync] = lambda: f
    o[sc.get_rate_limit] = lambda: sc.RateLimit(limit=100)
    return f


def auth(signer):
    return {"Authorization": f"Bearer {signer.token()}"}


URL = "/sources/integrations/meta"


def test_so_a_ti_da_lexgroup(client, signer, fx):
    assert client.get(URL, headers=auth(signer)).status_code == 403
    body = {"graphVersion": "v26.0"}
    assert client.put(URL, json=body, headers=auth(signer)).status_code == 403


def test_salvar_chave_nova_testa_cifra_e_nao_devolve_a_chave(client, signer, fx):
    fx.admin.admins.add(USER_ID)
    body = {"appId": "1234567", "appSecret": SECRET, "graphVersion": "v26.0", "syncPaused": False}
    r = client.put(URL, json=body, headers=auth(signer))
    out = r.json()
    assert r.status_code == 200 and out["saved"] and SECRET not in r.text
    assert fx.tested == [("1234567", SECRET, "v26.0")]
    key, config, ciphertext, action = fx.repo.saved[0]
    assert (key, action) == ("meta", "set") and BOX.decrypt(ciphertext) == SECRET
    assert config == {
        "graph_version": "v26.0",
        "sync_paused": False,
        "sync_interval_min": 10,
        "app_id": "1234567",
    }
    integ = out["integration"]
    assert integ["appId"] == "1234567" and integ["hasAppSecret"]
    assert integ["origin"]["appSecret"] == "tela"
    got = client.get(URL, headers=auth(signer)).json()
    assert got["hasAppSecret"] and "appSecret" not in got


def test_chave_que_a_meta_recusa_nao_grava(client, signer, fx):
    fx.admin.admins.add(USER_ID)
    fx.app_ok = False
    body = {"appId": "1234567", "appSecret": SECRET, "graphVersion": "v26.0"}
    out = client.put(URL, json=body, headers=auth(signer)).json()
    assert out["saved"] is False and fx.repo.saved == []


def test_manter_pausar_trocar_id_e_apagar(client, signer, fx):
    fx.admin.admins.add(USER_ID)
    fx.repo.value = stored({"app_id": "1234567", "graph_version": "v26.0"}, SECRET)
    # Só pausar: mantém a chave, não testa, acorda a coleta
    body = {"appId": "1234567", "graphVersion": "v26.0", "syncPaused": True}
    out = client.put(URL, json=body, headers=auth(signer)).json()
    assert out["saved"] and fx.repo.saved[-1][3] == "keep" and fx.tested == [] and fx.woke == 1
    assert out["integration"]["syncPaused"] is True
    # ID novo com a chave salva: testa com a chave que já estava
    body = {"appId": "7654321", "graphVersion": "v25.0", "syncPaused": True}
    client.put(URL, json=body, headers=auth(signer))
    assert fx.tested == [("7654321", SECRET, "v25.0")]
    # Sem ID: a chave sai junto
    body = {"appId": "", "graphVersion": "v26.0", "syncPaused": True}
    out = client.put(URL, json=body, headers=auth(signer)).json()
    assert fx.repo.saved[-1][3] == "clear" and not out["integration"]["hasAppSecret"]
    # Chave sem ID: recusado
    body = {"appId": "", "appSecret": SECRET, "graphVersion": "v26.0"}
    assert client.put(URL, json=body, headers=auth(signer)).status_code == 422


def test_intervalo_da_atualizacao(client, signer, fx):
    fx.admin.admins.add(USER_ID)
    got = client.get(URL, headers=auth(signer)).json()
    assert got["syncIntervalMin"] == 10 and got["intervals"] == [5, 10, 15, 30, 60]
    # Trocar o intervalo grava, acorda a coleta e a tela recebe o novo
    body = {"graphVersion": "v26.0", "syncIntervalMin": 30}
    out = client.put(URL, json=body, headers=auth(signer)).json()
    assert out["saved"] and out["integration"]["syncIntervalMin"] == 30 and fx.woke == 1
    assert fx.repo.saved[-1][1]["sync_interval_min"] == 30
    assert out["integration"]["origin"]["syncInterval"] == "tela"
    # Salvar de novo sem mudar nada não acorda
    client.put(URL, json=body, headers=auth(signer))
    assert fx.woke == 1
    # Fora da lista: recusado, nada gravado
    saved = len(fx.repo.saved)
    body = {"graphVersion": "v26.0", "syncIntervalMin": 7}
    assert client.put(URL, json=body, headers=auth(signer)).status_code == 422
    assert len(fx.repo.saved) == saved


def test_testar_app_usa_a_chave_em_uso_quando_nao_vem_outra(client, signer, fx):
    fx.admin.admins.add(USER_ID)
    body = {"appId": "1234567", "graphVersion": "v26.0"}
    out = client.post(f"{URL}/test", json=body, headers=auth(signer)).json()
    assert out["ok"] is False and "chave secreta" in out["checks"][0]["message"]
    fx.repo.value = stored({"app_id": "1234567"}, SECRET)
    fx.meta.invalidate()
    out = client.post(f"{URL}/test", json=body, headers=auth(signer)).json()
    assert out["ok"] and out["app"] == "LexHub Ads" and fx.tested[-1][1] == SECRET
