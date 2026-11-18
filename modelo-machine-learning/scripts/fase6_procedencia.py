# -*- coding: utf-8 -*-
"""
Fase 6 (extensao, 09/11/2026) - previsao de SUCESSO (procedencia) em 1G e 2G para a
pagina "Previsao Individualizada". O XGBoost-AFT das Fases 4-5 so preve QUANDO o
processo chega a um desfecho; aqui um classificador estima a CHANCE de o merito ser
favoravel, condicional a haver merito julgado naquela instancia:

  P(1G favoravel | ha sentenca de merito, x)   alvo: id_sentenca_merito_grau1 in (1, 3)
  P(2G favoravel | ha acordao de merito, x)    alvo: id_acordao_merito_grau2 in (1, 3)
                                               (acordao 8 = sentenca anulada fica fora)

Favoravel = procedente / parcialmente procedente COM proveito economico (mesmo criterio
do dashboard Sobrevivencia Processual e da coorte). Mesmas covariaveis (montar_X) e
mesmo split temporal da Fase 4. Validacao no teste: AUC, Brier, calibracao por decil,
contra (a) a taxa base (AUC 0,5) e (b) uma regressao logistica simples.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase6_procedencia.py
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
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

sys.path.insert(0, (ML_DIR + "/scripts"))
from fase4_rsf import montar_X  # noqa: E402
from fase6_grade import media_por_chave, montar_grade  # noqa: E402

BASE_DIR = ML_DIR
SEED = 42
PARAMS = {
    "objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist",
    "max_depth": 4, "learning_rate": 0.05, "min_child_weight": 20, "seed": SEED,
}

INSTANCIAS = {
    "1G": ("id_sentenca_merito_grau1", lambda s: s.notna()),
    "2G": ("id_acordao_merito_grau2", lambda s: s.notna() & (s != 8)),
}


def ajustar(treino, teste, col):
    """Classificador XGBoost com early stopping numa validacao interna TEMPORAL (ultimos
    15% do treino por data de distribuicao) - igual a Fase 4, nunca olha o teste."""
    treino = treino.sort_values("distribuicao_d").reset_index(drop=True)
    y_tr = treino[col].isin([1, 3]).astype(int).to_numpy()
    y_te = teste[col].isin([1, 3]).astype(int).to_numpy()
    X_tr = montar_X(treino)
    X_te = montar_X(teste, colunas_referencia=X_tr.columns)

    corte = int(len(treino) * 0.85)
    d_fit = xgb.DMatrix(X_tr.iloc[:corte], label=y_tr[:corte])
    d_val = xgb.DMatrix(X_tr.iloc[corte:], label=y_tr[corte:])
    b = xgb.train(PARAMS, d_fit, num_boost_round=2000, evals=[(d_val, "val")],
                  early_stopping_rounds=50, verbose_eval=False)
    rodadas = b.best_iteration + 1
    booster = xgb.train(PARAMS, xgb.DMatrix(X_tr, label=y_tr), num_boost_round=rodadas)
    p_te = booster.predict(xgb.DMatrix(X_te))

    logit = LogisticRegression(max_iter=2000, C=1.0).fit(X_tr.astype(float), y_tr)
    p_log = logit.predict_proba(X_te.astype(float))[:, 1]

    decis = pd.qcut(p_te, 10, labels=False, duplicates="drop")
    calib = [{"decil": int(q) + 1, "n": int((decis == q).sum()),
              "previsto": float(p_te[decis == q].mean()), "observado": float(y_te[decis == q].mean())}
             for q in sorted(np.unique(decis))]
    metricas = {
        "n_treino": int(len(treino)), "n_teste": int(len(teste)),
        "taxa_treino": float(y_tr.mean()), "taxa_teste": float(y_te.mean()),
        "rodadas": int(rodadas),
        "auc_xgb": float(roc_auc_score(y_te, p_te)), "auc_logistica": float(roc_auc_score(y_te, p_log)),
        "brier_xgb": float(brier_score_loss(y_te, p_te)), "brier_logistica": float(brier_score_loss(y_te, p_log)),
        "brier_taxa_base": float(brier_score_loss(y_te, np.full(len(y_te), y_tr.mean()))),
        "previsto_medio_teste": float(p_te.mean()),
    }
    return booster, X_tr.columns, metricas, calib


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")

    combos = montar_grade()  # 5 pontos de valor por faixa (ver fase6_grade.py)

    saida = {"metricas": {}, "calibracao": {}, "previsoes": {}}
    probs = {}
    for inst, (col, filtro) in INSTANCIAS.items():
        sub = df[filtro(df[col])]
        treino, teste = sub[sub["split"] == "treino"], sub[sub["split"] == "teste"]
        booster, colunas, metricas, calib = ajustar(treino, teste, col)
        saida["metricas"][inst] = metricas
        saida["calibracao"][inst] = calib
        print(f"\n=== {inst} ===")
        for k, v in metricas.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
        for c in calib:
            print(f"  decil {c['decil']:>2} (n={c['n']:>4}): previsto={c['previsto']:.3f} observado={c['observado']:.3f}")

        # ajuste final p/ producao: treino + teste (mesma quantidade de rodadas validada)
        y_all = sub[col].isin([1, 3]).astype(int).to_numpy()
        X_all = montar_X(sub)
        final = xgb.train(PARAMS, xgb.DMatrix(X_all, label=y_all), num_boost_round=metricas["rodadas"])
        X_c = montar_X(combos, colunas_referencia=X_all.columns)
        probs[inst] = final.predict(xgb.DMatrix(X_c))

    p1, p2 = media_por_chave(combos, probs["1G"]), media_por_chave(combos, probs["2G"])
    saida["previsoes"] = {k: [round(p1[k], 4), round(p2[k], 4)] for k in p1}

    with open(f"{BASE_DIR}/dados/fase6_procedencia.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False)
    print(f"\nSalvo: dados/fase6_procedencia.json ({len(saida['previsoes'])} combinacoes)")


if __name__ == "__main__":
    main()
