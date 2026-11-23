"""A unidade em uso nas famílias de análises unificadas (V2).

As cópias da v1 por unidade (NG, LA, RJ) só diferiam em poucos valores, como o id do escritório. Na família
unificada (app/analyses/familias/*), esses valores vêm da unidade em uso: cada família tem um ContextVar com os
valores da NG como padrão, e o arquivo de cada unidade chama as funções da família "na unidade" dele.
"""

from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps
from typing import Any


def na_unidade(var: ContextVar[dict[str, Any]], valores: dict[str, Any], fn: Callable) -> Callable:
    """`fn` chamada com os valores da unidade (ex.: {"ID_ESCRITORIO": 21}) em `var` enquanto roda."""

    @wraps(fn)
    def chamar(*args: Any, **kwargs: Any) -> Any:
        token = var.set(valores)
        try:
            return fn(*args, **kwargs)
        finally:
            var.reset(token)

    return chamar


def na_unidade_de(var: ContextVar[Any], obter: Callable[[], Any], fn: Callable) -> Callable:
    """`fn` chamada com `var` = `obter()` (lido na hora da chamada). Para famílias em que a própria unidade
    guarda o valor num ContextVar que pode mudar (ex.: o Controle de Processos, em que o dashboard do RJ põe o
    escritório 27 no ContextVar da NG): a família usa o ContextVar dela, e o cache por pedido o leva na chave."""

    @wraps(fn)
    def chamar(*args: Any, **kwargs: Any) -> Any:
        token = var.set(obter())
        try:
            return fn(*args, **kwargs)
        finally:
            var.reset(token)

    return chamar


class ValoresDoModulo:
    """Os valores da unidade lidos AO VIVO do módulo dela (ex.: um catálogo que a unidade grava com `global`
    durante o pedido). `nomes`: nome na família -> nome no módulo da unidade. Hash e igualdade pela identidade
    (o cache por pedido usa o objeto na chave)."""

    def __init__(self, globais: dict[str, Any], nomes: dict[str, str]):
        self._globais = globais
        self._nomes = nomes

    def __getitem__(self, nome: str) -> Any:
        return self._globais[self._nomes[nome]]
