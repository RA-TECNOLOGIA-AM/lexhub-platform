"""Marketing (banco NG) — dashboard da v1 /marketing_NG, sem mudança. Só existe para a NG na v1.

O cálculo é o da v1, na cópia app/analyses/v1_dashboard_generico_ng.py (handler "marketing_NG") e em
app/analyses/NG/marketing_ng.py. Na v1 a página filtrava clicando nos gráficos e mandava pares
`selection_dim` / `selection_value`; aqui cada dimensão é um filtro da V2 com o sufixo _marketing (os mesmos do
Marketing (LexPre), mais o dispositivo), convertido nos mesmos pares. Vários valores na mesma dimensão = OU.

Novo na V2: desde set/2026 o comercial da NG é registrado no LexPre (o banco NG parou de receber atendimentos em
22/10/2026). A resposta soma os números do Marketing (LexPre) do escritório da NG (marketing_soma_lexpre.py) e diz
em `lexpre` se a soma entrou: {"somado": bool, "motivo": texto quando não entrou}.
"""

from dataclasses import replace

from app.analyses import v1_dashboard_generico_ng as copia
from app.dashboards import generico_v1, marketing_lexpre
from app.dashboards.base import DashboardContext, DashboardModule, NotReady
from app.dashboards.marketing_lexpre import FILTROS as FILTROS_LEXPRE
from app.dashboards.marketing_soma_lexpre import somar_lexpre
from app.database import SourceUnavailable

# Filtro da V2 -> dimensão da v1 (_FIELD_MAP_CLIENTES, _FIELD_MAP_ANALISE_THIAGO e _FIELD_MAP_TRACKEAMENTO).
DIMENSOES = {**FILTROS_LEXPRE, "dispositivo_marketing": "dispositivo"}


def selecao(filters: dict[str, list[str]]) -> tuple[list[str] | None, list[str] | None]:
    """Os pares (dimensão, valor) da v1, um por valor escolhido."""
    dims: list[str] = []
    valores: list[str] = []
    for filtro, dim in DIMENSOES.items():
        for valor in filters.get(filtro) or []:
            if valor:
                dims.append(dim)
                valores.append(str(valor))
    return (dims or None, valores or None)


async def lexpre_da_unidade(ctx: DashboardContext) -> tuple[dict | None, str | None]:
    """O Marketing (LexPre) do escritório da unidade, com o mesmo período e filtros; (None, motivo) sem ele."""
    fonte = ctx.extra_sources.get("lexpre")
    ref = ctx.extra_refs.get("lexpre")
    if fonte is None or ref is None:
        return None, "A unidade não está ligada ao LexPre."
    if ctx.filters.get("dispositivo_marketing"):
        return None, "O LexPre não registra o dispositivo: com esse filtro, só o banco NG."
    lexpre_ctx = replace(
        ctx,
        source=fonte,
        unit_ref=ref,
        source_db="lexpre",
        # O Facebook Ads do LexPre vem do banco ng (o mesmo deste dashboard): CAC e ROAS do LexPre precisam dele.
        extra_sources={"ng": ctx.source},
        extra_refs={"ng": ctx.unit_ref},
    )
    try:
        return await marketing_lexpre.build(lexpre_ctx), None
    except SourceUnavailable:
        return None, "LexPre fora do ar: só os números do banco NG."


async def build(ctx: DashboardContext) -> dict:
    if ctx.unit_ref != "NG":
        raise NotReady("Marketing (banco NG) só existe na v1 para a NG")
    dims, valores = selecao(ctx.filters)
    resposta = await generico_v1.chamar_v1(
        ctx,
        copia,
        copia.HANDLERS["marketing_NG"],
        from_date=ctx.period.start,
        to_date=ctx.period.end,
        selection_dim=dims,
        selection_value=valores,
    )
    corpo = resposta.model_dump()
    lexpre, motivo = await lexpre_da_unidade(ctx)
    if lexpre is None:
        return {**corpo, "lexpre": {"somado": False, "motivo": motivo}}
    return {**somar_lexpre(corpo, lexpre), "lexpre": {"somado": True, "motivo": None}}


MODULE = DashboardModule(
    key="marketing",
    source_db="ng",
    source_label="NG",
    build=build,
    filters=dict.fromkeys(DIMENSOES, str),
    queries=copia.QUERIES_POR_DASHBOARD["marketing_NG"],
    # Novo na V2: o comercial do LexPre (escritório da NG) somado aos números do banco NG.
    extra_queries={"lexpre": marketing_lexpre.QUERIES},
)
