import asyncio

import pytest

from app.database import SourceUnavailable
from app.source_offices import LinkedUnit, OfficeRow, ProductOfficeReader
from conftest import USER_ID


class FakeOfficesRepo:
    """Banco da plataforma em memória: quem é TI da LexGroup e as refs já ligadas por produto."""

    def __init__(self):
        self.admins: set[str] = set()
        self.links: dict[str, dict[str, LinkedUnit]] = {}

    async def is_source_admin(self, user_id):
        return user_id in self.admins

    async def linked(self, product):
        return dict(self.links.get(product, {}))


class FakeReader:
    """Banco do produto em memória: produto -> escritórios."""

    def __init__(self):
        self.rows: dict[str, list[OfficeRow]] = {}
        self.down = False

    async def __call__(self, product):
        if self.down:
            raise SourceUnavailable(product)
        return list(self.rows.get(product, []))


@pytest.fixture
def offices(client):
    from app.source_offices import get_office_reader, get_offices_repo

    repo, reader = FakeOfficesRepo(), FakeReader()
    client.app.dependency_overrides[get_offices_repo] = lambda: repo
    client.app.dependency_overrides[get_office_reader] = lambda: reader
    return repo, reader


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def test_sem_login_401(client, offices):
    assert client.get("/sources/lexpre/offices").status_code == 401


def test_quem_nao_e_ti_da_lexgroup_recebe_403(client, signer, offices):
    assert client.get("/sources/lexpre/offices", headers=auth(signer)).status_code == 403


def test_lista_escritorios_do_lexpre_e_onde_ja_estao_ligados(client, signer, offices):
    repo, reader = offices
    repo.admins.add(USER_ID)
    reader.rows["lexpre"] = [
        OfficeRow(ref="1", name="Nicolas Gomes", activity=3412),
        OfficeRow(ref="4", name="Escritório Manaus Centro", activity=128),
    ]
    repo.links["lexpre"] = {"1": LinkedUnit(org="LexGroup", unit="NG", unit_name="Nicolas Gomes")}

    r = client.get("/sources/lexpre/offices", headers=auth(signer))

    assert r.status_code == 200
    assert r.json() == {
        "product": "lexpre",
        "activityLabel": "movimentações nos últimos 30 dias",
        "offices": [
            {
                "ref": "1",
                "name": "Nicolas Gomes",
                "activity": 3412,
                "linkedTo": {"org": "LexGroup", "unit": "NG", "unitName": "Nicolas Gomes"},
            },
            {"ref": "4", "name": "Escritório Manaus Centro", "activity": 128, "linkedTo": None},
        ],
    }


def test_lexflow_reconhece_os_codigos_da_v1_como_os_ids_do_banco(client, signer, offices):
    # A ligação do RJ é guardada como 'RJ' (código que os dashboards usam), mas no banco é o id 27.
    repo, reader = offices
    repo.admins.add(USER_ID)
    reader.rows["lexflow"] = [OfficeRow(ref="27", name="LA Rio de Janeiro", activity=402)]
    repo.links["lexflow"] = {"RJ": LinkedUnit(org="LexGroup", unit="RJ", unit_name="LA RJ")}

    body = client.get("/sources/lexflow/offices", headers=auth(signer)).json()

    assert body["activityLabel"] == "processos"
    assert body["offices"][0]["linkedTo"] == {"org": "LexGroup", "unit": "RJ", "unitName": "LA RJ"}


def test_banco_interno_nao_tem_lista(client, signer, offices):
    offices[0].admins.add(USER_ID)
    assert client.get("/sources/ng/offices", headers=auth(signer)).status_code == 422


def test_banco_do_produto_fora_do_ar_503(client, signer, offices):
    repo, reader = offices
    repo.admins.add(USER_ID)
    reader.down = True
    r = client.get("/sources/lexpre/offices", headers=auth(signer))
    assert r.status_code == 503


def test_leitor_guarda_a_lista_por_10_minutos():
    calls: list[str] = []
    now = {"t": 0.0}

    async def fetch(product):
        calls.append(product)
        return [OfficeRow(ref="1", name="A", activity=1)]

    reader = ProductOfficeReader(fetch, ttl_seconds=600, clock=lambda: now["t"])
    asyncio.run(reader("lexpre"))
    now["t"] = 599
    asyncio.run(reader("lexpre"))
    assert calls == ["lexpre"]
    now["t"] = 601
    asyncio.run(reader("lexpre"))
    asyncio.run(reader("lexflow"))
    assert calls == ["lexpre", "lexpre", "lexflow"]
