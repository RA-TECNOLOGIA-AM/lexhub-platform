import asyncio
import base64
import os

import pytest

from app.config import Settings
from app.database import SourceUnavailable
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


def row(key="gs_mc_abc123", connector="sheets", secret="https://docs.google.com/x", version=1):
    return RegisteredRow(
        id="s1",
        key=key,
        connector=connector,
        config={"tab": "A"},
        secret_ciphertext=BOX.encrypt(secret),
        config_version=version,
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
    assert asyncio.run(reg.get("gs_mc_abc123")).secret == "https://docs.google.com/x"
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


def test_planilha_conectada_baixa_pelo_link_decifrado(monkeypatch):
    seen = {}

    async def fake_download(db_name, url=None):
        seen["url"] = url
        return {"A": [{"x": 1}]}

    monkeypatch.setattr("app.sheets._download_and_parse", fake_download)
    reg = RegisteredSources(FakeRepo({"gs_mc_abc123": row()}), settings())
    rows = asyncio.run(RegisteredSourceFetcher(reg, "gs_mc_abc123").fetch("A"))
    assert rows == [{"x": 1}] and seen["url"] == "https://docs.google.com/x"


def test_roteamento_banco_do_env_planilha_antiga_e_fonte_da_tela():
    from app.registered_sources import RegisteredSourceFetcher as Reg
    from app.sheets import SheetSourceFetcher
    from app.sources import PgSourceFetcher, source_fetcher

    reg = RegisteredSources(FakeRepo({}), settings())
    assert isinstance(source_fetcher(object(), "ng", reg), PgSourceFetcher)
    assert isinstance(source_fetcher(object(), "sheets_financeiro_ng", reg), SheetSourceFetcher)
    assert isinstance(source_fetcher(object(), "pg_mc_abc123", reg), Reg)
    assert isinstance(source_fetcher(object(), "pg_mc_abc123", None), PgSourceFetcher)
