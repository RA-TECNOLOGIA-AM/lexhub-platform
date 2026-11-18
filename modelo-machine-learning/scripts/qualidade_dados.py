# -*- coding: utf-8 -*-
"""
Qualidade dos dados (passo 4 da revisao, 10/11/2026). Mede, sobre os processos da coorte de
modelagem (NG + LA/AM), os problemas de cadastro que afetam o estudo, em DUAS fotos dos
mesmos processos (ids presentes nas duas):
  - "estudo":   a foto congelada vigente (coorte_comum.SNAPSHOT_DIR) - o que os modelos usam;
  - "anterior": a foto de 09/11/2026 (coorte_comum.SNAPSHOT_ANTERIOR) - mostra o efeito das
                correcoes feitas na origem entre as duas (ex.: datas de acordao do NG, 10/11).

Grava dados/qualidade_dados.json (lido por gerar_capitulo_qualidade_dados.py).

Rodar: TCC - Luiz/.venv/bin/python scripts/qualidade_dados.py
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
from lifelines import KaplanMeierFitter

sys.path.insert(0, (ML_DIR + "/scripts"))
import coorte_comum as cc  # noqa: E402

BASE_DIR = ML_DIR
PASTAS = {"estudo": cc.SNAPSHOT_DIR, "anterior": cc.SNAPSHOT_ANTERIOR}
REF = {k: cc._data_referencia(v) for k, v in PASTAS.items()}


def ids_comuns():
    """Processos da coorte de modelagem presentes nas duas fotos."""
    ids = set(pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet", columns=["id"])["id"])
    for pasta in PASTAS.values():
        ids &= set(pd.read_parquet(f"{pasta}/coorte_sobrevivencia.parquet", columns=["id"])["id"])
        ids &= set(pd.read_parquet(f"{pasta}/fase6_datas_merito.parquet", columns=["id"])["id"])
    return ids


def carregar(versao, ids):
    pasta = PASTAS[versao]
    coorte = cc.limpar_tipo_acao(pd.read_parquet(f"{pasta}/coorte_sobrevivencia.parquet"))
    datas = pd.read_parquet(f"{pasta}/fase6_datas_merito.parquet")
    d = coorte[coorte["id"].isin(ids)].merge(datas, on="id", how="left")
    for c in ("distribuicao_d", "sentenca_d", "acordao_d", "acordo_d"):
        d[c] = pd.to_datetime(d[c])
    return d


def contar(d, ref):
    s1, s2 = d["id_sentenca_merito_grau1"], d["id_acordao_merito_grau2"]
    acordao_merito = s2.notna() & (s2 != 8)
    sent, acd, dist = d["sentenca_d"], d["acordao_d"], d["distribuicao_d"]
    tipo_2g_direto = d["tipo_acao"].fillna("").str.contains("RECURSO INOMINADO|APELA", regex=True)
    r = {
        "n_processos": int(len(d)),
        # datas
        "acordao_merito_sem_data": int((acordao_merito & acd.isna()).sum()),
        "acordao_merito_total": int(acordao_merito.sum()),
        "acordao_antes_da_sentenca": int((acordao_merito & acd.notna() & sent.notna() & (acd < sent)).sum()),
        "sentenca_antes_da_distribuicao": int((sent.notna() & (sent < dist)).sum()),
        "acordao_antes_da_distribuicao": int((acd.notna() & (acd < dist)).sum()),
        "datas_no_futuro": int(((sent > ref) | (acd > ref) | (d["acordo_d"] > ref)).sum()),
        "sentenca_com_data_sem_resultado": int((sent.notna() & s1.isna()).sum()),
        "sentenca_com_resultado_sem_data": int((sent.isna() & s1.notna()).sum()),
        # estrutura
        "acordao_merito_sem_sentenca": int((acordao_merito & s1.isna()).sum()),
        "acordao_merito_sem_sentenca_tipo_2g": int((acordao_merito & s1.isna() & tipo_2g_direto).sum()),
        # campos ausentes
        "sem_valor_causa": int(d["valor_causa"].isna().sum()),
        "sem_materia": int(d["materia"].isna().sum()),
        "sem_comarca": int(d["comarca"].isna().sum()),
        "sem_competencia": int(d["competencia"].isna().sum()),
        "sem_tipo_acao": int(d["tipo_acao"].isna().sum()),
    }
    # etiquetas de acordo x data do acordo (onde ha as duas e a etiqueta diz a fase)
    ac, et = d["acordo_d"].notna(), d["etiqueta_acordo"]
    antes_acd = acd.isna() | (d["acordo_d"] <= acd)
    pre_data = ac & (sent.isna() | (d["acordo_d"] <= sent)) & antes_acd
    pos_data = ac & sent.notna() & (d["acordo_d"] > sent) & antes_acd
    for fase, mask in (("PRE", pre_data), ("POS", pos_data)):
        com = ac & (et == fase)
        r[f"etiqueta_{fase}_com_data"] = int(com.sum())
        r[f"etiqueta_{fase}_discorda_data"] = int((com & ~mask).sum())
    r["acordo_so_etiqueta"] = int((et.notna() & ~ac).sum())
    r["acordo_so_data"] = int((ac & et.isna()).sum())
    r["acordo_data_e_etiqueta"] = int((ac & et.notna()).sum())
    return r


def tendencias(d):
    """Aceleracao (mediana KM ate o desfecho por ano de distribuicao) e % censurado."""
    d = d.assign(ano=d["distribuicao_d"].dt.year, ev=d["tipo_evento_e1"] != "CENSURADO")
    out = []
    for ano, g in d[d["ano"].between(2021, 2026)].groupby("ano"):
        med = KaplanMeierFitter().fit(g["duracao_dias_e1"], g["ev"]).median_survival_time_
        out.append({"ano": int(ano), "n": int(len(g)), "pct_censurado": float(1 - g["ev"].mean()),
                    "mediana_km_dias": float(med) if np.isfinite(med) else None})
    return out


def main():
    ids = ids_comuns()
    saida = {"referencia": {k: str(v.date()) for k, v in REF.items()}, "n_ids_comuns": len(ids),
             "mesma_foto": PASTAS["estudo"] == PASTAS["anterior"]}
    for versao in ("estudo", "anterior"):
        d = carregar(versao, ids)
        saida[versao] = contar(d, REF[versao])
        if versao == "estudo":
            saida["tendencias_estudo"] = tendencias(d)
    # quantas datas mudaram entre a foto anterior (e) e a do estudo (a), mesmos ids
    e = pd.read_parquet(f"{PASTAS['anterior']}/fase6_datas_merito.parquet")[["id", "acordao_d", "sentenca_d"]]
    a = pd.read_parquet(f"{PASTAS['estudo']}/fase6_datas_merito.parquet")[["id", "acordao_d", "sentenca_d"]]
    m = e[e["id"].isin(ids)].merge(a, on="id", suffixes=("_e", "_a"))
    for c in ("acordao_d", "sentenca_d"):
        x, y = pd.to_datetime(m[f"{c}_e"]), pd.to_datetime(m[f"{c}_a"])
        saida[f"mudancas_{c}"] = {
            "preenchidas": int((x.isna() & y.notna()).sum()),
            "apagadas": int((x.notna() & y.isna()).sum()),
            "alteradas": int((x.notna() & y.notna() & (x != y)).sum()),
        }
    with open(f"{BASE_DIR}/dados/qualidade_dados.json", "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)
    lado = pd.DataFrame({"anterior": saida["anterior"], "estudo": saida["estudo"]})
    lado["diferenca"] = lado["estudo"] - lado["anterior"]
    print(lado.to_string())
    print("\nmudancas datas:", saida["mudancas_acordao_d"], saida["mudancas_sentenca_d"])
    print("\ntendencias:", pd.DataFrame(saida["tendencias_estudo"]).to_string(index=False))
    print("\nSalvo: dados/qualidade_dados.json")


if __name__ == "__main__":
    main()
