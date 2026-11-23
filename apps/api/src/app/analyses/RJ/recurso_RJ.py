# Funções de análises do setor da Fase Recursal — Escritório RJ (LAADV RJ, id 27)
# Réplica de ``analyses/NG/recurso_NG.py`` (sem comissionamento: RJ não tem regra definida).

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import recurso as _familia  # V2: código único da família (familias/recurso.py)
import json
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
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"ID_ESCRITORIO": "ID_ESCRITORIO", "ID_SETOR_RECURSOS": "ID_SETOR_RECURSOS_RJ", "_IDS_FAMILIA_AVR_RETORNO": "_IDS_FAMILIA_AVR_RETORNO_RJ", "_IDS_FAMILIA_RETORNO_CR": "_IDS_FAMILIA_RETORNO_CR_RJ", "_ATIVIDADES_RECURSOS": "_ATIVIDADES_RECURSOS_RJ", "_IDS_ATIVIDADE_RECURSOS": "_IDS_ATIVIDADE_RECURSOS_RJ", "_NOMES_ATIVIDADE_RECURSOS": "_NOMES_ATIVIDADE_RECURSOS_RJ"})

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO = 27
ID_FASE_RECURSAL = _familia.ID_FASE_RECURSAL
ID_SETOR_RECURSOS_RJ = 198

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

_COL_DATA_ACORDAO_EMBARGOS = _familia._COL_DATA_ACORDAO_EMBARGOS

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

# Setor RECURSOS (LexFlow) — escritório RJ (``id_escritorio_assinante`` = 27)
_STATUS_AGENDAMENTO_ABERTO_RECURSOS = _familia._STATUS_AGENDAMENTO_ABERTO_RECURSOS

_STATUS_AGENDAMENTO_ENCERRADO_RECURSOS = _familia._STATUS_AGENDAMENTO_ENCERRADO_RECURSOS

# Status exibidos nos filtros da lista de tarefas (ordem fixa + extras do dataset)
_STATUS_FILTRO_TAREFAS_RECURSOS_RJ = _familia._STATUS_FILTRO_TAREFAS_RECURSOS

_SITUACOES_FILTRO_TAREFAS_RECURSOS_RJ = _familia._SITUACOES_FILTRO_TAREFAS_RECURSOS

# Ordem e slugs para gráfico de demandas encerradas por funcionário
_STATUS_DEMANDAS_FUNCIONARIO_RJ = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS_AGENDAMENTO_RECURSOS = _familia._SLUG_POR_STATUS_AGENDAMENTO_RECURSOS

# Catálogo de atividades do setor RECURSOS (RJ) — dinâmico, lido do banco
# (``setor_atividade`` / ``atividade`` do LexFlow, ``id_setor`` = 198). O RJ usa uma
# nomenclatura própria e bem mais granular (65+ atividades) que a LA (``id_setor`` = 16,
# ver ``set_atividades_recursos_LA_catalogo`` em ``recurso_LA.py``, mesmo padrão). O
# catálogo é atualizado via ``set_atividades_recursos_RJ_catalogo`` a cada ciclo de
# fetch, para que novas atividades cadastradas no setor apareçam automaticamente, sem
# precisar alterar código.
_ATIVIDADES_RECURSOS_RJ: tuple[tuple[int, str], ...] = ()
_IDS_ATIVIDADE_RECURSOS_RJ: frozenset[int] = frozenset()
_NOMES_ATIVIDADE_RECURSOS_RJ: frozenset[str] = frozenset()


def set_atividades_recursos_RJ_catalogo(catalogo: list[dict[str, Any]]) -> None:
    """
    Atualiza o catálogo dinâmico de atividades ativas do setor RECURSOS (RJ).

    ``catalogo`` vem da query ``atividades_setor_recursos_RJ`` (cacheada), com linhas
    ``{"id_atividade": int, "ATIVIDADE": str}``. Deve ser chamada antes de qualquer
    análise que dependa do catálogo (ex.: ``_build_recursal_RJ_stats``).
    """
    global _ATIVIDADES_RECURSOS_RJ, _IDS_ATIVIDADE_RECURSOS_RJ, _NOMES_ATIVIDADE_RECURSOS_RJ
    pares = tuple(
        (int(row["id_atividade"]), str(row["ATIVIDADE"]).strip())
        for row in catalogo
        if row.get("id_atividade") is not None and str(row.get("ATIVIDADE") or "").strip()
    )
    _ATIVIDADES_RECURSOS_RJ = pares
    _IDS_ATIVIDADE_RECURSOS_RJ = frozenset(aid for aid, _ in pares)
    _NOMES_ATIVIDADE_RECURSOS_RJ = frozenset(nome for _, nome in pares)

_RESULTADO_FAV = _familia._RESULTADO_FAV

_RESULTADO_DES = _familia._RESULTADO_DES

_RESULTADO_OUTROS = _familia._RESULTADO_OUTROS

# ``public.status_primeiro_grau`` (LexFlow) — IDs usados na fase Recursal (globais, válidos para RJ e LA)
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
_STATUS_1G_RECURSAL_RJ = _familia._STATUS_1G_RECURSAL

# ``public.status_segundo_grau`` (LexFlow) — IDs usados na fase Recursal (globais, válidos para RJ e LA)
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

_STATUS_2G_RECURSAL_RJ = _familia._STATUS_2G_RECURSAL

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


_base_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_recurso)


_processo_fase_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_fase_recursal)


_get_id_atividade_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_atividade_recursos)


_get_nome_atividade_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_nome_atividade_recursos)


_status_agendamento_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._status_agendamento_recursos)


_atividade_recursos_catalogo_valida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._atividade_recursos_catalogo_valida)


_rotulo_atividade_recursos_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_atividade_recursos)


_filtrar_recursos_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_recursos)


_get_dt_entrada_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_dt_entrada_recursal)


_get_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_sentenca)


_get_data_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao)


_get_data_acordao_embargos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao_embargos)


_get_data_acordao_provimento_mensal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao_provimento_mensal)


_valor_coluna_preenchido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_coluna_preenchido)


_col_recursal_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._col_recursal)


_get_numero_processo_recursal_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_numero_processo_recursal)


_mesclar_item_processo_recursal_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._mesclar_item_processo_recursal)


_chave_processo_recursal_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._chave_processo_recursal)


_deduplicar_por_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._deduplicar_por_processo)


_enriquecer_numero_processo_export_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._enriquecer_numero_processo_export)


_filtrar_fase_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_fase_recursal)


_filtrar_entrada_recursal_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_recursal_no_periodo)


# =============================================================================
# Totais
# =============================================================================

get_total_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_recurso)


_rotulo_subfase_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_subfase_recursal)


_rotulo_fase_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_fase_recursal)


_rotulo_operacao_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_operacao_recursal)


_rotulo_parte_adversa_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_parte_adversa_recursal)


_normalizar_materia_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia_recursal)


_rotulo_competencia_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_competencia_recursal)


_rotulo_vara_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_vara_recursal)


_processos_recursal_por_base = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processos_recursal_por_base)


_agrupar_recursal_por_chave = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agrupar_recursal_por_chave)


group_recursal_por_subfase_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_subfase)


group_recursal_por_atividade_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_atividade)


group_recursal_por_materia_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_materia)


group_recursal_por_competencia_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_competencia)


group_recursal_por_vara_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_vara)


get_entrada_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_entrada_recurso)

# =============================================================================
# Valores monetários
# =============================================================================

get_valor_causa_acordo_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordo_recurso)


# =============================================================================
# Totais por status 1º grau (``ID_1G`` / ``STATUS_1G``)
# =============================================================================

_filtrar_por_id_status_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_id_status_1g)


get_total_por_id_status_1g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_id_status_1g_recurso)


get_valor_causa_sentenca_por_id_status_1g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_por_id_status_1g_recurso)


get_total_sentenca_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_favoravel_recurso)


get_valor_causa_sentenca_sentenca_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_favoravel_recurso)


get_total_sentenca_desfavoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_desfavoravel_recurso)


get_valor_causa_sentenca_sentenca_desfavoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_desfavoravel_recurso)


get_total_procedente_1g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_procedente_1g_recurso)


get_valor_causa_sentenca_procedente_1g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_procedente_1g_recurso)


get_total_parcialmente_procedente_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_parcialmente_procedente_recurso)


get_valor_causa_sentenca_parcialmente_procedente_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_parcialmente_procedente_recurso)


get_total_sentenca_extincao_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_extincao_recurso)


get_valor_causa_sentenca_sentenca_extincao_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_extincao_recurso)


get_total_sentenca_parcialmente_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_parcialmente_favoravel_recurso)


get_valor_causa_sentenca_parcialmente_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_parcialmente_favoravel_recurso)


group_recursal_por_status_1g_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_status_1g)


# =============================================================================
# Totais por status 2º grau (``ID_2G`` / ``STATUS_2G``)
# =============================================================================

_filtrar_por_id_status_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_id_status_2g)


get_total_por_id_status_2g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_id_status_2g_recurso)


get_valor_causa_por_id_status_2g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_por_id_status_2g_recurso)


get_total_acordao_desfavoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_desfavoravel_recurso)


get_valor_causa_acordao_desfavoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_desfavoravel_recurso)


get_total_acordao_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_favoravel_recurso)


get_valor_causa_acordao_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_favoravel_recurso)


get_total_acordao_parcialmente_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_parcialmente_favoravel_recurso)


get_valor_causa_acordao_parcialmente_favoravel_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_parcialmente_favoravel_recurso)


get_total_acordao_parcial_retomada_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_parcial_retomada_recurso)


get_valor_causa_acordao_parcial_retomada_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_parcial_retomada_recurso)


get_total_acordao_extincao_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_extincao_recurso)


get_valor_causa_acordao_extincao_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_extincao_recurso)


# =============================================================================
# Meta de Provimento Mensal (RJ) — 80 processos providos/mês
# =============================================================================
#
# Conta processos com ``ID_2G`` em: Procedente (COM PE), Parc. Procedente (COM PE),
# Sentença Anulada (ambos os IDs legado/novo) e Procedente Sem Proveito Econômico —
# filtrado por ``DATA_ACORDAO`` no período, mesma base de ``group_recursal_por_status_2g_RJ``.

META_PROVIMENTO_MENSAL_RJ = _familia.META_PROVIMENTO_MENSAL

_IDS_2G_PROVIMENTO_MENSAL_RJ = _familia._IDS_2G_PROVIMENTO_MENSAL


get_total_provimento_mensal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_provimento_mensal)


group_recursal_por_status_2g_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_status_2g)


# =============================================================================
# Análise de decisões (cruzamento 1G × 2G)
# =============================================================================

_classificar_decisao_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_decisao_recursal)


_get_id_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_1g)


_get_id_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_2g)


_get_id_merito_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_merito_1g)


_get_id_merito_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_merito_2g)


rotulo_decisao_recursal_export_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.rotulo_decisao_recursal_export)


_filtrar_decisoes_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_decisoes_recursal)


get_total_decisoes_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_decisoes_recursal)


get_total_por_tipo_decisao_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_tipo_decisao_recursal)


get_valor_causa_por_tipo_decisao_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_por_tipo_decisao_recursal)


_percentual_decisao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._percentual_decisao)


get_decisoes_recursal_resumo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_decisoes_recursal_resumo)


group_decisoes_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_decisoes_recursal)


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


filtrar_por_juiz_1g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_por_juiz_1g_recurso)


filtrar_por_relator_2g_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_por_relator_2g_recurso)


_montar_ranking_magistrado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._montar_ranking_magistrado)


get_ranking_juizes_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_recursal)


get_ranking_relatores_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_relatores_recursal)


# =============================================================================
# Filtros combinados (status 1G/2G, juiz, relator, decisão)
# =============================================================================

RecursalLAFiltros = _familia.RecursalLAFiltros


_classificar_extinto_2g_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_extinto_2g_recursal)


_nome_em_conjunto_filtro = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_filtro)


filtrar_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_recursal)


get_opcoes_filtros_recursal_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_recursal)


_ordem_rotulo_vara = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._ordem_rotulo_vara)


# =============================================================================
# KPIs — agendamentos do setor RECURSOS (LexFlow)
# =============================================================================

_get_agendamento_status = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_status)


_get_agendamento_data_criacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_criacao)


_get_agendamento_data_conclusao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_conclusao)


_get_agendamento_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_prazo)


# =============================================================================
# Recurso Cancelado — AVR-RETORNO (análise equivocada) / RETORNO-CR (perda de prazo)
# =============================================================================
#
# O motivo "RECURSO CANCELADO OU ALTERADO" / "RECURSO ERRADO OU PERDIDO" NÃO
# fica registrado no encerramento das próprias "AVR - RETORNO"/"RETORNO - CR"
# — fica em ``agendamento.motivo_encaminhamento`` da atividade de ORIGEM (a
# que deu errado), quando ela é encerrada como "Cancelado" ou "Encerrado Não
# Cumprido". Esse jsonb também informa para qual ``id_setor_atividade`` de
# retorno o caso foi encaminhado (``itens[].id_setor_atividade``): validado
# contra os 4 casos reais em produção (2026-07). Aqui contamos pelo DESTINO
# (família AVR-RETORNO = análise de viabilidade equivocada; família
# RETORNO-CR = perda de prazo) — independente de quem cometeu o erro (isso é
# tratado no comissionamento do NG; o RJ não tem comissão).

_STATUS_AGENDAMENTO_CUMPRIDO = _familia._STATUS_AGENDAMENTO_CUMPRIDO

_STATUS_ORIGEM_ERRO_RJ = _familia._STATUS_ORIGEM_ERRO

_MOTIVOS_ERRO_RECURSO_RJ = _familia._MOTIVOS_ERRO_RECURSO

# Família "AVR - RETORNO": base (1909, staffada pela Confecção) + variantes
# 2G/CTRR/DECISÃO (staffadas pela Análise) — staffing verificado em
# usuario_setor_atividade (a base 1G é sempre invertida em relação às
# variantes 2G/CTRR/DECISÃO da mesma família).
_IDS_FAMILIA_AVR_RETORNO_RJ = frozenset({1909, 1924, 1921, 1938, 1949, 1954, 1944, 1952})
# Família "RETORNO - CR": base (1914, staffada pela Análise) + variantes
# (staffadas pela Confecção).
_IDS_FAMILIA_RETORNO_CR_RJ = frozenset({1914, 1928, 1923, 1939, 1950, 1955, 1945, 1953})


_get_agendamento_motivo_encaminhamento_itens = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_motivo_encaminhamento_itens)


_normalizar_motivo_encaminhamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_motivo_encaminhamento)


_itens_erro_recurso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._itens_erro_recurso)


_get_agendamento_data_cancelamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_cancelamento)


_get_agendamento_data_referencia_erro_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_referencia_erro)


_contar_recurso_cancelado_por_destino_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_recurso_cancelado_por_destino)


get_total_avr_retorno_recurso_cancelado_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_avr_retorno_recurso_cancelado)


get_total_retorno_cr_recurso_cancelado_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_retorno_cr_recurso_cancelado)


_agendamento_atividade_recursos_valida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_atividade_recursos_valida)


def get_kpis_atividades_recursos_RJ(
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
        "total_atividades_recursos_RJ": total,
        "atividades_recursos_em_andamento_RJ": em_andamento,
        "atividades_recursos_vencidas_RJ": vencidas,
        "atividades_recursos_vencem_hoje_RJ": vencem_hoje,
        "atividades_recursos_concluidas_RJ": concluidas,
    }


def get_kpis_atividades_recursos_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor RECURSOS usando ``PRAZO`` como eixo temporal,
    em vez de criação/conclusão (mesma lógica de
    ``get_kpis_emendas_manifestacoes_por_prazo_RJ``).

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
        "total_por_prazo_atividades_recursos_RJ": total,
        "por_prazo_em_andamento_atividades_recursos_RJ": em_andamento,
        "por_prazo_vencidas_atividades_recursos_RJ": vencidas,
        "por_prazo_vencem_hoje_atividades_recursos_RJ": vencem_hoje,
        "por_prazo_concluidas_atividades_recursos_RJ": concluidas,
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


group_recursal_processos_por_atividade_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_processos_por_atividade)


_status_agendamento_para_slug_demandas = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._status_agendamento_para_slug_demandas)


group_recursal_demandas_por_funcionario_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_demandas_por_funcionario)


group_recursal_resolvidos_por_dia_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_resolvidos_por_dia)


_MESES_ABREVIADOS_RJ = _familia._MESES_ABREVIADOS


group_recursal_resolvidos_por_mes_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_resolvidos_por_mes)


get_recursal_resolvidos_por_dia_por_funcionario_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_recursal_resolvidos_por_dia_por_funcionario)


get_media_recursal_resolvidos_por_funcionario_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_recursal_resolvidos_por_funcionario)


_formatar_pessoa_setor_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._formatar_pessoa_setor_recursos)


_formatar_descricao_tarefa_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._formatar_descricao_tarefa_recursos)


_get_agendamento_atividade_nome_lista = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_atividade_nome_lista)


_agendamento_incluir_lista_tarefas_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_incluir_lista_tarefas_recursos)


_classificar_situacao_tarefa_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_tarefa_recursos)


_SITUACOES_RECURSOS_VALIDAS = _familia._SITUACOES_RECURSOS_VALIDAS


RecursalAtividadesRecursosFiltros = _familia.RecursalAtividadesRecursosFiltros


_agendamento_match_filtros_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_recursos)


filtrar_agendamentos_recursos_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_recursos)


_get_recurso_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_recurso_processo_id)


processo_ids_recursal_de_agendamentos_recursos_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.processo_ids_recursal_de_agendamentos_recursos)


filtrar_recursal_RJ_por_processo_ids = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_recursal_por_processo_ids)


list_recursal_atividades_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_recursal_atividades_periodo)


get_opcoes_filtros_atividades_lista_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_atividades_lista)


# =============================================================================
# Extintos · 2º Grau (painel do Recursal)
# =============================================================================
#
# No NG esse painel lê do dashboard ``controle_processo_NG`` (campos
# ``controle_processo_extintos_*_recursal_NG``). O RJ não tem Controle de
# Processos, então os mesmos números são calculados aqui reaproveitando as
# funções do ``controle_processo_NG`` — que filtram ``ID_ESCRITORIO == 20`` na
# base. Para não duplicar a regra, as linhas do RJ (27) entram como cópias com o
# escritório trocado para 20; nada mais muda nas linhas.

def _linhas_rj_na_base_controle_ng(controle_processo: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from app.analyses.NG import controle_processo_NG as cp_ng

    return [
        {**row, _COL_ID_ESCRITORIO: cp_ng._ID_ESCRITORIO_NG}
        for row in controle_processo
        if _to_int(row.get(_COL_ID_ESCRITORIO)) == ID_ESCRITORIO
    ]


def get_extintos_2g_recursal_RJ(
    controle_processo: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Campos ``controle_processo_extintos_*_recursal_RJ`` (todas as situações, por ``DATA_ACORDAO``)."""
    from app.analyses.NG import controle_processo_NG as cp_ng

    base = _linhas_rj_na_base_controle_ng(controle_processo)
    kw = {"from_date": from_date, "to_date": to_date}
    return {
        "controle_processo_extintos_com_merito_2g_qtd_recursal_RJ":
            cp_ng.get_total_extintos_com_merito_2g_NG(base, **kw),
        "controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_RJ":
            cp_ng.get_valor_causa_acordao_total_extintos_com_merito_2g_NG(base, **kw),
        "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_RJ":
            cp_ng.get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG(base, **kw),
        "controle_processo_extintos_sem_merito_2g_qtd_recursal_RJ":
            cp_ng.get_total_extintos_sem_merito_2g_NG(base, **kw),
        "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_RJ":
            cp_ng.get_valor_causa_acordao_total_extintos_sem_merito_2g_NG(base, **kw),
        "controle_processo_taxa_provimento_2g_recursal_RJ":
            cp_ng.get_taxa_provimento_2g_NG(base, **kw),
    }
