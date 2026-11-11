"""Busca UMA vez as linhas reais do LexPre com as queries copiadas da v1 (source_queries.py da V2) e salva em rows.pkl.

Rodar com o Python da V2, de apps/api (lê o .env de lá). Só o LexPre é aberto (NG/LAADV desligados).
    python fetch_rows.py <saida_dir>
"""

import asyncio
import os
import pickle
import sys
from pathlib import Path

for d in ("NG", "LAADV", "LEXFLOW"):
    os.environ[f"DB_{d}_URL"] = ""
    os.environ[f"DB_{d}_HOST"] = ""

from app.config import Settings
from app.database import DatabaseManager
from app.sources import PgSourceFetcher

QUERIES = [
    "log_setor_demanda_lexpre_NG",
    "setor_func_lexpre_NG",
    "comercial_lexpre_NG",
    "demanda_rubrica_reunida_lexpre_NG",
    "audit_log_demandas_canceladas_lexpre_NG",
]


async def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    dbs = DatabaseManager(Settings())
    await dbs.initialize()
    try:
        fonte = PgSourceFetcher(dbs, "lexpre")
        rows = {}
        for q in QUERIES:
            rows[q] = await fonte.fetch(q)
            print(q, len(rows[q]))
    finally:
        await dbs.close()
    (out / "rows.pkl").write_bytes(pickle.dumps(rows))


asyncio.run(main())
