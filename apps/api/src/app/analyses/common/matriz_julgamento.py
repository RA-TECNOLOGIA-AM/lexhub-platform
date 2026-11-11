# Matriz de Julgamento — cruzamento Sentença/Acórdão de Mérito (1º x 2º grau)
#
# Fonte: PDF "novos campos.pdf" (enums propostos) + planilha Google Sheets
# "MATRIZ DE JULGAMENTO — 1º x 2º GRAU" (regras de cruzamento, ordem de
# aplicação, precedências), lidos integralmente em 2026-09-15. Ver plano
# ``/home/luiz/.claude/plans/linear-knitting-stardust.md`` para o contexto
# completo da migração.
#
# Este módulo cobre só o eixo de MÉRITO (sentença/acórdão). Embargos, Liminar
# e Acordo são eixos independentes definidos na mesma planilha, fora de
# escopo desta rodada — Embargos e Liminar ainda têm 0 linhas povoadas no
# banco (``sentenca_embargos_primeiro_grau``, ``liminar_primeiro_grau``,
# ``acordao_embargos_segundo_grau``, ``liminar_segundo_grau``) e Acordo não
# tem coluna nova dedicada (usa ``acordo_homologado``/``acordo_fechado``/
# ``pagamento_acordo``, já existentes em ``processo``).
#
# Compartilhado entre LA e NG (Recursal, Controle de Processos e os 4
# dashboards de Julgados) para eliminar a duplicação que existia antes desta
# mudança entre ``recurso_LA.py``/``recurso_NG.py`` e entre os 4 módulos
# ``julgados_*.py``.

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# =============================================================================
# IDs do esquema novo — ``sentenca_merito_primeiro_grau`` (1G) /
# ``acordao_merito_segundo_grau`` (2G), LexFlow. Hardcoded aqui como os demais
# catálogos de status já são no projeto (tabelas de lookup pequenas e
# estáveis, sem necessidade de round-trip ao banco para os IDs).
# =============================================================================

ID_MERITO_PROCEDENTE_COM_PE = 1
ID_MERITO_PROCEDENTE_SEM_PE = 2
ID_MERITO_PARC_PROCEDENTE_COM_PE = 3
ID_MERITO_PARC_PROCEDENTE_SEM_PE = 4
ID_MERITO_IMPROCEDENTE = 5
ID_MERITO_IMPROCEDENTE_PRESCRICAO = 6
ID_MERITO_EXTINTO_SEM_MERITO = 7
ID_MERITO_SENTENCA_ANULADA = 8  # exclusivo do 2º grau (acordao_merito_segundo_grau)

_IDS_MERITO_1G_VALIDOS = frozenset({
    ID_MERITO_PROCEDENTE_COM_PE, ID_MERITO_PROCEDENTE_SEM_PE,
    ID_MERITO_PARC_PROCEDENTE_COM_PE, ID_MERITO_PARC_PROCEDENTE_SEM_PE,
    ID_MERITO_IMPROCEDENTE, ID_MERITO_IMPROCEDENTE_PRESCRICAO,
    ID_MERITO_EXTINTO_SEM_MERITO,
})

_LABEL_MERITO: dict[int, str] = {
    ID_MERITO_PROCEDENTE_COM_PE: "PROCEDENTE COM PROVEITO ECONÔMICO",
    ID_MERITO_PROCEDENTE_SEM_PE: "PROCEDENTE SEM PROVEITO ECONÔMICO",
    ID_MERITO_PARC_PROCEDENTE_COM_PE: "PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO",
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: "PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO",
    ID_MERITO_IMPROCEDENTE: "IMPROCEDENTE",
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: "IMPROCEDENTE POR PRESCRIÇÃO/DECADÊNCIA",
    ID_MERITO_EXTINTO_SEM_MERITO: "EXTINTO SEM MÉRITO",
    ID_MERITO_SENTENCA_ANULADA: "SENTENÇA ANULADA",
}

# Ordem de exibição (1G: 7 valores; 2G: mesmos + Sentença Anulada)
IDS_MERITO_1G_ORDEM: tuple[int, ...] = (
    ID_MERITO_PROCEDENTE_COM_PE, ID_MERITO_PROCEDENTE_SEM_PE,
    ID_MERITO_PARC_PROCEDENTE_COM_PE, ID_MERITO_PARC_PROCEDENTE_SEM_PE,
    ID_MERITO_IMPROCEDENTE, ID_MERITO_IMPROCEDENTE_PRESCRICAO,
    ID_MERITO_EXTINTO_SEM_MERITO,
)
IDS_MERITO_2G_ORDEM: tuple[int, ...] = IDS_MERITO_1G_ORDEM + (ID_MERITO_SENTENCA_ANULADA,)
_IDS_MERITO_2G_VALIDOS = frozenset(IDS_MERITO_2G_ORDEM)


def rotulo_merito(id_merito: Optional[int]) -> str:
    if id_merito is None:
        return ""
    return _LABEL_MERITO.get(id_merito, "")


# =============================================================================
# Tradução do esquema antigo (``status_primeiro_grau``/``status_segundo_grau``,
# IDs 17-25, expostos nas queries como ``STATUS_1G``/``STATUS_2G``) para o
# esquema novo — por NOME normalizado, não por ID.
#
# Por quê por nome: o esquema antigo já passou por uma renomeação de IDs
# antes desta mudança (``controle_processo_{NG,LA}.py`` mistura IDs legados
# 4-9 com os atuais 17-25 no mesmo conjunto) — seguir IDs por uma 3ª geração
# de esquema seria frágil. Os nomes, por outro lado, batem quase literalmente
# entre as tabelas antiga e nova. Validado contra o banco em 2026-09-15:
# cruzando ``id_status_grau1`` × ``id_sentenca_merito_grau1`` nos 17.185
# processos com os dois campos preenchidos, a tradução abaixo bate em >99,9%
# dos casos (< 10 linhas destoantes no total, sem padrão sistemático).
# =============================================================================

def _normalizar_nome_status(nome: Optional[str]) -> str:
    if not nome:
        return ""
    s = str(nome).strip().upper()
    s = s.replace("(", "").replace(")", "")
    return " ".join(s.split())


_TRADUCAO_STATUS_ANTIGO_PARA_MERITO: dict[str, int] = {
    "PROCEDENTE COM PROVEITO ECONÔMICO": ID_MERITO_PROCEDENTE_COM_PE,
    "PROCEDENTE SEM PROVEITO ECONÔMICO": ID_MERITO_PROCEDENTE_SEM_PE,
    "PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO": ID_MERITO_PARC_PROCEDENTE_COM_PE,
    "PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO": ID_MERITO_PARC_PROCEDENTE_SEM_PE,
    "IMPROCEDENTE": ID_MERITO_IMPROCEDENTE,
    "EXTINTO SEM MÉRITO": ID_MERITO_EXTINTO_SEM_MERITO,
    "SENTENÇA ANULADA": ID_MERITO_SENTENCA_ANULADA,
    # "ACORDO HOMOLOGADO" (eixo próprio, fora de escopo) e "ENCERRADO 1G"
    # (equivale a "sem recurso") não têm entrada aqui de propósito — ver
    # ``_STATUS_ANTIGO_SEM_RECURSO``/``_STATUS_ANTIGO_FORA_DE_ESCOPO`` abaixo.
}

_STATUS_ANTIGO_SEM_RECURSO = frozenset({"ENCERRADO 1G"})
_STATUS_ANTIGO_FORA_DE_ESCOPO = frozenset({"ACORDO HOMOLOGADO"})


def traduzir_status_antigo_para_merito(nome_status_antigo: Optional[str]) -> Optional[int]:
    """
    Traduz um nome de status antigo (``STATUS_1G``/``STATUS_2G``) para o ID
    correspondente no esquema novo de mérito. Retorna ``None`` quando não há
    equivalente (acordo) ou quando equivale a "sem recurso" (``ENCERRADO 1G``).
    """
    norm = _normalizar_nome_status(nome_status_antigo)
    if not norm or norm in _STATUS_ANTIGO_SEM_RECURSO or norm in _STATUS_ANTIGO_FORA_DE_ESCOPO:
        return None
    return _TRADUCAO_STATUS_ANTIGO_PARA_MERITO.get(norm)


def resolver_id_merito_1g(
    id_sentenca_merito_grau1: Optional[int],
    status_1g_antigo: Optional[str] = None,
) -> Optional[int]:
    """Usa a coluna nova (``id_sentenca_merito_grau1``) quando presente; senão traduz o status antigo."""
    if id_sentenca_merito_grau1 is not None:
        return id_sentenca_merito_grau1
    return traduzir_status_antigo_para_merito(status_1g_antigo)


def resolver_id_merito_2g(
    id_acordao_merito_grau2: Optional[int],
    status_2g_antigo: Optional[str] = None,
) -> Optional[int]:
    """Usa a coluna nova (``id_acordao_merito_grau2``) quando presente; senão traduz o status antigo."""
    if id_acordao_merito_grau2 is not None:
        return id_acordao_merito_grau2
    return traduzir_status_antigo_para_merito(status_2g_antigo)


# =============================================================================
# Cruzamento 1G x 2G — "Resultado Mapeado" (Matriz de Julgamento)
# =============================================================================

BUCKET_MANTIDO_GANHO = "mantido_ganho"
BUCKET_GANHO_AMPLIADO = "ganho_ampliado"
BUCKET_REVERTIDO_GANHO = "revertido_ganho"
BUCKET_GANHO_REDUZIDO = "ganho_reduzido"
BUCKET_EXTINCAO_PERMITE_REAJUIZAR = "extincao_permite_reajuizar"
BUCKET_INSTRUCAO_RETOMADA = "instrucao_retomada"
BUCKET_MANTIDO_PERDA = "mantido_perda"
BUCKET_REVERTIDO_PERDA = "revertido_perda"

FAROL_VERDE = "verde"
FAROL_AMARELO = "amarelo"
FAROL_VERMELHO = "vermelho"
FAROL_NEUTRO = "neutro"

_LABEL_BUCKET: dict[str, str] = {
    BUCKET_MANTIDO_GANHO: "Mantido Ganho",
    BUCKET_GANHO_AMPLIADO: "Ganho Ampliado",
    BUCKET_REVERTIDO_GANHO: "Revertido Ganho",
    BUCKET_GANHO_REDUZIDO: "Ganho Reduzido",
    BUCKET_EXTINCAO_PERMITE_REAJUIZAR: "Extinção (Permite Reajuizar)",
    BUCKET_INSTRUCAO_RETOMADA: "Instrução Retomada",
    BUCKET_MANTIDO_PERDA: "Mantido Perda",
    BUCKET_REVERTIDO_PERDA: "Revertido Perda",
}

_FAROL_BUCKET: dict[str, str] = {
    BUCKET_MANTIDO_GANHO: FAROL_VERDE,
    BUCKET_GANHO_AMPLIADO: FAROL_VERDE,
    BUCKET_REVERTIDO_GANHO: FAROL_VERDE,
    BUCKET_GANHO_REDUZIDO: FAROL_AMARELO,
    BUCKET_EXTINCAO_PERMITE_REAJUIZAR: FAROL_AMARELO,
    BUCKET_INSTRUCAO_RETOMADA: FAROL_NEUTRO,
    BUCKET_MANTIDO_PERDA: FAROL_VERMELHO,
    BUCKET_REVERTIDO_PERDA: FAROL_VERMELHO,
}

# Reajuizável: True só para "Extinção (Permite Reajuizar)"; None para
# "Instrução Retomada" (processo volta à instrução, não transitou — não é
# nem ganho nem perda, "reajuizar" não se aplica); False nos demais
# (definitivos, com ou sem coisa julgada favorável).
_REAJUIZAVEL_BUCKET: dict[str, Optional[bool]] = {
    BUCKET_MANTIDO_GANHO: False,
    BUCKET_GANHO_AMPLIADO: False,
    BUCKET_REVERTIDO_GANHO: False,
    BUCKET_GANHO_REDUZIDO: False,
    BUCKET_EXTINCAO_PERMITE_REAJUIZAR: True,
    BUCKET_INSTRUCAO_RETOMADA: None,
    BUCKET_MANTIDO_PERDA: False,
    BUCKET_REVERTIDO_PERDA: False,
}


@dataclass(frozen=True)
class ResultadoMerito:
    bucket: str
    label: str
    farol: str
    reajuizavel: Optional[bool]


def _resultado(bucket: str) -> ResultadoMerito:
    return ResultadoMerito(
        bucket=bucket,
        label=_LABEL_BUCKET[bucket],
        farol=_FAROL_BUCKET[bucket],
        reajuizavel=_REAJUIZAVEL_BUCKET[bucket],
    )


def _preencher_linha(matriz: dict, id_1g: int, por_2g: dict[Optional[int], str]) -> None:
    for id_2g, bucket in por_2g.items():
        matriz[(id_1g, id_2g)] = bucket


# Matriz 7 (1G) x 9 (2G, incluindo ``None`` = sem recurso) — 63 combinações,
# transcritas literalmente da planilha "MATRIZ DE JULGAMENTO — 1º x 2º GRAU".
_MATRIZ_MERITO: dict[tuple[int, Optional[int]], str] = {}

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_PROCEDENTE_COM_PE, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_MANTIDO_GANHO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_GANHO_REDUZIDO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_GANHO_REDUZIDO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_GANHO_REDUZIDO,
    ID_MERITO_IMPROCEDENTE: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_MANTIDO_GANHO,
})

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_PROCEDENTE_SEM_PE, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_GANHO_AMPLIADO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_MANTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_GANHO_REDUZIDO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_GANHO_REDUZIDO,
    ID_MERITO_IMPROCEDENTE: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_MANTIDO_GANHO,
})

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_PARC_PROCEDENTE_COM_PE, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_GANHO_AMPLIADO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_GANHO_AMPLIADO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_MANTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_GANHO_REDUZIDO,
    ID_MERITO_IMPROCEDENTE: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_MANTIDO_GANHO,
})

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_PARC_PROCEDENTE_SEM_PE, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_GANHO_AMPLIADO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_GANHO_AMPLIADO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_GANHO_AMPLIADO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_MANTIDO_GANHO,
    ID_MERITO_IMPROCEDENTE: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_MANTIDO_GANHO,
})

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_IMPROCEDENTE, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_IMPROCEDENTE: BUCKET_MANTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_MANTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_MANTIDO_PERDA,
})

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_IMPROCEDENTE_PRESCRICAO, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_IMPROCEDENTE: BUCKET_MANTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_MANTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_MANTIDO_PERDA,
})

_preencher_linha(_MATRIZ_MERITO, ID_MERITO_EXTINTO_SEM_MERITO, {
    ID_MERITO_PROCEDENTE_COM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PROCEDENTE_SEM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_COM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_PARC_PROCEDENTE_SEM_PE: BUCKET_REVERTIDO_GANHO,
    ID_MERITO_IMPROCEDENTE: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_IMPROCEDENTE_PRESCRICAO: BUCKET_REVERTIDO_PERDA,
    ID_MERITO_EXTINTO_SEM_MERITO: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
    ID_MERITO_SENTENCA_ANULADA: BUCKET_INSTRUCAO_RETOMADA,
    None: BUCKET_EXTINCAO_PERMITE_REAJUIZAR,
})


def classificar_resultado_merito(
    id_1g: Optional[int],
    id_2g: Optional[int],
) -> Optional[ResultadoMerito]:
    """
    Cruza o mérito de 1º e 2º grau (esquema novo) e retorna o "Resultado
    Mapeado" (Matriz de Julgamento). ``id_2g=None`` representa "sem recurso"
    (coluna "(vazio)" da planilha — resultado espelha e transita o 1º grau).
    Retorna ``None`` quando ``id_1g`` não tem classificação de mérito válida
    (ex.: acordo, dado ausente, ou algum ID fora do 1-7 esperado).
    """
    if id_1g not in _IDS_MERITO_1G_VALIDOS:
        return None
    bucket = _MATRIZ_MERITO.get((id_1g, id_2g))
    if bucket is None:
        return None
    return _resultado(bucket)


# =============================================================================
# Extintos com/sem mérito e Taxa de Provimento (2º grau) — Controle de Processos
# =============================================================================

def eh_extinto_sem_merito_2g(id_2g: Optional[int]) -> bool:
    """``id_2g`` novo (ou traduzido do antigo) igual a EXTINTO SEM MÉRITO."""
    return id_2g == ID_MERITO_EXTINTO_SEM_MERITO


def eh_extinto_com_merito_2g(id_2g: Optional[int]) -> bool:
    """Qualquer decisão de 2º grau com mérito (todo ``id_2g`` novo válido exceto Extinto Sem Mérito)."""
    return id_2g in _IDS_MERITO_2G_VALIDOS and id_2g != ID_MERITO_EXTINTO_SEM_MERITO


# Taxa de provimento = positivos / total de acórdãos com mérito × 100.
# Positivos: procedente/parc. procedente (com ou sem PE), sentença anulada e
# extinto sem mérito. Fora do numerador (mas dentro do denominador via "com
# mérito"): improcedente e improcedente por prescrição/decadência — mesma
# fórmula de negócio já usada antes desta mudança, só a fonte do ID muda.
_IDS_2G_TAXA_PROVIMENTO_POSITIVOS: frozenset[int] = frozenset({
    ID_MERITO_PROCEDENTE_COM_PE, ID_MERITO_PROCEDENTE_SEM_PE,
    ID_MERITO_PARC_PROCEDENTE_COM_PE, ID_MERITO_PARC_PROCEDENTE_SEM_PE,
    ID_MERITO_SENTENCA_ANULADA, ID_MERITO_EXTINTO_SEM_MERITO,
})
_IDS_2G_TAXA_PROVIMENTO_IMPROCEDENTE: frozenset[int] = frozenset({
    ID_MERITO_IMPROCEDENTE, ID_MERITO_IMPROCEDENTE_PRESCRICAO,
})


def eh_decisao_positiva_taxa_provimento_2g(id_2g: Optional[int]) -> bool:
    return id_2g in _IDS_2G_TAXA_PROVIMENTO_POSITIVOS


def eh_decisao_improcedente_taxa_provimento_2g(id_2g: Optional[int]) -> bool:
    return id_2g in _IDS_2G_TAXA_PROVIMENTO_IMPROCEDENTE


# Listas prontas para endpoints que ecoam "quais IDs contam como X" (metadados de resposta).
IDS_MERITO_1G_COM_MERITO: tuple[int, ...] = tuple(
    i for i in IDS_MERITO_1G_ORDEM if i != ID_MERITO_EXTINTO_SEM_MERITO
)
IDS_MERITO_2G_COM_MERITO: tuple[int, ...] = tuple(
    i for i in IDS_MERITO_2G_ORDEM if i != ID_MERITO_EXTINTO_SEM_MERITO
)
IDS_MERITO_SEM_MERITO: tuple[int, ...] = (ID_MERITO_EXTINTO_SEM_MERITO,)


# =============================================================================
# Embargos (Sentença 1G / Acórdão 2G) — Status Resultante
#
# Matriz definida pelo usuário em 06/10/2026: o status resultante cruza o mérito
# VIGENTE ANTES dos embargos com o resultado lançado em
# ``sentenca_embargos_primeiro_grau``/``acordao_embargos_segundo_grau``. Casado
# por NOME (as duas tabelas têm IDs diferentes para REJEITADOS/NÃO CONHECIDOS).
# O mérito atual em ``processo`` já é o pós-embargo (o LexFlow atualiza na mesma
# edição em que lança o resultado) — o "antes" vem do ``processo_audit``, na
# query ``julgados`` (colunas ``*_PRE_EMBARGOS``).
# =============================================================================

STATUS_EMBARGO_REVERTIDO_GANHO = "Revertido Ganho"
STATUS_EMBARGO_REVERTIDO_PERDA = "Revertido Perda"
STATUS_EMBARGO_GANHO_AMPLIADO = "Ganho Ampliado"
STATUS_EMBARGO_GANHO_REDUZIDO = "Ganho Reduzido"
STATUS_EMBARGO_MANTIDO = "Status Mantido"
STATUS_EMBARGO_REVISAR = "Revisar Classificação"
# Embargo com data mas sem resultado lançado — fatia própria, sem estimativa.
STATUS_EMBARGO_SEM_RESULTADO = "Sem resultado lançado"

STATUS_EMBARGO_ORDEM: tuple[str, ...] = (
    STATUS_EMBARGO_REVERTIDO_GANHO,
    STATUS_EMBARGO_GANHO_AMPLIADO,
    STATUS_EMBARGO_GANHO_REDUZIDO,
    STATUS_EMBARGO_MANTIDO,
    STATUS_EMBARGO_REVERTIDO_PERDA,
    STATUS_EMBARGO_REVISAR,
    STATUS_EMBARGO_SEM_RESULTADO,
)

_EMB_REVERTEU_PROCEDENCIA = "REVERTEU PROCEDÊNCIA"
_EMB_REVERTEU_IMPROCEDENCIA = "REVERTEU IMPROCEDÊNCIA"
_EMB_PENDENCIA_SANEADA = "PENDÊNCIA SANEADA"
_EMB_AUMENTOU = "AUMENTOU A CONDENAÇÃO"
_EMB_REDUZIU = "REDUZIU A CONDENAÇÃO"
_EMB_PREJUDICADOS = "PREJUDICADOS"
_EMB_REJEITADOS = "REJEITADOS"
_EMB_NAO_CONHECIDOS = "NÃO CONHECIDOS"

# Status Mantido em qualquer mérito vigente (inclusive extinto/anulada/sem mérito).
_EMB_SEMPRE_MANTIDO = frozenset({
    _EMB_PENDENCIA_SANEADA, _EMB_PREJUDICADOS, _EMB_REJEITADOS, _EMB_NAO_CONHECIDOS,
})

_MATRIZ_EMBARGOS_PROCEDENTE: dict[str, str] = {
    _EMB_REVERTEU_PROCEDENCIA: STATUS_EMBARGO_REVISAR,
    _EMB_REVERTEU_IMPROCEDENCIA: STATUS_EMBARGO_REVERTIDO_PERDA,
    _EMB_AUMENTOU: STATUS_EMBARGO_GANHO_AMPLIADO,
    _EMB_REDUZIU: STATUS_EMBARGO_GANHO_REDUZIDO,
}
_MATRIZ_EMBARGOS_PARC_PROCEDENTE: dict[str, str] = {
    _EMB_REVERTEU_PROCEDENCIA: STATUS_EMBARGO_GANHO_AMPLIADO,
    _EMB_REVERTEU_IMPROCEDENCIA: STATUS_EMBARGO_REVERTIDO_PERDA,
    _EMB_AUMENTOU: STATUS_EMBARGO_GANHO_AMPLIADO,
    _EMB_REDUZIU: STATUS_EMBARGO_GANHO_REDUZIDO,
}
_MATRIZ_EMBARGOS_IMPROCEDENTE: dict[str, str] = {
    _EMB_REVERTEU_PROCEDENCIA: STATUS_EMBARGO_REVERTIDO_GANHO,
    _EMB_REVERTEU_IMPROCEDENCIA: STATUS_EMBARGO_REVISAR,
    _EMB_AUMENTOU: STATUS_EMBARGO_REVISAR,
    _EMB_REDUZIU: STATUS_EMBARGO_REVISAR,
}

_IDS_MERITO_PROCEDENTE_TOTAL = frozenset({ID_MERITO_PROCEDENTE_COM_PE, ID_MERITO_PROCEDENTE_SEM_PE})
_IDS_MERITO_PARC_PROCEDENTE = frozenset({ID_MERITO_PARC_PROCEDENTE_COM_PE, ID_MERITO_PARC_PROCEDENTE_SEM_PE})
_IDS_MERITO_IMPROCEDENTE_QUALQUER = frozenset({ID_MERITO_IMPROCEDENTE, ID_MERITO_IMPROCEDENTE_PRESCRICAO})


def classificar_status_embargos(
    id_merito_pre_embargos: Optional[int],
    nome_resultado_embargos: Optional[str],
) -> Optional[str]:
    """Status Resultante dos embargos a partir do mérito vigente antes dos embargos e do nome
    do resultado lançado. ``None`` quando não há resultado oficial (o chamador decide a
    estimativa). Mérito fora das 3 linhas da matriz (extinto, anulada, vazio): os resultados
    "sempre mantido" viram Status Mantido; os demais, Revisar Classificação."""
    resultado = _normalizar_nome_status(nome_resultado_embargos)
    if not resultado:
        return None
    if resultado in _EMB_SEMPRE_MANTIDO:
        return STATUS_EMBARGO_MANTIDO
    if id_merito_pre_embargos in _IDS_MERITO_PROCEDENTE_TOTAL:
        matriz = _MATRIZ_EMBARGOS_PROCEDENTE
    elif id_merito_pre_embargos in _IDS_MERITO_PARC_PROCEDENTE:
        matriz = _MATRIZ_EMBARGOS_PARC_PROCEDENTE
    elif id_merito_pre_embargos in _IDS_MERITO_IMPROCEDENTE_QUALQUER:
        matriz = _MATRIZ_EMBARGOS_IMPROCEDENTE
    else:
        return STATUS_EMBARGO_REVISAR
    return matriz.get(resultado, STATUS_EMBARGO_REVISAR)


def agrupar_status_embargos(status: list[str]) -> list[dict]:
    """Contagem por Status Resultante na ordem fixa de ``STATUS_EMBARGO_ORDEM`` (inclui zeros)."""
    contagem = {s: 0 for s in STATUS_EMBARGO_ORDEM}
    for s in status:
        if s in contagem:
            contagem[s] += 1
    return [{"name": s, "value": contagem[s]} for s in STATUS_EMBARGO_ORDEM]
