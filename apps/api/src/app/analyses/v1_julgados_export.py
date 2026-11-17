"""Exportação dos Julgados Acórdãos da v1 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (cópia de 17/11/2026; linha na v1 ao lado de cada bloco).
O gerar_generico.py copia só as rotas do dashboard; as rotas /export da v1 usam também estes campos,
rótulos e funções. Quem monta o arquivo na V2 é app/dashboards/export.py (CSV/XLSX de todos os dashboards).
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

# v1: dashboard_routes.py:32178
_CAMPOS_EXPORT_JULGADOS_ACORDAO_NG: Dict[str, str] = {
    "numero_processo": "NUMERO_PROCESSO",
    "materia": "MATERIA",
    "competencia": "COMPETENCIA",
    "comarca": "COMARCA",
    "uf": "UF",
    "fase": "FASE",
    "subfase": "SUBFASE",
    "camara_turma": "CAMARA_TURMA",
    "relator_2g": "RELATOR_2G",
    "merito_2g": "MERITO_ACORDAO_2G",
    "motivo_extincao": "MOTIVO_STATUS_2G",
    "data_ajuizamento": "DATA_AJUIZAMENTO",
    "data_acordao": "DATA_ACORDAO",
    "valor_acordao": "VALOR_ACORDAO",
    "data_acordao_embargos": "ACORDAO_EMBARGOS",
    "status_acordao_embargos": "STATUS_ACORDAO_EMBARGOS",
    "resultado_embargos_estimado": "RESULTADO_EMBARGOS_ESTIMADO",
}
# v1: dashboard_routes.py:32197
_LABELS_EXPORT_JULGADOS_ACORDAO_NG: Dict[str, str] = {
    "numero_processo": "Número do Processo",
    "materia": "Matéria",
    "competencia": "Competência",
    "comarca": "Comarca",
    "uf": "UF",
    "fase": "Fase",
    "subfase": "Subfase",
    "camara_turma": "Câmara/Turma",
    "relator_2g": "Relator (2G)",
    "merito_2g": "Acórdão de Mérito",
    "motivo_extincao": "Motivo da Extinção",
    "data_ajuizamento": "Data de Distribuição",
    "data_acordao": "Data do Acórdão",
    "valor_acordao": "Valor do Acórdão",
    "data_acordao_embargos": "Data do Acórdão de Embargos",
    "status_acordao_embargos": "Status do Acórdão de Embargos",
    "resultado_embargos_estimado": "Status Resultante dos Embargos",
}
# v1: dashboard_routes.py:32216 (LA e RJ: os mesmos campos do NG)
_CAMPOS_EXPORT_JULGADOS_ACORDAO_LA: Dict[str, str] = dict(_CAMPOS_EXPORT_JULGADOS_ACORDAO_NG)
_LABELS_EXPORT_JULGADOS_ACORDAO_LA: Dict[str, str] = dict(_LABELS_EXPORT_JULGADOS_ACORDAO_NG)
_CAMPOS_EXPORT_JULGADOS_ACORDAO_RJ: Dict[str, str] = dict(_CAMPOS_EXPORT_JULGADOS_ACORDAO_NG)
_LABELS_EXPORT_JULGADOS_ACORDAO_RJ: Dict[str, str] = dict(_LABELS_EXPORT_JULGADOS_ACORDAO_NG)


# v1: dashboard_routes.py:32222
def _filtrar_rows_julgados_por_data(
    rows: List[Dict[str, Any]],
    coluna: str,
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    # Sem período continua exigindo a data: o export só traz sentenças/acórdãos de fato, como o
    # dashboard (antes vinha a base inteira do escritório, inclusive processos sem julgamento).
    resultado: List[Dict[str, Any]] = []
    for row in rows:
        valor = row.get(coluna)
        if isinstance(valor, datetime):
            valor = valor.date()
        if not isinstance(valor, date):
            continue
        if from_date and valor < from_date:
            continue
        if to_date and valor > to_date:
            continue
        resultado.append(row)
    return resultado


# v1: dashboard_routes.py:32245
def _anotar_resultado_embargos_export(
    rows: List[Dict[str, Any]],
    resolver: Any,
) -> List[Dict[str, Any]]:
    """Injeta a coluna calculada RESULTADO_EMBARGOS_ESTIMADO (Status Resultante dos embargos, ou vazio)
    nas linhas do export, sem mutar os dicts originais (podem ser compartilhados pelo cache de
    `fetch_julgados_*`). Mesmo resolver do dashboard: matriz oficial (mérito antes dos embargos x
    resultado lançado) quando há resultado; "Sem resultado lançado" quando só há a data de embargo."""
    return [{**row, "RESULTADO_EMBARGOS_ESTIMADO": resolver(row) or ""} for row in rows]


# v1: dashboard_routes.py:32256
_CAMPOS_MOEDA_EXPORT_JULGADOS: frozenset[str] = frozenset({"valor_sentenca", "valor_acordao"})


# v1: dashboard_routes.py:32259
def _valor_moeda_julgados(val: Any) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# v1: dashboard_routes.py:32268
def _formatar_moeda_brl(valor: Optional[float]) -> str:
    if valor is None:
        return ""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"
