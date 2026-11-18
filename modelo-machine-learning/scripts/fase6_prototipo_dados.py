# -*- coding: utf-8 -*-
"""
Fase 6 - gera os dados REAIS para o protótipo interativo (artefato de preview),
substituindo a formula ilustrativa da Fase 5 por saidas de verdade do modelo
XGBoost-AFT ja treinado/validado nas Fases 4 e 5.

Nao sobe um servidor (o artefato eh uma pagina estatica hospedada fora deste
ambiente) - em vez disso, pre-calcula a mediana prevista (dias) do modelo REAL
para TODAS as combinacoes de opcoes que o formulario do mockup oferece (864
combinacoes: 4 tipos x 4 materias x 3 comarcas x 3 competencias x 2 escritorios
x 3 faixas de valor), e exporta um lookup pequeno (so "dias" por combinacao -
o resto, a curva de sobrevivencia S(t|x), e recomputado no proprio navegador
pela formula fechada da AFT log-normal, pois com escala fixa em 1,0 (Fase 4/5)
a FORMA da curva em escala log e identica entre casos - so desloca pela
mediana prevista. Isso elimina qualquer "aproximacao" visual: o navegador usa
a mesma formula matematica exata validada na Fase 5).

Tambem calcula, a partir dos dados reais de treino: (a) a mediana de duracao
por materia via Kaplan-Meier (pra comparar "este caso" com a materia em geral)
e (b) a importancia de variavel REAL (gain do XGBoost, ja salva em
dados/fase4_xgboost_importancia.csv), agregada por grupo de covariavel (as 6
secoes do formulario) - substitui os percentuais inventados do mockup da Fase 5.

Rodar: TCC - Luiz/.venv/bin/python scripts/fase6_prototipo_dados.py
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
from lifelines import KaplanMeierFitter

sys.path.insert(0, (ML_DIR + "/scripts"))
from coorte_comum import TOP_COMARCA, TOP_COMPETENCIA, TOP_MATERIA, bucket  # noqa: E402
from fase4_rsf import montar_X  # noqa: E402,F401  (usado por outros scripts via este modulo)
from fase4_xgboost_aft import DATA_REFERENCIA, montar_X_xgb, params_xgb  # noqa: E402

BASE_DIR = ML_DIR

# Materia/comarca/competencia: TODAS as categorias que o modelo enxerga (os buckets
# TOP_* + "Outros") - 04/11/2026, a pagina passou a ter multi-select nesses tres.
# Tipo de acao segue o subconjunto original do formulario.
TIPOS = ["INDENIZATÓRIA", "RECURSO INOMINADO", "APELAÇÃO CÍVEL", "CUMPRIMENTO DE SENTENÇA"]
MATERIAS = TOP_MATERIA + ["Outros"]
COMARCAS = TOP_COMARCA + ["Outros"]
COMPETENCIAS = TOP_COMPETENCIA + ["Outros"]
ESCRITORIOS = ["NG", "LA"]
# Faixas de valor de causa do formulario (09/11/2026: eram ate 5 mil / 5-20 mil / acima de
# 20 mil). Fonte unica - todos os scripts da Fase 6 usam FAIXAS/faixa_de daqui.
FAIXAS_LIMITES = [
    ("Até R$ 10 mil", 10_000),
    ("R$ 10 mil – 30 mil", 30_000),
    ("R$ 30 mil – 50 mil", 50_000),
    ("Acima de R$ 50 mil", float("inf")),
]
FAIXAS = [rotulo for rotulo, _ in FAIXAS_LIMITES]


def faixa_de(valor):
    """Rotulo da faixa p/ uma Series de valor de causa (limite superior incluso)."""
    bins = [-float("inf")] + [lim for _, lim in FAIXAS_LIMITES]
    return pd.cut(valor.astype(float), bins=bins, labels=FAIXAS, right=True).astype(str)

ESCRITORIO_PARA_ID = {"NG": 20, "LA": 21}

GRUPO_POR_PREFIXO = {
    "tipo_": "Tipo de ação",
    "mat_": "Matéria",
    "com_": "Comarca",
    "comp_": "Competência",
    "esc_": "Escritório",
    "log_valor_causa": "Valor de causa",
    "ano_dist": "Época (ano de distribuição)",
}


def agrupar_prefixo(col):
    for prefixo, grupo in GRUPO_POR_PREFIXO.items():
        if col.startswith(prefixo):
            return grupo
    return None


def main():
    df = pd.read_parquet(f"{BASE_DIR}/dados/fase4_coorte_com_split.parquet")
    treino_full = df[df["split"] == "treino"].reset_index(drop=True)

    X_treino_full = montar_X_xgb(treino_full)
    evento_treino_full = (treino_full["tipo_evento_e1"] != "CENSURADO").to_numpy()

    def montar_dmatrix(X, duracao, evento):
        lower = duracao.astype(float).copy()
        upper = duracao.astype(float).copy()
        upper[~evento] = np.inf
        d = xgb.DMatrix(X)
        d.set_float_info("label_lower_bound", lower)
        d.set_float_info("label_upper_bound", upper)
        return d

    # reusa a melhor iteracao ja validada na Fase 4 (early stopping), sem
    # recalcular - evita hand-typing: le do CSV que a Fase 4 ja salvou.
    xgb_metricas = pd.read_csv(f"{BASE_DIR}/dados/fase4_xgboost_metricas.csv")
    best_iteration = int(xgb_metricas.loc[0, "best_iteration"])
    print(f"Reajustando XGBoost-AFT no treino inteiro (num_boost_round={best_iteration + 1}, "
          f"ja validado nas Fases 4/5)...")

    # config revista apos o backtest (fase4_xgboost_aft.py): + ano de distribuicao,
    # base_score = mediana KM do treino (gravada pela Fase 4)
    params = params_xgb(float(xgb_metricas.loc[0, "base_score"]))
    d_treino_full = montar_dmatrix(X_treino_full, treino_full["duracao_dias_e1"].to_numpy(), evento_treino_full)
    booster = xgb.train(params, d_treino_full, num_boost_round=best_iteration + 1)

    # --- 1) lookup de mediana prevista (dias) p/ todas as combinacoes do formulario ---
    combos = []
    for tipo in TIPOS:
        for materia in MATERIAS:
            for comarca in COMARCAS:
                for competencia in COMPETENCIAS:
                    for escritorio in ESCRITORIOS:
                        for faixa in FAIXAS:
                            combos.append((tipo, materia, comarca, competencia, escritorio, faixa))
    print(f"Combinacoes do formulario: {len(combos)}")

    # valor de causa representativo por faixa = mediana REAL dos processos de
    # treino que caem nela (nao um numero arbitrario).
    vc = treino_full["valor_causa"].astype(float)
    faixa_treino = faixa_de(vc)
    faixa_bounds = {f: vc[faixa_treino == f] for f in FAIXAS}
    valor_por_faixa = {f: float(s.median()) for f, s in faixa_bounds.items()}
    print("Valor de causa representativo por faixa (mediana real do treino):")
    for f, v in valor_por_faixa.items():
        print(f"  {f}: R$ {v:,.2f}")

    combos_df = pd.DataFrame(combos, columns=["tipo_acao", "materia", "comarca", "competencia", "escritorio", "faixa"])
    combos_df["id_escritorio_assinante"] = combos_df["escritorio"].map(ESCRITORIO_PARA_ID)
    combos_df["valor_causa"] = combos_df["faixa"].map(valor_por_faixa)

    # processo NOVO: ano de distribuicao = data de referencia (ritmo mais recente)
    X_combos = montar_X_xgb(combos_df, colunas_referencia=X_treino_full.columns, data_referencia=DATA_REFERENCIA)
    d_combos = xgb.DMatrix(X_combos)
    pred_dias = booster.predict(d_combos)  # mediana prevista (ja na escala de dias, log-normal AFT)

    previsoes = {}
    for (tipo, materia, comarca, competencia, escritorio, faixa), dias in zip(combos, pred_dias):
        chave = "|".join([tipo, materia, comarca, competencia, escritorio, faixa])
        previsoes[chave] = max(1, round(float(dias)))

    # --- 2) mediana de duracao por materia (Kaplan-Meier, treino) ---
    # (a comparacao com multi-select usa a tabela km_materia abaixo - o navegador
    # calcula a KM da uniao das materias selecionadas.)
    materia_b = bucket(treino_full["materia"], TOP_MATERIA)
    evento_km = (treino_full["tipo_evento_e1"] != "CENSURADO")

    def mediana_km(mask):
        kmf = KaplanMeierFitter()
        kmf.fit(treino_full.loc[mask, "duracao_dias_e1"], event_observed=evento_km[mask])
        mediana = kmf.median_survival_time_
        return None if not np.isfinite(mediana) else round(float(mediana))

    medianas_materia = {m: mediana_km(materia_b == m) for m in MATERIAS}

    # --- 2c) categorias REAIS (04/11/2026: filtro mostra todas, nao so os buckets) ---
    # O modelo so enxerga TOP_* + "Outros"; categoria fora do top usa a previsao do
    # bucket "Outros", mas o peso da mistura e a comparacao KM usam a categoria real.
    NAO_INFORMADO = "Não informada"
    df_modelagem = df.copy()
    for col in ("materia", "comarca", "competencia"):
        df_modelagem[col] = df_modelagem[col].fillna(NAO_INFORMADO)
    treino_real = df_modelagem[df_modelagem["split"] == "treino"]
    tops = {"materia": TOP_MATERIA, "comarca": TOP_COMARCA, "competencia": TOP_COMPETENCIA}
    categorias_reais, grupo_modelo = {}, {}
    for col, top in tops.items():
        # ordem: top do modelo primeiro, depois as demais por frequencia no treino
        freq = df_modelagem[col].value_counts()
        demais = [c for c in freq.index if c not in top]
        categorias_reais[col] = [c for c in top if c in freq.index] + demais
        grupo_modelo[col] = {c: "Outros" for c in demais}
    # Peso/base com os 6 filtros da pagina (09/11/2026 - antes so materia x comarca x
    # competencia: LA em Belem mostrava "1 processo" que era do NG e a previsao saia
    # extrapolada). Chave: materia|comarca|competencia|tipo|escritorio|faixa (categorias
    # reais, so os tipos do formulario).
    tr6 = treino_real[treino_real["tipo_acao"].isin(TIPOS)].assign(
        esc=lambda x: x["id_escritorio_assinante"].map({v: k for k, v in ESCRITORIO_PARA_ID.items()}),
        faixa=lambda x: faixa_de(x["valor_causa"]))
    pesos_treino_real = {
        "|".join(k): int(n)
        for k, n in tr6.groupby(["materia", "comarca", "competencia", "tipo_acao", "esc", "faixa"]).size().items()
    }
    # --- 2d) procedencia empirica 1G/2G (09/11/2026) ---
    # O XGBoost-AFT so preve QUANDO; a taxa de sucesso vem do historico (coorte de
    # modelagem inteira, treino+teste - e descritivo, nao modelo). Mesmo criterio do
    # dashboard Sobrevivencia Processual: favoravel = merito 1 ou 3 (procedente /
    # parcialmente procedente COM proveito economico) / processos com merito julgado
    # naquela instancia. 2G: "sentenca anulada" (8) fora do denominador (nao e merito).
    # Chave = os 6 filtros da pagina, categorias reais -> [julg_1g, fav_1g, julg_2g, fav_2g].
    proc = df_modelagem[df_modelagem["tipo_acao"].isin(TIPOS)].copy()
    vc_proc = proc["valor_causa"].astype(float)
    proc["faixa"] = faixa_de(vc_proc)
    proc["esc"] = proc["id_escritorio_assinante"].map({v: k for k, v in ESCRITORIO_PARA_ID.items()})
    proc["j1"] = proc["id_sentenca_merito_grau1"].notna().astype(int)
    proc["f1"] = proc["id_sentenca_merito_grau1"].isin([1, 3]).astype(int)
    proc["j2"] = (proc["id_acordao_merito_grau2"].notna() & (proc["id_acordao_merito_grau2"] != 8)).astype(int)
    proc["f2"] = proc["id_acordao_merito_grau2"].isin([1, 3]).astype(int)
    g = proc.groupby(["materia", "comarca", "competencia", "tipo_acao", "esc", "faixa"])[["j1", "f1", "j2", "f2"]].sum()
    g = g[(g["j1"] + g["j2"]) > 0]
    procedencia = {"|".join(k): [int(x) for x in v] for k, v in zip(g.index, g.to_numpy())}
    print(f"\nProcedencia 1G/2G: {len(procedencia)} combinacoes | geral 1G "
          f"{proc.f1.sum() / proc.j1.sum():.1%} (n={proc.j1.sum()}), 2G {proc.f2.sum() / proc.j2.sum():.1%} "
          f"(n={proc.j2.sum()})")

    # tabela KM por materia (tempo, eventos, censuras) - o navegador junta as materias
    # selecionadas e calcula a mediana KM da uniao (exata, mesma regra do lifelines).
    km_tab = (treino_real.assign(ev=(treino_real["tipo_evento_e1"] != "CENSURADO").astype(int))
              .groupby(["materia", "duracao_dias_e1"])["ev"].agg(["sum", "count"]).reset_index())
    km_materia = {}
    for m, sub in km_tab.groupby("materia"):
        km_materia[m] = [[int(t), int(d), int(n - d)] for t, d, n in
                         zip(sub["duracao_dias_e1"], sub["sum"], sub["count"])]
    print(f"\nMediana de duracao por materia (Kaplan-Meier, treino): {medianas_materia}")

    # --- 2b) n de processos de treino por materia x comarca x competencia (bucketizados) ---
    # Peso da mistura quando ha mais de uma opcao selecionada (e aviso de extrapolacao
    # quando a combinacao nao existe no treino).
    chave_peso = (materia_b + "|" + bucket(treino_full["comarca"], TOP_COMARCA) + "|"
                  + bucket(treino_full["competencia"], TOP_COMPETENCIA))
    pesos_treino = {k: int(v) for k, v in chave_peso.value_counts().items()}

    # --- 3) importancia de variavel REAL (gain), agregada por grupo do formulario ---
    importancia = pd.read_csv(f"{BASE_DIR}/dados/fase4_xgboost_importancia.csv", index_col=0)["gain"]
    por_grupo = {}
    for col, gain in importancia.items():
        grupo = agrupar_prefixo(col)
        if grupo is None:
            continue
        por_grupo[grupo] = por_grupo.get(grupo, 0.0) + float(gain)
    total = sum(por_grupo.values())
    fatores = sorted(
        [{"nome": g, "pct": round(100 * v / total, 1)} for g, v in por_grupo.items()],
        key=lambda d: -d["pct"],
    )
    print("\nImportancia de variavel REAL (gain do XGBoost, agregada por grupo):")
    for f in fatores:
        print(f"  {f['nome']}: {f['pct']}%")

    saida = {
        "gerado_em": str(DATA_REFERENCIA.date()),  # data da foto dos dados
        "modelo": "XGBoost-AFT (Fase 4/5, num_boost_round=%d, + ano de distribuição)" % (best_iteration + 1),
        "previsoes": previsoes,
        "medianas_materia": medianas_materia,
        "pesos_treino": pesos_treino,
        "n_treino": int(len(treino_full)),
        "categorias_reais": categorias_reais,
        "grupo_modelo": grupo_modelo,
        "pesos_treino_real": pesos_treino_real,
        "km_materia": km_materia,
        "procedencia": procedencia,
        "faixas": FAIXAS,
        "opcoes_grade": {"materias": MATERIAS, "comarcas": COMARCAS, "competencias": COMPETENCIAS},
        "fatores": fatores,
        "valor_causa_por_faixa": valor_por_faixa,
    }
    out_path = f"{BASE_DIR}/dados/fase6_prototipo_previsoes.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=2)
    print(f"\nSalvo: {out_path} ({len(previsoes)} previsoes)")


if __name__ == "__main__":
    main()
