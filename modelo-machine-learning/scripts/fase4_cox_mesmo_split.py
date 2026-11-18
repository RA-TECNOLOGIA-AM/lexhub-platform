# -*- coding: utf-8 -*-
"""
Fase 4 - comparacao justa: ajusta o Cox (Fase 3) no MESMO split temporal
treino/teste usado pela RSF (fase4_split_temporal.py + fase4_rsf.py), pra
comparar C-index de teste contra C-index de teste - nao contra o C-index de
0,674 da Fase 3, que foi calculado sem split (treino = teste = coorte inteira,
favorece o Cox por "ver" os proprios dados de novo).

Reusa montar_X() de fase4_rsf.py pra garantir a MESMA matriz de covariaveis
(mesmos buckets, mesmas colunas) nos dois modelos - comparacao maca com maca.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase4_cox_mesmo_split.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import sys

import pandas as pd
from lifelines import CoxPHFitter

sys.path.insert(0, (ML_DIR + "/scripts"))
from fase4_rsf import montar_X  # noqa: E402

BASE_DIR = ML_DIR

pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    treino = df[df["split"] == "treino"].reset_index(drop=True)
    teste = df[df["split"] == "teste"].reset_index(drop=True)

    X_treino = montar_X(treino)
    X_teste = montar_X(teste, colunas_referencia=X_treino.columns)

    # lifelines quer bool/float num unico DataFrame com duration_col/event_col juntos
    treino_df = X_treino.astype(float).copy()
    treino_df["duracao"] = treino["duracao_dias_e1"].to_numpy()
    treino_df["evento"] = (treino["tipo_evento_e1"] != "CENSURADO").astype(int).to_numpy()

    teste_df = X_teste.astype(float).copy()
    teste_df["duracao"] = teste["duracao_dias_e1"].to_numpy()
    teste_df["evento"] = (teste["tipo_evento_e1"] != "CENSURADO").astype(int).to_numpy()

    # mesma colinearidade de sempre: dropar 1 categoria de referencia por dimensao
    # (aqui dropamos a mais frequente de cada bucket, igual fase3_cox.py)
    REF_DROP = [
        "tipo_INDENIZATÓRIA", "mat_Outros", "com_MANAUS", "comp_Juizado_Especial_Cível", "esc_LA",
    ]
    treino_df = treino_df.drop(columns=REF_DROP)
    teste_df = teste_df.drop(columns=REF_DROP)

    print(f"Treino: N={len(treino_df)}, eventos={int(treino_df['evento'].sum())}")
    print(f"Teste:  N={len(teste_df)}, eventos={int(teste_df['evento'].sum())}")

    cph = CoxPHFitter(penalizer=0.01)
    cph.fit(treino_df, duration_col="duracao", event_col="evento")

    cindex_treino = cph.score(treino_df, scoring_method="concordance_index")
    cindex_teste = cph.score(teste_df, scoring_method="concordance_index")

    print(f"\nC-index Cox (treino): {cindex_treino:.4f}")
    print(f"C-index Cox (teste):  {cindex_teste:.4f}")

    pd.DataFrame([{
        "modelo": "cox", "n_treino": len(treino_df), "n_teste": len(teste_df),
        "cindex_treino": cindex_treino, "cindex_teste": cindex_teste,
    }]).to_csv(f"{BASE_DIR}/dados/fase4_cox_mesmo_split_metricas.csv", index=False)
    print(f"\nSalvo: dados/fase4_cox_mesmo_split_metricas.csv")


if __name__ == "__main__":
    main()
