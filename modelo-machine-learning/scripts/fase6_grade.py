# -*- coding: utf-8 -*-
"""
Fase 6 - grade de combinacoes do formulario da pagina, compartilhada pelos modelos de
PROBABILIDADE (procedencia 1G/2G, acordos).

Valor de causa: cada faixa do formulario e representada por 5 pontos da distribuicao REAL
de valores do treino dentro da faixa (percentis 10/30/50/70/90), e a probabilidade da
combinacao e a MEDIA nesses 5 pontos (marginaliza o valor dentro da faixa). Antes era um
valor so (a mediana, ex.: R$ 13.119 na antiga faixa 5-20 mil) e ele caia num pico local de
acordo (NG indenizatoria R$ 10-15 mil: ~7% de acordo pre-sentenca x 3,6% na faixa toda) -
corrigido em 09/11/2026.

A mediana de dias (XGBoost-AFT, fase6_prototipo_dados.py) continua com o valor unico: o
valor de causa pesa ~3% naquele modelo e media de medianas nao e mediana.
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import numpy as np
import pandas as pd

from fase6_prototipo_dados import (
    COMARCAS, COMPETENCIAS, ESCRITORIO_PARA_ID, ESCRITORIOS, FAIXAS, MATERIAS, TIPOS, faixa_de,
)

BASE_DIR = ML_DIR
PERCENTIS = [0.10, 0.30, 0.50, 0.70, 0.90]
COLUNAS_CHAVE = ["tipo_acao", "materia", "comarca", "competencia", "escritorio", "faixa"]


def valores_por_faixa():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet", columns=["split", "valor_causa"])
    vc = df.loc[df["split"] == "treino", "valor_causa"].astype(float)
    fx = faixa_de(vc)
    grupos = {f: vc[fx == f] for f in FAIXAS}
    return {f: [float(s.quantile(q)) for q in PERCENTIS] for f, s in grupos.items()}


def montar_grade():
    """DataFrame com uma linha por (combinacao do formulario x ponto de valor da faixa)."""
    vals = valores_por_faixa()
    linhas = [(t, m, c, k, e, f, v) for t in TIPOS for m in MATERIAS for c in COMARCAS
              for k in COMPETENCIAS for e in ESCRITORIOS for f in FAIXAS for v in vals[f]]
    g = pd.DataFrame(linhas, columns=COLUNAS_CHAVE + ["valor_causa"])
    g["id_escritorio_assinante"] = g["escritorio"].map(ESCRITORIO_PARA_ID)
    return g


def ler_decisoes():
    """Decisoes de modelo/exibicao tomadas SEM o teste final (fase6_selecao_temporal.py)."""
    import json
    with open(f"{BASE_DIR}/dados/fase6_selecao_temporal.json", encoding="utf-8") as fh:
        return json.load(fh)["classificadores"]


def media_por_chave(grade, probs):
    """Media das probabilidades nos pontos de valor -> {chave 'tipo|materia|...|faixa': p}."""
    s = pd.Series(np.asarray(probs, dtype=float), index=grade.index)
    medias = s.groupby([grade[c] for c in COLUNAS_CHAVE], sort=False).mean()
    return {"|".join(k): float(v) for k, v in medias.items()}
