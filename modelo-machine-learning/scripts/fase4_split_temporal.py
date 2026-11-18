# -*- coding: utf-8 -*-
"""
Fase 4 - passo 1: split temporal treino/teste (ANTES de qualquer ajuste de modelo).

Corta a coorte por distribuicao_d (t0, desde 04/11/2026) (nao por linha aleatoria): os ~80% de processos
distribuídos mais cedo vao pro treino, os ~20% mais recentes pro teste. Isso evita
vazamento de informacao do futuro - o mesmo cuidado que o plano original da Fase 5
ja previa, so que aplicado desde ja, pra RSF e Cox/Fine-Gray poderem ser
comparados na mesma particao.

Mesmo escopo do Cox/Fine-Gray (fase3_cox.py): NG+LA, exclui quem nao tem valor_causa.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase4_split_temporal.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import sys

import pandas as pd

BASE_DIR = ML_DIR
PCT_TREINO = 0.8

sys.path.insert(0, f"{BASE_DIR}/scripts")
from coorte_comum import carregar_coorte  # noqa: E402


def main():
    df = carregar_coorte()
    df = df[df["id_escritorio_assinante"].isin([20, 21])].copy()
    antes = len(df)
    df = df.dropna(subset=["valor_causa"]).copy()
    print(f"Descartados por falta de valor_causa: {antes - len(df)}")

    df["distribuicao_d"] = pd.to_datetime(df["distribuicao_d"])
    df = df.sort_values("distribuicao_d").reset_index(drop=True)

    corte = df["distribuicao_d"].quantile(PCT_TREINO)
    df["split"] = df["distribuicao_d"].apply(lambda d: "treino" if d < corte else "teste")

    treino = df[df["split"] == "treino"]
    teste = df[df["split"] == "teste"]

    print(f"Data de corte (quantil {PCT_TREINO:.0%}): {corte.date()}")
    print(f"Treino: {len(treino)} processos (distribuídos {treino['distribuicao_d'].min().date()} a "
          f"{treino['distribuicao_d'].max().date()})")
    print(f"Teste:  {len(teste)} processos (distribuídos {teste['distribuicao_d'].min().date()} a "
          f"{teste['distribuicao_d'].max().date()})")

    for nome, sub in [("treino", treino), ("teste", teste)]:
        print(f"\nDistribuicao de tipo_evento_e1 no {nome}:")
        print(sub["tipo_evento_e1"].value_counts(normalize=True).mul(100).round(1).to_string())

    df.to_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet", index=False)
    print(f"\nSalvo: dados/fase4_coorte_com_split.parquet (coluna 'split': treino/teste)")


if __name__ == "__main__":
    main()
