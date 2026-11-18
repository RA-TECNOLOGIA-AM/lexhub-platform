# -*- coding: utf-8 -*-
"""
Fase 4 (adiantando parte da Fase 5): Brier Score integrado (IBS) dos tres
modelos no MESMO teste temporal - complementa o C-index (que mede so a ORDEM
das previsoes) com uma medida de CALIBRACAO (a probabilidade prevista bate com
a frequencia real?). Quanto menor o IBS, melhor (0 = perfeito; 0,25 e o "chute
constante de 0,5" de referencia pra comparar).

Metodologia:
  - Cox e RSF ja preveem S(t|x) nativamente (predict_survival_function).
  - XGBoost-AFT nao tem predict_survival_function pronto: o modelo foi
    ajustado como log-normal AFT (aft_loss_distribution="normal", scale=1.0),
    entao log(T) ~ Normal(log(pred), scale) por definicao do proprio ajuste -
    dai S(t|x) = 1 - Phi((ln(t) - ln(pred)) / scale) e a formula EXATA do
    modelo que ja treinamos, nao uma aproximacao nova. Checagem de sanidade:
    em t = pred, Phi(0) = 0,5 -> S(pred|x) = 0,5 sempre, por construcao (e o
    que se espera de uma mediana).
  - IBS calculado via sksurv.metrics.integrated_brier_score, numa grade de
    tempo comum aos tres modelos.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase4_brier_calibracao.py
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
from lifelines import CoxPHFitter
from scipy.stats import norm
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import brier_score, integrated_brier_score
from sksurv.util import Surv

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import hiperparametros_fase4  # noqa: E402
from fase4_rsf import montar_X, rsf_em_blocos  # noqa: E402
from fase4_xgboost_aft import montar_dmatrix, montar_X_xgb, params_xgb  # noqa: E402

BASE_DIR = ML_DIR
REF_DROP = ["tipo_INDENIZATÓRIA", "mat_Outros", "com_MANAUS", "comp_Juizado_Especial_Cível", "esc_LA"]


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    treino = df[df["split"] == "treino"].reset_index(drop=True)
    teste = df[df["split"] == "teste"].reset_index(drop=True)

    X_treino = montar_X(treino)
    X_teste = montar_X(teste, colunas_referencia=X_treino.columns)
    evento_treino = (treino["tipo_evento_e1"] != "CENSURADO").to_numpy()
    evento_teste = (teste["tipo_evento_e1"] != "CENSURADO").to_numpy()
    dur_treino = treino["duracao_dias_e1"].to_numpy()
    dur_teste = teste["duracao_dias_e1"].to_numpy()
    y_treino = Surv.from_arrays(event=evento_treino, time=dur_treino)
    y_teste = Surv.from_arrays(event=evento_teste, time=dur_teste)

    # grade de tempo: precisa ficar estritamente dentro do intervalo observado
    # no teste (exigencia do sksurv pra estimar a distribuicao de censura via KM).
    # NOTA: o teste e feito so de processos contratados nos ultimos ~8 meses (split
    # temporal), entao duracao_dias_e1 maxima observada la e baixa (~248 dias) -
    # nada a ver com o horizonte de 1800 dias usado no Fine-Gray (Fase 3). A grade
    # fica curta por construcao do proprio desenho do split, nao e bug.
    passo = 15
    grade = np.arange(passo, dur_teste.max() - 1, passo)
    print(f"Grade de avaliacao: {grade.min()}-{grade.max()} dias ({len(grade)} pontos) "
          f"- limitada pela duracao maxima observada no teste ({dur_teste.max()} dias)")

    # ---- Cox ----
    print("\nAjustando Cox...")
    treino_cox = X_treino.astype(float).copy()
    treino_cox["duracao"] = dur_treino
    treino_cox["evento"] = evento_treino.astype(int)
    teste_cox = X_teste.astype(float).drop(columns=REF_DROP)
    treino_cox = treino_cox.drop(columns=REF_DROP)  # dropa as referencias, mantem duracao/evento
    cph = CoxPHFitter(penalizer=0.01)
    cph.fit(treino_cox, duration_col="duracao", event_col="evento")
    sf_cox = cph.predict_survival_function(teste_cox, times=grade).T.to_numpy()  # (n_amostras, n_tempos)

    # ---- RSF (tunada: leaf=30, 300 arvores) ----
    print("Ajustando RSF (tunada)...")
    hp = hiperparametros_fase4()
    # em blocos de 30 arvores (memoria) - ver fase4_rsf.rsf_em_blocos
    _, sf_rsf = rsf_em_blocos(X_treino, y_treino, X_teste, grade, hp["rsf_min_samples_leaf"],
                              hp["rsf_n_estimators"])

    # ---- XGBoost-AFT ----
    print("Ajustando XGBoost-AFT...")
    # config revista apos o backtest: + ano de distribuicao, base_score = mediana KM do treino
    X_treino_xgb = montar_X_xgb(treino)
    X_teste_xgb = montar_X_xgb(teste, colunas_referencia=X_treino_xgb.columns)
    d_treino = montar_dmatrix(X_treino_xgb, dur_treino, evento_treino)
    d_teste_x = xgb.DMatrix(X_teste_xgb)
    booster = xgb.train(params_xgb(hp["xgb_base_score"]), d_treino, num_boost_round=hp["xgb_num_boost_round"])
    pred_xgb = booster.predict(d_teste_x)  # ja na escala original (exp da locacao prevista)
    log_pred = np.log(pred_xgb)
    # S(t|x) = 1 - Phi((ln(t) - ln(pred)) / scale), scale=1.0 (fixado no treino)
    sf_xgb = 1 - norm.cdf(np.subtract.outer(np.log(grade), log_pred).T, scale=1.0)
    # checagem de formula (nao e validacao empirica - e propriedade matematica
    # da lognormal por construcao): em t=pred, ln(t)-ln(pred)=0 -> S=1-Phi(0)=0,5
    print(f"Checagem de formula: S(t=pred|x) = {1 - norm.cdf(0, scale=1.0):.4f} (esperado 0,5000)")

    # ---- Brier score integrado + por tempo ----
    resultados = []
    for nome, sf in [("Cox", sf_cox), ("RSF_tunada", sf_rsf), ("XGBoost_AFT", sf_xgb)]:
        ibs = integrated_brier_score(y_treino, y_teste, sf, grade)
        _, bs_por_tempo = brier_score(y_treino, y_teste, sf, grade)
        resultados.append({"modelo": nome, "ibs": ibs, **{f"brier_{int(t)}d": b for t, b in zip(grade, bs_por_tempo)}})
        print(f"\n{nome}: IBS = {ibs:.4f}")

    resultados_df = pd.DataFrame(resultados)
    print("\n=== Resumo IBS (menor = melhor; 0,25 = chute constante 0,5) ===")
    print(resultados_df[["modelo", "ibs"]].to_string(index=False))

    resultados_df.to_csv(f"{BASE_DIR}/dados/fase4_brier_resultado.csv", index=False)
    print(f"\nSalvo: dados/fase4_brier_resultado.csv")


if __name__ == "__main__":
    main()
