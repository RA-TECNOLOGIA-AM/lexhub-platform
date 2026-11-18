"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (linha na v1 ao lado de cada bloco).
Gerado por scripts/copiar_v1/gerar_generico.py (banco lexflow). Únicas trocas, marcadas com "V2:":
  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;
  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo;
  * fontes de outro banco saem de FETCHES_BY_DASHBOARD (chegam vazias, como na v1 com a fonte fora do ar).
Dashboards: execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ.
"""

import asyncio
import logging
import time
from contextvars import ContextVar
from app.analyses.LA.controle_processo_LA import (
    filter_controle_processo_por_situacao_LA,
    get_comparativo_media_tempo_dias_fase_execucao_LA,
    get_comparativo_media_tempo_dias_fase_inicial_LA,
    get_comparativo_media_tempo_dias_fase_recursal_LA,
    get_comparativo_mediana_tempo_dias_fase_execucao_LA,
    get_comparativo_mediana_tempo_dias_fase_inicial_LA,
    get_comparativo_mediana_tempo_dias_fase_recursal_LA,
    get_extintos_com_merito_2g_por_tipo_sentenca_LA,
    get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA,
    get_extintos_com_merito_por_tipo_sentenca_LA,
    get_media_tempo_dias_fase_execucao_LA,
    get_media_tempo_dias_fase_execucao_por_mes_LA,
    get_media_tempo_dias_fase_inicial_LA,
    get_media_tempo_dias_fase_inicial_por_mes_LA,
    get_media_tempo_dias_fase_recursal_LA,
    get_media_tempo_dias_fase_recursal_por_mes_LA,
    get_mediana_tempo_dias_fase_execucao_LA,
    get_mediana_tempo_dias_fase_inicial_LA,
    get_mediana_tempo_dias_fase_recursal_LA,
    get_taxa_provimento_2g_LA,
    get_tempo_medio_dias_por_subfase_LA,
    get_total_controle_processo_LA,
    get_total_controle_processo_fase_arquivado_improcedente_LA,
    get_total_controle_processo_fase_arquivado_procedente_LA,
    get_total_controle_processo_fase_execucao_LA,
    get_total_controle_processo_fase_inicial_LA,
    get_total_controle_processo_fase_recursal_LA,
    get_total_controle_processo_fase_transito_julgado_LA,
    get_total_controle_processo_log_inicial_indeferida_LA,
    get_total_controle_processo_log_recursal_nao_provido_LA,
    get_total_extintos_com_merito_2g_LA,
    get_total_extintos_com_merito_LA,
    get_total_extintos_sem_merito_2g_LA,
    get_total_extintos_sem_merito_LA,
    get_valor_causa_acordao_total_extintos_com_merito_2g_LA,
    get_valor_causa_acordao_total_extintos_sem_merito_2g_LA,
    get_valor_causa_execucao_total_controle_processo_fase_execucao_LA,
    get_valor_causa_total_controle_processo_fase_arquivado_improcedente_LA,
    get_valor_causa_total_controle_processo_fase_arquivado_procedente_LA,
    get_valor_causa_total_controle_processo_fase_inicial_LA,
    get_valor_causa_total_controle_processo_fase_recursal_LA,
    get_valor_causa_total_controle_processo_fase_transito_julgado_LA,
    get_valor_causa_total_controle_processo_log_inicial_indeferida_LA,
    get_valor_causa_total_controle_processo_log_recursal_nao_provido_LA,
    get_valor_causa_total_extintos_com_merito_2g_LA,
    get_valor_causa_total_extintos_com_merito_LA,
    get_valor_causa_total_extintos_sem_merito_2g_LA,
    get_valor_causa_total_extintos_sem_merito_LA,
    group_controle_processo_por_fase_LA,
    group_controle_processo_por_subfase_na_fase_LA,
)
from app.analyses.LA.execucao_LA import (
    ExecucaoAtividadesFiltros,
    SITUACOES_VALIDAS_EXECUCAO,
    _extrair_duracoes_dias as _duracoes_execucao_la,
    _filtrar_em_execucao as _filtrar_em_execucao_la,
    _filtrar_entrada_execucao_no_periodo as _filtrar_entrada_execucao_no_periodo_la,
    _get_ag_processo_id,
    anotar_saida_execucao_export_LA,
    filter_execucao_LA_por_ano_ajuizamento,
    filter_execucao_LA_por_comarca,
    filter_execucao_LA_por_materia,
    filter_execucao_LA_por_subfase,
    filter_execucao_LA_por_uf,
    filtrar_agendamentos_execucao_LA,
    filtrar_saida_execucao_export_LA,
    get_atrasos_detalhamento_execucao_LA,
    get_detalhe_valor_execucao_vazio_LA,
    get_estoque_final_LA,
    get_kpis_atividades_execucao_LA,
    get_kpis_execucao_por_prazo_LA,
    get_media_execucao_resolvidos_por_funcionario_LA,
    get_media_execucao_resolvidos_por_funcionario_por_prazo_LA,
    get_media_mensal_atividades_execucao_LA,
    get_media_tempo_execucao_LA,
    get_media_tempo_execucao_por_mes_LA,
    get_mediana_tempo_execucao_LA,
    get_opcoes_comarca_execucao_LA,
    get_opcoes_filtros_execucao_LA,
    get_opcoes_filtros_execucao_por_prazo_LA,
    get_opcoes_materia_execucao_LA,
    get_opcoes_subfase_execucao_LA,
    get_opcoes_uf_execucao_LA,
    get_taxa_atualizacao_execucao_LA,
    get_taxa_recuperacao_execucao_LA,
    get_total_execucao_LA,
    get_total_incontroverso_saida_periodo_LA,
    get_total_saida_execucao_periodo_LA,
    get_total_valor_execucao_vazio_LA,
    get_tre_execucao_dax_LA,
    get_valor_causa_total_execucao_LA,
    get_valor_em_execucao_LA,
    get_valor_execucao_saida_periodo_LA,
    get_valor_honorarios_total_execucao_LA,
    get_valor_incontroverso_saida_periodo_LA,
    get_valor_remanescente_em_execucao_LA,
    get_valor_ted_saida_execucao_periodo_LA,
    group_alvaras_expedidos_por_dia_LA,
    group_atividades_ativas_criadas_por_atividade_LA,
    group_atividades_ativas_por_prazo_por_atividade_LA,
    group_atividades_criadas_por_atividade_LA,
    group_entrada_execucao_por_fluxo_cs_por_mes_LA,
    group_estoque_execucao_por_mes_LA,
    group_execucao_demandas_por_funcionario_LA,
    group_execucao_demandas_por_funcionario_completo_LA,
    group_execucao_demandas_por_funcionario_por_prazo_LA,
    group_execucao_demandas_por_funcionario_por_prazo_completo_LA,
    group_execucao_nao_cumprido_por_motivo_LA,
    group_execucao_por_ano_ajuizamento_LA,
    group_execucao_por_comarca_LA,
    group_execucao_por_materia_LA,
    group_execucao_por_subfase_LA,
    group_execucao_processos_por_atividade_LA,
    group_execucao_processos_por_atividade_por_prazo_LA,
    group_execucao_resolvidos_por_dia_LA,
    group_execucao_resolvidos_por_dia_por_prazo_LA,
    group_quantidade_entrada_execucao_por_mes_LA,
    group_quantidade_saida_execucao_por_mes_LA,
    group_taxa_conclusao_por_funcionario_LA,
    group_valor_entrada_execucao_por_mes_LA,
    group_valor_execucao_por_comarca_LA,
    group_valor_execucao_por_materia_LA,
    group_valor_execucao_por_subfase_LA,
    group_valor_execucao_saida_periodo_por_mes_LA,
    group_valor_recuperado_por_funcionario_LA,
    group_valor_remanescente_por_mes_LA,
    group_valor_saida_execucao_por_mes_LA,
    list_execucao_atividades_abertas_LA,
    list_execucao_atividades_periodo_LA,
    list_execucao_atividades_por_prazo_periodo_LA,
    list_processos_alvara_expedido_LA,
)
from app.analyses.LA.execucao_acordos_LA import (
    _extrair_duracoes_dias as _duracoes_execucao_acordos_la,
    _filtrar_em_execucao_acordos_LA,
    _filtrar_entrada_execucao_acordos_LA_no_periodo,
    _filtrar_saida_execucao_acordos_LA_no_periodo,
    filter_execucao_acordos_LA_por_ano_ajuizamento,
    filter_execucao_acordos_LA_por_comarca,
    filter_execucao_acordos_LA_por_materia,
    filter_execucao_acordos_LA_por_processo,
    filter_execucao_acordos_LA_por_sentenca,
    filter_execucao_acordos_LA_por_subfase,
    filter_execucao_acordos_LA_por_tipo_acao,
    filter_execucao_acordos_LA_por_uf,
    filtrar_agendamentos_diligencia_acordos_LA,
    filtrar_agendamentos_diligencia_expedicao_alvara_acordos_LA,
    filtrar_agendamentos_diligencia_por_colaborador_acordos_LA,
    filtrar_agendamentos_diligencia_por_tipo_acordos_LA,
    filtrar_agendamentos_execucao_acordos_LA,
    get_atrasos_detalhamento_execucao_acordos_LA,
    get_detalhe_valor_alcada_final_vazio_LA,
    get_estoque_final_execucao_acordos_LA,
    get_kpis_atividades_execucao_acordos_LA,
    get_kpis_diligencias_expedicao_alvara_acordos_LA,
    get_kpis_execucao_por_prazo_acordos_LA,
    get_media_execucao_resolvidos_por_funcionario_acordos_LA,
    get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_LA,
    get_media_mensal_atividades_execucao_acordos_LA,
    get_media_tempo_execucao_acordos_LA,
    get_media_tempo_execucao_acordos_LA_por_mes,
    get_mediana_tempo_execucao_acordos_LA,
    get_opcoes_comarca_execucao_acordos_LA,
    get_opcoes_filtros_execucao_acordos_LA,
    get_opcoes_filtros_execucao_por_prazo_acordos_LA,
    get_opcoes_materia_execucao_acordos_LA,
    get_opcoes_subfase_execucao_acordos_LA,
    get_opcoes_uf_execucao_acordos_LA,
    get_total_diligencias_execucao_acordos_LA,
    get_total_entrada_execucao_acordos_LA_periodo,
    get_total_execucao_acordos_LA,
    get_total_processos_fechamento_acordo_LA,
    get_total_saida_execucao_acordos_LA_periodo,
    get_total_valor_alcada_final_vazio_LA,
    get_tre_execucao_acordos_LA_dax,
    get_valor_alcada_final_total_execucao_acordos_LA,
    get_valor_entrada_execucao_acordos_LA_periodo,
    get_valor_saida_execucao_acordos_LA_periodo,
    get_valor_ted_saida_execucao_acordos_LA_periodo,
    group_alvaras_expedidos_acordos_por_dia_LA,
    group_atividades_ativas_criadas_por_atividade_acordos_LA,
    group_atividades_ativas_por_prazo_por_atividade_acordos_LA,
    group_estoque_execucao_acordos_por_mes_LA,
    group_execucao_acordos_LA_por_ano_ajuizamento,
    group_execucao_acordos_LA_por_comarca,
    group_execucao_acordos_LA_por_materia,
    group_execucao_acordos_LA_por_sentenca,
    group_execucao_acordos_LA_por_subfase,
    group_execucao_acordos_LA_por_tipo_acao,
    group_execucao_acordos_diligencias_por_processo_LA,
    group_execucao_demandas_por_funcionario_acordos_LA,
    group_execucao_demandas_por_funcionario_completo_acordos_LA,
    group_execucao_demandas_por_funcionario_por_prazo_acordos_LA,
    group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_LA,
    group_execucao_nao_cumprido_por_motivo_acordos_LA,
    group_execucao_processos_por_atividade_acordos_LA,
    group_execucao_processos_por_atividade_por_prazo_acordos_LA,
    group_execucao_resolvidos_por_dia_acordos_LA,
    group_execucao_resolvidos_por_dia_por_prazo_acordos_LA,
    group_fechamento_acordo_por_subfase_LA,
    group_quantidade_entrada_execucao_acordos_LA_por_mes,
    group_quantidade_saida_execucao_acordos_LA_por_mes,
    group_valor_entrada_execucao_acordos_LA_por_mes,
    group_valor_execucao_acordos_LA_por_comarca,
    group_valor_execucao_acordos_LA_por_materia,
    group_valor_execucao_acordos_LA_por_subfase,
    group_valor_fechamento_acordo_por_subfase_LA,
    group_valor_saida_execucao_acordos_LA_por_mes,
    list_execucao_acordos_LA_lista_entrada,
    list_execucao_acordos_LA_lista_saida,
    list_execucao_acordos_LA_lista_total,
    list_execucao_atividades_periodo_acordos_LA,
    list_execucao_atividades_por_prazo_periodo_acordos_LA,
    list_processos_alvara_expedido_acordos_LA,
    list_processos_diligencia_expedicao_alvara_cumprida_acordos_LA,
)
from app.analyses.LA.publicacoes_LA import (
    build_publicacoes_agendamento_apos_finalizacao_LA,
    filter_publicacoes_por_atividade_agendamento_LA,
    filter_publicacoes_por_documento_LA,
    filter_publicacoes_por_leitor_LA,
    filter_publicacoes_por_materia_LA,
    filter_publicacoes_por_orgao_LA,
    filter_publicacoes_por_setor_agendamento_LA,
    filter_publicacoes_por_status_agendamento_LA,
    filter_publicacoes_por_tribunal_LA,
    filter_publicacoes_recebidas_no_periodo_LA,
    filter_publicacoes_tratadas_no_periodo_LA,
    get_media_tempo_tratamento_publicacoes_LA,
    get_pct_tratadas_mesmo_dia_publicacoes_LA,
    get_publicacoes_com_data_disponibilizacao_LA,
    get_publicacoes_comissionamento_por_funcionario_LA,
    get_publicacoes_cumpridas_mesmo_dia_chegada_LA,
    get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_LA,
    get_publicacoes_pendentes_LA,
    get_publicacoes_pendentes_zeradas_no_periodo_LA,
    get_publicacoes_recebidas_no_dia_LA,
    get_publicacoes_recebidas_periodo_LA,
    get_publicacoes_tratadas_no_dia_LA,
    get_publicacoes_tratadas_periodo_LA,
    group_publicacoes_cumprido_por_leitor_LA,
    group_publicacoes_pendentes_por_dias_atraso_LA,
    group_publicacoes_pendentes_por_leitor_LA,
    group_publicacoes_por_comarca_LA,
    group_publicacoes_por_materia_LA,
    group_publicacoes_por_orgao_LA,
    group_publicacoes_por_tipo_documento_LA,
    group_publicacoes_por_tribunal_LA,
    group_publicacoes_recebidas_por_dia_LA,
    group_publicacoes_tratadas_por_dia_LA,
    list_publicacoes_LA,
    resolve_dia_referencia_fim_periodo_LA,
)
from app.analyses.LA.recurso_LA import (
    DECISAO_EXTINCAO_REAJUIZAR,
    DECISAO_GANHO_AMPLIADO,
    DECISAO_GANHO_REDUZIDO,
    DECISAO_INSTRUCAO_RETOMADA,
    DECISAO_MANTIDO_GANHO,
    DECISAO_MANTIDO_PERDA,
    DECISAO_REVERTIDO_GANHO,
    DECISAO_REVERTIDO_PERDA,
    RecursalAtividadesRecursosFiltros,
    RecursalLAFiltros,
    _SITUACOES_RECURSOS_VALIDAS,
    _col_recursal_la,
    _enriquecer_numero_processo_export_la,
    _get_numero_processo_recursal_la,
    filtrar_agendamentos_recursos_LA,
    filtrar_recursal_LA,
    filtrar_recursal_LA_por_processo_ids,
    get_decisoes_recursal_resumo_LA,
    get_entrada_recurso_LA,
    get_kpis_atividades_recursos_LA,
    get_kpis_atividades_recursos_por_prazo_LA,
    get_media_recursal_resolvidos_por_funcionario_LA,
    get_opcoes_filtros_atividades_lista_LA,
    get_opcoes_filtros_recursal_LA,
    get_ranking_juizes_recursal_LA,
    get_ranking_relatores_recursal_LA,
    get_recursal_resolvidos_por_dia_por_funcionario_LA,
    get_total_acordao_desfavoravel_recurso_LA,
    get_total_acordao_extincao_recurso_LA,
    get_total_acordao_favoravel_recurso_LA,
    get_total_acordao_parcial_retomada_recurso_LA,
    get_total_acordao_parcialmente_favoravel_recurso_LA,
    get_total_parcialmente_procedente_recurso_LA,
    get_total_procedente_1g_recurso_LA,
    get_total_recurso_LA,
    get_total_sentenca_desfavoravel_recurso_LA,
    get_total_sentenca_extincao_recurso_LA,
    get_total_sentenca_favoravel_recurso_LA,
    get_total_sentenca_parcialmente_favoravel_recurso_LA,
    get_valor_causa_acordao_desfavoravel_recurso_LA,
    get_valor_causa_acordao_extincao_recurso_LA,
    get_valor_causa_acordao_favoravel_recurso_LA,
    get_valor_causa_acordao_parcial_retomada_recurso_LA,
    get_valor_causa_acordao_parcialmente_favoravel_recurso_LA,
    get_valor_causa_acordo_recurso_LA,
    get_valor_causa_sentenca_parcialmente_favoravel_recurso_LA,
    get_valor_causa_sentenca_parcialmente_procedente_recurso_LA,
    get_valor_causa_sentenca_procedente_1g_recurso_LA,
    get_valor_causa_sentenca_sentenca_desfavoravel_recurso_LA,
    get_valor_causa_sentenca_sentenca_extincao_recurso_LA,
    get_valor_causa_sentenca_sentenca_favoravel_recurso_LA,
    group_decisoes_recursal_LA,
    group_recursal_demandas_por_funcionario_LA,
    group_recursal_por_competencia_LA,
    group_recursal_por_materia_LA,
    group_recursal_por_status_1g_LA,
    group_recursal_por_status_2g_LA,
    group_recursal_por_subfase_LA,
    group_recursal_por_vara_LA,
    group_recursal_processos_por_atividade_LA,
    group_recursal_resolvidos_por_dia_LA,
    group_recursal_resolvidos_por_mes_LA,
    list_recursal_atividades_periodo_LA,
    processo_ids_recursal_de_agendamentos_recursos_LA,
    rotulo_decisao_recursal_export_LA,
    set_atividades_recursos_LA_catalogo,
)
from app.analyses.NG.comercial_geral import (
    filter_comercial_geral_por_area_atuacao,
)
from app.analyses.NG.controle_processo_NG import (
    filter_controle_processo_com_numero_NG,
    filter_controle_processo_por_situacao_NG,
    filter_controle_processo_por_uf_NG,
    get_comparativo_media_tempo_dias_fase_execucao_NG,
    get_comparativo_media_tempo_dias_fase_inicial_NG,
    get_comparativo_media_tempo_dias_fase_recursal_NG,
    get_comparativo_mediana_tempo_dias_fase_execucao_NG,
    get_comparativo_mediana_tempo_dias_fase_inicial_NG,
    get_comparativo_mediana_tempo_dias_fase_recursal_NG,
    get_extintos_com_merito_2g_por_tipo_sentenca_NG,
    get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG,
    get_extintos_com_merito_por_tipo_sentenca_NG,
    get_media_tempo_dias_fase_execucao_NG,
    get_media_tempo_dias_fase_execucao_por_mes_NG,
    get_media_tempo_dias_fase_inicial_NG,
    get_media_tempo_dias_fase_inicial_por_mes_NG,
    get_media_tempo_dias_fase_recursal_NG,
    get_media_tempo_dias_fase_recursal_por_mes_NG,
    get_mediana_tempo_dias_fase_execucao_NG,
    get_mediana_tempo_dias_fase_inicial_NG,
    get_mediana_tempo_dias_fase_recursal_NG,
    get_opcoes_uf_NG,
    get_taxa_provimento_2g_NG,
    get_tempo_medio_dias_por_subfase_NG,
    get_total_controle_processo_NG,
    get_total_controle_processo_fase_arquivado_improcedente_NG,
    get_total_controle_processo_fase_arquivado_procedente_NG,
    get_total_controle_processo_fase_execucao_NG,
    get_total_controle_processo_fase_inicial_NG,
    get_total_controle_processo_fase_recursal_NG,
    get_total_controle_processo_fase_transito_julgado_NG,
    get_total_controle_processo_log_inicial_indeferida_NG,
    get_total_controle_processo_log_recursal_nao_provido_NG,
    get_total_extintos_com_merito_2g_NG,
    get_total_extintos_com_merito_NG,
    get_total_extintos_sem_merito_2g_NG,
    get_total_extintos_sem_merito_NG,
    get_valor_causa_acordao_total_extintos_com_merito_2g_NG,
    get_valor_causa_acordao_total_extintos_sem_merito_2g_NG,
    get_valor_causa_execucao_total_controle_processo_fase_execucao_NG,
    get_valor_causa_total_controle_processo_NG,
    get_valor_causa_total_controle_processo_fase_arquivado_improcedente_NG,
    get_valor_causa_total_controle_processo_fase_arquivado_procedente_NG,
    get_valor_causa_total_controle_processo_fase_inicial_NG,
    get_valor_causa_total_controle_processo_fase_recursal_NG,
    get_valor_causa_total_controle_processo_fase_transito_julgado_NG,
    get_valor_causa_total_controle_processo_log_inicial_indeferida_NG,
    get_valor_causa_total_controle_processo_log_recursal_nao_provido_NG,
    get_valor_causa_total_extintos_com_merito_2g_NG,
    get_valor_causa_total_extintos_com_merito_NG,
    get_valor_causa_total_extintos_sem_merito_2g_NG,
    get_valor_causa_total_extintos_sem_merito_NG,
    group_controle_processo_por_fase_NG,
    group_controle_processo_por_subfase_na_fase_NG,
)
from app.analyses.NG.execucao import (
    _extrair_duracoes_dias as _duracoes_execucao_ng,
    _filtrar_em_execucao as _filtrar_em_execucao_ng,
    _filtrar_entrada_execucao_no_periodo as _filtrar_entrada_execucao_no_periodo_ng,
    _get_ag_processo_id_ng,
    anotar_saida_execucao_export as anotar_saida_execucao_export_ng,
    filter_execucao_por_ano_ajuizamento,
    filter_execucao_por_comarca,
    filter_execucao_por_materia,
    filter_execucao_por_subfase,
    filter_execucao_por_uf,
    filtrar_agendamentos_diligencia_NG,
    filtrar_agendamentos_diligencia_expedicao_alvara_NG,
    filtrar_agendamentos_diligencia_por_colaborador_NG,
    filtrar_agendamentos_diligencia_por_tipo_NG,
    filtrar_agendamentos_execucao_NG,
    filtrar_saida_execucao_export as filtrar_saida_execucao_export_ng,
    get_atrasos_detalhamento_execucao_NG,
    get_detalhe_valor_execucao_vazio,
    get_estoque_final,
    get_kpis_atividades_execucao_NG,
    get_kpis_diligencias_expedicao_alvara_execucao_NG,
    get_kpis_execucao_por_prazo_NG,
    get_media_execucao_resolvidos_por_funcionario_NG,
    get_media_execucao_resolvidos_por_funcionario_por_prazo_NG,
    get_media_mensal_atividades_execucao_NG,
    get_media_tempo_execucao,
    get_media_tempo_execucao_por_mes,
    get_mediana_tempo_execucao,
    get_opcoes_comarca_execucao,
    get_opcoes_filtros_execucao_NG,
    get_opcoes_filtros_execucao_por_prazo_NG,
    get_opcoes_materia_execucao,
    get_opcoes_subfase_execucao,
    get_opcoes_uf_execucao,
    get_taxa_atualizacao_execucao_NG,
    get_taxa_recuperacao_execucao,
    get_total_diligencias_execucao_NG,
    get_total_execucao,
    get_total_incontroverso_saida_periodo,
    get_total_saida_execucao_periodo,
    get_total_valor_execucao_vazio,
    get_tre_execucao_dax,
    get_valor_causa_total_execucao,
    get_valor_em_execucao,
    get_valor_execucao_saida_periodo,
    get_valor_honorarios_total_execucao,
    get_valor_incontroverso_saida_periodo,
    get_valor_remanescente_em_execucao,
    get_valor_ted_saida_execucao_periodo,
    group_alvaras_expedidos_por_dia_NG,
    group_atividades_ativas_criadas_por_atividade_NG,
    group_atividades_ativas_por_prazo_por_atividade_NG,
    group_atividades_criadas_por_atividade_NG,
    group_entrada_execucao_por_fluxo_cs_por_mes_NG,
    group_estoque_execucao_por_mes,
    group_execucao_demandas_por_funcionario_NG,
    group_execucao_demandas_por_funcionario_completo_NG,
    group_execucao_demandas_por_funcionario_por_prazo_NG,
    group_execucao_demandas_por_funcionario_por_prazo_completo_NG,
    group_execucao_diligencias_por_processo_NG,
    group_execucao_nao_cumprido_por_motivo_NG,
    group_execucao_por_ano_ajuizamento_NG,
    group_execucao_por_comarca,
    group_execucao_por_materia,
    group_execucao_por_subfase,
    group_execucao_processos_por_atividade_NG,
    group_execucao_processos_por_atividade_por_prazo_NG,
    group_execucao_resolvidos_por_dia_NG,
    group_execucao_resolvidos_por_dia_por_prazo_NG,
    group_quantidade_entrada_execucao_por_mes,
    group_quantidade_saida_execucao_por_mes,
    group_taxa_conclusao_por_funcionario_NG,
    group_valor_entrada_execucao_por_mes,
    group_valor_execucao_por_comarca,
    group_valor_execucao_por_materia,
    group_valor_execucao_por_subfase,
    group_valor_execucao_saida_periodo_por_mes,
    group_valor_recuperado_por_funcionario_NG,
    group_valor_remanescente_por_mes,
    group_valor_saida_execucao_por_mes,
    list_execucao_atividades_abertas_NG,
    list_execucao_atividades_periodo_NG,
    list_execucao_atividades_por_prazo_periodo_NG,
    list_processos_alvara_expedido_NG,
    list_processos_diligencia_expedicao_alvara_cumprida_execucao_NG,
)
from app.analyses.NG.execucao_acordos import (
    _extrair_duracoes_dias as _duracoes_execucao_acordos_ng,
    _filtrar_em_execucao_acordos,
    _filtrar_entrada_execucao_acordos_no_periodo,
    _filtrar_saida_execucao_acordos_no_periodo,
    filter_execucao_acordos_por_ano_ajuizamento,
    filter_execucao_acordos_por_comarca,
    filter_execucao_acordos_por_materia,
    filter_execucao_acordos_por_processo,
    filter_execucao_acordos_por_sentenca,
    filter_execucao_acordos_por_subfase,
    filter_execucao_acordos_por_tipo_acao,
    filter_execucao_acordos_por_uf,
    filtrar_agendamentos_diligencia_acordos_NG,
    filtrar_agendamentos_diligencia_expedicao_alvara_acordos_NG,
    filtrar_agendamentos_diligencia_por_colaborador_acordos_NG,
    filtrar_agendamentos_diligencia_por_tipo_acordos_NG,
    filtrar_agendamentos_execucao_acordos_NG,
    get_atrasos_detalhamento_execucao_acordos_NG,
    get_detalhe_valor_alcada_final_vazio,
    get_estoque_final_execucao_acordos,
    get_kpis_atividades_execucao_acordos_NG,
    get_kpis_diligencias_expedicao_alvara_acordos_NG,
    get_kpis_execucao_por_prazo_acordos_NG,
    get_media_execucao_resolvidos_por_funcionario_acordos_NG,
    get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_NG,
    get_media_mensal_atividades_execucao_acordos_NG,
    get_media_tempo_execucao_acordos,
    get_media_tempo_execucao_acordos_por_mes,
    get_mediana_tempo_execucao_acordos,
    get_opcoes_comarca_execucao_acordos,
    get_opcoes_filtros_execucao_acordos_NG,
    get_opcoes_filtros_execucao_por_prazo_acordos_NG,
    get_opcoes_materia_execucao_acordos,
    get_opcoes_subfase_execucao_acordos,
    get_opcoes_uf_execucao_acordos,
    get_total_diligencias_execucao_acordos_NG,
    get_total_entrada_execucao_acordos_periodo,
    get_total_execucao_acordos,
    get_total_processos_fechamento_acordo,
    get_total_saida_execucao_acordos_periodo,
    get_total_valor_alcada_final_vazio,
    get_tre_execucao_acordos_dax,
    get_valor_alcada_final_total_execucao_acordos,
    get_valor_entrada_execucao_acordos_periodo,
    get_valor_saida_execucao_acordos_periodo,
    get_valor_ted_saida_execucao_acordos_NG_periodo,
    group_alvaras_expedidos_acordos_por_dia_NG,
    group_atividades_ativas_criadas_por_atividade_acordos_NG,
    group_atividades_ativas_por_prazo_por_atividade_acordos_NG,
    group_estoque_execucao_acordos_por_mes,
    group_execucao_acordos_diligencias_por_processo_NG,
    group_execucao_acordos_por_ano_ajuizamento,
    group_execucao_acordos_por_comarca,
    group_execucao_acordos_por_materia,
    group_execucao_acordos_por_sentenca,
    group_execucao_acordos_por_subfase,
    group_execucao_acordos_por_tipo_acao,
    group_execucao_demandas_por_funcionario_acordos_NG,
    group_execucao_demandas_por_funcionario_completo_acordos_NG,
    group_execucao_demandas_por_funcionario_por_prazo_acordos_NG,
    group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_NG,
    group_execucao_nao_cumprido_por_motivo_acordos_NG,
    group_execucao_processos_por_atividade_acordos_NG,
    group_execucao_processos_por_atividade_por_prazo_acordos_NG,
    group_execucao_resolvidos_por_dia_acordos_NG,
    group_execucao_resolvidos_por_dia_por_prazo_acordos_NG,
    group_fechamento_acordo_por_subfase,
    group_quantidade_entrada_execucao_acordos_por_mes,
    group_quantidade_saida_execucao_acordos_por_mes,
    group_valor_entrada_execucao_acordos_por_mes,
    group_valor_execucao_acordos_por_comarca,
    group_valor_execucao_acordos_por_materia,
    group_valor_execucao_acordos_por_subfase,
    group_valor_fechamento_acordo_por_subfase,
    group_valor_saida_execucao_acordos_por_mes,
    list_execucao_acordos_lista_entrada,
    list_execucao_acordos_lista_saida,
    list_execucao_acordos_lista_total,
    list_execucao_atividades_periodo_acordos_NG,
    list_execucao_atividades_por_prazo_periodo_acordos_NG,
    list_processos_alvara_expedido_acordos_NG,
    list_processos_diligencia_expedicao_alvara_cumprida_acordos_NG,
)
from app.analyses.NG.publicacoes_NG import (
    build_publicacoes_agendamento_apos_finalizacao_NG,
    filter_publicacoes_por_atividade_agendamento_NG,
    filter_publicacoes_por_documento_NG,
    filter_publicacoes_por_leitor_NG,
    filter_publicacoes_por_materia_NG,
    filter_publicacoes_por_orgao_NG,
    filter_publicacoes_por_setor_agendamento_NG,
    filter_publicacoes_por_status_agendamento_NG,
    filter_publicacoes_por_tribunal_NG,
    filter_publicacoes_recebidas_no_periodo_NG,
    filter_publicacoes_tratadas_no_periodo_NG,
    get_media_tempo_tratamento_publicacoes_NG,
    get_pct_tratadas_mesmo_dia_publicacoes_NG,
    get_publicacoes_com_data_disponibilizacao_NG,
    get_publicacoes_comissionamento_por_funcionario_NG,
    get_publicacoes_cumpridas_mesmo_dia_chegada_NG,
    get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_NG,
    get_publicacoes_pendentes_NG,
    get_publicacoes_pendentes_zeradas_no_periodo_NG,
    get_publicacoes_recebidas_no_dia_NG,
    get_publicacoes_recebidas_periodo_NG,
    get_publicacoes_tratadas_no_dia_NG,
    get_publicacoes_tratadas_periodo_NG,
    group_publicacoes_cumprido_por_leitor_NG,
    group_publicacoes_pendentes_por_dias_atraso_NG,
    group_publicacoes_pendentes_por_leitor_NG,
    group_publicacoes_por_comarca_NG,
    group_publicacoes_por_materia_NG,
    group_publicacoes_por_orgao_NG,
    group_publicacoes_por_tipo_documento_NG,
    group_publicacoes_por_tribunal_NG,
    group_publicacoes_recebidas_por_dia_NG,
    group_publicacoes_tratadas_por_dia_NG,
    group_publicacoes_visualizadas_por_dia_NG,
    list_publicacoes_NG,
    resolve_dia_referencia_fim_periodo_NG,
)
from app.analyses.NG.recurso_NG import (
    META_PROVIMENTO_MENSAL_NG,
    _col_recursal_ng,
    _enriquecer_numero_processo_export_ng,
    _get_numero_processo_recursal_ng,
    filtrar_agendamentos_recursos_NG,
    filtrar_recursal_NG,
    filtrar_recursal_NG_por_processo_ids,
    get_decisoes_recursal_resumo_NG,
    get_entrada_recurso_NG,
    get_kpis_atividades_recursos_NG,
    get_kpis_atividades_recursos_por_prazo_NG,
    get_media_recursal_resolvidos_por_funcionario_NG,
    get_opcoes_filtros_atividades_lista_NG,
    get_opcoes_filtros_recursal_NG,
    get_ranking_juizes_recursal_NG,
    get_ranking_relatores_recursal_NG,
    get_recursal_resolvidos_por_dia_por_funcionario_NG,
    get_total_acordao_desfavoravel_recurso_NG,
    get_total_acordao_extincao_recurso_NG,
    get_total_acordao_favoravel_recurso_NG,
    get_total_acordao_parcial_retomada_recurso_NG,
    get_total_acordao_parcialmente_favoravel_recurso_NG,
    get_total_avr_retorno_recurso_cancelado_NG,
    get_total_parcialmente_procedente_recurso_NG,
    get_total_procedente_1g_recurso_NG,
    get_total_provimento_mensal_NG,
    get_total_recurso_NG,
    get_total_retorno_cr_recurso_cancelado_NG,
    get_total_sentenca_desfavoravel_recurso_NG,
    get_total_sentenca_extincao_recurso_NG,
    get_total_sentenca_favoravel_recurso_NG,
    get_total_sentenca_parcialmente_favoravel_recurso_NG,
    get_valor_causa_acordao_desfavoravel_recurso_NG,
    get_valor_causa_acordao_extincao_recurso_NG,
    get_valor_causa_acordao_favoravel_recurso_NG,
    get_valor_causa_acordao_parcial_retomada_recurso_NG,
    get_valor_causa_acordao_parcialmente_favoravel_recurso_NG,
    get_valor_causa_acordo_recurso_NG,
    get_valor_causa_sentenca_parcialmente_favoravel_recurso_NG,
    get_valor_causa_sentenca_parcialmente_procedente_recurso_NG,
    get_valor_causa_sentenca_procedente_1g_recurso_NG,
    get_valor_causa_sentenca_sentenca_desfavoravel_recurso_NG,
    get_valor_causa_sentenca_sentenca_extincao_recurso_NG,
    get_valor_causa_sentenca_sentenca_favoravel_recurso_NG,
    group_decisoes_recursal_NG,
    group_recursal_demandas_por_funcionario_NG,
    group_recursal_por_competencia_NG,
    group_recursal_por_materia_NG,
    group_recursal_por_status_1g_NG,
    group_recursal_por_status_2g_NG,
    group_recursal_por_subfase_NG,
    group_recursal_por_vara_NG,
    group_recursal_processos_por_atividade_NG,
    group_recursal_resolvidos_por_dia_NG,
    group_recursal_resolvidos_por_mes_NG,
    list_recursal_atividades_periodo_NG,
    processo_ids_recursal_de_agendamentos_recursos_NG,
    rotulo_decisao_recursal_export_NG,
    set_atividades_recursos_NG_catalogo,
)
from app.analyses.RJ.execucao_RJ import (
    _extrair_duracoes_dias_rj as _duracoes_execucao_rj,
    _filtrar_em_execucao_RJ as _filtrar_em_execucao_rj,
    _filtrar_entrada_execucao_RJ_no_periodo as _filtrar_entrada_execucao_no_periodo_rj,
    _get_ag_processo_id_rj,
    anotar_saida_execucao_export_RJ,
    filter_execucao_RJ_por_ano_ajuizamento,
    filter_execucao_RJ_por_comarca,
    filter_execucao_RJ_por_materia,
    filter_execucao_RJ_por_subfase,
    filter_execucao_RJ_por_uf,
    filtrar_agendamentos_diligencia_RJ,
    filtrar_agendamentos_diligencia_expedicao_alvara_RJ,
    filtrar_agendamentos_diligencia_por_colaborador_RJ,
    filtrar_agendamentos_diligencia_por_tipo_RJ,
    filtrar_agendamentos_execucao_RJ,
    filtrar_saida_execucao_export_RJ,
    get_atrasos_detalhamento_execucao_RJ,
    get_detalhe_valor_execucao_vazio_RJ,
    get_estoque_final_RJ,
    get_kpis_atividades_execucao_RJ,
    get_kpis_diligencias_expedicao_alvara_execucao_RJ,
    get_kpis_execucao_por_prazo_RJ,
    get_media_execucao_resolvidos_por_funcionario_RJ,
    get_media_execucao_resolvidos_por_funcionario_por_prazo_RJ,
    get_media_mensal_atividades_execucao_RJ,
    get_media_tempo_execucao_RJ,
    get_media_tempo_execucao_RJ_por_mes,
    get_mediana_tempo_execucao_RJ,
    get_opcoes_comarca_execucao_RJ,
    get_opcoes_filtros_execucao_RJ,
    get_opcoes_filtros_execucao_por_prazo_RJ,
    get_opcoes_materia_execucao_RJ,
    get_opcoes_subfase_execucao_RJ,
    get_opcoes_uf_execucao_RJ,
    get_taxa_atualizacao_execucao_RJ,
    get_taxa_recuperacao_execucao_RJ,
    get_total_diligencias_execucao_RJ,
    get_total_execucao_RJ,
    get_total_incontroverso_saida_periodo_RJ,
    get_total_saida_execucao_RJ_periodo,
    get_total_valor_execucao_vazio_RJ,
    get_tre_execucao_RJ_dax,
    get_valor_causa_total_execucao_RJ,
    get_valor_em_execucao_RJ,
    get_valor_execucao_saida_periodo_RJ,
    get_valor_honorarios_total_execucao_RJ,
    get_valor_incontroverso_saida_periodo_RJ,
    get_valor_remanescente_em_execucao_RJ,
    get_valor_ted_saida_execucao_RJ_periodo,
    group_alvaras_expedidos_por_dia_RJ,
    group_atividades_ativas_criadas_por_atividade_RJ,
    group_atividades_ativas_por_prazo_por_atividade_RJ,
    group_atividades_criadas_por_atividade_RJ,
    group_entrada_execucao_por_fluxo_cs_por_mes_RJ,
    group_estoque_execucao_RJ_por_mes,
    group_execucao_RJ_por_ano_ajuizamento,
    group_execucao_RJ_por_comarca,
    group_execucao_RJ_por_materia,
    group_execucao_RJ_por_subfase,
    group_execucao_demandas_por_funcionario_RJ,
    group_execucao_demandas_por_funcionario_completo_RJ,
    group_execucao_demandas_por_funcionario_por_prazo_RJ,
    group_execucao_demandas_por_funcionario_por_prazo_completo_RJ,
    group_execucao_diligencias_por_processo_RJ,
    group_execucao_nao_cumprido_por_motivo_RJ,
    group_execucao_processos_por_atividade_RJ,
    group_execucao_processos_por_atividade_por_prazo_RJ,
    group_execucao_resolvidos_por_dia_RJ,
    group_execucao_resolvidos_por_dia_por_prazo_RJ,
    group_quantidade_entrada_execucao_RJ_por_mes,
    group_quantidade_saida_execucao_RJ_por_mes,
    group_taxa_conclusao_por_funcionario_RJ,
    group_valor_entrada_execucao_RJ_por_mes,
    group_valor_execucao_RJ_por_comarca,
    group_valor_execucao_RJ_por_materia,
    group_valor_execucao_RJ_por_subfase,
    group_valor_execucao_saida_periodo_RJ_por_mes,
    group_valor_recuperado_por_funcionario_RJ,
    group_valor_remanescente_por_mes_RJ,
    group_valor_saida_execucao_RJ_por_mes,
    list_execucao_atividades_abertas_RJ,
    list_execucao_atividades_periodo_RJ,
    list_execucao_atividades_por_prazo_periodo_RJ,
    list_processos_alvara_expedido_RJ,
    list_processos_diligencia_expedicao_alvara_cumprida_execucao_RJ,
)
from app.analyses.RJ.execucao_acordos_RJ import (
    _extrair_duracoes_dias as _duracoes_execucao_acordos_rj,
    _filtrar_em_execucao_acordos_RJ,
    _filtrar_entrada_execucao_acordos_RJ_no_periodo,
    _filtrar_saida_execucao_acordos_RJ_no_periodo,
    filter_execucao_acordos_RJ_por_ano_ajuizamento,
    filter_execucao_acordos_RJ_por_comarca,
    filter_execucao_acordos_RJ_por_materia,
    filter_execucao_acordos_RJ_por_processo,
    filter_execucao_acordos_RJ_por_sentenca,
    filter_execucao_acordos_RJ_por_subfase,
    filter_execucao_acordos_RJ_por_tipo_acao,
    filter_execucao_acordos_RJ_por_uf,
    filtrar_agendamentos_diligencia_acordos_RJ,
    filtrar_agendamentos_diligencia_expedicao_alvara_acordos_RJ,
    filtrar_agendamentos_diligencia_por_colaborador_acordos_RJ,
    filtrar_agendamentos_diligencia_por_tipo_acordos_RJ,
    filtrar_agendamentos_execucao_acordos_RJ,
    get_atrasos_detalhamento_execucao_acordos_RJ,
    get_detalhe_valor_alcada_final_vazio_RJ,
    get_estoque_final_execucao_acordos_RJ,
    get_kpis_atividades_execucao_acordos_RJ,
    get_kpis_diligencias_expedicao_alvara_acordos_RJ,
    get_kpis_execucao_por_prazo_acordos_RJ,
    get_media_execucao_resolvidos_por_funcionario_acordos_RJ,
    get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_RJ,
    get_media_mensal_atividades_execucao_acordos_RJ,
    get_media_tempo_execucao_acordos_RJ,
    get_media_tempo_execucao_acordos_RJ_por_mes,
    get_mediana_tempo_execucao_acordos_RJ,
    get_opcoes_comarca_execucao_acordos_RJ,
    get_opcoes_filtros_execucao_acordos_RJ,
    get_opcoes_filtros_execucao_por_prazo_acordos_RJ,
    get_opcoes_materia_execucao_acordos_RJ,
    get_opcoes_subfase_execucao_acordos_RJ,
    get_opcoes_uf_execucao_acordos_RJ,
    get_total_diligencias_execucao_acordos_RJ,
    get_total_entrada_execucao_acordos_RJ_periodo,
    get_total_execucao_acordos_RJ,
    get_total_processos_fechamento_acordo_RJ,
    get_total_saida_execucao_acordos_RJ_periodo,
    get_total_valor_alcada_final_vazio_RJ,
    get_tre_execucao_acordos_RJ_dax,
    get_valor_alcada_final_total_execucao_acordos_RJ,
    get_valor_entrada_execucao_acordos_RJ_periodo,
    get_valor_saida_execucao_acordos_RJ_periodo,
    get_valor_ted_saida_execucao_acordos_RJ_periodo,
    group_alvaras_expedidos_acordos_por_dia_RJ,
    group_atividades_ativas_criadas_por_atividade_acordos_RJ,
    group_atividades_ativas_por_prazo_por_atividade_acordos_RJ,
    group_estoque_execucao_acordos_por_mes_RJ,
    group_execucao_acordos_RJ_por_ano_ajuizamento,
    group_execucao_acordos_RJ_por_comarca,
    group_execucao_acordos_RJ_por_materia,
    group_execucao_acordos_RJ_por_sentenca,
    group_execucao_acordos_RJ_por_subfase,
    group_execucao_acordos_RJ_por_tipo_acao,
    group_execucao_acordos_diligencias_por_processo_RJ,
    group_execucao_demandas_por_funcionario_acordos_RJ,
    group_execucao_demandas_por_funcionario_completo_acordos_RJ,
    group_execucao_demandas_por_funcionario_por_prazo_acordos_RJ,
    group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_RJ,
    group_execucao_nao_cumprido_por_motivo_acordos_RJ,
    group_execucao_processos_por_atividade_acordos_RJ,
    group_execucao_processos_por_atividade_por_prazo_acordos_RJ,
    group_execucao_resolvidos_por_dia_acordos_RJ,
    group_execucao_resolvidos_por_dia_por_prazo_acordos_RJ,
    group_fechamento_acordo_por_subfase_RJ,
    group_quantidade_entrada_execucao_acordos_RJ_por_mes,
    group_quantidade_saida_execucao_acordos_RJ_por_mes,
    group_valor_entrada_execucao_acordos_RJ_por_mes,
    group_valor_execucao_acordos_RJ_por_comarca,
    group_valor_execucao_acordos_RJ_por_materia,
    group_valor_execucao_acordos_RJ_por_subfase,
    group_valor_fechamento_acordo_por_subfase_RJ,
    group_valor_saida_execucao_acordos_RJ_por_mes,
    list_execucao_acordos_RJ_lista_entrada,
    list_execucao_acordos_RJ_lista_saida,
    list_execucao_acordos_RJ_lista_total,
    list_execucao_atividades_periodo_acordos_RJ,
    list_execucao_atividades_por_prazo_periodo_acordos_RJ,
    list_processos_alvara_expedido_acordos_RJ,
    list_processos_diligencia_expedicao_alvara_cumprida_acordos_RJ,
)
from app.analyses.RJ.publicacoes_RJ import (
    build_publicacoes_agendamento_apos_finalizacao_RJ,
    filter_publicacoes_por_atividade_agendamento_RJ,
    filter_publicacoes_por_documento_RJ,
    filter_publicacoes_por_leitor_RJ,
    filter_publicacoes_por_materia_RJ,
    filter_publicacoes_por_orgao_RJ,
    filter_publicacoes_por_setor_agendamento_RJ,
    filter_publicacoes_por_status_agendamento_RJ,
    filter_publicacoes_por_tribunal_RJ,
    filter_publicacoes_recebidas_no_periodo_RJ,
    filter_publicacoes_tratadas_no_periodo_RJ,
    get_media_tempo_tratamento_publicacoes_RJ,
    get_pct_tratadas_mesmo_dia_publicacoes_RJ,
    get_publicacoes_com_data_disponibilizacao_RJ,
    get_publicacoes_comissionamento_por_funcionario_RJ,
    get_publicacoes_cumpridas_mesmo_dia_chegada_RJ,
    get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_RJ,
    get_publicacoes_pendentes_RJ,
    get_publicacoes_pendentes_zeradas_no_periodo_RJ,
    get_publicacoes_recebidas_no_dia_RJ,
    get_publicacoes_recebidas_periodo_RJ,
    get_publicacoes_tratadas_no_dia_RJ,
    get_publicacoes_tratadas_periodo_RJ,
    group_publicacoes_cumprido_por_leitor_RJ,
    group_publicacoes_pendentes_por_dias_atraso_RJ,
    group_publicacoes_pendentes_por_leitor_RJ,
    group_publicacoes_por_comarca_RJ,
    group_publicacoes_por_materia_RJ,
    group_publicacoes_por_orgao_RJ,
    group_publicacoes_por_tipo_documento_RJ,
    group_publicacoes_por_tribunal_RJ,
    group_publicacoes_recebidas_por_dia_RJ,
    group_publicacoes_tratadas_por_dia_RJ,
    group_publicacoes_visualizadas_por_dia_RJ,
    list_publicacoes_RJ,
    resolve_dia_referencia_fim_periodo_RJ,
)
from app.analyses.RJ.recurso_RJ import (
    META_PROVIMENTO_MENSAL_RJ,
    _col_recursal_rj,
    _enriquecer_numero_processo_export_rj,
    _get_numero_processo_recursal_rj,
    filtrar_agendamentos_recursos_RJ,
    filtrar_recursal_RJ,
    filtrar_recursal_RJ_por_processo_ids,
    get_decisoes_recursal_resumo_RJ,
    get_entrada_recurso_RJ,
    get_extintos_2g_recursal_RJ,
    get_kpis_atividades_recursos_RJ,
    get_kpis_atividades_recursos_por_prazo_RJ,
    get_media_recursal_resolvidos_por_funcionario_RJ,
    get_opcoes_filtros_atividades_lista_RJ,
    get_opcoes_filtros_recursal_RJ,
    get_ranking_juizes_recursal_RJ,
    get_ranking_relatores_recursal_RJ,
    get_recursal_resolvidos_por_dia_por_funcionario_RJ,
    get_total_acordao_desfavoravel_recurso_RJ,
    get_total_acordao_extincao_recurso_RJ,
    get_total_acordao_favoravel_recurso_RJ,
    get_total_acordao_parcial_retomada_recurso_RJ,
    get_total_acordao_parcialmente_favoravel_recurso_RJ,
    get_total_avr_retorno_recurso_cancelado_RJ,
    get_total_parcialmente_procedente_recurso_RJ,
    get_total_procedente_1g_recurso_RJ,
    get_total_provimento_mensal_RJ,
    get_total_recurso_RJ,
    get_total_retorno_cr_recurso_cancelado_RJ,
    get_total_sentenca_desfavoravel_recurso_RJ,
    get_total_sentenca_extincao_recurso_RJ,
    get_total_sentenca_favoravel_recurso_RJ,
    get_total_sentenca_parcialmente_favoravel_recurso_RJ,
    get_valor_causa_acordao_desfavoravel_recurso_RJ,
    get_valor_causa_acordao_extincao_recurso_RJ,
    get_valor_causa_acordao_favoravel_recurso_RJ,
    get_valor_causa_acordao_parcial_retomada_recurso_RJ,
    get_valor_causa_acordao_parcialmente_favoravel_recurso_RJ,
    get_valor_causa_acordo_recurso_RJ,
    get_valor_causa_sentenca_parcialmente_favoravel_recurso_RJ,
    get_valor_causa_sentenca_parcialmente_procedente_recurso_RJ,
    get_valor_causa_sentenca_procedente_1g_recurso_RJ,
    get_valor_causa_sentenca_sentenca_desfavoravel_recurso_RJ,
    get_valor_causa_sentenca_sentenca_extincao_recurso_RJ,
    get_valor_causa_sentenca_sentenca_favoravel_recurso_RJ,
    group_decisoes_recursal_RJ,
    group_recursal_demandas_por_funcionario_RJ,
    group_recursal_por_competencia_RJ,
    group_recursal_por_materia_RJ,
    group_recursal_por_status_1g_RJ,
    group_recursal_por_status_2g_RJ,
    group_recursal_por_subfase_RJ,
    group_recursal_por_vara_RJ,
    group_recursal_processos_por_atividade_RJ,
    group_recursal_resolvidos_por_dia_RJ,
    group_recursal_resolvidos_por_mes_RJ,
    list_recursal_atividades_periodo_RJ,
    processo_ids_recursal_de_agendamentos_recursos_RJ,
    rotulo_decisao_recursal_export_RJ,
    set_atividades_recursos_RJ_catalogo,
)
from app.utils import (
    parse_date_from_db,
)
from datetime import (
    date,
    datetime,
)
from fastapi import (
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import (
    StreamingResponse,
)
import csv
import io
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
from app.analyses.situacao_processo import aplicar_filtro_situacao_processo
from app.sources import SourceUnavailable  # V2: fonte fora do ar vira 503 na casca

# V2: fonte do banco de origem (no lugar de fetch_data_with_cache da v1). A casca passa a fonte do
# dashboard (SourceFetcher, já com o cache de 5 min) por `usar_fonte`; o recorte de situação do processo
# é o mesmo que a v1 aplica em fetch_data_with_cache.
_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico_lexflow")

def usar_fonte(fonte):
    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""
    return _fonte_ctx.set(fonte)


async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:
    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))


# V2: v1 dashboard_routes.py:3021 -> fetch_data_with_cache('execucao_LA', ...)
async def fetch_execucao() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_LA')


# V2: v1 dashboard_routes.py:3066 -> fetch_data_with_cache('agendamentos_setor_execucao_NG', ...)
async def fetch_agendamentos_setor_execucao_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_NG')


# V2: v1 dashboard_routes.py:2870 -> fetch_data_with_cache('execucao_LA', ...)
async def fetch_execucao_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_LA')


# V2: v1 dashboard_routes.py:2925 -> fetch_data_with_cache('agendamentos_setor_execucao_LA', ...)
async def fetch_agendamentos_setor_execucao_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_LA')


# V2: v1 dashboard_routes.py:3024 -> fetch_data_with_cache('execucao_RJ', ...)
async def fetch_execucao_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_RJ')


# V2: v1 dashboard_routes.py:3090 -> fetch_data_with_cache('agendamentos_setor_execucao_LA_RJ', ...)
async def fetch_agendamentos_setor_execucao_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_LA_RJ')


# V2: v1 dashboard_routes.py:3027 -> fetch_data_with_cache('execucao_acordos_NG', ...)
async def fetch_execucao_acordos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_acordos_NG')


# V2: v1 dashboard_routes.py:3036 -> fetch_data_with_cache('agendamentos_fechamento_acordos_NG', ...)
async def fetch_agendamentos_fechamento_acordos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_fechamento_acordos_NG')


# V2: v1 dashboard_routes.py:3072 -> fetch_data_with_cache('agendamentos_setor_execucao_acordos_NG', ...)
async def fetch_agendamentos_setor_execucao_acordos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_acordos_NG')


# V2: v1 dashboard_routes.py:3030 -> fetch_data_with_cache('execucao_acordos_LA', ...)
async def fetch_execucao_acordos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_acordos_LA')


# V2: v1 dashboard_routes.py:3054 -> fetch_data_with_cache('agendamentos_fechamento_acordos_LA', ...)
async def fetch_agendamentos_fechamento_acordos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_fechamento_acordos_LA')


# V2: v1 dashboard_routes.py:3078 -> fetch_data_with_cache('agendamentos_setor_execucao_acordos_LA', ...)
async def fetch_agendamentos_setor_execucao_acordos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_acordos_LA')


# V2: v1 dashboard_routes.py:3033 -> fetch_data_with_cache('execucao_acordos_RJ', ...)
async def fetch_execucao_acordos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_acordos_RJ')


# V2: v1 dashboard_routes.py:3060 -> fetch_data_with_cache('agendamentos_fechamento_acordos_RJ', ...)
async def fetch_agendamentos_fechamento_acordos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_fechamento_acordos_RJ')


# V2: v1 dashboard_routes.py:3084 -> fetch_data_with_cache('agendamentos_setor_execucao_acordos_RJ', ...)
async def fetch_agendamentos_setor_execucao_acordos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_acordos_RJ')


# V2: v1 dashboard_routes.py:2882 -> fetch_data_with_cache('setor_recurso_NG', ...)
async def fetch_recursal_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_recurso_NG')


# V2: v1 dashboard_routes.py:2885 -> fetch_data_with_cache('agendamentos_setor_recursos_NG', ...)
async def fetch_agendamentos_setor_recursos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_recursos_NG')


# V2: v1 dashboard_routes.py:2891 -> fetch_data_with_cache('atividades_setor_recursos_NG', ...)
async def fetch_atividades_setor_recursos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('atividades_setor_recursos_NG')


# V2: v1 dashboard_routes.py:2873 -> fetch_data_with_cache('setor_recurso', ...)
async def fetch_recursal_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_recurso')


# V2: v1 dashboard_routes.py:2876 -> fetch_data_with_cache('agendamentos_setor_recursos_LA', ...)
async def fetch_agendamentos_setor_recursos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_recursos_LA')


# V2: v1 dashboard_routes.py:2912 -> fetch_data_with_cache('atividades_setor_recursos_LA', ...)
async def fetch_atividades_setor_recursos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('atividades_setor_recursos_LA')


# V2: v1 dashboard_routes.py:2897 -> fetch_data_with_cache('setor_recurso_RJ', ...)
async def fetch_recursal_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_recurso_RJ')


# V2: v1 dashboard_routes.py:2900 -> fetch_data_with_cache('agendamentos_setor_recursos_RJ', ...)
async def fetch_agendamentos_setor_recursos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_recursos_RJ')


# V2: v1 dashboard_routes.py:2906 -> fetch_data_with_cache('atividades_setor_recursos_RJ', ...)
async def fetch_atividades_setor_recursos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('atividades_setor_recursos_RJ')


# V2: v1 dashboard_routes.py:3102 -> fetch_data_with_cache('controle_processo_todas_situacoes', ...)
async def fetch_controle_processo_todas_situacoes() -> List[Dict[str, Any]]:
    return await _fetch_v2('controle_processo_todas_situacoes')


# V2: v1 dashboard_routes.py:3099 -> fetch_data_with_cache('controle_processo', ...)
async def fetch_controle_processo_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('controle_processo')


# V2: v1 dashboard_routes.py:3105 -> fetch_data_with_cache('log_subfase_processual', ...)
async def fetch_log_subfase_processual() -> List[Dict[str, Any]]:
    return await _fetch_v2('log_subfase_processual')


# V2: v1 dashboard_routes.py:3096 -> fetch_data_with_cache('controle_processo', ...)
async def fetch_controle_processo_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('controle_processo')


# V2: v1 dashboard_routes.py:2846 -> fetch_data_with_cache('publicacoes_NG', ...)
async def fetch_publicacoes_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('publicacoes_NG')


# V2: v1 dashboard_routes.py:3015 -> fetch_data_with_cache('agendamentos_todos_setores_NG', ...)
async def fetch_agendamentos_todos_setores_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_todos_setores_NG')


# V2: v1 dashboard_routes.py:2843 -> fetch_data_with_cache('publicacoes_LA', ...)
async def fetch_publicacoes_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('publicacoes_LA')


# V2: v1 dashboard_routes.py:3009 -> fetch_data_with_cache('agendamentos_todos_setores_LA', ...)
async def fetch_agendamentos_todos_setores_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_todos_setores_LA')


# V2: v1 dashboard_routes.py:2849 -> fetch_data_with_cache('publicacoes_LA_RJ', ...)
async def fetch_publicacoes_LA_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('publicacoes_LA_RJ')


# V2: v1 dashboard_routes.py:2852 -> fetch_data_with_cache('agendamentos_todos_setores_LA_RJ', ...)
async def fetch_agendamentos_todos_setores_LA_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_todos_setores_LA_RJ')


# v1: dashboard_routes.py:2280
logger = logging.getLogger(__name__)


# v1: dashboard_routes.py:3151
def _resolve_date_range(
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Optional[date], Optional[date]]:
    """Normaliza o intervalo: se from_date sem to_date, usa hoje como fim."""
    if from_date and not to_date:
        return from_date, date.today()
    return from_date, to_date


# v1: dashboard_routes.py:3161
def _to_date(value: Any) -> Optional[date]:
    """Converte valor do banco para date, descartando None e tipos inválidos."""
    if value is None:
        return None
    parsed = parse_date_from_db(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


# v1: dashboard_routes.py:3173
def _in_range(d: date, from_date: Optional[date], to_date: Optional[date]) -> bool:
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    if to_date:
        return d <= to_date
    return True


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
    if not from_date and not to_date:
        return data

    filtered = []
    for item in data:
        for col in columns:
            raw = item.get(col) or item.get(col.lower())
            if raw is None:
                continue
            d = _to_date(raw)
            if d is None:
                continue
            if _in_range(d, from_date, to_date):
                filtered.append(item)
                break
    return filtered


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


# v1: dashboard_routes.py:3336
def _dedup_por_processo_id(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove linhas duplicadas por ``id`` de processo.

    A query ``controle_processo``/``controle_processo_todas_situacoes`` faz LEFT JOIN em
    ``adverso_processo`` (parte adversa), que pode ter mais de uma linha por processo —
    sem dedup, processos com múltiplas partes adversas são contados mais de uma vez.
    """
    vistos: set = set()
    unicos: List[Dict[str, Any]] = []
    for row in rows:
        pid = row.get("id")
        if pid is not None:
            if pid in vistos:
                continue
            vistos.add(pid)
        unicos.append(row)
    return unicos


# v1: dashboard_routes.py:3930
class ChartDataPoint(BaseModel):
    name: str
    value: float
    percent: Optional[float] = None
    valor_causa: Optional[float] = None
    valor_sentenca: Optional[float] = None
    valor_execucao: Optional[float] = None
    id_1g: Optional[int] = None
    id_2g: Optional[int] = None
    tipo: Optional[str] = None
    tempo_medio_dias: Optional[float] = None
    uf: Optional[str] = None
    concluidos: Optional[float] = None
    abertas: Optional[float] = None


# v1: dashboard_routes.py:3946
class ProcessoDadoFaltando(BaseModel):
    """Um processo com um campo faltando (alimenta o alerta clicável "Atenção" dos
    dashboards de Execução/Execução Acordos/Julgados — número do processo + qual
    informação falta, pra o usuário ir preencher no sistema de origem)."""

    numero_processo: str
    campo: str


# v1: dashboard_routes.py:3955
class InvestimentoCliquesLeadsPoint(BaseModel):
    name: str
    investimento: float
    cliques: int
    leads: int


# v1: dashboard_routes.py:3962
class RubricaCampanhaPoint(BaseModel):
    name: str
    ra: int
    ng: int


# v1: dashboard_routes.py:3968
class NpsRespostaRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    av_confianca: Optional[int] = None
    av_nivel_info: Optional[int] = None
    av_tempo_resposta: Optional[int] = None
    feedback_positivo: str
    feedback_melhoria: str
    etapa_preocupacao: str
    comentario: str


# v1: dashboard_routes.py:3984
class NpsFeedbackMelhoriaRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    feedback_melhoria: str


# v1: dashboard_routes.py:3994
class NpsFeedbackPositivoRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    feedback_positivo: str


# v1: dashboard_routes.py:4004
class NpsComentarioRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    comentario: str


# v1: dashboard_routes.py:4014
class RecursalRankingMagistradoRow(BaseModel):
    name: str
    initials: str
    total_casos: int
    taxa_sucesso: float
    fav: int
    des: int
    outros: int
    percent_fav: float
    percent_des: float
    percent_outros: float


# v1: dashboard_routes.py:4027
class JulgadosSentencaListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    fase: str
    subfase: str
    status_1g: str
    uf: str
    juiz: str
    data_sentenca: Optional[str] = None
    status_sentenca_embargos: str
    data_sentenca_embargos: Optional[str] = None


# v1: dashboard_routes.py:4040
class JulgadosAcordaoListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    fase: str
    subfase: str
    status_2g: str
    uf: str
    relator: str
    data_acordao: Optional[str] = None
    status_acordao_embargos: str
    data_acordao_embargos: Optional[str] = None


# v1: dashboard_routes.py:4053
class ExecucaoAcordosListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    uf: str
    data_execucao: Optional[str] = None
    valor_execucao: Optional[float] = None
    subfase: str


# v1: dashboard_routes.py:4062
class RecursalAtividadeTarefaRow(BaseModel):
    id: int
    status: str
    descricao: str
    pessoa_setor: str
    funcionario: str
    atividade: str
    prazo: Optional[str] = None
    em_andamento: bool = False
    vencida: bool = False
    vence_hoje: bool = False
    concluida: bool = False
    funcionario_atribuido: Optional[str] = None
    funcionario_encerramento: Optional[str] = None
    criado_em: Optional[str] = None
    concluido_em: Optional[str] = None
    operacao: Optional[str] = None
    encerrado_pelo_responsavel: Optional[bool] = None
    numero_processo: Optional[str] = None
    valor_execucao: Optional[float] = None
    valor_sentenca: Optional[float] = None
    valor_acordao: Optional[float] = None


# v1: dashboard_routes.py:4086
class DilacaoPorFuncionarioRow(BaseModel):
    funcionario: str
    qtd_dilacoes: int
    total_encerrados: int
    qtd_resolvidos: int
    taxa_dilacao: float


# v1: dashboard_routes.py:4094
class EmendasManifestacoesResolvidosPorUfRow(BaseModel):
    uf: str
    qtd_manifestacao: int
    qtd_dilacao: int
    qtd_total: int


# v1: dashboard_routes.py:4101
class EmendasManifestacoesComissaoRow(BaseModel):
    funcionario: str
    agenda_finalizada: int
    agenda_total: int
    agenda_percentual: float
    elegivel: bool
    faixa: Optional[str] = None
    qtd_manifestacao: int
    valor_manifestacao: float
    qtd_x_valor_manifestacao: float
    qtd_dilacao: int
    valor_dilacao: float
    qtd_x_valor_dilacao: float
    valor_comissao: float
    resolvidos_por_uf: Optional[List[EmendasManifestacoesResolvidosPorUfRow]] = None


# v1: dashboard_routes.py:4118
class RecursalAtividadesListaFiltrosOpcoes(BaseModel):
    funcionarios: List[str]
    atividades: List[str]
    status: List[str]
    situacoes: List[Dict[str, str]]


# v1: dashboard_routes.py:4125
class ExecucaoAtrasoBucket(BaseModel):
    dias: int
    label: str
    descricao: str
    count: int
    pct: float


# v1: dashboard_routes.py:4133
class ExecucaoAtrasosDetalhamento(BaseModel):
    total: int
    buckets: List[ExecucaoAtrasoBucket]


# v1: dashboard_routes.py:4138
class RubricaTotalRow(BaseModel):
    rubrica: str
    acoes: int
    valor_am: float
    total: float


# v1: dashboard_routes.py:4145
class ComissionamentoOrgDocRow(BaseModel):
    funcionario: str
    qtd_resolvidos: int
    valor_causa_gerado: float
    valor_comissao: float


# v1: dashboard_routes.py:4152
class ComissionamentoProtocoloRow(BaseModel):
    funcionario: str
    qtd_protocolados: int
    comissao_unitaria: Optional[float] = None
    valor_comissao: float


# v1: dashboard_routes.py:4159
class ComissionamentoPeticionamentoRow(BaseModel):
    funcionario: str
    qtd_acoes_massa: int
    valor_acoes_massa: float
    qtd_x_valor_massa: float
    qtd_acoes_especificas: int
    valor_acoes_especificas: float
    qtd_x_valor_especificas: float
    taxa_resolvidos: Optional[float] = None
    valor_comissao: float


# v1: dashboard_routes.py:4171
class ComissionamentoPendenciaRow(BaseModel):
    funcionario: str
    taxa_resolvido: Optional[float] = None
    taxa_cancelamento: Optional[float] = None
    qtd_resolvido: int
    valor: float
    qtd_x_valor: float
    comissao: float


# v1: dashboard_routes.py:4181
class ComissionamentoPublicacaoRow(BaseModel):
    funcionario: str
    qtd_lidas: int
    qtd_certas: int
    qtd_erradas: int
    valor_certa: float
    valor_errada: float
    comissao: float


# v1: dashboard_routes.py:4191
class ComissionamentoAndamentoRow(BaseModel):
    funcionario: str
    media_avaliacao: Optional[float] = None
    qtd_atendimentos: int
    valor_unitario: float
    valor_comissao: float


# v1: dashboard_routes.py:4199
class ComissionamentoComercialRow(BaseModel):
    atendente: str
    acoes: int
    comissao_base: float
    valor_fm: float
    proporcional_am_pa: float
    proporcional_pb: float
    comissao_com_fm: float


# v1: dashboard_routes.py:4209
class ComissionamentoComercialLARow(BaseModel):
    atendente: str
    acoes: int
    comissao_base: float
    valor_fm: float
    comissao_com_fm: float


# v1: dashboard_routes.py:4217
class TotalLeadsPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4222
class TotalClientesFechadosPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4227
class TaxaFechamentoGeralPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4232
class TotalLeadsCampanhaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4237
class TotalClientesFechadosCampanhaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4242
class TaxaFechamentoCampanhaPorCliente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4247
class TotalLeadsIndicacaoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4252
class TaxaFechamentoIndicacaoAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4257
class TotalClientesFechadosIndicacaoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4262
class TotalLeadsIndicacaoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4267
class TotalClientesFechadosIndicacaoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4272
class TaxaFechamentoIndicacaoPassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4277
class TotalLeadsRetornoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4282
class TotalClientesFechadosRetornoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4287
class TaxaFechamentoRetornoAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4292
class TotalLeadsRetornoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4297
class TotalClientesFechadosRetornoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4302
class TaxaFechamentoRetornoPassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4307
class TotalLeadsResgateAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4312
class TotalClientesFechadosResgateAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4317
class TaxaFechamentoResgateAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4322
class TotalLeadsResgatePassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4327
class TotalClientesFechadosResgatePassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4332
class TaxaFechamentoResgatePassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4371
class DashboardStats(BaseModel):
    # Tickets
    total_tickets: Optional[int] = None
    tickets_ag_atendimento: Optional[int] = None
    tickets_atendimento: Optional[int] = None
    total_encerrados: Optional[int] = None
    tickets_cancelados: Optional[int] = None
    tickets_reprovados: Optional[int] = None
    duracao_atendimento: Optional[float] = None
    taxa_resolucao: Optional[float] = None
    total_tickets_periodo_anterior: Optional[int] = None
    tickets_abertos: Optional[int] = None
    tickets_resolvidos: Optional[int] = None
    tickets_hoje: Optional[int] = None
    tickets_semana: Optional[int] = None
    tickets_mes: Optional[int] = None

    # Andamento Processual
    total_andamento_processual: Optional[int] = None
    andamento_processual_resolvidos: Optional[int] = None
    andamento_processual_nao_resolvidos: Optional[int] = None
    media_avaliacao: Optional[float] = None
    taxa_resolvidos: Optional[float] = None
    taxa_nao_resolvidos: Optional[float] = None
    media_espera: Optional[float] = None
    mediana_espera: Optional[float] = None
    media_atendimento: Optional[float] = None
    mediana_atendimento: Optional[float] = None
    funcionarios_andamento_processual: Optional[List[str]] = None
    funcionarios_andamento_filtro: Optional[List[str]] = None
    funcionario_andamento_filtro: Optional[str] = None
    funcionarios_filtro: Optional[List[str]] = None

    # Comercial Geral
    clientes_campanha_RA: Optional[int] = None
    clientes_campanha_NG: Optional[int] = None
    clientes_indicacao: Optional[int] = None
    clientes_redes_sociais: Optional[int] = None
    clientes_retorno: Optional[int] = None
    clientes_site: Optional[int] = None
    clientes_resgate: Optional[int] = None
    clientes_parceiros_externos: Optional[int] = None
    clientes_todos: Optional[int] = None
    clientes_cancelados: Optional[int] = None
    acoes_fechadas: Optional[int] = None
    total_rubricas_reunidas_fechadas: Optional[int] = None
    total_rubricas_reunidas_fechadas_LA: Optional[int] = None
    taxa_aproveitamento: Optional[float] = None
    comparativo_clientes_campanha_NG: Optional[float] = None
    comparativo_clientes_campanha_RA: Optional[float] = None
    comparativo_clientes_redes_sociais: Optional[float] = None
    comparativo_clientes_indicacao: Optional[float] = None
    comparativo_clientes_retorno: Optional[float] = None
    comparativo_clientes_resgate: Optional[float] = None
    comparativo_clientes_site: Optional[float] = None
    comparativo_clientes_parceiros_externos: Optional[float] = None
    comparativo_acoes_fechadas: Optional[float] = None
    acoes_fechadas_periodo_anterior: Optional[float] = None
    comparativo_clientes_todos: Optional[float] = None
    clientes_todos_periodo_anterior: Optional[float] = None
    comparativo_clientes_cancelados: Optional[float] = None
    comparativo_taxa_aproveitamento: Optional[float] = None
    valor_causa_confeccionado: Optional[float] = None
    ticket_medio_confeccionado: Optional[float] = None
    ticket_medio_protocolado: Optional[float] = None
    comparativo_ticket_medio_protocolado: Optional[float] = None
    tempo_medio_contratacao_protocolo: Optional[float] = None
    mediana_tempo_contratacao_protocolo: Optional[float] = None
    comparativo_tempo_medio_contratacao_protocolo: Optional[float] = None
    comparativo_mediana_tempo_contratacao_protocolo: Optional[float] = None
    comissao_base: Optional[float] = None
    atendentes_comerciais: Optional[List[str]] = None
    atendentes_comerciais_filtro: Optional[List[str]] = None
    atendente_comercial_filtro: Optional[str] = None
    funcionario_filtro: Optional[str] = None
    ufs_comercial_ng_opcoes: Optional[List[str]] = None
    uf_comercial_ng_filtro: Optional[str] = None
    segmentos_comercial_ng_opcoes: Optional[List[str]] = None
    segmentos_comercial_la_opcoes: Optional[List[str]] = None
    segmento_comercial_ng_filtro: Optional[str] = None
    segmento_comercial_la_filtro: Optional[str] = None
    area_atuacao_id_filtro: Optional[Union[int, List[int]]] = None

    # Actions NG
    total_leads: Optional[int] = None
    qtde_total_leads_anuncio_RA: Optional[int] = None
    qtde_total_leads_anuncio_NG: Optional[int] = None
    taxa_leads_geral: Optional[float] = None
    taxa_leads_anuncio_RA: Optional[float] = None
    taxa_leads_anuncio_NG: Optional[float] = None
    comparativo_leads_geral: Optional[float] = None
    comparativo_leads_anuncio_RA: Optional[float] = None
    comparativo_leads_anuncio_NG: Optional[float] = None
    comparativo_taxa_leads_geral: Optional[float] = None
    comparativo_taxa_leads_anuncio_RA: Optional[float] = None
    comparativo_taxa_leads_anuncio_NG: Optional[float] = None

    # Actions LA
    total_leads_LA: Optional[int] = None
    total_leads_anuncio_LA: Optional[int] = None
    taxa_leads_geral_LA: Optional[float] = None
    taxa_leads_anuncio_LA: Optional[float] = None

    # Protocolo NG
    protocolos_resolvidos: Optional[int] = None
    protocolados_de_reajuizamento: Optional[int] = None
    nao_protocolados: Optional[int] = None
    nao_protocolados_de_reajuizamento: Optional[int] = None
    valor_causa_protocolo_novo: Optional[float] = None
    comparativo_protocolos_resolvidos: Optional[float] = None
    protocolos_resolvidos_periodo_anterior: Optional[float] = None
    comparativo_valor_causa_protocolo: Optional[float] = None
    valor_causa_protocolo_periodo_anterior: Optional[float] = None
    valor_causa_protocolo_2026: Optional[float] = None
    meta_anual_comercial: Optional[float] = None
    media_tempo_protocolado: Optional[float] = None
    mediana_tempo_protocolado: Optional[float] = None
    comparativo_nao_protocolados: Optional[float] = None
    comparativo_tempo_medio_protocolos_resolvidos: Optional[float] = None
    fator_multiplicador: Optional[float] = None
    valor_por_estado_am_pa: Optional[float] = None
    valor_por_estado_pb: Optional[float] = None
    proporcional_am_pa: Optional[float] = None
    proporcional_pb: Optional[float] = None
    comissao_com_fm: Optional[float] = None
    ufs_protocolo_opcoes: Optional[List[str]] = None
    uf_protocolo_filtro: Optional[List[str]] = None
    ufs_peticionamento_opcoes: Optional[List[str]] = None
    uf_peticionamento_filtro: Optional[str] = None
    ufs_org_doc_opcoes: Optional[List[str]] = None
    uf_org_doc_filtro: Optional[str] = None
    ufs_pendencias_opcoes: Optional[List[str]] = None
    uf_pendencias_filtro: Optional[str] = None
    ufs_peticionamento_LA_opcoes: Optional[List[str]] = None
    uf_peticionamento_LA_filtro: Optional[str] = None
    ufs_org_doc_LA_opcoes: Optional[List[str]] = None
    uf_org_doc_LA_filtro: Optional[str] = None
    ufs_pendencia_LA_opcoes: Optional[List[str]] = None
    uf_pendencia_LA_filtro: Optional[str] = None

    # Organização de Documentos NG
    resolvidos_total: Optional[int] = None
    organizados_manualmente: Optional[int] = None
    organizados_e_peticionados_automaticamente: Optional[int] = None
    nao_organizados: Optional[int] = None
    cancelados: Optional[int] = None
    retorno_pet: Optional[int] = None
    retorno_pendencia: Optional[int] = None
    resolvidos_reajuizamento: Optional[int] = None
    comparativo_resolvidos_total: Optional[float] = None
    comparativo_organizados_manualmente: Optional[float] = None
    comparativo_resolvidos_reajuizamento: Optional[float] = None
    comparativo_organizados_e_peticionados_automaticamente: Optional[float] = None
    comparativo_cancelados: Optional[float] = None
    media_tempo_resolvidos: Optional[float] = None
    mediana_tempo_resolvidos: Optional[float] = None
    comparativo_tempo_medio_resolvidos_org_doc: Optional[float] = None

    # Organização de Documentos LA
    total_organizados_LA: Optional[int] = None
    total_organizados_manualmente_LA: Optional[int] = None
    total_organizados_automaticamente_LA: Optional[int] = None
    nao_organizados_LA: Optional[int] = None
    retorno_pendencia_LA: Optional[int] = None
    cancelados_LA: Optional[int] = None
    media_tempo_resolvidos_LA: Optional[float] = None
    mediana_tempo_resolvidos_LA: Optional[float] = None
    comparativo_resolvidos_total_LA: Optional[float] = None
    comparativo_organizados_manualmente_LA: Optional[float] = None
    comparativo_organizados_automaticamente_LA: Optional[float] = None
    comparativo_retorno_pendencia_LA: Optional[float] = None
    comparativo_cancelados_LA: Optional[float] = None

    # Pendências NG
    pendencias_total: Optional[int] = None
    pendencias_nao_resolvidas: Optional[int] = None
    pendencias_nao_resolvidas_com_atraso: Optional[int] = None
    pendencias_resolvidas: Optional[int] = None
    pendencias_canceladas: Optional[int] = None
    pendencias_taxa_nao_resolvidos: Optional[float] = None
    pendencias_taxa_resolvidos: Optional[float] = None
    pendencias_taxa_canceladas: Optional[float] = None
    pendencias_nao_resolvidas_reajuizamento: Optional[int] = None
    pendencias_resolvidas_reajuizamento: Optional[int] = None
    pendencias_triagem: Optional[int] = None
    media_tempo_resolvidos_pendencia: Optional[float] = None
    mediana_tempo_resolvidos_pendencia: Optional[float] = None
    comparativo_pendencias_resolvidas: Optional[float] = None
    comparativo_tempo_medio_pendencias_resolvidas: Optional[float] = None

    # Peticionamento NG
    total_peticionados: Optional[int] = None
    peticionados_automaticamente: Optional[int] = None
    peticionados_manualmente: Optional[int] = None
    nao_peticionados: Optional[int] = None
    resolvidos_reajuizamento_pet: Optional[int] = None
    nao_resolvidos_reajuizamento: Optional[int] = None
    media_tempo_peticionado: Optional[float] = None
    mediana_tempo_peticionado: Optional[float] = None
    comparativo_peticionados: Optional[float] = None
    comparativo_tempo_medio_peticionado: Optional[float] = None
    processos_em_revisao: Optional[int] = None
    comparativo_mediana_tempo_pet: Optional[float] = None
    comparativo_peticionados_manualmente: Optional[float] = None
    comparativo_peticionados_automaticamente: Optional[float] = None
    comparativo_peticionados_reajuizamento: Optional[float] = None
    comparativo_nao_peticionados_reajuizamento: Optional[float] = None
    comparativo_valor_causa_confeccionado: Optional[float] = None
    comparativo_ticket_medio_confeccionado: Optional[float] = None
    peticionamento_taxa_resolvidos: Optional[float] = None
    peticionamento_taxa_nao_resolvidos: Optional[float] = None

    # Execução NG
    total_em_execucao: Optional[int] = None
    valor_total_em_execucao: Optional[float] = None
    total_valor_execucao_vazio: Optional[int] = None
    total_valor_execucao_vazio_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    valor_honorarios_total_execucao: Optional[float] = None
    valor_em_execucao: Optional[float] = None
    valor_remanescente_em_execucao: Optional[float] = None
    estoque_inicial: Optional[int] = None
    tre: Optional[float] = None
    total_saida_execucao_periodo: Optional[int] = None
    total_incontroverso_saida_execucao_periodo: Optional[int] = None
    valor_execucao_saida_periodo: Optional[float] = None
    valor_incontroverso_saida_execucao_periodo: Optional[float] = None
    valor_ted_saida_execucao_periodo: Optional[float] = None
    taxa_recuperacao_execucao: Optional[float] = None
    media_tempo_execucao: Optional[float] = None
    taxa_atualizacao_execucao_NG: Optional[Dict[str, Any]] = None
    duracoes_tempo_execucao_NG: Optional[List[float]] = None
    mediana_tempo_execucao: Optional[float] = None
    execucao_materia_filtro: Optional[Union[str, List[str]]] = None
    execucao_subfase_filtro: Optional[Union[str, List[str]]] = None
    execucao_ano_ajuizamento_filtro: Optional[str] = None

    # Execução Acordos NG
    total_em_execucao_acordos_NG: Optional[int] = None
    valor_total_em_execucao_acordos_NG: Optional[float] = None
    total_valor_alcada_final_vazio_acordos_NG: Optional[int] = None
    total_valor_alcada_final_vazio_acordos_NG_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    estoque_inicial_execucao_acordos_NG: Optional[int] = None
    tre_execucao_acordos_NG: Optional[float] = None
    total_entrada_execucao_acordos_periodo_NG: Optional[int] = None
    valor_entrada_execucao_acordos_periodo_NG: Optional[float] = None
    total_saida_execucao_acordos_periodo_NG: Optional[int] = None
    valor_saida_execucao_acordos_periodo_NG: Optional[float] = None
    valor_ted_saida_execucao_acordos_periodo_NG: Optional[float] = None
    media_tempo_execucao_acordos_NG: Optional[float] = None
    duracoes_tempo_execucao_acordos_NG: Optional[List[float]] = None
    mediana_tempo_execucao_acordos_NG: Optional[float] = None
    total_atividades_execucao_acordos_NG: Optional[int] = None
    atividades_execucao_em_andamento_acordos_NG: Optional[int] = None
    atividades_execucao_vencidas_acordos_NG: Optional[int] = None
    atividades_execucao_vencem_hoje_acordos_NG: Optional[int] = None
    atividades_execucao_concluidas_acordos_NG: Optional[int] = None
    media_mensal_atividades_execucao_acordos_NG: Optional[float] = None
    total_por_prazo_execucao_acordos_NG: Optional[int] = None
    por_prazo_em_andamento_execucao_acordos_NG: Optional[int] = None
    por_prazo_vencidas_execucao_acordos_NG: Optional[int] = None
    por_prazo_vencem_hoje_execucao_acordos_NG: Optional[int] = None
    por_prazo_concluidas_execucao_acordos_NG: Optional[int] = None
    total_diligencias_execucao_acordos_NG: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_acordos_NG: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_acordos_NG: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_acordos_NG: Optional[float] = None
    execucao_acordos_materia_filtro_NG: Optional[Union[str, List[str]]] = None
    execucao_acordos_subfase_filtro_NG: Optional[List[str]] = None
    execucao_acordos_tipo_acao_filtro_NG: Optional[str] = None
    execucao_acordos_sentenca_filtro_NG: Optional[str] = None
    execucao_acordos_uf_filtro_NG: Optional[List[str]] = None
    execucao_acordos_uf_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_ano_ajuizamento_filtro_NG: Optional[str] = None
    execucao_acordos_processo_filtro_NG: Optional[str] = None
    execucao_acordos_comarca_filtro_NG: Optional[List[str]] = None
    execucao_acordos_comarca_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_materia_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_subfase_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_diligencia_tipo_filtro_NG: Optional[str] = None
    execucao_acordos_diligencia_colaborador_filtro_NG: Optional[str] = None
    total_fechamento_acordos_NG: Optional[int] = None
    total_em_execucao_acordos_LA: Optional[int] = None
    valor_total_em_execucao_acordos_LA: Optional[float] = None
    total_valor_alcada_final_vazio_acordos_LA: Optional[int] = None
    total_valor_alcada_final_vazio_acordos_LA_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    estoque_inicial_execucao_acordos_LA: Optional[int] = None
    tre_execucao_acordos_LA: Optional[float] = None
    total_entrada_execucao_acordos_periodo_LA: Optional[int] = None
    valor_entrada_execucao_acordos_periodo_LA: Optional[float] = None
    total_saida_execucao_acordos_periodo_LA: Optional[int] = None
    valor_saida_execucao_acordos_periodo_LA: Optional[float] = None
    valor_ted_saida_execucao_acordos_periodo_LA: Optional[float] = None
    media_tempo_execucao_acordos_LA: Optional[float] = None
    duracoes_tempo_execucao_acordos_LA: Optional[List[float]] = None
    mediana_tempo_execucao_acordos_LA: Optional[float] = None
    total_atividades_execucao_acordos_LA: Optional[int] = None
    atividades_execucao_em_andamento_acordos_LA: Optional[int] = None
    atividades_execucao_vencidas_acordos_LA: Optional[int] = None
    atividades_execucao_vencem_hoje_acordos_LA: Optional[int] = None
    atividades_execucao_concluidas_acordos_LA: Optional[int] = None
    media_mensal_atividades_execucao_acordos_LA: Optional[float] = None
    total_por_prazo_execucao_acordos_LA: Optional[int] = None
    por_prazo_em_andamento_execucao_acordos_LA: Optional[int] = None
    por_prazo_vencidas_execucao_acordos_LA: Optional[int] = None
    por_prazo_vencem_hoje_execucao_acordos_LA: Optional[int] = None
    por_prazo_concluidas_execucao_acordos_LA: Optional[int] = None
    total_diligencias_execucao_acordos_LA: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_acordos_LA: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_acordos_LA: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_acordos_LA: Optional[float] = None
    execucao_acordos_materia_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_acordos_subfase_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_acordos_tipo_acao_filtro_LA: Optional[str] = None
    execucao_acordos_sentenca_filtro_LA: Optional[str] = None
    execucao_acordos_uf_filtro_LA: Optional[List[str]] = None
    execucao_acordos_uf_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_ano_ajuizamento_filtro_LA: Optional[str] = None
    execucao_acordos_processo_filtro_LA: Optional[str] = None
    execucao_acordos_comarca_filtro_LA: Optional[List[str]] = None
    execucao_acordos_comarca_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_materia_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_subfase_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_diligencia_tipo_filtro_LA: Optional[str] = None
    execucao_acordos_diligencia_colaborador_filtro_LA: Optional[str] = None
    total_fechamento_acordos_LA: Optional[int] = None
    total_em_execucao_acordos_RJ: Optional[int] = None
    valor_total_em_execucao_acordos_RJ: Optional[float] = None
    total_valor_alcada_final_vazio_acordos_RJ: Optional[int] = None
    total_valor_alcada_final_vazio_acordos_RJ_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    estoque_inicial_execucao_acordos_RJ: Optional[int] = None
    tre_execucao_acordos_RJ: Optional[float] = None
    total_entrada_execucao_acordos_periodo_RJ: Optional[int] = None
    valor_entrada_execucao_acordos_periodo_RJ: Optional[float] = None
    total_saida_execucao_acordos_periodo_RJ: Optional[int] = None
    valor_saida_execucao_acordos_periodo_RJ: Optional[float] = None
    valor_ted_saida_execucao_acordos_periodo_RJ: Optional[float] = None
    media_tempo_execucao_acordos_RJ: Optional[float] = None
    duracoes_tempo_execucao_acordos_RJ: Optional[List[float]] = None
    mediana_tempo_execucao_acordos_RJ: Optional[float] = None
    total_atividades_execucao_acordos_RJ: Optional[int] = None
    atividades_execucao_em_andamento_acordos_RJ: Optional[int] = None
    atividades_execucao_vencidas_acordos_RJ: Optional[int] = None
    atividades_execucao_vencem_hoje_acordos_RJ: Optional[int] = None
    atividades_execucao_concluidas_acordos_RJ: Optional[int] = None
    media_mensal_atividades_execucao_acordos_RJ: Optional[float] = None
    total_por_prazo_execucao_acordos_RJ: Optional[int] = None
    por_prazo_em_andamento_execucao_acordos_RJ: Optional[int] = None
    por_prazo_vencidas_execucao_acordos_RJ: Optional[int] = None
    por_prazo_vencem_hoje_execucao_acordos_RJ: Optional[int] = None
    por_prazo_concluidas_execucao_acordos_RJ: Optional[int] = None
    total_diligencias_execucao_acordos_RJ: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_acordos_RJ: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_acordos_RJ: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_acordos_RJ: Optional[float] = None
    execucao_acordos_materia_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_acordos_subfase_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_acordos_tipo_acao_filtro_RJ: Optional[str] = None
    execucao_acordos_sentenca_filtro_RJ: Optional[str] = None
    execucao_acordos_uf_filtro_RJ: Optional[List[str]] = None
    execucao_acordos_uf_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_ano_ajuizamento_filtro_RJ: Optional[str] = None
    execucao_acordos_processo_filtro_RJ: Optional[str] = None
    execucao_acordos_comarca_filtro_RJ: Optional[List[str]] = None
    execucao_acordos_comarca_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_materia_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_subfase_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_diligencia_tipo_filtro_RJ: Optional[str] = None
    execucao_acordos_diligencia_colaborador_filtro_RJ: Optional[str] = None
    total_fechamento_acordos_RJ: Optional[int] = None

    total_atividades_execucao_NG: Optional[int] = None
    atividades_execucao_em_andamento_NG: Optional[int] = None
    total_atividades_criadas_execucao_NG: Optional[int] = None
    atividades_criadas_em_andamento_execucao_NG: Optional[int] = None
    atividades_execucao_abertas_NG: Optional[int] = None
    atividades_execucao_vencidas_NG: Optional[int] = None
    atividades_execucao_vencem_hoje_NG: Optional[int] = None
    atividades_execucao_concluidas_NG: Optional[int] = None
    media_mensal_atividades_execucao_NG: Optional[float] = None
    total_por_prazo_execucao_NG: Optional[int] = None
    por_prazo_em_andamento_execucao_NG: Optional[int] = None
    por_prazo_vencidas_execucao_NG: Optional[int] = None
    por_prazo_vencem_hoje_execucao_NG: Optional[int] = None
    por_prazo_concluidas_execucao_NG: Optional[int] = None
    total_diligencias_execucao_NG: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_NG: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_NG: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_NG: Optional[float] = None
    execucao_diligencia_tipo_filtro_NG: Optional[str] = None
    execucao_diligencia_colaborador_filtro_NG: Optional[str] = None
    execucao_uf_filtro_NG: Optional[List[str]] = None
    execucao_uf_opcoes_NG: Optional[List[str]] = None
    execucao_comarca_filtro_NG: Optional[List[str]] = None
    execucao_comarca_opcoes_NG: Optional[List[str]] = None
    execucao_materia_opcoes_NG: Optional[List[str]] = None
    execucao_subfase_opcoes_NG: Optional[List[str]] = None

    # Execução RJ (Condenação)
    total_em_execucao_RJ: Optional[int] = None
    valor_total_em_execucao_RJ: Optional[float] = None
    total_valor_execucao_vazio_RJ: Optional[int] = None
    total_valor_execucao_vazio_RJ_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    valor_honorarios_total_execucao_RJ: Optional[float] = None
    valor_em_execucao_RJ: Optional[float] = None
    valor_remanescente_em_execucao_RJ: Optional[float] = None
    estoque_inicial_RJ: Optional[int] = None
    tre_RJ: Optional[float] = None
    total_saida_execucao_periodo_RJ: Optional[int] = None
    total_incontroverso_saida_execucao_periodo_RJ: Optional[int] = None
    valor_execucao_saida_periodo_RJ: Optional[float] = None
    valor_incontroverso_saida_execucao_periodo_RJ: Optional[float] = None
    valor_ted_saida_execucao_periodo_RJ: Optional[float] = None
    taxa_recuperacao_execucao_RJ: Optional[float] = None
    media_tempo_execucao_RJ: Optional[float] = None
    taxa_atualizacao_execucao_RJ: Optional[Dict[str, Any]] = None
    duracoes_tempo_execucao_RJ: Optional[List[float]] = None
    mediana_tempo_execucao_RJ: Optional[float] = None
    execucao_materia_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_subfase_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_ano_ajuizamento_filtro_RJ: Optional[str] = None
    total_atividades_execucao_RJ: Optional[int] = None
    atividades_execucao_em_andamento_RJ: Optional[int] = None
    atividades_execucao_vencidas_RJ: Optional[int] = None
    atividades_execucao_vencem_hoje_RJ: Optional[int] = None
    atividades_execucao_concluidas_RJ: Optional[int] = None
    total_atividades_criadas_execucao_RJ: Optional[int] = None
    atividades_criadas_em_andamento_execucao_RJ: Optional[int] = None
    atividades_execucao_abertas_RJ: Optional[int] = None
    media_mensal_atividades_execucao_RJ: Optional[float] = None
    total_por_prazo_execucao_RJ: Optional[int] = None
    por_prazo_em_andamento_execucao_RJ: Optional[int] = None
    por_prazo_vencidas_execucao_RJ: Optional[int] = None
    por_prazo_vencem_hoje_execucao_RJ: Optional[int] = None
    por_prazo_concluidas_execucao_RJ: Optional[int] = None
    total_diligencias_execucao_RJ: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_RJ: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_RJ: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_RJ: Optional[float] = None
    execucao_diligencia_tipo_filtro_RJ: Optional[str] = None
    execucao_diligencia_colaborador_filtro_RJ: Optional[str] = None
    execucao_uf_filtro_RJ: Optional[List[str]] = None
    execucao_uf_opcoes_RJ: Optional[List[str]] = None
    execucao_comarca_filtro_RJ: Optional[List[str]] = None
    execucao_comarca_opcoes_RJ: Optional[List[str]] = None
    execucao_materia_opcoes_RJ: Optional[List[str]] = None
    execucao_subfase_opcoes_RJ: Optional[List[str]] = None

    # Comercial LA
    clientes_campanha_LA: Optional[int] = None
    clientes_indicacao_LA: Optional[int] = None
    clientes_redes_sociais_LA: Optional[int] = None
    clientes_retorno_LA: Optional[int] = None
    clientes_parceiro_LA: Optional[int] = None
    clientes_externos_LA: Optional[int] = None
    clientes_todos_LA: Optional[int] = None
    clientes_cancelados_LA: Optional[int] = None
    acoes_fechadas_LA: Optional[int] = None
    taxa_aproveitamento_LA: Optional[float] = None
    comparativo_clientes_campanha_LA: Optional[float] = None
    comparativo_clientes_indicacao_LA: Optional[float] = None
    comparativo_clientes_externos_LA: Optional[float] = None
    comparativo_clientes_parceiro_LA: Optional[float] = None
    comparativo_clientes_retorno_LA: Optional[float] = None
    comparativo_clientes_redes_sociais_LA: Optional[float] = None
    comparativo_clientes_cancelados_LA: Optional[float] = None
    comparativo_acoes_fechadas_LA: Optional[float] = None
    acoes_fechadas_periodo_anterior_LA: Optional[float] = None
    comparativo_taxa_aproveitamento_LA: Optional[float] = None
    comparativo_clientes_total_LA: Optional[float] = None
    clientes_total_periodo_anterior_LA: Optional[float] = None
    comissao_base_LA: Optional[float] = None
    tempo_medio_contratacao_protocolo_LA: Optional[float] = None
    mediana_tempo_contratacao_protocolo_LA: Optional[float] = None
    comparativo_tempo_medio_contratacao_protocolo_LA: Optional[float] = None
    comparativo_mediana_tempo_contratacao_protocolo_LA: Optional[float] = None

    # Protocolo LA
    protocolos_resolvidos_LA: Optional[int] = None
    protocolos_represados_LA: Optional[int] = None
    valor_causa_protocolado_LA: Optional[float] = None
    ticket_medio_protocolos_resolvidos_LA: Optional[float] = None
    media_tempo_protocolo_LA: Optional[float] = None
    mediana_tempo_protocolo_LA: Optional[float] = None
    comparativo_protocolos_resolvidos_LA: Optional[float] = None
    protocolos_resolvidos_periodo_anterior_LA: Optional[float] = None
    comparativo_valor_causa_protocolado_LA: Optional[float] = None
    valor_causa_protocolado_periodo_anterior_LA: Optional[float] = None
    comparativo_ticket_medio_protocolos_resolvidos_LA: Optional[float] = None
    comparativo_tempo_medio_protocolos_resolvidos_LA: Optional[float] = None
    comparativo_mediana_tempo_protocolos_resolvidos_LA: Optional[float] = None
    taxa_protocolados_LA: Optional[float] = None
    entradas_protocolo_LA: Optional[int] = None
    valor_causa_protocolado_LA_2026: Optional[float] = None
    meta_anual_comercial_LA: Optional[float] = None
    fator_multiplicador_LA: Optional[float] = None
    comissao_com_fm_LA: Optional[float] = None

    # Estratégico Geral (NG + LA)
    protocolos_resolvidos_geral: Optional[int] = None
    estrategico_geral_fase_inicial_total_processos: Optional[int] = None
    estrategico_geral_fase_inicial_valor_causa_total: Optional[float] = None
    estrategico_geral_fase_recursal_total_processos: Optional[int] = None
    estrategico_geral_fase_recursal_valor_causa_total: Optional[float] = None
    estrategico_geral_fase_recursal_valor_sentenca_total: Optional[float] = None
    estrategico_geral_fase_execucao_total_processos: Optional[int] = None
    estrategico_geral_fase_execucao_valor_causa_total: Optional[float] = None
    estrategico_geral_fase_execucao_valor_execucao_total: Optional[float] = None
    estrategico_geral_escritorio_filtro: Optional[str] = None
    estrategico_geral_escritorios_filtro: Optional[List[str]] = None
    estrategico_geral_comarcas_filtro: Optional[List[str]] = None

    # Peticionamento LA
    total_confeccionados_LA: Optional[int] = None
    confeccionados_manualmente_LA: Optional[int] = None
    confeccionados_automaticamente_LA: Optional[int] = None
    nao_confeccionados_LA: Optional[int] = None
    valor_causa_confeccionado_LA: Optional[float] = None
    ticket_medio_confeccionado_LA: Optional[float] = None
    tempo_medio_confeccao_LA: Optional[float] = None
    mediana_tempo_confeccao_LA: Optional[float] = None
    comparativo_confeccionados_LA: Optional[float] = None
    comparativo_confeccionados_automaticamente_LA: Optional[float] = None
    comparativo_confeccionados_manualmente_LA: Optional[float] = None
    comparativo_valor_causa_confeccionado_LA: Optional[float] = None
    comparativo_ticket_medio_confeccionado_LA: Optional[float] = None
    comparativo_tempo_medio_confeccionado_LA: Optional[float] = None
    comparativo_mediana_tempo_confeccionado_LA: Optional[float] = None
    peticionamento_taxa_resolvidos_LA: Optional[float] = None
    peticionamento_taxa_nao_resolvidos_LA: Optional[float] = None
    peticionamento_taxa_retorno_protocolo_LA: Optional[float] = None
    peticionamento_qtd_retorno_protocolo_LA: Optional[int] = None
    peticionamento_qtd_entrada_protocolo_LA: Optional[int] = None

    # Andamento Processual LA
    total_andamento_processual_LA: Optional[int] = None
    andamento_processual_resolvidos_LA: Optional[int] = None
    andamento_processual_nao_resolvidos_LA: Optional[int] = None
    media_avaliacao_LA: Optional[float] = None
    taxa_resolvidos_LA: Optional[float] = None
    taxa_nao_resolvidos_LA: Optional[float] = None
    media_espera_LA: Optional[float] = None
    mediana_espera_LA: Optional[float] = None
    media_atendimento_LA: Optional[float] = None
    mediana_atendimento_LA: Optional[float] = None

    # Execução LA
    total_em_execucao_LA: Optional[int] = None
    valor_total_em_execucao_LA: Optional[float] = None
    total_valor_execucao_vazio_LA: Optional[int] = None
    total_valor_execucao_vazio_LA_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    valor_honorarios_total_execucao_LA: Optional[float] = None
    valor_em_execucao_LA: Optional[float] = None
    valor_remanescente_em_execucao_LA: Optional[float] = None
    estoque_inicial_LA: Optional[int] = None
    tre_LA: Optional[float] = None
    total_saida_execucao_periodo_LA: Optional[int] = None
    total_incontroverso_saida_execucao_periodo_LA: Optional[int] = None
    valor_execucao_saida_periodo_LA: Optional[float] = None
    valor_incontroverso_saida_execucao_periodo_LA: Optional[float] = None
    valor_ted_saida_execucao_periodo_LA: Optional[float] = None
    taxa_recuperacao_execucao_LA: Optional[float] = None
    media_tempo_execucao_LA: Optional[float] = None
    taxa_atualizacao_execucao_LA: Optional[Dict[str, Any]] = None
    duracoes_tempo_execucao_LA: Optional[List[float]] = None
    mediana_tempo_execucao_LA: Optional[float] = None
    execucao_materia_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_subfase_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_ano_ajuizamento_filtro_LA: Optional[str] = None
    execucao_comarca_filtro_LA: Optional[List[str]] = None
    execucao_comarca_opcoes_LA: Optional[List[str]] = None
    execucao_uf_filtro_LA: Optional[List[str]] = None
    execucao_uf_opcoes_LA: Optional[List[str]] = None
    execucao_materia_opcoes_LA: Optional[List[str]] = None
    execucao_subfase_opcoes_LA: Optional[List[str]] = None
    total_atividades_execucao_LA: Optional[int] = None
    atividades_execucao_em_andamento_LA: Optional[int] = None
    total_atividades_criadas_execucao_LA: Optional[int] = None
    atividades_criadas_em_andamento_execucao_LA: Optional[int] = None
    atividades_execucao_abertas_LA: Optional[int] = None
    atividades_execucao_vencidas_LA: Optional[int] = None
    atividades_execucao_vencem_hoje_LA: Optional[int] = None
    atividades_execucao_concluidas_LA: Optional[int] = None
    media_mensal_atividades_execucao_LA: Optional[float] = None
    total_por_prazo_execucao_LA: Optional[int] = None
    por_prazo_em_andamento_execucao_LA: Optional[int] = None
    por_prazo_vencidas_execucao_LA: Optional[int] = None
    por_prazo_vencem_hoje_execucao_LA: Optional[int] = None
    por_prazo_concluidas_execucao_LA: Optional[int] = None

    # Fase Recursal LA (setor_recurso / LexFlow)
    total_recursal_LA: Optional[int] = None
    entrada_recursal_LA: Optional[int] = None
    valor_causa_acordo_recursal_LA: Optional[float] = None
    total_sentenca_favoravel_recurso_LA: Optional[int] = None
    total_sentenca_desfavoravel_recurso_LA: Optional[int] = None
    total_procedente_1g_recurso_LA: Optional[int] = None
    total_parcialmente_procedente_recurso_LA: Optional[int] = None
    total_sentenca_extincao_recurso_LA: Optional[int] = None
    total_sentenca_parcialmente_favoravel_recurso_LA: Optional[int] = None
    valor_causa_sentenca_favoravel_recurso_LA: Optional[float] = None
    valor_causa_sentenca_desfavoravel_recurso_LA: Optional[float] = None
    valor_causa_sentenca_procedente_1g_recurso_LA: Optional[float] = None
    valor_causa_sentenca_parcialmente_procedente_recurso_LA: Optional[float] = None
    valor_causa_sentenca_extincao_recurso_LA: Optional[float] = None
    valor_causa_sentenca_parcialmente_favoravel_recurso_LA: Optional[float] = None
    total_acordao_desfavoravel_recurso_LA: Optional[int] = None
    total_acordao_favoravel_recurso_LA: Optional[int] = None
    total_acordao_parcialmente_favoravel_recurso_LA: Optional[int] = None
    total_acordao_parcial_retomada_recurso_LA: Optional[int] = None
    total_acordao_extincao_recurso_LA: Optional[int] = None
    valor_causa_acordao_desfavoravel_recurso_LA: Optional[float] = None
    valor_causa_acordao_favoravel_recurso_LA: Optional[float] = None
    valor_causa_acordao_parcialmente_favoravel_recurso_LA: Optional[float] = None
    valor_causa_acordao_parcial_retomada_recurso_LA: Optional[float] = None
    valor_causa_acordao_extincao_recurso_LA: Optional[float] = None
    total_decisoes_recursal_LA: Optional[int] = None
    # Decisões recursais — Matriz de Julgamento (mérito 1G × 2G), 8 buckets
    total_mantido_ganho_recurso_LA: Optional[int] = None
    total_ganho_ampliado_recurso_LA: Optional[int] = None
    total_revertido_ganho_recurso_LA: Optional[int] = None
    total_ganho_reduzido_recurso_LA: Optional[int] = None
    total_mantido_perda_recurso_LA: Optional[int] = None
    total_revertido_perda_recurso_LA: Optional[int] = None
    total_extincao_reajuizar_recurso_LA: Optional[int] = None
    total_instrucao_retomada_recurso_LA: Optional[int] = None
    percent_mantido_ganho_recursal_LA: Optional[float] = None
    percent_ganho_ampliado_recursal_LA: Optional[float] = None
    percent_revertido_ganho_recursal_LA: Optional[float] = None
    percent_ganho_reduzido_recursal_LA: Optional[float] = None
    percent_mantido_perda_recursal_LA: Optional[float] = None
    percent_revertido_perda_recursal_LA: Optional[float] = None
    percent_extincao_reajuizar_recursal_LA: Optional[float] = None
    percent_instrucao_retomada_recursal_LA: Optional[float] = None
    valor_causa_mantido_ganho_recurso_LA: Optional[float] = None
    valor_causa_ganho_ampliado_recurso_LA: Optional[float] = None
    valor_causa_revertido_ganho_recurso_LA: Optional[float] = None
    valor_causa_ganho_reduzido_recurso_LA: Optional[float] = None
    valor_causa_mantido_perda_recurso_LA: Optional[float] = None
    valor_causa_revertido_perda_recurso_LA: Optional[float] = None
    valor_causa_extincao_reajuizar_recurso_LA: Optional[float] = None
    valor_causa_instrucao_retomada_recurso_LA: Optional[float] = None
    total_atividades_recursos_LA: Optional[int] = None
    atividades_recursos_em_andamento_LA: Optional[int] = None
    atividades_recursos_vencidas_LA: Optional[int] = None
    atividades_recursos_vencem_hoje_LA: Optional[int] = None
    atividades_recursos_concluidas_LA: Optional[int] = None
    # Mesmos KPIs de atividades, usando PRAZO como eixo temporal (toggle "Por prazo").
    total_por_prazo_atividades_recursos_LA: Optional[int] = None
    por_prazo_em_andamento_atividades_recursos_LA: Optional[int] = None
    por_prazo_vencidas_atividades_recursos_LA: Optional[int] = None
    por_prazo_vencem_hoje_atividades_recursos_LA: Optional[int] = None
    por_prazo_concluidas_atividades_recursos_LA: Optional[int] = None

    # Recursal NG
    total_recursal_NG: Optional[int] = None
    entrada_recursal_NG: Optional[int] = None
    valor_causa_acordo_recursal_NG: Optional[float] = None
    total_sentenca_favoravel_recurso_NG: Optional[int] = None
    total_sentenca_desfavoravel_recurso_NG: Optional[int] = None
    total_procedente_1g_recurso_NG: Optional[int] = None
    total_parcialmente_procedente_recurso_NG: Optional[int] = None
    total_sentenca_extincao_recurso_NG: Optional[int] = None
    total_sentenca_parcialmente_favoravel_recurso_NG: Optional[int] = None
    valor_causa_sentenca_favoravel_recurso_NG: Optional[float] = None
    valor_causa_sentenca_desfavoravel_recurso_NG: Optional[float] = None
    valor_causa_sentenca_procedente_1g_recurso_NG: Optional[float] = None
    valor_causa_sentenca_parcialmente_procedente_recurso_NG: Optional[float] = None
    valor_causa_sentenca_extincao_recurso_NG: Optional[float] = None
    valor_causa_sentenca_parcialmente_favoravel_recurso_NG: Optional[float] = None
    total_acordao_desfavoravel_recurso_NG: Optional[int] = None
    total_acordao_favoravel_recurso_NG: Optional[int] = None
    total_acordao_parcialmente_favoravel_recurso_NG: Optional[int] = None
    total_acordao_parcial_retomada_recurso_NG: Optional[int] = None
    total_acordao_extincao_recurso_NG: Optional[int] = None
    valor_causa_acordao_desfavoravel_recurso_NG: Optional[float] = None
    valor_causa_acordao_favoravel_recurso_NG: Optional[float] = None
    valor_causa_acordao_parcialmente_favoravel_recurso_NG: Optional[float] = None
    valor_causa_acordao_parcial_retomada_recurso_NG: Optional[float] = None
    valor_causa_acordao_extincao_recurso_NG: Optional[float] = None
    total_decisoes_recursal_NG: Optional[int] = None
    # Decisões recursais — Matriz de Julgamento (mérito 1G × 2G), 8 buckets
    total_mantido_ganho_recurso_NG: Optional[int] = None
    total_ganho_ampliado_recurso_NG: Optional[int] = None
    total_revertido_ganho_recurso_NG: Optional[int] = None
    total_ganho_reduzido_recurso_NG: Optional[int] = None
    total_mantido_perda_recurso_NG: Optional[int] = None
    total_revertido_perda_recurso_NG: Optional[int] = None
    total_extincao_reajuizar_recurso_NG: Optional[int] = None
    total_instrucao_retomada_recurso_NG: Optional[int] = None
    percent_mantido_ganho_recursal_NG: Optional[float] = None
    percent_ganho_ampliado_recursal_NG: Optional[float] = None
    percent_revertido_ganho_recursal_NG: Optional[float] = None
    percent_ganho_reduzido_recursal_NG: Optional[float] = None
    percent_mantido_perda_recursal_NG: Optional[float] = None
    percent_revertido_perda_recursal_NG: Optional[float] = None
    percent_extincao_reajuizar_recursal_NG: Optional[float] = None
    percent_instrucao_retomada_recursal_NG: Optional[float] = None
    valor_causa_mantido_ganho_recurso_NG: Optional[float] = None
    valor_causa_ganho_ampliado_recurso_NG: Optional[float] = None
    valor_causa_revertido_ganho_recurso_NG: Optional[float] = None
    valor_causa_ganho_reduzido_recurso_NG: Optional[float] = None
    valor_causa_mantido_perda_recurso_NG: Optional[float] = None
    valor_causa_revertido_perda_recurso_NG: Optional[float] = None
    valor_causa_extincao_reajuizar_recurso_NG: Optional[float] = None
    valor_causa_instrucao_retomada_recurso_NG: Optional[float] = None
    total_atividades_recursos_NG: Optional[int] = None
    atividades_recursos_em_andamento_NG: Optional[int] = None
    atividades_recursos_vencidas_NG: Optional[int] = None
    atividades_recursos_vencem_hoje_NG: Optional[int] = None
    atividades_recursos_concluidas_NG: Optional[int] = None
    # Mesmos KPIs de atividades, usando PRAZO como eixo temporal (toggle "Por prazo").
    total_por_prazo_atividades_recursos_NG: Optional[int] = None
    por_prazo_em_andamento_atividades_recursos_NG: Optional[int] = None
    por_prazo_vencidas_atividades_recursos_NG: Optional[int] = None
    por_prazo_vencem_hoje_atividades_recursos_NG: Optional[int] = None
    por_prazo_concluidas_atividades_recursos_NG: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — análise de viabilidade equivocada.
    avr_retorno_recurso_cancelado_NG: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — perda de prazo.
    retorno_cr_recurso_cancelado_NG: Optional[int] = None
    # Meta de Provimento Mensal — processos providos (ID_2G) no período.
    provimento_mensal_qtd_NG: Optional[int] = None
    provimento_mensal_meta_NG: Optional[int] = None
    # Recursal RJ
    total_recursal_RJ: Optional[int] = None
    entrada_recursal_RJ: Optional[int] = None
    valor_causa_acordo_recursal_RJ: Optional[float] = None
    total_sentenca_favoravel_recurso_RJ: Optional[int] = None
    total_sentenca_desfavoravel_recurso_RJ: Optional[int] = None
    total_procedente_1g_recurso_RJ: Optional[int] = None
    total_parcialmente_procedente_recurso_RJ: Optional[int] = None
    total_sentenca_extincao_recurso_RJ: Optional[int] = None
    total_sentenca_parcialmente_favoravel_recurso_RJ: Optional[int] = None
    valor_causa_sentenca_favoravel_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_desfavoravel_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_procedente_1g_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_parcialmente_procedente_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_extincao_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_parcialmente_favoravel_recurso_RJ: Optional[float] = None
    total_acordao_desfavoravel_recurso_RJ: Optional[int] = None
    total_acordao_favoravel_recurso_RJ: Optional[int] = None
    total_acordao_parcialmente_favoravel_recurso_RJ: Optional[int] = None
    total_acordao_parcial_retomada_recurso_RJ: Optional[int] = None
    total_acordao_extincao_recurso_RJ: Optional[int] = None
    valor_causa_acordao_desfavoravel_recurso_RJ: Optional[float] = None
    valor_causa_acordao_favoravel_recurso_RJ: Optional[float] = None
    valor_causa_acordao_parcialmente_favoravel_recurso_RJ: Optional[float] = None
    valor_causa_acordao_parcial_retomada_recurso_RJ: Optional[float] = None
    valor_causa_acordao_extincao_recurso_RJ: Optional[float] = None
    total_decisoes_recursal_RJ: Optional[int] = None
    # Decisões recursais — Matriz de Julgamento (mérito 1G × 2G), 8 buckets
    total_mantido_ganho_recurso_RJ: Optional[int] = None
    total_ganho_ampliado_recurso_RJ: Optional[int] = None
    total_revertido_ganho_recurso_RJ: Optional[int] = None
    total_ganho_reduzido_recurso_RJ: Optional[int] = None
    total_mantido_perda_recurso_RJ: Optional[int] = None
    total_revertido_perda_recurso_RJ: Optional[int] = None
    total_extincao_reajuizar_recurso_RJ: Optional[int] = None
    total_instrucao_retomada_recurso_RJ: Optional[int] = None
    percent_mantido_ganho_recursal_RJ: Optional[float] = None
    percent_ganho_ampliado_recursal_RJ: Optional[float] = None
    percent_revertido_ganho_recursal_RJ: Optional[float] = None
    percent_ganho_reduzido_recursal_RJ: Optional[float] = None
    percent_mantido_perda_recursal_RJ: Optional[float] = None
    percent_revertido_perda_recursal_RJ: Optional[float] = None
    percent_extincao_reajuizar_recursal_RJ: Optional[float] = None
    percent_instrucao_retomada_recursal_RJ: Optional[float] = None
    valor_causa_mantido_ganho_recurso_RJ: Optional[float] = None
    valor_causa_ganho_ampliado_recurso_RJ: Optional[float] = None
    valor_causa_revertido_ganho_recurso_RJ: Optional[float] = None
    valor_causa_ganho_reduzido_recurso_RJ: Optional[float] = None
    valor_causa_mantido_perda_recurso_RJ: Optional[float] = None
    valor_causa_revertido_perda_recurso_RJ: Optional[float] = None
    valor_causa_extincao_reajuizar_recurso_RJ: Optional[float] = None
    valor_causa_instrucao_retomada_recurso_RJ: Optional[float] = None
    total_atividades_recursos_RJ: Optional[int] = None
    atividades_recursos_em_andamento_RJ: Optional[int] = None
    atividades_recursos_vencidas_RJ: Optional[int] = None
    atividades_recursos_vencem_hoje_RJ: Optional[int] = None
    atividades_recursos_concluidas_RJ: Optional[int] = None
    # Mesmos KPIs de atividades, usando PRAZO como eixo temporal (toggle "Por prazo").
    total_por_prazo_atividades_recursos_RJ: Optional[int] = None
    por_prazo_em_andamento_atividades_recursos_RJ: Optional[int] = None
    por_prazo_vencidas_atividades_recursos_RJ: Optional[int] = None
    por_prazo_vencem_hoje_atividades_recursos_RJ: Optional[int] = None
    por_prazo_concluidas_atividades_recursos_RJ: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — análise de viabilidade equivocada.
    avr_retorno_recurso_cancelado_RJ: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — perda de prazo.
    retorno_cr_recurso_cancelado_RJ: Optional[int] = None
    # Meta de Provimento Mensal — processos providos (ID_2G) no período.
    provimento_mensal_qtd_RJ: Optional[int] = None
    provimento_mensal_meta_RJ: Optional[int] = None
    # Extintos · 2º Grau (painel do Recursal RJ) — no NG vêm do controle_processo_NG.
    controle_processo_extintos_com_merito_2g_qtd_recursal_RJ: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_RJ: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_RJ: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_2g_qtd_recursal_RJ: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_RJ: Optional[float] = None
    controle_processo_taxa_provimento_2g_recursal_RJ: Optional[float] = None

    # Pendências Intermediárias LA (LexFlow)
    total_atividades_intermediarias_LA: Optional[int] = None
    atividades_intermediarias_em_andamento_LA: Optional[int] = None
    atividades_intermediarias_vencidas_LA: Optional[int] = None
    atividades_intermediarias_vencem_hoje_LA: Optional[int] = None
    atividades_intermediarias_concluidas_LA: Optional[int] = None
    # Pendências Intermediárias LA — Por Prazo
    total_por_prazo_intermediarias_LA: Optional[int] = None
    por_prazo_em_andamento_intermediarias_LA: Optional[int] = None
    por_prazo_vencidas_intermediarias_LA: Optional[int] = None
    por_prazo_vencem_hoje_intermediarias_LA: Optional[int] = None
    por_prazo_concluidas_intermediarias_LA: Optional[int] = None
    # Pendências Intermediárias LA — Dilações
    dilacoes_intermediarias_total_encerrados_LA: Optional[int] = None
    dilacoes_intermediarias_count_LA: Optional[int] = None
    dilacoes_intermediarias_taxa_LA: Optional[float] = None
    dilacoes_intermediarias_faixa_LA: Optional[str] = None

    # Pendências Intermediárias NG (LexFlow)
    total_atividades_intermediarias_NG: Optional[int] = None
    atividades_intermediarias_em_andamento_NG: Optional[int] = None
    atividades_intermediarias_vencidas_NG: Optional[int] = None
    atividades_intermediarias_vencem_hoje_NG: Optional[int] = None
    atividades_intermediarias_concluidas_NG: Optional[int] = None
    # Pendências Intermediárias NG — Por Prazo
    total_por_prazo_intermediarias_NG: Optional[int] = None
    por_prazo_em_andamento_intermediarias_NG: Optional[int] = None
    por_prazo_vencidas_intermediarias_NG: Optional[int] = None
    por_prazo_vencem_hoje_intermediarias_NG: Optional[int] = None
    por_prazo_concluidas_intermediarias_NG: Optional[int] = None
    # Pendências Intermediárias NG — Dilações
    dilacoes_intermediarias_total_encerrados_NG: Optional[int] = None
    dilacoes_intermediarias_count_NG: Optional[int] = None
    dilacoes_intermediarias_taxa_NG: Optional[float] = None
    dilacoes_intermediarias_faixa_NG: Optional[str] = None

    # Emendas e Manifestações LA (LexFlow — Setor Intermediárias)
    total_atividades_emendas_manifestacoes_LA: Optional[int] = None
    atividades_emendas_manifestacoes_em_andamento_LA: Optional[int] = None
    atividades_emendas_manifestacoes_vencidas_LA: Optional[int] = None
    atividades_emendas_manifestacoes_vencem_hoje_LA: Optional[int] = None
    atividades_emendas_manifestacoes_concluidas_LA: Optional[int] = None
    # Emendas e Manifestações LA — Por Prazo
    total_por_prazo_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_em_andamento_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_vencidas_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_vencem_hoje_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_concluidas_emendas_manifestacoes_LA: Optional[int] = None

    # Emendas e Manifestações NG (LexFlow — Setor Manifestação)
    total_atividades_emendas_manifestacoes_NG: Optional[int] = None
    atividades_emendas_manifestacoes_em_andamento_NG: Optional[int] = None
    atividades_emendas_manifestacoes_vencidas_NG: Optional[int] = None
    atividades_emendas_manifestacoes_vencem_hoje_NG: Optional[int] = None
    atividades_emendas_manifestacoes_concluidas_NG: Optional[int] = None
    # Emendas e Manifestações NG — Por Prazo
    total_por_prazo_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_em_andamento_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_vencidas_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_vencem_hoje_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_concluidas_emendas_manifestacoes_NG: Optional[int] = None
    comparativo_qtd_manifestacoes_emendas_manifestacoes_NG: Optional[float] = None
    comparativo_qtd_dilacoes_emendas_manifestacoes_NG: Optional[float] = None
    emendas_manifestacoes_uf_opcoes_NG: Optional[List[str]] = None

    # Réplicas LA (LexFlow — Setor Réplicas)
    total_atividades_replicas_LA: Optional[int] = None
    atividades_replicas_em_andamento_LA: Optional[int] = None
    atividades_replicas_vencidas_LA: Optional[int] = None
    atividades_replicas_vencem_hoje_LA: Optional[int] = None
    atividades_replicas_concluidas_LA: Optional[int] = None
    # Réplicas LA — Por Prazo
    total_por_prazo_replicas_LA: Optional[int] = None
    por_prazo_em_andamento_replicas_LA: Optional[int] = None
    por_prazo_vencidas_replicas_LA: Optional[int] = None
    por_prazo_vencem_hoje_replicas_LA: Optional[int] = None
    por_prazo_concluidas_replicas_LA: Optional[int] = None
    # Réplicas LA — Taxa de procedência (1G)
    replicas_procedencia_total_processos_LA: Optional[int] = None
    replicas_procedencia_total_decididos_LA: Optional[int] = None
    replicas_procedencia_procedentes_LA: Optional[int] = None
    replicas_procedencia_pendentes_LA: Optional[int] = None
    replicas_taxa_procedencia_LA: Optional[float] = None

    # Réplicas NG (LexFlow — Setor Réplica)
    total_atividades_replicas_NG: Optional[int] = None
    atividades_replicas_em_andamento_NG: Optional[int] = None
    atividades_replicas_vencidas_NG: Optional[int] = None
    atividades_replicas_vencem_hoje_NG: Optional[int] = None
    atividades_replicas_concluidas_NG: Optional[int] = None
    # Réplicas NG — Por Prazo
    total_por_prazo_replicas_NG: Optional[int] = None
    por_prazo_em_andamento_replicas_NG: Optional[int] = None
    por_prazo_vencidas_replicas_NG: Optional[int] = None
    por_prazo_vencem_hoje_replicas_NG: Optional[int] = None
    por_prazo_concluidas_replicas_NG: Optional[int] = None
    # Réplicas NG — Taxa de procedência (1G)
    replicas_procedencia_total_processos_NG: Optional[int] = None
    replicas_procedencia_total_decididos_NG: Optional[int] = None
    replicas_procedencia_procedentes_NG: Optional[int] = None
    replicas_procedencia_pendentes_NG: Optional[int] = None
    replicas_taxa_procedencia_NG: Optional[float] = None
    # Reajuizamento LA (LexFlow — Setor Reajuizamento)
    total_atividades_reajuizamento_LA: Optional[int] = None
    atividades_reajuizamento_em_andamento_LA: Optional[int] = None
    atividades_reajuizamento_vencidas_LA: Optional[int] = None
    atividades_reajuizamento_vencem_hoje_LA: Optional[int] = None
    atividades_reajuizamento_concluidas_LA: Optional[int] = None
    # Reajuizamento LA — Decisão em "Avaliar Reajuizamento"
    reajuizamento_decisao_total_avaliadas_LA: Optional[int] = None
    reajuizamento_decisao_reajuizar_LA: Optional[int] = None
    reajuizamento_decisao_nao_reajuizar_LA: Optional[int] = None
    reajuizamento_taxa_decisao_reajuizar_LA: Optional[float] = None
    reajuizamento_ja_reajuizados_LA: Optional[int] = None

    # Controle de Processo LA (LexFlow)
    total_controle_processo_LA: Optional[int] = None
    controle_processo_situacao_filtro_LA: Optional[str] = None
    controle_processo_fase_filtro_LA: Optional[str] = None
    controle_processo_total_na_fase_LA: Optional[int] = None
    controle_processo_qtd_subfases_na_fase_LA: Optional[int] = None
    controle_processo_fase_inicial_qtd_LA: Optional[int] = None
    controle_processo_fase_inicial_valor_causa_LA: Optional[float] = None
    controle_processo_fase_recursal_qtd_LA: Optional[int] = None
    controle_processo_fase_recursal_valor_causa_LA: Optional[float] = None
    controle_processo_fase_execucao_qtd_LA: Optional[int] = None
    controle_processo_fase_execucao_valor_causa_execucao_LA: Optional[float] = None
    controle_processo_fase_arquivado_procedente_qtd_LA: Optional[int] = None
    controle_processo_fase_arquivado_procedente_valor_causa_LA: Optional[float] = None
    controle_processo_fase_arquivado_improcedente_qtd_LA: Optional[int] = None
    controle_processo_fase_arquivado_improcedente_valor_causa_LA: Optional[float] = None
    controle_processo_fase_transito_julgado_qtd_LA: Optional[int] = None
    controle_processo_fase_transito_julgado_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_com_merito_qtd_LA: Optional[int] = None
    controle_processo_extintos_com_merito_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_com_merito_por_tipo_sentenca_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_qtd_LA: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_LA: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_qtd_LA: Optional[int] = None
    controle_processo_extintos_sem_merito_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_qtd_LA: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_LA: Optional[float] = None
    controle_processo_taxa_provimento_2g_LA: Optional[float] = None
    # Recursal (todas as situações, inclui arquivado) — usado só pelo painel Extintos do Recursal.
    controle_processo_extintos_com_merito_2g_qtd_recursal_LA: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_LA: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_2g_qtd_recursal_LA: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_LA: Optional[float] = None
    controle_processo_taxa_provimento_2g_recursal_LA: Optional[float] = None
    controle_processo_log_inicial_indeferida_qtd_LA: Optional[int] = None
    controle_processo_log_inicial_indeferida_valor_causa_LA: Optional[float] = None
    controle_processo_log_recursal_nao_provido_qtd_LA: Optional[int] = None
    controle_processo_log_recursal_nao_provido_valor_causa_LA: Optional[float] = None
    controle_processo_fase_inicial_media_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_media_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_media_dias_LA: Optional[float] = None
    controle_processo_fase_inicial_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_inicial_comparativo_media_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_comparativo_media_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_comparativo_media_dias_LA: Optional[float] = None
    controle_processo_fase_inicial_comparativo_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_comparativo_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_comparativo_mediana_dias_LA: Optional[float] = None

    total_controle_processo_NG: Optional[int] = None
    controle_processo_valor_causa_total_NG: Optional[float] = None
    controle_processo_situacao_filtro_NG: Optional[str] = None
    controle_processo_uf_filtro_NG: Optional[List[str]] = None
    controle_processo_uf_opcoes_NG: Optional[List[str]] = None
    controle_processo_fase_filtro_NG: Optional[str] = None
    controle_processo_total_na_fase_NG: Optional[int] = None
    controle_processo_qtd_subfases_na_fase_NG: Optional[int] = None
    controle_processo_fase_inicial_qtd_NG: Optional[int] = None
    controle_processo_fase_inicial_valor_causa_NG: Optional[float] = None
    controle_processo_fase_recursal_qtd_NG: Optional[int] = None
    controle_processo_fase_recursal_valor_causa_NG: Optional[float] = None
    controle_processo_fase_execucao_qtd_NG: Optional[int] = None
    controle_processo_fase_execucao_valor_causa_execucao_NG: Optional[float] = None
    controle_processo_fase_arquivado_procedente_qtd_NG: Optional[int] = None
    controle_processo_fase_arquivado_procedente_valor_causa_NG: Optional[float] = None
    controle_processo_fase_arquivado_improcedente_qtd_NG: Optional[int] = None
    controle_processo_fase_arquivado_improcedente_valor_causa_NG: Optional[float] = None
    controle_processo_fase_transito_julgado_qtd_NG: Optional[int] = None
    controle_processo_fase_transito_julgado_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_com_merito_qtd_NG: Optional[int] = None
    controle_processo_extintos_com_merito_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_com_merito_por_tipo_sentenca_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_qtd_NG: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_NG: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_qtd_NG: Optional[int] = None
    controle_processo_extintos_sem_merito_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_qtd_NG: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_NG: Optional[float] = None
    controle_processo_taxa_provimento_2g_NG: Optional[float] = None
    # Recursal (todas as situações, inclui arquivado) — usado só pelo painel Extintos do Recursal.
    controle_processo_extintos_com_merito_2g_qtd_recursal_NG: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_2g_qtd_recursal_NG: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG: Optional[float] = None
    controle_processo_taxa_provimento_2g_recursal_NG: Optional[float] = None
    controle_processo_log_inicial_indeferida_qtd_NG: Optional[int] = None
    controle_processo_log_inicial_indeferida_valor_causa_NG: Optional[float] = None
    controle_processo_log_recursal_nao_provido_qtd_NG: Optional[int] = None
    controle_processo_log_recursal_nao_provido_valor_causa_NG: Optional[float] = None
    controle_processo_fase_inicial_media_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_media_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_media_dias_NG: Optional[float] = None
    controle_processo_fase_inicial_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_inicial_comparativo_media_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_comparativo_media_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_comparativo_media_dias_NG: Optional[float] = None
    controle_processo_fase_inicial_comparativo_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_comparativo_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_comparativo_mediana_dias_NG: Optional[float] = None

    # Pendências LA
    pendencias_total_LA: Optional[int] = None
    pendencias_nao_resolvidas_LA: Optional[int] = None
    pendencias_nao_resolvidas_com_atraso_LA: Optional[int] = None
    pendencias_resolvidas_LA: Optional[int] = None
    pendencias_canceladas_LA: Optional[int] = None
    pendencias_taxa_nao_resolvidos_LA: Optional[float] = None
    pendencias_taxa_resolvidos_LA: Optional[float] = None
    pendencias_taxa_canceladas_LA: Optional[float] = None
    pendencias_triagem_LA: Optional[int] = None
    media_tempo_resolvidos_pendencia_LA: Optional[float] = None
    mediana_tempo_resolvidos_pendencia_LA: Optional[float] = None
    comparativo_pendencias_resolvidas_LA: Optional[float] = None
    comparativo_tempo_medio_pendencias_resolvidas_LA: Optional[float] = None

    # Publicações LA (LexFlow)
    publicacoes_recebidas_periodo_LA: Optional[int] = None
    publicacoes_tratadas_periodo_LA: Optional[int] = None
    publicacoes_pendentes_LA: Optional[int] = None
    media_tempo_tratamento_publicacoes_LA: Optional[float] = None
    publicacoes_com_data_disponibilizacao_LA: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_chegada_LA: Optional[int] = None
    pct_tratadas_mesmo_dia_publicacoes_LA: Optional[float] = None
    dia_referencia_publicacoes_LA: Optional[str] = None
    publicacoes_tratadas_ultimo_dia_LA: Optional[int] = None
    publicacoes_recebidas_dia_referencia_LA: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_dia_referencia_LA: Optional[int] = None
    publicacoes_recebidas_hoje_LA: Optional[int] = None
    publicacoes_com_agendamento_apos_finalizacao_LA: Optional[int] = None
    publicacoes_sem_agendamento_apos_finalizacao_LA: Optional[int] = None
    publicacoes_pendentes_zeradas_no_periodo_LA: Optional[int] = None

    # Publicações NG (LexFlow)
    publicacoes_recebidas_periodo_NG: Optional[int] = None
    publicacoes_tratadas_periodo_NG: Optional[int] = None
    publicacoes_pendentes_NG: Optional[int] = None
    media_tempo_tratamento_publicacoes_NG: Optional[float] = None
    publicacoes_com_data_disponibilizacao_NG: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_chegada_NG: Optional[int] = None
    pct_tratadas_mesmo_dia_publicacoes_NG: Optional[float] = None
    dia_referencia_publicacoes_NG: Optional[str] = None
    publicacoes_tratadas_ultimo_dia_NG: Optional[int] = None
    publicacoes_recebidas_dia_referencia_NG: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_dia_referencia_NG: Optional[int] = None
    publicacoes_recebidas_hoje_NG: Optional[int] = None
    publicacoes_com_agendamento_apos_finalizacao_NG: Optional[int] = None
    publicacoes_sem_agendamento_apos_finalizacao_NG: Optional[int] = None
    publicacoes_pendentes_zeradas_no_periodo_NG: Optional[int] = None

    # Publicações RJ (LexFlow)
    publicacoes_recebidas_periodo_RJ: Optional[int] = None
    publicacoes_tratadas_periodo_RJ: Optional[int] = None
    publicacoes_pendentes_RJ: Optional[int] = None
    media_tempo_tratamento_publicacoes_RJ: Optional[float] = None
    publicacoes_com_data_disponibilizacao_RJ: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_chegada_RJ: Optional[int] = None
    pct_tratadas_mesmo_dia_publicacoes_RJ: Optional[float] = None
    dia_referencia_publicacoes_RJ: Optional[str] = None
    publicacoes_tratadas_ultimo_dia_RJ: Optional[int] = None
    publicacoes_recebidas_dia_referencia_RJ: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_dia_referencia_RJ: Optional[int] = None
    publicacoes_recebidas_hoje_RJ: Optional[int] = None
    publicacoes_com_agendamento_apos_finalizacao_RJ: Optional[int] = None
    publicacoes_sem_agendamento_apos_finalizacao_RJ: Optional[int] = None
    publicacoes_pendentes_zeradas_no_periodo_RJ: Optional[int] = None

    # NPS NG
    nps_total_respostas: Optional[int] = None
    nps_score: Optional[float] = None
    nps_taxa_confianca: Optional[float] = None
    nps_nivel_informacao: Optional[float] = None
    nps_nivel_indicacao: Optional[float] = None
    nps_media_tempo_resposta: Optional[float] = None
    nps_total_promotores: Optional[int] = None
    nps_total_neutros: Optional[int] = None
    nps_total_detratores: Optional[int] = None

    # Marketing NG
    marketing_ng_total_clientes: Optional[int] = None
    marketing_ng_media_idade: Optional[float] = None
    marketing_ng_triados_total_clientes: Optional[int] = None
    marketing_ng_triados_media_idade: Optional[float] = None
    marketing_ng_facebook_cliques: Optional[int] = None
    marketing_ng_facebook_pageview: Optional[int] = None
    marketing_ng_facebook_leads: Optional[int] = None
    marketing_ng_facebook_valor_gasto: Optional[float] = None
    marketing_ng_facebook_cac_campanha: Optional[float] = None
    marketing_ng_facebook_cac_geral: Optional[float] = None
    marketing_ng_facebook_roas_campanha: Optional[float] = None
    marketing_ng_facebook_roas_geral: Optional[float] = None
    marketing_ng_clientes_campanha: Optional[int] = None
    marketing_ng_leads: Optional[int] = None
    marketing_ng_indicacao_ativa: Optional[int] = None
    marketing_ng_indicacao_passiva: Optional[int] = None
    marketing_ng_retorno_ativa: Optional[int] = None
    marketing_ng_retorno_passiva: Optional[int] = None
    marketing_ng_campanha_ra: Optional[int] = None
    marketing_ng_campanha_ng: Optional[int] = None
    marketing_ng_conversao_ra: Optional[float] = None
    marketing_ng_conversao_ng: Optional[float] = None
    marketing_ng_protocolados_ra: Optional[int] = None
    marketing_ng_protocolados_ng: Optional[int] = None
    marketing_ng_valor_causa_ra: Optional[float] = None
    marketing_ng_valor_causa_ng: Optional[float] = None
    marketing_ng_ticket_medio_ra: Optional[float] = None
    marketing_ng_ticket_medio_ng: Optional[float] = None
    marketing_ng_total_trackeamento: Optional[int] = None
    marketing_ng_processos_assinados: Optional[int] = None
    marketing_ng_leads_ng: Optional[int] = None
    marketing_ng_acoes_ng: Optional[int] = None
    marketing_ng_aproveitamento_ng: Optional[float] = None
    marketing_ng_cpl_ng: Optional[float] = None
    marketing_ng_org_leads_facebook: Optional[int] = None
    marketing_ng_org_leads_instagram: Optional[int] = None
    marketing_ng_org_leads_site: Optional[int] = None
    marketing_ng_org_leads_google: Optional[int] = None
    marketing_ng_org_total_leads: Optional[int] = None
    marketing_ng_org_contratos: Optional[int] = None
    marketing_ng_org_acoes: Optional[int] = None
    marketing_ng_org_aproveitamento: Optional[float] = None
    marketing_ng_org_taxa_fechamento: Optional[float] = None
    marketing_ng_org_valor_causa: Optional[float] = None
    marketing_ng_org_ticket_medio: Optional[float] = None

    # Marketing LexPre NG (perfil de clientes)
    marketing_lexpre_ng_total_clientes: Optional[int] = None
    marketing_lexpre_ng_media_idade: Optional[float] = None
    marketing_lexpre_ng_triados_total_clientes: Optional[int] = None
    marketing_lexpre_ng_triados_media_idade: Optional[float] = None
    marketing_lexpre_ng_facebook_cliques: Optional[int] = None
    marketing_lexpre_ng_facebook_pageview: Optional[int] = None
    marketing_lexpre_ng_facebook_leads: Optional[int] = None
    marketing_lexpre_ng_facebook_valor_gasto: Optional[float] = None
    marketing_lexpre_ng_facebook_cac_campanha: Optional[float] = None
    marketing_lexpre_ng_facebook_cac_geral: Optional[float] = None
    marketing_lexpre_ng_facebook_roas_campanha: Optional[float] = None
    marketing_lexpre_ng_facebook_roas_geral: Optional[float] = None
    marketing_lexpre_ng_clientes_campanha: Optional[int] = None
    marketing_lexpre_ng_leads: Optional[int] = None
    marketing_lexpre_ng_indicacao_ativa: Optional[int] = None
    marketing_lexpre_ng_indicacao_passiva: Optional[int] = None
    marketing_lexpre_ng_retorno_ativa: Optional[int] = None
    marketing_lexpre_ng_retorno_passiva: Optional[int] = None
    marketing_lexpre_ng_campanha: Optional[int] = None
    marketing_lexpre_ng_conversao_campanha: Optional[float] = None
    marketing_lexpre_ng_protocolados_campanha: Optional[int] = None
    marketing_lexpre_ng_valor_causa_campanha: Optional[float] = None
    marketing_lexpre_ng_ticket_medio_campanha: Optional[float] = None
    marketing_lexpre_ng_total_trackeamento: Optional[int] = None
    marketing_lexpre_ng_processos_assinados: Optional[int] = None
    marketing_lexpre_ng_leads_campanha: Optional[int] = None
    marketing_lexpre_ng_acoes_campanha: Optional[int] = None
    marketing_lexpre_ng_aproveitamento_campanha: Optional[float] = None
    marketing_lexpre_ng_cpl_campanha: Optional[float] = None
    marketing_lexpre_ng_org_leads_facebook: Optional[int] = None
    marketing_lexpre_ng_org_leads_instagram: Optional[int] = None
    marketing_lexpre_ng_org_leads_site: Optional[int] = None
    marketing_lexpre_ng_org_leads_google: Optional[int] = None
    marketing_lexpre_ng_org_total_leads: Optional[int] = None
    marketing_lexpre_ng_org_contratos: Optional[int] = None
    marketing_lexpre_ng_org_acoes: Optional[int] = None
    marketing_lexpre_ng_org_aproveitamento: Optional[float] = None
    marketing_lexpre_ng_org_taxa_fechamento: Optional[float] = None
    marketing_lexpre_ng_org_valor_causa: Optional[float] = None
    marketing_lexpre_ng_org_ticket_medio: Optional[float] = None

    # Julgados NG
    julgados_sentenca_total_NG: Optional[int] = None
    julgados_sentenca_procedentes_NG: Optional[int] = None
    julgados_sentenca_improcedentes_NG: Optional[int] = None
    julgados_sentenca_extintos_NG: Optional[int] = None
    julgados_sentenca_tempo_medio_dias_NG: Optional[float] = None
    julgados_sentenca_embargos_tempo_medio_dias_NG: Optional[float] = None
    julgados_sentenca_valor_procedentes_NG: Optional[float] = None
    julgados_sentenca_embargados_NG: Optional[int] = None
    julgados_sentenca_revertidos_NG: Optional[int] = None
    comparativo_julgados_sentenca_total_NG: Optional[float] = None
    comparativo_julgados_sentenca_procedentes_NG: Optional[float] = None
    comparativo_julgados_sentenca_improcedentes_NG: Optional[float] = None
    comparativo_julgados_sentenca_extintos_NG: Optional[float] = None
    comparativo_julgados_sentenca_tempo_medio_dias_NG: Optional[float] = None
    comparativo_julgados_sentenca_valor_procedentes_NG: Optional[float] = None
    comparativo_julgados_sentenca_embargados_NG: Optional[float] = None
    comparativo_julgados_sentenca_revertidos_NG: Optional[float] = None
    julgados_uf_opcoes_NG: Optional[List[str]] = None
    julgados_sentenca_sem_juiz_NG: Optional[int] = None
    julgados_sentenca_sem_materia_NG: Optional[int] = None
    julgados_sentenca_sem_comarca_NG: Optional[int] = None
    julgados_sentenca_sem_competencia_NG: Optional[int] = None
    julgados_sentenca_sem_uf_NG: Optional[int] = None
    julgados_sentenca_sem_valor_pe_NG: Optional[int] = None
    julgados_sentenca_merito_sem_data_NG: Optional[int] = None
    julgados_sentenca_data_sem_merito_NG: Optional[int] = None
    julgados_sentenca_dados_faltando_NG: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças NG — Estudos de Extinção
    julgados_extincao_valor_NG: Optional[float] = None
    julgados_extincao_total_estoque_NG: Optional[int] = None
    julgados_extincao_valor_estoque_NG: Optional[float] = None
    julgados_comarca_opcoes_NG: Optional[List[str]] = None
    julgados_sentenca_total_estoque_NG: Optional[int] = None
    julgados_extincao_revertida_2g_NG: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_NG: Optional[int] = None
    # Julgados Sentenças NG — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_valor_NG: Optional[float] = None
    julgados_improcedencia_total_estoque_NG: Optional[int] = None
    julgados_improcedencia_valor_estoque_NG: Optional[float] = None
    julgados_improcedencia_revertida_2g_NG: Optional[int] = None
    julgados_improcedencia_revertida_2g_estoque_NG: Optional[int] = None
    # Julgados Acórdãos NG
    julgados_acordao_total_NG: Optional[int] = None
    julgados_acordao_procedentes_NG: Optional[int] = None
    julgados_acordao_improcedentes_NG: Optional[int] = None
    julgados_acordao_extintos_NG: Optional[int] = None
    julgados_acordao_nao_classificados_NG: Optional[int] = None
    julgados_acordao_tempo_medio_dias_NG: Optional[float] = None
    julgados_acordao_embargos_tempo_medio_dias_NG: Optional[float] = None
    julgados_acordao_valor_procedentes_NG: Optional[float] = None
    julgados_acordao_valor_fixado_procedentes_NG: Optional[float] = None
    julgados_acordao_embargados_NG: Optional[int] = None
    julgados_acordao_revertidos_NG: Optional[int] = None
    comparativo_julgados_acordao_total_NG: Optional[float] = None
    comparativo_julgados_acordao_procedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_improcedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_extintos_NG: Optional[float] = None
    comparativo_julgados_acordao_nao_classificados_NG: Optional[float] = None
    comparativo_julgados_acordao_tempo_medio_dias_NG: Optional[float] = None
    comparativo_julgados_acordao_valor_procedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_valor_fixado_procedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_embargados_NG: Optional[float] = None
    comparativo_julgados_acordao_revertidos_NG: Optional[float] = None
    julgados_acordao_uf_opcoes_NG: Optional[List[str]] = None
    julgados_acordao_sem_relator_NG: Optional[int] = None
    julgados_acordao_sem_materia_NG: Optional[int] = None
    julgados_acordao_sem_comarca_NG: Optional[int] = None
    julgados_acordao_sem_competencia_NG: Optional[int] = None
    julgados_acordao_sem_uf_NG: Optional[int] = None
    julgados_acordao_sem_valor_pe_NG: Optional[int] = None
    julgados_acordao_merito_sem_data_NG: Optional[int] = None
    julgados_acordao_data_sem_merito_NG: Optional[int] = None
    julgados_acordao_dados_faltando_NG: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Acórdãos NG — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_valor_NG: Optional[float] = None
    julgados_acordao_improcedencia_total_estoque_NG: Optional[int] = None
    julgados_acordao_improcedencia_valor_estoque_NG: Optional[float] = None
    julgados_acordao_improcedencia_stj_NG: Optional[int] = None
    julgados_acordao_improcedencia_stf_NG: Optional[int] = None
    julgados_acordao_improcedencia_stj_estoque_NG: Optional[int] = None
    julgados_acordao_improcedencia_stf_estoque_NG: Optional[int] = None
    julgados_acordao_total_estoque_NG: Optional[int] = None
    # Julgados Sentenças LA
    julgados_sentenca_total_LA: Optional[int] = None
    julgados_sentenca_procedentes_LA: Optional[int] = None
    julgados_sentenca_improcedentes_LA: Optional[int] = None
    julgados_sentenca_extintos_LA: Optional[int] = None
    julgados_sentenca_tempo_medio_dias_LA: Optional[float] = None
    julgados_sentenca_embargos_tempo_medio_dias_LA: Optional[float] = None
    julgados_sentenca_valor_procedentes_LA: Optional[float] = None
    julgados_sentenca_embargados_LA: Optional[int] = None
    julgados_sentenca_revertidos_LA: Optional[int] = None
    comparativo_julgados_sentenca_total_LA: Optional[float] = None
    comparativo_julgados_sentenca_procedentes_LA: Optional[float] = None
    comparativo_julgados_sentenca_improcedentes_LA: Optional[float] = None
    comparativo_julgados_sentenca_extintos_LA: Optional[float] = None
    comparativo_julgados_sentenca_tempo_medio_dias_LA: Optional[float] = None
    comparativo_julgados_sentenca_valor_procedentes_LA: Optional[float] = None
    comparativo_julgados_sentenca_embargados_LA: Optional[float] = None
    comparativo_julgados_sentenca_revertidos_LA: Optional[float] = None
    julgados_uf_opcoes_LA: Optional[List[str]] = None
    julgados_sentenca_sem_juiz_LA: Optional[int] = None
    julgados_sentenca_sem_materia_LA: Optional[int] = None
    julgados_sentenca_sem_comarca_LA: Optional[int] = None
    julgados_sentenca_sem_competencia_LA: Optional[int] = None
    julgados_sentenca_sem_uf_LA: Optional[int] = None
    julgados_sentenca_sem_valor_pe_LA: Optional[int] = None
    julgados_sentenca_merito_sem_data_LA: Optional[int] = None
    julgados_sentenca_data_sem_merito_LA: Optional[int] = None
    julgados_sentenca_dados_faltando_LA: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças LA — Estudos de Extinção
    julgados_extincao_valor_LA: Optional[float] = None
    julgados_extincao_total_estoque_LA: Optional[int] = None
    julgados_extincao_valor_estoque_LA: Optional[float] = None
    julgados_comarca_opcoes_LA: Optional[List[str]] = None
    julgados_sentenca_total_estoque_LA: Optional[int] = None
    julgados_extincao_revertida_2g_LA: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_LA: Optional[int] = None
    # Julgados Sentenças LA — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_valor_LA: Optional[float] = None
    julgados_improcedencia_total_estoque_LA: Optional[int] = None
    julgados_improcedencia_valor_estoque_LA: Optional[float] = None
    julgados_improcedencia_revertida_2g_LA: Optional[int] = None
    julgados_improcedencia_revertida_2g_estoque_LA: Optional[int] = None
    # Julgados Sentenças RJ
    julgados_sentenca_total_RJ: Optional[int] = None
    julgados_sentenca_procedentes_RJ: Optional[int] = None
    julgados_sentenca_improcedentes_RJ: Optional[int] = None
    julgados_sentenca_extintos_RJ: Optional[int] = None
    julgados_sentenca_tempo_medio_dias_RJ: Optional[float] = None
    julgados_sentenca_embargos_tempo_medio_dias_RJ: Optional[float] = None
    julgados_sentenca_valor_procedentes_RJ: Optional[float] = None
    julgados_sentenca_embargados_RJ: Optional[int] = None
    julgados_sentenca_revertidos_RJ: Optional[int] = None
    comparativo_julgados_sentenca_total_RJ: Optional[float] = None
    comparativo_julgados_sentenca_procedentes_RJ: Optional[float] = None
    comparativo_julgados_sentenca_improcedentes_RJ: Optional[float] = None
    comparativo_julgados_sentenca_extintos_RJ: Optional[float] = None
    comparativo_julgados_sentenca_tempo_medio_dias_RJ: Optional[float] = None
    comparativo_julgados_sentenca_valor_procedentes_RJ: Optional[float] = None
    comparativo_julgados_sentenca_embargados_RJ: Optional[float] = None
    comparativo_julgados_sentenca_revertidos_RJ: Optional[float] = None
    julgados_uf_opcoes_RJ: Optional[List[str]] = None
    julgados_sentenca_sem_juiz_RJ: Optional[int] = None
    julgados_sentenca_sem_materia_RJ: Optional[int] = None
    julgados_sentenca_sem_comarca_RJ: Optional[int] = None
    julgados_sentenca_sem_competencia_RJ: Optional[int] = None
    julgados_sentenca_sem_uf_RJ: Optional[int] = None
    julgados_sentenca_sem_valor_pe_RJ: Optional[int] = None
    julgados_sentenca_merito_sem_data_RJ: Optional[int] = None
    julgados_sentenca_data_sem_merito_RJ: Optional[int] = None
    julgados_sentenca_dados_faltando_RJ: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças RJ — Estudos de Extinção
    julgados_extincao_valor_RJ: Optional[float] = None
    julgados_extincao_total_estoque_RJ: Optional[int] = None
    julgados_extincao_valor_estoque_RJ: Optional[float] = None
    julgados_comarca_opcoes_RJ: Optional[List[str]] = None
    julgados_sentenca_total_estoque_RJ: Optional[int] = None
    julgados_extincao_revertida_2g_RJ: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_RJ: Optional[int] = None
    # Julgados Sentenças RJ — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_valor_RJ: Optional[float] = None
    julgados_improcedencia_total_estoque_RJ: Optional[int] = None
    julgados_improcedencia_valor_estoque_RJ: Optional[float] = None
    julgados_improcedencia_revertida_2g_RJ: Optional[int] = None
    julgados_improcedencia_revertida_2g_estoque_RJ: Optional[int] = None
    # Julgados Acórdãos LA
    julgados_acordao_total_LA: Optional[int] = None
    julgados_acordao_procedentes_LA: Optional[int] = None
    julgados_acordao_improcedentes_LA: Optional[int] = None
    julgados_acordao_extintos_LA: Optional[int] = None
    julgados_acordao_nao_classificados_LA: Optional[int] = None
    julgados_acordao_tempo_medio_dias_LA: Optional[float] = None
    julgados_acordao_embargos_tempo_medio_dias_LA: Optional[float] = None
    julgados_acordao_valor_procedentes_LA: Optional[float] = None
    julgados_acordao_valor_fixado_procedentes_LA: Optional[float] = None
    julgados_acordao_embargados_LA: Optional[int] = None
    julgados_acordao_revertidos_LA: Optional[int] = None
    comparativo_julgados_acordao_total_LA: Optional[float] = None
    comparativo_julgados_acordao_procedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_improcedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_extintos_LA: Optional[float] = None
    comparativo_julgados_acordao_nao_classificados_LA: Optional[float] = None
    comparativo_julgados_acordao_tempo_medio_dias_LA: Optional[float] = None
    comparativo_julgados_acordao_valor_procedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_valor_fixado_procedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_embargados_LA: Optional[float] = None
    comparativo_julgados_acordao_revertidos_LA: Optional[float] = None
    julgados_acordao_uf_opcoes_LA: Optional[List[str]] = None
    julgados_acordao_sem_relator_LA: Optional[int] = None
    julgados_acordao_sem_materia_LA: Optional[int] = None
    julgados_acordao_sem_comarca_LA: Optional[int] = None
    julgados_acordao_sem_competencia_LA: Optional[int] = None
    julgados_acordao_sem_uf_LA: Optional[int] = None
    julgados_acordao_sem_valor_pe_LA: Optional[int] = None
    julgados_acordao_merito_sem_data_LA: Optional[int] = None
    julgados_acordao_data_sem_merito_LA: Optional[int] = None
    julgados_acordao_dados_faltando_LA: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Acórdãos LA — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_valor_LA: Optional[float] = None
    julgados_acordao_improcedencia_total_estoque_LA: Optional[int] = None
    julgados_acordao_improcedencia_valor_estoque_LA: Optional[float] = None
    julgados_acordao_total_estoque_LA: Optional[int] = None
    # Julgados Acórdãos RJ
    julgados_acordao_total_RJ: Optional[int] = None
    julgados_acordao_procedentes_RJ: Optional[int] = None
    julgados_acordao_improcedentes_RJ: Optional[int] = None
    julgados_acordao_extintos_RJ: Optional[int] = None
    julgados_acordao_nao_classificados_RJ: Optional[int] = None
    julgados_acordao_tempo_medio_dias_RJ: Optional[float] = None
    julgados_acordao_embargos_tempo_medio_dias_RJ: Optional[float] = None
    julgados_acordao_valor_procedentes_RJ: Optional[float] = None
    julgados_acordao_valor_fixado_procedentes_RJ: Optional[float] = None
    julgados_acordao_embargados_RJ: Optional[int] = None
    julgados_acordao_revertidos_RJ: Optional[int] = None
    comparativo_julgados_acordao_total_RJ: Optional[float] = None
    comparativo_julgados_acordao_procedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_improcedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_extintos_RJ: Optional[float] = None
    comparativo_julgados_acordao_nao_classificados_RJ: Optional[float] = None
    comparativo_julgados_acordao_tempo_medio_dias_RJ: Optional[float] = None
    comparativo_julgados_acordao_valor_procedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_valor_fixado_procedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_embargados_RJ: Optional[float] = None
    comparativo_julgados_acordao_revertidos_RJ: Optional[float] = None
    julgados_acordao_uf_opcoes_RJ: Optional[List[str]] = None
    julgados_acordao_sem_relator_RJ: Optional[int] = None
    julgados_acordao_sem_materia_RJ: Optional[int] = None
    julgados_acordao_sem_comarca_RJ: Optional[int] = None
    julgados_acordao_sem_competencia_RJ: Optional[int] = None
    julgados_acordao_sem_uf_RJ: Optional[int] = None
    julgados_acordao_sem_valor_pe_RJ: Optional[int] = None
    julgados_acordao_merito_sem_data_RJ: Optional[int] = None
    julgados_acordao_data_sem_merito_RJ: Optional[int] = None
    julgados_acordao_dados_faltando_RJ: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Acórdãos RJ — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_valor_RJ: Optional[float] = None
    julgados_acordao_improcedencia_total_estoque_RJ: Optional[int] = None
    julgados_acordao_improcedencia_valor_estoque_RJ: Optional[float] = None
    julgados_acordao_total_estoque_RJ: Optional[int] = None


# v1: dashboard_routes.py:5810
class Activity(BaseModel):
    id: str
    type: str
    title: str
    description: str
    time: str
    user: str
    # Tickets: campos extraídos do log do Discord (opcionais para os demais usos)
    categoria: Optional[str] = None
    status: Optional[str] = None
    servidor: Optional[str] = None
    ticket_numero: Optional[str] = None
    anydesk: Optional[str] = None
    url: Optional[str] = None
    minutos_atras: Optional[int] = None


# v1: dashboard_routes.py:5827
class DashboardResponse(BaseModel):
    dashboard: str
    stats: DashboardStats

    # Tickets
    tickets_por_categoria: Optional[List[ChartDataPoint]] = None
    tickets_por_subcategoria: Optional[List[ChartDataPoint]] = None
    tickets_por_abertura: Optional[List[ChartDataPoint]] = None
    tickets_por_fechamento: Optional[List[ChartDataPoint]] = None
    tickets_por_mes: Optional[List[ChartDataPoint]] = None
    tickets_por_status: Optional[List[ChartDataPoint]] = None
    tickets_abertos_por_servidor: Optional[List[ChartDataPoint]] = None
    tickets_encerrados_por_servidor: Optional[List[ChartDataPoint]] = None
    recent_activities: Optional[List[Activity]] = None
    tickets_media_encerrados_por_colaborador: Optional[List[ChartDataPoint]] = None

    # Controle de Processo LA
    controle_processo_por_fase_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_por_fase_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_inicial_media_dias_por_mes_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_recursal_media_dias_por_mes_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_execucao_media_dias_por_mes_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_inicial_media_dias_por_mes_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_recursal_media_dias_por_mes_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_execucao_media_dias_por_mes_NG: Optional[List[ChartDataPoint]] = None
    estrategico_geral_fase_inicial_por_subfase: Optional[List[ChartDataPoint]] = None
    estrategico_geral_fase_recursal_por_subfase: Optional[List[ChartDataPoint]] = None
    estrategico_geral_fase_execucao_por_subfase: Optional[List[ChartDataPoint]] = None
    estrategico_geral_juridico_por_comarca: Optional[List[ChartDataPoint]] = None

    # Comercial Geral NG
    acoes_fechadas_por_atendente: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_diariamente: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_campanha_NG_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_campanha_RA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_indicacao_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_retorno_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_resgate_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_redes_sociais_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_site_por_rubrica: Optional[List[ChartDataPoint]] = None
    total_acoes_fechadas_por_rubrica: Optional[List[ChartDataPoint]] = None
    rubricas_total: Optional[List[RubricaTotalRow]] = None
    comissionamento_comercial_por_atendente: Optional[List[ComissionamentoComercialRow]] = None
    comissionamento_comercial_LA_por_atendente: Optional[List[ComissionamentoComercialLARow]] = None
    contratos_fechados_diariamente_por_atendente: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_mes: Optional[List[ChartDataPoint]] = None
    processos_fechados_por_mes: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_dia: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_por_dia: Optional[List[ChartDataPoint]] = None
    total_leads_por_atendente: Optional[TotalLeadsPorAtendente] = None
    total_leads_campanha_por_atendente: Optional[TotalLeadsCampanhaPorAtendente] = None
    total_clientes_fechados_por_atendente: Optional[TotalClientesFechadosPorAtendente] = None
    total_clientes_fechados_campanha_por_atendente: Optional[TotalClientesFechadosCampanhaPorAtendente] = None
    taxa_fechamento_geral_por_atendente: Optional[TaxaFechamentoGeralPorAtendente] = None
    taxa_fechamento_campanha_por_cliente: Optional[TaxaFechamentoCampanhaPorCliente] = None
    valor_causa_protocolo_novo_por_atendente: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolo_nao_protocolado_por_atendente: Optional[List[ChartDataPoint]] = None
    protocolos_resolvidos_por_atendente: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_atendente: Optional[List[ChartDataPoint]] = None
    total_leads_indicacao_ativa_por_atendente: Optional[TotalLeadsIndicacaoAtivaPorAtendente] = None
    total_clientes_fechados_indicacao_ativa_por_atendente: Optional[TotalClientesFechadosIndicacaoAtivaPorAtendente] = None
    taxa_fechamento_indicacao_ativa_por_atendente: Optional[TaxaFechamentoIndicacaoAtivaPorAtendente] = None
    total_leads_indicacao_passiva_por_atendente: Optional[TotalLeadsIndicacaoPassivaPorAtendente] = None
    total_clientes_fechados_indicacao_passiva_por_atendente: Optional[TotalClientesFechadosIndicacaoPassivaPorAtendente] = None
    taxa_fechamento_indicacao_passiva_por_atendente: Optional[TaxaFechamentoIndicacaoPassivaPorAtendente] = None
    total_leads_retorno_ativa_por_atendente: Optional[TotalLeadsRetornoAtivaPorAtendente] = None
    total_clientes_fechados_retorno_ativa_por_atendente: Optional[TotalClientesFechadosRetornoAtivaPorAtendente] = None
    taxa_fechamento_retorno_ativa_por_atendente: Optional[TaxaFechamentoRetornoAtivaPorAtendente] = None
    total_leads_retorno_passiva_por_atendente: Optional[TotalLeadsRetornoPassivaPorAtendente] = None
    total_clientes_fechados_retorno_passiva_por_atendente: Optional[TotalClientesFechadosRetornoPassivaPorAtendente] = None
    taxa_fechamento_retorno_passiva_por_atendente: Optional[TaxaFechamentoRetornoPassivaPorAtendente] = None
    total_leads_resgate_ativa_por_atendente: Optional[TotalLeadsResgateAtivaPorAtendente] = None
    total_clientes_fechados_resgate_ativa_por_atendente: Optional[TotalClientesFechadosResgateAtivaPorAtendente] = None
    taxa_fechamento_resgate_ativa_por_atendente: Optional[TaxaFechamentoResgateAtivaPorAtendente] = None
    total_leads_resgate_passiva_por_atendente: Optional[TotalLeadsResgatePassivaPorAtendente] = None
    total_clientes_fechados_resgate_passiva_por_atendente: Optional[TotalClientesFechadosResgatePassivaPorAtendente] = None
    taxa_fechamento_resgate_passiva_por_atendente: Optional[TaxaFechamentoResgatePassivaPorAtendente] = None
    nao_peticionados_por_atendente: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_atendente: Optional[List[ChartDataPoint]] = None
    pendencias_nao_resolvidas_por_atendente: Optional[List[ChartDataPoint]] = None
    protocolos_resolvidos_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    pendencias_nao_resolvidas_por_atendente_expandido: Optional[List[ChartDataPoint]] = None

    # Comercial LA
    acoes_fechadas_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_diariamente_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    contratos_fechados_diariamente_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    processos_fechados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolado_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_nao_protocolado_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    protocolos_resolvidos_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    pendencias_nao_resolvidas_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    total_acoes_fechadas_por_rubrica_LA: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_campanha_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_indicacao_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_retorno_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_redes_sociais_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_parceiros_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_externos_LA_por_rubrica: Optional[List[ChartDataPoint]] = None

    # Andamento Processual NG
    andamento_processual_total_por_mes: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador_avaliacao: Optional[List[ChartDataPoint]] = None
    comissionamento_andamento_por_funcionario: Optional[List[ComissionamentoAndamentoRow]] = None

    # Andamento Processual LA
    andamento_processual_total_por_mes_LA: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador_LA: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador_avaliacao_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_andamento_LA_por_funcionario: Optional[List[ComissionamentoAndamentoRow]] = None

    # Pendências NG
    pendencias_nao_resolvidas_por_origem: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_mes: Optional[List[ChartDataPoint]] = None
    media_pendencias_resolvidas_por_funcionario: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_dia: Optional[List[ChartDataPoint]] = None
    funcionarios_pendencias: Optional[List[str]] = None
    pendencias_resolvidas_por_dia_por_funcionario: Optional[Dict[str, List[ChartDataPoint]]] = None
    comissionamento_pendencias_por_funcionario: Optional[List[ComissionamentoPendenciaRow]] = None

    # Pendências LA
    pendencias_nao_resolvidas_por_origem_LA: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    media_pendencias_resolvidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_pendencias_LA: Optional[List[str]] = None
    pendencias_resolvidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    comissionamento_pendencias_LA_por_funcionario: Optional[List[ComissionamentoPendenciaRow]] = None

    # Org. Documentos NG
    resolvidos_total_por_materia: Optional[List[ChartDataPoint]] = None
    nao_organizados_total_por_materia: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_funcionario: Optional[List[ChartDataPoint]] = None
    resolvidos_por_funcionario: Optional[List[ChartDataPoint]] = None
    media_resolvidos_por_funcionario: Optional[List[ChartDataPoint]] = None
    resolvidos_total_por_mes: Optional[List[ChartDataPoint]] = None
    valor_causa_por_funcionario: Optional[List[ChartDataPoint]] = None
    comissionamento_por_funcionario: Optional[List[ComissionamentoOrgDocRow]] = None
    nao_resolvidos_total_por_mes: Optional[List[ChartDataPoint]] = None
    resolvidos_por_dia_org: Optional[List[ChartDataPoint]] = None
    funcionarios_org_doc: Optional[List[str]] = None                                # CORRIGIDO: sem duplicatas
    resolvidos_por_dia_por_funcionario_org: Optional[Dict[str, List[ChartDataPoint]]] = None  # CORRIGIDO: sem duplicatas

    # Org. Documentos LA
    nao_organizados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    organizados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_org_doc_LA_por_funcionario: Optional[List[ComissionamentoOrgDocRow]] = None
    media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    organizados_total_por_materia_LA: Optional[List[ChartDataPoint]] = None
    nao_organizados_total_por_materia_LA: Optional[List[ChartDataPoint]] = None
    resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_org_doc_LA: Optional[List[str]] = None
    resolvidos_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    nao_organizados_total_por_mes_LA: Optional[List[ChartDataPoint]] = None
    resolvidos_total_por_mes_LA: Optional[List[ChartDataPoint]] = None

    # Protocolo NG
    protocolados_por_materia: Optional[List[ChartDataPoint]] = None
    protocolados_por_funcionario: Optional[List[ChartDataPoint]] = None
    protocolados_por_sistema: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_materia: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_funcionario: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolo_novo_por_funcionario: Optional[List[ChartDataPoint]] = None
    media_protocolados_por_funcionario: Optional[List[ChartDataPoint]] = None
    comissionamento_protocolo_por_funcionario: Optional[List[ComissionamentoProtocoloRow]] = None
    protocolados_por_mes: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_mes: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_mes: Optional[List[ChartDataPoint]] = None
    protocolados_por_dia: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_dia: Optional[List[ChartDataPoint]] = None
    funcionarios_protocolo: Optional[List[str]] = None
    protocolados_por_dia_por_funcionario: Optional[Dict[str, List[ChartDataPoint]]] = None

    # Peticionamento NG
    peticionados_por_materia: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_materia: Optional[List[ChartDataPoint]] = None
    peticionados_por_dia: Optional[List[ChartDataPoint]] = None
    funcionarios_peticionamento: Optional[List[str]] = None
    peticionados_por_dia_por_funcionario: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_peticionado_por_funcionario: Optional[List[ChartDataPoint]] = None
    valor_peticionado_por_funcionario: Optional[List[ChartDataPoint]] = None
    peticionados_por_funcionario: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_funcionario: Optional[List[ChartDataPoint]] = None
    peticionados_por_mes: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_mes: Optional[List[ChartDataPoint]] = None
    comissionamento_peticionamento_por_funcionario: Optional[List[ComissionamentoPeticionamentoRow]] = None

    # Protocolo LA
    protocolados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    protocololados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    represados_protocolo_por_materia_LA: Optional[List[ChartDataPoint]] = None
    represados_protocolo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_protocolo_LA_por_funcionario: Optional[List[ComissionamentoProtocoloRow]] = None
    protocolados_por_sistema_LA: Optional[List[ChartDataPoint]] = None
    protocolados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    represados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    media_protocolados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    protocolados_por_funcionario_por_dia_LA: Optional[List[ChartDataPoint]] = None
    protocolados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_protocolo_LA: Optional[List[str]] = None
    protocolados_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None

    # Peticionamento LA
    confeccionados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    nao_confeccionados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    confeccionados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    nao_confeccionados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    valor_confeccionado_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    media_confeccionado_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    confeccionados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_confeccao_LA: Optional[List[str]] = None
    confeccionados_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    confeccionados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    nao_confeccionados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_peticionamento_LA_por_funcionario: Optional[List[ComissionamentoPeticionamentoRow]] = None

    # Publicações LA
    publicacoes_recebidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_tratadas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tribunal_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tipo_documento_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_materia_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_orgao_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_cumprido_por_leitor_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_leitor_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_dias_atraso_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_setor_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    comissionamento_publicacoes_LA_por_funcionario: Optional[List[ComissionamentoPublicacaoRow]] = None

    # Publicações NG
    publicacoes_recebidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_tratadas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_visualizadas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tribunal_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tipo_documento_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_materia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_orgao_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_cumprido_por_leitor_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_leitor_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_dias_atraso_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_setor_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    comissionamento_publicacoes_NG_por_funcionario: Optional[List[ComissionamentoPublicacaoRow]] = None

    # Publicações RJ
    publicacoes_recebidas_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_tratadas_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_visualizadas_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tribunal_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tipo_documento_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_orgao_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_cumprido_por_leitor_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_leitor_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_dias_atraso_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_setor_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    comissionamento_publicacoes_RJ_por_funcionario: Optional[List[ComissionamentoPublicacaoRow]] = None

    # Execução NG
    execucao_por_subfase: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_subfase: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_total: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_entrada: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_saida: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_total: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_entrada: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_saida: Optional[List[ChartDataPoint]] = None
    execucao_por_materia: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_materia: Optional[List[ChartDataPoint]] = None
    execucao_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    execucao_por_faixa_ultima_movimentacao: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    valor_execucao_saida_periodo_por_mes: Optional[List[ChartDataPoint]] = None
    valor_remanescente_por_mes: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_media_tempo_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_estoque_quantidade_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_estoque_valor_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_criadas_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_taxa_conclusao_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_entrada_fluxo_cs_por_mes_NG: Optional[List[Dict[str, Any]]] = None
    execucao_alvara_expedido_lista_NG: Optional[List[Dict[str, Any]]] = None
    execucao_alvaras_expedidos_por_dia_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvaras_expedidos_por_dia_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvara_expedido_lista_NG: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_valor_recuperado_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_NG: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_nao_cumprido_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_abertas_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_por_prazo_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atividades_lista_filtros_opcoes_por_prazo_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atrasos_detalhamento_NG: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_diligencias_por_processo_NG: Optional[List[ChartDataPoint]] = None
    execucao_diligencias_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_diligencias_expedicao_alvara_processos_NG: Optional[List[ExecucaoAcordosListaRow]] = None

    # Execução RJ (Condenação)
    execucao_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_saida_periodo_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_remanescente_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_media_tempo_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_estoque_quantidade_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_estoque_valor_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_atividades_criadas_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_taxa_conclusao_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_entrada_fluxo_cs_por_mes_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_alvara_expedido_lista_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_alvaras_expedidos_por_dia_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvaras_expedidos_por_dia_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvara_expedido_lista_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_atividades_abertas_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_ativas_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_demandas_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_valor_recuperado_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_nao_cumprido_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_atividades_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_por_prazo_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_filtros_opcoes_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atividades_lista_filtros_opcoes_por_prazo_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atrasos_detalhamento_RJ: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_diligencias_por_processo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_diligencias_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_diligencias_expedicao_alvara_processos_RJ: Optional[List[ExecucaoAcordosListaRow]] = None

    # Execução Acordos NG
    execucao_acordos_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_total_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_entrada_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_saida_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_total_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_entrada_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_saida_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_materia_NG: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_materia_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_tipo_acao_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_sentenca_NG: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_tempo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_quantidade_por_mes_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_valor_por_mes_NG: Optional[List[ChartDataPoint]] = None
    fechamento_acordo_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    valor_fechamento_acordo_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_lista_entrada_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_saida_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_total_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_resolvidos_por_dia_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_resolvidos_por_dia_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_nao_cumprido_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_por_prazo_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atrasos_detalhamento_NG: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_acordos_diligencias_por_processo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_diligencias_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_diligencias_expedicao_alvara_processos_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_materia_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_materia_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_tipo_acao_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_sentenca_LA: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_tempo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_quantidade_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_valor_por_mes_LA: Optional[List[ChartDataPoint]] = None
    fechamento_acordo_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    valor_fechamento_acordo_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_lista_entrada_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_saida_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_total_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_resolvidos_por_dia_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_nao_cumprido_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_por_prazo_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atrasos_detalhamento_LA: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_acordos_diligencias_por_processo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_diligencias_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_diligencias_expedicao_alvara_processos_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_tipo_acao_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_sentenca_RJ: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_tempo_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_quantidade_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_valor_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    fechamento_acordo_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    valor_fechamento_acordo_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_lista_entrada_RJ: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_saida_RJ: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_total_RJ: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_processos_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_processos_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_demandas_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_resolvidos_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_resolvidos_por_dia_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_nao_cumprido_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_por_prazo_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_filtros_opcoes_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atrasos_detalhamento_RJ: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_acordos_diligencias_por_processo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_diligencias_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_diligencias_expedicao_alvara_processos_RJ: Optional[List[ExecucaoAcordosListaRow]] = None

    # Execução LA
    execucao_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_status_1g_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_status_2g_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_materia_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_competencia_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_vara_LA: Optional[List[ChartDataPoint]] = None
    recursal_decisoes_LA: Optional[List[ChartDataPoint]] = None
    recursal_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    recursal_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    recursal_resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    recursal_resolvidos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_recursal_LA: Optional[List[str]] = None
    recursal_resolvidos_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    recursal_media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    recursal_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    recursal_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    ranking_juizes_recursal_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    # Recursal NG
    recursal_por_status_1g_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_status_2g_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_materia_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_competencia_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_vara_NG: Optional[List[ChartDataPoint]] = None
    recursal_decisoes_NG: Optional[List[ChartDataPoint]] = None
    recursal_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    recursal_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    recursal_resolvidos_por_dia_NG: Optional[List[ChartDataPoint]] = None
    recursal_resolvidos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_recursal_NG: Optional[List[str]] = None
    recursal_resolvidos_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    recursal_media_resolvidos_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    recursal_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    recursal_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    ranking_juizes_recursal_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    ranking_relatores_recursal_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    # Recursal RJ
    recursal_por_status_1g_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_status_2g_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_competencia_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_vara_RJ: Optional[List[ChartDataPoint]] = None
    recursal_decisoes_RJ: Optional[List[ChartDataPoint]] = None
    recursal_processos_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    recursal_demandas_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    recursal_resolvidos_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    recursal_resolvidos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    funcionarios_recursal_RJ: Optional[List[str]] = None
    recursal_resolvidos_por_dia_por_funcionario_RJ: Optional[Dict[str, List[ChartDataPoint]]] = None
    recursal_media_resolvidos_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    recursal_atividades_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    recursal_atividades_lista_filtros_opcoes_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    ranking_juizes_recursal_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    ranking_relatores_recursal_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    # Julgados NG
    ranking_juizes_sentenca_julgados_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_por_materia_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_competencia_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_motivo_extincao_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_motivo_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_estoque_NG: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças NG — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_comarca_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_NG: Optional[List[JulgadosSentencaListaRow]] = None
    # Julgados Acórdãos NG
    ranking_relatores_acordao_julgados_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_acordao_por_materia_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_competencia_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_motivo_extincao_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_embargos_resultado_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_procedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_extintos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_lista_NG: Optional[List[JulgadosAcordaoListaRow]] = None
    # Julgados Acórdãos NG — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_comarca_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_estoque_NG: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças LA
    ranking_juizes_sentenca_julgados_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_competencia_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_motivo_extincao_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_motivo_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_estoque_LA: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças LA — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_comarca_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_LA: Optional[List[JulgadosSentencaListaRow]] = None
    # Julgados Sentenças RJ
    ranking_juizes_sentenca_julgados_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_competencia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_motivo_extincao_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_motivo_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_estoque_RJ: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças RJ — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_comarca_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_RJ: Optional[List[JulgadosSentencaListaRow]] = None
    # Julgados Acórdãos LA
    ranking_relatores_acordao_julgados_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_acordao_por_materia_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_competencia_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_motivo_extincao_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_embargos_resultado_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_procedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_extintos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_lista_LA: Optional[List[JulgadosAcordaoListaRow]] = None
    # Julgados Acórdãos LA — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_comarca_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_estoque_LA: Optional[List[ChartDataPoint]] = None
    # Julgados Acórdãos RJ
    ranking_relatores_acordao_julgados_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_acordao_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_competencia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_motivo_extincao_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_embargos_resultado_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_procedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_extintos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_lista_RJ: Optional[List[JulgadosAcordaoListaRow]] = None
    # Julgados Acórdãos RJ — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_comarca_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_estoque_RJ: Optional[List[ChartDataPoint]] = None
    # Pendências Intermediárias LA
    intermediarias_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    intermediarias_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    intermediarias_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    dilacoes_intermediarias_por_funcionario_LA: Optional[List[DilacaoPorFuncionarioRow]] = None
    intermediarias_por_prazo_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_por_prazo_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    intermediarias_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_LA: Optional[List[str]] = None
    intermediarias_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_por_prazo_LA: Optional[List[str]] = None
    intermediarias_concluidas_por_prazo_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_prazo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    # Pendências Intermediárias NG
    intermediarias_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    intermediarias_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    intermediarias_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    dilacoes_intermediarias_por_funcionario_NG: Optional[List[DilacaoPorFuncionarioRow]] = None
    intermediarias_por_prazo_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_por_prazo_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    intermediarias_concluidas_por_mes_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_NG: Optional[List[str]] = None
    intermediarias_concluidas_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_por_prazo_NG: Optional[List[str]] = None
    intermediarias_concluidas_por_prazo_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_prazo_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    # Emendas e Manifestações LA
    emendas_manifestacoes_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_por_prazo_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_por_prazo_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_LA: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_por_prazo_LA: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_comissionamento_por_funcionario_LA: Optional[List[EmendasManifestacoesComissaoRow]] = None
    # Emendas e Manifestações NG
    emendas_manifestacoes_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_por_prazo_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_por_prazo_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_concluidas_por_mes_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_NG: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_por_prazo_NG: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_comissionamento_por_funcionario_NG: Optional[List[EmendasManifestacoesComissaoRow]] = None
    # Réplicas LA
    replicas_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    replicas_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    replicas_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_por_prazo_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_por_prazo_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_LA: Optional[List[str]] = None
    replicas_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_por_prazo_LA: Optional[List[str]] = None
    replicas_concluidas_por_prazo_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_prazo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    replicas_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    replicas_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    replicas_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_por_prazo_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_por_prazo_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_concluidas_por_mes_NG: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_NG: Optional[List[str]] = None
    replicas_concluidas_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_por_prazo_NG: Optional[List[str]] = None
    replicas_concluidas_por_prazo_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_prazo_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    # Reajuizamento LA
    reajuizamento_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    reajuizamento_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    reajuizamento_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    reajuizamento_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_reajuizamento_LA: Optional[List[str]] = None
    reajuizamento_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_reajuizamento_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_motivo_extincao_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_status_processo_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_extincao_por_grau_LA: Optional[List[ChartDataPoint]] = None
    ranking_relatores_recursal_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    execucao_por_materia_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_materia_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_faixa_ultima_movimentacao_LA: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_saida_periodo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_remanescente_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_media_tempo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_estoque_quantidade_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_estoque_valor_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_criadas_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_taxa_conclusao_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_entrada_fluxo_cs_por_mes_LA: Optional[List[Dict[str, Any]]] = None
    execucao_alvara_expedido_lista_LA: Optional[List[Dict[str, Any]]] = None
    execucao_alvaras_expedidos_por_dia_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvaras_expedidos_por_dia_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvara_expedido_lista_LA: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_valor_recuperado_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_nao_cumprido_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_abertas_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_por_prazo_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atividades_lista_filtros_opcoes_por_prazo_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atrasos_detalhamento_LA: Optional[ExecucaoAtrasosDetalhamento] = None

    # NPS NG
    nps_por_classificacao: Optional[List[ChartDataPoint]] = None
    nps_por_nota: Optional[List[ChartDataPoint]] = None
    nps_por_mes: Optional[List[ChartDataPoint]] = None
    nps_respostas_tabela: Optional[List[NpsRespostaRow]] = None
    nps_feedbacks_melhoria: Optional[List[NpsFeedbackMelhoriaRow]] = None
    nps_feedbacks_positivos: Optional[List[NpsFeedbackPositivoRow]] = None
    nps_comentarios: Optional[List[NpsComentarioRow]] = None

    # Marketing NG
    marketing_ng_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_ng_genero: Optional[List[ChartDataPoint]] = None
    marketing_ng_origem: Optional[List[ChartDataPoint]] = None
    marketing_ng_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_ng_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_ng_dispositivo: Optional[List[ChartDataPoint]] = None
    marketing_ng_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_ng_faixa_salarial: Optional[List[ChartDataPoint]] = None

    # Marketing NG · Triados
    marketing_ng_triados_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_genero: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_origem: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_dispositivo: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_faixa_salarial: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_tipo_residencia: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_pessoas_dependentes: Optional[List[ChartDataPoint]] = None
    marketing_ng_funil_pipeline: Optional[List[ChartDataPoint]] = None
    marketing_ng_investimento_cliques_leads: Optional[List[InvestimentoCliquesLeadsPoint]] = None
    marketing_ng_rubrica_campanha: Optional[List[RubricaCampanhaPoint]] = None
    marketing_ng_rubrica_protocolado: Optional[List[RubricaCampanhaPoint]] = None
    marketing_ng_total_clientes_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_protocolo_resolvido_total: Optional[List[ChartDataPoint]] = None
    marketing_ng_valor_causa_total: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_criativo: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_rubricas: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_criativo: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_total: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_facebook: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_instagram: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_site: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_google: Optional[List[ChartDataPoint]] = None

    # Marketing LexPre NG (perfil de clientes)
    marketing_lexpre_ng_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_genero: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_origem: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_faixa_salarial: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_genero: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_origem: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_faixa_salarial: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_tipo_residencia: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_pessoas_dependentes: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_investimento_cliques_leads: Optional[List[InvestimentoCliquesLeadsPoint]] = None
    marketing_lexpre_ng_total_clientes_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_protocolo_resolvido_total: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_valor_causa_total: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_rubrica_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_rubrica_protocolado: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_criativo: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_criativo: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_total: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_facebook: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_instagram: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_site: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_google: Optional[List[ChartDataPoint]] = None


# v1: dashboard_routes.py:7457
def _estoque_mensal_charts(
    quantidade_valor: Tuple[List[Dict[str, Any]], List[Dict[str, Any]]],
    chave_quantidade: str,
    chave_valor: str,
) -> Dict[str, List[ChartDataPoint]]:
    quantidade, valor = quantidade_valor
    return {
        chave_quantidade: [ChartDataPoint(**x) for x in quantidade],
        chave_valor: [ChartDataPoint(**x) for x in valor],
    }


# v1: dashboard_routes.py:7469
def _build_execucao_stats(
    execucao: List[Dict],
    all_execucao: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    execucao_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    diligencia_tipo_filtro: Optional[str] = None,
    diligencia_colaborador_filtro: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder para o domínio Execução NG.

    execucao     → dados filtrados por DATA_EXECUCAO (via filter_data)
    all_execucao → dados sem filtro de data (necessário para calcular saídas no período,
                   pois DATA_SAIDA não é a coluna usada pelo filter_data deste domínio)
    agendamentos → agendamentos do setor Execução NG para a seção Atividades

    Quando filtros de agendamento estão ativos, os dados de processo são restritos
    aos processos que possuem agendamentos correspondentes — todas as seções refletem
    o mesmo recorte.
    """
    # Antes do recorte por filtro de atividade abaixo: o gráfico de fluxo não deve
    # encolher quando a Confecção CS está filtrada.
    entrada_fluxo_cs_por_mes = (
        group_entrada_execucao_por_fluxo_cs_por_mes_NG(all_execucao, agendamentos)
        if agendamentos is not None
        else None
    )
    # Antes do recorte por filtro de atividade (mesmo motivo do gráfico de fluxo).
    taxa_atualizacao = (
        get_taxa_atualizacao_execucao_NG(all_execucao, agendamentos, from_date, to_date)
        if agendamentos is not None
        else None
    )
    alvara_expedido_lista = list_processos_alvara_expedido_NG(all_execucao)
    ag_filtrados: Optional[List[Dict]] = None
    if agendamentos is not None:
        ag_filtrados = filtrar_agendamentos_execucao_NG(
            agendamentos,
            execucao_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        if execucao_atividades_filtros is not None and execucao_atividades_filtros.ativo():
            processo_ids = frozenset(
                pid
                for row in ag_filtrados
                if (pid := _get_ag_processo_id_ng(row)) is not None
            )
            if processo_ids:
                execucao = [r for r in execucao if (r.get("id") or r.get("ID")) in processo_ids]
                all_execucao = [r for r in all_execucao if (r.get("id") or r.get("ID")) in processo_ids]
            else:
                execucao = []
                all_execucao = []

    # Sem período (statsSemFiltro) = leitura "Total em Execução" (estoque atual,
    # restrito a ID_FASE == 12); com período (stats) = leitura "Quantidade de
    # entrada" (sem restrição de fase atual, para bater com o gráfico mensal e o
    # cálculo de estoque). Usado tanto no KPI quanto nos gráficos "por matéria"
    # abaixo, que têm o mesmo dual-propósito conforme o modo Total/Qtd Entrada
    # selecionado no front.
    _sem_periodo = from_date is None or to_date is None
    stats = {
        "total_em_execucao": (
            get_total_execucao(execucao)
            if _sem_periodo
            else len(_filtrar_entrada_execucao_no_periodo_ng(execucao))
        ),
        "valor_total_em_execucao": get_valor_causa_total_execucao(execucao),
        "total_valor_execucao_vazio": get_total_valor_execucao_vazio(execucao),
        "total_valor_execucao_vazio_detalhe": get_detalhe_valor_execucao_vazio(execucao),
        "valor_honorarios_total_execucao": get_valor_honorarios_total_execucao(
            execucao
        ),
        "valor_em_execucao": get_valor_em_execucao(execucao),
        "valor_remanescente_em_execucao": get_valor_remanescente_em_execucao(execucao),
        "estoque_inicial": get_estoque_final(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "tre": get_tre_execucao_dax(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "total_saida_execucao_periodo": get_total_saida_execucao_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "total_incontroverso_saida_execucao_periodo": get_total_incontroverso_saida_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_execucao_saida_periodo": get_valor_execucao_saida_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_incontroverso_saida_execucao_periodo": get_valor_incontroverso_saida_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_ted_saida_execucao_periodo": get_valor_ted_saida_execucao_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "taxa_recuperacao_execucao": get_taxa_recuperacao_execucao(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "taxa_atualizacao_execucao_NG": taxa_atualizacao,
        "media_tempo_execucao": get_media_tempo_execucao(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        # Durações (dias) das saídas do período — o Estratégico Geral junta Condenação + Acordos
        # para calcular média/mediana do conjunto (somar as duas médias/medianas não vale).
        "duracoes_tempo_execucao_NG": _duracoes_execucao_ng(all_execucao, from_date, to_date),
        "mediana_tempo_execucao": get_mediana_tempo_execucao(
            all_execucao, from_date=from_date, to_date=to_date
        ),
    }
    charts = {
        "execucao_entrada_fluxo_cs_por_mes_NG": entrada_fluxo_cs_por_mes,
        "execucao_alvara_expedido_lista_NG": alvara_expedido_lista,
        "execucao_alvaras_expedidos_por_dia_NG": group_alvaras_expedidos_por_dia_NG(all_execucao),
        "execucao_por_subfase": [
            ChartDataPoint(**x) for x in group_execucao_por_subfase(execucao)
        ],
        "valor_execucao_por_subfase": [
            ChartDataPoint(**x) for x in group_valor_execucao_por_subfase(execucao)
        ],
        "execucao_por_comarca_total": [
            ChartDataPoint(**x)
            for x in group_execucao_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_por_comarca_entrada": [
            ChartDataPoint(**x)
            for x in group_execucao_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_por_comarca_saida": [
            ChartDataPoint(**x)
            for x in group_execucao_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_valor_por_comarca_total": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_valor_por_comarca_entrada": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_valor_por_comarca_saida": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_por_materia": [
            ChartDataPoint(**x)
            for x in group_execucao_por_materia(execucao, restringir_fase_atual=_sem_periodo)
        ],
        "valor_execucao_por_materia": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_materia(execucao, restringir_fase_atual=_sem_periodo)
        ],
        "execucao_por_ano_ajuizamento_NG": [
            ChartDataPoint(**x)
            for x in group_execucao_por_ano_ajuizamento_NG(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        **_estoque_mensal_charts(group_estoque_execucao_por_mes(all_execucao), "execucao_estoque_quantidade_por_mes", "execucao_estoque_valor_por_mes"),
        "execucao_media_tempo_por_mes": [
            ChartDataPoint(**x) for x in get_media_tempo_execucao_por_mes(all_execucao)
        ],
        "valor_saida_execucao_por_mes": [
            ChartDataPoint(**x)
            for x in group_valor_saida_execucao_por_mes(all_execucao)
        ],
        "valor_execucao_saida_periodo_por_mes": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_saida_periodo_por_mes(all_execucao)
        ],
        "valor_remanescente_por_mes": [
            ChartDataPoint(**x)
            for x in group_valor_remanescente_por_mes(all_execucao)
        ],
        "quantidade_saida_execucao_por_mes": [
            ChartDataPoint(**x)
            for x in group_quantidade_saida_execucao_por_mes(all_execucao)
        ],
        "quantidade_entrada_execucao_por_mes": [
            ChartDataPoint(**x)
            for x in group_quantidade_entrada_execucao_por_mes(all_execucao)
        ],
        "valor_entrada_execucao_por_mes": [
            ChartDataPoint(**x)
            for x in group_valor_entrada_execucao_por_mes(all_execucao)
        ],
    }

    if ag_filtrados is not None:
        stats.update(get_kpis_atividades_execucao_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats.update(get_kpis_execucao_por_prazo_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["media_mensal_atividades_execucao_NG"] = get_media_mensal_atividades_execucao_NG(
            ag_filtrados
        )
        charts["execucao_processos_por_atividade_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_ativas_por_atividade_NG"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_criadas_por_atividade_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_criadas_por_atividade_NG"] = [
            ChartDataPoint(**x)
            for x in group_atividades_criadas_por_atividade_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_processos_por_atividade_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_por_prazo_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_ativas_por_atividade_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_por_prazo_por_atividade_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_demandas_por_funcionario_NG"] = group_execucao_demandas_por_funcionario_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_completo_NG"] = group_execucao_demandas_por_funcionario_completo_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_taxa_conclusao_por_funcionario_NG"] = group_taxa_conclusao_por_funcionario_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_por_prazo_NG"] = group_execucao_demandas_por_funcionario_por_prazo_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_por_prazo_completo_NG"] = group_execucao_demandas_por_funcionario_por_prazo_completo_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_valor_recuperado_por_funcionario_NG"] = [
            ChartDataPoint(**x)
            for x in group_valor_recuperado_por_funcionario_NG(
                ag_filtrados, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_resolvidos_por_dia_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_NG(ag_filtrados)
        ]
        charts["execucao_resolvidos_por_dia_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_por_prazo_NG(ag_filtrados)
        ]
        charts["execucao_media_resolvidos_por_funcionario_NG"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_media_resolvidos_por_funcionario_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_por_prazo_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_nao_cumprido_por_motivo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_nao_cumprido_por_motivo_NG(ag_filtrados)
        ]
        charts["execucao_atividades_lista_NG"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_periodo_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_abertas_NG"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_abertas_NG(ag_filtrados)
        ]
        charts["execucao_atividades_lista_por_prazo_NG"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_por_prazo_periodo_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_lista_filtros_opcoes_NG"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_NG(agendamentos, from_date=from_date, to_date=to_date)
        )
        charts["execucao_atividades_lista_filtros_opcoes_por_prazo_NG"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_por_prazo_NG(agendamentos, from_date=from_date, to_date=to_date)
        )
        atrasos_raw = get_atrasos_detalhamento_execucao_NG(ag_filtrados)
        charts["execucao_atrasos_detalhamento_NG"] = ExecucaoAtrasosDetalhamento(
            total=atrasos_raw["total"],
            buckets=[ExecucaoAtrasoBucket(**b) for b in atrasos_raw["buckets"]],
        )

        # Diligências: subconjunto de `agendamentos` (não `ag_filtrados` — independente
        # dos filtros de funcionário/atividade/status/situação da seção Atividades).
        diligencias_ag = filtrar_agendamentos_diligencia_NG(agendamentos)
        stats["total_diligencias_execucao_NG"] = get_total_diligencias_execucao_NG(
            diligencias_ag, from_date=from_date, to_date=to_date
        )

        diligencias_ag_tipo_filtradas = filtrar_agendamentos_diligencia_por_tipo_NG(
            diligencias_ag, diligencia_tipo_filtro
        )
        diligencias_ag_processo = filtrar_agendamentos_diligencia_por_colaborador_NG(
            diligencias_ag_tipo_filtradas, diligencia_colaborador_filtro
        )
        charts["execucao_diligencias_por_processo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_diligencias_por_processo_NG(
                diligencias_ag_processo, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_diligencias_por_funcionario_NG"] = (
            group_execucao_demandas_por_funcionario_NG(
                diligencias_ag_tipo_filtradas, from_date=from_date, to_date=to_date
            )
        )

        expedicao_alvara_ag = filtrar_agendamentos_diligencia_expedicao_alvara_NG(
            diligencias_ag
        )
        kpis_expedicao_alvara = get_kpis_diligencias_expedicao_alvara_execucao_NG(
            expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
            colaborador=diligencia_colaborador_filtro,
        )
        stats["total_diligencias_expedicao_alvara_execucao_NG"] = kpis_expedicao_alvara["total"]
        stats["cumpridas_diligencias_expedicao_alvara_execucao_NG"] = kpis_expedicao_alvara["cumpridas"]
        stats["valor_diligencias_expedicao_alvara_execucao_NG"] = kpis_expedicao_alvara["valor"]
        charts["execucao_diligencias_expedicao_alvara_processos_NG"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_processos_diligencia_expedicao_alvara_cumprida_execucao_NG(
                expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
                colaborador=diligencia_colaborador_filtro,
            )
        ]

    return stats, charts


# v1: dashboard_routes.py:7833
def _build_execucao_RJ_stats(
    execucao: List[Dict],
    all_execucao: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    execucao_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    diligencia_tipo_filtro: Optional[str] = None,
    diligencia_colaborador_filtro: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder para o domínio Execução RJ (mirror de :func:`_build_execucao_stats`).
    """
    # Antes do recorte por filtro de atividade abaixo (mesmo motivo do NG).
    entrada_fluxo_cs_por_mes = (
        group_entrada_execucao_por_fluxo_cs_por_mes_RJ(all_execucao, agendamentos)
        if agendamentos is not None
        else None
    )
    # Antes do recorte por filtro de atividade (mesmo motivo do gráfico de fluxo).
    taxa_atualizacao = (
        get_taxa_atualizacao_execucao_RJ(all_execucao, agendamentos, from_date, to_date)
        if agendamentos is not None
        else None
    )
    alvara_expedido_lista = list_processos_alvara_expedido_RJ(all_execucao)
    ag_filtrados: Optional[List[Dict]] = None
    if agendamentos is not None:
        ag_filtrados = filtrar_agendamentos_execucao_RJ(
            agendamentos,
            execucao_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        if execucao_atividades_filtros is not None and execucao_atividades_filtros.ativo():
            processo_ids = frozenset(
                pid
                for row in ag_filtrados
                if (pid := _get_ag_processo_id_rj(row)) is not None
            )
            if processo_ids:
                execucao = [r for r in execucao if (r.get("id") or r.get("ID")) in processo_ids]
                all_execucao = [r for r in all_execucao if (r.get("id") or r.get("ID")) in processo_ids]
            else:
                execucao = []
                all_execucao = []

    _sem_periodo = from_date is None or to_date is None
    stats = {
        "total_em_execucao_RJ": (
            get_total_execucao_RJ(execucao)
            if _sem_periodo
            else len(_filtrar_entrada_execucao_no_periodo_rj(execucao))
        ),
        "valor_total_em_execucao_RJ": get_valor_causa_total_execucao_RJ(execucao),
        "total_valor_execucao_vazio_RJ": get_total_valor_execucao_vazio_RJ(execucao),
        "total_valor_execucao_vazio_RJ_detalhe": get_detalhe_valor_execucao_vazio_RJ(execucao),
        "valor_honorarios_total_execucao_RJ": get_valor_honorarios_total_execucao_RJ(
            execucao
        ),
        "valor_em_execucao_RJ": get_valor_em_execucao_RJ(execucao),
        "valor_remanescente_em_execucao_RJ": get_valor_remanescente_em_execucao_RJ(execucao),
        "estoque_inicial_RJ": get_estoque_final_RJ(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "tre_RJ": get_tre_execucao_RJ_dax(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "total_saida_execucao_periodo_RJ": get_total_saida_execucao_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "total_incontroverso_saida_execucao_periodo_RJ": get_total_incontroverso_saida_periodo_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_execucao_saida_periodo_RJ": get_valor_execucao_saida_periodo_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_incontroverso_saida_execucao_periodo_RJ": get_valor_incontroverso_saida_periodo_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_ted_saida_execucao_periodo_RJ": get_valor_ted_saida_execucao_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "taxa_recuperacao_execucao_RJ": get_taxa_recuperacao_execucao_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "taxa_atualizacao_execucao_RJ": taxa_atualizacao,
        "media_tempo_execucao_RJ": get_media_tempo_execucao_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        # Durações (dias) das saídas do período — o Estratégico Geral junta Condenação + Acordos
        # para calcular média/mediana do conjunto (somar as duas médias/medianas não vale).
        "duracoes_tempo_execucao_RJ": _duracoes_execucao_rj(all_execucao, from_date, to_date),
        "mediana_tempo_execucao_RJ": get_mediana_tempo_execucao_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
    }
    charts = {
        "execucao_entrada_fluxo_cs_por_mes_RJ": entrada_fluxo_cs_por_mes,
        "execucao_alvara_expedido_lista_RJ": alvara_expedido_lista,
        "execucao_alvaras_expedidos_por_dia_RJ": group_alvaras_expedidos_por_dia_RJ(all_execucao),
        "execucao_por_subfase_RJ": [
            ChartDataPoint(**x) for x in group_execucao_RJ_por_subfase(execucao)
        ],
        "valor_execucao_por_subfase_RJ": [
            ChartDataPoint(**x) for x in group_valor_execucao_RJ_por_subfase(execucao)
        ],
        "execucao_por_comarca_total_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_RJ_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_por_comarca_entrada_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_RJ_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_por_comarca_saida_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_RJ_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_valor_por_comarca_total_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_RJ_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_valor_por_comarca_entrada_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_RJ_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_valor_por_comarca_saida_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_RJ_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_por_materia_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_RJ_por_materia(execucao, restringir_fase_atual=_sem_periodo)
        ],
        "valor_execucao_por_materia_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_RJ_por_materia(execucao, restringir_fase_atual=_sem_periodo)
        ],
        "execucao_por_ano_ajuizamento_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_RJ_por_ano_ajuizamento(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        **_estoque_mensal_charts(group_estoque_execucao_RJ_por_mes(all_execucao), "execucao_estoque_quantidade_por_mes_RJ", "execucao_estoque_valor_por_mes_RJ"),
        "execucao_media_tempo_por_mes_RJ": [
            ChartDataPoint(**x) for x in get_media_tempo_execucao_RJ_por_mes(all_execucao)
        ],
        "valor_saida_execucao_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_saida_execucao_RJ_por_mes(all_execucao)
        ],
        "valor_execucao_saida_periodo_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_saida_periodo_RJ_por_mes(all_execucao)
        ],
        "valor_remanescente_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_remanescente_por_mes_RJ(all_execucao)
        ],
        "quantidade_saida_execucao_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_quantidade_saida_execucao_RJ_por_mes(all_execucao)
        ],
        "quantidade_entrada_execucao_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_quantidade_entrada_execucao_RJ_por_mes(all_execucao)
        ],
        "valor_entrada_execucao_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_entrada_execucao_RJ_por_mes(all_execucao)
        ],
    }

    if ag_filtrados is not None:
        stats.update(get_kpis_atividades_execucao_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats.update(get_kpis_execucao_por_prazo_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["media_mensal_atividades_execucao_RJ"] = get_media_mensal_atividades_execucao_RJ(
            ag_filtrados
        )
        charts["execucao_processos_por_atividade_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_ativas_por_atividade_RJ"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_criadas_por_atividade_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_criadas_por_atividade_RJ"] = [
            ChartDataPoint(**x)
            for x in group_atividades_criadas_por_atividade_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_processos_por_atividade_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_por_prazo_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_ativas_por_atividade_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_por_prazo_por_atividade_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_demandas_por_funcionario_RJ"] = group_execucao_demandas_por_funcionario_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_completo_RJ"] = group_execucao_demandas_por_funcionario_completo_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_taxa_conclusao_por_funcionario_RJ"] = group_taxa_conclusao_por_funcionario_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_por_prazo_RJ"] = group_execucao_demandas_por_funcionario_por_prazo_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_por_prazo_completo_RJ"] = group_execucao_demandas_por_funcionario_por_prazo_completo_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_valor_recuperado_por_funcionario_RJ"] = [
            ChartDataPoint(**x)
            for x in group_valor_recuperado_por_funcionario_RJ(
                ag_filtrados, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_resolvidos_por_dia_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_RJ(ag_filtrados)
        ]
        charts["execucao_resolvidos_por_dia_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_por_prazo_RJ(ag_filtrados)
        ]
        charts["execucao_media_resolvidos_por_funcionario_RJ"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_media_resolvidos_por_funcionario_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_por_prazo_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_nao_cumprido_por_motivo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_nao_cumprido_por_motivo_RJ(ag_filtrados)
        ]
        charts["execucao_atividades_lista_RJ"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_periodo_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_abertas_RJ"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_abertas_RJ(ag_filtrados)
        ]
        charts["execucao_atividades_lista_por_prazo_RJ"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_por_prazo_periodo_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_lista_filtros_opcoes_RJ"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_RJ(agendamentos, from_date=from_date, to_date=to_date)
        )
        charts["execucao_atividades_lista_filtros_opcoes_por_prazo_RJ"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_por_prazo_RJ(agendamentos, from_date=from_date, to_date=to_date)
        )
        atrasos_raw = get_atrasos_detalhamento_execucao_RJ(ag_filtrados)
        charts["execucao_atrasos_detalhamento_RJ"] = ExecucaoAtrasosDetalhamento(
            total=atrasos_raw["total"],
            buckets=[ExecucaoAtrasoBucket(**b) for b in atrasos_raw["buckets"]],
        )

        diligencias_ag = filtrar_agendamentos_diligencia_RJ(agendamentos)
        stats["total_diligencias_execucao_RJ"] = get_total_diligencias_execucao_RJ(
            diligencias_ag, from_date=from_date, to_date=to_date
        )

        diligencias_ag_tipo_filtradas = filtrar_agendamentos_diligencia_por_tipo_RJ(
            diligencias_ag, diligencia_tipo_filtro
        )
        diligencias_ag_processo = filtrar_agendamentos_diligencia_por_colaborador_RJ(
            diligencias_ag_tipo_filtradas, diligencia_colaborador_filtro
        )
        charts["execucao_diligencias_por_processo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_diligencias_por_processo_RJ(
                diligencias_ag_processo, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_diligencias_por_funcionario_RJ"] = (
            group_execucao_demandas_por_funcionario_RJ(
                diligencias_ag_tipo_filtradas, from_date=from_date, to_date=to_date
            )
        )

        expedicao_alvara_ag = filtrar_agendamentos_diligencia_expedicao_alvara_RJ(
            diligencias_ag
        )
        kpis_expedicao_alvara = get_kpis_diligencias_expedicao_alvara_execucao_RJ(
            expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
            colaborador=diligencia_colaborador_filtro,
        )
        stats["total_diligencias_expedicao_alvara_execucao_RJ"] = kpis_expedicao_alvara["total"]
        stats["cumpridas_diligencias_expedicao_alvara_execucao_RJ"] = kpis_expedicao_alvara["cumpridas"]
        stats["valor_diligencias_expedicao_alvara_execucao_RJ"] = kpis_expedicao_alvara["valor"]
        charts["execucao_diligencias_expedicao_alvara_processos_RJ"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_processos_diligencia_expedicao_alvara_cumprida_execucao_RJ(
                expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
                colaborador=diligencia_colaborador_filtro,
            )
        ]

    return stats, charts


# v1: dashboard_routes.py:8179
def _build_execucao_acordos_stats(
    execucao: List[Dict],
    all_execucao: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    execucao_acordos_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    processo_ids_ativos: Optional[frozenset] = None,
    diligencia_tipo_filtro: Optional[str] = None,
    diligencia_colaborador_filtro: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder para o domínio Execução Acordos NG (mirror de :func:`_build_execucao_stats`).

    execucao      → dados filtrados por DATA_ACORDO_FECHADO (via filter_data)
    all_execucao  → dados sem filtro de data (necessário para calcular saídas no
                    período, pois DATA_PAGAMENTO_ACORDO não é a coluna usada pelo
                    filter_data deste domínio)
    agendamentos  → agendamentos do setor ACORDOS NG para a seção Atividades
    processo_ids_ativos → quando informado (materia/subfase/tipo_acao/uf/processo
                    ativos no restante da página), restringe as seções Atividades
                    e Diligências aos agendamentos dos processos que sobreviveram
                    a esses filtros — sem isso, essas duas seções ignoravam
                    completamente os filtros de matéria/subfase/tipo/processo.

    Quando filtros de agendamento estão ativos, os dados de processo são restritos
    aos processos que possuem agendamentos correspondentes — todas as seções refletem
    o mesmo recorte.
    """
    if processo_ids_ativos is not None and agendamentos is not None:
        agendamentos = [
            row for row in agendamentos
            if _get_ag_processo_id_ng(row) in processo_ids_ativos
        ]

    ag_filtrados: Optional[List[Dict]] = None
    if agendamentos is not None:
        ag_filtrados = filtrar_agendamentos_execucao_acordos_NG(
            agendamentos,
            execucao_acordos_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        if execucao_acordos_atividades_filtros is not None and execucao_acordos_atividades_filtros.ativo():
            processo_ids = frozenset(
                pid
                for row in ag_filtrados
                if (pid := _get_ag_processo_id_ng(row)) is not None
            )
            if processo_ids:
                execucao = [r for r in execucao if (r.get("id") or r.get("ID")) in processo_ids]
                all_execucao = [r for r in all_execucao if (r.get("id") or r.get("ID")) in processo_ids]
            else:
                execucao = []
                all_execucao = []

    # Sem período (statsSemFiltro) = modo "Total" do gráfico por matéria (estoque
    # atual, restrito a ID_FASE == 30, como total_em_execucao_acordos_NG); com
    # período (stats) = modo "Qtd Entrada"/"Valor Entrada" (sem restrição de fase
    # atual, para bater com total_entrada_execucao_acordos_periodo_NG).
    _sem_periodo = from_date is None or to_date is None
    stats = {
        "total_em_execucao_acordos_NG": get_total_execucao_acordos(execucao),
        "valor_total_em_execucao_acordos_NG": get_valor_alcada_final_total_execucao_acordos(execucao),
        "total_valor_alcada_final_vazio_acordos_NG": get_total_valor_alcada_final_vazio(execucao),
        "total_valor_alcada_final_vazio_acordos_NG_detalhe": get_detalhe_valor_alcada_final_vazio(execucao),
        "estoque_inicial_execucao_acordos_NG": get_estoque_final_execucao_acordos(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "tre_execucao_acordos_NG": get_tre_execucao_acordos_dax(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "total_entrada_execucao_acordos_periodo_NG": get_total_entrada_execucao_acordos_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_entrada_execucao_acordos_periodo_NG": get_valor_entrada_execucao_acordos_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "total_saida_execucao_acordos_periodo_NG": get_total_saida_execucao_acordos_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_saida_execucao_acordos_periodo_NG": get_valor_saida_execucao_acordos_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_ted_saida_execucao_acordos_periodo_NG": get_valor_ted_saida_execucao_acordos_NG_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "media_tempo_execucao_acordos_NG": get_media_tempo_execucao_acordos(
            all_execucao, from_date, to_date
        ),
        # Durações (dias) das saídas do período — o Estratégico Geral junta Condenação + Acordos
        # para calcular média/mediana do conjunto (somar as duas médias/medianas não vale).
        "duracoes_tempo_execucao_acordos_NG": _duracoes_execucao_acordos_ng(all_execucao, from_date, to_date),
        "mediana_tempo_execucao_acordos_NG": get_mediana_tempo_execucao_acordos(
            all_execucao, from_date, to_date
        ),
    }
    charts = {
        "execucao_acordos_alvara_expedido_lista_NG": list_processos_alvara_expedido_acordos_NG(all_execucao),
        "execucao_acordos_alvaras_expedidos_por_dia_NG": group_alvaras_expedidos_acordos_por_dia_NG(all_execucao),
        "execucao_acordos_por_subfase_NG": [
            ChartDataPoint(**x) for x in group_execucao_acordos_por_subfase(execucao)
        ],
        "valor_execucao_acordos_por_subfase_NG": [
            ChartDataPoint(**x) for x in group_valor_execucao_acordos_por_subfase(execucao)
        ],
        "execucao_acordos_por_comarca_total_NG": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_acordos_por_comarca_entrada_NG": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_por_comarca_saida_NG": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_valor_por_comarca_total_NG": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_acordos_valor_por_comarca_entrada_NG": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_valor_por_comarca_saida_NG": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_por_materia_NG": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_por_materia(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "execucao_acordos_por_ano_ajuizamento_NG": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_por_ano_ajuizamento(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "valor_execucao_acordos_por_materia_NG": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_por_materia(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "execucao_acordos_por_tipo_acao_NG": [
            ChartDataPoint(**x) for x in group_execucao_acordos_por_tipo_acao(execucao)
        ],
        "execucao_acordos_por_sentenca_NG": [
            ChartDataPoint(**x) for x in group_execucao_acordos_por_sentenca(all_execucao)
        ],
        "valor_saida_execucao_acordos_por_mes_NG": [
            ChartDataPoint(**x)
            for x in group_valor_saida_execucao_acordos_por_mes(all_execucao)
        ],
        "quantidade_saida_execucao_acordos_por_mes_NG": [
            ChartDataPoint(**x)
            for x in group_quantidade_saida_execucao_acordos_por_mes(all_execucao)
        ],
        "quantidade_entrada_execucao_acordos_por_mes_NG": [
            ChartDataPoint(**x)
            for x in group_quantidade_entrada_execucao_acordos_por_mes(all_execucao)
        ],
        "valor_entrada_execucao_acordos_por_mes_NG": [
            ChartDataPoint(**x)
            for x in group_valor_entrada_execucao_acordos_por_mes(all_execucao)
        ],
        **_estoque_mensal_charts(group_estoque_execucao_acordos_por_mes(all_execucao), "execucao_acordos_estoque_quantidade_por_mes_NG", "execucao_acordos_estoque_valor_por_mes_NG"),
        "execucao_acordos_media_tempo_por_mes_NG": [
            ChartDataPoint(**x)
            for x in get_media_tempo_execucao_acordos_por_mes(all_execucao)
        ],
    }

    if ag_filtrados is not None:
        stats.update(get_kpis_atividades_execucao_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats.update(get_kpis_execucao_por_prazo_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["media_mensal_atividades_execucao_acordos_NG"] = get_media_mensal_atividades_execucao_acordos_NG(
            ag_filtrados
        )
        charts["execucao_acordos_processos_por_atividade_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_acordos_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_atividades_ativas_por_atividade_NG"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_criadas_por_atividade_acordos_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_processos_por_atividade_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_por_prazo_acordos_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_atividades_ativas_por_atividade_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_por_prazo_por_atividade_acordos_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_demandas_por_funcionario_NG"] = group_execucao_demandas_por_funcionario_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_completo_NG"] = group_execucao_demandas_por_funcionario_completo_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_por_prazo_NG"] = group_execucao_demandas_por_funcionario_por_prazo_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_por_prazo_completo_NG"] = group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_resolvidos_por_dia_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_acordos_NG(ag_filtrados)
        ]
        charts["execucao_acordos_resolvidos_por_dia_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_por_prazo_acordos_NG(ag_filtrados)
        ]
        charts["execucao_acordos_media_resolvidos_por_funcionario_NG"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_acordos_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_media_resolvidos_por_funcionario_por_prazo_NG"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_nao_cumprido_por_motivo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_nao_cumprido_por_motivo_acordos_NG(ag_filtrados)
        ]
        charts["execucao_acordos_atividades_lista_NG"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in _enriquecer_atividades_acordos_ng_com_dados_processo(
                list_execucao_atividades_periodo_acordos_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                ),
                ag_filtrados,
                all_execucao,
            )
        ]
        charts["execucao_acordos_atividades_lista_por_prazo_NG"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in _enriquecer_atividades_acordos_ng_com_dados_processo(
                list_execucao_atividades_por_prazo_periodo_acordos_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                ),
                ag_filtrados,
                all_execucao,
            )
        ]
        charts["execucao_acordos_atividades_lista_filtros_opcoes_NG"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_acordos_NG(agendamentos, from_date=from_date, to_date=to_date)
        )
        charts["execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_NG"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_por_prazo_acordos_NG(agendamentos, from_date=from_date, to_date=to_date)
        )
        atrasos_raw_acordos = get_atrasos_detalhamento_execucao_acordos_NG(ag_filtrados)
        charts["execucao_acordos_atrasos_detalhamento_NG"] = ExecucaoAtrasosDetalhamento(
            total=atrasos_raw_acordos["total"],
            buckets=[ExecucaoAtrasoBucket(**b) for b in atrasos_raw_acordos["buckets"]],
        )

        # Diligências: subconjunto de `agendamentos` (não `ag_filtrados` — independente
        # dos filtros de funcionário/atividade/status/situação da seção Atividades).
        diligencias_ag = filtrar_agendamentos_diligencia_acordos_NG(agendamentos)
        stats["total_diligencias_execucao_acordos_NG"] = get_total_diligencias_execucao_acordos_NG(
            diligencias_ag, from_date=from_date, to_date=to_date
        )

        # Os dois gráficos (processo e ranking por colaborador) respeitam o clique
        # nos cards de tipo ("Diligências de Expedição de Alvará"/"Cumpridas") — os
        # KPIs abaixo continuam usando `diligencias_ag` (não filtrado), como
        # referência fixa, igual aos cards de situação da seção Atividades.
        diligencias_ag_tipo_filtradas = filtrar_agendamentos_diligencia_por_tipo_acordos_NG(
            diligencias_ag, diligencia_tipo_filtro
        )
        # Só o gráfico "Processos com mais Diligências" também respeita o clique no
        # colaborador do ranking — o próprio ranking mantém todos os colaboradores
        # visíveis para comparação (mesmo padrão da seção Atividades).
        diligencias_ag_processo = filtrar_agendamentos_diligencia_por_colaborador_acordos_NG(
            diligencias_ag_tipo_filtradas, diligencia_colaborador_filtro
        )
        charts["execucao_acordos_diligencias_por_processo_NG"] = [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_diligencias_por_processo_NG(
                diligencias_ag_processo, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_diligencias_por_funcionario_NG"] = (
            group_execucao_demandas_por_funcionario_acordos_NG(
                diligencias_ag_tipo_filtradas, from_date=from_date, to_date=to_date
            )
        )

        expedicao_alvara_ag = filtrar_agendamentos_diligencia_expedicao_alvara_acordos_NG(
            diligencias_ag
        )
        kpis_expedicao_alvara = get_kpis_diligencias_expedicao_alvara_acordos_NG(
            expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
            colaborador=diligencia_colaborador_filtro,
        )
        stats["total_diligencias_expedicao_alvara_execucao_acordos_NG"] = kpis_expedicao_alvara["total"]
        stats["cumpridas_diligencias_expedicao_alvara_execucao_acordos_NG"] = kpis_expedicao_alvara["cumpridas"]
        stats["valor_diligencias_expedicao_alvara_execucao_acordos_NG"] = kpis_expedicao_alvara["valor"]
        charts["execucao_acordos_diligencias_expedicao_alvara_processos_NG"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_processos_diligencia_expedicao_alvara_cumprida_acordos_NG(
                expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
                colaborador=diligencia_colaborador_filtro,
            )
        ]

    return stats, charts


# v1: dashboard_routes.py:8525
def _build_execucao_acordos_LA_stats(
    execucao: List[Dict],
    all_execucao: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    execucao_acordos_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    processo_ids_ativos: Optional[frozenset] = None,
    diligencia_tipo_filtro: Optional[str] = None,
    diligencia_colaborador_filtro: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder para o domínio Execução Acordos LA (mirror de :func:`_build_execucao_stats`).

    execucao      → dados filtrados por DATA_ACORDO_FECHADO (via filter_data)
    all_execucao  → dados sem filtro de data (necessário para calcular saídas no
                    período, pois DATA_PAGAMENTO_ACORDO não é a coluna usada pelo
                    filter_data deste domínio)
    agendamentos  → agendamentos do setor ACORDOS LA para a seção Atividades
    processo_ids_ativos → quando informado (materia/subfase/tipo_acao/uf/processo
                    ativos no restante da página), restringe as seções Atividades
                    e Diligências aos agendamentos dos processos que sobreviveram
                    a esses filtros — sem isso, essas duas seções ignoravam
                    completamente os filtros de matéria/subfase/tipo/processo.

    Quando filtros de agendamento estão ativos, os dados de processo são restritos
    aos processos que possuem agendamentos correspondentes — todas as seções refletem
    o mesmo recorte.
    """
    if processo_ids_ativos is not None and agendamentos is not None:
        agendamentos = [
            row for row in agendamentos
            if _get_ag_processo_id_ng(row) in processo_ids_ativos
        ]

    ag_filtrados: Optional[List[Dict]] = None
    if agendamentos is not None:
        ag_filtrados = filtrar_agendamentos_execucao_acordos_LA(
            agendamentos,
            execucao_acordos_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        if execucao_acordos_atividades_filtros is not None and execucao_acordos_atividades_filtros.ativo():
            processo_ids = frozenset(
                pid
                for row in ag_filtrados
                if (pid := _get_ag_processo_id_ng(row)) is not None
            )
            if processo_ids:
                execucao = [r for r in execucao if (r.get("id") or r.get("ID")) in processo_ids]
                all_execucao = [r for r in all_execucao if (r.get("id") or r.get("ID")) in processo_ids]
            else:
                execucao = []
                all_execucao = []

    # Sem período (statsSemFiltro) = modo "Total" do gráfico por matéria (estoque
    # atual, restrito a ID_FASE == 30, como total_em_execucao_acordos_NG); com
    # período (stats) = modo "Qtd Entrada"/"Valor Entrada" (sem restrição de fase
    # atual, para bater com total_entrada_execucao_acordos_periodo_NG).
    _sem_periodo = from_date is None or to_date is None
    stats = {
        "total_em_execucao_acordos_LA": get_total_execucao_acordos_LA(execucao),
        "valor_total_em_execucao_acordos_LA": get_valor_alcada_final_total_execucao_acordos_LA(execucao),
        "total_valor_alcada_final_vazio_acordos_LA": get_total_valor_alcada_final_vazio_LA(execucao),
        "total_valor_alcada_final_vazio_acordos_LA_detalhe": get_detalhe_valor_alcada_final_vazio_LA(execucao),
        "estoque_inicial_execucao_acordos_LA": get_estoque_final_execucao_acordos_LA(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "tre_execucao_acordos_LA": get_tre_execucao_acordos_LA_dax(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "total_entrada_execucao_acordos_periodo_LA": get_total_entrada_execucao_acordos_LA_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_entrada_execucao_acordos_periodo_LA": get_valor_entrada_execucao_acordos_LA_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "total_saida_execucao_acordos_periodo_LA": get_total_saida_execucao_acordos_LA_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_saida_execucao_acordos_periodo_LA": get_valor_saida_execucao_acordos_LA_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_ted_saida_execucao_acordos_periodo_LA": get_valor_ted_saida_execucao_acordos_LA_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "media_tempo_execucao_acordos_LA": get_media_tempo_execucao_acordos_LA(
            all_execucao, from_date, to_date
        ),
        # Durações (dias) das saídas do período — o Estratégico Geral junta Condenação + Acordos
        # para calcular média/mediana do conjunto (somar as duas médias/medianas não vale).
        "duracoes_tempo_execucao_acordos_LA": _duracoes_execucao_acordos_la(all_execucao, from_date, to_date),
        "mediana_tempo_execucao_acordos_LA": get_mediana_tempo_execucao_acordos_LA(
            all_execucao, from_date, to_date
        ),
    }
    charts = {
        "execucao_acordos_alvara_expedido_lista_LA": list_processos_alvara_expedido_acordos_LA(all_execucao),
        "execucao_acordos_alvaras_expedidos_por_dia_LA": group_alvaras_expedidos_acordos_por_dia_LA(all_execucao),
        "execucao_acordos_por_subfase_LA": [
            ChartDataPoint(**x) for x in group_execucao_acordos_LA_por_subfase(execucao)
        ],
        "valor_execucao_acordos_por_subfase_LA": [
            ChartDataPoint(**x) for x in group_valor_execucao_acordos_LA_por_subfase(execucao)
        ],
        "execucao_acordos_por_comarca_total_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_LA_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_acordos_por_comarca_entrada_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_LA_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_por_comarca_saida_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_LA_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_valor_por_comarca_total_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_LA_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_acordos_valor_por_comarca_entrada_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_LA_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_valor_por_comarca_saida_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_LA_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_por_materia_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_LA_por_materia(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "execucao_acordos_por_ano_ajuizamento_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_LA_por_ano_ajuizamento(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "valor_execucao_acordos_por_materia_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_LA_por_materia(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "execucao_acordos_por_tipo_acao_LA": [
            ChartDataPoint(**x) for x in group_execucao_acordos_LA_por_tipo_acao(execucao)
        ],
        "execucao_acordos_por_sentenca_LA": [
            ChartDataPoint(**x) for x in group_execucao_acordos_LA_por_sentenca(all_execucao)
        ],
        "valor_saida_execucao_acordos_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_valor_saida_execucao_acordos_LA_por_mes(all_execucao)
        ],
        "quantidade_saida_execucao_acordos_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_quantidade_saida_execucao_acordos_LA_por_mes(all_execucao)
        ],
        "quantidade_entrada_execucao_acordos_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_quantidade_entrada_execucao_acordos_LA_por_mes(all_execucao)
        ],
        "valor_entrada_execucao_acordos_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_valor_entrada_execucao_acordos_LA_por_mes(all_execucao)
        ],
        **_estoque_mensal_charts(group_estoque_execucao_acordos_por_mes_LA(all_execucao), "execucao_acordos_estoque_quantidade_por_mes_LA", "execucao_acordos_estoque_valor_por_mes_LA"),
        "execucao_acordos_media_tempo_por_mes_LA": [
            ChartDataPoint(**x)
            for x in get_media_tempo_execucao_acordos_LA_por_mes(all_execucao)
        ],
    }

    if ag_filtrados is not None:
        stats.update(get_kpis_atividades_execucao_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats.update(get_kpis_execucao_por_prazo_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["media_mensal_atividades_execucao_acordos_LA"] = get_media_mensal_atividades_execucao_acordos_LA(
            ag_filtrados
        )
        charts["execucao_acordos_processos_por_atividade_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_acordos_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_atividades_ativas_por_atividade_LA"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_criadas_por_atividade_acordos_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_processos_por_atividade_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_por_prazo_acordos_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_atividades_ativas_por_atividade_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_por_prazo_por_atividade_acordos_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_demandas_por_funcionario_LA"] = group_execucao_demandas_por_funcionario_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_completo_LA"] = group_execucao_demandas_por_funcionario_completo_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_por_prazo_LA"] = group_execucao_demandas_por_funcionario_por_prazo_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_por_prazo_completo_LA"] = group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_resolvidos_por_dia_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_acordos_LA(ag_filtrados)
        ]
        charts["execucao_acordos_resolvidos_por_dia_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_por_prazo_acordos_LA(ag_filtrados)
        ]
        charts["execucao_acordos_media_resolvidos_por_funcionario_LA"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_acordos_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_media_resolvidos_por_funcionario_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_nao_cumprido_por_motivo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_nao_cumprido_por_motivo_acordos_LA(ag_filtrados)
        ]
        charts["execucao_acordos_atividades_lista_LA"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in _enriquecer_atividades_acordos_la_com_dados_processo(
                list_execucao_atividades_periodo_acordos_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                ),
                ag_filtrados,
                all_execucao,
            )
        ]
        charts["execucao_acordos_atividades_lista_por_prazo_LA"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in _enriquecer_atividades_acordos_la_com_dados_processo(
                list_execucao_atividades_por_prazo_periodo_acordos_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                ),
                ag_filtrados,
                all_execucao,
            )
        ]
        charts["execucao_acordos_atividades_lista_filtros_opcoes_LA"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_acordos_LA(agendamentos, from_date=from_date, to_date=to_date)
        )
        charts["execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_LA"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_por_prazo_acordos_LA(agendamentos, from_date=from_date, to_date=to_date)
        )
        atrasos_raw_acordos = get_atrasos_detalhamento_execucao_acordos_LA(ag_filtrados)
        charts["execucao_acordos_atrasos_detalhamento_LA"] = ExecucaoAtrasosDetalhamento(
            total=atrasos_raw_acordos["total"],
            buckets=[ExecucaoAtrasoBucket(**b) for b in atrasos_raw_acordos["buckets"]],
        )

        # Diligências: subconjunto de `agendamentos` (não `ag_filtrados` — independente
        # dos filtros de funcionário/atividade/status/situação da seção Atividades).
        diligencias_ag = filtrar_agendamentos_diligencia_acordos_LA(agendamentos)
        stats["total_diligencias_execucao_acordos_LA"] = get_total_diligencias_execucao_acordos_LA(
            diligencias_ag, from_date=from_date, to_date=to_date
        )

        # Os dois gráficos (processo e ranking por colaborador) respeitam o clique
        # nos cards de tipo ("Diligências de Expedição de Alvará"/"Cumpridas") — os
        # KPIs abaixo continuam usando `diligencias_ag` (não filtrado), como
        # referência fixa, igual aos cards de situação da seção Atividades.
        diligencias_ag_tipo_filtradas = filtrar_agendamentos_diligencia_por_tipo_acordos_LA(
            diligencias_ag, diligencia_tipo_filtro
        )
        # Só o gráfico "Processos com mais Diligências" também respeita o clique no
        # colaborador do ranking — o próprio ranking mantém todos os colaboradores
        # visíveis para comparação (mesmo padrão da seção Atividades).
        diligencias_ag_processo = filtrar_agendamentos_diligencia_por_colaborador_acordos_LA(
            diligencias_ag_tipo_filtradas, diligencia_colaborador_filtro
        )
        charts["execucao_acordos_diligencias_por_processo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_diligencias_por_processo_LA(
                diligencias_ag_processo, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_diligencias_por_funcionario_LA"] = (
            group_execucao_demandas_por_funcionario_acordos_LA(
                diligencias_ag_tipo_filtradas, from_date=from_date, to_date=to_date
            )
        )

        expedicao_alvara_ag = filtrar_agendamentos_diligencia_expedicao_alvara_acordos_LA(
            diligencias_ag
        )
        kpis_expedicao_alvara = get_kpis_diligencias_expedicao_alvara_acordos_LA(
            expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
            colaborador=diligencia_colaborador_filtro,
        )
        stats["total_diligencias_expedicao_alvara_execucao_acordos_LA"] = kpis_expedicao_alvara["total"]
        stats["cumpridas_diligencias_expedicao_alvara_execucao_acordos_LA"] = kpis_expedicao_alvara["cumpridas"]
        stats["valor_diligencias_expedicao_alvara_execucao_acordos_LA"] = kpis_expedicao_alvara["valor"]
        charts["execucao_acordos_diligencias_expedicao_alvara_processos_LA"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_processos_diligencia_expedicao_alvara_cumprida_acordos_LA(
                expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
                colaborador=diligencia_colaborador_filtro,
            )
        ]

    return stats, charts


# v1: dashboard_routes.py:8872
def _build_execucao_acordos_RJ_stats(
    execucao: List[Dict],
    all_execucao: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    execucao_acordos_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    processo_ids_ativos: Optional[frozenset] = None,
    diligencia_tipo_filtro: Optional[str] = None,
    diligencia_colaborador_filtro: Optional[str] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder para o domínio Execução Acordos LA (mirror de :func:`_build_execucao_stats`).

    execucao      → dados filtrados por DATA_ACORDO_FECHADO (via filter_data)
    all_execucao  → dados sem filtro de data (necessário para calcular saídas no
                    período, pois DATA_PAGAMENTO_ACORDO não é a coluna usada pelo
                    filter_data deste domínio)
    agendamentos  → agendamentos do setor ACORDOS LA para a seção Atividades
    processo_ids_ativos → quando informado (materia/subfase/tipo_acao/uf/processo
                    ativos no restante da página), restringe as seções Atividades
                    e Diligências aos agendamentos dos processos que sobreviveram
                    a esses filtros — sem isso, essas duas seções ignoravam
                    completamente os filtros de matéria/subfase/tipo/processo.

    Quando filtros de agendamento estão ativos, os dados de processo são restritos
    aos processos que possuem agendamentos correspondentes — todas as seções refletem
    o mesmo recorte.
    """
    if processo_ids_ativos is not None and agendamentos is not None:
        agendamentos = [
            row for row in agendamentos
            if _get_ag_processo_id_ng(row) in processo_ids_ativos
        ]

    ag_filtrados: Optional[List[Dict]] = None
    if agendamentos is not None:
        ag_filtrados = filtrar_agendamentos_execucao_acordos_RJ(
            agendamentos,
            execucao_acordos_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        if execucao_acordos_atividades_filtros is not None and execucao_acordos_atividades_filtros.ativo():
            processo_ids = frozenset(
                pid
                for row in ag_filtrados
                if (pid := _get_ag_processo_id_ng(row)) is not None
            )
            if processo_ids:
                execucao = [r for r in execucao if (r.get("id") or r.get("ID")) in processo_ids]
                all_execucao = [r for r in all_execucao if (r.get("id") or r.get("ID")) in processo_ids]
            else:
                execucao = []
                all_execucao = []

    # Sem período (statsSemFiltro) = modo "Total" do gráfico por matéria (estoque
    # atual, restrito a ID_FASE == 30, como total_em_execucao_acordos_NG); com
    # período (stats) = modo "Qtd Entrada"/"Valor Entrada" (sem restrição de fase
    # atual, para bater com total_entrada_execucao_acordos_periodo_NG).
    _sem_periodo = from_date is None or to_date is None
    stats = {
        "total_em_execucao_acordos_RJ": get_total_execucao_acordos_RJ(execucao),
        "valor_total_em_execucao_acordos_RJ": get_valor_alcada_final_total_execucao_acordos_RJ(execucao),
        "total_valor_alcada_final_vazio_acordos_RJ": get_total_valor_alcada_final_vazio_RJ(execucao),
        "total_valor_alcada_final_vazio_acordos_RJ_detalhe": get_detalhe_valor_alcada_final_vazio_RJ(execucao),
        "estoque_inicial_execucao_acordos_RJ": get_estoque_final_execucao_acordos_RJ(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "tre_execucao_acordos_RJ": get_tre_execucao_acordos_RJ_dax(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "total_entrada_execucao_acordos_periodo_RJ": get_total_entrada_execucao_acordos_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_entrada_execucao_acordos_periodo_RJ": get_valor_entrada_execucao_acordos_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "total_saida_execucao_acordos_periodo_RJ": get_total_saida_execucao_acordos_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_saida_execucao_acordos_periodo_RJ": get_valor_saida_execucao_acordos_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_ted_saida_execucao_acordos_periodo_RJ": get_valor_ted_saida_execucao_acordos_RJ_periodo(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "media_tempo_execucao_acordos_RJ": get_media_tempo_execucao_acordos_RJ(
            all_execucao, from_date, to_date
        ),
        # Durações (dias) das saídas do período — o Estratégico Geral junta Condenação + Acordos
        # para calcular média/mediana do conjunto (somar as duas médias/medianas não vale).
        "duracoes_tempo_execucao_acordos_RJ": _duracoes_execucao_acordos_rj(all_execucao, from_date, to_date),
        "mediana_tempo_execucao_acordos_RJ": get_mediana_tempo_execucao_acordos_RJ(
            all_execucao, from_date, to_date
        ),
    }
    charts = {
        "execucao_acordos_alvara_expedido_lista_RJ": list_processos_alvara_expedido_acordos_RJ(all_execucao),
        "execucao_acordos_alvaras_expedidos_por_dia_RJ": group_alvaras_expedidos_acordos_por_dia_RJ(all_execucao),
        "execucao_acordos_por_subfase_RJ": [
            ChartDataPoint(**x) for x in group_execucao_acordos_RJ_por_subfase(execucao)
        ],
        "valor_execucao_acordos_por_subfase_RJ": [
            ChartDataPoint(**x) for x in group_valor_execucao_acordos_RJ_por_subfase(execucao)
        ],
        "execucao_acordos_por_comarca_total_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_RJ_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_acordos_por_comarca_entrada_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_RJ_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_por_comarca_saida_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_RJ_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_valor_por_comarca_total_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_RJ_por_comarca(all_execucao, criterio="total")
        ],
        "execucao_acordos_valor_por_comarca_entrada_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_RJ_por_comarca(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_valor_por_comarca_saida_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_RJ_por_comarca(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_acordos_por_materia_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_RJ_por_materia(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "execucao_acordos_por_ano_ajuizamento_RJ": [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_RJ_por_ano_ajuizamento(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "valor_execucao_acordos_por_materia_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_acordos_RJ_por_materia(
                execucao, restringir_fase_atual=_sem_periodo
            )
        ],
        "execucao_acordos_por_tipo_acao_RJ": [
            ChartDataPoint(**x) for x in group_execucao_acordos_RJ_por_tipo_acao(execucao)
        ],
        "execucao_acordos_por_sentenca_RJ": [
            ChartDataPoint(**x) for x in group_execucao_acordos_RJ_por_sentenca(all_execucao)
        ],
        "valor_saida_execucao_acordos_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_saida_execucao_acordos_RJ_por_mes(all_execucao)
        ],
        "quantidade_saida_execucao_acordos_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_quantidade_saida_execucao_acordos_RJ_por_mes(all_execucao)
        ],
        "quantidade_entrada_execucao_acordos_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_quantidade_entrada_execucao_acordos_RJ_por_mes(all_execucao)
        ],
        "valor_entrada_execucao_acordos_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_valor_entrada_execucao_acordos_RJ_por_mes(all_execucao)
        ],
        **_estoque_mensal_charts(group_estoque_execucao_acordos_por_mes_RJ(all_execucao), "execucao_acordos_estoque_quantidade_por_mes_RJ", "execucao_acordos_estoque_valor_por_mes_RJ"),
        "execucao_acordos_media_tempo_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in get_media_tempo_execucao_acordos_RJ_por_mes(all_execucao)
        ],
    }

    if ag_filtrados is not None:
        stats.update(get_kpis_atividades_execucao_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats.update(get_kpis_execucao_por_prazo_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["media_mensal_atividades_execucao_acordos_RJ"] = get_media_mensal_atividades_execucao_acordos_RJ(
            ag_filtrados
        )
        charts["execucao_acordos_processos_por_atividade_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_acordos_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_atividades_ativas_por_atividade_RJ"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_criadas_por_atividade_acordos_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_processos_por_atividade_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_por_prazo_acordos_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_atividades_ativas_por_atividade_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_por_prazo_por_atividade_acordos_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_demandas_por_funcionario_RJ"] = group_execucao_demandas_por_funcionario_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_completo_RJ"] = group_execucao_demandas_por_funcionario_completo_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_por_prazo_RJ"] = group_execucao_demandas_por_funcionario_por_prazo_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_demandas_por_funcionario_por_prazo_completo_RJ"] = group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_acordos_resolvidos_por_dia_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_acordos_RJ(ag_filtrados)
        ]
        charts["execucao_acordos_resolvidos_por_dia_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_por_prazo_acordos_RJ(ag_filtrados)
        ]
        charts["execucao_acordos_media_resolvidos_por_funcionario_RJ"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_acordos_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_media_resolvidos_por_funcionario_por_prazo_RJ"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_RJ(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_nao_cumprido_por_motivo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_nao_cumprido_por_motivo_acordos_RJ(ag_filtrados)
        ]
        charts["execucao_acordos_atividades_lista_RJ"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in _enriquecer_atividades_acordos_rj_com_dados_processo(
                list_execucao_atividades_periodo_acordos_RJ(
                    ag_filtrados, from_date=from_date, to_date=to_date
                ),
                ag_filtrados,
                all_execucao,
            )
        ]
        charts["execucao_acordos_atividades_lista_por_prazo_RJ"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in _enriquecer_atividades_acordos_rj_com_dados_processo(
                list_execucao_atividades_por_prazo_periodo_acordos_RJ(
                    ag_filtrados, from_date=from_date, to_date=to_date
                ),
                ag_filtrados,
                all_execucao,
            )
        ]
        charts["execucao_acordos_atividades_lista_filtros_opcoes_RJ"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_acordos_RJ(agendamentos, from_date=from_date, to_date=to_date)
        )
        charts["execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_RJ"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_por_prazo_acordos_RJ(agendamentos, from_date=from_date, to_date=to_date)
        )
        atrasos_raw_acordos = get_atrasos_detalhamento_execucao_acordos_RJ(ag_filtrados)
        charts["execucao_acordos_atrasos_detalhamento_RJ"] = ExecucaoAtrasosDetalhamento(
            total=atrasos_raw_acordos["total"],
            buckets=[ExecucaoAtrasoBucket(**b) for b in atrasos_raw_acordos["buckets"]],
        )

        # Diligências: subconjunto de `agendamentos` (não `ag_filtrados` — independente
        # dos filtros de funcionário/atividade/status/situação da seção Atividades).
        diligencias_ag = filtrar_agendamentos_diligencia_acordos_RJ(agendamentos)
        stats["total_diligencias_execucao_acordos_RJ"] = get_total_diligencias_execucao_acordos_RJ(
            diligencias_ag, from_date=from_date, to_date=to_date
        )

        # Os dois gráficos (processo e ranking por colaborador) respeitam o clique
        # nos cards de tipo ("Diligências de Expedição de Alvará"/"Cumpridas") — os
        # KPIs abaixo continuam usando `diligencias_ag` (não filtrado), como
        # referência fixa, igual aos cards de situação da seção Atividades.
        diligencias_ag_tipo_filtradas = filtrar_agendamentos_diligencia_por_tipo_acordos_RJ(
            diligencias_ag, diligencia_tipo_filtro
        )
        # Só o gráfico "Processos com mais Diligências" também respeita o clique no
        # colaborador do ranking — o próprio ranking mantém todos os colaboradores
        # visíveis para comparação (mesmo padrão da seção Atividades).
        diligencias_ag_processo = filtrar_agendamentos_diligencia_por_colaborador_acordos_RJ(
            diligencias_ag_tipo_filtradas, diligencia_colaborador_filtro
        )
        charts["execucao_acordos_diligencias_por_processo_RJ"] = [
            ChartDataPoint(**x)
            for x in group_execucao_acordos_diligencias_por_processo_RJ(
                diligencias_ag_processo, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_diligencias_por_funcionario_RJ"] = (
            group_execucao_demandas_por_funcionario_acordos_RJ(
                diligencias_ag_tipo_filtradas, from_date=from_date, to_date=to_date
            )
        )

        expedicao_alvara_ag = filtrar_agendamentos_diligencia_expedicao_alvara_acordos_RJ(
            diligencias_ag
        )
        kpis_expedicao_alvara = get_kpis_diligencias_expedicao_alvara_acordos_RJ(
            expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
            colaborador=diligencia_colaborador_filtro,
        )
        stats["total_diligencias_expedicao_alvara_execucao_acordos_RJ"] = kpis_expedicao_alvara["total"]
        stats["cumpridas_diligencias_expedicao_alvara_execucao_acordos_RJ"] = kpis_expedicao_alvara["cumpridas"]
        stats["valor_diligencias_expedicao_alvara_execucao_acordos_RJ"] = kpis_expedicao_alvara["valor"]
        charts["execucao_acordos_diligencias_expedicao_alvara_processos_RJ"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_processos_diligencia_expedicao_alvara_cumprida_acordos_RJ(
                expedicao_alvara_ag, all_execucao, from_date=from_date, to_date=to_date,
                colaborador=diligencia_colaborador_filtro,
            )
        ]

    return stats, charts


# v1: dashboard_routes.py:9216
def _build_execucao_LA_stats(
    execucao: List[Dict],
    all_execucao: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    execucao_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder para o domínio Execução LA.

    execucao     → dados filtrados por DATA_EXECUCAO (via filter_data)
    all_execucao → dados sem filtro de data (necessário para calcular saídas no período,
                   pois DATA_SAIDA não é a coluna usada pelo filter_data deste domínio)
    agendamentos → agendamentos do setor Execução para a seção Atividades no período

    Quando filtros de agendamento estão ativos, os dados de processo (execucao / all_execucao)
    são restritos aos processos que possuem agendamentos correspondentes — isso faz com que
    todas as seções da página reflitam o mesmo recorte.
    """
    # Pré-calcular agendamentos filtrados quando disponíveis
    # Antes do recorte por filtro de atividade abaixo (mesmo motivo do NG).
    entrada_fluxo_cs_por_mes = (
        group_entrada_execucao_por_fluxo_cs_por_mes_LA(all_execucao, agendamentos)
        if agendamentos is not None
        else None
    )
    # Antes do recorte por filtro de atividade (mesmo motivo do gráfico de fluxo).
    taxa_atualizacao = (
        get_taxa_atualizacao_execucao_LA(all_execucao, agendamentos, from_date, to_date)
        if agendamentos is not None
        else None
    )
    alvara_expedido_lista = list_processos_alvara_expedido_LA(all_execucao)
    ag_filtrados: Optional[List[Dict]] = None
    if agendamentos is not None:
        ag_filtrados = filtrar_agendamentos_execucao_LA(
            agendamentos,
            execucao_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        # Quando há filtros ativos, restringir dados de processo aos IDs correspondentes
        if execucao_atividades_filtros is not None and execucao_atividades_filtros.ativo():
            processo_ids = frozenset(
                pid
                for row in ag_filtrados
                if (pid := _get_ag_processo_id(row)) is not None
            )
            if processo_ids:
                execucao = [r for r in execucao if (r.get("id") or r.get("ID")) in processo_ids]
                all_execucao = [r for r in all_execucao if (r.get("id") or r.get("ID")) in processo_ids]
            else:
                execucao = []
                all_execucao = []

    stats = {
        "total_em_execucao_LA": get_total_execucao_LA(execucao),
        "valor_total_em_execucao_LA": get_valor_causa_total_execucao_LA(execucao),
        "total_valor_execucao_vazio_LA": get_total_valor_execucao_vazio_LA(execucao),
        "total_valor_execucao_vazio_LA_detalhe": get_detalhe_valor_execucao_vazio_LA(execucao),
        "valor_honorarios_total_execucao_LA": get_valor_honorarios_total_execucao_LA(
            execucao
        ),
        "valor_em_execucao_LA": get_valor_em_execucao_LA(execucao),
        "valor_remanescente_em_execucao_LA": get_valor_remanescente_em_execucao_LA(execucao),
        "estoque_inicial_LA": get_estoque_final_LA(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "tre_LA": get_tre_execucao_dax_LA(
            all_execucao,
            from_date,
            to_date,
            execucao_fluxos_periodo=all_execucao,
        ),
        "total_saida_execucao_periodo_LA": get_total_saida_execucao_periodo_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "total_incontroverso_saida_execucao_periodo_LA": get_total_incontroverso_saida_periodo_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_execucao_saida_periodo_LA": get_valor_execucao_saida_periodo_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_incontroverso_saida_execucao_periodo_LA": get_valor_incontroverso_saida_periodo_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "valor_ted_saida_execucao_periodo_LA": get_valor_ted_saida_execucao_periodo_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "taxa_recuperacao_execucao_LA": get_taxa_recuperacao_execucao_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        "taxa_atualizacao_execucao_LA": taxa_atualizacao,
        "media_tempo_execucao_LA": get_media_tempo_execucao_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
        # Durações (dias) das saídas do período — o Estratégico Geral junta Condenação + Acordos
        # para calcular média/mediana do conjunto (somar as duas médias/medianas não vale).
        "duracoes_tempo_execucao_LA": _duracoes_execucao_la(all_execucao, from_date, to_date),
        "mediana_tempo_execucao_LA": get_mediana_tempo_execucao_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
    }
    charts = {
        "execucao_entrada_fluxo_cs_por_mes_LA": entrada_fluxo_cs_por_mes,
        "execucao_alvara_expedido_lista_LA": alvara_expedido_lista,
        "execucao_alvaras_expedidos_por_dia_LA": group_alvaras_expedidos_por_dia_LA(all_execucao),
        "execucao_por_subfase_LA": [ChartDataPoint(**x) for x in group_execucao_por_subfase_LA(execucao)],
        "valor_execucao_por_subfase_LA": [
            ChartDataPoint(**x) for x in group_valor_execucao_por_subfase_LA(execucao)
        ],
        "execucao_por_comarca_total_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_por_comarca_LA(all_execucao, criterio="total")
        ],
        "execucao_por_comarca_entrada_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_por_comarca_LA(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_por_comarca_saida_LA": [
            ChartDataPoint(**x)
            for x in group_execucao_por_comarca_LA(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_valor_por_comarca_total_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_comarca_LA(all_execucao, criterio="total")
        ],
        "execucao_valor_por_comarca_entrada_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_comarca_LA(
                all_execucao, criterio="entrada", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_valor_por_comarca_saida_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_por_comarca_LA(
                all_execucao, criterio="saida", from_date=from_date, to_date=to_date
            )
        ],
        "execucao_por_materia_LA": [ChartDataPoint(**x) for x in group_execucao_por_materia_LA(execucao)],
        "valor_execucao_por_materia_LA": [
            ChartDataPoint(**x) for x in group_valor_execucao_por_materia_LA(execucao)
        ],
        "execucao_por_ano_ajuizamento_LA": [
            ChartDataPoint(**x) for x in group_execucao_por_ano_ajuizamento_LA(execucao)
        ],
        **_estoque_mensal_charts(group_estoque_execucao_por_mes_LA(all_execucao), "execucao_estoque_quantidade_por_mes_LA", "execucao_estoque_valor_por_mes_LA"),
        "execucao_media_tempo_por_mes_LA": [
            ChartDataPoint(**x) for x in get_media_tempo_execucao_por_mes_LA(all_execucao)
        ],
        "valor_saida_execucao_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_valor_saida_execucao_por_mes_LA(all_execucao)
        ],
        "valor_execucao_saida_periodo_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_valor_execucao_saida_periodo_por_mes_LA(all_execucao)
        ],
        "valor_remanescente_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_valor_remanescente_por_mes_LA(all_execucao)
        ],
        "quantidade_saida_execucao_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_quantidade_saida_execucao_por_mes_LA(all_execucao)
        ],
        "quantidade_entrada_execucao_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_quantidade_entrada_execucao_por_mes_LA(all_execucao)
        ],
        "valor_entrada_execucao_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_valor_entrada_execucao_por_mes_LA(all_execucao)
        ],
    }

    if ag_filtrados is not None:
        stats.update(get_kpis_atividades_execucao_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats.update(get_kpis_execucao_por_prazo_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["media_mensal_atividades_execucao_LA"] = get_media_mensal_atividades_execucao_LA(
            ag_filtrados
        )
        charts["execucao_processos_por_atividade_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_ativas_por_atividade_LA"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_criadas_por_atividade_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_criadas_por_atividade_LA"] = [
            ChartDataPoint(**x)
            for x in group_atividades_criadas_por_atividade_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_processos_por_atividade_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_processos_por_atividade_por_prazo_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_ativas_por_atividade_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in group_atividades_ativas_por_prazo_por_atividade_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_demandas_por_funcionario_LA"] = group_execucao_demandas_por_funcionario_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_completo_LA"] = group_execucao_demandas_por_funcionario_completo_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_taxa_conclusao_por_funcionario_LA"] = group_taxa_conclusao_por_funcionario_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_por_prazo_LA"] = group_execucao_demandas_por_funcionario_por_prazo_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_demandas_por_funcionario_por_prazo_completo_LA"] = group_execucao_demandas_por_funcionario_por_prazo_completo_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        charts["execucao_valor_recuperado_por_funcionario_LA"] = [
            ChartDataPoint(**x)
            for x in group_valor_recuperado_por_funcionario_LA(
                ag_filtrados, all_execucao, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_resolvidos_por_dia_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_LA(ag_filtrados)
        ]
        charts["execucao_resolvidos_por_dia_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_resolvidos_por_dia_por_prazo_LA(ag_filtrados)
        ]
        charts["execucao_media_resolvidos_por_funcionario_LA"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_media_resolvidos_por_funcionario_por_prazo_LA"] = [
            ChartDataPoint(**x)
            for x in get_media_execucao_resolvidos_por_funcionario_por_prazo_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_nao_cumprido_por_motivo_LA"] = [
            ChartDataPoint(**x)
            for x in group_execucao_nao_cumprido_por_motivo_LA(ag_filtrados)
        ]
        charts["execucao_atividades_lista_LA"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_periodo_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_abertas_LA"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_abertas_LA(ag_filtrados)
        ]
        charts["execucao_atividades_lista_por_prazo_LA"] = [
            RecursalAtividadeTarefaRow(**x)
            for x in list_execucao_atividades_por_prazo_periodo_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_atividades_lista_filtros_opcoes_LA"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_LA(agendamentos, from_date=from_date, to_date=to_date)
        )
        charts["execucao_atividades_lista_filtros_opcoes_por_prazo_LA"] = RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_execucao_por_prazo_LA(agendamentos, from_date=from_date, to_date=to_date)
        )
        atrasos_raw = get_atrasos_detalhamento_execucao_LA(ag_filtrados)
        charts["execucao_atrasos_detalhamento_LA"] = ExecucaoAtrasosDetalhamento(
            total=atrasos_raw["total"],
            buckets=[ExecucaoAtrasoBucket(**b) for b in atrasos_raw["buckets"]],
        )

    return stats, charts


# v1: dashboard_routes.py:9516
_DECISOES_RECURSAL_VALIDAS = frozenset({
    DECISAO_MANTIDO_GANHO,
    DECISAO_GANHO_AMPLIADO,
    DECISAO_REVERTIDO_GANHO,
    DECISAO_GANHO_REDUZIDO,
    DECISAO_MANTIDO_PERDA,
    DECISAO_REVERTIDO_PERDA,
    DECISAO_EXTINCAO_REAJUIZAR,
    DECISAO_INSTRUCAO_RETOMADA,
})


# v1: dashboard_routes.py:9527
_EXTINTOS_2G_RECURSAL_VALIDOS = frozenset({"com_merito", "sem_merito"})


# v1: dashboard_routes.py:9530
def _parse_recursal_atividades_recursos_filtros(
    funcionario_recursos: Optional[List[str]] = None,
    atividade_recursos: Optional[List[str]] = None,
    status_recursos: Optional[List[str]] = None,
    situacao_recursos: Optional[List[str]] = None,
) -> Optional[RecursalAtividadesRecursosFiltros]:
    """Filtros cumulativos da seção Atividades no período (agendamentos RECURSOS)."""
    funcionarios: set[str] = set()
    if funcionario_recursos:
        for nome in funcionario_recursos:
            t = str(nome or "").strip()
            if t:
                funcionarios.add(t)

    atividades: set[str] = set()
    if atividade_recursos:
        for raw in atividade_recursos:
            t = str(raw or "").strip()
            if t:
                atividades.add(t)

    status: set[str] = set()
    if status_recursos:
        for raw in status_recursos:
            t = str(raw or "").strip()
            if t:
                status.add(t)

    situacoes: set[str] = set()
    if situacao_recursos:
        for raw in situacao_recursos:
            chave = str(raw or "").strip()
            if not chave:
                continue
            if chave not in _SITUACOES_RECURSOS_VALIDAS:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Situação inválida: '{chave}'. "
                        f"Valores: {sorted(_SITUACOES_RECURSOS_VALIDAS)}"
                    ),
                )
            situacoes.add(chave)

    filtros = RecursalAtividadesRecursosFiltros(
        funcionarios=frozenset(funcionarios) if funcionarios else None,
        atividades=frozenset(atividades) if atividades else None,
        status=frozenset(status) if status else None,
        situacoes=frozenset(situacoes) if situacoes else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:9583
def _parse_recursal_la_filtros_completos(
    id_1g: Optional[List[int]] = None,
    id_2g: Optional[List[int]] = None,
    juiz: Optional[List[str]] = None,
    relator: Optional[List[str]] = None,
    decisao: Optional[List[str]] = None,
    materia: Optional[List[str]] = None,
    parte_adversa: Optional[List[str]] = None,
    competencia: Optional[List[str]] = None,
    vara: Optional[List[str]] = None,
    subfase: Optional[List[str]] = None,
    fase: Optional[List[str]] = None,
    operacao: Optional[List[str]] = None,
    extinto_2g: Optional[List[str]] = None,
    funcionario_recursos: Optional[List[str]] = None,
    atividade_recursos: Optional[List[str]] = None,
    status_recursos: Optional[List[str]] = None,
    situacao_recursos: Optional[List[str]] = None,
) -> Tuple[Optional[RecursalLAFiltros], Optional[RecursalAtividadesRecursosFiltros]]:
    """Filtros de processo + filtros de agendamentos RECURSOS (seção Atividades)."""
    return (
        _parse_recursal_la_filtros(
            id_1g=id_1g,
            id_2g=id_2g,
            juiz=juiz,
            relator=relator,
            decisao=decisao,
            materia=materia,
            parte_adversa=parte_adversa,
            competencia=competencia,
            vara=vara,
            subfase=subfase,
            fase=fase,
            operacao=operacao,
            extinto_2g=extinto_2g,
        ),
        _parse_recursal_atividades_recursos_filtros(
            funcionario_recursos=funcionario_recursos,
            atividade_recursos=atividade_recursos,
            status_recursos=status_recursos,
            situacao_recursos=situacao_recursos,
        ),
    )


# v1: dashboard_routes.py:9628
def _parse_recursal_la_filtros(
    id_1g: Optional[List[int]] = None,
    id_2g: Optional[List[int]] = None,
    juiz: Optional[List[str]] = None,
    relator: Optional[List[str]] = None,
    decisao: Optional[List[str]] = None,
    materia: Optional[List[str]] = None,
    parte_adversa: Optional[List[str]] = None,
    competencia: Optional[List[str]] = None,
    vara: Optional[List[str]] = None,
    subfase: Optional[List[str]] = None,
    fase: Optional[List[str]] = None,
    operacao: Optional[List[str]] = None,
    atividade: Optional[List[str]] = None,
    extinto_2g: Optional[List[str]] = None,
) -> Optional[RecursalLAFiltros]:
    """Monta filtros cumulativos a partir dos query params do dashboard Recursal LA."""
    ids_1g: set[int] = set()
    if id_1g:
        for raw in id_1g:
            if raw is not None:
                ids_1g.add(int(raw))

    ids_2g: set[int] = set()
    if id_2g:
        for raw in id_2g:
            if raw is not None:
                ids_2g.add(int(raw))

    juizes: set[str] = set()
    if juiz:
        for nome in juiz:
            t = str(nome or "").strip()
            if t:
                juizes.add(t)

    relatores: set[str] = set()
    if relator:
        for nome in relator:
            t = str(nome or "").strip()
            if t:
                relatores.add(t)

    decisoes: set[str] = set()
    if decisao:
        for raw in decisao:
            chave = str(raw or "").strip()
            if not chave:
                continue
            if chave not in _DECISOES_RECURSAL_VALIDAS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Decisão inválida: '{chave}'. Valores: {sorted(_DECISOES_RECURSAL_VALIDAS)}",
                )
            decisoes.add(chave)

    materias: set[str] = set()
    if materia:
        for raw in materia:
            t = str(raw or "").strip()
            if t:
                materias.add(t)

    partes_adversas: set[str] = set()
    if parte_adversa:
        for raw in parte_adversa:
            t = str(raw or "").strip()
            if t:
                partes_adversas.add(t)

    competencias: set[str] = set()
    if competencia:
        for raw in competencia:
            t = str(raw or "").strip()
            if t:
                competencias.add(t)

    varas: set[str] = set()
    if vara:
        for raw in vara:
            t = str(raw or "").strip()
            if t:
                varas.add(t)

    subfases: set[str] = set()
    if subfase:
        for raw in subfase:
            t = str(raw or "").strip()
            if t:
                subfases.add(t)

    fases: set[str] = set()
    if fase:
        for raw in fase:
            t = str(raw or "").strip()
            if t:
                fases.add(t)

    operacoes: set[str] = set()
    if operacao:
        for raw in operacao:
            t = str(raw or "").strip()
            if t:
                operacoes.add(t)

    atividades: set[str] = set()
    if atividade:
        for raw in atividade:
            t = str(raw or "").strip()
            if t:
                atividades.add(t)

    extintos_2g: set[str] = set()
    if extinto_2g:
        for raw in extinto_2g:
            chave = str(raw or "").strip()
            if not chave:
                continue
            if chave not in _EXTINTOS_2G_RECURSAL_VALIDOS:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Extinto 2G inválido: '{chave}'. "
                        f"Valores: {sorted(_EXTINTOS_2G_RECURSAL_VALIDOS)}"
                    ),
                )
            extintos_2g.add(chave)

    filtros = RecursalLAFiltros(
        id_1g=frozenset(ids_1g) if ids_1g else None,
        id_2g=frozenset(ids_2g) if ids_2g else None,
        juizes=frozenset(juizes) if juizes else None,
        relatores=frozenset(relatores) if relatores else None,
        decisoes=frozenset(decisoes) if decisoes else None,
        materias=frozenset(materias) if materias else None,
        partes_adversas=frozenset(partes_adversas) if partes_adversas else None,
        competencias=frozenset(competencias) if competencias else None,
        varas=frozenset(varas) if varas else None,
        subfases=frozenset(subfases) if subfases else None,
        fases=frozenset(fases) if fases else None,
        operacoes=frozenset(operacoes) if operacoes else None,
        atividades=frozenset(atividades) if atividades else None,
        extintos_2g=frozenset(extintos_2g) if extintos_2g else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:9828
async def _recursal_la_distribuicao_response(
    *,
    dashboard_slug: str,
    chart_field: str,
    group_fn: Any,
    from_date: Optional[date],
    to_date: Optional[date],
    base: str,
    filtros: Optional[RecursalLAFiltros],
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
) -> DashboardResponse:
    """Resposta padrão para gráficos de distribuição (subfase, matéria, UF, operação)."""
    base_norm = (base or "estoque").strip().lower()
    if base_norm not in ("estoque", "entrada"):
        base_norm = "estoque"

    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        atividades_recursos_filtros,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_fn(
            all_rows,
            from_date=from_date,
            to_date=to_date,
            base=base_norm,
        )
    ]

    if base_norm == "entrada":
        total_base = get_entrada_recurso_LA(all_rows, from_date, to_date)
        stats = DashboardStats(entrada_recursal_LA=total_base)
    else:
        total_base = get_total_recurso_LA(all_rows)
        stats = DashboardStats(total_recursal_LA=total_base)

    return DashboardResponse(
        dashboard=dashboard_slug,
        stats=stats,
        **{chart_field: chart},
    )


# v1: dashboard_routes.py:9875
def _aplicar_filtros_recursal_la_rows(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
) -> List[Dict]:
    return filtrar_recursal_LA(rows, filtros)


# v1: dashboard_routes.py:9882
async def _rows_recursal_la_filtradas(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    agendamentos: Optional[List[Dict]] = None,
    atividades_catalogo: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Aplica filtros de processo (fase Recursal) e, quando ativos, restringe aos
    processos vinculados a agendamentos RECURSOS filtrados no período.

    Sempre atualiza o catálogo dinâmico de atividades do setor RECURSOS (LA) antes
    de filtrar — via ``atividades_catalogo`` (se já disponível no caller) ou
    buscando (cacheado) quando omitido — pois ``filtrar_recursal_LA`` já restringe
    ao escopo do setor RECURSOS internamente.
    """
    if atividades_catalogo is None:
        atividades_catalogo = await fetch_atividades_setor_recursos_LA()
    set_atividades_recursos_LA_catalogo(atividades_catalogo)
    if atividades_recursos_filtros is not None and atividades_recursos_filtros.ativo():
        ag_base = agendamentos
        if ag_base is None:
            ag_base = await fetch_agendamentos_setor_recursos_LA()
        processo_ids = processo_ids_recursal_de_agendamentos_recursos_LA(
            ag_base,
            atividades_recursos_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        rows = filtrar_recursal_LA_por_processo_ids(rows, processo_ids)
    return _aplicar_filtros_recursal_la_rows(rows, filtros)


# v1: dashboard_routes.py:9918
async def _recursal_ng_distribuicao_response(
    *,
    dashboard_slug: str,
    chart_field: str,
    group_fn: Any,
    from_date: Optional[date],
    to_date: Optional[date],
    base: str,
    filtros: Optional[RecursalLAFiltros],
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
) -> DashboardResponse:
    """Resposta padrão para gráficos de distribuição (subfase, matéria, UF, operação) — NG."""
    base_norm = (base or "estoque").strip().lower()
    if base_norm not in ("estoque", "entrada"):
        base_norm = "estoque"

    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        atividades_recursos_filtros,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_fn(
            all_rows,
            from_date=from_date,
            to_date=to_date,
            base=base_norm,
        )
    ]

    if base_norm == "entrada":
        total_base = get_entrada_recurso_NG(all_rows, from_date, to_date)
        stats = DashboardStats(entrada_recursal_NG=total_base)
    else:
        total_base = get_total_recurso_NG(all_rows)
        stats = DashboardStats(total_recursal_NG=total_base)

    return DashboardResponse(
        dashboard=dashboard_slug,
        stats=stats,
        **{chart_field: chart},
    )


# v1: dashboard_routes.py:9965
def _aplicar_filtros_recursal_ng_rows(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
) -> List[Dict]:
    return filtrar_recursal_NG(rows, filtros)


# v1: dashboard_routes.py:9972
async def _rows_recursal_ng_filtradas(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    agendamentos: Optional[List[Dict]] = None,
    atividades_catalogo: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Aplica filtros de processo (fase Recursal) e, quando ativos, restringe aos
    processos vinculados a agendamentos RECURSOS (NG) filtrados no período.

    Sempre atualiza o catálogo dinâmico de atividades do setor RECURSOS (NG) antes
    de filtrar — via ``atividades_catalogo`` (se já disponível no caller) ou
    buscando (cacheado) quando omitido — pois ``filtrar_recursal_NG`` já restringe
    ao escopo do setor RECURSOS internamente.
    """
    if atividades_catalogo is None:
        atividades_catalogo = await fetch_atividades_setor_recursos_NG()
    set_atividades_recursos_NG_catalogo(atividades_catalogo)
    if atividades_recursos_filtros is not None and atividades_recursos_filtros.ativo():
        ag_base = agendamentos
        if ag_base is None:
            ag_base = await fetch_agendamentos_setor_recursos_NG()
        processo_ids = processo_ids_recursal_de_agendamentos_recursos_NG(
            ag_base,
            atividades_recursos_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        rows = filtrar_recursal_NG_por_processo_ids(rows, processo_ids)
    return _aplicar_filtros_recursal_ng_rows(rows, filtros)


# v1: dashboard_routes.py:10008
async def _recursal_rj_distribuicao_response(
    *,
    dashboard_slug: str,
    chart_field: str,
    group_fn: Any,
    from_date: Optional[date],
    to_date: Optional[date],
    base: str,
    filtros: Optional[RecursalLAFiltros],
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
) -> DashboardResponse:
    """Resposta padrão para gráficos de distribuição (subfase, matéria, UF, operação) — RJ."""
    base_norm = (base or "estoque").strip().lower()
    if base_norm not in ("estoque", "entrada"):
        base_norm = "estoque"

    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        atividades_recursos_filtros,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_fn(
            all_rows,
            from_date=from_date,
            to_date=to_date,
            base=base_norm,
        )
    ]

    if base_norm == "entrada":
        total_base = get_entrada_recurso_RJ(all_rows, from_date, to_date)
        stats = DashboardStats(entrada_recursal_RJ=total_base)
    else:
        total_base = get_total_recurso_RJ(all_rows)
        stats = DashboardStats(total_recursal_RJ=total_base)

    return DashboardResponse(
        dashboard=dashboard_slug,
        stats=stats,
        **{chart_field: chart},
    )


# v1: dashboard_routes.py:10055
def _aplicar_filtros_recursal_rj_rows(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
) -> List[Dict]:
    return filtrar_recursal_RJ(rows, filtros)


# v1: dashboard_routes.py:10062
async def _rows_recursal_rj_filtradas(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    agendamentos: Optional[List[Dict]] = None,
    atividades_catalogo: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Aplica filtros de processo (fase Recursal) e, quando ativos, restringe aos
    processos vinculados a agendamentos RECURSOS (RJ) filtrados no período.

    Sempre atualiza o catálogo dinâmico de atividades do setor RECURSOS (RJ) antes
    de filtrar — via ``atividades_catalogo`` (se já disponível no caller) ou
    buscando (cacheado) quando omitido — pois ``filtrar_recursal_RJ`` já restringe
    ao escopo do setor RECURSOS internamente.
    """
    if atividades_catalogo is None:
        atividades_catalogo = await fetch_atividades_setor_recursos_RJ()
    set_atividades_recursos_RJ_catalogo(atividades_catalogo)
    if atividades_recursos_filtros is not None and atividades_recursos_filtros.ativo():
        ag_base = agendamentos
        if ag_base is None:
            ag_base = await fetch_agendamentos_setor_recursos_RJ()
        processo_ids = processo_ids_recursal_de_agendamentos_recursos_RJ(
            ag_base,
            atividades_recursos_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        rows = filtrar_recursal_RJ_por_processo_ids(rows, processo_ids)
    return _aplicar_filtros_recursal_rj_rows(rows, filtros)


# v1: dashboard_routes.py:10098
def _chart_from_decisoes_item(item: Dict[str, Any]) -> ChartDataPoint:
    return ChartDataPoint(
        name=str(item.get("name") or ""),
        value=float(item.get("value") or 0),
        percent=item.get("percent"),
        valor_causa=item.get("valor_causa"),
        tipo=item.get("tipo"),
    )


# v1: dashboard_routes.py:10108
def _build_recursal_LA_stats(
    all_recursal: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    atividades_catalogo: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder do domínio Fase Recursal LA — três métricas independentes:

    ``atividades_catalogo`` é o catálogo dinâmico de atividades do setor RECURSOS (LA)
    (query ``atividades_setor_recursos_LA``, cacheada); atualiza a whitelist usada por
    ``recurso_LA`` antes de qualquer cálculo desta função.

    - ``total_recursal_LA``: estoque (``ID_FASE`` = 8), sem filtro de data
    - ``entrada_recursal_LA``: fase 8 com ``DT_ENTRADA_RECURSAL`` no período
    """
    set_atividades_recursos_LA_catalogo(atividades_catalogo or [])
    stats = {
        "total_recursal_LA": get_total_recurso_LA(all_recursal),
        "entrada_recursal_LA": get_entrada_recurso_LA(
            all_recursal,
            from_date=from_date,
            to_date=to_date,
        ),
        "valor_causa_acordo_recursal_LA": get_valor_causa_acordo_recurso_LA(all_recursal),
        "total_sentenca_favoravel_recurso_LA": get_total_sentenca_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_desfavoravel_recurso_LA": get_total_sentenca_desfavoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_procedente_1g_recurso_LA": get_total_procedente_1g_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_parcialmente_procedente_recurso_LA": get_total_parcialmente_procedente_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_extincao_recurso_LA": get_total_sentenca_extincao_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_parcialmente_favoravel_recurso_LA": (
            get_total_sentenca_parcialmente_favoravel_recurso_LA(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ),
        "valor_causa_sentenca_favoravel_recurso_LA": get_valor_causa_sentenca_sentenca_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_desfavoravel_recurso_LA": get_valor_causa_sentenca_sentenca_desfavoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_procedente_1g_recurso_LA": get_valor_causa_sentenca_procedente_1g_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_parcialmente_procedente_recurso_LA": get_valor_causa_sentenca_parcialmente_procedente_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_extincao_recurso_LA": get_valor_causa_sentenca_sentenca_extincao_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_parcialmente_favoravel_recurso_LA": get_valor_causa_sentenca_parcialmente_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_desfavoravel_recurso_LA": get_total_acordao_desfavoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_favoravel_recurso_LA": get_total_acordao_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_parcialmente_favoravel_recurso_LA": get_total_acordao_parcialmente_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_parcial_retomada_recurso_LA": get_total_acordao_parcial_retomada_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_extincao_recurso_LA": get_total_acordao_extincao_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_desfavoravel_recurso_LA": get_valor_causa_acordao_desfavoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_favoravel_recurso_LA": get_valor_causa_acordao_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_parcialmente_favoravel_recurso_LA": get_valor_causa_acordao_parcialmente_favoravel_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_parcial_retomada_recurso_LA": get_valor_causa_acordao_parcial_retomada_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_extincao_recurso_LA": get_valor_causa_acordao_extincao_recurso_LA(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        **_build_decisoes_recursal_LA_stats(all_recursal, from_date, to_date),
    }
    agendamentos_base = agendamentos or []
    agendamentos_filtrados = filtrar_agendamentos_recursos_LA(
        agendamentos_base,
        atividades_recursos_filtros,
        from_date=from_date,
        to_date=to_date,
    )
    stats.update(
        get_kpis_atividades_recursos_LA(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        )
    )
    stats.update(
        get_kpis_atividades_recursos_por_prazo_LA(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        )
    )
    funcionarios_producao_recursal_la, por_dia_por_func_producao_recursal_la = _per_func_to_chart(
        get_recursal_resolvidos_por_dia_por_funcionario_LA(agendamentos_filtrados)
    )
    charts = {
        "recursal_por_subfase_LA": [
            ChartDataPoint(**x)
            for x in group_recursal_por_subfase_LA(all_recursal)
        ],
        "recursal_por_status_1g_LA": [
            ChartDataPoint(**x)
            for x in group_recursal_por_status_1g_LA(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_por_status_2g_LA": [
            ChartDataPoint(**x)
            for x in group_recursal_por_status_2g_LA(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_decisoes_LA": [
            ChartDataPoint(**x)
            for x in group_decisoes_recursal_LA(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "ranking_juizes_recursal_LA": [
            RecursalRankingMagistradoRow(**x)
            for x in get_ranking_juizes_recursal_LA(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "ranking_relatores_recursal_LA": [
            RecursalRankingMagistradoRow(**x)
            for x in get_ranking_relatores_recursal_LA(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_processos_por_atividade_LA": [
            ChartDataPoint(**x)
            for x in group_recursal_processos_por_atividade_LA(
                agendamentos_filtrados,
                from_date=from_date,
                to_date=to_date,
            )
        ],
        "recursal_demandas_por_funcionario_LA": group_recursal_demandas_por_funcionario_LA(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        ),
        "recursal_resolvidos_por_dia_LA": [
            ChartDataPoint(**x)
            for x in group_recursal_resolvidos_por_dia_LA(agendamentos_filtrados)
        ],
        "recursal_resolvidos_por_mes_LA": [
            ChartDataPoint(**x)
            for x in group_recursal_resolvidos_por_mes_LA(agendamentos_filtrados)
        ],
        "funcionarios_recursal_LA": funcionarios_producao_recursal_la,
        "recursal_resolvidos_por_dia_por_funcionario_LA": {
            k: [ChartDataPoint(**i) for i in v]
            for k, v in por_dia_por_func_producao_recursal_la.items()
        },
        "recursal_media_resolvidos_por_funcionario_LA": [
            ChartDataPoint(**x)
            for x in get_media_recursal_resolvidos_por_funcionario_LA(
                agendamentos_filtrados, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_atividades_lista_LA": [
            RecursalAtividadeTarefaRow(**x)
            for x in list_recursal_atividades_periodo_LA(
                agendamentos_filtrados,
                from_date=from_date,
                to_date=to_date,
            )
        ],
        "recursal_atividades_lista_filtros_opcoes_LA": RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_atividades_lista_LA(
                agendamentos_base,
                from_date=from_date,
                to_date=to_date,
            )
        ),
    }
    return stats, charts


# v1: dashboard_routes.py:10315
def _build_decisoes_recursal_LA_stats(
    all_recursal: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Dict[str, Any]:
    """Stats de decisões recursais (cruzamento 1G × 2G, filtro por ``DATA_ACORDAO``)."""
    resumo = get_decisoes_recursal_resumo_LA(all_recursal, from_date=from_date, to_date=to_date)
    por_tipo = {str(item["tipo"]): item for item in resumo.get("itens", [])}

    def _item(tipo: str, campo_total: str, campo_percent: str, campo_valor: str) -> Dict[str, Any]:
        row = por_tipo.get(tipo, {})
        return {
            campo_total: row.get("value", 0),
            campo_percent: row.get("percent", 0.0),
            campo_valor: row.get("valor_causa", 0.0),
        }

    stats: Dict[str, Any] = {"total_decisoes_recursal_LA": resumo.get("total", 0)}
    _tipos = [
        (DECISAO_MANTIDO_GANHO,     "total_mantido_ganho_recurso_LA",     "percent_mantido_ganho_recursal_LA",     "valor_causa_mantido_ganho_recurso_LA"),
        (DECISAO_GANHO_AMPLIADO,    "total_ganho_ampliado_recurso_LA",    "percent_ganho_ampliado_recursal_LA",    "valor_causa_ganho_ampliado_recurso_LA"),
        (DECISAO_REVERTIDO_GANHO,   "total_revertido_ganho_recurso_LA",   "percent_revertido_ganho_recursal_LA",   "valor_causa_revertido_ganho_recurso_LA"),
        (DECISAO_GANHO_REDUZIDO,    "total_ganho_reduzido_recurso_LA",    "percent_ganho_reduzido_recursal_LA",    "valor_causa_ganho_reduzido_recurso_LA"),
        (DECISAO_MANTIDO_PERDA,     "total_mantido_perda_recurso_LA",     "percent_mantido_perda_recursal_LA",     "valor_causa_mantido_perda_recurso_LA"),
        (DECISAO_REVERTIDO_PERDA,   "total_revertido_perda_recurso_LA",   "percent_revertido_perda_recursal_LA",   "valor_causa_revertido_perda_recurso_LA"),
        (DECISAO_EXTINCAO_REAJUIZAR, "total_extincao_reajuizar_recurso_LA", "percent_extincao_reajuizar_recursal_LA", "valor_causa_extincao_reajuizar_recurso_LA"),
        (DECISAO_INSTRUCAO_RETOMADA, "total_instrucao_retomada_recurso_LA", "percent_instrucao_retomada_recursal_LA", "valor_causa_instrucao_retomada_recurso_LA"),
    ]
    for tipo, campo_total, campo_percent, campo_valor in _tipos:
        stats.update(_item(tipo, campo_total, campo_percent, campo_valor))
    return stats


# v1: dashboard_routes.py:10348
def _build_recursal_NG_stats(
    all_recursal: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    atividades_catalogo: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder do domínio Fase Recursal NG — três métricas independentes:

    - ``total_recursal_NG``: estoque (``ID_FASE`` = 8), sem filtro de data
    - ``entrada_recursal_NG``: fase 8 com ``DT_ENTRADA_RECURSAL`` no período

    ``atividades_catalogo`` é o catálogo dinâmico de atividades do setor RECURSOS (NG)
    (query ``atividades_setor_recursos_NG``, cacheada); atualiza a whitelist usada por
    ``recurso_NG`` antes de qualquer cálculo desta função.
    """
    set_atividades_recursos_NG_catalogo(atividades_catalogo or [])
    stats = {
        "total_recursal_NG": get_total_recurso_NG(all_recursal),
        "entrada_recursal_NG": get_entrada_recurso_NG(
            all_recursal,
            from_date=from_date,
            to_date=to_date,
        ),
        "valor_causa_acordo_recursal_NG": get_valor_causa_acordo_recurso_NG(all_recursal),
        "total_sentenca_favoravel_recurso_NG": get_total_sentenca_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_desfavoravel_recurso_NG": get_total_sentenca_desfavoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_procedente_1g_recurso_NG": get_total_procedente_1g_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_parcialmente_procedente_recurso_NG": get_total_parcialmente_procedente_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_extincao_recurso_NG": get_total_sentenca_extincao_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_parcialmente_favoravel_recurso_NG": (
            get_total_sentenca_parcialmente_favoravel_recurso_NG(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ),
        "valor_causa_sentenca_favoravel_recurso_NG": get_valor_causa_sentenca_sentenca_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_desfavoravel_recurso_NG": get_valor_causa_sentenca_sentenca_desfavoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_procedente_1g_recurso_NG": get_valor_causa_sentenca_procedente_1g_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_parcialmente_procedente_recurso_NG": get_valor_causa_sentenca_parcialmente_procedente_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_extincao_recurso_NG": get_valor_causa_sentenca_sentenca_extincao_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_parcialmente_favoravel_recurso_NG": get_valor_causa_sentenca_parcialmente_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_desfavoravel_recurso_NG": get_total_acordao_desfavoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_favoravel_recurso_NG": get_total_acordao_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_parcialmente_favoravel_recurso_NG": get_total_acordao_parcialmente_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_parcial_retomada_recurso_NG": get_total_acordao_parcial_retomada_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_extincao_recurso_NG": get_total_acordao_extincao_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_desfavoravel_recurso_NG": get_valor_causa_acordao_desfavoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_favoravel_recurso_NG": get_valor_causa_acordao_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_parcialmente_favoravel_recurso_NG": get_valor_causa_acordao_parcialmente_favoravel_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_parcial_retomada_recurso_NG": get_valor_causa_acordao_parcial_retomada_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_extincao_recurso_NG": get_valor_causa_acordao_extincao_recurso_NG(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        **_build_decisoes_recursal_NG_stats(all_recursal, from_date, to_date),
    }
    agendamentos_base = agendamentos or []
    agendamentos_filtrados = filtrar_agendamentos_recursos_NG(
        agendamentos_base,
        atividades_recursos_filtros,
        from_date=from_date,
        to_date=to_date,
    )
    stats.update(
        get_kpis_atividades_recursos_NG(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        )
    )
    stats.update(
        get_kpis_atividades_recursos_por_prazo_NG(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        )
    )
    stats["avr_retorno_recurso_cancelado_NG"] = get_total_avr_retorno_recurso_cancelado_NG(
        agendamentos_filtrados, from_date=from_date, to_date=to_date
    )
    stats["retorno_cr_recurso_cancelado_NG"] = get_total_retorno_cr_recurso_cancelado_NG(
        agendamentos_filtrados, from_date=from_date, to_date=to_date
    )
    stats["provimento_mensal_qtd_NG"] = get_total_provimento_mensal_NG(
        all_recursal, from_date=from_date, to_date=to_date
    )
    stats["provimento_mensal_meta_NG"] = META_PROVIMENTO_MENSAL_NG
    funcionarios_producao_recursal_ng, por_dia_por_func_producao_recursal_ng = _per_func_to_chart(
        get_recursal_resolvidos_por_dia_por_funcionario_NG(agendamentos_filtrados)
    )
    charts = {
        "recursal_por_subfase_NG": [
            ChartDataPoint(**x)
            for x in group_recursal_por_subfase_NG(all_recursal)
        ],
        "recursal_por_status_1g_NG": [
            ChartDataPoint(**x)
            for x in group_recursal_por_status_1g_NG(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_por_status_2g_NG": [
            ChartDataPoint(**x)
            for x in group_recursal_por_status_2g_NG(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_decisoes_NG": [
            ChartDataPoint(**x)
            for x in group_decisoes_recursal_NG(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "ranking_juizes_recursal_NG": [
            RecursalRankingMagistradoRow(**x)
            for x in get_ranking_juizes_recursal_NG(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "ranking_relatores_recursal_NG": [
            RecursalRankingMagistradoRow(**x)
            for x in get_ranking_relatores_recursal_NG(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_processos_por_atividade_NG": [
            ChartDataPoint(**x)
            for x in group_recursal_processos_por_atividade_NG(
                agendamentos_filtrados,
                from_date=from_date,
                to_date=to_date,
            )
        ],
        "recursal_demandas_por_funcionario_NG": group_recursal_demandas_por_funcionario_NG(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        ),
        "recursal_resolvidos_por_dia_NG": [
            ChartDataPoint(**x)
            for x in group_recursal_resolvidos_por_dia_NG(agendamentos_filtrados)
        ],
        "recursal_resolvidos_por_mes_NG": [
            ChartDataPoint(**x)
            for x in group_recursal_resolvidos_por_mes_NG(agendamentos_filtrados)
        ],
        "funcionarios_recursal_NG": funcionarios_producao_recursal_ng,
        "recursal_resolvidos_por_dia_por_funcionario_NG": {
            k: [ChartDataPoint(**i) for i in v]
            for k, v in por_dia_por_func_producao_recursal_ng.items()
        },
        "recursal_media_resolvidos_por_funcionario_NG": [
            ChartDataPoint(**x)
            for x in get_media_recursal_resolvidos_por_funcionario_NG(
                agendamentos_filtrados, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_atividades_lista_NG": [
            RecursalAtividadeTarefaRow(**x)
            for x in list_recursal_atividades_periodo_NG(
                agendamentos_filtrados,
                from_date=from_date,
                to_date=to_date,
            )
        ],
        "recursal_atividades_lista_filtros_opcoes_NG": RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_atividades_lista_NG(
                agendamentos_base,
                from_date=from_date,
                to_date=to_date,
            )
        ),
    }
    return stats, charts


# v1: dashboard_routes.py:10565
def _build_decisoes_recursal_NG_stats(
    all_recursal: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Dict[str, Any]:
    """Stats de decisões recursais (cruzamento 1G × 2G, filtro por ``DATA_ACORDAO``)."""
    resumo = get_decisoes_recursal_resumo_NG(all_recursal, from_date=from_date, to_date=to_date)
    por_tipo = {str(item["tipo"]): item for item in resumo.get("itens", [])}

    def _item(tipo: str, campo_total: str, campo_percent: str, campo_valor: str) -> Dict[str, Any]:
        row = por_tipo.get(tipo, {})
        return {
            campo_total: row.get("value", 0),
            campo_percent: row.get("percent", 0.0),
            campo_valor: row.get("valor_causa", 0.0),
        }

    stats: Dict[str, Any] = {"total_decisoes_recursal_NG": resumo.get("total", 0)}
    _tipos = [
        (DECISAO_MANTIDO_GANHO,     "total_mantido_ganho_recurso_NG",     "percent_mantido_ganho_recursal_NG",     "valor_causa_mantido_ganho_recurso_NG"),
        (DECISAO_GANHO_AMPLIADO,    "total_ganho_ampliado_recurso_NG",    "percent_ganho_ampliado_recursal_NG",    "valor_causa_ganho_ampliado_recurso_NG"),
        (DECISAO_REVERTIDO_GANHO,   "total_revertido_ganho_recurso_NG",   "percent_revertido_ganho_recursal_NG",   "valor_causa_revertido_ganho_recurso_NG"),
        (DECISAO_GANHO_REDUZIDO,    "total_ganho_reduzido_recurso_NG",    "percent_ganho_reduzido_recursal_NG",    "valor_causa_ganho_reduzido_recurso_NG"),
        (DECISAO_MANTIDO_PERDA,     "total_mantido_perda_recurso_NG",     "percent_mantido_perda_recursal_NG",     "valor_causa_mantido_perda_recurso_NG"),
        (DECISAO_REVERTIDO_PERDA,   "total_revertido_perda_recurso_NG",   "percent_revertido_perda_recursal_NG",   "valor_causa_revertido_perda_recurso_NG"),
        (DECISAO_EXTINCAO_REAJUIZAR, "total_extincao_reajuizar_recurso_NG", "percent_extincao_reajuizar_recursal_NG", "valor_causa_extincao_reajuizar_recurso_NG"),
        (DECISAO_INSTRUCAO_RETOMADA, "total_instrucao_retomada_recurso_NG", "percent_instrucao_retomada_recursal_NG", "valor_causa_instrucao_retomada_recurso_NG"),
    ]
    for tipo, campo_total, campo_percent, campo_valor in _tipos:
        stats.update(_item(tipo, campo_total, campo_percent, campo_valor))
    return stats


# v1: dashboard_routes.py:10598
def _build_recursal_RJ_stats(
    all_recursal: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    agendamentos: Optional[List[Dict]] = None,
    atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    atividades_catalogo: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    """
    Builder do domínio Fase Recursal RJ — três métricas independentes:

    - ``total_recursal_RJ``: estoque (``ID_FASE`` = 8), sem filtro de data
    - ``entrada_recursal_RJ``: fase 8 com ``DT_ENTRADA_RECURSAL`` no período

    ``atividades_catalogo`` é o catálogo dinâmico de atividades do setor RECURSOS (RJ)
    (query ``atividades_setor_recursos_RJ``, cacheada); atualiza a whitelist usada por
    ``recurso_RJ`` antes de qualquer cálculo desta função.
    """
    set_atividades_recursos_RJ_catalogo(atividades_catalogo or [])
    stats = {
        "total_recursal_RJ": get_total_recurso_RJ(all_recursal),
        "entrada_recursal_RJ": get_entrada_recurso_RJ(
            all_recursal,
            from_date=from_date,
            to_date=to_date,
        ),
        "valor_causa_acordo_recursal_RJ": get_valor_causa_acordo_recurso_RJ(all_recursal),
        "total_sentenca_favoravel_recurso_RJ": get_total_sentenca_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_desfavoravel_recurso_RJ": get_total_sentenca_desfavoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_procedente_1g_recurso_RJ": get_total_procedente_1g_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_parcialmente_procedente_recurso_RJ": get_total_parcialmente_procedente_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_extincao_recurso_RJ": get_total_sentenca_extincao_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_sentenca_parcialmente_favoravel_recurso_RJ": (
            get_total_sentenca_parcialmente_favoravel_recurso_RJ(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ),
        "valor_causa_sentenca_favoravel_recurso_RJ": get_valor_causa_sentenca_sentenca_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_desfavoravel_recurso_RJ": get_valor_causa_sentenca_sentenca_desfavoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_procedente_1g_recurso_RJ": get_valor_causa_sentenca_procedente_1g_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_parcialmente_procedente_recurso_RJ": get_valor_causa_sentenca_parcialmente_procedente_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_extincao_recurso_RJ": get_valor_causa_sentenca_sentenca_extincao_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_sentenca_parcialmente_favoravel_recurso_RJ": get_valor_causa_sentenca_parcialmente_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_desfavoravel_recurso_RJ": get_total_acordao_desfavoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_favoravel_recurso_RJ": get_total_acordao_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_parcialmente_favoravel_recurso_RJ": get_total_acordao_parcialmente_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_parcial_retomada_recurso_RJ": get_total_acordao_parcial_retomada_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "total_acordao_extincao_recurso_RJ": get_total_acordao_extincao_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_desfavoravel_recurso_RJ": get_valor_causa_acordao_desfavoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_favoravel_recurso_RJ": get_valor_causa_acordao_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_parcialmente_favoravel_recurso_RJ": get_valor_causa_acordao_parcialmente_favoravel_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_parcial_retomada_recurso_RJ": get_valor_causa_acordao_parcial_retomada_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        "valor_causa_acordao_extincao_recurso_RJ": get_valor_causa_acordao_extincao_recurso_RJ(
            all_recursal, from_date=from_date, to_date=to_date
        ),
        **_build_decisoes_recursal_RJ_stats(all_recursal, from_date, to_date),
    }
    agendamentos_base = agendamentos or []
    agendamentos_filtrados = filtrar_agendamentos_recursos_RJ(
        agendamentos_base,
        atividades_recursos_filtros,
        from_date=from_date,
        to_date=to_date,
    )
    stats.update(
        get_kpis_atividades_recursos_RJ(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        )
    )
    stats.update(
        get_kpis_atividades_recursos_por_prazo_RJ(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        )
    )
    stats["avr_retorno_recurso_cancelado_RJ"] = get_total_avr_retorno_recurso_cancelado_RJ(
        agendamentos_filtrados, from_date=from_date, to_date=to_date
    )
    stats["retorno_cr_recurso_cancelado_RJ"] = get_total_retorno_cr_recurso_cancelado_RJ(
        agendamentos_filtrados, from_date=from_date, to_date=to_date
    )
    stats["provimento_mensal_qtd_RJ"] = get_total_provimento_mensal_RJ(
        all_recursal, from_date=from_date, to_date=to_date
    )
    stats["provimento_mensal_meta_RJ"] = META_PROVIMENTO_MENSAL_RJ
    funcionarios_producao_recursal_rj, por_dia_por_func_producao_recursal_rj = _per_func_to_chart(
        get_recursal_resolvidos_por_dia_por_funcionario_RJ(agendamentos_filtrados)
    )
    charts = {
        "recursal_por_subfase_RJ": [
            ChartDataPoint(**x)
            for x in group_recursal_por_subfase_RJ(all_recursal)
        ],
        "recursal_por_status_1g_RJ": [
            ChartDataPoint(**x)
            for x in group_recursal_por_status_1g_RJ(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_por_status_2g_RJ": [
            ChartDataPoint(**x)
            for x in group_recursal_por_status_2g_RJ(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_decisoes_RJ": [
            ChartDataPoint(**x)
            for x in group_decisoes_recursal_RJ(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "ranking_juizes_recursal_RJ": [
            RecursalRankingMagistradoRow(**x)
            for x in get_ranking_juizes_recursal_RJ(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "ranking_relatores_recursal_RJ": [
            RecursalRankingMagistradoRow(**x)
            for x in get_ranking_relatores_recursal_RJ(
                all_recursal, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_processos_por_atividade_RJ": [
            ChartDataPoint(**x)
            for x in group_recursal_processos_por_atividade_RJ(
                agendamentos_filtrados,
                from_date=from_date,
                to_date=to_date,
            )
        ],
        "recursal_demandas_por_funcionario_RJ": group_recursal_demandas_por_funcionario_RJ(
            agendamentos_filtrados,
            from_date=from_date,
            to_date=to_date,
        ),
        "recursal_resolvidos_por_dia_RJ": [
            ChartDataPoint(**x)
            for x in group_recursal_resolvidos_por_dia_RJ(agendamentos_filtrados)
        ],
        "recursal_resolvidos_por_mes_RJ": [
            ChartDataPoint(**x)
            for x in group_recursal_resolvidos_por_mes_RJ(agendamentos_filtrados)
        ],
        "funcionarios_recursal_RJ": funcionarios_producao_recursal_rj,
        "recursal_resolvidos_por_dia_por_funcionario_RJ": {
            k: [ChartDataPoint(**i) for i in v]
            for k, v in por_dia_por_func_producao_recursal_rj.items()
        },
        "recursal_media_resolvidos_por_funcionario_RJ": [
            ChartDataPoint(**x)
            for x in get_media_recursal_resolvidos_por_funcionario_RJ(
                agendamentos_filtrados, from_date=from_date, to_date=to_date
            )
        ],
        "recursal_atividades_lista_RJ": [
            RecursalAtividadeTarefaRow(**x)
            for x in list_recursal_atividades_periodo_RJ(
                agendamentos_filtrados,
                from_date=from_date,
                to_date=to_date,
            )
        ],
        "recursal_atividades_lista_filtros_opcoes_RJ": RecursalAtividadesListaFiltrosOpcoes(
            **get_opcoes_filtros_atividades_lista_RJ(
                agendamentos_base,
                from_date=from_date,
                to_date=to_date,
            )
        ),
    }
    return stats, charts


# v1: dashboard_routes.py:10815
def _build_decisoes_recursal_RJ_stats(
    all_recursal: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Dict[str, Any]:
    """Stats de decisões recursais (cruzamento 1G × 2G, filtro por ``DATA_ACORDAO``)."""
    resumo = get_decisoes_recursal_resumo_RJ(all_recursal, from_date=from_date, to_date=to_date)
    por_tipo = {str(item["tipo"]): item for item in resumo.get("itens", [])}

    def _item(tipo: str, campo_total: str, campo_percent: str, campo_valor: str) -> Dict[str, Any]:
        row = por_tipo.get(tipo, {})
        return {
            campo_total: row.get("value", 0),
            campo_percent: row.get("percent", 0.0),
            campo_valor: row.get("valor_causa", 0.0),
        }

    stats: Dict[str, Any] = {"total_decisoes_recursal_RJ": resumo.get("total", 0)}
    _tipos = [
        (DECISAO_MANTIDO_GANHO,     "total_mantido_ganho_recurso_RJ",     "percent_mantido_ganho_recursal_RJ",     "valor_causa_mantido_ganho_recurso_RJ"),
        (DECISAO_GANHO_AMPLIADO,    "total_ganho_ampliado_recurso_RJ",    "percent_ganho_ampliado_recursal_RJ",    "valor_causa_ganho_ampliado_recurso_RJ"),
        (DECISAO_REVERTIDO_GANHO,   "total_revertido_ganho_recurso_RJ",   "percent_revertido_ganho_recursal_RJ",   "valor_causa_revertido_ganho_recurso_RJ"),
        (DECISAO_GANHO_REDUZIDO,    "total_ganho_reduzido_recurso_RJ",    "percent_ganho_reduzido_recursal_RJ",    "valor_causa_ganho_reduzido_recurso_RJ"),
        (DECISAO_MANTIDO_PERDA,     "total_mantido_perda_recurso_RJ",     "percent_mantido_perda_recursal_RJ",     "valor_causa_mantido_perda_recurso_RJ"),
        (DECISAO_REVERTIDO_PERDA,   "total_revertido_perda_recurso_RJ",   "percent_revertido_perda_recursal_RJ",   "valor_causa_revertido_perda_recurso_RJ"),
        (DECISAO_EXTINCAO_REAJUIZAR, "total_extincao_reajuizar_recurso_RJ", "percent_extincao_reajuizar_recursal_RJ", "valor_causa_extincao_reajuizar_recurso_RJ"),
        (DECISAO_INSTRUCAO_RETOMADA, "total_instrucao_retomada_recurso_RJ", "percent_instrucao_retomada_recursal_RJ", "valor_causa_instrucao_retomada_recurso_RJ"),
    ]
    for tipo, campo_total, campo_percent, campo_valor in _tipos:
        stats.update(_item(tipo, campo_total, campo_percent, campo_valor))
    return stats


# v1: dashboard_routes.py:11078
def _build_publicacoes_LA_stats(
    publicacoes: List[Dict],
    agendamentos: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    dia_ref = resolve_dia_referencia_fim_periodo_LA(from_date, to_date)
    hoje = date.today()
    pub_recebidas_periodo = filter_publicacoes_recebidas_no_periodo_LA(publicacoes, from_date, to_date)
    pub_tratadas_periodo = filter_publicacoes_tratadas_no_periodo_LA(publicacoes, from_date, to_date)
    com_agendamento, sem_agendamento, agendamento_por_atividade, agendamento_por_setor = (
        build_publicacoes_agendamento_apos_finalizacao_LA(publicacoes, agendamentos, from_date, to_date)
    )

    stats = {
        "publicacoes_recebidas_periodo_LA": get_publicacoes_recebidas_periodo_LA(publicacoes, from_date, to_date),
        "publicacoes_tratadas_periodo_LA": get_publicacoes_tratadas_periodo_LA(publicacoes, from_date, to_date),
        "publicacoes_pendentes_LA": get_publicacoes_pendentes_LA(publicacoes),
        "media_tempo_tratamento_publicacoes_LA": get_media_tempo_tratamento_publicacoes_LA(publicacoes, from_date, to_date),
        "publicacoes_com_data_disponibilizacao_LA": get_publicacoes_com_data_disponibilizacao_LA(publicacoes),
        "publicacoes_cumpridas_mesmo_dia_chegada_LA": get_publicacoes_cumpridas_mesmo_dia_chegada_LA(publicacoes),
        "pct_tratadas_mesmo_dia_publicacoes_LA": get_pct_tratadas_mesmo_dia_publicacoes_LA(publicacoes, dia_ref),
        "dia_referencia_publicacoes_LA": dia_ref.isoformat(),
        "publicacoes_tratadas_ultimo_dia_LA": get_publicacoes_tratadas_no_dia_LA(publicacoes, dia_ref),
        "publicacoes_recebidas_dia_referencia_LA": get_publicacoes_recebidas_no_dia_LA(publicacoes, dia_ref),
        "publicacoes_cumpridas_mesmo_dia_dia_referencia_LA": get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_LA(publicacoes, dia_ref),
        "publicacoes_recebidas_hoje_LA": get_publicacoes_recebidas_no_dia_LA(publicacoes, hoje),
        "publicacoes_com_agendamento_apos_finalizacao_LA": com_agendamento,
        "publicacoes_sem_agendamento_apos_finalizacao_LA": sem_agendamento,
        "publicacoes_pendentes_zeradas_no_periodo_LA": get_publicacoes_pendentes_zeradas_no_periodo_LA(publicacoes, from_date, to_date),
    }
    charts = {
        "publicacoes_recebidas_por_dia_LA": [ChartDataPoint(**x) for x in group_publicacoes_recebidas_por_dia_LA(publicacoes, from_date, to_date)],
        "publicacoes_tratadas_por_dia_LA": [ChartDataPoint(**x) for x in group_publicacoes_tratadas_por_dia_LA(publicacoes, from_date, to_date)],
        "publicacoes_por_tribunal_LA": [ChartDataPoint(**x) for x in group_publicacoes_por_tribunal_LA(pub_recebidas_periodo)],
        "publicacoes_por_tipo_documento_LA": [ChartDataPoint(**x) for x in group_publicacoes_por_tipo_documento_LA(pub_recebidas_periodo)],
        "publicacoes_por_materia_LA": [ChartDataPoint(**x) for x in group_publicacoes_por_materia_LA(pub_recebidas_periodo)],
        "publicacoes_por_orgao_LA": [ChartDataPoint(**x) for x in group_publicacoes_por_orgao_LA(pub_recebidas_periodo)],
        "publicacoes_por_comarca_LA": [ChartDataPoint(**x) for x in group_publicacoes_por_comarca_LA(pub_recebidas_periodo)],
        "publicacoes_cumprido_por_leitor_LA": [ChartDataPoint(**x) for x in group_publicacoes_cumprido_por_leitor_LA(pub_tratadas_periodo)],
        "publicacoes_pendentes_por_leitor_LA": [ChartDataPoint(**x) for x in group_publicacoes_pendentes_por_leitor_LA(publicacoes)],
        "publicacoes_pendentes_por_dias_atraso_LA": [ChartDataPoint(**x) for x in group_publicacoes_pendentes_por_dias_atraso_LA(publicacoes, data_referencia=dia_ref, modo_atraso="ate_referencia")],
        "publicacoes_agendamento_apos_finalizacao_por_atividade_LA": [ChartDataPoint(**x) for x in agendamento_por_atividade],
        "publicacoes_agendamento_apos_finalizacao_por_setor_LA": [ChartDataPoint(**x) for x in agendamento_por_setor],
        "publicacoes_lista_LA": [RecursalAtividadeTarefaRow(**x) for x in list_publicacoes_LA(pub_recebidas_periodo)],
        "comissionamento_publicacoes_LA_por_funcionario": [
            ComissionamentoPublicacaoRow(**x)
            for x in get_publicacoes_comissionamento_por_funcionario_LA(publicacoes, agendamentos, from_date, to_date)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:11131
def _build_publicacoes_NG_stats(
    publicacoes: List[Dict],
    agendamentos: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    dia_ref = resolve_dia_referencia_fim_periodo_NG(from_date, to_date)
    hoje = date.today()
    pub_recebidas_periodo = filter_publicacoes_recebidas_no_periodo_NG(publicacoes, from_date, to_date)
    pub_tratadas_periodo = filter_publicacoes_tratadas_no_periodo_NG(publicacoes, from_date, to_date)
    com_agendamento, sem_agendamento, agendamento_por_atividade, agendamento_por_setor = (
        build_publicacoes_agendamento_apos_finalizacao_NG(publicacoes, agendamentos, from_date, to_date)
    )

    stats = {
        "publicacoes_recebidas_periodo_NG": get_publicacoes_recebidas_periodo_NG(publicacoes, from_date, to_date),
        "publicacoes_tratadas_periodo_NG": get_publicacoes_tratadas_periodo_NG(publicacoes, from_date, to_date),
        "publicacoes_pendentes_NG": get_publicacoes_pendentes_NG(publicacoes),
        "media_tempo_tratamento_publicacoes_NG": get_media_tempo_tratamento_publicacoes_NG(publicacoes, from_date, to_date),
        "publicacoes_com_data_disponibilizacao_NG": get_publicacoes_com_data_disponibilizacao_NG(publicacoes),
        "publicacoes_cumpridas_mesmo_dia_chegada_NG": get_publicacoes_cumpridas_mesmo_dia_chegada_NG(publicacoes),
        "pct_tratadas_mesmo_dia_publicacoes_NG": get_pct_tratadas_mesmo_dia_publicacoes_NG(publicacoes, dia_ref),
        "dia_referencia_publicacoes_NG": dia_ref.isoformat(),
        "publicacoes_tratadas_ultimo_dia_NG": get_publicacoes_tratadas_no_dia_NG(publicacoes, dia_ref),
        "publicacoes_recebidas_dia_referencia_NG": get_publicacoes_recebidas_no_dia_NG(publicacoes, dia_ref),
        "publicacoes_cumpridas_mesmo_dia_dia_referencia_NG": get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_NG(publicacoes, dia_ref),
        "publicacoes_recebidas_hoje_NG": get_publicacoes_recebidas_no_dia_NG(publicacoes, hoje),
        "publicacoes_com_agendamento_apos_finalizacao_NG": com_agendamento,
        "publicacoes_sem_agendamento_apos_finalizacao_NG": sem_agendamento,
        "publicacoes_pendentes_zeradas_no_periodo_NG": get_publicacoes_pendentes_zeradas_no_periodo_NG(publicacoes, from_date, to_date),
    }
    charts = {
        "publicacoes_recebidas_por_dia_NG": [ChartDataPoint(**x) for x in group_publicacoes_recebidas_por_dia_NG(publicacoes, from_date, to_date)],
        "publicacoes_tratadas_por_dia_NG": [ChartDataPoint(**x) for x in group_publicacoes_tratadas_por_dia_NG(publicacoes, from_date, to_date)],
        "publicacoes_visualizadas_por_dia_NG": [ChartDataPoint(**x) for x in group_publicacoes_visualizadas_por_dia_NG(publicacoes, from_date, to_date)],
        "publicacoes_por_tribunal_NG": [ChartDataPoint(**x) for x in group_publicacoes_por_tribunal_NG(pub_recebidas_periodo)],
        "publicacoes_por_tipo_documento_NG": [ChartDataPoint(**x) for x in group_publicacoes_por_tipo_documento_NG(pub_recebidas_periodo)],
        "publicacoes_por_materia_NG": [ChartDataPoint(**x) for x in group_publicacoes_por_materia_NG(pub_recebidas_periodo)],
        "publicacoes_por_orgao_NG": [ChartDataPoint(**x) for x in group_publicacoes_por_orgao_NG(pub_recebidas_periodo)],
        "publicacoes_por_comarca_NG": [ChartDataPoint(**x) for x in group_publicacoes_por_comarca_NG(pub_recebidas_periodo)],
        "publicacoes_cumprido_por_leitor_NG": [ChartDataPoint(**x) for x in group_publicacoes_cumprido_por_leitor_NG(pub_tratadas_periodo)],
        "publicacoes_pendentes_por_leitor_NG": [ChartDataPoint(**x) for x in group_publicacoes_pendentes_por_leitor_NG(publicacoes)],
        "publicacoes_pendentes_por_dias_atraso_NG": [ChartDataPoint(**x) for x in group_publicacoes_pendentes_por_dias_atraso_NG(publicacoes, data_referencia=dia_ref, modo_atraso="ate_referencia")],
        "publicacoes_agendamento_apos_finalizacao_por_atividade_NG": [ChartDataPoint(**x) for x in agendamento_por_atividade],
        "publicacoes_agendamento_apos_finalizacao_por_setor_NG": [ChartDataPoint(**x) for x in agendamento_por_setor],
        "publicacoes_lista_NG": [RecursalAtividadeTarefaRow(**x) for x in list_publicacoes_NG(pub_recebidas_periodo, agendamentos)],
        "comissionamento_publicacoes_NG_por_funcionario": [
            ComissionamentoPublicacaoRow(**x)
            for x in get_publicacoes_comissionamento_por_funcionario_NG(publicacoes, agendamentos, from_date, to_date)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:11185
def _build_publicacoes_RJ_stats(
    publicacoes: List[Dict],
    agendamentos: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    dia_ref = resolve_dia_referencia_fim_periodo_RJ(from_date, to_date)
    hoje = date.today()
    pub_recebidas_periodo = filter_publicacoes_recebidas_no_periodo_RJ(publicacoes, from_date, to_date)
    pub_tratadas_periodo = filter_publicacoes_tratadas_no_periodo_RJ(publicacoes, from_date, to_date)
    com_agendamento, sem_agendamento, agendamento_por_atividade, agendamento_por_setor = (
        build_publicacoes_agendamento_apos_finalizacao_RJ(publicacoes, agendamentos, from_date, to_date)
    )

    stats = {
        "publicacoes_recebidas_periodo_RJ": get_publicacoes_recebidas_periodo_RJ(publicacoes, from_date, to_date),
        "publicacoes_tratadas_periodo_RJ": get_publicacoes_tratadas_periodo_RJ(publicacoes, from_date, to_date),
        "publicacoes_pendentes_RJ": get_publicacoes_pendentes_RJ(publicacoes),
        "media_tempo_tratamento_publicacoes_RJ": get_media_tempo_tratamento_publicacoes_RJ(publicacoes, from_date, to_date),
        "publicacoes_com_data_disponibilizacao_RJ": get_publicacoes_com_data_disponibilizacao_RJ(publicacoes),
        "publicacoes_cumpridas_mesmo_dia_chegada_RJ": get_publicacoes_cumpridas_mesmo_dia_chegada_RJ(publicacoes),
        "pct_tratadas_mesmo_dia_publicacoes_RJ": get_pct_tratadas_mesmo_dia_publicacoes_RJ(publicacoes, dia_ref),
        "dia_referencia_publicacoes_RJ": dia_ref.isoformat(),
        "publicacoes_tratadas_ultimo_dia_RJ": get_publicacoes_tratadas_no_dia_RJ(publicacoes, dia_ref),
        "publicacoes_recebidas_dia_referencia_RJ": get_publicacoes_recebidas_no_dia_RJ(publicacoes, dia_ref),
        "publicacoes_cumpridas_mesmo_dia_dia_referencia_RJ": get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_RJ(publicacoes, dia_ref),
        "publicacoes_recebidas_hoje_RJ": get_publicacoes_recebidas_no_dia_RJ(publicacoes, hoje),
        "publicacoes_com_agendamento_apos_finalizacao_RJ": com_agendamento,
        "publicacoes_sem_agendamento_apos_finalizacao_RJ": sem_agendamento,
        "publicacoes_pendentes_zeradas_no_periodo_RJ": get_publicacoes_pendentes_zeradas_no_periodo_RJ(publicacoes, from_date, to_date),
    }
    charts = {
        "publicacoes_recebidas_por_dia_RJ": [ChartDataPoint(**x) for x in group_publicacoes_recebidas_por_dia_RJ(publicacoes, from_date, to_date)],
        "publicacoes_tratadas_por_dia_RJ": [ChartDataPoint(**x) for x in group_publicacoes_tratadas_por_dia_RJ(publicacoes, from_date, to_date)],
        "publicacoes_visualizadas_por_dia_RJ": [ChartDataPoint(**x) for x in group_publicacoes_visualizadas_por_dia_RJ(publicacoes, from_date, to_date)],
        "publicacoes_por_tribunal_RJ": [ChartDataPoint(**x) for x in group_publicacoes_por_tribunal_RJ(pub_recebidas_periodo)],
        "publicacoes_por_tipo_documento_RJ": [ChartDataPoint(**x) for x in group_publicacoes_por_tipo_documento_RJ(pub_recebidas_periodo)],
        "publicacoes_por_materia_RJ": [ChartDataPoint(**x) for x in group_publicacoes_por_materia_RJ(pub_recebidas_periodo)],
        "publicacoes_por_orgao_RJ": [ChartDataPoint(**x) for x in group_publicacoes_por_orgao_RJ(pub_recebidas_periodo)],
        "publicacoes_por_comarca_RJ": [ChartDataPoint(**x) for x in group_publicacoes_por_comarca_RJ(pub_recebidas_periodo)],
        "publicacoes_cumprido_por_leitor_RJ": [ChartDataPoint(**x) for x in group_publicacoes_cumprido_por_leitor_RJ(pub_tratadas_periodo)],
        "publicacoes_pendentes_por_leitor_RJ": [ChartDataPoint(**x) for x in group_publicacoes_pendentes_por_leitor_RJ(publicacoes)],
        "publicacoes_pendentes_por_dias_atraso_RJ": [ChartDataPoint(**x) for x in group_publicacoes_pendentes_por_dias_atraso_RJ(publicacoes, data_referencia=dia_ref, modo_atraso="ate_referencia")],
        "publicacoes_agendamento_apos_finalizacao_por_atividade_RJ": [ChartDataPoint(**x) for x in agendamento_por_atividade],
        "publicacoes_agendamento_apos_finalizacao_por_setor_RJ": [ChartDataPoint(**x) for x in agendamento_por_setor],
        "publicacoes_lista_RJ": [RecursalAtividadeTarefaRow(**x) for x in list_publicacoes_RJ(pub_recebidas_periodo, agendamentos)],
        "comissionamento_publicacoes_RJ_por_funcionario": [
            ComissionamentoPublicacaoRow(**x)
            for x in get_publicacoes_comissionamento_por_funcionario_RJ(publicacoes, agendamentos, from_date, to_date)
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:15223
def _filtro_multi(valor: Any) -> Optional[Union[str, List[str]]]:
    """Filtro de matéria/subfase da Execução: aceita texto único ou lista (``?materia=A&materia=B``).
    Um valor → texto (comportamento antigo); dois ou mais → lista; vazio → ``None``."""
    if valor is None:
        return None
    if isinstance(valor, (list, tuple, set)):
        itens = [str(v).strip() for v in valor if v is not None and str(v).strip()]
        if not itens:
            return None
        return itens[0] if len(itens) == 1 else itens
    texto = str(valor).strip()
    return texto or None


# v1: dashboard_routes.py:20666
_CAMPOS_EXPORT_EXECUCAO_NG: Dict[str, str] = {
    "numero_processo": "NUMERO_PROCESSO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "materia": "MATERIA",
    "uf": "UF",
    "comarca": "COMARCA",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "data_distribuicao": "DATA_DISTRIBUICAO",
    "data_execucao": "DATA_EXECUCAO",
    "ultima_movimentacao": "ULTIMA_MOVIMENTACAO",
    "valor_causa": "VALOR_CAUSA",
    "dano_material": "DANO_MATERIAL",
    "dano_moral": "DANO_MORAL",
    "valor_execucao": "VALOR_EXECUCAO",
    "dano_material_execucao": "DANO_MATERIAL_EXECUCAO",
    "dano_moral_execucao": "DANO_MORAL_EXECUCAO",
    "valor_honorarios": "VALOR_HONORARIOS",
    "valor_ted": "VALOR_TED",
    "valor_multas": "VALOR_MULTAS",
    "sucumbencia_porcentagem": "SUCUMBENCIA_PORCENTAGEM",
    "valor_sucumbencia": "VALOR_SUCUMBENCIA",
    "valor_alvara": "VALOR_ALVARA",
    "valor_alvara_incontroverso": "VALOR_ALVARA_INCONTROVERSO",
    "data_transito_julgado": "DATA_TRANSITO_JULGADO",
    "data_encerramento": "DATA_ENCERRAMENTO",
    "data_expedicao_alvara": "DATA_EXPEDICAO_ALVARA",
    "data_saida": "DATA_COMPENSACAO_ALVARA",
    "valor_incontroverso": "VALOR_INCONTROVERSO",
    "data_expedicao_alvara_incontroverso": "DATA_EXPEDICAO_ALVARA_INCONTROVERSO",
    "data_compensacao_alvara_incontroverso": "DATA_COMPENSACAO_ALVARA_INCONTROVERSO",
    "valor_remanescente": "VALOR_REMANESCENTE",
    "tipo_saida_periodo": "TIPO_SAIDA_PERIODO",
    "valor_saida_periodo": "VALOR_SAIDA_PERIODO",
}


# v1: dashboard_routes.py:20703
_LABELS_EXPORT_EXECUCAO_NG: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "fase": "Fase",
    "subfase": "Subfase",
    "materia": "Matéria",
    "uf": "UF",
    "comarca": "Comarca",
    "vara": "Vara",
    "competencia": "Competência",
    "data_distribuicao": "Data de Distribuição",
    "data_execucao": "Data de Execução",
    "ultima_movimentacao": "Última Movimentação",
    "valor_causa": "Valor de Causa (R$)",
    "dano_material": "Dano Material (R$)",
    "dano_moral": "Dano Moral (R$)",
    "valor_execucao": "Valor de Execução (R$)",
    "dano_material_execucao": "Dano Material Execução (R$)",
    "dano_moral_execucao": "Dano Moral Execução (R$)",
    "valor_honorarios": "Valor de Honorários (R$)",
    "valor_ted": "Valor TED (R$)",
    "valor_multas": "Valor das Multas (R$)",
    "sucumbencia_porcentagem": "Sucumbência (%)",
    "valor_sucumbencia": "Valor da Sucumbência (R$)",
    "valor_alvara": "Valor do Alvará (R$)",
    "valor_alvara_incontroverso": "Valor do Alvará do Incontroverso (R$)",
    "data_transito_julgado": "Data de Trânsito em Julgado",
    "data_encerramento": "Data de Encerramento",
    "data_expedicao_alvara": "Data da Expedição do Alvará",
    "data_saida": "Data de Saída (Compensação do Alvará)",
    "valor_incontroverso": "Valor Incontroverso (R$)",
    "data_expedicao_alvara_incontroverso": "Data da Expedição do Alvará do Incontroverso",
    "data_compensacao_alvara_incontroverso": "Data de Compensação do Alvará do Incontroverso",
    "valor_remanescente": "Valor Remanescente (R$)",
    "tipo_saida_periodo": "Tipo de Saída no Período",
    "valor_saida_periodo": "Valor de Saída no Período (R$)",
}


# v1: dashboard_routes.py:20741
_CRITERIOS_EXPORT_EXECUCAO_NG = ("entrada", "saida", "total")


# v1: dashboard_routes.py:20744
async def _rows_execucao_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[str],
    subfase: Optional[str],
    ano_ajuizamento_execucao: Optional[str],
    criterio: str = "entrada",
    uf: Optional[List[str]] = None,
    comarca: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/execucao` (Execução NG), para exportação
    linha a linha — mesma query, sem campos adicionais e sem a seção de Atividades.

    ``criterio`` escolhe o mesmo recorte usado pelos cards de Indicadores (mesmo
    padrão do extrator de Execução de Acordos):
    - "entrada": processos com DATA_EXECUCAO no período — mesmo critério de
      `_filtrar_entrada_execucao_no_periodo`.
    - "saida": processos que saíram da Execução (foram para o Financeiro) no
      período — mesmo critério de `_filtrar_saida_no_periodo`.
    - "total": total atual em Execução (ID_FASE == 12), sem filtro de período —
      mesmo critério do card "Total em Execução" / `_filtrar_em_execucao`.

    Não pré-filtra por data via `filter_data` (que usa DATA_EXECUCAO): "saida" e
    "total" usam colunas/critério de data diferentes, e cada critério abaixo já
    aplica seu próprio recorte de data internamente.
    """
    all_rows = await fetch_execucao()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    materia_filtro = _filtro_multi(materia)
    subfase_filtro = _filtro_multi(subfase)
    ano_filtro = (
        str(ano_ajuizamento_execucao).strip()
        if ano_ajuizamento_execucao and str(ano_ajuizamento_execucao).strip()
        else None
    )
    uf_filtro = [str(u).strip().upper() for u in uf if str(u).strip()] if uf else None
    comarca_filtro = [str(c).strip() for c in comarca if str(c).strip()] if comarca else None
    rows = filter_execucao_por_comarca(
        filter_execucao_por_uf(
            filter_execucao_por_ano_ajuizamento(
                filter_execucao_por_subfase(
                    filter_execucao_por_materia(all_rows, materia_filtro),
                    subfase_filtro,
                ),
                ano_filtro,
            ),
            uf_filtro,
        ),
        comarca_filtro,
    )
    if criterio == "saida":
        recorte = filtrar_saida_execucao_export_ng(rows, from_date, to_date)
    elif criterio == "total":
        recorte = _filtrar_em_execucao_ng(rows)
    else:
        recorte = _filtrar_entrada_execucao_no_periodo_ng(rows, from_date, to_date)
    return anotar_saida_execucao_export_ng(recorte, from_date, to_date)


# v1: dashboard_routes.py:20881
_CAMPOS_EXPORT_EXECUCAO_RJ: Dict[str, str] = dict(_CAMPOS_EXPORT_EXECUCAO_NG)


# v1: dashboard_routes.py:20882
_LABELS_EXPORT_EXECUCAO_RJ: Dict[str, str] = dict(_LABELS_EXPORT_EXECUCAO_NG)


# v1: dashboard_routes.py:20883
_CRITERIOS_EXPORT_EXECUCAO_RJ = ("entrada", "saida", "total")


# v1: dashboard_routes.py:20886
async def _rows_execucao_RJ_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[str],
    subfase: Optional[str],
    ano_ajuizamento_execucao: Optional[str],
    criterio: str = "entrada",
    uf: Optional[List[str]] = None,
    comarca: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/execucao_RJ`, para exportação linha a
    linha — mesma query, sem campos adicionais e sem a seção de Atividades.
    Mesmos critérios de `_rows_execucao_filtradas` (NG)."""
    all_rows = await fetch_execucao_RJ()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    materia_filtro = _filtro_multi(materia)
    subfase_filtro = _filtro_multi(subfase)
    ano_filtro = (
        str(ano_ajuizamento_execucao).strip()
        if ano_ajuizamento_execucao and str(ano_ajuizamento_execucao).strip()
        else None
    )
    uf_filtro = [str(u).strip().upper() for u in uf if str(u).strip()] if uf else None
    comarca_filtro = [str(c).strip() for c in comarca if str(c).strip()] if comarca else None
    rows = filter_execucao_RJ_por_comarca(
        filter_execucao_RJ_por_uf(
            filter_execucao_RJ_por_ano_ajuizamento(
                filter_execucao_RJ_por_subfase(
                    filter_execucao_RJ_por_materia(all_rows, materia_filtro),
                    subfase_filtro,
                ),
                ano_filtro,
            ),
            uf_filtro,
        ),
        comarca_filtro,
    )
    if criterio == "saida":
        recorte = filtrar_saida_execucao_export_RJ(rows, from_date, to_date)
    elif criterio == "total":
        recorte = _filtrar_em_execucao_rj(rows)
    else:
        recorte = _filtrar_entrada_execucao_no_periodo_rj(rows, from_date, to_date)
    return anotar_saida_execucao_export_RJ(recorte, from_date, to_date)


# v1: dashboard_routes.py:21006
_CAMPOS_EXPORT_EXECUCAO_ACORDOS_NG: Dict[str, str] = {
    "numero_processo": "NUMERO_PROCESSO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "materia": "MATERIA",
    "uf": "UF",
    "comarca": "COMARCA",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "data_acordo_fechado": "DATA_ACORDO_FECHADO",
    "data_acordo_homologado": "DATA_ACORDO_HOMOLOGADO",
    "data_pagamento_acordo": "DATA_PAGAMENTO_ACORDO",
    "data_expedicao_alvara_acordo": "DATA_EXPEDICAO_ALVARA_ACORDO",
    "data_distribuicao": "DATA_DISTRIBUICAO",
    "data_execucao": "DATA_EXECUCAO",
    "ultima_movimentacao": "ULTIMA_MOVIMENTACAO",
    "valor_alcada_final": "VALOR_ALCADA_FINAL",
    "valor_proposta_recebida": "VALOR_PROPOSTA_RECEBIDA",
    "valor_contraproposta": "VALOR_CONTRAPROPOSTA",
    "valor_alvara": "VALOR_ALVARA",
}


# v1: dashboard_routes.py:21028
_LABELS_EXPORT_EXECUCAO_ACORDOS_NG: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "fase": "Fase",
    "subfase": "Subfase",
    "materia": "Matéria",
    "uf": "UF",
    "comarca": "Comarca",
    "vara": "Vara",
    "competencia": "Competência",
    "data_acordo_fechado": "Data de Acordo Fechado",
    "data_acordo_homologado": "Data de Acordo Homologado",
    "data_pagamento_acordo": "Data de Pagamento do Acordo",
    "data_expedicao_alvara_acordo": "Data da Expedição do Alvará de Acordo",
    "data_distribuicao": "Data de Distribuição",
    "data_execucao": "Data de Execução",
    "ultima_movimentacao": "Última Movimentação",
    "valor_alcada_final": "Valor de Alçada Final (R$)",
    "valor_proposta_recebida": "Valor de Proposta Recebida (R$)",
    "valor_contraproposta": "Valor de Contraproposta (R$)",
    "valor_alvara": "Valor do Alvará (R$)",
}


# v1: dashboard_routes.py:21051
_CRITERIOS_EXPORT_EXECUCAO_ACORDOS_NG = ("entrada", "saida", "total")


# v1: dashboard_routes.py:21054
_CAMPOS_EXPORT_EXECUCAO_ACORDOS_LA: Dict[str, str] = {
    "numero_processo": "NUMERO_PROCESSO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "materia": "MATERIA",
    "uf": "UF",
    "comarca": "COMARCA",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "data_acordo_fechado": "DATA_ACORDO_FECHADO",
    "data_acordo_homologado": "DATA_ACORDO_HOMOLOGADO",
    "data_pagamento_acordo": "DATA_PAGAMENTO_ACORDO",
    "data_expedicao_alvara_acordo": "DATA_EXPEDICAO_ALVARA_ACORDO",
    "data_distribuicao": "DATA_DISTRIBUICAO",
    "data_execucao": "DATA_EXECUCAO",
    "ultima_movimentacao": "ULTIMA_MOVIMENTACAO",
    "valor_alcada_final": "VALOR_ALCADA_FINAL",
    "valor_proposta_recebida": "VALOR_PROPOSTA_RECEBIDA",
    "valor_contraproposta": "VALOR_CONTRAPROPOSTA",
    "valor_alvara": "VALOR_ALVARA",
}


# v1: dashboard_routes.py:21076
_LABELS_EXPORT_EXECUCAO_ACORDOS_LA: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "fase": "Fase",
    "subfase": "Subfase",
    "materia": "Matéria",
    "uf": "UF",
    "comarca": "Comarca",
    "vara": "Vara",
    "competencia": "Competência",
    "data_acordo_fechado": "Data de Acordo Fechado",
    "data_acordo_homologado": "Data de Acordo Homologado",
    "data_pagamento_acordo": "Data de Pagamento do Acordo",
    "data_expedicao_alvara_acordo": "Data da Expedição do Alvará de Acordo",
    "data_distribuicao": "Data de Distribuição",
    "data_execucao": "Data de Execução",
    "ultima_movimentacao": "Última Movimentação",
    "valor_alcada_final": "Valor de Alçada Final (R$)",
    "valor_proposta_recebida": "Valor de Proposta Recebida (R$)",
    "valor_contraproposta": "Valor de Contraproposta (R$)",
    "valor_alvara": "Valor do Alvará (R$)",
}


# v1: dashboard_routes.py:21099
_CRITERIOS_EXPORT_EXECUCAO_ACORDOS_LA = ("entrada", "saida", "total")


# v1: dashboard_routes.py:21101
_CAMPOS_EXPORT_EXECUCAO_ACORDOS_RJ: Dict[str, str] = {
    "numero_processo": "NUMERO_PROCESSO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "materia": "MATERIA",
    "uf": "UF",
    "comarca": "COMARCA",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "data_acordo_fechado": "DATA_ACORDO_FECHADO",
    "data_acordo_homologado": "DATA_ACORDO_HOMOLOGADO",
    "data_pagamento_acordo": "DATA_PAGAMENTO_ACORDO",
    "data_expedicao_alvara_acordo": "DATA_EXPEDICAO_ALVARA_ACORDO",
    "data_distribuicao": "DATA_DISTRIBUICAO",
    "data_execucao": "DATA_EXECUCAO",
    "ultima_movimentacao": "ULTIMA_MOVIMENTACAO",
    "valor_alcada_final": "VALOR_ALCADA_FINAL",
    "valor_proposta_recebida": "VALOR_PROPOSTA_RECEBIDA",
    "valor_contraproposta": "VALOR_CONTRAPROPOSTA",
    "valor_alvara": "VALOR_ALVARA",
}


# v1: dashboard_routes.py:21123
_LABELS_EXPORT_EXECUCAO_ACORDOS_RJ: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "fase": "Fase",
    "subfase": "Subfase",
    "materia": "Matéria",
    "uf": "UF",
    "comarca": "Comarca",
    "vara": "Vara",
    "competencia": "Competência",
    "data_acordo_fechado": "Data de Acordo Fechado",
    "data_acordo_homologado": "Data de Acordo Homologado",
    "data_pagamento_acordo": "Data de Pagamento do Acordo",
    "data_expedicao_alvara_acordo": "Data da Expedição do Alvará de Acordo",
    "data_distribuicao": "Data de Distribuição",
    "data_execucao": "Data de Execução",
    "ultima_movimentacao": "Última Movimentação",
    "valor_alcada_final": "Valor de Alçada Final (R$)",
    "valor_proposta_recebida": "Valor de Proposta Recebida (R$)",
    "valor_contraproposta": "Valor de Contraproposta (R$)",
    "valor_alvara": "Valor do Alvará (R$)",
}


# v1: dashboard_routes.py:21146
_CRITERIOS_EXPORT_EXECUCAO_ACORDOS_RJ = ("entrada", "saida", "total")


# v1: dashboard_routes.py:21149
async def _rows_execucao_acordos_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[str],
    subfase: Optional[str],
    tipo_acao_execucao_acordos: Optional[str],
    uf: Optional[List[str]],
    criterio: str = "entrada",
    comarca: Optional[List[str]] = None,
    ano_ajuizamento_execucao_acordos: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/execucao_acordos_NG`, para exportação
    linha a linha — mesma query, sem campos adicionados e sem a seção de
    Atividades.

    ``criterio`` escolhe o mesmo recorte usado pela seção "Execuções de
    Acordo" (tabela) e pelos cards de Indicadores:
    - "entrada": acordos com entrada na execução no período (etiqueta "Acordo"
      + DATA_EXECUCAO no período) — mesmo critério de
      `list_execucao_acordos_lista_entrada`.
    - "saida": acordos pagos no período (DATA_PAGAMENTO_ACORDO no período) —
      mesmo critério de `list_execucao_acordos_lista_saida`.
    - "total": total atual em Execução de Acordos (fase ACORDO, sem filtro de
      período) — mesmo critério de `list_execucao_acordos_lista_total` e do
      card "Total em Execução de Acordos".

    Não pré-filtra por data via `filter_data`/`_FILTER_COLUMNS` (que usa
    DATA_EXECUCAO): "saida" e "total" usam colunas/critério de data
    diferentes, e cada filtro de critério abaixo já aplica seu próprio recorte
    de data internamente.
    """
    all_rows = await fetch_execucao_acordos_NG()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    materia_filtro = _filtro_multi(materia)
    subfase_filtro = _filtro_multi(subfase)
    tipo_acao_filtro = (
        str(tipo_acao_execucao_acordos).strip()
        if tipo_acao_execucao_acordos and str(tipo_acao_execucao_acordos).strip()
        else None
    )
    uf_filtro = (
        [str(u).strip().upper() for u in uf if str(u).strip()]
        if uf
        else None
    )
    comarca_filtro = (
        [str(c).strip() for c in comarca if str(c).strip()]
        if comarca
        else None
    )
    ano_ajuizamento_filtro = (
        str(ano_ajuizamento_execucao_acordos).strip()
        if ano_ajuizamento_execucao_acordos and str(ano_ajuizamento_execucao_acordos).strip()
        else None
    )
    rows = filter_execucao_acordos_por_ano_ajuizamento(
        filter_execucao_acordos_por_comarca(
            filter_execucao_acordos_por_uf(
                filter_execucao_acordos_por_tipo_acao(
                    filter_execucao_acordos_por_subfase(
                        filter_execucao_acordos_por_materia(all_rows, materia_filtro),
                        subfase_filtro,
                    ),
                    tipo_acao_filtro,
                ),
                uf_filtro,
            ),
            comarca_filtro,
        ),
        ano_ajuizamento_filtro,
    )
    if criterio == "saida":
        return _filtrar_saida_execucao_acordos_no_periodo(rows, from_date, to_date)
    if criterio == "total":
        return _filtrar_em_execucao_acordos(rows)
    return _filtrar_entrada_execucao_acordos_no_periodo(rows, from_date, to_date)


# v1: dashboard_routes.py:21303
async def _rows_execucao_acordos_LA_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[str],
    subfase: Optional[str],
    tipo_acao_execucao_acordos: Optional[str],
    uf: Optional[List[str]],
    criterio: str = "entrada",
    comarca: Optional[List[str]] = None,
    ano_ajuizamento_execucao_acordos: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/execucao_acordos_LA`, para exportação
    linha a linha — mesma query, sem campos adicionados e sem a seção de
    Atividades.

    ``criterio`` escolhe o mesmo recorte usado pela seção "Execuções de
    Acordo" (tabela) e pelos cards de Indicadores:
    - "entrada": acordos com entrada na execução no período (etiqueta "Acordo"
      + DATA_EXECUCAO no período) — mesmo critério de
      `list_execucao_acordos_LA_lista_entrada`.
    - "saida": acordos pagos no período (DATA_PAGAMENTO_ACORDO no período) —
      mesmo critério de `list_execucao_acordos_LA_lista_saida`.
    - "total": total atual em Execução de Acordos (fase ACORDO, sem filtro de
      período) — mesmo critério de `list_execucao_acordos_LA_lista_total` e do
      card "Total em Execução de Acordos".

    Não pré-filtra por data via `filter_data`/`_FILTER_COLUMNS` (que usa
    DATA_EXECUCAO): "saida" e "total" usam colunas/critério de data
    diferentes, e cada filtro de critério abaixo já aplica seu próprio recorte
    de data internamente.
    """
    all_rows = await fetch_execucao_acordos_LA()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    materia_filtro = _filtro_multi(materia)
    subfase_filtro = _filtro_multi(subfase)
    tipo_acao_filtro = (
        str(tipo_acao_execucao_acordos).strip()
        if tipo_acao_execucao_acordos and str(tipo_acao_execucao_acordos).strip()
        else None
    )
    uf_filtro = (
        [str(u).strip().upper() for u in uf if str(u).strip()]
        if uf
        else None
    )
    comarca_filtro = (
        [str(c).strip() for c in comarca if str(c).strip()]
        if comarca
        else None
    )
    ano_ajuizamento_filtro = (
        str(ano_ajuizamento_execucao_acordos).strip()
        if ano_ajuizamento_execucao_acordos and str(ano_ajuizamento_execucao_acordos).strip()
        else None
    )
    rows = filter_execucao_acordos_LA_por_ano_ajuizamento(
        filter_execucao_acordos_LA_por_comarca(
            filter_execucao_acordos_LA_por_uf(
                filter_execucao_acordos_LA_por_tipo_acao(
                    filter_execucao_acordos_LA_por_subfase(
                        filter_execucao_acordos_LA_por_materia(all_rows, materia_filtro),
                        subfase_filtro,
                    ),
                    tipo_acao_filtro,
                ),
                uf_filtro,
            ),
            comarca_filtro,
        ),
        ano_ajuizamento_filtro,
    )
    if criterio == "saida":
        return _filtrar_saida_execucao_acordos_LA_no_periodo(rows, from_date, to_date)
    if criterio == "total":
        return _filtrar_em_execucao_acordos_LA(rows)
    return _filtrar_entrada_execucao_acordos_LA_no_periodo(rows, from_date, to_date)


# v1: dashboard_routes.py:21457
async def _rows_execucao_acordos_RJ_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[str],
    subfase: Optional[str],
    tipo_acao_execucao_acordos: Optional[str],
    uf: Optional[List[str]],
    criterio: str = "entrada",
    comarca: Optional[List[str]] = None,
    ano_ajuizamento_execucao_acordos: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/execucao_acordos_RJ`, para exportação
    linha a linha — mesma query, sem campos adicionados e sem a seção de
    Atividades.

    ``criterio`` escolhe o mesmo recorte usado pela seção "Execuções de
    Acordo" (tabela) e pelos cards de Indicadores:
    - "entrada": acordos com entrada na execução no período (etiqueta "Acordo"
      + DATA_EXECUCAO no período) — mesmo critério de
      `list_execucao_acordos_RJ_lista_entrada`.
    - "saida": acordos pagos no período (DATA_PAGAMENTO_ACORDO no período) —
      mesmo critério de `list_execucao_acordos_RJ_lista_saida`.
    - "total": total atual em Execução de Acordos (fase ACORDO, sem filtro de
      período) — mesmo critério de `list_execucao_acordos_RJ_lista_total` e do
      card "Total em Execução de Acordos".

    Não pré-filtra por data via `filter_data`/`_FILTER_COLUMNS` (que usa
    DATA_EXECUCAO): "saida" e "total" usam colunas/critério de data
    diferentes, e cada filtro de critério abaixo já aplica seu próprio recorte
    de data internamente.
    """
    all_rows = await fetch_execucao_acordos_RJ()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    materia_filtro = _filtro_multi(materia)
    subfase_filtro = _filtro_multi(subfase)
    tipo_acao_filtro = (
        str(tipo_acao_execucao_acordos).strip()
        if tipo_acao_execucao_acordos and str(tipo_acao_execucao_acordos).strip()
        else None
    )
    uf_filtro = (
        [str(u).strip().upper() for u in uf if str(u).strip()]
        if uf
        else None
    )
    comarca_filtro = (
        [str(c).strip() for c in comarca if str(c).strip()]
        if comarca
        else None
    )
    ano_ajuizamento_filtro = (
        str(ano_ajuizamento_execucao_acordos).strip()
        if ano_ajuizamento_execucao_acordos and str(ano_ajuizamento_execucao_acordos).strip()
        else None
    )
    rows = filter_execucao_acordos_RJ_por_ano_ajuizamento(
        filter_execucao_acordos_RJ_por_comarca(
            filter_execucao_acordos_RJ_por_uf(
                filter_execucao_acordos_RJ_por_tipo_acao(
                    filter_execucao_acordos_RJ_por_subfase(
                        filter_execucao_acordos_RJ_por_materia(all_rows, materia_filtro),
                        subfase_filtro,
                    ),
                    tipo_acao_filtro,
                ),
                uf_filtro,
            ),
            comarca_filtro,
        ),
        ano_ajuizamento_filtro,
    )
    if criterio == "saida":
        return _filtrar_saida_execucao_acordos_RJ_no_periodo(rows, from_date, to_date)
    if criterio == "total":
        return _filtrar_em_execucao_acordos_RJ(rows)
    return _filtrar_entrada_execucao_acordos_RJ_no_periodo(rows, from_date, to_date)


# v1: dashboard_routes.py:21983
_CAMPOS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG: Dict[str, str] = {
    "numero_processo": "numero_processo",
    "atividade": "atividade",
    "status": "status",
    "situacao": "situacao",
    "funcionario": "funcionario",
    "funcionario_atribuido": "funcionario_atribuido",
    "funcionario_encerramento": "funcionario_encerramento",
    "prazo": "prazo",
    "criado_em": "criado_em",
    "descricao": "descricao",
    "operacao": "operacao",
}


# v1: dashboard_routes.py:21997
_LABELS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "atividade": "Atividade",
    "status": "Status",
    "situacao": "Situação",
    "funcionario": "Responsável Atual",
    "funcionario_atribuido": "Funcionário Atribuído",
    "funcionario_encerramento": "Funcionário que Encerrou",
    "prazo": "Prazo",
    "criado_em": "Criado em",
    "descricao": "Descrição",
    "operacao": "Operação",
}


# v1: dashboard_routes.py:22011
_VIEWS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG = ("concluidas", "por_prazo")


# v1: dashboard_routes.py:22013
_CAMPOS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_LA: Dict[str, str] = {
    "numero_processo": "numero_processo",
    "atividade": "atividade",
    "status": "status",
    "situacao": "situacao",
    "funcionario": "funcionario",
    "funcionario_atribuido": "funcionario_atribuido",
    "funcionario_encerramento": "funcionario_encerramento",
    "prazo": "prazo",
    "criado_em": "criado_em",
    "descricao": "descricao",
    "operacao": "operacao",
}


# v1: dashboard_routes.py:22027
_LABELS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_LA: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "atividade": "Atividade",
    "status": "Status",
    "situacao": "Situação",
    "funcionario": "Responsável Atual",
    "funcionario_atribuido": "Funcionário Atribuído",
    "funcionario_encerramento": "Funcionário que Encerrou",
    "prazo": "Prazo",
    "criado_em": "Criado em",
    "descricao": "Descrição",
    "operacao": "Operação",
}


# v1: dashboard_routes.py:22041
_VIEWS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_LA = ("concluidas", "por_prazo")


# v1: dashboard_routes.py:22043
_CAMPOS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_RJ: Dict[str, str] = {
    "numero_processo": "numero_processo",
    "atividade": "atividade",
    "status": "status",
    "situacao": "situacao",
    "funcionario": "funcionario",
    "funcionario_atribuido": "funcionario_atribuido",
    "funcionario_encerramento": "funcionario_encerramento",
    "prazo": "prazo",
    "criado_em": "criado_em",
    "descricao": "descricao",
    "operacao": "operacao",
}


# v1: dashboard_routes.py:22057
_LABELS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_RJ: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "atividade": "Atividade",
    "status": "Status",
    "situacao": "Situação",
    "funcionario": "Responsável Atual",
    "funcionario_atribuido": "Funcionário Atribuído",
    "funcionario_encerramento": "Funcionário que Encerrou",
    "prazo": "Prazo",
    "criado_em": "Criado em",
    "descricao": "Descrição",
    "operacao": "Operação",
}


# v1: dashboard_routes.py:22071
_VIEWS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_RJ = ("concluidas", "por_prazo")


# v1: dashboard_routes.py:22074
def _situacao_label_execucao_acordos_atividade(item: Dict[str, Any]) -> str:
    """Reduz os 4 flags booleanos (em_andamento/vencida/vence_hoje/concluida) de
    ``RecursalAtividadeTarefaRow`` a um único rótulo legível para a planilha."""
    if item.get("concluida"):
        return "Concluída"
    if item.get("vencida"):
        return "Vencida"
    if item.get("vence_hoje"):
        return "Vence hoje"
    if item.get("em_andamento"):
        return "Em andamento"
    return "—"


# v1: dashboard_routes.py:22088
def _mapa_agendamento_para_processo_id_acordos_ng(
    agendamentos: List[Dict[str, Any]],
) -> Dict[int, Any]:
    """A query de agendamentos só traz `processo_id` (interno) — mapeia
    agendamento_id → processo_id para juntar dados do processo (número,
    valor de alçada final) nas linhas de atividade."""
    mapa: Dict[int, Any] = {}
    for row in agendamentos:
        ag_id = row.get("id") or row.get("ID")
        pid = _get_ag_processo_id_ng(row)
        if ag_id is not None and pid is not None:
            mapa[int(ag_id)] = pid
    return mapa


# v1: dashboard_routes.py:22103
def _mapa_numero_e_valor_por_processo_id_acordos_ng(
    processos: List[Dict[str, Any]],
    processo_ids: set,
) -> Tuple[Dict[Any, str], Dict[Any, float]]:
    numero_por_id: Dict[Any, str] = {}
    valor_por_id: Dict[Any, float] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        if pid not in processo_ids:
            continue
        numero = p.get("NUMERO_PROCESSO")
        if numero:
            numero_por_id[pid] = str(numero)
        valor = p.get("VALOR_ALCADA_FINAL")
        if valor is not None:
            try:
                valor_por_id[pid] = float(valor)
            except (TypeError, ValueError):
                pass
    return numero_por_id, valor_por_id


# v1: dashboard_routes.py:22125
def _enriquecer_atividades_acordos_ng_com_dados_processo(
    itens: List[Dict[str, Any]],
    ag_filtrados: List[Dict[str, Any]],
    processos: List[Dict[str, Any]],
    *,
    incluir_numero_processo: bool = False,
) -> List[Dict[str, Any]]:
    """Junta cada linha de atividade (agendamento) com dados do processo
    associado (via `processo_id`): sempre o valor de alçada final
    (`valor_execucao`), e opcionalmente o número do processo."""
    ag_para_processo = _mapa_agendamento_para_processo_id_acordos_ng(ag_filtrados)
    processo_ids = set(ag_para_processo.values())
    numero_por_id, valor_por_id = _mapa_numero_e_valor_por_processo_id_acordos_ng(
        processos, processo_ids
    )
    for item in itens:
        ag_id = item.get("id")
        pid = ag_para_processo.get(int(ag_id)) if ag_id is not None else None
        if incluir_numero_processo:
            item["numero_processo"] = numero_por_id.get(pid) if pid is not None else None
        item["valor_execucao"] = valor_por_id.get(pid) if pid is not None else None
    return itens


# v1: dashboard_routes.py:22149
def _mapa_agendamento_para_processo_id_acordos_la(
    agendamentos: List[Dict[str, Any]],
) -> Dict[int, Any]:
    """A query de agendamentos só traz `processo_id` (interno) — mapeia
    agendamento_id → processo_id para juntar dados do processo (número,
    valor de alçada final) nas linhas de atividade."""
    mapa: Dict[int, Any] = {}
    for row in agendamentos:
        ag_id = row.get("id") or row.get("ID")
        pid = _get_ag_processo_id_ng(row)
        if ag_id is not None and pid is not None:
            mapa[int(ag_id)] = pid
    return mapa


# v1: dashboard_routes.py:22164
def _mapa_numero_e_valor_por_processo_id_acordos_la(
    processos: List[Dict[str, Any]],
    processo_ids: set,
) -> Tuple[Dict[Any, str], Dict[Any, float]]:
    numero_por_id: Dict[Any, str] = {}
    valor_por_id: Dict[Any, float] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        if pid not in processo_ids:
            continue
        numero = p.get("NUMERO_PROCESSO")
        if numero:
            numero_por_id[pid] = str(numero)
        valor = p.get("VALOR_ALCADA_FINAL")
        if valor is not None:
            try:
                valor_por_id[pid] = float(valor)
            except (TypeError, ValueError):
                pass
    return numero_por_id, valor_por_id


# v1: dashboard_routes.py:22186
def _enriquecer_atividades_acordos_la_com_dados_processo(
    itens: List[Dict[str, Any]],
    ag_filtrados: List[Dict[str, Any]],
    processos: List[Dict[str, Any]],
    *,
    incluir_numero_processo: bool = False,
) -> List[Dict[str, Any]]:
    """Junta cada linha de atividade (agendamento) com dados do processo
    associado (via `processo_id`): sempre o valor de alçada final
    (`valor_execucao`), e opcionalmente o número do processo."""
    ag_para_processo = _mapa_agendamento_para_processo_id_acordos_la(ag_filtrados)
    processo_ids = set(ag_para_processo.values())
    numero_por_id, valor_por_id = _mapa_numero_e_valor_por_processo_id_acordos_la(
        processos, processo_ids
    )
    for item in itens:
        ag_id = item.get("id")
        pid = ag_para_processo.get(int(ag_id)) if ag_id is not None else None
        if incluir_numero_processo:
            item["numero_processo"] = numero_por_id.get(pid) if pid is not None else None
        item["valor_execucao"] = valor_por_id.get(pid) if pid is not None else None
    return itens


# v1: dashboard_routes.py:22210
def _mapa_agendamento_para_processo_id_acordos_rj(
    agendamentos: List[Dict[str, Any]],
) -> Dict[int, Any]:
    """A query de agendamentos só traz `processo_id` (interno) — mapeia
    agendamento_id → processo_id para juntar dados do processo (número,
    valor de alçada final) nas linhas de atividade."""
    mapa: Dict[int, Any] = {}
    for row in agendamentos:
        ag_id = row.get("id") or row.get("ID")
        pid = _get_ag_processo_id_ng(row)
        if ag_id is not None and pid is not None:
            mapa[int(ag_id)] = pid
    return mapa


# v1: dashboard_routes.py:22225
def _mapa_numero_e_valor_por_processo_id_acordos_rj(
    processos: List[Dict[str, Any]],
    processo_ids: set,
) -> Tuple[Dict[Any, str], Dict[Any, float]]:
    numero_por_id: Dict[Any, str] = {}
    valor_por_id: Dict[Any, float] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        if pid not in processo_ids:
            continue
        numero = p.get("NUMERO_PROCESSO")
        if numero:
            numero_por_id[pid] = str(numero)
        valor = p.get("VALOR_ALCADA_FINAL")
        if valor is not None:
            try:
                valor_por_id[pid] = float(valor)
            except (TypeError, ValueError):
                pass
    return numero_por_id, valor_por_id


# v1: dashboard_routes.py:22247
def _enriquecer_atividades_acordos_rj_com_dados_processo(
    itens: List[Dict[str, Any]],
    ag_filtrados: List[Dict[str, Any]],
    processos: List[Dict[str, Any]],
    *,
    incluir_numero_processo: bool = False,
) -> List[Dict[str, Any]]:
    """Junta cada linha de atividade (agendamento) com dados do processo
    associado (via `processo_id`): sempre o valor de alçada final
    (`valor_execucao`), e opcionalmente o número do processo."""
    ag_para_processo = _mapa_agendamento_para_processo_id_acordos_rj(ag_filtrados)
    processo_ids = set(ag_para_processo.values())
    numero_por_id, valor_por_id = _mapa_numero_e_valor_por_processo_id_acordos_rj(
        processos, processo_ids
    )
    for item in itens:
        ag_id = item.get("id")
        pid = ag_para_processo.get(int(ag_id)) if ag_id is not None else None
        if incluir_numero_processo:
            item["numero_processo"] = numero_por_id.get(pid) if pid is not None else None
        item["valor_execucao"] = valor_por_id.get(pid) if pid is not None else None
    return itens


# v1: dashboard_routes.py:22271
async def _rows_execucao_acordos_atividades_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    funcionario: Optional[List[str]],
    atividade: Optional[List[str]],
    status: Optional[List[str]],
    situacao: Optional[List[str]],
    view: str,
) -> List[Dict[str, Any]]:
    """Réplica os filtros da seção Atividades do dashboard `/execucao_acordos_NG`,
    para exportação linha a linha da tabela de tarefas (agendamentos).

    ``view`` escolhe o mesmo eixo temporal do toggle "Concluídas"/"Por prazo"
    da seção: "concluidas" usa DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO; "por_prazo"
    usa PRAZO como eixo.
    """
    agendamentos = await fetch_agendamentos_setor_execucao_acordos_NG()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros = _parse_execucao_atividades_filtros(funcionario, atividade, status, situacao)
    ag_filtrados = filtrar_agendamentos_execucao_acordos_NG(
        agendamentos, filtros, from_date=from_date, to_date=to_date
    )
    if view == "por_prazo":
        itens = list_execucao_atividades_por_prazo_periodo_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
    else:
        itens = list_execucao_atividades_periodo_acordos_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )

    processos = await fetch_execucao_acordos_NG()
    itens = _enriquecer_atividades_acordos_ng_com_dados_processo(
        itens, ag_filtrados, processos, incluir_numero_processo=True
    )

    for item in itens:
        item["situacao"] = _situacao_label_execucao_acordos_atividade(item)

    return itens


# v1: dashboard_routes.py:22390
async def _rows_execucao_acordos_la_atividades_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    funcionario: Optional[List[str]],
    atividade: Optional[List[str]],
    status: Optional[List[str]],
    situacao: Optional[List[str]],
    view: str,
) -> List[Dict[str, Any]]:
    """Réplica os filtros da seção Atividades do dashboard `/execucao_acordos_LA`,
    para exportação linha a linha da tabela de tarefas (agendamentos).

    ``view`` escolhe o mesmo eixo temporal do toggle "Concluídas"/"Por prazo"
    da seção: "concluidas" usa DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO; "por_prazo"
    usa PRAZO como eixo.
    """
    agendamentos = await fetch_agendamentos_setor_execucao_acordos_LA()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros = _parse_execucao_atividades_filtros(funcionario, atividade, status, situacao)
    ag_filtrados = filtrar_agendamentos_execucao_acordos_LA(
        agendamentos, filtros, from_date=from_date, to_date=to_date
    )
    if view == "por_prazo":
        itens = list_execucao_atividades_por_prazo_periodo_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
    else:
        itens = list_execucao_atividades_periodo_acordos_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )

    processos = await fetch_execucao_acordos_LA()
    itens = _enriquecer_atividades_acordos_la_com_dados_processo(
        itens, ag_filtrados, processos, incluir_numero_processo=True
    )

    for item in itens:
        item["situacao"] = _situacao_label_execucao_acordos_atividade(item)

    return itens


# v1: dashboard_routes.py:22509
async def _rows_execucao_acordos_rj_atividades_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    funcionario: Optional[List[str]],
    atividade: Optional[List[str]],
    status: Optional[List[str]],
    situacao: Optional[List[str]],
    view: str,
) -> List[Dict[str, Any]]:
    """Réplica os filtros da seção Atividades do dashboard `/execucao_acordos_RJ`,
    para exportação linha a linha da tabela de tarefas (agendamentos).

    ``view`` escolhe o mesmo eixo temporal do toggle "Concluídas"/"Por prazo"
    da seção: "concluidas" usa DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO; "por_prazo"
    usa PRAZO como eixo.
    """
    agendamentos = await fetch_agendamentos_setor_execucao_acordos_RJ()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros = _parse_execucao_atividades_filtros(funcionario, atividade, status, situacao)
    ag_filtrados = filtrar_agendamentos_execucao_acordos_RJ(
        agendamentos, filtros, from_date=from_date, to_date=to_date
    )
    if view == "por_prazo":
        itens = list_execucao_atividades_por_prazo_periodo_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
    else:
        itens = list_execucao_atividades_periodo_acordos_RJ(
            ag_filtrados, from_date=from_date, to_date=to_date
        )

    processos = await fetch_execucao_acordos_RJ()
    itens = _enriquecer_atividades_acordos_rj_com_dados_processo(
        itens, ag_filtrados, processos, incluir_numero_processo=True
    )

    for item in itens:
        item["situacao"] = _situacao_label_execucao_acordos_atividade(item)

    return itens


# v1: dashboard_routes.py:23977
async def get_recursal_LA_filtros_opcoes():
    """Listas de status, decisões, juízes e relatores para o painel de filtros."""
    all_rows = await fetch_recursal_LA()
    return get_opcoes_filtros_recursal_LA(all_rows)


# v1: dashboard_routes.py:24013
async def get_recursal_LA_por_subfase(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description=(
            "estoque = todos em fase 8 (sem filtro de data); "
            "entrada = fase 8 com DT_ENTRADA_RECURSAL no período (from/to obrigatórios)."
        ),
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por subfase na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_la_distribuicao_response(
        dashboard_slug="recursal_LA/por_subfase",
        chart_field="recursal_por_subfase_LA",
        group_fn=group_recursal_por_subfase_LA,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:24073
async def get_recursal_LA_por_materia(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por matéria na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_la_distribuicao_response(
        dashboard_slug="recursal_LA/por_materia",
        chart_field="recursal_por_materia_LA",
        group_fn=group_recursal_por_materia_LA,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:24130
async def get_recursal_LA_por_competencia(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por competência na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_la_distribuicao_response(
        dashboard_slug="recursal_LA/por_competencia",
        chart_field="recursal_por_competencia_LA",
        group_fn=group_recursal_por_competencia_LA,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:24187
async def get_recursal_LA_por_vara(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por vara na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_la_distribuicao_response(
        dashboard_slug="recursal_LA/por_vara",
        chart_field="recursal_por_vara_LA",
        group_fn=group_recursal_por_vara_LA,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:24244
async def get_recursal_LA_status_1g(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Totais na fase Recursal por status de 1º grau (``ID_1G``), sem filtro de data.

    Cadastro LexFlow (``status_primeiro_grau``): 4 Favorável, 5 Desfavorável, 6 Procedente,
    7 Parcialmente procedente, 8 Extinção, 9 Parcialmente favorável, entre outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_recursal_por_status_1g_LA(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_LA",
        stats=DashboardStats(
            total_sentenca_favoravel_recurso_LA=get_total_sentenca_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_desfavoravel_recurso_LA=get_total_sentenca_desfavoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_procedente_1g_recurso_LA=get_total_procedente_1g_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_parcialmente_procedente_recurso_LA=get_total_parcialmente_procedente_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_extincao_recurso_LA=get_total_sentenca_extincao_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_parcialmente_favoravel_recurso_LA=(
                get_total_sentenca_parcialmente_favoravel_recurso_LA(
                    all_rows, from_date=from_date, to_date=to_date
                )
            ),
            valor_causa_sentenca_favoravel_recurso_LA=get_valor_causa_sentenca_sentenca_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_desfavoravel_recurso_LA=get_valor_causa_sentenca_sentenca_desfavoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_procedente_1g_recurso_LA=get_valor_causa_sentenca_procedente_1g_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_parcialmente_procedente_recurso_LA=get_valor_causa_sentenca_parcialmente_procedente_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_extincao_recurso_LA=get_valor_causa_sentenca_sentenca_extincao_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_parcialmente_favoravel_recurso_LA=get_valor_causa_sentenca_parcialmente_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
        ),
        recursal_por_status_1g_LA=chart,
    )


# v1: dashboard_routes.py:24483
async def get_recursal_LA_status_2g(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Totais na fase Recursal por status de 2º grau (``ID_2G``), sem filtro de data.

    Cadastro LexFlow (``status_segundo_grau``): 4 Desfavorável, 5 Favorável, 6 Parcialmente
    favorável, 7 Parcial (retomada), 8 Extinção, entre outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_recursal_por_status_2g_LA(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_LA",
        stats=DashboardStats(
            total_acordao_desfavoravel_recurso_LA=get_total_acordao_desfavoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_favoravel_recurso_LA=get_total_acordao_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_parcialmente_favoravel_recurso_LA=get_total_acordao_parcialmente_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_parcial_retomada_recurso_LA=get_total_acordao_parcial_retomada_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_extincao_recurso_LA=get_total_acordao_extincao_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_desfavoravel_recurso_LA=get_valor_causa_acordao_desfavoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_favoravel_recurso_LA=get_valor_causa_acordao_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_parcialmente_favoravel_recurso_LA=get_valor_causa_acordao_parcialmente_favoravel_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_parcial_retomada_recurso_LA=get_valor_causa_acordao_parcial_retomada_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_extincao_recurso_LA=get_valor_causa_acordao_extincao_recurso_LA(
                all_rows, from_date=from_date, to_date=to_date
            ),
        ),
        recursal_por_status_2g_LA=chart,
    )


# v1: dashboard_routes.py:24690
async def get_recursal_LA_decisoes(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Decisões recursais (cruzamento 1G × 2G) no período.

    Classifica Mantido/Revertido Ganho/Perda e Extinção (Permite Reajuizar).
    Filtro de período por ``DATA_ACORDAO``.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        _chart_from_decisoes_item(x)
        for x in group_decisoes_recursal_LA(all_rows, from_date=from_date, to_date=to_date)
    ]
    return DashboardResponse(
        dashboard="recursal_LA",
        stats=DashboardStats(**_build_decisoes_recursal_LA_stats(all_rows, from_date, to_date)),
        recursal_decisoes_LA=chart,
    )


# v1: dashboard_routes.py:24754
async def get_recursal_LA_ranking_juizes(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Ranking de juízes por taxa de sucesso nas sentenças (1G).

    Filtro de período por ``DATA_SENTENCA``. Classificação: Fav / Des / Outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    ranking = [
        RecursalRankingMagistradoRow(**x)
        for x in get_ranking_juizes_recursal_LA(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_LA",
        stats=DashboardStats(),
        ranking_juizes_recursal_LA=ranking,
    )


# v1: dashboard_routes.py:24819
async def get_recursal_LA_ranking_relatores(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Ranking de relatores por taxa de sucesso nos acórdãos (2G).

    Filtro de período por ``DATA_ACORDAO``. Classificação: Fav / Des / Outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    ranking = [
        RecursalRankingMagistradoRow(**x)
        for x in get_ranking_relatores_recursal_LA(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_LA",
        stats=DashboardStats(),
        ranking_relatores_recursal_LA=ranking,
    )


# v1: dashboard_routes.py:24970
async def get_recursal_NG_filtros_opcoes():
    """Listas de status, decisões, juízes e relatores para o painel de filtros."""
    all_rows = await fetch_recursal_NG()
    return get_opcoes_filtros_recursal_NG(all_rows)


# v1: dashboard_routes.py:25006
async def get_recursal_NG_por_subfase(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description=(
            "estoque = todos em fase 8 (sem filtro de data); "
            "entrada = fase 8 com DT_ENTRADA_RECURSAL no período (from/to obrigatórios)."
        ),
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por subfase na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_ng_distribuicao_response(
        dashboard_slug="recursal_NG/por_subfase",
        chart_field="recursal_por_subfase_NG",
        group_fn=group_recursal_por_subfase_NG,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:25066
async def get_recursal_NG_por_materia(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por matéria na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_ng_distribuicao_response(
        dashboard_slug="recursal_NG/por_materia",
        chart_field="recursal_por_materia_NG",
        group_fn=group_recursal_por_materia_NG,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:25123
async def get_recursal_NG_por_competencia(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por competência na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_ng_distribuicao_response(
        dashboard_slug="recursal_NG/por_competencia",
        chart_field="recursal_por_competencia_NG",
        group_fn=group_recursal_por_competencia_NG,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:25180
async def get_recursal_NG_por_vara(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por vara na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_ng_distribuicao_response(
        dashboard_slug="recursal_NG/por_vara",
        chart_field="recursal_por_vara_NG",
        group_fn=group_recursal_por_vara_NG,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:25237
async def get_recursal_NG_status_1g(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Totais na fase Recursal por status de 1º grau (``ID_1G``), sem filtro de data.

    Cadastro LexFlow (``status_primeiro_grau``): 4 Favorável, 5 Desfavorável, 6 Procedente,
    7 Parcialmente procedente, 8 Extinção, 9 Parcialmente favorável, entre outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_recursal_por_status_1g_NG(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_NG",
        stats=DashboardStats(
            total_sentenca_favoravel_recurso_NG=get_total_sentenca_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_desfavoravel_recurso_NG=get_total_sentenca_desfavoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_procedente_1g_recurso_NG=get_total_procedente_1g_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_parcialmente_procedente_recurso_NG=get_total_parcialmente_procedente_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_extincao_recurso_NG=get_total_sentenca_extincao_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_parcialmente_favoravel_recurso_NG=(
                get_total_sentenca_parcialmente_favoravel_recurso_NG(
                    all_rows, from_date=from_date, to_date=to_date
                )
            ),
            valor_causa_sentenca_favoravel_recurso_NG=get_valor_causa_sentenca_sentenca_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_desfavoravel_recurso_NG=get_valor_causa_sentenca_sentenca_desfavoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_procedente_1g_recurso_NG=get_valor_causa_sentenca_procedente_1g_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_parcialmente_procedente_recurso_NG=get_valor_causa_sentenca_parcialmente_procedente_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_extincao_recurso_NG=get_valor_causa_sentenca_sentenca_extincao_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_parcialmente_favoravel_recurso_NG=get_valor_causa_sentenca_parcialmente_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
        ),
        recursal_por_status_1g_NG=chart,
    )


# v1: dashboard_routes.py:25476
async def get_recursal_NG_status_2g(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Totais na fase Recursal por status de 2º grau (``ID_2G``), sem filtro de data.

    Cadastro LexFlow (``status_segundo_grau``): 4 Desfavorável, 5 Favorável, 6 Parcialmente
    favorável, 7 Parcial (retomada), 8 Extinção, entre outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_recursal_por_status_2g_NG(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_NG",
        stats=DashboardStats(
            total_acordao_desfavoravel_recurso_NG=get_total_acordao_desfavoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_favoravel_recurso_NG=get_total_acordao_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_parcialmente_favoravel_recurso_NG=get_total_acordao_parcialmente_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_parcial_retomada_recurso_NG=get_total_acordao_parcial_retomada_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_extincao_recurso_NG=get_total_acordao_extincao_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_desfavoravel_recurso_NG=get_valor_causa_acordao_desfavoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_favoravel_recurso_NG=get_valor_causa_acordao_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_parcialmente_favoravel_recurso_NG=get_valor_causa_acordao_parcialmente_favoravel_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_parcial_retomada_recurso_NG=get_valor_causa_acordao_parcial_retomada_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_extincao_recurso_NG=get_valor_causa_acordao_extincao_recurso_NG(
                all_rows, from_date=from_date, to_date=to_date
            ),
        ),
        recursal_por_status_2g_NG=chart,
    )


# v1: dashboard_routes.py:25683
async def get_recursal_NG_decisoes(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Decisões recursais (cruzamento 1G × 2G) no período.

    Classifica Mantido/Revertido Ganho/Perda e Extinção (Permite Reajuizar).
    Filtro de período por ``DATA_ACORDAO``.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        _chart_from_decisoes_item(x)
        for x in group_decisoes_recursal_NG(all_rows, from_date=from_date, to_date=to_date)
    ]
    return DashboardResponse(
        dashboard="recursal_NG",
        stats=DashboardStats(**_build_decisoes_recursal_NG_stats(all_rows, from_date, to_date)),
        recursal_decisoes_NG=chart,
    )


# v1: dashboard_routes.py:25747
async def get_recursal_NG_ranking_juizes(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Ranking de juízes por taxa de sucesso nas sentenças (1G).

    Filtro de período por ``DATA_SENTENCA``. Classificação: Fav / Des / Outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    ranking = [
        RecursalRankingMagistradoRow(**x)
        for x in get_ranking_juizes_recursal_NG(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_NG",
        stats=DashboardStats(),
        ranking_juizes_recursal_NG=ranking,
    )


# v1: dashboard_routes.py:25812
async def get_recursal_NG_ranking_relatores(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Ranking de relatores por taxa de sucesso nos acórdãos (2G).

    Filtro de período por ``DATA_ACORDAO``. Classificação: Fav / Des / Outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    ranking = [
        RecursalRankingMagistradoRow(**x)
        for x in get_ranking_relatores_recursal_NG(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_NG",
        stats=DashboardStats(),
        ranking_relatores_recursal_NG=ranking,
    )


# v1: dashboard_routes.py:25963
async def get_recursal_RJ_filtros_opcoes():
    """Listas de status, decisões, juízes e relatores para o painel de filtros."""
    all_rows = await fetch_recursal_RJ()
    return get_opcoes_filtros_recursal_RJ(all_rows)


# v1: dashboard_routes.py:25999
async def get_recursal_RJ_por_subfase(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description=(
            "estoque = todos em fase 8 (sem filtro de data); "
            "entrada = fase 8 com DT_ENTRADA_RECURSAL no período (from/to obrigatórios)."
        ),
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por subfase na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_rj_distribuicao_response(
        dashboard_slug="recursal_RJ/por_subfase",
        chart_field="recursal_por_subfase_RJ",
        group_fn=group_recursal_por_subfase_RJ,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:26059
async def get_recursal_RJ_por_materia(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por matéria na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_rj_distribuicao_response(
        dashboard_slug="recursal_RJ/por_materia",
        chart_field="recursal_por_materia_RJ",
        group_fn=group_recursal_por_materia_RJ,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:26116
async def get_recursal_RJ_por_competencia(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por competência na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_rj_distribuicao_response(
        dashboard_slug="recursal_RJ/por_competencia",
        chart_field="recursal_por_competencia_RJ",
        group_fn=group_recursal_por_competencia_RJ,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:26173
async def get_recursal_RJ_por_vara(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    base: str = Query(
        "estoque",
        description="estoque = fase 8; entrada = DT_ENTRADA_RECURSAL no período.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """Distribuição por vara na fase Recursal (estoque ou entrada no período)."""
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _recursal_rj_distribuicao_response(
        dashboard_slug="recursal_RJ/por_vara",
        chart_field="recursal_por_vara_RJ",
        group_fn=group_recursal_por_vara_RJ,
        from_date=from_date,
        to_date=to_date,
        base=base,
        filtros=filtros,
        atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:26230
async def get_recursal_RJ_status_1g(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Totais na fase Recursal por status de 1º grau (``ID_1G``), sem filtro de data.

    Cadastro LexFlow (``status_primeiro_grau``): 4 Favorável, 5 Desfavorável, 6 Procedente,
    7 Parcialmente procedente, 8 Extinção, 9 Parcialmente favorável, entre outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_recursal_por_status_1g_RJ(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_RJ",
        stats=DashboardStats(
            total_sentenca_favoravel_recurso_RJ=get_total_sentenca_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_desfavoravel_recurso_RJ=get_total_sentenca_desfavoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_procedente_1g_recurso_RJ=get_total_procedente_1g_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_parcialmente_procedente_recurso_RJ=get_total_parcialmente_procedente_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_extincao_recurso_RJ=get_total_sentenca_extincao_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_sentenca_parcialmente_favoravel_recurso_RJ=(
                get_total_sentenca_parcialmente_favoravel_recurso_RJ(
                    all_rows, from_date=from_date, to_date=to_date
                )
            ),
            valor_causa_sentenca_favoravel_recurso_RJ=get_valor_causa_sentenca_sentenca_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_desfavoravel_recurso_RJ=get_valor_causa_sentenca_sentenca_desfavoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_procedente_1g_recurso_RJ=get_valor_causa_sentenca_procedente_1g_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_parcialmente_procedente_recurso_RJ=get_valor_causa_sentenca_parcialmente_procedente_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_extincao_recurso_RJ=get_valor_causa_sentenca_sentenca_extincao_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_sentenca_parcialmente_favoravel_recurso_RJ=get_valor_causa_sentenca_parcialmente_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
        ),
        recursal_por_status_1g_RJ=chart,
    )


# v1: dashboard_routes.py:26469
async def get_recursal_RJ_status_2g(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Totais na fase Recursal por status de 2º grau (``ID_2G``), sem filtro de data.

    Cadastro LexFlow (``status_segundo_grau``): 4 Desfavorável, 5 Favorável, 6 Parcialmente
    favorável, 7 Parcial (retomada), 8 Extinção, entre outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        ChartDataPoint(**x)
        for x in group_recursal_por_status_2g_RJ(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_RJ",
        stats=DashboardStats(
            total_acordao_desfavoravel_recurso_RJ=get_total_acordao_desfavoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_favoravel_recurso_RJ=get_total_acordao_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_parcialmente_favoravel_recurso_RJ=get_total_acordao_parcialmente_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_parcial_retomada_recurso_RJ=get_total_acordao_parcial_retomada_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            total_acordao_extincao_recurso_RJ=get_total_acordao_extincao_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_desfavoravel_recurso_RJ=get_valor_causa_acordao_desfavoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_favoravel_recurso_RJ=get_valor_causa_acordao_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_parcialmente_favoravel_recurso_RJ=get_valor_causa_acordao_parcialmente_favoravel_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_parcial_retomada_recurso_RJ=get_valor_causa_acordao_parcial_retomada_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
            valor_causa_acordao_extincao_recurso_RJ=get_valor_causa_acordao_extincao_recurso_RJ(
                all_rows, from_date=from_date, to_date=to_date
            ),
        ),
        recursal_por_status_2g_RJ=chart,
    )


# v1: dashboard_routes.py:26676
async def get_recursal_RJ_decisoes(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Decisões recursais (cruzamento 1G × 2G) no período.

    Classifica Mantido/Revertido Ganho/Perda e Extinção (Permite Reajuizar).
    Filtro de período por ``DATA_ACORDAO``.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    chart = [
        _chart_from_decisoes_item(x)
        for x in group_decisoes_recursal_RJ(all_rows, from_date=from_date, to_date=to_date)
    ]
    return DashboardResponse(
        dashboard="recursal_RJ",
        stats=DashboardStats(**_build_decisoes_recursal_RJ_stats(all_rows, from_date, to_date)),
        recursal_decisoes_RJ=chart,
    )


# v1: dashboard_routes.py:26740
async def get_recursal_RJ_ranking_juizes(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Ranking de juízes por taxa de sucesso nas sentenças (1G).

    Filtro de período por ``DATA_SENTENCA``. Classificação: Fav / Des / Outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    ranking = [
        RecursalRankingMagistradoRow(**x)
        for x in get_ranking_juizes_recursal_RJ(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_RJ",
        stats=DashboardStats(),
        ranking_juizes_recursal_RJ=ranking,
    )


# v1: dashboard_routes.py:26805
async def get_recursal_RJ_ranking_relatores(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None, description="Filtra por matéria(s)"),
    competencia: Optional[List[str]] = Query(None, description="Filtra por competência(s)"),
    vara: Optional[List[str]] = Query(None, description="Filtra por vara(s)"),
    subfase: Optional[List[str]] = Query(None, description="Filtra por subfase(s)"),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Ranking de relatores por taxa de sucesso nos acórdãos (2G).

    Filtro de período por ``DATA_ACORDAO``. Classificação: Fav / Des / Outros.
    """
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        filtros_atividades,
        from_date,
        to_date,
    )
    ranking = [
        RecursalRankingMagistradoRow(**x)
        for x in get_ranking_relatores_recursal_RJ(
            all_rows, from_date=from_date, to_date=to_date
        )
    ]
    return DashboardResponse(
        dashboard="recursal_RJ",
        stats=DashboardStats(),
        ranking_relatores_recursal_RJ=ranking,
    )


# v1: dashboard_routes.py:26871
_CAMPOS_EXPORT_RECURSAL_LA: Dict[str, str] = {
    "id": "id",
    "numero_processo": "NUMERO_PROCESSO",
    "uf": "UF",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "data_ajuizamento": "DATA_AJUIZAMENTO",
    "data_ultima_movimentacao": "DATA_ULTIMA_MOVIMENTACAO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "operacao": "OPERACAO",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "valor_causa_sentenca": "VALOR_CAUSA_SENTENCA",
    "valor_causa_acordo": "VALOR_CAUSA_ACORDO",
    "dano_moral_sentenca": "DANO_MORAL_SENTENCA",
    "dano_material_sentenca": "DANO_MATERIAL_SENTENCA",
    "status_1g": "STATUS_1G",
    "juiz_1g": "JUIZ_1G",
    "status_2g": "STATUS_2G",
    "relator_2g": "RELATOR_2G",
    "decisao": "__computed_decisao__",
    "data_sentenca": "DATA_SENTENCA",
    "data_acordao": "DATA_ACORDAO",
    "data_transito_julgado": "DATA_TRANSITO_JULGADO",
    "dt_entrada_recursal": "DT_ENTRADA_RECURSAL",
    "dt_saida_recursal": "DT_SAIDA_RECURSAL",
    "atividade_recursos": "ATIVIDADE_RECURSOS",
    "status_agendamento_recursos": "STATUS_AGENDAMENTO_RECURSOS",
}


# v1: dashboard_routes.py:26902
_LABELS_EXPORT_RECURSAL_LA: Dict[str, str] = {
    "id": "ID",
    "numero_processo": "Número do Processo",
    "uf": "UF",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "data_ajuizamento": "Data de Ajuizamento",
    "data_ultima_movimentacao": "Última Movimentação",
    "fase": "Fase",
    "subfase": "Subfase",
    "operacao": "Operação",
    "vara": "Vara",
    "competencia": "Competência",
    "valor_causa_sentenca": "Valor da Causa (Sentença)",
    "valor_causa_acordo": "Valor da Causa (Acordo)",
    "dano_moral_sentenca": "Dano Moral (Sentença)",
    "dano_material_sentenca": "Dano Material (Sentença)",
    "status_1g": "Status 1º Grau",
    "juiz_1g": "Juiz (1º Grau)",
    "status_2g": "Status 2º Grau",
    "relator_2g": "Relator (2º Grau)",
    "decisao": "Decisão",
    "data_sentenca": "Data da Sentença",
    "data_acordao": "Data do Acórdão",
    "data_transito_julgado": "Data Trânsito em Julgado",
    "dt_entrada_recursal": "Data Entrada Recursal",
    "dt_saida_recursal": "Data Saída Recursal",
    "atividade_recursos": "Atividade em Andamento",
    "status_agendamento_recursos": "Status da Atividade",
}


# v1: dashboard_routes.py:26934
_CAMPOS_EXPORT_RECURSAL_NG: Dict[str, str] = {
    "id": "id",
    "numero_processo": "NUMERO_PROCESSO",
    "uf": "UF",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "data_ajuizamento": "DATA_AJUIZAMENTO",
    "data_ultima_movimentacao": "DATA_ULTIMA_MOVIMENTACAO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "operacao": "OPERACAO",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "valor_causa_sentenca": "VALOR_CAUSA_SENTENCA",
    "valor_causa_acordo": "VALOR_CAUSA_ACORDO",
    "dano_moral_sentenca": "DANO_MORAL_SENTENCA",
    "dano_material_sentenca": "DANO_MATERIAL_SENTENCA",
    "status_1g": "STATUS_1G",
    "juiz_1g": "JUIZ_1G",
    "status_2g": "STATUS_2G",
    "relator_2g": "RELATOR_2G",
    "decisao": "__computed_decisao__",
    "data_sentenca": "DATA_SENTENCA",
    "data_acordao": "DATA_ACORDAO",
    "data_transito_julgado": "DATA_TRANSITO_JULGADO",
    "dt_entrada_recursal": "DT_ENTRADA_RECURSAL",
    "dt_saida_recursal": "DT_SAIDA_RECURSAL",
    "atividade_recursos": "ATIVIDADE_RECURSOS",
    "status_agendamento_recursos": "STATUS_AGENDAMENTO_RECURSOS",
}


# v1: dashboard_routes.py:26965
_LABELS_EXPORT_RECURSAL_NG: Dict[str, str] = {
    "id": "ID",
    "numero_processo": "Número do Processo",
    "uf": "UF",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "data_ajuizamento": "Data de Ajuizamento",
    "data_ultima_movimentacao": "Última Movimentação",
    "fase": "Fase",
    "subfase": "Subfase",
    "operacao": "Operação",
    "vara": "Vara",
    "competencia": "Competência",
    "valor_causa_sentenca": "Valor da Causa (Sentença)",
    "valor_causa_acordo": "Valor da Causa (Acordo)",
    "dano_moral_sentenca": "Dano Moral (Sentença)",
    "dano_material_sentenca": "Dano Material (Sentença)",
    "status_1g": "Status 1º Grau",
    "juiz_1g": "Juiz (1º Grau)",
    "status_2g": "Status 2º Grau",
    "relator_2g": "Relator (2º Grau)",
    "decisao": "Decisão",
    "data_sentenca": "Data da Sentença",
    "data_acordao": "Data do Acórdão",
    "data_transito_julgado": "Data Trânsito em Julgado",
    "dt_entrada_recursal": "Data Entrada Recursal",
    "dt_saida_recursal": "Data Saída Recursal",
    "atividade_recursos": "Atividade em Andamento",
    "status_agendamento_recursos": "Status da Atividade",
}


# v1: dashboard_routes.py:26998
_CAMPOS_EXPORT_RECURSAL_RJ: Dict[str, str] = {
    "id": "id",
    "numero_processo": "NUMERO_PROCESSO",
    "uf": "UF",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "data_ajuizamento": "DATA_AJUIZAMENTO",
    "data_ultima_movimentacao": "DATA_ULTIMA_MOVIMENTACAO",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "operacao": "OPERACAO",
    "vara": "VARA",
    "competencia": "COMPETENCIA",
    "valor_causa_sentenca": "VALOR_CAUSA_SENTENCA",
    "valor_causa_acordo": "VALOR_CAUSA_ACORDO",
    "dano_moral_sentenca": "DANO_MORAL_SENTENCA",
    "dano_material_sentenca": "DANO_MATERIAL_SENTENCA",
    "status_1g": "STATUS_1G",
    "juiz_1g": "JUIZ_1G",
    "status_2g": "STATUS_2G",
    "relator_2g": "RELATOR_2G",
    "decisao": "__computed_decisao__",
    "data_sentenca": "DATA_SENTENCA",
    "data_acordao": "DATA_ACORDAO",
    "data_transito_julgado": "DATA_TRANSITO_JULGADO",
    "dt_entrada_recursal": "DT_ENTRADA_RECURSAL",
    "dt_saida_recursal": "DT_SAIDA_RECURSAL",
    "atividade_recursos": "ATIVIDADE_RECURSOS",
    "status_agendamento_recursos": "STATUS_AGENDAMENTO_RECURSOS",
}


# v1: dashboard_routes.py:27029
_LABELS_EXPORT_RECURSAL_RJ: Dict[str, str] = {
    "id": "ID",
    "numero_processo": "Número do Processo",
    "uf": "UF",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "data_ajuizamento": "Data de Ajuizamento",
    "data_ultima_movimentacao": "Última Movimentação",
    "fase": "Fase",
    "subfase": "Subfase",
    "operacao": "Operação",
    "vara": "Vara",
    "competencia": "Competência",
    "valor_causa_sentenca": "Valor da Causa (Sentença)",
    "valor_causa_acordo": "Valor da Causa (Acordo)",
    "dano_moral_sentenca": "Dano Moral (Sentença)",
    "dano_material_sentenca": "Dano Material (Sentença)",
    "status_1g": "Status 1º Grau",
    "juiz_1g": "Juiz (1º Grau)",
    "status_2g": "Status 2º Grau",
    "relator_2g": "Relator (2º Grau)",
    "decisao": "Decisão",
    "data_sentenca": "Data da Sentença",
    "data_acordao": "Data do Acórdão",
    "data_transito_julgado": "Data Trânsito em Julgado",
    "dt_entrada_recursal": "Data Entrada Recursal",
    "dt_saida_recursal": "Data Saída Recursal",
    "atividade_recursos": "Atividade em Andamento",
    "status_agendamento_recursos": "Status da Atividade",
}


# v1: dashboard_routes.py:27062
_RELATORIO_DATE_COLUNAS_EXPORT: Dict[str, str] = {
    "data_ajuizamento": "DATA_AJUIZAMENTO",
    "data_sentenca": "DATA_SENTENCA",
    "data_acordao": "DATA_ACORDAO",
    "data_transito_julgado": "DATA_TRANSITO_JULGADO",
    "dt_entrada_recursal": "DT_ENTRADA_RECURSAL",
    "dt_saida_recursal": "DT_SAIDA_RECURSAL",
    "data_ultima_movimentacao": "DATA_ULTIMA_MOVIMENTACAO",
}


# v1: dashboard_routes.py:27073
def _parse_intervalos_datas_relatorio_export(
    query_params: Any,
) -> Dict[str, Tuple[Optional[date], Optional[date]]]:
    """Lê ``{slug}_from`` / ``{slug}_to`` dos query params do relatório."""
    intervalos: Dict[str, Tuple[Optional[date], Optional[date]]] = {}
    for slug in _RELATORIO_DATE_COLUNAS_EXPORT:
        raw_de = query_params.get(f"{slug}_from")
        raw_ate = query_params.get(f"{slug}_to")
        de = parse_date_from_db(raw_de) if raw_de else None
        ate = parse_date_from_db(raw_ate) if raw_ate else None
        if de or ate:
            intervalos[slug] = (de, ate)
    return intervalos


# v1: dashboard_routes.py:27088
def _filtrar_rows_intervalos_datas_relatorio(
    rows: List[Dict[str, Any]],
    intervalos: Dict[str, Tuple[Optional[date], Optional[date]]],
) -> List[Dict[str, Any]]:
    if not intervalos:
        return rows
    filtrados: List[Dict[str, Any]] = []
    for row in rows:
        incluir = True
        for slug, (de, ate) in intervalos.items():
            col = _RELATORIO_DATE_COLUNAS_EXPORT[slug]
            val = row.get(col) or row.get(col.lower())
            dt = parse_date_from_db(val)
            if de is not None and (dt is None or dt < de):
                incluir = False
                break
            if ate is not None and (dt is None or dt > ate):
                incluir = False
                break
        if incluir:
            filtrados.append(row)
    return filtrados


# v1: dashboard_routes.py:27112
def _formatar_valor_export_recursal_la(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, (date, datetime)):
        return val.strftime("%d/%m/%Y")
    return str(val)


# v1: dashboard_routes.py:27120
def _valor_campo_export_recursal_la(row: Dict[str, Any], slug: str) -> Any:
    if slug == "decisao":
        return rotulo_decisao_recursal_export_LA(row)
    if slug == "numero_processo":
        numero = _get_numero_processo_recursal_la(row)
        return numero if numero else None
    col = _CAMPOS_EXPORT_RECURSAL_LA[slug]
    if col.startswith("__computed_"):
        return None
    return _col_recursal_la(row, col, col.lower(), col.upper())


# v1: dashboard_routes.py:27132
def _linhas_export_recursal_la(
    all_rows: List[Dict[str, Any]],
    slugs: List[str],
) -> Tuple[List[str], List[List[str]]]:
    headers = [_LABELS_EXPORT_RECURSAL_LA[s] for s in slugs]
    data_rows: List[List[str]] = []
    for row in all_rows:
        linha = []
        for slug in slugs:
            val = _valor_campo_export_recursal_la(row, slug)
            linha.append(_formatar_valor_export_recursal_la(val))
        data_rows.append(linha)
    return headers, data_rows


# v1: dashboard_routes.py:27147
def _gerar_csv_export_recursal_la(headers: List[str], data_rows: List[List[str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for linha in data_rows:
        writer.writerow(linha)
    return output.getvalue().encode("utf-8-sig")


# v1: dashboard_routes.py:27156
def _gerar_xlsx_export_recursal_la(
    headers: List[str],
    data_rows: List[List[str]],
    slugs: List[str],
) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório"
    ws.append(headers)
    for row_idx, linha in enumerate(data_rows, start=2):
        for col_idx, val in enumerate(linha, start=1):
            slug = slugs[col_idx - 1] if col_idx - 1 < len(slugs) else ""
            cell = ws.cell(row=row_idx, column=col_idx)
            if slug == "numero_processo" and val:
                cell.value = str(val)
                cell.number_format = "@"
            else:
                cell.value = val

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# v1: dashboard_routes.py:27184
async def export_recursal_LA(
    request: Request,
    format: str = Query(
        "csv",
        description="Formato do arquivo: csv ou xlsx.",
    ),
    campos: Optional[List[str]] = Query(
        None,
        description="Slugs dos campos a incluir no CSV (ex.: numero_processo, materia). "
                    "Padrão: todos os campos disponíveis.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None),
    parte_adversa: Optional[List[str]] = Query(None),
    competencia: Optional[List[str]] = Query(None),
    vara: Optional[List[str]] = Query(None),
    subfase: Optional[List[str]] = Query(None),
    fase: Optional[List[str]] = Query(None),
    operacao: Optional[List[str]] = Query(None),
    extinto_2g: Optional[List[str]] = Query(None),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Exporta os processos da fase Recursal (LA) filtrados como CSV ou XLSX.

    O parâmetro ``campos`` define quais colunas aparecem no arquivo; aceita os mesmos
    slugs listados em ``_CAMPOS_EXPORT_RECURSAL_LA``. Se omitido, exporta todos.
    Os demais parâmetros espelham os filtros do endpoint ``/recursal_LA``.
    """
    formato = (format or "csv").strip().lower()
    if formato not in ("csv", "xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Use csv ou xlsx.",
        )

    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g, id_2g, juiz, relator, decisao, materia, parte_adversa, competencia,
        vara, subfase, fase, operacao, extinto_2g,
        funcionario_recursos, atividade_recursos, status_recursos, situacao_recursos,
    )

    intervalos_datas = _parse_intervalos_datas_relatorio_export(request.query_params)

    all_rows = await _rows_recursal_la_filtradas(
        await fetch_recursal_LA(),
        filtros,
        filtros_atividades,
        None,
        None,
    )
    all_rows = _filtrar_rows_intervalos_datas_relatorio(all_rows, intervalos_datas)
    all_rows = _enriquecer_numero_processo_export_la(all_rows)

    campos_validos = list(_CAMPOS_EXPORT_RECURSAL_LA.keys())
    if campos:
        slugs = [c for c in campos if c in _CAMPOS_EXPORT_RECURSAL_LA]
        if not slugs:
            slugs = campos_validos
    else:
        slugs = campos_validos

    headers, data_rows = _linhas_export_recursal_la(all_rows, slugs)

    if formato == "xlsx":
        file_bytes = _gerar_xlsx_export_recursal_la(headers, data_rows, slugs)
        filename = "recursal_LA_relatorio.xlsx"
        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        file_bytes = _gerar_csv_export_recursal_la(headers, data_rows)
        filename = "recursal_LA_relatorio.csv"
        media_type = "text/csv; charset=utf-8"

    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# v1: dashboard_routes.py:27273
def _formatar_valor_export_recursal_ng(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, (date, datetime)):
        return val.strftime("%d/%m/%Y")
    return str(val)


# v1: dashboard_routes.py:27281
def _valor_campo_export_recursal_ng(row: Dict[str, Any], slug: str) -> Any:
    if slug == "decisao":
        return rotulo_decisao_recursal_export_NG(row)
    if slug == "numero_processo":
        numero = _get_numero_processo_recursal_ng(row)
        return numero if numero else None
    col = _CAMPOS_EXPORT_RECURSAL_NG[slug]
    if col.startswith("__computed_"):
        return None
    return _col_recursal_ng(row, col, col.lower(), col.upper())


# v1: dashboard_routes.py:27293
def _linhas_export_recursal_ng(
    all_rows: List[Dict[str, Any]],
    slugs: List[str],
) -> Tuple[List[str], List[List[str]]]:
    headers = [_LABELS_EXPORT_RECURSAL_NG[s] for s in slugs]
    data_rows: List[List[str]] = []
    for row in all_rows:
        linha = []
        for slug in slugs:
            val = _valor_campo_export_recursal_ng(row, slug)
            linha.append(_formatar_valor_export_recursal_ng(val))
        data_rows.append(linha)
    return headers, data_rows


# v1: dashboard_routes.py:27308
def _gerar_csv_export_recursal_ng(headers: List[str], data_rows: List[List[str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for linha in data_rows:
        writer.writerow(linha)
    return output.getvalue().encode("utf-8-sig")


# v1: dashboard_routes.py:27317
def _gerar_xlsx_export_recursal_ng(
    headers: List[str],
    data_rows: List[List[str]],
    slugs: List[str],
) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório"
    ws.append(headers)
    for row_idx, linha in enumerate(data_rows, start=2):
        for col_idx, val in enumerate(linha, start=1):
            slug = slugs[col_idx - 1] if col_idx - 1 < len(slugs) else ""
            cell = ws.cell(row=row_idx, column=col_idx)
            if slug == "numero_processo" and val:
                cell.value = str(val)
                cell.number_format = "@"
            else:
                cell.value = val

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# v1: dashboard_routes.py:27345
async def export_recursal_NG(
    request: Request,
    format: str = Query(
        "csv",
        description="Formato do arquivo: csv ou xlsx.",
    ),
    campos: Optional[List[str]] = Query(
        None,
        description="Slugs dos campos a incluir no CSV (ex.: numero_processo, materia). "
                    "Padrão: todos os campos disponíveis.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None),
    parte_adversa: Optional[List[str]] = Query(None),
    competencia: Optional[List[str]] = Query(None),
    vara: Optional[List[str]] = Query(None),
    subfase: Optional[List[str]] = Query(None),
    fase: Optional[List[str]] = Query(None),
    operacao: Optional[List[str]] = Query(None),
    extinto_2g: Optional[List[str]] = Query(None),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Exporta os processos da fase Recursal (NG) filtrados como CSV ou XLSX.

    O parâmetro ``campos`` define quais colunas aparecem no arquivo; aceita os mesmos
    slugs listados em ``_CAMPOS_EXPORT_RECURSAL_NG``. Se omitido, exporta todos.
    Os demais parâmetros espelham os filtros do endpoint ``/recursal_NG``.
    """
    formato = (format or "csv").strip().lower()
    if formato not in ("csv", "xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Use csv ou xlsx.",
        )

    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g, id_2g, juiz, relator, decisao, materia, parte_adversa, competencia,
        vara, subfase, fase, operacao, extinto_2g,
        funcionario_recursos, atividade_recursos, status_recursos, situacao_recursos,
    )

    intervalos_datas = _parse_intervalos_datas_relatorio_export(request.query_params)

    all_rows = await _rows_recursal_ng_filtradas(
        await fetch_recursal_NG(),
        filtros,
        filtros_atividades,
        None,
        None,
    )
    all_rows = _filtrar_rows_intervalos_datas_relatorio(all_rows, intervalos_datas)
    all_rows = _enriquecer_numero_processo_export_ng(all_rows)

    campos_validos = list(_CAMPOS_EXPORT_RECURSAL_NG.keys())
    if campos:
        slugs = [c for c in campos if c in _CAMPOS_EXPORT_RECURSAL_NG]
        if not slugs:
            slugs = campos_validos
    else:
        slugs = campos_validos

    headers, data_rows = _linhas_export_recursal_ng(all_rows, slugs)

    if formato == "xlsx":
        file_bytes = _gerar_xlsx_export_recursal_ng(headers, data_rows, slugs)
        filename = "recursal_NG_relatorio.xlsx"
        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        file_bytes = _gerar_csv_export_recursal_ng(headers, data_rows)
        filename = "recursal_NG_relatorio.csv"
        media_type = "text/csv; charset=utf-8"

    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# v1: dashboard_routes.py:27435
def _formatar_valor_export_recursal_rj(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, (date, datetime)):
        return val.strftime("%d/%m/%Y")
    return str(val)


# v1: dashboard_routes.py:27443
def _valor_campo_export_recursal_rj(row: Dict[str, Any], slug: str) -> Any:
    if slug == "decisao":
        return rotulo_decisao_recursal_export_RJ(row)
    if slug == "numero_processo":
        numero = _get_numero_processo_recursal_rj(row)
        return numero if numero else None
    col = _CAMPOS_EXPORT_RECURSAL_RJ[slug]
    if col.startswith("__computed_"):
        return None
    return _col_recursal_rj(row, col, col.lower(), col.upper())


# v1: dashboard_routes.py:27455
def _linhas_export_recursal_rj(
    all_rows: List[Dict[str, Any]],
    slugs: List[str],
) -> Tuple[List[str], List[List[str]]]:
    headers = [_LABELS_EXPORT_RECURSAL_RJ[s] for s in slugs]
    data_rows: List[List[str]] = []
    for row in all_rows:
        linha = []
        for slug in slugs:
            val = _valor_campo_export_recursal_rj(row, slug)
            linha.append(_formatar_valor_export_recursal_rj(val))
        data_rows.append(linha)
    return headers, data_rows


# v1: dashboard_routes.py:27470
def _gerar_csv_export_recursal_rj(headers: List[str], data_rows: List[List[str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for linha in data_rows:
        writer.writerow(linha)
    return output.getvalue().encode("utf-8-sig")


# v1: dashboard_routes.py:27479
def _gerar_xlsx_export_recursal_rj(
    headers: List[str],
    data_rows: List[List[str]],
    slugs: List[str],
) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório"
    ws.append(headers)
    for row_idx, linha in enumerate(data_rows, start=2):
        for col_idx, val in enumerate(linha, start=1):
            slug = slugs[col_idx - 1] if col_idx - 1 < len(slugs) else ""
            cell = ws.cell(row=row_idx, column=col_idx)
            if slug == "numero_processo" and val:
                cell.value = str(val)
                cell.number_format = "@"
            else:
                cell.value = val

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# v1: dashboard_routes.py:27507
async def export_recursal_RJ(
    request: Request,
    format: str = Query(
        "csv",
        description="Formato do arquivo: csv ou xlsx.",
    ),
    campos: Optional[List[str]] = Query(
        None,
        description="Slugs dos campos a incluir no CSV (ex.: numero_processo, materia). "
                    "Padrão: todos os campos disponíveis.",
    ),
    id_1g: Optional[List[int]] = Query(None),
    id_2g: Optional[List[int]] = Query(None),
    juiz: Optional[List[str]] = Query(None),
    relator: Optional[List[str]] = Query(None),
    decisao: Optional[List[str]] = Query(None),
    materia: Optional[List[str]] = Query(None),
    parte_adversa: Optional[List[str]] = Query(None),
    competencia: Optional[List[str]] = Query(None),
    vara: Optional[List[str]] = Query(None),
    subfase: Optional[List[str]] = Query(None),
    fase: Optional[List[str]] = Query(None),
    operacao: Optional[List[str]] = Query(None),
    extinto_2g: Optional[List[str]] = Query(None),
    funcionario_recursos: Optional[List[str]] = Query(None),
    atividade_recursos: Optional[List[str]] = Query(None),
    status_recursos: Optional[List[str]] = Query(None),
    situacao_recursos: Optional[List[str]] = Query(None),
):
    """
    Exporta os processos da fase Recursal (RJ) filtrados como CSV ou XLSX.

    O parâmetro ``campos`` define quais colunas aparecem no arquivo; aceita os mesmos
    slugs listados em ``_CAMPOS_EXPORT_RECURSAL_RJ``. Se omitido, exporta todos.
    Os demais parâmetros espelham os filtros do endpoint ``/recursal_RJ``.
    """
    formato = (format or "csv").strip().lower()
    if formato not in ("csv", "xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Use csv ou xlsx.",
        )

    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g, id_2g, juiz, relator, decisao, materia, parte_adversa, competencia,
        vara, subfase, fase, operacao, extinto_2g,
        funcionario_recursos, atividade_recursos, status_recursos, situacao_recursos,
    )

    intervalos_datas = _parse_intervalos_datas_relatorio_export(request.query_params)

    all_rows = await _rows_recursal_rj_filtradas(
        await fetch_recursal_RJ(),
        filtros,
        filtros_atividades,
        None,
        None,
    )
    all_rows = _filtrar_rows_intervalos_datas_relatorio(all_rows, intervalos_datas)
    all_rows = _enriquecer_numero_processo_export_rj(all_rows)

    campos_validos = list(_CAMPOS_EXPORT_RECURSAL_RJ.keys())
    if campos:
        slugs = [c for c in campos if c in _CAMPOS_EXPORT_RECURSAL_RJ]
        if not slugs:
            slugs = campos_validos
    else:
        slugs = campos_validos

    headers, data_rows = _linhas_export_recursal_rj(all_rows, slugs)

    if formato == "xlsx":
        file_bytes = _gerar_xlsx_export_recursal_rj(headers, data_rows, slugs)
        filename = "recursal_RJ_relatorio.xlsx"
        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        file_bytes = _gerar_csv_export_recursal_rj(headers, data_rows)
        filename = "recursal_RJ_relatorio.csv"
        media_type = "text/csv; charset=utf-8"

    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# v1: dashboard_routes.py:27915
def _parse_execucao_atividades_filtros(
    funcionario: Optional[List[str]] = None,
    atividade: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    situacao: Optional[List[str]] = None,
) -> Optional[ExecucaoAtividadesFiltros]:
    """Parser de filtros cumulativos da seção Atividades (agendamentos Execução)."""
    funcionarios: set[str] = set()
    if funcionario:
        for nome in funcionario:
            t = str(nome or "").strip()
            if t:
                funcionarios.add(t)

    atividades: set[str] = set()
    if atividade:
        for raw in atividade:
            t = str(raw or "").strip()
            if t:
                atividades.add(t)

    status_set: set[str] = set()
    if status:
        for raw in status:
            t = str(raw or "").strip()
            if t:
                status_set.add(t)

    situacoes: set[str] = set()
    if situacao:
        for raw in situacao:
            chave = str(raw or "").strip()
            if not chave:
                continue
            if chave not in SITUACOES_VALIDAS_EXECUCAO:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Situação inválida: '{chave}'. "
                        f"Valores: {sorted(SITUACOES_VALIDAS_EXECUCAO)}"
                    ),
                )
            situacoes.add(chave)

    filtros = ExecucaoAtividadesFiltros(
        funcionarios=frozenset(funcionarios) if funcionarios else None,
        atividades=frozenset(atividades) if atividades else None,
        status=frozenset(status_set) if status_set else None,
        situacoes=frozenset(situacoes) if situacoes else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:29861
_CAMPOS_EXPORT_EXECUCAO_LA: Dict[str, str] = dict(_CAMPOS_EXPORT_EXECUCAO_NG)


# v1: dashboard_routes.py:29862
_LABELS_EXPORT_EXECUCAO_LA: Dict[str, str] = dict(_LABELS_EXPORT_EXECUCAO_NG)


# v1: dashboard_routes.py:29865
_CRITERIOS_EXPORT_EXECUCAO_LA = ("entrada", "saida", "total")


# v1: dashboard_routes.py:29868
async def _rows_execucao_la_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[str],
    subfase: Optional[str],
    ano_ajuizamento_execucao: Optional[str],
    criterio: str = "entrada",
    uf: Optional[List[str]] = None,
    comarca: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/execucao_LA`, para exportação linha a
    linha — mesma query, sem campos adicionais e sem a seção de Atividades.

    ``criterio`` escolhe o mesmo recorte usado pelos cards de Indicadores (mesmo
    padrão do extrator de Execução de Acordos):
    - "entrada": processos com DATA_EXECUCAO no período — mesmo critério de
      `_filtrar_entrada_execucao_no_periodo`.
    - "saida": processos que saíram da Execução (foram para o Financeiro) no
      período — mesmo critério de `_filtrar_saida_no_periodo`.
    - "total": total atual em Execução (ID_FASE == 12), sem filtro de período —
      mesmo critério do card "Total em Execução" / `_filtrar_em_execucao`.

    Não pré-filtra por data via `filter_data` (que usa DATA_EXECUCAO): "saida" e
    "total" usam colunas/critério de data diferentes, e cada critério abaixo já
    aplica seu próprio recorte de data internamente.
    """
    all_rows = await fetch_execucao_LA()
    from_date, to_date = _resolve_date_range(from_date, to_date)
    materia_filtro = _filtro_multi(materia)
    subfase_filtro = _filtro_multi(subfase)
    ano_filtro = (
        str(ano_ajuizamento_execucao).strip()
        if ano_ajuizamento_execucao and str(ano_ajuizamento_execucao).strip()
        else None
    )
    uf_filtro = [str(u).strip().upper() for u in uf if str(u).strip()] if uf else None
    comarca_filtro = [str(c).strip() for c in comarca if str(c).strip()] if comarca else None
    rows = filter_execucao_LA_por_comarca(
        filter_execucao_LA_por_uf(
            filter_execucao_LA_por_ano_ajuizamento(
                filter_execucao_LA_por_subfase(
                    filter_execucao_LA_por_materia(all_rows, materia_filtro),
                    subfase_filtro,
                ),
                ano_filtro,
            ),
            uf_filtro,
        ),
        comarca_filtro,
    )
    if criterio == "saida":
        recorte = filtrar_saida_execucao_export_LA(rows, from_date, to_date)
    elif criterio == "total":
        recorte = _filtrar_em_execucao_la(rows)
    else:
        recorte = _filtrar_entrada_execucao_no_periodo_la(rows, from_date, to_date)
    return anotar_saida_execucao_export_LA(recorte, from_date, to_date)


# V2: só os dashboards desta cópia (v1: FETCHES_BY_DASHBOARD, mesmas fontes e chaves).
FETCHES_BY_DASHBOARD: Dict[str, List[Tuple[str, Any]]] = {
    "execucao": [("execucao", fetch_execucao), ("agendamentos_setor_execucao_NG", fetch_agendamentos_setor_execucao_NG)],
    "execucao_LA": [("execucao_LA", fetch_execucao_LA), ("agendamentos_setor_execucao_LA", fetch_agendamentos_setor_execucao_LA)],
    "execucao_RJ": [("execucao_RJ", fetch_execucao_RJ), ("agendamentos_setor_execucao_RJ", fetch_agendamentos_setor_execucao_RJ)],
    "execucao_acordos_NG": [("execucao_acordos_NG", fetch_execucao_acordos_NG), ("agendamentos_fechamento_acordos_NG", fetch_agendamentos_fechamento_acordos_NG), ("agendamentos_setor_execucao_acordos_NG", fetch_agendamentos_setor_execucao_acordos_NG)],
    "execucao_acordos_LA": [("execucao_acordos_LA", fetch_execucao_acordos_LA), ("agendamentos_fechamento_acordos_LA", fetch_agendamentos_fechamento_acordos_LA), ("agendamentos_setor_execucao_acordos_LA", fetch_agendamentos_setor_execucao_acordos_LA)],
    "execucao_acordos_RJ": [("execucao_acordos_RJ", fetch_execucao_acordos_RJ), ("agendamentos_fechamento_acordos_RJ", fetch_agendamentos_fechamento_acordos_RJ), ("agendamentos_setor_execucao_acordos_RJ", fetch_agendamentos_setor_execucao_acordos_RJ)],
    "recursal_NG": [("recursal_NG", fetch_recursal_NG), ("agendamentos_setor_recursos_NG", fetch_agendamentos_setor_recursos_NG), ("atividades_setor_recursos_NG", fetch_atividades_setor_recursos_NG)],
    "recursal_LA": [("recursal_LA", fetch_recursal_LA), ("agendamentos_setor_recursos_LA", fetch_agendamentos_setor_recursos_LA), ("atividades_setor_recursos_LA", fetch_atividades_setor_recursos_LA)],
    "recursal_RJ": [("recursal_RJ", fetch_recursal_RJ), ("agendamentos_setor_recursos_RJ", fetch_agendamentos_setor_recursos_RJ), ("atividades_setor_recursos_RJ", fetch_atividades_setor_recursos_RJ), ("controle_processo_todas_situacoes", fetch_controle_processo_todas_situacoes)],
    "controle_processo_NG": [("controle_processo_NG", fetch_controle_processo_NG), ("log_subfase_processual", fetch_log_subfase_processual), ("controle_processo_todas_situacoes", fetch_controle_processo_todas_situacoes)],
    "controle_processo_LA": [("controle_processo_LA", fetch_controle_processo_LA), ("log_subfase_processual", fetch_log_subfase_processual), ("controle_processo_todas_situacoes", fetch_controle_processo_todas_situacoes)],
    "publicacoes_NG": [("publicacoes_NG", fetch_publicacoes_NG), ("agendamentos_todos_setores_NG", fetch_agendamentos_todos_setores_NG)],
    "publicacoes_LA": [("publicacoes_LA", fetch_publicacoes_LA), ("agendamentos_todos_setores_LA", fetch_agendamentos_todos_setores_LA)],
    "publicacoes_RJ": [("publicacoes_LA_RJ", fetch_publicacoes_LA_RJ), ("agendamentos_todos_setores_LA_RJ", fetch_agendamentos_todos_setores_LA_RJ)],
}
DASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)


# v1: dashboard_routes.py:11255 — V2: início igual, só os ramos de execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA, recursal_RJ, controle_processo_NG, controle_processo_LA, publicacoes_NG, publicacoes_LA, publicacoes_RJ
async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards
    dashboard_name: str,
    from_date: Optional[date],
    to_date: Optional[date],
    leitor: Optional[Union[str, List[str]]] = None,
    materia: Optional[Union[str, List[str]]] = None,
    documento: Optional[str] = None,
    tribunal: Optional[str] = None,
    orgao: Optional[str] = None,
    atividade_agendamento: Optional[str] = None,
    setor_agendamento: Optional[str] = None,
    status_agendamento: Optional[str] = None,
    fase: Optional[str] = None,
    subfase: Optional[Any] = None,
    tipo_acao_execucao_acordos: Optional[str] = None,
    tipo_sentenca_execucao_acordos: Optional[str] = None,
    ano_ajuizamento_execucao_acordos: Optional[str] = None,
    ano_ajuizamento_execucao: Optional[str] = None,
    diligencia_tipo_execucao: Optional[str] = None,
    diligencia_colaborador_execucao: Optional[str] = None,
    uf_execucao_acordos_ng: Optional[List[str]] = None,
    comarca_execucao_acordos_ng: Optional[List[str]] = None,
    uf_execucao_acordos_la: Optional[List[str]] = None,
    comarca_execucao_acordos_la: Optional[List[str]] = None,
    uf_execucao_acordos_rj: Optional[List[str]] = None,
    comarca_execucao_acordos_rj: Optional[List[str]] = None,
    uf_execucao_ng: Optional[List[str]] = None,
    comarca_execucao_ng: Optional[List[str]] = None,
    comarca_execucao_la: Optional[List[str]] = None,
    uf_execucao_la: Optional[List[str]] = None,
    uf_execucao_rj: Optional[List[str]] = None,
    comarca_execucao_rj: Optional[List[str]] = None,
    numero_processo_execucao_acordos: Optional[str] = None,
    diligencia_tipo_execucao_acordos: Optional[str] = None,
    diligencia_colaborador_execucao_acordos: Optional[str] = None,
    situacao: Optional[str] = None,
    uf_controle_processo_ng: Optional[List[str]] = None,
    recursal_la_filtros: Optional[RecursalLAFiltros] = None,
    recursal_atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    execucao_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    execucao_acordos_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
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
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    filtered_data: Dict[str, List] = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in all_data.items()
    }
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
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
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "execucao":
        materia_filtro = _filtro_multi(materia)
        subfase_filtro = _filtro_multi(subfase)
        ano_ajuizamento_filtro = (
            str(ano_ajuizamento_execucao).strip()
            if ano_ajuizamento_execucao and str(ano_ajuizamento_execucao).strip()
            else None
        )
        diligencia_tipo_filtro_execucao = (
            str(diligencia_tipo_execucao).strip()
            if diligencia_tipo_execucao and str(diligencia_tipo_execucao).strip()
            else None
        )
        diligencia_colaborador_filtro_execucao = (
            str(diligencia_colaborador_execucao).strip()
            if diligencia_colaborador_execucao and str(diligencia_colaborador_execucao).strip()
            else None
        )
        uf_filtro_execucao_ng = (
            [str(u).strip().upper() for u in uf_execucao_ng if str(u).strip()]
            if uf_execucao_ng
            else None
        )
        comarca_filtro_execucao_ng = (
            [str(c).strip() for c in comarca_execucao_ng if str(c).strip()]
            if comarca_execucao_ng
            else None
        )
        # Opções de UF/Comarca vêm da base sem NENHUM filtro (nem materia/subfase/ano/uf/
        # comarca), para a lista de opções não encolher conforme o usuário filtra — mesmo
        # padrão de `execucao_acordos_NG` (get_opcoes_uf_execucao_acordos).
        uf_opcoes_execucao_ng = get_opcoes_uf_execucao(_a("execucao"))
        comarca_opcoes_execucao_ng = get_opcoes_comarca_execucao(_a("execucao"))
        materia_opcoes_execucao_ng = get_opcoes_materia_execucao(_a("execucao"))
        subfase_opcoes_execucao_ng = get_opcoes_subfase_execucao(_a("execucao"))
        execucao_rows = filter_execucao_por_comarca(
            filter_execucao_por_uf(
                filter_execucao_por_ano_ajuizamento(
                    filter_execucao_por_subfase(
                        filter_execucao_por_materia(_f("execucao"), materia_filtro),
                        subfase_filtro,
                    ),
                    ano_ajuizamento_filtro,
                ),
                uf_filtro_execucao_ng,
            ),
            comarca_filtro_execucao_ng,
        )
        all_execucao_rows = filter_execucao_por_comarca(
            filter_execucao_por_uf(
                filter_execucao_por_ano_ajuizamento(
                    filter_execucao_por_subfase(
                        filter_execucao_por_materia(_a("execucao"), materia_filtro),
                        subfase_filtro,
                    ),
                    ano_ajuizamento_filtro,
                ),
                uf_filtro_execucao_ng,
            ),
            comarca_filtro_execucao_ng,
        )
        stats, charts = _build_execucao_stats(
            execucao=execucao_rows,
            all_execucao=all_execucao_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_execucao_NG"),
            execucao_atividades_filtros=execucao_atividades_filtros,
            diligencia_tipo_filtro=diligencia_tipo_filtro_execucao,
            diligencia_colaborador_filtro=diligencia_colaborador_filtro_execucao,
        )
        stats["execucao_materia_filtro"] = materia_filtro
        stats["execucao_subfase_filtro"] = subfase_filtro
        stats["execucao_ano_ajuizamento_filtro"] = ano_ajuizamento_filtro
        stats["execucao_diligencia_tipo_filtro_NG"] = diligencia_tipo_filtro_execucao
        stats["execucao_diligencia_colaborador_filtro_NG"] = diligencia_colaborador_filtro_execucao
        stats["execucao_uf_filtro_NG"] = uf_filtro_execucao_ng
        stats["execucao_uf_opcoes_NG"] = uf_opcoes_execucao_ng
        stats["execucao_comarca_filtro_NG"] = comarca_filtro_execucao_ng
        stats["execucao_comarca_opcoes_NG"] = comarca_opcoes_execucao_ng
        stats["execucao_materia_opcoes_NG"] = materia_opcoes_execucao_ng
        stats["execucao_subfase_opcoes_NG"] = subfase_opcoes_execucao_ng
        logger.info("Dashboard 'execucao' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="execucao", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "execucao_RJ":
        materia_filtro = _filtro_multi(materia)
        subfase_filtro = _filtro_multi(subfase)
        ano_ajuizamento_filtro = (
            str(ano_ajuizamento_execucao).strip()
            if ano_ajuizamento_execucao and str(ano_ajuizamento_execucao).strip()
            else None
        )
        diligencia_tipo_filtro_execucao = (
            str(diligencia_tipo_execucao).strip()
            if diligencia_tipo_execucao and str(diligencia_tipo_execucao).strip()
            else None
        )
        diligencia_colaborador_filtro_execucao = (
            str(diligencia_colaborador_execucao).strip()
            if diligencia_colaborador_execucao and str(diligencia_colaborador_execucao).strip()
            else None
        )
        uf_filtro_execucao_rj = (
            [str(u).strip().upper() for u in uf_execucao_rj if str(u).strip()]
            if uf_execucao_rj
            else None
        )
        comarca_filtro_execucao_rj = (
            [str(c).strip() for c in comarca_execucao_rj if str(c).strip()]
            if comarca_execucao_rj
            else None
        )
        # Opções de UF/Comarca vêm da base sem NENHUM filtro (nem materia/subfase/ano/uf/
        # comarca), para a lista de opções não encolher conforme o usuário filtra — mesmo
        # padrão de `execucao`.
        uf_opcoes_execucao_rj = get_opcoes_uf_execucao_RJ(_a("execucao_RJ"))
        comarca_opcoes_execucao_rj = get_opcoes_comarca_execucao_RJ(_a("execucao_RJ"))
        materia_opcoes_execucao_rj = get_opcoes_materia_execucao_RJ(_a("execucao_RJ"))
        subfase_opcoes_execucao_rj = get_opcoes_subfase_execucao_RJ(_a("execucao_RJ"))
        execucao_rows = filter_execucao_RJ_por_comarca(
            filter_execucao_RJ_por_uf(
                filter_execucao_RJ_por_ano_ajuizamento(
                    filter_execucao_RJ_por_subfase(
                        filter_execucao_RJ_por_materia(_f("execucao_RJ"), materia_filtro),
                        subfase_filtro,
                    ),
                    ano_ajuizamento_filtro,
                ),
                uf_filtro_execucao_rj,
            ),
            comarca_filtro_execucao_rj,
        )
        all_execucao_rows = filter_execucao_RJ_por_comarca(
            filter_execucao_RJ_por_uf(
                filter_execucao_RJ_por_ano_ajuizamento(
                    filter_execucao_RJ_por_subfase(
                        filter_execucao_RJ_por_materia(_a("execucao_RJ"), materia_filtro),
                        subfase_filtro,
                    ),
                    ano_ajuizamento_filtro,
                ),
                uf_filtro_execucao_rj,
            ),
            comarca_filtro_execucao_rj,
        )
        stats, charts = _build_execucao_RJ_stats(
            execucao=execucao_rows,
            all_execucao=all_execucao_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_execucao_RJ"),
            execucao_atividades_filtros=execucao_atividades_filtros,
            diligencia_tipo_filtro=diligencia_tipo_filtro_execucao,
            diligencia_colaborador_filtro=diligencia_colaborador_filtro_execucao,
        )
        stats["execucao_materia_filtro_RJ"] = materia_filtro
        stats["execucao_subfase_filtro_RJ"] = subfase_filtro
        stats["execucao_ano_ajuizamento_filtro_RJ"] = ano_ajuizamento_filtro
        stats["execucao_diligencia_tipo_filtro_RJ"] = diligencia_tipo_filtro_execucao
        stats["execucao_diligencia_colaborador_filtro_RJ"] = diligencia_colaborador_filtro_execucao
        stats["execucao_uf_filtro_RJ"] = uf_filtro_execucao_rj
        stats["execucao_uf_opcoes_RJ"] = uf_opcoes_execucao_rj
        stats["execucao_comarca_filtro_RJ"] = comarca_filtro_execucao_rj
        stats["execucao_comarca_opcoes_RJ"] = comarca_opcoes_execucao_rj
        stats["execucao_materia_opcoes_RJ"] = materia_opcoes_execucao_rj
        stats["execucao_subfase_opcoes_RJ"] = subfase_opcoes_execucao_rj
        logger.info("Dashboard 'execucao_RJ' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="execucao_RJ", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "execucao_acordos_NG":
        materia_filtro = _filtro_multi(materia)
        subfase_filtro = (
            [str(s).strip() for s in subfase if str(s).strip()]
            if isinstance(subfase, list)
            else (str(subfase).strip() if subfase and str(subfase).strip() else None)
        )
        tipo_acao_filtro = (
            str(tipo_acao_execucao_acordos).strip()
            if tipo_acao_execucao_acordos and str(tipo_acao_execucao_acordos).strip()
            else None
        )
        sentenca_filtro_acordos_ng = (
            str(tipo_sentenca_execucao_acordos).strip()
            if tipo_sentenca_execucao_acordos and str(tipo_sentenca_execucao_acordos).strip()
            else None
        )
        uf_filtro_acordos_ng = (
            [str(u).strip().upper() for u in uf_execucao_acordos_ng if str(u).strip()]
            if uf_execucao_acordos_ng
            else None
        )
        ano_ajuizamento_filtro = (
            str(ano_ajuizamento_execucao_acordos).strip()
            if ano_ajuizamento_execucao_acordos and str(ano_ajuizamento_execucao_acordos).strip()
            else None
        )
        processo_filtro_acordos_ng = (
            str(numero_processo_execucao_acordos).strip()
            if numero_processo_execucao_acordos and str(numero_processo_execucao_acordos).strip()
            else None
        )
        diligencia_tipo_filtro_acordos_ng = (
            str(diligencia_tipo_execucao_acordos).strip()
            if diligencia_tipo_execucao_acordos and str(diligencia_tipo_execucao_acordos).strip()
            else None
        )
        diligencia_colaborador_filtro_acordos_ng = (
            str(diligencia_colaborador_execucao_acordos).strip()
            if diligencia_colaborador_execucao_acordos and str(diligencia_colaborador_execucao_acordos).strip()
            else None
        )
        comarca_filtro_acordos_ng = (
            [str(c).strip() for c in comarca_execucao_acordos_ng if str(c).strip()]
            if comarca_execucao_acordos_ng
            else None
        )
        uf_opcoes_acordos_ng = get_opcoes_uf_execucao_acordos(_a("execucao_acordos_NG"))
        comarca_opcoes_acordos_ng = get_opcoes_comarca_execucao_acordos(_a("execucao_acordos_NG"))
        materia_opcoes_acordos_ng = get_opcoes_materia_execucao_acordos(_a("execucao_acordos_NG"))
        subfase_opcoes_acordos_ng = get_opcoes_subfase_execucao_acordos(_a("execucao_acordos_NG"))
        execucao_acordos_rows = filter_execucao_acordos_por_processo(
            filter_execucao_acordos_por_comarca(
                filter_execucao_acordos_por_ano_ajuizamento(
                    filter_execucao_acordos_por_uf(
                        filter_execucao_acordos_por_sentenca(
                            filter_execucao_acordos_por_tipo_acao(
                                filter_execucao_acordos_por_subfase(
                                    filter_execucao_acordos_por_materia(_f("execucao_acordos_NG"), materia_filtro),
                                    subfase_filtro,
                                ),
                                tipo_acao_filtro,
                            ),
                            sentenca_filtro_acordos_ng,
                        ),
                        uf_filtro_acordos_ng,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_acordos_ng,
            ),
            processo_filtro_acordos_ng,
        )
        all_execucao_acordos_rows = filter_execucao_acordos_por_processo(
            filter_execucao_acordos_por_comarca(
                filter_execucao_acordos_por_ano_ajuizamento(
                    filter_execucao_acordos_por_uf(
                        filter_execucao_acordos_por_sentenca(
                            filter_execucao_acordos_por_tipo_acao(
                                filter_execucao_acordos_por_subfase(
                                    filter_execucao_acordos_por_materia(_a("execucao_acordos_NG"), materia_filtro),
                                    subfase_filtro,
                                ),
                                tipo_acao_filtro,
                            ),
                            sentenca_filtro_acordos_ng,
                        ),
                        uf_filtro_acordos_ng,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_acordos_ng,
            ),
            processo_filtro_acordos_ng,
        )
        filtro_processo_acordos_ativo = bool(
            materia_filtro or subfase_filtro or tipo_acao_filtro or sentenca_filtro_acordos_ng
            or uf_filtro_acordos_ng or ano_ajuizamento_filtro or processo_filtro_acordos_ng
            or comarca_filtro_acordos_ng
        )
        processo_ids_ativos_acordos = (
            frozenset(
                pid for r in all_execucao_acordos_rows
                if (pid := (r.get("id") or r.get("ID"))) is not None
            )
            if filtro_processo_acordos_ativo
            else None
        )
        stats, charts = _build_execucao_acordos_stats(
            execucao=execucao_acordos_rows,
            all_execucao=all_execucao_acordos_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_execucao_acordos_NG"),
            execucao_acordos_atividades_filtros=execucao_acordos_atividades_filtros,
            processo_ids_ativos=processo_ids_ativos_acordos,
            diligencia_tipo_filtro=diligencia_tipo_filtro_acordos_ng,
            diligencia_colaborador_filtro=diligencia_colaborador_filtro_acordos_ng,
        )
        stats["execucao_acordos_materia_filtro_NG"] = materia_filtro
        stats["execucao_acordos_subfase_filtro_NG"] = subfase_filtro
        stats["execucao_acordos_tipo_acao_filtro_NG"] = tipo_acao_filtro
        stats["execucao_acordos_sentenca_filtro_NG"] = sentenca_filtro_acordos_ng
        stats["execucao_acordos_uf_filtro_NG"] = uf_filtro_acordos_ng
        stats["execucao_acordos_uf_opcoes_NG"] = uf_opcoes_acordos_ng
        stats["execucao_acordos_ano_ajuizamento_filtro_NG"] = ano_ajuizamento_filtro
        stats["execucao_acordos_processo_filtro_NG"] = processo_filtro_acordos_ng
        stats["execucao_acordos_diligencia_tipo_filtro_NG"] = diligencia_tipo_filtro_acordos_ng
        stats["execucao_acordos_diligencia_colaborador_filtro_NG"] = diligencia_colaborador_filtro_acordos_ng
        stats["execucao_acordos_comarca_filtro_NG"] = comarca_filtro_acordos_ng
        stats["execucao_acordos_comarca_opcoes_NG"] = comarca_opcoes_acordos_ng
        stats["execucao_acordos_materia_opcoes_NG"] = materia_opcoes_acordos_ng
        stats["execucao_acordos_subfase_opcoes_NG"] = subfase_opcoes_acordos_ng
        stats["total_fechamento_acordos_NG"] = get_total_processos_fechamento_acordo(
            _a("execucao_acordos_NG"),
            _a("agendamentos_fechamento_acordos_NG"),
        )
        charts["fechamento_acordo_por_subfase_NG"] = [
            ChartDataPoint(**x)
            for x in group_fechamento_acordo_por_subfase(_a("execucao_acordos_NG"))
        ]
        charts["valor_fechamento_acordo_por_subfase_NG"] = [
            ChartDataPoint(**x)
            for x in group_valor_fechamento_acordo_por_subfase(_a("execucao_acordos_NG"))
        ]
        charts["execucao_acordos_lista_entrada_NG"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_lista_entrada(
                all_execucao_acordos_rows, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_lista_saida_NG"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_lista_saida(
                all_execucao_acordos_rows, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_lista_total_NG"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_lista_total(all_execucao_acordos_rows)
        ]
        logger.info("Dashboard 'execucao_acordos_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="execucao_acordos_NG", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "execucao_acordos_LA":
        materia_filtro = _filtro_multi(materia)
        subfase_filtro = _filtro_multi(subfase)
        tipo_acao_filtro = (
            str(tipo_acao_execucao_acordos).strip()
            if tipo_acao_execucao_acordos and str(tipo_acao_execucao_acordos).strip()
            else None
        )
        sentenca_filtro_acordos_la = (
            str(tipo_sentenca_execucao_acordos).strip()
            if tipo_sentenca_execucao_acordos and str(tipo_sentenca_execucao_acordos).strip()
            else None
        )
        uf_filtro_acordos_la = (
            [str(u).strip().upper() for u in uf_execucao_acordos_la if str(u).strip()]
            if uf_execucao_acordos_la
            else None
        )
        ano_ajuizamento_filtro = (
            str(ano_ajuizamento_execucao_acordos).strip()
            if ano_ajuizamento_execucao_acordos and str(ano_ajuizamento_execucao_acordos).strip()
            else None
        )
        processo_filtro_acordos_la = (
            str(numero_processo_execucao_acordos).strip()
            if numero_processo_execucao_acordos and str(numero_processo_execucao_acordos).strip()
            else None
        )
        diligencia_tipo_filtro_acordos_la = (
            str(diligencia_tipo_execucao_acordos).strip()
            if diligencia_tipo_execucao_acordos and str(diligencia_tipo_execucao_acordos).strip()
            else None
        )
        diligencia_colaborador_filtro_acordos_la = (
            str(diligencia_colaborador_execucao_acordos).strip()
            if diligencia_colaborador_execucao_acordos and str(diligencia_colaborador_execucao_acordos).strip()
            else None
        )
        comarca_filtro_acordos_la = (
            [str(c).strip() for c in comarca_execucao_acordos_la if str(c).strip()]
            if comarca_execucao_acordos_la
            else None
        )
        uf_opcoes_acordos_la = get_opcoes_uf_execucao_acordos_LA(_a("execucao_acordos_LA"))
        comarca_opcoes_acordos_la = get_opcoes_comarca_execucao_acordos_LA(_a("execucao_acordos_LA"))
        materia_opcoes_acordos_la = get_opcoes_materia_execucao_acordos_LA(_a("execucao_acordos_LA"))
        subfase_opcoes_acordos_la = get_opcoes_subfase_execucao_acordos_LA(_a("execucao_acordos_LA"))
        execucao_acordos_rows = filter_execucao_acordos_LA_por_processo(
            filter_execucao_acordos_LA_por_comarca(
                filter_execucao_acordos_LA_por_ano_ajuizamento(
                    filter_execucao_acordos_LA_por_uf(
                        filter_execucao_acordos_LA_por_sentenca(
                            filter_execucao_acordos_LA_por_tipo_acao(
                                filter_execucao_acordos_LA_por_subfase(
                                    filter_execucao_acordos_LA_por_materia(_f("execucao_acordos_LA"), materia_filtro),
                                    subfase_filtro,
                                ),
                                tipo_acao_filtro,
                            ),
                            sentenca_filtro_acordos_la,
                        ),
                        uf_filtro_acordos_la,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_acordos_la,
            ),
            processo_filtro_acordos_la,
        )
        all_execucao_acordos_rows = filter_execucao_acordos_LA_por_processo(
            filter_execucao_acordos_LA_por_comarca(
                filter_execucao_acordos_LA_por_ano_ajuizamento(
                    filter_execucao_acordos_LA_por_uf(
                        filter_execucao_acordos_LA_por_sentenca(
                            filter_execucao_acordos_LA_por_tipo_acao(
                                filter_execucao_acordos_LA_por_subfase(
                                    filter_execucao_acordos_LA_por_materia(_a("execucao_acordos_LA"), materia_filtro),
                                    subfase_filtro,
                                ),
                                tipo_acao_filtro,
                            ),
                            sentenca_filtro_acordos_la,
                        ),
                        uf_filtro_acordos_la,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_acordos_la,
            ),
            processo_filtro_acordos_la,
        )
        filtro_processo_acordos_ativo = bool(
            materia_filtro or subfase_filtro or tipo_acao_filtro or sentenca_filtro_acordos_la
            or uf_filtro_acordos_la or ano_ajuizamento_filtro or processo_filtro_acordos_la
            or comarca_filtro_acordos_la
        )
        processo_ids_ativos_acordos = (
            frozenset(
                pid for r in all_execucao_acordos_rows
                if (pid := (r.get("id") or r.get("ID"))) is not None
            )
            if filtro_processo_acordos_ativo
            else None
        )
        stats, charts = _build_execucao_acordos_LA_stats(
            execucao=execucao_acordos_rows,
            all_execucao=all_execucao_acordos_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_execucao_acordos_LA"),
            execucao_acordos_atividades_filtros=execucao_acordos_atividades_filtros,
            processo_ids_ativos=processo_ids_ativos_acordos,
            diligencia_tipo_filtro=diligencia_tipo_filtro_acordos_la,
            diligencia_colaborador_filtro=diligencia_colaborador_filtro_acordos_la,
        )
        stats["execucao_acordos_materia_filtro_LA"] = materia_filtro
        stats["execucao_acordos_subfase_filtro_LA"] = subfase_filtro
        stats["execucao_acordos_tipo_acao_filtro_LA"] = tipo_acao_filtro
        stats["execucao_acordos_sentenca_filtro_LA"] = sentenca_filtro_acordos_la
        stats["execucao_acordos_uf_filtro_LA"] = uf_filtro_acordos_la
        stats["execucao_acordos_uf_opcoes_LA"] = uf_opcoes_acordos_la
        stats["execucao_acordos_ano_ajuizamento_filtro_LA"] = ano_ajuizamento_filtro
        stats["execucao_acordos_processo_filtro_LA"] = processo_filtro_acordos_la
        stats["execucao_acordos_diligencia_tipo_filtro_LA"] = diligencia_tipo_filtro_acordos_la
        stats["execucao_acordos_diligencia_colaborador_filtro_LA"] = diligencia_colaborador_filtro_acordos_la
        stats["execucao_acordos_comarca_filtro_LA"] = comarca_filtro_acordos_la
        stats["execucao_acordos_comarca_opcoes_LA"] = comarca_opcoes_acordos_la
        stats["execucao_acordos_materia_opcoes_LA"] = materia_opcoes_acordos_la
        stats["execucao_acordos_subfase_opcoes_LA"] = subfase_opcoes_acordos_la
        stats["total_fechamento_acordos_LA"] = get_total_processos_fechamento_acordo_LA(
            _a("execucao_acordos_LA"),
            _a("agendamentos_fechamento_acordos_LA"),
        )
        charts["fechamento_acordo_por_subfase_LA"] = [
            ChartDataPoint(**x)
            for x in group_fechamento_acordo_por_subfase_LA(_a("execucao_acordos_LA"))
        ]
        charts["valor_fechamento_acordo_por_subfase_LA"] = [
            ChartDataPoint(**x)
            for x in group_valor_fechamento_acordo_por_subfase_LA(_a("execucao_acordos_LA"))
        ]
        charts["execucao_acordos_lista_entrada_LA"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_LA_lista_entrada(
                all_execucao_acordos_rows, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_lista_saida_LA"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_LA_lista_saida(
                all_execucao_acordos_rows, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_lista_total_LA"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_LA_lista_total(all_execucao_acordos_rows)
        ]
        logger.info("Dashboard 'execucao_acordos_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="execucao_acordos_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "execucao_acordos_RJ":
        materia_filtro = _filtro_multi(materia)
        subfase_filtro = _filtro_multi(subfase)
        tipo_acao_filtro = (
            str(tipo_acao_execucao_acordos).strip()
            if tipo_acao_execucao_acordos and str(tipo_acao_execucao_acordos).strip()
            else None
        )
        sentenca_filtro_acordos_rj = (
            str(tipo_sentenca_execucao_acordos).strip()
            if tipo_sentenca_execucao_acordos and str(tipo_sentenca_execucao_acordos).strip()
            else None
        )
        uf_filtro_acordos_rj = (
            [str(u).strip().upper() for u in uf_execucao_acordos_rj if str(u).strip()]
            if uf_execucao_acordos_rj
            else None
        )
        ano_ajuizamento_filtro = (
            str(ano_ajuizamento_execucao_acordos).strip()
            if ano_ajuizamento_execucao_acordos and str(ano_ajuizamento_execucao_acordos).strip()
            else None
        )
        processo_filtro_acordos_rj = (
            str(numero_processo_execucao_acordos).strip()
            if numero_processo_execucao_acordos and str(numero_processo_execucao_acordos).strip()
            else None
        )
        diligencia_tipo_filtro_acordos_rj = (
            str(diligencia_tipo_execucao_acordos).strip()
            if diligencia_tipo_execucao_acordos and str(diligencia_tipo_execucao_acordos).strip()
            else None
        )
        diligencia_colaborador_filtro_acordos_rj = (
            str(diligencia_colaborador_execucao_acordos).strip()
            if diligencia_colaborador_execucao_acordos and str(diligencia_colaborador_execucao_acordos).strip()
            else None
        )
        comarca_filtro_acordos_rj = (
            [str(c).strip() for c in comarca_execucao_acordos_rj if str(c).strip()]
            if comarca_execucao_acordos_rj
            else None
        )
        uf_opcoes_acordos_rj = get_opcoes_uf_execucao_acordos_RJ(_a("execucao_acordos_RJ"))
        comarca_opcoes_acordos_rj = get_opcoes_comarca_execucao_acordos_RJ(_a("execucao_acordos_RJ"))
        materia_opcoes_acordos_rj = get_opcoes_materia_execucao_acordos_RJ(_a("execucao_acordos_RJ"))
        subfase_opcoes_acordos_rj = get_opcoes_subfase_execucao_acordos_RJ(_a("execucao_acordos_RJ"))
        execucao_acordos_rows = filter_execucao_acordos_RJ_por_processo(
            filter_execucao_acordos_RJ_por_comarca(
                filter_execucao_acordos_RJ_por_ano_ajuizamento(
                    filter_execucao_acordos_RJ_por_uf(
                        filter_execucao_acordos_RJ_por_sentenca(
                            filter_execucao_acordos_RJ_por_tipo_acao(
                                filter_execucao_acordos_RJ_por_subfase(
                                    filter_execucao_acordos_RJ_por_materia(_f("execucao_acordos_RJ"), materia_filtro),
                                    subfase_filtro,
                                ),
                                tipo_acao_filtro,
                            ),
                            sentenca_filtro_acordos_rj,
                        ),
                        uf_filtro_acordos_rj,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_acordos_rj,
            ),
            processo_filtro_acordos_rj,
        )
        all_execucao_acordos_rows = filter_execucao_acordos_RJ_por_processo(
            filter_execucao_acordos_RJ_por_comarca(
                filter_execucao_acordos_RJ_por_ano_ajuizamento(
                    filter_execucao_acordos_RJ_por_uf(
                        filter_execucao_acordos_RJ_por_sentenca(
                            filter_execucao_acordos_RJ_por_tipo_acao(
                                filter_execucao_acordos_RJ_por_subfase(
                                    filter_execucao_acordos_RJ_por_materia(_a("execucao_acordos_RJ"), materia_filtro),
                                    subfase_filtro,
                                ),
                                tipo_acao_filtro,
                            ),
                            sentenca_filtro_acordos_rj,
                        ),
                        uf_filtro_acordos_rj,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_acordos_rj,
            ),
            processo_filtro_acordos_rj,
        )
        filtro_processo_acordos_ativo = bool(
            materia_filtro or subfase_filtro or tipo_acao_filtro or sentenca_filtro_acordos_rj
            or uf_filtro_acordos_rj or ano_ajuizamento_filtro or processo_filtro_acordos_rj
            or comarca_filtro_acordos_rj
        )
        processo_ids_ativos_acordos = (
            frozenset(
                pid for r in all_execucao_acordos_rows
                if (pid := (r.get("id") or r.get("ID"))) is not None
            )
            if filtro_processo_acordos_ativo
            else None
        )
        stats, charts = _build_execucao_acordos_RJ_stats(
            execucao=execucao_acordos_rows,
            all_execucao=all_execucao_acordos_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_execucao_acordos_RJ"),
            execucao_acordos_atividades_filtros=execucao_acordos_atividades_filtros,
            processo_ids_ativos=processo_ids_ativos_acordos,
            diligencia_tipo_filtro=diligencia_tipo_filtro_acordos_rj,
            diligencia_colaborador_filtro=diligencia_colaborador_filtro_acordos_rj,
        )
        stats["execucao_acordos_materia_filtro_RJ"] = materia_filtro
        stats["execucao_acordos_subfase_filtro_RJ"] = subfase_filtro
        stats["execucao_acordos_tipo_acao_filtro_RJ"] = tipo_acao_filtro
        stats["execucao_acordos_sentenca_filtro_RJ"] = sentenca_filtro_acordos_rj
        stats["execucao_acordos_uf_filtro_RJ"] = uf_filtro_acordos_rj
        stats["execucao_acordos_uf_opcoes_RJ"] = uf_opcoes_acordos_rj
        stats["execucao_acordos_ano_ajuizamento_filtro_RJ"] = ano_ajuizamento_filtro
        stats["execucao_acordos_processo_filtro_RJ"] = processo_filtro_acordos_rj
        stats["execucao_acordos_diligencia_tipo_filtro_RJ"] = diligencia_tipo_filtro_acordos_rj
        stats["execucao_acordos_diligencia_colaborador_filtro_RJ"] = diligencia_colaborador_filtro_acordos_rj
        stats["execucao_acordos_comarca_filtro_RJ"] = comarca_filtro_acordos_rj
        stats["execucao_acordos_comarca_opcoes_RJ"] = comarca_opcoes_acordos_rj
        stats["execucao_acordos_materia_opcoes_RJ"] = materia_opcoes_acordos_rj
        stats["execucao_acordos_subfase_opcoes_RJ"] = subfase_opcoes_acordos_rj
        stats["total_fechamento_acordos_RJ"] = get_total_processos_fechamento_acordo_RJ(
            _a("execucao_acordos_RJ"),
            _a("agendamentos_fechamento_acordos_RJ"),
        )
        charts["fechamento_acordo_por_subfase_RJ"] = [
            ChartDataPoint(**x)
            for x in group_fechamento_acordo_por_subfase_RJ(_a("execucao_acordos_RJ"))
        ]
        charts["valor_fechamento_acordo_por_subfase_RJ"] = [
            ChartDataPoint(**x)
            for x in group_valor_fechamento_acordo_por_subfase_RJ(_a("execucao_acordos_RJ"))
        ]
        charts["execucao_acordos_lista_entrada_RJ"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_RJ_lista_entrada(
                all_execucao_acordos_rows, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_lista_saida_RJ"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_RJ_lista_saida(
                all_execucao_acordos_rows, from_date=from_date, to_date=to_date
            )
        ]
        charts["execucao_acordos_lista_total_RJ"] = [
            ExecucaoAcordosListaRow(**x)
            for x in list_execucao_acordos_RJ_lista_total(all_execucao_acordos_rows)
        ]
        logger.info("Dashboard 'execucao_acordos_RJ' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="execucao_acordos_RJ", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "execucao_LA":
        materia_filtro = _filtro_multi(materia)
        subfase_filtro = _filtro_multi(subfase)
        ano_ajuizamento_filtro = (
            str(ano_ajuizamento_execucao).strip()
            if ano_ajuizamento_execucao and str(ano_ajuizamento_execucao).strip()
            else None
        )
        comarca_filtro_execucao_la = (
            [str(c).strip() for c in comarca_execucao_la if str(c).strip()]
            if comarca_execucao_la
            else None
        )
        uf_filtro_execucao_la = (
            [str(u).strip().upper() for u in uf_execucao_la if str(u).strip()]
            if uf_execucao_la
            else None
        )
        # Opções de Comarca/UF vêm da base sem NENHUM filtro (nem materia/subfase/ano/
        # comarca/uf), para a lista de opções não encolher conforme o usuário filtra.
        comarca_opcoes_execucao_la = get_opcoes_comarca_execucao_LA(_a("execucao_LA"))
        uf_opcoes_execucao_la = get_opcoes_uf_execucao_LA(_a("execucao_LA"))
        materia_opcoes_execucao_la = get_opcoes_materia_execucao_LA(_a("execucao_LA"))
        subfase_opcoes_execucao_la = get_opcoes_subfase_execucao_LA(_a("execucao_LA"))
        execucao_rows = filter_execucao_LA_por_uf(
            filter_execucao_LA_por_comarca(
                filter_execucao_LA_por_ano_ajuizamento(
                    filter_execucao_LA_por_subfase(
                        filter_execucao_LA_por_materia(_f("execucao_LA"), materia_filtro),
                        subfase_filtro,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_execucao_la,
            ),
            uf_filtro_execucao_la,
        )
        all_execucao_rows = filter_execucao_LA_por_uf(
            filter_execucao_LA_por_comarca(
                filter_execucao_LA_por_ano_ajuizamento(
                    filter_execucao_LA_por_subfase(
                        filter_execucao_LA_por_materia(_a("execucao_LA"), materia_filtro),
                        subfase_filtro,
                    ),
                    ano_ajuizamento_filtro,
                ),
                comarca_filtro_execucao_la,
            ),
            uf_filtro_execucao_la,
        )
        stats, charts = _build_execucao_LA_stats(
            execucao=execucao_rows,
            all_execucao=all_execucao_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_execucao_LA"),
            execucao_atividades_filtros=execucao_atividades_filtros,
        )
        stats["execucao_materia_filtro_LA"] = materia_filtro
        stats["execucao_subfase_filtro_LA"] = subfase_filtro
        stats["execucao_ano_ajuizamento_filtro_LA"] = ano_ajuizamento_filtro
        stats["execucao_comarca_filtro_LA"] = comarca_filtro_execucao_la
        stats["execucao_comarca_opcoes_LA"] = comarca_opcoes_execucao_la
        stats["execucao_uf_filtro_LA"] = uf_filtro_execucao_la
        stats["execucao_uf_opcoes_LA"] = uf_opcoes_execucao_la
        stats["execucao_materia_opcoes_LA"] = materia_opcoes_execucao_la
        stats["execucao_subfase_opcoes_LA"] = subfase_opcoes_execucao_la
        logger.info("Dashboard 'execucao_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="execucao_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "recursal_LA":
        atividades_catalogo_la = _a("atividades_setor_recursos_LA")
        recursal_rows = await _rows_recursal_la_filtradas(
            _a("recursal_LA"),
            recursal_la_filtros,
            recursal_atividades_recursos_filtros,
            from_date,
            to_date,
            agendamentos=_a("agendamentos_setor_recursos_LA"),
            atividades_catalogo=atividades_catalogo_la,
        )
        stats, charts = _build_recursal_LA_stats(
            all_recursal=recursal_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_recursos_LA"),
            atividades_recursos_filtros=recursal_atividades_recursos_filtros,
            atividades_catalogo=atividades_catalogo_la,
        )
        logger.info("Dashboard 'recursal_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="recursal_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "recursal_NG":
        atividades_catalogo_ng = _a("atividades_setor_recursos_NG")
        recursal_rows = await _rows_recursal_ng_filtradas(
            _a("recursal_NG"),
            recursal_la_filtros,
            recursal_atividades_recursos_filtros,
            from_date,
            to_date,
            agendamentos=_a("agendamentos_setor_recursos_NG"),
            atividades_catalogo=atividades_catalogo_ng,
        )
        stats, charts = _build_recursal_NG_stats(
            all_recursal=recursal_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_recursos_NG"),
            atividades_recursos_filtros=recursal_atividades_recursos_filtros,
            atividades_catalogo=atividades_catalogo_ng,
        )
        logger.info("Dashboard 'recursal_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="recursal_NG", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "recursal_RJ":
        atividades_catalogo_rj = _a("atividades_setor_recursos_RJ")
        recursal_rows = await _rows_recursal_rj_filtradas(
            _a("recursal_RJ"),
            recursal_la_filtros,
            recursal_atividades_recursos_filtros,
            from_date,
            to_date,
            agendamentos=_a("agendamentos_setor_recursos_RJ"),
            atividades_catalogo=atividades_catalogo_rj,
        )
        stats, charts = _build_recursal_RJ_stats(
            all_recursal=recursal_rows,
            from_date=from_date,
            to_date=to_date,
            agendamentos=_a("agendamentos_setor_recursos_RJ"),
            atividades_recursos_filtros=recursal_atividades_recursos_filtros,
            atividades_catalogo=atividades_catalogo_rj,
        )
        # Extintos · 2º Grau: no NG vêm do controle_processo_NG; o RJ calcula aqui
        # (todas as situações, inclui arquivado — mesma base do painel NG).
        stats.update(get_extintos_2g_recursal_RJ(
            _dedup_por_processo_id(_a("controle_processo_todas_situacoes")),
            from_date=from_date,
            to_date=to_date,
        ))
        logger.info("Dashboard 'recursal_RJ' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="recursal_RJ", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "controle_processo_LA":
        base = filter_controle_processo_por_situacao_LA(_f("controle_processo_LA"), situacao)
        _all_situacao_LA = filter_controle_processo_por_situacao_LA(_a("controle_processo_LA"), situacao)
        _recursal_base_LA = _dedup_por_processo_id(_a("controle_processo_todas_situacoes"))
        fase_filtro = str(fase).strip() if fase and str(fase).strip() else None
        subfase_items = group_controle_processo_por_subfase_na_fase_LA(base, fase_filtro)
        total_na_fase = int(sum(float(x["value"]) for x in subfase_items)) if fase_filtro else None
        if fase_filtro:
            _tempo_medio_por_subfase_LA = {
                item["name"]: item["value"]
                for item in get_tempo_medio_dias_por_subfase_LA(
                    _a("log_subfase_processual"), fase_filtro, situacao
                )
            }
            for _item in subfase_items:
                _item["tempo_medio_dias"] = _tempo_medio_por_subfase_LA.get(_item["name"])
        stats = {
            "total_controle_processo_LA": get_total_controle_processo_LA(base),
            "controle_processo_situacao_filtro_LA": (situacao or "ambos").strip().lower(),
            "controle_processo_fase_filtro_LA": fase_filtro,
            "controle_processo_total_na_fase_LA": total_na_fase,
            "controle_processo_qtd_subfases_na_fase_LA": (len(subfase_items) if fase_filtro else None),
            "controle_processo_fase_inicial_qtd_LA": get_total_controle_processo_fase_inicial_LA(base),
            "controle_processo_fase_inicial_valor_causa_LA": get_valor_causa_total_controle_processo_fase_inicial_LA(base),
            "controle_processo_fase_recursal_qtd_LA": get_total_controle_processo_fase_recursal_LA(base),
            "controle_processo_fase_recursal_valor_causa_LA": get_valor_causa_total_controle_processo_fase_recursal_LA(base),
            "controle_processo_fase_execucao_qtd_LA": get_total_controle_processo_fase_execucao_LA(base),
            "controle_processo_fase_execucao_valor_causa_execucao_LA": get_valor_causa_execucao_total_controle_processo_fase_execucao_LA(base),
            "controle_processo_fase_arquivado_procedente_qtd_LA": get_total_controle_processo_fase_arquivado_procedente_LA(base),
            "controle_processo_fase_arquivado_procedente_valor_causa_LA": get_valor_causa_total_controle_processo_fase_arquivado_procedente_LA(base),
            "controle_processo_fase_arquivado_improcedente_qtd_LA": get_total_controle_processo_fase_arquivado_improcedente_LA(base),
            "controle_processo_fase_arquivado_improcedente_valor_causa_LA": get_valor_causa_total_controle_processo_fase_arquivado_improcedente_LA(base),
            "controle_processo_fase_transito_julgado_qtd_LA": get_total_controle_processo_fase_transito_julgado_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_transito_julgado_valor_causa_LA": get_valor_causa_total_controle_processo_fase_transito_julgado_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_qtd_LA": get_total_extintos_com_merito_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_valor_causa_LA": get_valor_causa_total_extintos_com_merito_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_por_tipo_sentenca_LA": get_extintos_com_merito_por_tipo_sentenca_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_qtd_LA": get_total_extintos_com_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_valor_causa_LA": get_valor_causa_total_extintos_com_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_LA": get_extintos_com_merito_2g_por_tipo_sentenca_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_valor_causa_acordao_LA": get_valor_causa_acordao_total_extintos_com_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA": get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_qtd_LA": get_total_extintos_sem_merito_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_valor_causa_LA": get_valor_causa_total_extintos_sem_merito_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_qtd_LA": get_total_extintos_sem_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_valor_causa_LA": get_valor_causa_total_extintos_sem_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_LA": get_valor_causa_acordao_total_extintos_sem_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_taxa_provimento_2g_LA": get_taxa_provimento_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            # Recursal (painel "Extintos · 2º Grau"): todas as situações (inclui arquivado),
            # diferente do Controle de Processos, que respeita o filtro de situação (ativo/suspenso).
            "controle_processo_extintos_com_merito_2g_qtd_recursal_LA": get_total_extintos_com_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_LA": get_valor_causa_acordao_total_extintos_com_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_LA": get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_qtd_recursal_LA": get_total_extintos_sem_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_LA": get_valor_causa_acordao_total_extintos_sem_merito_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_taxa_provimento_2g_recursal_LA": get_taxa_provimento_2g_LA(_recursal_base_LA, from_date=from_date, to_date=to_date),
            "controle_processo_log_inicial_indeferida_qtd_LA": get_total_controle_processo_log_inicial_indeferida_LA(base),
            "controle_processo_log_inicial_indeferida_valor_causa_LA": get_valor_causa_total_controle_processo_log_inicial_indeferida_LA(base),
            "controle_processo_log_recursal_nao_provido_qtd_LA": get_total_controle_processo_log_recursal_nao_provido_LA(base),
            "controle_processo_log_recursal_nao_provido_valor_causa_LA": get_valor_causa_total_controle_processo_log_recursal_nao_provido_LA(base),
            "controle_processo_fase_inicial_media_dias_LA": get_media_tempo_dias_fase_inicial_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_media_dias_LA": get_media_tempo_dias_fase_recursal_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_media_dias_LA": get_media_tempo_dias_fase_execucao_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_inicial_mediana_dias_LA": get_mediana_tempo_dias_fase_inicial_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_mediana_dias_LA": get_mediana_tempo_dias_fase_recursal_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_mediana_dias_LA": get_mediana_tempo_dias_fase_execucao_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_inicial_comparativo_media_dias_LA": get_comparativo_media_tempo_dias_fase_inicial_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_comparativo_media_dias_LA": get_comparativo_media_tempo_dias_fase_recursal_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_comparativo_media_dias_LA": get_comparativo_media_tempo_dias_fase_execucao_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_inicial_comparativo_mediana_dias_LA": get_comparativo_mediana_tempo_dias_fase_inicial_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_comparativo_mediana_dias_LA": get_comparativo_mediana_tempo_dias_fase_recursal_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_comparativo_mediana_dias_LA": get_comparativo_mediana_tempo_dias_fase_execucao_LA(_all_situacao_LA, from_date=from_date, to_date=to_date),
        }
        charts = {
            "controle_processo_por_fase_LA": [ChartDataPoint(**x) for x in group_controle_processo_por_fase_LA(base)],
            "controle_processo_por_subfase_LA": [ChartDataPoint(**x) for x in subfase_items],
            "controle_processo_fase_inicial_media_dias_por_mes_LA": [ChartDataPoint(**x) for x in get_media_tempo_dias_fase_inicial_por_mes_LA(_all_situacao_LA)],
            "controle_processo_fase_recursal_media_dias_por_mes_LA": [ChartDataPoint(**x) for x in get_media_tempo_dias_fase_recursal_por_mes_LA(_all_situacao_LA)],
            "controle_processo_fase_execucao_media_dias_por_mes_LA": [ChartDataPoint(**x) for x in get_media_tempo_dias_fase_execucao_por_mes_LA(_all_situacao_LA)],
        }
        logger.info("Dashboard 'controle_processo_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="controle_processo_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "controle_processo_NG":
        uf_filtro_ng = [str(u).strip().upper() for u in uf_controle_processo_ng if str(u).strip()] if uf_controle_processo_ng else None
        _uf_opcoes_ng = get_opcoes_uf_NG(
            filter_controle_processo_por_situacao_NG(_a("controle_processo_NG"), situacao)
        )
        # Dedup por processo: o LEFT JOIN em adverso_processo gera 1 linha por parte adversa,
        # o que inflava contagens/valores das fases (ex.: Inicial 6.262 linhas = 5.589 processos).
        # Processos sem número (cadastro incompleto) ficam fora de tudo.
        base = _dedup_por_processo_id(filter_controle_processo_com_numero_NG(filter_controle_processo_por_uf_NG(
            filter_controle_processo_por_situacao_NG(_f("controle_processo_NG"), situacao), uf_filtro_ng
        )))
        _all_situacao_NG = _dedup_por_processo_id(filter_controle_processo_com_numero_NG(filter_controle_processo_por_uf_NG(
            filter_controle_processo_por_situacao_NG(_a("controle_processo_NG"), situacao), uf_filtro_ng
        )))
        _recursal_base_NG = _dedup_por_processo_id(_a("controle_processo_todas_situacoes"))
        fase_filtro = str(fase).strip() if fase and str(fase).strip() else None
        subfase_items = group_controle_processo_por_subfase_na_fase_NG(base, fase_filtro)
        total_na_fase = int(sum(float(x["value"]) for x in subfase_items)) if fase_filtro else None
        if fase_filtro:
            _tempo_medio_por_subfase_NG = {
                item["name"]: item["value"]
                for item in get_tempo_medio_dias_por_subfase_NG(
                    _a("log_subfase_processual"), fase_filtro, situacao
                )
            }
            for _item in subfase_items:
                _item["tempo_medio_dias"] = _tempo_medio_por_subfase_NG.get(_item["name"])
        stats = {
            "total_controle_processo_NG": get_total_controle_processo_NG(base),
            "controle_processo_valor_causa_total_NG": get_valor_causa_total_controle_processo_NG(base),
            "controle_processo_situacao_filtro_NG": (situacao or "ambos").strip().lower(),
            "controle_processo_uf_filtro_NG": uf_filtro_ng,
            "controle_processo_uf_opcoes_NG": _uf_opcoes_ng,
            "controle_processo_fase_filtro_NG": fase_filtro,
            "controle_processo_total_na_fase_NG": total_na_fase,
            "controle_processo_qtd_subfases_na_fase_NG": (len(subfase_items) if fase_filtro else None),
            "controle_processo_fase_inicial_qtd_NG": get_total_controle_processo_fase_inicial_NG(base),
            "controle_processo_fase_inicial_valor_causa_NG": get_valor_causa_total_controle_processo_fase_inicial_NG(base),
            "controle_processo_fase_recursal_qtd_NG": get_total_controle_processo_fase_recursal_NG(base),
            "controle_processo_fase_recursal_valor_causa_NG": get_valor_causa_total_controle_processo_fase_recursal_NG(base),
            "controle_processo_fase_execucao_qtd_NG": get_total_controle_processo_fase_execucao_NG(base),
            "controle_processo_fase_execucao_valor_causa_execucao_NG": get_valor_causa_execucao_total_controle_processo_fase_execucao_NG(base),
            "controle_processo_fase_arquivado_procedente_qtd_NG": get_total_controle_processo_fase_arquivado_procedente_NG(base),
            "controle_processo_fase_arquivado_procedente_valor_causa_NG": get_valor_causa_total_controle_processo_fase_arquivado_procedente_NG(base),
            "controle_processo_fase_arquivado_improcedente_qtd_NG": get_total_controle_processo_fase_arquivado_improcedente_NG(base),
            "controle_processo_fase_arquivado_improcedente_valor_causa_NG": get_valor_causa_total_controle_processo_fase_arquivado_improcedente_NG(base),
            "controle_processo_fase_transito_julgado_qtd_NG": get_total_controle_processo_fase_transito_julgado_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_transito_julgado_valor_causa_NG": get_valor_causa_total_controle_processo_fase_transito_julgado_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_qtd_NG": get_total_extintos_com_merito_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_valor_causa_NG": get_valor_causa_total_extintos_com_merito_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_por_tipo_sentenca_NG": get_extintos_com_merito_por_tipo_sentenca_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_qtd_NG": get_total_extintos_com_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_valor_causa_NG": get_valor_causa_total_extintos_com_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_NG": get_extintos_com_merito_2g_por_tipo_sentenca_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_valor_causa_acordao_NG": get_valor_causa_acordao_total_extintos_com_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG": get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_qtd_NG": get_total_extintos_sem_merito_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_valor_causa_NG": get_valor_causa_total_extintos_sem_merito_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_qtd_NG": get_total_extintos_sem_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_valor_causa_NG": get_valor_causa_total_extintos_sem_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_NG": get_valor_causa_acordao_total_extintos_sem_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_taxa_provimento_2g_NG": get_taxa_provimento_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            # Recursal (painel "Extintos · 2º Grau"): todas as situações (inclui arquivado),
            # diferente do Controle de Processos, que respeita o filtro de situação (ativo/suspenso).
            "controle_processo_extintos_com_merito_2g_qtd_recursal_NG": get_total_extintos_com_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG": get_valor_causa_acordao_total_extintos_com_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG": get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_qtd_recursal_NG": get_total_extintos_sem_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG": get_valor_causa_acordao_total_extintos_sem_merito_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_taxa_provimento_2g_recursal_NG": get_taxa_provimento_2g_NG(_recursal_base_NG, from_date=from_date, to_date=to_date),
            "controle_processo_log_inicial_indeferida_qtd_NG": get_total_controle_processo_log_inicial_indeferida_NG(base),
            "controle_processo_log_inicial_indeferida_valor_causa_NG": get_valor_causa_total_controle_processo_log_inicial_indeferida_NG(base),
            "controle_processo_log_recursal_nao_provido_qtd_NG": get_total_controle_processo_log_recursal_nao_provido_NG(base),
            "controle_processo_log_recursal_nao_provido_valor_causa_NG": get_valor_causa_total_controle_processo_log_recursal_nao_provido_NG(base),
            "controle_processo_fase_inicial_media_dias_NG": get_media_tempo_dias_fase_inicial_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_media_dias_NG": get_media_tempo_dias_fase_recursal_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_media_dias_NG": get_media_tempo_dias_fase_execucao_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_inicial_mediana_dias_NG": get_mediana_tempo_dias_fase_inicial_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_mediana_dias_NG": get_mediana_tempo_dias_fase_recursal_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_mediana_dias_NG": get_mediana_tempo_dias_fase_execucao_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_inicial_comparativo_media_dias_NG": get_comparativo_media_tempo_dias_fase_inicial_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_comparativo_media_dias_NG": get_comparativo_media_tempo_dias_fase_recursal_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_comparativo_media_dias_NG": get_comparativo_media_tempo_dias_fase_execucao_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_inicial_comparativo_mediana_dias_NG": get_comparativo_mediana_tempo_dias_fase_inicial_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_recursal_comparativo_mediana_dias_NG": get_comparativo_mediana_tempo_dias_fase_recursal_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
            "controle_processo_fase_execucao_comparativo_mediana_dias_NG": get_comparativo_mediana_tempo_dias_fase_execucao_NG(_all_situacao_NG, from_date=from_date, to_date=to_date),
        }
        charts = {
            "controle_processo_por_fase_NG": [ChartDataPoint(**x) for x in group_controle_processo_por_fase_NG(base)],
            "controle_processo_por_subfase_NG": [ChartDataPoint(**x) for x in subfase_items],
            "controle_processo_fase_inicial_media_dias_por_mes_NG": [ChartDataPoint(**x) for x in get_media_tempo_dias_fase_inicial_por_mes_NG(_all_situacao_NG)],
            "controle_processo_fase_recursal_media_dias_por_mes_NG": [ChartDataPoint(**x) for x in get_media_tempo_dias_fase_recursal_por_mes_NG(_all_situacao_NG)],
            "controle_processo_fase_execucao_media_dias_por_mes_NG": [ChartDataPoint(**x) for x in get_media_tempo_dias_fase_execucao_por_mes_NG(_all_situacao_NG)],
        }
        logger.info("Dashboard 'controle_processo_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="controle_processo_NG", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "publicacoes_LA":
        pub = _a("publicacoes_LA")
        pub = filter_publicacoes_por_leitor_LA(pub, leitor)
        pub = filter_publicacoes_por_materia_LA(pub, materia)
        pub = filter_publicacoes_por_documento_LA(pub, documento)
        pub = filter_publicacoes_por_tribunal_LA(pub, tribunal)
        pub = filter_publicacoes_por_orgao_LA(pub, orgao)
        agendamentos_pub = _a("agendamentos_todos_setores_LA")
        pub = filter_publicacoes_por_atividade_agendamento_LA(pub, agendamentos_pub, atividade_agendamento, from_date, to_date)
        pub = filter_publicacoes_por_setor_agendamento_LA(pub, agendamentos_pub, setor_agendamento, from_date, to_date)
        pub = filter_publicacoes_por_status_agendamento_LA(pub, agendamentos_pub, status_agendamento, from_date, to_date)
        stats, charts = _build_publicacoes_LA_stats(pub, agendamentos_pub, from_date, to_date)
        logger.info("Dashboard 'publicacoes_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="publicacoes_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "publicacoes_NG":
        pub = _a("publicacoes_NG")
        pub = filter_publicacoes_por_leitor_NG(pub, leitor)
        pub = filter_publicacoes_por_materia_NG(pub, materia)
        pub = filter_publicacoes_por_documento_NG(pub, documento)
        pub = filter_publicacoes_por_tribunal_NG(pub, tribunal)
        pub = filter_publicacoes_por_orgao_NG(pub, orgao)
        agendamentos_pub = _a("agendamentos_todos_setores_NG")
        pub = filter_publicacoes_por_atividade_agendamento_NG(pub, agendamentos_pub, atividade_agendamento, from_date, to_date)
        pub = filter_publicacoes_por_setor_agendamento_NG(pub, agendamentos_pub, setor_agendamento, from_date, to_date)
        pub = filter_publicacoes_por_status_agendamento_NG(pub, agendamentos_pub, status_agendamento, from_date, to_date)
        stats, charts = _build_publicacoes_NG_stats(pub, agendamentos_pub, from_date, to_date)
        logger.info("Dashboard 'publicacoes_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="publicacoes_NG", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "publicacoes_RJ":
        pub = _a("publicacoes_LA_RJ")
        pub = filter_publicacoes_por_leitor_RJ(pub, leitor)
        pub = filter_publicacoes_por_materia_RJ(pub, materia)
        pub = filter_publicacoes_por_documento_RJ(pub, documento)
        pub = filter_publicacoes_por_tribunal_RJ(pub, tribunal)
        pub = filter_publicacoes_por_orgao_RJ(pub, orgao)
        agendamentos_pub = _a("agendamentos_todos_setores_LA_RJ")
        pub = filter_publicacoes_por_atividade_agendamento_RJ(pub, agendamentos_pub, atividade_agendamento, from_date, to_date)
        pub = filter_publicacoes_por_setor_agendamento_RJ(pub, agendamentos_pub, setor_agendamento, from_date, to_date)
        pub = filter_publicacoes_por_status_agendamento_RJ(pub, agendamentos_pub, status_agendamento, from_date, to_date)
        stats, charts = _build_publicacoes_RJ_stats(pub, agendamentos_pub, from_date, to_date)
        logger.info("Dashboard 'publicacoes_RJ' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="publicacoes_RJ", stats=DashboardStats(**stats), **charts)
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
    raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' não encontrado.")


# v1: dashboard_routes.py:23265 (rota sem os decoradores)
async def get_execucao_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria).",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra pela subfase (igual ao `name` dos gráficos por subfase).",
    ),
    ano_ajuizamento_execucao: Optional[str] = Query(
        None,
        description="Filtra pelo ano de ajuizamento (igual ao `name` do gráfico correspondente, ex.: `2024` ou 'Sem data de ajuizamento').",
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf=AM&uf=PA`). Omitido/vazio = todas as UFs."
        ),
    ),
    comarca: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por comarca do processo — aceita múltiplos valores "
            "(`?comarca=Manaus&comarca=Manacapuru`). Omitido/vazio = todas as comarcas."
        ),
    ),
    funcionario_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades NG)",
    ),
    atividade_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade (seção Atividades NG)",
    ),
    status_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status (seção Atividades NG)",
    ),
    situacao_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
    diligencia_tipo_execucao: Optional[str] = Query(
        None,
        description="Filtra os gráficos de diligências: expedicao_alvara ou expedicao_alvara_cumprida.",
    ),
    diligencia_colaborador_execucao: Optional[str] = Query(
        None,
        description="Filtra o gráfico 'Processos com mais Diligências' pelo colaborador clicado no ranking.",
    ),
):
    """Dashboard de Execução NG."""
    filtros = _parse_execucao_atividades_filtros(
        funcionario_execucao,
        atividade_execucao,
        status_execucao,
        situacao_execucao,
    )
    return await _get_dashboard_response(
        "execucao",
        from_date,
        to_date,
        materia=materia,
        subfase=subfase,
        ano_ajuizamento_execucao=ano_ajuizamento_execucao,
        uf_execucao_ng=uf,
        comarca_execucao_ng=comarca,
        execucao_atividades_filtros=filtros,
        diligencia_tipo_execucao=diligencia_tipo_execucao,
        diligencia_colaborador_execucao=diligencia_colaborador_execucao,
    )


# v1: dashboard_routes.py:27970 (rota sem os decoradores)
async def get_execucao_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria LA).",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra pela subfase (igual ao `name` dos gráficos por subfase LA).",
    ),
    ano_ajuizamento_execucao: Optional[str] = Query(
        None,
        description="Filtra pelo ano de ajuizamento (igual ao `name` do gráfico correspondente, ex.: `2024` ou 'Sem data de ajuizamento').",
    ),
    comarca: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por comarca do processo — aceita múltiplos valores "
            "(`?comarca=Manaus&comarca=Manacapuru`). Omitido/vazio = todas as comarcas."
        ),
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf=AM&uf=PA`). Omitido/vazio = todas as UFs."
        ),
    ),
    funcionario_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades)",
    ),
    atividade_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade",
    ),
    status_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status",
    ),
    situacao_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
):
    """Dashboard de Execução LA."""
    filtros = _parse_execucao_atividades_filtros(
        funcionario_execucao,
        atividade_execucao,
        status_execucao,
        situacao_execucao,
    )
    return await _get_dashboard_response(
        "execucao_LA",
        from_date,
        to_date,
        materia=materia,
        subfase=subfase,
        ano_ajuizamento_execucao=ano_ajuizamento_execucao,
        comarca_execucao_la=comarca,
        uf_execucao_la=uf,
        execucao_atividades_filtros=filtros,
    )


# v1: dashboard_routes.py:23343 (rota sem os decoradores)
async def get_execucao_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria).",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra pela subfase (igual ao `name` dos gráficos por subfase).",
    ),
    ano_ajuizamento_execucao: Optional[str] = Query(
        None,
        description="Filtra pelo ano de ajuizamento (igual ao `name` do gráfico correspondente, ex.: `2024` ou 'Sem data de ajuizamento').",
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo — aceita múltiplos valores (`?uf=RJ&uf=SP`). "
            "Omitido/vazio = todas as UFs."
        ),
    ),
    comarca: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por comarca do processo — aceita múltiplos valores "
            "(`?comarca=Rio de Janeiro`). Omitido/vazio = todas as comarcas."
        ),
    ),
    funcionario_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades RJ)",
    ),
    atividade_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade (seção Atividades RJ)",
    ),
    status_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status (seção Atividades RJ)",
    ),
    situacao_execucao: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
    diligencia_tipo_execucao: Optional[str] = Query(
        None,
        description="Filtra os gráficos de diligências: expedicao_alvara ou expedicao_alvara_cumprida.",
    ),
    diligencia_colaborador_execucao: Optional[str] = Query(
        None,
        description="Filtra o gráfico 'Processos com mais Diligências' pelo colaborador clicado no ranking.",
    ),
):
    """Dashboard de Execução (Condenação) RJ."""
    filtros = _parse_execucao_atividades_filtros(
        funcionario_execucao,
        atividade_execucao,
        status_execucao,
        situacao_execucao,
    )
    return await _get_dashboard_response(
        "execucao_RJ",
        from_date,
        to_date,
        materia=materia,
        subfase=subfase,
        ano_ajuizamento_execucao=ano_ajuizamento_execucao,
        uf_execucao_rj=uf,
        comarca_execucao_rj=comarca,
        execucao_atividades_filtros=filtros,
        diligencia_tipo_execucao=diligencia_tipo_execucao,
        diligencia_colaborador_execucao=diligencia_colaborador_execucao,
    )


# v1: dashboard_routes.py:23421 (rota sem os decoradores)
async def get_execucao_acordos_ng_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria).",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra pela subfase (igual ao `name` dos gráficos por subfase) — "
            "aceita múltiplos valores (`?subfase=A&subfase=B`)."
        ),
    ),
    tipo_acao_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por classificação Judicial/Extrajudicial (igual ao `name` do gráfico correspondente).",
    ),
    tipo_sentenca_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por classificação Pré-Sentença/Pós-Sentença (igual ao `name` do gráfico correspondente).",
    ),
    ano_ajuizamento_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra pelo ano de ajuizamento (igual ao `name` do gráfico correspondente, ex.: `2024` ou 'Sem data de ajuizamento').",
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf=AM&uf=PA`). Omitido/vazio = todas as UFs."
        ),
    ),
    funcionario_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades NG)",
    ),
    atividade_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade (seção Atividades NG)",
    ),
    status_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status (seção Atividades NG)",
    ),
    situacao_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
    numero_processo_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por um único número de processo (igual ao `name` dos gráficos por processo).",
    ),
    diligencia_tipo_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra os gráficos de diligências: expedicao_alvara ou expedicao_alvara_cumprida.",
    ),
    diligencia_colaborador_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra o gráfico 'Processos com mais Diligências' pelo colaborador clicado no ranking.",
    ),
    comarca: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por comarca do processo — aceita múltiplos valores "
            "(`?comarca=Manaus&comarca=Manacapuru`). Omitido/vazio = todas as comarcas."
        ),
    ),
):
    """Dashboard de Execução Acordos NG."""
    filtros = _parse_execucao_atividades_filtros(
        funcionario_execucao_acordos,
        atividade_execucao_acordos,
        status_execucao_acordos,
        situacao_execucao_acordos,
    )
    return await _get_dashboard_response(
        "execucao_acordos_NG",
        from_date,
        to_date,
        materia=materia,
        subfase=subfase,
        tipo_acao_execucao_acordos=tipo_acao_execucao_acordos,
        tipo_sentenca_execucao_acordos=tipo_sentenca_execucao_acordos,
        ano_ajuizamento_execucao_acordos=ano_ajuizamento_execucao_acordos,
        uf_execucao_acordos_ng=uf,
        execucao_acordos_atividades_filtros=filtros,
        numero_processo_execucao_acordos=numero_processo_execucao_acordos,
        diligencia_tipo_execucao_acordos=diligencia_tipo_execucao_acordos,
        diligencia_colaborador_execucao_acordos=diligencia_colaborador_execucao_acordos,
        comarca_execucao_acordos_ng=comarca,
    )


# v1: dashboard_routes.py:23517 (rota sem os decoradores)
async def get_execucao_acordos_la_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria).",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra pela subfase (igual ao `name` dos gráficos por subfase).",
    ),
    tipo_acao_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por classificação Judicial/Extrajudicial (igual ao `name` do gráfico correspondente).",
    ),
    tipo_sentenca_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por classificação Pré-Sentença/Pós-Sentença (igual ao `name` do gráfico correspondente).",
    ),
    ano_ajuizamento_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra pelo ano de ajuizamento (igual ao `name` do gráfico correspondente, ex.: `2024` ou 'Sem data de ajuizamento').",
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf=AM&uf=PA`). Omitido/vazio = todas as UFs."
        ),
    ),
    funcionario_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades LA)",
    ),
    atividade_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade (seção Atividades LA)",
    ),
    status_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status (seção Atividades LA)",
    ),
    situacao_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
    numero_processo_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por um único número de processo (igual ao `name` dos gráficos por processo).",
    ),
    diligencia_tipo_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra os gráficos de diligências: expedicao_alvara ou expedicao_alvara_cumprida.",
    ),
    diligencia_colaborador_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra o gráfico 'Processos com mais Diligências' pelo colaborador clicado no ranking.",
    ),
    comarca: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por comarca do processo — aceita múltiplos valores "
            "(`?comarca=Manaus&comarca=Manacapuru`). Omitido/vazio = todas as comarcas."
        ),
    ),
):
    """Dashboard de Execução Acordos LA."""
    filtros = _parse_execucao_atividades_filtros(
        funcionario_execucao_acordos,
        atividade_execucao_acordos,
        status_execucao_acordos,
        situacao_execucao_acordos,
    )
    return await _get_dashboard_response(
        "execucao_acordos_LA",
        from_date,
        to_date,
        materia=materia,
        subfase=subfase,
        tipo_acao_execucao_acordos=tipo_acao_execucao_acordos,
        tipo_sentenca_execucao_acordos=tipo_sentenca_execucao_acordos,
        ano_ajuizamento_execucao_acordos=ano_ajuizamento_execucao_acordos,
        uf_execucao_acordos_la=uf,
        execucao_acordos_atividades_filtros=filtros,
        numero_processo_execucao_acordos=numero_processo_execucao_acordos,
        diligencia_tipo_execucao_acordos=diligencia_tipo_execucao_acordos,
        diligencia_colaborador_execucao_acordos=diligencia_colaborador_execucao_acordos,
        comarca_execucao_acordos_la=comarca,
    )


# v1: dashboard_routes.py:23610 (rota sem os decoradores)
async def get_execucao_acordos_rj_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria).",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra pela subfase (igual ao `name` dos gráficos por subfase).",
    ),
    tipo_acao_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por classificação Judicial/Extrajudicial (igual ao `name` do gráfico correspondente).",
    ),
    tipo_sentenca_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por classificação Pré-Sentença/Pós-Sentença (igual ao `name` do gráfico correspondente).",
    ),
    ano_ajuizamento_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra pelo ano de ajuizamento (igual ao `name` do gráfico correspondente, ex.: `2024` ou 'Sem data de ajuizamento').",
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf=AM&uf=PA`). Omitido/vazio = todas as UFs."
        ),
    ),
    funcionario_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades RJ)",
    ),
    atividade_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade (seção Atividades RJ)",
    ),
    status_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status (seção Atividades RJ)",
    ),
    situacao_execucao_acordos: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
    numero_processo_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra por um único número de processo (igual ao `name` dos gráficos por processo).",
    ),
    diligencia_tipo_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra os gráficos de diligências: expedicao_alvara ou expedicao_alvara_cumprida.",
    ),
    diligencia_colaborador_execucao_acordos: Optional[str] = Query(
        None,
        description="Filtra o gráfico 'Processos com mais Diligências' pelo colaborador clicado no ranking.",
    ),
    comarca: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por comarca do processo — aceita múltiplos valores "
            "(`?comarca=Manaus&comarca=Manacapuru`). Omitido/vazio = todas as comarcas."
        ),
    ),
):
    """Dashboard de Execução Acordos LA."""
    filtros = _parse_execucao_atividades_filtros(
        funcionario_execucao_acordos,
        atividade_execucao_acordos,
        status_execucao_acordos,
        situacao_execucao_acordos,
    )
    return await _get_dashboard_response(
        "execucao_acordos_RJ",
        from_date,
        to_date,
        materia=materia,
        subfase=subfase,
        tipo_acao_execucao_acordos=tipo_acao_execucao_acordos,
        tipo_sentenca_execucao_acordos=tipo_sentenca_execucao_acordos,
        ano_ajuizamento_execucao_acordos=ano_ajuizamento_execucao_acordos,
        uf_execucao_acordos_rj=uf,
        execucao_acordos_atividades_filtros=filtros,
        numero_processo_execucao_acordos=numero_processo_execucao_acordos,
        diligencia_tipo_execucao_acordos=diligencia_tipo_execucao_acordos,
        diligencia_colaborador_execucao_acordos=diligencia_colaborador_execucao_acordos,
        comarca_execucao_acordos_rj=comarca,
    )


# v1: dashboard_routes.py:24884 (rota sem os decoradores)
async def get_recursal_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None, description="Filtra por ID(s) de status 1º grau"),
    id_2g: Optional[List[int]] = Query(None, description="Filtra por ID(s) de status 2º grau"),
    juiz: Optional[List[str]] = Query(None, description="Filtra por nome(s) de juiz (1G)"),
    relator: Optional[List[str]] = Query(None, description="Filtra por nome(s) de relator (2G)"),
    decisao: Optional[List[str]] = Query(
        None,
        description="Filtra por tipo(s) de decisão recursal (ex.: mantido_ganho)",
    ),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra por matéria(s) (rótulo normalizado do gráfico)",
    ),
    competencia: Optional[List[str]] = Query(
        None,
        description="Filtra por competência(s) (rótulo do gráfico)",
    ),
    vara: Optional[List[str]] = Query(
        None,
        description="Filtra por vara(s) (rótulo do gráfico, ex.: 1º vara)",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra por subfase(s) (rótulo do gráfico)",
    ),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por funcionário (seção Atividades)",
    ),
    atividade_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por atividade do catálogo",
    ),
    status_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por status do agendamento",
    ),
    situacao_recursos: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas"
        ),
    ),
):
    """
    Dashboard da fase Recursal (LA).

    Retorna ``total_recursal_NG`` (estoque, fase 8) e ``entrada_recursal_NG`` (fase 8 + entrada no período).
    Filtros cumulativos opcionais: ``id_1g``, ``id_2g``, ``juiz``, ``relator``, ``decisao``,
    ``materia``, ``competencia``, ``vara``, ``subfase``, ``extinto_2g``.
    Filtros da seção Atividades: ``funcionario_recursos``, ``atividade_recursos``,
    ``status_recursos``, ``situacao_recursos``.
    """
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _get_dashboard_response(
        "recursal_NG",
        from_date,
        to_date,
        recursal_la_filtros=filtros,
        recursal_atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:23891 (rota sem os decoradores)
async def get_recursal_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None, description="Filtra por ID(s) de status 1º grau"),
    id_2g: Optional[List[int]] = Query(None, description="Filtra por ID(s) de status 2º grau"),
    juiz: Optional[List[str]] = Query(None, description="Filtra por nome(s) de juiz (1G)"),
    relator: Optional[List[str]] = Query(None, description="Filtra por nome(s) de relator (2G)"),
    decisao: Optional[List[str]] = Query(
        None,
        description="Filtra por tipo(s) de decisão recursal (ex.: mantido_ganho)",
    ),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra por matéria(s) (rótulo normalizado do gráfico)",
    ),
    competencia: Optional[List[str]] = Query(
        None,
        description="Filtra por competência(s) (rótulo do gráfico)",
    ),
    vara: Optional[List[str]] = Query(
        None,
        description="Filtra por vara(s) (rótulo do gráfico, ex.: 1º vara)",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra por subfase(s) (rótulo do gráfico)",
    ),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por funcionário (seção Atividades)",
    ),
    atividade_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por atividade do catálogo",
    ),
    status_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por status do agendamento",
    ),
    situacao_recursos: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas"
        ),
    ),
):
    """
    Dashboard da fase Recursal (LA).

    Retorna ``total_recursal_LA`` (estoque, fase 8) e ``entrada_recursal_LA`` (fase 8 + entrada no período).
    Filtros cumulativos opcionais: ``id_1g``, ``id_2g``, ``juiz``, ``relator``, ``decisao``,
    ``materia``, ``competencia``, ``vara``, ``subfase``, ``extinto_2g``.
    Filtros da seção Atividades: ``funcionario_recursos``, ``atividade_recursos``,
    ``status_recursos``, ``situacao_recursos``.
    """
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _get_dashboard_response(
        "recursal_LA",
        from_date,
        to_date,
        recursal_la_filtros=filtros,
        recursal_atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:25877 (rota sem os decoradores)
async def get_recursal_RJ_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    id_1g: Optional[List[int]] = Query(None, description="Filtra por ID(s) de status 1º grau"),
    id_2g: Optional[List[int]] = Query(None, description="Filtra por ID(s) de status 2º grau"),
    juiz: Optional[List[str]] = Query(None, description="Filtra por nome(s) de juiz (1G)"),
    relator: Optional[List[str]] = Query(None, description="Filtra por nome(s) de relator (2G)"),
    decisao: Optional[List[str]] = Query(
        None,
        description="Filtra por tipo(s) de decisão recursal (ex.: mantido_ganho)",
    ),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra por matéria(s) (rótulo normalizado do gráfico)",
    ),
    competencia: Optional[List[str]] = Query(
        None,
        description="Filtra por competência(s) (rótulo do gráfico)",
    ),
    vara: Optional[List[str]] = Query(
        None,
        description="Filtra por vara(s) (rótulo do gráfico, ex.: 1º vara)",
    ),
    subfase: Optional[List[str]] = Query(
        None,
        description="Filtra por subfase(s) (rótulo do gráfico)",
    ),
    extinto_2g: Optional[List[str]] = Query(
        None,
        description="Extintos 2º grau: com_merito (ID_2G 17,19–23) ou sem_merito (ID_2G 18)",
    ),
    funcionario_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por funcionário (seção Atividades)",
    ),
    atividade_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por atividade do catálogo",
    ),
    status_recursos: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos RECURSOS por status do agendamento",
    ),
    situacao_recursos: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas"
        ),
    ),
):
    """
    Dashboard da fase Recursal (LA).

    Retorna ``total_recursal_RJ`` (estoque, fase 8) e ``entrada_recursal_RJ`` (fase 8 + entrada no período).
    Filtros cumulativos opcionais: ``id_1g``, ``id_2g``, ``juiz``, ``relator``, ``decisao``,
    ``materia``, ``competencia``, ``vara``, ``subfase``, ``extinto_2g``.
    Filtros da seção Atividades: ``funcionario_recursos``, ``atividade_recursos``,
    ``status_recursos``, ``situacao_recursos``.
    """
    filtros, filtros_atividades = _parse_recursal_la_filtros_completos(
        id_1g=id_1g,
        id_2g=id_2g,
        juiz=juiz,
        relator=relator,
        decisao=decisao,
        materia=materia,
        competencia=competencia,
        vara=vara,
        subfase=subfase,
        extinto_2g=extinto_2g,
        funcionario_recursos=funcionario_recursos,
        atividade_recursos=atividade_recursos,
        status_recursos=status_recursos,
        situacao_recursos=situacao_recursos,
    )
    return await _get_dashboard_response(
        "recursal_RJ",
        from_date,
        to_date,
        recursal_la_filtros=filtros,
        recursal_atividades_recursos_filtros=filtros_atividades,
    )


# v1: dashboard_routes.py:28649 (rota sem os decoradores)
async def get_controle_processo_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    fase: Optional[str] = Query(
        None,
        description=(
            "Filtra o gráfico de subfases pela fase selecionada (ex.: INICIAL). "
            "Quando omitido, `controle_processo_por_subfase_NG` vem vazio."
        ),
    ),
    situacao: Optional[str] = Query(
        None,
        description=(
            "Filtra por situação do processo: `ativo`, `suspenso` (ou `sobrestado`) "
            "ou `ambos`/omitido (padrão — ATIVO e SUSPENSO/SOBRESTADO)."
        ),
    ),
    uf: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf=AM&uf=PA`). Omitido/vazio = todas as UFs."
        ),
    ),
):
    """Dashboard de Controle de Processos LA (LexFlow)."""
    return await _get_dashboard_response(
        "controle_processo_NG", from_date, to_date, fase=fase, situacao=situacao, uf_controle_processo_ng=uf
    )


# v1: dashboard_routes.py:28226 (rota sem os decoradores)
async def get_controle_processo_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    fase: Optional[str] = Query(
        None,
        description=(
            "Filtra o gráfico de subfases pela fase selecionada (ex.: INICIAL). "
            "Quando omitido, `controle_processo_por_subfase_LA` vem vazio."
        ),
    ),
    situacao: Optional[str] = Query(
        None,
        description=(
            "Filtra por situação do processo: `ativo`, `suspenso` (ou `sobrestado`) "
            "ou `ambos`/omitido (padrão — ATIVO e SUSPENSO/SOBRESTADO)."
        ),
    ),
):
    """Dashboard de Controle de Processos LA (LexFlow)."""
    return await _get_dashboard_response("controle_processo_LA", from_date, to_date, fase=fase, situacao=situacao)


# v1: dashboard_routes.py:30057 (rota sem os decoradores)
async def get_publicacoes_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    leitor: Optional[List[str]] = Query(
        None,
        description="Filtra todas as métricas e gráficos ao leitor (nome completo ou como nos rótulos). Omitir = visão geral.",
    ),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria (mesmo texto dos rótulos dos gráficos, ex. SEM MATERIA).",
    ),
    documento: Optional[str] = Query(
        None,
        description="Filtra pelo tipo de documento (rótulos em maiúsculas, alinhado ao gráfico por documento).",
    ),
    tribunal: Optional[str] = Query(
        None,
        description="Filtra pelo tribunal (ex. SEM TRIBUNAL ou sigla como nos rótulos).",
    ),
    orgao: Optional[str] = Query(
        None,
        description="Filtra pelo órgão (ex. SEM ORGAO ou valor como nos rótulos).",
    ),
    atividade_agendamento: Optional[str] = Query(
        None,
        description="Filtra pela atividade do agendamento criado após a conclusão (rótulo do gráfico 'Por atividade').",
    ),
    setor_agendamento: Optional[str] = Query(
        None,
        description="Filtra pelo setor de destino do agendamento criado após a conclusão (rótulo do gráfico 'Por setor').",
    ),
    status_agendamento: Optional[str] = Query(
        None,
        description="Filtra por 'com' ou 'sem' agendamento criado após a conclusão da publicação.",
    ),
):
    """Dashboard de publicações LexFlow (NG)."""
    return await _get_dashboard_response(
        "publicacoes_NG",
        from_date,
        to_date,
        leitor=leitor,
        materia=materia,
        documento=documento,
        tribunal=tribunal,
        orgao=orgao,
        atividade_agendamento=atividade_agendamento,
        setor_agendamento=setor_agendamento,
        status_agendamento=status_agendamento,
    )


# v1: dashboard_routes.py:30003 (rota sem os decoradores)
async def get_publicacoes_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    leitor: Optional[List[str]] = Query(
        None,
        description="Filtra todas as métricas e gráficos ao leitor (nome completo ou como nos rótulos). Omitir = visão geral.",
    ),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria (mesmo texto dos rótulos dos gráficos, ex. SEM MATERIA).",
    ),
    documento: Optional[str] = Query(
        None,
        description="Filtra pelo tipo de documento (rótulos em maiúsculas, alinhado ao gráfico por documento).",
    ),
    tribunal: Optional[str] = Query(
        None,
        description="Filtra pelo tribunal (ex. SEM TRIBUNAL ou sigla como nos rótulos).",
    ),
    orgao: Optional[str] = Query(
        None,
        description="Filtra pelo órgão (ex. SEM ORGAO ou valor como nos rótulos).",
    ),
    atividade_agendamento: Optional[str] = Query(
        None,
        description="Filtra pela atividade do agendamento criado após a conclusão (rótulo do gráfico 'Por atividade').",
    ),
    setor_agendamento: Optional[str] = Query(
        None,
        description="Filtra pelo setor de destino do agendamento criado após a conclusão (rótulo do gráfico 'Por setor').",
    ),
    status_agendamento: Optional[str] = Query(
        None,
        description="Filtra por 'com' ou 'sem' agendamento criado após a conclusão da publicação.",
    ),
):
    """Dashboard de publicações LexFlow (LAADV)."""
    return await _get_dashboard_response(
        "publicacoes_LA",
        from_date,
        to_date,
        leitor=leitor,
        materia=materia,
        documento=documento,
        tribunal=tribunal,
        orgao=orgao,
        atividade_agendamento=atividade_agendamento,
        setor_agendamento=setor_agendamento,
        status_agendamento=status_agendamento,
    )


# v1: dashboard_routes.py:30111 (rota sem os decoradores)
async def get_publicacoes_RJ_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    leitor: Optional[List[str]] = Query(
        None,
        description="Filtra todas as métricas e gráficos ao leitor (nome completo ou como nos rótulos). Omitir = visão geral.",
    ),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria (mesmo texto dos rótulos dos gráficos, ex. SEM MATERIA).",
    ),
    documento: Optional[str] = Query(
        None,
        description="Filtra pelo tipo de documento (rótulos em maiúsculas, alinhado ao gráfico por documento).",
    ),
    tribunal: Optional[str] = Query(
        None,
        description="Filtra pelo tribunal (ex. SEM TRIBUNAL ou sigla como nos rótulos).",
    ),
    orgao: Optional[str] = Query(
        None,
        description="Filtra pelo órgão (ex. SEM ORGAO ou valor como nos rótulos).",
    ),
    atividade_agendamento: Optional[str] = Query(
        None,
        description="Filtra pela atividade do agendamento criado após a conclusão (rótulo do gráfico 'Por atividade').",
    ),
    setor_agendamento: Optional[str] = Query(
        None,
        description="Filtra pelo setor de destino do agendamento criado após a conclusão (rótulo do gráfico 'Por setor').",
    ),
    status_agendamento: Optional[str] = Query(
        None,
        description="Filtra por 'com' ou 'sem' agendamento criado após a conclusão da publicação.",
    ),
):
    """Dashboard de publicações LexFlow (RJ)."""
    return await _get_dashboard_response(
        "publicacoes_RJ",
        from_date,
        to_date,
        leitor=leitor,
        materia=materia,
        documento=documento,
        tribunal=tribunal,
        orgao=orgao,
        atividade_agendamento=atividade_agendamento,
        setor_agendamento=setor_agendamento,
        status_agendamento=status_agendamento,
    )


# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache).
HANDLERS = {"execucao": get_execucao_dashboard, "execucao_LA": get_execucao_LA_dashboard, "execucao_RJ": get_execucao_rj_dashboard, "execucao_acordos_NG": get_execucao_acordos_ng_dashboard, "execucao_acordos_LA": get_execucao_acordos_la_dashboard, "execucao_acordos_RJ": get_execucao_acordos_rj_dashboard, "recursal_NG": get_recursal_NG_dashboard, "recursal_LA": get_recursal_LA_dashboard, "recursal_RJ": get_recursal_RJ_dashboard, "controle_processo_NG": get_controle_processo_NG_dashboard, "controle_processo_LA": get_controle_processo_LA_dashboard, "publicacoes_NG": get_publicacoes_NG_dashboard, "publicacoes_LA": get_publicacoes_LA_dashboard, "publicacoes_RJ": get_publicacoes_RJ_dashboard}
QUERIES_POR_DASHBOARD = {'execucao': ('execucao_LA', 'agendamentos_setor_execucao_NG'), 'execucao_LA': ('execucao_LA', 'agendamentos_setor_execucao_LA'), 'execucao_RJ': ('execucao_RJ', 'agendamentos_setor_execucao_LA_RJ'), 'execucao_acordos_NG': ('execucao_acordos_NG', 'agendamentos_fechamento_acordos_NG', 'agendamentos_setor_execucao_acordos_NG'), 'execucao_acordos_LA': ('execucao_acordos_LA', 'agendamentos_fechamento_acordos_LA', 'agendamentos_setor_execucao_acordos_LA'), 'execucao_acordos_RJ': ('execucao_acordos_RJ', 'agendamentos_fechamento_acordos_RJ', 'agendamentos_setor_execucao_acordos_RJ'), 'recursal_NG': ('setor_recurso_NG', 'agendamentos_setor_recursos_NG', 'atividades_setor_recursos_NG'), 'recursal_LA': ('setor_recurso', 'agendamentos_setor_recursos_LA', 'atividades_setor_recursos_LA'), 'recursal_RJ': ('setor_recurso_RJ', 'agendamentos_setor_recursos_RJ', 'atividades_setor_recursos_RJ', 'controle_processo_todas_situacoes'), 'controle_processo_NG': ('controle_processo', 'log_subfase_processual', 'controle_processo_todas_situacoes'), 'controle_processo_LA': ('controle_processo', 'log_subfase_processual', 'controle_processo_todas_situacoes'), 'publicacoes_NG': ('publicacoes_NG', 'agendamentos_todos_setores_NG'), 'publicacoes_LA': ('publicacoes_LA', 'agendamentos_todos_setores_LA'), 'publicacoes_RJ': ('publicacoes_LA_RJ', 'agendamentos_todos_setores_LA_RJ')}
