# -*- coding: utf-8 -*-
"""
Fase 6 - exporta o snapshot estatico consumido pela pagina "Previsao Individualizada"
do LexHub: lookup do XGBoost-AFT (fase6_prototipo_previsoes.json) + metricas de
validacao das Fases 4-5. Grava direto no repo api_dashboards
(src/app/analyses/GERAL/data/tcc_previsao_individual.json) - so dado agregado,
nenhum processo individual.

Rodar depois de fase6_prototipo_dados.py:
  TCC - Luiz/.venv/bin/python scripts/fase6_exportar_bundle_api.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import csv
import json

TCC_DADOS = (ML_DIR + "/dados")
OUT = (REPO_DIR + "/apps/api/src/app/analyses/GERAL/data/tcc_previsao_individual.json")


def ler_csv(nome):
    with open(f"{TCC_DADOS}/{nome}", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    with open(f"{TCC_DADOS}/fase6_prototipo_previsoes.json", encoding="utf-8") as fh:
        fase6 = json.load(fh)
    with open(f"{TCC_DADOS}/fase6_procedencia.json", encoding="utf-8") as fh:
        procedencia_modelo = json.load(fh)
    with open(f"{TCC_DADOS}/fase6_procedencia_2g.json", encoding="utf-8") as fh:
        procedencia_2g = json.load(fh)
    with open(f"{TCC_DADOS}/fase6_acordos.json", encoding="utf-8") as fh:
        acordos = json.load(fh)
    with open(f"{TCC_DADOS}/fase6_selecao_temporal.json", encoding="utf-8") as fh:
        selecao = json.load(fh)
    import pandas as pd
    s1 = pd.read_parquet(f"{TCC_DADOS}/fase4_coorte_com_split.parquet", columns=["id_sentenca_merito_grau1"])[
        "id_sentenca_merito_grau1"]
    desfav = s1[s1.notna() & ~s1.isin([1, 3])]
    fracao_extinto = round(float((desfav == 7).mean()), 4)

    cox = ler_csv("fase4_cox_mesmo_split_metricas.csv")[0]
    rsf = ler_csv("fase4_rsf_tunada_metricas.csv")[0]
    xgb = ler_csv("fase4_xgboost_metricas.csv")[0]
    ic = {r["modelo"]: r for r in ler_csv("fase5_bootstrap_ic.csv")}
    vitorias = ler_csv("fase5_bootstrap_vitorias.csv")[0]
    brier = {r["modelo"]: r for r in ler_csv("fase4_brier_resultado.csv")}
    calibracao = ler_csv("fase5_calibracao.csv")

    def cindex(treino_teste, chave):
        return {
            "treino": float(treino_teste["cindex_treino"]), "teste": float(treino_teste["cindex_teste"]),
            "ic95_min": float(ic[chave]["ic_2.5%"]), "ic95_max": float(ic[chave]["ic_97.5%"]),
        }

    n = int(vitorias["n_validas"])
    bundle = {
        "gerado_em": fase6["gerado_em"],
        "modelo": fase6["modelo"],
        "opcoes": {
            "tiposAcao": ["INDENIZATÓRIA", "RECURSO INOMINADO", "APELAÇÃO CÍVEL", "CUMPRIMENTO DE SENTENÇA"],
            "materias": fase6["categorias_reais"]["materia"],
            "comarcas": fase6["categorias_reais"]["comarca"],
            "competencias": fase6["categorias_reais"]["competencia"],
            "escritorios": ["NG", "LA"],
            "faixasValor": fase6["faixas"],
        },
        # [mediana prevista (dias, XGBoost-AFT), procedencia 1G prevista em milesimos
        # (classificador XGBoost, fase6_procedencia.py)] - mesma chave, um item so.
        # + procedencia 2G prevista (regressao logistica, fase6_procedencia_2g.py) nos
        # cenarios do 1G: procedente c/ proveito | improcedente | extinto (milesimos)
        # + acordo pos-sentenca previsto (fase6_acordos.py) nos mesmos 3 cenarios do 1G.
        # Ordem: [dias, proc1G, proc2G x3, acordoPos x3, acordoPre]; milesimos (acordoPre em
        # dez-milesimos - valores ~1-4%, precisa de mais resolucao p/ o risco relativo).
        "previsoes": {k: [d, round(procedencia_modelo["previsoes"][k][0] * 1000)]
                         + [round(x * 1000) for x in procedencia_2g["previsoes"][k]]
                         + [round(x * 1000) for x in acordos["previsoes"][k][1:]]
                         + [round(acordos["previsoes"][k][0] * 10000)]  # acordo pre (dez-milesimos)
                      for k, d in fase6["previsoes"].items()},
        # acordo pre-sentenca: so historico (modelo nao superou a taxa base), mesma chave de
        # `procedencia`: [resolvidos no 1G, acordos pre-sentenca]
        "historico_acordo_pre": acordos["historico_pre"],
        "metricas_acordos": acordos["metricas"],
        # acordo pre e mostrado RELATIVO: p(perfil) / media_prevista_12m (x taxa_observada_12m)
        "referencia_acordo_pre": acordos["referencia_pre"],
        "medianas_materia": fase6["medianas_materia"],
        "grupo_modelo": fase6["grupo_modelo"],
        "pesos_treino": fase6["pesos_treino_real"],
        "km_materia": fase6["km_materia"],
        "procedencia": fase6["procedencia"],
        # chance combinada do 2G (1G ainda sem sentenca) = p1G*P(2G|1G fav) + (1-p1G)*
        # [f*P(2G|extinto) + (1-f)*P(2G|improcedente)], f = fracao historica de extincao
        # entre as sentencas de merito desfavoraveis (sem proveito conta como improcedente)
        "fracao_extinto_1g_desfavoravel": fracao_extinto,
        # como a pagina exibe cada probabilidade (previsao / relativo / historico) e qual
        # modelo - decidido SEM o teste final (fase6_selecao_temporal.py)
        "exibicao": {k: v["exibir"] for k, v in selecao["classificadores"].items()},
        "metricas_procedencia_2g": {
            "modelo": procedencia_2g["modelo_final"], "n_teste": procedencia_2g["n_teste"],
            "teste_de": procedencia_2g["teste_de"], "teste_ate": procedencia_2g["teste_ate"],
            **{k: v for k, v in procedencia_2g["metricas"]["com_resultado_1g"].items() if k != "calibracao"},
        },
        "metricas_procedencia": procedencia_modelo["metricas"],
        "n_treino": fase6["n_treino"],
        "fatores_importancia": fase6["fatores"],
        "valor_causa_por_faixa": fase6["valor_causa_por_faixa"],
        "metricas": {
            "cindex": {
                "Cox": cindex(cox, "Cox"),
                "RSF_tunada": cindex(rsf, "RSF_tunada"),
                "XGBoost_AFT": cindex(xgb, "XGBoost_AFT"),
            },
            "vitorias_pareadas_bootstrap": {
                "xgb_vs_cox_pct": 100 * int(vitorias["xgb_vs_cox"]) / n,
                "xgb_vs_rsf_pct": 100 * int(vitorias["xgb_vs_rsf"]) / n,
                "rsf_vs_cox_pct": 100 * int(vitorias["rsf_vs_cox"]) / n,
                "n_validas": n,
            },
            "brier_score_integrado": {m: float(brier[m]["ibs"]) for m in ("Cox", "RSF_tunada", "XGBoost_AFT")},
            "calibracao_90_dias": [
                {
                    "modelo": r["modelo"], "quartil": int(r["quartil"]), "n": int(r["n"]),
                    "previsto": float(r["s_previsto_medio"]), "observado": float(r["s_observado_km"]),
                }
                for r in calibracao
            ],
        },
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        # compacto: com a grade completa sao ~9,7 mil previsoes
        json.dump(bundle, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"Gravado: {OUT} ({len(bundle['previsoes'])} previsoes)")


if __name__ == "__main__":
    main()
