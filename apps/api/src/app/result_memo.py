"""Memória dos cálculos dos dashboards: o mesmo pedido sobre os mesmos dados não é calculado de novo.

O cálculo (a cópia da v1) roda em Python sobre todas as linhas da fonte e prende o único worker da API
por segundos. Aqui fica guardado o resultado de cada pedido (quem chama monta a chave: dashboard,
unidade, período, filtros, quem vê a comissão, dia...) junto com a versão de cada query que o cálculo
leu (`fetched_at` no cache das fontes, app/source_cache.py). O resultado guardado vale enquanto:
  * todas essas queries continuam na mesma versão no cache das fontes (dado renovado = recalcula);
  * não passou de `max_age` (protege o que o cálculo usa sem passar pela fonte, como a hora atual).

Assim voltar a uma combinação de filtros já vista, ou abrir a mesma tela que outra pessoa acabou de
abrir, responde na hora. Pedidos iguais ao mesmo tempo: um calcula e os outros esperam o mesmo
resultado. Uma requisição cancelada não cancela o cálculo (o próximo pedido aproveita).

Só guarda quando todas as fontes do pedido informam versão (`TrackedFetcher`, ex.: CachedSourceFetcher);
senão (testes, fonte sem cache) só calcula.
"""

import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Hashable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

Compute = Callable[[], Awaitable[Any]]


class TrackedFetcher(Protocol):
    """Fonte que diz o que leu e em que versão (ver CachedSourceFetcher)."""

    reads: list[tuple[str, float]]  # (query, fetched_at) de cada leitura, na ordem

    async def version(self, query_name: str) -> float:
        """A versão (fetched_at) do dado que a leitura dessa query devolveria agora; conta como leitura."""
        ...


def is_tracked(fetcher: Any) -> bool:
    """A fonte informa versão? Lê os atributos de verdade (um embrulho como o GuardedSourceFetcher só
    tem `reads` se a fonte de dentro tiver); `isinstance` com Protocol não executaria a property."""
    return hasattr(fetcher, "reads") and callable(getattr(fetcher, "version", None))


Dep = tuple[str, str, float]  # (banco, query, fetched_at)


@dataclass(frozen=True)
class Memo:
    value: Any
    deps: tuple[Dep, ...]
    at: float  # quando foi calculado (relógio de `ResultMemo`)


class ResultMemo:
    def __init__(
        self,
        max_entries: int = 64,
        max_age: float = 300,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._max = max_entries
        self._max_age = max_age
        self._clock = clock
        # A usada há mais tempo sai primeiro.
        self._entries: OrderedDict[Hashable, Memo] = OrderedDict()
        self._running: dict[Hashable, asyncio.Task[Memo]] = {}

    def __len__(self) -> int:
        return len(self._entries)

    async def get_or_compute(
        self, key: Hashable, fetchers: Mapping[str, Any], compute: Compute
    ) -> Any:
        """O resultado guardado para `key`, se os dados lidos ainda forem os mesmos; senão calcula.

        `fetchers`: banco -> a fonte desta requisição (as mesmas que `compute` usa).
        """
        if self._max <= 0 or not all(is_tracked(f) for f in fetchers.values()):
            return await compute()

        memo = self._entries.get(key)
        if memo is not None:
            if self._clock() - memo.at < self._max_age and await _same_versions(memo, fetchers):
                if key in self._entries:
                    self._entries.move_to_end(key)
                return memo.value
            if self._entries.get(key) is memo:
                del self._entries[key]  # dado renovado ou velho demais

        task = self._running.get(key)
        if task is not None:
            # O mesmo pedido está sendo calculado agora (outra requisição): espera esse.
            memo = await asyncio.shield(task)
            # Registra as leituras também nas fontes desta requisição (meta.synced_at e memórias de fora).
            await _same_versions(memo, fetchers)
            return memo.value

        task = asyncio.create_task(self._compute(key, fetchers, compute))
        self._running[key] = task
        task.add_done_callback(lambda done: self._finished(key, done))
        return (await asyncio.shield(task)).value

    async def _compute(self, key: Hashable, fetchers: Mapping[str, Any], compute: Compute) -> Memo:
        marks = {db: len(f.reads) for db, f in fetchers.items()}
        value = await compute()
        deps = tuple(
            dict.fromkeys(
                (db, query, version)
                for db, f in fetchers.items()
                for query, version in f.reads[marks[db] :]
            )
        )
        memo = Memo(value=value, deps=deps, at=self._clock())
        if deps:  # sem leitura de fonte não dá para saber quando vence: não guarda
            self._entries[key] = memo
            self._entries.move_to_end(key)
            while len(self._entries) > self._max:
                self._entries.popitem(last=False)
        return memo

    def _finished(self, key: Hashable, task: asyncio.Task[Memo]) -> None:
        if self._running.get(key) is task:
            del self._running[key]
        if not task.cancelled():
            task.exception()  # quem esperava já recebeu o erro; lida aqui para o asyncio não reclamar


async def _same_versions(memo: Memo, fetchers: Mapping[str, Any]) -> bool:
    """Cada query lida no cálculo ainda está na mesma versão nas fontes desta requisição?"""
    for db, query, version in memo.deps:
        fetcher = fetchers.get(db)
        if fetcher is None or await fetcher.version(query) != version:
            return False
    return True


async def run_now(_key: Hashable, compute: Compute) -> Any:
    """Sem memória: só calcula (padrão do DashboardContext; testes e exportação)."""
    return await compute()


def filters_key(filters: Mapping[str, list[Any]]) -> tuple:
    """Os filtros como parte de uma chave: só os preenchidos, na ordem dos valores recebidos."""
    return tuple(sorted((name, tuple(values)) for name, values in filters.items() if values))
