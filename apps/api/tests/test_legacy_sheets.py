import asyncio
import os

from app.database import SourceUnavailable
from app.legacy_sheets import migrate
from app.secret_box import SecretBox
from app.sheets import TabInfo

BOX = SecretBox(os.urandom(32))
NG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQabcdefghijklmnopqrstuvNG/pub?output=xlsx"
LA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQabcdefghijklmnopqrstuvLA/pub?output=xlsx"


class FakeRepo:
    """As planilhas antigas no banco: sem link até o script gravar; não sobrescreve."""

    def __init__(self, with_link=()):
        self.saved: dict[str, tuple[str, dict | None]] = {k: ("v1:x", None) for k in with_link}

    async def without_link(self, keys):
        return {k for k in keys if k not in self.saved}

    async def save(self, key, ciphertext, schema):
        if key in self.saved:
            return False
        self.saved[key] = (ciphertext, schema)
        return True


async def read(link):
    return {"REPASSES CLIENTES": TabInfo(10, ["HONO", "DATA"])}


def run(repo, links, reader=read):
    return asyncio.run(migrate(repo, BOX, links, reader))


def test_cifra_os_links_e_guarda_as_abas():
    repo = FakeRepo()
    out = run(repo, {"sheets_financeiro_ng": NG, "sheets_financeiro_la": LA})
    assert [o.saved for o in out] == [True, True]
    cipher, schema = repo.saved["sheets_financeiro_ng"]
    assert BOX.decrypt(cipher) == NG and NG not in cipher
    assert schema == {"REPASSES CLIENTES": [["HONO", ""], ["DATA", ""]]}
    assert all(NG not in o.result for o in out)  # o link nunca vai para a tela


def test_repetir_nao_sobrescreve():
    repo = FakeRepo(with_link=["sheets_financeiro_ng"])
    out = run(
        repo, {"sheets_financeiro_ng": "https://docs.google.com/outro", "sheets_financeiro_la": LA}
    )
    assert out[0].result.startswith("já estava") and not out[0].saved
    assert repo.saved["sheets_financeiro_ng"] == ("v1:x", None) and out[1].saved


def test_sem_link_ou_link_invalido_fica_de_fora():
    repo = FakeRepo()
    out = run(repo, {"sheets_financeiro_ng": "https://exemplo.com/planilha"})
    assert [o.result for o in out] == [
        "link inválido (não é de planilha do Google)",
        "sem link no .env",
    ]
    assert repo.saved == {}


def test_planilha_fora_do_ar_grava_sem_as_abas():
    async def down(link):
        raise SourceUnavailable("x")

    repo = FakeRepo()
    out = run(repo, {"sheets_financeiro_ng": NG}, down)
    assert out[0].saved and repo.saved["sheets_financeiro_ng"][1] is None
