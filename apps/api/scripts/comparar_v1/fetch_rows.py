"""Busca UMA vez as linhas reais de um banco de origem com as queries copiadas da v1 e salva em rows.pkl.

Rodar com o Python da V2, de apps/api (lê o .env de lá). Só o banco pedido é aberto.
    python fetch_rows.py <saida_dir> <lexpre|lexflow>
As queries são as que os dashboards da V2 daquela fonte declaram (DashboardModule.queries).
"""

import asyncio
import os
import pickle
import sys
from pathlib import Path

FONTE = sys.argv[2]
for d in ("NG", "LAADV", "LEXFLOW", "LEXPRE"):
    if d.lower() != FONTE:
        os.environ[f"DB_{d}_URL"] = ""
        os.environ[f"DB_{d}_HOST"] = ""

from app.config import Settings
from app.dashboards import DASHBOARDS
from app.database import DatabaseManager
from app.sources import PgSourceFetcher

QUERIES = list(
    dict.fromkeys(q for m in DASHBOARDS.values() if m.source_db == FONTE for q in m.queries)
)


async def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    dbs = DatabaseManager(Settings())
    await dbs.initialize()
    try:
        fonte = PgSourceFetcher(dbs, FONTE)
        rows = {}
        for q in QUERIES:
            rows[q] = await fonte.fetch(q)
            print(q, len(rows[q]))
    finally:
        await dbs.close()
    (out / "rows.pkl").write_bytes(pickle.dumps(rows))


asyncio.run(main())
