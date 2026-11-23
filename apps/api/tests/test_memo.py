"""app.analyses.common.memo: o cache por pedido (a mesma conta uma vez dentro de um pedido)."""

import asyncio
from contextvars import ContextVar

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.common import memo

CHAMADAS: list[str] = []
_unidade: ContextVar[int] = ContextVar("unidade_teste", default=20)


@memo.por_pedido()
def base(linhas: list[dict], minimo: int = 0) -> list[dict]:
    CHAMADAS.append("base")
    return [r for r in linhas if r["v"] >= minimo]


@memo.por_pedido(contexto=(_unidade,))
def da_unidade(linhas: list[dict]) -> list[dict]:
    CHAMADAS.append("unidade")
    return [r for r in linhas if r["u"] == _unidade.get()]


@memo.por_pedido(copiar=False)
async def buscar(nome: str) -> list[dict]:
    CHAMADAS.append("busca")
    return [{"v": 1, "u": 20}, {"v": 5, "u": 21}]


def test_fora_do_pedido_calcula_sempre():
    CHAMADAS.clear()
    linhas = [{"v": 1, "u": 20}]
    base(linhas)
    base(linhas)
    assert CHAMADAS == ["base", "base"]


def test_no_pedido_calcula_uma_vez_por_lista_e_argumentos():
    CHAMADAS.clear()
    linhas = [{"v": 1, "u": 20}, {"v": 5, "u": 21}]
    outra = list(linhas)  # mesmo conteúdo, outra lista: outra conta

    async def calculo():
        a = base(linhas)
        b = base(linhas)
        c = base(linhas, minimo=3)
        d = base(outra)
        return a, b, c, d

    a, b, c, d = asyncio.run(memo.no_pedido(calculo()))
    assert CHAMADAS == ["base", "base", "base"]
    assert a == b and a is not b  # cópia rasa: alterar uma não muda a guardada
    assert c == [{"v": 5, "u": 21}]
    assert d == a
    a.append("x")
    assert len(b) == 2


def test_contexto_entra_na_chave():
    CHAMADAS.clear()
    linhas = [{"v": 1, "u": 20}, {"v": 5, "u": 21}]

    async def calculo():
        ng = da_unidade(linhas)
        token = _unidade.set(21)
        la = da_unidade(linhas)
        _unidade.reset(token)
        return ng, la, da_unidade(linhas)

    ng, la, ng2 = asyncio.run(memo.no_pedido(calculo()))
    assert CHAMADAS == ["unidade", "unidade"]
    assert ng == ng2 == [{"v": 1, "u": 20}] and la == [{"v": 5, "u": 21}]


def test_busca_devolve_a_mesma_lista_e_o_cache_acaba_com_o_pedido():
    CHAMADAS.clear()

    async def calculo():
        a = await buscar("q")
        b = await buscar("q")
        return a is b, base(a) == base(b)

    assert asyncio.run(memo.no_pedido(calculo())) == (True, True)
    assert CHAMADAS == ["busca", "base"]
    asyncio.run(memo.no_pedido(buscar("q")))  # outro pedido: busca de novo
    assert CHAMADAS == ["busca", "base", "busca"]


def test_argumento_que_nao_serve_de_chave_calcula_sem_cache():
    CHAMADAS.clear()

    class NaoHashavel:
        __hash__ = None  # type: ignore[assignment]

        def __ge__(self, outro: object) -> bool:
            return True

    linhas = [{"v": NaoHashavel(), "u": 20}]
    minimo = NaoHashavel()

    async def calculo():
        base(linhas, minimo)
        base(linhas, minimo)

    asyncio.run(memo.no_pedido(calculo()))
    assert CHAMADAS == ["base", "base"]
