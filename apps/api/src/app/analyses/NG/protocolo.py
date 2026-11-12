# Funções de analises do setor de protocolo

from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date
from collections import defaultdict
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.NG.comercial_geral import _formatar_nome_atendente, get_comissao_base

# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Função para converter o valor de causa para float.
def _converter_valor_causa(valor_causa: Any) -> float:
    """
    Converte o valor da causa para float, tratando diferentes tipos de entrada.
    Suporta: Decimal, int, float, string formatada, None.
    """
    # Se o valor for None, retorna 0.0
    if valor_causa is None:
        return 0.0
    
    try:
        # Se for Decimal, converte diretamente para float
        if isinstance(valor_causa, Decimal):
            return float(valor_causa)
        # Se já for número, converte para float
        elif isinstance(valor_causa, (int, float)):
            return float(valor_causa)
        # Se for string, limpa e converte
        elif isinstance(valor_causa, str):
            # Remove espaços e caracteres especiais, mantém apenas números, ponto e vírgula
            valor_limpo = valor_causa.strip().replace(",", ".")
            # Remove qualquer caractere que não seja número ou ponto
            valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')
            if valor_limpo:
                return float(valor_limpo)
            else:
                return 0.0  # String vazia após limpeza
        else:
            # Para outros tipos, tenta converter para string primeiro
            return float(str(valor_causa).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        # Se não conseguir converter, retorna 0.0
        return 0.0

# Função auxiliar que retorna a lista filtrada de protocolos resolvidos.
def _filtrar_protocolos_resolvidos(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra e retorna apenas os protocolos resolvidos."""
    return [
        p for p in protocolos
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["DISTRIBUÍDO", "PROTOCOLADO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar que retorna a lista de protocolos resolvidos de reajuizamento.
def _filtrar_protocolados_de_reajuizamento(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra e retorna apenas os protocolos resolvidos de reajuizamento."""
    return [
        p for p in protocolos
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["DISTRIBUÍDO", "PROTOCOLADO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "TRUE" or
            p.get("REAJUIZAMENTO") is True
        )
    ]

# Função auxiliar que retorna a lista de não protocolados.
def _filtrar_protocolos_nao_protocolados(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra e retorna apenas os protocolos não protocolados."""
    return [
        p for p in protocolos
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["NÃO INICIADO", "NÃO PROTOCOLADO", "PRÉ-PROTOCOLADO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" 
            or p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar que retorna a lista de não protocolados de reajuizamento.
def _filtrar_nao_protocolados_de_reajuizamento(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra e retorna apenas os protocolos não protocolados de reajuizamento."""
    return [
        p for p in protocolos
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["NÃO INICIADO", "NÃO PROTOCOLADO", "PRÉ-PROTOCOLADO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "TRUE" or
            p.get("REAJUIZAMENTO") is True
        )
    ]

# Função para filtrar os dados e crealizar as analises de comparativos entre o periodo atual e o periodo anterior de qualquer outra analise.
def _filter_by_date_range(protocolos: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados de protocolos por intervalo de datas usando a coluna DATA_CRIACAO."""
    filtered = []
    for p in protocolos:
        try:
            # Usa a coluna SAIDA para filtrar
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue

            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue

            # Garantir que saida_date é sempre date, não datetime
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()
            elif not isinstance(saida_date, date):
                continue

            # Verificar se a data está no intervalo
            if from_date <= saida_date <= to_date:
                filtered.append(p)
        except (ValueError, AttributeError, TypeError):
            continue

    return filtered

# Meta anual de valor de causa para processos protocolados em 2026 (em reais).
META_VALOR_CAUSA_2026 = 240_000_000

def _filtrar_protocolos_por_ano(protocolos: List[Dict[str, Any]], ano: int) -> List[Dict[str, Any]]:
    """Filtra protocolos cuja data de saída (protocolo) está no ano informado."""
    filtered = []
    for p in protocolos:
        try:
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue
            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()
            elif not isinstance(saida_date, date):
                continue
            if saida_date.year == ano:
                filtered.append(p)
        except (ValueError, AttributeError, TypeError):
            continue
    return filtered

# Função auxiliar que retorna uma lista com as MATERIAS de protocolo.
def _get_materias_protocolo(protocolos: List[Dict[str, Any]]) -> List[str]:
    """Retorna uma lista com as MATERIAS únicas de protocolo."""
    if not protocolos:
        return []
    return list(set(p.get("MATERIA") or "Sem matéria" for p in protocolos))


def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - ' (ex: 'BX_ANT_FIN - BANCO BRADESCO' -> 'BX_ANT_FIN')."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"


# Formata o nome do funcionário.
def _formatar_nome_funcionario(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome da funcionario."""
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo

    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0].upper()
    return " ".join(partes[:2]).upper()


def filter_protocolo_por_materia(
    protocolos: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_por_materia` em ``org_doc``
    (:func:`_normalizar_materia`).
    """
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(protocolos)
    return [p for p in protocolos if _normalizar_materia(p.get("MATERIA")) in alvos]


def filter_protocolo_por_funcionario(
    protocolos: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_por_funcionario` em ``org_doc``
    (:func:`_formatar_nome_funcionario` deste módulo).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(protocolos)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in protocolos
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_protocolo_por_funcionarios(
    protocolos: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários (união — OR)."""
    if not funcionarios:
        return list(protocolos)
    alvos = {
        _formatar_nome_funcionario(str(f).strip())
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(protocolos)
    return [
        p for p in protocolos
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) in alvos
    ]


def filter_protocolo_por_sistema(
    protocolos: List[Dict[str, Any]],
    sistema: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Alinhado ao rótulo de :func:`group_protocolados_por_sistema`
    (``p.get('SISTEMA') or 'Sem sistema'``).
    """
    if sistema is None or not str(sistema).strip():
        return list(protocolos)
    alvo = str(sistema).strip()
    return [
        p for p in protocolos
        if (p.get("SISTEMA") or "Sem sistema") == alvo
    ]


def _normalizar_uf_protocolo(raw: Any) -> str:
    """Normaliza a UF vinda do banco ou da query para comparação."""
    return str(raw or "").strip().upper()


def list_ufs_protocolo(protocolos: List[Dict[str, Any]]) -> List[str]:
    """Lista única de UFs disponíveis no recorte atual de protocolos."""
    vistos: set[str] = set()
    saida: List[str] = []
    for row in protocolos or []:
        uf = _normalizar_uf_protocolo(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_protocolo_por_uf(
    protocolos: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe protocolos aos registros de uma ou mais UFs."""
    if uf is None:
        return list(protocolos)
    ufs = [uf] if isinstance(uf, str) else list(uf)
    alvo = {_normalizar_uf_protocolo(u) for u in ufs if str(u).strip()}
    if not alvo:
        return list(protocolos)
    return [
        p for p in protocolos
        if _normalizar_uf_protocolo(p.get("UF") or p.get("uf")) in alvo
    ]


# -----------------------------------------------------------------------------
# 2 - Funções de Protocolados
# -----------------------------------------------------------------------------

# Retorna a quantidade de protocolos resolvidos.
def get_protocolos_resolvidos(protocolos: List[Dict[str, Any]]) -> int:
    return len(_filtrar_protocolos_resolvidos(protocolos))

# Retorna a quantidade de protocolados de reajuizamento.
def get_protocolados_de_reajuizamento(protocolos: List[Dict[str, Any]]) -> int:
    return len(_filtrar_protocolados_de_reajuizamento(protocolos))

# Retorna a quantidade de protocolos resolvidos por atendente.
def get_protocolos_por_atendente(protocolos: List[Dict[str, Any]]) -> Dict[str, int]:
    protocolos_resolvidos = _filtrar_protocolos_resolvidos(protocolos)
    atendente_counts = defaultdict(int)
    for p in protocolos_resolvidos:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# Retorna a soma do valor da causa para protocolos.
def get_valor_causa_protocolo_novo(protocolos: List[Dict[str, Any]]) -> float:
    total = 0.0
    for p in protocolos:
        # Verifica se atende aos critérios
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["DISTRIBUÍDO", "PROTOCOLADO"]
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
        
        if status_ok and reajuizamento_ok:
            materia = str(p.get("MATERIA") or "").strip().upper()
            # Para matéria ANP, considera apenas o valor do dano moral
            if materia == "ANP":
                valor_causa = p.get("DANO_MORAL")
            else:
                valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
            
            # Se o valor for None, pula para o próximo
            if valor_causa is None:
                continue
            
            # Converte o valor usando a função auxiliar
            valor_convertido = _converter_valor_causa(valor_causa)
            
            # Soma apenas se o valor for válido e maior que zero
            if valor_convertido > 0:
                total += valor_convertido
    
    return total

# Retorna a soma do valor da causa para protocolos por atendente.
def get_valor_causa_protocolo_novo_por_atendente(protocolos: List[Dict[str, Any]]) -> Dict[str, float]:
    atendente_values = defaultdict(float)
    for p in protocolos:
        # Verifica se atende aos critérios
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["DISTRIBUÍDO", "PROTOCOLADO"]
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
        
        if status_ok and reajuizamento_ok:
            atendente = p.get("ATENDENTE") or "Sem atendente"
            atendente_formatado = _formatar_nome_atendente(atendente)
            materia = str(p.get("MATERIA") or "").strip().upper()
            valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA"))
            if valor_causa is not None:
                valor_convertido = _converter_valor_causa(valor_causa)
                if valor_convertido > 0:
                    atendente_values[atendente_formatado] += valor_convertido
    
    return dict(atendente_values)

# Retorna a soma do valor de causa para protocolos por funcionário.
def get_valor_causa_protocolo_novo_por_funcionario(protocolos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Valor de causa dos protocolados (status DISTRIBUÍDO/PROTOCOLADO, reajuizamento False) agrupado por FUNCIONARIO."""
    funcionario_values = defaultdict(float)
    for p in protocolos:
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["DISTRIBUÍDO", "PROTOCOLADO"]
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
        if status_ok and reajuizamento_ok:
            funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
            materia = str(p.get("MATERIA") or "").strip().upper()
            valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA"))
            if valor_causa is not None:
                valor_convertido = _converter_valor_causa(valor_causa)
                if valor_convertido > 0:
                    funcionario_values[funcionario] += valor_convertido
    return dict(funcionario_values)

# Retorna o ticket medio de protocolos resolvidos.
def get_ticket_medio_protocolos_resolvidos(protocolos: List[Dict[str, Any]]) -> float:
    qtd = get_protocolos_resolvidos(protocolos)
    if qtd == 0:
        # print(f"[get_ticket_medio_protocolos_resolvidos] retorno: 0.0 (qtd=0)")
        return 0.0
    valor = get_valor_causa_protocolo_novo(protocolos) / qtd
    # print(f"[get_ticket_medio_protocolos_resolvidos] retorno: {valor} (valor_causa/{qtd})")
    return round(valor, 2)

# Retorna a soma do valor de causa para protocolos em 2026. (METRICA DO COMERCIAL).
def get_valor_causa_protocolo_2026(protocolos: List[Dict[str, Any]]) -> float:
    """
    Retorna a soma do valor de causa dos processos protocolados em 2026.
    Usa a mesma lógica de get_valor_causa_protocolo_novo (status DISTRIBUÍDO/PROTOCOLADO,
    reajuizamento FALSE), filtrando apenas pelo ano 2026 na data de saída (protocolo).
    """
    protocolos_2026 = _filtrar_protocolos_por_ano(protocolos, 2026)
    return get_valor_causa_protocolo_novo(protocolos_2026)

# Agrupa processos protocolados por Materia.
def group_protocolados_por_materia(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Materia (rótulo = :func:`_normalizar_materia`, alinhado ao filtro)."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos protocolados por Funcionario.
def group_protocolados_por_funcionario(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Funcionario."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# R$ 1,00 por processo protocolado (resolvido).
_VALOR_COMISSAO_POR_PROTOCOLADO = Decimal("1.00")


def get_protocolo_comissionamento_por_funcionario(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Comissão = R$ 1,00 × quantidade de processos protocolados (resolvidos).
    O valor de causa não entra no cálculo (ex.: 500 processos → R$ 500,00).

    Usa apenas `group_protocolados_por_funcionario` (DISTRIBUÍDO/PROTOCOLADO, sem reajuizamento).

    Retorna linhas com: funcionario, qtd_protocolados, valor_comissao.
    """
    linhas: List[Dict[str, Any]] = []
    for r in group_protocolados_por_funcionario(protocolos):
        nome = r["name"]
        qtd = int(r["value"])
        comissao = (_VALOR_COMISSAO_POR_PROTOCOLADO * Decimal(qtd)).quantize(Decimal("0.01"))
        linhas.append({
            "funcionario": nome,
            "qtd_protocolados": qtd,
            "valor_comissao": float(comissao),
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# Agrupa processos protocolados por Sistema.
def group_protocolados_por_sistema(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Sistema."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        sistema = p.get("SISTEMA") or "Sem sistema"
        grouped[sistema] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Função auxiliar para extrair os dias
def _extrair_duracoes_dias(protocolos: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    duracoes: List[float] = []

    for p in protocolos_agrupados:
        try:
            entrada_str = p.get("ENTRADA") or p.get("entrada")
            saida_str = p.get("SAIDA") or p.get("saida")

            if not entrada_str or not saida_str:
                continue

            entrada_date = parse_date_from_db(entrada_str)
            saida_date = parse_date_from_db(saida_str)

            if not entrada_date or not saida_date:
                continue

            if isinstance(entrada_date, datetime):
                entrada_date = entrada_date.date()
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()

            if not isinstance(entrada_date, date) or not isinstance(saida_date, date):
                continue

            duracao_dias = (saida_date - entrada_date).days
            if duracao_dias > 0:
                duracoes.append(float(duracao_dias))

        except (ValueError, AttributeError, TypeError):
            continue

    return duracoes

# Retorna o tempo médio (em dias) para o processo protocolado no setor, de forma geral.
def get_media_tempo_protocolado(protocolos: List[Dict[str, Any]]) -> float:
    """Tempo médio (em dias) entre DATA_EXECUCAO e DATA_ENCERRAMENTO."""
    duracoes = _extrair_duracoes_dias(protocolos)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) para o processo protocolado no setor, de forma geral.
def get_mediana_tempo_protocolado(protocolos: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(protocolos)

    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)

# Função auxiliar para extrair os dias desde a contratacao ate o protocolo.
def _extrair_duracoes_dias_pre_protocolo(protocolos: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    duracoes: List[float] = []

    for p in protocolos_agrupados:
        try:
            entrada_str = p.get("DATA_CONTRATACAO") or p.get("data_contratacao")
            saida_str = p.get("SAIDA") or p.get("saida")

            if not entrada_str or not saida_str:
                continue

            entrada_date = parse_date_from_db(entrada_str)
            saida_date = parse_date_from_db(saida_str)

            if not entrada_date or not saida_date:
                continue

            if isinstance(entrada_date, datetime):
                entrada_date = entrada_date.date()
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()

            if not isinstance(entrada_date, date) or not isinstance(saida_date, date):
                continue

            duracao_dias = (saida_date - entrada_date).days
            if duracao_dias > 0:
                duracoes.append(float(duracao_dias))

        except (ValueError, AttributeError, TypeError):
            continue

    return duracoes

# Retorna o tempo médio (em dias) para o processo protocolado no setor, de forma geral.
def get_media_tempo_contratacao_protocolado(protocolos: List[Dict[str, Any]]) -> float:
    """Tempo médio (em dias) entre DATA_EXECUCAO e DATA_ENCERRAMENTO."""
    duracoes = _extrair_duracoes_dias_pre_protocolo(protocolos)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) entre contratação e protocolo.
def get_mediana_tempo_contratacao_protocolado(protocolos: List[Dict[str, Any]]) -> float:
    """Mediana do tempo (em dias) entre assinatura do contrato (DATA_CONTRATACAO) e protocolo (SAIDA)."""
    duracoes = _extrair_duracoes_dias_pre_protocolo(protocolos)
    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)

# Retorna o comparativo do tempo médio de contratação até protocolo (vs período anterior equivalente).
def get_comparativo_tempo_medio_contratacao_protocolado(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    tempo_medio_atual = get_media_tempo_contratacao_protocolado(dados_periodo_atual)
    tempo_medio_anterior = get_media_tempo_contratacao_protocolado(dados_periodo_anterior)

    if tempo_medio_anterior == 0:
        return 0.0
    variacao = ((tempo_medio_atual - tempo_medio_anterior) / tempo_medio_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo da mediana de tempo de contratação até protocolo (vs período anterior equivalente).
def get_comparativo_mediana_tempo_contratacao_protocolado(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    mediana_atual = get_mediana_tempo_contratacao_protocolado(dados_periodo_atual)
    mediana_anterior = get_mediana_tempo_contratacao_protocolado(dados_periodo_anterior)

    if mediana_anterior == 0:
        return 0.0
    variacao = ((mediana_atual - mediana_anterior) / mediana_anterior) * 100
    return round(variacao, 2)

# Retorna a média de processos resolvidos por funcionário.
def get_media_protocolados_por_funcionario(
    protocolos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Média de processos protocolados por FUNCIONARIO."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        saida_str = p.get("SAIDA") or p.get("saida")

        grouped[funcionario]["total"] += 1

        if saida_str:
            try:
                saida_date = parse_date_from_db(saida_str)
                if not saida_date:
                    continue

                data_key = saida_date

                if from_date or to_date:
                    if from_date and to_date:
                        if from_date <= data_key <= to_date:
                            grouped[funcionario]["dias"].add(data_key)
                    elif from_date:
                        if data_key >= from_date:
                            grouped[funcionario]["dias"].add(data_key)
                    elif to_date:
                        if data_key <= to_date:
                            grouped[funcionario]["dias"].add(data_key)
                else:
                    grouped[funcionario]["dias"].add(data_key)
            except (ValueError, AttributeError, TypeError):
                pass

    result = []
    for funcionario, stats in grouped.items():
        total = stats["total"]
        dias = len(stats["dias"])
        if dias > 0:
            media = total / dias
            result.append({
                "name": funcionario,
                "value": round(media, 2)
            })
    return sorted(result, key=lambda x: x["value"], reverse=True)

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]

def group_protocolados_por_mes(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos Protocolados por Mês."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped: Dict[str, Dict[str, Any]] = {}

    for p in protocolos_agrupados:
        try:
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue

            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue

            month_key = f"{saida_date.year}-{saida_date.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[saida_date.month - 1]} {saida_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]  # ou sort por month_key

def group_valor_causa_protocolados_por_mes(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a soma do valor de causa dos processos Protocolados por Mês."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped: Dict[str, Dict[str, Any]] = {}

    for p in protocolos_agrupados:
        try:
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue

            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue

            materia = str(p.get("MATERIA") or "").strip().upper()
            valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (
                p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
            )
            if valor_causa is None:
                continue

            valor_convertido = _converter_valor_causa(valor_causa)
            if valor_convertido <= 0:
                continue

            month_key = f"{saida_date.year}-{saida_date.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[saida_date.month - 1]} {saida_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            grouped[month_key]["value"] += valor_convertido

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]

# agrupa processos protocolados por dia.
def group_protocolados_por_dia(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por dia. Retorna lista [{ name, value }, ...] ordenada por data."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        saida_str = p.get("SAIDA") or p.get("saida")
        if not saida_str:
            continue
        dt = parse_date_from_db(saida_str)
        if dt:
            dia_key = dt.strftime("%Y-%m-%d")
            grouped[dia_key] += 1
    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": count} for dia, count in sorted_items]


def group_valor_causa_protocolados_por_dia(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a soma do valor de causa dos processos protocolados por dia."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(float)
    for p in protocolos_agrupados:
        saida_str = p.get("SAIDA") or p.get("saida")
        if not saida_str:
            continue

        dt = parse_date_from_db(saida_str)
        if not dt:
            continue

        materia = str(p.get("MATERIA") or "").strip().upper()
        valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (
            p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
        )
        if valor_causa is None:
            continue

        valor_convertido = _converter_valor_causa(valor_causa)
        if valor_convertido <= 0:
            continue

        dia_key = dt.strftime("%Y-%m-%d")
        grouped[dia_key] += valor_convertido

    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": round(valor, 2)} for dia, valor in sorted_items]

# Retorna processos protocolados por dia por funcionário.
def get_protocolados_por_dia_por_funcionario(protocolos: List[Dict[str, Any]]) -> Dict[str, Any]:
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    # grouped[dia][funcionario] = count
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in protocolos_agrupados:
        saida_str = p.get("SAIDA") or p.get("saida")
        if not saida_str:
            continue
        dt = parse_date_from_db(saida_str)
        if dt:
            dia_key = dt.strftime("%Y-%m-%d")
            funcionario = p.get("FUNCIONARIO") or "Sem funcionário"
            grouped[dia_key][funcionario] += 1

    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted(set(f for dia_data in grouped.values() for f in dia_data.keys()))
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {}
    for func in funcionarios:
        por_funcionario[func] = [
            {"name": dia, "value": grouped[dia].get(func, 0)}
            for dia in dias_ordenados
        ]
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}
# -----------------------------------------------------------------------------
# 3 - Funções de Não Protocolados
# -----------------------------------------------------------------------------

# Retorna a quantidade de protocolos não protocolados.
def get_nao_protocolados(protocolos: List[Dict[str, Any]]) -> int:
    return len(_filtrar_protocolos_nao_protocolados(protocolos))

# Retorna a quantidade de não protocolados de reajuizamento.
def get_nao_protocolados_de_reajuizamento(protocolos: List[Dict[str, Any]]) -> int:
    return len(_filtrar_nao_protocolados_de_reajuizamento(protocolos))

# Retorna a quantidade de protocolos não protocolados por atendente.
def get_nao_protocolados_por_atendente(protocolos: List[Dict[str, Any]]) -> Dict[str, int]:
    protocolos_nao_protocolados = _filtrar_protocolos_nao_protocolados(protocolos)
    atendente_counts = defaultdict(int)
    for p in protocolos_nao_protocolados:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# Retorna a soma do valor de causa para os não protocolados.
def get_valor_causa_protocolo_nao_protocolado(protocolos: List[Dict[str, Any]]) -> float:
    protocolos_nao_protocolados = _filtrar_protocolos_nao_protocolados(protocolos)
    total = 0.0
    for p in protocolos_nao_protocolados:
        # Tenta obter o valor da causa
        valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
        
        # Se o valor for None, pula para o próximo
        if valor_causa is None:
            continue
        
        # Converte o valor usando a função auxiliar
        valor_convertido = _converter_valor_causa(valor_causa)
        
        # Soma apenas se o valor for válido e maior que zero
        if valor_convertido > 0:
            total += valor_convertido
    
    return total if total > 0.0 else 0.0

# Retorna a soma do valor de causa para os não protocolados por atendente.
def get_valor_causa_protocolo_nao_protocolado_por_atendente(protocolos: List[Dict[str, Any]]) -> Dict[str, float]:
    protocolos_nao_protocolados = _filtrar_protocolos_nao_protocolados(protocolos)
    atendente_values = defaultdict(float)
    for p in protocolos_nao_protocolados:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        
        # Tenta obter o valor da causa
        valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
        if valor_causa is not None:
            valor_convertido = _converter_valor_causa(valor_causa)
            if valor_convertido > 0:
                atendente_values[atendente_formatado] += valor_convertido
    
    return dict(atendente_values)

# Agrupa processos não protocolados por Materia.
def group_nao_protocolados_por_materia(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agrupados = _filtrar_protocolos_nao_protocolados(protocolos)
    # print(f"[DEBUG] group_represados_por_materia — total filtrados: {len(agrupados)}")
    group = defaultdict(int)
    for p in agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        group[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in group.items()
    ]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print(f"[DEBUG] group_represados_por_materia — resultado ({len(result)} itens): {result[:5]}")
    return result

# Agrupa processos não protocolados por Funcionario.
def group_nao_protocolados_por_funcionario(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não protocolados por Funcionario."""
    protocolos_agrupados = _filtrar_protocolos_nao_protocolados(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

_SEM_DATA_KEY = "_sem_data"
_SEM_DATA_ENTRY = {"name": "Sem data", "value": 0}
_SEM_DATA_SORT = "9999-99"

def group_nao_protocolados_por_mes(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não protocolados por Mês."""
    protocolos_agrupados = _filtrar_protocolos_nao_protocolados(protocolos)
    grouped: Dict[str, Dict[str, Any]] = {}

    def _registrar_sem_data():
        grouped.setdefault(_SEM_DATA_KEY, {"name": "Sem data", "value": 0})
        grouped[_SEM_DATA_KEY]["value"] += 1

    for p in protocolos_agrupados:
        try:
            entrada_str = p.get("ENTRADA") or p.get("entrada")
            if not entrada_str:
                _registrar_sem_data()
                continue

            entrada_date = parse_date_from_db(entrada_str)
            if not entrada_date:
                _registrar_sem_data()
                continue

            month_key = f"{entrada_date.year}-{entrada_date.month:02d}"
            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[entrada_date.month - 1]} {entrada_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0}
            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            _registrar_sem_data()

    def _sort_key(item: tuple) -> tuple:
        k, _ = item
        return (1, _SEM_DATA_SORT) if k == _SEM_DATA_KEY else (0, k)

    return [v for _, v in sorted(grouped.items(), key=_sort_key)]

# -----------------------------------------------------------------------------
# 4 - Funções de Comparativos
# -----------------------------------------------------------------------------

def _valor_periodo_anterior_protocolo(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]],
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
    """
    Valor absoluto da métrica no período anterior (mesmo recorte de calendário
    usado pelas funções ``get_comparativo_*``).

    Necessário porque o Estratégico Geral combina NG+LA+RJ somando os valores
    absolutos de cada escritório antes de calcular UM percentual combinado —
    nunca somando os percentuais de cada escritório entre si (matematicamente
    inválido: dois +30% de bases diferentes não fazem um +60% combinado).
    """
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return metrica_fn(
        _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    )


def get_protocolos_resolvidos_periodo_anterior(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior_protocolo(
        protocolos, all_protocolos, from_date, to_date, get_protocolos_resolvidos
    )


def get_valor_causa_protocolo_periodo_anterior(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior_protocolo(
        protocolos, all_protocolos, from_date, to_date, get_valor_causa_protocolo_novo
    )


# Retorna a variação percentual do valor de causa para protocolos.
def get_comparativo_valor_causa_protocolo(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    protocolos_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    protocolos_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular valor total da causa em cada período
    dados_periodo_atual = get_valor_causa_protocolo_novo(protocolos_periodo_atual)
    dados_periodo_anterior = get_valor_causa_protocolo_novo(protocolos_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de protocolos resolvidos.
def get_comparativo_protocolos_resolvidos(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    protocolos_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    protocolos_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_protocolos_resolvidos(protocolos_periodo_atual)
    dados_periodo_anterior = get_protocolos_resolvidos(protocolos_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de não protocolados.
def get_comparativo_nao_protocolados(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    protocolos_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    protocolos_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de não protocolados em cada período
    dados_periodo_atual = get_nao_protocolados(protocolos_periodo_atual)
    dados_periodo_anterior = get_nao_protocolados(protocolos_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de ticket medio de protocolos resolvidos.
def get_comparativo_ticket_medio_protocolos_resolvidos(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    protocolos_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    protocolos_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular ticket medio em cada período
    dados_periodo_atual = get_ticket_medio_protocolos_resolvidos(protocolos_periodo_atual)
    dados_periodo_anterior = get_ticket_medio_protocolos_resolvidos(protocolos_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de tempo médio de protocolos resolvidos.
def get_comparativo_tempo_medio_protocolos_resolvidos(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_media_tempo_protocolado(dados_periodo_atual)
    dados_periodo_anterior = get_media_tempo_protocolado(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)


# -----------------------------------------------------------------------------
# 2.1 - Medidas de comissão proporcional (DAX -> Python)
# -----------------------------------------------------------------------------

def get_fator_multiplicador_para_atingido(atingido: float) -> float:
    """
    FM (1,0 a 4,0) a partir do valor de causa protocolado (atingido), mesma escada do DAX.

    IF(Atingido > 4000000, 4.0,
       IF(Atingido >= 2500000 && Atingido <= 4000000, Atingido/1000000, 1))
    """
    a = float(atingido or 0.0)
    if a > 4_000_000:
        return 4.0
    if 2_500_000 <= a <= 4_000_000:
        return a / 1_000_000
    return 1.0


def get_fator_multiplicador(protocolos: List[Dict[str, Any]]) -> float:
    """
    FATOR_MULTIPLICADOR (FM) baseado no VALOR_CAUSA_PROTOCOLO global.

    Observação: VALOR_CAUSA_PROTOCOLO usa a mesma lógica de `get_valor_causa_protocolo_novo`.
    """
    atingido = float(get_valor_causa_protocolo_novo(protocolos) or 0.0)
    return get_fator_multiplicador_para_atingido(atingido)


def _valor_causa_row_protocolo(p: Dict[str, Any]) -> float:
    """Equivalente ao IF(MATERIA='ANP', DANO_MORAL, VALOR_DA_CAUSA) com fallback."""
    materia = str(p.get("MATERIA") or "").strip().upper()
    if materia == "ANP":
        valor = p.get("DANO_MORAL")
    else:
        valor = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
    return _converter_valor_causa(valor)


def get_valor_por_estado_am_pa(protocolos: List[Dict[str, Any]]) -> float:
    """
    VALOR_POR_ESTADO_AM_PA conforme DAX.

    DAX filtra:
    - STATUS = "DISTRIBUÍDO"
    - UF in {"AM","PA"}
    - REAJUIZAMENTO = "False"
    e soma por linha: IF(MATERIA="ANP", DANO_MORAL, VALOR_DA_CAUSA)
    """
    total = 0.0
    for p in protocolos:
        status_ok = str(p.get("STATUS") or "").strip().upper() == "DISTRIBUÍDO"
        uf_ok = str(p.get("UF") or "").strip().upper() in {"AM", "PA"}
        reaju_ok = (str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or p.get("REAJUIZAMENTO") is False)
        if status_ok and uf_ok and reaju_ok:
            v = _valor_causa_row_protocolo(p)
            if v > 0:
                total += v
    return total

def get_valor_por_estado_pb(protocolos: List[Dict[str, Any]]) -> float:
    total = 0.0
    for p in protocolos:
        status_ok = str(p.get("STATUS") or "").strip().upper() == "DISTRIBUÍDO"
        uf_ok = str(p.get("UF") or "").strip().upper() in {"PB"}
        reaju_ok = (str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or p.get("REAJUIZAMENTO") is False)
        if status_ok and uf_ok and reaju_ok:
            v = _valor_causa_row_protocolo(p)
            if v > 0:
                total += v
    return total


def _get_valor_por_estado(protocolos: List[Dict[str, Any]], ufs: set[str]) -> float:
    """Versão genérica do VALOR_POR_ESTADO_* com os mesmos filtros do DAX (STATUS DISTRIBUÍDO, REAJUIZAMENTO False)."""
    total = 0.0
    ufs_norm = {str(u).strip().upper() for u in ufs}
    for p in protocolos:
        status_ok = str(p.get("STATUS") or "").strip().upper() == "DISTRIBUÍDO"
        uf_ok = str(p.get("UF") or "").strip().upper() in ufs_norm
        reaju_ok = (str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or p.get("REAJUIZAMENTO") is False)
        if status_ok and uf_ok and reaju_ok:
            v = _valor_causa_row_protocolo(p)
            if v > 0:
                total += v
    return total


def get_comissao_proporcional_am_pa(
    protocolos: List[Dict[str, Any]],
    *,
    comissao_base: float,
) -> float:
    """
    COMISSAO_PROPORCIONAL_AM_PA em **reais** (mesmo valor exibido no Power BI como moeda).

    DAX usa DIVIDE(ValorEstado, ValorTotalCausa, 0) * [FM]. No modelo, o cartão em R$ corresponde a
    aplicar essa razão sobre o **pool de comissão**: FATOR_MULTIPLICADOR × COMISSAO_BASE do período
    (COMISSAO_BASE = soma VALOR_AM das ações fechadas, mesma lógica do comercial).

    Portanto: (ValorEstado / ValorTotalCausa) * get_fator_multiplicador * comissao_base
    """
    valor_estado = float(get_valor_por_estado_am_pa(protocolos) or 0.0)
    valor_total = float(get_valor_causa_protocolo_novo(protocolos) or 0.0)
    base = float(comissao_base or 0.0)
    if valor_total <= 0 or base <= 0:
        return 0.0
    fm = float(get_fator_multiplicador(protocolos) or 0.0)
    return round((valor_estado / valor_total) * fm * base, 2)


def get_comissao_proporcional_am(
    protocolos: List[Dict[str, Any]],
    *,
    comissao_base: float,
) -> float:
    """COMISSAO_PROPORCIONAL_AM em reais: (ValorEstado_AM / ValorTotalCausa) * FM * COMISSAO_BASE."""
    valor_total = float(get_valor_causa_protocolo_novo(protocolos) or 0.0)
    base = float(comissao_base or 0.0)
    if valor_total <= 0 or base <= 0:
        return 0.0
    fm = float(get_fator_multiplicador(protocolos) or 0.0)
    valor_estado = _get_valor_por_estado(protocolos, {"AM"})
    return round((valor_estado / valor_total) * fm * base, 2)


def get_comissao_proporcional_pa(
    protocolos: List[Dict[str, Any]],
    *,
    comissao_base: float,
) -> float:
    """COMISSAO_PROPORCIONAL_PA em reais: (ValorEstado_PA / ValorTotalCausa) * FM * COMISSAO_BASE."""
    valor_total = float(get_valor_causa_protocolo_novo(protocolos) or 0.0)
    base = float(comissao_base or 0.0)
    if valor_total <= 0 or base <= 0:
        return 0.0
    fm = float(get_fator_multiplicador(protocolos) or 0.0)
    valor_estado = _get_valor_por_estado(protocolos, {"PA"})
    return round((valor_estado / valor_total) * fm * base, 2)


def get_comissao_proporcional_pb(
    protocolos: List[Dict[str, Any]],
    *,
    comissao_base: float,
) -> float:
    """COMISSAO_PROPORCIONAL_PB em reais: (ValorEstado_PB / ValorTotalCausa) * FM * COMISSAO_BASE."""
    valor_total = float(get_valor_causa_protocolo_novo(protocolos) or 0.0)
    base = float(comissao_base or 0.0)
    if valor_total <= 0 or base <= 0:
        return 0.0
    fm = float(get_fator_multiplicador(protocolos) or 0.0)
    valor_estado = _get_valor_por_estado(protocolos, {"PB"})
    return round((valor_estado / valor_total) * fm * base, 2)

def get_comissao_com_fm(
    protocolos: List[Dict[str, Any]],
    comercial_geral: List[Dict[str, Any]],
) -> float:
    """
    Pool de comissão após o fator: COMISSAO_BASE (período) × FATOR_MULTIPLICADOR (valor causa protocolo).
    `comercial_geral` deve estar no mesmo recorte de datas usado em `protocolos`.
    """
    fm = float(get_fator_multiplicador(protocolos) or 0.0)
    base = float(get_comissao_base(comercial_geral) or 0.0)
    return round(fm * base, 2)


def get_proporcionais_am_pa_pb_sobre_comissao_com_fm(
    protocolos: List[Dict[str, Any]],
    comissao_com_fm: float,
) -> Tuple[float, float]:
    """
    Reparte o pool **comissao_com_fm** entre os cartões AM/PA e PB com soma exata ao total (como no PBI).

    A fatia de PB segue o DAX: DIVIDE(valor_pb, VALOR_CAUSA_PROTOCOLO, 0) × pool.
    O valor de AM/PA é o **resto** do pool (absorve demais UFs, PROTOCOLADO no denominador vs DISTRIBUÍDO
    só nos estados, etc.), para que proporcional_am_pa + proporcional_pb == comissao_com_fm.
    """
    pool = float(comissao_com_fm or 0.0)
    valor_total = float(get_valor_causa_protocolo_novo(protocolos) or 0.0)
    if pool <= 0:
        return 0.0, 0.0
    if valor_total <= 0:
        return round(pool, 2), 0.0

    v_pb = float(get_valor_por_estado_pb(protocolos) or 0.0)
    proporcional_pb = round((v_pb / valor_total) * pool, 2)
    if proporcional_pb < 0:
        proporcional_pb = 0.0
    if proporcional_pb > pool:
        proporcional_pb = round(pool, 2)
    proporcional_am_pa = round(pool - proporcional_pb, 2)
    return proporcional_am_pa, proporcional_pb