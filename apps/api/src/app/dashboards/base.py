"""O molde de todo dashboard da V2: o que a casca entrega ao módulo e o que o módulo devolve.

A casca (routes/dashboards.py) cuida do que é da V2: acesso, período, filtros, unidade -> fonte,
`meta` e comissão. O módulo de cada dashboard (ex.: protocolo_lexpre.py) só calcula os números,
com as queries e funções `filter_*` copiadas da v1, a partir do `DashboardContext`.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol


class DashboardInputError(ValueError):
    """Período ou filtro inválido na URL (vira 422 com a mensagem)."""


class SourceFetcher(Protocol):
    """Busca uma query registrada (mesmo nome da v1, ex.: "log_setor_demanda_lexpre_NG")."""

    async def fetch(self, query_name: str) -> list[dict[str, Any]]: ...


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


@dataclass(frozen=True)
class ExportSpec:
    """Exportação de um dashboard, como na v1 (`_CAMPOS_EXPORT_*`, `_LABELS_EXPORT_*`, `_rows_*_export`)."""

    fields: dict[str, str]  # slug -> coluna das linhas (= _CAMPOS_EXPORT_* da v1, mesma ordem)
    labels: dict[str, str]  # slug -> cabeçalho do arquivo (= _LABELS_EXPORT_* da v1)
    sheet_name: str  # nome da aba no XLSX (igual à v1)
    rows: Callable[[DashboardContext], Awaitable[list[dict[str, Any]]]]  # = _rows_*_export da v1


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
