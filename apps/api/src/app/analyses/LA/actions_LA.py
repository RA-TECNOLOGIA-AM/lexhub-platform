# Análises e processamento de dados de ACTIONS LA

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
import statistics
from app.utils import parse_date_from_db
from app.analyses.LA.comercial_LA import get_clientes_todos_LA, get_clientes_campanha, _filter_by_date_range as filter_comercial_by_date_range, _formatar_nome_atendente

# Retorna o total de Leads
def get_total_leads_LA(actions: List[Dict[str, Any]]) -> int:
    return len(actions)


# Retorna o total de Leads de Anúncio (LA)
def get_total_leads_anuncio_LA(actions: List[Dict[str, Any]]) -> int:
    filtered = [
        action for action in actions
        if action.get("CANAL_AQUISICAO")
        and str(action.get("CANAL_AQUISICAO", "")).strip().upper() == "ANUNCIO"
    ]
    return len(filtered)


# Retorna a taxa de Leads Geral (LA)
def get_taxa_leads_geral_LA(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> float:
    total_leads = get_total_leads_LA(actions)
    clientes_todos = get_clientes_todos_LA(comercial_geral)

    if total_leads == 0:
        return 0.0

    if clientes_todos == 0:
        return 0.0

    taxa = (clientes_todos / total_leads) * 100
    resultado = round(taxa, 2)
    return resultado


# Retorna a taxa de Leads de Anúncio (LA)
def get_taxa_leads_anuncio_LA(actions: List[Dict[str, Any]], comercial_geral: List[Dict[str, Any]]) -> float:
    total_leads_anuncio = get_total_leads_anuncio_LA(actions)
    clientes_campanha = get_clientes_campanha(comercial_geral)

    if total_leads_anuncio == 0:
        return 0.0

    if clientes_campanha == 0:
        return 0.0

    taxa = (clientes_campanha / total_leads_anuncio) * 100
    resultado = round(taxa, 2)
    return resultado