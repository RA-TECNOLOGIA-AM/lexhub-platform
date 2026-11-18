# -*- coding: utf-8 -*-
"""
Fase 5 (complemento, 09/11/2026) - BACKTEST com acompanhamento longo.

Problema que resolve: o teste da Fase 4/5 (processos distribuidos de mar a nov/2026) so
observa ate ~224 dias, mas as medianas previstas vao de ~150 a ~900 dias - a previsao de
prazo longo nao estava validada.

Desenho ("como se estivessemos na data de origem T0"):
  - TREINO: processos distribuidos ANTES de T0, com o desfecho CENSURADO em T0
    (evento so conta se aconteceu ate T0; duracao = min(data do evento, T0) - distribuicao).
    Nenhuma informacao posterior a T0 entra no ajuste.
  - TESTE: processos distribuidos nos 6 meses seguintes a T0, com o acompanhamento
    COMPLETO ate a extracao (09/11/2026) -> no minimo 497 (jan/2025) / 682 dias (jul/2024).
  - Hiperparametros FIXOS da Fase 4 (Cox penalizer 0,01; XGBoost-AFT normal/escala 1,0,
    profundidade 4, lr 0,05; RSF leaf=15) - so o n de rodadas do XGBoost e escolhido, por
    early stopping numa validacao interna temporal (15% mais recentes do treino). O teste
    nao e usado pra nenhuma escolha.

Metricas no teste: C-index; Brier integrado (30-730d); calibracao em 180/365/545/730 dias
(quartis de S(t) prevista x Kaplan-Meier observado); e acuracia da MEDIANA prevista
(decis da mediana prevista do XGBoost-AFT x mediana KM observada no decil).

Limitacao registrada: as listas de categorias (coorte_comum.TOP_*) foram derivadas da coorte
inteira (so frequencia, nao desfecho) - vazamento minimo e aceito.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase5_backtest.py
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
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_censored, integrated_brier_score
from sksurv.util import Surv

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import DATA_REFERENCIA  # noqa: E402
from fase4_rsf import montar_X  # noqa: E402
from fase4_xgboost_aft import montar_dmatrix  # noqa: E402

BASE_DIR = ML_DIR
# Origens: 2023 e jan/2024 foram testadas e descartadas (09/11/2026) - o treino nessas datas
# tinha 58 e 1.260 eventos (a carteira so ganha volume a partir de 2024: ~4 mil -> 13 mil
# processos/ano), C-index 0,48-0,55. Com jul/2024 e jan/2025 o treino tem 4,3-6,5 mil eventos.
ORIGENS = ["2024-07-01", "2025-01-01"]
JANELA_TESTE_MESES = 6
HORIZONTES = [180, 365, 545, 730]
GRADE_IBS = np.arange(30, 731, 30)
REF_DROP = ["tipo_INDENIZATÓRIA", "mat_Outros", "com_MANAUS", "comp_Juizado_Especial_Cível", "esc_LA"]
SEED = 42
PARAMS_XGB = {
    "objective": "survival:aft", "eval_metric": "aft-nloglik",
    "aft_loss_distribution": "normal", "aft_loss_distribution_scale": 1.0,
    "tree_method": "hist", "max_depth": 4, "learning_rate": 0.05,
    "min_child_weight": 20, "seed": SEED,
}


def preparar(df, t0):
    t0 = pd.Timestamp(t0)
    t1 = t0 + pd.DateOffset(months=JANELA_TESTE_MESES)
    dist = pd.to_datetime(df["distribuicao_d"])
    data_ev = pd.to_datetime(df["data_evento_e1"])
    evento = df["tipo_evento_e1"] != "CENSURADO"

    tr = df[dist < t0].copy()
    ev_ate_t0 = evento[tr.index] & (data_ev[tr.index] <= t0)
    fim = data_ev[tr.index].where(data_ev[tr.index] <= t0, t0)
    tr["dur"] = (fim - dist[tr.index]).dt.days.clip(lower=1)
    tr["ev"] = ev_ate_t0
    tr = tr.sort_values("distribuicao_d").reset_index(drop=True)

    te = df[(dist >= t0) & (dist < t1)].copy()
    te["dur"] = te["duracao_dias_e1"].clip(lower=1)
    te["ev"] = evento[te.index]
    te = te.reset_index(drop=True)
    return tr, te


def ano_frac(d):
    dt = pd.to_datetime(d["distribuicao_d"])
    return (dt.dt.year + (dt.dt.dayofyear - 1) / 365.25).to_numpy()


def km_em(dur, ev, t):
    kmf = KaplanMeierFitter().fit(dur, event_observed=ev)
    return float(kmf.survival_function_at_times(t).iloc[0])


def km_mediana(dur, ev):
    m = KaplanMeierFitter().fit(dur, event_observed=ev).median_survival_time_
    return float(m) if np.isfinite(m) else None


def rodar_origem(df, t0):
    tr, te = preparar(df, t0)
    X_tr = montar_X(tr)
    X_te = montar_X(te, colunas_referencia=X_tr.columns)
    y_tr = Surv.from_arrays(event=tr["ev"].to_numpy(), time=tr["dur"].to_numpy())
    dur_te, ev_te = te["dur"].to_numpy(), te["ev"].to_numpy()
    y_te = Surv.from_arrays(event=ev_te, time=dur_te)
    seguimento_min = (DATA_REFERENCIA - pd.to_datetime(te["distribuicao_d"]).max()).days
    info = {
        "origem": t0, "n_treino": int(len(tr)), "eventos_treino": int(tr["ev"].sum()),
        "n_teste": int(len(te)), "eventos_teste": int(ev_te.sum()),
        "seguimento_min_teste_dias": int(seguimento_min),
    }
    print(f"\n######## ORIGEM {t0} ########")
    print(f"Treino: {info['n_treino']} ({info['eventos_treino']} eventos ate T0) | Teste: {info['n_teste']} "
          f"({info['eventos_teste']} eventos ate hoje) | seguimento minimo do teste: {seguimento_min} dias")

    # ---- Cox ----
    d_cox = X_tr.astype(float).drop(columns=REF_DROP, errors="ignore")
    d_cox = d_cox.loc[:, d_cox.std() > 0]
    cols_cox = list(d_cox.columns)
    d_cox["duracao"], d_cox["evento"] = tr["dur"].to_numpy(), tr["ev"].astype(int).to_numpy()
    cph = CoxPHFitter(penalizer=0.01).fit(d_cox, duration_col="duracao", event_col="evento")
    X_te_cox = X_te.astype(float)[cols_cox]
    risco_cox = cph.predict_partial_hazard(X_te_cox).to_numpy()
    s_cox = lambda ts: cph.predict_survival_function(X_te_cox, times=ts).to_numpy().T  # noqa: E731

    # ---- XGBoost-AFT: config de producao x variante "ano + base_score" ----
    # Variante (09/11/2026): (a) base_score = mediana KM do treino - o modelo comeca no nivel
    # certo; sem isso, com lr 0,05, o NIVEL das previsoes depende de quantas rodadas o early
    # stopping escolhe (jul/2024 parou em 36 -> medianas 2-3x curtas demais); (b) ano de
    # distribuicao como covariavel - os processos ficaram mais rapidos (mediana ~720 dias p/
    # distribuidos em 2022, ~250 em 2024, ~190 em 2025) e o modelo precisa saber de que
    # "epoca" e o processo; num processo novo, as arvores usam o ritmo mais recente.
    def ajustar_xgb(X_a, X_b, params):
        corte = int(len(tr) * 0.85)
        d_fit = montar_dmatrix(X_a.iloc[:corte], tr["dur"].to_numpy()[:corte], tr["ev"].to_numpy()[:corte])
        d_val = montar_dmatrix(X_a.iloc[corte:], tr["dur"].to_numpy()[corte:], tr["ev"].to_numpy()[corte:])
        b = xgb.train(params, d_fit, num_boost_round=2000, evals=[(d_val, "val")],
                      early_stopping_rounds=50, verbose_eval=False)
        rod = b.best_iteration + 1
        final = xgb.train(params, montar_dmatrix(X_a, tr["dur"].to_numpy(), tr["ev"].to_numpy()), num_boost_round=rod)
        return final.predict(xgb.DMatrix(X_b)), rod

    med_xgb, rodadas = ajustar_xgb(X_tr, X_te, PARAMS_XGB)
    s_xgb = lambda ts: np.array([1 - norm.cdf(np.log(t / med_xgb)) for t in ts]).T  # noqa: E731
    info["xgb_rodadas"] = int(rodadas)

    km_treino = KaplanMeierFitter().fit(tr["dur"], event_observed=tr["ev"]).median_survival_time_
    med_xgb2, rodadas2 = ajustar_xgb(X_tr.assign(ano_dist=ano_frac(tr)), X_te.assign(ano_dist=ano_frac(te)),
                                     {**PARAMS_XGB, "base_score": float(km_treino)})
    s_xgb2 = lambda ts: np.array([1 - norm.cdf(np.log(t / med_xgb2)) for t in ts]).T  # noqa: E731
    info["xgb_ano_base_rodadas"] = int(rodadas2)
    info["km_mediana_treino"] = float(km_treino)

    # ---- RSF ----
    rsf = RandomSurvivalForest(n_estimators=200, min_samples_split=10, min_samples_leaf=15,
                               max_features="sqrt", n_jobs=2, random_state=SEED).fit(X_tr, y_tr)
    risco_rsf = rsf.predict(X_te)
    fn_rsf = rsf.predict_survival_function(X_te)
    s_rsf = lambda ts: np.array([[f(min(t, f.x[-1])) for t in ts] for f in fn_rsf])  # noqa: E731

    modelos = {"Cox": (risco_cox, s_cox), "RSF": (risco_rsf, s_rsf), "XGBoost_AFT_config_antiga": (-med_xgb, s_xgb),
               "XGBoost_AFT": (-med_xgb2, s_xgb2)}

    # grade do IBS limitada ao que o teste observa (sksurv exige t < max do teste)
    grade = GRADE_IBS[GRADE_IBS < dur_te.max()]
    linhas_metricas, linhas_calib = [], []
    for nome, (risco, s_fn) in modelos.items():
        cidx = concordance_index_censored(ev_te, dur_te, risco)[0]
        ibs = integrated_brier_score(y_tr, y_te, s_fn(grade), grade)
        linhas_metricas.append({"origem": t0, "modelo": nome, "cindex": cidx, "ibs_30_730": ibs})
        print(f"  {nome:<12} C-index {cidx:.4f} | IBS(30-{grade.max()}d) {ibs:.4f}")
        s_h = s_fn(HORIZONTES)
        for j, h in enumerate(HORIZONTES):
            q = pd.qcut(s_h[:, j], 4, labels=False, duplicates="drop")
            for k in sorted(np.unique(q)):
                m = q == k
                linhas_calib.append({
                    "origem": t0, "modelo": nome, "horizonte": h, "quartil": int(k) + 1, "n": int(m.sum()),
                    "previsto": float(s_h[m, j].mean()), "observado": km_em(dur_te[m], ev_te[m], h),
                })

    calib = pd.DataFrame(linhas_calib)
    calib["erro_abs"] = (calib["previsto"] - calib["observado"]).abs()
    resumo = calib.groupby(["modelo", "horizonte"])["erro_abs"].mean().unstack().round(3)
    print("\n  Erro absoluto medio de calibracao (quartis) por horizonte:")
    print("  " + resumo.to_string().replace("\n", "\n  "))

    # ---- acuracia da mediana prevista (quintis), nas duas configs do XGBoost-AFT ----
    linhas_med = []
    for nome, med in (("XGBoost_AFT_config_antiga", med_xgb), ("XGBoost_AFT", med_xgb2)):
        q = pd.qcut(med, 5, labels=False, duplicates="drop")
        print(f"\n  {nome} - mediana prevista x observada (KM) por quintil:")
        for k in sorted(np.unique(q)):
            m = q == k
            r = {"origem": t0, "modelo": nome, "quintil": int(k) + 1, "n": int(m.sum()),
                 "mediana_prevista": float(np.median(med[m])),
                 "mediana_km_observada": km_mediana(dur_te[m], ev_te[m])}
            linhas_med.append(r)
            obs = f"{r['mediana_km_observada']:.0f}" if r["mediana_km_observada"] else "nao atingida"
            print(f"    quintil {r['quintil']} (n={r['n']:>4}): prevista {r['mediana_prevista']:6.0f} | observada {obs}")
    return info, linhas_metricas, linhas_calib, linhas_med


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    infos, mets, cals, meds = [], [], [], []
    for t0 in ORIGENS:
        info, m, c, md = rodar_origem(df, t0)
        infos.append(info), mets.extend(m), cals.extend(c), meds.extend(md)
    pd.DataFrame(mets).to_csv(f"{BASE_DIR}/dados/fase5_backtest_metricas.csv", index=False)
    pd.DataFrame(cals).to_csv(f"{BASE_DIR}/dados/fase5_backtest_calibracao.csv", index=False)
    pd.DataFrame(meds).to_csv(f"{BASE_DIR}/dados/fase5_backtest_medianas.csv", index=False)
    with open(f"{BASE_DIR}/dados/fase5_backtest_info.json", "w", encoding="utf-8") as fh:
        json.dump(infos, fh, ensure_ascii=False, indent=2)
    print("\nSalvo: dados/fase5_backtest_{metricas,calibracao,medianas}.csv, fase5_backtest_info.json")


if __name__ == "__main__":
    main()
