# -*- coding: utf-8 -*-
"""
Fase 4 - ponto pendente 2: XGBoost-AFT (Accelerated Failure Time), a segunda
alternativa de ML que o plano original cita ao lado da RSF.

Formato de dado que o AFT do XGBoost exige: em vez de (duracao, evento), cada
linha vira um INTERVALO [lower_bound, upper_bound] de tempo de sobrevivencia
plausivel:
  - evento observado: lower = upper = duracao (sabemos o tempo exato)
  - censurado: lower = duracao, upper = +inf (so sabemos que sobreviveu PELO
    MENOS ate ali)

Usa um corte de validacao dentro do TREINO (nunca toca o teste) soh pra early
stopping. Avalia no mesmo teste/split temporal dos outros dois modelos
(fase4_rsf.py, fase4_cox_mesmo_split.py) - mesma matriz de covariaveis
(montar_X), pra comparacao direta.

Direcao do risco: AFT preve o PROPRIO tempo de sobrevivencia (quanto maior,
mais lento) - o oposto de Cox/RSF (que prevem risco/hazard, maior = mais
rapido). Por isso o concordance index aqui usa -predicao como "risk score".

Configuracao revista em 09/11/2026 apos o backtest (fase5_backtest.py):
  - ANO DE DISTRIBUICAO como covariavel (ano_dist): os processos ficaram mais rapidos ao
    longo do tempo (mediana ~720 dias p/ distribuidos em 2022, ~250 em 2024, ~190 em 2025);
    sem saber a "epoca", o modelo preve o ritmo antigo. Num processo novo usa-se a data de
    referencia (as arvores caem no ritmo mais recente que viram).
  - base_score = mediana Kaplan-Meier do treino: o modelo comeca no nivel certo. Sem isso,
    com lr 0,05, o NIVEL das previsoes dependia de quantas rodadas o early stopping escolhia
    (no backtest de jul/2024 parou em 36 -> medianas 2-3x curtas demais).
  Backtest: C-index 0,674 -> 0,701 (jul/2024) e 0,616 -> 0,633 (jan/2025); calibracao estavel
  nas duas origens. Brier, Fase 5 e Fase 6 usam montar_X_xgb/params_xgb daqui.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase4_xgboost_aft.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sksurv.metrics import concordance_index_censored

sys.path.insert(0, (ML_DIR + "/scripts"))
from fase4_rsf import montar_X  # noqa: E402
from lifelines import KaplanMeierFitter  # noqa: E402

BASE_DIR = ML_DIR
from coorte_comum import DATA_REFERENCIA  # noqa: E402  ("hoje" p/ processos novos, da foto congelada)

PARAMS_XGB = {
    "objective": "survival:aft",
    "eval_metric": "aft-nloglik",
    "aft_loss_distribution": "normal",
    "aft_loss_distribution_scale": 1.0,
    "tree_method": "hist",
    "max_depth": 4,
    "learning_rate": 0.05,
    "min_child_weight": 20,
    "seed": 42,
}


def ano_frac(datas):
    dt = pd.to_datetime(datas)
    return (dt.dt.year + (dt.dt.dayofyear - 1) / 365.25).to_numpy() if hasattr(dt, "dt") else \
        dt.year + (dt.dayofyear - 1) / 365.25


def montar_X_xgb(df, colunas_referencia=None, data_referencia=None):
    """montar_X + ano de distribuicao. data_referencia: usa essa data p/ todas as linhas
    (processo novo, Fase 6) em vez de df['distribuicao_d']."""
    X = montar_X(df)
    X["ano_dist"] = (ano_frac(df["distribuicao_d"]) if data_referencia is None
                     else float(ano_frac(pd.Timestamp(data_referencia))))
    if colunas_referencia is not None:
        X = X.reindex(columns=colunas_referencia, fill_value=False)
    return X


def mediana_km(duracao, evento):
    return float(KaplanMeierFitter().fit(duracao, event_observed=evento).median_survival_time_)


def params_xgb(base_score):
    return {**PARAMS_XGB, "base_score": float(base_score)}


def montar_dmatrix(X, duracao, evento):
    lower = duracao.astype(float).copy()
    upper = duracao.astype(float).copy()
    upper[~evento] = np.inf  # censurado: so sabemos "sobreviveu >= duracao"
    d = xgb.DMatrix(X)
    d.set_float_info("label_lower_bound", lower)
    d.set_float_info("label_upper_bound", upper)
    return d


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    treino_full = df[df["split"] == "treino"].reset_index(drop=True)
    teste = df[df["split"] == "teste"].reset_index(drop=True)

    X_treino_full = montar_X_xgb(treino_full)
    X_teste = montar_X_xgb(teste, colunas_referencia=X_treino_full.columns)

    # corte interno so pra early stopping (85/15 do treino, por ORDEM TEMPORAL
    # de novo - nao aleatorio, pra nao vazar "futuro dentro do treino")
    treino_full_sorted = treino_full.sort_values("distribuicao_d")
    corte_idx = treino_full_sorted.index[int(len(treino_full_sorted) * 0.85)]
    corte_data = treino_full.loc[corte_idx, "distribuicao_d"]
    is_fit = treino_full["distribuicao_d"] < corte_data

    X_fit = X_treino_full[is_fit.to_numpy()].reset_index(drop=True)
    X_val = X_treino_full[~is_fit.to_numpy()].reset_index(drop=True)
    treino_fit = treino_full[is_fit].reset_index(drop=True)
    treino_val = treino_full[~is_fit].reset_index(drop=True)

    evento_fit = (treino_fit["tipo_evento_e1"] != "CENSURADO").to_numpy()
    evento_val = (treino_val["tipo_evento_e1"] != "CENSURADO").to_numpy()
    evento_treino_full = (treino_full["tipo_evento_e1"] != "CENSURADO").to_numpy()
    evento_teste = (teste["tipo_evento_e1"] != "CENSURADO").to_numpy()

    d_fit = montar_dmatrix(X_fit, treino_fit["duracao_dias_e1"].to_numpy(), evento_fit)
    d_val = montar_dmatrix(X_val, treino_val["duracao_dias_e1"].to_numpy(), evento_val)
    d_treino_full = montar_dmatrix(X_treino_full, treino_full["duracao_dias_e1"].to_numpy(), evento_treino_full)
    d_teste = montar_dmatrix(X_teste, teste["duracao_dias_e1"].to_numpy(), evento_teste)

    print(f"Fit interno: N={len(X_fit)} | Validacao interna: N={len(X_val)} | Teste: N={len(X_teste)}")

    base_fit = mediana_km(treino_fit["duracao_dias_e1"], evento_fit)
    base_full = mediana_km(treino_full["duracao_dias_e1"], evento_treino_full)
    print(f"base_score (mediana KM): fit interno {base_fit:.0f} d | treino inteiro {base_full:.0f} d")

    booster = xgb.train(
        params_xgb(base_fit),
        d_fit, num_boost_round=2000,
        evals=[(d_fit, "fit"), (d_val, "val")],
        early_stopping_rounds=50, verbose_eval=100,
    )
    print(f"\nMelhor iteracao (early stopping): {booster.best_iteration}")

    # reajusta no TREINO INTEIRO com o num_boost_round escolhido pela validacao interna
    # (mesma logica de "achar o hiperparametro no que sobrou, usar tudo no final")
    booster_final = xgb.train(params_xgb(base_full), d_treino_full, num_boost_round=booster.best_iteration + 1)

    pred_treino = booster_final.predict(d_treino_full)  # tempo previsto (maior = sobrevive mais)
    pred_teste = booster_final.predict(d_teste)

    cindex_treino = concordance_index_censored(evento_treino_full, treino_full["duracao_dias_e1"], -pred_treino)[0]
    cindex_teste = concordance_index_censored(evento_teste, teste["duracao_dias_e1"], -pred_teste)[0]

    print(f"\nC-index XGBoost-AFT (treino): {cindex_treino:.4f}")
    print(f"C-index XGBoost-AFT (teste):  {cindex_teste:.4f}")


    importancia = booster_final.get_score(importance_type="gain")
    importancia = pd.Series(importancia).sort_values(ascending=False)
    print("\n=== Importancia de variavel (gain) ===")
    print(importancia.to_string())

    importancia.to_frame("gain").to_csv(f"{BASE_DIR}/dados/fase4_xgboost_importancia.csv")
    pd.DataFrame([{
        "best_iteration": booster.best_iteration, "base_score": base_full,
        "cindex_treino": cindex_treino, "cindex_teste": cindex_teste,
    }]).to_csv(f"{BASE_DIR}/dados/fase4_xgboost_metricas.csv", index=False)
    print(f"\nSalvo: dados/fase4_xgboost_importancia.csv, dados/fase4_xgboost_metricas.csv")


if __name__ == "__main__":
    main()
