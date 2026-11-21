"""Recursal (LexFlow) — as páginas da v1 NG/Recursal.tsx, LA/Recursal_LA.tsx e RJ/Recursal_RJ.tsx.

A v1 montava a página no navegador com 18 chamadas a /recursal_<u> e às sub-rotas dele (por_subfase, por_materia,
por_competencia, por_vara, status_1g, status_2g, decisoes, ranking/juizes, ranking/relatores, filtros/opcoes) e a
/controle_processo_<u> (Extintos 2º grau; o RJ lê esses números do próprio /recursal_RJ). Aqui a API faz as mesmas
chamadas (as rotas copiadas sem mudança em app/analyses/v1_dashboard_generico.py) e devolve só os campos que a
página usa, sempre com os nomes da NG (os do LA e do RJ seguem generico_v1.nome_na_unidade), para o front ser um só.

Como na v1, cada gráfico clicável vem SEM o filtro da própria dimensão (para continuar mostrando todas as fatias);
os da seção Atividades vão sempre. Única mudança de cálculo: o filtro de decisão, que na v1 dava erro (ver a nota
"V2:" em analyses/<u>/recurso_<u>.py).
"""

from dataclasses import replace
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import generico_v1, recursal_export
from app.dashboards.base import DashboardContext, DashboardInputError, DashboardModule, NotReady
from app.unit_scope import com_recorte

UNIDADES = ("NG", "LA", "RJ")

# Filtros dos processos (a v1 manda id_1g/id_2g como inteiros) e os da seção Atividades.
FILTROS_PROCESSO = (
    "id_1g",
    "id_2g",
    "juiz",
    "relator",
    "decisao",
    "materia",
    "competencia",
    "vara",
    "subfase",
    "extinto_2g",
)
FILTROS_ATIVIDADES = (
    "funcionario_recursos",
    "atividade_recursos",
    "status_recursos",
    "situacao_recursos",
)
INTEIROS = ("id_1g", "id_2g")

DECISOES = (
    "mantido_ganho",
    "ganho_ampliado",
    "revertido_ganho",
    "ganho_reduzido",
    "mantido_perda",
    "revertido_perda",
    "extincao_reajuizar",
    "instrucao_retomada",
)

# As listas de /filtros/opcoes que a página usa (painel de filtros).
OPCOES = (
    "status_1g",
    "status_2g",
    "decisoes",
    "juizes",
    "relatores",
    "materias",
    "competencias",
    "varas",
    "subfases",
    "extintos_2g",
)

# Os campos que a página da v1 lê de cada chamada, com os nomes da NG.
CAMPOS: dict[str, dict[str, tuple[str, ...]]] = {
    "periodo": {
        "stats": (
            "entrada_recursal_NG",
            "valor_causa_acordo_recursal_NG",
            "avr_retorno_recurso_cancelado_NG",
            "retorno_cr_recurso_cancelado_NG",
            "total_por_prazo_atividades_recursos_NG",
            "por_prazo_em_andamento_atividades_recursos_NG",
            "por_prazo_vencidas_atividades_recursos_NG",
            "por_prazo_vencem_hoje_atividades_recursos_NG",
            "por_prazo_concluidas_atividades_recursos_NG",
            "total_atividades_recursos_NG",
            "atividades_recursos_em_andamento_NG",
            "atividades_recursos_vencidas_NG",
            "atividades_recursos_vencem_hoje_NG",
            "atividades_recursos_concluidas_NG",
            "provimento_mensal_qtd_NG",
            "provimento_mensal_meta_NG",
            # Extintos 2º grau (só o RJ manda aqui; NG e LA vêm do controle de processo)
            "controle_processo_extintos_com_merito_2g_qtd_recursal_NG",
            "controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG",
            "controle_processo_taxa_provimento_2g_recursal_NG",
            "controle_processo_extintos_sem_merito_2g_qtd_recursal_NG",
            "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG",
        ),
        "listas": (
            "recursal_processos_por_atividade_NG",
            "recursal_demandas_por_funcionario_NG",
            "recursal_media_resolvidos_por_funcionario_NG",
            "recursal_atividades_lista_NG",
            "recursal_atividades_lista_filtros_opcoes_NG",
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG",
        ),
    },
    "historico": {"stats": ("total_recursal_NG",), "listas": ()},
    "producao": {
        "stats": (),
        "listas": (
            "recursal_resolvidos_por_mes_NG",
            "recursal_resolvidos_por_dia_NG",
            "recursal_resolvidos_por_dia_por_funcionario_NG",
        ),
    },
    "subfase": {
        "stats": ("total_recursal_NG", "entrada_recursal_NG"),
        "listas": ("recursal_por_subfase_NG",),
    },
    "materia": {
        "stats": ("total_recursal_NG", "entrada_recursal_NG"),
        "listas": ("recursal_por_materia_NG",),
    },
    "competencia": {"stats": (), "listas": ("recursal_por_competencia_NG",)},
    "vara": {"stats": (), "listas": ("recursal_por_vara_NG",)},
    "decisoes": {
        "stats": (
            "total_decisoes_recursal_NG",
            *(f"total_{k}_recurso_NG" for k in DECISOES),
            *(f"percent_{k}_recursal_NG" for k in DECISOES),
        ),
        "listas": (),
    },
    "status_1g": {"stats": (), "listas": ("recursal_por_status_1g_NG",)},
    "status_2g": {"stats": (), "listas": ("recursal_por_status_2g_NG",)},
    "juizes": {"stats": (), "listas": ("ranking_juizes_recursal_NG",)},
    "relatores": {"stats": (), "listas": ("ranking_relatores_recursal_NG",)},
    "controle": {
        "stats": (
            "controle_processo_extintos_com_merito_2g_qtd_recursal_NG",
            "controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG",
            "controle_processo_taxa_provimento_2g_recursal_NG",
            "controle_processo_extintos_sem_merito_2g_qtd_recursal_NG",
            "controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG",
        ),
        "listas": (
            "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG",
        ),
    },
}


def _so(resposta: dict[str, Any], chave: str, unidade: str) -> dict[str, Any]:
    """Só os campos usados, lidos pelo nome da unidade e devolvidos com o nome da NG."""
    campos = CAMPOS[chave]
    stats = resposta.get("stats") or {}

    def nome(c: str) -> str:
        return generico_v1.nome_na_unidade(c, unidade)

    def valor(c: str) -> Any:
        # Na v1 a lista "por tipo" dos Extintos pode vir na raiz ou em stats.
        n = nome(c)
        return resposta[n] if resposta.get(n) is not None else stats.get(n)

    corpo = {
        "stats": {c: stats.get(nome(c)) for c in campos["stats"]},
        **{c: valor(c) for c in campos["listas"]},
    }
    # Sem os campos vazios das linhas (o modelo de ponto da v1 manda uma dúzia de campos sempre null; a lista de
    # tarefas é o maior pedaço da resposta).
    for c, lista in corpo.items():
        if isinstance(lista, list):
            corpo[c] = [
                {k: x for k, x in item.items() if x is not None} if isinstance(item, dict) else item
                for item in lista
            ]
    return corpo


def filtro_v2(nome: str) -> str:
    """O nome do filtro na V2: os dos processos com o sufixo _recursal (juiz -> juiz_recursal), para não
    misturar com os de outros dashboards; os da seção Atividades já são únicos (funcionario_recursos...)."""
    return f"{nome}_recursal" if nome in FILTROS_PROCESSO else nome


def filtros_da_pagina(ctx: DashboardContext) -> dict[str, list[Any] | None]:
    """Os filtros do pedido no formato das rotas da v1 (lista ou None; id_1g e id_2g inteiros)."""
    saida: dict[str, list[Any] | None] = {}
    for nome in (*FILTROS_PROCESSO, *FILTROS_ATIVIDADES):
        valores = [str(v).strip() for v in ctx.filters.get(filtro_v2(nome)) or [] if str(v).strip()]
        if nome in INTEIROS:
            try:
                saida[nome] = [int(v) for v in valores] or None
            except ValueError:
                raise DashboardInputError(f"{nome}: use os ids numéricos do status") from None
        else:
            saida[nome] = valores or None
    return saida


async def build(ctx: DashboardContext) -> dict:
    u = ctx.unit_ref
    if u not in UNIDADES:
        raise NotReady("Recursal existe na NG, no LA e no RJ (como na v1)")
    filtros = filtros_da_pagina(ctx)
    ini, fim = ctx.period.start, ctx.period.end

    def rota(sufixo: str):
        return getattr(v1, f"get_recursal_{u}_{sufixo}")

    def sem(dim: str | None) -> dict[str, Any]:
        # O gráfico de uma dimensão vem sem o filtro dela (como os "chart opts" da v1).
        return {k: (None if k == dim else val) for k, val in filtros.items()}

    async def chamar(fn, de: date | None, ate: date | None, **kw: Any) -> dict[str, Any]:
        todos = dict.fromkeys(generico_v1._parametros(fn))
        todos.update(kw)
        resposta = await generico_v1.chamar_v1(ctx, v1, fn, from_date=de, to_date=ate, **todos)
        return resposta.model_dump()

    principal = v1.HANDLERS[f"recursal_{u}"]
    corpo: dict[str, Any] = {
        "periodo": _so(await chamar(principal, ini, fim, **filtros), "periodo", u),
        "historico": _so(await chamar(principal, None, None, **filtros), "historico", u),
        # A produção mês a mês da v1 vinha do histórico todo, sem nenhum filtro.
        "producao": _so(await chamar(principal, None, None), "producao", u),
    }
    for chave, dim in (
        ("subfase", "subfase"),
        ("materia", "materia"),
        ("competencia", "competencia"),
        ("vara", "vara"),
    ):
        fn = rota(f"por_{chave}")
        corpo[chave] = {
            "estoque": _so(await chamar(fn, None, None, base="estoque", **sem(dim)), chave, u),
            "entrada": _so(await chamar(fn, ini, fim, base="entrada", **sem(dim)), chave, u),
        }
    for chave, sufixo, dim in (
        ("decisoes", "decisoes", "decisao"),
        ("status_1g", "status_1g", "id_1g"),
        ("status_2g", "status_2g", "id_2g"),
        ("juizes", "ranking_juizes", "juiz"),
        ("relatores", "ranking_relatores", "relator"),
    ):
        corpo[chave] = _so(await chamar(rota(sufixo), ini, fim, **sem(dim)), chave, u)

    # Extintos 2º grau: NG e LA vêm do controle de processo (sem os filtros da página, como na v1); o RJ, do
    # próprio /recursal_RJ (com os filtros).
    if u == "RJ":
        corpo["controle"] = {
            "stats": {c: corpo["periodo"]["stats"].get(c) for c in CAMPOS["controle"]["stats"]},
            **{c: corpo["periodo"].get(c) for c in CAMPOS["controle"]["listas"]},
        }
    else:
        controle = v1.HANDLERS[f"controle_processo_{u}"]
        corpo["controle"] = _so(await chamar(controle, ini, fim), "controle", u)

    opcoes = await generico_v1.chamar_v1(ctx, v1, rota("filtros_opcoes"))
    opcoes = opcoes.model_dump() if hasattr(opcoes, "model_dump") else dict(opcoes or {})
    corpo["opcoes"] = {k: opcoes.get(k) for k in OPCOES}
    corpo["unidade"] = u
    # Relatório de comissão do setor Recursos (só NG, como a v1): só para quem vê a comissão de todos.
    corpo["comissao"] = await recursal_export.comissao(ctx) if ctx.can_see_commission else None
    return corpo


MODULE = DashboardModule(
    key="recursal",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={
        **{
            filtro_v2(n): (int if n in INTEIROS else str)
            for n in (*FILTROS_PROCESSO, *FILTROS_ATIVIDADES)
        },
        "situacao_processo": str,
    },
    export=recursal_export.PROCESSOS,
    queries=tuple(
        dict.fromkeys(
            q
            for nome in (
                *(f"recursal_{u}" for u in UNIDADES),
                "controle_processo_NG",
                "controle_processo_LA",
            )
            for q in v1.QUERIES_POR_DASHBOARD[nome]
        )
    ),
)

# Só as linhas da unidade da tela nas queries que trazem todos os escritórios (app/unit_scope.py).
MODULE = replace(MODULE, unit_scoped=com_recorte(MODULE.queries))
