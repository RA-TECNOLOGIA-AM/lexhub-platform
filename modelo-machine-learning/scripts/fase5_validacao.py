# -*- coding: utf-8 -*-
"""
Fase 5 - Validacao: o que a Fase 4 ja cobriu (C-index, Brier Score, split
temporal) mais o que faltava explicitamente do plano original:
  (1) intervalo de confianca via bootstrap do TESTE (nao refaz o ajuste a cada
      rodada - reamostra os sujeitos do teste com reposicao e recalcula o
      C-index com os MESMOS 3 modelos ja treinados; comparacao pareada, porque
      cada rodada usa a mesma reamostragem nos tres modelos);
  (2) calibracao de verdade: probabilidade prevista vs. observada (Kaplan-Meier)
      num horizonte fixo, em grupos (quartis) de risco previsto - nao so o
      Brier Score agregado da Fase 4.

Reusa os hiperparametros ja escolhidos na Fase 4 (lidos via hiperparametros_fase4():
Cox penalizer=0.01; RSF leaf/arvores do tuning; XGBoost-AFT rodadas + base_score, com ano
de distribuicao) - a Fase 5 valida o que ja foi ajustado, nao reabre o tuning.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase5_validacao.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import gc
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from lifelines import CoxPHFitter, KaplanMeierFitter
from scipy.stats import norm
from sksurv.ensemble import RandomSurvivalForest
from sksurv.metrics import concordance_index_censored
from sksurv.util import Surv

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import hiperparametros_fase4  # noqa: E402
from fase4_rsf import montar_X, rsf_em_blocos  # noqa: E402
from fase4_xgboost_aft import montar_dmatrix, montar_X_xgb, params_xgb  # noqa: E402

BASE_DIR = ML_DIR
REF_DROP = ["tipo_INDENIZATÓRIA", "mat_Outros", "com_MANAUS", "comp_Juizado_Especial_Cível", "esc_LA"]
N_BOOTSTRAP = 500
HORIZONTE_CALIBRACAO = 90  # dias - dentro do range observado no teste (max 221d na coorte de 04/11/2026)
SEED = 42


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

    # ---- reajusta os 3 modelos finais (mesmos hiperparametros da Fase 4) ----
    print("Ajustando Cox...")
    treino_cox = X_treino.astype(float).copy()
    treino_cox["duracao"] = dur_treino
    treino_cox["evento"] = evento_treino.astype(int)
    treino_cox = treino_cox.drop(columns=REF_DROP)
    teste_cox = X_teste.astype(float).drop(columns=REF_DROP)
    cph = CoxPHFitter(penalizer=0.01)
    cph.fit(treino_cox, duration_col="duracao", event_col="evento")
    risco_cox = cph.predict_partial_hazard(teste_cox).to_numpy()  # maior = mais rapido

    # RSF em blocos: N_BLOCOS_RSF florestas menores (sementes diferentes), uma por vez,
    # descartadas logo apos prever. Uma floresta unica de 300 arvores com as curvas por
    # folha (precisa delas pra calibracao) pede ~6,4 GB e foi morta por falta de memoria
    # em 04/11/2026. E matematicamente a mesma coisa: no sksurv, risco e S(t|x) da floresta
    # sao a MEDIA das arvores (com os mesmos tempos unicos do treino), entao a media de
    # blocos de tamanho igual = floresta unica com o total de arvores.
    hp = hiperparametros_fase4()
    print(f"Ajustando RSF (tunada, leaf={hp['rsf_min_samples_leaf']}) em blocos de 30 arvores...")
    risco_rsf, _s = rsf_em_blocos(X_treino, y_treino, X_teste, [HORIZONTE_CALIBRACAO],
                                  hp["rsf_min_samples_leaf"], hp["rsf_n_estimators"], seed=SEED)
    s_rsf_horizonte = _s[:, 0]

    print("Ajustando XGBoost-AFT...")
    # config revista apos o backtest: + ano de distribuicao, base_score = mediana KM do treino
    X_treino_xgb = montar_X_xgb(treino)
    X_teste_xgb = montar_X_xgb(teste, colunas_referencia=X_treino_xgb.columns)
    d_treino = montar_dmatrix(X_treino_xgb, dur_treino, evento_treino)
    d_teste_x = xgb.DMatrix(X_teste_xgb)
    booster = xgb.train(params_xgb(hp["xgb_base_score"]), d_treino, num_boost_round=hp["xgb_num_boost_round"])
    pred_xgb = booster.predict(d_teste_x)  # tempo previsto (maior = sobrevive mais)
    risco_xgb = -pred_xgb  # inverte: maior "risco" = tempo previsto menor

    riscos = {"Cox": risco_cox, "RSF_tunada": risco_rsf, "XGBoost_AFT": risco_xgb}

    # ---- (1) bootstrap pareado do teste ----
    print(f"\nBootstrap ({N_BOOTSTRAP} reamostragens do teste, pareado nos 3 modelos)...")
    rng = np.random.RandomState(SEED)
    n = len(dur_teste)
    amostras = {nome: [] for nome in riscos}
    vitorias = {"xgb_vs_cox": 0, "xgb_vs_rsf": 0, "rsf_vs_cox": 0}
    validas = 0
    for b in range(N_BOOTSTRAP):
        idx = rng.randint(0, n, size=n)
        if evento_teste[idx].sum() == 0:
            continue
        cindices = {}
        falhou = False
        for nome, risco in riscos.items():
            try:
                cindices[nome] = concordance_index_censored(evento_teste[idx], dur_teste[idx], risco[idx])[0]
            except ZeroDivisionError:
                falhou = True
                break
        if falhou:
            continue
        for nome in riscos:
            amostras[nome].append(cindices[nome])
        vitorias["xgb_vs_cox"] += cindices["XGBoost_AFT"] > cindices["Cox"]
        vitorias["xgb_vs_rsf"] += cindices["XGBoost_AFT"] > cindices["RSF_tunada"]
        vitorias["rsf_vs_cox"] += cindices["RSF_tunada"] > cindices["Cox"]
        validas += 1

    print(f"Reamostragens validas: {validas}/{N_BOOTSTRAP}")
    resultado_ic = []
    for nome, vals in amostras.items():
        vals = np.array(vals)
        resultado_ic.append({
            "modelo": nome, "cindex_medio": vals.mean(),
            "ic_2.5%": np.percentile(vals, 2.5), "ic_97.5%": np.percentile(vals, 97.5),
        })
        print(f"{nome}: C-index = {vals.mean():.4f}  IC95% [{np.percentile(vals,2.5):.4f}, "
              f"{np.percentile(vals,97.5):.4f}]")

    print("\n=== Probabilidade empirica de vitoria (pareada, mesma reamostragem) ===")
    for chave, n_vit in vitorias.items():
        print(f"{chave}: {100*n_vit/validas:.1f}%")

    pd.DataFrame(resultado_ic).to_csv(f"{BASE_DIR}/dados/fase5_bootstrap_ic.csv", index=False)
    pd.DataFrame([{**vitorias, "n_validas": validas}]).to_csv(
        f"{BASE_DIR}/dados/fase5_bootstrap_vitorias.csv", index=False)

    # ---- (2) calibracao em horizonte fixo ----
    print(f"\n=== Calibracao em t={HORIZONTE_CALIBRACAO} dias (quartis de risco previsto) ===")

    def sobrevivencia_cox(t):
        return cph.predict_survival_function(teste_cox, times=[t]).to_numpy().flatten()

    def sobrevivencia_rsf(t):
        assert t == HORIZONTE_CALIBRACAO  # so foi pre-calculado nesse horizonte (ver blocos acima)
        return s_rsf_horizonte

    def sobrevivencia_xgb(t):
        log_pred = np.log(pred_xgb)
        return 1 - norm.cdf((np.log(t) - log_pred), scale=1.0)

    funcs_sobrevivencia = {"Cox": sobrevivencia_cox, "RSF_tunada": sobrevivencia_rsf, "XGBoost_AFT": sobrevivencia_xgb}

    linhas_calibracao = []
    for nome, func in funcs_sobrevivencia.items():
        s_prevista = func(HORIZONTE_CALIBRACAO)
        quartil = pd.qcut(s_prevista, 4, labels=False, duplicates="drop")
        print(f"\n{nome}:")
        for q in sorted(pd.unique(quartil)):
            mask = quartil == q
            kmf = KaplanMeierFitter()
            kmf.fit(dur_teste[mask], event_observed=evento_teste[mask])
            s_obs = kmf.survival_function_at_times(HORIZONTE_CALIBRACAO).iloc[0]
            s_prev_media = s_prevista[mask].mean()
            print(f"  Quartil {int(q)+1} (n={mask.sum()}): previsto={s_prev_media:.3f} | "
                  f"observado(KM)={s_obs:.3f} | diferença={s_prev_media-s_obs:+.3f}")
            linhas_calibracao.append({
                "modelo": nome, "quartil": int(q) + 1, "n": int(mask.sum()),
                "s_previsto_medio": s_prev_media, "s_observado_km": s_obs,
            })

    pd.DataFrame(linhas_calibracao).to_csv(f"{BASE_DIR}/dados/fase5_calibracao.csv", index=False)
    print(f"\nSalvo: dados/fase5_bootstrap_ic.csv, dados/fase5_bootstrap_vitorias.csv, "
          "dados/fase5_calibracao.csv")


if __name__ == "__main__":
    main()
