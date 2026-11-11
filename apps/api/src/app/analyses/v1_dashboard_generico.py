"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (cópia de 11/11/2026; linha na v1 ao lado de cada bloco).
Gerado por script a partir da v1: handlers das rotas (sem os decoradores), ramos
`if dashboard_name == ...` e tudo que eles usam. Únicas trocas, marcadas com "V2:":
  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;
  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo.
Dashboards: execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA.
"""

import asyncio
import logging
import time
from contextvars import ContextVar
from app.analyses.LA.execucao_LA import (
    ExecucaoAtividadesFiltros,
    SITUACOES_VALIDAS_EXECUCAO,
    _get_ag_processo_id,
    filter_execucao_LA_por_ano_ajuizamento,
    filter_execucao_LA_por_comarca,
    filter_execucao_LA_por_materia,
    filter_execucao_LA_por_subfase,
    filter_execucao_LA_por_uf,
    filtrar_agendamentos_execucao_LA,
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
    filtrar_agendamentos_recursos_LA,
    filtrar_recursal_LA,
    filtrar_recursal_LA_por_processo_ids,
    get_decisoes_recursal_resumo_LA,
    get_entrada_recurso_LA,
    get_kpis_atividades_recursos_LA,
    get_kpis_atividades_recursos_por_prazo_LA,
    get_media_recursal_resolvidos_por_funcionario_LA,
    get_opcoes_filtros_atividades_lista_LA,
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
    group_recursal_por_status_1g_LA,
    group_recursal_por_status_2g_LA,
    group_recursal_por_subfase_LA,
    group_recursal_processos_por_atividade_LA,
    group_recursal_resolvidos_por_dia_LA,
    group_recursal_resolvidos_por_mes_LA,
    list_recursal_atividades_periodo_LA,
    processo_ids_recursal_de_agendamentos_recursos_LA,
    set_atividades_recursos_LA_catalogo,
)
from app.analyses.NG.execucao import (
    _filtrar_entrada_execucao_no_periodo as _filtrar_entrada_execucao_no_periodo_ng,
    _get_ag_processo_id_ng,
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
from app.analyses.NG.recurso_NG import (
    META_PROVIMENTO_MENSAL_NG,
    filtrar_agendamentos_recursos_NG,
    filtrar_recursal_NG,
    filtrar_recursal_NG_por_processo_ids,
    get_decisoes_recursal_resumo_NG,
    get_entrada_recurso_NG,
    get_kpis_atividades_recursos_NG,
    get_kpis_atividades_recursos_por_prazo_NG,
    get_media_recursal_resolvidos_por_funcionario_NG,
    get_opcoes_filtros_atividades_lista_NG,
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
    group_recursal_por_status_1g_NG,
    group_recursal_por_status_2g_NG,
    group_recursal_por_subfase_NG,
    group_recursal_processos_por_atividade_NG,
    group_recursal_resolvidos_por_dia_NG,
    group_recursal_resolvidos_por_mes_NG,
    list_recursal_atividades_periodo_NG,
    processo_ids_recursal_de_agendamentos_recursos_NG,
    set_atividades_recursos_NG_catalogo,
)
from app.analyses.RJ.execucao_RJ import (
    _filtrar_entrada_execucao_RJ_no_periodo as _filtrar_entrada_execucao_no_periodo_rj,
    _get_ag_processo_id_rj,
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
from app.analyses.situacao_processo import aplicar_filtro_situacao_processo
from app.sources import SourceUnavailable  # V2: fonte fora do ar vira 503 na casca

# V2: fonte do banco de origem (no lugar de fetch_data_with_cache da v1). A casca passa a fonte do
# dashboard (SourceFetcher, já com o cache de 5 min) por `usar_fonte`; o recorte de situação do processo
# é o mesmo que a v1 aplica em fetch_data_with_cache.
_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico")

def usar_fonte(fonte):
    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""
    return _fonte_ctx.set(fonte)


async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:
    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))


# V2: v1 dashboard_routes.py:2708 -> fetch_data_with_cache('execucao_LA', ...)
async def fetch_execucao_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_LA')


# V2: v1 dashboard_routes.py:2711 -> fetch_data_with_cache('setor_recurso', ...)
async def fetch_recursal_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_recurso')


# V2: v1 dashboard_routes.py:2714 -> fetch_data_with_cache('agendamentos_setor_recursos_LA', ...)
async def fetch_agendamentos_setor_recursos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_recursos_LA')


# V2: v1 dashboard_routes.py:2720 -> fetch_data_with_cache('setor_recurso_NG', ...)
async def fetch_recursal_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_recurso_NG')


# V2: v1 dashboard_routes.py:2723 -> fetch_data_with_cache('agendamentos_setor_recursos_NG', ...)
async def fetch_agendamentos_setor_recursos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_recursos_NG')


# V2: v1 dashboard_routes.py:2729 -> fetch_data_with_cache('atividades_setor_recursos_NG', ...)
async def fetch_atividades_setor_recursos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('atividades_setor_recursos_NG')


# V2: v1 dashboard_routes.py:2735 -> fetch_data_with_cache('atividades_setor_recursos_LA', ...)
async def fetch_atividades_setor_recursos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('atividades_setor_recursos_LA')


# V2: v1 dashboard_routes.py:2748 -> fetch_data_with_cache('agendamentos_setor_execucao_LA', ...)
async def fetch_agendamentos_setor_execucao_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_LA')


# V2: v1 dashboard_routes.py:2844 -> fetch_data_with_cache('execucao_LA', ...)
async def fetch_execucao() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_LA')


# V2: v1 dashboard_routes.py:2847 -> fetch_data_with_cache('execucao_RJ', ...)
async def fetch_execucao_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_RJ')


# V2: v1 dashboard_routes.py:2850 -> fetch_data_with_cache('execucao_acordos_NG', ...)
async def fetch_execucao_acordos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_acordos_NG')


# V2: v1 dashboard_routes.py:2853 -> fetch_data_with_cache('execucao_acordos_LA', ...)
async def fetch_execucao_acordos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_acordos_LA')


# V2: v1 dashboard_routes.py:2856 -> fetch_data_with_cache('execucao_acordos_RJ', ...)
async def fetch_execucao_acordos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('execucao_acordos_RJ')


# V2: v1 dashboard_routes.py:2859 -> fetch_data_with_cache('agendamentos_fechamento_acordos_NG', ...)
async def fetch_agendamentos_fechamento_acordos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_fechamento_acordos_NG')


# V2: v1 dashboard_routes.py:2877 -> fetch_data_with_cache('agendamentos_fechamento_acordos_LA', ...)
async def fetch_agendamentos_fechamento_acordos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_fechamento_acordos_LA')


# V2: v1 dashboard_routes.py:2883 -> fetch_data_with_cache('agendamentos_fechamento_acordos_RJ', ...)
async def fetch_agendamentos_fechamento_acordos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_fechamento_acordos_RJ')


# V2: v1 dashboard_routes.py:2889 -> fetch_data_with_cache('agendamentos_setor_execucao_NG', ...)
async def fetch_agendamentos_setor_execucao_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_NG')


# V2: v1 dashboard_routes.py:2895 -> fetch_data_with_cache('agendamentos_setor_execucao_acordos_NG', ...)
async def fetch_agendamentos_setor_execucao_acordos_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_acordos_NG')


# V2: v1 dashboard_routes.py:2901 -> fetch_data_with_cache('agendamentos_setor_execucao_acordos_LA', ...)
async def fetch_agendamentos_setor_execucao_acordos_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_acordos_LA')


# V2: v1 dashboard_routes.py:2907 -> fetch_data_with_cache('agendamentos_setor_execucao_acordos_RJ', ...)
async def fetch_agendamentos_setor_execucao_acordos_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_acordos_RJ')


# V2: v1 dashboard_routes.py:2913 -> fetch_data_with_cache('agendamentos_setor_execucao_LA_RJ', ...)
async def fetch_agendamentos_setor_execucao_RJ() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_execucao_LA_RJ')



# v1: dashboard_routes.py:2121
# ─── Configurações ───────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


# v1: dashboard_routes.py:2974
# ─── Utilitários de data ─────────────────────────────────────────────────────
def _resolve_date_range(
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Optional[date], Optional[date]]:
    """Normaliza o intervalo: se from_date sem to_date, usa hoje como fim."""
    if from_date and not to_date:
        return from_date, date.today()
    return from_date, to_date


# v1: dashboard_routes.py:2984
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


# v1: dashboard_routes.py:2996
def _in_range(d: date, from_date: Optional[date], to_date: Optional[date]) -> bool:
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    if to_date:
        return d <= to_date
    return True


# v1: dashboard_routes.py:3006
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


# v1: dashboard_routes.py:3036
# ─── Configuração centralizada de filtros por fonte ──────────────────────────
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


# v1: dashboard_routes.py:3080
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


# v1: dashboard_routes.py:3106
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


# v1: dashboard_routes.py:3743
# ─── Modelos Pydantic ────────────────────────────────────────────────────────
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


# v1: dashboard_routes.py:3759
class ProcessoDadoFaltando(BaseModel):
    """Um processo com um campo faltando (alimenta o alerta clicável "Atenção" dos
    dashboards de Execução/Execução Acordos/Julgados — número do processo + qual
    informação falta, pra o usuário ir preencher no sistema de origem)."""

    numero_processo: str
    campo: str


# v1: dashboard_routes.py:3768
class InvestimentoCliquesLeadsPoint(BaseModel):
    name: str
    investimento: float
    cliques: int
    leads: int


# v1: dashboard_routes.py:3775
class RubricaCampanhaPoint(BaseModel):
    name: str
    ra: int
    ng: int


# v1: dashboard_routes.py:3781
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


# v1: dashboard_routes.py:3797
class NpsFeedbackMelhoriaRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    feedback_melhoria: str


# v1: dashboard_routes.py:3807
class NpsFeedbackPositivoRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    feedback_positivo: str


# v1: dashboard_routes.py:3817
class NpsComentarioRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    comentario: str


# v1: dashboard_routes.py:3827
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


# v1: dashboard_routes.py:3840
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


# v1: dashboard_routes.py:3853
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


# v1: dashboard_routes.py:3866
class ExecucaoAcordosListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    uf: str
    data_execucao: Optional[str] = None
    valor_execucao: Optional[float] = None
    subfase: str


# v1: dashboard_routes.py:3875
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


# v1: dashboard_routes.py:3899
class DilacaoPorFuncionarioRow(BaseModel):
    funcionario: str
    qtd_dilacoes: int
    total_encerrados: int
    qtd_resolvidos: int
    taxa_dilacao: float


# v1: dashboard_routes.py:3907
class EmendasManifestacoesResolvidosPorUfRow(BaseModel):
    uf: str
    qtd_manifestacao: int
    qtd_dilacao: int
    qtd_total: int


# v1: dashboard_routes.py:3914
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


# v1: dashboard_routes.py:3931
class RecursalAtividadesListaFiltrosOpcoes(BaseModel):
    funcionarios: List[str]
    atividades: List[str]
    status: List[str]
    situacoes: List[Dict[str, str]]


# v1: dashboard_routes.py:3938
class ExecucaoAtrasoBucket(BaseModel):
    dias: int
    label: str
    descricao: str
    count: int
    pct: float


# v1: dashboard_routes.py:3946
class ExecucaoAtrasosDetalhamento(BaseModel):
    total: int
    buckets: List[ExecucaoAtrasoBucket]


# v1: dashboard_routes.py:3951
class RubricaTotalRow(BaseModel):
    rubrica: str
    acoes: int
    valor_am: float
    total: float


# v1: dashboard_routes.py:3958
class ComissionamentoOrgDocRow(BaseModel):
    funcionario: str
    qtd_resolvidos: int
    valor_causa_gerado: float
    valor_comissao: float


# v1: dashboard_routes.py:3965
class ComissionamentoProtocoloRow(BaseModel):
    funcionario: str
    qtd_protocolados: int
    comissao_unitaria: Optional[float] = None
    valor_comissao: float


# v1: dashboard_routes.py:3972
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


# v1: dashboard_routes.py:3984
class ComissionamentoPendenciaRow(BaseModel):
    funcionario: str
    taxa_resolvido: Optional[float] = None
    taxa_cancelamento: Optional[float] = None
    qtd_resolvido: int
    valor: float
    qtd_x_valor: float
    comissao: float


# v1: dashboard_routes.py:3994
class ComissionamentoPublicacaoRow(BaseModel):
    funcionario: str
    qtd_lidas: int
    qtd_certas: int
    qtd_erradas: int
    valor_certa: float
    valor_errada: float
    comissao: float


# v1: dashboard_routes.py:4004
class ComissionamentoAndamentoRow(BaseModel):
    funcionario: str
    media_avaliacao: Optional[float] = None
    qtd_atendimentos: int
    valor_unitario: float
    valor_comissao: float


# v1: dashboard_routes.py:4012
class ComissionamentoComercialRow(BaseModel):
    atendente: str
    acoes: int
    comissao_base: float
    valor_fm: float
    proporcional_am_pa: float
    proporcional_pb: float
    comissao_com_fm: float


# v1: dashboard_routes.py:4022
class ComissionamentoComercialLARow(BaseModel):
    atendente: str
    acoes: int
    comissao_base: float
    valor_fm: float
    comissao_com_fm: float


# v1: dashboard_routes.py:4030
class TotalLeadsPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4035
class TotalClientesFechadosPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4040
class TaxaFechamentoGeralPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4045
class TotalLeadsCampanhaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4050
class TotalClientesFechadosCampanhaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4055
class TaxaFechamentoCampanhaPorCliente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4060
class TotalLeadsIndicacaoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4065
class TaxaFechamentoIndicacaoAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4070
class TotalClientesFechadosIndicacaoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4075
class TotalLeadsIndicacaoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4080
class TotalClientesFechadosIndicacaoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4085
class TaxaFechamentoIndicacaoPassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4090
class TotalLeadsRetornoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4095
class TotalClientesFechadosRetornoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4100
class TaxaFechamentoRetornoAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4105
class TotalLeadsRetornoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4110
class TotalClientesFechadosRetornoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4115
class TaxaFechamentoRetornoPassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4120
class TotalLeadsResgateAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4125
class TotalClientesFechadosResgateAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4130
class TaxaFechamentoResgateAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4135
class TotalLeadsResgatePassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4140
class TotalClientesFechadosResgatePassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4145
class TaxaFechamentoResgatePassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4184
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
    julgados_sentenca_dados_faltando_NG: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças NG — Estudos de Extinção
    julgados_extincao_valor_NG: Optional[float] = None
    julgados_extincao_total_estoque_NG: Optional[int] = None
    julgados_extincao_valor_estoque_NG: Optional[float] = None
    julgados_comarca_opcoes_NG: Optional[List[str]] = None
    julgados_sentenca_total_estoque_NG: Optional[int] = None
    julgados_extincao_revertida_2g_NG: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_NG: Optional[int] = None
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
    julgados_acordao_dados_faltando_NG: Optional[List[ProcessoDadoFaltando]] = None
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
    julgados_sentenca_dados_faltando_LA: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças LA — Estudos de Extinção
    julgados_extincao_valor_LA: Optional[float] = None
    julgados_extincao_total_estoque_LA: Optional[int] = None
    julgados_extincao_valor_estoque_LA: Optional[float] = None
    julgados_comarca_opcoes_LA: Optional[List[str]] = None
    julgados_sentenca_total_estoque_LA: Optional[int] = None
    julgados_extincao_revertida_2g_LA: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_LA: Optional[int] = None
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
    julgados_acordao_dados_faltando_LA: Optional[List[ProcessoDadoFaltando]] = None


# v1: dashboard_routes.py:5423
class Activity(BaseModel):
    id: str
    type: str
    title: str
    description: str
    time: str
    user: str


# v1: dashboard_routes.py:5432
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
    julgados_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_LA: Optional[List[JulgadosSentencaListaRow]] = None
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


# v1: dashboard_routes.py:6967
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


# v1: dashboard_routes.py:6979
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
        "media_tempo_execucao": get_media_tempo_execucao(
            all_execucao, from_date=from_date, to_date=to_date
        ),
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


# v1: dashboard_routes.py:7333
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
        "media_tempo_execucao_RJ": get_media_tempo_execucao_RJ(
            all_execucao, from_date=from_date, to_date=to_date
        ),
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


# v1: dashboard_routes.py:7669
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


# v1: dashboard_routes.py:8012
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


# v1: dashboard_routes.py:8356
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


# v1: dashboard_routes.py:8697
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
        "media_tempo_execucao_LA": get_media_tempo_execucao_LA(
            all_execucao, from_date=from_date, to_date=to_date
        ),
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


# v1: dashboard_routes.py:8987
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


# v1: dashboard_routes.py:8998
_EXTINTOS_2G_RECURSAL_VALIDOS = frozenset({"com_merito", "sem_merito"})


# v1: dashboard_routes.py:9001
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


# v1: dashboard_routes.py:9054
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


# v1: dashboard_routes.py:9099
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


# v1: dashboard_routes.py:9346
def _aplicar_filtros_recursal_la_rows(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
) -> List[Dict]:
    return filtrar_recursal_LA(rows, filtros)


# v1: dashboard_routes.py:9353
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


# v1: dashboard_routes.py:9436
def _aplicar_filtros_recursal_ng_rows(
    rows: List[Dict],
    filtros: Optional[RecursalLAFiltros],
) -> List[Dict]:
    return filtrar_recursal_NG(rows, filtros)


# v1: dashboard_routes.py:9443
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


# v1: dashboard_routes.py:9489
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


# v1: dashboard_routes.py:9696
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


# v1: dashboard_routes.py:9729
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


# v1: dashboard_routes.py:9946
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


# v1: dashboard_routes.py:13842
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


# v1: dashboard_routes.py:20707
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


# v1: dashboard_routes.py:20722
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


# v1: dashboard_routes.py:20744
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


# v1: dashboard_routes.py:20768
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


# v1: dashboard_routes.py:20783
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


# v1: dashboard_routes.py:20805
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


# v1: dashboard_routes.py:20829
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


# v1: dashboard_routes.py:20844
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


# v1: dashboard_routes.py:20866
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


# v1: dashboard_routes.py:21884 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:21962 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:22040 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:22136 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:22229 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:22510 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:23503 (handler da rota, sem os decoradores)
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


# v1: dashboard_routes.py:25316
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


# v1: dashboard_routes.py:25371 (handler da rota, sem os decoradores)
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
}
DASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)
# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache).
HANDLERS = {"execucao": get_execucao_dashboard, "execucao_LA": get_execucao_LA_dashboard, "execucao_RJ": get_execucao_rj_dashboard, "execucao_acordos_NG": get_execucao_acordos_ng_dashboard, "execucao_acordos_LA": get_execucao_acordos_la_dashboard, "execucao_acordos_RJ": get_execucao_acordos_rj_dashboard, "recursal_NG": get_recursal_NG_dashboard, "recursal_LA": get_recursal_LA_dashboard}
QUERIES_POR_DASHBOARD = {'execucao': ('execucao_LA', 'agendamentos_setor_execucao_NG'), 'execucao_LA': ('execucao_LA', 'agendamentos_setor_execucao_LA'), 'execucao_RJ': ('execucao_RJ', 'agendamentos_setor_execucao_LA_RJ'), 'execucao_acordos_NG': ('execucao_acordos_NG', 'agendamentos_fechamento_acordos_NG', 'agendamentos_setor_execucao_acordos_NG'), 'execucao_acordos_LA': ('execucao_acordos_LA', 'agendamentos_fechamento_acordos_LA', 'agendamentos_setor_execucao_acordos_LA'), 'execucao_acordos_RJ': ('execucao_acordos_RJ', 'agendamentos_fechamento_acordos_RJ', 'agendamentos_setor_execucao_acordos_RJ'), 'recursal_NG': ('setor_recurso_NG', 'agendamentos_setor_recursos_NG', 'atividades_setor_recursos_NG'), 'recursal_LA': ('setor_recurso', 'agendamentos_setor_recursos_LA', 'atividades_setor_recursos_LA')}


# v1: dashboard_routes.py:10386 — V2: início igual, só os ramos de execucao, execucao_LA, execucao_RJ, execucao_acordos_NG, execucao_acordos_LA, execucao_acordos_RJ, recursal_NG, recursal_LA
async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards
    dashboard_name: str,
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]] = None,
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
    recursal_la_filtros: Optional[RecursalLAFiltros] = None,
    recursal_atividades_recursos_filtros: Optional[RecursalAtividadesRecursosFiltros] = None,
    execucao_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
    execucao_acordos_atividades_filtros: Optional[ExecucaoAtividadesFiltros] = None,
) -> DashboardResponse:
    # V2: (bloco de outros dashboards da v1 omitido)
    t0 = time.time()
    logger.info("Dashboard '%s' (from=%s, to=%s)", dashboard_name, from_date, to_date)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    # 1. Buscar apenas as fontes necessárias para este dashboard
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
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # 2. Aplicar filtros de data
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
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    def _f(key: str) -> List:
        return filtered_data.get(key, [])
    def _a(key: str) -> List:
        return all_data.get(key, [])
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
    # CORRIGIDO: usa o builder dedicado em vez de bloco inline
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
