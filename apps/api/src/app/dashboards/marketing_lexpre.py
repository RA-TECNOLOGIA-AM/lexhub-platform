"""Marketing (LexPre) — dashboard da v1 /marketing_lexpre_NG e /marketing_lexpre_LA, ligado à casca da V2.

Corpo do ramo `marketing_lexpre_NG`/`marketing_lexpre_LA` de `_get_dashboard_response`
(api_dashboards/src/app/dashboard_routes.py) copiado SEM mudar a lógica, com os mesmos nomes da v1; o cálculo
fica em app/analyses/NG/marketing_lexpre.py (cópia da v1). Só a entrada mudou:
    escritorio (ESCRITORIO_NGAM/LAAM)          -> int(ctx.unit_ref)             (app.unit_source_refs, lexpre)
    from_date / to_date                        -> ctx.period.start / end
    _f(chave) / _a(chave)                      -> filter_data(chave, linhas, período) / as linhas sem filtro
    fetch_facebook_ads() (banco ng)            -> ctx.extra_sources["ng"] (só a NG tem o banco ng ligado;
                                                  na LA a v1 só usava campanhas "[LA]", que não existem: zero)
    selection_dim / selection_value (pares)    -> um filtro por dimensão (sufixo _marketing; ver FILTROS)

Exportação (v1: /marketing-lexpre/export e /marketing-lexpre-la/export): o relatório "Leads" (principal) e o
"Facebook Ads" (?relatorio=facebook), cujo detalhamento a v1 escolhia pelas colunas marcadas; aqui, pela opção
"Detalhamento" da janela, já que a casca escolhe as colunas depois de buscar as linhas.
"""

from typing import Any

from app.analyses.NG.comercial_lexpre import (
    build_mapa_rubricas_reunidas as build_mapa_rubricas_reunidas_comercial_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    _FIELD_MAP_CLIENTES as _FIELD_MAP_CLIENTES_LEXPRE,
)
from app.analyses.NG.marketing_lexpre import (
    CAMPOS_EXPORT as CAMPOS_EXPORT_MARKETING_LEXPRE,
)
from app.analyses.NG.marketing_lexpre import (
    CAMPOS_EXPORT_FACEBOOK as CAMPOS_EXPORT_FACEBOOK_MARKETING_LEXPRE,
)
from app.analyses.NG.marketing_lexpre import (
    ESCRITORIO_LAAM as ESCRITORIO_LAAM_MARKETING_LEXPRE,
)
from app.analyses.NG.marketing_lexpre import (
    METRICAS_EXPORT_FACEBOOK,
    get_marketing_lexpre_ng_aquisicao_stats,
    get_marketing_lexpre_ng_stats,
)
from app.analyses.NG.marketing_lexpre import (
    apply_selection_filters as apply_selection_filters_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    filtrar_triados as filtrar_triados_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_analise_aquisicao as get_analise_aquisicao_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_facebook_ads_stats as get_facebook_ads_stats_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_fechamento_campanhas as get_fechamento_campanhas_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_linhas_export as get_linhas_export_marketing_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_linhas_facebook_ads_export as get_linhas_facebook_ads_export_marketing_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_media_idade as get_media_idade_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_organico as get_organico_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    get_total_clientes as get_total_clientes_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_faixa_etaria as group_faixa_etaria_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_faixa_salarial as group_faixa_salarial_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_genero as group_genero_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_investimento_cliques_leads as group_investimento_cliques_leads_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_ocupacao as group_ocupacao_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_origem as group_origem_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_pessoas_dependentes as group_pessoas_dependentes_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_prospeccao as group_prospeccao_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_tipo_residencia as group_tipo_residencia_lexpre,
)
from app.analyses.NG.marketing_lexpre import (
    group_tipo_trafego as group_tipo_trafego_lexpre,
)
from app.analyses.v1_dashboard_generico_ng import filter_data
from app.dashboards.base import DashboardContext, DashboardModule, ExportOption, ExportSpec
from app.database import SourceUnavailable

# v1: QUERY_MAP["marketing_lexpre_NG"] (as mesmas nas duas unidades; o recorte de escritório é no cálculo).
QUERIES = (
    "perfil_clientes_lexpre",
    "comercial_lexpre_NG",
    "demanda_rubrica_reunida_lexpre_NG",
    "log_setor_demanda_lexpre_NG",
)
# metrics_ads.facebook_ads (banco ng): sem coluna de escritório; as contas são da NG.
QUERY_FACEBOOK = "facebook_ads"

# Dimensões do drill-down da v1 (selection_dim) -> filtro da V2 (o nome da URL leva o sufixo _marketing para
# não se confundir com os filtros de outros dashboards, ex.: `rubrica` do Comercial, que aceita um valor só).
FILTROS = {
    "faixa_etaria_marketing": "faixa_etaria",
    "canal_aquisicao_marketing": "canal_aquisicao",
    "genero_marketing": "genero",
    "tipo_trafego_marketing": "tipo_trafego",
    "ocupacao_marketing": "ocupacao",
    "prospeccao_marketing": "prospeccao",
    "tipo_residencia_marketing": "tipo_residencia",
    "pessoas_dependentes_marketing": "pessoas_dependentes",
    "rubrica_marketing": "rubrica",
    "categoria_marketing": "categoria",
    "posicionamento_marketing": "posicionamento",
    "campanha_marketing": "campanha",
    "conjunto_marketing": "conjunto",
    "criativo_marketing": "criativo",
}


def selection_pairs(filters: dict[str, list[Any]]) -> list[tuple[str, str]]:
    """Os pares (dimensão, valor) da v1 (zip de selection_dim e selection_value) a partir dos filtros da V2."""
    return [(dim, str(v)) for chave, dim in FILTROS.items() for v in filters.get(chave, [])]


def _facebook_ads_do_escritorio_marketing_lexpre(
    rows: list[dict[str, Any]],
    escritorio_id: int,
) -> list[dict[str, Any]]:
    """v1: dashboard_routes.py, mesmo nome (sem mudança).

    Recorte de metrics_ads.facebook_ads por escritório, para o Marketing (LexPre).
    A tabela não tem coluna de escritório: as contas (Ca01/Ca02) são do NG. O LA usa
    só campanhas com prefixo "[LA]" — hoje nenhuma (a conta de anúncios do LA ainda
    não é ingerida), então os indicadores de anúncio do LA ficam zerados. O NG
    segue com a tabela inteira. Usado pelo dashboard e pelo export.
    """
    if escritorio_id == ESCRITORIO_LAAM_MARKETING_LEXPRE:
        return [r for r in rows if str(r.get("campaign") or "").strip().upper().startswith("[LA]")]
    return rows


async def _facebook_ads(ctx: DashboardContext) -> list[dict[str, Any]]:
    """As linhas do Facebook Ads (banco ng), todas as datas. V2: unidade sem o banco ng da NG ligado (LA) ou
    com ele fora do ar = sem anúncios (os indicadores de anúncio ficam zerados, como a LA já ficava na v1)."""
    fonte = ctx.extra_sources.get("ng")
    # As contas de anúncio são da NG: o RJ, que também lê o banco ng, não leva os anúncios dela.
    if fonte is None or ctx.extra_refs.get("ng") != "NG":
        return []
    try:
        return await fonte.fetch(QUERY_FACEBOOK)
    except SourceUnavailable:
        return []


async def build(ctx: DashboardContext) -> dict[str, Any]:
    # --- entrada (V2) ---
    escritorio_marketing_lexpre = int(ctx.unit_ref)
    from_date, to_date = ctx.period.start, ctx.period.end
    marketing_selection_pairs = selection_pairs(ctx.filters)
    perfil_rows = await ctx.source.fetch("perfil_clientes_lexpre")
    comercial_rows = await ctx.source.fetch("comercial_lexpre_NG")
    reunidas_rows = await ctx.source.fetch("demanda_rubrica_reunida_lexpre_NG")
    log_setor_rows = await ctx.source.fetch("log_setor_demanda_lexpre_NG")
    facebook_raw = await _facebook_ads(ctx)

    # v1: _f / _a (filtro de data da v1 por fonte: ENTRADA no perfil, date no Facebook Ads)
    def _f(chave: str) -> list[dict[str, Any]]:
        if chave == "marketing_lexpre_NG":
            return filter_data(chave, perfil_rows, from_date, to_date)
        return filter_data(chave, facebook_raw, from_date, to_date)

    _a = {
        "comercial_lexpre_ng": comercial_rows,
        "demanda_rubrica_reunida_lexpre": reunidas_rows,
        "log_setor_demanda_lexpre_ng": log_setor_rows,
    }.__getitem__

    # --- v1: ramo marketing_lexpre_NG / marketing_lexpre_LA (sem mudança daqui para baixo) ---
    clientes = apply_selection_filters_lexpre(
        _f("marketing_lexpre_NG"),
        marketing_selection_pairs,
        _FIELD_MAP_CLIENTES_LEXPRE,
        escritorio_marketing_lexpre,
    )
    triados = filtrar_triados_lexpre(clientes)
    stats = get_marketing_lexpre_ng_stats(clientes)
    stats["marketing_lexpre_ng_triados_total_clientes"] = get_total_clientes_lexpre(triados)
    stats["marketing_lexpre_ng_triados_media_idade"] = get_media_idade_lexpre(triados)
    facebook_ads_rows = _facebook_ads_do_escritorio_marketing_lexpre(
        _f("facebook_ads"), escritorio_marketing_lexpre
    )
    comercial_rows = _a("comercial_lexpre_ng")
    stats.update(get_facebook_ads_stats_lexpre(facebook_ads_rows))
    stats.update(
        get_marketing_lexpre_ng_aquisicao_stats(
            comercial_rows, facebook_ads_rows, from_date, to_date, escritorio_marketing_lexpre
        )
    )
    # Fechamento Campanhas: clientes pelas regras do Comercial LexPre, protocolados
    # pelas do dashboard Protocolo LexPre (log de setor). O drill-down de rubrica
    # só recorta esta seção (igual ao marketing_NG).
    mapa_rubricas_reunidas_lexpre = build_mapa_rubricas_reunidas_comercial_lexpre(
        _a("demanda_rubrica_reunida_lexpre")
    )
    campanhas_stats, campanhas_charts = get_fechamento_campanhas_lexpre(
        comercial_rows,
        _a("log_setor_demanda_lexpre_ng"),
        from_date,
        to_date,
        mapa_rubricas_reunidas_lexpre,
        rubrica=[v for d, v in marketing_selection_pairs if d == "rubrica"],
        escritorio_id=escritorio_marketing_lexpre,
    )
    stats.update(campanhas_stats)
    # Ind. Performance de MKT: CPL = valor gasto (Facebook) ÷ leads de campanha.
    leads_campanha = stats["marketing_lexpre_ng_leads_campanha"]
    stats["marketing_lexpre_ng_cpl_campanha"] = (
        round(stats["marketing_lexpre_ng_facebook_valor_gasto"] / leads_campanha, 2)
        if leads_campanha
        else 0.0
    )
    aquisicao_stats, aquisicao_charts = get_analise_aquisicao_lexpre(
        comercial_rows, from_date, to_date, marketing_selection_pairs, escritorio_marketing_lexpre
    )
    stats.update(aquisicao_stats)
    organico_stats, organico_charts = get_organico_lexpre(
        comercial_rows,
        _a("log_setor_demanda_lexpre_ng"),
        from_date,
        to_date,
        mapa_rubricas_reunidas_lexpre,
        marketing_selection_pairs,
        escritorio_marketing_lexpre,
    )
    stats.update(organico_stats)
    charts = {
        "marketing_lexpre_ng_faixa_etaria": group_faixa_etaria_lexpre(clientes),
        "marketing_lexpre_ng_genero": group_genero_lexpre(clientes),
        "marketing_lexpre_ng_origem": group_origem_lexpre(clientes),
        "marketing_lexpre_ng_ocupacao": group_ocupacao_lexpre(clientes),
        "marketing_lexpre_ng_tipo_trafego": group_tipo_trafego_lexpre(clientes),
        "marketing_lexpre_ng_prospeccao": group_prospeccao_lexpre(clientes),
        "marketing_lexpre_ng_faixa_salarial": group_faixa_salarial_lexpre(clientes),
        "marketing_lexpre_ng_triados_faixa_etaria": group_faixa_etaria_lexpre(triados),
        "marketing_lexpre_ng_triados_genero": group_genero_lexpre(triados),
        "marketing_lexpre_ng_triados_origem": group_origem_lexpre(triados),
        "marketing_lexpre_ng_triados_ocupacao": group_ocupacao_lexpre(triados),
        "marketing_lexpre_ng_triados_tipo_trafego": group_tipo_trafego_lexpre(triados),
        "marketing_lexpre_ng_triados_prospeccao": group_prospeccao_lexpre(triados),
        "marketing_lexpre_ng_triados_faixa_salarial": group_faixa_salarial_lexpre(triados),
        "marketing_lexpre_ng_triados_tipo_residencia": group_tipo_residencia_lexpre(triados),
        "marketing_lexpre_ng_triados_pessoas_dependentes": group_pessoas_dependentes_lexpre(
            triados
        ),
        "marketing_lexpre_ng_investimento_cliques_leads": group_investimento_cliques_leads_lexpre(
            facebook_ads_rows
        ),
        **campanhas_charts,
        **aquisicao_charts,
        **organico_charts,
    }
    # V2: o nome da v1 (as chaves seguem com o prefixo marketing_lexpre_ng_ nas duas unidades, como na v1).
    nome_v1 = (
        "marketing_lexpre_LA"
        if escritorio_marketing_lexpre == ESCRITORIO_LAAM_MARKETING_LEXPRE
        else "marketing_lexpre_NG"
    )
    return {"dashboard": nome_v1, "stats": stats, "charts": charts}


# --- Exportação ---


async def export_leads(ctx: DashboardContext) -> list[dict[str, Any]]:
    """v1: _linhas_leads_marketing_lexpre — uma linha por lead do período, com o drill-down da página."""
    return get_linhas_export_marketing_lexpre(
        await ctx.source.fetch("comercial_lexpre_NG"),
        await ctx.source.fetch("perfil_clientes_lexpre"),
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"),
        ctx.period.start,
        ctx.period.end,
        build_mapa_rubricas_reunidas_comercial_lexpre(
            await ctx.source.fetch("demanda_rubrica_reunida_lexpre_NG")
        ),
        selection_pairs(ctx.filters),
        int(ctx.unit_ref),
    )


# Detalhamento da aba Facebook Ads: na v1, as dimensões marcadas entre as colunas. Valor -> dimensões.
_POR_CAMPANHA = ("conta", "id_conta", "campanha", "campaign_id")
_POR_CONJUNTO = (*_POR_CAMPANHA, "conjunto", "adset_id")
_POR_ANUNCIO = (*_POR_CONJUNTO, "anuncio", "ad_id")
DETALHAMENTO_FACEBOOK = {
    "anuncio": _POR_ANUNCIO,
    "conjunto": _POR_CONJUNTO,
    "campanha": _POR_CAMPANHA,
    "dia": ("data", *_POR_ANUNCIO),
    "total": (),
}


async def export_facebook(ctx: DashboardContext) -> list[dict[str, Any]]:
    """v1: _linhas_facebook_ads_marketing_lexpre — período e escritório (não segue o drill-down, como na v1)."""
    escritorio_id = int(ctx.unit_ref)
    facebook_rows = _facebook_ads_do_escritorio_marketing_lexpre(
        filter_data("facebook_ads", await _facebook_ads(ctx), ctx.period.start, ctx.period.end),
        escritorio_id,
    )
    dims = DETALHAMENTO_FACEBOOK[ctx.export_options.get("detalhamento", "anuncio")]
    _, linhas = get_linhas_facebook_ads_export_marketing_lexpre(
        facebook_rows,
        await ctx.source.fetch("comercial_lexpre_NG"),
        ctx.period.start,
        ctx.period.end,
        escritorio_id,
        [*dims, *METRICAS_EXPORT_FACEBOOK],
    )
    return linhas


MODULE = DashboardModule(
    key="marketing-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    queries=QUERIES,
    extra_queries={"ng": (QUERY_FACEBOOK,)},
    filters=dict.fromkeys(FILTROS, str),
    export=ExportSpec(
        fields={slug: slug for slug in CAMPOS_EXPORT_MARKETING_LEXPRE},
        labels=CAMPOS_EXPORT_MARKETING_LEXPRE,
        sheet_name="Leads",
        rows=export_leads,
        title="Leads",
    ),
    export_reports={
        "facebook": ExportSpec(
            fields={slug: slug for slug in CAMPOS_EXPORT_FACEBOOK_MARKETING_LEXPRE},
            labels=CAMPOS_EXPORT_FACEBOOK_MARKETING_LEXPRE,
            sheet_name="Facebook Ads",
            rows=export_facebook,
            title="Facebook Ads",
            options=(
                ExportOption(
                    key="detalhamento",
                    label="Detalhamento",
                    choices={
                        "anuncio": "Por anúncio",
                        "conjunto": "Por conjunto",
                        "campanha": "Por campanha",
                        "dia": "Por dia e anúncio",
                        "total": "Só o total",
                    },
                ),
            ),
        ),
    },
)
