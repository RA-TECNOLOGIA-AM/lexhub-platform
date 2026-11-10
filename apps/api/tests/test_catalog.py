from app.catalog import DashboardUnitRow, UpcomingRow
from conftest import USER_ID


def row(key="protocolo-lexpre", unit="NG", can_export=True, can_see_commission=True, **kw):
    base = {
        "title": "Protocolo",
        "area": "Operação jurídica",
        "desc": "Protocolados, represados e devoluções.",
        "source": "LexPre",
        "max_delay_min": 60,
    }
    return DashboardUnitRow(
        key=key,
        unit_code=unit,
        can_export=can_export,
        can_see_commission=can_see_commission,
        **{**base, **kw},
    )


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def test_sem_login_401(client):
    assert client.get("/orgs/lexgroup/dashboards").status_code == 401


def test_formato_do_card(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row())

    r = client.get("/orgs/lexgroup/dashboards", headers=auth(signer))

    assert r.status_code == 200
    assert r.json() == {
        "available": [
            {
                "key": "protocolo-lexpre",
                "title": "Protocolo",
                "area": "Operação jurídica",
                "desc": "Protocolados, represados e devoluções.",
                "units": ["NG"],
                "source": "LexPre",
                "synced_at": None,
                "max_delay_min": 60,
                "can_export": True,
                "can_see_commission": True,
            }
        ],
        "upcoming": [],
    }


def test_um_card_por_dashboard_com_as_unidades_na_ordem(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    for r in (
        row(unit="LA"),
        row(unit="NG"),
        row(key="pendencias", title="Pendências", unit="NG"),
    ):
        catalog_repo.add(USER_ID, repo.org_id, r)

    available = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"]

    assert [(d["key"], d["units"]) for d in available] == [
        ("protocolo-lexpre", ["LA", "NG"]),
        ("pendencias", ["NG"]),
    ]


def test_exportar_e_comissao_so_se_valer_em_todas_as_unidades(client, signer, repo, catalog_repo):
    """Gestor na NG e leitor na LA: o botão não aparece (a API negaria na LA)."""
    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row(unit="NG"))
    catalog_repo.add(
        USER_ID, repo.org_id, row(unit="LA", can_export=False, can_see_commission=False)
    )

    card = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"][0]

    assert card["units"] == ["NG", "LA"]
    assert card["can_export"] is False
    assert card["can_see_commission"] is False


def test_colaborador_exporta_mas_nao_ve_comissao(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row(can_see_commission=False))
    card = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"][0]
    assert card["can_export"] is True
    assert card["can_see_commission"] is False


def test_membro_sem_dashboard_liberado_ve_catalogo_vazio(client, signer, repo):
    """Diferente da v1: sem equipe ou unidade, não vê nenhum."""
    repo.join(USER_ID)
    r = client.get("/orgs/lexgroup/dashboards", headers=auth(signer))
    assert r.status_code == 200
    assert r.json() == {"available": [], "upcoming": []}


def test_em_breve(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    catalog_repo.upcoming = [UpcomingRow(title="Peticionamento", area="Operação jurídica")]
    body = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()
    assert body["upcoming"] == [{"title": "Peticionamento", "area": "Operação jurídica"}]


def test_nao_membro_403_e_audita(client, signer, repo, catalog_repo):
    catalog_repo.add(USER_ID, repo.org_id, row())  # mesmo com dados, sem ser membro não vê
    r = client.get("/orgs/lexgroup/dashboards", headers={**auth(signer), "User-Agent": "pytest"})
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    a = repo.audits[0]
    assert a.action == "org.access_denied"
    assert a.actor_user_id == USER_ID
    assert a.org_id is None
    assert a.target_id == "lexgroup"
    assert a.user_agent == "pytest"


def test_org_inexistente_403_igual(client, signer, repo):
    r = client.get("/orgs/nao-existe/dashboards", headers=auth(signer))
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    assert repo.audits[0].target_id == "nao-existe"


def test_membro_nao_audita(client, signer, repo):
    repo.join(USER_ID)
    client.get("/orgs/lexgroup/dashboards", headers=auth(signer))
    assert repo.audits == []


def test_slug_invalido_422(client, signer):
    assert client.get("/orgs/Org_X/dashboards", headers=auth(signer)).status_code == 422
