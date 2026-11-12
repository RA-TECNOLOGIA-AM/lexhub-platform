# Análises e processamento de dados de ACTIONS

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
import statistics
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.NG.comercial_geral import get_clientes_todos, get_clientes_campanha_RA, get_clientes_campanha_NG, _filter_by_date_range as filter_comercial_by_date_range, _formatar_nome_atendente

# Retorna o total de Leads
def get_total_leads(actions: List[Dict[str, Any]]) -> int:
    return len(actions)

# Retorna o total de Leads de Anúncio RA
def get_total_leads_anuncio_RA(actions: List[Dict[str, Any]]) -> int:
    filtered = [
        action for action in actions
        if action.get("CANAL_ATUAL") and str(action.get("CANAL_ATUAL", "")).strip().upper() == "ANUNCIO"
    ]
    return len(filtered)

# Retorna o total de Leads de Anúncio NG (inclui ANUNCIO_LA_RJ para o dashboard RJ)
_CANAIS_ANUNCIO_NG = frozenset({"ANUNCIO_NG", "ANUNCIO_LA_RJ"})

def get_total_leads_anuncio_NG(actions: List[Dict[str, Any]]) -> int:
    filtered = [
        action for action in actions
        if action.get("CANAL_ATUAL") and str(action.get("CANAL_ATUAL", "")).strip().upper() in _CANAIS_ANUNCIO_NG
    ]
    return len(filtered)

# Retorna o total de Leads de campanha (ANUNCIO + ANUNCIO_NG)
def get_total_leads_campanha(actions: List[Dict[str, Any]]) -> int:
    return get_total_leads_anuncio_RA(actions) + get_total_leads_anuncio_NG(actions)

# Retorna o taxa de Leads Geral
def get_taxa_leads_geral(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> float:
    total_leads = get_total_leads(actions)
    clientes_todos = get_clientes_todos(comercial_geral)
    
    if total_leads == 0:
        return 0.0
    
    if clientes_todos == 0:
        return 0.0
    
    taxa = (clientes_todos / total_leads) * 100
    resultado = round(taxa, 2)
    
    return resultado

# Retorna a taxa de Leads de Anúncio RA
def get_taxa_leads_anuncio_RA(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> float:
    total_leads_anuncio_RA = get_total_leads_anuncio_RA(actions)
    clientes_campanha_RA = get_clientes_campanha_RA(comercial_geral)
    
    if total_leads_anuncio_RA == 0:
        return 0.0
    
    if clientes_campanha_RA == 0:
        return 0.0
    
    taxa = (clientes_campanha_RA / total_leads_anuncio_RA) * 100
    resultado = round(taxa, 2)
    
    return resultado

# Retorna a taxa de Leads de Anúncio NG
def get_taxa_leads_anuncio_NG(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> float:
    total_leads_anuncio_NG = get_total_leads_anuncio_NG(actions)
    clientes_campanha_NG = get_clientes_campanha_NG(comercial_geral)
    
    if total_leads_anuncio_NG == 0:
        return 0.0
    
    if clientes_campanha_NG == 0:
        return 0.0
    
    taxa = (clientes_campanha_NG / total_leads_anuncio_NG) * 100
    resultado = round(taxa, 2)
    
    
    return resultado

def _filter_by_date_range(actions: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados de actions por intervalo de datas usando a coluna DATA_UPS."""
    filtered = []
    for item in actions:
        try:
            # Usa a coluna ENTRADA para filtrar
            entrada_str = item.get("ENTRADA") or item.get("entrada")
            if not entrada_str:
                continue

            entrada_date = parse_date_from_db(entrada_str)
            if not entrada_date:
                continue

            # Garantir que entrada_date é sempre date, não datetime
            if isinstance(entrada_date, datetime):
                entrada_date = entrada_date.date()
            elif not isinstance(entrada_date, date):
                continue

            # Verificar se a data está no intervalo
            if from_date <= entrada_date <= to_date:
                filtered.append(item)
        except (ValueError, AttributeError, TypeError):
            continue

    return filtered

# Retorna a variação percentual de Leads Geral
def get_comparativo_leads_geral(
    actions: List[Dict[str, Any]], 
    all_actions: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_actions if all_actions is not None else actions
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(actions, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de Leads Geral para cada período
    qtd_atual = get_total_leads(dados_periodo_atual)
    qtd_anterior = get_total_leads(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de Leads de Anúncio RA
def get_comparativo_leads_anuncio_RA(
    actions: List[Dict[str, Any]], 
    all_actions: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_actions if all_actions is not None else actions
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(actions, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de Leads de Anúncio RA para cada período
    qtd_atual = get_total_leads_anuncio_RA(dados_periodo_atual)
    qtd_anterior = get_total_leads_anuncio_RA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de Leads de Anúncio NG
def get_comparativo_leads_anuncio_NG(
    actions: List[Dict[str, Any]], 
    all_actions: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_actions if all_actions is not None else actions
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(actions, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de Leads de Anúncio NG para cada período
    qtd_atual = get_total_leads_anuncio_NG(dados_periodo_atual)
    qtd_anterior = get_total_leads_anuncio_NG(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de taxa de Leads Geral
def get_comparativo_taxa_leads_geral(
    actions: List[Dict[str, Any]], 
    comercial_geral: List[Dict[str, Any]],
    all_actions: Optional[List[Dict[str, Any]]] = None,
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca_actions = all_actions if all_actions is not None else actions
    dados_para_busca_comercial = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior (actions e comercial)
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    actions_periodo_atual = _filter_by_date_range(actions, data_inicio_atual, data_fim_atual)
    comercial_periodo_atual = filter_comercial_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    actions_periodo_anterior = _filter_by_date_range(dados_para_busca_actions, data_inicio_anterior, data_fim_anterior)
    comercial_periodo_anterior = filter_comercial_by_date_range(dados_para_busca_comercial, data_inicio_anterior, data_fim_anterior)
    
    # Calcular taxa de Leads Geral para cada período
    taxa_atual = get_taxa_leads_geral(actions_periodo_atual, comercial_periodo_atual)
    taxa_anterior = get_taxa_leads_geral(actions_periodo_anterior, comercial_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if taxa_anterior == 0:
        return 0.0
    
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de taxa de Leads de Anúncio RA
def get_comparativo_taxa_leads_anuncio_RA(
    actions: List[Dict[str, Any]], 
    comercial_geral: List[Dict[str, Any]],
    all_actions: Optional[List[Dict[str, Any]]] = None,
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca_actions = all_actions if all_actions is not None else actions
    dados_para_busca_comercial = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior (actions e comercial)
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    actions_periodo_atual = _filter_by_date_range(actions, data_inicio_atual, data_fim_atual)
    comercial_periodo_atual = filter_comercial_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    actions_periodo_anterior = _filter_by_date_range(dados_para_busca_actions, data_inicio_anterior, data_fim_anterior)
    comercial_periodo_anterior = filter_comercial_by_date_range(dados_para_busca_comercial, data_inicio_anterior, data_fim_anterior)
    
    # Calcular taxa de Leads de Anúncio RA para cada período
    taxa_atual = get_taxa_leads_anuncio_RA(actions_periodo_atual, comercial_periodo_atual)
    taxa_anterior = get_taxa_leads_anuncio_RA(actions_periodo_anterior, comercial_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if taxa_anterior == 0:
        return 0.0
    
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de taxa de Leads de Anúncio NG
def get_comparativo_taxa_leads_anuncio_NG(
    actions: List[Dict[str, Any]], 
    comercial_geral: List[Dict[str, Any]],
    all_actions: Optional[List[Dict[str, Any]]] = None,
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca_actions = all_actions if all_actions is not None else actions
    dados_para_busca_comercial = all_comercial_geral if all_comercial_geral is not None else comercial_geral

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior (actions e comercial)
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    actions_periodo_atual = _filter_by_date_range(actions, data_inicio_atual, data_fim_atual)
    comercial_periodo_atual = filter_comercial_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    actions_periodo_anterior = _filter_by_date_range(dados_para_busca_actions, data_inicio_anterior, data_fim_anterior)
    comercial_periodo_anterior = filter_comercial_by_date_range(dados_para_busca_comercial, data_inicio_anterior, data_fim_anterior)
    
    # Calcular taxa de Leads de Anúncio NG para cada período
    taxa_atual = get_taxa_leads_anuncio_NG(actions_periodo_atual, comercial_periodo_atual)
    taxa_anterior = get_taxa_leads_anuncio_NG(actions_periodo_anterior, comercial_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if taxa_anterior == 0:
        return 0.0
    
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# ===============================================
# RETORNA AS ANALISES PARA COLOCAR NO GRAFICO DE ATENDENTES 
# ===============================================

# Retorna o total de Leads (via get_total_leads) agrupado por atendente usando _formatar_nome_atendente
def get_total_leads_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_leads = get_total_leads(actions)
    atendente_counts = defaultdict(int)
    for action in actions:
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return {"total": total_leads, "por_atendente": dict(atendente_counts)}

# Canais que contam como contrato fechado (mesmo critério de get_clientes_todos em comercial_geral)
_CANAIS_CLIENTES_TODOS = {
    "ANUNCIO", "ANUNCIO_NG", "INDICAÇÃO",
    "REDES SOCIAIS", "INSTAGRAM", "X", "FACEBOOK",
    "RETORNO", "SITE", "RESGATE", "PARCEIRO", "EXTERNO",
}

# Canais de campanha (ANUNCIO + ANUNCIO_NG)
_CANAIS_CAMPANHA = {"ANUNCIO", "ANUNCIO_NG"}


# Retorna o total de leads de campanha (ANUNCIO + ANUNCIO_NG) e agrupa por atendente
def get_total_leads_campanha_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        if canal not in _CANAIS_CAMPANHA:
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total_leads_campanha = sum(atendente_counts.values())
    return {"total": total_leads_campanha, "por_atendente": dict(atendente_counts)}

# Retorna o total de clientes fechados de campanha (ANUNCIO + ANUNCIO_NG)
def get_total_clientes_fechados_campanha(comercial_geral: List[Dict[str, Any]]) -> int:
    return get_clientes_campanha_RA(comercial_geral) + get_clientes_campanha_NG(comercial_geral)


# Retorna o total de clientes fechados de campanha (ANUNCIO + ANUNCIO_NG) e agrupa por atendente
def get_total_clientes_fechados_campanha_por_atendente(comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_clientes_fechados_campanha = get_total_clientes_fechados_campanha(comercial_geral)
    # Só conta como cliente fechado de campanha: motivo_encerramento == 11 e canal ANUNCIO ou ANUNCIO_NG
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("motivo_encerramento") != 11:
            continue
        canal = (comercial.get("CANAL_ATUAL") or "").strip().upper()
        if canal not in _CANAIS_CAMPANHA:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    return {"total": total_clientes_fechados_campanha, "por_atendente": por_atendente}

# Retorna o total de contratos fechados (get_clientes_todos) e a quantidade por atendente
def get_total_clientes_fechados_por_atendente(comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_clientes_fechados = get_clientes_todos(comercial_geral)
    # Só conta como contrato fechado: motivo_encerramento == 11 e canal em um dos canais de get_clientes_todos
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("motivo_encerramento") != 11:
            continue
        canal = (comercial.get("CANAL_ATUAL") or "").strip().upper()
        if canal not in _CANAIS_CLIENTES_TODOS:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    return {"total": total_clientes_fechados, "por_atendente": por_atendente}

# Retorna a taxa de fechamento geral agrupado por atendente (valores em porcentagem)
def get_taxa_fechamento_geral_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    taxa_geral = get_taxa_leads_geral(actions, comercial_geral)
    leads_por_atendente = get_total_leads_por_atendente(actions)["por_atendente"]
    clientes_por_atendente = get_total_clientes_fechados_por_atendente(comercial_geral)["por_atendente"]
    por_atendente = {}
    for nome in set(leads_por_atendente) | set(clientes_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": taxa_geral, "por_atendente": por_atendente}


# Retorna a taxa de fechamento de campanha (clientes fechados campanha / leads campanha) por atendente (valores em %)
def get_taxa_fechamento_campanha_por_cliente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_campanha_por_atendente(comercial_geral)
    leads_result = get_total_leads_campanha_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}

# Retorna o total de leads de indicação ativa e agrupa por atendente
def get_total_leads_indicacao_ativa_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        propeccao = (action.get("PROSPECCAO") or "").strip().upper()
        if canal != "INDICAÇÃO" or propeccao != "ATIVA":
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total = sum(atendente_counts.values())
    return {"total": total, "por_atendente": dict(atendente_counts)}

def _action_assinado_em_in_range(
    action: Dict[str, Any], from_date: Optional[date], to_date: Optional[date]
) -> bool:
    """Verifica se ASSINADO_EM da action está no intervalo (não usa ENTRADA)."""
    if not from_date and not to_date:
        return True
    assinado_str = action.get("ASSINADO_EM") or action.get("assinado_em")
    if not assinado_str:
        return False
    assinado_date = parse_date_from_db(assinado_str)
    if not assinado_date:
        return False
    if isinstance(assinado_date, datetime):
        assinado_date = assinado_date.date()
    elif not isinstance(assinado_date, date):
        return False
    if from_date and to_date:
        return from_date <= assinado_date <= to_date
    if from_date:
        return assinado_date >= from_date
    if to_date:
        return assinado_date <= to_date
    return True


# Retorna o total de clientes fechados de indicação ativa e agrupa por atendente.
def get_total_clientes_fechados_indicacao_ativa_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    # Da tabela actions: CANAL_ATUAL = INDICAÇÃO, PROPECCAO = ATIVA, MOTIVO_ENCERRAMENTO = 11
    motivo = 11
    ids_indicacao_ativa_fechados = {
        (action.get("ID_ACTION") or action.get("id"))
        for action in actions
        if (action.get("CANAL_ATUAL") or "").strip().upper() == "INDICAÇÃO"
        and (action.get("PROPECCAO") or action.get("PROSPECCAO") or "").strip().upper() == "ATIVA"
        and (action.get("MOTIVO_ENCERRAMENTO") or action.get("motivo_encerramento")) == motivo
        and (action.get("ID_ACTION") or action.get("id")) is not None
        and _action_assinado_em_in_range(action, from_date, to_date)
    }
    # Do comercial_geral só verificamos STATUS <> 2; atendente e ID_ACTION vêm daqui
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("STATUS") == 2:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None or id_action not in ids_indicacao_ativa_fechados:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    total = sum(por_atendente.values())
    return {"total": total, "por_atendente": por_atendente}

# Retorna a taxa de fechamento de indicação ativa por atendente (Clientes fechados indicacao ativa / leads indicacao ativa)
def get_taxa_fechamento_indicacao_ativa_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_indicacao_ativa_por_atendente(comercial_geral, actions)
    leads_result = get_total_leads_indicacao_ativa_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}

# Retorna o total de leads de indicação passiva e agrupa por atendente
def get_total_leads_indicacao_passiva_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        propeccao = (action.get("PROSPECCAO") or "").strip().upper()
        if canal != "INDICAÇÃO" or propeccao != "PASSIVA":
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total = sum(atendente_counts.values())
    return {"total": total, "por_atendente": dict(atendente_counts)}

# Retorna o total de clientes fechados de indicação ativa e agrupa por atendente.
def get_total_clientes_fechados_indicacao_passiva_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    motivo = 11
    ids_indicacao_passiva_fechados = {
        (action.get("ID_ACTION") or action.get("id"))
        for action in actions
        if (action.get("CANAL_ATUAL") or "").strip().upper() == "INDICAÇÃO"
        and (action.get("PROPECCAO") or action.get("PROSPECCAO") or "").strip().upper() == "PASSIVA"
        and (action.get("MOTIVO_ENCERRAMENTO") or action.get("motivo_encerramento")) == motivo
        and (action.get("ID_ACTION") or action.get("id")) is not None
        and _action_assinado_em_in_range(action, from_date, to_date)
    }
    # Do comercial_geral só verificamos STATUS <> 2; atendente e ID_ACTION vêm daqui
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("STATUS") == 2:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None or id_action not in ids_indicacao_passiva_fechados:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    total = sum(por_atendente.values())
    return {"total": total, "por_atendente": por_atendente}

# Retorna a taxa de fechamento de indicação passiva por atendente (Clientes fechados indicacao passiva / leads indicacao passiva)
def get_taxa_fechamento_indicacao_passiva_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_indicacao_passiva_por_atendente(comercial_geral, actions)
    leads_result = get_total_leads_indicacao_passiva_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}

# Retorna o total de leads de Retorno ativa e agrupa por atendente
def get_total_leads_retorno_ativa_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        propeccao = (action.get("PROSPECCAO") or "").strip().upper()
        if canal != "RETORNO" or propeccao != "ATIVA":
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total = sum(atendente_counts.values())
    return {"total": total, "por_atendente": dict(atendente_counts)}

# Retorna Total clientes fechados de Retorno ativa e agrupa por atendente
def get_total_clientes_fechados_retorno_ativa_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    motivo = 11
    ids_retorno_ativa_fechados = {
        (action.get("ID_ACTION") or action.get("id"))
        for action in actions
        if (action.get("CANAL_ATUAL") or "").strip().upper() == "RETORNO"
        and (action.get("PROPECCAO") or action.get("PROSPECCAO") or "").strip().upper() == "ATIVA"
        and (action.get("MOTIVO_ENCERRAMENTO") or action.get("motivo_encerramento")) == motivo
        and (action.get("ID_ACTION") or action.get("id")) is not None
        and _action_assinado_em_in_range(action, from_date, to_date)
    }
    # Do comercial_geral só verificamos STATUS <> 2; atendente e ID_ACTION vêm daqui
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("STATUS") == 2:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None or id_action not in ids_retorno_ativa_fechados:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    total = sum(por_atendente.values())
    return {"total": total, "por_atendente": por_atendente}

# Retorna a taxa de fechamento de retorno ativa por atendente (Clientes fechados retorno ativa / leads retorno ativa)
def get_taxa_fechamento_retorno_ativa_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_retorno_ativa_por_atendente(comercial_geral, actions)
    leads_result = get_total_leads_retorno_ativa_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}

# Retorna o total de leads de Retorno passiva e agrupa por atendente
def get_total_leads_retorno_passiva_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        propeccao = (action.get("PROSPECCAO") or "").strip().upper()
        if canal != "RETORNO" or propeccao != "PASSIVA":
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total = sum(atendente_counts.values())
    return {"total": total, "por_atendente": dict(atendente_counts)}

# Retorna Total clientes fechados de Retorno passiva e agrupa por atendente
def get_total_clientes_fechados_retorno_passiva_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    motivo = 11
    ids_retorno_passiva_fechados = {
        (action.get("ID_ACTION") or action.get("id"))
        for action in actions
        if (action.get("CANAL_ATUAL") or "").strip().upper() == "RETORNO"
        and (action.get("PROPECCAO") or action.get("PROSPECCAO") or "").strip().upper() == "PASSIVA"
        and (action.get("MOTIVO_ENCERRAMENTO") or action.get("motivo_encerramento")) == motivo
        and (action.get("ID_ACTION") or action.get("id")) is not None
        and _action_assinado_em_in_range(action, from_date, to_date)
    }
    # Do comercial_geral só verificamos STATUS <> 2; atendente e ID_ACTION vêm daqui
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("STATUS") == 2:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None or id_action not in ids_retorno_passiva_fechados:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    total = sum(por_atendente.values())
    return {"total": total, "por_atendente": por_atendente}

# Retorna a taxa de fechamento de retorno passiva por atendente (Clientes fechados retorno passiva / leads retorno passiva)
def get_taxa_fechamento_retorno_passiva_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_retorno_passiva_por_atendente(comercial_geral, actions)
    leads_result = get_total_leads_retorno_passiva_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}

# Retorna o total de leads de Resgate ativa e agrupa por atendente
def get_total_leads_resgate_ativa_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        propeccao = (action.get("PROSPECCAO") or "").strip().upper()
        if canal != "RESGATE" or propeccao != "ATIVA":
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total = sum(atendente_counts.values())
    return {"total": total, "por_atendente": dict(atendente_counts)}

# Retorna Total clientes fechados de Resgate ativa e agrupa por atendente
def get_total_clientes_fechados_resgate_ativa_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    motivo = 11
    ids_resgate_ativa_fechados = {
        (action.get("ID_ACTION") or action.get("id"))
        for action in actions
        if (action.get("CANAL_ATUAL") or "").strip().upper() == "RESGATE"
        and (action.get("PROPECCAO") or action.get("PROSPECCAO") or "").strip().upper() == "ATIVA"
        and (action.get("MOTIVO_ENCERRAMENTO") or action.get("motivo_encerramento")) == motivo
        and (action.get("ID_ACTION") or action.get("id")) is not None
        and _action_assinado_em_in_range(action, from_date, to_date)
    }
    # Do comercial_geral só verificamos STATUS <> 2; atendente e ID_ACTION vêm daqui
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("STATUS") == 2:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None or id_action not in ids_resgate_ativa_fechados:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    total = sum(por_atendente.values())
    return {"total": total, "por_atendente": por_atendente}

# Retorna a taxa de fechamento de resgate ativa por atendente (Clientes fechados resgate ativa / leads resgate ativa)
def get_taxa_fechamento_resgate_ativa_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_resgate_ativa_por_atendente(comercial_geral, actions)
    leads_result = get_total_leads_resgate_ativa_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}

# Retorna o total de leads de Resgate passiva e agrupa por atendente
def get_total_leads_resgate_passiva_por_atendente(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    atendente_counts = defaultdict(int)
    for action in actions:
        canal = (action.get("CANAL_ATUAL") or "").strip().upper()
        propeccao = (action.get("PROSPECCAO") or "").strip().upper()
        if canal != "RESGATE" or propeccao != "PASSIVA":
            continue
        atendente = action.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    total = sum(atendente_counts.values())
    return {"total": total, "por_atendente": dict(atendente_counts)}

# Retorna Total clientes fechados de Resgate Passiva e agrupa por atendente
def get_total_clientes_fechados_resgate_passiva_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    motivo = 11
    ids_resgate_passiva_fechados = {
        (action.get("ID_ACTION") or action.get("id"))
        for action in actions
        if (action.get("CANAL_ATUAL") or "").strip().upper() == "RESGATE"
        and (action.get("PROPECCAO") or action.get("PROSPECCAO") or "").strip().upper() == "PASSIVA"
        and (action.get("MOTIVO_ENCERRAMENTO") or action.get("motivo_encerramento")) == motivo
        and (action.get("ID_ACTION") or action.get("id")) is not None
        and _action_assinado_em_in_range(action, from_date, to_date)
    }
    # Do comercial_geral só verificamos STATUS <> 2; atendente e ID_ACTION vêm daqui
    atendente_ids: Dict[str, set] = defaultdict(set)
    for comercial in comercial_geral:
        if comercial.get("STATUS") == 2:
            continue
        id_action = comercial.get("ID_ACTION")
        if id_action is None or id_action not in ids_resgate_passiva_fechados:
            continue
        atendente = comercial.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_ids[atendente_formatado].add(id_action)
    por_atendente = {nome: len(ids) for nome, ids in atendente_ids.items()}
    total = sum(por_atendente.values())
    return {"total": total, "por_atendente": por_atendente}

# Retorna a taxa de fechamento de resgate passiva por atendente (Clientes fechados resgate passiva / leads resgate passiva)
def get_taxa_fechamento_resgate_passiva_por_atendente(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> Dict[str, Any]:
    clientes_result = get_total_clientes_fechados_resgate_passiva_por_atendente(comercial_geral, actions)
    leads_result = get_total_leads_resgate_passiva_por_atendente(actions)
    total_clientes = clientes_result["total"]
    total_leads = leads_result["total"]
    total_taxa = round((total_clientes / total_leads) * 100, 2) if total_leads else 0.0
    clientes_por_atendente = clientes_result["por_atendente"]
    leads_por_atendente = leads_result["por_atendente"]
    por_atendente = {}
    for nome in set(clientes_por_atendente) | set(leads_por_atendente):
        leads = leads_por_atendente.get(nome, 0) or 1
        clientes = clientes_por_atendente.get(nome, 0)
        taxa = (clientes / leads) * 100 if leads else 0.0
        por_atendente[nome] = round(taxa, 2)
    return {"total": total_taxa, "por_atendente": por_atendente}