import asyncio
import os
from datetime import UTC, date, datetime, timedelta

from app.facebook_ads import CONVERSATION_TYPE, GraphError
from app.facebook_ads_sync import AdsSource, AdsSync, SyncState, chunks, plan
from app.secret_box import SecretBox

BOX = SecretBox(os.urandom(32))
TODAY = date(2026, 11, 26)
NOW = datetime(2026, 11, 26, 15, 0, tzinfo=UTC)  # 11h em Manaus: ainda 26/11


def test_chunks_em_blocos_de_31_dias():
    assert chunks(date(2026, 1, 1), date(2026, 3, 5)) == [
        (date(2026, 1, 1), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 3, 3)),
        (date(2026, 3, 4), date(2026, 3, 5)),
    ]
    assert chunks(TODAY, TODAY) == [(TODAY, TODAY)]


def _plan(state, *, version=1, deep=False, backfill=90):
    return plan(TODAY, state, collect_version=version, backfill_days=backfill, deep=deep)


def test_plan_primeira_coleta_e_personalizacao_nova_buscam_o_historico():
    windows, backfill = _plan(None)
    assert backfill and windows[0][0] == TODAY - timedelta(days=89) and windows[-1][1] == TODAY
    assert all((b - a).days < 31 for a, b in windows)
    # A personalização mudou o que é coletado (versão 2): o histórico de novo
    windows, backfill = _plan(SyncState(1, True, TODAY), version=2)
    assert backfill and windows[0][0] == TODAY - timedelta(days=89)


def test_plan_historico_interrompido_continua_do_ultimo_dia():
    windows, backfill = _plan(SyncState(1, False, date(2026, 10, 1)))
    assert backfill and windows[0][0] == date(2026, 10, 1)


def test_plan_depois_ontem_e_hoje_e_uma_vez_por_dia_28_dias():
    done = SyncState(1, True, TODAY)
    assert _plan(done) == ([(TODAY - timedelta(days=1), TODAY)], False)
    assert _plan(done, deep=True) == ([(TODAY - timedelta(days=27), TODAY)], False)


def test_plan_coleta_parada_traz_o_buraco_sem_passar_do_historico():
    assert _plan(SyncState(1, True, date(2026, 11, 10)), backfill=1095)[0] == [
        (date(2026, 11, 10), TODAY)
    ]
    windows, _ = _plan(SyncState(1, True, date(2020, 1, 1)), backfill=60)
    assert windows[0][0] == TODAY - timedelta(days=59)


class FakeRepo:
    def __init__(self, sources, states=None):
        self._sources = sources
        self._states = states or {}
        self.replaced: list[tuple] = []
        self.saved_states: list[tuple] = []
        self.entities: list[dict] = []
        self.records: list[tuple] = []

    async def sources(self):
        return self._sources

    async def states(self, source_id):
        return dict(self._states.get(source_id, {}))

    async def replace(self, source_id, dataset, window, rows):
        self.replaced.append((source_id, dataset, window, rows))
        return len(rows)

    async def set_state(self, source_id, dataset, state):
        self.saved_states.append((dataset, state))
        self._states.setdefault(source_id, {})[dataset] = state

    async def upsert_entities(self, source_id, rows):
        self.entities += rows
        return len(rows)

    async def record(self, source_id, ok, rows, ms, error):
        self.records.append((source_id, ok, rows, error))


class FakeGraph:
    def __init__(self, fail=None):
        self.fail = fail
        self.reports: list[dict] = []
        self.entity_calls: list[tuple] = []
        self.tokens: list[str] = []

    def __call__(self, token):
        self.tokens.append(token)
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return None

    async def report(self, account_id, **kw):
        self.reports.append({"account": account_id, **kw})
        if self.fail:
            raise self.fail
        row = {
            "date_start": kw["since"].isoformat(),
            "campaign_id": "11",
            "ad_id": "1",
            "spend": "10",
            "age": "25-34",
            "gender": "female",
            "actions": [{"action_type": CONVERSATION_TYPE, "value": "3"}],
        }
        return [row, {"ad_name": "sem id"}]  # a segunda é descartada

    async def entities(self, account_id, level, *, creatives=False, campaigns=None, ids=None):
        self.entity_calls.append((level, creatives, campaigns))
        return [{"id": {"campaign": "11", "adset": "22", "ad": "33"}[level], "name": level}]


CONFIG = {
    "ad_account_id": "act_1",
    "timezone": "America/Manaus",
    "metrics": ["reach"],
    "conversions": [CONVERSATION_TYPE],
    "campaigns": ["11"],
    "breakdowns": ["age_gender"],
    "backfill_days": 60,
    "creatives": True,
    "collect_version": 1,
}


def source(**config):
    return AdsSource(
        id="src-1",
        key="fb_mc_000001",
        config={**CONFIG, **config},
        secret_ciphertext=BOX.encrypt("EAAB-token"),
    )


def make_sync(repo, graph, clock):
    return AdsSync(repo, BOX, graph, interval=600, now=lambda: NOW, clock=lambda: clock[0])


def test_primeira_coleta_historico_de_anuncios_e_detalhamentos_e_entidades():
    repo, graph = FakeRepo([source()]), FakeGraph()
    asyncio.run(make_sync(repo, graph, [0.0]).run_once())
    assert graph.tokens == ["EAAB-token"]
    datasets = [(r[1], r[2]) for r in repo.replaced]
    # 60 dias em 2 blocos, para os anúncios e para idade/gênero
    assert [d for d, _ in datasets] == ["ads", "ads", "age_gender", "age_gender"]
    assert datasets[0][1][0] == TODAY - timedelta(days=59) and datasets[-1][1][1] == TODAY
    ads_report, age_report = graph.reports[0], graph.reports[2]
    assert ads_report["level"] == "ad" and ads_report["campaigns"] == ("11",)
    assert "reach,frequency" in ads_report["fields"]
    assert age_report["level"] == "campaign" and age_report["breakdowns"] == ("age", "gender")
    row = repo.replaced[0][3][0]
    assert row["results"] == 3 and row["conversations"] == 3
    age_row = repo.replaced[2][3][0]
    assert (age_row["dim1"], age_row["dim2"]) == ("25-34", "female")
    # Estado: o primeiro bloco ainda é histórico, o último fecha
    states = [(d, s.backfill_done) for d, s in repo.saved_states]
    assert states == [("ads", False), ("ads", True), ("age_gender", False), ("age_gender", True)]
    assert [e["level"] for e in repo.entities] == ["campaign", "adset", "ad"]
    assert graph.entity_calls[-1] == ("ad", True, ("11",))
    assert repo.records == [("src-1", True, 4, None)]


def test_depois_so_ontem_e_hoje_e_um_dia_depois_os_28_dias():
    states = {"src-1": {"ads": SyncState(1, True, TODAY), "age_gender": SyncState(1, True, TODAY)}}
    repo, graph, clock = FakeRepo([source()], states), FakeGraph(), [1000.0]
    sync = make_sync(repo, graph, clock)
    asyncio.run(sync.run_once())  # a primeira rodada da API é a "funda"
    assert graph.reports[0]["since"] == TODAY - timedelta(days=27)
    asyncio.run(sync.run_once())
    assert graph.reports[-1]["since"] == TODAY - timedelta(days=1)
    assert len(graph.entity_calls) == 3  # entidades só na rodada funda
    clock[0] += 24 * 3600
    asyncio.run(sync.run_once())
    assert graph.reports[-1]["since"] == TODAY - timedelta(days=27)


def test_alcance_com_detalhamento_so_nos_ultimos_13_meses():
    repo, graph = FakeRepo([source(backfill_days=1095)]), FakeGraph()
    asyncio.run(make_sync(repo, graph, [0.0]).run_once())
    breakdown_calls = [r for r in graph.reports if r.get("breakdowns")]
    assert "reach" not in breakdown_calls[0]["fields"]  # bloco de 3 anos atrás
    assert "reach" in breakdown_calls[-1]["fields"]  # bloco de agora


def test_erro_da_meta_vai_para_o_log_e_nao_para_as_outras_fontes():
    other = AdsSource("src-2", "fb_mc_000002", CONFIG, BOX.encrypt("x"))
    repo = FakeRepo([source(), other])
    graph = FakeGraph(fail=GraphError(401, 190, None, "Invalid OAuth access token"))
    asyncio.run(make_sync(repo, graph, [0.0]).run_once())
    assert [r[0] for r in repo.records] == ["src-1", "src-2"]
    ok, rows, error = repo.records[0][1:]
    assert not ok and rows == 0 and error.startswith("A Meta recusou o token")
    assert repo.replaced == [] and repo.saved_states == []


def test_token_que_nao_abre_vai_para_o_log():
    other_box = SecretBox(os.urandom(32))
    bad = AdsSource("src-1", "fb_mc_000001", CONFIG, other_box.encrypt("x"))
    repo, graph = FakeRepo([bad]), FakeGraph()
    asyncio.run(make_sync(repo, graph, [0.0]).run_once())
    assert repo.records[0][1] is False and "Troque o token" in repo.records[0][3]
    assert graph.reports == []


def test_wake_antecipa_a_rodada():
    states = {"src-1": {"ads": SyncState(1, True, TODAY), "age_gender": SyncState(1, True, TODAY)}}
    repo, graph = FakeRepo([source()], states), FakeGraph()
    sync = AdsSync(repo, BOX, graph, interval=3600, now=lambda: NOW)

    async def go():
        async def no_sleep(_):
            return None

        task = asyncio.create_task(sync.loop(initial_delay=0, sleep=no_sleep))
        for _ in range(50):
            if len(repo.records) == 1:
                break
            await asyncio.sleep(0.01)
        sync.wake()
        for _ in range(50):
            if len(repo.records) == 2:
                break
            await asyncio.sleep(0.01)
        task.cancel()
        return len(repo.records)

    assert asyncio.run(go()) == 2
