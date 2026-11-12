# Análises e processamento de dados de Andamento Processual LA

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
from decimal import Decimal
import statistics

from app.utils import parse_datetime_from_db, parse_date_from_db


def _formatar_nome_responsavel_andamento_LA(nome_completo: str) -> str:
    """Mesmo padrão de exibição/filtro que outros dashboards (primeiro + segundo nome, maiúsculo)."""
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo

    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0].upper()
    return " ".join(partes[:2]).upper()


def _chave_responsavel_andamento_LA(item: Dict[str, Any]) -> str:
    nome = item.get("RESPONSAVEL") or item.get("responsavel") or ""
    return _formatar_nome_responsavel_andamento_LA(str(nome).strip()) if nome else ""


def list_funcionarios_andamento_processual_LA(andamento_processual: List[Dict[str, Any]]) -> List[str]:
    """Nomes curtos únicos dos responsáveis no conjunto (para select no frontend)."""
    chaves = {_chave_responsavel_andamento_LA(item) for item in andamento_processual}
    chaves.discard("")
    return sorted(chaves)


def filter_andamento_processual_por_funcionario_LA(
    andamento_processual: List[Dict[str, Any]],
    nome_funcionario: str,
) -> List[Dict[str, Any]]:
    """Filtra linhas cujo responsável corresponde ao valor retornado em list_funcionarios_andamento_processual_LA."""
    alvo = str(nome_funcionario).strip()
    if not alvo:
        return andamento_processual
    return [a for a in andamento_processual if _chave_responsavel_andamento_LA(a) == alvo]


def filter_andamento_processual_por_funcionarios_LA(
    andamento_processual: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais responsáveis (união — OR)."""
    if not funcionarios:
        return list(andamento_processual)
    alvos = {
        str(f).strip()
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(andamento_processual)
    return [a for a in andamento_processual if _chave_responsavel_andamento_LA(a) in alvos]


# Retorna os Resolvidos do Andamento Processual
def get_andamento_resolvido_LA(andamento_processual: List[Dict[str, Any]]) -> int:
    return len([
        a for a in andamento_processual
        if a.get("STATUS") and str(a.get("STATUS", "")).upper() == "RESOLVIDO"
    ])

# Retorna os Não Resolvidos do Andamento Processual
def get_andamento_nao_resolvido_LA(andamento_processual: List[Dict[str, Any]]) -> int:
    return len([
        a for a in andamento_processual
        if a.get("STATUS") and (
            str(a.get("STATUS", "")).upper() == "NÃO INICIADO" or 
            str(a.get("STATUS", "")).upper() == "EM ANDAMENTO"
        )
    ])

# Retorna o Total de Andamento Processual
def get_andamento_total_LA(andamento_processual: List[Dict[str, Any]]) -> int:
    return len(andamento_processual)

# Retorna a média de avaliações, quando não houver avaliações, retorna None
def get_andamento_media_avaliacao_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    avaliacoes = []
    for item in andamento_processual:
        avaliacao = item.get("AVALIACAO") or item.get("avaliacao")
        if avaliacao is not None:
            try:
                # Tenta converter para float
                valor = float(avaliacao)
                avaliacoes.append(valor)
            except (ValueError, TypeError):
                continue
    
    if not avaliacoes:
        return None
    
    return round(sum(avaliacoes) / len(avaliacoes), 2)

# Retorna a taxa de resolvidos do Andamento Processual
def get_andamento_taxa_resolvidos_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    total = get_andamento_total_LA(andamento_processual)
    if total == 0:
        return None
    return round((get_andamento_resolvido_LA(andamento_processual) / total) * 100, 2)

# Retorna a taxa de não resolvidos do Andamento Processual
def get_andamento_taxa_nao_resolvidos_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    total = get_andamento_total_LA(andamento_processual)
    if total == 0:
        return None
    return round((get_andamento_nao_resolvido_LA(andamento_processual) / total) * 100, 2)

# Função auxiliar para extrair os dias
# def _extrair_duracoes_dias(andamento_processual: List[Dict[str, Any]]) -> List[float]:
#     protocolos_agrupados = get_andamento_resolvido_LA(andamento_processual)
#     duracoes: List[float] = []

#     for p in protocolos_agrupados:
#         try:
#             entrada_str = p.get("ENTRADA") or p.get("entrada")
#             saida_str = p.get("INICIO_ATENDIMENTO") or p.get("inicio_atendimento")

#             if not entrada_str or not saida_str:
#                 continue

#             entrada_date = parse_date_from_db(entrada_str)
#             saida_date = parse_date_from_db(saida_str)

#             if not entrada_date or not saida_date:
#                 continue

#             if isinstance(entrada_date, datetime):
#                 entrada_date = entrada_date.date()
#             if isinstance(saida_date, datetime):
#                 saida_date = saida_date.date()

#             if not isinstance(entrada_date, date) or not isinstance(saida_date, date):
#                 continue

#             duracao_dias = (saida_date - entrada_date).days
#             if duracao_dias > 0:
#                 duracoes.append(float(duracao_dias))

#         except (ValueError, AttributeError, TypeError):
#             continue

#     return duracoes

# Retorna a média do tempo de espera
def get_andamento_media_tempo_espera_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    tempos_espera_horas = []
    
    for item in andamento_processual:
        entrada_str = item.get("ENTRADA") or item.get("entrada")
        inicio_str = item.get("INICIO_ATENDIMENTO") or item.get("inicio_atendimento")
        
        if not entrada_str or not inicio_str:
            continue
        
        try:
            entrada_dt = parse_datetime_from_db(entrada_str)
            inicio_dt = parse_datetime_from_db(inicio_str)
            
            if not entrada_dt or not inicio_dt:
                continue
            
            # Calcula diferença em horas
            diferenca = (inicio_dt - entrada_dt).total_seconds() / 3600
            
            # Só adiciona se a diferença for positiva (início após entrada)
            if diferenca >= 0:
                tempos_espera_horas.append(diferenca)
        except (ValueError, AttributeError, TypeError):
            continue
    
    if not tempos_espera_horas:
        return None
    
    return round(sum(tempos_espera_horas) / len(tempos_espera_horas), 2)

# Retorna a mediana do tempo de espera
def get_andamento_mediana_tempo_espera_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    tempos_espera_horas = []
    
    for item in andamento_processual:
        entrada_str = item.get("ENTRADA") or item.get("entrada")
        inicio_str = item.get("INICIO_ATENDIMENTO") or item.get("inicio_atendimento")
        
        if not entrada_str or not inicio_str:
            continue
        
        try:
            entrada_dt = parse_datetime_from_db(entrada_str)
            inicio_dt = parse_datetime_from_db(inicio_str)
            
            if not entrada_dt or not inicio_dt:
                continue
            
            # Calcula diferença em horas
            diferenca = (inicio_dt - entrada_dt).total_seconds() / 3600
            
            # Só adiciona se a diferença for positiva (início após entrada)
            if diferenca >= 0:
                tempos_espera_horas.append(diferenca)
        except (ValueError, AttributeError, TypeError):
            continue
    
    if not tempos_espera_horas:
        return None
    
    return round(statistics.median(tempos_espera_horas), 2)

# Retorna o a média do tempo de atendimento do cliente
def get_andamento_media_tempo_atendimento_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calcula a média do tempo de espera em horas.
    Tempo de espera = diferença entre INICIO_ATENDIMENTO e ENTRADA.
    Retorna None se não houver dados válidos.
    """
    tempos_atendimento_horas = []
    
    for item in andamento_processual:
        inicio_str = item.get("INICIO_ATENDIMENTO") or item.get("inicio_atendimento")
        saida_str = item.get("SAIDA") or item.get("saida")
        
        if not inicio_str or not saida_str:
            continue
        
        try:
            inicio_dt = parse_datetime_from_db(inicio_str)
            saida_dt = parse_datetime_from_db(saida_str)
            
            if not inicio_dt or not saida_dt:
                continue
            
            # Calcula diferença em horas
            diferenca = (saida_dt - inicio_dt).total_seconds() / 3600
            
            # Só adiciona se a diferença for positiva (início após entrada)
            if diferenca >= 0:
                tempos_atendimento_horas.append(diferenca)
        except (ValueError, AttributeError, TypeError):
            continue
    
    if not tempos_atendimento_horas:
        return None
    
    return round(sum(tempos_atendimento_horas) / len(tempos_atendimento_horas), 2)

# Retorna a mediana do tempo de atendimento do cliente
def get_andamento_mediana_tempo_atendimento_LA(andamento_processual: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calcula a mediana do tempo de atendimento do cliente em horas.
    Tempo de atendimento = diferença entre INICIO_ATENDIMENTO e SAIDA.
    Retorna None se não houver dados válidos.
    """
    tempos_atendimento_horas = []
    
    for item in andamento_processual:
        inicio_str = item.get("INICIO_ATENDIMENTO") or item.get("inicio_atendimento")  
        saida_str = item.get("SAIDA") or item.get("saida")

        if not inicio_str or not saida_str:
            continue
        
        try:
            inicio_dt = parse_datetime_from_db(inicio_str)
            saida_dt = parse_datetime_from_db(saida_str)
            
            if not inicio_dt or not saida_dt:
                continue
            
            # Calcula diferença em horas
            diferenca = (saida_dt - inicio_dt).total_seconds() / 3600
            
            # Só adiciona se a diferença for positiva (início após entrada)
            if diferenca >= 0:
                tempos_atendimento_horas.append(diferenca)
        except (ValueError, AttributeError, TypeError):
            continue
    
    if not tempos_atendimento_horas:
        return None
    
    return round(statistics.median(tempos_atendimento_horas), 2)

# Agrupa os andamentos processuais por colaborador e retorna o ranking ordenado por quantidade de andamentos processuais.
def group_andamento_processual_by_colaborador_LA(andamento_processual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Filtra apenas os itens resolvidos
    resolvidos = [
        a for a in andamento_processual
        if a.get("STATUS") and str(a.get("STATUS", "")).upper() == "RESOLVIDO"
    ]

    andamento_processual_by_colaborador = defaultdict(int)
    
    for item in resolvidos:
        colaborador = item.get("RESPONSAVEL") or item.get("responsavel")
        if colaborador:  # Só conta se houver colaborador
            andamento_processual_by_colaborador[colaborador] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in andamento_processual_by_colaborador.items()
    ]
    # Retorna ranking ordenado por quantidade (maior para menor)
    return sorted(result, key=lambda y: y["value"], reverse=True)[:5]

# Agrupa as avaliações por colaborador e retorna o ranking ordenado por média de avaliações.
def group_andamento_processual_by_colaborador_avaliacao_LA(andamento_processual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Filtra apenas os itens resolvidos
    resolvidos = [
        a for a in andamento_processual
        if a.get("STATUS") and str(a.get("STATUS", "")).upper() == "RESOLVIDO"
    ]
    
    # Agrupa itens resolvidos por colaborador
    itens_por_colaborador = defaultdict(list)
    for item in resolvidos:
        colaborador = item.get("RESPONSAVEL") or item.get("responsavel")
        if colaborador:
            itens_por_colaborador[colaborador].append(item)
    
    # Calcula a média de avaliações para cada colaborador usando get_andamento_media_avaliacao
    result = []
    for colaborador, itens in itens_por_colaborador.items():
        media = get_andamento_media_avaliacao_LA(itens)
        if media is not None:  # Só adiciona se houver avaliações
            result.append({"name": colaborador, "value": media})
    
    # Retorna ranking ordenado por média de avaliações (maior para menor)
    return sorted(result, key=lambda y: y["value"], reverse=True)[:5]

# Agrupa atendimentos resolvidos total por mês.
def group_andamento_processual_total_por_mes_LA(andamento_processual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa atendimentos resolvidos total por mês (usa data de SAIDA)."""
    resolvidos = [
        a for a in andamento_processual
        if a.get("STATUS") and str(a.get("STATUS", "")).upper() == "RESOLVIDO"
    ]
    grouped = {}
    month_names = [
        "jan", "fev", "mar", "abr", "mai", "jun",
        "jul", "ago", "set", "out", "nov", "dez"
    ]
    for item in resolvidos:
        try:
            data_saida_str = item.get("SAIDA") or item.get("saida")
            if not data_saida_str:
                continue

            data_saida = parse_date_from_db(data_saida_str)
            if not data_saida:
                continue
            if isinstance(data_saida, datetime):
                data_saida = data_saida.date()

            month_key = f"{data_saida.year}-{data_saida.month:02d}"
            month_name = f"{month_names[data_saida.month - 1]} {data_saida.year}"

            if month_key not in grouped:
                grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
            grouped[month_key]["value"] += 1
        except (ValueError, AttributeError, TypeError):
            continue

    result = [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]
    return result


def _valor_unitario_comissao_andamento_LA(media: Optional[float]) -> Decimal:
    """Faixas por média de avaliação (atendimento): 9,50–9,59 / 9,60–9,69 / ≥9,70; abaixo de 9,50 → 0."""
    if media is None:
        return Decimal("0")
    if media >= 9.70:
        return Decimal("1.30")
    if 9.60 <= media <= 9.69:
        return Decimal("0.80")
    if 9.50 <= media <= 9.59:
        return Decimal("0.30")
    return Decimal("0")


def get_andamento_comissionamento_por_funcionario_LA(
    andamento_processual: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Por colaborador (RESOLVIDO com responsável): média de avaliação (campo AVALIACAO) só dos
    itens daquele colaborador, qtd de atendimentos resolvidos, valor unitário da faixa e comissão.
    """
    resolvidos = [
        a for a in andamento_processual
        if a.get("STATUS") and str(a.get("STATUS", "")).upper() == "RESOLVIDO"
    ]
    itens_por_colaborador: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in resolvidos:
        colaborador = item.get("RESPONSAVEL") or item.get("responsavel")
        if colaborador:
            itens_por_colaborador[str(colaborador)].append(item)

    linhas: List[Dict[str, Any]] = []
    for funcionario, itens in itens_por_colaborador.items():
        qtd = len(itens)
        media = get_andamento_media_avaliacao_LA(itens)
        unit = _valor_unitario_comissao_andamento_LA(media)
        prod = (Decimal(qtd) * unit).quantize(Decimal("0.01"))
        comissao = float(prod)
        linhas.append({
            "funcionario": funcionario,
            "media_avaliacao": media,
            "qtd_atendimentos": qtd,
            "valor_unitario": float(unit),
            "valor_comissao": comissao,
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas