# -*- coding: utf-8 -*-
"""
Selecao de modelos SEM olhar o teste final (ponto 1a da revisao, 09/11/2026).

Antes, varias escolhas foram feitas olhando o conjunto de teste: a granularidade das
categorias (24 materias / 8 comarcas, no teste de 04/11), logistica x XGBoost na procedencia
2G e nos acordos (Brier no teste) e se a pagina mostra previsao, previsao relativa ou
historico. Aqui todas saem de validacao que NAO toca o teste final:

  A) GRANULARIDADE (XGBoost-AFT): backtest nas origens jul/2024 e jan/2025 (fase5_backtest),
     cujas janelas de avaliacao sao processos distribuidos em 2024-2025 - nenhum deles esta
     no teste final (distribuidos a partir de 25/03/2026). Configs: 8/8, 24/8, 24/14.
  B) CLASSIFICADORES (procedencia 1G, procedencia 2G, acordo pre, acordo pos): validacao
     temporal com janela expansiva DENTRO dos 80% mais antigos de cada populacao (o teste
     final e o resto): 3 dobras, treino = primeiros 50/60/70%, validacao = os 10% seguintes.
     Candidatos: regressao logistica x XGBoost (rodadas por early stopping no treino da
     dobra), contra a taxa base (media do treino da dobra).

Regra de exibicao, fixada ANTES de rodar:
  - modelo = o de menor Brier medio nas dobras;
  - "previsao" se esse Brier medio < Brier da taxa base; senao "relativo" se AUC medio
    >= 0,60; senao "historico".

Saida: dados/fase6_selecao_temporal.json (decisoes) e .csv (metricas por dobra). Os scripts
fase6_procedencia*.py e fase6_acordos.py leem as decisoes daqui.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase6_selecao_temporal.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import contextlib
import io
import json
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sksurv.metrics import concordance_index_censored

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import carregar_datas_merito  # noqa: E402
import coorte_comum as cc  # noqa: E402
import fase4_rsf as f4  # noqa: E402
import fase5_backtest as bt  # noqa: E402
from fase4_xgboost_aft import montar_dmatrix, montar_X_xgb, mediana_km, params_xgb  # noqa: E402
from fase6_procedencia_2g import (  # noqa: E402
    DATA_REFERENCIA, RESULTADO_1G, montar_X_2g, treinar,
)

BASE_DIR = ML_DIR
FRACOES_TREINO = [0.50, 0.60, 0.70]
FRACAO_VAL = 0.10
LIMIAR_AUC_RELATIVO = 0.60


# ------------------------------------------------------------------ A) granularidade
def avaliar_granularidade(df):
    configs = {
        "8 materias / 8 comarcas": (cc.TOP_MATERIA[:8], cc.TOP_COMARCA[:8]),
        "24 materias / 8 comarcas": (cc.TOP_MATERIA, cc.TOP_COMARCA[:8]),
        "24 materias / 14 comarcas": (cc.TOP_MATERIA, cc.TOP_COMARCA[:8] + [
            "TABATINGA", "NHAMUNDÁ", "SANTO ANTÔNIO DO IÇÁ", "PRESIDENTE FIGUEIREDO", "HUMAITÁ", "BARREIRINHA"]),
    }
    original = (f4.TOP_MATERIA, f4.TOP_COMARCA)
    linhas = []
    try:
        for nome, (mats, coms) in configs.items():
            f4.TOP_MATERIA, f4.TOP_COMARCA = mats, coms
            for t0 in bt.ORIGENS:
                tr, te = bt.preparar(df, t0)
                X_tr = montar_X_xgb(tr)
                X_te = montar_X_xgb(te, colunas_referencia=X_tr.columns)
                corte = int(len(tr) * 0.85)
                params = params_xgb(mediana_km(tr["dur"], tr["ev"]))
                b = xgb.train(params, montar_dmatrix(X_tr.iloc[:corte], tr["dur"].to_numpy()[:corte],
                                                     tr["ev"].to_numpy()[:corte]), 2000,
                              evals=[(montar_dmatrix(X_tr.iloc[corte:], tr["dur"].to_numpy()[corte:],
                                                     tr["ev"].to_numpy()[corte:]), "val")],
                              early_stopping_rounds=50, verbose_eval=False)
                final = xgb.train(params, montar_dmatrix(X_tr, tr["dur"].to_numpy(), tr["ev"].to_numpy()),
                                  b.best_iteration + 1)
                med = final.predict(xgb.DMatrix(X_te))
                dur, ev = te["dur"].to_numpy(), te["ev"].to_numpy()
                cidx = concordance_index_censored(ev, dur, -med)[0]
                erros = []
                for h in bt.HORIZONTES:
                    s = 1 - norm.cdf(np.log(h / med))
                    q = pd.qcut(s, 4, labels=False, duplicates="drop")
                    erros.append(np.mean([abs(s[q == k].mean() - bt.km_em(dur[q == k], ev[q == k], h))
                                          for k in np.unique(q)]))
                linhas.append({"config": nome, "origem": t0, "cindex": cidx, "erro_calib_medio": float(np.mean(erros))})
                print(f"  {nome:<26} {t0}: C-index {cidx:.4f} | erro calib medio (180-730d) {np.mean(erros):.3f}")
    finally:
        f4.TOP_MATERIA, f4.TOP_COMARCA = original
    res = pd.DataFrame(linhas)
    resumo = res.groupby("config")[["cindex", "erro_calib_medio"]].mean().sort_values("cindex", ascending=False)
    print("\n  Media nas 2 origens:\n  " + resumo.round(4).to_string().replace("\n", "\n  "))
    return res, resumo.index[0], resumo


# ------------------------------------------------------------------ B) classificadores
def populacoes():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet").merge(
        carregar_datas_merito(), on="id", how="left")
    for c in ("sentenca_d", "acordao_d"):
        df[c] = pd.to_datetime(df[c])
        df.loc[df[c] > DATA_REFERENCIA, c] = pd.NaT
    df["resultado_1g"] = df["id_sentenca_merito_grau1"].map(RESULTADO_1G).fillna("SEM_SENTENCA")

    p1 = df[df["id_sentenca_merito_grau1"].notna()].copy()
    p1["y"] = p1["id_sentenca_merito_grau1"].isin([1, 3]).astype(int)
    p1["data"] = p1["sentenca_d"].fillna(pd.to_datetime(p1["data_evento_e1"]))

    p2 = df[df["id_acordao_merito_grau2"].notna() & (df["id_acordao_merito_grau2"] != 8)
            & df["acordao_d"].notna()].copy()
    p2["y"] = p2["id_acordao_merito_grau2"].isin([1, 3]).astype(int)
    p2["data"] = p2["acordao_d"]

    import fase6_acordos  # importa aqui: o modulo imprime contagens ao preparar
    with contextlib.redirect_stdout(io.StringIO()):
        pre, pos = fase6_acordos.preparar()
    pre["data"], pos["data"] = pd.to_datetime(pre["data_resolucao"]), pd.to_datetime(pos["data_resolucao"])
    return {
        "procedencia_1g": (p1, False),
        "procedencia_2g": (p2, True),
        "acordo_pre": (pre, False),
        "acordo_pos": (pos, True),
    }


def avaliar_classificador(nome, pop, com_1g):
    pop = pop.sort_values("data").reset_index(drop=True)
    pre_teste = pop.iloc[: int(len(pop) * 0.80)].reset_index(drop=True)  # teste final = 20% finais
    n = len(pre_teste)
    linhas = []
    for f in FRACOES_TREINO:
        tr = pre_teste.iloc[: int(n * f)].reset_index(drop=True)
        va = pre_teste.iloc[int(n * f): int(n * (f + FRACAO_VAL))].reset_index(drop=True)
        X_tr = montar_X_2g(tr, com_1g)
        X_va = montar_X_2g(va, com_1g, colunas_referencia=X_tr.columns)
        y_tr, y_va = tr["y"].to_numpy(), va["y"].to_numpy()
        if y_va.sum() == 0 or y_va.sum() == len(y_va):
            continue
        p_log = LogisticRegression(max_iter=3000).fit(X_tr.astype(float), y_tr).predict_proba(X_va.astype(float))[:, 1]
        booster, _ = treinar(X_tr, y_tr)
        p_xgb = booster.predict(xgb.DMatrix(X_va))
        linhas.append({
            "populacao": nome, "dobra_treino_frac": f, "n_val": int(len(va)), "eventos_val": int(y_va.sum()),
            "auc_logistica": roc_auc_score(y_va, p_log), "auc_xgboost": roc_auc_score(y_va, p_xgb),
            "brier_logistica": brier_score_loss(y_va, p_log), "brier_xgboost": brier_score_loss(y_va, p_xgb),
            "brier_taxa_base": brier_score_loss(y_va, np.full(len(y_va), y_tr.mean())),
        })
    res = pd.DataFrame(linhas)
    m = res.mean(numeric_only=True)
    modelo = "logistica" if m["brier_logistica"] <= m["brier_xgboost"] else "xgboost"
    brier, auc = m[f"brier_{modelo}"], m[f"auc_{modelo}"]
    exibir = "previsao" if brier < m["brier_taxa_base"] else ("relativo" if auc >= LIMIAR_AUC_RELATIVO else "historico")
    decisao = {"modelo": modelo, "exibir": exibir, "auc_medio": float(auc), "brier_medio": float(brier),
               "brier_taxa_base_medio": float(m["brier_taxa_base"]), "dobras": int(len(res))}
    print(f"  {nome:<15} AUC log {m['auc_logistica']:.3f} / xgb {m['auc_xgboost']:.3f} | Brier log "
          f"{m['brier_logistica']:.5f} / xgb {m['brier_xgboost']:.5f} / base {m['brier_taxa_base']:.5f} "
          f"-> {modelo}, exibir: {exibir}")
    return res, decisao


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    print("=== A) Granularidade das categorias (backtest, XGBoost-AFT) ===")
    res_a, melhor, resumo = avaliar_granularidade(df)
    print(f"  -> escolhida: {melhor}")

    print("\n=== B) Classificadores (validacao temporal dentro dos 80% mais antigos) ===")
    decisoes, todas = {}, [res_a.assign(parte="granularidade")]
    for nome, (pop, com_1g) in populacoes().items():
        res, dec = avaliar_classificador(nome, pop, com_1g)
        decisoes[nome] = dec
        todas.append(res.assign(parte="classificador"))

    saida = {"granularidade": {"escolhida": melhor, "resumo": resumo.round(4).reset_index().to_dict("records")},
             "classificadores": decisoes,
             "regra": "modelo = menor Brier medio; previsao se Brier < taxa base; senao relativo se AUC >= 0,60; senao historico"}
    with open(f"{BASE_DIR}/dados/fase6_selecao_temporal.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)
    pd.concat(todas, ignore_index=True).to_csv(f"{BASE_DIR}/dados/fase6_selecao_temporal.csv", index=False)
    print("\nSalvo: dados/fase6_selecao_temporal.json e .csv")


if __name__ == "__main__":
    main()
