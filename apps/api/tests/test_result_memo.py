"""Memória dos cálculos (app/result_memo.py): guarda por pedido e versão dos dados lidos."""

import asyncio
from contextvars import ContextVar
from datetime import date
from types import SimpleNamespace

import pytest

from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, Period
from app.result_memo import ResultMemo, filters_key


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


class Fonte:
    """Fonte que informa versão (como CachedSourceFetcher): query -> fetched_at."""

    def __init__(self, versoes: dict[str, float] | None = None):
        self.versoes = versoes if versoes is not None else {"q": 1.0}
        self.reads: list[tuple[str, float]] = []

    async def fetch(self, query_name):
        self.reads.append((query_name, self.versoes[query_name]))
        return [{"query": query_name}]

    async def version(self, query_name):
        self.reads.append((query_name, self.versoes[query_name]))
        return self.versoes[query_name]


class Calculo:
    """O cálculo de um dashboard: lê a query q e conta quantas vezes rodou."""

    def __init__(self, fonte, query: str = "q", delay: float = 0.0):
        self.fonte = fonte
        self.query = query
        self.delay = delay
        self.vezes = 0

    async def __call__(self):
        self.vezes += 1
        await self.fonte.fetch(self.query)
        if self.delay:
            await asyncio.sleep(self.delay)
        return {"vez": self.vezes}


def run(coro):
    return asyncio.run(coro)


def test_mesmo_pedido_sobre_os_mesmos_dados_calcula_uma_vez():
    memo, fonte = ResultMemo(), Fonte()
    calc = Calculo(fonte)

    async def go():
        a = await memo.get_or_compute("k", {"ng": fonte}, calc)
        b = await memo.get_or_compute("k", {"ng": Fonte()}, calc)  # outra requisição, mesma versão
        return a, b

    a, b = run(go())
    assert calc.vezes == 1
    assert b is a


def test_dado_renovado_calcula_de_novo():
    memo, fonte = ResultMemo(), Fonte()
    calc = Calculo(fonte)

    async def go():
        await memo.get_or_compute("k", {"ng": fonte}, calc)
        fonte.versoes["q"] = 2.0  # o cache das fontes trouxe dado novo
        return await memo.get_or_compute("k", {"ng": fonte}, calc)

    assert run(go()) == {"vez": 2}


def test_outro_pedido_calcula_o_seu():
    memo, fonte = ResultMemo(), Fonte()
    calc = Calculo(fonte)

    async def go():
        await memo.get_or_compute(("resposta", "ANP"), {"ng": fonte}, calc)
        await memo.get_or_compute(("resposta", "MORA"), {"ng": fonte}, calc)
        return await memo.get_or_compute(("resposta", "ANP"), {"ng": fonte}, calc)

    assert run(go()) == {"vez": 1}  # voltar ao filtro anterior não recalcula
    assert calc.vezes == 2


def test_velho_demais_calcula_de_novo_mesmo_com_os_mesmos_dados():
    clock = Clock()
    memo, fonte = ResultMemo(max_age=300, clock=clock), Fonte()
    calc = Calculo(fonte)

    async def go():
        await memo.get_or_compute("k", {"ng": fonte}, calc)
        clock.now += 300
        return await memo.get_or_compute("k", {"ng": fonte}, calc)

    assert run(go()) == {"vez": 2}


def test_fonte_sem_versao_so_calcula():
    class SemVersao:
        async def fetch(self, query_name):
            return []

    memo = ResultMemo()
    fonte = SemVersao()
    calc = Calculo(fonte)

    async def go():
        await memo.get_or_compute("k", {"ng": fonte}, calc)
        await memo.get_or_compute("k", {"ng": fonte}, calc)

    run(go())
    assert calc.vezes == 2
    assert len(memo) == 0


def test_desligada_so_calcula():
    memo, fonte = ResultMemo(max_entries=0), Fonte()
    calc = Calculo(fonte)

    async def go():
        await memo.get_or_compute("k", {"ng": fonte}, calc)
        await memo.get_or_compute("k", {"ng": fonte}, calc)

    run(go())
    assert calc.vezes == 2


def test_calculo_que_nao_le_fonte_nao_fica_guardado():
    memo, fonte = ResultMemo(), Fonte()
    vezes = []

    async def sem_leitura():
        vezes.append(1)
        return {}

    async def go():
        await memo.get_or_compute("k", {"ng": fonte}, sem_leitura)
        await memo.get_or_compute("k", {"ng": fonte}, sem_leitura)

    run(go())
    assert len(vezes) == 2


def test_erro_nao_fica_guardado():
    memo, fonte = ResultMemo(), Fonte()
    vezes = []

    async def falha():
        vezes.append(1)
        await fonte.fetch("q")
        raise ValueError("filtro inválido")

    async def go():
        for _ in range(2):
            with pytest.raises(ValueError):
                await memo.get_or_compute("k", {"ng": fonte}, falha)

    run(go())
    assert len(vezes) == 2


def test_limite_de_resultados_sai_o_usado_ha_mais_tempo():
    memo, fonte = ResultMemo(max_entries=2), Fonte()
    calc = Calculo(fonte)

    async def go():
        await memo.get_or_compute("a", {"ng": fonte}, calc)  # 1
        await memo.get_or_compute("b", {"ng": fonte}, calc)  # 2
        await memo.get_or_compute("a", {"ng": fonte}, calc)  # guardado: "a" vira a mais recente
        await memo.get_or_compute("c", {"ng": fonte}, calc)  # 3: sai "b"
        await memo.get_or_compute("a", {"ng": fonte}, calc)  # guardado
        await memo.get_or_compute("b", {"ng": fonte}, calc)  # 4: tinha saído

    run(go())
    assert calc.vezes == 4
    assert len(memo) == 2


def test_pedidos_iguais_ao_mesmo_tempo_calculam_uma_vez():
    memo = ResultMemo()
    fonte = Fonte()
    calc = Calculo(fonte, delay=0.05)
    outras = [Fonte() for _ in range(4)]

    async def go():
        return await asyncio.gather(
            memo.get_or_compute("k", {"ng": fonte}, calc),
            *(memo.get_or_compute("k", {"ng": f}, calc) for f in outras),
        )

    resultados = run(go())
    assert calc.vezes == 1
    assert all(r is resultados[0] for r in resultados)
    # quem esperou também registra a leitura (meta.synced_at da sua resposta)
    assert all(f.reads == [("q", 1.0)] for f in outras)


def test_requisicao_cancelada_nao_cancela_o_calculo():
    memo, fonte = ResultMemo(), Fonte()
    calc = Calculo(fonte, delay=0.05)

    async def go():
        desistiu = asyncio.create_task(memo.get_or_compute("k", {"ng": fonte}, calc))
        await asyncio.sleep(0.01)
        desistiu.cancel()
        depois = await memo.get_or_compute("k", {"ng": fonte}, calc)
        return desistiu, depois

    desistiu, depois = run(go())
    assert desistiu.cancelled()
    assert calc.vezes == 1
    assert depois == {"vez": 1}


def test_resultado_de_dentro_guardado_entra_nas_dependencias_do_de_fora():
    """O histórico guardado (de dentro) conta como leitura para a resposta (de fora)."""
    memo = ResultMemo()
    fonte = Fonte({"periodo": 1.0, "base": 1.0})
    historico = Calculo(fonte, query="base")

    async def resposta(fonte):
        await fonte.fetch("periodo")
        return await memo.get_or_compute("historico", {"ng": fonte}, historico)

    async def go():
        await memo.get_or_compute("historico", {"ng": fonte}, historico)  # já calculado antes
        await memo.get_or_compute("resposta", {"ng": fonte}, lambda: resposta(fonte))
        fonte.versoes["base"] = 2.0  # só a query do histórico mudou
        return await memo.get_or_compute("resposta", {"ng": fonte}, lambda: resposta(fonte))

    assert run(go()) == {"vez": 2}  # a resposta percebeu e recalculou o histórico


def test_filters_key_ignora_vazios_e_nao_depende_da_ordem_dos_nomes():
    assert filters_key({"uf": ["AM"], "materia": ["ANP", "MORA"], "funcionario": []}) == (
        ("materia", ("ANP", "MORA")),
        ("uf", ("AM",)),
    )
    assert filters_key({"b": [1], "a": [2]}) == filters_key({"a": [2], "b": [1]})


# --- generico_v1: o histórico (sem período) não é recalculado quando só o período muda -------

_fonte_ctx: ContextVar = ContextVar("fonte_teste_memo")


def test_generico_trocar_so_o_periodo_reaproveita_o_historico():
    chamadas: list[date | None] = []

    async def handler(from_date: date | None = None, to_date: date | None = None):
        chamadas.append(from_date)
        await _fonte_ctx.get().fetch("q")
        body = {"stats": {"total": 1 if from_date else 99}, "por_mes": [from_date is None]}
        return SimpleNamespace(model_dump=lambda: body)

    copia = SimpleNamespace(
        HANDLERS={"rota": handler},
        QUERIES_POR_DASHBOARD={"rota": ("q",)},
        usar_fonte=lambda fonte: _fonte_ctx.set(fonte),
        _fonte_ctx=_fonte_ctx,
    )
    modulo = generico_v1.modulo(
        key="teste",
        v1_por_unidade={"NG": "rota"},
        descricao_falta="-",
        copia=copia,
        historico=("por_mes", "stats.total_historico=stats.total"),
    )
    memo, fonte = ResultMemo(), Fonte()

    async def remember(key, compute):
        return await memo.get_or_compute(("teste", key), {"lexflow": fonte}, compute)

    def ctx(inicio: date) -> DashboardContext:
        return DashboardContext(
            source=fonte,
            unit_ref="NG",
            period=Period(inicio, date(2026, 11, 17)),
            filters={},
            can_see_commission=True,
            remember=remember,
        )

    async def go():
        a = await modulo.build(ctx(date(2026, 11, 1)))
        b = await modulo.build(ctx(date(2026, 10, 1)))
        return a, b

    a, b = run(go())
    assert chamadas == [date(2026, 11, 1), None, date(2026, 10, 1)]  # histórico rodou uma vez
    for body in (a, b):
        assert body["por_mes"] == [True]
        assert body["stats"] == {"total": 1, "total_historico": 99}
