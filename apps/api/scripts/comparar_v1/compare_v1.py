"""Lado v1 da comparação: busca as linhas reais do LexPre UMA vez (fetch da v1), salva, e roda os builders da v1.

Rodar com o Python da v1, de dentro de api_dashboards/src:
    python compare_v1.py <saida_dir>
Gera <saida_dir>/rows.pkl (linhas por query) e <saida_dir>/v1_<caso>.json.
"""

import asyncio
import json
import pickle
import sys
from datetime import date
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

import app.dashboard_routes as r

FETCH = {
    "log_setor_demanda_lexpre_NG": "fetch_log_setor_demanda_lexpre_ng",
    "setor_func_lexpre_NG": "fetch_setor_func_lexpre",
    "comercial_lexpre_NG": "fetch_comercial_lexpre_ng",
    "demanda_rubrica_reunida_lexpre_NG": "fetch_demanda_rubrica_reunida_lexpre",
    "audit_log_demandas_canceladas_lexpre_NG": "fetch_audit_log_demandas_canceladas_lexpre",
}

# Períodos: mês fechado anterior e o mês corrente até hoje (o padrão da v1 e da V2).
HOJE = date.today()
INICIO_MES = HOJE.replace(day=1)
ANT_FIM = INICIO_MES.fromordinal(INICIO_MES.toordinal() - 1)
ANT_INI = ANT_FIM.replace(day=1)
PERIODOS = {"mes_anterior": (ANT_INI, ANT_FIM), "mes_atual": (INICIO_MES, HOJE)}
ESCRITORIOS = {"NG": 1, "LA": 2, "RJ": 3}


async def main():
    rows = pickle.loads(
        (out / "rows.pkl").read_bytes()
    )  # mesmas linhas que a V2 vai usar (fetch_rows.py)

    # Daqui em diante a v1 usa exatamente as mesmas linhas.
    for q, fn in FETCH.items():
        data = rows[q]

        async def _fixo(data=data):
            return data

        setattr(r, fn, _fixo)

    casos = {}
    for unidade, esc in ESCRITORIOS.items():
        for nome_p, (ini, fim) in PERIODOS.items():
            sfx = f"{unidade}_{nome_p}"
            casos[f"protocolo-lexpre_{sfx}"] = r._build_protocolo_lexpre_response(
                esc, ini, fim, None, None, None, None
            )
            casos[f"org-documentos-lexpre_{sfx}"] = r._build_org_doc_lexpre_response(
                esc, ini, fim, None, None, None, None
            )
            casos[f"peticionamento-lexpre_{sfx}"] = r._build_peticionamento_lexpre_response(
                esc, ini, fim, None, None, None, None
            )
            casos[f"pendencias-lexpre_{sfx}"] = r._build_pendencia_lexpre_response(
                esc, ini, fim, None, None, None
            )
            casos[f"comercial-lexpre_{sfx}"] = r._build_comercial_lexpre_response(
                esc, ini, fim, None, None, None, None, None
            )
            # Comissão: gestor (sem usuário = sem restrição na v1).
            casos[f"comissao-lexpre_{sfx}"] = r._build_comercial_lexpre_response(
                esc,
                ini,
                fim,
                None,
                None,
                None,
                None,
                None,
                usuario_logado=None,
                escopo_proprio=True,
            )
    for nome, coro in casos.items():
        res = await coro
        (out / f"v1_{nome}.json").write_text(
            json.dumps(res.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, indent=1),
            encoding="utf-8",
        )
    print("casos v1:", len(casos))
    print("periodos:", {k: (a.isoformat(), b.isoformat()) for k, (a, b) in PERIODOS.items()})


asyncio.run(main())
