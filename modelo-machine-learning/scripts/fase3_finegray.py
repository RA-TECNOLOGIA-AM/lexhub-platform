# -*- coding: utf-8 -*-
"""Fase 3 (parte 2), v2: Fine-Gray via Cox ponderado (IPCW), horizonte truncado em 1800 dias."""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import sys
import time
import numpy as np
import pandas as pd
from lifelines import CoxTimeVaryingFitter, KaplanMeierFitter

pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda v: f"{v:.4f}")

HORIZONTE_MAX = 1800.0  # mesmo horizonte usado no resto do dashboard/analise


def ajustar_fine_gray(df, duration_col, event_col, event_of_interest, covariate_cols, grade_passo=90, penalizer=0.05, verbose=True):
    df = df.reset_index(drop=True).copy()
    df["subj_id"] = df.index
    # trunca horizonte: quem passaria de 1800d e re-censurado em 1800d (censura administrativa)
    alem_horizonte = df[duration_col] > HORIZONTE_MAX
    df.loc[alem_horizonte, duration_col] = HORIZONTE_MAX
    df.loc[alem_horizonte, event_col] = 0

    grade = np.arange(0.0, HORIZONTE_MAX + grade_passo, grade_passo)
    n_grade = len(grade)

    cens_evt = (df[event_col] == 0).astype(int)
    kmf_cens = KaplanMeierFitter()
    kmf_cens.fit(df[duration_col], event_observed=cens_evt)
    G_grid = kmf_cens.survival_function_at_times(grade).values  # vetor alinhado com `grade`, calculado 1 vez só

    linhas = []
    t0 = time.time()
    for i, row in enumerate(df.itertuples(index=False)):
        t_i = float(getattr(row, duration_col))
        ev_i = getattr(row, event_col)
        cov = {c: getattr(row, c) for c in covariate_cols}
        rid = row.subj_id
        if ev_i == event_of_interest:
            linhas.append({"subj_id": rid, "start": 0.0, "stop": t_i, "event": 1, "weight": 1.0, **cov})
        elif ev_i == 0:
            linhas.append({"subj_id": rid, "start": 0.0, "stop": t_i, "event": 0, "weight": 1.0, **cov})
        else:
            idx_i = max(np.searchsorted(grade, t_i, side="right") - 1, 0)
            g_ti = G_grid[idx_i]
            linhas.append({"subj_id": rid, "start": 0.0, "stop": t_i, "event": 0, "weight": 1.0, **cov})
            if g_ti > 0:
                prev = t_i
                for j in range(idx_i + 1, n_grade):
                    w = G_grid[j] / g_ti
                    if w <= 1e-4:
                        break
                    linhas.append({"subj_id": rid, "start": prev, "stop": float(grade[j]), "event": 0, "weight": w, **cov})
                    prev = float(grade[j])
        if verbose and (i + 1) % 5000 == 0:
            print(f"  ... {i+1}/{len(df)} sujeitos processados ({time.time()-t0:.1f}s, {len(linhas)} linhas ate agora)", flush=True)

    long_df = pd.DataFrame(linhas)
    long_df = long_df[long_df["stop"] > long_df["start"]]
    ajustar_fine_gray.n_linhas_longas = len(long_df)
    print(f"Construcao do dataset longo: {time.time()-t0:.1f}s | {len(long_df)} linhas (de {len(df)} sujeitos)", flush=True)

    ctv = CoxTimeVaryingFitter(penalizer=penalizer)
    t1 = time.time()
    ctv.fit(long_df, id_col="subj_id", event_col="event", start_col="start", stop_col="stop", weights_col="weight")
    print(f"Ajuste do Cox ponderado: {time.time()-t1:.1f}s", flush=True)
    return ctv


if __name__ == "__main__":
    sys.path.insert(0, (ML_DIR + "/scripts"))
    from coorte_comum import TOP_COMARCA, TOP_COMPETENCIA, TOP_MATERIA, TOP_TIPO_ACAO, bucket, carregar_coorte

    df = carregar_coorte()
    df = df[df["id_escritorio_assinante"].isin([20, 21])].copy()
    df["duracao"] = df["duracao_dias_e1"].astype(float)

    MAPA_EVENTO = {"CENSURADO": 0, "MERITO_FAVORAVEL_COM_PROVEITO": 1, "ACORDO": 2, "MERITO_SEM_PROVEITO_OU_DESFAVORAVEL": 3}
    df["evento_cod"] = df["tipo_evento_e1"].map(MAPA_EVENTO)

    df["tipo_acao_b"] = bucket(df["tipo_acao"], TOP_TIPO_ACAO)
    df["materia_b"] = bucket(df["materia"], TOP_MATERIA)
    df["comarca_b"] = bucket(df["comarca"], TOP_COMARCA)
    df["competencia_b"] = bucket(df["competencia"], TOP_COMPETENCIA)
    df["escritorio"] = df["id_escritorio_assinante"].map({20: "NG", 21: "LA"})
    df = df.dropna(subset=["valor_causa"]).copy()
    df["valor_causa"] = df["valor_causa"].astype(float)
    df["log_valor_causa"] = np.log1p(df["valor_causa"].clip(lower=0))

    ref_tipo = df["tipo_acao_b"].value_counts().idxmax()
    ref_materia = df["materia_b"].value_counts().idxmax()
    ref_comarca = df["comarca_b"].value_counts().idxmax()
    ref_competencia = df["competencia_b"].value_counts().idxmax()

    dummies_tipo = pd.get_dummies(df["tipo_acao_b"], prefix="tipo").drop(columns=[f"tipo_{ref_tipo}"])
    dummies_materia = pd.get_dummies(df["materia_b"], prefix="mat").drop(columns=[f"mat_{ref_materia}"])
    dummies_comarca = pd.get_dummies(df["comarca_b"], prefix="com").drop(columns=[f"com_{ref_comarca}"])
    dummies_competencia = pd.get_dummies(df["competencia_b"], prefix="comp").drop(columns=[f"comp_{ref_competencia}"])
    dummies_escritorio = pd.get_dummies(df["escritorio"], prefix="esc", drop_first=True)
    dummies_tipo.columns = [c.replace(" ", "_") for c in dummies_tipo.columns]
    dummies_materia.columns = [c.replace(" ", "_") for c in dummies_materia.columns]
    dummies_comarca.columns = [c.replace(" ", "_") for c in dummies_comarca.columns]
    dummies_competencia.columns = [c.replace(" ", "_") for c in dummies_competencia.columns]

    modelo_df = pd.concat([
        df[["duracao", "evento_cod", "log_valor_causa"]].reset_index(drop=True),
        dummies_tipo.reset_index(drop=True), dummies_materia.reset_index(drop=True),
        dummies_comarca.reset_index(drop=True), dummies_competencia.reset_index(drop=True),
        dummies_escritorio.reset_index(drop=True),
    ], axis=1)

    cov_cols = (
        ["log_valor_causa"] + list(dummies_tipo.columns) + list(dummies_materia.columns)
        + list(dummies_comarca.columns) + list(dummies_competencia.columns) + list(dummies_escritorio.columns)
    )

    modo = sys.argv[1] if len(sys.argv) > 1 else "full"

    if modo == "teste":
        amostra = modelo_df.sample(n=3000, random_state=0).reset_index(drop=True)
        print("N (amostra teste):", len(amostra), "| eventos:", amostra["evento_cod"].value_counts().to_dict())
        fg = ajustar_fine_gray(amostra, "duracao", "evento_cod", event_of_interest=1, covariate_cols=cov_cols, grade_passo=90, penalizer=0.05)
        print(fg.summary[["coef", "exp(coef)", "p"]].sort_values("exp(coef)").to_string())
    else:
        print("N:", len(modelo_df), "| distribuicao de eventos:", modelo_df["evento_cod"].value_counts().to_dict())
        print("Referencia tipo_acao:", ref_tipo, "| Referencia materia:", ref_materia)
        fg = ajustar_fine_gray(modelo_df, "duracao", "evento_cod", event_of_interest=1, covariate_cols=cov_cols, grade_passo=90, penalizer=0.05)
        print("\n=== FINE-GRAY - evento de interesse: MERITO_FAVORAVEL_COM_PROVEITO ===")
        print("Log-likelihood:", round(fg.log_likelihood_, 2))
        resumo = fg.summary[["coef", "exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]].sort_values("exp(coef)")
        print(resumo.to_string())
        resumo.to_csv((ML_DIR + "/dados/fase3_finegray_subdist_hr.csv"))
        import json
        contagem = modelo_df["evento_cod"].value_counts().to_dict()
        with open((ML_DIR + "/dados/fase3_finegray_resumo.json"), "w", encoding="utf-8") as fh:
            json.dump({
                "n_modelo": int(len(modelo_df)), "evento_interesse": int(contagem.get(1, 0)),
                "concorrente_acordo": int(contagem.get(2, 0)), "concorrente_merito_desfav": int(contagem.get(3, 0)),
                "censurados": int(contagem.get(0, 0)), "linhas_longas": int(ajustar_fine_gray.n_linhas_longas),
                "loglik": float(fg.log_likelihood_),
            }, fh, ensure_ascii=False, indent=2)
