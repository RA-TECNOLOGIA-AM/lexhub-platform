import base64
import os

import pytest

from app.connection_check import Check, CheckResult
from app.database import SourceUnavailable
from app.secret_box import SecretBox
from app.sheets import InvalidSheetLink, TabInfo
from app.source_admin import ManagedSource, RuleBroken
from conftest import USER_ID

BOX = SecretBox(os.urandom(32))
LINK = "https://docs.google.com/spreadsheets/d/e/2PACX-abcdefghijklmnopqrstuvwxyz/pub?output=xlsx"


class FakeAdminRepo:
    """Banco da plataforma em memória: TI da LexGroup, unidades e as fontes conectadas."""

    def __init__(self):
        self.admins: set[str] = set()
        self.units = {("cliente", "MC"): "unit-1"}
        self.sources: dict[str, ManagedSource] = {}
        self.runs: list[tuple] = []
        self.calls: list[tuple] = []
        self.fail: Exception | None = None

    async def is_source_admin(self, user_id):
        return user_id in self.admins

    async def unit_id(self, org_slug, unit_code):
        return self.units.get((org_slug, unit_code))

    async def source(self, org_slug, key):
        return self.sources.get(key)

    async def connect(
        self, user_id, unit_id, connector, name, detail, config, ciphertext, writer_ack, schema
    ):
        if self.fail:
            raise self.fail
        key = f"{'gs' if connector == 'sheets' else connector[:2]}_mc_000001"
        self.calls.append(
            ("connect", connector, name, detail, config, ciphertext, writer_ack, schema)
        )
        self.sources[key] = ManagedSource(
            id="src-1",
            key=key,
            org_id="org-1",
            unit_id=unit_id,
            connector=connector,
            name=name,
            config=config,
            secret_ciphertext=ciphertext,
        )
        return {"id": key, "connector": connector, "name": name, "status": "no_dashboards"}

    async def set_secret(self, user_id, source_id, ciphertext, writer_ack, schema):
        self.calls.append(("set_secret", source_id, ciphertext, writer_ack))
        return {"id": "pg_mc_000001", "status": "no_dashboards"}

    async def disconnect(self, user_id, source_id):
        self.calls.append(("disconnect", source_id))

    async def set_enabled(self, user_id, source_id, enabled):
        if self.fail:
            raise self.fail
        self.calls.append(("set_enabled", user_id, source_id, enabled))
        return {"id": "pg_mc_000001", "status": "healthy" if enabled else "disabled"}

    async def record_run(self, source_id, kind, ok, checks, ms, error):
        self.runs.append((source_id, kind, ok, error))


def db_result(*, ok=True, can_write=False) -> CheckResult:
    checks = [Check("network", True, "A API alcançou h:5432"), Check("login", ok, "x")]
    if ok:
        checks += [
            Check("read", True, "2 tabelas"),
            Check("readOnly", not can_write, "y", severity="warn" if can_write else "error"),
        ]
    return CheckResult(
        checks, can_write=can_write, schema_cache={"public.t": [["id", "int"]]} if ok else None
    )


class Fakes:
    def __init__(self):
        self.repo = FakeAdminRepo()
        self.db = db_result()
        self.targets: list = []
        self.tabs: dict[str, TabInfo] | Exception = {
            "FINANCEIRO": TabInfo(120, ["DATA", "VALOR"]),
            "METAS": TabInfo(12, ["MES", "META"]),
        }
        self.invalidated: list[str] = []
        self.switch_invalidated = 0

    async def check_db(self, target):
        self.targets.append(target)
        return self.db

    async def read_sheet(self, link):
        if isinstance(self.tabs, Exception):
            raise self.tabs
        return self.tabs

    async def invalidate(self, key):
        self.invalidated.append(key)


class FakeSwitch:
    def __init__(self, fakes):
        self.fakes = fakes

    def invalidate(self):
        self.fakes.switch_invalidated += 1


@pytest.fixture
def fx(client):
    from app.routes import source_connections as sc
    from app.source_admin import get_source_admin_repo
    from app.sources import get_registered_sources, get_source_switch

    f = Fakes()
    o = client.app.dependency_overrides
    o[get_source_admin_repo] = lambda: f.repo
    o[sc.get_db_checker] = lambda: f.check_db
    o[sc.get_sheet_reader] = lambda: f.read_sheet
    o[sc.get_secret_box] = lambda: BOX
    o[sc.get_rate_limit] = lambda: sc.RateLimit(limit=100)
    o[get_registered_sources] = lambda: f
    o[get_source_switch] = lambda: FakeSwitch(f)
    return f


def auth(signer):
    return {"Authorization": f"Bearer {signer.token()}"}


DB = {
    "connector": "postgres",
    "name": "Banco Manaus",
    "host": "db.operacao.com.br",
    "database": "operacao",
    "user": "lexhub_leitura",
    "password": "s3nh@",
}


def test_so_a_ti_da_lexgroup(client, signer, fx):
    r = client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer))
    assert r.status_code == 403
    assert client.get("/sources/connect-info", headers=auth(signer)).status_code == 403


def test_conecta_postgres_cifra_a_senha_e_registra_o_teste(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    r = client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer))
    assert r.status_code == 200
    body = r.json()
    assert body["saved"] and body["source"]["id"] == "po_mc_000001"
    assert [c["key"] for c in body["checks"]] == ["network", "login", "read", "readOnly"]
    _, _connector, _name, detail, config, ciphertext, _writer_ack, schema = fx.repo.calls[0]
    assert config == {
        "host": "db.operacao.com.br",
        "port": 5432,
        "database": "operacao",
        "user": "lexhub_leitura",
        "ssl": True,
    }
    assert "s3nh@" not in str(fx.repo.calls) and BOX.decrypt(ciphertext) == "s3nh@"
    assert detail == "Postgres · db.operacao.com.br/operacao" and schema == {
        "public.t": [["id", "int"]]
    }
    assert fx.targets[0].port == 5432 and fx.repo.runs == [("src-1", "test", True, None)]
    assert "s3nh@" not in r.text


def test_mysql_usa_a_porta_3306(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    client.post(
        "/orgs/cliente/units/MC/sources", json={**DB, "connector": "mysql"}, headers=auth(signer)
    )
    assert fx.targets[0].port == 3306 and fx.targets[0].connector == "mysql"


def test_teste_falhou_nao_grava(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    fx.db = db_result(ok=False)
    body = client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer)).json()
    assert body == {**body, "saved": False, "needsWriterAck": False, "source": None}
    assert fx.repo.calls == []


def test_usuario_que_escreve_pede_confirmacao_e_salva_com_ela(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    fx.db = db_result(can_write=True)
    first = client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer)).json()
    assert first["needsWriterAck"] and not first["saved"] and fx.repo.calls == []
    second = client.post(
        "/orgs/cliente/units/MC/sources", json={**DB, "writerAck": True}, headers=auth(signer)
    ).json()
    assert second["saved"] and fx.repo.calls[0][6] is True


def test_conecta_planilha_com_o_link_cifrado(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    sheet = {"connector": "sheets", "name": "Financeiro MC", "url": LINK, "tab": "FINANCEIRO"}
    body = client.post("/orgs/cliente/units/MC/sources", json=sheet, headers=auth(signer)).json()
    assert body["saved"]
    _, connector, _, detail, config, ciphertext, _, _ = fx.repo.calls[0]
    assert (
        connector == "sheets"
        and config == {"tab": "FINANCEIRO"}
        and BOX.decrypt(ciphertext) == LINK
    )
    assert detail == "Google Planilhas · aba FINANCEIRO"
    # As abas e colunas vão para o detalhe técnico (o analista vê); o link nunca volta.
    assert fx.repo.calls[0][7] == {
        "FINANCEIRO": [["DATA", ""], ["VALOR", ""]],
        "METAS": [["MES", ""], ["META", ""]],
    }
    assert LINK not in str(body)


def test_planilha_com_aba_inexistente_ou_que_nao_baixa(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    sheet = {"connector": "sheets", "name": "F", "url": LINK, "tab": "NAO_TEM"}
    body = client.post("/orgs/cliente/units/MC/sources", json=sheet, headers=auth(signer)).json()
    assert not body["saved"] and "não existe" in body["checks"][1]["message"]
    fx.tabs = SourceUnavailable("x")
    body = client.post(
        "/orgs/cliente/units/MC/sources", json={**sheet, "tab": "FINANCEIRO"}, headers=auth(signer)
    ).json()
    assert not body["saved"] and "Publicar na Web" in body["checks"][0]["message"]


def test_inspecionar_planilha_lista_as_abas(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    r = client.post("/sources/sheets/inspect", json={"url": LINK}, headers=auth(signer))
    assert r.json() == {
        "tabs": [{"name": "FINANCEIRO", "rows": 120}, {"name": "METAS", "rows": 12}]
    }
    fx.tabs = InvalidSheetLink("x")
    r = client.post(
        "/sources/sheets/inspect",
        json={"url": "https://exemplo.com/planilha"},
        headers=auth(signer),
    )
    assert r.status_code == 422 and "Link inválido" in r.json()["detail"]


def test_unidade_inexistente_404_e_regra_do_banco_409(client, signer, fx):
    fx.repo.admins.add(USER_ID)
    assert (
        client.post("/orgs/cliente/units/XX/sources", json=DB, headers=auth(signer)).status_code
        == 404
    )
    fx.repo.fail = RuleBroken("Dê um nome para a fonte.\nCONTEXT: ...")
    r = client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer))
    assert r.status_code == 409 and r.json()["detail"] == "Dê um nome para a fonte."


def _connected(fx, ciphertext=None):
    fx.repo.admins.add(USER_ID)
    fx.repo.sources["pg_mc_000001"] = ManagedSource(
        id="src-1",
        key="pg_mc_000001",
        org_id="org-1",
        unit_id="unit-1",
        connector="postgres",
        name="Banco",
        config={"host": "db.x.com", "port": 5432, "database": "d", "user": "u", "ssl": True},
        secret_ciphertext=ciphertext or BOX.encrypt("antiga"),
    )


def test_testar_de_novo_usa_a_senha_salva_e_grava_no_log(client, signer, fx):
    _connected(fx)
    r = client.post("/orgs/cliente/sources/pg_mc_000001/test", headers=auth(signer))
    assert r.json()["ok"] and fx.targets[0].password == "antiga"
    assert fx.repo.runs == [("src-1", "test", True, None)]


def test_trocar_senha_testa_a_nova_e_invalida_o_pool(client, signer, fx):
    _connected(fx)
    r = client.put(
        "/orgs/cliente/sources/pg_mc_000001/secret", json={"password": "nova"}, headers=auth(signer)
    )
    assert r.json()["saved"] and fx.targets[0].password == "nova"
    assert BOX.decrypt(fx.repo.calls[0][2]) == "nova" and fx.invalidated == ["pg_mc_000001"]
    r = client.put("/orgs/cliente/sources/pg_mc_000001/secret", json={}, headers=auth(signer))
    assert r.status_code == 422


def test_desconectar_e_fonte_que_nao_e_da_tela(client, signer, fx):
    _connected(fx)
    assert (
        client.delete("/orgs/cliente/sources/pg_mc_000001", headers=auth(signer)).status_code == 204
    )
    assert ("disconnect", "src-1") in fx.repo.calls and fx.invalidated == ["pg_mc_000001"]
    fx.repo.sources["lexpre"] = ManagedSource(
        id="p",
        key="lexpre",
        org_id="o",
        unit_id=None,
        connector="lexpre",
        name="LexPre",
        config={},
        secret_ciphertext=None,
    )
    assert client.delete("/orgs/cliente/sources/lexpre", headers=auth(signer)).status_code == 409


def test_desligar_e_religar_limpa_os_caches_na_hora(client, signer, fx):
    _connected(fx)
    url = "/orgs/cliente/sources/pg_mc_000001/enabled"
    r = client.put(url, json={"enabled": False}, headers=auth(signer))
    assert r.status_code == 200 and r.json()["status"] == "disabled"
    assert fx.repo.calls[-1] == ("set_enabled", USER_ID, "src-1", False)
    assert fx.invalidated == ["pg_mc_000001"] and fx.switch_invalidated == 1
    r = client.put(url, json={"enabled": True}, headers=auth(signer))
    assert r.json()["status"] == "healthy" and fx.switch_invalidated == 2
    # Religar não pede segredo: nenhuma troca de senha aconteceu.
    assert not any(c[0] == "set_secret" for c in fx.repo.calls)
    assert client.put(url, json={}, headers=auth(signer)).status_code == 422


def test_so_a_ti_liga_e_desliga(client, signer, fx):
    _connected(fx)
    fx.repo.admins.clear()
    r = client.put(
        "/orgs/cliente/sources/pg_mc_000001/enabled", json={"enabled": False}, headers=auth(signer)
    )
    assert r.status_code == 403 and fx.repo.calls == [] and fx.switch_invalidated == 0


def test_ligar_desligar_regra_do_banco_vira_409(client, signer, fx):
    _connected(fx)
    fx.repo.fail = RuleBroken("Informe se a fonte fica ligada ou desligada.\nCONTEXT: ...")
    r = client.put(
        "/orgs/cliente/sources/pg_mc_000001/enabled", json={"enabled": False}, headers=auth(signer)
    )
    assert r.status_code == 409 and r.json()["detail"].startswith("Informe se a fonte")
    assert fx.switch_invalidated == 0


def test_connect_info(client, signer, fx):
    from app.config import get_settings

    fx.repo.admins.add(USER_ID)
    settings = get_settings().model_copy(
        update={
            "SOURCE_SECRET_KEY": base64.b64encode(os.urandom(32)).decode(),
            "SOURCE_EGRESS_IP": "203.0.113.10",
        }
    )
    client.app.dependency_overrides[get_settings] = lambda: settings
    assert client.get("/sources/connect-info", headers=auth(signer)).json() == {
        "ready": True,
        "egressIp": "203.0.113.10",
    }


def test_limite_de_testes(client, signer, fx):
    from app.routes import source_connections as sc

    fx.repo.admins.add(USER_ID)
    client.app.dependency_overrides[sc.get_rate_limit] = lambda: limiter
    limiter = sc.RateLimit(limit=1)
    assert (
        client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer)).status_code
        == 200
    )
    assert (
        client.post("/orgs/cliente/units/MC/sources", json=DB, headers=auth(signer)).status_code
        == 429
    )
