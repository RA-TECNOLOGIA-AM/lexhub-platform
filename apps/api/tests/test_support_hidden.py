"""Modo suporte: GET /orgs/{org}/support/sessions/{id}/hidden — o que o membro não vê numa unidade, e por quê."""

from app.support import HiddenRow
from conftest import USER_ID
from test_support_mode import MEMBER, as_member, auth, session  # noqa: F401  (fixture)

URL = "/orgs/lexgroup/support/sessions/{sid}/hidden?unit=NG"


def test_hidden_lista_motivos(client, signer, support_repo, session):  # noqa: F811
    support_repo.hidden_rows[("NG", MEMBER)] = [
        HiddenRow(key="comercial", title="Comercial", area="comercial", reason="no_sector_rule"),
        HiddenRow(key="nps", title="NPS", area="marketing", reason="dashboard_off"),
    ]
    r = client.get(URL.format(sid=session), headers=as_member(signer, session))
    assert r.status_code == 200
    assert r.json() == [
        {"key": "comercial", "title": "Comercial", "area": "comercial", "reason": "no_sector_rule"},
        {"key": "nps", "title": "NPS", "area": "marketing", "reason": "dashboard_off"},
    ]


def test_hidden_exige_sessao(client, signer, support_repo, session):  # noqa: F811
    # sem o cabeçalho: não está em suporte
    assert client.get(URL.format(sid=session), headers=auth(signer)).status_code == 404
    # cabeçalho de uma sessão, caminho de outra
    other = "00000000-0000-4000-8000-000000000999"
    assert client.get(URL.format(sid=other), headers=as_member(signer, session)).status_code == 404


def test_hidden_unidade_invalida_422(client, signer, session):  # noqa: F811
    r = client.get(
        f"/orgs/lexgroup/support/sessions/{session}/hidden?unit=ng!", headers=as_member(signer, session)
    )
    assert r.status_code == 422


def test_hidden_nao_e_do_dev(client, signer, support_repo, session):  # noqa: F811
    # a lista é do membro, nunca de quem pede
    support_repo.hidden_rows[("NG", USER_ID)] = [
        HiddenRow(key="x", title="X", area="a", reason="no_unit_role")
    ]
    r = client.get(URL.format(sid=session), headers=as_member(signer, session))
    assert r.json() == []
