"""Exportação do Protocolo, Peticionamento, Org. de Documentos e Pendências (banco legado), como na v1.

v1: GET /protocolo/export (NG), /protocolo_RJ/export, /protocolo_LA/export, e o mesmo para /peticionamento,
/org-documentos (/org_doc_RJ, /org_doc_LA) e /pendencias (/pendencias_RJ, /pendencia_LA). Campos, rótulos e
linhas são a cópia da v1 em app/analyses/v1_legado_export.py; aqui só a entrada muda (ctx.filters e ctx.period
no lugar dos parâmetros da rota) e a unidade escolhe a função: NG tira o RJ, RJ fica só com ele
(excluir_rj=False) e a LA lê o banco laadv, com os campos dela (ExportSpec.por_unidade).
"""

from collections.abc import Awaitable, Callable
from typing import Any

from app.analyses import v1_dashboard_generico_la as copia_la
from app.analyses import v1_dashboard_generico_ng as copia_ng
from app.analyses import v1_legado_export as v1
from app.dashboards.base import DashboardContext, ExportSpec, NotReady
from app.dashboards.generico_v1 import chamar_v1

Linhas = Callable[[DashboardContext], Awaitable[list[dict[str, Any]]]]


def _lista(ctx: DashboardContext, nome: str) -> list[Any] | None:
    """Filtro de vários valores (Optional[List] na rota da v1): vazio = None."""
    return list(ctx.filters.get(nome) or []) or None


def _um(ctx: DashboardContext, nome: str) -> Any:
    """Filtro de um valor só (Optional[str] na rota da v1)."""
    return next(iter(ctx.filters.get(nome) or []), None)


def _ng_rj(nome: str, filtros: Callable[[DashboardContext], list[Any]]) -> Linhas:
    """As linhas da NG (sem o RJ) ou do RJ (só ele), como as rotas /x/export e /x_RJ/export da v1.
    `nome`: a função de v1_legado_export (lida na hora, para o teste poder trocar)."""

    async def linhas(ctx: DashboardContext) -> list[dict[str, Any]]:
        if ctx.unit_ref not in ("NG", "RJ"):
            raise NotReady("Exportação não existe na v1 para esta unidade")
        return await chamar_v1(
            ctx,
            copia_ng,
            getattr(v1, nome),
            ctx.period.start,
            ctx.period.end,
            *filtros(ctx),
            excluir_rj=ctx.unit_ref != "RJ",
        )

    return linhas


def _la(nome: str, filtros: Callable[[DashboardContext], list[Any]]) -> Linhas:
    """As linhas da LA (banco laadv), como a rota /x_LA/export da v1."""

    async def linhas(ctx: DashboardContext) -> list[dict[str, Any]]:
        return await chamar_v1(
            ctx, copia_la, getattr(v1, nome), ctx.period.start, ctx.period.end, *filtros(ctx)
        )

    return linhas


def _spec(campos: str, aba: str, ng_rj: Linhas, la: Linhas) -> ExportSpec:
    """O relatório da NG/RJ e, na LA, o dela (outros campos e outra aba, como na v1)."""
    return ExportSpec(
        fields=getattr(v1, f"_CAMPOS_EXPORT_{campos}_NG"),
        labels=getattr(v1, f"_LABELS_EXPORT_{campos}_NG"),
        sheet_name=aba,
        rows=ng_rj,
        por_unidade={
            "LA": ExportSpec(
                fields=getattr(v1, f"_CAMPOS_EXPORT_{campos}_LA"),
                labels=getattr(v1, f"_LABELS_EXPORT_{campos}_LA"),
                sheet_name=f"{aba} LA",
                rows=la,
            )
        },
    )


PROTOCOLO = _spec(
    "PROTOCOLO",
    "Protocolo",
    _ng_rj(
        "_rows_protocolo_filtradas",
        lambda c: [
            _lista(c, "materia"),
            _lista(c, "funcionario"),
            _um(c, "sistema"),
            _lista(c, "uf_protocolo"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
    _la(
        "_rows_protocolo_la_filtradas",
        lambda c: [
            _lista(c, "materia"),
            _lista(c, "funcionario"),
            _um(c, "sistema"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
)

PETICIONAMENTO = _spec(
    "PETICIONAMENTO",
    "Peticionamento",
    _ng_rj(
        "_rows_peticionamento_filtradas",
        lambda c: [
            _lista(c, "materia"),
            _lista(c, "funcionario"),
            _um(c, "uf_peticionamento"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
    _la(
        "_rows_peticionamento_la_filtradas",
        lambda c: [
            _lista(c, "materia"),
            _lista(c, "funcionario"),
            _um(c, "uf_peticionamento_LA"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
)

ORG_DOC = _spec(
    "ORG_DOC",
    "Org Doc",
    _ng_rj(
        "_rows_org_doc_filtradas",
        lambda c: [
            _lista(c, "materia"),
            _lista(c, "funcionario"),
            _um(c, "uf_org_doc"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
    _la(
        "_rows_org_doc_la_filtradas",
        lambda c: [
            _lista(c, "materia"),
            _lista(c, "funcionario"),
            _um(c, "uf_org_doc_LA"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
)

PENDENCIAS = _spec(
    "PENDENCIAS",
    "Pendências",
    _ng_rj(
        "_rows_pendencias_filtradas",
        lambda c: [
            _lista(c, "funcionario"),
            _um(c, "uf_pendencias"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
    _la(
        "_rows_pendencias_la_filtradas",
        lambda c: [
            _lista(c, "funcionario"),
            _um(c, "uf_pendencia_LA"),
            _lista(c, "area_atuacao_id"),
        ],
    ),
)
