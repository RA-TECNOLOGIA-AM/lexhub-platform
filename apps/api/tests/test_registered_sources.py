import asyncio
import base64
import os

import pytest

from app.config import Settings
from app.database import SourceDisabled, SourceUnavailable
from app.registered_sources import RegisteredRow, RegisteredSourceFetcher, RegisteredSources
from app.secret_box import SecretBox
from app.sheets import InvalidSheetLink, sheet_download_url

KEY = base64.b64encode(os.urandom(32)).decode()
BOX = SecretBox.from_setting(KEY)


def settings(**over) -> Settings:
    base = {
        "SUPABASE_URL": "https://x.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "pk",
        "SOURCE_SECRET_KEY": KEY,
    }
    return Settings(_env_file=None, **{**base, **over})


class FakeRepo:
    def __init__(self, rows):
        self.rows = rows
        self.loads = 0

    async def load(self, key):
        self.loads += 1
        return self.rows.get(key)


PUB = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQabcdefghijklmnopqrstuv/pubhtml"


def row(key="gs_mc_abc123", connector="sheets", secret=PUB, version=1, enabled=True, config=None):
    return RegisteredRow(
        id="s1",
        key=key,
        connector=connector,
        config={"tab": "A"} if config is None else config,
        secret_ciphertext=BOX.encrypt(secret),
        config_version=version,
        enabled=enabled,
    )


def test_link_colado_vira_link_de_download():
    pub = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQabcdefghijklmnopqrstuv/pubhtml"
    assert sheet_download_url(pub) == (
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vQabcdefghijklmnopqrstuv/pub?output=xlsx"
    )
    shared = "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit#gid=0"
    assert sheet_download_url(shared) == (
        "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/export?format=xlsx"
    )
    for bad in (
        "http://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit",
        "https://evil.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit",
        "https://docs.google.com.evil.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit",
        "https://docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit",
    ):
        with pytest.raises(InvalidSheetLink):
            sheet_download_url(bad)


def test_decifra_guarda_por_5_minutos_e_esquece_ao_invalidar():
    now = {"t": 0.0}
    repo = FakeRepo({"gs_mc_abc123": row()})
    reg = RegisteredSources(repo, settings(), ttl=300, clock=lambda: now["t"])
    assert asyncio.run(reg.get("gs_mc_abc123")).secret == PUB
    now["t"] = 299
    asyncio.run(reg.get("gs_mc_abc123"))
    assert repo.loads == 1
    asyncio.run(reg.invalidate("gs_mc_abc123"))
    asyncio.run(reg.get("gs_mc_abc123"))
    assert repo.loads == 2


def test_fonte_inexistente_ou_chave_errada_fica_indisponivel():
    reg = RegisteredSources(FakeRepo({}), settings())
    with pytest.raises(SourceUnavailable):
        asyncio.run(reg.get("pg_x_000000"))
    other_key = base64.b64encode(os.urandom(32)).decode()
    reg = RegisteredSources(
        FakeRepo({"gs_mc_abc123": row()}), settings(SOURCE_SECRET_KEY=other_key)
    )
    with pytest.raises(SourceUnavailable):
        asyncio.run(reg.get("gs_mc_abc123"))


def test_planilha_baixa_pelo_link_decifrado_convertido_em_xlsx(monkeypatch):
    seen = {}

    async def fake_download(db_name, url):
        seen["url"] = url
        return {"A": [{"x": 1}]}

    monkeypatch.setattr("app.sheets._download_and_parse", fake_download)
    reg = RegisteredSources(FakeRepo({"gs_mc_abc123": row()}), settings())
    rows = asyncio.run(RegisteredSourceFetcher(reg, "gs_mc_abc123").fetch("A"))
    # O link colado (pubhtml) não é baixado como está: vira o de download em XLSX.
    assert rows == [{"x": 1}] and seen["url"] == sheet_download_url(PUB)
    assert seen["url"].endswith("/pub?output=xlsx")


def test_planilha_antiga_le_qualquer_aba_pelo_link_do_banco(monkeypatch):
    async def fake_download(db_name, url):
        return {"REPASSES CLIENTES": [{"HONO": 10}], "OUTRA": []}

    monkeypatch.setattr("app.sheets._download_and_parse", fake_download)
    old = row(key="sheets_financeiro_ng", config={})
    reg = RegisteredSources(FakeRepo({"sheets_financeiro_ng": old}), settings())
    fetcher = RegisteredSourceFetcher(reg, "sheets_financeiro_ng")
    assert asyncio.run(fetcher.fetch("REPASSES CLIENTES")) == [{"HONO": 10}]


def test_fonte_desligada_nao_abre_e_religada_volta_sem_novo_link(monkeypatch):
    async def fake_download(db_name, url):
        return {"A": [{"x": 1}]}

    monkeypatch.setattr("app.sheets._download_and_parse", fake_download)
    repo = FakeRepo({"gs_mc_abc123": row(enabled=False)})
    reg = RegisteredSources(repo, settings())
    with pytest.raises(SourceDisabled):
        asyncio.run(reg.get("gs_mc_abc123"))
    # Religou (mesmo segredo no banco): a API invalida e a próxima leitura já funciona.
    repo.rows["gs_mc_abc123"] = row(enabled=True)
    asyncio.run(reg.invalidate("gs_mc_abc123"))
    assert asyncio.run(RegisteredSourceFetcher(reg, "gs_mc_abc123").fetch("A")) == [{"x": 1}]


def test_roteamento_banco_do_env_e_fonte_com_segredo_no_banco():
    from app.registered_sources import RegisteredSourceFetcher as Reg
    from app.sources import PgSourceFetcher, source_fetcher

    reg = RegisteredSources(FakeRepo({}), settings())
    assert isinstance(source_fetcher(object(), "ng", reg), PgSourceFetcher)
    assert isinstance(source_fetcher(object(), "sheets_financeiro_ng", reg), Reg)
    assert isinstance(source_fetcher(object(), "pg_mc_abc123", reg), Reg)
    # Sem o banco da plataforma: indisponível (não tenta o .env, que não tem mais o link).
    with pytest.raises(SourceUnavailable):
        asyncio.run(source_fetcher(object(), "sheets_financeiro_ng", None).fetch("A"))
