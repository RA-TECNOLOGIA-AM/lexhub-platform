# Funções de análises do setor da Fase Recursal — Escritório Nicolas Gomes (NG)

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
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"ID_ESCRITORIO": "ID_ESCRITORIO", "ID_SETOR_RECURSOS": "ID_SETOR_RECURSOS_NG", "_IDS_FAMILIA_AVR_RETORNO": "_IDS_FAMILIA_AVR_RETORNO_NG", "_IDS_FAMILIA_RETORNO_CR": "_IDS_FAMILIA_RETORNO_CR_NG", "_ATIVIDADES_RECURSOS": "_ATIVIDADES_RECURSOS_NG", "_IDS_ATIVIDADE_RECURSOS": "_IDS_ATIVIDADE_RECURSOS_NG", "_NOMES_ATIVIDADE_RECURSOS": "_NOMES_ATIVIDADE_RECURSOS_NG"})

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO = 20
ID_FASE_RECURSAL = _familia.ID_FASE_RECURSAL
ID_SETOR_RECURSOS_NG = 149

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

# Setor RECURSOS (LexFlow) — escritório NG (``id_escritorio_assinante`` = 20)
_STATUS_AGENDAMENTO_ABERTO_RECURSOS = _familia._STATUS_AGENDAMENTO_ABERTO_RECURSOS

_STATUS_AGENDAMENTO_ENCERRADO_RECURSOS = _familia._STATUS_AGENDAMENTO_ENCERRADO_RECURSOS

# Status exibidos nos filtros da lista de tarefas (ordem fixa + extras do dataset)
_STATUS_FILTRO_TAREFAS_RECURSOS_NG = _familia._STATUS_FILTRO_TAREFAS_RECURSOS

_SITUACOES_FILTRO_TAREFAS_RECURSOS_NG = _familia._SITUACOES_FILTRO_TAREFAS_RECURSOS

# Ordem e slugs para gráfico de demandas encerradas por funcionário
_STATUS_DEMANDAS_FUNCIONARIO_NG = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS_AGENDAMENTO_RECURSOS = _familia._SLUG_POR_STATUS_AGENDAMENTO_RECURSOS

# Catálogo de atividades do setor RECURSOS (NG) — dinâmico, lido do banco
# (``setor_atividade`` / ``atividade`` do LexFlow, ``id_setor`` = 149). O NG usa uma
# nomenclatura própria e bem mais granular (65+ atividades) que a LA (``id_setor`` = 16,
# ver ``set_atividades_recursos_LA_catalogo`` em ``recurso_LA.py``, mesmo padrão). O
# catálogo é atualizado via ``set_atividades_recursos_NG_catalogo`` a cada ciclo de
# fetch, para que novas atividades cadastradas no setor apareçam automaticamente, sem
# precisar alterar código.
_ATIVIDADES_RECURSOS_NG: tuple[tuple[int, str], ...] = ()
_IDS_ATIVIDADE_RECURSOS_NG: frozenset[int] = frozenset()
_NOMES_ATIVIDADE_RECURSOS_NG: frozenset[str] = frozenset()


def set_atividades_recursos_NG_catalogo(catalogo: list[dict[str, Any]]) -> None:
    """
    Atualiza o catálogo dinâmico de atividades ativas do setor RECURSOS (NG).

    ``catalogo`` vem da query ``atividades_setor_recursos_NG`` (cacheada), com linhas
    ``{"id_atividade": int, "ATIVIDADE": str}``. Deve ser chamada antes de qualquer
    análise que dependa do catálogo (ex.: ``_build_recursal_NG_stats``).
    """
    global _ATIVIDADES_RECURSOS_NG, _IDS_ATIVIDADE_RECURSOS_NG, _NOMES_ATIVIDADE_RECURSOS_NG
    pares = tuple(
        (int(row["id_atividade"]), str(row["ATIVIDADE"]).strip())
        for row in catalogo
        if row.get("id_atividade") is not None and str(row.get("ATIVIDADE") or "").strip()
    )
    _ATIVIDADES_RECURSOS_NG = pares
    _IDS_ATIVIDADE_RECURSOS_NG = frozenset(aid for aid, _ in pares)
    _NOMES_ATIVIDADE_RECURSOS_NG = frozenset(nome for _, nome in pares)

_RESULTADO_FAV = _familia._RESULTADO_FAV

_RESULTADO_DES = _familia._RESULTADO_DES

_RESULTADO_OUTROS = _familia._RESULTADO_OUTROS

# ``public.status_primeiro_grau`` (LexFlow) — IDs usados na fase Recursal (globais, válidos para NG e LA)
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
_STATUS_1G_RECURSAL_NG = _familia._STATUS_1G_RECURSAL

# ``public.status_segundo_grau`` (LexFlow) — IDs usados na fase Recursal (globais, válidos para NG e LA)
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

_STATUS_2G_RECURSAL_NG = _familia._STATUS_2G_RECURSAL

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


_base_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_recurso)


_processo_fase_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_fase_recursal)


_get_id_atividade_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_atividade_recursos)


_get_nome_atividade_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_nome_atividade_recursos)


_status_agendamento_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._status_agendamento_recursos)


_atividade_recursos_catalogo_valida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._atividade_recursos_catalogo_valida)


_rotulo_atividade_recursos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_atividade_recursos)


_filtrar_recursos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_recursos)


_get_dt_entrada_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_dt_entrada_recursal)


_get_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_sentenca)


_get_data_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao)


_get_data_acordao_embargos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao_embargos)


_get_data_acordao_provimento_mensal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao_provimento_mensal)


_valor_coluna_preenchido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_coluna_preenchido)


_col_recursal_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._col_recursal)


_get_numero_processo_recursal_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_numero_processo_recursal)


_mesclar_item_processo_recursal_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._mesclar_item_processo_recursal)


_chave_processo_recursal_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._chave_processo_recursal)


_deduplicar_por_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._deduplicar_por_processo)


_enriquecer_numero_processo_export_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._enriquecer_numero_processo_export)


_filtrar_fase_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_fase_recursal)


_filtrar_entrada_recursal_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_recursal_no_periodo)


# =============================================================================
# Totais
# =============================================================================

get_total_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_recurso)


_rotulo_subfase_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_subfase_recursal)


_rotulo_fase_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_fase_recursal)


_rotulo_operacao_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_operacao_recursal)


_rotulo_parte_adversa_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_parte_adversa_recursal)


_normalizar_materia_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia_recursal)


_rotulo_competencia_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_competencia_recursal)


_rotulo_vara_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._rotulo_vara_recursal)


_processos_recursal_por_base = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processos_recursal_por_base)


_agrupar_recursal_por_chave = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agrupar_recursal_por_chave)


group_recursal_por_subfase_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_subfase)


group_recursal_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_atividade)


group_recursal_por_materia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_materia)


group_recursal_por_competencia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_competencia)


group_recursal_por_vara_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_vara)


get_entrada_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_entrada_recurso)

# =============================================================================
# Valores monetários
# =============================================================================

get_valor_causa_acordo_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordo_recurso)


# =============================================================================
# Totais por status 1º grau (``ID_1G`` / ``STATUS_1G``)
# =============================================================================

_filtrar_por_id_status_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_id_status_1g)


get_total_por_id_status_1g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_id_status_1g_recurso)


get_valor_causa_sentenca_por_id_status_1g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_por_id_status_1g_recurso)


get_total_sentenca_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_favoravel_recurso)


get_valor_causa_sentenca_sentenca_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_favoravel_recurso)


get_total_sentenca_desfavoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_desfavoravel_recurso)


get_valor_causa_sentenca_sentenca_desfavoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_desfavoravel_recurso)


get_total_procedente_1g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_procedente_1g_recurso)


get_valor_causa_sentenca_procedente_1g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_procedente_1g_recurso)


get_total_parcialmente_procedente_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_parcialmente_procedente_recurso)


get_valor_causa_sentenca_parcialmente_procedente_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_parcialmente_procedente_recurso)


get_total_sentenca_extincao_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_extincao_recurso)


get_valor_causa_sentenca_sentenca_extincao_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_sentenca_extincao_recurso)


get_total_sentenca_parcialmente_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentenca_parcialmente_favoravel_recurso)


get_valor_causa_sentenca_parcialmente_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_sentenca_parcialmente_favoravel_recurso)


group_recursal_por_status_1g_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_status_1g)


# =============================================================================
# Totais por status 2º grau (``ID_2G`` / ``STATUS_2G``)
# =============================================================================

_filtrar_por_id_status_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_id_status_2g)


get_total_por_id_status_2g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_id_status_2g_recurso)


get_valor_causa_por_id_status_2g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_por_id_status_2g_recurso)


get_total_acordao_desfavoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_desfavoravel_recurso)


get_valor_causa_acordao_desfavoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_desfavoravel_recurso)


get_total_acordao_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_favoravel_recurso)


get_valor_causa_acordao_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_favoravel_recurso)


get_total_acordao_parcialmente_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_parcialmente_favoravel_recurso)


get_valor_causa_acordao_parcialmente_favoravel_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_parcialmente_favoravel_recurso)


get_total_acordao_parcial_retomada_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_parcial_retomada_recurso)


get_valor_causa_acordao_parcial_retomada_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_parcial_retomada_recurso)


get_total_acordao_extincao_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordao_extincao_recurso)


get_valor_causa_acordao_extincao_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_acordao_extincao_recurso)


# =============================================================================
# Meta de Provimento Mensal (NG) — 80 processos providos/mês
# =============================================================================
#
# Conta processos com ``ID_2G`` em: Procedente (COM PE), Parc. Procedente (COM PE),
# Sentença Anulada (ambos os IDs legado/novo) e Procedente Sem Proveito Econômico —
# filtrado por ``DATA_ACORDAO`` no período, mesma base de ``group_recursal_por_status_2g_NG``.

META_PROVIMENTO_MENSAL_NG = _familia.META_PROVIMENTO_MENSAL

_IDS_2G_PROVIMENTO_MENSAL_NG = _familia._IDS_2G_PROVIMENTO_MENSAL


get_total_provimento_mensal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_provimento_mensal)


group_recursal_por_status_2g_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_por_status_2g)


# =============================================================================
# Análise de decisões (cruzamento 1G × 2G)
# =============================================================================

_classificar_decisao_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_decisao_recursal)


_get_id_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_1g)


_get_id_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_2g)


_get_id_merito_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_merito_1g)


_get_id_merito_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_merito_2g)


rotulo_decisao_recursal_export_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.rotulo_decisao_recursal_export)


_filtrar_decisoes_recursal = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_decisoes_recursal)


get_total_decisoes_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_decisoes_recursal)


get_total_por_tipo_decisao_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_por_tipo_decisao_recursal)


get_valor_causa_por_tipo_decisao_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_por_tipo_decisao_recursal)


_percentual_decisao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._percentual_decisao)


get_decisoes_recursal_resumo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_decisoes_recursal_resumo)


group_decisoes_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_decisoes_recursal)


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


filtrar_por_juiz_1g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_por_juiz_1g_recurso)


filtrar_por_relator_2g_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_por_relator_2g_recurso)


_montar_ranking_magistrado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._montar_ranking_magistrado)


get_ranking_juizes_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_recursal)


get_ranking_relatores_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_relatores_recursal)


# =============================================================================
# Filtros combinados (status 1G/2G, juiz, relator, decisão)
# =============================================================================

RecursalLAFiltros = _familia.RecursalLAFiltros


_classificar_extinto_2g_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_extinto_2g_recursal)


_nome_em_conjunto_filtro = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_filtro)


filtrar_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_recursal)


get_opcoes_filtros_recursal_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_recursal)


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
# tratado separadamente no comissionamento, por subsetor de origem).

_STATUS_AGENDAMENTO_CUMPRIDO = _familia._STATUS_AGENDAMENTO_CUMPRIDO

_STATUS_ORIGEM_ERRO_NG = _familia._STATUS_ORIGEM_ERRO

_MOTIVOS_ERRO_RECURSO_NG = _familia._MOTIVOS_ERRO_RECURSO

# Família "AVR - RETORNO": base (973, staffada pela Confecção) + variantes
# 2G/CTRR/DECISÃO (staffadas pela Análise) — staffing verificado em
# usuario_setor_atividade (a base 1G é sempre invertida em relação às
# variantes 2G/CTRR/DECISÃO da mesma família).
_IDS_FAMILIA_AVR_RETORNO_NG = frozenset({973, 990, 986, 1006, 1019, 1025, 1013, 1023})
# Família "RETORNO - CR": base (978, staffada pela Análise) + variantes
# (staffadas pela Confecção).
_IDS_FAMILIA_RETORNO_CR_NG = frozenset({978, 994, 988, 1007, 1020, 1026, 1014, 1024})


_get_agendamento_motivo_encaminhamento_itens = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_motivo_encaminhamento_itens)


_normalizar_motivo_encaminhamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_motivo_encaminhamento)


_itens_erro_recurso_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._itens_erro_recurso)


_get_agendamento_data_cancelamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_cancelamento)


_get_agendamento_data_referencia_erro_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_data_referencia_erro)


_contar_recurso_cancelado_por_destino_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_recurso_cancelado_por_destino)


get_total_avr_retorno_recurso_cancelado_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_avr_retorno_recurso_cancelado)


get_total_retorno_cr_recurso_cancelado_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_retorno_cr_recurso_cancelado)


# =============================================================================
# Comissão — setor RECURSOS (NG)
# =============================================================================
#
# Regras do escritório (documento de 2026-07):
#   - Quantidade: R$0,50 por atividade de Análise concluída (Encerrado
#     Cumprido, DATA_HORA_CONCLUSAO no período) e R$2,00 por atividade de
#     Confecção concluída. A família AVR-RETORNO/RETORNO-CR (retrabalho) não
#     conta para quantidade.
#   - Qualidade: bônus de R$200,00 a cada colaborador do setor se a meta de
#     80 processos providos/mês (``META_PROVIMENTO_MENSAL_NG``) for atingida;
#     bônus de R$100,00 individual se o colaborador não teve nenhum erro no
#     mês ("zero retrabalho").
#   - Erros: quando uma atividade é encerrada como "Cancelado" ou "Encerrado
#     Não Cumprido" com motivo "RECURSO CANCELADO OU ALTERADO" ou "RECURSO
#     ERRADO OU PERDIDO" (únicos motivos usados na prática — o sistema não
#     distingue "cancelado" de "alterado" nem "errado" de "perdido" como
#     textos separados), o desconto é atribuído a quem foi ATRIBUÍDO na
#     atividade de ORIGEM, e o valor (R$1,00 ou R$4,00) é definido pelo
#     SUBSETOR dessa atividade de origem — não pelo texto do motivo, já que a
#     mesma string aparece em origens de ambos os subsetores na prática.
#
# Roster e classificação de atividades por subsetor verificados diretamente
# contra ``usuario_setor_atividade`` (2026-07): não existe tabela dedicada de
# "subsetor", por isso o roster é fixo (Giovanna atua nos dois subsetores e
# comissiona pela atividade que efetivamente concluir). Vivian Alessandra Souza
# Fernandes é a líder do setor e fica fora do relatório de comissão (11/2026).

_ROSTER_ANALISE_RECURSOS_NG = _familia._ROSTER_ANALISE_RECURSOS

_ROSTER_CONFECCAO_RECURSOS_NG = _familia._ROSTER_CONFECCAO_RECURSOS

_ROSTER_COMISSAO_RECURSOS_NG = _familia._ROSTER_COMISSAO_RECURSOS

_IDS_ATIVIDADE_ANALISE_QTD_NG = _familia._IDS_ATIVIDADE_ANALISE_QTD

_IDS_ATIVIDADE_CONFECCAO_QTD_NG = _familia._IDS_ATIVIDADE_CONFECCAO_QTD

_STATUS_QTD_ANALISE_NG = _familia._STATUS_QTD_ANALISE

VALOR_UNITARIO_ANALISE_NG = _familia.VALOR_UNITARIO_ANALISE

VALOR_UNITARIO_CONFECCAO_NG = _familia.VALOR_UNITARIO_CONFECCAO

VALOR_DESCONTO_ERRO_ANALISE_NG = _familia.VALOR_DESCONTO_ERRO_ANALISE

VALOR_DESCONTO_ERRO_ANALISE_ALTERADO_NG = _familia.VALOR_DESCONTO_ERRO_ANALISE_ALTERADO

VALOR_DESCONTO_ERRO_CONFECCAO_NG = _familia.VALOR_DESCONTO_ERRO_CONFECCAO

VALOR_BONUS_META_QUALIDADE_NG = _familia.VALOR_BONUS_META_QUALIDADE

VALOR_BONUS_ZERO_RETRABALHO_NG = _familia.VALOR_BONUS_ZERO_RETRABALHO

_get_agendamento_id_setor_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_id_setor_atividade)


_get_agendamento_funcionario_atribuido_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_atribuido_NG)


_get_agendamento_motivo_texto_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_motivo_texto)


_get_agendamento_numero_processo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_numero_processo)


get_comissao_recursos_NG_por_funcionario = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_comissao_recursos_por_funcionario)


_agendamento_atividade_recursos_valida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_atividade_recursos_valida)


get_kpis_atividades_recursos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_atividades_recursos)


get_kpis_atividades_recursos_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_atividades_recursos_por_prazo)


_get_agendamento_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_processo_id)


_get_agendamento_atividade_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_atividade_nome)


_get_agendamento_funcionario_atribuido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_atribuido)


_get_agendamento_funcionario_encerramento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_encerramento)


_get_agendamento_funcionario_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_funcionario_nome)


_agendamento_tem_encerrador_identificado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_tem_encerrador_identificado)


_filtrar_agendamentos_recursos_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_agendamentos_recursos_no_periodo)


_filtrar_agendamentos_encerrados_recursos_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_agendamentos_encerrados_recursos_no_periodo)


_agrupar_processos_distintos_por_chave = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agrupar_processos_distintos_por_chave)


group_recursal_processos_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_processos_por_atividade)


_status_agendamento_para_slug_demandas = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._status_agendamento_para_slug_demandas)


group_recursal_demandas_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_demandas_por_funcionario)


group_recursal_resolvidos_por_dia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_resolvidos_por_dia)


_MESES_ABREVIADOS_NG = _familia._MESES_ABREVIADOS


group_recursal_resolvidos_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_recursal_resolvidos_por_mes)


get_recursal_resolvidos_por_dia_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_recursal_resolvidos_por_dia_por_funcionario)


get_media_recursal_resolvidos_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_recursal_resolvidos_por_funcionario)


_formatar_pessoa_setor_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._formatar_pessoa_setor_recursos)


_formatar_descricao_tarefa_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._formatar_descricao_tarefa_recursos)


_get_agendamento_atividade_nome_lista = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_agendamento_atividade_nome_lista)


_agendamento_incluir_lista_tarefas_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_incluir_lista_tarefas_recursos)


_classificar_situacao_tarefa_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_tarefa_recursos)


_SITUACOES_RECURSOS_VALIDAS = _familia._SITUACOES_RECURSOS_VALIDAS


RecursalAtividadesRecursosFiltros = _familia.RecursalAtividadesRecursosFiltros


_agendamento_match_filtros_recursos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_recursos)


filtrar_agendamentos_recursos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_recursos)


_get_recurso_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_recurso_processo_id)


processo_ids_recursal_de_agendamentos_recursos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.processo_ids_recursal_de_agendamentos_recursos)


filtrar_recursal_NG_por_processo_ids = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_recursal_por_processo_ids)


list_recursal_atividades_periodo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_recursal_atividades_periodo)


get_opcoes_filtros_atividades_lista_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_atividades_lista)
