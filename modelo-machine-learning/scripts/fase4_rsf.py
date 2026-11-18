# -*- coding: utf-8 -*-
"""
Fase 4 - passo 2: ajusta a Random Survival Forest no TREINO (split temporal ja
feito em fase4_split_temporal.py), avalia no TESTE, e compara com o C-index do
Cox (Fase 3) na mesma coorte/escopo (NG+LA, mesmas covariaveis bucketizadas).

Evento/duracao: mesma definicao all-cause do Cox (fase3_cox.py) - qualquer
desfecho vs. censurado, duracao_dias_e1. NAO e o analogo do Fine-Gray (RSF do
scikit-survival nao tem riscos competitivos nativo) - fica registrado como
limitacao, igual documentado no capitulo da Fase 3 pra outros pontos.

Buckets de tipo_acao/materia/comarca/competencia: os MESMOS fixados em
fase3_cox.py (derivados da coorte inteira, nao so do treino) - mantido assim
por consistencia com o resto do projeto; e uma simplificacao menor ja aceita
antes (mesma lista usada no Cox e no Fine-Gray).

Ambiente tem pouca RAM (~9,6GB, compartilhada com VS Code/vite/outros processos);
n_jobs=-1 com 500 arvores OOM-matou o processo (exit 137) na primeira tentativa.
Rodar com poucos jobs e testar o tempo/memoria antes de subir a escala.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase4_rsf.py [n_estimators] [n_jobs]
  ex.: .venv/bin/python scripts/fase4_rsf.py 50 2      (teste rapido)
       .venv/bin/python scripts/fase4_rsf.py 500 2     (rodada final)
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import sys
import time

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sksurv.ensemble import RandomSurvivalForest
from sksurv.util import Surv

pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")

BASE_DIR = ML_DIR

sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import (  # noqa: E402
    TOP_COMARCA, TOP_COMPETENCIA, TOP_MATERIA, TOP_TIPO_ACAO, bucket,
)


def montar_X(df, colunas_referencia=None):
    """One-hot das covariaveis bucketizadas. Se colunas_referencia for passado
    (as colunas do treino), reindexa o teste pra ter exatamente as mesmas colunas
    (categoria ausente no teste vira 0 em vez de quebrar o alinhamento)."""
    df = df.copy()
    df["tipo_acao_b"] = bucket(df["tipo_acao"], TOP_TIPO_ACAO)
    df["materia_b"] = bucket(df["materia"], TOP_MATERIA)
    df["comarca_b"] = bucket(df["comarca"], TOP_COMARCA)
    df["competencia_b"] = bucket(df["competencia"], TOP_COMPETENCIA)
    df["escritorio"] = df["id_escritorio_assinante"].map({20: "NG", 21: "LA"})
    df["log_valor_causa"] = np.log1p(df["valor_causa"].astype(float).clip(lower=0))

    dummies = pd.concat([
        pd.get_dummies(df["tipo_acao_b"], prefix="tipo"),
        pd.get_dummies(df["materia_b"], prefix="mat"),
        pd.get_dummies(df["comarca_b"], prefix="com"),
        pd.get_dummies(df["competencia_b"], prefix="comp"),
        pd.get_dummies(df["escritorio"], prefix="esc"),
    ], axis=1)
    dummies.columns = [c.replace(" ", "_") for c in dummies.columns]
    X = pd.concat([df[["log_valor_causa"]].reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)

    if colunas_referencia is not None:
        X = X.reindex(columns=colunas_referencia, fill_value=False)
    return X


def rsf_em_blocos(X_treino, y_treino, X_teste, tempos, min_samples_leaf, n_estimators,
                  arvores_por_bloco=30, seed=42, n_jobs=2):
    """RSF ajustada em BLOCOS de florestas pequenas (sementes seed, seed+1, ...), cada uma
    descartada logo apos prever - p/ caber na memoria quando as curvas de sobrevivencia sao
    necessarias (Brier, calibracao). No sksurv o risco e S(t|x) da floresta sao a MEDIA das
    arvores (mesmos tempos unicos do treino), entao a media de blocos de tamanho igual e a
    mesma coisa que uma floresta unica com o total de arvores.
    10/11/2026: com min_samples_leaf=5 (escolhido pelo tuning na foto final) uma floresta de
    300 arvores com curvas estourou a memoria (Brier morto apos 54 min) - blocos de 30.
    Retorna (risco medio [n_teste], S(tempos) medio [n_teste, len(tempos)])."""
    import gc
    n_blocos = max(1, n_estimators // arvores_por_bloco)
    risco = np.zeros(len(X_teste))
    surv = np.zeros((len(X_teste), len(tempos)))
    for b in range(n_blocos):
        rsf = RandomSurvivalForest(n_estimators=arvores_por_bloco, min_samples_split=10,
                                   min_samples_leaf=min_samples_leaf, max_features="sqrt",
                                   n_jobs=n_jobs, random_state=seed + b)
        rsf.fit(X_treino, y_treino)
        risco += rsf.predict(X_teste) / n_blocos
        surv += np.vstack([fn(np.minimum(tempos, fn.x[-1])) for fn in rsf.predict_survival_function(X_teste)]) / n_blocos
        del rsf
        gc.collect()
    return risco, surv


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    treino = df[df["split"] == "treino"].reset_index(drop=True)
    teste = df[df["split"] == "teste"].reset_index(drop=True)

    X_treino = montar_X(treino)
    X_teste = montar_X(teste, colunas_referencia=X_treino.columns)

    evento_treino = (treino["tipo_evento_e1"] != "CENSURADO").to_numpy()
    evento_teste = (teste["tipo_evento_e1"] != "CENSURADO").to_numpy()
    y_treino = Surv.from_arrays(event=evento_treino, time=treino["duracao_dias_e1"].to_numpy())
    y_teste = Surv.from_arrays(event=evento_teste, time=teste["duracao_dias_e1"].to_numpy())

    print(f"Treino: N={len(X_treino)}, eventos={evento_treino.sum()} ({evento_treino.mean():.1%})")
    print(f"Teste:  N={len(X_teste)}, eventos={evento_teste.sum()} ({evento_teste.mean():.1%})")
    print(f"Covariaveis: {list(X_treino.columns)}")

    n_estimators = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    n_jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    print(f"\nConfig: n_estimators={n_estimators}, n_jobs={n_jobs} "
          "(ambiente com pouca RAM - ver nota no cabecalho se precisar ajustar)")

    rsf = RandomSurvivalForest(
        n_estimators=n_estimators,
        min_samples_split=10,
        min_samples_leaf=15,
        max_features="sqrt",
        n_jobs=n_jobs,
        random_state=42,
        low_memory=True,  # so risco (C-index/permutation); curvas nao sao usadas aqui
    )

    t0 = time.time()
    rsf.fit(X_treino, y_treino)
    print(f"\nAjuste concluido em {time.time()-t0:.1f}s")

    cindex_treino = rsf.score(X_treino, y_treino)
    cindex_teste = rsf.score(X_teste, y_teste)
    print(f"\nC-index (treino): {cindex_treino:.4f}")
    print(f"C-index (teste):  {cindex_teste:.4f}")

    # sksurv.RandomSurvivalForest nao implementa feature_importances_ (impureza) -
    # usa permutation importance (queda no C-index ao embaralhar cada coluna).
    # rsf.predict() e caro (escala com n_trees x n_samples: ~4,7s pra 50 arvores x
    # 8033 linhas no teste completo - pra 500 arvores seria ~45s POR chamada, e
    # permutation_importance faz 1 + n_repeats x n_features chamadas). Por isso:
    #   (a) n_jobs=1 aqui de proposito - com >1, joblib falhou ao tentar "picklar"
    #       a RSF pra mandar pros processos workers (PicklingError);
    #   (b) roda numa AMOSTRA do teste (SUBSAMPLE_PERM linhas), nao no teste
    #       inteiro - o C-index "oficial" do modelo (cindex_teste acima) ja foi
    #       calculado no teste completo antes disso, isso aqui e so pra
    #       ranquear importancia relativa de variavel, nao precisa do dado todo.
    SUBSAMPLE_PERM = min(2000, len(X_teste))
    N_REPEATS_PERM = 3
    idx_sample = np.random.RandomState(42).choice(len(X_teste), size=SUBSAMPLE_PERM, replace=False)
    X_teste_sample = X_teste.iloc[idx_sample]
    y_teste_sample = y_teste[idx_sample]

    t1 = time.time()
    perm = permutation_importance(
        rsf, X_teste_sample, y_teste_sample, n_repeats=N_REPEATS_PERM, random_state=42, n_jobs=1,
    )
    print(f"Permutation importance (amostra de {SUBSAMPLE_PERM}, {N_REPEATS_PERM} repeticoes) "
          f"calculada em {time.time()-t1:.1f}s")
    importancias = pd.Series(perm.importances_mean, index=X_treino.columns).sort_values(ascending=False)
    print("\n=== IMPORTANCIA DE VARIAVEL (permutation importance, queda no C-index) ===")
    print(importancias.to_string())

    importancias.to_frame("importancia").to_csv(f"{BASE_DIR}/dados/fase4_rsf_importancia.csv")
    pd.DataFrame([{
        "n_estimators": n_estimators, "min_samples_leaf": 15,
        "n_treino": len(X_treino), "n_teste": len(X_teste),
        "eventos_treino": int(evento_treino.sum()), "eventos_teste": int(evento_teste.sum()),
        "cindex_treino": cindex_treino, "cindex_teste": cindex_teste,
    }]).to_csv(f"{BASE_DIR}/dados/fase4_rsf_metricas.csv", index=False)
    print(f"\nSalvo: dados/fase4_rsf_importancia.csv, dados/fase4_rsf_metricas.csv")


if __name__ == "__main__":
    main()
