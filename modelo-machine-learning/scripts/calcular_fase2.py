# -*- coding: utf-8 -*-
"""
Recalcula todos os numeros do capitulo da Fase 2 (estatistica descritiva, medianas
de Kaplan-Meier, rankings e testes de log-rank) a partir da coorte vigente -
conferencia independente dos valores do dashboard interativo (TypeScript).

Nao filtra escritorio aqui: desde 09/11/2026 a propria coorte oficial (.sql) ja e
so NG+LA/AM (RJ saiu do estudo), o mesmo escopo das Fases 3-6.

Rodar: TCC - Luiz/.venv/bin/python scripts/calcular_fase2.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import json
import sys

import pandas as pd
from lifelines import KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import carregar_coorte  # noqa: E402

pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")

MIN_N = 30
TOP_N = 8


def mediana_km(duracao, evento):
    kmf = KaplanMeierFitter()
    kmf.fit(duracao, event_observed=evento)
    return kmf.median_survival_time_


def ranking_e_logrank(df, campo, duracao_col, evento_col):
    contagem = df[campo].value_counts()
    top = contagem[contagem >= MIN_N].head(TOP_N).index.tolist()
    sub = df[df[campo].isin(top)]

    linhas = []
    for cat in top:
        grp = sub[sub[campo] == cat]
        med = mediana_km(grp[duracao_col], grp[evento_col])
        linhas.append({"categoria": cat, "mediana": med, "n": len(grp)})
    linhas.sort(key=lambda r: (r["mediana"] if pd.notna(r["mediana"]) else -1), reverse=True)

    result = multivariate_logrank_test(sub[duracao_col], sub[campo], sub[evento_col])
    return linhas, result.test_statistic, result.degrees_of_freedom, result.p_value


def main():
    df = carregar_coorte()
    df["evento_e1"] = (df["tipo_evento_e1"] != "CENSURADO").astype(int)

    saida = {}
    saida["n_total"] = len(df)

    # ---- Estagio 1 ----
    med_geral_e1 = mediana_km(df["duracao_dias_e1"], df["evento_e1"])
    n_favoravel = int((df["tipo_evento_e1"] == "MERITO_FAVORAVEL_COM_PROVEITO").sum())
    n_elegivel_e2 = int(df["tipo_evento_e1"].isin(["ACORDO", "MERITO_FAVORAVEL_COM_PROVEITO"]).sum())

    saida["estagio1"] = {
        "n": len(df),
        "mediana": med_geral_e1,
        "n_favoravel": n_favoravel,
        "pct_favoravel": round(100 * n_favoravel / len(df), 1),
        "n_elegivel_e2": n_elegivel_e2,
    }

    rank_tipo_e1, chi2_tipo_e1, gl_tipo_e1, p_tipo_e1 = ranking_e_logrank(df, "tipo_acao", "duracao_dias_e1", "evento_e1")
    rank_mat_e1, chi2_mat_e1, gl_mat_e1, p_mat_e1 = ranking_e_logrank(df, "materia", "duracao_dias_e1", "evento_e1")
    saida["estagio1"]["ranking_tipo_acao"] = rank_tipo_e1
    saida["estagio1"]["logrank_tipo_acao"] = {"chi2": chi2_tipo_e1, "gl": gl_tipo_e1, "p": p_tipo_e1}
    saida["estagio1"]["ranking_materia"] = rank_mat_e1
    saida["estagio1"]["logrank_materia"] = {"chi2": chi2_mat_e1, "gl": gl_mat_e1, "p": p_mat_e1}

    # ---- Estagio 2 ----
    df_e2 = df[df["tipo_evento_e2"].notna()].copy()
    df_e2["evento_e2"] = (df_e2["tipo_evento_e2"] == "PAGO").astype(int)
    med_geral_e2 = mediana_km(df_e2["duracao_dias_e2"], df_e2["evento_e2"])
    n_pago = int((df_e2["tipo_evento_e2"] == "PAGO").sum())

    saida["estagio2"] = {
        "n": len(df_e2),
        "mediana": med_geral_e2,
        "n_pago": n_pago,
        "pct_pago": round(100 * n_pago / len(df_e2), 1),
    }

    rank_tipo_e2, chi2_tipo_e2, gl_tipo_e2, p_tipo_e2 = ranking_e_logrank(df_e2, "tipo_acao", "duracao_dias_e2", "evento_e2")
    rank_mat_e2, chi2_mat_e2, gl_mat_e2, p_mat_e2 = ranking_e_logrank(df_e2, "materia", "duracao_dias_e2", "evento_e2")
    saida["estagio2"]["ranking_tipo_acao"] = rank_tipo_e2
    saida["estagio2"]["logrank_tipo_acao"] = {"chi2": chi2_tipo_e2, "gl": gl_tipo_e2, "p": p_tipo_e2}
    saida["estagio2"]["ranking_materia"] = rank_mat_e2
    saida["estagio2"]["logrank_materia"] = {"chi2": chi2_mat_e2, "gl": gl_mat_e2, "p": p_mat_e2}

    print(json.dumps(saida, ensure_ascii=False, indent=2, default=str))
    with open("dados/fase2_numeros.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2, default=str)
    print("\nSalvo em dados/fase2_numeros.json")


if __name__ == "__main__":
    main()
