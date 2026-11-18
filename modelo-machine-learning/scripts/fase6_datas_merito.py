# -*- coding: utf-8 -*-
"""
Fase 6 (extensao, 09/11/2026) - busca no LexFlow as DATAS de sentenca (1G), acordao (2G) e acordo
dos mesmos ids da coorte de modelagem (fase4_coorte_com_split.parquet), sem reextrair a
coorte (mantem a mesma foto do banco das Fases 2-6). Usado por fase6_procedencia_2g.py
para separar treino/teste pela DATA DO ACORDAO.

So sai id (serial interno) + datas - nenhum numero de processo (ver pseudonimizacao em
atualizar_dashboard_tcc.py). Mesma regra de data valida da coorte (1971 .. hoje + 730d).

Rodar: TCC - Luiz/.venv/bin/python scripts/fase6_datas_merito.py
"""
import os as _os_ml

# V2 (modelo-machine-learning/): a pasta do estudo vem de LEXHUB_ML_DIR; sem ela, é esta pasta (a de scripts/ menos um
# nível). Antes (pasta "TCC - Luiz" da v1) o caminho era fixo na máquina do pesquisador.
ML_DIR = _os_ml.environ.get("LEXHUB_ML_DIR") or _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__)))
REPO_DIR = _os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.dirname(_os_ml.path.abspath(__file__))))
import asyncio
import os

import asyncpg
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = ML_DIR
load_dotenv((_os_ml.environ.get("LEXHUB_API_ENV") or REPO_DIR + "/apps/api/.env"))

SQL = """
select p.id,
       case when (p.sentenca at time zone 'America/Manaus')::date
                 between '1971-01-01' and current_date + 730
            then (p.sentenca at time zone 'America/Manaus')::date end as sentenca_d,
       case when p.acordao_data between '1971-01-01' and current_date + 730
            then p.acordao_data end as acordao_d,
       case when (p.acordo_fechado at time zone 'America/Manaus')::date
                 between '1971-01-01' and current_date + 730
            then (p.acordo_fechado at time zone 'America/Manaus')::date end as acordo_d,
       -- etiqueta de acordo (09/11/2026): pega acordo sem data preenchida. Duas fontes no
       -- LexFlow: tabela processo_etiqueta e a lista jsonb id_etiquetas_lista. Fase pelo nome
       -- quando a etiqueta diz (PRE/POS-SENTENCA); senao 'GENERICA' (classificada no script).
       (select case when bool_or(e.nome ilike '%pré-sentença%' or e.nome ilike '%pre-sentenca%'
                                 or e.nome ilike '%pré sentença%') then 'PRE'
                    when bool_or(e.nome ilike '%pós-sentença%' or e.nome ilike '%pos-sentenca%') then 'POS'
                    else 'GENERICA' end
          from etiquetas e
         where e.nome ilike '%acordo%'
           and (exists (select 1 from processo_etiqueta pe where pe.id_processo = p.id and pe.id_etiqueta = e.id)
                or coalesce(p.id_etiquetas_lista::jsonb @> to_jsonb(array[e.id]), false))
        having count(*) > 0) as etiqueta_acordo
from processo p
where p.id = any($1::int[])
"""


async def main():
    # ids da coorte ATUAL inteira (extraida por atualizar_dashboard_tcc.py), p/ a foto nova ter
    # as datas de todos os processos - o split e refeito depois a partir da foto
    ids = pd.read_parquet(f"{BASE_DIR}/dados/coorte_sobrevivencia_atual.parquet", columns=["id"])["id"]
    conn = await asyncpg.connect(
        host=os.environ["DB_LEXFLOW_HOST"], port=os.environ["DB_LEXFLOW_PORT"],
        database=os.environ["DB_LEXFLOW_NAME"], user=os.environ["DB_LEXFLOW_USER"],
        password=os.environ["DB_LEXFLOW_PASSWORD"],
    )
    try:
        rows = await conn.fetch(SQL, [int(i) for i in ids])
    finally:
        await conn.close()
    df = pd.DataFrame([dict(r) for r in rows])
    # 10/11/2026: grava em *_atual - o TCC le a versao congelada (coorte_comum.DATAS_MERITO_PATH)
    df.to_parquet(f"{BASE_DIR}/dados/fase6_datas_merito_atual.parquet", index=False)
    print(f"{len(df)} ids | sentenca_d: {df.sentenca_d.notna().sum()} | acordao_d: {df.acordao_d.notna().sum()} | "
          f"acordo_d: {df.acordo_d.notna().sum()} | etiqueta_acordo: {df.etiqueta_acordo.value_counts().to_dict()}")


if __name__ == "__main__":
    asyncio.run(main())
