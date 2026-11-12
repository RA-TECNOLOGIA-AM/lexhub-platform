# Funções de analises do setor de peticionamento

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from collections import defaultdict
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, parse_datetime_from_db, resolver_periodo_comparativo
from app.analyses.LA.comercial_LA import _formatar_nome_atendente

# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Função auxiliar que retorna a lista de não peticionados.
def _filtrar_nao_peticionados(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PETICIONAMENTO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar para filtrar a quantidade de peticionados.
def _filtrar_total_peticionados(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLO", "CONCLUIDO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Confeccionados manualmente
def _filtrar_total_peticionados_manualmente(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLO", "CONCLUIDO"]
        and (
            str(p.get("PET_AUTO", "")).upper() == "FALSE" or
            p.get("PET_AUTO") is False
        )
    ]

# Confeccionados Automaticamente
def _filtrar_total_peticionados_automaticamente(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLO", "CONCLUIDO"]
        and (
            str(p.get("PET_AUTO", "")).upper() == "TRUE" or
            p.get("PET_AUTO") is True
        )
    ]

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

# Função para filtrar os dados e crealizar as analises de comparativos entre o periodo atual e o periodo anterior de qualquer outra analise.
def _filter_by_date_range(peticionados: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados de protocolos por intervalo de datas usando a coluna DATA_CRIACAO."""
    filtered = []
    for p in peticionados:
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

# Formata o nome do funcionário.
def _formatar_nome_funcionario(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome da funcionario."""
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo

    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0].upper()
    return " ".join(partes[:2]).upper()


def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - ' (ex: 'BX_ANT_FIN - BANCO BRADESCO' -> 'BX_ANT_FIN')."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"


def filter_peticionamento_LA_por_materia(
    peticionados: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_LA_por_materia` em ``org_doc_LA``
    (:func:`_normalizar_materia`).
    """
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(peticionados)
    return [p for p in peticionados if _normalizar_materia(p.get("MATERIA")) in alvos]


def filter_peticionamento_LA_por_funcionario(
    peticionados: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_LA_por_funcionario` em ``org_doc_LA``
    (:func:`_formatar_nome_funcionario` deste módulo).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(peticionados)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in peticionados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_peticionamento_LA_por_funcionarios(
    peticionados: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários LA (união — OR)."""
    if not funcionarios:
        return list(peticionados)
    alvos = {
        _formatar_nome_funcionario(str(f).strip())
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(peticionados)
    return [
        p for p in peticionados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) in alvos
    ]


def _normalizar_uf_peticionamento_LA(raw: Any) -> str:
    """Normaliza a UF vinda do banco ou da query para comparação."""
    return str(raw or "").strip().upper()


def list_ufs_peticionamento_LA(peticionados: List[Dict[str, Any]]) -> List[str]:
    """Lista única de UFs disponíveis no recorte atual de peticionamento LA."""
    vistos: set[str] = set()
    saida: List[str] = []
    for row in peticionados or []:
        uf = _normalizar_uf_peticionamento_LA(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_peticionamento_LA_por_uf(
    peticionados: List[Dict[str, Any]],
    uf: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Restringe peticionamento LA aos registros de uma UF."""
    if uf is None or not str(uf).strip():
        return list(peticionados)
    alvo = _normalizar_uf_peticionamento_LA(uf)
    return [
        p for p in peticionados
        if _normalizar_uf_peticionamento_LA(p.get("UF") or p.get("uf")) == alvo
    ]


# -----------------------------------------------------------------------------
# 2 - Funções de Peticionamento
# -----------------------------------------------------------------------------

# Retorna a quantidades de processos Confeccionados
def get_total_confeccionados_LA (peticionados: List[Dict[str, Any]]) -> int:
    return len (_filtrar_total_peticionados(peticionados))

# Retorna a quantidades de processos Não Confeccionados
def get_nao_confeccionados_LA (peticionados: List[Dict[str, Any]]) -> int:
    return len (_filtrar_nao_peticionados(peticionados))

# Retorna a soma de confeccionados e não confeccionados (base para taxas).
# Se all_peticionados for informado, usa-o para contar não confeccionados (ex.: dashboard com período filtrado).
def get_total_peticionamento_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
) -> int:
    nao_src = all_peticionados if all_peticionados is not None else peticionados
    return get_total_confeccionados_LA(peticionados) + get_nao_confeccionados_LA(nao_src)

# Retorna a taxa de resolvidos (confeccionados / total) em percentual.
def get_peticionamento_taxa_resolvidos_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
) -> Optional[float]:
    total = get_total_peticionamento_LA(peticionados, all_peticionados)
    if total == 0:
        return None
    return round((get_total_confeccionados_LA(peticionados) / total) * 100, 2)

# Retorna a taxa de não resolvidos (não confeccionados / total) em percentual.
def get_peticionamento_taxa_nao_resolvidos_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
) -> Optional[float]:
    nao_src = all_peticionados if all_peticionados is not None else peticionados
    total = get_total_peticionamento_LA(peticionados, all_peticionados)
    if total == 0:
        return None
    return round((get_nao_confeccionados_LA(nao_src) / total) * 100, 2)


def _dt_log_fase_entrada(p: Dict[str, Any], col_upper: str) -> Optional[datetime]:
    """Lê timestamp da CTE log_fase (colunas DATA_* da query setor_confeccao_LA)."""
    raw = p.get(col_upper)
    if raw is None:
        raw = p.get(col_upper.lower())
    if raw is None:
        return None
    return parse_datetime_from_db(raw)


def _peticionados_unicos_por_processo(
    peticionados: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Uma linha por PROCESSO_ID para não duplicar contagens com vários registros em peticionamento."""
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for p in peticionados:
        pid = p.get("PROCESSO_ID")
        if pid is None:
            pid = p.get("processo_id")
        if pid is None:
            continue
        if pid in seen:
            continue
        seen.add(pid)
        out.append(p)
    return out


def _processo_retornou_protocolo_para_peticionamento(p: Dict[str, Any]) -> bool:
    """
    Retorno protocolo → peticionamento: última entrada em peticionamento (log subfase 5, ação 1)
    é posterior à entrada em protocolo (subfase 6, ação 1), conforme agregação MAX na query.
    """
    dt_pet = _dt_log_fase_entrada(p, "DATA_ENTRADA_PET")
    dt_proto = _dt_log_fase_entrada(p, "DATA_ENTRADA_PROTOCOLO")
    if dt_pet is None or dt_proto is None:
        return False
    return dt_pet > dt_proto


def get_peticionamento_qtd_entrada_protocolo_LA(
    peticionados: List[Dict[str, Any]],
) -> int:
    """Processos (únicos) com registro de entrada em protocolo em log_fase."""
    return sum(
        1
        for p in _peticionados_unicos_por_processo(peticionados)
        if _dt_log_fase_entrada(p, "DATA_ENTRADA_PROTOCOLO") is not None
    )


def get_peticionamento_qtd_retorno_protocolo_LA(
    peticionados: List[Dict[str, Any]],
) -> int:
    """Processos (únicos) que voltaram ao peticionamento após terem entrado em protocolo."""
    return sum(
        1
        for p in _peticionados_unicos_por_processo(peticionados)
        if _processo_retornou_protocolo_para_peticionamento(p)
    )


def get_peticionamento_taxa_retorno_protocolo_LA(
    peticionados: List[Dict[str, Any]],
) -> Optional[float]:
    """
    Taxa de retorno (percentual): retornos / processos que chegaram ao protocolo.
    None se não houver nenhum processo com entrada em protocolo na base filtrada.
    """
    base = get_peticionamento_qtd_entrada_protocolo_LA(peticionados)
    if base == 0:
        return None
    ret = get_peticionamento_qtd_retorno_protocolo_LA(peticionados)
    return round((ret / base) * 100, 2)

# Retorna a quantidades de processos Confeccionados Manualmente.
def get_total_confeccionados_manualmente_LA (peticionados: List[Dict[str, Any]]) -> int:
    return len (_filtrar_total_peticionados_manualmente(peticionados))

# Retorna a quantidades de processos Confeccionados Automaticamente.
def get_total_confeccionados_automaticamente_LA (peticionados: List[Dict[str, Any]]) -> int:
    return len (_filtrar_total_peticionados_automaticamente(peticionados))

# Retorna a soma do valor da causa para confeccionados.
def get_valor_causa_confeccionado_LA(peticionados: List[Dict[str, Any]]) -> float:
    total = 0.0
    for p in peticionados:
        # Verifica se atende aos critérios
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLO", "CONCLUIDO"]

        if status_ok:
            materia = str(p.get("MATERIA") or "").strip().upper()
            # Para matéria ANP, soma o valor da coluna DANO_MORAL; demais matérias usam valor da causa
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
    
    return round(total, 2)

# Retorna o ticket medio de confeccionados.
def get_ticket_medio_confeccionados_LA(peticionados: List[Dict[str, Any]]) -> float:
    qtd = get_total_confeccionados_LA(peticionados)
    if qtd == 0:
        return 0.0
    valor = get_valor_causa_confeccionado_LA(peticionados) / qtd
    return round(valor, 2)

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]
_SEM_DATA_KEY = "_sem_data"
_SEM_DATA_ENTRY = {"name": "Sem data", "value": 0}
_SEM_DATA_SORT = "9999-99"

# Agrupados processos confeccionados por mês
def group_confeccionados_por_mes_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos Protocolados por Mês."""
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
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

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]

    # Agrupados processos não protocolados por mês

# Agrupados processos não confeccionados por mês
def group_nao_confeccionados_por_mes_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não protocolados por Mês."""
    protocolos_agrupados = _filtrar_nao_peticionados(peticionados)
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
# 3 - Agrupados por funcionários
# -----------------------------------------------------------------------------

# agrupa processos resolvidos por funcionario
def group_confeccionados_por_funcionario_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Funcionario."""
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# agrupa processos não resolvidos por funcionario
def group_nao_confeccionados_por_funcionario_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Funcionario."""
    protocolos_agrupados = _filtrar_nao_peticionados(peticionados)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos peticionados por dia.
def group_confeccionados_por_dia_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    peticionados_agrupados = _filtrar_total_peticionados(peticionados)
    grouped = defaultdict(int)
    for p in peticionados_agrupados:
        dia = p.get("SAIDA") or p.get("saida")
        if not dia:
            continue
        dt = parse_date_from_db(dia)
        if  dt:
            dia_key = dt.strftime("%Y-%m-%d")
            grouped[dia_key] += 1
    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": count} for dia, count in sorted_items]

# Retorna processos peticionados por dia por funcionário.
def get_confeccionados_por_dia_por_funcionario_LA(peticionados: List[Dict[str, Any]]) -> Dict[str, Any]:
    peticionados_agrupados = _filtrar_total_peticionados(peticionados)
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in peticionados_agrupados:
        dia = p.get("SAIDA") or p.get("saida")
        if not dia:
            continue
        dt = parse_date_from_db(dia)
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

# Retorna a soma do valor de causa para protocolos por funcionário.
def get_valor_causa_confeccionado_por_funcionario_LA(peticionados: List[Dict[str, Any]]) -> Dict[str, float]:
    funcionario_values = defaultdict(float)
    for p in peticionados:
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLO","CONCLUIDO"]
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


# -----------------------------------------------------------------------------
# Comissionamento (apenas confecções manuais)
# -----------------------------------------------------------------------------

def _materia_e_especifica_pet_LA(materia_raw: Any) -> bool:
    s = str(materia_raw or "").strip().upper()
    if not s:
        return False
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s == "ESPECIFICA"


# id de "ADMINISTRATIVO" em juridico.area_atuacao (mesmo id usado no NG).
_AREA_ATUACAO_ADMINISTRATIVO_ID = 2

# Rubricas que, só na LA, usam a tabela de comissão da ESPECIFICA mesmo sem
# pertencer à matéria ESPECIFICA nem à área ADMINISTRATIVO.
_MATERIAS_TABELA_ESPECIFICA_EXTRA_LA = {"JUROS_ABUSIVOS"}


# True quando a peça deve usar a tabela de comissão da ESPECIFICA (R$7/13/20):
# matéria ESPECIFICA, rubrica cuja área de atuação é ADMINISTRATIVO (ex.: ESPECIFICA ADM,
# progressões e gratificações de servidor público) — mesma lógica em todos os escritórios —
# ou JUROS_ABUSIVOS, que segue essa tabela só na LA.
def _elegivel_tabela_especifica_pet_LA(p: Dict[str, Any]) -> bool:
    materia = str(p.get("MATERIA") or "").strip().upper().replace(" ", "_")
    if _materia_e_especifica_pet_LA(p.get("MATERIA")):
        return True
    if materia in _MATERIAS_TABELA_ESPECIFICA_EXTRA_LA:
        return True
    area_id = p.get("AREA_ATUACAO_ID")
    if area_id is not None:
        try:
            if int(area_id) == _AREA_ATUACAO_ADMINISTRATIVO_ID:
                return True
        except (TypeError, ValueError):
            pass
    return str(p.get("AREA_ATUACAO") or "").strip().upper() == "ADMINISTRATIVO"


def _filtrar_peticionados_por_funcionario_nome_LA(
    peticionados: List[Dict[str, Any]],
    nome_funcionario: str,
) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário") == nome_funcionario
    ]


def _preco_unitario_massa_pet_LA(taxa: Optional[float]) -> Decimal:
    if taxa is None:
        return Decimal("0")
    if taxa >= 98:
        return Decimal("3.00")
    if taxa >= 85:
        return Decimal("1.50")
    if taxa >= 70:
        return Decimal("0.50")
    return Decimal("0")


def _preco_unitario_especifica_pet_LA(taxa: Optional[float]) -> Decimal:
    if taxa is None:
        return Decimal("0")
    if taxa >= 95:
        return Decimal("20.00")
    if taxa >= 85:
        return Decimal("13.00")
    if taxa >= 50:
        return Decimal("7.00")
    return Decimal("0")


def get_peticionamento_comissionamento_por_funcionario_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    peticionados_taxa: Optional[List[Dict[str, Any]]] = None,
    all_peticionados_taxa: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Comissão só sobre confecções manuais (PET_AUTO falso).

    Regras de faixa e taxa: iguais ao NG, usando `get_peticionamento_taxa_resolvidos_LA` por funcionário.

    A taxa usada para definir a faixa de comissão é sempre a taxa GERAL do funcionário
    (todas as matérias), não a taxa recortada pela matéria filtrada no dashboard —
    por isso `peticionados_taxa`/`all_peticionados_taxa` (sem filtro de matéria) são
    aceitos separadamente de `peticionados`/`all_peticionados` (usados só para contar
    as quantidades de Massa/ESPECIFICA exibidas). Quando não informados, cai no
    comportamento anterior (recorte igual ao de contagem).
    """
    manual = _filtrar_total_peticionados_manualmente(peticionados)
    all_src = all_peticionados if all_peticionados is not None else peticionados
    taxa_src = peticionados_taxa if peticionados_taxa is not None else peticionados
    all_taxa_src = all_peticionados_taxa if all_peticionados_taxa is not None else all_src

    contagem: Dict[str, Dict[str, int]] = defaultdict(lambda: {"massa": 0, "especifica": 0})
    for p in manual:
        nome = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        if _elegivel_tabela_especifica_pet_LA(p):
            contagem[nome]["especifica"] += 1
        else:
            contagem[nome]["massa"] += 1

    linhas: List[Dict[str, Any]] = []
    for nome in sorted(contagem.keys()):
        massa = contagem[nome]["massa"]
        especifica = contagem[nome]["especifica"]
        if massa == 0 and especifica == 0:
            continue

        pet_f = _filtrar_peticionados_por_funcionario_nome_LA(taxa_src, nome)
        all_f = _filtrar_peticionados_por_funcionario_nome_LA(all_taxa_src, nome)
        taxa = get_peticionamento_taxa_resolvidos_LA(pet_f, all_f)

        pm = _preco_unitario_massa_pet_LA(taxa)
        pe = _preco_unitario_especifica_pet_LA(taxa)
        sub_m = (Decimal(massa) * pm).quantize(Decimal("0.01"))
        sub_e = (Decimal(especifica) * pe).quantize(Decimal("0.01"))
        total = (sub_m + sub_e).quantize(Decimal("0.01"))

        linhas.append({
            "funcionario": nome,
            "qtd_acoes_massa": massa,
            "valor_acoes_massa": float(pm),
            "qtd_x_valor_massa": float(sub_m),
            "qtd_acoes_especificas": especifica,
            "valor_acoes_especificas": float(pe),
            "qtd_x_valor_especificas": float(sub_e),
            "taxa_resolvidos": taxa,
            "valor_comissao": float(total),
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# Retorna a média de processos resolvidos por funcionário.
def get_media_confeccionado_por_funcionario_LA(
    peticionados: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Média de processos protocolados por FUNCIONARIO."""
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
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

# -----------------------------------------------------------------------------
# 4 - Funções do Comercial
# -----------------------------------------------------------------------------

# Retorna a quatntidade total de peticionados por atendente.
def get_total_peticionados_por_atendente_LA(peticionados: List[Dict[str, Any]]) -> Dict[str, int]:
    peticionados = _filtrar_total_peticionados(peticionados)
    atendente_counts = defaultdict(int)
    for p in peticionados:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# Retorna a quantidade de não peticionados por atendente.
def get_nao_peticionados_por_atendente_LA(peticionados: List[Dict[str, Any]]) -> Dict[str, int]:
    nao_peticionados = _filtrar_nao_peticionados(peticionados)
    atendente_counts = defaultdict(int)
    for p in nao_peticionados:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# -----------------------------------------------------------------------------
# 4 - Agrupados por matéria
# -----------------------------------------------------------------------------

# Agrupa os processos confeccionados por matéria.
def group_confeccionados_por_materia_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agrupados = _filtrar_total_peticionados(peticionados)
    # print(f"[DEBUG] group_protocolados_por_materia_LA — total filtrados: {len(agrupados)}")
    group = defaultdict(int)
    for p in agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        group[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in group.items()
    ]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print(f"[DEBUG] group_protocolados_por_materia_LA — resultado ({len(result)} itens): {result[:5]}")
    return result

# Agrupa os processos NÃO confeccionados por matéria.
def group_nao_confeccionados_por_materia_LA(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agrupados = _filtrar_nao_peticionados(peticionados)
    # print(f"[DEBUG] group_represados_por_materia_LA — total filtrados: {len(agrupados)}")
    group = defaultdict(int)
    for p in agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        group[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in group.items()
    ]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print(f"[DEBUG] group_represados_por_materia_LA — resultado ({len(result)} itens): {result[:5]}")
    return result

# -----------------------------------------------------------------------------
# 5 - Tempo de Produção
# -----------------------------------------------------------------------------

# Função auxiliar para extrair os dias
def _extrair_duracoes_dias(peticionados: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
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

# Retorna o tempo médio (em dias) para o processo confeccionado no setor, de forma geral.
def get_media_tempo_confeccionado_LA(peticionados: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(peticionados)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) para o processo confeccionado no setor, de forma geral.
def get_mediana_tempo_confeccionado_LA(peticionados: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(peticionados)

    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)

# -----------------------------------------------------------------------------
# 6 - Comparativo de Tempo
# -----------------------------------------------------------------------------

# Retorna a variação percentual de confeccionados.
def get_comparativo_confeccionados_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_total_confeccionados_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_total_confeccionados_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

    # Retorna a variação percentual de confeccionados.

# Retorna a variação percentual de confeccionados automaticamente.
def get_comparativo_confeccionados_automaticamente_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_total_confeccionados_automaticamente_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_total_confeccionados_automaticamente_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de confeccionados manualmente.
def get_comparativo_confeccionados_manualmente_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_total_confeccionados_manualmente_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_total_confeccionados_manualmente_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de valor de causa.
def get_comparativo_valor_causa_confeccionado_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_valor_causa_confeccionado_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_valor_causa_confeccionado_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de ticket médio.
def get_comparativo_ticket_medio_confeccionado_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_ticket_medio_confeccionados_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_ticket_medio_confeccionados_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de tempo médio.
def get_comparativo_tempo_medio_confeccionado_LA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_media_tempo_confeccionado_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_media_tempo_confeccionado_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de mediana de tempo.
def get_comparativo_mediana_tempo_confeccionadoLA(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    confeccionados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    confeccionados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de protocolos resolvidos em cada período
    dados_periodo_atual = get_mediana_tempo_confeccionado_LA(confeccionados_periodo_atual)
    dados_periodo_anterior = get_mediana_tempo_confeccionado_LA(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)