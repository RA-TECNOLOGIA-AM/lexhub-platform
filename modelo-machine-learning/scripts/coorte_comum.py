# -*- coding: utf-8 -*-
"""
Definicoes compartilhadas por todas as fases do TCC (2 a 6): carga da coorte,
limpeza de tipo_acao e buckets de covariaveis. Antes cada script tinha sua copia
das listas TOP_* - centralizado aqui em 04/11/2026, quando a coorte foi
reancorada na DISTRIBUICAO (antes contratacao) e os buckets precisaram ser
refeitos de uma vez em todos os scripts.
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import re

import pandas as pd

BASE_DIR = ML_DIR
# Foto CONGELADA do banco usada em todas as fases (10/11/2026): o cron diario de
# atualizar_dashboard_tcc.py reextraia e sobrescrevia a coorte (rodou em 21 e 26/10), o que
# faria qualquer reprocessamento divergir dos PDFs. Agora o cron grava em *_atual e o TCC so
# le daqui; o hash e conferido a cada carga (manifesto.json).
SNAPSHOT_DIR = f"{BASE_DIR}/dados/congelado_20261110"  # foto FINAL (10/11/2026); a de 09/11 e a SNAPSHOT_ANTERIOR
COORTE_PATH = f"{SNAPSHOT_DIR}/coorte_sobrevivencia.parquet"
# foto anterior (09/11/2026), mantida para o apendice de qualidade comparar o efeito das
# correcoes feitas na origem entre as duas fotos
SNAPSHOT_ANTERIOR = f"{BASE_DIR}/dados/congelado_20261109"


def _data_referencia(pasta):
    """Data da extracao da foto ('hoje' p/ processo novo, datas 'no futuro' = erro, fim do
    acompanhamento). Lida do manifesto; fotos antigas sem o campo usam o nome da pasta."""
    import json as _json
    with open(f"{pasta}/manifesto.json", encoding="utf-8") as fh:
        man = _json.load(fh)
    return pd.Timestamp(man.get("data_referencia") or pasta.rsplit("_", 1)[-1])


DATA_REFERENCIA = _data_referencia(SNAPSHOT_DIR)
DATA_REFERENCIA_BR = DATA_REFERENCIA.strftime("%d/%m/%Y")
DATAS_MERITO_PATH = f"{SNAPSHOT_DIR}/fase6_datas_merito.parquet"

# Agravos (interno civel, de instrumento...) sao incidentes processuais, e Mandado de
# Seguranca e remedio constitucional atipico do perfil do escritorio - nao sao o tipo de
# acao principal da causa. Mesma regra do dashboard (TccSobrevivenciaProcessual.tsx):
# o processo continua na coorte, so perde o tipo de acao (cai em "Outros" nos modelos).
TIPO_ACAO_EXCLUIDO = re.compile(r"AGRAVO|MANDADO DE SEGURANÇA", re.IGNORECASE)

# Buckets: top por volume na coorte NG+LA vigente (04/11/2026, t0 = distribuicao),
# depois de tirar agravos/mandado de seguranca. Tipo de acao para em 7 - o 8o
# (EXIBICAO, n=23) nao tem volume pra virar categoria propria.
TOP_TIPO_ACAO = [
    "INDENIZATÓRIA", "RECURSO INOMINADO", "APELAÇÃO CÍVEL", "CUMPRIMENTO DE SENTENÇA",
    "EMBARGOS DE DECLARAÇÃO CÍVEL", "PETIÇÃO CÍVEL", "EMBARGOS",
]
# Materia ampliada em 04/11/2026: criterio objetivo = toda categoria com
# >= 300 processos na coorte de modelagem NG+LA (N=47.948). Antes eram so as 8
# maiores de cada, e o "Outros" de materia juntava 49% do treino com medianas de
# 181 a 618 dias (SVA x JUROS_ABUSIVOS) - a previsao nao distinguia nada disso.
# Cobertura de materia: 51% -> 88%. Competencia (4, ja cobre 96%) e tipo de acao seguem
# como estavam.
# Comarca: o mesmo criterio (>=300) foi testado (14 comarcas, backup em
# backups_fases_ampliado_24mat_14com/) e PIOROU o teste - C-index XGBoost 0,6269 ->
# 0,6225 e erro de calibracao a 90d nas comarcas novas 0,17 -> 0,30 (Humaita, Tabatinga:
# poucos processos e drift temporal). Com materia ampliada e comarca nas 8 originais o
# C-index foi 0,6277 (mesmas 49 rodadas) - por isso comarca ficou como estava.
TOP_MATERIA = [
    "ANP", "ESPECIFICA", "SLN", "PARC_CRED_PESS", "MORA", "COI_BOLETO", "CESTA", "RMC",
    "GASTO_C_CRED", "SVA", "COBRANCA_IND", "TARIFA_IND", "JUROS_ABUSIVOS", "RCC", "BX_ANT_FIN",
    "SEGURO", "RUBRICAS_REUNIDAS", "INV_FACIL", "SAQUE_TERMINAL", "JUROS_NC", "TIT_CAP",
    "AD_DEPOSITANTE", "ANUIDADE", "VIDA_PREV",
]
# 09/11/2026 (ponto 1a): a decisao acima tinha sido tomada OLHANDO O TESTE. Refeita sem o
# teste (fase6_selecao_temporal.py, backtest jul/2024 + jan/2025 com o XGBoost atual):
# 24/14 = C-index medio 0,673 / erro calib 0,133; 24/8 = 0,667 / 0,146; 8/8 = 0,663 / 0,142
# -> comarca tambem ampliada pelo criterio >= 300 processos (14 comarcas).
# 10/11/2026 (foto final): a mesma regra apontou 24/8 por 0,0008 de C-index medio (0,6670 x
# 0,6662 - empate), com 24/14 melhor calibrada (0,137 x 0,144). Decisao do usuario: MANTER 24/14
# (desempate por calibracao decidido apos ver o resultado - registrado como limitacao na Fase 4).
TOP_COMARCA = [
    "MANAUS", "SÃO GABRIEL DA CACHOEIRA", "PARINTINS", "MANACAPURU", "TEFÉ", "ITACOATIARA",
    "BENJAMIN CONSTANT", "IRANDUBA", "TABATINGA", "NHAMUNDÁ", "SANTO ANTÔNIO DO IÇÁ",
    "PRESIDENTE FIGUEIREDO", "HUMAITÁ", "BARREIRINHA",
]
TOP_COMPETENCIA = ["Juizado Especial Cível", "Vara Cível", "Turma Recursal", "Câmara Cível"]


def limpar_tipo_acao(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    excluir = df["tipo_acao"].fillna("").str.contains(TIPO_ACAO_EXCLUIDO)
    df.loc[excluir, "tipo_acao"] = None
    return df


def conferir_snapshot(caminho: str) -> None:
    """Para com erro se o arquivo congelado nao bate com o hash do manifesto."""
    import hashlib
    import json
    import os
    with open(f"{SNAPSHOT_DIR}/manifesto.json", encoding="utf-8") as fh:
        esperado = json.load(fh)[os.path.basename(caminho)]["sha256"]
    with open(caminho, "rb") as fh:
        atual = hashlib.sha256(fh.read()).hexdigest()
    if atual != esperado:
        raise RuntimeError(f"Snapshot do TCC alterado: {caminho} (sha256 {atual[:12]} != {esperado[:12]})")


def carregar_coorte() -> pd.DataFrame:
    """Coorte oficial (t0 = distribuicao, foto congelada) ja com a limpeza de tipo_acao aplicada."""
    conferir_snapshot(COORTE_PATH)
    return limpar_tipo_acao(pd.read_parquet(COORTE_PATH))


def carregar_datas_merito() -> pd.DataFrame:
    """Datas de sentenca/acordao/acordo + etiqueta de acordo (foto congelada, mesmos ids)."""
    conferir_snapshot(DATAS_MERITO_PATH)
    return pd.read_parquet(DATAS_MERITO_PATH)


def bucket(serie, top, outros="Outros"):
    return serie.where(serie.isin(top), outros).fillna(outros)


def hiperparametros_fase4() -> dict:
    """Hiperparametros escolhidos na Fase 4 (tuning da RSF + early stopping do XGBoost),
    lidos dos CSVs que a propria Fase 4 grava - Brier, Fase 5 e Fase 6 nunca
    hardcodam esses numeros, pra nao ficarem defasados quando a Fase 4 roda de novo."""
    rsf = pd.read_csv(f"{BASE_DIR}/dados/fase4_rsf_tunada_metricas.csv").iloc[0]
    xgb = pd.read_csv(f"{BASE_DIR}/dados/fase4_xgboost_metricas.csv").iloc[0]
    return {
        "rsf_min_samples_leaf": int(rsf["melhor_min_samples_leaf"]),
        "rsf_n_estimators": int(rsf["n_estimators"]),
        "xgb_num_boost_round": int(xgb["best_iteration"]) + 1,
        "xgb_base_score": float(xgb["base_score"]),
    }
