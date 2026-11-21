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
resultado com e sem as linhas das outras unidades (tests/test_unit_scope_paridade.py) e, com os dados
reais, por scripts/comparar_v1/conferir_recorte_unidade.py (189 de 189 idênticos em 21/11/2026). Liga e
desliga em SOURCE_UNIT_SCOPE.
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # só tipo: os módulos de dashboard importam este arquivo
    from app.dashboards.base import SourceFetcher

# Query da v1 que traz todas as unidades -> coluna do escritório no resultado (uma só, com esse nome).
# Fora daqui: as que já filtram a unidade no SQL e as com ORDER BY no fim (a ordem de um SELECT externo
# não é garantida, e há cálculo que depende dela, ex.: log_subfase_processual).
#
# Conferido em 20/11/2026 (auditoria do código + dados do LexFlow): todo cálculo, exportação e lista de
# opções dos dashboards que as leem descarta as outras unidades (ID_ESCRITORIO) antes de deduplicar ou
# contar. Os dois caminhos que olham linhas de outra unidade não mudam nada com os dados de hoje: o
# "campos-faltando" dos Julgados casa por NUMERO_PROCESSO (nenhum número se repete entre escritórios; com
# o recorte, passa a casar sempre com a própria unidade) e as Atividades dos Acordos casam o agendamento
# da unidade com o processo pelo id (nenhum aponta para processo de outro escritório). Linhas repetidas
# do mesmo processo (uma por parte adversa) só diferem na parte adversa, que sem ORDER BY já não tinha
# ordem garantida.
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


def com_recorte(queries: Iterable[str]) -> tuple[str, ...]:
    """As queries de um dashboard que aceitam o recorte (para `DashboardModule.unit_scoped`)."""
    return tuple(q for q in dict.fromkeys(queries) if q in UNIT_COLUMN)


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


# Ordem fixa das linhas destas queries: id do processo e parte adversa. Nenhuma tem ORDER BY, então o banco
# devolvia as linhas na ordem do plano, que muda com o recorte (e pode mudar sozinha). O cálculo da v1 tem
# listas sem desempate (matérias com a mesma contagem, processos da mesma data) e, no Recursal e no Controle,
# um processo vem numa linha por parte adversa e vale a primeira. Ordenadas, a query inteira e o recorte dão
# o mesmo resultado, e a mesma tela não troca a ordem dos empatados a cada atualização. Conferido nos dados de
# 21/11/2026: as linhas repetidas de um processo só diferem na parte adversa; com a mesma parte, são iguais.
_COLUNA_ID = {"julgados": "ID"}  # nas outras, "id"


def ordem_canonica(query_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """As linhas de uma query do recorte (inteira ou 'nome@N') na ordem fixa; as outras queries, como vieram."""
    base = query_name.partition(SEP)[0]
    if base not in UNIT_COLUMN:
        return rows
    coluna = _COLUNA_ID.get(base, "id")

    def chave(row: dict[str, Any]) -> tuple:
        pid = row.get(coluna)
        parte = row.get("PARTE_ADVERSA")
        return (pid is None, pid if pid is not None else 0, parte is None, str(parte or ""))

    rows.sort(key=chave)
    return rows


class UnitScopedSource:
    """SourceFetcher que pede ao cache a versão recortada das queries `queries` (só a unidade da tela).

    Repassa o resto (versão, leituras e hora da sincronização), para a memória dos cálculos e o `meta`.
    """

    def __init__(self, inner: "SourceFetcher", escritorio: int, queries: frozenset[str]):
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
    source: "SourceFetcher", source_db: str, unit_ref: str, queries: tuple[str, ...]
) -> "SourceFetcher":
    """A fonte do pedido, recortada na unidade quando dá: banco LexFlow, unidade conhecida e o módulo
    com queries que aceitam o recorte. Senão, a mesma fonte."""
    escritorio = ESCRITORIO_POR_UNIDADE.get(unit_ref)
    scoped = frozenset(q for q in queries if q in UNIT_COLUMN)
    if source_db != "lexflow" or escritorio is None or not scoped:
        return source
    return UnitScopedSource(source, escritorio, scoped)
