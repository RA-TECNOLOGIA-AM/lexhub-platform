from app.me import MembershipRow, OrgRow, UnitRow, initials
from conftest import USER_ID

LEXGROUP = OrgRow(id="org-1", slug="lexgroup", name="LexGroup", unit_count=3)
PARCEIRO = OrgRow(id="org-2", slug="cliente-parceiro", name="Cliente parceiro", unit_count=1)

# Permissões de cada papel, como em app.role_permissions.
ADMIN = frozenset({"org.dashboards.all", "dashboards.export", "members.manage"})
GESTOR = frozenset({"unit.dashboards.all", "dashboards.export", "unit.members.manage"})
COLABORADOR = frozenset({"dashboards.export"})
NENHUMA = frozenset()


def unit(code, name, role_name=None, permissions=NENHUMA):
    return UnitRow(code=code, name=name, role_name=role_name, permissions=permissions)


def membership(role_name="Membro", permissions=NENHUMA, units=(), full_name="Luís Tápia"):
    return MembershipRow(
        full_name=full_name, role_name=role_name, permissions=permissions, units=tuple(units)
    )


def auth(signer, **claims) -> dict:
    return {"Authorization": f"Bearer {signer.token(**claims)}"}


def test_sem_login_401(client):
    assert client.get("/me").status_code == 401


def test_admin_formato_completo(client, signer, me_repo):
    units = [unit("LA", "Luis Albert AM"), unit("NG", "Nicolas Gomes")]
    me_repo.add(USER_ID, LEXGROUP, membership("Desenvolvedor", ADMIN, units))
    me_repo.add(USER_ID, PARCEIRO, membership())

    r = client.get("/me", headers=auth(signer))

    assert r.status_code == 200
    assert r.json() == {
        "user": {
            "name": "Luís Tápia",
            "initials": "LT",
            "role_label": "Desenvolvedor",
            "can_export": True,
            "can_see_commission": True,
            "platform_staff": False,
        },
        "org": {"slug": "lexgroup", "name": "LexGroup", "sub": "3 unidades"},
        "units": [
            {"code": "LA", "name": "Luis Albert AM"},
            {"code": "NG", "name": "Nicolas Gomes"},
        ],
        "orgs": [
            {"slug": "lexgroup", "name": "LexGroup", "sub": "3 unidades"},
            {"slug": "cliente-parceiro", "name": "Cliente parceiro", "sub": "1 unidade"},
        ],
    }


def test_sem_org_usa_a_primeira(client, signer, me_repo):
    """O banco já devolve a última usada primeiro."""
    me_repo.add(USER_ID, PARCEIRO, membership())
    me_repo.add(USER_ID, LEXGROUP, membership())
    assert client.get("/me", headers=auth(signer)).json()["org"]["slug"] == "cliente-parceiro"


def test_org_pedida(client, signer, me_repo):
    me_repo.add(USER_ID, LEXGROUP, membership())
    me_repo.add(USER_ID, PARCEIRO, membership())
    body = client.get("/me?org=cliente-parceiro", headers=auth(signer)).json()
    assert body["org"]["slug"] == "cliente-parceiro"
    assert len(body["orgs"]) == 2


def test_org_de_que_nao_e_membro_403_e_audita(client, signer, me_repo, repo):
    me_repo.add(USER_ID, LEXGROUP, membership())
    r = client.get("/me?org=outra-org", headers={**auth(signer), "User-Agent": "pytest"})
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    a = repo.audits[0]
    assert a.action == "org.access_denied"
    assert a.actor_user_id == USER_ID
    assert a.org_id is None  # não revela o id de uma organização de que não faz parte
    assert a.target_type == "org"
    assert a.target_id == "outra-org"
    assert a.user_agent == "pytest"


def test_sem_nenhuma_org_403(client, signer, repo):
    r = client.get("/me", headers=auth(signer))
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    assert repo.audits[0].action == "org.access_denied"


def test_acesso_liberado_nao_audita(client, signer, me_repo, repo):
    me_repo.add(USER_ID, LEXGROUP, membership())
    client.get("/me", headers=auth(signer))
    assert repo.audits == []


def test_gestor_numa_unidade_leitor_noutra(client, signer, me_repo):
    units = [unit("NG", "Nicolas Gomes", "Gestor", GESTOR), unit("RJ", "Luis Albert RJ", "Leitor")]
    me_repo.add(USER_ID, LEXGROUP, membership(units=units))
    user = client.get("/me", headers=auth(signer)).json()["user"]
    assert user["role_label"] == "Gestor · Leitor"
    assert user["can_export"] is True
    assert user["can_see_commission"] is True


def test_colaborador_exporta_mas_nao_ve_comissao(client, signer, me_repo):
    units = [unit("NG", "Nicolas Gomes", "Colaborador", COLABORADOR)]
    me_repo.add(USER_ID, LEXGROUP, membership(units=units))
    user = client.get("/me", headers=auth(signer)).json()["user"]
    assert user["role_label"] == "Colaborador"
    assert user["can_export"] is True
    assert user["can_see_commission"] is False


def test_leitor_nao_exporta(client, signer, me_repo):
    me_repo.add(USER_ID, LEXGROUP, membership(units=[unit("NG", "Nicolas Gomes", "Leitor")]))
    user = client.get("/me", headers=auth(signer)).json()["user"]
    assert user["can_export"] is False
    assert user["can_see_commission"] is False


def test_sem_unidade_mostra_papel_da_org_e_nenhuma_unidade(client, signer, me_repo):
    me_repo.add(USER_ID, LEXGROUP, membership(units=[]))
    body = client.get("/me", headers=auth(signer)).json()
    assert body["user"]["role_label"] == "Membro"
    assert body["units"] == []


def test_platform_staff_vem_do_app_metadata(client, signer, me_repo):
    me_repo.add(USER_ID, LEXGROUP, membership())
    staff = auth(signer, app_metadata={"platform_staff": True})
    assert client.get("/me", headers=staff).json()["user"]["platform_staff"] is True


def test_platform_staff_no_user_metadata_nao_vale(client, signer, me_repo):
    """user_metadata o próprio usuário altera: não pode dar acesso à plataforma."""
    me_repo.add(USER_ID, LEXGROUP, membership())
    fake = auth(signer, user_metadata={"platform_staff": True})
    assert client.get("/me", headers=fake).json()["user"]["platform_staff"] is False


def test_slug_invalido_422(client, signer):
    assert client.get("/me?org=Org_Maiuscula", headers=auth(signer)).status_code == 422


def test_iniciais():
    assert initials("Luís Tápia") == "LT"
    assert initials("ana maria souza") == "AS"
    assert initials("Ana") == "A"
    assert initials("  ") == ""
