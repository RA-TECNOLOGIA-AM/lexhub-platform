# Análises e processamento de dados de Tickets

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
from zoneinfo import ZoneInfo

from app.utils import parse_datetime_from_db

# Mapeamento de IDs de servidor para nomes
SERVIDORES_MAP = {
    "1240372949047971983": "NG",
    "1280915379488686141": "LA-AM",
    "1402645041918382090": "LA-RJ"
}

# Retorna tickets com status "reprovado"
def get_tickets_reprovados(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        t for t in tickets
        if t.get("status") and t.get("status", "").lower() == "reprovado"
    ]

# Retorna tickets válidos (excluindo reprovados)
def get_tickets_validos(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        t for t in tickets
        if not t.get("status") or t.get("status", "").lower() != "reprovado"
    ]

# Retorna tickets válidos com status "em atendimento"
def get_tickets_em_atendimento(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tickets_validos = get_tickets_validos(tickets)
    
    return [
        t for t in tickets_validos
        if t.get("status") and t.get("status", "").lower() == "em atendimento"
    ]

# Retorna tickets válidos com status "resolvido"
def get_tickets_resolvidos(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tickets_validos = get_tickets_validos(tickets)
    
    return [
        t for t in tickets_validos
        if t.get("status") and t.get("status", "").lower() == "resolvido"
    ]

# Retorna tickets válidos com status "em análise"
def get_tickets_ag_atendimento(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tickets_validos = get_tickets_validos(tickets)
    
    return [
        t for t in tickets_validos
        if t.get("status") and t.get("status", "").lower() == "em análise"
    ]

# Retorna tickets válidos com status "cancelado"
def get_tickets_cancelados(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tickets_validos = get_tickets_validos(tickets)
    
    return [
        t for t in tickets_validos
        if t.get("status") and t.get("status", "").lower() == "cancelado"
    ]

# Determina o tipo de atividade baseado na mesma lógica das funções auxiliares.
# Retorna: "success" para resolvidos, "pending" para em atendimento/análise, "warning" para outros.
def get_activity_type(ticket: Dict[str, Any]) -> str:
    status = ticket.get("status")
    if not status:
        return "warning"
    
    status_lower = str(status).lower()
    
    # Usa a mesma lógica de get_tickets_validos (exclui reprovados)
    is_valido = status_lower != "reprovado"
    
    if not is_valido:
        return "warning"
    
    # Usa a mesma lógica de get_tickets_resolvidos
    if status_lower == "resolvido":
        return "success"
    
    # Usa a mesma lógica de get_tickets_em_atendimento e get_tickets_ag_atendimento
    if status_lower in ["em atendimento", "em análise"]:
        return "pending"
    
    # Outros status válidos (cancelado, etc) ou desconhecidos
    return "warning"

# Processa tickets e retorna estatísticas
def get_tickets_stats(tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Usar função auxiliar para tickets reprovados
    tickets_reprovados = get_tickets_reprovados(tickets)

    # Usar função auxiliar para tickets válidos
    tickets_validos = get_tickets_validos(tickets)

    # Usar função auxiliar para tickets em atendimento
    tickets_ag_atendimento = get_tickets_ag_atendimento(tickets)

    # Usar função auxiliar para tickets em atendimento
    tickets_atendimento = get_tickets_em_atendimento(tickets)

    # Usar função auxiliar para tickets resolvidos
    total_encerrados = get_tickets_resolvidos(tickets)

    # Usar função auxiliar para tickets resolvidos
    tickets_cancelados = get_tickets_cancelados(tickets)

    # Calcular duração média do atendimento
    # Duração = diferença entre data_criacao e data_ultima_atualizacao
    total_duracao_ms = 0
    tickets_com_duracao = 0

    for ticket in tickets_validos:
        try:
            data_criacao_str = ticket.get("data_criacao")
            data_atualizacao_str = ticket.get("data_ultima_atualizacao") or data_criacao_str

            if not data_criacao_str or not data_atualizacao_str:
                continue

            # Converter strings do banco para datetime
            data_criacao = parse_datetime_from_db(data_criacao_str)
            data_atualizacao = parse_datetime_from_db(data_atualizacao_str)
            
            if not data_criacao or not data_atualizacao:
                continue

            duracao = (data_atualizacao - data_criacao).total_seconds() * 1000  # em milissegundos
            if duracao > 0:
                total_duracao_ms += duracao
                tickets_com_duracao += 1
        except (ValueError, AttributeError, TypeError):
            # Ignora tickets com datas inválidas
            continue

    duracao_media_horas = (
        total_duracao_ms / tickets_com_duracao / (1000 * 60 * 60)
        if tickets_com_duracao > 0
        else 0
    )

    # Calcular taxa de resolução (baseado nos tickets válidos)
    taxa_resolucao = (
        (len(total_encerrados) / len(tickets_validos)) * 100
        if len(tickets_validos) > 0
        else 0
    )

    return {
        "total_tickets": len(tickets_validos),  # Exclui reprovados
        "tickets_ag_atendimento": len(tickets_ag_atendimento),
        "tickets_atendimento": len(tickets_atendimento),
        "total_encerrados": len(total_encerrados),
        "tickets_cancelados": len(tickets_cancelados),
        "tickets_reprovados": len(tickets_reprovados),
        "duracao_atendimento": duracao_media_horas,
        "taxa_resolucao": taxa_resolucao,
    }

# -----------------------------------------------------------------------------
# Drill-down: filtro por seleção
# -----------------------------------------------------------------------------
def apply_ticket_selection_filter(
    tickets: List[Dict[str, Any]],
    selection_dim: Optional[str],
    selection_value: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Filtra a lista de tickets para suportar drill-down no dashboard.

    selection_dim: "categoria" | "sub_categoria" | "status" | "servidor"
    selection_value: valor clicado no gráfico (comparado case-insensitive).
    """
    if not selection_dim or selection_value is None:
        return tickets

    dim = str(selection_dim).strip().lower()
    value_norm = str(selection_value).strip().lower()

    if not dim or value_norm == "":
        return tickets

    # Mapeia a "categoria chave" que aparece nos gráficos.
    def get_ticket_categoria(t: Dict[str, Any]) -> str:
        return str(t.get("categoria") or "Sem categoria")

    def get_ticket_subcategoria(t: Dict[str, Any]) -> str:
        return str(t.get("sub_categoria") or "Sem subcategoria")

    def get_ticket_status(t: Dict[str, Any]) -> str:
        # group_tickets_by_status usa "Sem status" quando status é None/ausente.
        return str(t.get("status") or "Sem status")

    def get_ticket_servidor_nome(t: Dict[str, Any]) -> str:
        servidor_id = t.get("servidor")
        if servidor_id:
            servidor_id = str(servidor_id)
            return str(SERVIDORES_MAP.get(servidor_id, servidor_id))
        return "Sem servidor"

    if dim == "categoria":
        return [t for t in tickets if get_ticket_categoria(t).lower() == value_norm]
    if dim in ("sub_categoria", "subcategoria", "subcategory"):
        return [t for t in tickets if get_ticket_subcategoria(t).lower() == value_norm]
    if dim == "status":
        return [t for t in tickets if get_ticket_status(t).lower() == value_norm]
    if dim in ("servidor", "server"):
        return [t for t in tickets if get_ticket_servidor_nome(t).lower() == value_norm]

    # Dimensão desconhecida: não filtra para não quebrar o dashboard.
    return tickets

# Agrupa tickets por categoria
def group_tickets_by_category(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Usar função auxiliar para tickets válidos (excluindo reprovados)
    tickets_validos = get_tickets_validos(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_validos:
        categoria = ticket.get("categoria") or "Sem categoria"
        grouped[categoria] += 1

    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa tickets por subcategoria
def group_tickets_by_subcategory(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Usar função auxiliar para tickets válidos (excluindo reprovados)
    tickets_validos = get_tickets_validos(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_validos:
        sub_categoria = ticket.get("sub_categoria") or "Sem subcategoria"
        grouped[sub_categoria] += 1

    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa tickets por total de aberturas de tickets por usuário e retorna um ranking ordenado por quantidade de tickets abertos.
def group_tickets_ranking_abertura(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Usar função auxiliar para tickets válidos (excluindo reprovados)
    tickets_validos = get_tickets_validos(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_validos:
        # Tenta primeiro "usuario" (singular), depois "usuarios" (plural)
        usuario = ticket.get("usuario") or ticket.get("usuarios") or "Sem usuário"
        grouped[usuario] += 1

    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    # Retorna ranking ordenado por quantidade (maior para menor)
    return sorted(result, key=lambda y: y["value"], reverse=True)[:5]

def group_tickets_ranking_fechados(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa tickets encerrados (status "resolvido") por quem encerrou (atualizado_por).
    Retorna um ranking ordenado por quantidade de tickets fechados.
    """
    # Usar a função auxiliar para filtrar apenas tickets resolvidos
    tickets_encerrados = get_tickets_resolvidos(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_encerrados:
        # Pega o campo atualizado_por que indica quem encerrou o ticket
        atualizado_por = ticket.get("atualizado_por") or "Sem funcionário"
        grouped[atualizado_por] += 1

    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    # Retorna ranking ordenado por quantidade (maior para menor)
    return sorted(result, key=lambda y: y["value"], reverse=True)[:5]

def group_tickets_media_encerrados_por_colaborador(
    tickets: List[Dict[str, Any]], 
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Calcula a média de tickets encerrados por colaborador.
    A média é calculada considerando apenas os dias em que houve movimentação (data_ultima_atualizacao)
    dentro do período selecionado.
    
    Lógica: MEDIA = TOTAL_ENCERRADOS / DIAS_UTEIS
    onde DIAS_UTEIS = quantidade de dias distintos com atualização dentro do período
    
    Args:
        tickets: Lista de tickets
        from_date: Data inicial do período (opcional)
        to_date: Data final do período (opcional)
    
    Retorna um ranking ordenado por média (maior para menor).
    """
    # Usar a função auxiliar para filtrar apenas tickets resolvidos
    tickets_encerrados = get_tickets_resolvidos(tickets)
    
    # Estrutura: {colaborador: {"total": int, "dias": set}}
    colaborador_stats = defaultdict(lambda: {"total": 0, "dias": set()})
    
    for ticket in tickets_encerrados:
        atualizado_por = ticket.get("atualizado_por") or "Sem funcionário"
        data_atualizacao = ticket.get("data_ultima_atualizacao") or ticket.get("data_criacao")
        
        # Incrementa total de tickets
        colaborador_stats[atualizado_por]["total"] += 1
        
        # Extrai apenas a data (sem hora) para contar dias distintos
        if data_atualizacao:
            try:
                date_obj = parse_datetime_from_db(data_atualizacao)
                if not date_obj:
                    continue
                
                # Usa apenas a data (sem hora) como chave
                data_key = date_obj.date()
                
                # Verifica se a data está dentro do período filtrado
                if from_date or to_date:
                    # Se há filtro de período, verifica se a data está dentro do intervalo
                    if from_date and to_date:
                        if from_date <= data_key <= to_date:
                            colaborador_stats[atualizado_por]["dias"].add(data_key)
                    elif from_date:
                        if data_key >= from_date:
                            colaborador_stats[atualizado_por]["dias"].add(data_key)
                    elif to_date:
                        if data_key <= to_date:
                            colaborador_stats[atualizado_por]["dias"].add(data_key)
                else:
                    # Se não há filtro, conta todos os dias
                    colaborador_stats[atualizado_por]["dias"].add(data_key)
            except (ValueError, AttributeError, TypeError):
                # Se não conseguir parsear a data, ignora esse ticket para contagem de dias
                pass
    
    # Calcula média para cada colaborador
    result = []
    for colaborador, stats in colaborador_stats.items():
        total_encerrados = stats["total"]
        dias_uteis = len(stats["dias"])
        
        # Calcula média: divide total por dias úteis
        # Se não houver dias úteis, retorna None (equivalente a BLANK() no Power BI)
        if dias_uteis > 0:
            media = total_encerrados / dias_uteis
            result.append({
                "name": colaborador,
                "value": round(media, 2)  # Arredonda para 2 casas decimais
            })
        # Se dias_uteis == 0, não adiciona ao resultado (equivalente a BLANK)
    
    # Retorna ranking ordenado por média (maior para menor)
    return sorted(result, key=lambda x: x["value"], reverse=True)

def group_tickets_abertos_por_servidor(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa tickets em aberto (status "em atendimento") por servidor.
    Retorna um ranking ordenado por quantidade de tickets.
    """
    # Usar a lógica já existente para filtrar tickets em atendimento
    tickets_abertos = get_tickets_em_atendimento(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_abertos:
        servidor_id = ticket.get("servidor")
        if servidor_id:
            # Converter para string caso seja número
            servidor_id = str(servidor_id)
            # Usar o nome do servidor se existir no mapeamento, senão usa o ID
            servidor_nome = SERVIDORES_MAP.get(servidor_id, servidor_id)
            grouped[servidor_nome] += 1
        else:
            # Incluir tickets sem servidor na categoria "Sem servidor"
            grouped["Sem servidor"] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    # Retorna ranking ordenado por quantidade (maior para menor)
    return sorted(result, key=lambda x: x["value"], reverse=True)

def group_tickets_encerrados_por_servidor(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa tickets encerrados (status "resolvido") por servidor.
    Retorna um ranking ordenado por quantidade de tickets.
    """
    # Usar a função auxiliar para filtrar tickets resolvidos
    tickets_encerrados = get_tickets_resolvidos(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_encerrados:
        servidor_id = ticket.get("servidor")
        if servidor_id:
            # Converter para string caso seja número
            servidor_id = str(servidor_id)
            # Usar o nome do servidor se existir no mapeamento, senão usa o ID
            servidor_nome = SERVIDORES_MAP.get(servidor_id, servidor_id)
            grouped[servidor_nome] += 1
        else:
            # Incluir tickets sem servidor na categoria "Sem servidor"
            grouped["Sem servidor"] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    # Retorna ranking ordenado por quantidade (maior para menor)
    return sorted(result, key=lambda x: x["value"], reverse=True)

def group_tickets_by_month(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa tickets por mês (apenas tickets válidos, excluindo reprovados)
    """
    # Usar função auxiliar para tickets válidos
    tickets_validos = get_tickets_validos(tickets)
    
    grouped = {}

    for ticket in tickets_validos:
        try:
            data_criacao_str = ticket.get("data_criacao")
            if not data_criacao_str:
                continue

            # Tentar diferentes formatos de data
            date_obj = parse_datetime_from_db(data_criacao_str)
            if not date_obj:
                continue

            month_key = f"{date_obj.year}-{date_obj.month:02d}"

            # Formatar nome do mês em português
            month_names = [
                "jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"
            ]
            month_name = f"{month_names[date_obj.month - 1]} {date_obj.year}"

            if month_key not in grouped:
                grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
            grouped[month_key]["value"] += 1
        except (ValueError, AttributeError, TypeError):
            # Ignora tickets com data inválida
            continue

    result = [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]
    return result

def group_tickets_by_status(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa tickets por status (apenas tickets válidos, excluindo reprovados)
    """
    # Usar função auxiliar para tickets válidos (excluindo reprovados)
    tickets_validos = get_tickets_validos(tickets)
    
    grouped = defaultdict(int)
    for ticket in tickets_validos:
        status = ticket.get("status") or "Sem status"
        grouped[status] += 1

    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Os timestamps de Log_tickets_discord são gravados sem fuso, no horário de Brasília
# (conferido em 13/11/2026: max(data_ultima_atualizacao)=10:49 com now()=13:51 UTC).
_FUSO_TICKETS = ZoneInfo("America/Sao_Paulo")

# Campos que o bot do Discord anexa no fim da descrição: ", AnyDesk: 123", ", ID: 1195", ", Url: https://..."
_RE_CAMPO_DESCRICAO = re.compile(r",\s*(AnyDesk|ID|Url)\s*:\s*", re.IGNORECASE)
_VALORES_VAZIOS = {"", "0", "não informado", "nao informado", "-", "none", "null"}


def parse_descricao_ticket(descricao: Optional[str]) -> Dict[str, Optional[str]]:
    """Separa o texto livre dos campos estruturados que o bot grava na descrição.

    Retorna {"texto", "anydesk", "ticket_numero", "url"} — campos ausentes ou
    "Não informado" viram None.
    """
    bruto = (descricao or "").strip()
    bruto = re.sub(r"^descri[çc][ãa]o\s*:\s*", "", bruto, flags=re.IGNORECASE)
    partes = _RE_CAMPO_DESCRICAO.split(bruto)
    texto = partes[0].strip()
    campos: Dict[str, Optional[str]] = {"anydesk": None, "id": None, "url": None}
    for i in range(1, len(partes) - 1, 2):
        chave = partes[i].lower()
        valor = partes[i + 1].strip().rstrip(",").strip()
        if valor.lower() in _VALORES_VAZIOS:
            continue
        campos[chave] = valor

    numero = None
    if campos["id"]:
        m = re.search(r"\d+", campos["id"])
        numero = m.group(0) if m else None
    url = campos["url"] if campos["url"] and campos["url"].lower().startswith("http") else None
    if not url:
        # Link colado no meio do texto, sem o rótulo "Url:"
        m_url = re.search(r"https?://\S+", texto)
        url = m_url.group(0).rstrip(".,;)") if m_url else None
    anydesk = re.sub(r"\s+", "", campos["anydesk"]) if campos["anydesk"] else None
    if anydesk and not re.fullmatch(r"\d{6,}", anydesk):
        anydesk = None

    if texto and texto[-1] not in ".!?":
        texto += "."
    return {"texto": texto or "Sem descrição", "anydesk": anydesk, "ticket_numero": numero, "url": url}


def _tempo_relativo(minutos: int) -> str:
    if minutos < 1:
        return "agora"
    if minutos < 60:
        return f"há {minutos} min"
    horas = minutos // 60
    if horas < 24:
        return f"há {horas} h"
    dias = horas // 24
    return f"há {dias} dia{'s' if dias > 1 else ''}"


def tickets_to_activities(tickets: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
    """Converte tickets nas movimentações recentes (mais recente primeiro)."""
    agora = datetime.now(_FUSO_TICKETS).replace(tzinfo=None)

    def get_update_time(ticket: Dict[str, Any]) -> Optional[datetime]:
        update_str = ticket.get("data_ultima_atualizacao") or ticket.get("data_criacao")
        if not update_str:
            return None
        try:
            parsed = parse_datetime_from_db(update_str)
            return parsed.replace(tzinfo=None) if parsed else None
        except (ValueError, AttributeError, TypeError):
            return None

    sorted_tickets = sorted(
        tickets,
        key=lambda t: get_update_time(t) or datetime.min,
        reverse=True,
    )[:limit]

    activities = []
    for ticket in sorted_tickets:
        try:
            update_date = get_update_time(ticket)
            minutos = max(int((agora - update_date).total_seconds() // 60), 0) if update_date else None
            info = parse_descricao_ticket(ticket.get("descricao"))
            servidor_id = str(ticket.get("servidor") or "")
            activities.append({
                "id": ticket.get("id_unico") or str(ticket.get("id", "")),
                "type": get_activity_type(ticket),
                "title": ticket.get("categoria") or "Ticket",
                "description": info["texto"],
                "time": _tempo_relativo(minutos) if minutos is not None else "",
                "user": ticket.get("usuario") or "Sistema",
                "categoria": ticket.get("categoria") or None,
                "status": ticket.get("status") or None,
                "servidor": SERVIDORES_MAP.get(servidor_id) if servidor_id else None,
                "ticket_numero": info["ticket_numero"],
                "anydesk": info["anydesk"],
                "url": info["url"],
                "minutos_atras": minutos,
            })
        except Exception:
            # Ignora tickets com problemas
            continue

    return activities


def contar_tickets_validos_no_periodo(
    tickets: List[Dict[str, Any]], inicio: date, fim: date
) -> int:
    """Tickets válidos (não reprovados) criados entre `inicio` e `fim` (inclusive)."""
    total = 0
    for ticket in get_tickets_validos(tickets):
        criado = parse_datetime_from_db(ticket.get("data_criacao"))
        if criado and inicio <= criado.date() <= fim:
            total += 1
    return total
