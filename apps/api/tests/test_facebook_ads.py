import asyncio
import json
from datetime import date
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

from app.facebook_ads import (
    CONVERSATION_TYPE,
    AdsSettings,
    AdsSettingsIn,
    GraphClient,
    GraphError,
    GraphUnavailable,
    account_options,
    check_account,
    normalize_account,
    parse_breakdown_row,
    parse_entity,
    parse_row,
    preview,
    token_info,
)

TOKEN = "EAAB" + "t" * 60


class FakeGraph:
    """Graph API falsa: responde por caminho; guarda cada pedido para conferir cabeçalho e parâmetros."""

    def __init__(self, routes):
        self.routes = routes  # caminho -> resposta (dict, (status, dict), callable ou exceção)
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.removeprefix("/v26.0")
        answer = self.routes[path]
        if callable(answer):
            answer = answer(request)
        if isinstance(answer, Exception):
            raise answer
        status, body = answer if isinstance(answer, tuple) else (200, answer)
        return httpx.Response(status, json=body)

    def client(self, token=TOKEN, **kwargs) -> GraphClient:
        return GraphClient(token, transport=httpx.MockTransport(self.handler), **kwargs)


def error(code, subcode=None, status=400, message="erro"):
    return (status, {"error": {"code": code, "error_subcode": subcode, "message": message}})


def run(coro):
    return asyncio.run(coro)


ACCOUNT = {
    "name": "NG Anúncios",
    "currency": "BRL",
    "timezone_name": "America/Manaus",
    "account_status": 1,
}
WEEK = {"data": [{"spend": "1234.5", "impressions": "98765"}]}
ME = {"id": "1", "name": "Coletor LexHub"}


def test_normalize_account():
    assert normalize_account("act_123") == "act_123"
    assert normalize_account(" 123 456 ") == "act_123456"
    assert normalize_account("act_") is None
    assert normalize_account("conta 1") is None
    assert normalize_account("") is None


def test_token_vai_no_cabecalho_e_nunca_na_url():
    graph = FakeGraph({"/me": ME})

    async def go():
        async with graph.client(app_secret="segredo") as c:
            await c.me()

    run(go())
    req = graph.requests[0]
    assert req.headers["Authorization"] == f"Bearer {TOKEN}"
    assert TOKEN not in str(req.url)
    assert len(req.url.params["appsecret_proof"]) == 64  # HMAC-SHA256 do token com a chave do app


def test_erros_da_meta_viram_tipos():
    graph = FakeGraph(
        {
            "/me": error(190, status=401),
            "/act_1": error(100, 33),
            "/act_2": error(17),
            "/act_3": error(10, status=403),
            "/act_4": error(1, message="Please reduce the amount of data you're asking for"),
            "/act_5": httpx.ConnectTimeout("lento"),
        }
    )

    async def go():
        kinds = []
        async with graph.client() as c:
            for path in ("/me", "/act_1", "/act_2", "/act_3", "/act_4"):
                with pytest.raises(GraphError) as exc:
                    await c.get(path)
                kinds.append(exc.value.kind)
            with pytest.raises(GraphUnavailable):
                await c.get("/act_5")
        return kinds

    assert run(go()) == ["token", "not_found", "throttle", "permission", "too_much"]


def test_relatorio_segue_as_paginas_e_filtra_campanhas():
    pages = iter(
        [
            {"data": [{"ad_id": "1"}], "paging": {"cursors": {"after": "AA"}, "next": "https://x"}},
            {"data": [{"ad_id": "2"}], "paging": {"cursors": {"after": "BB"}}},
        ]
    )
    graph = FakeGraph({"/act_9/insights": lambda req: next(pages)})

    async def go():
        async with graph.client() as c:
            return await c.report(
                "act_9",
                level="ad",
                fields="ad_id",
                since=date(2026, 11, 1),
                until=date(2026, 11, 2),
                daily=True,
                breakdowns=("age", "gender"),
                campaigns=["11", "22"],
            )

    assert [r["ad_id"] for r in run(go())] == ["1", "2"]
    first, second = (r.url.params for r in graph.requests)
    assert first["level"] == "ad" and first["time_increment"] == "1" and "after" not in first
    assert first["breakdowns"] == "age,gender"
    assert json.loads(first["time_range"]) == {"since": "2026-11-01", "until": "2026-11-02"}
    assert json.loads(first["filtering"]) == [
        {"field": "campaign.id", "operator": "IN", "value": ["11", "22"]}
    ]
    assert second["after"] == "AA"


def test_relatorio_divide_o_periodo_quando_a_meta_pede_menos_dados():
    def answer(req):
        span = json.loads(req.url.params["time_range"])
        if span["since"] != span["until"]:
            return error(1, message="Please reduce the amount of data")
        return {"data": [{"ad_id": "1", "date_start": span["since"]}]}

    graph = FakeGraph({"/act_9/insights": answer})

    async def go():
        async with graph.client() as c:
            return await c.report(
                "act_9", level="ad", fields="x", since=date(2026, 11, 1), until=date(2026, 11, 4)
            )

    assert [r["date_start"] for r in run(go())] == [
        "2026-11-01",
        "2026-11-02",
        "2026-11-03",
        "2026-11-04",
    ]


def test_relatorio_divide_o_periodo_quando_a_meta_nao_responde_a_tempo():
    def answer(req):
        span = json.loads(req.url.params["time_range"])
        if span["since"] != span["until"]:
            raise httpx.ReadTimeout("lento", request=req)
        return {"data": [{"ad_id": "1", "date_start": span["since"]}]}

    graph = FakeGraph({"/act_9/insights": answer})

    async def go():
        async with graph.client() as c:
            return await c.report(
                "act_9", level="ad", fields="x", since=date(2026, 11, 1), until=date(2026, 11, 3)
            )

    assert [r["date_start"] for r in run(go())] == ["2026-11-01", "2026-11-02", "2026-11-03"]


def test_relatorio_de_um_dia_que_nao_responde_a_tempo_vira_erro():
    def answer(req):
        raise httpx.ReadTimeout("lento", request=req)

    graph = FakeGraph({"/act_9/insights": answer})

    async def go():
        async with graph.client() as c:
            return await c.report(
                "act_9", level="ad", fields="x", since=date(2026, 11, 1), until=date(2026, 11, 1)
            )

    with pytest.raises(GraphUnavailable) as exc:
        run(go())
    assert exc.value.timeout
    assert len(graph.requests) == 1


def test_rede_fora_nao_divide_o_periodo():
    def answer(req):
        raise httpx.ConnectError("sem rede", request=req)

    graph = FakeGraph({"/act_9/insights": answer})

    async def go():
        async with graph.client() as c:
            return await c.report(
                "act_9", level="ad", fields="x", since=date(2026, 11, 1), until=date(2026, 11, 30)
            )

    with pytest.raises(GraphUnavailable) as exc:
        run(go())
    assert not exc.value.timeout
    assert len(graph.requests) == 1


def test_lista_pede_paginas_menores_quando_a_meta_pede_menos_dados():
    # Anúncios com o criativo: a Meta recusa a página de 500 e aceita a de 100; o cursor continua.
    def answer(req):
        limit, after = int(req.url.params["limit"]), req.url.params.get("after")
        if limit > 100:
            return error(1, status=500, message="Please reduce the amount of data")
        if after is None:
            return {"data": [{"id": "1"}], "paging": {"cursors": {"after": "AA"}, "next": "x"}}
        return {"data": [{"id": "2"}], "paging": {"cursors": {"after": "BB"}}}

    graph = FakeGraph({"/act_9/ads": answer})

    async def go():
        async with graph.client() as c:
            return await c.entities("act_9", "ad", creatives=True)

    assert [r["id"] for r in run(go())] == ["1", "2"]
    sent = [(r.url.params["limit"], r.url.params.get("after")) for r in graph.requests]
    assert sent == [("500", None), ("100", None), ("100", "AA")]


def test_lista_desiste_quando_nem_a_menor_pagina_passa():
    graph = FakeGraph({"/act_9/ads": error(1, status=500, message="Please reduce the amount")})

    async def go():
        async with graph.client() as c:
            return await c.entities("act_9", "ad", creatives=True)

    with pytest.raises(GraphError) as exc:
        run(go())
    assert exc.value.kind == "too_much"
    assert [r.url.params["limit"] for r in graph.requests] == ["500", "100", "25"]


ROW = {
    "date_start": "2026-11-25",
    "account_id": "123",
    "account_currency": "BRL",
    "campaign_id": "11",
    "ad_id": "120200000000001",
    "ad_name": "Anúncio",
    "spend": "150.256",
    "impressions": "10000",
    "reach": "8000",
    "frequency": "1.25",
    "clicks": "320",
    "inline_link_clicks": "210",
    "outbound_clicks": [{"action_type": "outbound_click", "value": "190"}],
    "actions": [
        {"action_type": "onsite_conversion.lead_grouped", "value": "7"},
        {"action_type": "offsite_conversion.fb_pixel_lead", "value": "2"},
        {"action_type": "landing_page_view", "value": "180"},
        {"action_type": CONVERSATION_TYPE, "value": "5"},
    ],
    "video_thruplay_watched_actions": [{"action_type": "video_view", "value": "40"}],
    "quality_ranking": "ABOVE_AVERAGE",
    "engagement_rate_ranking": "UNKNOWN",
}


def test_parse_row_resultados_e_grupos_de_metricas():
    basic = parse_row(ROW, AdsSettings(metrics=(), conversions=("lead", CONVERSATION_TYPE)))
    assert basic["day"] == date(2026, 11, 25) and basic["spend"] == Decimal("150.26")
    assert (basic["impressions"], basic["clicks"], basic["link_clicks"]) == (10000, 320, 210)
    assert (basic["leads"], basic["conversations"], basic["landing_page_views"]) == (9, 5, 180)
    assert basic["outbound_clicks"] == 190
    # 'lead' não veio agregado: resultados soma só o que foi escolhido
    assert basic["results"] == Decimal(5)
    assert basic["frequency"] is None and basic["video_thruplays"] is None
    assert basic["quality_ranking"] is None

    full = parse_row(
        ROW,
        AdsSettings(
            metrics=("reach", "video", "quality"),
            conversions=("onsite_conversion.lead_grouped", CONVERSATION_TYPE),
        ),
    )
    assert full["results"] == Decimal(12) and full["reach"] == 8000
    assert full["frequency"] == Decimal("1.2500") and full["video_thruplays"] == 40
    assert full["video_plays"] == 0
    assert full["quality_ranking"] == "ABOVE_AVERAGE" and full["engagement_ranking"] is None

    assert parse_row({"date_start": "2026-11-25"}) is None
    assert parse_row({"date_start": "ontem", "ad_id": "1"}) is None


def test_parse_breakdown_row_por_segmento():
    row = {**ROW, "age": "25-34", "gender": "female", "publisher_platform": "instagram"}
    settings = AdsSettings(conversions=("lead",))
    age = parse_breakdown_row(row, "age_gender", settings)
    assert (age["breakdown"], age["dim1"], age["dim2"], age["campaign_id"]) == (
        "age_gender",
        "25-34",
        "female",
        "11",
    )
    assert parse_breakdown_row(row, "platform", settings)["dim2"] == ""
    assert parse_breakdown_row({**row, "campaign_id": None}, "region", settings) is None


def test_parse_entity_orcamento_datas_e_criativo():
    camp = parse_entity(
        "campaign",
        {
            "id": "11",
            "name": "Captação",
            "objective": "OUTCOME_LEADS",
            "effective_status": "ACTIVE",
            "daily_budget": "5000",
            "start_time": "2026-11-01T10:00:00-0400",
        },
    )
    assert camp["daily_budget"] == Decimal("50.00") and camp["campaign_id"] == "11"
    assert (
        camp["start_time"].isoformat() == "2026-11-01T10:00:00-04:00" and camp["creative"] is None
    )
    ad = parse_entity(
        "ad",
        {
            "id": "33",
            "adset_id": "22",
            "campaign_id": "11",
            "creative": {
                "id": "9",
                "object_story_spec": {
                    "link_data": {
                        "name": "Fale com um advogado",
                        "message": "Atendimento hoje",
                        "link": "https://wa.me/55",
                        "picture": "https://img",
                        "call_to_action": {"type": "WHATSAPP_MESSAGE"},
                    }
                },
            },
        },
    )
    assert ad["creative"] == {
        "id": "9",
        "title": "Fale com um advogado",
        "body": "Atendimento hoje",
        "imageUrl": "https://img",
        "linkUrl": "https://wa.me/55",
        "callToAction": "WHATSAPP_MESSAGE",
    }
    assert parse_entity("ad", {"id": "x"}) is None


def test_settings_config_e_quando_refazer_o_historico():
    s = AdsSettings.from_config(
        {"ad_account_id": "act_1"}
    )  # fonte conectada antes da personalização
    assert s.conversions == ("lead", CONVERSATION_TYPE) and s.campaigns is None
    assert AdsSettings.from_config(s.to_config()) == s
    assert not s.needs_recollect(AdsSettings(conversions=("lead",), creatives=False))
    assert s.needs_recollect(AdsSettings(breakdowns=("region",)))
    assert s.needs_recollect(AdsSettings(campaigns=("11",)))
    assert s.needs_recollect(AdsSettings(backfill_days=90))
    assert "video_p25_watched_actions" in AdsSettings(metrics=("video",)).ad_fields()
    assert "reach" not in AdsSettings(metrics=("reach",)).breakdown_fields(with_reach=False)


def test_settings_da_tela_validados():
    ok = AdsSettingsIn(breakdowns=["region", "age_gender"], conversions=["lead", "lead"])
    s = ok.to_settings(3)
    assert s.breakdowns == ("age_gender", "region") and s.conversions == ("lead",)
    assert s.collect_version == 3
    with pytest.raises(ValidationError):
        AdsSettingsIn(campaigns=[])  # "só as escolhidas" sem nenhuma
    with pytest.raises(ValidationError):
        AdsSettingsIn(conversions=["lead; drop"])
    with pytest.raises(ValidationError):
        AdsSettingsIn(backfillDays=30)


def _factory(graph):
    return lambda token: graph.client(token)


def test_check_account_passa_com_a_conta_ativa():
    graph = FakeGraph({"/me": ME, "/act_1": ACCOUNT, "/act_1/insights": WEEK})
    result, info = run(check_account(_factory(graph), "act_1", TOKEN))
    assert result.ok and info.name == "NG Anúncios" and info.timezone == "America/Manaus"
    assert [c.key for c in result.checks] == ["network", "login", "read", "account"]
    assert "BRL 1.234,50 gastos e 98.765 impressões" in result.checks[2].message
    assert set(result.schema_cache) == {
        "app.facebook_ads_daily",
        "app.facebook_ads_breakdowns",
        "app.facebook_ads_entities",
    }


def test_check_account_conta_parada_e_aviso():
    graph = FakeGraph(
        {"/me": ME, "/act_1": {**ACCOUNT, "account_status": 2}, "/act_1/insights": {}}
    )
    result, info = run(check_account(_factory(graph), "act_1", TOKEN))
    assert result.ok and info is not None
    assert result.checks[3].severity == "warn" and "desativada" in result.checks[3].message


def test_check_account_token_recusado_ou_conta_sem_acesso():
    graph = FakeGraph({"/me": error(190, status=401)})
    result, info = run(check_account(_factory(graph), "act_1", TOKEN))
    assert not result.ok and info is None and result.error.startswith("A Meta recusou o token")
    assert [c.skipped for c in result.checks] == [False, False, True, True]

    graph = FakeGraph({"/me": ME, "/act_1": error(100, 33)})
    result, _ = run(check_account(_factory(graph), "act_1", TOKEN))
    assert not result.ok and "não achou essa conta" in result.error

    graph = FakeGraph({"/me": httpx.ConnectError("sem rede")})
    result, _ = run(check_account(_factory(graph), "act_1", TOKEN))
    assert not result.ok and result.checks[0].key == "network" and not result.checks[0].ok


def _insights(req):
    level = req.url.params["level"]
    if "breakdowns" in req.url.params:
        return {
            "data": [
                {"age": "25-34", "gender": "female", "spend": "30", "actions": []},
                {"age": "35-44", "gender": "male", "spend": "70", "actions": []},
            ]
        }
    if level == "campaign" and req.url.params["fields"] == "campaign_id,spend":
        return {"data": [{"campaign_id": "11", "spend": "300"}]}
    if level == "account" and req.url.params["fields"] == "actions":
        return {"data": [{"actions": [{"action_type": CONVERSATION_TYPE, "value": "12"}]}]}
    if level == "account":
        return {
            "data": [
                {
                    "date_start": "2026-11-19",
                    "date_stop": "2026-11-25",
                    "spend": "100",
                    "impressions": "5000",
                    "reach": "4000",
                    "actions": [{"action_type": "lead", "value": "4"}],
                }
            ]
        }
    if level == "campaign":
        return {
            "data": [
                {"campaign_id": "11", "campaign_name": "A", "spend": "40", "actions": []},
                {"campaign_id": "22", "campaign_name": "B", "spend": "60", "actions": []},
            ]
        }
    return {"data": [{"ad_id": "33", "ad_name": "Anúncio", "spend": "60", "actions": []}]}


CAMPAIGNS = {
    "data": [
        {"id": "22", "name": "Pausada", "effective_status": "PAUSED", "objective": "OUTCOME_LEADS"},
        {
            "id": "11",
            "name": "Captação",
            "effective_status": "ACTIVE",
            "objective": "OUTCOME_LEADS",
        },
    ]
}
ADS = {"data": [{"id": "33", "creative": {"id": "9", "title": "Fale conosco"}}]}


def test_opcoes_da_conta_campanhas_por_gasto_e_conversoes():
    graph = FakeGraph({"/act_1/campaigns": CAMPAIGNS, "/act_1/insights": _insights})

    async def go():
        async with graph.client() as c:
            return await account_options(c, "act_1")

    out = run(go())
    assert [c["id"] for c in out["campaigns"]] == ["11", "22"]
    assert out["campaigns"][0]["spend30"] == 300.0
    first = out["conversions"][0]
    assert first["type"] == CONVERSATION_TYPE and first["count30"] == 12
    assert "Conversas iniciadas" in first["label"]
    assert {"lead", "landing_page_view"} <= {c["type"] for c in out["conversions"]}


def test_previa_totais_campanhas_detalhamentos_e_criativos():
    graph = FakeGraph({"/act_1/insights": _insights, "/act_1/ads": ADS})
    settings = AdsSettings(metrics=("reach",), conversions=("lead",), breakdowns=("age_gender",))

    async def go():
        async with graph.client() as c:
            return await preview(c, "act_1", settings)

    out = run(go())
    assert (out["since"], out["until"]) == ("2026-11-19", "2026-11-25")
    assert out["totals"]["spend"] == 100.0 and out["totals"]["results"] == 4.0
    assert out["totals"]["reach"] == 4000 and out["totals"]["thruplays"] is None
    assert [c["id"] for c in out["campaigns"]] == ["22", "11"]
    assert out["breakdowns"][0]["key"] == "age_gender"
    assert out["breakdowns"][0]["rows"][0]["segment"] == ["35-44", "male"]
    assert out["ads"][0]["creative"] == {"id": "9", "title": "Fale conosco"}
    ads_request = next(r for r in graph.requests if r.url.path.endswith("/ads"))
    assert json.loads(ads_request.url.params["filtering"])[0]["field"] == "ad.id"


def _token_routes(perms, accounts=None, debug=None):
    routes = {
        "/me": ME,
        "/me/permissions": {"data": [{"permission": p, "status": st} for p, st in perms]},
        "/me/adaccounts": accounts
        or {
            "data": [
                {
                    "id": "act_2",
                    "name": "Zeta Parada",
                    "currency": "BRL",
                    "timezone_name": "America/Manaus",
                    "account_status": 2,
                    "amount_spent": "990",
                },
                {
                    "id": "act_1",
                    "name": "NG Anúncios",
                    "currency": "BRL",
                    "timezone_name": "America/Manaus",
                    "account_status": 1,
                    "amount_spent": "1234500",
                    "business": {"id": "9", "name": "LexGroup"},
                },
            ]
        },
        "/me/businesses": {"data": [{"id": "9", "name": "LexGroup"}]},
        # O negócio tem mais uma conta, não atribuída ao usuário do token; a de clientes não abre.
        "/9/owned_ad_accounts": {
            "data": [
                {"id": "act_1", "name": "NG Anúncios", "account_status": 1},
                {"id": "act_3", "name": "RJ Anúncios", "currency": "BRL", "account_status": 1},
            ]
        },
        "/9/client_ad_accounts": error(10, status=403),
    }
    if debug is not None:
        routes["/debug_token"] = debug
    return routes


def test_token_mostra_permissoes_possibilidades_e_contas_com_nome():
    perms = [
        ("ads_read", "granted"),
        ("ads_management", "granted"),
        ("business_management", "granted"),
        ("leads_retrieval", "declined"),
    ]
    debug = {"data": {"type": "SYSTEM_USER", "expires_at": 0, "application": "LexHub"}}
    graph = FakeGraph(_token_routes(perms, debug=debug))

    async def go():
        async with graph.client() as c:
            return await token_info(c, app_token="1|segredo")

    out = run(go())
    assert out["ok"] and out["user"]["name"] == "Coletor LexHub"
    # As que o token lê primeiro (ativas antes), depois as do negócio sem acesso aos relatórios
    assert [a["name"] for a in out["accounts"]] == ["NG Anúncios", "Zeta Parada", "RJ Anúncios"]
    assert [a["assigned"] for a in out["accounts"]] == [True, True, False]
    first = out["accounts"][0]
    assert first["id"] == "act_1" and first["business"] == "LexGroup" and first["spent"] == 12345.0
    assert out["accounts"][1]["status"] == "desativada" and not out["accounts"][1]["active"]
    assert out["accounts"][2]["business"] == "LexGroup" and out["accounts"][2]["businessId"] == "9"
    assert "1 do negócio sem acesso" in out["checks"][-1]["message"]
    assert out["tokenType"] == "Usuário do sistema" and out["neverExpires"] is True
    assert out["app"] == "LexHub" and out["businesses"] == [{"id": "9", "name": "LexGroup"}]
    caps = {c["key"]: c["status"] for c in out["capabilities"]}
    assert caps["insights"] == "used" and caps["manage"] == "warn"
    assert caps["business"] == "available" and caps["leads"] == "missing"
    assert [p["granted"] for p in out["permissions"]] == [True, True, True, False]
    debug_req = next(r for r in graph.requests if r.url.path.endswith("/debug_token"))
    assert debug_req.headers["Authorization"] == "Bearer 1|segredo"
    assert "appsecret_proof" not in debug_req.url.params


def test_token_sem_ads_read_ou_sem_contas():
    graph = FakeGraph(_token_routes([("public_profile", "granted")]))

    async def go():
        async with graph.client() as c:
            return await token_info(c)

    out = run(go())
    assert not out["ok"] and out["accounts"] == [] and out["tokenType"] is None
    assert "ads_read" in out["checks"][-1]["message"]
    assert not any(r.url.path.endswith("/me/adaccounts") for r in graph.requests)

    graph = FakeGraph({"/me": error(190, status=401)})

    async def recusado():
        async with graph.client() as c:
            return await token_info(c)

    out = run(recusado())
    assert not out["ok"] and out["checks"][1]["message"].startswith("A Meta recusou o token")
