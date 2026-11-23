"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (linha na v1 ao lado de cada bloco).
Gerado por scripts/copiar_v1/gerar_generico.py (banco ng). Únicas trocas, marcadas com "V2:":
  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;
  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo;
  * fontes de outro banco saem de FETCHES_BY_DASHBOARD (chegam vazias, como na v1 com a fonte fora do ar).
Dashboards: protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG, nps_NG, tickets.
"""

import asyncio
import logging
import time
from contextvars import ContextVar
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.LA.actions_LA import (
    get_taxa_leads_anuncio_LA,
    get_taxa_leads_geral_LA,
    get_total_leads_LA,
    get_total_leads_anuncio_LA,
)
from app.analyses.LA.andamento_processual_LA import (
    get_andamento_comissionamento_por_funcionario_LA,
    get_andamento_media_avaliacao_LA,
    get_andamento_media_tempo_atendimento_LA,
    get_andamento_media_tempo_espera_LA,
    get_andamento_mediana_tempo_atendimento_LA,
    get_andamento_mediana_tempo_espera_LA,
    get_andamento_nao_resolvido_LA,
    get_andamento_resolvido_LA,
    get_andamento_taxa_nao_resolvidos_LA,
    get_andamento_taxa_resolvidos_LA,
    get_andamento_total_LA,
    group_andamento_processual_by_colaborador_LA,
    group_andamento_processual_by_colaborador_avaliacao_LA,
    group_andamento_processual_total_por_mes_LA,
)
from app.analyses.LA.comercial_LA import (
    _formatar_nome_atendente as _formatar_nome_atendente_LA,
    filter_comercial_LA_por_segmento,
    get_acoes_fechadas_LA,
    get_acoes_fechadas_campanha_LA,
    get_acoes_fechadas_externos_LA,
    get_acoes_fechadas_indicacao_LA,
    get_acoes_fechadas_parceiros_LA,
    get_acoes_fechadas_periodo_anterior_LA,
    get_acoes_fechadas_redes_sociais_LA,
    get_acoes_fechadas_retorno_LA,
    get_clientes_campanha,
    get_clientes_cancelados_LA,
    get_clientes_externos_LA,
    get_clientes_indicacao_LA,
    get_clientes_parceiro_LA,
    get_clientes_redes_sociais_LA,
    get_clientes_retorno_LA,
    get_clientes_todos_LA,
    get_clientes_total_periodo_anterior_LA,
    get_comercial_comissionamento_por_atendente_LA,
    get_comissao_base_LA,
    get_comparativo_acoes_fechadas_LA,
    get_comparativo_clientes_campanha_LA,
    get_comparativo_clientes_cancelados_LA,
    get_comparativo_clientes_externos_LA,
    get_comparativo_clientes_indicacao_LA,
    get_comparativo_clientes_parceiro_LA,
    get_comparativo_clientes_redes_sociais_LA,
    get_comparativo_clientes_retorno_LA,
    get_comparativo_clientes_total_LA,
    get_comparativo_taxa_aproveitamento_LA,
    get_rubricas_reunidas_fechadas_LA,
    get_rubricas_total_tabela_LA,
    get_taxa_aproveitamento_LA,
    get_total_acoes_fechadas_por_atendente_LA,
    get_total_acoes_fechadas_por_rubrica_LA,
    group_acoes_fechadas_diariamente_por_atendente_LA,
    group_acoes_fechadas_por_dia_LA,
    group_contratos_fechados_diariamente_por_atendente_LA,
    group_contratos_fechados_por_dia_LA,
    group_contratos_fechados_por_mes_LA,
    group_processos_fechados_por_mes_LA,
    list_atendentes_comerciais as list_atendentes_comerciais_LA,
    list_segmentos_comercial_la,
    normalizar_segmento_comercial_la,
)
from app.analyses.LA.org_doc_LA import (
    get_cancelados_LA,
    get_comissionamento_por_funcionario_LA,
    get_comparativo_cancelados_LA,
    get_comparativo_organizados_automaticamente_LA,
    get_comparativo_organizados_manualmente_LA,
    get_comparativo_resolvidos_total_LA,
    get_comparativo_retorno_pendencia_LA,
    get_media_resolvidos_por_funcionario_LA,
    get_media_tempo_resolvidos_LA,
    get_mediana_tempo_resolvidos_LA,
    get_nao_organizados_LA,
    get_nao_organizados_por_atendente_LA,
    get_resolvidos_por_dia_por_funcionario_LA,
    get_retorno_pendencia_LA,
    get_total_organizados_LA,
    get_total_organizados_automaticamente_LA,
    get_total_organizados_manualmente_LA,
    get_valor_causa_por_funcionario_LA,
    group_nao_organizados_por_funcionario_LA,
    group_nao_organizados_total_por_materia_LA,
    group_nao_organizados_total_por_mes_LA,
    group_organizados_por_funcionario_LA,
    group_organizados_total_por_materia_LA,
    group_resolvidos_por_dia_LA,
    group_resolvidos_total_por_mes_LA,
)
from app.analyses.LA.pendencia_LA import (
    get_media_pendencias_resolvidas_por_funcionario_LA,
    get_media_tempo_resolvidos_pendencia_LA,
    get_mediana_tempo_resolvidos_pendencia_LA,
    get_pendencias_canceladas_LA,
    get_pendencias_comissionamento_por_funcionario_LA,
    get_pendencias_nao_resolvidas_LA,
    get_pendencias_nao_resolvidas_com_atraso_LA,
    get_pendencias_nao_resolvidas_por_atendente_LA,
    get_pendencias_nao_resolvidas_por_origem_LA,
    get_pendencias_resolvidas_LA,
    get_pendencias_resolvidas_por_dia_por_funcionario_LA,
    get_pendencias_taxa_canceladas_LA,
    get_pendencias_taxa_nao_resolvidos_LA,
    get_pendencias_taxa_resolvidos_LA,
    get_pendencias_total_LA,
    get_pendencias_triagem_LA,
    group_pendencias_resolvidas_por_dia_LA,
    group_pendencias_resolvidas_por_mes_LA,
)
from app.analyses.LA.peticionamento_LA import (
    get_comparativo_confeccionados_LA,
    get_comparativo_confeccionados_automaticamente_LA,
    get_comparativo_confeccionados_manualmente_LA,
    get_comparativo_mediana_tempo_confeccionadoLA,
    get_comparativo_tempo_medio_confeccionado_LA,
    get_comparativo_ticket_medio_confeccionado_LA,
    get_comparativo_valor_causa_confeccionado_LA,
    get_confeccionados_por_dia_por_funcionario_LA,
    get_media_confeccionado_por_funcionario_LA,
    get_media_tempo_confeccionado_LA,
    get_mediana_tempo_confeccionado_LA,
    get_nao_confeccionados_LA,
    get_nao_peticionados_por_atendente_LA,
    get_peticionamento_comissionamento_por_funcionario_LA,
    get_peticionamento_qtd_entrada_protocolo_LA,
    get_peticionamento_qtd_retorno_protocolo_LA,
    get_peticionamento_taxa_nao_resolvidos_LA,
    get_peticionamento_taxa_resolvidos_LA,
    get_peticionamento_taxa_retorno_protocolo_LA,
    get_ticket_medio_confeccionados_LA,
    get_total_confeccionados_LA,
    get_total_confeccionados_automaticamente_LA,
    get_total_confeccionados_manualmente_LA,
    get_valor_causa_confeccionado_LA,
    get_valor_causa_confeccionado_por_funcionario_LA,
    group_confeccionados_por_dia_LA,
    group_confeccionados_por_funcionario_LA,
    group_confeccionados_por_materia_LA,
    group_confeccionados_por_mes_LA,
    group_nao_confeccionados_por_funcionario_LA,
    group_nao_confeccionados_por_materia_LA,
    group_nao_confeccionados_por_mes_LA,
)
from app.analyses.LA.protocolo_LA import (
    META_VALOR_CAUSA_2026_LA,
    get_comissao_com_fm_LA,
    get_comparativo_mediana_tempo_contratacao_protocolado_LA,
    get_comparativo_mediana_tempo_protocolos_resolvidos_LA,
    get_comparativo_protocolos_resolvidos_LA,
    get_comparativo_tempo_medio_contratacao_protocolado_LA,
    get_comparativo_tempo_medio_protocolos_resolvidos_LA,
    get_comparativo_ticket_medio_protocolos_resolvidos_LA,
    get_comparativo_valor_causa_protocolado_LA,
    get_entradas_protocolo_LA,
    get_fator_multiplicador_LA,
    get_media_protocolados_por_funcionario_LA,
    get_media_tempo_contratacao_protocolado_LA,
    get_media_tempo_protocolado_LA,
    get_mediana_tempo_contratacao_protocolado_LA,
    get_mediana_tempo_protocolado_LA,
    get_nao_protocolados_por_atendente_LA,
    get_protocolados_por_dia_por_funcionario_LA,
    get_protocolo_comissionamento_por_funcionario_LA,
    get_protocolos_represados_LA,
    get_protocolos_resolvidos_LA,
    get_protocolos_resolvidos_periodo_anterior_LA,
    get_protocolos_resolvidos_por_atendente_LA,
    get_taxa_protocolados_LA,
    get_ticket_medio_protocolos_resolvidos_LA,
    get_valor_causa_nao_protocolado_por_atendente_LA,
    get_valor_causa_protocolado_LA,
    get_valor_causa_protocolado_LA_2026,
    get_valor_causa_protocolado_periodo_anterior_LA,
    get_valor_causa_protocolado_por_atendente_LA,
    get_valor_causa_protocolado_por_funcionario_LA,
    group_protocolados_por_dia_LA,
    group_protocolados_por_funcionario_LA,
    group_protocolados_por_materia_LA,
    group_protocolados_por_mes_LA,
    group_protocolados_por_sistema_LA,
    group_represados_por_funcionario_LA,
    group_represados_por_materia_LA,
    group_represados_por_mes_LA,
    group_valor_causa_protocolados_por_dia_LA,
    group_valor_causa_protocolados_por_mes_LA,
)
from app.analyses.NG.NPS_NG import (
    get_comentarios,
    get_feedbacks_melhoria,
    get_feedbacks_positivos,
    get_nps_stats,
    get_respostas_tabela,
    group_nps_por_classificacao,
    group_nps_por_mes,
    group_nps_por_nota,
)
from app.analyses.NG.actions import (
    get_comparativo_leads_anuncio_NG,
    get_comparativo_leads_anuncio_RA,
    get_comparativo_leads_geral,
    get_comparativo_taxa_leads_anuncio_NG,
    get_comparativo_taxa_leads_anuncio_RA,
    get_comparativo_taxa_leads_geral,
    get_taxa_fechamento_campanha_por_cliente,
    get_taxa_fechamento_geral_por_atendente,
    get_taxa_fechamento_indicacao_ativa_por_atendente,
    get_taxa_fechamento_indicacao_passiva_por_atendente,
    get_taxa_fechamento_resgate_ativa_por_atendente,
    get_taxa_fechamento_resgate_passiva_por_atendente,
    get_taxa_fechamento_retorno_ativa_por_atendente,
    get_taxa_fechamento_retorno_passiva_por_atendente,
    get_taxa_leads_anuncio_NG,
    get_taxa_leads_anuncio_RA,
    get_taxa_leads_geral,
    get_total_clientes_fechados_campanha,
    get_total_clientes_fechados_campanha_por_atendente,
    get_total_clientes_fechados_indicacao_ativa_por_atendente,
    get_total_clientes_fechados_indicacao_passiva_por_atendente,
    get_total_clientes_fechados_por_atendente,
    get_total_clientes_fechados_resgate_ativa_por_atendente,
    get_total_clientes_fechados_resgate_passiva_por_atendente,
    get_total_clientes_fechados_retorno_ativa_por_atendente,
    get_total_clientes_fechados_retorno_passiva_por_atendente,
    get_total_leads,
    get_total_leads_anuncio_NG,
    get_total_leads_anuncio_RA,
    get_total_leads_campanha_por_atendente,
    get_total_leads_indicacao_ativa_por_atendente,
    get_total_leads_indicacao_passiva_por_atendente,
    get_total_leads_por_atendente,
    get_total_leads_resgate_ativa_por_atendente,
    get_total_leads_resgate_passiva_por_atendente,
    get_total_leads_retorno_ativa_por_atendente,
    get_total_leads_retorno_passiva_por_atendente,
)
from app.analyses.NG.comercial_geral import (
    _formatar_nome_atendente as _formatar_nome_atendente_NG,
    filter_comercial_geral_por_area_atuacao,
    filter_comercial_geral_por_segmento,
    filter_comercial_geral_por_uf,
    get_acoes_fechadas,
    get_acoes_fechadas_campanha_NG,
    get_acoes_fechadas_campanha_RA,
    get_acoes_fechadas_indicacao,
    get_acoes_fechadas_periodo_anterior,
    get_acoes_fechadas_redes_sociais,
    get_acoes_fechadas_resgate,
    get_acoes_fechadas_retorno,
    get_acoes_fechadas_site,
    get_clientes_campanha_NG,
    get_clientes_campanha_RA,
    get_clientes_cancelados,
    get_clientes_indicacao,
    get_clientes_parceiros_externos,
    get_clientes_redes_sociais,
    get_clientes_resgate,
    get_clientes_retorno,
    get_clientes_site,
    get_clientes_todos,
    get_clientes_todos_periodo_anterior,
    get_comercial_comissionamento_por_atendente,
    get_comissao_base,
    get_comparativo_acoes_fechadas,
    get_comparativo_clientes_campanha_NG,
    get_comparativo_clientes_campanha_RA,
    get_comparativo_clientes_cancelados,
    get_comparativo_clientes_indicacao,
    get_comparativo_clientes_parceiros_externos,
    get_comparativo_clientes_redes_sociais,
    get_comparativo_clientes_resgate,
    get_comparativo_clientes_retorno,
    get_comparativo_clientes_site,
    get_comparativo_clientes_todos,
    get_comparativo_taxa_aproveitamento,
    get_rubricas_reunidas_fechadas,
    get_rubricas_total_tabela,
    get_taxa_aproveitamento,
    get_total_acoes_fechadas_por_rubrica,
    group_acoes_fechadas_diariamente,
    group_acoes_fechadas_por_atendente,
    group_acoes_fechadas_por_dia,
    group_contratos_fechados_diariamente_por_atendente,
    group_contratos_fechados_por_dia,
    group_contratos_fechados_por_mes,
    group_processos_fechados_por_mes,
    list_atendentes_comerciais,
    list_segmentos_comercial_ng,
    list_ufs_comercial_ng,
    normalizar_segmento_comercial_ng,
)
from app.analyses.NG.marketing_ng import (
    _FIELD_MAP_ANALISE_THIAGO,
    _FIELD_MAP_CLIENTES,
    _FIELD_MAP_TRACKEAMENTO,
    apply_selection_filters,
    filtrar_canais_organico,
    filtrar_canal_aquisicao,
    filtrar_fechados_trackeamento,
    filtrar_triados,
    get_acoes_ng,
    get_acoes_organico,
    get_acoes_ra,
    get_facebook_ads_stats,
    get_leads_por_canal,
    get_marketing_ng_cac_roas_stats,
    get_marketing_ng_stats,
    get_media_idade,
    get_protocolo_resolvido_saida_ng,
    get_protocolo_resolvido_saida_ra,
    get_qtd_clientes_campanha_ng,
    get_qtd_clientes_campanha_ra,
    get_qtd_clientes_organico,
    get_ticket_medio_ng,
    get_ticket_medio_ra,
    get_total_clientes,
    get_total_leads_campanha_ng,
    get_total_leads_campanha_ra,
    get_total_leads_organico,
    get_total_trackeamento,
    get_valor_causa_protocolo_ng,
    get_valor_causa_protocolo_organico,
    get_valor_causa_protocolo_ra,
    group_campanha_organico,
    group_campanha_trackeamento,
    group_canal_aquisicao_trackeamento,
    group_categoria_criativo,
    group_conjunto_trackeamento,
    group_criativo_trackeamento,
    group_dispositivo,
    group_faixa_etaria,
    group_faixa_salarial,
    group_funil_pipeline,
    group_genero,
    group_investimento_cliques_leads,
    group_ocupacao,
    group_origem,
    group_pessoas_dependentes,
    group_posicionamento_padronizado,
    group_prospeccao,
    group_protocolo_resolvido_total,
    group_rubrica_campanha,
    group_rubrica_organico,
    group_rubrica_protocolado,
    group_tipo_residencia,
    group_tipo_trafego,
    group_total_clientes_campanha,
    group_valor_causa_total,
)
from app.analyses.NG.org_doc import (
    _filtrar_nao_organizados,
    filter_org_doc_por_funcionarios,
    filter_org_doc_por_materia,
    filter_org_doc_por_uf,
    get_cancelados,
    get_comissionamento_por_funcionario,
    get_comparativo_cancelados,
    get_comparativo_organizados_e_peticionados_automaticamente,
    get_comparativo_organizados_manualmente,
    get_comparativo_resolvidos_reajuizamento,
    get_comparativo_resolvidos_total,
    get_comparativo_tempo_medio_resolvidos_org_doc,
    get_media_resolvidos_por_funcionario,
    get_media_tempo_resolvidos,
    get_mediana_tempo_resolvidos,
    get_nao_organizados,
    get_nao_organizados_por_atendente,
    get_organizados_e_peticionados_automaticamente,
    get_organizados_manualmente,
    get_resolvidos_por_dia_por_funcionario,
    get_resolvidos_reajuizamento,
    get_resolvidos_total,
    get_retorno_pendencia,
    get_retorno_pet,
    get_valor_causa_por_funcionario,
    group_nao_organizados_por_funcionario,
    group_nao_organizados_total_por_materia,
    group_nao_resolvidos_total_por_mes,
    group_resolvidos_por_dia,
    group_resolvidos_por_funcionario,
    group_resolvidos_total_por_materia,
    group_resolvidos_total_por_mes,
    list_ufs_org_doc,
)
from app.analyses.NG.pendencia import (
    _filtrar_pendencias_nao_resolvidas,
    filter_pendencia_por_funcionarios,
    filter_pendencia_por_uf,
    get_comparativo_pendencias_resolvidas,
    get_comparativo_tempo_medio_pendencias_resolvidas,
    get_media_pendencias_resolvidas_por_funcionario,
    get_media_tempo_resolvidos_pendencia,
    get_mediana_tempo_resolvidos_pendencia,
    get_pendencias_canceladas,
    get_pendencias_comissionamento_por_funcionario,
    get_pendencias_nao_resolvidas,
    get_pendencias_nao_resolvidas_com_atraso,
    get_pendencias_nao_resolvidas_por_atendente,
    get_pendencias_nao_resolvidas_por_origem,
    get_pendencias_nao_resolvidas_reajuizamento,
    get_pendencias_resolvidas,
    get_pendencias_resolvidas_por_dia_por_funcionario,
    get_pendencias_resolvidas_reajuizamento,
    get_pendencias_taxa_canceladas,
    get_pendencias_taxa_nao_resolvidos,
    get_pendencias_taxa_resolvidos,
    get_pendencias_total,
    get_pendencias_triagem,
    group_pendencias_resolvidas_por_dia,
    group_pendencias_resolvidas_por_mes,
    list_ufs_pendencia,
)
from app.analyses.NG.peticionamento import (
    _filtrar_nao_peticionados,
    filter_peticionamento_por_funcionarios,
    filter_peticionamento_por_materia,
    filter_peticionamento_por_uf,
    get_comparativo_nao_peticionados_reajuizamento,
    get_comparativo_peticionados,
    get_comparativo_peticionados_automaticamente,
    get_comparativo_peticionados_manualmente,
    get_comparativo_peticionados_reajuizamento,
    get_comparativo_tempo_mediana_peticionado,
    get_comparativo_tempo_medio_peticionado,
    get_comparativo_ticket_medio_confeccionado,
    get_comparativo_valor_causa_confeccionado,
    get_media_peticionado_por_funcionario,
    get_media_tempo_peticionado,
    get_mediana_tempo_peticionado,
    get_nao_peticionados,
    get_nao_peticionados_por_atendente,
    get_nao_resolvidos_reajuizamento,
    get_peticionados_automaticamente,
    get_peticionados_manualmente,
    get_peticionados_por_dia_por_funcionario,
    get_peticionamento_comissionamento_por_funcionario,
    get_peticionamento_taxa_nao_resolvidos,
    get_peticionamento_taxa_resolvidos,
    get_processos_em_revisao,
    get_resolvidos_reajuizamento_pet,
    get_ticket_medio_confeccionado,
    get_total_peticionados,
    get_valor_causa_confeccionado,
    get_valor_causa_peticionado_por_funcionario,
    group_nao_peticionados_por_funcionario,
    group_nao_peticionados_por_materia,
    group_nao_peticionados_por_mes,
    group_peticionados_por_dia,
    group_peticionados_por_funcionario,
    group_peticionados_por_materia,
    group_peticionados_por_mes,
    list_ufs_peticionamento,
)
from app.analyses.NG.protocolo import (
    META_VALOR_CAUSA_2026,
    _filtrar_protocolos_nao_protocolados,
    _filtrar_protocolos_resolvidos,
    filter_protocolo_por_funcionarios,
    filter_protocolo_por_materia,
    filter_protocolo_por_sistema,
    filter_protocolo_por_uf,
    get_comissao_com_fm,
    get_comparativo_mediana_tempo_contratacao_protocolado,
    get_comparativo_nao_protocolados,
    get_comparativo_protocolos_resolvidos,
    get_comparativo_tempo_medio_contratacao_protocolado,
    get_comparativo_tempo_medio_protocolos_resolvidos,
    get_comparativo_ticket_medio_protocolos_resolvidos,
    get_comparativo_valor_causa_protocolo,
    get_fator_multiplicador,
    get_media_protocolados_por_funcionario,
    get_media_tempo_contratacao_protocolado,
    get_media_tempo_protocolado,
    get_mediana_tempo_contratacao_protocolado,
    get_mediana_tempo_protocolado,
    get_nao_protocolados,
    get_nao_protocolados_de_reajuizamento,
    get_nao_protocolados_por_atendente,
    get_proporcionais_am_pa_pb_sobre_comissao_com_fm,
    get_protocolados_de_reajuizamento,
    get_protocolados_por_dia_por_funcionario,
    get_protocolo_comissionamento_por_funcionario,
    get_protocolos_por_atendente,
    get_protocolos_resolvidos,
    get_protocolos_resolvidos_periodo_anterior,
    get_ticket_medio_protocolos_resolvidos,
    get_valor_causa_protocolo_2026,
    get_valor_causa_protocolo_nao_protocolado_por_atendente,
    get_valor_causa_protocolo_novo,
    get_valor_causa_protocolo_novo_por_atendente,
    get_valor_causa_protocolo_novo_por_funcionario,
    get_valor_causa_protocolo_periodo_anterior,
    get_valor_por_estado_am_pa,
    get_valor_por_estado_pb,
    group_nao_protocolados_por_funcionario,
    group_nao_protocolados_por_materia,
    group_nao_protocolados_por_mes,
    group_protocolados_por_dia,
    group_protocolados_por_funcionario,
    group_protocolados_por_materia,
    group_protocolados_por_mes,
    group_protocolados_por_sistema,
    group_valor_causa_protocolados_por_dia,
    group_valor_causa_protocolados_por_mes,
    list_ufs_protocolo,
)
from app.analyses.NG.tickets import (
    apply_ticket_selection_filter,
    contar_tickets_validos_no_periodo,
    get_tickets_stats,
    group_tickets_abertos_por_servidor,
    group_tickets_by_category,
    group_tickets_by_month,
    group_tickets_by_status,
    group_tickets_by_subcategory,
    group_tickets_encerrados_por_servidor,
    group_tickets_media_encerrados_por_colaborador,
    group_tickets_ranking_abertura,
    group_tickets_ranking_fechados,
    tickets_to_activities,
)
from app.utils import (
    parse_date_from_db,
    resolver_periodo_comparativo,
)
from collections import (
    defaultdict,
)
from dataclasses import (
    dataclass,
)
from datetime import (
    date,
    datetime,
)
from fastapi import (
    HTTPException,
    Query,
)
from pydantic import (
    BaseModel,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
from app.analyses.situacao_processo import _situacoes_processo_ctx, aplicar_filtro_situacao_processo
from app.sources import SourceUnavailable  # V2: fonte fora do ar vira 503 na casca

# V2: fonte do banco de origem (no lugar de fetch_data_with_cache da v1). A casca passa a fonte do
# dashboard (SourceFetcher, já com o cache de 5 min) por `usar_fonte`; o recorte de situação do processo
# é o mesmo que a v1 aplica em fetch_data_with_cache.
_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico_ng")

def usar_fonte(fonte):
    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""
    return _fonte_ctx.set(fonte)


@memo.por_pedido(contexto=(_fonte_ctx, _situacoes_processo_ctx), copiar=False)
async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:
    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))


# V2: v1 dashboard_routes.py:2821 -> fetch_data_with_cache('setor_protocolo', ...)
async def fetch_protocolos() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_protocolo')


# V2: v1 dashboard_routes.py:2798 -> fetch_data_with_cache('comercial_geral_NG', ...)
async def fetch_comercial_geral() -> List[Dict[str, Any]]:
    return await _fetch_v2('comercial_geral_NG')


# V2: v1 dashboard_routes.py:2824 -> fetch_data_with_cache('setor_confeccao', ...)
async def fetch_peticionamento() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_confeccao')


# V2: v1 dashboard_routes.py:2827 -> fetch_data_with_cache('setor_org_doc', ...)
async def fetch_org_doc() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_org_doc')


# V2: v1 dashboard_routes.py:2830 -> fetch_data_with_cache('setor_pendencias', ...)
async def fetch_pendencias() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_pendencias')


# V2: v1 dashboard_routes.py:2818 -> fetch_data_with_cache('actions_NG_2', ...)
async def fetch_actions() -> List[Dict[str, Any]]:
    return await _fetch_v2('actions_NG_2')


# V2: v1 dashboard_routes.py:2833 -> fetch_data_with_cache('rubrica_count_por_processo', ...)
async def fetch_rubrica_count_por_processo() -> List[Dict[str, Any]]:
    return await _fetch_v2('rubrica_count_por_processo')


# V2: v1 dashboard_routes.py:3134 -> fetch_data_with_cache('perfil_clientes_NG', ...)
async def fetch_marketing_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('perfil_clientes_NG')


# V2: v1 dashboard_routes.py:3140 -> fetch_data_with_cache('facebook_ads', ...)
async def fetch_facebook_ads() -> List[Dict[str, Any]]:
    return await _fetch_v2('facebook_ads')


# V2: v1 dashboard_routes.py:3143 -> fetch_data_with_cache('Analise_thiago', ...)
async def fetch_analise_thiago() -> List[Dict[str, Any]]:
    return await _fetch_v2('Analise_thiago')


# V2: v1 dashboard_routes.py:3146 -> fetch_data_with_cache('trackeamento_NG_2', ...)
async def fetch_trackeamento_ng_2() -> List[Dict[str, Any]]:
    return await _fetch_v2('trackeamento_NG_2')


# V2: v1 dashboard_routes.py:3128 -> fetch_data_with_cache('nps_NG', ...)
async def fetch_nps_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('nps_NG')


# V2: v1 dashboard_routes.py:2792 -> fetch_data_with_cache('tickets', ...)
async def fetch_tickets() -> List[Dict[str, Any]]:
    return await _fetch_v2('tickets')


# v1: dashboard_routes.py:2280
logger = logging.getLogger(__name__)


# v1: dashboard_routes.py:3151
def _resolve_date_range(
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Optional[date], Optional[date]]:
    """Normaliza o intervalo: se from_date sem to_date, usa hoje como fim."""
    return periodo.resolver_intervalo(from_date, to_date)


# v1: dashboard_routes.py:3161
_to_date = conversao.para_data  # V2: era uma cópia local (app/analyses/common/conversao.py)


# v1: dashboard_routes.py:3173
# V2: _in_range virou parte de periodo.filtrar_por_colunas (era usado só lá).


# v1: dashboard_routes.py:3183
def _filter_by_columns(
    data: List[Dict[str, Any]],
    columns: List[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Filtra registros verificando as colunas na ordem fornecida.
    Inclui o registro se QUALQUER coluna tiver data dentro do intervalo (OR lógico).
    Colunas são verificadas em caixa-alta e caixa-baixa automaticamente.
    """
    return periodo.filtrar_por_colunas(data, columns, from_date, to_date, para_data=_to_date)


# v1: dashboard_routes.py:3213
_FILTER_COLUMNS: Dict[str, List[str]] = {
    "tickets":              ["data_criacao"],
    "andamento_processual": ["ENTRADA"],
    "comercial_geral":      ["ASSINATURA"],
    "actions":              ["ENTRADA", "ASSINADO_EM"],
    "protocolos":           ["SAIDA"],
    "peticionamento":       ["DATA_CONFECCAO"],
    "org_doc":              ["SAIDA", "ENTRADA"],
    "pendencias":           ["ENTRADA"],
    "execucao":             ["DATA_EXECUCAO"],
    "execucao_RJ":          ["DATA_EXECUCAO"],
    "execucao_acordos_NG":  ["DATA_EXECUCAO"],
    "execucao_acordos_LA":  ["DATA_EXECUCAO"],
    "execucao_acordos_RJ":  ["DATA_EXECUCAO"],
    "publicacoes_NG":       ["DATA_DISPONIBILIZACAO", "DATA_CONCLUSAO"],
    "publicacoes_RJ":       ["DATA_DISPONIBILIZACAO", "DATA_CONCLUSAO"],
    # LA
    "comercial_LA":            ["ASSINADO_EM"],
    "actions_LA":              ["ENTRADA", "ASSINADO_EM"],
    "protocolo_LA":            ["SAIDA"],
    "peticionamento_LA":       ["SAIDA"],
    "org_doc_LA":              ["SAIDA"],
    "pendencias_LA":           ["ENTRADA"],
    "execucao_LA":             ["DATA_EXECUCAO"],
    "controle_processo_LA":    ["DATA_AJUIZAMENTO", "DATA_LOG_ULTIMA_ENTRADA"],
    "controle_processo_NG":    ["DATA_AJUIZAMENTO", "DATA_LOG_ULTIMA_ENTRADA"],
    "andamento_processual_LA": ["ENTRADA"],
    "pendencia_LA":            ["ENTRADA"],
    "publicacoes_LA":          ["DATA_DISPONIBILIZACAO", "DATA_CONCLUSAO"],
    "estrategico_geral":       ["SAIDA"],
    # Julgados: sem entrada aqui — o filtro de data (e o comparativo com o
    # período anterior) é feito dentro de `analyses/NG/julgados.py`, que
    # precisa do dado bruto (sem pré-filtro) para calcular o período anterior.
    # NPS
    "nps_NG":                  ["DATA"],
    "nps_LA":                  ["DATA"],
    # Marketing
    "marketing_NG":            ["ASSINATURA"],
    "marketing_lexpre_NG":     ["ENTRADA"],
    "facebook_ads":            ["date"],
    "trackeamento_ng_2":       ["DATA_TRACKEAMENTO"],
}


# v1: dashboard_routes.py:3257
def filter_data(
    key: str,
    data: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """Aplica o filtro de data à fonte identificada por `key`."""
    columns = _FILTER_COLUMNS.get(key)
    if not columns:
        return data
    return _filter_by_columns(data, columns, from_date, to_date)


# v1: dashboard_routes.py:3270
def dict_to_chart_data(
    d: Dict[str, Any],
    *,
    sort: bool = True,
    cast_int: bool = False,
) -> List[Dict[str, Any]]:
    """Converte dict {nome: valor} para lista [{name, value}], ordenada decrescente."""
    items = list(d.items())
    if sort:
        items = sorted(items, key=lambda x: x[1], reverse=True)
    return [{"name": k, "value": int(v) if cast_int else v} for k, v in items]


# v1: dashboard_routes.py:3283
def _per_func_to_chart(
    raw: Dict[str, Any],
) -> Tuple[List[str], Dict[str, List[Dict[str, Any]]]]:
    """
    Extrai a estrutura retornada por get_*_por_dia_por_funcionario().
    Retorna (lista_funcionarios, {func: [{name, value}]}).
    """
    funcionarios: List[str] = raw.get("funcionarios", [])
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {
        k: [{"name": x["name"], "value": x["value"]} for x in v]
        for k, v in raw.get("por_funcionario", {}).items()
    }
    return funcionarios, por_funcionario


# v1: dashboard_routes.py:3357
_ATENDENTE_COMERCIAL_KEYS_NG = frozenset({
    "comercial_geral", "actions", "protocolos", "peticionamento", "org_doc", "pendencias",
})


# v1: dashboard_routes.py:3360
_ATENDENTE_COMERCIAL_KEYS_LA = frozenset({
    "comercial_LA", "actions_LA", "protocolo_LA", "peticionamento_LA", "org_doc_LA", "pendencias_LA",
})


# v1: dashboard_routes.py:3363
_ATENDENTE_COMERCIAL_KEYS = _ATENDENTE_COMERCIAL_KEYS_NG | _ATENDENTE_COMERCIAL_KEYS_LA


# v1: dashboard_routes.py:3412
def _expandir_valores_query_lista(valores: Optional[List[str]]) -> List[str]:
    """Expande parâmetros repetidos e valores separados por vírgula."""
    if not valores:
        return []
    saida: List[str] = []
    for raw in valores:
        if raw is None:
            continue
        for parte in str(raw).split(","):
            t = parte.strip()
            if t:
                saida.append(t)
    return saida


# v1: dashboard_routes.py:3427
def _brutos_atendentes_comercial_query(
    atendente_comercial: Optional[List[str]] = None,
    funcionario: Optional[List[str]] = None,
) -> List[str]:
    """Valores brutos únicos de ``atendente_comercial`` e ``funcionario``."""
    vistos: set[str] = set()
    saida: List[str] = []
    for origem in (atendente_comercial, funcionario):
        for item in _expandir_valores_query_lista(origem):
            if item not in vistos:
                vistos.add(item)
                saida.append(item)
    return saida


# v1: dashboard_routes.py:3442
def _normalizar_atendentes_comercial_query(
    atendentes: Optional[List[str]],
    *,
    usar_formato_la: bool = False,
) -> List[str]:
    """Normaliza nomes vindos de um ou vários ``atendente_comercial`` na query."""
    expandidos = _expandir_valores_query_lista(atendentes)
    if not expandidos:
        return []
    fmt = _formatar_nome_atendente_LA if usar_formato_la else _formatar_nome_atendente_NG
    vistos: set[str] = set()
    saida: List[str] = []
    for raw in expandidos:
        t = fmt(str(raw or "").strip())
        if t and t not in vistos:
            vistos.add(t)
            saida.append(t)
    return saida


# v1: dashboard_routes.py:3475
_NG_UF_FILTER_KEYS = frozenset({"comercial_geral", "protocolos", "pendencias", "peticionamento", "org_doc", "actions", "andamento_processual"})


# v1: dashboard_routes.py:3477
def _filtrar_dados_ng_por_uf(data: Dict[str, List], uf: str, *, excluir: bool = False) -> Dict[str, List]:
    """Filtra (ou exclui) uma UF nos datasets NG que têm coluna UF."""
    uf_norm = str(uf).strip().upper()
    result = {}
    for key, rows in data.items():
        if key in _NG_UF_FILTER_KEYS:
            if excluir:
                result[key] = [r for r in rows if str(r.get("UF") or "").strip().upper() != uf_norm]
            else:
                result[key] = [r for r in rows if str(r.get("UF") or "").strip().upper() == uf_norm]
        else:
            result[key] = rows
    return result


# v1: dashboard_routes.py:3492
def _aplicar_filtros_comercial_dashboard(
    filtered_data: Dict[str, List],
    all_data: Dict[str, List],
    *,
    dashboard_name: str,
    atendente_comercial: Optional[List[str]],
    funcionario: Optional[List[str]],
) -> tuple[Dict[str, List], Dict[str, List], List[str]]:
    """Restringe todos os datasets exibidos na página comercial aos atendentes selecionados."""
    ac_brutos = _brutos_atendentes_comercial_query(atendente_comercial, funcionario)
    if not ac_brutos:
        return filtered_data, all_data, []

    if dashboard_name in ("comercial", "comercial_RJ"):
        ac_ng = _normalizar_atendentes_comercial_query(ac_brutos, usar_formato_la=False)
        ac_la = _normalizar_atendentes_comercial_query(ac_brutos, usar_formato_la=True)
        if ac_ng:
            filtered_data = _aplicar_filtro_atendentes_comercial(
                filtered_data, ac_ng, keys=_ATENDENTE_COMERCIAL_KEYS_NG, usar_formato_la=False,
            )
            all_data = _aplicar_filtro_atendentes_comercial(
                all_data, ac_ng, keys=_ATENDENTE_COMERCIAL_KEYS_NG, usar_formato_la=False,
            )
        if ac_la and dashboard_name == "comercial":
            filtered_data = _aplicar_filtro_atendentes_comercial(
                filtered_data, ac_la, keys=_ATENDENTE_COMERCIAL_KEYS_LA, usar_formato_la=True,
            )
            all_data = _aplicar_filtro_atendentes_comercial(
                all_data, ac_la, keys=_ATENDENTE_COMERCIAL_KEYS_LA, usar_formato_la=True,
            )
    else:
        ac_la = _normalizar_atendentes_comercial_query(ac_brutos, usar_formato_la=True)
        if ac_la:
            filtered_data = _aplicar_filtro_atendentes_comercial(
                filtered_data, ac_la, keys=_ATENDENTE_COMERCIAL_KEYS_LA, usar_formato_la=True,
            )
            all_data = _aplicar_filtro_atendentes_comercial(
                all_data, ac_la, keys=_ATENDENTE_COMERCIAL_KEYS_LA, usar_formato_la=True,
            )

    return filtered_data, all_data, ac_brutos


# v1: dashboard_routes.py:3535
def _linha_bate_atendentes_comercial(
    row: Dict[str, Any],
    atendentes_fmt: frozenset[str],
    *,
    usar_formato_la: bool = False,
) -> bool:
    fmt = _formatar_nome_atendente_LA if usar_formato_la else _formatar_nome_atendente_NG
    for key in ("ATENDENTE", "ATENDENTE_COMERCIAL", "ATENDENTE_COMERCIAL_NOME"):
        v = row.get(key)
        if v is None or v == "":
            continue
        if fmt(str(v).strip()) in atendentes_fmt:
            return True
    return False


# v1: dashboard_routes.py:3551
def _filtrar_lista_por_atendentes_comercial(
    rows: List[Dict[str, Any]],
    atendentes_fmt: frozenset[str],
    *,
    usar_formato_la: bool = False,
) -> List[Dict[str, Any]]:
    if not atendentes_fmt:
        return list(rows)
    return [
        r for r in rows
        if _linha_bate_atendentes_comercial(r, atendentes_fmt, usar_formato_la=usar_formato_la)
    ]


# v1: dashboard_routes.py:3565
def _aplicar_filtro_atendentes_comercial(
    datasets: Dict[str, List],
    atendentes: List[str],
    *,
    keys: frozenset | None = None,
    usar_formato_la: bool = False,
) -> Dict[str, List]:
    if not atendentes:
        return datasets
    atendentes_fmt = frozenset(atendentes)
    active_keys = keys if keys is not None else _ATENDENTE_COMERCIAL_KEYS
    return {
        k: (
            _filtrar_lista_por_atendentes_comercial(
                v, atendentes_fmt, usar_formato_la=usar_formato_la
            )
            if k in active_keys
            else v
        )
        for k, v in datasets.items()
    }


# v1: dashboard_routes.py:3588
def _normalizar_funcionarios_query(funcionarios: Optional[List[str]]) -> List[str]:
    """Lista única de nomes de funcionário vindos da query (trim, sem vazios)."""
    vistos: set[str] = set()
    saida: List[str] = []
    for raw in _expandir_valores_query_lista(funcionarios):
        if raw not in vistos:
            vistos.add(raw)
            saida.append(raw)
    return saida


# v1: dashboard_routes.py:3912
@dataclass
class ComercialLAContext:
    """Agrupa as fontes de dados necessárias para o builder comercial LA."""
    comercial: List[Dict]
    all_comercial: List[Dict]
    actions: List[Dict]
    protocolo: List[Dict]
    all_protocolo: List[Dict]
    peticionamento: List[Dict]
    all_peticionamento: List[Dict]
    org_doc: List[Dict]
    all_org_doc: List[Dict]
    pendencias: List[Dict]
    all_pendencias: List[Dict]
    from_date: Optional[date]
    to_date: Optional[date]


# V2: os modelos de resposta da v1 ficam num módulo só (app/analyses/v1_modelos.py).
from app.analyses.v1_modelos import (  # noqa: F401  (usados aqui e por quem importa deste módulo)
    ChartDataPoint,
    ProcessoDadoFaltando,
    InvestimentoCliquesLeadsPoint,
    RubricaCampanhaPoint,
    NpsRespostaRow,
    NpsFeedbackMelhoriaRow,
    NpsFeedbackPositivoRow,
    NpsComentarioRow,
    RecursalRankingMagistradoRow,
    JulgadosSentencaListaRow,
    JulgadosAcordaoListaRow,
    ExecucaoAcordosListaRow,
    RecursalAtividadeTarefaRow,
    DilacaoPorFuncionarioRow,
    EmendasManifestacoesResolvidosPorUfRow,
    EmendasManifestacoesComissaoRow,
    RecursalAtividadesListaFiltrosOpcoes,
    ExecucaoAtrasoBucket,
    ExecucaoAtrasosDetalhamento,
    RubricaTotalRow,
    ComissionamentoOrgDocRow,
    ComissionamentoProtocoloRow,
    ComissionamentoPeticionamentoRow,
    ComissionamentoPendenciaRow,
    ComissionamentoPublicacaoRow,
    ComissionamentoAndamentoRow,
    ComissionamentoComercialRow,
    ComissionamentoComercialLARow,
    TotalLeadsPorAtendente,
    TotalClientesFechadosPorAtendente,
    TaxaFechamentoGeralPorAtendente,
    TotalLeadsCampanhaPorAtendente,
    TotalClientesFechadosCampanhaPorAtendente,
    TaxaFechamentoCampanhaPorCliente,
    TotalLeadsIndicacaoAtivaPorAtendente,
    TaxaFechamentoIndicacaoAtivaPorAtendente,
    TotalClientesFechadosIndicacaoAtivaPorAtendente,
    TotalLeadsIndicacaoPassivaPorAtendente,
    TotalClientesFechadosIndicacaoPassivaPorAtendente,
    TaxaFechamentoIndicacaoPassivaPorAtendente,
    TotalLeadsRetornoAtivaPorAtendente,
    TotalClientesFechadosRetornoAtivaPorAtendente,
    TaxaFechamentoRetornoAtivaPorAtendente,
    TotalLeadsRetornoPassivaPorAtendente,
    TotalClientesFechadosRetornoPassivaPorAtendente,
    TaxaFechamentoRetornoPassivaPorAtendente,
    TotalLeadsResgateAtivaPorAtendente,
    TotalClientesFechadosResgateAtivaPorAtendente,
    TaxaFechamentoResgateAtivaPorAtendente,
    TotalLeadsResgatePassivaPorAtendente,
    TotalClientesFechadosResgatePassivaPorAtendente,
    TaxaFechamentoResgatePassivaPorAtendente,
    DashboardStats,
    Activity,
    DashboardResponse,
)


# v1: dashboard_routes.py:6830
def _build_tickets_stats(
    tickets: List[Dict],
    all_tickets: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    stats = get_tickets_stats(tickets)
    # Comparativo do card "Total de Tickets": mesmo recorte de dias um mês antes.
    _, _, inicio_anterior, fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    stats["total_tickets_periodo_anterior"] = contar_tickets_validos_no_periodo(
        all_tickets, inicio_anterior, fim_anterior
    )
    charts = {
        "tickets_por_categoria": [ChartDataPoint(**x) for x in group_tickets_by_category(tickets)],
        "tickets_por_subcategoria": [ChartDataPoint(**x) for x in group_tickets_by_subcategory(tickets)],
        "tickets_por_abertura": [ChartDataPoint(**x) for x in group_tickets_ranking_abertura(tickets)],
        "tickets_por_fechamento": [ChartDataPoint(**x) for x in group_tickets_ranking_fechados(tickets)],
        "tickets_por_mes": [ChartDataPoint(**x) for x in group_tickets_by_month(all_tickets)],
        "tickets_por_status": [ChartDataPoint(**x) for x in group_tickets_by_status(tickets)],
        "tickets_abertos_por_servidor": [ChartDataPoint(**x) for x in group_tickets_abertos_por_servidor(tickets)],
        "tickets_encerrados_por_servidor": [ChartDataPoint(**x) for x in group_tickets_encerrados_por_servidor(tickets)],
        "recent_activities": [Activity(**x) for x in tickets_to_activities(tickets)],
        "tickets_media_encerrados_por_colaborador": [
            ChartDataPoint(**x)
            for x in group_tickets_media_encerrados_por_colaborador(tickets, from_date, to_date)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:6894
def _build_comercial_stats(
    comercial: List[Dict],
    all_comercial: List[Dict],
    actions: List[Dict],
    all_actions: List[Dict],
    protocolos: List[Dict],
    all_protocolos: List[Dict],
    peticionamento: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    stats = {
        "clientes_campanha_RA": get_clientes_campanha_RA(comercial),
        "clientes_campanha_NG": get_clientes_campanha_NG(comercial),
        "clientes_indicacao": get_clientes_indicacao(comercial),
        "clientes_redes_sociais": get_clientes_redes_sociais(comercial),
        "clientes_retorno": get_clientes_retorno(comercial),
        "clientes_site": get_clientes_site(comercial),
        "clientes_resgate": get_clientes_resgate(comercial),
        "clientes_parceiros_externos": get_clientes_parceiros_externos(comercial),
        "clientes_todos": get_clientes_todos(comercial),
        "clientes_cancelados": get_clientes_cancelados(comercial),
        "acoes_fechadas": get_acoes_fechadas(comercial),
        "total_rubricas_reunidas_fechadas": get_rubricas_reunidas_fechadas(comercial),
        "taxa_aproveitamento": get_taxa_aproveitamento(comercial),
        "comparativo_clientes_campanha_NG": get_comparativo_clientes_campanha_NG(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_campanha_RA": get_comparativo_clientes_campanha_RA(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_redes_sociais": get_comparativo_clientes_redes_sociais(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_indicacao": get_comparativo_clientes_indicacao(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_retorno": get_comparativo_clientes_retorno(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_resgate": get_comparativo_clientes_resgate(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_site": get_comparativo_clientes_site(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_parceiros_externos": get_comparativo_clientes_parceiros_externos(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_acoes_fechadas": get_comparativo_acoes_fechadas(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "acoes_fechadas_periodo_anterior": get_acoes_fechadas_periodo_anterior(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_todos": get_comparativo_clientes_todos(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "clientes_todos_periodo_anterior": get_clientes_todos_periodo_anterior(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_clientes_cancelados": get_comparativo_clientes_cancelados(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_taxa_aproveitamento": get_comparativo_taxa_aproveitamento(comercial, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "valor_causa_confeccionado": get_valor_causa_confeccionado(peticionamento),
        "ticket_medio_confeccionado": get_ticket_medio_confeccionado(peticionamento),
        "ticket_medio_protocolado": get_ticket_medio_protocolos_resolvidos(protocolos),
        "comparativo_ticket_medio_protocolado": get_comparativo_ticket_medio_protocolos_resolvidos(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "total_leads": get_total_leads(actions),
        "qtde_total_leads_anuncio_RA": get_total_leads_anuncio_RA(actions),
        "qtde_total_leads_anuncio_NG": get_total_leads_anuncio_NG(actions),
        "taxa_leads_geral": get_taxa_leads_geral(actions, comercial),
        "taxa_leads_anuncio_RA": get_taxa_leads_anuncio_RA(actions, comercial),
        "taxa_leads_anuncio_NG": get_taxa_leads_anuncio_NG(actions, comercial),
        "comparativo_leads_geral": get_comparativo_leads_geral(actions, all_actions=all_actions, from_date=from_date, to_date=to_date),
        "comparativo_leads_anuncio_RA": get_comparativo_leads_anuncio_RA(actions, all_actions=all_actions, from_date=from_date, to_date=to_date),
        "comparativo_leads_anuncio_NG": get_comparativo_leads_anuncio_NG(actions, all_actions=all_actions, from_date=from_date, to_date=to_date),
        "comparativo_taxa_leads_geral": get_comparativo_taxa_leads_geral(actions, comercial, all_actions=all_actions, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_taxa_leads_anuncio_RA": get_comparativo_taxa_leads_anuncio_RA(actions, comercial, all_actions=all_actions, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comparativo_taxa_leads_anuncio_NG": get_comparativo_taxa_leads_anuncio_NG(actions, comercial, all_actions=all_actions, all_comercial_geral=all_comercial, from_date=from_date, to_date=to_date),
        "comissao_base": get_comissao_base(comercial),
    }
    charts = {
        "acoes_fechadas_por_atendente": [ChartDataPoint(**x) for x in group_acoes_fechadas_por_atendente(comercial)],
        "acoes_fechadas_diariamente": [ChartDataPoint(**x) for x in group_acoes_fechadas_diariamente(comercial)],
        "acoes_fechadas_campanha_NG_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_campanha_NG(comercial)],
        "acoes_fechadas_campanha_RA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_campanha_RA(comercial)],
        "acoes_fechadas_site_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_site(comercial)],
        "total_acoes_fechadas_por_rubrica": [ChartDataPoint(**x) for x in get_total_acoes_fechadas_por_rubrica(comercial)],
        "rubricas_total": [RubricaTotalRow(**x) for x in get_rubricas_total_tabela(comercial)],
        "comissionamento_comercial_por_atendente": [ComissionamentoComercialRow(**x) for x in get_comercial_comissionamento_por_atendente(comercial, protocolos)],
        "acoes_fechadas_indicacao_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_indicacao(comercial)],
        "acoes_fechadas_retorno_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_retorno(comercial)],
        "acoes_fechadas_resgate_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_resgate(comercial)],
        "acoes_fechadas_redes_sociais_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_redes_sociais(comercial)],
        "contratos_fechados_diariamente_por_atendente": [ChartDataPoint(**x) for x in group_contratos_fechados_diariamente_por_atendente(comercial)],
        "contratos_fechados_por_mes": [ChartDataPoint(**x) for x in group_contratos_fechados_por_mes(comercial)],
        "processos_fechados_por_mes": [ChartDataPoint(**x) for x in group_processos_fechados_por_mes(comercial)],
        "contratos_fechados_por_dia": [ChartDataPoint(**x) for x in group_contratos_fechados_por_dia(comercial)],
        "acoes_fechadas_por_dia": [ChartDataPoint(**x) for x in group_acoes_fechadas_por_dia(comercial)],
        "total_leads_por_atendente": TotalLeadsPorAtendente(**get_total_leads_por_atendente(actions)),
        "total_clientes_fechados_por_atendente": TotalClientesFechadosPorAtendente(**get_total_clientes_fechados_por_atendente(comercial)),
        "total_clientes_fechados_campanha_por_atendente": TotalClientesFechadosCampanhaPorAtendente(**get_total_clientes_fechados_campanha_por_atendente(comercial)),
        "taxa_fechamento_geral_por_atendente": TaxaFechamentoGeralPorAtendente(**get_taxa_fechamento_geral_por_atendente(actions, comercial)),
        "taxa_fechamento_campanha_por_cliente": TaxaFechamentoCampanhaPorCliente(**get_taxa_fechamento_campanha_por_cliente(actions, comercial)),
        "total_leads_campanha_por_atendente": TotalLeadsCampanhaPorAtendente(**get_total_leads_campanha_por_atendente(actions)),
        "total_leads_indicacao_ativa_por_atendente": TotalLeadsIndicacaoAtivaPorAtendente(**get_total_leads_indicacao_ativa_por_atendente(actions)),
        "total_clientes_fechados_indicacao_ativa_por_atendente": TotalClientesFechadosIndicacaoAtivaPorAtendente(**get_total_clientes_fechados_indicacao_ativa_por_atendente(comercial, actions)),
        "taxa_fechamento_indicacao_ativa_por_atendente": TaxaFechamentoIndicacaoAtivaPorAtendente(**get_taxa_fechamento_indicacao_ativa_por_atendente(actions, comercial)),
        "total_leads_indicacao_passiva_por_atendente": TotalLeadsIndicacaoPassivaPorAtendente(**get_total_leads_indicacao_passiva_por_atendente(actions)),
        "total_clientes_fechados_indicacao_passiva_por_atendente": TotalClientesFechadosIndicacaoPassivaPorAtendente(**get_total_clientes_fechados_indicacao_passiva_por_atendente(comercial, actions)),
        "taxa_fechamento_indicacao_passiva_por_atendente": TaxaFechamentoIndicacaoPassivaPorAtendente(**get_taxa_fechamento_indicacao_passiva_por_atendente(actions, comercial)),
        "total_leads_retorno_ativa_por_atendente": TotalLeadsRetornoAtivaPorAtendente(**get_total_leads_retorno_ativa_por_atendente(actions)),
        "total_clientes_fechados_retorno_ativa_por_atendente": TotalClientesFechadosRetornoAtivaPorAtendente(**get_total_clientes_fechados_retorno_ativa_por_atendente(comercial, actions)),
        "taxa_fechamento_retorno_ativa_por_atendente": TaxaFechamentoRetornoAtivaPorAtendente(**get_taxa_fechamento_retorno_ativa_por_atendente(actions, comercial)),
        "total_leads_retorno_passiva_por_atendente": TotalLeadsRetornoPassivaPorAtendente(**get_total_leads_retorno_passiva_por_atendente(actions)),
        "total_clientes_fechados_retorno_passiva_por_atendente": TotalClientesFechadosRetornoPassivaPorAtendente(**get_total_clientes_fechados_retorno_passiva_por_atendente(comercial, actions)),
        "taxa_fechamento_retorno_passiva_por_atendente": TaxaFechamentoRetornoPassivaPorAtendente(**get_taxa_fechamento_retorno_passiva_por_atendente(actions, comercial)),
        "total_leads_resgate_ativa_por_atendente": TotalLeadsResgateAtivaPorAtendente(**get_total_leads_resgate_ativa_por_atendente(actions)),
        "total_clientes_fechados_resgate_ativa_por_atendente": TotalClientesFechadosResgateAtivaPorAtendente(**get_total_clientes_fechados_resgate_ativa_por_atendente(comercial, actions)),
        "taxa_fechamento_resgate_ativa_por_atendente": TaxaFechamentoResgateAtivaPorAtendente(**get_taxa_fechamento_resgate_ativa_por_atendente(actions, comercial)),
        "total_leads_resgate_passiva_por_atendente": TotalLeadsResgatePassivaPorAtendente(**get_total_leads_resgate_passiva_por_atendente(actions)),
        "total_clientes_fechados_resgate_passiva_por_atendente": TotalClientesFechadosResgatePassivaPorAtendente(**get_total_clientes_fechados_resgate_passiva_por_atendente(comercial, actions)),
        "taxa_fechamento_resgate_passiva_por_atendente": TaxaFechamentoResgatePassivaPorAtendente(**get_taxa_fechamento_resgate_passiva_por_atendente(actions, comercial)),
    }
    return stats, charts


# v1: dashboard_routes.py:6997
def _build_protocolo_stats(
    protocolos: List[Dict],
    all_protocolos: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    comercial_geral: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    func_raw = get_protocolados_por_dia_por_funcionario(protocolos)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)
    pool_com_fm = get_comissao_com_fm(protocolos, comercial_geral or [])
    proporcional_am_pa, proporcional_pb = get_proporcionais_am_pa_pb_sobre_comissao_com_fm(protocolos, pool_com_fm)

    stats = {
        "protocolos_resolvidos": get_protocolos_resolvidos(protocolos),
        "protocolados_de_reajuizamento": get_protocolados_de_reajuizamento(protocolos),
        "nao_protocolados": get_nao_protocolados(all_protocolos),
        "nao_protocolados_de_reajuizamento": get_nao_protocolados_de_reajuizamento(all_protocolos),
        "valor_causa_protocolo_novo": get_valor_causa_protocolo_novo(protocolos),
        "valor_causa_protocolo_2026": get_valor_causa_protocolo_2026(all_protocolos),
        "meta_anual_comercial": META_VALOR_CAUSA_2026,
        "comparativo_protocolos_resolvidos": get_comparativo_protocolos_resolvidos(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "protocolos_resolvidos_periodo_anterior": get_protocolos_resolvidos_periodo_anterior(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "comparativo_valor_causa_protocolo": get_comparativo_valor_causa_protocolo(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "valor_causa_protocolo_periodo_anterior": get_valor_causa_protocolo_periodo_anterior(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "comparativo_nao_protocolados": get_comparativo_nao_protocolados(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "media_tempo_protocolado": get_media_tempo_protocolado(protocolos),
        "mediana_tempo_protocolado": get_mediana_tempo_protocolado(protocolos),
        "comparativo_tempo_medio_protocolos_resolvidos": get_comparativo_tempo_medio_protocolos_resolvidos(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "tempo_medio_contratacao_protocolo": get_media_tempo_contratacao_protocolado(protocolos),
        "mediana_tempo_contratacao_protocolo": get_mediana_tempo_contratacao_protocolado(protocolos),
        "comparativo_tempo_medio_contratacao_protocolo": get_comparativo_tempo_medio_contratacao_protocolado(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_contratacao_protocolo": get_comparativo_mediana_tempo_contratacao_protocolado(protocolos, all_protocolos=all_protocolos, from_date=from_date, to_date=to_date),
        "fator_multiplicador": get_fator_multiplicador(protocolos),
        "valor_por_estado_am_pa": get_valor_por_estado_am_pa(protocolos),
        "valor_por_estado_pb": get_valor_por_estado_pb(protocolos),
        "comissao_com_fm": pool_com_fm,
        "proporcional_am_pa": proporcional_am_pa,
        "proporcional_pb": proporcional_pb,
    }
    charts = {
        "protocolados_por_materia": [ChartDataPoint(**x) for x in group_protocolados_por_materia(protocolos)],
        "protocolados_por_funcionario": [ChartDataPoint(**x) for x in group_protocolados_por_funcionario(protocolos)],
        "protocolados_por_sistema": [ChartDataPoint(**x) for x in group_protocolados_por_sistema(protocolos)],
        "nao_protocolados_por_materia": [ChartDataPoint(**x) for x in group_nao_protocolados_por_materia(all_protocolos)],
        "nao_protocolados_por_funcionario": [ChartDataPoint(**x) for x in group_nao_protocolados_por_funcionario(all_protocolos)],
        "valor_causa_protocolo_novo_por_funcionario": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolo_novo_por_funcionario(protocolos))],
        "media_protocolados_por_funcionario": [ChartDataPoint(**x) for x in get_media_protocolados_por_funcionario(protocolos, from_date=from_date, to_date=to_date)],
        "comissionamento_protocolo_por_funcionario": [ComissionamentoProtocoloRow(**x) for x in get_protocolo_comissionamento_por_funcionario(protocolos)],
        "protocolados_por_mes": [ChartDataPoint(**x) for x in group_protocolados_por_mes(protocolos)],
        "valor_causa_protocolados_por_mes": [ChartDataPoint(**x) for x in group_valor_causa_protocolados_por_mes(protocolos)],
        "nao_protocolados_por_mes": [ChartDataPoint(**x) for x in group_nao_protocolados_por_mes(all_protocolos)],
        "protocolados_por_dia": [ChartDataPoint(**x) for x in group_protocolados_por_dia(protocolos)],
        "valor_causa_protocolados_por_dia": [ChartDataPoint(**x) for x in group_valor_causa_protocolados_por_dia(protocolos)],
        "funcionarios_protocolo": funcionarios,
        "protocolados_por_dia_por_funcionario": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "valor_causa_protocolo_novo_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolo_novo_por_atendente(protocolos))],
        "valor_causa_protocolo_nao_protocolado_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolo_nao_protocolado_por_atendente(all_protocolos))],
        "protocolos_resolvidos_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_protocolos_por_atendente(protocolos))],
        "nao_protocolados_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_protocolados_por_atendente(all_protocolos))],
    }
    return stats, charts


# v1: dashboard_routes.py:7241
def _build_peticionamento_stats(
    peticionamento: List[Dict],
    all_peticionamento: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    peticionamento_taxa: Optional[List[Dict]] = None,
    all_peticionamento_taxa: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    func_raw = get_peticionados_por_dia_por_funcionario(peticionamento)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "total_peticionados": get_total_peticionados(peticionamento),
        "peticionados_automaticamente": get_peticionados_automaticamente(peticionamento),
        "peticionados_manualmente": get_peticionados_manualmente(peticionamento),
        "processos_em_revisao": get_processos_em_revisao(peticionamento),
        "nao_peticionados": get_nao_peticionados(all_peticionamento),
        "valor_causa_confeccionado": get_valor_causa_confeccionado(peticionamento),
        "ticket_medio_confeccionado": get_ticket_medio_confeccionado(peticionamento),
        "resolvidos_reajuizamento_pet": get_resolvidos_reajuizamento_pet(peticionamento),
        "nao_resolvidos_reajuizamento": get_nao_resolvidos_reajuizamento(peticionamento),
        "media_tempo_peticionado": get_media_tempo_peticionado(peticionamento),
        "mediana_tempo_peticionado": get_mediana_tempo_peticionado(peticionamento),
        "comparativo_peticionados": get_comparativo_peticionados(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_tempo_medio_peticionado": get_comparativo_tempo_medio_peticionado(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_pet": get_comparativo_tempo_mediana_peticionado(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_peticionados_manualmente": get_comparativo_peticionados_manualmente(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_peticionados_automaticamente": get_comparativo_peticionados_automaticamente(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_peticionados_reajuizamento": get_comparativo_peticionados_reajuizamento(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_nao_peticionados_reajuizamento": get_comparativo_nao_peticionados_reajuizamento(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_valor_causa_confeccionado": get_comparativo_valor_causa_confeccionado(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "comparativo_ticket_medio_confeccionado": get_comparativo_ticket_medio_confeccionado(peticionamento, all_peticionados=all_peticionamento, from_date=from_date, to_date=to_date),
        "peticionamento_taxa_resolvidos": get_peticionamento_taxa_resolvidos(peticionamento, all_peticionamento),
        "peticionamento_taxa_nao_resolvidos": get_peticionamento_taxa_nao_resolvidos(peticionamento, all_peticionamento),
    }
    charts = {
        "peticionados_por_materia": [ChartDataPoint(**x) for x in group_peticionados_por_materia(peticionamento)],
        "nao_peticionados_por_materia": [ChartDataPoint(**x) for x in group_nao_peticionados_por_materia(peticionamento)],
        "nao_peticionados_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_peticionados_por_atendente(all_peticionamento), cast_int=True)],
        "peticionados_por_dia": [ChartDataPoint(**x) for x in group_peticionados_por_dia(peticionamento)],
        "funcionarios_peticionamento": funcionarios,
        "peticionados_por_dia_por_funcionario": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "media_peticionado_por_funcionario": [ChartDataPoint(**x) for x in get_media_peticionado_por_funcionario(peticionamento, from_date=from_date, to_date=to_date)],
        "valor_peticionado_por_funcionario": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_peticionado_por_funcionario(peticionamento))],
        "peticionados_por_funcionario": [ChartDataPoint(**x) for x in group_peticionados_por_funcionario(peticionamento)],
        "nao_peticionados_por_funcionario": [ChartDataPoint(**x) for x in group_nao_peticionados_por_funcionario(all_peticionamento)],
        "peticionados_por_mes": [ChartDataPoint(**x) for x in group_peticionados_por_mes(peticionamento)],
        "nao_peticionados_por_mes": [ChartDataPoint(**x) for x in group_nao_peticionados_por_mes(peticionamento)],
        "comissionamento_peticionamento_por_funcionario": [
            ComissionamentoPeticionamentoRow(**x)
            for x in get_peticionamento_comissionamento_por_funcionario(
                peticionamento, all_peticionamento, peticionamento_taxa, all_peticionamento_taxa,
            )
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:7299
def _build_org_doc_stats(
    org_doc: List[Dict],
    all_org_doc: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    # CORRIGIDO: chamada única (estava triplicada)
    func_raw = get_resolvidos_por_dia_por_funcionario(org_doc)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "resolvidos_total": get_resolvidos_total(org_doc),
        "organizados_manualmente": get_organizados_manualmente(org_doc),
        "organizados_e_peticionados_automaticamente": get_organizados_e_peticionados_automaticamente(org_doc),
        "nao_organizados": get_nao_organizados(org_doc),
        "cancelados": get_cancelados(org_doc),
        "retorno_pet": get_retorno_pet(org_doc),
        "retorno_pendencia": get_retorno_pendencia(org_doc),
        "resolvidos_reajuizamento": get_resolvidos_reajuizamento(org_doc),
        "media_tempo_resolvidos": get_media_tempo_resolvidos(org_doc),
        "mediana_tempo_resolvidos": get_mediana_tempo_resolvidos(org_doc),
        "comparativo_resolvidos_total": get_comparativo_resolvidos_total(org_doc, all_organizados=all_org_doc, from_date=from_date, to_date=to_date),
        "comparativo_organizados_manualmente": get_comparativo_organizados_manualmente(org_doc, all_organizados=all_org_doc, from_date=from_date, to_date=to_date),
        "comparativo_resolvidos_reajuizamento": get_comparativo_resolvidos_reajuizamento(org_doc, all_organizados=all_org_doc, from_date=from_date, to_date=to_date),
        "comparativo_organizados_e_peticionados_automaticamente": get_comparativo_organizados_e_peticionados_automaticamente(org_doc, all_organizados=all_org_doc, from_date=from_date, to_date=to_date),
        "comparativo_cancelados": get_comparativo_cancelados(org_doc, all_organizados=all_org_doc, from_date=from_date, to_date=to_date),
        "comparativo_tempo_medio_resolvidos_org_doc": get_comparativo_tempo_medio_resolvidos_org_doc(org_doc, all_organizados=all_org_doc, from_date=from_date, to_date=to_date),
    }
    charts = {
        "nao_organizados_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_organizados_por_atendente(all_org_doc), cast_int=True)],
        "resolvidos_total_por_materia": [ChartDataPoint(**x) for x in group_resolvidos_total_por_materia(org_doc)],
        "nao_organizados_total_por_materia": [ChartDataPoint(**x) for x in group_nao_organizados_total_por_materia(org_doc)],
        "nao_organizados_por_funcionario": [ChartDataPoint(**x) for x in group_nao_organizados_por_funcionario(org_doc)],
        "resolvidos_por_funcionario": [ChartDataPoint(**x) for x in group_resolvidos_por_funcionario(org_doc)],
        "media_resolvidos_por_funcionario": [ChartDataPoint(**x) for x in get_media_resolvidos_por_funcionario(org_doc, from_date=from_date, to_date=to_date)],
        "resolvidos_total_por_mes": [ChartDataPoint(**x) for x in group_resolvidos_total_por_mes(all_org_doc)],
        "valor_causa_por_funcionario": [ChartDataPoint(**x) for x in get_valor_causa_por_funcionario(org_doc)],
        "comissionamento_por_funcionario": [ComissionamentoOrgDocRow(**x) for x in get_comissionamento_por_funcionario(org_doc)],
        "nao_resolvidos_total_por_mes": [ChartDataPoint(**x) for x in group_nao_resolvidos_total_por_mes(org_doc)],
        "resolvidos_por_dia_org": [ChartDataPoint(**x) for x in group_resolvidos_por_dia(org_doc)],
        "funcionarios_org_doc": funcionarios,
        "resolvidos_por_dia_por_funcionario_org": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
    }
    return stats, charts


# v1: dashboard_routes.py:7345
def _build_pendencias_stats(
    pendencias: List[Dict],
    all_pendencias: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    func_raw = get_pendencias_resolvidas_por_dia_por_funcionario(pendencias)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "pendencias_total": get_pendencias_total(pendencias),
        "pendencias_nao_resolvidas": get_pendencias_nao_resolvidas(pendencias),
        "pendencias_nao_resolvidas_com_atraso": get_pendencias_nao_resolvidas_com_atraso(pendencias),
        "pendencias_resolvidas": get_pendencias_resolvidas(pendencias),
        "pendencias_canceladas": get_pendencias_canceladas(pendencias),
        "pendencias_taxa_nao_resolvidos": get_pendencias_taxa_nao_resolvidos(pendencias),
        "pendencias_taxa_resolvidos": get_pendencias_taxa_resolvidos(pendencias),
        "pendencias_taxa_canceladas": get_pendencias_taxa_canceladas(pendencias),
        "pendencias_nao_resolvidas_reajuizamento": get_pendencias_nao_resolvidas_reajuizamento(pendencias),
        "pendencias_resolvidas_reajuizamento": get_pendencias_resolvidas_reajuizamento(pendencias),
        "pendencias_triagem": get_pendencias_triagem(pendencias),
        "media_tempo_resolvidos_pendencia": get_media_tempo_resolvidos_pendencia(pendencias),
        "mediana_tempo_resolvidos_pendencia": get_mediana_tempo_resolvidos_pendencia(pendencias),
        "comparativo_pendencias_resolvidas": get_comparativo_pendencias_resolvidas(pendencias, all_pendencias=all_pendencias, from_date=from_date, to_date=to_date),
        "comparativo_tempo_medio_pendencias_resolvidas": get_comparativo_tempo_medio_pendencias_resolvidas(pendencias, all_pendencias=all_pendencias, from_date=from_date, to_date=to_date),
    }
    charts = {
        "pendencias_nao_resolvidas_por_atendente": [ChartDataPoint(**x) for x in dict_to_chart_data(get_pendencias_nao_resolvidas_por_atendente(all_pendencias), cast_int=True)],
        "pendencias_nao_resolvidas_por_origem": [ChartDataPoint(**x) for x in get_pendencias_nao_resolvidas_por_origem(pendencias)],
        "pendencias_resolvidas_por_mes": [ChartDataPoint(**x) for x in group_pendencias_resolvidas_por_mes(pendencias)],
        "media_pendencias_resolvidas_por_funcionario": [ChartDataPoint(**x) for x in get_media_pendencias_resolvidas_por_funcionario(pendencias)],
        "pendencias_resolvidas_por_dia": [ChartDataPoint(**x) for x in group_pendencias_resolvidas_por_dia(pendencias)],
        "funcionarios_pendencias": funcionarios,
        "pendencias_resolvidas_por_dia_por_funcionario": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "comissionamento_pendencias_por_funcionario": [
            ComissionamentoPendenciaRow(**x) for x in get_pendencias_comissionamento_por_funcionario(pendencias)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:7386
def _build_comercial_LA_stats(ctx: ComercialLAContext) -> Tuple[Dict, Dict]:
    stats = {
        "clientes_campanha_LA": get_clientes_campanha(ctx.comercial),
        "clientes_indicacao_LA": get_clientes_indicacao_LA(ctx.comercial),
        "clientes_redes_sociais_LA": get_clientes_redes_sociais_LA(ctx.comercial),
        "clientes_retorno_LA": get_clientes_retorno_LA(ctx.comercial),
        "clientes_parceiro_LA": get_clientes_parceiro_LA(ctx.comercial),
        "clientes_externos_LA": get_clientes_externos_LA(ctx.comercial),
        "clientes_todos_LA": get_clientes_todos_LA(ctx.comercial),
        "clientes_cancelados_LA": get_clientes_cancelados_LA(ctx.comercial),
        "acoes_fechadas_LA": get_acoes_fechadas_LA(ctx.comercial),
        "total_rubricas_reunidas_fechadas_LA": get_rubricas_reunidas_fechadas_LA(ctx.comercial),
        "taxa_aproveitamento_LA": get_taxa_aproveitamento_LA(ctx.comercial),
        "comparativo_clientes_campanha_LA": get_comparativo_clientes_campanha_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_indicacao_LA": get_comparativo_clientes_indicacao_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_externos_LA": get_comparativo_clientes_externos_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_parceiro_LA": get_comparativo_clientes_parceiro_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_retorno_LA": get_comparativo_clientes_retorno_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_redes_sociais_LA": get_comparativo_clientes_redes_sociais_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_cancelados_LA": get_comparativo_clientes_cancelados_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_acoes_fechadas_LA": get_comparativo_acoes_fechadas_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "acoes_fechadas_periodo_anterior_LA": get_acoes_fechadas_periodo_anterior_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_taxa_aproveitamento_LA": get_comparativo_taxa_aproveitamento_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_clientes_total_LA": get_comparativo_clientes_total_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "clientes_total_periodo_anterior_LA": get_clientes_total_periodo_anterior_LA(ctx.comercial, ctx.all_comercial, from_date=ctx.from_date, to_date=ctx.to_date),
        "total_leads_LA": get_total_leads_LA(ctx.actions),
        "total_leads_anuncio_LA": get_total_leads_anuncio_LA(ctx.actions),
        "taxa_leads_geral_LA": get_taxa_leads_geral_LA(ctx.actions, ctx.comercial),
        "taxa_leads_anuncio_LA": get_taxa_leads_anuncio_LA(ctx.actions, ctx.comercial),
        "protocolos_resolvidos_LA": get_protocolos_resolvidos_LA(ctx.protocolo),
        "valor_causa_protocolado_LA": get_valor_causa_protocolado_LA(ctx.protocolo),
        "valor_causa_protocolado_LA_2026": get_valor_causa_protocolado_LA_2026(ctx.all_protocolo),
        "meta_anual_comercial_LA": META_VALOR_CAUSA_2026_LA,
        "ticket_medio_protocolos_resolvidos_LA": get_ticket_medio_protocolos_resolvidos_LA(ctx.protocolo),
        "comparativo_protocolos_resolvidos_LA": get_comparativo_protocolos_resolvidos_LA(ctx.protocolo, ctx.all_protocolo, from_date=ctx.from_date, to_date=ctx.to_date),
        "protocolos_resolvidos_periodo_anterior_LA": get_protocolos_resolvidos_periodo_anterior_LA(ctx.protocolo, ctx.all_protocolo, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_valor_causa_protocolado_LA": get_comparativo_valor_causa_protocolado_LA(ctx.protocolo, ctx.all_protocolo, from_date=ctx.from_date, to_date=ctx.to_date),
        "valor_causa_protocolado_periodo_anterior_LA": get_valor_causa_protocolado_periodo_anterior_LA(ctx.protocolo, ctx.all_protocolo, from_date=ctx.from_date, to_date=ctx.to_date),
        "comparativo_ticket_medio_protocolos_resolvidos_LA": get_comparativo_ticket_medio_protocolos_resolvidos_LA(ctx.protocolo, ctx.all_protocolo, from_date=ctx.from_date, to_date=ctx.to_date),
        "comissao_base_LA": get_comissao_base_LA(ctx.comercial),
    }
    charts = {
        "total_acoes_fechadas_por_rubrica_LA": [ChartDataPoint(**x) for x in get_total_acoes_fechadas_por_rubrica_LA(ctx.comercial)],
        "acoes_fechadas_campanha_LA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_campanha_LA(ctx.comercial)],
        "acoes_fechadas_indicacao_LA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_indicacao_LA(ctx.comercial)],
        "acoes_fechadas_retorno_LA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_retorno_LA(ctx.comercial)],
        "acoes_fechadas_redes_sociais_LA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_redes_sociais_LA(ctx.comercial)],
        "acoes_fechadas_parceiros_LA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_parceiros_LA(ctx.comercial)],
        "acoes_fechadas_externos_LA_por_rubrica": [ChartDataPoint(**x) for x in get_acoes_fechadas_externos_LA(ctx.comercial)],
        "acoes_fechadas_por_atendente_LA": [ChartDataPoint(**x) for x in get_total_acoes_fechadas_por_atendente_LA(ctx.comercial)],
        "acoes_fechadas_diariamente_por_atendente_LA": [ChartDataPoint(**x) for x in group_acoes_fechadas_diariamente_por_atendente_LA(ctx.comercial)],
        "contratos_fechados_diariamente_por_atendente_LA": [ChartDataPoint(**x) for x in group_contratos_fechados_diariamente_por_atendente_LA(ctx.comercial)],
        "contratos_fechados_por_mes_LA": [ChartDataPoint(**x) for x in group_contratos_fechados_por_mes_LA(ctx.comercial)],
        "processos_fechados_por_mes_LA": [ChartDataPoint(**x) for x in group_processos_fechados_por_mes_LA(ctx.comercial)],
        "contratos_fechados_por_dia_LA": [ChartDataPoint(**x) for x in group_contratos_fechados_por_dia_LA(ctx.comercial)],
        "acoes_fechadas_por_dia_LA": [ChartDataPoint(**x) for x in group_acoes_fechadas_por_dia_LA(ctx.comercial)],
        "valor_causa_protocolado_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolado_por_atendente_LA(ctx.protocolo))],
        "valor_causa_nao_protocolado_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_nao_protocolado_por_atendente_LA(ctx.all_protocolo))],
        "protocolos_resolvidos_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_protocolos_resolvidos_por_atendente_LA(ctx.protocolo), cast_int=True)],
        "nao_protocolados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_protocolados_por_atendente_LA(ctx.all_protocolo), cast_int=True)],
        "nao_peticionados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_peticionados_por_atendente_LA(ctx.all_peticionamento), cast_int=True)],
        "nao_organizados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_organizados_por_atendente_LA(ctx.all_org_doc), cast_int=True)],
        "pendencias_nao_resolvidas_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_pendencias_nao_resolvidas_por_atendente_LA(ctx.all_pendencias), cast_int=True)],
        "comissionamento_comercial_LA_por_atendente": [
            ComissionamentoComercialLARow(**x)
            for x in get_comercial_comissionamento_por_atendente_LA(ctx.comercial, ctx.protocolo)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:10848
def _build_org_doc_LA_stats(
    org_doc_LA: List[Dict],
    all_org_doc_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    func_raw = get_resolvidos_por_dia_por_funcionario_LA(org_doc_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "total_organizados_LA": get_total_organizados_LA(org_doc_LA),
        "nao_organizados_LA": get_nao_organizados_LA(org_doc_LA),
        "total_organizados_manualmente_LA": get_total_organizados_manualmente_LA(org_doc_LA),
        "total_organizados_automaticamente_LA": get_total_organizados_automaticamente_LA(org_doc_LA),
        "retorno_pendencia_LA": get_retorno_pendencia_LA(org_doc_LA),
        "cancelados_LA": get_cancelados_LA(org_doc_LA),
        "media_tempo_resolvidos_LA": get_media_tempo_resolvidos_LA(org_doc_LA),
        "mediana_tempo_resolvidos_LA": get_mediana_tempo_resolvidos_LA(org_doc_LA),
        "comparativo_resolvidos_total_LA": get_comparativo_resolvidos_total_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_organizados_manualmente_LA": get_comparativo_organizados_manualmente_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_organizados_automaticamente_LA": get_comparativo_organizados_automaticamente_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_retorno_pendencia_LA": get_comparativo_retorno_pendencia_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_cancelados_LA": get_comparativo_cancelados_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
    }
    charts = {
        "nao_organizados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_organizados_por_atendente_LA(all_org_doc_LA), cast_int=True)],
        "nao_organizados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_nao_organizados_por_funcionario_LA(org_doc_LA)],
        "organizados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_organizados_por_funcionario_LA(org_doc_LA)],
        "valor_causa_por_funcionario_LA": [ChartDataPoint(**x) for x in get_valor_causa_por_funcionario_LA(org_doc_LA)],
        "comissionamento_org_doc_LA_por_funcionario": [ComissionamentoOrgDocRow(**x) for x in get_comissionamento_por_funcionario_LA(org_doc_LA)],
        "media_resolvidos_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_resolvidos_por_funcionario_LA(org_doc_LA)],
        "organizados_total_por_materia_LA": [ChartDataPoint(**x) for x in group_organizados_total_por_materia_LA(org_doc_LA)],
        "nao_organizados_total_por_materia_LA": [ChartDataPoint(**x) for x in group_nao_organizados_total_por_materia_LA(org_doc_LA)],
        "nao_organizados_total_por_mes_LA": [ChartDataPoint(**x) for x in group_nao_organizados_total_por_mes_LA(all_org_doc_LA)],
        "resolvidos_total_por_mes_LA": [ChartDataPoint(**x) for x in group_resolvidos_total_por_mes_LA(all_org_doc_LA)],
        "resolvidos_por_dia_LA": [ChartDataPoint(**x) for x in group_resolvidos_por_dia_LA(org_doc_LA)],
        "funcionarios_org_doc_LA": funcionarios,
        "resolvidos_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
    }
    return stats, charts


# v1: dashboard_routes.py:10890
def _build_protocolo_LA_stats(
    protocolo_LA: List[Dict],
    all_protocolo_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    comercial_LA: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    func_raw = get_protocolados_por_dia_por_funcionario_LA(protocolo_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)
    pool_com_fm = get_comissao_com_fm_LA(protocolo_LA, comercial_LA or [])
    taxa_prot_la = get_taxa_protocolados_LA(protocolo_LA, all_protocolo_LA, from_date, to_date)

    stats = {
        "protocolos_resolvidos_LA": get_protocolos_resolvidos_LA(protocolo_LA),
        "protocolos_represados_LA": get_protocolos_represados_LA(protocolo_LA),
        "valor_causa_protocolado_LA": get_valor_causa_protocolado_LA(protocolo_LA),
        "ticket_medio_protocolos_resolvidos_LA": get_ticket_medio_protocolos_resolvidos_LA(protocolo_LA),
        "media_tempo_protocolo_LA": get_media_tempo_protocolado_LA(protocolo_LA),
        "mediana_tempo_protocolo_LA": get_mediana_tempo_protocolado_LA(protocolo_LA),
        "comparativo_tempo_medio_protocolos_resolvidos_LA": get_comparativo_tempo_medio_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_protocolos_resolvidos_LA": get_comparativo_mediana_tempo_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "taxa_protocolados_LA": taxa_prot_la,
        "entradas_protocolo_LA": get_entradas_protocolo_LA(all_protocolo_LA, from_date, to_date),
        "comparativo_protocolos_resolvidos_LA": get_comparativo_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "protocolos_resolvidos_periodo_anterior_LA": get_protocolos_resolvidos_periodo_anterior_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_valor_causa_protocolado_LA": get_comparativo_valor_causa_protocolado_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "valor_causa_protocolado_periodo_anterior_LA": get_valor_causa_protocolado_periodo_anterior_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_ticket_medio_protocolos_resolvidos_LA": get_comparativo_ticket_medio_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "valor_causa_protocolado_LA_2026": get_valor_causa_protocolado_LA_2026(all_protocolo_LA),
        "meta_anual_comercial_LA": META_VALOR_CAUSA_2026_LA,
        "fator_multiplicador_LA": get_fator_multiplicador_LA(protocolo_LA),
        "comissao_com_fm_LA": pool_com_fm,
        "tempo_medio_contratacao_protocolo_LA": get_media_tempo_contratacao_protocolado_LA(protocolo_LA),
        "mediana_tempo_contratacao_protocolo_LA": get_mediana_tempo_contratacao_protocolado_LA(protocolo_LA),
        "comparativo_tempo_medio_contratacao_protocolo_LA": get_comparativo_tempo_medio_contratacao_protocolado_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_contratacao_protocolo_LA": get_comparativo_mediana_tempo_contratacao_protocolado_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
    }
    charts = {
        "valor_causa_protocolado_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolado_por_atendente_LA(protocolo_LA))],
        "valor_causa_nao_protocolado_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_nao_protocolado_por_atendente_LA(all_protocolo_LA))],
        "protocolos_resolvidos_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_protocolos_resolvidos_por_atendente_LA(protocolo_LA), cast_int=True)],
        "nao_protocolados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_protocolados_por_atendente_LA(all_protocolo_LA), cast_int=True)],
        "protocolados_por_dia_LA": [ChartDataPoint(**x) for x in group_protocolados_por_dia_LA(protocolo_LA)],
        "valor_causa_protocolados_por_dia_LA": [ChartDataPoint(**x) for x in group_valor_causa_protocolados_por_dia_LA(protocolo_LA)],
        "funcionarios_protocolo_LA": funcionarios,
        "protocolados_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "protocolados_por_materia_LA": [ChartDataPoint(**x) for x in group_protocolados_por_materia_LA(protocolo_LA)],
        "protocololados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_protocolados_por_funcionario_LA(protocolo_LA)],
        "represados_protocolo_por_materia_LA": [ChartDataPoint(**x) for x in group_represados_por_materia_LA(all_protocolo_LA)],
        "represados_protocolo_por_funcionario_LA": [ChartDataPoint(**x) for x in group_represados_por_funcionario_LA(all_protocolo_LA)],
        "valor_causa_protocolo_por_funcionario_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolado_por_funcionario_LA(protocolo_LA))],
        "comissionamento_protocolo_LA_por_funcionario": [ComissionamentoProtocoloRow(**x) for x in get_protocolo_comissionamento_por_funcionario_LA(protocolo_LA, taxa=taxa_prot_la)],
        "protocolados_por_sistema_LA": [ChartDataPoint(**x) for x in group_protocolados_por_sistema_LA(protocolo_LA)],
        "protocolados_por_mes_LA": [ChartDataPoint(**x) for x in group_protocolados_por_mes_LA(protocolo_LA)],
        "valor_causa_protocolados_por_mes_LA": [ChartDataPoint(**x) for x in group_valor_causa_protocolados_por_mes_LA(protocolo_LA)],
        "media_protocolados_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_protocolados_por_funcionario_LA(protocolo_LA, from_date=from_date, to_date=to_date)],
        "represados_por_mes_LA": [ChartDataPoint(**x) for x in group_represados_por_mes_LA(protocolo_LA)],
    }
    return stats, charts


# v1: dashboard_routes.py:10951
def _build_peticionamento_LA_stats(
    peticionamento_LA: List[Dict],
    all_peticionamento_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    peticionamento_LA_taxa: Optional[List[Dict]] = None,
    all_peticionamento_LA_taxa: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    func_raw = get_confeccionados_por_dia_por_funcionario_LA(peticionamento_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "total_confeccionados_LA": get_total_confeccionados_LA(peticionamento_LA),
        "confeccionados_manualmente_LA": get_total_confeccionados_manualmente_LA(peticionamento_LA),
        "confeccionados_automaticamente_LA": get_total_confeccionados_automaticamente_LA(peticionamento_LA),
        "nao_confeccionados_LA": get_nao_confeccionados_LA(all_peticionamento_LA),
        "valor_causa_confeccionado_LA": get_valor_causa_confeccionado_LA(peticionamento_LA),
        "ticket_medio_confeccionado_LA": get_ticket_medio_confeccionados_LA(peticionamento_LA),
        "tempo_medio_confeccao_LA": get_media_tempo_confeccionado_LA(peticionamento_LA),
        "mediana_tempo_confeccao_LA": get_mediana_tempo_confeccionado_LA(peticionamento_LA),
        "comparativo_confeccionados_LA": get_comparativo_confeccionados_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_confeccionados_automaticamente_LA": get_comparativo_confeccionados_automaticamente_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_confeccionados_manualmente_LA": get_comparativo_confeccionados_manualmente_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_valor_causa_confeccionado_LA": get_comparativo_valor_causa_confeccionado_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_ticket_medio_confeccionado_LA": get_comparativo_ticket_medio_confeccionado_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_tempo_medio_confeccionado_LA": get_comparativo_tempo_medio_confeccionado_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_confeccionado_LA": get_comparativo_mediana_tempo_confeccionadoLA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "peticionamento_taxa_resolvidos_LA": get_peticionamento_taxa_resolvidos_LA(peticionamento_LA, all_peticionamento_LA),
        "peticionamento_taxa_nao_resolvidos_LA": get_peticionamento_taxa_nao_resolvidos_LA(peticionamento_LA, all_peticionamento_LA),
        "peticionamento_taxa_retorno_protocolo_LA": get_peticionamento_taxa_retorno_protocolo_LA(peticionamento_LA),
        "peticionamento_qtd_retorno_protocolo_LA": get_peticionamento_qtd_retorno_protocolo_LA(peticionamento_LA),
        "peticionamento_qtd_entrada_protocolo_LA": get_peticionamento_qtd_entrada_protocolo_LA(peticionamento_LA),
    }
    charts = {
        "confeccionados_por_dia_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_dia_LA(peticionamento_LA)],
        "funcionarios_confeccao_LA": funcionarios,
        "confeccionados_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "confeccionados_por_materia_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_materia_LA(peticionamento_LA)],
        "nao_confeccionados_por_materia_LA": [ChartDataPoint(**x) for x in group_nao_confeccionados_por_materia_LA(all_peticionamento_LA)],
        "confeccionados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_funcionario_LA(peticionamento_LA)],
        "nao_confeccionados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_nao_confeccionados_por_funcionario_LA(all_peticionamento_LA)],
        "valor_confeccionado_por_funcionario_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_confeccionado_por_funcionario_LA(peticionamento_LA))],
        "media_confeccionado_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_confeccionado_por_funcionario_LA(peticionamento_LA, from_date=from_date, to_date=to_date)],
        "confeccionados_por_mes_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_mes_LA(peticionamento_LA)],
        "nao_confeccionados_por_mes_LA": [ChartDataPoint(**x) for x in group_nao_confeccionados_por_mes_LA(peticionamento_LA)],
        "comissionamento_peticionamento_LA_por_funcionario": [
            ComissionamentoPeticionamentoRow(**x)
            for x in get_peticionamento_comissionamento_por_funcionario_LA(
                peticionamento_LA, all_peticionamento_LA, peticionamento_LA_taxa, all_peticionamento_LA_taxa,
            )
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:11006
def _build_andamento_LA_stats(
    andamento_LA: List[Dict],
    all_andamento_LA: List[Dict],
) -> Tuple[Dict, Dict]:
    stats = {
        "total_andamento_processual_LA": get_andamento_total_LA(andamento_LA),
        "andamento_processual_resolvidos_LA": get_andamento_resolvido_LA(andamento_LA),
        "andamento_processual_nao_resolvidos_LA": get_andamento_nao_resolvido_LA(andamento_LA),
        "media_avaliacao_LA": get_andamento_media_avaliacao_LA(andamento_LA),
        "taxa_resolvidos_LA": get_andamento_taxa_resolvidos_LA(andamento_LA),
        "taxa_nao_resolvidos_LA": get_andamento_taxa_nao_resolvidos_LA(andamento_LA),
        "media_espera_LA": get_andamento_media_tempo_espera_LA(andamento_LA),
        "mediana_espera_LA": get_andamento_mediana_tempo_espera_LA(andamento_LA),
        "media_atendimento_LA": get_andamento_media_tempo_atendimento_LA(andamento_LA),
        "mediana_atendimento_LA": get_andamento_mediana_tempo_atendimento_LA(andamento_LA),
    }
    charts = {
        "andamento_processual_por_colaborador_LA": [
            ChartDataPoint(**x) for x in group_andamento_processual_by_colaborador_LA(andamento_LA)
        ],
        "andamento_processual_por_colaborador_avaliacao_LA": [
            ChartDataPoint(**x) for x in group_andamento_processual_by_colaborador_avaliacao_LA(andamento_LA)
        ],
        "andamento_processual_total_por_mes_LA": [
            ChartDataPoint(**x) for x in group_andamento_processual_total_por_mes_LA(all_andamento_LA)
        ],
        "comissionamento_andamento_LA_por_funcionario": [
            ComissionamentoAndamentoRow(**x)
            for x in get_andamento_comissionamento_por_funcionario_LA(andamento_LA)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:11040
def _build_pendencias_LA_stats(
    pendencias_LA: List[Dict],
    all_pendencias_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    func_raw = get_pendencias_resolvidas_por_dia_por_funcionario_LA(pendencias_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "pendencias_total_LA": get_pendencias_total_LA(pendencias_LA),
        "pendencias_nao_resolvidas_LA": get_pendencias_nao_resolvidas_LA(pendencias_LA),
        "pendencias_nao_resolvidas_com_atraso_LA": get_pendencias_nao_resolvidas_com_atraso_LA(pendencias_LA),
        "pendencias_resolvidas_LA": get_pendencias_resolvidas_LA(pendencias_LA),
        "pendencias_canceladas_LA": get_pendencias_canceladas_LA(pendencias_LA),
        "pendencias_taxa_nao_resolvidos_LA": get_pendencias_taxa_nao_resolvidos_LA(pendencias_LA),
        "pendencias_taxa_resolvidos_LA": get_pendencias_taxa_resolvidos_LA(pendencias_LA),
        "pendencias_taxa_canceladas_LA": get_pendencias_taxa_canceladas_LA(pendencias_LA),
        "pendencias_triagem_LA": get_pendencias_triagem_LA(pendencias_LA),
        "media_tempo_resolvidos_pendencia_LA": get_media_tempo_resolvidos_pendencia_LA(pendencias_LA),
        "mediana_tempo_resolvidos_pendencia_LA": get_mediana_tempo_resolvidos_pendencia_LA(pendencias_LA),
    }
    charts = {
        "pendencias_nao_resolvidas_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_pendencias_nao_resolvidas_por_atendente_LA(all_pendencias_LA), cast_int=True)],
        # CORRIGIDO: chaves com sufixo _LA para não sobrescrever dados NG no dashboard comercial
        "pendencias_nao_resolvidas_por_origem_LA": [ChartDataPoint(**x) for x in get_pendencias_nao_resolvidas_por_origem_LA(pendencias_LA)],
        "pendencias_resolvidas_por_mes_LA": [ChartDataPoint(**x) for x in group_pendencias_resolvidas_por_mes_LA(pendencias_LA)],
        "media_pendencias_resolvidas_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_pendencias_resolvidas_por_funcionario_LA(pendencias_LA)],
        "pendencias_resolvidas_por_dia_LA": [ChartDataPoint(**x) for x in group_pendencias_resolvidas_por_dia_LA(pendencias_LA)],
        "funcionarios_pendencias_LA": funcionarios,
        "pendencias_resolvidas_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "comissionamento_pendencias_LA_por_funcionario": [
            ComissionamentoPendenciaRow(**x) for x in get_pendencias_comissionamento_por_funcionario_LA(pendencias_LA)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:15047
def _build_rubrica_count_by_processo(rubrica_count_data: List[Dict]) -> Dict:
    """Retorna {ID_PROCESSO: N_RUBRICAS} a partir da query rubrica_count_por_processo.
    Processos sem entrada no mapa são normais (N=1 por padrão no lookup)."""
    return {row["ID_PROCESSO"]: row["N_RUBRICAS"] for row in rubrica_count_data if row.get("ID_PROCESSO") is not None}


# v1: dashboard_routes.py:15053
def _agrupar_expandido_por_atendente(
    rows: List[Dict],
    filter_fn,
    atendente_key: str,
    rubrica_counts: Dict,
) -> Dict[str, int]:
    """Agrega processos por atendente multiplicando pelo número de rubricas de cada processo."""
    filtered = filter_fn(rows)
    counts: Dict = defaultdict(int)
    for row in filtered:
        atendente = row.get(atendente_key) or "Sem atendente"
        atendente_fmt = _formatar_nome_atendente_NG(atendente)
        id_processo = row.get("ID_PROCESSO")
        n = rubrica_counts.get(id_processo, 1) if id_processo is not None else 1
        counts[atendente_fmt] += n
    return {name: int(v) for name, v in counts.items()}


# v1: dashboard_routes.py:15071
async def _build_dashboard_comercial_completo(
    dashboard_name: str,
    _f, _a,
    from_date: Optional[date],
    to_date: Optional[date],
    atendentes_comerciais_opcoes: Optional[List[str]],
    atendentes_comerciais_filtro: Optional[List[str]],
    ufs_comercial_ng_opcoes: Optional[List[str]],
    uf_comercial_ng_filtro: Optional[str],
    segmento_comercial_ng_filtro: Optional[str],
    segmento_comercial_la_filtro: Optional[str],
    area_atuacao_id_filtro: Optional[Union[int, List[int]]] = None,
    t0: float = 0.0,
) -> DashboardResponse:
    """Orquestra todos os builders para os dashboards 'comercial' e 'comercial_LA'."""
    all_stats: Dict = {}
    all_charts: Dict = {}

    if atendentes_comerciais_opcoes is not None:
        all_stats["atendentes_comerciais"] = atendentes_comerciais_opcoes
        ac_filtro = list(atendentes_comerciais_filtro or [])
        all_stats["atendentes_comerciais_filtro"] = ac_filtro or None
        all_stats["funcionarios_filtro"] = ac_filtro or None
        all_stats["atendente_comercial_filtro"] = ", ".join(ac_filtro) if ac_filtro else None
        all_stats["funcionario_filtro"] = ", ".join(ac_filtro) if ac_filtro else None
    if ufs_comercial_ng_opcoes is not None:
        all_stats["ufs_comercial_ng_opcoes"] = ufs_comercial_ng_opcoes
        all_stats["uf_comercial_ng_filtro"] = uf_comercial_ng_filtro
    all_stats["segmentos_comercial_ng_opcoes"] = list_segmentos_comercial_ng()
    all_stats["segmentos_comercial_la_opcoes"] = list_segmentos_comercial_la()
    all_stats["segmento_comercial_ng_filtro"] = segmento_comercial_ng_filtro
    all_stats["segmento_comercial_la_filtro"] = segmento_comercial_la_filtro
    all_stats["area_atuacao_id_filtro"] = area_atuacao_id_filtro

    # Comercial NG
    s, c = _build_comercial_stats(_f("comercial_geral"), _a("comercial_geral"), _f("actions"), _a("actions"), _f("protocolos"), _a("protocolos"), _f("peticionamento"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Protocolo NG
    s, c = _build_protocolo_stats(_f("protocolos"), _a("protocolos"), from_date, to_date, comercial_geral=_f("comercial_geral"))
    all_stats.update(s); all_charts.update(c)

    # Peticionamento NG
    s, c = _build_peticionamento_stats(_f("peticionamento"), _a("peticionamento"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Org Doc NG
    s, c = _build_org_doc_stats(_f("org_doc"), _a("org_doc"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Pendências NG
    s, c = _build_pendencias_stats(_f("pendencias"), _a("pendencias"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Fila expandida — cada rubrica reunida conta como N rubricas (apenas para o gráfico de fila)
    _rc = _build_rubrica_count_by_processo(_a("rubrica_count_por_processo"))
    # Protocolados também por rubrica, para o segmento "Protocolado" da fila usar a mesma unidade dos demais.
    # Mesma base de `protocolos_resolvidos_por_atendente` (período filtrado), só expandida.
    all_charts["protocolos_resolvidos_por_atendente_expandido"] = [
        ChartDataPoint(**x) for x in dict_to_chart_data(
            _agrupar_expandido_por_atendente(_f("protocolos"), _filtrar_protocolos_resolvidos, "ATENDENTE", _rc),
            cast_int=True,
        )
    ]
    all_charts["nao_protocolados_por_atendente_expandido"] = [
        ChartDataPoint(**x) for x in dict_to_chart_data(
            _agrupar_expandido_por_atendente(_a("protocolos"), _filtrar_protocolos_nao_protocolados, "ATENDENTE", _rc),
            cast_int=True,
        )
    ]
    all_charts["nao_peticionados_por_atendente_expandido"] = [
        ChartDataPoint(**x) for x in dict_to_chart_data(
            _agrupar_expandido_por_atendente(_a("peticionamento"), _filtrar_nao_peticionados, "ATENDENTE_COMERCIAL", _rc),
            cast_int=True,
        )
    ]
    all_charts["nao_organizados_por_atendente_expandido"] = [
        ChartDataPoint(**x) for x in dict_to_chart_data(
            _agrupar_expandido_por_atendente(_a("org_doc"), _filtrar_nao_organizados, "ATENDENTE_COMERCIAL", _rc),
            cast_int=True,
        )
    ]
    all_charts["pendencias_nao_resolvidas_por_atendente_expandido"] = [
        ChartDataPoint(**x) for x in dict_to_chart_data(
            _agrupar_expandido_por_atendente(_a("pendencias"), _filtrar_pendencias_nao_resolvidas, "ATENDENTE", _rc),
            cast_int=True,
        )
    ]

    # Protocolo LA
    s, c = _build_protocolo_LA_stats(_f("protocolo_LA"), _a("protocolo_LA"), from_date, to_date, comercial_LA=_f("comercial_LA"))
    all_stats.update(s); all_charts.update(c)

    # Peticionamento LA
    s, c = _build_peticionamento_LA_stats(_f("peticionamento_LA"), _a("peticionamento_LA"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Org Doc LA — CORRIGIDO: estava ausente no builder comercial
    s, c = _build_org_doc_LA_stats(_f("org_doc_LA"), _a("org_doc_LA"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Andamento Processual LA
    s, c = _build_andamento_LA_stats(_f("andamento_processual_LA"), _a("andamento_processual_LA"))
    all_stats.update(s); all_charts.update(c)

    # Pendencias LA
    s, c = _build_pendencias_LA_stats(_f("pendencia_LA"), _a("pendencia_LA"), from_date, to_date)
    all_stats.update(s); all_charts.update(c)

    # Comercial LA
    ctx_la = ComercialLAContext(
        comercial=_f("comercial_LA"), all_comercial=_a("comercial_LA"),
        actions=_f("actions_LA"),
        protocolo=_f("protocolo_LA"), all_protocolo=_a("protocolo_LA"),
        peticionamento=_f("peticionamento_LA"), all_peticionamento=_a("peticionamento_LA"),
        org_doc=_f("org_doc_LA"), all_org_doc=_a("org_doc_LA"),
        pendencias=_f("pendencias_LA"), all_pendencias=_a("pendencias_LA"),
        from_date=from_date, to_date=to_date,
    )
    s, c = _build_comercial_LA_stats(ctx_la)
    all_stats.update(s); all_charts.update(c)

    if dashboard_name == "comercial_LA":
        all_charts["rubricas_total"] = [RubricaTotalRow(**x) for x in get_rubricas_total_tabela_LA(_f("comercial_LA"))]

    logger.info("Dashboard '%s' processado em %.2fs", dashboard_name, time.time() - t0)
    return DashboardResponse(dashboard=dashboard_name, stats=DashboardStats(**all_stats), **all_charts)


# V2: só os dashboards desta cópia (v1: FETCHES_BY_DASHBOARD, mesmas fontes e chaves).
# V2: comercial sem as fontes de outro banco: comercial_LA (comercial_geral_LA, banco laadv), protocolo_LA (setor_protocolo_LA, banco laadv), peticionamento_LA (setor_confeccao_LA, banco laadv), org_doc_LA (setor_org_documentos_LA, banco laadv), pendencias_LA (setor_pendencia_LA, banco laadv), actions_LA (actions_LA, banco laadv), execucao_LA (execucao_LA, banco lexflow), andamento_processual_LA (andamento_processual_LA, banco laadv).
FETCHES_BY_DASHBOARD: Dict[str, List[Tuple[str, Any]]] = {
    "protocolo": [("protocolos", fetch_protocolos), ("comercial_geral", fetch_comercial_geral)],
    "protocolo_RJ": [("protocolos", fetch_protocolos), ("comercial_geral", fetch_comercial_geral)],
    "peticionamento": [("peticionamento", fetch_peticionamento)],
    "peticionamento_RJ": [("peticionamento", fetch_peticionamento)],
    "org-documentos": [("org_doc", fetch_org_doc)],
    "org_doc_RJ": [("org_doc", fetch_org_doc)],
    "pendencias": [("pendencias", fetch_pendencias)],
    "pendencias_RJ": [("pendencias", fetch_pendencias)],
    "comercial": [("comercial_geral", fetch_comercial_geral), ("actions", fetch_actions), ("protocolos", fetch_protocolos), ("peticionamento", fetch_peticionamento), ("org_doc", fetch_org_doc), ("pendencias", fetch_pendencias), ("rubrica_count_por_processo", fetch_rubrica_count_por_processo)],
    "comercial_RJ": [("comercial_geral", fetch_comercial_geral), ("actions", fetch_actions), ("protocolos", fetch_protocolos), ("peticionamento", fetch_peticionamento), ("org_doc", fetch_org_doc), ("pendencias", fetch_pendencias), ("rubrica_count_por_processo", fetch_rubrica_count_por_processo)],
    "marketing_NG": [("marketing_NG", fetch_marketing_NG), ("facebook_ads", fetch_facebook_ads), ("actions", fetch_actions), ("protocolos", fetch_protocolos), ("comercial_geral", fetch_comercial_geral), ("analise_thiago", fetch_analise_thiago), ("trackeamento_ng_2", fetch_trackeamento_ng_2)],
    "nps_NG": [("nps_NG", fetch_nps_NG)],
    "tickets": [("tickets", fetch_tickets)],
}
DASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)


# v1: dashboard_routes.py:11255 — V2: início igual, só os ramos de protocolo, protocolo_RJ, peticionamento, peticionamento_RJ, org-documentos, org_doc_RJ, pendencias, pendencias_RJ, comercial, comercial_RJ, marketing_NG, nps_NG, tickets
async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards
    dashboard_name: str,
    from_date: Optional[date],
    to_date: Optional[date],
    selection_dim: Optional[List[str]] = None,
    selection_value: Optional[List[str]] = None,
    funcionario: Optional[List[str]] = None,
    atendente_comercial: Optional[List[str]] = None,
    segmento_comercial_ng: Optional[str] = None,
    uf_comercial_ng: Optional[str] = None,
    segmento_comercial_la: Optional[str] = None,
    materia: Optional[Union[str, List[str]]] = None,
    sistema: Optional[str] = None,
    uf_protocolo: Optional[List[str]] = None,
    uf_peticionamento: Optional[str] = None,
    uf_org_doc: Optional[str] = None,
    uf_pendencias: Optional[str] = None,
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> DashboardResponse:
    if dashboard_name not in DASHBOARD_NAMES:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' não encontrado.")
    t0 = time.time()
    logger.info("Dashboard '%s' (from=%s, to=%s)", dashboard_name, from_date, to_date)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    fetches_config = FETCHES_BY_DASHBOARD[dashboard_name]
    # V2: mesma busca da v1 (_gather_dashboard_fetches = gather com return_exceptions)
    results = await asyncio.gather(*[fn() for _, fn in fetches_config], return_exceptions=True)
    # V2: banco de origem fora do ar = 503 na casca (a v1 seguia com a fonte vazia quando havia mais de uma)
    for res in results:
        if isinstance(res, SourceUnavailable):
            raise res
    all_data: Dict[str, List] = {}
    source_errors: List[Tuple[str, Exception]] = []
    for (key, _), res in zip(fetches_config, results):
        if isinstance(res, Exception):
            source_errors.append((key, res))
            all_data[key] = []
        else:
            all_data[key] = res
    if source_errors:
        if len(fetches_config) == 1:
            failed_key, failed_exc = source_errors[0]
            logger.exception("Falha ao buscar fonte '%s' no dashboard '%s'", failed_key, dashboard_name, exc_info=failed_exc)
            if isinstance(failed_exc, HTTPException):
                raise failed_exc
            raise HTTPException(status_code=500, detail=f"Falha ao buscar dados de '{failed_key}'")
        for failed_key, failed_exc in source_errors:
            logger.warning("Fonte '%s' indisponível no dashboard '%s': %s", failed_key, dashboard_name, failed_exc)
    _rj_atendentes_exclusion: frozenset = frozenset()
    if dashboard_name == "comercial":
        _raw_cg = all_data.get("comercial_geral", [])
        # Mapa: nome_raw -> tem_alguma_action_ng (UF não-vazia e não-RJ)
        _emp_has_ng: Dict[str, bool] = {}
        for _r in _raw_cg:
            _att = str(_r.get("ATENDENTE") or "").strip()
            if not _att:
                continue
            _uf = str(_r.get("UF") or "").strip().upper()
            if _uf and _uf != "RJ":
                _emp_has_ng[_att] = True
            elif _att not in _emp_has_ng:
                _emp_has_ng[_att] = False
        # Somente funcionários sem nenhuma action NG (exclusivamente RJ ou sem UF)
        _rj_only_names = {emp for emp, has_ng in _emp_has_ng.items() if not has_ng}
        _rj_only_rows = [r for r in _raw_cg if str(r.get("ATENDENTE") or "").strip() in _rj_only_names]
        _rj_atendentes_exclusion = frozenset(list_atendentes_comerciais(_rj_only_rows))
        all_data = _filtrar_dados_ng_por_uf(all_data, "RJ", excluir=True)
    elif dashboard_name in ("comercial_RJ", "protocolo_RJ", "peticionamento_RJ", "org_doc_RJ", "pendencias_RJ", "andamento_processual_RJ"):
        all_data = _filtrar_dados_ng_por_uf(all_data, "RJ", excluir=False)
    elif dashboard_name in ("protocolo", "peticionamento", "org-documentos", "pendencias", "andamento-processual"):
        all_data = _filtrar_dados_ng_por_uf(all_data, "RJ", excluir=True)
    filtered_data: Dict[str, List] = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in all_data.items()
    }
    atendentes_comerciais_opcoes: Optional[List[str]] = None
    ufs_comercial_ng_opcoes: Optional[List[str]] = None
    ac_list: List[str] = []
    if dashboard_name in ("comercial", "comercial_LA", "comercial_RJ"):
        source_key = "comercial_geral" if dashboard_name in ("comercial", "comercial_RJ") else "comercial_LA"
        if dashboard_name in ("comercial", "comercial_RJ"):
            ufs_comercial_ng_opcoes = list_ufs_comercial_ng(filtered_data.get("comercial_geral", []))
            ng_ops_all = list_atendentes_comerciais(filtered_data.get("comercial_geral", []))
            # Para o dashboard NG, excluir funcionários que operam no escritório RJ
            ng_ops = [emp for emp in ng_ops_all if emp not in _rj_atendentes_exclusion]
            atendentes_comerciais_opcoes = sorted(
                set(ng_ops),
                key=lambda x: x.casefold(),
            )
        else:
            atendentes_comerciais_opcoes = list_atendentes_comerciais_LA(
                filtered_data.get(source_key, [])
            )
        filtered_data, all_data, ac_list = _aplicar_filtros_comercial_dashboard(
            filtered_data,
            all_data,
            dashboard_name=dashboard_name,
            atendente_comercial=atendente_comercial,
            funcionario=funcionario,
        )
    uf_ng_aplicado: Optional[str] = None
    if dashboard_name == "comercial" and uf_comercial_ng and str(uf_comercial_ng).strip():
        uf_ng_aplicado = str(uf_comercial_ng).strip().upper()
        filtered_data["comercial_geral"] = filter_comercial_geral_por_uf(
            filtered_data.get("comercial_geral", []), uf_ng_aplicado
        )
        all_data["comercial_geral"] = filter_comercial_geral_por_uf(
            all_data.get("comercial_geral", []), uf_ng_aplicado
        )
    segmento_ng_aplicado: Optional[str] = None
    segmento_la_aplicado: Optional[str] = None
    if dashboard_name in ("comercial", "comercial_LA", "comercial_RJ"):
        if dashboard_name == "comercial_LA" and segmento_comercial_ng and str(segmento_comercial_ng).strip():
            raise HTTPException(status_code=400, detail="Use apenas segmento_comercial_la no dashboard comercial_LA.")
        if dashboard_name in ("comercial", "comercial_RJ") and segmento_comercial_ng and str(segmento_comercial_ng).strip():
            try:
                segmento_ng_aplicado = normalizar_segmento_comercial_ng(str(segmento_comercial_ng).strip())
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            filtered_data["comercial_geral"] = filter_comercial_geral_por_segmento(filtered_data.get("comercial_geral", []), segmento_ng_aplicado)
            all_data["comercial_geral"] = filter_comercial_geral_por_segmento(all_data.get("comercial_geral", []), segmento_ng_aplicado)
        if segmento_comercial_la and str(segmento_comercial_la).strip():
            try:
                segmento_la_aplicado = normalizar_segmento_comercial_la(str(segmento_comercial_la).strip())
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            filtered_data["comercial_LA"] = filter_comercial_LA_por_segmento(filtered_data.get("comercial_LA", []), segmento_la_aplicado)
            all_data["comercial_LA"] = filter_comercial_LA_por_segmento(all_data.get("comercial_LA", []), segmento_la_aplicado)
    area_atuacao_id_aplicado: Optional[Union[int, List[int]]] = None
    if dashboard_name in ("comercial", "comercial_LA", "comercial_RJ") and area_atuacao_id is not None:
        area_atuacao_id_aplicado = area_atuacao_id
        if dashboard_name in ("comercial", "comercial_RJ"):
            filtered_data["comercial_geral"] = filter_comercial_geral_por_area_atuacao(filtered_data.get("comercial_geral", []), area_atuacao_id)
            all_data["comercial_geral"] = filter_comercial_geral_por_area_atuacao(all_data.get("comercial_geral", []), area_atuacao_id)
        else:
            filtered_data["comercial_LA"] = filter_comercial_geral_por_area_atuacao(filtered_data.get("comercial_LA", []), area_atuacao_id)
            all_data["comercial_LA"] = filter_comercial_geral_por_area_atuacao(all_data.get("comercial_LA", []), area_atuacao_id)
    _PREPROTOCOLO_AREA_KEY = {
        "pendencia_LA":      "pendencia_LA",
        "org_doc_LA":        "org_doc_LA",
        "peticionamento_LA": "peticionamento_LA",
        "protocolo_LA":      "protocolo_LA",
        "pendencias":        "pendencias",
        "pendencias_RJ":     "pendencias",
        "org-documentos":    "org_doc",
        "org_doc_RJ":        "org_doc",
        "peticionamento":    "peticionamento",
        "peticionamento_RJ": "peticionamento",
        "protocolo":         "protocolos",
        "protocolo_RJ":      "protocolos",
    }
    if dashboard_name in _PREPROTOCOLO_AREA_KEY and area_atuacao_id is not None:
        _key = _PREPROTOCOLO_AREA_KEY[dashboard_name]
        area_atuacao_id_aplicado = area_atuacao_id
        filtered_data[_key] = filter_comercial_geral_por_area_atuacao(filtered_data.get(_key, []), area_atuacao_id)
        all_data[_key] = filter_comercial_geral_por_area_atuacao(all_data.get(_key, []), area_atuacao_id)
    def _f(key: str) -> List:
        return filtered_data.get(key, [])
    def _a(key: str) -> List:
        return all_data.get(key, [])
    if dashboard_name == "tickets":
        ticket_selection_pairs = list(zip(selection_dim or [], selection_value or []))
        tickets = _f("tickets")
        all_tickets = _a("tickets")
        for _dim, _value in ticket_selection_pairs:
            tickets = apply_ticket_selection_filter(tickets, selection_dim=_dim, selection_value=_value)
            all_tickets = apply_ticket_selection_filter(all_tickets, selection_dim=_dim, selection_value=_value)
        stats, charts = _build_tickets_stats(tickets, all_tickets, from_date, to_date)
        logger.info("Dashboard 'tickets' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="tickets", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name in ("protocolo", "protocolo_RJ"):
        funcs_proto = _normalizar_funcionarios_query(funcionario)
        ufs_protocolo_opcoes = list_ufs_protocolo(_f("protocolos"))
        uf_protocolo_filtro = [str(u).strip().upper() for u in uf_protocolo if str(u).strip()] if uf_protocolo else None
        proto = filter_protocolo_por_uf(
            filter_protocolo_por_sistema(
                filter_protocolo_por_funcionarios(
                    filter_protocolo_por_materia(_f("protocolos"), materia),
                    funcs_proto,
                ),
                sistema,
            ),
            uf_protocolo_filtro,
        )
        all_proto = filter_protocolo_por_uf(
            filter_protocolo_por_sistema(
                filter_protocolo_por_funcionarios(
                    filter_protocolo_por_materia(_a("protocolos"), materia),
                    funcs_proto,
                ),
                sistema,
            ),
            uf_protocolo_filtro,
        )
        comercial_protocolo = filter_comercial_geral_por_uf(_f("comercial_geral"), uf_protocolo_filtro)
        stats, charts = _build_protocolo_stats(proto, all_proto, from_date, to_date, comercial_geral=comercial_protocolo)
        stats["ufs_protocolo_opcoes"] = ufs_protocolo_opcoes
        stats["uf_protocolo_filtro"] = uf_protocolo_filtro
        stats["funcionarios_filtro"] = funcs_proto or None
        stats["funcionario_filtro"] = ", ".join(funcs_proto) if funcs_proto else None
        logger.info("Dashboard '%s' processado em %.2fs", dashboard_name, time.time() - t0)
        return DashboardResponse(dashboard=dashboard_name, stats=DashboardStats(**stats), **charts)
    if dashboard_name in ("peticionamento", "peticionamento_RJ"):
        funcs_pet = _normalizar_funcionarios_query(funcionario)
        ufs_peticionamento_opcoes = list_ufs_peticionamento(_f("peticionamento"))
        uf_peticionamento_filtro = (
            str(uf_peticionamento).strip().upper()
            if uf_peticionamento and str(uf_peticionamento).strip()
            else None
        )
        pet = filter_peticionamento_por_uf(
            filter_peticionamento_por_funcionarios(
                filter_peticionamento_por_materia(_f("peticionamento"), materia),
                funcs_pet,
            ),
            uf_peticionamento_filtro,
        )
        all_pet = filter_peticionamento_por_uf(
            filter_peticionamento_por_funcionarios(
                filter_peticionamento_por_materia(_a("peticionamento"), materia),
                funcs_pet,
            ),
            uf_peticionamento_filtro,
        )
        # Sem filtro de matéria: usado só para a taxa de resolvidos do comissionamento,
        # que deve refletir a taxa GERAL do funcionário, não a taxa recortada pela matéria filtrada.
        pet_taxa = filter_peticionamento_por_uf(
            filter_peticionamento_por_funcionarios(_f("peticionamento"), funcs_pet),
            uf_peticionamento_filtro,
        )
        all_pet_taxa = filter_peticionamento_por_uf(
            filter_peticionamento_por_funcionarios(_a("peticionamento"), funcs_pet),
            uf_peticionamento_filtro,
        )
        stats, charts = _build_peticionamento_stats(pet, all_pet, from_date, to_date, pet_taxa, all_pet_taxa)
        stats["ufs_peticionamento_opcoes"] = ufs_peticionamento_opcoes
        stats["uf_peticionamento_filtro"] = uf_peticionamento_filtro
        stats["funcionarios_filtro"] = funcs_pet or None
        stats["funcionario_filtro"] = ", ".join(funcs_pet) if funcs_pet else None
        logger.info("Dashboard '%s' processado em %.2fs", dashboard_name, time.time() - t0)
        return DashboardResponse(dashboard=dashboard_name, stats=DashboardStats(**stats), **charts)
    if dashboard_name in ("org-documentos", "org_doc_RJ"):
        funcs_od = _normalizar_funcionarios_query(funcionario)
        ufs_org_doc_opcoes = list_ufs_org_doc(_f("org_doc"))
        uf_org_doc_filtro = (
            str(uf_org_doc).strip().upper() if uf_org_doc and str(uf_org_doc).strip() else None
        )
        od = filter_org_doc_por_uf(
            filter_org_doc_por_funcionarios(
                filter_org_doc_por_materia(_f("org_doc"), materia),
                funcs_od,
            ),
            uf_org_doc_filtro,
        )
        all_od = filter_org_doc_por_uf(
            filter_org_doc_por_funcionarios(
                filter_org_doc_por_materia(_a("org_doc"), materia),
                funcs_od,
            ),
            uf_org_doc_filtro,
        )
        stats, charts = _build_org_doc_stats(od, all_od, from_date, to_date)
        stats["ufs_org_doc_opcoes"] = ufs_org_doc_opcoes
        stats["uf_org_doc_filtro"] = uf_org_doc_filtro
        stats["funcionarios_filtro"] = funcs_od or None
        stats["funcionario_filtro"] = ", ".join(funcs_od) if funcs_od else None
        logger.info("Dashboard '%s' processado em %.2fs", dashboard_name, time.time() - t0)
        return DashboardResponse(dashboard=dashboard_name, stats=DashboardStats(**stats), **charts)
    if dashboard_name in ("pendencias", "pendencias_RJ"):
        funcs_pend = _normalizar_funcionarios_query(funcionario)
        ufs_pendencias_opcoes = list_ufs_pendencia(_f("pendencias"))
        uf_pendencias_filtro = (
            str(uf_pendencias).strip().upper()
            if uf_pendencias and str(uf_pendencias).strip()
            else None
        )
        pend = filter_pendencia_por_uf(
            filter_pendencia_por_funcionarios(_f("pendencias"), funcs_pend),
            uf_pendencias_filtro,
        )
        all_pend = filter_pendencia_por_uf(
            filter_pendencia_por_funcionarios(_a("pendencias"), funcs_pend),
            uf_pendencias_filtro,
        )
        stats, charts = _build_pendencias_stats(pend, all_pend, from_date, to_date)
        stats["ufs_pendencias_opcoes"] = ufs_pendencias_opcoes
        stats["uf_pendencias_filtro"] = uf_pendencias_filtro
        stats["funcionarios_filtro"] = funcs_pend or None
        stats["funcionario_filtro"] = ", ".join(funcs_pend) if funcs_pend else None
        logger.info("Dashboard '%s' processado em %.2fs", dashboard_name, time.time() - t0)
        return DashboardResponse(dashboard=dashboard_name, stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "nps_NG":
        respostas = _f("nps_NG")
        stats = get_nps_stats(respostas)
        charts = {
            "nps_por_classificacao": [
                ChartDataPoint(**x) for x in group_nps_por_classificacao(respostas)
            ],
            "nps_por_nota": [
                ChartDataPoint(**x) for x in group_nps_por_nota(respostas)
            ],
            "nps_por_mes": [
                ChartDataPoint(**x) for x in group_nps_por_mes(respostas)
            ],
            "nps_respostas_tabela": [
                NpsRespostaRow(**x) for x in get_respostas_tabela(respostas)
            ],
            "nps_feedbacks_melhoria": [
                NpsFeedbackMelhoriaRow(**x) for x in get_feedbacks_melhoria(respostas)
            ],
            "nps_feedbacks_positivos": [
                NpsFeedbackPositivoRow(**x) for x in get_feedbacks_positivos(respostas)
            ],
            "nps_comentarios": [
                NpsComentarioRow(**x) for x in get_comentarios(respostas)
            ],
        }
        logger.info("Dashboard 'nps_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="nps_NG", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "marketing_NG":
        # Filtros interativos (drill-down por clique nos gráficos, aplicados na
        # página toda). Múltiplos valores na mesma dimensão = OR; dimensões
        # diferentes = AND. Injetados 1x por linha-base — os subconjuntos
        # derivados (triados, analise_thiago_*, trackeamento_*) herdam automaticamente.
        marketing_selection_pairs = list(zip(selection_dim or [], selection_value or []))
        clientes = apply_selection_filters(_f("marketing_NG"), marketing_selection_pairs, _FIELD_MAP_CLIENTES)
        triados = filtrar_triados(clientes)
        # facebook_ads assume coluna de data "date" (convenção do banco ng,
        # ex. public.trackeamento) — ainda não confirmada no schema real de
        # metrics_ads.facebook_ads.
        facebook_ads_rows = _f("facebook_ads")
        if facebook_ads_rows:
            _amostra = facebook_ads_rows[0]
            logger.info(
                "[debug facebook_ads] total_linhas=%d chaves=%s date_valor=%r date_tipo=%s",
                len(facebook_ads_rows),
                list(_amostra.keys()),
                _amostra.get("date"),
                type(_amostra.get("date")),
            )
        else:
            logger.info("[debug facebook_ads] facebook_ads_rows veio vazio")
        # Funil de pipeline (actions_NG_2): filtra explicitamente só por ENTRADA
        # (não por ASSINADO_EM, ao contrário do filtro padrão da chave "actions"
        # usado por outros dashboards) para refletir a coorte que entrou no período.
        pipeline_rows = _filter_by_columns(_a("actions"), ["ENTRADA"], from_date, to_date)
        # CAC/ROAS usam o mesmo filtro de data da página (ENTRADA em actions,
        # SAIDA em protocolos via _f padrão) para bater com o restante da seção.
        actions_all_rows = pipeline_rows
        protocolos_all_rows = _f("protocolos")
        stats = get_marketing_ng_stats(clientes)
        stats["marketing_ng_triados_total_clientes"] = get_total_clientes(triados)
        stats["marketing_ng_triados_media_idade"] = get_media_idade(triados)
        stats.update(get_facebook_ads_stats(facebook_ads_rows))
        stats.update(get_marketing_ng_cac_roas_stats(facebook_ads_rows, actions_all_rows, protocolos_all_rows))
        comercial_geral_rows = _f("comercial_geral")
        stats["marketing_ng_clientes_campanha"] = get_total_clientes_fechados_campanha(comercial_geral_rows)
        stats["marketing_ng_leads"] = get_total_leads(pipeline_rows)
        stats["marketing_ng_indicacao_ativa"] = get_total_leads_indicacao_ativa_por_atendente(pipeline_rows)["total"]
        stats["marketing_ng_indicacao_passiva"] = get_total_leads_indicacao_passiva_por_atendente(pipeline_rows)["total"]
        stats["marketing_ng_retorno_ativa"] = get_total_leads_retorno_ativa_por_atendente(pipeline_rows)["total"]
        stats["marketing_ng_retorno_passiva"] = get_total_leads_retorno_passiva_por_atendente(pipeline_rows)["total"]
        # Fechamento Campanhas (Analise_thiago): Campanha (clientes fechados) filtra
        # por ASSINATURA no período; total de leads (denominador da conversão)
        # filtra por ENTRADA no período — duas coortes diferentes, confirmado
        # contra o Power BI (Campanha NG = 41 só bate com ASSINATURA).
        # Protocolados/Valor de Causa filtram por SAIDA_PROTOCO no período da página.
        analise_thiago_rows = apply_selection_filters(
            _a("analise_thiago"), marketing_selection_pairs, _FIELD_MAP_ANALISE_THIAGO
        )
        analise_thiago_assinatura = _filter_by_columns(analise_thiago_rows, ["ASSINATURA"], from_date, to_date)
        analise_thiago_entrada = _filter_by_columns(analise_thiago_rows, ["ENTRADA"], from_date, to_date)
        campanha_ra = get_qtd_clientes_campanha_ra(analise_thiago_assinatura)
        campanha_ng = get_qtd_clientes_campanha_ng(analise_thiago_assinatura)
        leads_ra_entrada = get_total_leads_campanha_ra(analise_thiago_entrada)
        leads_ng_entrada = get_total_leads_campanha_ng(analise_thiago_entrada)
        stats["marketing_ng_campanha_ra"] = campanha_ra
        stats["marketing_ng_campanha_ng"] = campanha_ng
        stats["marketing_ng_conversao_ra"] = round(campanha_ra / leads_ra_entrada * 100, 2) if leads_ra_entrada else 0.0
        stats["marketing_ng_conversao_ng"] = round(campanha_ng / leads_ng_entrada * 100, 2) if leads_ng_entrada else 0.0
        stats["marketing_ng_protocolados_ra"] = get_protocolo_resolvido_saida_ra(analise_thiago_rows, from_date, to_date)
        stats["marketing_ng_protocolados_ng"] = get_protocolo_resolvido_saida_ng(analise_thiago_rows, from_date, to_date)
        stats["marketing_ng_valor_causa_ra"] = get_valor_causa_protocolo_ra(analise_thiago_rows, from_date, to_date)
        stats["marketing_ng_valor_causa_ng"] = get_valor_causa_protocolo_ng(analise_thiago_rows, from_date, to_date)
        acoes_ra = get_acoes_ra(analise_thiago_rows, from_date, to_date)
        acoes_ng = get_acoes_ng(analise_thiago_rows, from_date, to_date)
        stats["marketing_ng_ticket_medio_ra"] = get_ticket_medio_ra(stats["marketing_ng_valor_causa_ra"], acoes_ra)
        stats["marketing_ng_ticket_medio_ng"] = get_ticket_medio_ng(stats["marketing_ng_valor_causa_ng"], acoes_ng)
        # Análise de Aquisição (trackeamento_NG_2): a DAX TOTAL_FECHADOS não usa
        # USERELATIONSHIP, então o filtro de data aplicado pelo relatório usa a
        # relação ATIVA/principal (DATA_TRACKEAMENTO) — a relação por ASSINADO_EM
        # existe no modelo mas fica inativa para essa medida.
        trackeamento_rows = apply_selection_filters(
            _a("trackeamento_ng_2"), marketing_selection_pairs, _FIELD_MAP_TRACKEAMENTO
        )
        trackeamento_por_data = _filter_by_columns(trackeamento_rows, ["DATA_TRACKEAMENTO"], from_date, to_date)
        fechados_trackeamento = filtrar_fechados_trackeamento(trackeamento_por_data)
        stats["marketing_ng_total_trackeamento"] = get_total_trackeamento(trackeamento_por_data)
        stats["marketing_ng_processos_assinados"] = len(fechados_trackeamento)
        # Ind. Performance de MKT - NG: métricas e gráficos já calculados acima,
        # reaproveitados e recortados para o canal ANUNCIO_NG.
        stats["marketing_ng_leads_ng"] = leads_ng_entrada
        stats["marketing_ng_acoes_ng"] = acoes_ng
        stats["marketing_ng_aproveitamento_ng"] = round(acoes_ng / campanha_ng, 2) if campanha_ng else 0.0
        stats["marketing_ng_cpl_ng"] = (
            round(stats["marketing_ng_facebook_valor_gasto"] / leads_ng_entrada, 2) if leads_ng_entrada else 0.0
        )
        trackeamento_ng_only = filtrar_canal_aquisicao(trackeamento_por_data, "ANUNCIO_NG")
        rubricas_ng = [
            {"name": x["name"], "value": x["ng"]}
            for x in group_rubrica_campanha(analise_thiago_assinatura)
            if x["ng"] > 0
        ]
        # Ind. Orgânico de MKT - NG (Analise_thiago, canais SITE/GOOGLE/INSTAGRAM/FACEBOOK):
        # mesmas condições de leads/ações/contratos já usadas nas seções anteriores,
        # generalizadas para os 4 canais orgânicos.
        org_leads_facebook = get_leads_por_canal(analise_thiago_entrada, "FACEBOOK")
        org_leads_instagram = get_leads_por_canal(analise_thiago_entrada, "INSTAGRAM")
        org_leads_site = get_leads_por_canal(analise_thiago_entrada, "SITE")
        org_leads_google = get_leads_por_canal(analise_thiago_entrada, "GOOGLE")
        org_total_leads = get_total_leads_organico(analise_thiago_entrada)
        org_contratos = get_qtd_clientes_organico(analise_thiago_assinatura)
        org_acoes = get_acoes_organico(analise_thiago_rows, from_date, to_date)
        org_valor_causa = get_valor_causa_protocolo_organico(analise_thiago_rows, from_date, to_date)
        stats["marketing_ng_org_leads_facebook"] = org_leads_facebook
        stats["marketing_ng_org_leads_instagram"] = org_leads_instagram
        stats["marketing_ng_org_leads_site"] = org_leads_site
        stats["marketing_ng_org_leads_google"] = org_leads_google
        stats["marketing_ng_org_total_leads"] = org_total_leads
        stats["marketing_ng_org_contratos"] = org_contratos
        stats["marketing_ng_org_acoes"] = org_acoes
        stats["marketing_ng_org_aproveitamento"] = round(org_acoes / org_contratos, 2) if org_contratos else 0.0
        stats["marketing_ng_org_taxa_fechamento"] = (
            round(org_contratos / org_total_leads * 100, 2) if org_total_leads else 0.0
        )
        stats["marketing_ng_org_valor_causa"] = org_valor_causa
        stats["marketing_ng_org_ticket_medio"] = get_ticket_medio_ng(org_valor_causa, org_acoes)
        organico_leads_rows = filtrar_canais_organico(analise_thiago_entrada)
        charts = {
            "marketing_ng_faixa_etaria": [
                ChartDataPoint(**x) for x in group_faixa_etaria(clientes)
            ],
            "marketing_ng_genero": [
                ChartDataPoint(**x) for x in group_genero(clientes)
            ],
            "marketing_ng_origem": [
                ChartDataPoint(**x) for x in group_origem(clientes)
            ],
            "marketing_ng_ocupacao": [
                ChartDataPoint(**x) for x in group_ocupacao(clientes)
            ],
            "marketing_ng_tipo_trafego": [
                ChartDataPoint(**x) for x in group_tipo_trafego(clientes)
            ],
            "marketing_ng_dispositivo": [
                ChartDataPoint(**x) for x in group_dispositivo(clientes)
            ],
            "marketing_ng_prospeccao": [
                ChartDataPoint(**x) for x in group_prospeccao(clientes)
            ],
            "marketing_ng_faixa_salarial": [
                ChartDataPoint(**x) for x in group_faixa_salarial(clientes)
            ],
            # Triados (RESP_TRIAGEM? = TRUE)
            "marketing_ng_triados_faixa_etaria": [
                ChartDataPoint(**x) for x in group_faixa_etaria(triados)
            ],
            "marketing_ng_triados_genero": [
                ChartDataPoint(**x) for x in group_genero(triados)
            ],
            "marketing_ng_triados_origem": [
                ChartDataPoint(**x) for x in group_origem(triados)
            ],
            "marketing_ng_triados_ocupacao": [
                ChartDataPoint(**x) for x in group_ocupacao(triados)
            ],
            "marketing_ng_triados_tipo_trafego": [
                ChartDataPoint(**x) for x in group_tipo_trafego(triados)
            ],
            "marketing_ng_triados_dispositivo": [
                ChartDataPoint(**x) for x in group_dispositivo(triados)
            ],
            "marketing_ng_triados_prospeccao": [
                ChartDataPoint(**x) for x in group_prospeccao(triados)
            ],
            "marketing_ng_triados_faixa_salarial": [
                ChartDataPoint(**x) for x in group_faixa_salarial(triados)
            ],
            "marketing_ng_triados_tipo_residencia": [
                ChartDataPoint(**x) for x in group_tipo_residencia(triados)
            ],
            "marketing_ng_triados_pessoas_dependentes": [
                ChartDataPoint(**x) for x in group_pessoas_dependentes(triados)
            ],
            "marketing_ng_funil_pipeline": [
                ChartDataPoint(**x) for x in group_funil_pipeline(pipeline_rows)
            ],
            "marketing_ng_investimento_cliques_leads": [
                InvestimentoCliquesLeadsPoint(**x) for x in group_investimento_cliques_leads(facebook_ads_rows)
            ],
            "marketing_ng_rubrica_campanha": [
                RubricaCampanhaPoint(**x) for x in group_rubrica_campanha(analise_thiago_assinatura)
            ],
            "marketing_ng_rubrica_protocolado": [
                RubricaCampanhaPoint(**x) for x in group_rubrica_protocolado(analise_thiago_rows, from_date, to_date)
            ],
            "marketing_ng_total_clientes_campanha": [
                ChartDataPoint(**x) for x in group_total_clientes_campanha(analise_thiago_assinatura)
            ],
            "marketing_ng_protocolo_resolvido_total": [
                ChartDataPoint(**x) for x in group_protocolo_resolvido_total(analise_thiago_rows, from_date, to_date)
            ],
            "marketing_ng_valor_causa_total": [
                ChartDataPoint(**x) for x in group_valor_causa_total(analise_thiago_rows, from_date, to_date)
            ],
            "marketing_ng_trackeamento_categoria": [
                ChartDataPoint(**x) for x in group_categoria_criativo(trackeamento_por_data)
            ],
            "marketing_ng_trackeamento_posicionamento": [
                ChartDataPoint(**x) for x in group_posicionamento_padronizado(trackeamento_por_data)
            ],
            "marketing_ng_trackeamento_canal_aquisicao": [
                ChartDataPoint(**x) for x in group_canal_aquisicao_trackeamento(trackeamento_por_data)
            ],
            "marketing_ng_trackeamento_campanha": [
                ChartDataPoint(**x) for x in group_campanha_trackeamento(trackeamento_por_data)
            ],
            "marketing_ng_fechamento_categoria": [
                ChartDataPoint(**x) for x in group_categoria_criativo(fechados_trackeamento)
            ],
            "marketing_ng_fechamento_posicionamento": [
                ChartDataPoint(**x) for x in group_posicionamento_padronizado(fechados_trackeamento)
            ],
            "marketing_ng_fechamento_canal_aquisicao": [
                ChartDataPoint(**x) for x in group_canal_aquisicao_trackeamento(fechados_trackeamento)
            ],
            "marketing_ng_fechamento_campanha": [
                ChartDataPoint(**x) for x in group_campanha_trackeamento(fechados_trackeamento)
            ],
            "marketing_ng_ind_campanha": [
                ChartDataPoint(**x) for x in group_campanha_trackeamento(trackeamento_ng_only)
            ],
            "marketing_ng_ind_posicionamento": [
                ChartDataPoint(**x) for x in group_posicionamento_padronizado(trackeamento_ng_only)
            ],
            "marketing_ng_ind_conjunto": [
                ChartDataPoint(**x) for x in group_conjunto_trackeamento(trackeamento_ng_only)
            ],
            "marketing_ng_ind_criativo": [
                ChartDataPoint(**x) for x in group_criativo_trackeamento(trackeamento_ng_only)
            ],
            "marketing_ng_ind_categoria": [
                ChartDataPoint(**x) for x in group_categoria_criativo(trackeamento_ng_only)
            ],
            "marketing_ng_ind_rubricas": [ChartDataPoint(**x) for x in rubricas_ng],
            "marketing_ng_org_campanha": [
                ChartDataPoint(**x) for x in group_campanha_organico(organico_leads_rows)
            ],
            "marketing_ng_org_posicionamento": [
                ChartDataPoint(**x) for x in group_posicionamento_padronizado(organico_leads_rows)
            ],
            "marketing_ng_org_conjunto": [
                ChartDataPoint(**x) for x in group_conjunto_trackeamento(organico_leads_rows)
            ],
            "marketing_ng_org_criativo": [
                ChartDataPoint(**x) for x in group_criativo_trackeamento(organico_leads_rows)
            ],
            "marketing_ng_org_categoria": [
                ChartDataPoint(**x) for x in group_categoria_criativo(organico_leads_rows)
            ],
            "marketing_ng_org_rubricas_total": [
                ChartDataPoint(**x) for x in group_rubrica_organico(analise_thiago_rows, from_date, to_date)
            ],
            "marketing_ng_org_rubricas_facebook": [
                ChartDataPoint(**x)
                for x in group_rubrica_organico(analise_thiago_rows, from_date, to_date, "FACEBOOK")
            ],
            "marketing_ng_org_rubricas_instagram": [
                ChartDataPoint(**x)
                for x in group_rubrica_organico(analise_thiago_rows, from_date, to_date, "INSTAGRAM")
            ],
            "marketing_ng_org_rubricas_site": [
                ChartDataPoint(**x)
                for x in group_rubrica_organico(analise_thiago_rows, from_date, to_date, "SITE")
            ],
            "marketing_ng_org_rubricas_google": [
                ChartDataPoint(**x)
                for x in group_rubrica_organico(analise_thiago_rows, from_date, to_date, "GOOGLE")
            ],
        }
        logger.info("Dashboard 'marketing_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="marketing_NG", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name in ("comercial", "comercial_LA", "comercial_RJ"):
        return await _build_dashboard_comercial_completo(
            dashboard_name=dashboard_name,
            _f=_f, _a=_a,
            from_date=from_date, to_date=to_date,
            atendentes_comerciais_opcoes=atendentes_comerciais_opcoes,
            atendentes_comerciais_filtro=ac_list,
            ufs_comercial_ng_opcoes=ufs_comercial_ng_opcoes,
            uf_comercial_ng_filtro=uf_ng_aplicado,
            segmento_comercial_ng_filtro=segmento_ng_aplicado,
            segmento_comercial_la_filtro=segmento_la_aplicado,
            area_atuacao_id_filtro=area_atuacao_id_aplicado,
            t0=t0,
        )
    raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' não encontrado.")


# v1: dashboard_routes.py:19512 (rota sem os decoradores)
async def get_protocolo_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual `org_doc`: ex. Sem materia, código antes de ' - ').",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis (repita o parâmetro para vários; como nos gráficos de protocolo).",
    ),
    sistema: Optional[str] = Query(
        None,
        description="Filtra pelo sistema (rótulo igual ao `name` de protocolados_por_sistema, ex. Sem sistema).",
    ),
    uf_protocolo: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra protocolos por uma ou mais UFs (repita o parâmetro para várias, "
            "ex.: `?uf_protocolo=AM&uf_protocolo=PA`). Valores disponíveis em GET /protocolo/ufs."
        ),
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Protocolo."""
    return await _get_dashboard_response(
        "protocolo",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        sistema=sistema,
        uf_protocolo=uf_protocolo,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:19488 (rota sem os decoradores)
async def get_protocolo_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(None),
    funcionario: Optional[List[str]] = Query(None),
    sistema: Optional[str] = Query(None),
    uf_protocolo: Optional[List[str]] = Query(None),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Protocolo — escritório RJ."""
    return await _get_dashboard_response(
        "protocolo_RJ",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        sistema=sistema,
        uf_protocolo=uf_protocolo,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:19802 (rota sem os decoradores)
async def get_peticionamento_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual `org_doc`: ex. Sem materia, código antes de ' - ').",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis (repita o parâmetro para vários; como nos gráficos NG de peticionamento).",
    ),
    uf_peticionamento: Optional[str] = Query(
        None,
        description="Filtra peticionamento pela UF. Valores disponíveis em GET /peticionamento/ufs.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Peticionamento."""
    return await _get_dashboard_response(
        "peticionamento",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        uf_peticionamento=uf_peticionamento,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:19780 (rota sem os decoradores)
async def get_peticionamento_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(None),
    funcionario: Optional[List[str]] = Query(None),
    uf_peticionamento: Optional[str] = Query(None),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Peticionamento — escritório RJ."""
    return await _get_dashboard_response(
        "peticionamento_RJ",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        uf_peticionamento=uf_peticionamento,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:20080 (rota sem os decoradores)
async def get_org_documentos_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria, ex. Sem materia).",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis (repita o parâmetro para vários; como nos gráficos).",
    ),
    uf_org_doc: Optional[str] = Query(
        None,
        description="Filtra org. documentos pela UF. Valores disponíveis em GET /org-documentos/ufs.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Organização de Documentos."""
    return await _get_dashboard_response(
        "org-documentos",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        uf_org_doc=uf_org_doc,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:20058 (rota sem os decoradores)
async def get_org_doc_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(None),
    funcionario: Optional[List[str]] = Query(None),
    uf_org_doc: Optional[str] = Query(None),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Organização de Documentos — escritório RJ."""
    return await _get_dashboard_response(
        "org_doc_RJ",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        uf_org_doc=uf_org_doc,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:20424 (rota sem os decoradores)
async def get_pendencias_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis (repita o parâmetro para vários; como em funcionarios_pendencias).",
    ),
    uf_pendencias: Optional[str] = Query(
        None,
        description="Filtra pendências pela UF. Valores disponíveis em GET /pendencias/ufs.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Pendências."""
    return await _get_dashboard_response(
        "pendencias",
        from_date,
        to_date,
        funcionario=funcionario,
        uf_pendencias=uf_pendencias,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:20404 (rota sem os decoradores)
async def get_pendencias_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    funcionario: Optional[List[str]] = Query(None),
    uf_pendencias: Optional[str] = Query(None),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Pendências — escritório RJ."""
    return await _get_dashboard_response(
        "pendencias_RJ",
        from_date,
        to_date,
        funcionario=funcionario,
        uf_pendencias=uf_pendencias,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:15489 (rota sem os decoradores)
async def get_comercial_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    atendente_comercial: Optional[List[str]] = Query(
        None,
        description="Filtra métricas pelos atendentes comerciais (repita o parâmetro para vários; nomes como em atendentes_comerciais).",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Alias de atendente_comercial (repita o parâmetro para vários; mesmo padrão das outras páginas).",
    ),
    segmento_comercial_ng: Optional[str] = Query(
        None,
        description="Filtra apenas `comercial_geral` (NG). Slugs: CAMPANHA_RA, CAMPANHA_NG, REDES_SOCIAIS, INDICACAO, RETORNO, SITE, RESGATE, CANCELADOS. Ver GET /comercial/segmentos.",
    ),
    uf_comercial_ng: Optional[str] = Query(
        None,
        description="Filtra apenas `comercial_geral` (NG) pela UF. Valores disponíveis em GET /comercial/ufs.",
    ),
    segmento_comercial_la: Optional[str] = Query(
        None,
        description="Filtra apenas `comercial_LA`. Slugs: CAMPANHA, REDES_SOCIAIS, INDICACAO, RETORNO, PARCEIROS, EXTERNOS, CANCELADOS. Ver GET /comercial_LA/segmentos.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(
        None,
        description="Filtra processos pela área de atuação (ID). Ver GET /comercial/areas_atuacao.",
    ),
):
    """Dashboard Comercial NG."""
    return await _get_dashboard_response(
        "comercial",
        from_date,
        to_date,
        atendente_comercial=atendente_comercial,
        funcionario=funcionario,
        segmento_comercial_ng=segmento_comercial_ng,
        uf_comercial_ng=uf_comercial_ng,
        segmento_comercial_la=segmento_comercial_la,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:15847 (rota sem os decoradores)
async def get_comercial_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    atendente_comercial: Optional[List[str]] = Query(None),
    funcionario: Optional[List[str]] = Query(None),
    segmento_comercial_ng: Optional[str] = Query(
        None,
        description="Filtra `comercial_geral` RJ por segmento. Mesmos slugs do NG.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(
        None,
        description="Filtra processos pela área de atuação (ID). Ver GET /comercial/areas_atuacao.",
    ),
):
    """Dashboard Comercial RJ."""
    return await _get_dashboard_response(
        "comercial_RJ",
        from_date,
        to_date,
        atendente_comercial=atendente_comercial,
        funcionario=funcionario,
        segmento_comercial_ng=segmento_comercial_ng,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:32638 (rota sem os decoradores)
async def get_marketing_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    selection_dim: Optional[List[str]] = Query(None, alias="selection_dim"),
    selection_value: Optional[List[str]] = Query(None, alias="selection_value"),
):
    """Dashboard de Marketing / Perfil de Clientes — banco NG.

    Perfil demográfico (idade, gênero, ocupação, faixa salarial) e de aquisição
    (origem, tipo de tráfego, dispositivo, prospecção) dos clientes assinados.

    `selection_dim`/`selection_value` (pares posicionais, repetíveis) aplicam
    filtros de drill-down — múltiplos valores na mesma dimensão = OR; dimensões
    diferentes = AND. Ver `apply_selection_filters` em `analyses/NG/marketing_ng.py`.
    """
    return await _get_dashboard_response(
        "marketing_NG", from_date, to_date, selection_dim, selection_value
    )


# v1: dashboard_routes.py:32608 (rota sem os decoradores)
async def get_nps_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
):
    """Dashboard de NPS (Net Promoter Score) — banco NG.

    Retorna métricas de satisfação (NPS, taxa de confiança, nível de informação,
    nível de indicação, tempo médio de resposta) e tabelas de respostas,
    feedbacks de melhoria, feedbacks positivos e comentários livres.
    """
    return await _get_dashboard_response("nps_NG", from_date, to_date)


# v1: dashboard_routes.py:15252 (rota sem os decoradores)
async def get_tickets_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    selection_dim: Optional[List[str]] = Query(None, alias="selection_dim"),
    selection_value: Optional[List[str]] = Query(None, alias="selection_value"),
):
    """Dashboard de Tickets."""
    return await _get_dashboard_response("tickets", from_date, to_date, selection_dim, selection_value)


# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache).
HANDLERS = {"protocolo": get_protocolo_dashboard, "protocolo_RJ": get_protocolo_rj_dashboard, "peticionamento": get_peticionamento_dashboard, "peticionamento_RJ": get_peticionamento_rj_dashboard, "org-documentos": get_org_documentos_dashboard, "org_doc_RJ": get_org_doc_rj_dashboard, "pendencias": get_pendencias_dashboard, "pendencias_RJ": get_pendencias_rj_dashboard, "comercial": get_comercial_dashboard, "comercial_RJ": get_comercial_rj_dashboard, "marketing_NG": get_marketing_NG_dashboard, "nps_NG": get_nps_NG_dashboard, "tickets": get_tickets_dashboard}
QUERIES_POR_DASHBOARD = {'protocolo': ('setor_protocolo', 'comercial_geral_NG'), 'protocolo_RJ': ('setor_protocolo', 'comercial_geral_NG'), 'peticionamento': ('setor_confeccao',), 'peticionamento_RJ': ('setor_confeccao',), 'org-documentos': ('setor_org_doc',), 'org_doc_RJ': ('setor_org_doc',), 'pendencias': ('setor_pendencias',), 'pendencias_RJ': ('setor_pendencias',), 'comercial': ('comercial_geral_NG', 'actions_NG_2', 'setor_protocolo', 'setor_confeccao', 'setor_org_doc', 'setor_pendencias', 'rubrica_count_por_processo'), 'comercial_RJ': ('comercial_geral_NG', 'actions_NG_2', 'setor_protocolo', 'setor_confeccao', 'setor_org_doc', 'setor_pendencias', 'rubrica_count_por_processo'), 'marketing_NG': ('perfil_clientes_NG', 'facebook_ads', 'actions_NG_2', 'setor_protocolo', 'comercial_geral_NG', 'Analise_thiago', 'trackeamento_NG_2'), 'nps_NG': ('nps_NG',), 'tickets': ('tickets',)}
