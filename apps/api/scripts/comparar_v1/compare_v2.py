"""Lado V2 da comparação: roda os módulos da V2 sobre as MESMAS linhas (rows.pkl) e compara com a v1.

Rodar com o Python da V2, de dentro de lexhub-platform/apps/api/src:
    python compare_v2.py <saida_dir>
Compara campo a campo (sem `opcoes_filtro`, que é novo da V2) e escreve <saida_dir>/relatorio.json.
"""

import asyncio
import json
import pickle
import sys
from datetime import date
from pathlib import Path

from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardContext, Period

out = Path(sys.argv[1])
rows = pickle.loads((out / "rows.pkl").read_bytes())

HOJE = date.today()
INICIO_MES = HOJE.replace(day=1)
ANT_FIM = INICIO_MES.fromordinal(INICIO_MES.toordinal() - 1)
ANT_INI = ANT_FIM.replace(day=1)
PERIODOS = {"mes_anterior": (ANT_INI, ANT_FIM), "mes_atual": (INICIO_MES, HOJE)}
ESCRITORIOS = {"NG": "1", "LA": "2", "RJ": "3"}
KEYS = [
    "protocolo-lexpre",
    "org-documentos-lexpre",
    "peticionamento-lexpre",
    "pendencias-lexpre",
    "comercial-lexpre",
    "comissao-lexpre",
]


class Fonte:
    async def fetch(self, name):
        return rows[name]

    def synced_at(self):
        return None


def diffs(a, b, path=""):
    """Lista de diferenças (caminho, v1, v2). Floats com tolerância de arredondamento."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((f"{path}.{k}", a.get(k, "<ausente>"), b.get(k, "<ausente>")))
            else:
                out += diffs(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [(f"{path}[len]", len(a), len(b))]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diffs(x, y, f"{path}[{i}]")]
    numeros = (isinstance(a, float) or isinstance(b, float)) and a is not None and b is not None
    perto = numeros and abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(a)))
    if perto:
        return []
    return [] if a == b else [(path, a, b)]


async def main():
    relatorio = {}
    for key in KEYS:
        mod = DASHBOARDS[key]
        filtros = {f: [] for f in mod.filters}
        for unidade, ref in ESCRITORIOS.items():
            for nome_p, (ini, fim) in PERIODOS.items():
                caso = f"{key}_{unidade}_{nome_p}"
                ctx = DashboardContext(
                    source=Fonte(),
                    unit_ref=ref,
                    period=Period(ini, fim),
                    filters=filtros,
                    can_see_commission=True,
                )
                v2 = json.loads(json.dumps(await mod.build(ctx), default=str))
                v2.pop("opcoes_filtro", None)
                v1 = json.loads((out / f"v1_{caso}.json").read_text(encoding="utf-8"))
                d = diffs(v1, v2)
                relatorio[caso] = {"diferencas": len(d), "exemplos": d[:10]}
                print(f"{caso:55s} {'IGUAL' if not d else f'{len(d)} DIFERENÇAS'}")
    (out / "relatorio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )


asyncio.run(main())
