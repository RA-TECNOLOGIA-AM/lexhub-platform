# -*- coding: utf-8 -*-
"""
Extrai a coorte de sobrevivencia processual para uso do pesquisador (Fases 3/4).

Pipeline, pensado para rodar via cron (sem intervencao manual):
  1. Roda a query de coorte (coorte_sobrevivencia_2_estagios.sql) contra o LexFlow.
  2. Salva a coorte em dados/coorte_sobrevivencia.{csv,parquet}.

O dashboard "Sobrevivencia Processual" do LexHub NAO depende mais deste script
(14/10/2026): a api_dashboards roda a mesma coorte (query `tcc_sobrevivencia_processual`
em src/app/queries.py) e monta o payload em
src/app/analyses/GERAL/tcc_sobrevivencia_processual.py. Mudou a definicao da coorte
no .sql daqui? Replicar la tambem.

Agendado via crontab para rodar todo dia as 18h. Loga tudo em TCC - Luiz/logs/refresh.log.

Covariaveis (13/10/2026): comarca e competencia sao atributos fixos do processo
(entram tambem como covariavel no Cox/Fine-Gray, ver scripts/fase3_*.py). Fase,
subfase, juiz_1g e relator_2g sao estado atual/pos-desfecho do processo - saem
so como ranking exploratorio aqui no dashboard, nunca como covariavel do
modelo formal (ver nota no cabecalho de coorte_sobrevivencia_2_estagios.sql).

Pseudonimizacao (19/10/2026, Fase 1 do plano): `numero_processo` e o unico
identificador real que ainda saia em texto puro nos arquivos de pesquisa (o
endpoint de producao, `tcc_sobrevivencia_processual` em queries.py, nunca expos
esse campo). Numero de processo da pra consultar publicamente no site do
tribunal e achar as partes reais, entao conta como dado pessoal pra fins de
LGPD/conduta etica do TCC. A partir desta versao, o numero cru e trocado por um
hash SHA-256 truncado (16 hex) com salt fixo do projeto logo apos a extracao,
antes de qualquer gravacao em disco - o valor original nunca chega a tocar
CSV/parquet. Nao e reversivel sem o salt (que fica so neste arquivo, nunca
publicado). `id` (serial do Postgres) continua sendo exportado sem hash: exige
acesso direto ao banco pra virar um numero de processo real, risco bem menor,
e e usado internamente pra cruzar com Inconsistencias_Datas_Processo.csv
durante a auditoria de qualidade de dado (esse CSV de triagem operacional, por
sua vez, continua com numero_processo em texto puro de proposito - e pra uso
interno de quem vai corrigir o cadastro na origem, nao faz parte da coorte de
pesquisa em si).
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import asyncio
import hashlib
import os
from datetime import datetime

from dotenv import load_dotenv

BASE_DIR = ML_DIR
SQL_PATH = f"{BASE_DIR}/coorte_sobrevivencia_2_estagios.sql"
# 10/11/2026: grava em *_atual. O TCC NAO le estes arquivos - usa a foto congelada em
# dados/congelado_20261109/ (ver coorte_comum.py). Pra atualizar o estudo de proposito,
# criar uma nova pasta congelada a partir daqui e apontar coorte_comum.SNAPSHOT_DIR pra ela.
CSV_OUT = f"{BASE_DIR}/dados/coorte_sobrevivencia_atual.csv"
PARQUET_OUT = f"{BASE_DIR}/dados/coorte_sobrevivencia_atual.parquet"

# Salt fixo do projeto - so define o "namespace" do hash, nao precisa ser segredo
# forte (a pseudonimizacao aqui e contra re-identificacao casual/publicacao
# acidental, nao contra um atacante com acesso ao banco de producao).
SALT_PSEUDONIMIZACAO = "tcc-luiz-reis-sobrevivencia-processual-2026"

load_dotenv((_os_ml.environ.get("LEXHUB_API_ENV") or REPO_DIR + "/apps/api/.env"))

import asyncpg
import pandas as pd


def log(msg: str) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}", flush=True)


def pseudonimizar_numero_processo(df: pd.DataFrame) -> pd.DataFrame:
    """Troca numero_processo por um hash SHA-256 truncado (16 hex). Nao reversivel sem o salt."""
    def hashear(numero: str) -> str:
        return hashlib.sha256(f"{SALT_PSEUDONIMIZACAO}:{numero}".encode("utf-8")).hexdigest()[:16]

    df = df.copy()
    df["numero_processo_hash"] = df["numero_processo"].astype(str).map(hashear)
    df = df.drop(columns=["numero_processo"])
    # numero_processo_hash logo depois de id, no lugar onde numero_processo estava
    colunas = [c for c in df.columns if c not in ("id", "numero_processo_hash")]
    return df[["id", "numero_processo_hash", *colunas]]


async def extrair_coorte() -> pd.DataFrame:
    with open(SQL_PATH, "r", encoding="utf-8") as f:
        query = f.read()

    conn = await asyncpg.connect(
        host=os.environ["DB_LEXFLOW_HOST"],
        port=os.environ["DB_LEXFLOW_PORT"],
        database=os.environ["DB_LEXFLOW_NAME"],
        user=os.environ["DB_LEXFLOW_USER"],
        password=os.environ["DB_LEXFLOW_PASSWORD"],
    )
    try:
        rows = await conn.fetch(query)
    finally:
        await conn.close()

    df = pd.DataFrame([dict(r) for r in rows])
    df = pseudonimizar_numero_processo(df)
    df.to_csv(CSV_OUT, index=False, sep=";", encoding="utf-8-sig")
    df.to_parquet(PARQUET_OUT, index=False)
    log(f"Coorte extraida: {len(df)} processos -> {PARQUET_OUT}")
    return df


async def main():
    log("Iniciando extracao da coorte de Sobrevivencia Processual")
    try:
        await extrair_coorte()
        log("Refresh concluido com sucesso")
    except Exception as exc:  # noqa: BLE001 - job de cron, queremos logar e sair com erro visivel
        log(f"ERRO no refresh: {exc!r}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
