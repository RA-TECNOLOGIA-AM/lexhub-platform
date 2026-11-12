# Funções de analises do setor de peticionamento

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from collections import defaultdict
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.NG.comercial_geral import _formatar_nome_atendente

# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Função auxiliar que retorna a lista de não peticionados
def _filtrar_nao_peticionados(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["NÃO INICIADO", "RETORNO PENDÊNCIA"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função que retorna o total de peticionados.
def _filtrar_total_peticionados(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLAR"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função que retorna o total em Revisão.
def _filtrar_total_revisao(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["REVISÃO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar que retorna a lista de peticionados automaticamente.
def _filtrar_peticionados_automaticamente(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtrados = [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLAR"]
        and p.get("PET_AUTO") and str(p.get("PET_AUTO", "")).upper() == "TRUE"
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]
    # print(f"Processos com PET_AUTO = TRUE: {len(filtrados)}")
    return filtrados

# Função auxiliar que retorna a lista de peticionados manualmente.
def _filtrar_peticionados_manualmente(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _eh_manual(p: Dict[str, Any]) -> bool:
        val = p.get("PET_AUTO")
        return val is False or val == 0 or str(val or "").upper() == "FALSE"

    filtrados = [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLAR"]
        and _eh_manual(p)
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]
    # print(f"Processos com PET_AUTO = FALSE: {len(filtrados)}")
    return filtrados

# Função auxiliar que retorna os resolvidos reajuizamentos.
def _filtrar_resolvidos_reajuizamento(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLAR", "REVISÃO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "TRUE" or
            p.get("REAJUIZAMENTO") is True
        )
    ]

# Função auxiliar que retorna os não resolvidos reajuizamentos.
def _filtrar_nao_resolvidos_reajuizamento(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["NÃO INICIADO", "REVISÃO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função para converter o valor de causa para float.
def _converter_valor_causa(valor_causa: Any) -> float:
    """
    Converte o valor da causa para float, tratando diferentes tipos de entrada.
    Suporta: Decimal, int, float, string formatada, None.
    """
    if valor_causa is None:
        return 0.0
    try:
        if isinstance(valor_causa, Decimal):
            return float(valor_causa)
        elif isinstance(valor_causa, (int, float)):
            return float(valor_causa)
        elif isinstance(valor_causa, str):
            valor_limpo = valor_causa.strip().replace(",", ".")
            valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')
            if valor_limpo:
                return float(valor_limpo)
            else:
                return 0.0
        else:
            return float(str(valor_causa).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        return 0.0

# Formata o nome do funcionário.
def _formatar_nome_funcionario(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome da funcionario."""
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo

    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0]
    return " ".join(partes[:2])


def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - ' (ex: 'BX_ANT_FIN - BANCO BRADESCO' -> 'BX_ANT_FIN')."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"


def filter_peticionamento_por_materia(
    peticionados: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_por_materia` em ``org_doc``
    (:func:`_normalizar_materia`).
    """
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(peticionados)
    return [p for p in peticionados if _normalizar_materia(p.get("MATERIA")) in alvos]


def filter_peticionamento_por_funcionario(
    peticionados: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_por_funcionario` em ``org_doc``
    (:func:`_formatar_nome_funcionario` deste módulo).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(peticionados)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in peticionados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_peticionamento_por_funcionarios(
    peticionados: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários (união — OR)."""
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


def _normalizar_uf_peticionamento(raw: Any) -> str:
    """Normaliza a UF vinda do banco ou da query para comparação."""
    return str(raw or "").strip().upper()


def list_ufs_peticionamento(peticionados: List[Dict[str, Any]]) -> List[str]:
    """Lista única de UFs disponíveis no recorte atual de peticionamento."""
    vistos: set[str] = set()
    saida: List[str] = []
    for row in peticionados or []:
        uf = _normalizar_uf_peticionamento(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_peticionamento_por_uf(
    peticionados: List[Dict[str, Any]],
    uf: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Restringe peticionamento aos registros de uma UF."""
    if uf is None or not str(uf).strip():
        return list(peticionados)
    alvo = _normalizar_uf_peticionamento(uf)
    return [
        p for p in peticionados
        if _normalizar_uf_peticionamento(p.get("UF") or p.get("uf")) == alvo
    ]


# Filtrar processos peticionados por intervalo de datas usando a coluna SAIDA.
def _filter_by_date_range(peticionados: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados peticionados por intervalo de datas usando a coluna DATA_CONFECCAO."""
    filtered = []
    for item in peticionados:
        try:
            saida_str = item.get("DATA_CONFECCAO") or item.get("data_confeccao")
            if not saida_str:
                continue
            
            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue
            
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()
            elif not isinstance(saida_date, date):
                continue

            if from_date <= saida_date <= to_date:
                filtered.append(item)
        except (ValueError, AttributeError, TypeError):
            continue

    return filtered

# -----------------------------------------------------------------------------
# 2 - Funções de Peticionamento
# -----------------------------------------------------------------------------

# Retorna a quantidade total de peticionados.
def get_total_peticionados(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_total_peticionados(peticionados))

# Retorna a quantidade de processos em revisão.
def get_processos_em_revisao(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_total_revisao(peticionados))

# Retorna a quantidade de peticionados automaticamente.
def get_peticionados_automaticamente(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_peticionados_automaticamente(peticionados))

# Retorna a quantidade de peticionados manualmente.
def get_peticionados_manualmente(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_peticionados_manualmente(peticionados))

# Retorna a quantidade de não peticionados.
def get_nao_peticionados(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_nao_peticionados(peticionados))

# Retorna a soma de peticionados e não peticionados (base para taxas).
# Se all_peticionados for informado, usa-o para contar não peticionados (ex.: dashboard com período filtrado).
def get_total_peticionamento(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
) -> int:
    nao_src = all_peticionados if all_peticionados is not None else peticionados
    return get_total_peticionados(peticionados) + get_nao_peticionados(nao_src)

# Retorna a taxa de resolvidos (peticionados / total) em percentual.
def get_peticionamento_taxa_resolvidos(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
) -> Optional[float]:
    total = get_total_peticionamento(peticionados, all_peticionados)
    if total == 0:
        return None
    return round((get_total_peticionados(peticionados) / total) * 100, 2)

# Retorna a taxa de não resolvidos (não peticionados / total) em percentual.
def get_peticionamento_taxa_nao_resolvidos(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
) -> Optional[float]:
    nao_src = all_peticionados if all_peticionados is not None else peticionados
    total = get_total_peticionamento(peticionados, all_peticionados)
    if total == 0:
        return None
    return round((get_nao_peticionados(nao_src) / total) * 100, 2)

# Retorna a quantidade de resolvidos reajuizamentos.
def get_resolvidos_reajuizamento_pet(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_resolvidos_reajuizamento(peticionados))

# Retorna a quantidade de não resolvidos reajuizamentos.
def get_nao_resolvidos_reajuizamento(peticionados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_nao_resolvidos_reajuizamento(peticionados))

# Retorna o valor de causa confeccionado (peticionados)
def get_valor_causa_confeccionado(peticionados: List[Dict[str, Any]]) -> float:
    total = 0.0
    for p in peticionados:
        # Verifica se atende aos critérios
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLAR"]

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

# Retorna valor de causa confeccionado por quantidade de matéria (média por matéria).
def get_ticket_medio_confeccionado(peticionados: List[Dict[str, Any]]) -> float:
    qtd = get_qtd_materia_peticionamento(peticionados)
    if qtd == 0:
        # print(f"[get_ticket_medio_confeccionado] retorno: 0.0 (qtd=0)")
        return 0.0
    valor = get_valor_causa_confeccionado(peticionados) / qtd
    # print(f"[get_ticket_medio_confeccionado] retorno: {valor} (valor_causa/{qtd})")
    return round(valor, 2)

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]
_SEM_DATA_KEY = "_sem_data"
_SEM_DATA_ENTRY = {"name": "Sem data", "value": 0}
_SEM_DATA_SORT = "9999-99"

# Agrupados processos confeccionados por mês
def group_peticionados_por_mes(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos Protocolados por Mês."""
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
    grouped: Dict[str, Dict[str, Any]] = {}

    for p in protocolos_agrupados:
        try:
            saida_str = p.get("DATA_CONTRATACAO") or p.get("data_contratacao")
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

# Agrupados processos não confeccionados por mês
def group_nao_peticionados_por_mes(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
# 4 - Agrupados por funcionario.
# -----------------------------------------------------------------------------

# agrupa processos resolvidos por funcionario
def group_peticionados_por_funcionario(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
def group_nao_peticionados_por_funcionario(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
def group_peticionados_por_dia(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    peticionados_agrupados = _filtrar_total_peticionados(peticionados)
    grouped = defaultdict(int)
    for p in peticionados_agrupados:
        dia = p.get("DATA_CONFECCAO") or p.get("data_confeccao")
        if not dia:
            continue
        dt = parse_date_from_db(dia)
        if  dt:
            dia_key = dt.strftime("%Y-%m-%d")
            grouped[dia_key] += 1
    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": count} for dia, count in sorted_items]

# Retorna processos peticionados por dia por funcionário.
def get_peticionados_por_dia_por_funcionario(peticionados: List[Dict[str, Any]]) -> Dict[str, Any]:
    peticionados_agrupados = _filtrar_total_peticionados(peticionados)
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in peticionados_agrupados:
        dia = p.get("DATA_CONFECCAO") or p.get("data_confeccao")
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
def get_valor_causa_peticionado_por_funcionario(peticionados: List[Dict[str, Any]]) -> Dict[str, float]:
    funcionario_values = defaultdict(float)
    for p in peticionados:
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PROTOCOLAR"]
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
# 4b - Comissionamento (apenas ações manuais concluídas)
# -----------------------------------------------------------------------------

def _materia_e_especifica_pet(materia_raw: Any) -> bool:
    """True quando a matéria é ESPECIFICA (aceita rótulo antes de ' - ')."""
    s = str(materia_raw or "").strip().upper()
    if not s:
        return False
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s == "ESPECIFICA"


# id de "ADMINISTRATIVO" em juridico.area_atuacao (mesmo id usado na LA).
_AREA_ATUACAO_ADMINISTRATIVO_ID = 2


# True quando a peça deve usar a tabela de comissão da ESPECIFICA (R$7/13/20):
# matéria ESPECIFICA, ou rubrica cuja área de atuação é ADMINISTRATIVO (ex.: progressões e
# gratificações de servidor público) — mesma lógica em todos os escritórios (NG, LA, RJ).
def _elegivel_tabela_especifica_pet(p: Dict[str, Any]) -> bool:
    if _materia_e_especifica_pet(p.get("MATERIA")):
        return True
    area_id = p.get("AREA_ATUACAO_ID")
    if area_id is not None:
        try:
            if int(area_id) == _AREA_ATUACAO_ADMINISTRATIVO_ID:
                return True
        except (TypeError, ValueError):
            pass
    return str(p.get("AREA_ATUACAO") or "").strip().upper() == "ADMINISTRATIVO"


def _filtrar_peticionados_por_funcionario_nome(
    peticionados: List[Dict[str, Any]],
    nome_funcionario: str,
) -> List[Dict[str, Any]]:
    return [
        p for p in peticionados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário") == nome_funcionario
    ]


def _preco_unitario_massa_pet(taxa: Optional[float]) -> Decimal:
    """Ações de massa: faixas por % de demanda concluída (taxa do funcionário)."""
    if taxa is None:
        return Decimal("0")
    if taxa >= 98:
        return Decimal("3.00")
    if taxa >= 85:
        return Decimal("1.50")
    if taxa >= 70:
        return Decimal("0.50")
    return Decimal("0")


def _preco_unitario_especifica_pet(taxa: Optional[float]) -> Decimal:
    """Ações ESPECIFICA: faixas por % de demanda concluída."""
    if taxa is None:
        return Decimal("0")
    if taxa >= 95:
        return Decimal("20.00")
    if taxa >= 85:
        return Decimal("13.00")
    if taxa >= 50:
        return Decimal("7.00")
    return Decimal("0")


def get_peticionamento_comissionamento_por_funcionario(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    peticionados_taxa: Optional[List[Dict[str, Any]]] = None,
    all_peticionados_taxa: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Comissão só sobre peticionamentos manuais (PROTOCOLAR + PET_AUTO falso).

    Por funcionário: conta ações de massa vs ESPECIFICA; aplica valor unitário conforme
    `get_peticionamento_taxa_resolvidos` no recorte do funcionário.

    A taxa usada para definir a faixa de comissão é sempre a taxa GERAL do funcionário
    (todas as matérias), não a taxa recortada pela matéria filtrada no dashboard —
    por isso `peticionados_taxa`/`all_peticionados_taxa` (sem filtro de matéria) são
    aceitos separadamente de `peticionados`/`all_peticionados` (usados só para contar
    as quantidades de Massa/ESPECIFICA exibidas). Quando não informados, cai no
    comportamento anterior (recorte igual ao de contagem).

    Massa: R$ 0,50 / 1,50 / 3,00 nas faixas 70% / 85% / 98%.
    ESPECIFICA: R$ 7 / 13 / 20 nas faixas 50% / 85% / 95%.

    Retorno inclui valor unitário e subtotais (qtd × valor) por tipo, taxa e total.
    """
    manual = _filtrar_peticionados_manualmente(peticionados)
    all_src = all_peticionados if all_peticionados is not None else peticionados
    taxa_src = peticionados_taxa if peticionados_taxa is not None else peticionados
    all_taxa_src = all_peticionados_taxa if all_peticionados_taxa is not None else all_src

    contagem: Dict[str, Dict[str, int]] = defaultdict(lambda: {"massa": 0, "especifica": 0})
    for p in manual:
        nome = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        if _elegivel_tabela_especifica_pet(p):
            contagem[nome]["especifica"] += 1
        else:
            contagem[nome]["massa"] += 1

    linhas: List[Dict[str, Any]] = []
    for nome in sorted(contagem.keys()):
        massa = contagem[nome]["massa"]
        especifica = contagem[nome]["especifica"]
        if massa == 0 and especifica == 0:
            continue

        pet_f = _filtrar_peticionados_por_funcionario_nome(taxa_src, nome)
        all_f = _filtrar_peticionados_por_funcionario_nome(all_taxa_src, nome)
        taxa = get_peticionamento_taxa_resolvidos(pet_f, all_f)

        pm = _preco_unitario_massa_pet(taxa)
        pe = _preco_unitario_especifica_pet(taxa)
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
def get_media_peticionado_por_funcionario(
    peticionados: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Média de processos protocolados por FUNCIONARIO."""
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        saida_str = p.get("DATA_CONFECCAO") or p.get("data_confeccao")

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
# 3 - Funções de por Atendente comercial
# -----------------------------------------------------------------------------

# Retorna a quantidade de peticionados por atendente.
def get_nao_peticionados_por_atendente(peticionados: List[Dict[str, Any]]) -> Dict[str, int]:
    nao_peticionados = _filtrar_nao_peticionados(peticionados)
    atendente_counts = defaultdict(int)
    for p in nao_peticionados:
        atendente = p.get("ATENDENTE_COMERCIAL") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    # Garantir que todos os valores são inteiros (contagem de processos)
    return {name: int(value) for name, value in dict(atendente_counts).items()}

# -----------------------------------------------------------------------------
# 2 - Funções temporais
# -----------------------------------------------------------------------------

 # Função auxiliar para extrair os dias
def _extrair_duracoes_dias(peticionados: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_total_peticionados(peticionados)
    duracoes: List[float] = []

    for p in protocolos_agrupados:
        try:
            entrada_str = p.get("ENTRADA") or p.get("entrada")
            saida_str = p.get("DATA_CONFECCAO") or p.get("data_confeccao")

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

# Retorna o tempo médio (em dias) para o processo peticionado no setor, de forma geral.
def get_media_tempo_peticionado(peticionados: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(peticionados)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) para o processo peticionado no setor, de forma geral.
def get_mediana_tempo_peticionado(peticionados: List[Dict[str, Any]]) -> float:
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
# 2 - Funções que agrupam por Matéria
# -----------------------------------------------------------------------------

# Agrupa processos peticionados por matéria.
def group_peticionados_por_materia(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos peticionados por matéria."""
    peticionados_agrupados = _filtrar_total_peticionados(peticionados)
    grouped = defaultdict(int)
    for p in peticionados_agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna a quantidade de matéria confeccionada (protocolar, não reajustado).
def get_qtd_materia_peticionamento(peticionados: List[Dict[str, Any]]) -> int:
    count = 0
    for p in peticionados:
        if str(p.get("STATUS", "")).upper() != "PROTOCOLAR":
            continue
        reaj = p.get("REAJUIZAMENTO")
        if str(reaj).upper() != "FALSE" and reaj is not False:
            continue
        materia = p.get("MATERIA")
        if materia is not None and str(materia).strip() != "":
            count += 1
    # print(f"[get_qtd_materia_peticionamento] retorno: {count}")
    return count


# Agrupa processos não peticionados por matéria.
def group_nao_peticionados_por_materia(peticionados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não peticionados por matéria."""
    nao_peticionados_agrupados = _filtrar_nao_peticionados(peticionados)
    grouped = defaultdict(int)
    for p in nao_peticionados_agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# -----------------------------------------------------------------------------
# 3 - Comparativo
# -----------------------------------------------------------------------------

# Retorna a variação percentual de peticionados.
def get_comparativo_peticionados(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_total_peticionados(dados_periodo_atual)
    dados_periodo_anterior = get_total_peticionados(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de tempo médio de peticionados.
def get_comparativo_tempo_medio_peticionado(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_media_tempo_peticionado(dados_periodo_atual)
    dados_periodo_anterior = get_media_tempo_peticionado(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de mediana de tempo de peticionados.
def get_comparativo_tempo_mediana_peticionado(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_mediana_tempo_peticionado(dados_periodo_atual)
    dados_periodo_anterior = get_mediana_tempo_peticionado(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de peticionados manualmente.
def get_comparativo_peticionados_manualmente(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_peticionados_manualmente (dados_periodo_atual)
    dados_periodo_anterior = get_peticionados_manualmente(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de peticionados automaticamente.
def get_comparativo_peticionados_automaticamente(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_peticionados_automaticamente(dados_periodo_atual)
    dados_periodo_anterior = get_peticionados_automaticamente(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de peticionados reajuizamento.
def get_comparativo_peticionados_reajuizamento(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_resolvidos_reajuizamento_pet (dados_periodo_atual)
    dados_periodo_anterior = get_resolvidos_reajuizamento_pet(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de não peticionados reajuizamento.
def get_comparativo_nao_peticionados_reajuizamento(
    peticionados: List[Dict[str, Any]],
    all_peticionados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_peticionados if all_peticionados is not None else peticionados
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(peticionados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_nao_resolvidos_reajuizamento (dados_periodo_atual)
    dados_periodo_anterior = get_nao_resolvidos_reajuizamento(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de valor de causa.
def get_comparativo_valor_causa_confeccionado(
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
    dados_periodo_atual = get_valor_causa_confeccionado(confeccionados_periodo_atual)
    dados_periodo_anterior = get_valor_causa_confeccionado(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de valor de causa.
def get_comparativo_ticket_medio_confeccionado(
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
    dados_periodo_atual = get_ticket_medio_confeccionado(confeccionados_periodo_atual)
    dados_periodo_anterior = get_ticket_medio_confeccionado(confeccionados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if dados_periodo_anterior == 0:
        # Se não houver dados do período anterior, retornar 0
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)