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
                "source_disabled": False,
                "max_delay_min": 60,
                "can_export": True,
                "can_see_commission": True,
                "disabled_units": [],
                "can_toggle": False,
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


def test_dev_ve_as_unidades_desligadas(client, signer, repo, catalog_repo):
    """Desligado numa unidade: o card do Dev mostra a unidade e a marca em disabled_units."""
    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row(unit="NG", can_toggle=True))
    catalog_repo.add(USER_ID, repo.org_id, row(unit="LA", enabled=False, can_toggle=True))

    card = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"][0]

    assert card["units"] == ["NG", "LA"]
    assert card["disabled_units"] == ["LA"]
    assert card["can_toggle"] is True


def test_ligar_desligar_dashboard(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    r = client.put(
        "/orgs/lexgroup/units/LA/dashboards/protocolo-lexpre/enabled",
        json={"enabled": False},
        headers=auth(signer),
    )
    assert r.status_code == 200
    assert r.json() == {"unit": "LA", "dashboard": "protocolo-lexpre", "enabled": False}
    assert catalog_repo.switched == [(USER_ID, "lexgroup", "LA", "protocolo-lexpre", False)]


def test_ligar_desligar_sem_permissao_403(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    catalog_repo.allowed = False
    r = client.put(
        "/orgs/lexgroup/units/LA/dashboards/protocolo-lexpre/enabled",
        json={"enabled": False},
        headers=auth(signer),
    )
    assert r.status_code == 403
    assert r.json() == {"detail": "Só o Desenvolvedor liga e desliga dashboards."}


def test_ligar_desligar_dashboard_inexistente_404(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    catalog_repo.missing = True
    r = client.put(
        "/orgs/lexgroup/units/LA/dashboards/nao-existe/enabled",
        json={"enabled": True},
        headers=auth(signer),
    )
    assert r.status_code == 404


def test_ligar_desligar_sem_login_401(client):
    r = client.put(
        "/orgs/lexgroup/units/LA/dashboards/protocolo-lexpre/enabled", json={"enabled": False}
    )
    assert r.status_code == 401


def test_card_mostra_quando_o_dado_veio_do_banco(client, signer, repo, catalog_repo):
    """Com a query do dashboard no cache, o card ganha synced_at ("Atualizado há X min")."""
    from app.source_cache import Entry

    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row())  # protocolo-lexpre
    catalog_repo.add(USER_ID, repo.org_id, row(key="pendencias-lexpre", title="Pendências"))
    cache = client.app.state.source_cache
    cache._store.set("lexpre:log_setor_demanda_lexpre_NG", Entry([], 1_762_869_600.0))

    cards = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"]

    assert cards[0]["synced_at"] == "2025-11-11T14:00:00Z"
    # Pendências tem a query do log no cache (a setor_func ainda não): conta o que está no cache.
    assert cards[1]["synced_at"] == "2025-11-11T14:00:00Z"


def test_card_sem_nenhuma_query_no_cache_fica_sem_hora(client, signer, repo, catalog_repo):
    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row(key="pendencias-lexpre", title="Pendências"))

    cards = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"]

    assert cards[0]["synced_at"] is None


def test_card_usa_o_dado_mais_antigo_entre_as_queries_no_cache(client, signer, repo, catalog_repo):
    """Recursal: 12 queries das três unidades; com só as da NG no cache, o card já mostra a hora."""
    from app.source_cache import Entry

    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row(key="recursal", title="Recursal"))
    cache = client.app.state.source_cache
    cache._store.set("lexflow:setor_recurso_NG", Entry([], 1_762_869_600.0))  # 14:00
    cache._store.set("lexflow:agendamentos_setor_recursos_NG", Entry([], 1_762_873_200.0))  # 15:00

    cards = client.get("/orgs/lexgroup/dashboards", headers=auth(signer)).json()["available"]

    assert cards[0]["synced_at"] == "2025-11-11T14:00:00Z"


# --- Fonte desligada no card -----------------------------------------------------------------------


class _Disabled:
    def __init__(self, keys: set[str] | None):
        self.keys = keys  # None = o banco da plataforma não respondeu

    async def disabled_keys(self) -> set[str]:
        if self.keys is None:
            raise ConnectionError("plataforma fora")
        return self.keys


def _cards_with_switch(client, signer, repo, catalog_repo, disabled):
    from app.source_switch import SourceSwitch

    repo.join(USER_ID)
    catalog_repo.add(USER_ID, repo.org_id, row())  # protocolo-lexpre: lexpre (do .env)
    catalog_repo.add(
        USER_ID,
        repo.org_id,
        row(key="meta-anual", title="Meta anual", source="Planilha do financeiro"),
    )
    client.app.state.source_switch = SourceSwitch(_Disabled(disabled))
    r = client.get("/orgs/lexgroup/dashboards", headers=auth(signer))
    assert r.status_code == 200
    return {c["key"]: c for c in r.json()["available"]}


def test_card_diz_que_a_fonte_dele_esta_desligada(client, signer, repo, catalog_repo):
    cards = _cards_with_switch(client, signer, repo, catalog_repo, {"sheets_financeiro_ng"})

    assert cards["meta-anual"]["source_disabled"] is True
    assert cards["protocolo-lexpre"]["source_disabled"] is False


def test_sem_a_lista_de_desligadas_o_hub_abre_normal(client, signer, repo, catalog_repo):
    """O dashboard confere de novo ao abrir (423); o hub nunca cai por causa disso."""
    cards = _cards_with_switch(client, signer, repo, catalog_repo, None)

    assert not any(c["source_disabled"] for c in cards.values())
