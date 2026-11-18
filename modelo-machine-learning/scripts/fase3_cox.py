# -*- coding: utf-8 -*-
"""
Fase 3 (parte 1) - Cox Proportional Hazards, Estagio 1 (distribuicao -> merito/acordo).

Modelo baseline interpretavel: hazard(t|X) = h0(t) * exp(beta . X).
Covariaveis: tipo_acao (bucket top-8 + Outros), materia (bucket top-8 + Outros),
log(valor_causa), escritorio (NG/LA - RJ fora do escopo: 9,4k processos com t0=distribuicao, 96% censurados).

Rodar: TCC - Luiz/.venv/bin/python scripts/fase3_cox.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import json
import sys

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")

BASE_DIR = ML_DIR

sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import (  # noqa: E402
    TOP_COMARCA, TOP_COMPETENCIA, TOP_MATERIA, TOP_TIPO_ACAO, bucket, carregar_coorte,
)



def main():
    df = carregar_coorte()
    df = df[df["id_escritorio_assinante"].isin([20, 21])].copy()  # NG, LA - exclui RJ (ver docstring) e id=3 (teste)
    df["duracao"] = df["duracao_dias_e1"].astype(float)
    df["evento"] = (df["tipo_evento_e1"] != "CENSURADO").astype(int)

    df["tipo_acao_b"] = bucket(df["tipo_acao"], TOP_TIPO_ACAO)
    df["materia_b"] = bucket(df["materia"], TOP_MATERIA)
    df["comarca_b"] = bucket(df["comarca"], TOP_COMARCA)
    df["competencia_b"] = bucket(df["competencia"], TOP_COMPETENCIA)
    df["escritorio"] = df["id_escritorio_assinante"].map({20: "NG", 21: "LA"})

    antes = len(df)
    df = df.dropna(subset=["valor_causa"]).copy()
    df["valor_causa"] = df["valor_causa"].astype(float)  # asyncpg/parquet guarda numeric como Decimal (object)
    df["log_valor_causa"] = np.log1p(df["valor_causa"].clip(lower=0))
    print(f"Descartadas por falta de valor_causa: {antes - len(df)} ({(antes - len(df)) / antes:.2%})")

    modelo_df = df[[
        "duracao", "evento", "tipo_acao_b", "materia_b", "comarca_b", "competencia_b",
        "log_valor_causa", "escritorio",
    ]].copy()
    print("N final para modelagem:", len(modelo_df))

    ref_tipo = df["tipo_acao_b"].value_counts().idxmax()
    ref_materia = df["materia_b"].value_counts().idxmax()
    ref_comarca = df["comarca_b"].value_counts().idxmax()
    ref_competencia = df["competencia_b"].value_counts().idxmax()
    print("Referencia tipo_acao:", ref_tipo, "| Referencia materia:", ref_materia,
          "| Referencia comarca:", ref_comarca, "| Referencia competencia:", ref_competencia)

    dummies_tipo = pd.get_dummies(modelo_df["tipo_acao_b"], prefix="tipo").drop(columns=[f"tipo_{ref_tipo}"])
    dummies_materia = pd.get_dummies(modelo_df["materia_b"], prefix="mat").drop(columns=[f"mat_{ref_materia}"])
    dummies_comarca = pd.get_dummies(modelo_df["comarca_b"], prefix="com").drop(columns=[f"com_{ref_comarca}"])
    dummies_competencia = pd.get_dummies(modelo_df["competencia_b"], prefix="comp").drop(columns=[f"comp_{ref_competencia}"])
    dummies_escritorio = pd.get_dummies(modelo_df["escritorio"], prefix="esc", drop_first=True)  # NG referencia

    X = pd.concat([
        modelo_df[["duracao", "evento", "log_valor_causa"]],
        dummies_tipo, dummies_materia, dummies_comarca, dummies_competencia, dummies_escritorio,
    ], axis=1)
    X.columns = [c.replace(" ", "_") for c in X.columns]

    cph = CoxPHFitter(penalizer=0.01)
    cph.fit(X, duration_col="duracao", event_col="evento")

    print("\n=== RESUMO DO MODELO ===")
    print("N =", cph._n_examples, " eventos =", int(X["evento"].sum()))
    print("Concordance index:", round(cph.concordance_index_, 4))
    print("Log-likelihood:", round(cph.log_likelihood_, 2))
    print("AIC:", round(cph.AIC_partial_, 2))

    resumo = cph.summary[["coef", "exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].sort_values("exp(coef)")
    print("\n=== HAZARD RATIOS (ordenado) ===")
    print(resumo.to_string())
    resumo.to_csv(f"{BASE_DIR}/dados/fase3_cox_hazard_ratios.csv")

    print("\n=== TESTE DE PROPORCIONALIDADE (Schoenfeld) ===")
    from lifelines.statistics import proportional_hazard_test
    # mesmo criterio do cph.check_assumptions usado antes: rejeita se km OU rank der p<0,05
    ph = proportional_hazard_test(cph, X, time_transform=["km", "rank"])
    p_min = ph.summary["p"].groupby(level=0).min()
    n_violadas = int((p_min < 0.05).sum())
    print(f"Covariaveis com PH rejeitada (p<0,05 em km ou rank): {n_violadas} de {len(resumo)}")

    # resumo numerico lido pelo gerar_capitulo_fase3.py (nada digitado a mao no capitulo)
    with open(f"{BASE_DIR}/dados/fase3_cox_resumo.json", "w", encoding="utf-8") as fh:
        json.dump({
            "n_modelo": int(len(X)), "n_descartados_valor_causa": int(antes - len(df)),
            "pct_descartados": 100 * (antes - len(df)) / antes,
            "eventos": int(X["evento"].sum()), "censurados": int(len(X) - X["evento"].sum()),
            "cindex": float(cph.concordance_index_), "loglik": float(cph.log_likelihood_),
            "aic": float(cph.AIC_partial_), "n_covariaveis": int(len(resumo)),
            "n_covariaveis_ph_violadas": n_violadas,
        }, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
