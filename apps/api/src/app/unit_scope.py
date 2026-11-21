"""Só as linhas da unidade da tela: as queries do LexFlow que trazem todos os escritórios.

Várias queries copiadas da v1 trazem os processos de TODAS as unidades (NG, LA e RJ, ~90 mil linhas) e o
cálculo em Python descarta as das outras pelo ID_ESCRITORIO. Cada linha descartada já tinha saído do
Supabase (egress cobrado). Aqui a mesma query é pedida só com as linhas da unidade:

    select * from (<query da v1, sem mudança>) q where q."ID_ESCRITORIO" = 20

O cache guarda a versão recortada com outro nome ('execucao_LA@20'), então o recorte de uma unidade nunca
é servido a outra. Quem calcula continua pedindo 'execucao_LA' (o recorte de situação do processo e os
nomes da v1 não mudam): quem troca o nome é a `UnitScopedSource`, entre o cálculo e o cache.

Só entra no recorte a query cujo cálculo descarta as outras unidades ANTES de qualquer conta. Cada módulo
de dashboard diz quais são as suas (`DashboardModule.unit_scoped`), conferido com testes que comparam o
resultado com e sem as linhas das outras unidades (tests/test_unit_scope.py).
"""

from typing import Any

from app.dashboards.base import SourceFetcher

# Query da v1 que traz todas as unidades -> coluna do escritório no resultado (uma só, com esse nome).
# Fora daqui: as que já filtram a unidade no SQL e as com ORDER BY no fim (a ordem de um SELECT externo
# não é garantida, e há cálculo que depende dela, ex.: log_subfase_processual).
UNIT_COLUMN: dict[str, str] = {
    "execucao_LA": "ID_ESCRITORIO",
    "execucao_RJ": "ID_ESCRITORIO",
    "execucao_acordos_NG": "ID_ESCRITORIO",
    "execucao_acordos_LA": "ID_ESCRITORIO",
    "execucao_acordos_RJ": "ID_ESCRITORIO",
    "setor_recurso": "ID_ESCRITORIO",
    "setor_recurso_NG": "ID_ESCRITORIO",
    "setor_recurso_RJ": "ID_ESCRITORIO",
    "controle_processo": "ID_ESCRITORIO",
    "controle_processo_todas_situacoes": "ID_ESCRITORIO",
    "julgados": "ID_ESCRITORIO",
}

# Unidade (app.unit_source_refs do LexFlow) -> id_escritorio_assinante no LexFlow.
ESCRITORIO_POR_UNIDADE: dict[str, int] = {"NG": 20, "LA": 21, "RJ": 27}

SEP = "@"


def scoped_name(query_name: str, escritorio: int) -> str:
    """'execucao_LA', 20 -> 'execucao_LA@20' (o nome da versão recortada no cache e no log)."""
    return f"{query_name}{SEP}{int(escritorio)}"


def split_scoped(name: str) -> tuple[str, int | None]:
    """'execucao_LA@20' -> ('execucao_LA', 20); 'execucao_LA' -> ('execucao_LA', None)."""
    base, sep, escritorio = name.partition(SEP)
    if not sep:
        return name, None
    if base not in UNIT_COLUMN or not escritorio.isdigit():
        raise KeyError(f"Recorte por unidade desconhecido: {name}")
    return base, int(escritorio)


def scoped_sql(query_name: str, sql: str, escritorio: int) -> str:
    """A query da v1, sem mudança, dentro de um SELECT que deixa só as linhas do escritório."""
    column = UNIT_COLUMN[query_name]
    body = sql.strip().rstrip(";")
    return f'select * from (\n{body}\n) q where q."{column}" = {int(escritorio)}'


class UnitScopedSource:
    """SourceFetcher que pede ao cache a versão recortada das queries `queries` (só a unidade da tela).

    Repassa o resto (versão, leituras e hora da sincronização), para a memória dos cálculos e o `meta`.
    """

    def __init__(self, inner: SourceFetcher, escritorio: int, queries: frozenset[str]):
        self._inner = inner
        self._escritorio = escritorio
        self._queries = queries

    def _name(self, query_name: str) -> str:
        if query_name in self._queries:
            return scoped_name(query_name, self._escritorio)
        return query_name

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        return await self._inner.fetch(self._name(query_name))

    @property
    def reads(self) -> list[tuple[str, float]]:
        return self._inner.reads  # type: ignore[attr-defined]  (sem `reads` = memória não usa)

    async def version(self, query_name: str) -> float:
        return await self._inner.version(self._name(query_name))  # type: ignore[attr-defined]

    def synced_at(self) -> float | None:
        return self._inner.synced_at()


def scope_source(
    source: SourceFetcher, source_db: str, unit_ref: str, queries: tuple[str, ...]
) -> SourceFetcher:
    """A fonte do pedido, recortada na unidade quando dá: banco LexFlow, unidade conhecida e o módulo
    com queries que aceitam o recorte. Senão, a mesma fonte."""
    escritorio = ESCRITORIO_POR_UNIDADE.get(unit_ref)
    scoped = frozenset(q for q in queries if q in UNIT_COLUMN)
    if source_db != "lexflow" or escritorio is None or not scoped:
        return source
    return UnitScopedSource(source, escritorio, scoped)
