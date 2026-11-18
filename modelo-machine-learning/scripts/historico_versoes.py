# -*- coding: utf-8 -*-
"""
Recalcula os numeros das VERSOES ANTERIORES que os capitulos citam como historico, em vez
de deixa-los digitados a mao (10/11/2026, passo 3 - reprodutibilidade). Grava
dados/historico_versoes.json, lido por gerar_capitulo_fase3/4/5.py.

Versoes recalculadas sobre a foto congelada (coorte_comum.SNAPSHOT_DIR):
  (a) 24 materias / 8 comarcas, XGBoost-AFT na config ANTIGA (sem ano de distribuicao, sem
      base_score) - "rodada da manha de 09/11", antes do backtest;
  (b) 24 materias / 8 comarcas, XGBoost-AFT na config REVISTA (ano + base_score) - "rodada
      da tarde de 09/11", antes do ponto 1a trocar para 14 comarcas;
  (c) Cox da Fase 3 (in-sample) com 24 materias / 8 comarcas.
E duas analises que estavam so no log da conversa:
  (d) calibracao a 90 dias por categoria nova, 8/8 x 24/14, na coorte de 04/11/2026
      (backups_fases_ampliado_24mat_14com/) - motivo do descarte inicial das comarcas;
  (e) cobertura empirica das faixas de 50% e 80% do XGBoost-AFT atual no backtest.

Os mesmos procedimentos dos scripts originais (mesmas sementes): se o valor recalculado
bater com o do log, o historico esta confirmado.

Rodar: TCC - Luiz/.venv/bin/python scripts/historico_versoes.py
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
from lifelines import CoxPHFitter, KaplanMeierFitter
from scipy.stats import norm
from sksurv.metrics import concordance_index_censored

sys.path.insert(0, (ML_DIR + "/scripts"))
import coorte_comum as cc  # noqa: E402
import fase4_rsf as f4  # noqa: E402
import fase5_backtest as bt  # noqa: E402
from fase4_xgboost_aft import PARAMS_XGB, mediana_km, montar_dmatrix, montar_X_xgb, params_xgb  # noqa: E402

BASE_DIR = ML_DIR
REF_DROP = ["tipo_INDENIZATÓRIA", "mat_Outros", "com_MANAUS", "comp_Juizado_Especial_Cível", "esc_LA"]
COMARCAS_8 = cc.TOP_COMARCA[:8]


class Granularidade:
    """Troca temporariamente as listas de categorias usadas por montar_X."""

    def __init__(self, materias, comarcas):
        self.novo = (materias, comarcas)

    def __enter__(self):
        self.antigo = (f4.TOP_MATERIA, f4.TOP_COMARCA)
        f4.TOP_MATERIA, f4.TOP_COMARCA = self.novo

    def __exit__(self, *a):
        f4.TOP_MATERIA, f4.TOP_COMARCA = self.antigo


def evento(df):
    return (df["tipo_evento_e1"] != "CENSURADO").to_numpy()


def cox_teste(tr, te):
    X_tr = f4.montar_X(tr)
    X_te = f4.montar_X(te, colunas_referencia=X_tr.columns)
    d = X_tr.astype(float).drop(columns=REF_DROP)
    d["duracao"], d["evento"] = tr["duracao_dias_e1"].to_numpy(), evento(tr).astype(int)
    cph = CoxPHFitter(penalizer=0.01).fit(d, duration_col="duracao", event_col="evento")
    return cph.predict_partial_hazard(X_te.astype(float).drop(columns=REF_DROP)).to_numpy()


def xgb_teste(tr, te, revista):
    """Mesmo procedimento do fase4_xgboost_aft.py: early stopping nos 15% mais recentes do
    treino (por data de distribuicao), reajuste no treino inteiro. revista=False = config
    antiga (sem ano de distribuicao, sem base_score)."""
    montar = montar_X_xgb if revista else f4.montar_X
    X_tr = montar(tr)
    X_te = montar(te, colunas_referencia=X_tr.columns)
    ordenado = tr.sort_values("distribuicao_d")
    corte_data = tr.loc[ordenado.index[int(len(ordenado) * 0.85)], "distribuicao_d"]
    fit = (tr["distribuicao_d"] < corte_data).to_numpy()
    dur, ev = tr["duracao_dias_e1"].to_numpy(), evento(tr)
    p_fit = params_xgb(mediana_km(dur[fit], ev[fit])) if revista else PARAMS_XGB
    p_all = params_xgb(mediana_km(dur, ev)) if revista else PARAMS_XGB
    b = xgb.train(p_fit, montar_dmatrix(X_tr[fit].reset_index(drop=True), dur[fit], ev[fit]), 2000,
                  evals=[(montar_dmatrix(X_tr[~fit].reset_index(drop=True), dur[~fit], ev[~fit]), "val")],
                  early_stopping_rounds=50, verbose_eval=False)
    final = xgb.train(p_all, montar_dmatrix(X_tr, dur, ev), num_boost_round=b.best_iteration + 1)
    return final.predict(xgb.DMatrix(X_te)), b.best_iteration + 1


def vitorias_bootstrap(ev, dur, risco_a, risco_b, n=500, seed=42):
    """% de reamostragens em que A tem C-index maior que B (mesmo laco/semente da Fase 5)."""
    rng = np.random.RandomState(seed)
    vit = validas = 0
    for _ in range(n):
        idx = rng.randint(0, len(dur), size=len(dur))
        if ev[idx].sum() == 0:
            continue
        try:
            ca = concordance_index_censored(ev[idx], dur[idx], risco_a[idx])[0]
            cb = concordance_index_censored(ev[idx], dur[idx], risco_b[idx])[0]
        except ZeroDivisionError:
            continue
        vit += ca > cb
        validas += 1
    return 100 * vit / validas


def cox_fase3_insample():
    """Cox da Fase 3 (coorte inteira NG+LA, in-sample), mesma montagem do fase3_cox.py."""
    df = cc.carregar_coorte()
    df = df[df["id_escritorio_assinante"].isin([20, 21])].dropna(subset=["valor_causa"]).copy()
    df["duracao"] = df["duracao_dias_e1"].astype(float)
    df["evento"] = (df["tipo_evento_e1"] != "CENSURADO").astype(int)
    b = {"tipo": cc.bucket(df["tipo_acao"], cc.TOP_TIPO_ACAO), "mat": cc.bucket(df["materia"], cc.TOP_MATERIA),
         "com": cc.bucket(df["comarca"], COMARCAS_8), "comp": cc.bucket(df["competencia"], cc.TOP_COMPETENCIA)}
    dummies = [pd.get_dummies(s, prefix=p).drop(columns=[f"{p}_{s.value_counts().idxmax()}"]) for p, s in b.items()]
    esc = pd.get_dummies(df["id_escritorio_assinante"].map({20: "NG", 21: "LA"}), prefix="esc", drop_first=True)
    X = pd.concat([df[["duracao", "evento"]], np.log1p(df["valor_causa"].astype(float).clip(lower=0)).rename("lv"),
                   *dummies, esc], axis=1)
    X.columns = [c.replace(" ", "_") for c in X.columns]
    return float(CoxPHFitter(penalizer=0.01).fit(X, duration_col="duracao", event_col="evento").concordance_index_)


def calibracao_categorias_041126():
    """Erro de calibracao a 90 dias por categoria NOVA, 8/8 x 24/14 (config antiga do XGB),
    na coorte/split de 04/11/2026 - a analise que levou a descartar as comarcas novas."""
    pasta = f"{BASE_DIR}/backups_fases_ampliado_24mat_14com"
    df = pd.read_parquet(f"{pasta}/fase4_coorte_com_split.parquet")
    tr, te = df[df["split"] == "treino"].reset_index(drop=True), df[df["split"] == "teste"].reset_index(drop=True)
    r_8 = int(pd.read_csv(f"{BASE_DIR}/backups_fases_pre_ampliacao/fase4_xgboost_metricas.csv")["best_iteration"][0]) + 1
    r_24 = int(pd.read_csv(f"{pasta}/fase4_xgboost_metricas.csv")["best_iteration"][0]) + 1
    preds = {}
    for nome, mats, coms, rod in (("8/8", cc.TOP_MATERIA[:8], COMARCAS_8, r_8),
                                  ("24/14", cc.TOP_MATERIA, cc.TOP_COMARCA, r_24)):
        with Granularidade(mats, coms):
            X_tr = f4.montar_X(tr)
            X_te = f4.montar_X(te, colunas_referencia=X_tr.columns)
            b = xgb.train(PARAMS_XGB, montar_dmatrix(X_tr, tr["duracao_dias_e1"].to_numpy(), evento(tr)), rod)
            preds[nome] = b.predict(xgb.DMatrix(X_te))
    dur, ev = te["duracao_dias_e1"].to_numpy(), evento(te)
    s90 = {k: 1 - norm.cdf(np.log(90 / v)) for k, v in preds.items()}
    linhas = []
    for col, cats in (("materia", cc.TOP_MATERIA[8:]), ("comarca", cc.TOP_COMARCA[8:])):
        for cat in cats:
            m = (te[col] == cat).to_numpy()
            if m.sum() < 80:
                continue
            obs = float(KaplanMeierFitter().fit(dur[m], ev[m]).survival_function_at_times(90).iloc[0])
            linhas.append({"campo": col, "categoria": cat, "n_teste": int(m.sum()), "s90_observado": obs,
                           "erro_8_8": float(s90["8/8"][m].mean() - obs),
                           "erro_24_14": float(s90["24/14"][m].mean() - obs)})
    t = pd.DataFrame(linhas)
    resumo = {}
    for col in ("materia", "comarca"):
        s = t[t["campo"] == col]
        resumo[col] = {k: float(np.average(s[f"erro_{k.replace('/', '_')}"].abs(), weights=s["n_teste"]))
                       for k in ("8/8", "24/14")}
    return t.to_dict("records"), resumo


def cobertura_faixas_backtest():
    """Fracao dos processos reais dentro das faixas de 50% (P25-P75) e 80% (P10-P90) do
    XGBoost-AFT atual, no backtest. z = ln(T / mediana prevista) ~ N(0,1) se calibrado; KM
    de z (transformacao monotona por processo preserva a censura)."""
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    out = {}
    for t0 in bt.ORIGENS:
        tr, te = bt.preparar(df, t0)
        X_tr = montar_X_xgb(tr)
        X_te = montar_X_xgb(te, colunas_referencia=X_tr.columns)
        p = params_xgb(mediana_km(tr["dur"], tr["ev"]))
        c = int(len(tr) * 0.85)
        b = xgb.train(p, montar_dmatrix(X_tr.iloc[:c], tr["dur"].to_numpy()[:c], tr["ev"].to_numpy()[:c]), 2000,
                      evals=[(montar_dmatrix(X_tr.iloc[c:], tr["dur"].to_numpy()[c:], tr["ev"].to_numpy()[c:]), "v")],
                      early_stopping_rounds=50, verbose_eval=False)
        med = xgb.train(p, montar_dmatrix(X_tr, tr["dur"].to_numpy(), tr["ev"].to_numpy()),
                        b.best_iteration + 1).predict(xgb.DMatrix(X_te))
        z = np.log(te["dur"].to_numpy() / med) + 20  # desloca p/ positivo (KM exige tempo > 0)
        km = KaplanMeierFitter().fit(z, te["ev"].to_numpy())
        s = lambda v: float(km.survival_function_at_times(v + 20).iloc[0])  # noqa: E731
        out[t0] = {"faixa_50": s(-0.6745) - s(0.6745), "faixa_80": s(-1.2816) - s(1.2816)}
    return out


def main():
    split = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    tr = split[split["split"] == "treino"].reset_index(drop=True)
    te = split[split["split"] == "teste"].reset_index(drop=True)
    dur, ev = te["duracao_dias_e1"].to_numpy(), evento(te)

    saida = {}
    with Granularidade(cc.TOP_MATERIA, COMARCAS_8):
        risco_cox = cox_teste(tr, te)
        med_antiga, rod_antiga = xgb_teste(tr, te, revista=False)
        med_revista, rod_revista = xgb_teste(tr, te, revista=True)
    c = lambda r: float(concordance_index_censored(ev, dur, r)[0])  # noqa: E731
    saida["24mat_8com_config_antiga"] = {
        "descricao": "24 materias / 8 comarcas, XGBoost-AFT sem ano de distribuicao e sem base_score (09/11 manha)",
        "cindex_teste_xgb": c(-med_antiga), "rodadas_xgb": rod_antiga,
        "pct_vitorias_xgb_vs_cox": vitorias_bootstrap(ev, dur, -med_antiga, risco_cox),
    }
    saida["24mat_8com_config_revista"] = {
        "descricao": "24 materias / 8 comarcas, XGBoost-AFT com ano + base_score (09/11 tarde, antes do ponto 1a)",
        "cindex_teste_xgb": c(-med_revista), "cindex_teste_cox": c(risco_cox), "rodadas_xgb": rod_revista,
        "pct_vitorias_xgb_vs_cox": vitorias_bootstrap(ev, dur, -med_revista, risco_cox),
    }
    saida["fase3_cox_24mat_8com_insample"] = {"cindex": cox_fase3_insample()}
    cats, resumo = calibracao_categorias_041126()
    saida["calibracao_categorias_041126"] = {"por_categoria": cats, "erro_abs_medio_ponderado": resumo}
    saida["cobertura_faixas_backtest"] = cobertura_faixas_backtest()

    with open(f"{BASE_DIR}/dados/historico_versoes.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "por_categoria"} for k, v in saida.items()},
                     ensure_ascii=False, indent=1))
    print("\nSalvo: dados/historico_versoes.json")


if __name__ == "__main__":
    main()
