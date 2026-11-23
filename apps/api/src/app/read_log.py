"""Registro de leituras: quando cada query 'banco:query' foi lida do banco de origem, e se falhou.

Por que existe: os dados do cache já sobrevivem a deploy/reload no Redis (L2), mas a hora mostrada no
hub e em Unidades e fontes vinha só da memória do processo, e voltava a "Atualiza ao abrir" a cada
reinício. Aqui a hora fica em memória e numa chave pequena do Redis por banco ('reads:{banco}' ->
{query: Read}), lida de volta na primeira vez que alguém pergunta por aquele banco.

Custo: uma gravação pequena no Redis a cada busca no banco que o cache JÁ faz (nenhuma consulta nova
aos bancos de origem, nenhum egress a mais). Redis fora do ar = só memória (como o resto do cache).

Quem grava: SourceCache._load (busca, conferência sem mudança e aquecedor). Quem lê: o card do hub
(routes/catalog.py) e a tela de fontes (routes/source_freshness.py).
"""

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass, replace

from app.cache import CacheService

KEEP_FOR = 7 * 86_400  # a hora fica no Redis por 7 dias sem nenhuma leitura nova do banco


@dataclass(frozen=True)
class Read:
    ok_at: float | None  # epoch da última leitura boa (None = nunca leu)
    fail_at: float | None = None  # epoch da última falha DEPOIS da leitura boa (None = nenhuma)
    error: str | None = None  # só o tipo do erro, nunca a mensagem (pode ter host/usuário)


def summarize(reads: Iterable[Read]) -> tuple[float | None, float | None, str | None]:
    """A fonte inteira a partir das leituras das queries dela: (última leitura boa, falha, erro).

    Falha só se a tentativa mais recente (de qualquer query) falhou; houve leitura boa depois = nenhuma.
    É a regra da tela Unidades e fontes e da tela Clientes (um lugar só).
    """
    reads = list(reads)
    ok_at = max((r.ok_at for r in reads if r.ok_at is not None), default=None)
    fail = max(((r.fail_at, r.error) for r in reads if r.fail_at is not None), default=None)
    if fail is None or (ok_at is not None and fail[0] <= ok_at):
        return ok_at, None, None
    return ok_at, fail[0], fail[1]


def _split(key: str) -> tuple[str, str]:
    db, _, query = key.partition(":")
    return db, query


class ReadLog:
    def __init__(self, shared: CacheService, keep_for: int = KEEP_FOR):
        self._shared = shared
        self._keep_for = keep_for
        self._by_db: dict[str, dict[str, Read]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def _db(self, db: str) -> dict[str, Read]:
        """As leituras do banco `db`; na primeira vez, traz o que estava no Redis."""
        if db in self._by_db:
            return self._by_db[db]
        async with self._locks.setdefault(db, asyncio.Lock()):
            if db not in self._by_db:
                saved = await self._shared.get(f"reads:{db}")
                self._by_db[db] = dict(saved) if isinstance(saved, dict) else {}
        return self._by_db[db]

    async def _save(self, db: str) -> None:
        await self._shared.set(f"reads:{db}", dict(self._by_db[db]), self._keep_for)

    async def ok(self, key: str, at: float) -> None:
        db, query = _split(key)
        (await self._db(db))[query] = Read(ok_at=at)
        await self._save(db)

    async def failed(self, key: str, at: float, error: str) -> None:
        db, query = _split(key)
        reads = await self._db(db)
        reads[query] = replace(reads.get(query, Read(ok_at=None)), fail_at=at, error=error)
        await self._save(db)

    async def forget(self, db: str) -> None:
        """Esquece a fonte `db` (desligar, religar ou desconectar): ela volta como "ainda não lida"."""
        self._by_db[db] = {}
        await self._shared.delete(f"reads:{db}")

    async def ok_at(self, key: str) -> float | None:
        db, query = _split(key)
        read = (await self._db(db)).get(query)
        return read.ok_at if read else None

    async def of_db(self, db: str) -> dict[str, Read]:
        return dict(await self._db(db))
