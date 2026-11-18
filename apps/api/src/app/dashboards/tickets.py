"""Tickets (banco NG, tabela Log_tickets_discord) — o dashboard da v1 /tickets (NG/Tickets.tsx), sem mudança.

O cálculo é o da v1, na cópia app/analyses/v1_dashboard_generico_ng.py (handler "tickets") e em
app/analyses/NG/tickets.py. Na v1 a página filtrava clicando nos gráficos e mandava pares
`selection_dim` / `selection_value` (categoria, sub_categoria, status, servidor); aqui cada um é um filtro
da V2 (ticket_categoria, ticket_subcategoria, ticket_status, ticket_servidor), convertido nos mesmos pares.

A tabela tem os tickets dos três servidores do Discord (NG, LA-AM e LA-RJ) e a v1 só tinha a página na NG:
na V2 também só na NG; o servidor é um filtro da própria página.
"""

from app.analyses import v1_dashboard_generico_ng as copia
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, DashboardModule, NotReady

# Filtro da V2 -> dimensão da v1 (apply_ticket_selection_filter), na ordem em que a página da v1 mandava.
DIMENSOES = {
    "ticket_categoria": "categoria",
    "ticket_subcategoria": "sub_categoria",
    "ticket_status": "status",
    "ticket_servidor": "servidor",
}


def selecao(filters: dict[str, list[str]]) -> tuple[list[str] | None, list[str] | None]:
    """Os pares (dimensão, valor) da v1; um valor por dimensão, como a página da v1."""
    dims: list[str] = []
    valores: list[str] = []
    for filtro, dim in DIMENSOES.items():
        valor = next(iter(filters.get(filtro) or []), None)
        if valor:
            dims.append(dim)
            valores.append(valor)
    return (dims or None, valores or None)


async def build(ctx: DashboardContext) -> dict:
    if ctx.unit_ref != "NG":
        raise NotReady("Tickets só existe na NG (como na v1): a tabela já traz os três servidores")
    dims, valores = selecao(ctx.filters)
    resposta = await generico_v1.chamar_v1(
        ctx,
        copia,
        copia.HANDLERS["tickets"],
        from_date=ctx.period.start,
        to_date=ctx.period.end,
        selection_dim=dims,
        selection_value=valores,
    )
    return resposta.model_dump()


MODULE = DashboardModule(
    key="tickets",
    source_db="ng",
    source_label="NG",
    build=build,
    filters=dict.fromkeys(DIMENSOES, str),
    queries=copia.QUERIES_POR_DASHBOARD["tickets"],
)
