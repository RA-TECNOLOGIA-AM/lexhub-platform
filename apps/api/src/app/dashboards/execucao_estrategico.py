"""Execução Estratégico Geral (NG, LA e RJ) — as páginas da v1 NG/ExecucaoEstrategicoGeral.tsx,
LA/ExecucaoEstrategicoGeralLA.tsx e RJ/ExecucaoEstrategicoGeralRJ.tsx (a mesma página, com as rotas de cada escritório).

A v1 não tem rota própria: a página chamava 8 vezes as rotas /execucao e /execucao_acordos_NG (LA: /execucao_LA e
/execucao_acordos_LA; RJ: _RJ) e somava no navegador. Os campos voltam sempre com os nomes da NG (os do LA e do RJ
seguem a regra de generico_v1.nome_na_unidade), para o front ser um só.
Aqui a API faz as mesmas 8 chamadas (os handlers da cópia sem mudança em app/analyses/v1_dashboard_generico.py) e
devolve só os campos que a página usa; a soma, o escopo (Ambos / Condenação / Acordos), os comparativos e os merges
ficam no front, como na v1 (pages/dashboards/execucao-estrategico/estrategico.ts).

  condenacao / acordos: `atual` (período), `historico` (sem período) e `anterior` (o mesmo recorte de dias um mês
    antes, como getPeriodoComparativoAnterior da v1) — com matéria, subfase, ano de ajuizamento, UF e comarca;
  confeccao: a Execução no período com as atividades da Confecção CS escolhidas (padrão: as 4), o funcionário e a
    situação — SEM UF e comarca, como na v1; confeccao_por_atividade: o mesmo com as 4 atividades sempre.
"""

import calendar
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, DashboardModule, NotReady

# v1: ATIVIDADES_CONFECCAO_CS (ExecucaoEstrategicoGeral.tsx).
ATIVIDADES_CONFECCAO_CS = (
    "Elaborar Cumprimento de Sentença (1G)",
    "Elaborar Cumprimento de Sentença (2G)",
    "Manifestação Cálculo 1",
    "Manifestação Cálculo 2",
)
# LA e RJ: mais a atividade antiga, sem grau, que ainda recebe tarefas (ExecucaoEstrategicoGeralLA/RJ.tsx).
ATIVIDADES_CONFECCAO_CS_POR_UNIDADE = {
    "NG": ATIVIDADES_CONFECCAO_CS,
    "LA": ("Elaborar Cumprimento de Sentença", *ATIVIDADES_CONFECCAO_CS),
    "RJ": ("Elaborar Cumprimento de Sentença", *ATIVIDADES_CONFECCAO_CS),
}
# As rotas da v1 de cada escritório: (Condenação, Acordos).
ROTAS = {
    "NG": ("execucao", "execucao_acordos_NG"),
    "LA": ("execucao_LA", "execucao_acordos_LA"),
    "RJ": ("execucao_RJ", "execucao_acordos_RJ"),
}

# Os campos que a página da v1 lê de cada chamada (o resto da resposta da rota não vai para o navegador).
CAMPOS = {
    "condenacao_atual": {
        "stats": (
            "total_em_execucao",
            "total_saida_execucao_periodo",
            "total_incontroverso_saida_execucao_periodo",
            "duracoes_tempo_execucao_NG",
            "estoque_inicial",
            "valor_em_execucao",
            "valor_incontroverso_saida_execucao_periodo",
            "valor_execucao_saida_periodo",
            "valor_ted_saida_execucao_periodo",
            "taxa_atualizacao_execucao_NG",
            "execucao_uf_opcoes_NG",
            "execucao_comarca_opcoes_NG",
            "execucao_materia_opcoes_NG",
            "execucao_subfase_opcoes_NG",
        ),
        "listas": (
            "execucao_por_materia",
            "valor_execucao_por_materia",
            "valor_execucao_por_subfase",
            "execucao_por_ano_ajuizamento_NG",
            "execucao_por_comarca_entrada",
            "execucao_por_comarca_saida",
        ),
    },
    "condenacao_historico": {
        "stats": ("total_em_execucao", "valor_total_em_execucao", "valor_remanescente_em_execucao"),
        "listas": (
            "quantidade_entrada_execucao_por_mes",
            "quantidade_saida_execucao_por_mes",
            "execucao_por_materia",
            "execucao_entrada_fluxo_cs_por_mes_NG",
            "valor_entrada_execucao_por_mes",
            "valor_execucao_por_subfase",
            "execucao_por_ano_ajuizamento_NG",
            "valor_saida_execucao_por_mes",
            "execucao_media_tempo_por_mes",
            "execucao_por_comarca_total",
            "execucao_alvaras_expedidos_por_dia_NG",
            "execucao_alvara_expedido_lista_NG",
        ),
    },
    "condenacao_anterior": {
        "stats": (
            "total_em_execucao",
            "total_saida_execucao_periodo",
            "duracoes_tempo_execucao_NG",
            "valor_em_execucao",
            "valor_execucao_saida_periodo",
            "taxa_atualizacao_execucao_NG",
        ),
        "listas": (),
    },
    "acordos_atual": {
        "stats": (
            "total_entrada_execucao_acordos_periodo_NG",
            "total_saida_execucao_acordos_periodo_NG",
            "duracoes_tempo_execucao_acordos_NG",
            "estoque_inicial_execucao_acordos_NG",
            "valor_entrada_execucao_acordos_periodo_NG",
            "valor_saida_execucao_acordos_periodo_NG",
            "valor_ted_saida_execucao_acordos_periodo_NG",
            "execucao_acordos_uf_opcoes_NG",
            "execucao_acordos_comarca_opcoes_NG",
            "execucao_acordos_materia_opcoes_NG",
            "execucao_acordos_subfase_opcoes_NG",
        ),
        "listas": (
            "execucao_acordos_por_materia_NG",
            "valor_execucao_acordos_por_materia_NG",
            "valor_execucao_acordos_por_subfase_NG",
            "execucao_acordos_por_ano_ajuizamento_NG",
            "execucao_acordos_por_comarca_entrada_NG",
            "execucao_acordos_por_comarca_saida_NG",
        ),
    },
    "acordos_historico": {
        "stats": ("total_em_execucao_acordos_NG", "valor_total_em_execucao_acordos_NG"),
        "listas": (
            "quantidade_entrada_execucao_acordos_por_mes_NG",
            "quantidade_saida_execucao_acordos_por_mes_NG",
            "execucao_acordos_por_materia_NG",
            "valor_entrada_execucao_acordos_por_mes_NG",
            "valor_execucao_acordos_por_subfase_NG",
            "execucao_acordos_por_ano_ajuizamento_NG",
            "valor_saida_execucao_acordos_por_mes_NG",
            "execucao_acordos_media_tempo_por_mes_NG",
            "execucao_acordos_por_comarca_total_NG",
            "execucao_acordos_alvaras_expedidos_por_dia_NG",
            "execucao_acordos_alvara_expedido_lista_NG",
        ),
    },
    "acordos_anterior": {
        "stats": (
            "total_entrada_execucao_acordos_periodo_NG",
            "total_saida_execucao_acordos_periodo_NG",
            "duracoes_tempo_execucao_acordos_NG",
            "valor_entrada_execucao_acordos_periodo_NG",
            "valor_saida_execucao_acordos_periodo_NG",
        ),
        "listas": (),
    },
    "confeccao": {
        "stats": (
            "total_atividades_criadas_execucao_NG",
            "atividades_execucao_abertas_NG",
            "atividades_execucao_concluidas_NG",
        ),
        "listas": (
            "execucao_atividades_lista_filtros_opcoes_NG",
            "execucao_nao_cumprido_por_motivo_NG",
            "execucao_taxa_conclusao_por_funcionario_NG",
            "execucao_atividades_lista_NG",
            "execucao_atividades_abertas_NG",
        ),
    },
    "confeccao_por_atividade": {
        "stats": (),
        "listas": ("execucao_atividades_criadas_por_atividade_NG",),
    },
}


def mes_anterior(d: date) -> date:
    """O mesmo dia um mês civil antes; dia que não existe no mês vira o último (31/03 -> 28 ou 29/02).

    = shiftDateByMonths(date, -1) da v1 (getPeriodoComparativoAnterior).
    """
    ano, mes = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def _so(resposta: dict[str, Any], chave: str, unidade: str = "NG") -> dict[str, Any]:
    """Só os campos que a página usa, lidos pelo nome da unidade e devolvidos com o nome da NG."""
    campos = CAMPOS[chave]
    stats = resposta.get("stats") or {}

    def nome(c: str) -> str:
        return generico_v1.nome_na_unidade(c, unidade)

    return {
        "stats": {c: stats.get(nome(c)) for c in campos["stats"]},
        **{c: resposta.get(nome(c)) for c in campos["listas"]},
    }


def _lista(ctx: DashboardContext, chave: str) -> list[Any] | None:
    return list(ctx.filters.get(chave) or []) or None


async def build(ctx: DashboardContext) -> dict:
    u = ctx.unit_ref
    if u not in ROTAS:
        raise NotReady("O Execução Estratégico Geral existe na NG, no LA e no RJ (como na v1)")
    exec_ng = v1.HANDLERS[ROTAS[u][0]]
    acordos_ng = v1.HANDLERS[ROTAS[u][1]]
    padrao = list(ATIVIDADES_CONFECCAO_CS_POR_UNIDADE[u])
    nomes_exec = generico_v1._parametros(exec_ng)
    nomes_acordos = generico_v1._parametros(acordos_ng)
    ano = next(iter(ctx.filters.get("ano_ajuizamento") or []), None)
    comuns = {"materia": _lista(ctx, "materia"), "subfase": _lista(ctx, "subfase")}
    local = {"uf": _lista(ctx, "uf"), "comarca": _lista(ctx, "comarca")}

    async def chamar(handler, nomes, de, ate, **kw) -> dict[str, Any]:
        todos = dict.fromkeys(nomes)  # os handlers da v1 têm Query() como padrão: tudo explícito
        todos.update(kw)
        resposta = await generico_v1.chamar_v1(ctx, v1, handler, from_date=de, to_date=ate, **todos)
        return resposta.model_dump()

    ini, fim = ctx.period.start, ctx.period.end
    ant_ini, ant_fim = mes_anterior(ini), mes_anterior(fim)
    cond = {**comuns, **local, "ano_ajuizamento_execucao": ano}
    acor = {**comuns, **local, "ano_ajuizamento_execucao_acordos": ano}
    atividades = _lista(ctx, "atividade_execucao") or padrao
    cs = {
        **comuns,
        "ano_ajuizamento_execucao": ano,
        "funcionario_execucao": _lista(ctx, "funcionario_execucao"),
        "situacao_execucao": _lista(ctx, "situacao_execucao"),
    }
    return {
        "condenacao": {
            "atual": _so(
                await chamar(exec_ng, nomes_exec, ini, fim, **cond), "condenacao_atual", u
            ),
            "historico": _so(
                await chamar(exec_ng, nomes_exec, None, None, **cond), "condenacao_historico", u
            ),
            "anterior": _so(
                await chamar(exec_ng, nomes_exec, ant_ini, ant_fim, **cond),
                "condenacao_anterior",
                u,
            ),
        },
        "acordos": {
            "atual": _so(
                await chamar(acordos_ng, nomes_acordos, ini, fim, **acor), "acordos_atual", u
            ),
            "historico": _so(
                await chamar(acordos_ng, nomes_acordos, None, None, **acor), "acordos_historico", u
            ),
            "anterior": _so(
                await chamar(acordos_ng, nomes_acordos, ant_ini, ant_fim, **acor),
                "acordos_anterior",
                u,
            ),
        },
        "confeccao": _so(
            await chamar(exec_ng, nomes_exec, ini, fim, **cs, atividade_execucao=atividades),
            "confeccao",
            u,
        ),
        "confeccao_por_atividade": _so(
            await chamar(
                exec_ng,
                nomes_exec,
                ini,
                fim,
                **cs,
                atividade_execucao=padrao,
            ),
            "confeccao_por_atividade",
            u,
        ),
        "periodo_anterior": {"from": ant_ini.isoformat(), "to": ant_fim.isoformat()},
        "atividades_confeccao": padrao,
    }


MODULE = DashboardModule(
    key="execucao-estrategico",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={
        "materia": str,
        "subfase": str,
        "uf": str,
        "comarca": str,
        "ano_ajuizamento": str,  # vai nos dois nomes da v1 (ano_ajuizamento_execucao e _acordos)
        "atividade_execucao": str,  # Confecção CS
        "funcionario_execucao": str,
        "situacao_execucao": str,
        "situacao_processo": str,
    },
    queries=tuple(
        dict.fromkeys(
            q for rotas in ROTAS.values() for r in rotas for q in v1.QUERIES_POR_DASHBOARD[r]
        )
    ),
)
