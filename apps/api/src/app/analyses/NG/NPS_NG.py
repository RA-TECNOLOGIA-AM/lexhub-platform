"""Análises de NPS (Net Promoter Score) — banco NG.

Fonte: relatorios.nps_escritorio

Campos de avaliação (escala 0–10):
  AV_TEMPO_RESPOSTA  — satisfação com tempo de resposta
  AV_NIVEL_INFO      — nível de informação percebido
  AV_PROB_IND        — probabilidade de indicação (base do NPS clássico)
  AV_CONFIANCA       — confiança futura no escritório
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.utils import parse_date_from_db


def _validos(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra linhas que têm ao menos a nota de indicação válida (0–10)."""
    out = []
    for r in respostas:
        val = r.get("AV_PROB_IND")
        if val is None:
            continue
        try:
            n = int(val)
            if 0 <= n <= 10:
                out.append(r)
        except (ValueError, TypeError):
            continue
    return out


def _safe_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        n = int(v)
        return n if 0 <= n <= 10 else None
    except (ValueError, TypeError):
        return None


def _classificar(nota: int) -> str:
    if nota >= 9:
        return "Promotor"
    elif nota >= 7:
        return "Neutro"
    return "Detrator"


def _avg(values: List[int]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


# ─── Métricas escalares ───────────────────────────────────────────────────────

def get_total_respostas(respostas: List[Dict[str, Any]]) -> int:
    return len(_validos(respostas))


def get_nivel_indicacao(respostas: List[Dict[str, Any]]) -> float:
    """NPS = (% promotores − % detratores) × 100, baseado em AV_PROB_IND."""
    validos = _validos(respostas)
    total = len(validos)
    if total == 0:
        return 0.0
    notas = [int(r["AV_PROB_IND"]) for r in validos]
    promotores = sum(1 for n in notas if n >= 9)
    detratores = sum(1 for n in notas if n <= 6)
    return round(((promotores - detratores) / total) * 100, 2)


def get_taxa_confianca(respostas: List[Dict[str, Any]]) -> float:
    """Taxa de confiança = % de respostas com AV_CONFIANCA >= 7."""
    validos = _validos(respostas)
    total = len(validos)
    if total == 0:
        return 0.0
    confiantes = sum(
        1 for r in validos
        if _safe_int(r.get("AV_CONFIANCA")) is not None and int(r["AV_CONFIANCA"]) >= 7
    )
    return round((confiantes / total) * 100, 2)


def get_nivel_informacao(respostas: List[Dict[str, Any]]) -> float:
    """Nível de informação = média de AV_NIVEL_INFO (0–10)."""
    vals = [int(r["AV_NIVEL_INFO"]) for r in _validos(respostas) if _safe_int(r.get("AV_NIVEL_INFO")) is not None]
    return _avg(vals)


def get_media_tempo_resposta(respostas: List[Dict[str, Any]]) -> float:
    """Média de satisfação com tempo de resposta = média de AV_TEMPO_RESPOSTA (0–10)."""
    vals = [int(r["AV_TEMPO_RESPOSTA"]) for r in _validos(respostas) if _safe_int(r.get("AV_TEMPO_RESPOSTA")) is not None]
    return _avg(vals)


def get_total_promotores(respostas: List[Dict[str, Any]]) -> int:
    return sum(1 for r in _validos(respostas) if int(r["AV_PROB_IND"]) >= 9)


def get_total_neutros(respostas: List[Dict[str, Any]]) -> int:
    return sum(1 for r in _validos(respostas) if 7 <= int(r["AV_PROB_IND"]) <= 8)


def get_total_detratores(respostas: List[Dict[str, Any]]) -> int:
    return sum(1 for r in _validos(respostas) if int(r["AV_PROB_IND"]) <= 6)


def get_nps_stats(respostas: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "nps_total_respostas":      get_total_respostas(respostas),
        "nps_score":                get_nivel_indicacao(respostas),
        "nps_taxa_confianca":       get_taxa_confianca(respostas),
        "nps_nivel_informacao":     get_nivel_informacao(respostas),
        "nps_nivel_indicacao":      get_nivel_indicacao(respostas),
        "nps_media_tempo_resposta": get_media_tempo_resposta(respostas),
        "nps_total_promotores":     get_total_promotores(respostas),
        "nps_total_neutros":        get_total_neutros(respostas),
        "nps_total_detratores":     get_total_detratores(respostas),
    }


# ─── Agrupamentos / gráficos ──────────────────────────────────────────────────

def group_nps_por_classificacao(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {"Promotor": 0, "Neutro": 0, "Detrator": 0}
    for r in _validos(respostas):
        counts[_classificar(int(r["AV_PROB_IND"]))] += 1
    return [{"name": k, "value": v} for k, v in counts.items() if v > 0]


def group_nps_por_nota(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Distribuição de AV_PROB_IND por nota (0–10)."""
    counts: Dict[int, int] = {i: 0 for i in range(11)}
    for r in _validos(respostas):
        counts[int(r["AV_PROB_IND"])] += 1
    return [{"name": str(i), "value": counts[i]} for i in range(11)]


def group_nps_por_mes(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Total de respostas por mês."""
    by_month: Dict[str, int] = defaultdict(int)
    for r in _validos(respostas):
        raw_date = r.get("DATA")
        if not raw_date:
            continue
        d = parse_date_from_db(raw_date)
        if not d:
            continue
        by_month[f"{d.year}-{d.month:02d}"] += 1

    return [{"name": mes, "value": total} for mes, total in sorted(by_month.items())]


# ─── Tabelas ──────────────────────────────────────────────────────────────────

def get_respostas_tabela(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for r in _validos(respostas):
        nota = int(r["AV_PROB_IND"])
        rows.append({
            "id":                   r.get("ID") or 0,
            "cliente":              str(r.get("CLIENTE") or ""),
            "telefone":             str(r.get("TELEFONE") or ""),
            "data":                 str(r.get("DATA") or ""),
            "classificacao":        _classificar(nota),
            "av_prob_ind":          nota,
            "av_confianca":         _safe_int(r.get("AV_CONFIANCA")),
            "av_nivel_info":        _safe_int(r.get("AV_NIVEL_INFO")),
            "av_tempo_resposta":    _safe_int(r.get("AV_TEMPO_RESPOSTA")),
            "feedback_positivo":    str(r.get("FEEDBACK_POSITIVO") or ""),
            "feedback_melhoria":    str(r.get("FEEDBACK_MELHORIA") or ""),
            "etapa_preocupacao":    str(r.get("ETAPA_PREOCUPACAO") or ""),
            "comentario":           str(r.get("COMENTARIO") or ""),
        })
    return sorted(rows, key=lambda x: x.get("data") or "", reverse=True)


def get_feedbacks_melhoria(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id":               r.get("ID") or 0,
            "cliente":          str(r.get("CLIENTE") or ""),
            "telefone":         str(r.get("TELEFONE") or ""),
            "data":             str(r.get("DATA") or ""),
            "classificacao":    _classificar(int(r["AV_PROB_IND"])),
            "av_prob_ind":      int(r["AV_PROB_IND"]),
            "feedback_melhoria": str(r.get("FEEDBACK_MELHORIA") or ""),
        }
        for r in _validos(respostas)
        if r.get("FEEDBACK_MELHORIA") and str(r["FEEDBACK_MELHORIA"]).strip()
    ]


def get_feedbacks_positivos(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id":               r.get("ID") or 0,
            "cliente":          str(r.get("CLIENTE") or ""),
            "telefone":         str(r.get("TELEFONE") or ""),
            "data":             str(r.get("DATA") or ""),
            "classificacao":    _classificar(int(r["AV_PROB_IND"])),
            "av_prob_ind":      int(r["AV_PROB_IND"]),
            "feedback_positivo": str(r.get("FEEDBACK_POSITIVO") or ""),
        }
        for r in _validos(respostas)
        if r.get("FEEDBACK_POSITIVO") and str(r["FEEDBACK_POSITIVO"]).strip()
    ]


def get_comentarios(respostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id":               r.get("ID") or 0,
            "cliente":          str(r.get("CLIENTE") or ""),
            "telefone":         str(r.get("TELEFONE") or ""),
            "data":             str(r.get("DATA") or ""),
            "classificacao":    _classificar(int(r["AV_PROB_IND"])),
            "av_prob_ind":      int(r["AV_PROB_IND"]),
            "comentario":       str(r.get("COMENTARIO") or ""),
        }
        for r in _validos(respostas)
        if r.get("COMENTARIO") and str(r["COMENTARIO"]).strip()
    ]
