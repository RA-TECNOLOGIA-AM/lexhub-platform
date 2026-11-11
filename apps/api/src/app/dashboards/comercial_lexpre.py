"""Comercial (LexPre) — cálculo da v1 ligado à casca da V2.

Corpo de `_build_comercial_lexpre_response` (api_dashboards/src/app/dashboard_routes.py) copiado SEM mudar
a lógica, com os mesmos nomes da v1. Só a entrada mudou (mesmas trocas do protocolo_lexpre.py), mais:
    fetch_comercial_lexpre_ng() etc.          -> ctx.source.fetch("comercial_lexpre_NG") etc.
    segmento_comercial, rubrica (um valor)    -> o 1º valor de ctx.filters[...]
    usuario_logado / escopo_proprio           -> ctx / parâmetro de build (identidade_v1.py)
Na v1 o mesmo endpoint serve o Comercial e a Comissão Comercial (esta com escopo_proprio=True).
Exportar ainda não: o export da v1 tem duas abas (assinadas + "Valor Protocolado (FM)") e a casca
da V2 exporta uma aba só.
Novo na V2: `opcoes_filtro` (antes dos filtros).
"""

from datetime import datetime
from typing import Any  # Optional: anotação do corpo da v1 (_canal_stat)

from fastapi import HTTPException

from app.analyses.NG.comercial_lexpre import (
    build_mapa_rubricas_reunidas as build_mapa_rubricas_reunidas_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    build_mapa_valor_rubrica_associada as build_mapa_valor_rubrica_associada_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    filter_comercial_lexpre_por_area_atuacao as filter_comercial_lexpre_por_area_atuacao_ng,
)
from app.analyses.NG.comercial_lexpre import (
    filter_comercial_lexpre_por_atendentes as filter_comercial_lexpre_por_atendentes_ng,
)
from app.analyses.NG.comercial_lexpre import (
    filter_comercial_lexpre_por_escritorio as filter_comercial_lexpre_por_escritorio_ng,
)
from app.analyses.NG.comercial_lexpre import (
    filter_comercial_lexpre_por_rubrica as filter_comercial_lexpre_por_rubrica_ng,
)
from app.analyses.NG.comercial_lexpre import (
    filter_comercial_lexpre_por_segmento as filter_comercial_lexpre_por_segmento_ng,
)
from app.analyses.NG.comercial_lexpre import (
    filter_comercial_lexpre_por_uf as filter_comercial_lexpre_por_uf_ng,
)
from app.analyses.NG.comercial_lexpre import (
    get_acoes_fechadas as get_acoes_fechadas_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_acoes_fechadas_hoje_por_atendente as get_acoes_fechadas_hoje_por_atendente_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_acoes_fechadas_por_rubrica as get_acoes_fechadas_por_rubrica_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_clientes_fechados as get_clientes_fechados_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_clientes_por_canal as get_clientes_por_canal_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_clientes_todos as get_clientes_todos_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_acoes_fechadas as get_comparativo_acoes_fechadas_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_canal as get_comparativo_canal_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_demandas_canceladas as get_comparativo_demandas_canceladas_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_leads_campanha as get_comparativo_leads_campanha_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_taxa_aproveitamento as get_comparativo_taxa_aproveitamento_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_taxa_leads_campanha as get_comparativo_taxa_leads_campanha_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_taxa_leads_geral as get_comparativo_taxa_leads_geral_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_comparativo_total_leads as get_comparativo_total_leads_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_contratos_fechados_hoje_por_atendente as get_contratos_fechados_hoje_por_atendente_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_demandas_canceladas as get_demandas_canceladas_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_leads_campanha_periodo as get_leads_campanha_periodo_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_ranking_acoes_fechadas_por_atendente as get_ranking_acoes_fechadas_por_atendente_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_rubricas_reunidas_fechadas as get_rubricas_reunidas_fechadas_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_tabela_por_atendente as get_tabela_por_atendente_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_taxa_aproveitamento as get_taxa_aproveitamento_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_taxa_leads_campanha as get_taxa_leads_campanha_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_taxa_leads_geral as get_taxa_leads_geral_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_totais_tabela_por_atendente as get_totais_tabela_por_atendente_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_total_leads as get_total_leads_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_total_leads_periodo as get_total_leads_periodo_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    get_valor_causa_protocolado as get_valor_causa_protocolado_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    list_areas_atuacao_comerciais as list_areas_atuacao_comerciais_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    list_atendentes_comerciais as list_atendentes_comerciais_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    list_ufs_comerciais as list_ufs_comerciais_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_comissao_base as get_comissao_base_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_comissao_com_fm as get_comissao_com_fm_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_comissao_com_fm_liquida as get_comissao_com_fm_liquida_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_comissionamento_por_atendente as get_comissionamento_por_atendente_comercial_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_desconto_cancelamentos_periodo_anterior as get_desconto_cancelamentos_periodo_anterior_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_fator_multiplicador as get_fator_multiplicador_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_proporcionais_am_pa_pb_sobre_comissao_com_fm as get_proporcionais_am_pa_pb_lexpre,
)
from app.analyses.NG.comissao_lexpre import (
    get_rubricas_total_tabela as get_rubricas_total_tabela_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_comparativo_protocolados as get_comparativo_protocolados_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_comparativo_ticket_medio_protocolado as get_comparativo_ticket_medio_protocolado_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_comparativo_valor_causa_protocolado as get_comparativo_valor_causa_protocolado_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_fila_pre_protocolo_por_atendente as get_fila_pre_protocolo_por_atendente_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_protocolados as get_protocolados_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_tempo_medio_ate_protocolo_horas as get_tempo_medio_ate_protocolo_horas_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_ticket_medio_protocolado as get_ticket_medio_protocolado_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_valor_causa_por_atendente as get_valor_causa_por_atendente_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_valor_causa_protocolado as get_valor_causa_protocolado_lexpre,
)
from app.analyses.NG.protocolo_lexpre import (
    get_valor_causa_protocolado_por_atendente as get_valor_causa_protocolado_por_atendente_lexpre,
)
from app.analyses.v1_routes import (
    ChartDataPoint,
    ComercialLexpreCanalStat,
    ComercialLexpreComissionamentoAtendenteRow,
    ComercialLexpreFilaPreProtocoloItem,
    ComercialLexpreNGResponse,
    ComercialLexpreNGStats,
    ComercialLexpreRatioStat,
    ComercialLexpreValorCausaPorAtendenteItem,
)
from app.dashboards.base import DashboardContext, DashboardModule
from app.dashboards.identidade_v1 import get_atendente_vinculado, is_gestor_ou_desenvolvedor

QUERIES = (
    "comercial_lexpre_NG",
    "demanda_rubrica_reunida_lexpre_NG",
    "audit_log_demandas_canceladas_lexpre_NG",
)


def opcoes_filtro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Novo na V2: os catálogos dos filtros que a v1 servia em rotas separadas, numa resposta só.

    Mesmas funções de GET /comercial-lexpre/atendentes, /areas_atuacao e /ufs (linhas do escritório,
    antes dos filtros); os canais são os valores aceitos por segmento_comercial.
    """
    return {
        "atendentes": list_atendentes_comerciais_lexpre(rows),
        "areas": list_areas_atuacao_comerciais_lexpre(rows),
        "ufs": list_ufs_comerciais_lexpre(rows),
        "segmentos": list(SEGMENTOS),
    }


# Canais aceitos em segmento_comercial (v1: descrição do parâmetro em GET /comercial-lexpre).
SEGMENTOS = (
    "CAMPANHA",
    "REDES_SOCIAIS",
    "RETORNO",
    "RESGATE",
    "INDICACAO",
    "SITE",
    "PARCEIROS",
    "EXTERNOS",
)


async def build(ctx: DashboardContext, escopo_proprio: bool = False) -> dict:
    """Comercial (geral): escopo_proprio=False, todo mundo vê todo mundo, como na v1.
    A Comissão Comercial chama com escopo_proprio=True (ver comissao_lexpre.py)."""
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    from_date = ctx.period.start
    to_date = ctx.period.end
    atendente_comercial = ctx.filters["atendente_comercial"]
    segmento_comercial = next(iter(ctx.filters["segmento_comercial"]), None)  # v1: um valor só
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]
    rubrica = next(iter(ctx.filters["rubrica"]), None)  # v1: um valor só
    usuario_logado = ctx  # V2: identidade vem da casca (ver identidade_v1.py)

    # --- v1: _build_comercial_lexpre_response (sem mudança daqui para baixo) ---
    rows = filter_comercial_lexpre_por_escritorio_ng(
        await ctx.source.fetch("comercial_lexpre_NG"), escritorio_id=escritorio_id
    )
    opcoes = opcoes_filtro(rows)  # V2: antes dos filtros
    rows = filter_comercial_lexpre_por_atendentes_ng(rows, atendente_comercial)
    rows = filter_comercial_lexpre_por_area_atuacao_ng(rows, area_atuacao_id)
    rows = filter_comercial_lexpre_por_uf_ng(rows, uf)
    try:
        rows = filter_comercial_lexpre_por_segmento_ng(rows, segmento_comercial)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    demanda_rubrica_reunida_raw = await ctx.source.fetch("demanda_rubrica_reunida_lexpre_NG")
    mapa_rubricas_reunidas = build_mapa_rubricas_reunidas_comercial_lexpre(
        demanda_rubrica_reunida_raw
    )
    rows = filter_comercial_lexpre_por_rubrica_ng(rows, rubrica, mapa_rubricas_reunidas)
    mapa_valor_rubrica_associada = build_mapa_valor_rubrica_associada_comercial_lexpre(
        demanda_rubrica_reunida_raw
    )

    # Atendente comercial não-Gestor/Desenvolvedor (ex.: Patricia, Isabelle): a
    # página inteira — todo KPI e gráfico, não só o comissionamento — deve
    # mostrar só os dados dela. Pedido do usuário (01/10/2026): "todo o
    # Dashboard de comissão do comercial deve aparecer os dados dela, todos os
    # gráficos e os KPIs". Em vez de filtrar campo por campo, força o MESMO
    # filtro já usado pelo seletor manual de "Funcionários" (`atendente_comercial`)
    # em cima de `rows` — ignora qualquer `atendente_comercial` vindo da URL
    # (senão dava pra contornar a restrição trocando o parâmetro). Como toda
    # métrica da página deriva de `rows`, isso basta pra escopar tudo (pool de
    # comissão, FM, rubricas, leads, etc.) de uma vez só. Ver
    # usuario_atendente_comercial/app/auth.py. Sem vínculo cadastrado (e não
    # Gestor/Dev) => `rows` vira vazio, a página inteira zera (nega por padrão).
    if (
        escopo_proprio
        and usuario_logado is not None
        and not is_gestor_ou_desenvolvedor(usuario_logado)
    ):
        atendente_vinculado = await get_atendente_vinculado(usuario_logado)
        rows = (
            filter_comercial_lexpre_por_atendentes_ng(rows, [atendente_vinculado])
            if atendente_vinculado
            else []
        )

    ano_atual = datetime.now().year

    comissao_base = get_comissao_base_lexpre(
        rows, from_date, to_date, mapa_rubricas_reunidas, mapa_valor_rubrica_associada
    )
    fator_multiplicador = get_fator_multiplicador_lexpre(rows, from_date, to_date)
    comissao_com_fm = get_comissao_com_fm_lexpre(
        rows, from_date, to_date, mapa_rubricas_reunidas, mapa_valor_rubrica_associada
    )
    cancelamentos_raw = await ctx.source.fetch("audit_log_demandas_canceladas_lexpre_NG")
    desconto_cancelamentos = get_desconto_cancelamentos_periodo_anterior_lexpre(
        rows,
        cancelamentos_raw,
        from_date,
        to_date,
        mapa_rubricas_reunidas,
        mapa_valor_rubrica_associada,
    )
    comissao_com_fm_liquida = get_comissao_com_fm_liquida_lexpre(
        rows,
        cancelamentos_raw,
        from_date,
        to_date,
        mapa_rubricas_reunidas,
        mapa_valor_rubrica_associada,
    )
    proporcional_am_pa, proporcional_pb = get_proporcionais_am_pa_pb_lexpre(
        rows, comissao_com_fm_liquida, from_date, to_date
    )
    comissionamento_por_atendente = get_comissionamento_por_atendente_comercial_lexpre(
        rows,
        cancelamentos_raw,
        from_date,
        to_date,
        mapa_rubricas_reunidas,
        mapa_valor_rubrica_associada,
    )
    canais_slugs = {
        "total": None,
        "campanha": "CAMPANHA",
        "redes_sociais": "REDES_SOCIAIS",
        "retorno": "RETORNO",
        "resgate": "RESGATE",
        "indicacao": "INDICACAO",
        "site": "SITE",
        "parceiros": "PARCEIROS",
        "externos": "EXTERNOS",
    }
    rubricas_total_tabela = {
        slug: get_rubricas_total_tabela_lexpre(
            rows, canal, from_date, to_date, mapa_rubricas_reunidas, mapa_valor_rubrica_associada
        )
        for slug, canal in canais_slugs.items()
    }

    def _canal_stat(canal: str | None) -> ComercialLexpreCanalStat:
        total = (
            get_clientes_todos_comercial_lexpre(rows, from_date, to_date)
            if canal is None
            else get_clientes_por_canal_comercial_lexpre(rows, canal, from_date, to_date)
        )
        comparativo = get_comparativo_canal_comercial_lexpre(rows, canal, from_date, to_date)
        return ComercialLexpreCanalStat(total=total, comparativo=comparativo)

    response = ComercialLexpreNGResponse(
        stats=ComercialLexpreNGStats(
            total_leads=get_total_leads_comercial_lexpre(rows),
            clientes_fechados=get_clientes_fechados_comercial_lexpre(rows),
            valor_causa_protocolado_ano=get_valor_causa_protocolado_comercial_lexpre(
                rows, ano=ano_atual
            ),
            ano_meta=ano_atual,
            clientes_campanha=_canal_stat("CAMPANHA"),
            clientes_redes_sociais=_canal_stat("REDES_SOCIAIS"),
            clientes_retorno=_canal_stat("RETORNO"),
            clientes_resgate=_canal_stat("RESGATE"),
            clientes_indicacao=_canal_stat("INDICACAO"),
            clientes_site=_canal_stat("SITE"),
            clientes_parceiros=_canal_stat("PARCEIROS"),
            clientes_externos=_canal_stat("EXTERNOS"),
            clientes_todos=_canal_stat(None),
            demandas_canceladas=ComercialLexpreCanalStat(
                total=get_demandas_canceladas_comercial_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_demandas_canceladas_comercial_lexpre(
                    rows, from_date, to_date
                ),
            ),
            acoes_fechadas=ComercialLexpreCanalStat(
                total=get_acoes_fechadas_comercial_lexpre(
                    rows, from_date, to_date, mapa_rubricas_reunidas
                ),
                comparativo=get_comparativo_acoes_fechadas_comercial_lexpre(
                    rows, from_date, to_date, mapa_rubricas_reunidas
                ),
            ),
            rubricas_reunidas_fechadas=get_rubricas_reunidas_fechadas_comercial_lexpre(
                rows, from_date, to_date
            ),
            taxa_aproveitamento=ComercialLexpreRatioStat(
                total=get_taxa_aproveitamento_comercial_lexpre(
                    rows, from_date, to_date, mapa_rubricas_reunidas
                ),
                comparativo=get_comparativo_taxa_aproveitamento_comercial_lexpre(
                    rows, from_date, to_date, mapa_rubricas_reunidas
                ),
            ),
            leads_geral=ComercialLexpreCanalStat(
                total=get_total_leads_periodo_comercial_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_total_leads_comercial_lexpre(rows, from_date, to_date),
            ),
            leads_campanha=ComercialLexpreCanalStat(
                total=get_leads_campanha_periodo_comercial_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_leads_campanha_comercial_lexpre(
                    rows, from_date, to_date
                ),
            ),
            taxa_leads_geral=ComercialLexpreRatioStat(
                total=get_taxa_leads_geral_comercial_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_taxa_leads_geral_comercial_lexpre(
                    rows, from_date, to_date
                ),
            ),
            taxa_leads_campanha=ComercialLexpreRatioStat(
                total=get_taxa_leads_campanha_comercial_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_taxa_leads_campanha_comercial_lexpre(
                    rows, from_date, to_date
                ),
            ),
            ranking_acoes_fechadas_por_atendente=[
                ChartDataPoint(**x)
                for x in get_ranking_acoes_fechadas_por_atendente_comercial_lexpre(
                    rows, from_date, to_date, mapa_reunidas=mapa_rubricas_reunidas
                )
            ],
            acoes_fechadas_hoje_por_atendente=[
                ChartDataPoint(**x)
                for x in get_acoes_fechadas_hoje_por_atendente_comercial_lexpre(
                    rows, mapa_rubricas_reunidas
                )
            ],
            contratos_fechados_hoje_por_atendente=[
                ChartDataPoint(**x)
                for x in get_contratos_fechados_hoje_por_atendente_comercial_lexpre(rows)
            ],
            # "Protocolados"/"Ticket Médio" são contagem de demandas fisicamente
            # protocoladas — NÃO usa mapa_rubricas_reunidas (isso é só pra "Ações
            # Fechadas"/comissão, onde uma demanda "reunida" conta 1x por
            # componente). Passar o mapa aqui inflava a contagem (ex.: 541 em vez
            # dos ~297 reais) — mesmo fix já aplicado em
            # `_build_comercial_lexpre_resumo_estrategico_geral`, propagado aqui
            # em 30/09/2026 (usuário reportou divergência com o Protocolo LexPre).
            protocolados=ComercialLexpreCanalStat(
                total=get_protocolados_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_protocolados_lexpre(rows, from_date, to_date),
            ),
            valor_causa_protocolado=ComercialLexpreRatioStat(
                total=get_valor_causa_protocolado_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_valor_causa_protocolado_lexpre(
                    rows, from_date, to_date
                ),
            ),
            ticket_medio_protocolado=ComercialLexpreRatioStat(
                total=get_ticket_medio_protocolado_lexpre(rows, from_date, to_date),
                comparativo=get_comparativo_ticket_medio_protocolado_lexpre(
                    rows, from_date, to_date
                ),
            ),
            tempo_medio_ate_protocolo_horas=get_tempo_medio_ate_protocolo_horas_lexpre(
                rows, from_date, to_date, mapa_rubricas_reunidas
            ),
            fila_pre_protocolo_por_atendente=[
                ComercialLexpreFilaPreProtocoloItem(**x)
                for x in get_fila_pre_protocolo_por_atendente_lexpre(
                    rows, mapa_reunidas=mapa_rubricas_reunidas
                )
            ],
            valor_causa_por_atendente=[
                ComercialLexpreValorCausaPorAtendenteItem(**x)
                for x in get_valor_causa_por_atendente_lexpre(rows, from_date, to_date)
            ],
            acoes_fechadas_por_rubrica={
                slug: [
                    ChartDataPoint(**x)
                    for x in get_acoes_fechadas_por_rubrica_comercial_lexpre(
                        rows, canal, from_date, to_date, mapa_reunidas=mapa_rubricas_reunidas
                    )
                ]
                for slug, canal in canais_slugs.items()
            },
            tabela_por_atendente=get_tabela_por_atendente_comercial_lexpre(
                rows, from_date, to_date
            ),
            totais_tabela_por_atendente=get_totais_tabela_por_atendente_comercial_lexpre(
                rows, from_date, to_date
            ),
            valor_causa_protocolado_por_atendente_periodo=get_valor_causa_protocolado_por_atendente_lexpre(
                rows, from_date, to_date
            ),
            comissao_base=comissao_base,
            fator_multiplicador=fator_multiplicador,
            comissao_com_fm=comissao_com_fm,
            desconto_cancelamentos=desconto_cancelamentos,
            comissao_com_fm_liquida=comissao_com_fm_liquida,
            proporcional_am_pa=proporcional_am_pa,
            proporcional_pb=proporcional_pb,
            rubricas_total_tabela=rubricas_total_tabela,
            comissionamento_por_atendente=[
                ComercialLexpreComissionamentoAtendenteRow(**x)
                for x in comissionamento_por_atendente
            ],
        )
    )
    # --- saída (V2): o JSON da v1 + opcoes_filtro ---
    return {**response.model_dump(), "opcoes_filtro": opcoes}


MODULE = DashboardModule(
    key="comercial-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    queries=QUERIES,
    # Mesmos parâmetros da v1 (GET /comercial-lexpre).
    filters={
        "atendente_comercial": str,
        "segmento_comercial": str,
        "area_atuacao_id": int,
        "uf": str,
        "rubrica": str,
    },
)
