"""Confere com dados reais que o recorte por unidade (app/unit_scope.py) não muda nenhum número.

Rodar de apps/api, com o .env que acessa o LexFlow (só leitura):
    $env:PYTHONPATH = "$PWD\\src"
    .venv\\Scripts\\python.exe scripts\\comparar_v1\\conferir_recorte_unidade.py <saida_dir>

1. Busca UMA vez, no LexFlow, as queries dos dashboards com recorte: a inteira e o recorte de cada unidade
   (o SQL de verdade, `nome@escritorio`). Salva em <saida_dir>/recorte.pkl e reaproveita se já existir.
   Custa uns 0,5 GB de egress uma vez; a pasta tem dados do LexFlow: mantenha fora do Git.
2. Confere que o SQL do recorte devolve exatamente as linhas da unidade que a query inteira devolve.
3. Roda cada dashboard com `unit_scoped` (dados e cada exportação) por unidade e período, uma vez com a
   query inteira (como era) e outra com o recorte (como fica), e compara o JSON campo a campo.

Imprime IGUAL ou o número de diferenças por caso e grava <saida_dir>/relatorio_recorte.json.
Sai com código 1 se houver qualquer diferença.
"""

import asyncio
import json
import os
import pickle
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

# Só o LexFlow é aberto.
for _db in ("NG", "LAADV", "LEXPRE"):
    os.environ[f"DB_{_db}_URL"] = ""
    os.environ[f"DB_{_db}_HOST"] = ""

from app.config import Settings
from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardContext, Period
from app.database import DatabaseManager
from app.sources import PgSourceFetcher
from app.unit_scope import (
    ESCRITORIO_POR_UNIDADE,
    UNIT_COLUMN,
    ordem_canonica,
    scope_source,
    scoped_name,
)

OUT = Path(sys.argv[1])
UNIDADES = ("NG", "LA", "RJ")
HOJE = date.today()
INICIO_MES = HOJE.replace(day=1)
ANT_FIM = date.fromordinal(INICIO_MES.toordinal() - 1)
PERIODOS = {
    "mes_atual": (INICIO_MES, HOJE),
    "mes_anterior": (ANT_FIM.replace(day=1), ANT_FIM),
    "ano": (HOJE.replace(month=1, day=1), HOJE),
}
MODULOS = {k: m for k, m in DASHBOARDS.items() if m.source_db == "lexflow" and m.unit_scoped}


def _todas_as_queries() -> list[str]:
    return list(dict.fromkeys(q for m in MODULOS.values() for q in m.queries))


async def buscar() -> dict[str, list[dict]]:
    arquivo = OUT / "recorte.pkl"
    if arquivo.exists():
        print(f"Reaproveitando {arquivo}")
        return pickle.loads(arquivo.read_bytes())
    # Só o LexFlow é usado: o Supabase da plataforma (login) fica com valores que nunca são chamados.
    dbs = DatabaseManager(Settings(SUPABASE_URL="http://localhost", SUPABASE_PUBLISHABLE_KEY="-"))
    dbs.start()
    inicio = time.monotonic()
    while not dbs.is_up("lexflow"):
        if time.monotonic() - inicio > 60:
            raise SystemExit("LexFlow não conectou em 60 s: confira DB_LEXFLOW_* no .env")
        await asyncio.sleep(0.5)
    rows: dict[str, list[dict]] = {}
    try:
        fonte = PgSourceFetcher(dbs, "lexflow")
        nomes = _todas_as_queries()
        nomes += [
            scoped_name(q, e)
            for q in nomes
            if q in UNIT_COLUMN
            for e in ESCRITORIO_POR_UNIDADE.values()
        ]
        for nome in nomes:
            rows[nome] = await fonte.fetch(nome)
            print(f"{nome:50s} {len(rows[nome]):>7} linhas")
    finally:
        await dbs.close()
    OUT.mkdir(parents=True, exist_ok=True)
    arquivo.write_bytes(pickle.dumps(rows))
    return rows


def _chave(row: dict) -> str:
    return json.dumps(row, sort_keys=True, default=str)


def conferir_sql(rows: dict[str, list[dict]]) -> list[str]:
    """O recorte do banco = as linhas da unidade na query inteira (mesmas linhas, mesmas quantidades)."""
    erros = []
    for nome, linhas in rows.items():
        if "@" in nome or nome not in UNIT_COLUMN:
            continue
        coluna = UNIT_COLUMN[nome]
        for escritorio in ESCRITORIO_POR_UNIDADE.values():
            esperado = Counter(_chave(r) for r in linhas if r.get(coluna) == escritorio)
            veio = Counter(_chave(r) for r in rows[scoped_name(nome, escritorio)])
            ok = esperado == veio
            print(f"SQL {scoped_name(nome, escritorio):45s} {'IGUAL' if ok else 'DIFERENTE'}")
            if not ok:
                erros.append(scoped_name(nome, escritorio))
    return erros


class Fonte:
    """As linhas salvas, pelo nome que o cache usaria (a inteira ou o recorte 'nome@escritorio')."""

    def __init__(self, rows):
        self._rows = rows

    async def fetch(self, name):
        # Cópia (o cálculo nunca vê a lista do outro lado), na ordem fixa que o PgSourceFetcher aplica: o
        # recorte.pkl pode ter sido salvo antes dela.
        return ordem_canonica(name, [dict(r) for r in self._rows[name]])

    def synced_at(self):
        return None


def diffs(a, b, path=""):
    """(caminho, inteira, recorte) de cada diferença. Floats com tolerância de arredondamento."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
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
    if numeros and abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(a))):
        return []
    return [] if a == b else [(path, a, b)]


def _ctx(modulo, unidade, ini, fim, fonte, opcoes=None):
    return DashboardContext(
        source=fonte,
        source_db="lexflow",
        unit_ref=unidade,
        period=Period(ini, fim),
        filters={f: [] for f in modulo.filters},
        can_see_commission=True,
        export_options=opcoes or {},
    )


def _relatorios(modulo):
    """(nome, ExportSpec, opções) de cada exportação, com cada escolha de cada opção."""
    specs = ([("export", modulo.export)] if modulo.export else []) + list(
        modulo.export_reports.items()
    )
    for nome, spec in specs:
        padrao = {o.key: next(iter(o.choices)) for o in spec.options}
        yield nome, spec, padrao
        for opcao in spec.options:
            for escolha in list(opcao.choices)[1:]:
                yield f"{nome}[{opcao.key}={escolha}]", spec, {**padrao, opcao.key: escolha}


async def _rodar(trabalho):
    try:
        return json.loads(json.dumps(await trabalho, default=str))
    except Exception as exc:  # noqa: BLE001 — o erro também é resultado: os dois lados precisam dar o mesmo
        return {"<erro>": f"{type(exc).__name__}: {exc}"}


def _sem_ordem(valor):
    """O mesmo JSON com cada lista ordenada: compara o conteúdo sem olhar a posição dos itens."""
    if isinstance(valor, dict):
        return {k: _sem_ordem(v) for k, v in valor.items()}
    if isinstance(valor, list):
        itens = [_sem_ordem(v) for v in valor]
        return sorted(itens, key=lambda v: json.dumps(v, sort_keys=True, default=str))
    return valor


async def comparar(rows) -> dict:
    relatorio = {}
    inteira = Fonte(rows)
    for key, modulo in MODULOS.items():
        for unidade in UNIDADES:
            recorte = scope_source(Fonte(rows), "lexflow", unidade, modulo.unit_scoped)
            for nome_p, (ini, fim) in PERIODOS.items():
                trabalhos = [
                    (
                        "dados",
                        lambda f, m=modulo, u=unidade, a=ini, b=fim: m.build(_ctx(m, u, a, b, f)),
                    )
                ]
                trabalhos += [
                    (
                        nome,
                        lambda f, s=spec, o=opcoes, m=modulo, u=unidade, a=ini, b=fim: s.rows(
                            _ctx(m, u, a, b, f, o)
                        ),
                    )
                    for nome, spec, opcoes in _relatorios(modulo)
                ]
                for nome, fazer in trabalhos:
                    caso = f"{key}_{unidade}_{nome_p}_{nome}"
                    antes = await _rodar(fazer(inteira))
                    depois = await _rodar(fazer(recorte))
                    d = diffs(antes, depois)
                    # Mesmos itens em outra posição de alguma lista (empates sem critério) = "SÓ ORDEM".
                    conteudo = diffs(_sem_ordem(antes), _sem_ordem(depois)) if d else []
                    estado = "IGUAL" if not d else ("SÓ ORDEM" if not conteudo else "DIFERENÇAS")
                    relatorio[caso] = {
                        "estado": estado,
                        "diferencas": len(conteudo),
                        "so_ordem": bool(d) and not conteudo,
                        "exemplos": (conteudo or d)[:10],
                    }
                    erro = " (erro nos dois lados)" if "<erro>" in antes else ""
                    extra = f" ({len(conteudo)})" if conteudo else ""
                    print(f"{caso:75s} {estado}{extra}{erro}")
    return relatorio


async def main():
    rows = await buscar()
    erros_sql = conferir_sql(rows)
    relatorio = await comparar(rows)
    relatorio["_sql"] = {"diferentes": erros_sql}
    (OUT / "relatorio_recorte.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )
    casos = [v for k, v in relatorio.items() if not k.startswith("_")]
    estados = {
        e: sum(1 for v in casos if v["estado"] == e) for e in ("IGUAL", "SÓ ORDEM", "DIFERENÇAS")
    }
    print(
        f"\n{estados['IGUAL']} de {len(casos)} casos iguais, {estados['SÓ ORDEM']} só com outra ordem, "
        f"{estados['DIFERENÇAS']} com conteúdo diferente; SQL diferente: {erros_sql or 'nenhum'}"
    )
    # Ordem diferente já muda o que a tela mostra (itens empatados trocam de lugar): também reprova.
    if estados["SÓ ORDEM"] or estados["DIFERENÇAS"] or erros_sql:
        sys.exit(1)


asyncio.run(main())
