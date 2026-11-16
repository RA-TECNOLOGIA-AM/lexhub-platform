"""Meta inteligente por atendente — cópia da v1 (api_dashboards/src/app/analyses/NG/ml/meta_inteligente.py),
SEM mudar a lógica. Na v1 era a rota GET /comercial-lexpre/ml/meta_inteligente; na V2 sai na própria
resposta do Comercial (LexPre), campo `meta_inteligente` (ver app/dashboards/comercial_lexpre.py).

Média móvel ponderada (meses recentes pesam mais) + tendência linear do valor de causa protocolado por
atendente/mês; meta sugerida = projeção do próximo mês + stretch goal (10%).
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from collections import defaultdict
import statistics
from app.utils import parse_date_from_db
from app.analyses.NG.comercial_geral import _is_atendente_ativo


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _agrupar_valor_causa_por_atendente_mes(
    comercial_geral: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Retorna { atendente: { "YYYY-MM": valor_causa_total } }
    Considera apenas registros protocolados (STATUS == 1, REAJUIZAMENTO == False).
    """
    resultado: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for c in comercial_geral:
        if not _is_atendente_ativo(c):
            continue
        # Mesmo filtro que get_acoes_fechadas / protocolados
        if not c.get("SAIDA") and not c.get("saida"):
            continue

        atendente = str(c.get("ATENDENTE") or "Sem atendente").strip()
        valor_causa = c.get("VALOR_DA_CAUSA") or c.get("valor_da_causa") or 0

        try:
            valor_causa = float(valor_causa)
        except (ValueError, TypeError):
            continue

        assinatura = c.get("SAIDA") or c.get("saida")
        if not assinatura:
            continue

        data_obj = parse_date_from_db(assinatura)
        if not data_obj:
            continue

        if isinstance(data_obj, datetime):
            data_obj = data_obj.date()

        chave_mes = f"{data_obj.year}-{data_obj.month:02d}"
        resultado[atendente][chave_mes] += valor_causa

    return resultado


def _calcular_tendencia_linear(valores: List[float]) -> float:
    """
    Calcula a inclinação da reta de tendência (regressão linear simples).
    Retorna quanto o valor cresce/decresce por mês em média.
    """
    n = len(valores)
    if n < 2:
        return 0.0

    x_media = (n - 1) / 2
    y_media = statistics.mean(valores)

    numerador = sum((i - x_media) * (v - y_media) for i, v in enumerate(valores))
    denominador = sum((i - x_media) ** 2 for i in range(n))

    if denominador == 0:
        return 0.0

    return numerador / denominador


def _media_movel_ponderada(valores: List[float]) -> float:
    """
    Média ponderada: meses mais recentes têm peso maior.
    Ex.: 3 meses → pesos [1, 2, 3]; 6 meses → pesos [1,2,3,4,5,6].
    """
    n = len(valores)
    if n == 0:
        return 0.0

    pesos = list(range(1, n + 1))
    soma_ponderada = sum(p * v for p, v in zip(pesos, valores))
    soma_pesos = sum(pesos)

    return soma_ponderada / soma_pesos


def _classificar_tendencia(tendencia: float, media: float) -> str:
    """Classifica a tendência em relação à média mensal."""
    if media == 0:
        return "estável"

    pct = (tendencia / media) * 100

    if pct >= 10:
        return "crescimento forte"
    elif pct >= 3:
        return "crescimento moderado"
    elif pct <= -10:
        return "queda forte"
    elif pct <= -3:
        return "queda moderada"
    else:
        return "estável"


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------


def calcular_meta_inteligente_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    meses_historico: int = 6,
    stretch_goal_pct: float = 0.10,
    meta_global_periodo: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula meta inteligente de valor de causa protocolado por atendente.

    Parâmetros
    ----------
    comercial_geral      : lista de registros do setor comercial
    meses_historico      : quantos meses anteriores usar no cálculo (padrão: 6)
    stretch_goal_pct     : percentual adicional de desafio na meta (padrão: 10%)
    meta_global_periodo  : se informado, distribui a meta global entre os atendentes
                           proporcionalmente à performance histórica

    Retorna
    -------
    {
        "gerado_em": "YYYY-MM-DD",
        "meses_considerados": 6,
        "meta_global": 15000000.0,          # se informada
        "atendentes": [
            {
                "atendente": "João Silva",
                "meses_com_dados": 6,
                "historico_mensal": [        # últimos N meses ordenados
                    {"mes": "2024-10", "valor": 820000.0},
                    ...
                ],
                "media_simples": 950000.0,
                "media_ponderada": 1020000.0,
                "tendencia_mensal": 35000.0,
                "tendencia_label": "crescimento moderado",
                "projecao_proximo_mes": 1055000.0,
                "meta_sugerida": 1160500.0,  # projeção + stretch goal
                "meta_proporcional": 3200000.0,  # se meta_global informada
                "percentual_da_equipe": 21.3,
            },
            ...
        ],
        "totais": {
            "media_equipe_mes": 4200000.0,
            "projecao_total_proximo_mes": 4800000.0,
            "meta_total_sugerida": 5280000.0,
        }
    }
    """
    historico = _agrupar_valor_causa_por_atendente_mes(comercial_geral)

    if not historico:
        return {
            "gerado_em": date.today().isoformat(),
            "meses_considerados": meses_historico,
            "atendentes": [],
            "totais": {},
        }

    # Todos os meses presentes nos dados, ordenados
    todos_os_meses = sorted({mes for meses in historico.values() for mes in meses.keys()})

    # Pegar apenas os últimos N meses disponíveis
    meses_selecionados = todos_os_meses[-meses_historico:]

    resultado_atendentes = []
    soma_media_ponderada = 0.0

    for atendente, meses_valores in historico.items():
        # Série dos meses selecionados (0.0 se o atendente não teve dado naquele mês)
        serie = [meses_valores.get(mes, 0.0) for mes in meses_selecionados]

        meses_com_dados = sum(1 for v in serie if v > 0)

        # Atendentes com menos de 2 meses de dados não geram meta confiável
        if meses_com_dados < 2:
            continue

        media_simples = statistics.mean(serie)
        media_ponderada = _media_movel_ponderada(serie)
        tendencia = _calcular_tendencia_linear(serie)
        tendencia_label = _classificar_tendencia(tendencia, media_simples)

        # Projeção: média ponderada + tendência do último período
        projecao = max(0.0, media_ponderada + tendencia)

        # Meta = projeção + stretch goal
        meta_sugerida = projecao * (1 + stretch_goal_pct)

        soma_media_ponderada += media_ponderada

        historico_mensal = [
            {"mes": mes, "valor": round(meses_valores.get(mes, 0.0), 2)}
            for mes in meses_selecionados
        ]

        resultado_atendentes.append(
            {
                "atendente": atendente,
                "meses_com_dados": meses_com_dados,
                "historico_mensal": historico_mensal,
                "media_simples": round(media_simples, 2),
                "media_ponderada": round(media_ponderada, 2),
                "tendencia_mensal": round(tendencia, 2),
                "tendencia_label": tendencia_label,
                "projecao_proximo_mes": round(projecao, 2),
                "meta_sugerida": round(meta_sugerida, 2),
                "percentual_da_equipe": 0.0,  # calculado abaixo
                "meta_proporcional": 0.0,  # calculado abaixo
            }
        )

    # Ordenar do maior valor protocolado para o menor
    resultado_atendentes.sort(key=lambda x: x["media_ponderada"], reverse=True)

    # Calcular participação % de cada atendente na equipe
    # e meta proporcional (se meta_global informada)
    for row in resultado_atendentes:
        if soma_media_ponderada > 0:
            pct = (row["media_ponderada"] / soma_media_ponderada) * 100
            row["percentual_da_equipe"] = round(pct, 1)

            if meta_global_periodo:
                row["meta_proporcional"] = round(meta_global_periodo * (pct / 100), 2)

    # Totais
    projecao_total = sum(r["projecao_proximo_mes"] for r in resultado_atendentes)
    meta_total = sum(r["meta_sugerida"] for r in resultado_atendentes)
    n = len(resultado_atendentes)

    totais = {
        "media_equipe_mes": round(soma_media_ponderada / n, 2) if n > 0 else 0.0,
        "projecao_total_proximo_mes": round(projecao_total, 2),
        "meta_total_sugerida": round(meta_total, 2),
    }

    return {
        "gerado_em": date.today().isoformat(),
        "meses_considerados": meses_historico,
        "meta_global": meta_global_periodo,
        "atendentes": resultado_atendentes,
        "totais": totais,
    }
