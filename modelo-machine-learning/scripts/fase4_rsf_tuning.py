# -*- coding: utf-8 -*-
"""
Fase 4 - ponto pendente 1: tuning de hiperparametro da RSF via cross-validation
NO TREINO (nunca toca o teste), depois reajusta com o melhor min_samples_leaf
em mais arvores e reavalia no teste - pra comparar com o resultado "palpite
unico" de fase4_rsf.py (min_samples_leaf=15, C-index teste=0,6275).

Busca pequena de proposito (ambiente lento/pouca RAM, ver fase4_rsf.py): fixa
n_estimators=100 durante a busca (rapido o suficiente pra rodar varios folds),
so sobe pra n_estimators=300 no ajuste final com o melhor parametro.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase4_rsf_tuning.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import sys
import time

import pandas as pd
from sklearn.model_selection import GridSearchCV, KFold
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv

sys.path.insert(0, (ML_DIR + "/scripts"))
from fase4_rsf import montar_X  # noqa: E402

BASE_DIR = ML_DIR


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    treino = df[df["split"] == "treino"].reset_index(drop=True)
    teste = df[df["split"] == "teste"].reset_index(drop=True)

    X_treino = montar_X(treino)
    X_teste = montar_X(teste, colunas_referencia=X_treino.columns)
    y_treino = Surv.from_arrays(
        event=(treino["tipo_evento_e1"] != "CENSURADO").to_numpy(),
        time=treino["duracao_dias_e1"].to_numpy(),
    )
    y_teste = Surv.from_arrays(
        event=(teste["tipo_evento_e1"] != "CENSURADO").to_numpy(),
        time=teste["duracao_dias_e1"].to_numpy(),
    )

    grade = {"min_samples_leaf": [5, 15, 30, 50]}
    # low_memory=True: nao guarda as curvas de sobrevivencia por folha (so o risco, que e o
    # que o C-index usa). Sem isso, leaf=5 estourou a RAM (~6,7 GB, OOM) com a coorte de
    # 04/11/2026. Brier/Fase 5 refazem o ajuste sem low_memory porque precisam das curvas.
    base = RandomSurvivalForest(n_estimators=100, min_samples_split=10, max_features="sqrt",
                                 n_jobs=2, random_state=42, low_memory=True)
    busca = GridSearchCV(base, grade, cv=KFold(n_splits=3, shuffle=True, random_state=42),
                          n_jobs=1, refit=False, verbose=2)

    t0 = time.time()
    busca.fit(X_treino, y_treino)
    print(f"\nBusca concluida em {time.time()-t0:.1f}s")

    resultados = pd.DataFrame(busca.cv_results_)[["param_min_samples_leaf", "mean_test_score", "std_test_score"]]
    resultados = resultados.sort_values("mean_test_score", ascending=False)
    print("\n=== C-index medio (3-fold CV, so no treino) por min_samples_leaf ===")
    print(resultados.to_string(index=False))

    melhor_leaf = int(resultados.iloc[0]["param_min_samples_leaf"])
    print(f"\nMelhor min_samples_leaf: {melhor_leaf}")

    print(f"\nReajustando com min_samples_leaf={melhor_leaf}, n_estimators=300 (treino inteiro)...")
    rsf_final = RandomSurvivalForest(n_estimators=300, min_samples_split=10, min_samples_leaf=melhor_leaf,
                                      max_features="sqrt", n_jobs=2, random_state=42, low_memory=True)
    t0 = time.time()
    rsf_final.fit(X_treino, y_treino)
    print(f"Ajuste final concluido em {time.time()-t0:.1f}s")

    cindex_treino = rsf_final.score(X_treino, y_treino)
    cindex_teste = rsf_final.score(X_teste, y_teste)
    print(f"\nC-index RSF tunada (treino): {cindex_treino:.4f}")
    print(f"C-index RSF tunada (teste):  {cindex_teste:.4f}")

    resultados.to_csv(f"{BASE_DIR}/dados/fase4_rsf_tuning_cv.csv", index=False)
    pd.DataFrame([{
        "melhor_min_samples_leaf": melhor_leaf, "n_estimators": 300,
        "cindex_treino": cindex_treino, "cindex_teste": cindex_teste,
    }]).to_csv(f"{BASE_DIR}/dados/fase4_rsf_tunada_metricas.csv", index=False)
    print(f"\nSalvo: dados/fase4_rsf_tuning_cv.csv, dados/fase4_rsf_tunada_metricas.csv")


if __name__ == "__main__":
    main()
