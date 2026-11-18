# -*- coding: utf-8 -*-
"""
Fase 6 (extensao, 09/11/2026) - previsao de procedencia no 2G, versao 2.

A 1a tentativa (fase6_procedencia.py) validou o 2G com o split temporal da Fase 4 (por
data de DISTRIBUICAO): o teste so tinha 1.010 acordaos - processos distribuidos em
mar-nov/2026 que ja tinham acordao, ou seja, so os excepcionalmente rapidos - e o modelo
deu AUC 0,48. Num 5-fold aleatorio o mesmo modelo deu 0,79: o sinal existe, o teste e
que era enviesado. Aqui:

  (1) split pela DATA DO ACORDAO: os 20% de acordaos mais recentes viram teste (todo
      tipo de processo, nao so os rapidos); early stopping numa validacao interna com os
      15% mais recentes do treino. Continua sendo validacao "no futuro", sem vazamento.
  (2) RESULTADO DO 1G como covariavel (procedente c/ proveito / sem proveito /
      improcedente / extinto / sem sentenca registrada - ex.: recurso inominado). Um
      processo novo ainda nao tem sentenca, entao a pagina usa isso como CENARIO.

Alvo: acordao de merito favoravel (1 ou 3 = procedente / parcialmente procedente COM
proveito economico); acordao 8 (sentenca anulada) fica fora. Compara com e sem o
resultado do 1G, contra regressao logistica e taxa base.

Rodar (depois de fase6_datas_merito.py e fase6_prototipo_dados.py):
  TCC - Luiz/.venv/bin/python scripts/fase6_procedencia_2g.py
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
from coorte_comum import carregar_datas_merito  # noqa: E402
from fase4_rsf import montar_X  # noqa: E402
from fase6_prototipo_dados import (  # noqa: E402
    COMARCAS, COMPETENCIAS, ESCRITORIO_PARA_ID, ESCRITORIOS, FAIXAS, MATERIAS, TIPOS,
)

BASE_DIR = ML_DIR
from coorte_comum import DATA_REFERENCIA  # noqa: E402  (extracao da foto; data "no futuro" = erro de cadastro)
SEED = 42
PARAMS = {
    "objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist",
    "max_depth": 4, "learning_rate": 0.05, "min_child_weight": 20, "seed": SEED,
}
RESULTADO_1G = {1: "FAV", 3: "FAV", 2: "SEM_PROVEITO", 4: "SEM_PROVEITO", 5: "IMPROCEDENTE", 7: "EXTINTO"}
CATEGORIAS_1G = ["FAV", "SEM_PROVEITO", "IMPROCEDENTE", "EXTINTO", "SEM_SENTENCA"]
CENARIOS_PAGINA = ["FAV", "IMPROCEDENTE", "EXTINTO"]  # ordem exportada no bundle


def montar_X_2g(df, com_1g, colunas_referencia=None):
    X = montar_X(df, colunas_referencia=None)
    if com_1g:
        r1 = pd.Categorical(df["resultado_1g"], categories=CATEGORIAS_1G)
        X = pd.concat([X, pd.get_dummies(r1, prefix="r1").reset_index(drop=True)], axis=1)
    if colunas_referencia is not None:
        X = X.reindex(columns=colunas_referencia, fill_value=False)
    return X


def treinar(X_tr, y_tr):
    """Early stopping nos 15% mais recentes do treino (X_tr ja ordenado por data)."""
    corte = int(len(X_tr) * 0.85)
    b = xgb.train(PARAMS, xgb.DMatrix(X_tr.iloc[:corte], label=y_tr[:corte]), num_boost_round=2000,
                  evals=[(xgb.DMatrix(X_tr.iloc[corte:], label=y_tr[corte:]), "val")],
                  early_stopping_rounds=50, verbose_eval=False)
    rodadas = b.best_iteration + 1
    return xgb.train(PARAMS, xgb.DMatrix(X_tr, label=y_tr), num_boost_round=rodadas), rodadas


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet").merge(
        carregar_datas_merito(), on="id", how="left")
    df["acordao_d"] = pd.to_datetime(df["acordao_d"])
    sub = df[df["id_acordao_merito_grau2"].notna() & (df["id_acordao_merito_grau2"] != 8)
             & df["acordao_d"].notna() & (df["acordao_d"] <= DATA_REFERENCIA)].copy()
    sub["resultado_1g"] = sub["id_sentenca_merito_grau1"].map(RESULTADO_1G).fillna("SEM_SENTENCA")
    sub["y"] = sub["id_acordao_merito_grau2"].isin([1, 3]).astype(int)
    sub = sub.sort_values("acordao_d").reset_index(drop=True)

    corte = int(len(sub) * 0.80)
    treino, teste = sub.iloc[:corte].reset_index(drop=True), sub.iloc[corte:].reset_index(drop=True)
    y_tr, y_te = treino["y"].to_numpy(), teste["y"].to_numpy()
    print(f"Acordaos de merito: {len(sub)} | treino {len(treino)} (ate {treino.acordao_d.max().date()}) | "
          f"teste {len(teste)} ({teste.acordao_d.min().date()} a {teste.acordao_d.max().date()})")
    print(f"Taxa de sucesso 2G: treino {y_tr.mean():.3f} | teste {y_te.mean():.3f}")

    resultados = {}
    for com_1g in (False, True):
        nome = "com_resultado_1g" if com_1g else "sem_resultado_1g"
        X_tr = montar_X_2g(treino, com_1g)
        X_te = montar_X_2g(teste, com_1g, colunas_referencia=X_tr.columns)
        booster, rodadas = treinar(X_tr, y_tr)
        p = booster.predict(xgb.DMatrix(X_te))
        p_log = LogisticRegression(max_iter=3000).fit(X_tr.astype(float), y_tr).predict_proba(X_te.astype(float))[:, 1]
        decis = pd.qcut(p, 10, labels=False, duplicates="drop")
        resultados[nome] = {
            "rodadas": int(rodadas),
            "auc_xgb": float(roc_auc_score(y_te, p)), "auc_logistica": float(roc_auc_score(y_te, p_log)),
            "brier_xgb": float(brier_score_loss(y_te, p)), "brier_logistica": float(brier_score_loss(y_te, p_log)),
            "brier_taxa_base": float(brier_score_loss(y_te, np.full(len(y_te), y_tr.mean()))),
            "calibracao": [{"decil": int(q) + 1, "n": int((decis == q).sum()),
                            "previsto": float(p[decis == q].mean()), "observado": float(y_te[decis == q].mean())}
                           for q in sorted(np.unique(decis))],
        }
        r = resultados[nome]
        print(f"\n=== {nome} === rodadas={r['rodadas']} | AUC xgb {r['auc_xgb']:.3f} / logistica "
              f"{r['auc_logistica']:.3f} | Brier xgb {r['brier_xgb']:.4f} / logistica {r['brier_logistica']:.4f} "
              f"/ taxa base {r['brier_taxa_base']:.4f}")
        for c in r["calibracao"]:
            print(f"  decil {c['decil']:>2} (n={c['n']:>4}): previsto={c['previsto']:.3f} observado={c['observado']:.3f}")

    # taxa observada no teste por resultado do 1G (sanidade dos cenarios)
    print("\nTeste - sucesso 2G observado por resultado do 1G:")
    print(teste.groupby("resultado_1g")["y"].agg(["size", "mean"]).round(3).to_string())

    # ---- modelo final (com resultado do 1G), treino+teste ----
    # Qual modelo: decidido SEM o teste (fase6_selecao_temporal.py, validacao temporal dentro
    # dos 80% mais antigos). Antes era escolhido pelo Brier no teste (dava logistica).
    from fase6_grade import ler_decisoes
    modelo_final = ler_decisoes()["procedencia_2g"]["modelo"]
    X_all = montar_X_2g(sub, True)
    if modelo_final == "logistica":
        lr = LogisticRegression(max_iter=3000).fit(X_all.astype(float), sub["y"].to_numpy())
        prever = lambda X: lr.predict_proba(X.astype(float))[:, 1]  # noqa: E731
    else:
        bst = xgb.train(PARAMS, xgb.DMatrix(X_all, label=sub["y"].to_numpy()),
                        num_boost_round=resultados["com_resultado_1g"]["rodadas"])
        prever = lambda X: bst.predict(xgb.DMatrix(X))  # noqa: E731
    print(f"\nModelo final (selecao temporal, sem o teste): {modelo_final}")

    from fase6_grade import media_por_chave, montar_grade
    base = montar_grade()  # 5 pontos de valor por faixa (ver fase6_grade.py)
    probs = {}
    for cen in CENARIOS_PAGINA:
        b = base.assign(resultado_1g=cen)
        probs[cen] = media_por_chave(base, prever(montar_X_2g(b, True, colunas_referencia=X_all.columns)))

    previsoes = {k: [round(probs[c][k], 4) for c in CENARIOS_PAGINA] for k in probs[CENARIOS_PAGINA[0]]}

    saida = {"cenarios": CENARIOS_PAGINA, "modelo_final": modelo_final,
             "metricas": resultados,
             "n_acordaos": int(len(sub)), "n_teste": int(len(teste)),
             "teste_de": str(teste.acordao_d.min().date()), "teste_ate": str(teste.acordao_d.max().date()),
             "previsoes": previsoes}
    with open(f"{BASE_DIR}/dados/fase6_procedencia_2g.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False)
    print(f"\nSalvo: dados/fase6_procedencia_2g.json ({len(previsoes)} combinacoes x {len(CENARIOS_PAGINA)} cenarios)")


if __name__ == "__main__":
    main()
