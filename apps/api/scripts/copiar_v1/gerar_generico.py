"""Gera a cópia SEM mudança de dashboards "genéricos" da v1 (ramos de `_get_dashboard_response`).

Mesmo método da cópia do LexFlow (app/analyses/v1_dashboard_generico.py), agora como script reutilizável:
lê api_dashboards/src/app/dashboard_routes.py pela AST e escreve um módulo com
  * os handlers das rotas (sem os decoradores), achados pela chamada `_get_dashboard_response("<nome>", ...)`;
  * `_get_dashboard_response` com o mesmo início da v1, só com os ramos dos dashboards pedidos
    (blocos e variáveis só de outros dashboards saem; parâmetros que sobram sem uso também);
  * tudo que eles usam no dashboard_routes.py (funções, classes, constantes), na ordem da v1;
  * os fetch_* trocados por `_fetch_v2('<query>')` (fonte da V2 + recorte de situação do processo);
    fontes de outro banco saem de FETCHES_BY_DASHBOARD (um módulo da V2 lê um banco só);
  * FETCHES_BY_DASHBOARD, DASHBOARD_NAMES, HANDLERS e QUERIES_POR_DASHBOARD para a casca.
Também copia, sem mudança, os módulos app/analyses/* da v1 que ainda faltam na V2.

Uso (PowerShell, em apps/api):
  .venv\\Scripts\\python.exe scripts\\copiar_v1\\gerar_generico.py --banco ng \\
      --saida src\\app\\analyses\\v1_dashboard_generico_ng.py protocolo peticionamento org-documentos pendencias
"""

import argparse
import ast
import builtins
import re
import shutil
import sys
from pathlib import Path

V1_APP = Path(r"C:\workspace\api_dashboards\src\app")
V2_APP = Path(__file__).resolve().parents[2] / "src" / "app"
ROUTES = V1_APP / "dashboard_routes.py"

# Módulos da v1 que na V2 têm outro caminho.
RENOMEAR_IMPORT = {"app.situacao_processo": "app.analyses.situacao_processo"}
# Nomes que a V2 gera (não copia da v1).
GERADOS = {
    "FETCHES_BY_DASHBOARD",
    "DASHBOARD_NAMES",
    "_gather_dashboard_fetches",
    "router",
    "_dashboard_endpoint",
}

AVISO_BLOCO = "# V2: (bloco de outros dashboards da v1 omitido)"
AVISO_VAR = "# V2: (variável só de outros dashboards da v1 omitida)"
GATHER_V2 = """\
    # V2: mesma busca da v1 (_gather_dashboard_fetches = gather com return_exceptions)
    results = await asyncio.gather(*[fn() for _, fn in fetches_config], return_exceptions=True)
    # V2: banco de origem fora do ar = 503 na casca (a v1 seguia com a fonte vazia quando havia mais de uma)
    for res in results:
        if isinstance(res, SourceUnavailable):
            raise res"""


def nomes_usados(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def nomes_lidos(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


class V1:
    def __init__(self) -> None:
        self.src = ROUTES.read_text(encoding="utf-8")
        self.tree = ast.parse(self.src)
        self.defs: dict[str, ast.stmt] = {}  # nome -> última definição no topo do módulo
        self.imports: dict[str, tuple[str, str]] = {}  # nome local -> (módulo, nome original)
        for stmt in self.tree.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.defs[stmt.name] = stmt
            elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                alvos = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                for alvo in alvos:
                    for n in ast.walk(alvo):
                        if isinstance(n, ast.Name):
                            self.defs[n.id] = stmt
            elif isinstance(stmt, ast.ImportFrom) and stmt.module:
                for a in stmt.names:
                    self.imports[a.asname or a.name] = (stmt.module, a.name)
            elif isinstance(stmt, ast.Import):
                for a in stmt.names:
                    self.imports[a.asname or a.name.split(".")[0]] = (a.name, "")

    def seg(self, node: ast.AST) -> str:
        return ast.get_source_segment(self.src, node, padded=True)

    def seg_def(self, node: ast.stmt) -> str:
        """Definição do topo do módulo com os decoradores (ex.: @dataclass), linhas inteiras da v1."""
        inicio = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        return "\n".join(self.src.splitlines()[inicio - 1 : node.end_lineno])

    def fetches(self) -> dict[str, list[tuple[str, str]]]:
        """FETCHES_BY_DASHBOARD da v1: dashboard -> [(chave, fetch_*)] (expande as listas somadas)."""
        listas: dict[str, list[tuple[str, str]]] = {}

        def avaliar(expr: ast.expr) -> list[tuple[str, str]]:
            if isinstance(expr, ast.List):
                return [(e.elts[0].value, e.elts[1].id) for e in expr.elts]
            if isinstance(expr, ast.BinOp):
                return avaliar(expr.left) + avaliar(expr.right)
            if isinstance(expr, ast.Name):
                return listas[expr.id]
            raise ValueError(f"FETCHES_BY_DASHBOARD: expressão não suportada {ast.dump(expr)[:80]}")

        resultado: dict[str, list[tuple[str, str]]] = {}
        for stmt in self.tree.body:
            if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                continue
            alvo = stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target
            if not isinstance(alvo, ast.Name):
                continue
            if alvo.id.startswith("_FETCHES_") and isinstance(stmt.value, (ast.List, ast.BinOp)):
                listas[alvo.id] = avaliar(stmt.value)
            if alvo.id == "FETCHES_BY_DASHBOARD":
                for k, v in zip(stmt.value.keys, stmt.value.values):
                    resultado[k.value] = avaliar(v)
        return resultado

    def query_do_fetch(self, nome: str) -> str:
        fn = self.defs[nome]
        for n in ast.walk(fn):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == "fetch_data_with_cache"
            ):
                return n.args[0].value
        raise ValueError(f"{nome}: não chama fetch_data_with_cache('<query>', ...)")

    def handler(self, dashboard: str) -> ast.AsyncFunctionDef:
        """A rota GET (fora as /export) que chama _get_dashboard_response("<dashboard>", ...)."""
        achados = []
        for stmt in self.tree.body:
            if not isinstance(stmt, ast.AsyncFunctionDef):
                continue
            rota = any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and d.func.attr == "get"
                and d.args
                and isinstance(d.args[0], ast.Constant)
                and not d.args[0].value.endswith("/export")
                for d in stmt.decorator_list
            )
            for n in ast.walk(stmt):
                if (
                    rota
                    and isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name)
                    and n.func.id == "_get_dashboard_response"
                    and n.args
                    and isinstance(n.args[0], ast.Constant)
                    and n.args[0].value == dashboard
                ):
                    achados.append(stmt)
                    break
        if len(achados) != 1:
            raise ValueError(f"{dashboard}: {len(achados)} rotas chamam _get_dashboard_response")
        return achados[0]


def dashboards_no_teste(test: ast.expr, todos: set[str]) -> set[str]:
    return {n.value for n in ast.walk(test) if isinstance(n, ast.Constant) and n.value in todos}


def podar_if(node: ast.If, pedidos: set[str], todos: set[str]) -> list[ast.stmt] | None:
    """O `if dashboard_name ...` sem os braços de outros dashboards; None = cópia sem mudança."""
    citados = dashboards_no_teste(node.test, todos)
    resto = None
    if node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
        podado = podar_if(node.orelse[0], pedidos, todos)
        if podado is not None:
            resto = podado
    if citados and not (citados & pedidos):
        return resto if resto is not None else node.orelse  # este braço é só de outros dashboards
    if resto is None:
        return None
    novo = ast.If(test=node.test, body=node.body, orelse=resto)
    return [ast.fix_missing_locations(ast.copy_location(novo, node))]


def gerar_get_dashboard_response(
    v1: V1, pedidos: set[str], todos: set[str]
) -> tuple[str, set[str]]:
    fn = v1.defs["_get_dashboard_response"]
    pecas: list[tuple[str, ast.AST | None]] = []  # (texto, nó para análise de uso)
    for stmt in fn.body:
        if isinstance(stmt, ast.If):
            podado = podar_if(stmt, pedidos, todos)
            if podado is None:
                pecas.append((v1.seg(stmt), stmt))
            elif not podado:
                pecas.append((f"    {AVISO_BLOCO}", None))
            else:
                mod = ast.Module(body=podado, type_ignores=[])
                texto = "\n".join("    " + linha for linha in ast.unparse(mod).splitlines())
                pecas.append((texto, mod))
            continue
        if (
            isinstance(stmt, ast.Assign)
            and isinstance(stmt.value, ast.Await)
            and isinstance(stmt.value.value, ast.Call)
            and getattr(stmt.value.value.func, "id", "") == "_gather_dashboard_fetches"
        ):
            pecas.append((GATHER_V2, ast.parse("asyncio; SourceUnavailable")))
            continue
        pecas.append((v1.seg(stmt), stmt))

    # Variáveis atribuídas no topo da função que ninguém mais lê: saem (até não sobrar nenhuma).
    while True:
        removeu = False
        for i, (texto, no) in enumerate(pecas):
            if not isinstance(no, (ast.Assign, ast.AnnAssign)):
                continue
            alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
            nomes = {n.id for a in alvos for n in ast.walk(a) if isinstance(n, ast.Name)}
            lidos = set().union(
                *(nomes_lidos(o) for j, (_, o) in enumerate(pecas) if j != i and o is not None)
            )
            if not (nomes & lidos):
                pecas[i] = (f"    {AVISO_VAR}", None)
                removeu = True
        if not removeu:
            break

    usados = set().union(*(nomes_usados(o) for _, o in pecas if o is not None))
    params = []
    anotacoes: set[str] = set()
    for arg, default in zip(
        fn.args.args, [None] * (len(fn.args.args) - len(fn.args.defaults)) + fn.args.defaults
    ):
        if default is None or arg.arg in usados:
            params.append(
                f"    {v1.seg(arg)}"
                + (f" = {v1.seg(default)}" if default is not None else "")
                + ","
            )
            if arg.annotation is not None:
                anotacoes |= nomes_usados(arg.annotation)
    corpo = "\n".join(t if t.startswith("    ") else "    " + t for t, _ in pecas)
    # Indentação: get_source_segment(padded=True) já devolve a 1ª linha com a indentação original.
    texto = (
        "async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards\n"
        + "\n".join(params)
        + f"\n) -> {v1.seg(fn.returns)}:\n"
        + corpo
        + "\n"
    )
    return texto, usados | anotacoes | nomes_usados(fn.returns)


def gerar(pedidos: list[str], banco: str, saida: Path) -> None:
    v1 = V1()
    sys.path.insert(0, str(V1_APP.parent))
    queries_v1 = ast.literal_eval(_dict_queries())
    fetches_v1 = v1.fetches()
    todos = set(fetches_v1)
    pedidos_set = set(pedidos)

    # fetch_* -> query; fontes de outro banco saem.
    fetches: dict[str, list[tuple[str, str]]] = {}
    fora_do_banco: dict[str, list[str]] = {}
    query_de: dict[str, str] = {}
    for d in pedidos:
        for chave, fn in fetches_v1[d]:
            q = v1.query_do_fetch(fn)
            if queries_v1[q] != banco:
                fora_do_banco.setdefault(d, []).append(f"{chave} ({q}, banco {queries_v1[q]})")
                continue
            query_de[fn] = q
            fetches.setdefault(d, []).append((chave, fn))

    handlers = {d: v1.handler(d) for d in pedidos}
    get_resp, usados_resp = gerar_get_dashboard_response(v1, pedidos_set, todos)

    # Fecho: tudo do dashboard_routes.py que os handlers e o _get_dashboard_response usam.
    pendentes = set(usados_resp)
    for h in handlers.values():
        corpo = ast.Module(body=h.body, type_ignores=[])
        pendentes |= nomes_usados(corpo) | nomes_usados(h.args)
    copiar: set[str] = set()
    importar: set[str] = set()
    vistos: set[str] = set()
    while pendentes:
        nome = pendentes.pop()
        if nome in vistos:
            continue
        vistos.add(nome)
        if nome in GERADOS or nome in query_de or nome == "_get_dashboard_response":
            continue
        if nome in v1.defs:
            copiar.add(nome)
            pendentes |= nomes_usados(v1.defs[nome])
        elif nome in v1.imports:
            importar.add(nome)
    nos_copiados = sorted(
        {id(v1.defs[n]): v1.defs[n] for n in copiar}.values(), key=lambda s: s.lineno
    )
    nos_copiados = [n for n in nos_copiados if n not in handlers.values()]

    # Imports agrupados por módulo, só os nomes usados.
    por_modulo: dict[str, list[str]] = {}
    for nome in sorted(importar):
        mod, original = v1.imports[nome]
        mod = RENOMEAR_IMPORT.get(mod, mod)
        if not original:
            if mod not in ("asyncio", "logging", "time"):  # já vêm no cabeçalho
                por_modulo.setdefault(f"import {mod}", [])
            continue
        por_modulo.setdefault(mod, []).append(
            original if original == nome else f"{original} as {nome}"
        )
    linhas_import = []
    for mod, nomes in sorted(por_modulo.items()):
        if mod.startswith("import "):
            linhas_import.append(mod)
        else:
            linhas_import.append(
                f"from {mod} import (\n" + "".join(f"    {n},\n" for n in nomes) + ")"
            )
    proibidos = [
        m
        for m in por_modulo
        if m.split()[-1] in ("app.cache", "app.database", "app.queries", "app.config", "app.auth")
    ]
    if proibidos:
        raise SystemExit(f"Ainda depende da infraestrutura da v1: {proibidos}")

    # Texto final.
    rotulo = ", ".join(pedidos)
    partes = [
        (
            f'"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.\n\n'
            f"Origem: api_dashboards/src/app/dashboard_routes.py (linha na v1 ao lado de cada bloco).\n"
            f'Gerado por scripts/copiar_v1/gerar_generico.py (banco {banco}). Únicas trocas, marcadas com "V2:":\n'
            f"  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;\n"
            f"  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo;\n"
            f"  * fontes de outro banco saem de FETCHES_BY_DASHBOARD (chegam vazias, como na v1 com a fonte fora do ar).\n"
            f'Dashboards: {rotulo}.\n"""\n'
        ),
        "import asyncio\nimport logging\nimport time\nfrom contextvars import ContextVar",
        *linhas_import,
        "from app.analyses.situacao_processo import aplicar_filtro_situacao_processo",
        "from app.sources import SourceUnavailable  # V2: fonte fora do ar vira 503 na casca\n",
        (
            "# V2: fonte do banco de origem (no lugar de fetch_data_with_cache da v1). A casca passa a fonte do\n"
            "# dashboard (SourceFetcher, já com o cache de 5 min) por `usar_fonte`; o recorte de situação do processo\n"
            "# é o mesmo que a v1 aplica em fetch_data_with_cache.\n"
            f'_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico_{banco}")\n\n'
            "def usar_fonte(fonte):\n"
            '    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""\n'
            "    return _fonte_ctx.set(fonte)\n\n\n"
            "async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:\n"
            "    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))\n"
        ),
    ]
    for fn, q in query_de.items():
        partes.append(
            f"\n# V2: v1 dashboard_routes.py:{v1.defs[fn].lineno} -> fetch_data_with_cache('{q}', ...)\n"
            f"async def {fn}() -> List[Dict[str, Any]]:\n    return await _fetch_v2('{q}')\n"
        )
    for no in nos_copiados:
        partes.append(f"\n# v1: dashboard_routes.py:{no.lineno}\n{v1.seg_def(no)}\n")
    partes.append(
        "\n# V2: só os dashboards desta cópia (v1: FETCHES_BY_DASHBOARD, mesmas fontes e chaves)."
    )
    for d, fora in fora_do_banco.items():
        partes.append(f"# V2: {d} sem as fontes de outro banco: {', '.join(fora)}.")
    partes.append("FETCHES_BY_DASHBOARD: Dict[str, List[Tuple[str, Any]]] = {")
    for d in pedidos:
        itens = ", ".join(f'("{c}", {fn})' for c, fn in fetches.get(d, []))
        partes.append(f'    "{d}": [{itens}],')
    partes.append("}\nDASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)")
    partes.append(
        f"\n\n# v1: dashboard_routes.py:{v1.defs['_get_dashboard_response'].lineno} — V2: início igual, só os ramos de {rotulo}"
    )
    partes.append(get_resp)
    for d, h in handlers.items():
        sem_decorador = v1.src.splitlines()[h.lineno - 1 : h.end_lineno]
        partes.append(
            f"\n# v1: dashboard_routes.py:{h.lineno} (rota sem os decoradores)\n"
            + "\n".join(sem_decorador)
            + "\n"
        )
    partes.append(
        "\n# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache)."
    )
    partes.append("HANDLERS = {" + ", ".join(f'"{d}": {h.name}' for d, h in handlers.items()) + "}")
    qpd = {d: tuple(dict.fromkeys(query_de[fn] for _, fn in fetches.get(d, []))) for d in pedidos}
    partes.append(f"QUERIES_POR_DASHBOARD = {qpd!r}\n")
    texto = "\n".join(partes)
    ast.parse(texto)  # gera só Python válido
    saida.write_text(texto, encoding="utf-8")  # fim de linha nativo, como o .editorconfig
    print(f"{saida}: {len(texto.splitlines())} linhas, {len(nos_copiados)} definições da v1")
    for d, fora in fora_do_banco.items():
        print(f"  {d}: fontes de outro banco omitidas: {', '.join(fora)}")

    faltando = [n for n in builtins_ausentes(texto)]
    if faltando:
        print(f"  ATENÇÃO, nomes sem definição: {sorted(faltando)}")
    copiar_analises(texto)
    registrar_queries(list(dict.fromkeys(query_de.values())), rotulo)


def registrar_queries(nomes: list[str], para_que: str) -> None:
    """Acrescenta em app/source_queries.py, com o texto da v1 sem mudança, as queries que ainda faltam."""
    from datetime import date

    destino = V2_APP / "source_queries.py"
    atual = destino.read_text(encoding="utf-8")
    src_v1 = (V1_APP / "queries.py").read_text(encoding="utf-8")
    entradas = {}
    for node in ast.walk(ast.parse(src_v1)):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value in nomes and isinstance(v, ast.Dict):
                    entradas[k.value] = (
                        k.lineno,
                        ast.get_source_segment(src_v1, v, padded=True).lstrip(),
                    )
    novas = []
    hoje = date.today().strftime("%d/%m/%Y")
    for nome in nomes:
        if f'\n    "{nome}": {{' in atual:
            continue
        linha, texto = entradas[nome]
        novas.append(
            f'    # v1: queries.py:{linha}, "{nome}" (copiada em {hoje}). {para_que}.\n    "{nome}": {texto},\n'
        )
    if not novas:
        return
    fim = atual.rstrip().rfind("}")
    destino.write_text(
        atual[:fim] + "".join(novas) + atual[fim:], encoding="utf-8"
    )  # fim de linha nativo, como o .editorconfig
    print(f"  queries registradas em source_queries.py: {len(novas)}")


def builtins_ausentes(texto: str) -> set[str]:
    """Nomes lidos no topo das funções que não são definidos, importados nem builtins (aproximação)."""
    tree = ast.parse(texto)
    definidos = set(dir(builtins))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definidos.add(n.name)
            for a in ast.walk(n.args) if not isinstance(n, ast.ClassDef) else []:
                if isinstance(a, ast.arg):
                    definidos.add(a.arg)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            definidos.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            definidos |= {a.asname or a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ExceptHandler) and n.name:
            definidos.add(n.name)
        elif isinstance(n, ast.arg):
            definidos.add(n.arg)
    return {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    } - definidos


def copiar_analises(texto: str) -> None:
    """Copia da v1, sem mudança, os módulos app.analyses.* importados que ainda não existem na V2."""
    fila = re.findall(r"^from (app\.analyses\.[\w.]+) import", texto, flags=re.MULTILINE)
    vistos = set()
    while fila:
        mod = fila.pop()
        if mod in vistos:
            continue
        vistos.add(mod)
        rel = Path(*mod.split(".")[1:]).with_suffix(".py")
        destino, origem = V2_APP / rel, V1_APP / rel
        if not destino.exists():
            if not origem.exists():
                print(f"  ATENÇÃO: {mod} não existe na v1 nem na V2")
                continue
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origem, destino)
            print(f"  copiado da v1: {rel}")
        elif origem.exists() and origem.read_bytes() != destino.read_bytes():
            print(f"  já existe na V2 (diferente da v1, mantido): {rel}")
        fila += re.findall(
            r"^\s*from (app\.analyses\.[\w.]+) import",
            destino.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )


def _dict_queries() -> str:
    """{nome: banco} de api_dashboards/src/app/queries.py, sem importar a v1."""
    tree = ast.parse((V1_APP / "queries.py").read_text(encoding="utf-8"))
    bancos = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Dict):
                    for kk, vv in zip(v.keys, v.values):
                        if (
                            isinstance(kk, ast.Constant)
                            and kk.value == "database"
                            and isinstance(vv, ast.Constant)
                        ):
                            bancos[k.value] = vv.value
    return repr(bancos)


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--banco", required=True, choices=("ng", "laadv", "lexflow", "lexpre"))
    p.add_argument("--saida", required=True, type=Path)
    p.add_argument("dashboards", nargs="+", help="nomes da v1 (chaves de FETCHES_BY_DASHBOARD)")
    a = p.parse_args()
    gerar(a.dashboards, a.banco, a.saida)
