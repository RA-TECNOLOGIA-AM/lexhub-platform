# -*- coding: utf-8 -*-
"""
Valida a implementacao do Fine-Gray via Cox ponderado (IPCW, Geskus 2011) ANTES
de aplicar nos dados reais. Invariante matematica usada para validar: quando nao
ha risco competitivo (todo mundo e 'evento de interesse' ou censurado), o
Fine-Gray tem que ser EXATAMENTE igual a um Cox padrao na mesma base, porque o
peso IPCW fica trivialmente 1 para todo mundo (ninguem precisa ser
'reponderado' por causa de um evento competidor que nunca acontece).
"""
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, CoxTimeVaryingFitter, KaplanMeierFitter

rng = np.random.default_rng(42)


def ajustar_fine_gray(df, duration_col, event_col, event_of_interest, covariate_cols,
                       grade_passo=30, penalizer=0.0):
    """
    df: cada linha = um sujeito. event_col tem valores em {0 (censurado), event_of_interest, outros...}.
    Retorna um CoxTimeVaryingFitter ajustado via Cox ponderado (truque de Geskus/Fine-Gray).
    """
    df = df.reset_index(drop=True).copy()
    df["_id"] = df.index
    tempo_max = df[duration_col].max()
    grade = np.arange(0, tempo_max + grade_passo, grade_passo)

    # G(t) = KM da "censura": evento = censura (event_col==0), tudo mais (qualquer evento real) e censurado p/ essa KM auxiliar
    cens_evt = (df[event_col] == 0).astype(int)
    kmf_cens = KaplanMeierFitter()
    kmf_cens.fit(df[duration_col], event_observed=cens_evt)

    def G(t):
        if t <= 0:
            return 1.0
        # sobrevivencia da censura no ultimo tempo <= t (funcao em escada, 1.0 antes do 1o evento)
        sf = kmf_cens.survival_function_at_times(t)
        return float(sf.iloc[0])

    linhas = []
    for _, row in df.iterrows():
        t_i = row[duration_col]
        ev_i = row[event_col]
        cov = {c: row[c] for c in covariate_cols}
        if ev_i == event_of_interest:
            linhas.append({"_id": row["_id"], "start": 0.0, "stop": float(t_i), "event": 1, "weight": 1.0, **cov})
        elif ev_i == 0:
            linhas.append({"_id": row["_id"], "start": 0.0, "stop": float(t_i), "event": 0, "weight": 1.0, **cov})
        else:
            # evento competidor em t_i: risco "fake" se estende ate o fim da grade, peso = G(t)/G(t_i)
            g_ti = G(t_i)
            pontos = [p for p in grade if p > t_i]
            # primeiro trecho: do inicio ate t_i, ainda sem reponderacao (peso 1, como qualquer um em risco)
            linhas.append({"_id": row["_id"], "start": 0.0, "stop": float(t_i), "event": 0, "weight": 1.0, **cov})
            prev = t_i
            for p in pontos:
                w = G(p) / g_ti if g_ti > 0 else 0.0
                if w <= 0:
                    break
                linhas.append({"_id": row["_id"], "start": float(prev), "stop": float(p), "event": 0, "weight": w, **cov})
                prev = p

    long_df = pd.DataFrame(linhas)
    long_df = long_df[long_df["stop"] > long_df["start"]]  # remove intervalos de duracao zero

    ctv = CoxTimeVaryingFitter(penalizer=penalizer)
    ctv.fit(long_df, id_col="_id", event_col="event", start_col="start", stop_col="stop", weights_col="weight")
    return ctv


# ============================================================
# VALIDACAO 1: sem risco competitivo -> tem que bater com Cox padrao
# ============================================================
n = 600
x1 = rng.normal(size=n)
x2 = rng.binomial(1, 0.4, size=n)
risco = np.exp(0.8 * x1 - 0.5 * x2)
tempo_evento = rng.exponential(1.0 / risco) * 100
tempo_censura = rng.exponential(1.0, size=n) * 150
duracao = np.minimum(tempo_evento, tempo_censura)
evento = (tempo_evento <= tempo_censura).astype(int)  # 1 = evento de interesse, 0 = censurado (SEM competidor)

df_sem_competidor = pd.DataFrame({"duracao": duracao, "evento": evento, "x1": x1, "x2": x2})

cox_padrao = CoxPHFitter()
cox_padrao.fit(df_sem_competidor, duration_col="duracao", event_col="evento")

fg_sem_competidor = ajustar_fine_gray(
    df_sem_competidor, "duracao", "evento", event_of_interest=1, covariate_cols=["x1", "x2"], grade_passo=5,
)

print("=== VALIDACAO 1: sem risco competitivo (tem que bater) ===")
print("Cox padrao:\n", cox_padrao.summary[["coef", "exp(coef)", "p"]])
print("\nFine-Gray (via IPCW, deveria ser quase identico):\n", fg_sem_competidor.summary[["coef", "exp(coef)", "p"]])
diff = (cox_padrao.summary["coef"].values - fg_sem_competidor.summary["coef"].values)
print("\nDiferenca absoluta nos coeficientes:", np.abs(diff))
assert np.all(np.abs(diff) < 0.05), "Fine-Gray sem competidor deveria bater com Cox padrao!"
print(">>> PASSOU: diferenca < 0.05 em todos os coeficientes.\n")

# ============================================================
# VALIDACAO 2: com risco competitivo real - so verifica que roda e os sinais fazem sentido
# ============================================================
n = 2000
x1 = rng.normal(size=n)
risco_interesse = np.exp(0.6 * x1)
risco_competidor = np.exp(-0.4 * x1)
t_interesse = rng.exponential(1.0 / risco_interesse) * 80
t_competidor = rng.exponential(1.0 / risco_competidor) * 80
t_censura = rng.exponential(1.0, size=n) * 120

tempo = np.minimum.reduce([t_interesse, t_competidor, t_censura])
evento = np.zeros(n, dtype=int)
evento[(t_interesse == tempo)] = 1
evento[(t_competidor == tempo) & (t_interesse != tempo)] = 2
# censura = 0 (default) quando t_censura foi o minimo

df_com_competidor = pd.DataFrame({"duracao": tempo, "evento": evento, "x1": x1})
print("Distribuicao de eventos (validacao 2):", df_com_competidor["evento"].value_counts().to_dict())

fg_com_competidor = ajustar_fine_gray(
    df_com_competidor, "duracao", "evento", event_of_interest=1, covariate_cols=["x1"], grade_passo=5,
)
print("\n=== VALIDACAO 2: com risco competitivo (so verifica que roda e sinal e coerente) ===")
print(fg_com_competidor.summary[["coef", "exp(coef)", "p"]])
print("Coeficiente verdadeiro de x1 no evento de interesse: +0.6 (positivo, maior x1 -> evento de interesse mais rapido)")
