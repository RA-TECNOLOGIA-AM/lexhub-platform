"""Lado v1 da comparação para o LexFlow: roda as ROTAS da v1 (Execução, Acordos, Recursal) sobre rows.pkl.

Rodar com o Python da v1, com PYTHONPATH = api_dashboards/src:
    python compare_v1_lexflow.py <saida_dir>
A v1 busca pelas próprias funções; só a camada de cache (fetch_data_with_cache) é trocada para devolver
as linhas de rows.pkl, com o mesmo recorte de situação do processo que ela aplica.
"""

import asyncio
import inspect
import json
import pickle
import sys
from datetime import date
from pathlib import Path

out = Path(sys.argv[1])

import app.dashboard_routes as r
from app.situacao_processo import aplicar_filtro_situacao_processo

HOJE = date.today()
INICIO_MES = HOJE.replace(day=1)
ANT_FIM = INICIO_MES.fromordinal(INICIO_MES.toordinal() - 1)
ANT_INI = ANT_FIM.replace(day=1)
PERIODOS = {"mes_anterior": (ANT_INI, ANT_FIM), "mes_atual": (INICIO_MES, HOJE)}

# (key na V2, unidade) -> rota da v1
ROTAS = {
    ("execucao", "NG"): r.get_execucao_dashboard,
    ("execucao", "LA"): r.get_execucao_LA_dashboard,
    ("execucao", "RJ"): r.get_execucao_rj_dashboard,
    ("acordos", "NG"): r.get_execucao_acordos_ng_dashboard,
    ("acordos", "LA"): r.get_execucao_acordos_la_dashboard,
    ("acordos", "RJ"): r.get_execucao_acordos_rj_dashboard,
    ("recursal", "NG"): r.get_recursal_NG_dashboard,
    ("recursal", "LA"): r.get_recursal_LA_dashboard,
}


async def main():
    rows = pickle.loads((out / "rows.pkl").read_bytes())

    async def _fetch_fixo(query_name, cache_key=None, **_):
        return aplicar_filtro_situacao_processo(query_name, rows[query_name])

    r.fetch_data_with_cache = _fetch_fixo

    n = 0
    for (key, unidade), rota in ROTAS.items():
        original = inspect.unwrap(rota)
        nomes = [
            p for p in inspect.signature(original).parameters if p not in ("from_date", "to_date")
        ]
        for nome_p, (ini, fim) in PERIODOS.items():
            res = await original(from_date=ini, to_date=fim, **{p: None for p in nomes})
            (out / f"v1_{key}_{unidade}_{nome_p}.json").write_text(
                json.dumps(
                    res.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=1
                ),
                encoding="utf-8",
            )
            n += 1
    print("casos v1:", n)


asyncio.run(main())
