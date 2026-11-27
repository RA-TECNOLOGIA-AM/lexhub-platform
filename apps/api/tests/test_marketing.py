"""Marketing (LexPre): o cálculo da v1 (/marketing_lexpre_NG e _LA) na casca da V2.

LexPre é a fonte principal (perfil, comercial, log de setor); o Facebook Ads vem do banco ng, que só a NG tem
ligado: na LA os indicadores de anúncio ficam zerados, como já ficavam na v1 (só campanhas "[LA]").
"""

import csv
import io
import uuid
from datetime import date

from app.dashboards import DASHBOARDS
from app.dashboards.marketing_lexpre import FILTROS, selection_pairs
from conftest import USER_ID


def auth(signer) -> dict:
    return {"Authorization": f"Bearer {signer.token()}"}


def url(unit: str, sufixo: str = "") -> str:
    return f"/orgs/lexgroup/units/{unit}/dashboards/marketing-lexpre{sufixo}"


def perfil(atendimento: int, escritorio: int, entrada: date, genero: str, **extra) -> dict:
    return {
        "escritorio_id": escritorio,
        "ATENDIMENTO": atendimento,
        "ENTRADA": entrada,
        "NASCIMENTO": date(1990, 1, 1),
        "GENERO": genero,
        "CANAL_AQUISICAO": "CAMPANHA",
        "TIPO_TRAFEGO": "PAGO",
        "PROSPECCAO": "PASSIVA",
        **extra,
    }


def anuncio(dia: date, gasto: float, campanha: str = "Campanha NG") -> dict:
    return {
        "date": dia,
        "campaign": campanha,
        "ad_id": "ad-1",
        "valor_gasto": gasto,
        "cliques_no_link": 10,
        "landing_page_view": 5,
        "leads": 2,
    }


def _pronto(repo, sources, unit: str = "NG", escritorio: str = "1", com_ng: bool = True) -> None:
    repo.units.setdefault(("lexgroup", unit), str(uuid.uuid4()))
    repo.grant(USER_ID, unit, "marketing-lexpre", "all")
    unidade = repo.units[("lexgroup", unit)]
    repo.unit_refs[(unidade, "lexpre")] = escritorio
    if com_ng:
        repo.unit_refs[(unidade, "ng")] = unit
    sources.data["perfil_clientes_lexpre"] = [
        perfil(1, 1, date(2026, 11, 3), "FEMININO", PS_OCUPACAO="AUTÔNOMO"),
        perfil(2, 1, date(2026, 11, 4), "MASCULINO"),
        perfil(3, 1, date(2026, 10, 1), "FEMININO"),  # fora do período
        perfil(4, 2, date(2026, 11, 5), "FEMININO"),  # escritório LAAM
    ]
    sources.data["comercial_lexpre_NG"] = []
    sources.data["demanda_rubrica_reunida_lexpre_NG"] = []
    sources.data["log_setor_demanda_lexpre_NG"] = []
    sources.data["facebook_ads"] = [
        anuncio(date(2026, 11, 2), 100.0),
        anuncio(date(2026, 11, 3), 50.5),
        anuncio(date(2026, 10, 2), 999.0),  # fora do período
    ]


def test_ng_recorta_o_escritorio_e_soma_o_facebook_do_banco_ng(client, signer, repo, sources):
    _pronto(repo, sources)
    r = client.get(url("NG") + "?from=2026-11-01&to=2026-11-11", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["source"] == "LexPre"
    assert body["dashboard"] == "marketing_lexpre_NG"
    s = body["stats"]
    assert s["marketing_lexpre_ng_total_clientes"] == 2  # só escritório 1, no período
    assert s["marketing_lexpre_ng_triados_total_clientes"] == 1  # só o que respondeu a pesquisa
    assert s["marketing_lexpre_ng_facebook_valor_gasto"] == 150.5
    assert s["marketing_lexpre_ng_facebook_cliques"] == 20
    generos = {p["name"]: p["value"] for p in body["charts"]["marketing_lexpre_ng_genero"]}
    assert generos == {"FEMININO": 1, "MASCULINO": 1}


def test_la_sem_banco_ng_zera_os_anuncios_e_nao_le_o_ng(client, signer, repo, sources):
    _pronto(repo, sources, unit="LA", escritorio="2", com_ng=False)
    r = client.get(url("LA") + "?from=2026-11-01&to=2026-11-11", headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["dashboard"] == "marketing_lexpre_LA"
    assert body["stats"]["marketing_lexpre_ng_total_clientes"] == 1  # só o do escritório 2
    assert body["stats"]["marketing_lexpre_ng_facebook_valor_gasto"] == 0


def test_filtro_clicavel_vira_o_par_da_v1(client, signer, repo, sources):
    _pronto(repo, sources)
    r = client.get(
        url("NG") + "?from=2026-11-01&to=2026-11-11&genero_marketing=FEMININO",
        headers=auth(signer),
    )
    assert r.status_code == 200, r.text
    assert r.json()["stats"]["marketing_lexpre_ng_total_clientes"] == 1


def test_selection_pairs_traduz_os_filtros_para_as_dimensoes_da_v1():
    assert selection_pairs({"genero_marketing": ["F"], "rubrica_marketing": ["MORA", "CESTA"]}) == [
        ("genero", "F"),
        ("rubrica", "MORA"),
        ("rubrica", "CESTA"),
    ]
    assert set(DASHBOARDS["marketing-lexpre"].filters) == set(FILTROS)


def _csv(r) -> list[list[str]]:
    return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))


def test_exporta_leads_e_facebook_ads(client, signer, repo, sources):
    _pronto(repo, sources)
    repo.exporters.add(USER_ID)
    base = url("NG", "/export") + "?from=2026-11-01&to=2026-11-11"

    r = client.get(base, headers=auth(signer))
    assert r.status_code == 200, r.text
    assert _csv(r)[0][0] == "ID do Atendimento"

    r = client.get(
        base + "&relatorio=facebook&detalhamento=campanha&campos=campanha&campos=valor_gasto",
        headers=auth(signer),
    )
    assert r.status_code == 200, r.text
    assert _csv(r) == [["Campanha", "Valor Gasto (R$)"], ["Campanha NG", "150.5"]]


# --- Marketing (banco NG): o mesmo handler da v1, com os filtros por dimensão ---


def test_marketing_ng_filtro_por_dimensao_e_graficos(client, signer, repo, sources):
    from app.dashboards.marketing import selecao

    repo.grant(USER_ID, "NG", "marketing", "all")
    repo.unit_refs[(repo.units[("lexgroup", "NG")], "ng")] = "NG"
    sources.data["perfil_clientes_NG"] = [
        {"ASSINATURA": date(2026, 11, 3), "GENERO": "FEMININO", "NASCIMENTO": date(1990, 1, 1)},
        {"ASSINATURA": date(2026, 11, 4), "GENERO": "MASCULINO", "NASCIMENTO": date(1980, 1, 1)},
        {"ASSINATURA": date(2026, 10, 4), "GENERO": "MASCULINO"},  # fora do período
    ]
    base = "/orgs/lexgroup/units/NG/dashboards/marketing?from=2026-11-01&to=2026-11-11"

    r = client.get(base, headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["stats"]["marketing_ng_total_clientes"] == 2
    generos = {p["name"]: p["value"] for p in body["marketing_ng_genero"]}
    assert generos == {"FEMININO": 1, "MASCULINO": 1}

    r = client.get(base + "&genero_marketing=FEMININO", headers=auth(signer))
    assert r.json()["stats"]["marketing_ng_total_clientes"] == 1

    assert selecao({"dispositivo_marketing": ["Mobile"], "rubrica_marketing": ["MORA", "CESTA"]}) == (
        ["rubrica", "rubrica", "dispositivo"],
        ["MORA", "CESTA", "Mobile"],
    )


# --- Marketing (banco NG) + LexPre: a soma do comercial que passou para o LexPre ---


def test_soma_lexpre_regras():
    from app.dashboards.marketing_soma_lexpre import somar_lexpre

    ng = {
        "stats": {
            "marketing_ng_total_clientes": 10,
            "marketing_ng_media_idade": 40.0,
            "marketing_ng_facebook_valor_gasto": 1000.0,
            "marketing_ng_facebook_cac_campanha": 100.0,  # 10 clientes de campanha
            "marketing_ng_facebook_roas_campanha": 2.0,
            "marketing_ng_campanha_ng": 5,
            "marketing_ng_leads_ng": 50,
            "marketing_ng_acoes_ng": 8,
            "marketing_ng_valor_causa_ng": 800.0,
            "marketing_ng_facebook_cliques": 300,
        },
        "marketing_ng_genero": [{"name": "FEMININO", "value": 6}, {"name": "MASCULINO", "value": 4}],
        "marketing_ng_rubrica_campanha": [{"name": "MORA", "ra": 1, "ng": 2}],
        "marketing_ng_ind_rubricas": [{"name": "MORA", "value": 2}],
        "marketing_ng_total_clientes_campanha": [{"name": "NG", "value": 5}, {"name": "Total", "value": 10}],
        "marketing_ng_funil_pipeline": [{"name": "ASSINADO", "value": 3}],
    }
    lexpre = {
        "stats": {
            "marketing_lexpre_ng_total_clientes": 30,
            "marketing_lexpre_ng_media_idade": 44.0,
            "marketing_lexpre_ng_facebook_valor_gasto": 1000.0,
            "marketing_lexpre_ng_facebook_cac_campanha": 25.0,  # 40 clientes de campanha
            "marketing_lexpre_ng_facebook_roas_campanha": 3.0,
            "marketing_lexpre_ng_campanha": 15,
            "marketing_lexpre_ng_leads_campanha": 150,
            "marketing_lexpre_ng_acoes_campanha": 12,
            "marketing_lexpre_ng_valor_causa_campanha": 1200.0,
            "marketing_lexpre_ng_facebook_cliques": 300,
        },
        "charts": {
            "marketing_lexpre_ng_genero": [{"name": "feminino", "value": 20}, {"name": "OUTRO", "value": 1}],
            "marketing_lexpre_ng_rubrica_campanha": [{"name": "MORA", "value": 5}, {"name": "CESTA", "value": 4}],
            "marketing_lexpre_ng_total_clientes_campanha": [
                {"name": "Campanha", "value": 15},
                {"name": "Total", "value": 30},
            ],
            "marketing_lexpre_ng_investimento_cliques_leads": [{"name": "01/11", "investimento": 9}],
        },
    }
    r = somar_lexpre(ng, lexpre)
    s = r["stats"]
    assert s["marketing_ng_total_clientes"] == 40
    assert s["marketing_ng_media_idade"] == 43.0  # (40*10 + 44*30) / 40
    assert s["marketing_ng_facebook_valor_gasto"] == 1000.0  # mesma tabela: não soma
    assert s["marketing_ng_facebook_cliques"] == 300
    assert s["marketing_ng_facebook_cac_campanha"] == 20.0  # 1000 / (10 + 40)
    assert s["marketing_ng_facebook_roas_campanha"] == 5.0
    assert s["marketing_ng_campanha_ng"] == 20
    assert s["marketing_ng_conversao_ng"] == 10.0  # 20 / 200
    assert s["marketing_ng_ticket_medio_ng"] == 100.0  # 2000 / 20 ações (regra do legado)
    assert s["marketing_ng_cpl_ng"] == 5.0
    assert r["marketing_ng_genero"] == [
        {"name": "FEMININO", "value": 26},
        {"name": "MASCULINO", "value": 4},
        {"name": "OUTRO", "value": 1},
    ]
    assert r["marketing_ng_rubrica_campanha"] == [
        {"name": "MORA", "ra": 1, "ng": 7},
        {"name": "CESTA", "ra": 0, "ng": 4},
    ]
    assert {p["name"]: p["value"] for p in r["marketing_ng_ind_rubricas"]} == {"MORA": 7, "CESTA": 4}
    assert {p["name"]: p["value"] for p in r["marketing_ng_total_clientes_campanha"]} == {"NG": 20, "Total": 40}
    assert r["marketing_ng_funil_pipeline"] == [{"name": "ASSINADO", "value": 3}]  # só o legado tem
    assert "marketing_ng_investimento_cliques_leads" not in r


def _ng_com_lexpre(repo, sources):
    repo.grant(USER_ID, "NG", "marketing", "all")
    unidade = repo.units[("lexgroup", "NG")]
    repo.unit_refs[(unidade, "ng")] = "NG"
    repo.unit_refs[(unidade, "lexpre")] = "1"
    sources.data["perfil_clientes_NG"] = [
        {"ASSINATURA": date(2026, 10, 3), "GENERO": "FEMININO", "NASCIMENTO": date(1990, 1, 1)},
    ]
    sources.data["perfil_clientes_lexpre"] = [
        perfil(1, 1, date(2026, 11, 3), "FEMININO"),
        perfil(2, 1, date(2026, 11, 4), "MASCULINO"),
        perfil(4, 2, date(2026, 11, 5), "FEMININO"),  # LA: fora
    ]
    for q in ("comercial_lexpre_NG", "demanda_rubrica_reunida_lexpre_NG", "log_setor_demanda_lexpre_NG"):
        sources.data[q] = []


def test_marketing_ng_soma_o_lexpre_da_ng(client, signer, repo, sources):
    _ng_com_lexpre(repo, sources)
    base = "/orgs/lexgroup/units/NG/dashboards/marketing?from=2026-10-01&to=2026-11-11"
    r = client.get(base, headers=auth(signer))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lexpre"] == {"somado": True, "motivo": None}
    assert body["stats"]["marketing_ng_total_clientes"] == 3  # 1 do legado + 2 do LexPre (NG)
    assert {p["name"]: p["value"] for p in body["marketing_ng_genero"]} == {"FEMININO": 2, "MASCULINO": 1}

    # Filtro de dispositivo: o LexPre não tem, então só o legado.
    r = client.get(base + "&dispositivo_marketing=Mobile", headers=auth(signer))
    assert r.json()["lexpre"]["somado"] is False


def test_marketing_ng_sem_lexpre_ligado_fica_so_com_o_legado(client, signer, repo, sources):
    _ng_com_lexpre(repo, sources)
    del repo.unit_refs[(repo.units[("lexgroup", "NG")], "lexpre")]
    r = client.get("/orgs/lexgroup/units/NG/dashboards/marketing?from=2026-10-01&to=2026-11-11", headers=auth(signer))
    body = r.json()
    assert body["lexpre"]["somado"] is False
    assert body["stats"]["marketing_ng_total_clientes"] == 1


# --- Facebook Ads das contas da Meta conectadas na unidade (app/dashboards/anuncios_meta.py) ---------------------


def _conta_meta(repo, sources, unit: str, key: str, linhas: list[dict]) -> None:
    """Uma conta de anúncios conectada na unidade (app.unit_source_refs, key 'fb_...', ref '*')."""
    repo.unit_refs[(repo.units[("lexgroup", unit)], key)] = "*"
    sources.by_db[key] = {"facebook_ads": linhas}


def test_ng_com_contas_da_meta_le_as_contas_e_nao_o_banco_ng(client, signer, repo, sources):
    _pronto(repo, sources)
    _conta_meta(repo, sources, "NG", "fb_ng_aaa111", [anuncio(date(2026, 11, 2), 300.0)])
    _conta_meta(repo, sources, "NG", "fb_ng_bbb222", [anuncio(date(2026, 11, 3), 25.0)])
    r = client.get(url("NG") + "?from=2026-11-01&to=2026-11-11", headers=auth(signer))
    assert r.status_code == 200, r.text
    s = r.json()["stats"]
    assert s["marketing_lexpre_ng_facebook_valor_gasto"] == 325.0  # as duas contas, nada do banco ng (150,5)
    assert s["marketing_lexpre_ng_facebook_cliques"] == 20


def test_la_com_conta_da_meta_tem_os_anuncios_sem_o_recorte_la(client, signer, repo, sources):
    # Na v1 a LA só via campanhas "[LA]" do banco ng (nenhuma): com a conta dela, entra tudo da conta.
    _pronto(repo, sources, unit="LA", escritorio="2", com_ng=False)
    _conta_meta(repo, sources, "LA", "fb_la_ccc333", [anuncio(date(2026, 11, 4), 80.0, "Campanha LA")])
    r = client.get(url("LA") + "?from=2026-11-01&to=2026-11-11", headers=auth(signer))
    assert r.status_code == 200, r.text
    assert r.json()["stats"]["marketing_lexpre_ng_facebook_valor_gasto"] == 80.0


def test_conta_da_meta_desligada_fica_de_fora_e_o_resto_segue(client, signer, repo, sources):
    _pronto(repo, sources)
    _conta_meta(repo, sources, "NG", "fb_ng_aaa111", [anuncio(date(2026, 11, 2), 300.0)])
    _conta_meta(repo, sources, "NG", "fb_ng_bbb222", [anuncio(date(2026, 11, 3), 25.0)])
    sources.disabled.add("fb_ng_aaa111")
    r = client.get(url("NG") + "?from=2026-11-01&to=2026-11-11", headers=auth(signer))
    assert r.status_code == 200, r.text
    s = r.json()["stats"]
    assert s["marketing_lexpre_ng_facebook_valor_gasto"] == 25.0
    assert s["marketing_lexpre_ng_total_clientes"] == 2


def test_exporta_o_facebook_ads_das_contas_da_meta(client, signer, repo, sources):
    _pronto(repo, sources)
    repo.exporters.add(USER_ID)
    _conta_meta(repo, sources, "NG", "fb_ng_aaa111", [anuncio(date(2026, 11, 2), 300.0, "Meta")])
    r = client.get(
        url("NG", "/export")
        + "?from=2026-11-01&to=2026-11-11&relatorio=facebook&detalhamento=campanha"
        + "&campos=campanha&campos=valor_gasto",
        headers=auth(signer),
    )
    assert r.status_code == 200, r.text
    assert _csv(r) == [["Campanha", "Valor Gasto (R$)"], ["Meta", "300.0"]]


def test_marketing_ng_le_o_facebook_das_contas_da_meta(client, signer, repo, sources):
    _ng_com_lexpre(repo, sources)
    sources.data["facebook_ads"] = [anuncio(date(2026, 10, 5), 999.0)]  # banco ng: não entra
    _conta_meta(repo, sources, "NG", "fb_ng_aaa111", [anuncio(date(2026, 10, 5), 400.0)])
    base = "/orgs/lexgroup/units/NG/dashboards/marketing?from=2026-10-01&to=2026-11-11"
    r = client.get(base, headers=auth(signer))
    assert r.status_code == 200, r.text
    s = r.json()["stats"]
    assert s["marketing_ng_facebook_valor_gasto"] == 400.0
    assert s["marketing_ng_facebook_cliques"] == 10


def test_conta_da_meta_carregando_o_historico_deixa_a_unidade_no_banco_ng(client, signer, repo, sources):
    # Uma conta pela metade daria o gasto pela metade: enquanto alguma carrega, nenhuma entra.
    _pronto(repo, sources)
    _conta_meta(repo, sources, "NG", "fb_ng_aaa111", [anuncio(date(2026, 11, 2), 300.0)])
    _conta_meta(repo, sources, "NG", "fb_ng_bbb222", [anuncio(date(2026, 11, 3), 25.0)])
    sources.loading.add("fb_ng_bbb222")
    r = client.get(url("NG") + "?from=2026-11-01&to=2026-11-11", headers=auth(signer))
    assert r.status_code == 200, r.text
    assert r.json()["stats"]["marketing_lexpre_ng_facebook_valor_gasto"] == 150.5  # o banco ng
