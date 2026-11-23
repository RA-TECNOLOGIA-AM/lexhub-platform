# Funções de análises do setor da Fase Recursal — Escritório Luis Albert AM

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import recurso as _familia  # V2: código único da família (familias/recurso.py)
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from app.analyses.common import textos  # V2: nomes e rótulos de texto num módulo só
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.utils import parse_date_from_db
from app.analyses.common import matriz_julgamento as mj

# V2: os valores desta unidade para a família, lidos ao vivo deste módulo (common/unidade.py).
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"ID_ESCRITORIO": "ID_ESCRITORIO", "ID_SETOR_RECURSOS": "ID_SETOR_RECURSOS_LA", "_ATIVIDADES_RECURSOS": "_ATIVIDADES_RECURSOS_LA", "_IDS_ATIVIDADE_RECURSOS": "_IDS_ATIVIDADE_RECURSOS_LA", "_NOMES_ATIVIDADE_RECURSOS": "_NOMES_ATIVIDADE_RECURSOS_LA"})

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO = 21
ID_FASE_RECURSAL = _familia.ID_FASE_RECURSAL
ID_SETOR_RECURSOS_LA = 16

_COL_ID_ESCRITORIO = _familia._COL_ID_ESCRITORIO

_COL_ID_FASE = _familia._COL_ID_FASE

COL_DT_ENTRADA_RECURSAL = _familia.COL_DT_ENTRADA_RECURSAL

COL_VALOR_CAUSA_ACORDO = _familia.COL_VALOR_CAUSA_ACORDO

COL_VALOR_CAUSA_SENTENCA = _familia.COL_VALOR_CAUSA_SENTENCA

_COL_ID_1G = _familia._COL_ID_1G

_COL_STATUS_1G = _familia._COL_STATUS_1G

_COL_ID_2G = _familia._COL_ID_2G

_COL_STATUS_2G = _familia._COL_STATUS_2G

_COL_DATA_SENTENCA = _familia._COL_DATA_SENTENCA

_COL_DATA_ACORDAO = _familia._COL_DATA_ACORDAO

_COL_JUIZ_1G = _familia._COL_JUIZ_1G

_COL_RELATOR_2G = _familia._COL_RELATOR_2G

_COL_SUBFASE = _familia._COL_SUBFASE

_COL_FASE = _familia._COL_FASE

_COL_OPERACAO = _familia._COL_OPERACAO

_COL_MATERIA = _familia._COL_MATERIA

_COL_PARTE_ADVERSA = _familia._COL_PARTE_ADVERSA

_COL_NUMERO_PROCESSO = _familia._COL_NUMERO_PROCESSO

_COL_COMPETENCIA = _familia._COL_COMPETENCIA

_COL_VARA = _familia._COL_VARA

_COL_ID_ATIVIDADE_RECURSOS = _familia._COL_ID_ATIVIDADE_RECURSOS

_COL_ATIVIDADE_RECURSOS = _familia._COL_ATIVIDADE_RECURSOS

_COL_STATUS_AGENDAMENTO_RECURSOS = _familia._COL_STATUS_AGENDAMENTO_RECURSOS

_COL_ID_SETOR_ATIVIDADE_RECURSOS = _familia._COL_ID_SETOR_ATIVIDADE_RECURSOS

_COL_FUNCIONARIO_ATRIBUIDO = _familia._COL_FUNCIONARIO_ATRIBUIDO

_COL_FUNCIONARIO_ENCERRAMENTO = _familia._COL_FUNCIONARIO_ENCERRAMENTO

_COL_ID_USUARIO_ENCERRAMENTO = _familia._COL_ID_USUARIO_ENCERRAMENTO

_SEM_SUBFASE = _familia._SEM_SUBFASE

_SEM_MATERIA = _familia._SEM_MATERIA

_SEM_COMPETENCIA = _familia._SEM_COMPETENCIA

_SEM_VARA = _familia._SEM_VARA

_SEM_ATIVIDADE_RECURSOS = _familia._SEM_ATIVIDADE_RECURSOS

_SEM_FUNCIONARIO_RECURSOS = _familia._SEM_FUNCIONARIO_RECURSOS

# Setor RECURSOS (LexFlow) — escritório LA (``id_escritorio_assinante`` = 21)
_STATUS_AGENDAMENTO_ABERTO_RECURSOS = _familia._STATUS_AGENDAMENTO_ABERTO_RECURSOS

_STATUS_AGENDAMENTO_ENCERRADO_RECURSOS = _familia._STATUS_AGENDAMENTO_ENCERRADO_RECURSOS

# Status exibidos nos filtros da lista de tarefas (ordem fixa + extras do dataset)
_STATUS_FILTRO_TAREFAS_RECURSOS_LA = _familia._STATUS_FILTRO_TAREFAS_RECURSOS

_SITUACOES_FILTRO_TAREFAS_RECURSOS_LA = _familia._SITUACOES_FILTRO_TAREFAS_RECURSOS

# Ordem e slugs para gráfico de demandas encerradas por funcionário
_STATUS_DEMANDAS_FUNCIONARIO_LA = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS_AGENDAMENTO_RECURSOS = _familia._SLUG_POR_STATUS_AGENDAMENTO_RECURSOS
# Atividades de retorno (inconformidade) não contam como demanda encerrada
# no gráfico "Demandas por funcionário".
_ATIVIDADES_EXCLUIDAS_DEMANDAS_FUNCIONARIO_LA = frozenset({
    "RETORNO ELABORAÇÃO INCONFORMIDADE",
    "RETORNO ANÁLISE INCONFORMIDADE",
})

# Catálogo de atividades do setor RECURSOS (LA) — dinâmico, lido do banco
# (``setor_atividade`` / ``atividade`` do LexFlow, ``id_setor`` = 16). Antes era uma
# lista fixa no código (28 atividades) que ficou desatualizada e fazia tarefas de
# atividades novas somem silenciosamente dos KPIs (ex.: "ELABORAR CONTRARRAZÕES
# APELAÇÃO", "ELABORAR CONTRARRAZOES INOMINADO", "DILIGÊNCIA HT/NHT" e "REVISAR
# MEMORIAIS HT/NHT" nunca chegaram a entrar na lista, apesar de ativas no LexFlow —
# achado em 2026-09-16). Agora, como no NG, o catálogo é atualizado via
# ``set_atividades_recursos_LA_catalogo`` a cada ciclo de fetch.
_ATIVIDADES_RECURSOS_LA: tuple[tuple[int, str], ...] = ()
_IDS_ATIVIDADE_RECURSOS_LA: frozenset[int] = frozenset()
_NOMES_ATIVIDADE_RECURSOS_LA: frozenset[str] = frozenset()


def set_atividades_recursos_LA_catalogo(catalogo: list[dict[str, Any]]) -> None:
    """
    Atualiza o catálogo dinâmico de atividades ativas do setor RECURSOS (LA).

    ``catalogo`` vem da query ``atividades_setor_recursos_LA`` (cacheada), com linhas
    ``{"id_atividade": int, "ATIVIDADE": str}``. Deve ser chamada antes de qualquer
    análise que dependa do catálogo (ex.: ``_build_recursal_LA_stats``).
    """
    global _ATIVIDADES_RECURSOS_LA, _IDS_ATIVIDADE_RECURSOS_LA, _NOMES_ATIVIDADE_RECURSOS_LA
    pares = tuple(
        (int(row["id_atividade"]), str(row["ATIVIDADE"]).strip())
        for row in catalogo
        if row.get("id_atividade") is not None and str(row.get("ATIVIDADE") or "").strip()
    )
    _ATIVIDADES_RECURSOS_LA = pares
    _IDS_ATIVIDADE_RECURSOS_LA = frozenset(aid for aid, _ in pares)
    _NOMES_ATIVIDADE_RECURSOS_LA = frozenset(nome for _, nome in pares)

_RESULTADO_FAV = _familia._RESULTADO_FAV

_RESULTADO_DES = _familia._RESULTADO_DES

_RESULTADO_OUTROS = _familia._RESULTADO_OUTROS

# ``public.status_primeiro_grau`` (LexFlow) — IDs usados na fase Recursal LA
_ID_1G_ACORDO_HOMOLOGADO = _familia._ID_1G_ACORDO_HOMOLOGADO

_ID_1G_EXTINTO_SEM_MERITO = _familia._ID_1G_EXTINTO_SEM_MERITO

_ID_1G_IMPROCEDENTE = _familia._ID_1G_IMPROCEDENTE

_ID_1G_PROCEDENTE_COM_PE = _familia._ID_1G_PROCEDENTE_COM_PE

_ID_1G_PARC_PROCEDENTE_COM_PE = _familia._ID_1G_PARC_PROCEDENTE_COM_PE

_ID_1G_PROCEDENTE_SEM_PE = _familia._ID_1G_PROCEDENTE_SEM_PE

_ID_1G_PARC_PROCEDENTE_SEM_PE = _familia._ID_1G_PARC_PROCEDENTE_SEM_PE
# Aliases legados (compatibilidade interna)
_ID_1G_SENTENCA_FAVORAVEL = _familia._ID_1G_SENTENCA_FAVORAVEL

_ID_1G_SENTENCA_DESFAVORAVEL = _familia._ID_1G_SENTENCA_DESFAVORAVEL

_ID_1G_PROCEDENTE = _familia._ID_1G_PROCEDENTE

_ID_1G_PARCIALMENTE_PROCEDENTE = _familia._ID_1G_PARCIALMENTE_PROCEDENTE

_ID_1G_SENTENCA_EXTINCAO = _familia._ID_1G_SENTENCA_EXTINCAO

_ID_1G_SENTENCA_PARCIALMENTE_FAVORAVEL = _familia._ID_1G_SENTENCA_PARCIALMENTE_FAVORAVEL

# Ordem de exibição nos gráficos (somente status com volume na recursal)
_STATUS_1G_RECURSAL_LA = _familia._STATUS_1G_RECURSAL

# ``public.status_segundo_grau`` (LexFlow) — IDs usados na fase Recursal LA
_ID_2G_ACORDO_HOMOLOGADO = _familia._ID_2G_ACORDO_HOMOLOGADO

_ID_2G_EXTINTO_SEM_MERITO = _familia._ID_2G_EXTINTO_SEM_MERITO

_ID_2G_IMPROCEDENTE = _familia._ID_2G_IMPROCEDENTE

_ID_2G_PARC_PROCEDENTE_COM_PE = _familia._ID_2G_PARC_PROCEDENTE_COM_PE

_ID_2G_PROCEDENTE_COM_PE = _familia._ID_2G_PROCEDENTE_COM_PE

_ID_2G_SENTENCA_ANULADA = _familia._ID_2G_SENTENCA_ANULADA

_ID_2G_ENCERRADO_1G = _familia._ID_2G_ENCERRADO_1G

_ID_2G_PROCEDENTE_SEM_PE = _familia._ID_2G_PROCEDENTE_SEM_PE

_ID_2G_PARC_PROCEDENTE_SEM_PE = _familia._ID_2G_PARC_PROCEDENTE_SEM_PE
# Aliases legados (compatibilidade interna)
_ID_2G_ACORDAO_DESFAVORAVEL = _familia._ID_2G_ACORDAO_DESFAVORAVEL

_ID_2G_ACORDAO_FAVORAVEL = _familia._ID_2G_ACORDAO_FAVORAVEL

_ID_2G_ACORDAO_PARCIALMENTE_FAVORAVEL = _familia._ID_2G_ACORDAO_PARCIALMENTE_FAVORAVEL

_ID_2G_ACORDAO_PARCIAL_RETOMADA_INSTRUCAO = _familia._ID_2G_ACORDAO_PARCIAL_RETOMADA_INSTRUCAO

_ID_2G_ACORDAO_EXTINCAO = _familia._ID_2G_ACORDAO_EXTINCAO

_ID_2G_SENTENCA_ANULADA_NOVA = _familia._ID_2G_SENTENCA_ANULADA_NOVA

_ID_2G_PROCEDENTE_COM_PE_NOVO = _familia._ID_2G_PROCEDENTE_COM_PE_NOVO

_ID_2G_PARC_PROCEDENTE_COM_PE_NOVO = _familia._ID_2G_PARC_PROCEDENTE_COM_PE_NOVO

_ID_2G_PROCEDENTE_SEM_PE_NOVO = _familia._ID_2G_PROCEDENTE_SEM_PE_NOVO

_ID_2G_PARC_PROCEDENTE_SEM_PE_NOVO = _familia._ID_2G_PARC_PROCEDENTE_SEM_PE_NOVO

_ID_2G_IMPROCEDENTE_NOVO = _familia._ID_2G_IMPROCEDENTE_NOVO

_STATUS_2G_RECURSAL_LA = _familia._STATUS_2G_RECURSAL

# =============================================================================
# Grupos semânticos 1G × 2G — Matriz de Classificação (Resultado 1G × 2G)
# =============================================================================

# Linha 1G → categoria
_IDS_1G_PROCEDENTE_COM_PE = _familia._IDS_1G_PROCEDENTE_COM_PE

_IDS_1G_PROCEDENTE_SEM_PE = _familia._IDS_1G_PROCEDENTE_SEM_PE

_IDS_1G_PARC_PROCEDENTE_COM_PE = _familia._IDS_1G_PARC_PROCEDENTE_COM_PE

_IDS_1G_PARC_PROCEDENTE_SEM_PE = _familia._IDS_1G_PARC_PROCEDENTE_SEM_PE

_IDS_1G_IMPROCEDENTE_DECISAO = _familia._IDS_1G_IMPROCEDENTE_DECISAO

_IDS_1G_EXTINTO_DECISAO = _familia._IDS_1G_EXTINTO_DECISAO

_IDS_1G_ACORDO_DECISAO = _familia._IDS_1G_ACORDO_DECISAO

# Coluna 2G → categoria
_IDS_2G_PROCEDENTE_COM_PE = _familia._IDS_2G_PROCEDENTE_COM_PE

_IDS_2G_PROCEDENTE_SEM_PE = _familia._IDS_2G_PROCEDENTE_SEM_PE

_IDS_2G_PARC_PROCEDENTE_COM_PE = _familia._IDS_2G_PARC_PROCEDENTE_COM_PE

_IDS_2G_PARC_PROCEDENTE_SEM_PE = _familia._IDS_2G_PARC_PROCEDENTE_SEM_PE

_IDS_2G_IMPROCEDENTE_DECISAO = _familia._IDS_2G_IMPROCEDENTE_DECISAO

_IDS_2G_EXTINCAO_SEM_MERITO = _familia._IDS_2G_EXTINCAO_SEM_MERITO

_IDS_2G_SENTENCA_ANULADA = _familia._IDS_2G_SENTENCA_ANULADA

# Cruzamento 1G × 2G — "Resultado Mapeado" (Matriz de Julgamento, ver
# ``app.analyses.common.matriz_julgamento``). Os 10 tipos antigos (com a
# distinção COM/SEM PE embutida no nome do bucket, "Acordo Homologado" e
# "Extinção Mantida (Reajuizar)") foram substituídos pelos 8 buckets da nova
# matriz de mérito — a distinção de PE agora é um atributo à parte
# (``efeito_pe`` na planilha, não modelado aqui) e Acordo virou um eixo
# próprio, fora de escopo desta migração (ver plano de 2026-09-15).
DECISAO_MANTIDO_GANHO = _familia.DECISAO_MANTIDO_GANHO

DECISAO_GANHO_AMPLIADO = _familia.DECISAO_GANHO_AMPLIADO

DECISAO_REVERTIDO_GANHO = _familia.DECISAO_REVERTIDO_GANHO

DECISAO_GANHO_REDUZIDO = _familia.DECISAO_GANHO_REDUZIDO

DECISAO_EXTINCAO_REAJUIZAR = _familia.DECISAO_EXTINCAO_REAJUIZAR

DECISAO_INSTRUCAO_RETOMADA = _familia.DECISAO_INSTRUCAO_RETOMADA

DECISAO_MANTIDO_PERDA = _familia.DECISAO_MANTIDO_PERDA

DECISAO_REVERTIDO_PERDA = _familia.DECISAO_REVERTIDO_PERDA

_LABEL_DECISAO_RECURSAL = _familia._LABEL_DECISAO_RECURSAL

_EXTINTOS_2G_FILTRO_VALIDOS = _familia._EXTINTOS_2G_FILTRO_VALIDOS

_LABEL_EXTINTO_2G = _familia._LABEL_EXTINTO_2G

_DECISOES_RECURSAL_ORDEM = _familia._DECISOES_RECURSAL_ORDEM

# Grupos legados (mantidos para compatibilidade com funções de ranking/resultado)
_IDS_1G_FAVORAVEL = _familia._IDS_1G_FAVORAVEL

_IDS_1G_DESFAVORAVEL = _familia._IDS_1G_DESFAVORAVEL

_IDS_1G_OUTROS = _familia._IDS_1G_OUTROS

_IDS_2G_FAVORAVEL = _familia._IDS_2G_FAVORAVEL

_IDS_2G_DESFAVORAVEL = _familia._IDS_2G_DESFAVORAVEL

_IDS_2G_OUTROS = _familia._IDS_2G_OUTROS


# =============================================================================
# Helpers internos
# =============================================================================

_converter_valor = _familia._converter_valor


_get_valor_causa_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_causa_acordo)


_get_valor_causa_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_causa_sentenca)


_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_base_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_recurso)


_processo_fase_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_fase_recursal)


_get_id_atividade_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_atividade_recursos)


_get_nome_atividade_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_nome_atividade_recursos)


_status_agendamento_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._status_agendamento_recursos)


_atividade_recursos_catalogo_valida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._atividade_recursos_catalogo_valida)


_rotulo_atividade_recursos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_atividade_recursos)


_filtrar_recursos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_recursos)


_get_dt_entrada_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_dt_entrada_recursal)


_get_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_sentenca)


_get_data_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao)


_valor_coluna_preenchido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_coluna_preenchido)


_col_recursal_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._col_recursal)


_get_numero_processo_recursal_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_numero_processo_recursal)


_mesclar_item_processo_recursal_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._mesclar_item_processo_recursal)


_chave_processo_recursal_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._chave_processo_recursal)


_deduplicar_por_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._deduplicar_por_processo)


_enriquecer_numero_processo_export_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._enriquecer_numero_processo_export)


_filtrar_fase_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_fase_recursal)


_filtrar_entrada_recursal_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_recursal_no_periodo)


# =============================================================================
# Totais
# =============================================================================

get_total_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_recurso)


_rotulo_subfase_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_subfase_recursal)


_rotulo_fase_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_fase_recursal)


_rotulo_operacao_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_operacao_recursal)


_rotulo_parte_adversa_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_parte_adversa_recursal)


_normalizar_materia_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia_recursal)


_rotulo_competencia_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_competencia_recursal)


_rotulo_vara_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_vara_recursal)


_processos_recursal_por_base = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processos_recursal_por_base)


_agrupar_recursal_por_chave = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agrupar_recursal_por_chave)


group_recursal_por_subfase_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_subfase)


group_recursal_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_atividade)


group_recursal_por_materia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_materia)


group_recursal_por_competencia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_competencia)


group_recursal_por_vara_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_vara)


get_entrada_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_entrada_recurso)

# =============================================================================
# Valores monetários
# =============================================================================

get_valor_causa_acordo_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordo_recurso)


# =============================================================================
# Totais por status 1º grau (``ID_1G`` / ``STATUS_1G``)
# =============================================================================

_filtrar_por_id_status_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_id_status_1g)


get_total_por_id_status_1g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_id_status_1g_recurso)


get_valor_causa_sentenca_por_id_status_1g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_por_id_status_1g_recurso)


get_total_sentenca_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_favoravel_recurso)


get_valor_causa_sentenca_sentenca_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_favoravel_recurso)


get_total_sentenca_desfavoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_desfavoravel_recurso)


get_valor_causa_sentenca_sentenca_desfavoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_desfavoravel_recurso)


get_total_procedente_1g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_procedente_1g_recurso)


get_valor_causa_sentenca_procedente_1g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_procedente_1g_recurso)


get_total_parcialmente_procedente_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_parcialmente_procedente_recurso)


get_valor_causa_sentenca_parcialmente_procedente_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_parcialmente_procedente_recurso)


get_total_sentenca_extincao_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_extincao_recurso)


get_valor_causa_sentenca_sentenca_extincao_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_extincao_recurso)


get_total_sentenca_parcialmente_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_parcialmente_favoravel_recurso)


get_valor_causa_sentenca_parcialmente_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_parcialmente_favoravel_recurso)


group_recursal_por_status_1g_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_status_1g)


# =============================================================================
# Totais por status 2º grau (``ID_2G`` / ``STATUS_2G``)
# =============================================================================

_filtrar_por_id_status_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_id_status_2g)


get_total_por_id_status_2g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_id_status_2g_recurso)


get_valor_causa_por_id_status_2g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_por_id_status_2g_recurso)


get_total_acordao_desfavoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_desfavoravel_recurso)


get_valor_causa_acordao_desfavoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_desfavoravel_recurso)


get_total_acordao_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_favoravel_recurso)


get_valor_causa_acordao_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_favoravel_recurso)


get_total_acordao_parcialmente_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_parcialmente_favoravel_recurso)


get_valor_causa_acordao_parcialmente_favoravel_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_parcialmente_favoravel_recurso)


get_total_acordao_parcial_retomada_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_parcial_retomada_recurso)


get_valor_causa_acordao_parcial_retomada_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_parcial_retomada_recurso)


get_total_acordao_extincao_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_extincao_recurso)


get_valor_causa_acordao_extincao_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_extincao_recurso)


group_recursal_por_status_2g_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_status_2g)


# =============================================================================
# Análise de decisões (cruzamento 1G × 2G)
# =============================================================================

_classificar_decisao_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_decisao_recursal)


_get_id_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_1g)


_get_id_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_2g)


_get_id_merito_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_merito_1g)


_get_id_merito_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_merito_2g)


rotulo_decisao_recursal_export_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.rotulo_decisao_recursal_export)


_filtrar_decisoes_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_decisoes_recursal)


get_total_decisoes_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_decisoes_recursal)


get_total_por_tipo_decisao_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_tipo_decisao_recursal)


get_valor_causa_por_tipo_decisao_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_por_tipo_decisao_recursal)


_percentual_decisao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._percentual_decisao)


get_decisoes_recursal_resumo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_decisoes_recursal_resumo)


group_decisoes_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_decisoes_recursal)


# =============================================================================
# Rankings por juiz (1G / sentença) e relator (2G / acórdão)
# =============================================================================

_normalizar_nome_magistrado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_nome_magistrado)


_iniciais_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._iniciais_nome)


_nome_magistrado_coincide = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_magistrado_coincide)


_classificar_resultado_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_resultado_1g)


_classificar_resultado_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_resultado_2g)


_get_juiz_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_juiz_1g)


_get_relator_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_relator_2g)


filtrar_por_juiz_1g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_por_juiz_1g_recurso)


filtrar_por_relator_2g_recurso_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_por_relator_2g_recurso)


_montar_ranking_magistrado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._montar_ranking_magistrado)


get_ranking_juizes_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_recursal)


get_ranking_relatores_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_relatores_recursal)


# =============================================================================
# Filtros combinados (status 1G/2G, juiz, relator, decisão)
# =============================================================================

RecursalLAFiltros = _familia.RecursalLAFiltros


_classificar_extinto_2g_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_extinto_2g_recursal)


_nome_em_conjunto_filtro = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_filtro)


filtrar_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_recursal)


get_opcoes_filtros_recursal_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_recursal)


_ordem_rotulo_vara = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._ordem_rotulo_vara)


# =============================================================================
# KPIs — agendamentos do setor RECURSOS (LexFlow)
# =============================================================================

_get_agendamento_status = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_status)


_get_agendamento_data_criacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_criacao)


_get_agendamento_data_conclusao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_conclusao)


_get_agendamento_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_prazo)


_agendamento_atividade_recursos_valida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_atividade_recursos_valida)


def get_kpis_atividades_recursos_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor RECURSOS no período selecionado.

    - **Total**: criadas no período (``DATA_HORA_CRIACAO``)
    - **Em andamento**: criadas no período e ainda abertas (Recebido / Visualizado)
    - **Vencidas**: abertas criadas no período com ``PRAZO`` anterior a ``ref_date``
    - **Vencem hoje**: abertas criadas no período com ``PRAZO`` = ``ref_date``
    - **Concluídas**: encerradas no período (``DATA_HORA_CONCLUSAO``)
    """
    ref = ref_date or date.today()
    rows = [row for row in agendamentos if _agendamento_atividade_recursos_valida(row)]

    total = 0
    em_andamento = 0
    vencidas = 0
    vencem_hoje = 0
    concluidas = 0

    for row in rows:
        criacao = _get_agendamento_data_criacao(row)
        conclusao = _get_agendamento_data_conclusao(row)
        status = _get_agendamento_status(row) or ""
        prazo = _get_agendamento_prazo(row)
        aberta = status in _STATUS_AGENDAMENTO_ABERTO_RECURSOS

        if _data_no_periodo(criacao, from_date, to_date):
            total += 1
            if aberta:
                em_andamento += 1
                if prazo is not None:
                    if prazo < ref:
                        vencidas += 1
                    elif prazo == ref:
                        vencem_hoje += 1

        if status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
            if _data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_recursos_LA": total,
        "atividades_recursos_em_andamento_LA": em_andamento,
        "atividades_recursos_vencidas_LA": vencidas,
        "atividades_recursos_vencem_hoje_LA": vencem_hoje,
        "atividades_recursos_concluidas_LA": concluidas,
    }


def get_kpis_atividades_recursos_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor RECURSOS usando ``PRAZO`` como eixo temporal,
    em vez de criação/conclusão (mesma lógica de
    ``get_kpis_emendas_manifestacoes_por_prazo_NG``/``get_kpis_atividades_recursos_por_prazo_NG``).

    - **Total**: abertas (Recebido/Visualizado) com ``PRAZO`` no período
    - **Em andamento**: coincide com Total (toda aberta já conta como "em andamento")
    - **Vencidas**: abertas com ``PRAZO`` no período anterior a ``ref_date``
    - **Vencem hoje**: abertas com ``PRAZO`` no período igual a ``ref_date``
    - **Concluídas**: encerradas com ``PRAZO`` no período (contagem separada do Total)
    """
    ref = ref_date or date.today()
    rows = [row for row in agendamentos if _agendamento_atividade_recursos_valida(row)]

    total = 0
    em_andamento = 0
    vencidas = 0
    vencem_hoje = 0
    concluidas = 0

    for row in rows:
        prazo = _get_agendamento_prazo(row)
        status = _get_agendamento_status(row) or ""
        if not _data_no_periodo(prazo, from_date, to_date):
            continue

        if status in _STATUS_AGENDAMENTO_ABERTO_RECURSOS:
            total += 1
            em_andamento += 1
            if prazo is not None and prazo < ref:
                vencidas += 1
            elif prazo is not None and prazo == ref:
                vencem_hoje += 1
        elif status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
            concluidas += 1

    return {
        "total_por_prazo_atividades_recursos_LA": total,
        "por_prazo_em_andamento_atividades_recursos_LA": em_andamento,
        "por_prazo_vencidas_atividades_recursos_LA": vencidas,
        "por_prazo_vencem_hoje_atividades_recursos_LA": vencem_hoje,
        "por_prazo_concluidas_atividades_recursos_LA": concluidas,
    }


_get_agendamento_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_processo_id)


_get_agendamento_atividade_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_atividade_nome)


_get_agendamento_funcionario_atribuido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_atribuido)


_get_agendamento_funcionario_encerramento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_encerramento)


_get_agendamento_funcionario_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_nome)


_agendamento_tem_encerrador_identificado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_tem_encerrador_identificado)


_filtrar_agendamentos_recursos_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_agendamentos_recursos_no_periodo)


_filtrar_agendamentos_encerrados_recursos_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_agendamentos_encerrados_recursos_no_periodo)


_agrupar_processos_distintos_por_chave = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agrupar_processos_distintos_por_chave)


group_recursal_processos_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_processos_por_atividade)


_status_agendamento_para_slug_demandas = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._status_agendamento_para_slug_demandas)


def group_recursal_demandas_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido),
    com ``DATA_HORA_CONCLUSAO`` no período.

    Contabiliza somente registros com ``id_usuario_encerramento`` preenchido;
    o nome exibido vem de ``nome_usuario_encerramento`` (quem de fato encerrou,
    que pode diferir do responsável atribuído).
    """
    base = _filtrar_agendamentos_encerrados_recursos_no_periodo(
        agendamentos,
        from_date=from_date,
        to_date=to_date,
        exigir_encerrador=True,
    )

    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        if (
            _get_agendamento_atividade_nome(row).upper()
            in _ATIVIDADES_EXCLUIDAS_DEMANDAS_FUNCIONARIO_LA
        ):
            continue
        funcionario = _get_agendamento_funcionario_encerramento(row)
        if not funcionario:
            continue
        slug = _status_agendamento_para_slug_demandas(_get_agendamento_status(row))
        if slug not in {s for s, _ in _STATUS_DEMANDAS_FUNCIONARIO_LA}:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_LA:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)

    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def group_recursal_resolvidos_por_dia_LA(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária: quantidade de atividades do setor RECURSOS "Encerrado
    Cumprido" por dia de conclusão (``DATA_HORA_CONCLUSAO``), histórico
    completo — LA. O filtro por período (calendário do dashboard) é aplicado
    no frontend, como em :func:`group_execucao_resolvidos_por_dia_LA`.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != "Encerrado Cumprido":
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


_MESES_ABREVIADOS_LA = _familia._MESES_ABREVIADOS


def group_recursal_resolvidos_por_mes_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Produção mensal: quantidade de atividades do setor RECURSOS "Encerrado
    Cumprido" por mês de conclusão (``DATA_HORA_CONCLUSAO``) — LA. Usado como
    visão inicial (drill-down) de :func:`group_recursal_resolvidos_por_dia_LA`.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != "Encerrado Cumprido":
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None or not _data_no_periodo(conclusao, from_date, to_date):
            continue
        month_key = f"{conclusao.year}-{conclusao.month:02d}"
        if month_key not in grouped:
            month_name = f"{_MESES_ABREVIADOS_LA[conclusao.month - 1]} {conclusao.year}"
            grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
        grouped[month_key]["value"] += 1

    return [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]


def get_recursal_resolvidos_por_dia_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """
    Produção diária por funcionário (encerrador) — LA. Usado para recalcular a
    visão mensal/diária de produção quando o filtro de funcionário da seção
    Atividades está ativo (mesmo mecanismo de Réplicas).
    """
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != "Encerrado Cumprido":
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None or not _data_no_periodo(conclusao, from_date, to_date):
            continue
        funcionario = _get_agendamento_funcionario_encerramento(row)
        if not funcionario:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")][funcionario] += 1

    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted({f for dia_data in grouped.values() for f in dia_data.keys()})
    por_funcionario = {
        func: [
            {"name": dia, "value": grouped[dia].get(func, 0)}
            for dia in dias_ordenados
        ]
        for func in funcionarios
    }
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}


def get_media_recursal_resolvidos_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Média de atividades do setor RECURSOS "Encerrado Cumprido" por
    funcionário no período (LA).

    Média = total de atividades cumpridas ÷ número de dias distintos com
    conclusão no período, mesmo critério de
    :func:`get_media_execucao_resolvidos_por_funcionario_LA`.
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != "Encerrado Cumprido":
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None or not _data_no_periodo(conclusao, from_date, to_date):
            continue
        funcionario = _get_agendamento_funcionario_encerramento(row)
        if not funcionario:
            continue
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["dias"].add(conclusao)

    itens: list[dict[str, Any]] = []
    for nome, info in grouped.items():
        dias = len(info["dias"])
        if dias == 0:
            continue
        itens.append({"name": nome, "value": round(info["total"] / dias, 2)})
    return sorted(itens, key=lambda x: x["value"], reverse=True)


_formatar_pessoa_setor_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._formatar_pessoa_setor_recursos)


_formatar_descricao_tarefa_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._formatar_descricao_tarefa_recursos)


_get_agendamento_atividade_nome_lista = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_atividade_nome_lista)


_agendamento_incluir_lista_tarefas_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_incluir_lista_tarefas_recursos)


_classificar_situacao_tarefa_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_tarefa_recursos)


_SITUACOES_RECURSOS_VALIDAS = _familia._SITUACOES_RECURSOS_VALIDAS


RecursalAtividadesRecursosFiltros = _familia.RecursalAtividadesRecursosFiltros


_agendamento_match_filtros_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_recursos)


filtrar_agendamentos_recursos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_recursos)


_get_recurso_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_recurso_processo_id)


processo_ids_recursal_de_agendamentos_recursos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.processo_ids_recursal_de_agendamentos_recursos)


filtrar_recursal_LA_por_processo_ids = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_recursal_por_processo_ids)


list_recursal_atividades_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_recursal_atividades_periodo)


get_opcoes_filtros_atividades_lista_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_atividades_lista)
