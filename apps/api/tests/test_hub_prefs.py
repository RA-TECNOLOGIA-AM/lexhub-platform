from app.hub_prefs import clean_order
from conftest import USER_ID

FAV = "/orgs/lexgroup/favorites"
ORDER = "/orgs/lexgroup/hub-order"


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


# --- Favoritos -------------------------------------------------------------


def test_sem_login_401(client):
    assert client.get(FAV).status_code == 401
    assert client.post(f"{FAV}/protocolo-lexpre").status_code == 401
    assert client.put(ORDER, json=[]).status_code == 401


def test_sem_favoritos_lista_vazia(client, signer, repo):
    repo.join(USER_ID)
    r = client.get(FAV, headers=auth(signer))
    assert r.status_code == 200
    assert r.json() == []


def test_favoritar_e_listar(client, signer, repo, hub_repo):
    repo.join(USER_ID)
    hub_repo.visible = {"protocolo-lexpre", "pendencias"}

    assert client.post(f"{FAV}/pendencias", headers=auth(signer)).status_code == 204
    assert client.post(f"{FAV}/protocolo-lexpre", headers=auth(signer)).status_code == 204

    assert client.get(FAV, headers=auth(signer)).json() == ["pendencias", "protocolo-lexpre"]


def test_favoritar_duas_vezes_nao_e_erro(client, signer, repo, hub_repo):
    repo.join(USER_ID)
    hub_repo.visible = {"pendencias"}
    client.post(f"{FAV}/pendencias", headers=auth(signer))
    assert client.post(f"{FAV}/pendencias", headers=auth(signer)).status_code == 204
    assert client.get(FAV, headers=auth(signer)).json() == ["pendencias"]


def test_desfavoritar(client, signer, repo, hub_repo):
    repo.join(USER_ID)
    hub_repo.visible = {"pendencias"}
    client.post(f"{FAV}/pendencias", headers=auth(signer))
    assert client.delete(f"{FAV}/pendencias", headers=auth(signer)).status_code == 204
    assert client.get(FAV, headers=auth(signer)).json() == []


def test_desfavoritar_o_que_nao_estava_nao_e_erro(client, signer, repo):
    repo.join(USER_ID)
    assert client.delete(f"{FAV}/pendencias", headers=auth(signer)).status_code == 204


def test_favoritar_o_que_nao_pode_ver_403_e_audita(client, signer, repo):
    """Dashboard inexistente, "em breve" ou sem acesso: mesma resposta."""
    repo.join(USER_ID)
    r = client.post(f"{FAV}/comissao", headers={**auth(signer), "User-Agent": "pytest"})
    assert r.status_code == 403
    assert r.json() == {"detail": "Sem acesso"}
    a = repo.audits[0]
    assert a.action == "dashboard.access_denied"
    assert a.org_id == repo.org_id
    assert a.target_id == "comissao"
    assert a.metadata == {"org": "lexgroup", "action": "favorite"}


def test_favoritos_de_org_de_que_nao_e_membro_403(client, signer, repo):
    assert client.get(FAV, headers=auth(signer)).status_code == 403
    assert client.post(f"{FAV}/pendencias", headers=auth(signer)).status_code == 403
    assert repo.audits[0].action == "org.access_denied"


def test_key_invalida_422(client, signer, repo):
    repo.join(USER_ID)
    assert client.post(f"{FAV}/Key_Maiuscula", headers=auth(signer)).status_code == 422


# --- Ordem dos cards -------------------------------------------------------


def test_sem_ordem_salva_lista_vazia(client, signer, repo):
    repo.join(USER_ID)
    r = client.get(ORDER, headers=auth(signer))
    assert r.status_code == 200
    assert r.json() == []


def test_salvar_e_ler_ordem(client, signer, repo):
    repo.join(USER_ID)
    keys = ["pendencias", "protocolo-lexpre"]
    assert client.put(ORDER, json=keys, headers=auth(signer)).status_code == 204
    assert client.get(ORDER, headers=auth(signer)).json() == keys


def test_ordem_sem_repetidos(client, signer, repo, hub_repo):
    repo.join(USER_ID)
    client.put(ORDER, json=["a1", "b1", "a1"], headers=auth(signer))
    assert hub_repo.orders[(USER_ID, repo.org_id)] == ["a1", "b1"]


def test_ordem_com_key_invalida_422(client, signer, repo):
    repo.join(USER_ID)
    assert client.put(ORDER, json=["ok-key", "NAO OK"], headers=auth(signer)).status_code == 422


def test_ordem_grande_demais_422(client, signer, repo):
    repo.join(USER_ID)
    keys = [f"k{i}" for i in range(201)]
    assert client.put(ORDER, json=keys, headers=auth(signer)).status_code == 422


def test_ordem_que_nao_e_lista_422(client, signer, repo):
    repo.join(USER_ID)
    assert client.put(ORDER, json={"keys": []}, headers=auth(signer)).status_code == 422


def test_ordem_de_org_de_que_nao_e_membro_403(client, signer, repo):
    assert client.put(ORDER, json=[], headers=auth(signer)).status_code == 403


def test_clean_order():
    assert clean_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]
    assert clean_order([]) == []
