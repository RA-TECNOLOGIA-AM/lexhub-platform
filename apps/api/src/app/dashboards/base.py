"""O molde de todo dashboard da V2: o que a casca entrega ao módulo e o que o módulo devolve.

A casca (routes/dashboards.py) cuida do que é da V2: acesso, período, filtros, unidade -> fonte,
`meta` e comissão. O módulo de cada dashboard (ex.: protocolo_lexpre.py) só calcula os números,
com as queries e funções `filter_*` copiadas da v1, a partir do `DashboardContext`.
"""

from collections.abc import Awaitable, Callable, Hashable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from app.result_memo import run_now

Remember = Callable[[Hashable, Callable[[], Awaitable[Any]]], Awaitable[Any]]


class DashboardInputError(ValueError):
    """Período ou filtro inválido na URL (vira 422 com a mensagem)."""


class SourceFetcher(Protocol):
    """Busca uma query registrada (mesmo nome da v1, ex.: "log_setor_demanda_lexpre_NG")."""

    async def fetch(self, query_name: str) -> list[dict[str, Any]]: ...

    # Quando veio do banco o dado mais antigo usado (epoch s); None = nada buscado. Vai no meta.synced_at.
    def synced_at(self) -> float | None: ...


@dataclass(frozen=True)
class Period:
    start: date
    end: date


@dataclass(frozen=True)
class DashboardContext:
    """Tudo que o módulo recebe. O escopo já vem resolvido: 'own' é negado antes (sem vínculo ainda)."""

    source: SourceFetcher  # busca as queries no banco de origem do dashboard
    unit_ref: str  # id da unidade na fonte (app.unit_source_refs; LexPre: escritorio_id "1")
    period: Period
    filters: dict[str, list[Any]]  # só os filtros que o módulo declara, já convertidos
    can_see_commission: bool  # a casca também remove a comissão da resposta se for False
    # Quem a pessoa é na fonte (app.member_source_refs). Só vem preenchido nos módulos com
    # own_rows_only e para quem não gere a unidade; None = sem vínculo (a página zera).
    own_ref: str | None = None
    # Outros bancos que o módulo lê além do seu (DashboardModule.extra_queries), só os que a unidade tem
    # ligados (app.unit_source_refs): banco -> busca e banco -> ref da unidade nele.
    extra_sources: dict[str, SourceFetcher] = field(default_factory=dict)
    extra_refs: dict[str, str] = field(default_factory=dict)
    # De que banco `source` lê: o do módulo ou, numa unidade sem ele, um dos alt_sources.
    source_db: str = ""
    # Exportação: as opções escolhidas na janela (ExportSpec.options), ex.: {"criterio": "saida"}.
    export_options: dict[str, str] = field(default_factory=dict)
    # Memória dos cálculos (app/result_memo.py): `await ctx.remember(chave, calcular)` devolve o resultado
    # guardado do mesmo cálculo sobre os mesmos dados, ou calcula. A chave só precisa dizer o que muda
    # dentro do dashboard (ex.: período e filtros): a casca junta dashboard, unidade, fonte, comissão e dia.
    remember: Remember = run_now


@dataclass(frozen=True)
class ExportOption:
    """Uma escolha da exportação além dos campos, como na v1 (ex.: o recorte entrada/saida/total da Execução)."""

    key: str  # o parâmetro na URL (?criterio=saida)
    label: str  # o nome na janela ("Recorte")
    choices: dict[str, str]  # valor -> rótulo, na ordem da janela; o primeiro é o padrão


@dataclass(frozen=True)
class ExportSpec:
    """Exportação de um dashboard, como na v1 (`_CAMPOS_EXPORT_*`, `_LABELS_EXPORT_*`, `_rows_*_export`)."""

    fields: dict[str, str]  # slug -> coluna das linhas (= _CAMPOS_EXPORT_* da v1, mesma ordem)
    labels: dict[str, str]  # slug -> cabeçalho do arquivo (= _LABELS_EXPORT_* da v1)
    sheet_name: str  # nome da aba no XLSX (igual à v1)
    rows: Callable[[DashboardContext], Awaitable[list[dict[str, Any]]]]  # = _rows_*_export da v1
    # Escolhas da janela além dos campos (chegam em ctx.export_options).
    options: tuple[ExportOption, ...] = ()
    # Nome do relatório quando o dashboard tem mais de um ("Processos", "Atividades").
    title: str = ""
    # Nome da aba por unidade, quando a v1 mudava (ex.: "Execução LA"); sem a unidade, vale sheet_name.
    sheet_name_por_unidade: dict[str, str] = field(default_factory=dict)
    # XLSX com uma aba por valor desta coluna (ex.: a informação faltando), na ordem de `sheet_order` (o que não
    # estiver nela vai depois, na ordem em que aparece); a coluna sai das abas. Vazio = uma aba só (sheet_name).
    sheet_by: str = ""
    sheet_order: tuple[str, ...] = ()
    # Nome da aba para um valor longo (o Excel corta em 31 caracteres), ex.: "Data do acórdão (mérito lançado)".
    sheet_titles: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AltSource:
    """Outro banco de onde o dashboard sai numa unidade que não tem o banco principal."""

    label: str  # o que aparece no `meta.source` ("LA")
    queries: tuple[str, ...] = ()  # o aquecedor do cache as mantém quentes


@dataclass(frozen=True)
class DashboardModule:
    key: str  # mesma key de app.dashboard_catalog
    source_db: str  # banco de origem ('lexpre', 'lexflow', 'ng', 'laadv')
    source_label: str  # o que aparece no `meta.source` ("LexPre")
    build: Callable[[DashboardContext], Awaitable[dict[str, Any]]]
    filters: dict[str, type] = field(default_factory=dict)  # nome na URL -> tipo (str ou int)
    commission_fields: tuple[
        str, ...
    ] = ()  # listas de comissão: todos para quem gere, só a sua para os demais
    commission_person_key: str = "funcionario"  # campo de cada linha com o nome da pessoa na fonte
    v2_only_fields: tuple[str, ...] = ()  # campos novos da V2 sem regra ainda: vêm null
    export: ExportSpec | None = None  # None = o dashboard não exporta
    # Outros relatórios do mesmo dashboard (?relatorio=<chave>), ex.: as Atividades dos Acordos na v1.
    export_reports: dict[str, ExportSpec] = field(default_factory=dict)
    queries: tuple[str, ...] = ()  # queries que usa: o aquecedor do cache as mantém quentes
    # A página inteira só com os dados da própria pessoa para quem não gere a unidade
    # (v1: escopo_proprio da Comissão Comercial). A casca preenche ctx.own_ref.
    own_rows_only: bool = False
    # Queries de outros bancos que o módulo também lê (banco -> queries), ex.: o Comercial (LexPre) soma o
    # protocolado no banco legado. A casca entrega ctx.extra_sources dos bancos ligados à unidade.
    extra_queries: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # Bancos alternativos (banco -> AltSource): a unidade sem `source_db` lê o primeiro destes que tiver
    # ligado, ex.: o Protocolo legado sai do banco ng no NG e no RJ e do laadv na LA (rotas _LA da v1).
    alt_sources: dict[str, AltSource] = field(default_factory=dict)
    # Queries de `queries` que podem vir só com as linhas da unidade da tela (app/unit_scope.py): o cálculo
    # descarta as das outras unidades antes de qualquer conta. Conferido em tests/test_unit_scope_paridade.py.
    unit_scoped: tuple[str, ...] = ()

    def pick_source(self, refs: dict[str, str]) -> tuple[str, str] | None:
        """(banco, ref da unidade nele) de onde o dashboard sai nesta unidade; None = nenhum ligado."""
        for db in (self.source_db, *self.alt_sources):
            if (ref := refs.get(db)) is not None:
                return db, ref
        return None

    def label_of(self, db: str) -> str:
        """O nome da fonte (`meta.source`) quando o dashboard sai do banco `db`."""
        alt = self.alt_sources.get(db)
        return alt.label if alt is not None else self.source_label


class NotReady(Exception):
    """O módulo existe, mas o cálculo ainda não foi ligado (aguardando a cópia da v1)."""


def resolve_period(start: date | None, end: date | None, today: date) -> Period:
    """Sem período: do dia 1 do mês até hoje (igual à v1). Com período: os dois e em ordem."""
    if start is None and end is None:
        return Period(today.replace(day=1), today)
    if start is None or end is None:
        raise DashboardInputError("Informe as duas datas do período (from e to)")
    if start > end:
        raise DashboardInputError("A data inicial (from) é depois da final (to)")
    return Period(start, end)


def parse_filters(declared: dict[str, type], raw: dict[str, list[str]]) -> dict[str, list[Any]]:
    """Pega da URL só os filtros que o módulo declara (valor repetido = vários) e converte o tipo."""
    filters: dict[str, list[Any]] = {}
    for name, kind in declared.items():
        values = [v for v in raw.get(name, []) if v != ""]
        try:
            filters[name] = [kind(v) for v in values]
        except ValueError:
            raise DashboardInputError(f"Filtro {name} inválido") from None
    return filters


def own_rows(rows: list[dict[str, Any]] | None, person_key: str, own_ref: str | None) -> list[dict]:
    """Só as linhas da própria pessoa. Sem vínculo com a fonte (own_ref None): nenhuma."""
    if own_ref is None:
        return []
    return [r for r in rows or [] if r.get(person_key) == own_ref]


def shape_response(
    module: DashboardModule,
    data: dict[str, Any],
    meta: dict[str, Any],
    can_see_commission: bool,
    own_ref: str | None = None,
) -> dict[str, Any]:
    """Junta `meta` + o que o módulo calculou e completa os campos da V2.

    Comissão: quem gere a unidade (can_see_commission) vê a de todos; os demais, só a própria linha
    (pelo vínculo pessoa -> funcionário na fonte; sem vínculo, nenhuma).
    """
    body = {"meta": meta, **data}
    if not can_see_commission:
        for name in module.commission_fields:
            if name in body:
                body[name] = own_rows(body[name], module.commission_person_key, own_ref)
    for name in module.v2_only_fields:
        body.setdefault(name, None)
    return body
