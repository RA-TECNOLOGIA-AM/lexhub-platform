"""Recorte por unidade não muda resultado: cada dashboard com `unit_scoped`, dados e exportações, por unidade.

Roda o cálculo duas vezes sobre as mesmas linhas sintéticas: com a query inteira (linhas de NG, LA e RJ, como o
banco devolve hoje) e com o recorte (só as da unidade, como o `where q."ID_ESCRITORIO" = N` devolve). As linhas
das outras unidades são cópias das da unidade com outro escritório, ids e números de processo: passam pelos
mesmos filtros de data, fase e situação, então qualquer conta que as usasse mudaria o resultado.

A prova com os dados de verdade é scripts/comparar_v1/conferir_recorte_unidade.py; este teste pega regressão
(alguém que passe a usar as linhas cruas antes do filtro de escritório).
"""

import asyncio
import json
import re
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards.base import DashboardContext, Period
from app.source_queries import QUERIES
from app.unit_scope import ESCRITORIO_POR_UNIDADE, UNIT_COLUMN, scope_source, split_scoped

MODULOS = sorted(k for k, m in DASHBOARDS.items() if m.unit_scoped)
UNIDADES = tuple(ESCRITORIO_POR_UNIDADE)
POR_UNIDADE = 30  # processos de cada escritório em cada query

# Cadastros do LexFlow (tabelas fase, situacao, status_processual e status_primeiro_grau).
FASES = [
    (8, "RECURSAL"),
    (12, "EXECUÇÃO"),
    (30, "ACORDO"),
    (26, "FINANCEIRO"),
    (25, "INICIAL"),
    (11, "TRÂNSITO EM JULGADO"),
    (1, "CONHECIMENTO"),
]
SITUACOES = [(1, "ATIVO"), (2, "ARQUIVADO"), (6, "SUSPENSO/SOBRESTADO")]
SUBFASES = [
    "PAUTADO PARA JULGAMENTO",
    "ELABORAR RECURSO",
    "AG. ANÁLISE RECURSO",
    "AG. CONTRARRAZÕES",
    "PAGO",
    "AG. SENTENÇA",
    "AG. DESPACHO INICIAL",
]
MERITOS = [
    (17, "ACORDO HOMOLOGADO"),
    (18, "EXTINTO SEM MÉRITO"),
    (19, "IMPROCEDENTE"),
    (20, "PROCEDENTE COM PROVEITO ECONÔMICO"),
    (21, "PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO"),
]
_TIPOS_SQL = {
    "integer",
    "int",
    "text",
    "bigint",
    "numeric",
    "date",
    "timestamp",
    "varchar",
    "jsonb",
}


def colunas(sql: str) -> list[str]:
    """Os nomes das colunas do resultado (aliases com e sem aspas, e o p.id sem alias)."""
    nomes = re.findall(r'\bas\s+"([^"]+)"', sql, re.IGNORECASE)
    nomes += [
        n
        for n in re.findall(r"\bas\s+([a-z_][a-z0-9_]*)\b", sql, re.IGNORECASE)
        if n.lower() not in _TIPOS_SQL
    ]
    if re.search(r"select\s+p\.id\s*,", sql, re.IGNORECASE):
        nomes.append("id")
    return list(dict.fromkeys(nomes))


def valor(col: str, k: int, escritorio: int):
    """Um valor plausível para a coluna `col` do processo `k` do `escritorio`."""
    c = col.upper()
    dia = (
        date(2026, 1, 5) + timedelta(days=9 * k) if k % 6 else date(2025, 6, 1) + timedelta(days=k)
    )
    if col in ("id", "processo_id", "id_processo") or c == "ID_PROCESSO":
        return escritorio * 10_000 + k
    if c in ("ID_ESCRITORIO", "ID_ESCRITORIO_ASSINANTE"):
        return escritorio
    if c == "ESCRITORIO":
        return f"ESCRITÓRIO {escritorio}"
    if c == "ID_SITUACAO":
        return SITUACOES[k % 2][0]  # ativo e arquivado (os que todas as queries trazem)
    if c == "SITUACAO":
        return SITUACOES[k % 2][1]
    if c == "ID_FASE":
        return FASES[k % len(FASES)][0]
    if c == "FASE":
        return FASES[k % len(FASES)][1]
    if c == "SUBFASE":
        return SUBFASES[k % len(SUBFASES)]
    if c == "NUMERO_PROCESSO":
        return f"{escritorio}{k:05d}-00.2026.8.04.0001"
    if c in ("ID_1G", "ID_SENTENCA_MERITO_1G"):
        return MERITOS[k % len(MERITOS)][0]
    if c in ("ID_2G", "ID_ACORDAO_MERITO_2G"):
        return MERITOS[(k + 2) % len(MERITOS)][0]
    if c in ("STATUS_1G", "STATUS_2G", "MERITO_SENTENCA", "MERITO_ACORDAO"):
        return MERITOS[k % len(MERITOS)][1]
    if c.startswith(("DATA", "DT_")) or c in ("ULTIMA_MOVIMENTACAO", "DATA_ULTIMA_MOVIMENTACAO"):
        return None if k % 7 == 3 else dia
    if c.startswith(("VALOR", "DANO", "SUCUMBENCIA")):
        return Decimal(1000 + 37 * k) if k % 5 else None
    if c.startswith("TEM_"):
        return k % 2 == 0
    if c in ("MATERIA",):
        return ["ANP", "MORA", "CDC - CONSUMIDOR", "BANCÁRIO"][k % 4]
    if c == "UF":
        return ["AM", "RJ", "SP"][k % 3]
    if c in ("COMARCA", "COMPETENCIA", "AREA_ATUACAO", "OPERACAO", "PARTE_ADVERSA"):
        return f"{c} {k % 3}"
    if c in ("VARA",):
        return (k % 3) + 1
    if c in ("JUIZ_1G", "RELATOR_2G"):
        return f"{c} {k % 4}"
    if c.endswith("_EXTRAS"):
        return None
    if "ATIVIDADE" in c or "AGENDAMENTO" in c:
        return None  # sem agendamento aberto no setor: o processo fica no estoque (ex.: Recursal)
    if c.startswith("ID_"):
        return (k % 5) + 1
    return None


def linhas(query: str, escritorio: int) -> list[dict]:
    cols = colunas(QUERIES[query]["query"])
    return [{c: valor(c, k, escritorio) for c in cols} for k in range(POR_UNIDADE)]


class Banco:
    """O banco do LexFlow de mentira para uma unidade: a query inteira traz todos os escritórios; o recorte
    ('nome@N'), só o N; as outras queries (já filtradas no SQL) só a unidade."""

    def __init__(self, unidade: str):
        self.escritorio = ESCRITORIO_POR_UNIDADE[unidade]

    async def fetch(self, name):
        base, recorte = split_scoped(name)
        if base not in UNIT_COLUMN:
            return linhas(base, self.escritorio)
        todos = ESCRITORIO_POR_UNIDADE.values() if recorte is None else (recorte,)
        return [r for e in todos for r in linhas(base, e)]

    def synced_at(self):
        return None


def _ctx(modulo, unidade, periodo, fonte, opcoes=None):
    return DashboardContext(
        source=fonte,
        source_db="lexflow",
        unit_ref=unidade,
        period=Period(*periodo),
        filters={f: [] for f in modulo.filters},
        can_see_commission=True,
        export_options=opcoes or {},
    )


def _trabalhos(modulo):
    """(nome, fazer(ctx), opções) de cada cálculo: os dados e cada exportação com cada escolha de opção."""
    yield "dados", modulo.build, {}
    specs = ([("export", modulo.export)] if modulo.export else []) + list(
        modulo.export_reports.items()
    )
    for nome, spec in specs:
        padrao = {o.key: next(iter(o.choices)) for o in spec.options}
        escolhas = [padrao] + [
            {**padrao, o.key: c} for o in spec.options for c in list(o.choices)[1:]
        ]
        for opcoes in escolhas:
            yield f"{nome} {opcoes}", spec.rows, opcoes


async def _json(trabalho):
    return json.loads(json.dumps(await trabalho, default=str, sort_keys=True))


class BancoTriplicado(Banco):
    """Sensibilidade: as cópias das outras unidades entram como se fossem da própria unidade."""

    async def fetch(self, name):
        base, _ = split_scoped(name)
        rows = linhas(base, self.escritorio)
        if base in UNIT_COLUMN:
            for e in ESCRITORIO_POR_UNIDADE.values():
                if e != self.escritorio:
                    rows += [{**r, UNIT_COLUMN[base]: self.escritorio} for r in linhas(base, e)]
        return rows


PERIODOS = {
    "ano": (date(2026, 1, 1), date(2026, 11, 20)),
    "mes": (date(2026, 3, 1), date(2026, 3, 31)),
}


@pytest.mark.parametrize("key", MODULOS)
def test_recorte_por_unidade_nao_muda_dados_nem_exportacoes(key):
    modulo = DASHBOARDS[key]

    async def rodar():
        sensiveis = 0
        for unidade in UNIDADES:
            for nome_p, periodo in PERIODOS.items():
                inteira = Banco(unidade)
                recorte = scope_source(Banco(unidade), "lexflow", unidade, modulo.unit_scoped)
                assert recorte is not inteira
                for nome, fazer, opcoes in _trabalhos(modulo):
                    caso = f"{key} {unidade} {nome_p} {nome}"
                    antes = await _json(fazer(_ctx(modulo, unidade, periodo, inteira, opcoes)))
                    depois = await _json(fazer(_ctx(modulo, unidade, periodo, recorte, opcoes)))
                    assert antes == depois, caso
                    if nome == "dados":
                        triplo = BancoTriplicado(unidade)
                        mais = await _json(fazer(_ctx(modulo, unidade, periodo, triplo, opcoes)))
                        sensiveis += mais != antes
        return sensiveis

    # Os dados sintéticos precisam chegar às contas: com o triplo de linhas da unidade, o resultado muda.
    # Se não mudasse, as linhas das outras unidades também não mudariam nada e o teste não provaria nada.
    assert asyncio.run(rodar()) == len(UNIDADES) * len(PERIODOS)


def test_linhas_sinteticas_tem_as_colunas_das_queries():
    for q in UNIT_COLUMN:
        cols = colunas(QUERIES[q]["query"])
        assert UNIT_COLUMN[q] in cols, q
        assert "id" in cols or "ID_PROCESSO" in cols, q
