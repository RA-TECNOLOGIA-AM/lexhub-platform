# -*- coding: utf-8 -*-
"""
Diagnostico de generalizacao do XGBoost-AFT (13/11/2026): o modelo aprende padroes gerais
ou decora o treino? Tres testes sobre o split oficial (fase4_coorte_com_split.parquet),
mesma configuracao de producao (ano de distribuicao + base_score):

  1) CURVA POR RODADAS: C-index de treino e teste a cada numero de rodadas. Num modelo que
     decora, o gap treino-teste cresce com as rodadas e o teste cai; aqui se mede isso.
  2) CURVA DE APRENDIZADO: treina com os 10/25/50/100% processos MAIS RECENTES do treino
     (mesmas rodadas da Fase 4) e mede treino x teste. Mostra se mais dados ainda ajudam e
     de onde vem o gap (processos antigos, com acompanhamento longo, sao mais faceis de
     ordenar - inflam o C-index de treino).
  3) TESTE DE PERMUTACAO: embaralha (duracao, evento) entre os processos do treino - quebra
     qualquer relacao real com as covariaveis. O C-index no teste deve cair para ~0,5; se
     ficasse alto, haveria vazamento ou artefato.

Grava dados/diagnostico_generalizacao.json (lido por gerar_capitulo_fase5.py).

Rodar: TCC - Luiz/.venv/bin/python scripts/diagnostico_generalizacao.py
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
from sksurv.metrics import concordance_index_censored

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import hiperparametros_fase4  # noqa: E402
from fase4_xgboost_aft import mediana_km, montar_dmatrix, montar_X_xgb, params_xgb  # noqa: E402

BASE_DIR = ML_DIR
RODADAS_CURVA = [10, 25, 50, 75, 100, 150, 200, 300, 400]
FRACOES = [0.10, 0.25, 0.50, 1.00]
N_PERMUTACOES = 5
SEED = 42


def cidx(evento, duracao, pred_tempo):
    return float(concordance_index_censored(evento, duracao, -pred_tempo)[0])


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    tr = df[df["split"] == "treino"].reset_index(drop=True)
    te = df[df["split"] == "teste"].reset_index(drop=True)
    X_tr = montar_X_xgb(tr)
    X_te = montar_X_xgb(te, colunas_referencia=X_tr.columns)
    d_tr, e_tr = tr["duracao_dias_e1"].to_numpy(), (tr["tipo_evento_e1"] != "CENSURADO").to_numpy()
    d_te, e_te = te["duracao_dias_e1"].to_numpy(), (te["tipo_evento_e1"] != "CENSURADO").to_numpy()
    rodadas_prod = hiperparametros_fase4()["xgb_num_boost_round"]
    params = params_xgb(mediana_km(d_tr, e_tr))
    dm_tr, dm_te = xgb.DMatrix(X_tr), xgb.DMatrix(X_te)

    # 1) curva por rodadas
    booster = xgb.train(params, montar_dmatrix(X_tr, d_tr, e_tr), max(RODADAS_CURVA))
    curva = []
    for r in RODADAS_CURVA:
        a = cidx(e_tr, d_tr, booster.predict(dm_tr, iteration_range=(0, r)))
        t = cidx(e_te, d_te, booster.predict(dm_te, iteration_range=(0, r)))
        curva.append({"rodadas": r, "treino": a, "teste": t, "gap": a - t})
        print(f"rodadas {r:>3}: treino {a:.3f} | teste {t:.3f} | gap {a - t:.3f}")

    # 2) curva de aprendizado (processos mais recentes do treino)
    aprendizado = []
    ordenado = tr.sort_values("distribuicao_d").reset_index(drop=True)
    for f in FRACOES:
        s = ordenado.iloc[-int(len(ordenado) * f):]
        X_s = montar_X_xgb(s, colunas_referencia=X_tr.columns)
        d_s, e_s = s["duracao_dias_e1"].to_numpy(), (s["tipo_evento_e1"] != "CENSURADO").to_numpy()
        m = xgb.train(params_xgb(mediana_km(d_s, e_s)), montar_dmatrix(X_s, d_s, e_s), rodadas_prod)
        a, t = cidx(e_s, d_s, m.predict(xgb.DMatrix(X_s))), cidx(e_te, d_te, m.predict(dm_te))
        aprendizado.append({"fracao": f, "n": int(len(s)), "treino": a, "teste": t, "gap": a - t,
                            "desde": str(pd.Timestamp(s["distribuicao_d"].min()).date())})
        print(f"{f:>4.0%} ({len(s):>5}, desde {aprendizado[-1]['desde']}): treino {a:.3f} | teste {t:.3f}")

    # 3) teste de permutacao
    rng = np.random.RandomState(SEED)
    perm = []
    for _ in range(N_PERMUTACOES):
        idx = rng.permutation(len(tr))
        m = xgb.train(params, montar_dmatrix(X_tr, d_tr[idx], e_tr[idx]), rodadas_prod)
        perm.append({"treino": cidx(e_tr[idx], d_tr[idx], m.predict(dm_tr)), "teste": cidx(e_te, d_te, m.predict(dm_te))})
    t_perm = [p["teste"] for p in perm]
    print(f"permutacao ({N_PERMUTACOES}x): teste medio {np.mean(t_perm):.3f} (min {min(t_perm):.3f}, max {max(t_perm):.3f})")

    real = xgb.train(params, montar_dmatrix(X_tr, d_tr, e_tr), rodadas_prod)
    saida = {
        "rodadas_producao": rodadas_prod,
        "cindex_real": {"treino": cidx(e_tr, d_tr, real.predict(dm_tr)), "teste": cidx(e_te, d_te, real.predict(dm_te))},
        "curva_rodadas": curva,
        "curva_aprendizado": aprendizado,
        "permutacao": {"n": N_PERMUTACOES, "rodadas": perm, "teste_medio": float(np.mean(t_perm)),
                       "teste_min": float(min(t_perm)), "teste_max": float(max(t_perm)),
                       "treino_medio": float(np.mean([p["treino"] for p in perm]))},
    }
    with open(f"{BASE_DIR}/dados/diagnostico_generalizacao.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)
    print("\nSalvo: dados/diagnostico_generalizacao.json")


if __name__ == "__main__":
    main()
