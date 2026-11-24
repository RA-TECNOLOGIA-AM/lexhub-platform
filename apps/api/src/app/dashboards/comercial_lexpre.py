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

import calendar
from datetime import date, datetime
from typing import Any  # Optional: anotação do corpo da v1 (_canal_stat)
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.analyses.LA.protocolo_LA import (
    get_valor_causa_protocolado_LA_2026,
    get_valor_causa_protocolado_por_atendente_LA,
)
from app.analyses.NG.comercial_lexpre import (
    _expandir_ids_para_contagem as _expandir_ids_para_contagem_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    _is_assinado as _is_assinado_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    _to_date as _to_date_comercial_lexpre,
)
from app.analyses.NG.comercial_lexpre import (
    _valor_am_por_componente as _valor_am_por_componente_comercial_lexpre,
)
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
    listar_demandas_canceladas_desconto as listar_demandas_canceladas_desconto_lexpre,
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
from app.analyses.NG.ml.meta_inteligente import calcular_meta_inteligente_por_atendente
from app.analyses.NG.protocolo import (
    get_valor_causa_protocolo_2026,
    get_valor_causa_protocolo_novo_por_atendente,
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
    get_registros_para_meta_inteligente as get_registros_para_meta_inteligente_lexpre,
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
from app.analyses.v1_dashboard_generico_ng import _filtrar_dados_ng_por_uf, filter_data
from app.analyses.v1_routes import (
    ChartDataPoint,
    ComercialLexpreCanalStat,
    ComercialLexpreComissionamentoAtendenteRow,
    ComercialLexpreDemandaCanceladaDesconto,
    ComercialLexpreFilaPreProtocoloItem,
    ComercialLexpreNGResponse,
    ComercialLexpreNGStats,
    ComercialLexpreRatioStat,
    ComercialLexpreValorCausaPorAtendenteItem,
)
from app.dashboards import pre_protocolo
from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec
from app.dashboards.identidade_v1 import get_atendente_vinculado, is_gestor_ou_desenvolvedor
from app.database import SourceUnavailable

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
    rows_escritorio = (
        rows  # V2: a Meta Inteligente usa o escritório inteiro, sem os filtros (como a v1)
    )
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
    demandas_canceladas_desconto = listar_demandas_canceladas_desconto_lexpre(
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
            demandas_canceladas_desconto=[
                ComercialLexpreDemandaCanceladaDesconto(**x)
                for x in demandas_canceladas_desconto
            ],
        )
    )
    # --- saída (V2): o JSON da v1 + opcoes_filtro ---
    result = {**response.model_dump(), "opcoes_filtro": opcoes}
    if not escopo_proprio:
        # V2: o card "Meta Inteligente por Atendente" da v1 (antes GET /comercial-lexpre/ml/meta_inteligente),
        # já com as três janelas do seletor (últimos 3, 6 e 12 meses). Ignora período e filtros, como na v1.
        result["meta_inteligente"] = meta_inteligente_por_janela(rows_escritorio)
        # V2: a soma com o banco legado que o front da v1 fazia com duas rotas a mais
        # (GET /comercial-lexpre[-la]/valor_causa_protocolado_legado e .../por_atendente_legado).
        result.update(await protocolado_legado(ctx, from_date, to_date))
    return result


# Banco legado de cada unidade (o protocolado antes da migração para o LexPre), como na v1:
# NG -> banco `ng` (setor_protocolo); LA -> banco `laadv` (setor_protocolo_LA). O RJ não somava na v1.
LEGADO = {
    "ng": ("NG", "setor_protocolo", "protocolos"),
    "laadv": ("LA", "setor_protocolo_LA", "protocolo_LA"),
}


async def protocolado_legado(ctx: DashboardContext, from_date: Any, to_date: Any) -> dict[str, Any]:
    """Valor de causa protocolado no banco legado da unidade: no ano (meta anual; 2026 fixo e sem filtros,
    como na v1) e por atendente no período (Meta por Atendente; chave = primeiro nome, a mesma do LexPre).

    `valor_causa_protocolado_legado` = None quando a unidade não tem legado ligado ou ele está fora do ar
    (a página segue só com o LexPre e avisa)."""
    for db, (unidade, query, chave_periodo) in LEGADO.items():
        fonte = ctx.extra_sources.get(db)
        if fonte is None or ctx.extra_refs.get(db) != unidade:
            continue
        try:
            protocolos = await fonte.fetch(query)
        except SourceUnavailable:
            break
        periodo = filter_data(chave_periodo, protocolos, from_date, to_date)
        if db == "ng":
            ano = get_valor_causa_protocolo_2026(protocolos)
            # V2: o banco ng tem NG e RJ juntos; a Meta por Atendente do NG não mostra quem é do RJ
            # (mesmo corte do Protocolo NG da v1: sem os protocolos de UF RJ).
            periodo_ng = _filtrar_dados_ng_por_uf({"protocolos": periodo}, "RJ", excluir=True)
            por_atendente = get_valor_causa_protocolo_novo_por_atendente(periodo_ng["protocolos"])
        else:
            ano = get_valor_causa_protocolado_LA_2026(protocolos)
            por_atendente = get_valor_causa_protocolado_por_atendente_LA(periodo)
        return {
            "valor_causa_protocolado_legado": ano,
            "valor_causa_protocolado_por_atendente_legado": por_atendente,
        }
    return {
        "valor_causa_protocolado_legado": None,
        "valor_causa_protocolado_por_atendente_legado": {},
    }


# Meta do trimestre usada pela v1 no card (metaGlobal={12_000_000}): distribuída entre os atendentes
# pela participação de cada um (meta_proporcional).
META_TRIMESTRAL_COMERCIAL = 12_000_000.0
JANELAS_META_INTELIGENTE = (3, 6, 12)


def meta_inteligente_por_janela(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """{"3": ..., "6": ..., "12": ...}: a resposta da v1 para cada janela de meses de histórico."""
    registros = get_registros_para_meta_inteligente_lexpre(rows)
    return {
        str(meses): calcular_meta_inteligente_por_atendente(
            comercial_geral=registros,
            meses_historico=meses,
            stretch_goal_pct=0.10,
            meta_global_periodo=META_TRIMESTRAL_COMERCIAL,
        )
        for meses in JANELAS_META_INTELIGENTE
    }


# v1: dashboard_routes.py:17057 / 17075 (_CAMPOS_EXPORT_COMERCIAL_LEXPRE_NG e _LABELS_...), sem mudança:
# as colunas da query comercial_lexpre_NG.
CAMPOS_EXPORT = {
    "id_action": "ID_ACTION",
    "cliente": "CLIENTE",
    "atendente": "ATENDENTE",
    "uf": "UF",
    "canal_aquisicao": "CANAL_AQUISICAO",
    "motivo_encerramento": "MOTIVO_ENCERRAMENTO",
    "assinatura": "DATA_ASSINATURA",
    "rubrica": "RUBRICA",
    "area_atuacao": "AREA_ATUACAO_NOME",
    "valor_am": "VALOR_AM",
    "status_demanda": "STATUS_DEMANDA",
    "valor_causa": "VALOR_CAUSA",
    "numero_processo": "NUMERO_PROCESSO",
    "data_protocolo": "DATA_PROTOCOLO",
    "setor": "SETOR_NOME",
}
LABELS_EXPORT = {
    "id_action": "ID do Atendimento",
    "cliente": "Nome do Cliente",
    "atendente": "Atendente",
    "uf": "UF",
    "canal_aquisicao": "Canal de Aquisição",
    "motivo_encerramento": "Motivo de Encerramento",
    "assinatura": "Data de Assinatura",
    "rubrica": "Rubrica",
    "area_atuacao": "Área de Atuação",
    "valor_am": "Valor (R$)",
    "status_demanda": "Status da Demanda",
    "valor_causa": "Valor de Causa (R$)",
    "numero_processo": "Número do Processo",
    "data_protocolo": "Data de Protocolo",
    "setor": "Setor",
}


# v1: dashboard_routes.py:17188 (_build_comercial_lexpre_export, aba principal)
async def export_rows(ctx: DashboardContext, escopo_proprio: bool = False) -> list[dict[str, Any]]:
    """As demandas assinadas no período (DATA_ASSINATURA), com os filtros da página, como a aba principal do
    export da v1. Rubrica reunida (pacote) vira uma linha por componente, com o nome e o VALOR_AM dele.
    A v1 tinha uma segunda aba ("Valor Protocolado (FM)"); a casca da V2 exporta uma aba só."""
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    from_date, to_date = ctx.period.start, ctx.period.end
    segmento_comercial = next(iter(ctx.filters["segmento_comercial"]), None)
    rubrica = next(iter(ctx.filters["rubrica"]), None)

    # --- v1: _rows_filtradas_comercial_lexpre (sem mudança) ---
    rows = filter_comercial_lexpre_por_escritorio_ng(
        await ctx.source.fetch("comercial_lexpre_NG"), escritorio_id=escritorio_id
    )
    rows = filter_comercial_lexpre_por_atendentes_ng(rows, ctx.filters["atendente_comercial"])
    rows = filter_comercial_lexpre_por_area_atuacao_ng(rows, ctx.filters["area_atuacao_id"])
    rows = filter_comercial_lexpre_por_uf_ng(rows, ctx.filters["uf"])
    try:
        rows = filter_comercial_lexpre_por_segmento_ng(rows, segmento_comercial)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    demanda_rubrica_reunida_raw = await ctx.source.fetch("demanda_rubrica_reunida_lexpre_NG")
    mapa_rubricas_reunidas = build_mapa_rubricas_reunidas_comercial_lexpre(
        demanda_rubrica_reunida_raw
    )
    mapa_valor_rubrica_associada = build_mapa_valor_rubrica_associada_comercial_lexpre(
        demanda_rubrica_reunida_raw
    )
    rows = filter_comercial_lexpre_por_rubrica_ng(rows, rubrica, mapa_rubricas_reunidas)

    # Comissão Comercial: quem não é Gestor/Desenvolvedor exporta só as próprias linhas (como a v1).
    usuario_logado = ctx  # V2: identidade vem da casca (ver identidade_v1.py)
    if escopo_proprio and not is_gestor_ou_desenvolvedor(usuario_logado):
        atendente_vinculado = await get_atendente_vinculado(usuario_logado)
        rows = (
            filter_comercial_lexpre_por_atendentes_ng(rows, [atendente_vinculado])
            if atendente_vinculado
            else []
        )

    # --- v1: _filtrar_rows_por_assinatura_comercial_lexpre (sem mudança) ---
    def _no_periodo(row: dict[str, Any]) -> bool:
        if not _is_assinado_comercial_lexpre(row):
            return False
        data_assinatura = _to_date_comercial_lexpre(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            return False
        if from_date and data_assinatura < from_date:
            return False
        if to_date and data_assinatura > to_date:  # noqa: SIM103 (igual à v1)
            return False
        return True

    # --- v1: _registros_export_comercial_lexpre (a expansão das rubricas reunidas) ---
    # V2: devolve a linha da query com RUBRICA/VALOR_AM do componente (a casca escolhe as colunas).
    registros: list[dict[str, Any]] = []
    for row in (r for r in rows if _no_periodo(r)):
        componentes = _expandir_ids_para_contagem_comercial_lexpre(row, mapa_rubricas_reunidas)
        for _sub_id, nome_componente in componentes:
            registros.append(
                {
                    **row,
                    "RUBRICA": nome_componente,
                    "VALOR_AM": _valor_am_por_componente_comercial_lexpre(
                        row, nome_componente, mapa_valor_rubrica_associada
                    ),
                }
            )
    return registros


# --- V2: prévia do que ainda pode ser protocolado (modal "Ritmo da meta" do card Meta <ano>) ---

# Represados de cada setor do Pré-protocolo: o campo do `stats` de cada módulo LexPre (os mesmos números da
# seção "Represados por setor" do Pré-protocolo, setores.ts).
CAMPO_REPRESADOS = {
    "pendencias": "pendencias_nao_resolvidas",
    "org_documentos": "represados",
    "peticionamento": "represados",
    "protocolo": "represados",
}
MESES_TICKET_PREVIA = 3


def hoje_manaus() -> date:
    return datetime.now(ZoneInfo("America/Manaus")).date()


def meses_antes(d: date, meses: int) -> date:
    """O mesmo dia `meses` meses civis antes; dia que não existe no mês vira o último (31/05 - 3 = 28/02)."""
    total = d.year * 12 + d.month - 1 - meses
    ano, mes = divmod(total, 12)
    mes += 1
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def _numero(stats: Any, campo: str) -> int:
    v = stats.get(campo) if isinstance(stats, dict) else getattr(stats, campo, None)
    return int(v) if isinstance(v, (int, float)) else 0


async def previa_represados(ctx: DashboardContext, hoje: date | None = None) -> dict[str, Any]:
    """Quanto ainda pode ser protocolado: o ticket médio protocolado dos últimos 3 meses (de hoje para trás, o
    escritório inteiro, sem os filtros da página, como a meta) × os processos represados nos 4 setores do
    Pré-protocolo agora (Pendência, Org. Documentos, Peticionamento e Protocolo, acumulados, sem data)."""
    hoje = hoje or hoje_manaus()
    de = meses_antes(hoje, MESES_TICKET_PREVIA)
    rows = filter_comercial_lexpre_por_escritorio_ng(
        await ctx.source.fetch("comercial_lexpre_NG"), escritorio_id=int(ctx.unit_ref)
    )
    ticket = get_ticket_medio_protocolado_lexpre(rows, de, hoje)
    setores = await pre_protocolo.build(ctx)
    represados = {
        setor: _numero((setores.get(setor) or {}).get("stats"), campo)
        for setor, campo in CAMPO_REPRESADOS.items()
    }
    total = sum(represados.values())
    return {
        "de": de.isoformat(),
        "ate": hoje.isoformat(),
        "ticket_medio": ticket,
        "represados": represados,
        "total_represados": total,
        "valor": round(ticket * total, 2),
    }


async def build_comercial(ctx: DashboardContext) -> dict:
    """O Comercial (LexPre) da v1 + a prévia dos represados (V2). A Comissão Comercial usa só o `build`."""
    body = await build(ctx)
    body["previa_represados"] = await previa_represados(ctx)
    return body


MODULE = DashboardModule(
    key="comercial-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build_comercial,
    # + as buscas do Pré-protocolo (os represados da prévia), para o aquecedor do cache.
    queries=tuple(dict.fromkeys((*QUERIES, *pre_protocolo.MODULE.queries))),
    extra_queries={db: (query,) for db, (_, query, _) in LEGADO.items()},
    # Mesmos parâmetros da v1 (GET /comercial-lexpre).
    filters={
        "atendente_comercial": str,
        "segmento_comercial": str,
        "area_atuacao_id": int,
        "uf": str,
        "rubrica": str,
    },
    export=ExportSpec(
        fields=CAMPOS_EXPORT,
        labels=LABELS_EXPORT,
        sheet_name="Comercial (LexPre)",
        rows=export_rows,
    ),
)
