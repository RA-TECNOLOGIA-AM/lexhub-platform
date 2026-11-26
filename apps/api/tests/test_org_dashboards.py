"""Rotas do dashboard da organização (Estratégico Geral): /orgs/{org}/geral/dashboards/{key}."""

import pytest
from tests.conftest import USER_ID

from app.org_dashboard import OrgDashboardUnit, ResolvedOrgDashboard, get_org_dashboard_repo

KEY = "estrategico-geral"
URL = f"/orgs/lexgroup/geral/dashboards/{KEY}"


class FakeOrgDashboardRepo:
    """Unidades do dashboard 'org' e quais a pessoa vê (o banco decide: só Owner e Desenvolvedor)."""

    def __init__(self):
        self.org_id = "00000000-0000-0000-0000-00000000000f"
        self.units = ["NG", "LA", "RJ"]
        self.visible: set[str] = set()  # unidades que a pessoa vê
        self.exists = True

    async def resolve(self, user_id, org_slug, dashboard_key):
        if not self.exists or org_slug != "lexgroup" or dashboard_key != KEY:
            return None
        return ResolvedOrgDashboard(
            org_id=self.org_id,
            title="Estratégico Geral",
            source="Várias fontes",
            units=[
                OrgDashboardUnit(
                    code=c,
                    name=f"Unidade {c}",
                    timezone="America/Manaus",
                    visible=c in self.visible,
                )
                for c in self.units
            ],
        )


@pytest.fixture
def org_repo(client) -> FakeOrgDashboardRepo:
    fake = FakeOrgDashboardRepo()
    client.app.dependency_overrides[get_org_dashboard_repo] = lambda: fake
    return fake


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def test_owner_ou_dev_recebe_o_esqueleto(client, signer, org_repo):
    org_repo.visible = {"NG", "LA", "RJ"}

    res = client.get(URL, headers=auth(signer))

    assert res.status_code == 200
    body = res.json()
    assert body["meta"] == {
        "unit": "geral",
        "from": "2026-11-01",
        "to": "2026-11-11",
        "source": "Várias fontes",
        "synced_at": None,
        "timezone": "America/Manaus",
    }
    assert [u["code"] for u in body["units"]] == ["NG", "LA", "RJ"]
    assert all(u["data"] == {} for u in body["units"])


def test_periodo_da_url(client, signer, org_repo):
    org_repo.visible = {"NG", "LA", "RJ"}

    res = client.get(URL, params={"from": "2026-10-01", "to": "2026-10-31"}, headers=auth(signer))

    assert (res.json()["meta"]["from"], res.json()["meta"]["to"]) == ("2026-10-01", "2026-10-31")


def test_periodo_invertido_422(client, signer, org_repo):
    org_repo.visible = {"NG", "LA", "RJ"}

    res = client.get(URL, params={"from": "2026-10-31", "to": "2026-10-01"}, headers=auth(signer))

    assert res.status_code == 422


def test_sem_todas_as_unidades_403_auditado(client, signer, org_repo, repo):
    # Ex.: Gestor da NG — o banco nega o 'org' a quem não é Owner/Dev; faltar uma unidade já basta.
    org_repo.visible = {"NG", "LA"}

    res = client.get(URL, headers=auth(signer))

    assert res.status_code == 403
    [entry] = repo.audits
    assert entry.action == "dashboard.access_denied"
    assert entry.actor_user_id == USER_ID
    assert entry.target_id == KEY
    assert entry.metadata == {"org": "lexgroup", "unit": "GERAL"}


def test_dashboard_que_nao_e_da_organizacao_403(client, signer, org_repo):
    org_repo.exists = False

    res = client.get(URL, headers=auth(signer))

    assert res.status_code == 403


def test_sem_login_401(client, org_repo):
    assert client.get(URL).status_code == 401


def test_rota_access(client, signer, org_repo):
    org_repo.visible = {"NG", "LA", "RJ"}

    res = client.get(f"{URL}/access", headers=auth(signer))

    assert res.json() == {
        "org": "lexgroup",
        "unit": "geral",
        "dashboard": KEY,
        "units": ["NG", "LA", "RJ"],
    }
