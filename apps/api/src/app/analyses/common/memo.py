"""Cache por pedido (V2): dentro de UM pedido, a mesma conta sobre as mesmas linhas é feita uma vez só.

As cópias da v1 refazem muito trabalho dentro do mesmo pedido: o Controle de Processos roda o cálculo
inteiro da Execução 4 vezes, e cada um refaz a base (`_base_execucao_LA`, 142 vezes num pedido) e relê o JSON
dos incontroversos de cada linha (800 mil vezes). Aqui fica o resultado dessas funções enquanto o pedido dura:

    @memo.por_pedido()                   # função pura das linhas (e dos outros argumentos)
    def _base_execucao(execucao): ...

    @memo.por_pedido(contexto=(_escritorio_ctx,))   # também depende de um ContextVar
    def _base_controle_processo_NG(controle_processo): ...

`no_pedido(...)` abre o cache para um cálculo (a casca da API faz isso em cada pedido e exportação); fora
dele, as funções rodam como sempre. A chave usa a IDENTIDADE das listas e dicionários recebidos (as linhas do
pedido) e o valor dos demais argumentos; a referência fica guardada junto, então a identidade não é reusada
por outro objeto enquanto o pedido dura. Lista devolvida sai como cópia rasa: quem altera a lista recebida
(append, sort) não muda a guardada. Só entra aqui função que não altera as linhas nem lê estado global.
"""

import inspect
from collections.abc import Awaitable, Callable, Iterable
from contextvars import ContextVar
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")

_PEDIDO: ContextVar[dict | None] = ContextVar("lexhub_memo_por_pedido", default=None)


async def no_pedido(calculo: Awaitable[T]) -> T:
    """Roda `calculo` com o cache por pedido aberto (e o descarta no fim)."""
    token = _PEDIDO.set({})
    try:
        return await calculo
    finally:
        _PEDIDO.reset(token)


def _parte(valor: Any, refs: list) -> Any:
    if isinstance(valor, (list, dict, set)):
        refs.append(valor)
        return ("id", type(valor).__name__, id(valor))
    if isinstance(valor, tuple):
        return tuple(_parte(v, refs) for v in valor)
    return valor


def _chave(fn: Callable, args: tuple, kwargs: dict, contexto: Iterable[ContextVar]) -> tuple:
    refs: list = []
    chave = (
        fn,
        tuple(_parte(a, refs) for a in args),
        tuple(sorted((k, _parte(v, refs)) for k, v in kwargs.items())),
        tuple(_parte(c.get(), refs) for c in contexto),
    )
    hash(chave)  # TypeError: argumento que não dá para usar na chave -> calcula sem cache
    return chave, refs


def por_pedido(*, contexto: tuple[ContextVar, ...] = (), copiar: bool = True) -> Callable:
    """Guarda o resultado da função durante o pedido (ver o módulo). Aceita funções e corrotinas.

    `copiar=False`: devolve a MESMA lista a cada chamada (a busca das linhas: assim as funções seguintes,
    que guardam pela identidade da lista, também acertam o cache). Só para listas que ninguém altera."""

    def _saida(resultado: Any) -> Any:
        return list(resultado) if copiar and isinstance(resultado, list) else resultado

    def decorar(fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def assincrona(*args: Any, **kwargs: Any) -> Any:
                memo = _PEDIDO.get()
                if memo is None:
                    return await fn(*args, **kwargs)
                try:
                    chave, refs = _chave(fn, args, kwargs, contexto)
                except TypeError:
                    return await fn(*args, **kwargs)
                if chave not in memo:
                    memo[chave] = (refs, await fn(*args, **kwargs))
                return _saida(memo[chave][1])

            return assincrona

        @wraps(fn)
        def sincrona(*args: Any, **kwargs: Any) -> Any:
            memo = _PEDIDO.get()
            if memo is None:
                return fn(*args, **kwargs)
            try:
                chave, refs = _chave(fn, args, kwargs, contexto)
            except TypeError:
                return fn(*args, **kwargs)
            if chave not in memo:
                memo[chave] = (refs, fn(*args, **kwargs))
            return _saida(memo[chave][1])

        return sincrona

    return decorar
