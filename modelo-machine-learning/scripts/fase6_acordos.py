# -*- coding: utf-8 -*-
"""
Fase 6 (extensao, 09/11/2026) - previsao de ACORDO pre e pos-sentenca para a pagina
"Previsao Individualizada" (linha secundaria dos cards de procedencia 1G/2G).

Mesma regra do dashboard Sobrevivencia Processual (tipo_acordo em queries.py), com as
datas de fase6_datas_merito.py:
  fonte do acordo: acordo_fechado (com data) OU etiqueta de acordo (so etiqueta: fase pelo
  nome ou pela situacao do processo - ver preparar())
  pre-sentenca = acordo antes de qualquer sentenca (e antes do acordao)
  pos-sentenca = acordo depois da sentenca e antes do acordao (processo ja em 2G)
  (acordo depois do acordao = fase de execucao, fora deste escopo)

Probabilidades CONDICIONAIS, no mesmo formato da procedencia:
  PRE: entre os processos que se resolveram no 1G (sentenca OU acordo pre), P(acordo)
  POS: entre os que tiveram sentenca e depois se resolveram (acordao de merito OU acordo
       pos), P(acordo) - com o resultado do 1G como covariavel/cenario (1G procedente ->
       ~17% fecham acordo; improcedente -> ~1%).

Evento raro (1.479 acordos em 47.666 processos) - validacao no teste temporal pela data
da resolucao (20% mais recentes), regressao logistica x XGBoost x taxa base; o modelo
final e o de menor Brier no teste.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase6_acordos.py
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import carregar_datas_merito  # noqa: E402
from fase6_procedencia_2g import (  # noqa: E402
    CENARIOS_PAGINA, DATA_REFERENCIA, PARAMS, RESULTADO_1G, montar_X_2g, treinar,
)
from fase6_grade import ler_decisoes, media_por_chave, montar_grade  # noqa: E402
from fase6_prototipo_dados import ESCRITORIO_PARA_ID, TIPOS, faixa_de  # noqa: E402

BASE_DIR = ML_DIR


def preparar():
    d = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet").merge(
        carregar_datas_merito(), on="id", how="left")
    for c in ("sentenca_d", "acordao_d", "acordo_d"):
        d[c] = pd.to_datetime(d[c])
        d.loc[d[c] > DATA_REFERENCIA, c] = pd.NaT  # data "no futuro" = erro de cadastro
    d["resultado_1g"] = d["id_sentenca_merito_grau1"].map(RESULTADO_1G).fillna("SEM_SENTENCA")
    ac = d["acordo_d"].notna()
    antes_acordao = d["acordao_d"].isna() | (d["acordo_d"] <= d["acordao_d"])
    pre_data = ac & (d["sentenca_d"].isna() | (d["acordo_d"] <= d["sentenca_d"])) & antes_acordao
    pos_data = ac & d["sentenca_d"].notna() & (d["acordo_d"] > d["sentenca_d"]) & antes_acordao
    acordao_merito = (d["acordao_d"].notna() & d["sentenca_d"].notna() & (d["acordao_d"] >= d["sentenca_d"])
                      & d["id_acordao_merito_grau2"].notna() & (d["id_acordao_merito_grau2"] != 8))

    # Acordo SO por etiqueta (sem acordo_fechado; 09/11/2026): fase pelo nome da etiqueta
    # quando ela diz; etiqueta generica -> sem sentenca de MERITO = pre (sentenca sem merito
    # costuma ser a homologacao do proprio acordo); com sentenca de merito e sem acordao de
    # merito = pos; com acordao = ja na execucao (fora, igual ao acordo pos-acordao com data).
    et = d["etiqueta_acordo"]
    so_etiqueta = et.notna() & ~ac
    tem_merito_1g = d["id_sentenca_merito_grau1"].notna()
    pre_et = so_etiqueta & ((et == "PRE") | ((et == "GENERICA") & ~tem_merito_1g & ~acordao_merito))
    pos_et = so_etiqueta & ((et == "POS") | ((et == "GENERICA") & tem_merito_1g & ~acordao_merito)) & ~pre_et
    pre, pos = pre_data | pre_et, pos_data | pos_et
    print(f"Acordos pre: {pre_data.sum()} por data + {pre_et.sum()} so etiqueta | "
          f"pos: {pos_data.sum()} por data + {pos_et.sum()} so etiqueta")
    # conferencia: onde ha data E etiqueta com fase no nome, as duas regras concordam?
    for fase, mask in (("PRE", pre_data), ("POS", pos_data)):
        com_nome = ac & et.isin(["PRE", "POS"])
        print(f"  etiqueta {fase} x data: {((et == fase) & mask & com_nome).sum()} concordam / "
              f"{((et == fase) & ~mask & com_nome).sum()} discordam")
    # data de resolucao p/ o split quando so ha etiqueta: data do evento E1 da coorte
    # (ultima movimentacao/merito) - proxy, a etiqueta nao tem data confiavel
    d["acordo_d"] = d["acordo_d"].fillna(pd.to_datetime(d["data_evento_e1"]).where(so_etiqueta))

    pop_pre = d[pre | d["sentenca_d"].notna()].copy()
    pop_pre["y"] = pre[pop_pre.index].astype(int)
    pop_pre["data_resolucao"] = np.where(pop_pre["y"] == 1, pop_pre["acordo_d"], pop_pre["sentenca_d"])

    pop_pos = d[pos | acordao_merito].copy()
    pop_pos["y"] = pos[pop_pos.index].astype(int)
    pop_pos["data_resolucao"] = np.where(pop_pos["y"] == 1, pop_pos["acordo_d"], pop_pos["acordao_d"])
    return pop_pre, pop_pos


def avaliar(pop, com_1g, nome):
    pop = pop.sort_values("data_resolucao").reset_index(drop=True)
    corte = int(len(pop) * 0.80)
    tr, te = pop.iloc[:corte].reset_index(drop=True), pop.iloc[corte:].reset_index(drop=True)
    X_tr = montar_X_2g(tr, com_1g)
    X_te = montar_X_2g(te, com_1g, colunas_referencia=X_tr.columns)
    y_tr, y_te = tr["y"].to_numpy(), te["y"].to_numpy()
    booster, rodadas = treinar(X_tr, y_tr)
    p_xgb = booster.predict(xgb.DMatrix(X_te))
    p_log = LogisticRegression(max_iter=3000).fit(X_tr.astype(float), y_tr).predict_proba(X_te.astype(float))[:, 1]
    m = {
        "n_treino": int(len(tr)), "n_teste": int(len(te)),
        "eventos_treino": int(y_tr.sum()), "eventos_teste": int(y_te.sum()),
        "taxa_treino": float(y_tr.mean()), "taxa_teste": float(y_te.mean()),
        "teste_de": str(pd.Timestamp(te["data_resolucao"].min()).date()),
        "auc_xgb": float(roc_auc_score(y_te, p_xgb)), "auc_logistica": float(roc_auc_score(y_te, p_log)),
        "brier_xgb": float(brier_score_loss(y_te, p_xgb)), "brier_logistica": float(brier_score_loss(y_te, p_log)),
        "brier_taxa_base": float(brier_score_loss(y_te, np.full(len(y_te), y_tr.mean()))),
        "previsto_medio_xgb": float(p_xgb.mean()), "previsto_medio_logistica": float(p_log.mean()),
        "rodadas_xgb": int(rodadas),
    }
    m["modelo_final"] = "logistica" if m["brier_logistica"] <= m["brier_xgb"] else "xgboost"
    print(f"\n=== {nome} === treino {m['n_treino']} ({m['eventos_treino']} acordos) | teste {m['n_teste']} "
          f"({m['eventos_teste']} acordos, desde {m['teste_de']})")
    print(f"  taxa treino {m['taxa_treino']:.3f} | teste {m['taxa_teste']:.3f}")
    print(f"  AUC  xgb {m['auc_xgb']:.3f} | logistica {m['auc_logistica']:.3f}")
    print(f"  Brier xgb {m['brier_xgb']:.5f} | logistica {m['brier_logistica']:.5f} | taxa base {m['brier_taxa_base']:.5f}")
    print(f"  previsto medio xgb {m['previsto_medio_xgb']:.3f} | logistica {m['previsto_medio_logistica']:.3f} "
          f"-> final: {m['modelo_final']}")
    if com_1g:
        te = te.assign(p=p_log if m["modelo_final"] == "logistica" else p_xgb)
        print(te.groupby("resultado_1g")[["p", "y"]].agg(["mean"]).round(3).to_string())
    return m


def ajustar_final(pop, com_1g, modelo, rodadas):
    X = montar_X_2g(pop, com_1g)
    y = pop["y"].to_numpy()
    if modelo == "logistica":
        lr = LogisticRegression(max_iter=3000).fit(X.astype(float), y)
        return X.columns, lambda Xn: lr.predict_proba(Xn.astype(float))[:, 1]
    b = xgb.train(PARAMS, xgb.DMatrix(X, label=y), num_boost_round=rodadas)
    return X.columns, lambda Xn: b.predict(xgb.DMatrix(Xn))


def main():
    pop_pre, pop_pos = preparar()
    m_pre = avaliar(pop_pre, False, "ACORDO PRE-SENTENCA")
    m_pos = avaliar(pop_pos, True, "ACORDO POS-SENTENCA (com resultado do 1G)")

    base = montar_grade()  # 5 pontos de valor por faixa (ver fase6_grade.py)

    # Acordo PRE: modelo ordena bem (AUC ~0,69) mas o NIVEL depende da epoca (campanhas de
    # acordo: pico de 7% no fim de 2024, 0,8% no 2o sem/2026) e nao supera a taxa base em
    # Brier. Decisao 09/11/2026: a pagina mostra o risco RELATIVO do perfil = p(perfil) /
    # media prevista dos processos resolvidos nos ultimos 12 meses, e o % aproximado =
    # relativo x taxa observada nesses 12 meses. Sempre XGBoost aqui (ordenacao igual a da
    # logistica, Brier bruto melhor).
    # modelo e forma de exibicao decididos SEM o teste (fase6_selecao_temporal.py); a
    # referencia de 12 meses continua sendo gravada (usada so se exibir == "relativo")
    decisoes = ler_decisoes()
    m_pre["modelo_final"] = decisoes["acordo_pre"]["modelo"]
    m_pos["modelo_final"] = decisoes["acordo_pos"]["modelo"]
    cols_pre, prever_pre = ajustar_final(pop_pre, False, m_pre["modelo_final"], m_pre["rodadas_xgb"])
    p_pre = media_por_chave(base, prever_pre(montar_X_2g(base, False, colunas_referencia=cols_pre)))
    # referencia POR ESCRITORIO (NG fecha ~10x mais acordo pre que LA - "x a media" do
    # proprio escritorio e o que faz sentido pra quem le)
    recente = pop_pre[pd.to_datetime(pop_pre["data_resolucao"]) > DATA_REFERENCIA - pd.DateOffset(months=12)].copy()
    recente["p"] = prever_pre(montar_X_2g(recente, False, colunas_referencia=cols_pre))
    referencia_pre = {}
    for esc, id_esc in ESCRITORIO_PARA_ID.items():
        r = recente[recente["id_escritorio_assinante"] == id_esc]
        referencia_pre[esc] = {
            "media_prevista_12m": float(r["p"].mean()), "taxa_observada_12m": float(r["y"].mean()),
            "n_12m": int(len(r)), "acordos_12m": int(r["y"].sum()),
        }
    print(f"\nReferencia acordo pre (12 meses): {referencia_pre}")
    cols_pos, prever_pos = ajustar_final(pop_pos, True, m_pos["modelo_final"], m_pos["rodadas_xgb"])
    p_pos = {c: media_por_chave(base, prever_pos(montar_X_2g(base.assign(resultado_1g=c), True,
                                                             colunas_referencia=cols_pos)))
             for c in CENARIOS_PAGINA}

    previsoes = {k: [round(p_pre[k], 5)] + [round(p_pos[c][k], 4) for c in CENARIOS_PAGINA] for k in p_pre}

    # Taxa HISTORICA do acordo pre por combinacao dos 6 filtros (categorias reais):
    # [resolvidos no 1G, acordos pre] - comparacao no tooltip da pagina.
    h = pop_pre[pop_pre["tipo_acao"].isin(TIPOS)].copy()
    for c in ("materia", "comarca", "competencia"):
        h[c] = h[c].fillna("Não informada")
    vc = h["valor_causa"].astype(float)
    h["faixa"] = faixa_de(vc)
    h["esc"] = h["id_escritorio_assinante"].map({v: k for k, v in ESCRITORIO_PARA_ID.items()})
    g = h.groupby(["materia", "comarca", "competencia", "tipo_acao", "esc", "faixa"])["y"].agg(["size", "sum"])
    historico_pre = {"|".join(k): [int(n), int(a)] for k, (n, a) in zip(g.index, g.to_numpy())}

    with open(f"{BASE_DIR}/dados/fase6_acordos.json", "w", encoding="utf-8") as fh:
        json.dump({"cenarios_pos": CENARIOS_PAGINA, "metricas": {"pre": m_pre, "pos": m_pos},
                   "previsoes": previsoes, "historico_pre": historico_pre,
                   "referencia_pre": referencia_pre}, fh, ensure_ascii=False)
    print(f"\nSalvo: dados/fase6_acordos.json ({len(previsoes)} combinacoes)")


if __name__ == "__main__":
    main()
