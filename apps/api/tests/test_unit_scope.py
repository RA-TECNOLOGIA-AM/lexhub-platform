"""Recorte por unidade (app/unit_scope.py): as queries do LexFlow que trazem todos os escritórios vêm só com
as linhas da unidade da tela, sem mudar o que o cálculo pede nem o SQL da v1."""

import asyncio

import pytest

from app.dashboards import DASHBOARDS
from app.routes.catalog import _query_fetched_at
from app.source_cache import Entry, MemoryStore, SourceCache
from app.source_queries import QUERIES
from app.sources import PgSourceFetcher
from app.unit_scope import (
    ESCRITORIO_POR_UNIDADE,
    UNIT_COLUMN,
    UnitScopedSource,
    scope_source,
    scoped_name,
    scoped_sql,
    split_scoped,
)


def run(coro):
    return asyncio.run(coro)


def test_nome_do_recorte_vai_e_volta():
    assert scoped_name("execucao_LA", 20) == "execucao_LA@20"
    assert split_scoped("execucao_LA@20") == ("execucao_LA", 20)
    assert split_scoped("execucao_LA") == ("execucao_LA", None)


@pytest.mark.parametrize(
    "nome", ["execucao_LA@x", "nao_existe@20", "agendamentos_setor_execucao_NG@20"]
)
def test_recorte_desconhecido_e_erro(nome):
    with pytest.raises(KeyError):
        split_scoped(nome)


def test_sql_do_recorte_embrulha_a_query_da_v1_sem_mudar():
    sql = QUERIES["execucao_LA"]["query"]
    recorte = scoped_sql("execucao_LA", sql + ";\n", 21)
    assert recorte.startswith("select * from (\n")
    assert sql.strip() in recorte
    assert recorte.endswith(') q where q."ID_ESCRITORIO" = 21')


def test_queries_com_recorte_sao_do_lexflow_e_tem_uma_coluna_de_escritorio_so():
    for nome, coluna in UNIT_COLUMN.items():
        spec = QUERIES[nome]
        assert spec["database"] == "lexflow", nome
        assert spec["query"].count(f'"{coluna}"') == 1, nome
        # ORDER BY no fim: a ordem não sobreviveria ao SELECT de fora (fica sem recorte).
        assert not spec["query"].rstrip().lower().split("\n")[-1].strip().startswith("order by"), (
            nome
        )


def test_cada_dashboard_so_recorta_queries_suas_e_conhecidas():
    for key, module in DASHBOARDS.items():
        for q in module.unit_scoped:
            assert q in UNIT_COLUMN, (key, q)
            assert q in module.queries, (key, q)
            assert module.source_db == "lexflow", key


def test_unidades_do_lexflow():
    assert ESCRITORIO_POR_UNIDADE == {"NG": 20, "LA": 21, "RJ": 27}


class Inner:
    def __init__(self):
        self.pedidos = []
        self.reads = [("x", 1.0)]

    async def fetch(self, name):
        self.pedidos.append(("fetch", name))
        return [{"nome": name}]

    async def version(self, name):
        self.pedidos.append(("version", name))
        return 7.0

    def synced_at(self):
        return 123.0


def test_fonte_recortada_troca_so_o_nome_das_queries_do_modulo():
    inner = Inner()
    fonte = UnitScopedSource(inner, 20, frozenset({"execucao_LA"}))
    assert run(fonte.fetch("execucao_LA")) == [{"nome": "execucao_LA@20"}]
    assert run(fonte.fetch("agendamentos_setor_execucao_NG")) == [
        {"nome": "agendamentos_setor_execucao_NG"}
    ]
    assert run(fonte.version("execucao_LA")) == 7.0
    assert run(fonte.version("execucao_LA@20")) == 7.0  # nome que veio de `reads`: passa direto
    assert inner.pedidos[-2:] == [("version", "execucao_LA@20"), ("version", "execucao_LA@20")]
    assert fonte.reads is inner.reads
    assert fonte.synced_at() == 123.0


def test_so_recorta_no_lexflow_com_unidade_conhecida_e_query_que_aceita():
    inner = Inner()
    assert isinstance(scope_source(inner, "lexflow", "NG", ("execucao_LA",)), UnitScopedSource)
    assert scope_source(inner, "lexpre", "NG", ("execucao_LA",)) is inner
    assert scope_source(inner, "lexflow", "SP", ("execucao_LA",)) is inner
    assert scope_source(inner, "lexflow", "NG", ()) is inner
    assert scope_source(inner, "lexflow", "NG", ("agendamentos_setor_execucao_NG",)) is inner


class FakeManager:
    """Conexões de mentira: devolve o SQL que chegou ao banco."""

    def __init__(self):
        self.sql = []

    def get_connection(self, name):
        manager = self

        class _Conn:
            def transaction(self, **kwargs):
                class _Tx:
                    async def __aenter__(self):
                        return None

                    async def __aexit__(self, *exc):
                        return False

                return _Tx()

            async def fetch(self, query):
                manager.sql.append(query)
                return []

            async def fetchval(self, query):
                manager.sql.append(query)
                return "fp"

            def is_closed(self):
                return False

        class _Ctx:
            async def __aenter__(self):
                return _Conn()

            async def __aexit__(self, *exc):
                return False

        return _Ctx()

    async def expire_connections(self, name):
        return None

    def report_failure(self, name, exc):
        return None


def test_banco_recebe_a_query_recortada_e_a_inteira_continua_igual():
    manager = FakeManager()
    fonte = PgSourceFetcher(manager, "lexflow")
    run(fonte.fetch("execucao_LA@27"))
    run(fonte.fetch("execucao_LA"))
    run(fonte.fetch_if_changed("execucao_LA@27", None))
    recorte, inteira, fp, recorte2 = manager.sql
    assert recorte == scoped_sql("execucao_LA", QUERIES["execucao_LA"]["query"], 27)
    assert inteira == QUERIES["execucao_LA"]["query"]
    assert recorte2 == recorte
    assert '"ID_ESCRITORIO" = 27' in fp  # a impressão digital também é do recorte


def test_recorte_de_query_de_outro_banco_e_erro():
    fonte = PgSourceFetcher(FakeManager(), "lexpre")
    with pytest.raises(ValueError):
        run(fonte.fetch("execucao_LA@20"))


def test_card_do_hub_considera_o_recorte_mais_novo():
    cache = SourceCache(MemoryStore(), ttl=300, clock=lambda: 1000.0)
    assert run(_query_fetched_at(cache, "lexflow", "execucao_LA")) is None
    cache._store.set("lexflow:execucao_LA@20", Entry(data=[], fetched_at=500.0))
    cache._store.set("lexflow:execucao_LA@21", Entry(data=[], fetched_at=700.0))
    assert run(_query_fetched_at(cache, "lexflow", "execucao_LA")) == 700.0
    cache._store.set("lexpre:q", Entry(data=[], fetched_at=600.0))
    assert run(_query_fetched_at(cache, "lexpre", "q")) == 600.0


# --- Casca: a rota de dados e a de exportação pedem o recorte da unidade da tela --------------------

from app.dashboards.base import DashboardModule, ExportSpec
from app.routes.dashboards import get_unit_scope
from conftest import USER_ID


@pytest.fixture
def lexflow_module(monkeypatch, repo):
    """Módulo falso do LexFlow com recorte em execucao_LA (agendamentos fica inteira)."""

    async def build(ctx):
        rows = await ctx.source.fetch("execucao_LA")
        await ctx.source.fetch("agendamentos_setor_execucao_NG")
        return {"linhas": len(rows)}

    async def rows(ctx):
        return await ctx.source.fetch("execucao_LA")

    fake = DashboardModule(
        key="execucao",
        source_db="lexflow",
        source_label="LexFlow",
        build=build,
        queries=("execucao_LA", "agendamentos_setor_execucao_NG"),
        unit_scoped=("execucao_LA",),
        export=ExportSpec(fields={"id": "id"}, labels={"id": "ID"}, sheet_name="E", rows=rows),
    )
    monkeypatch.setitem(DASHBOARDS, "execucao", fake)
    repo.units.setdefault(("lexgroup", "RJ"), "00000000-0000-0000-0000-0000000000a7")
    for unit in ("NG", "RJ"):
        repo.grant(USER_ID, unit, "execucao", "all")
        repo.unit_refs[(repo.units[("lexgroup", unit)], "lexflow")] = unit
    repo.exporters.add(USER_ID)


def _auth(signer):
    return {"Authorization": f"Bearer {signer.token()}"}


@pytest.fixture
def recorte_ligado(client):
    """SOURCE_UNIT_SCOPE=true (o padrão; explícito para o teste não depender do ambiente)."""
    client.app.dependency_overrides[get_unit_scope] = lambda: True


@pytest.mark.parametrize(("unit", "escritorio"), [("NG", 20), ("RJ", 27)])
def test_rota_de_dados_pede_o_recorte_da_unidade(
    client, signer, sources, lexflow_module, recorte_ligado, unit, escritorio
):
    r = client.get(f"/orgs/lexgroup/units/{unit}/dashboards/execucao", headers=_auth(signer))
    assert r.status_code == 200, r.text
    assert sources.last.fetched == [f"execucao_LA@{escritorio}", "agendamentos_setor_execucao_NG"]


def test_rota_de_exportacao_pede_o_recorte_da_unidade(
    client, signer, sources, lexflow_module, recorte_ligado
):
    r = client.get("/orgs/lexgroup/units/NG/dashboards/execucao/export", headers=_auth(signer))
    assert r.status_code == 200, r.text
    assert sources.last.fetched == ["execucao_LA@20"]


def test_recorte_vem_ligado_por_padrao(client, signer, sources, lexflow_module):
    r = client.get("/orgs/lexgroup/units/NG/dashboards/execucao", headers=_auth(signer))
    assert r.status_code == 200, r.text
    assert sources.last.fetched == ["execucao_LA@20", "agendamentos_setor_execucao_NG"]
    assert get_unit_scope() is True


def test_recorte_desligado_pede_a_query_inteira(client, signer, sources, lexflow_module):
    client.app.dependency_overrides[get_unit_scope] = lambda: False
    r = client.get("/orgs/lexgroup/units/NG/dashboards/execucao", headers=_auth(signer))
    assert r.status_code == 200, r.text
    assert sources.last.fetched == ["execucao_LA", "agendamentos_setor_execucao_NG"]


# --- ordem fixa das linhas -----------------------------------------------------------------------------

from app.unit_scope import ordem_canonica


def test_ordem_fixa_por_id_e_parte_adversa_nas_queries_do_recorte():
    linhas = [
        {"id": 3, "PARTE_ADVERSA": "B"},
        {"id": 1, "PARTE_ADVERSA": None},
        {"id": 3, "PARTE_ADVERSA": "A"},
        {"id": None, "PARTE_ADVERSA": "X"},
        {"id": 2, "PARTE_ADVERSA": "Z"},
    ]
    ordenadas = ordem_canonica("setor_recurso_NG@20", list(linhas))
    assert [(r["id"], r["PARTE_ADVERSA"]) for r in ordenadas] == [
        (1, None),
        (2, "Z"),
        (3, "A"),
        (3, "B"),
        (None, "X"),
    ]
    # A inteira e o recorte ficam na mesma ordem relativa: recortar depois de ordenar = ordenar o recorte.
    inteira = ordem_canonica("setor_recurso_NG", list(reversed(linhas)))
    assert inteira == ordenadas


def test_ordem_fixa_usa_a_coluna_ID_nos_julgados_e_nao_mexe_nas_outras_queries():
    julgados = ordem_canonica("julgados", [{"ID": 9}, {"ID": 4}])
    assert [r["ID"] for r in julgados] == [4, 9]
    outra = [{"id": 2}, {"id": 1}]
    assert ordem_canonica("agendamentos_setor_execucao_NG", outra) == [{"id": 2}, {"id": 1}]


def test_banco_devolve_as_linhas_do_recorte_em_ordem_fixa():
    class Manager(FakeManager):
        def get_connection(self, name):
            ctx = super().get_connection(name)

            class _Ctx:
                async def __aenter__(self_inner):
                    conn = await ctx.__aenter__()

                    async def fetch(query):
                        return [{"id": 5}, {"id": 1}, {"id": 3}]

                    conn.fetch = fetch
                    return conn

                async def __aexit__(self_inner, *exc):
                    return False

            return _Ctx()

    fonte = PgSourceFetcher(Manager(), "lexflow")
    assert [r["id"] for r in run(fonte.fetch("execucao_LA@20"))] == [1, 3, 5]
    assert [r["id"] for r in run(fonte.fetch("execucao_LA"))] == [1, 3, 5]
    rows, _ = run(fonte.fetch_if_changed("execucao_LA", None))
    assert [r["id"] for r in rows] == [1, 3, 5]
    assert [r["id"] for r in run(fonte.fetch("agendamentos_setor_execucao_NG"))] == [5, 1, 3]
