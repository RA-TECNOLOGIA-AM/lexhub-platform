"""Controle de Processos (NG) — a página da v1 NG/ControleProcessos.tsx (área Jurídico).

A v1 não tem rota própria: a página fazia 10 chamadas e somava no navegador. Aqui a API faz as mesmas chamadas (as
rotas copiadas sem mudança) e devolve só os campos que a página usa; as somas e a esteira ficam no front, como na v1
(pages/dashboards/controle-processos/controle.ts).

  controle (LexFlow, /controle_processo_NG em app/analyses/v1_dashboard_generico.py):
    periodo   — com o período, a situação e as UFs: médias e medianas por fase, extintos e improcedência;
    historico — sem período: as fases da esteira, trânsito em julgado, opções de UF e de fase, séries mês a mês;
    fase      — sem período, com a fase escolhida: as subfases dela (só quando há fase; a v1 fazia o mesmo).
  protocolo (banco NG legado, /protocolo em v1_dashboard_generico_ng.py): protocolados e tempo até o protocolo;
  lexpre (LexPre, o cálculo do dashboard Protocolo LexPre): os protocolados da coexistência pós-migração;
  execucao / acordos (LexFlow, /execucao e /execucao_acordos_NG): saídas no período e o estoque de agora.

Filtros da página (os da v1): situação (ativo | suspenso; nenhuma = os dois), UFs (várias) e a fase do gráfico de
subfases. A situação não vai ao Protocolo nem à Execução (como na v1: "suspenso" zera esses números no front).
A chamada I da v1 (a de período com a fase) não é feita: a página nunca lia o resultado dela.
"""

from dataclasses import replace
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.analyses import v1_dashboard_generico_ng as v1_ng
from app.dashboards import generico_v1, protocolo_lexpre
from app.dashboards.base import DashboardContext, DashboardInputError, DashboardModule, NotReady
from app.dashboards.pendencias_intermediarias import _sem_nulos

UNIDADE = "NG"
SITUACOES = ("ativo", "suspenso")

FILTROS = {"situacao_controle": str, "uf_controle": str, "fase_controle": str}

CAMPOS_PERIODO = (
    "controle_processo_fase_inicial_media_dias_NG",
    "controle_processo_fase_recursal_media_dias_NG",
    "controle_processo_fase_execucao_media_dias_NG",
    "controle_processo_fase_inicial_mediana_dias_NG",
    "controle_processo_fase_recursal_mediana_dias_NG",
    "controle_processo_fase_execucao_mediana_dias_NG",
    "controle_processo_fase_inicial_comparativo_media_dias_NG",
    "controle_processo_fase_recursal_comparativo_media_dias_NG",
    "controle_processo_fase_execucao_comparativo_media_dias_NG",
    "controle_processo_fase_inicial_comparativo_mediana_dias_NG",
    "controle_processo_fase_recursal_comparativo_mediana_dias_NG",
    "controle_processo_fase_execucao_comparativo_mediana_dias_NG",
    "controle_processo_extintos_com_merito_qtd_NG",
    "controle_processo_extintos_com_merito_valor_causa_NG",
    "controle_processo_extintos_com_merito_2g_qtd_NG",
    "controle_processo_extintos_com_merito_2g_valor_causa_NG",
    "controle_processo_extintos_sem_merito_qtd_NG",
    "controle_processo_extintos_sem_merito_valor_causa_NG",
    "controle_processo_extintos_sem_merito_2g_qtd_NG",
    "controle_processo_extintos_sem_merito_2g_valor_causa_NG",
    "controle_processo_fase_arquivado_improcedente_qtd_NG",
    "controle_processo_fase_arquivado_improcedente_valor_causa_NG",
    "controle_processo_extintos_com_merito_por_tipo_sentenca_NG",
    "controle_processo_extintos_com_merito_2g_por_tipo_sentenca_NG",
    "controle_processo_taxa_provimento_2g_NG",
    "total_controle_processo_NG",
)
CAMPOS_HISTORICO = (
    "total_controle_processo_NG",
    "controle_processo_valor_causa_total_NG",
    "controle_processo_fase_inicial_qtd_NG",
    "controle_processo_fase_inicial_valor_causa_NG",
    "controle_processo_log_inicial_indeferida_qtd_NG",
    "controle_processo_log_inicial_indeferida_valor_causa_NG",
    "controle_processo_fase_recursal_qtd_NG",
    "controle_processo_fase_recursal_valor_causa_NG",
    "controle_processo_log_recursal_nao_provido_qtd_NG",
    "controle_processo_log_recursal_nao_provido_valor_causa_NG",
    "controle_processo_fase_transito_julgado_qtd_NG",
    "controle_processo_fase_transito_julgado_valor_causa_NG",
    "controle_processo_uf_opcoes_NG",
    "controle_processo_por_fase_NG",
    "controle_processo_fase_inicial_media_dias_por_mes_NG",
    "controle_processo_fase_recursal_media_dias_por_mes_NG",
    "controle_processo_fase_execucao_media_dias_por_mes_NG",
)
CAMPOS_FASE = (
    "controle_processo_por_subfase_NG",
    "controle_processo_qtd_subfases_na_fase_NG",
    "controle_processo_total_na_fase_NG",
)
CAMPOS_PROTOCOLO = (
    "protocolos_resolvidos",
    "valor_causa_protocolo_novo",
    "tempo_medio_contratacao_protocolo",
    "mediana_tempo_contratacao_protocolo",
    "comparativo_tempo_medio_contratacao_protocolo",
    "comparativo_mediana_tempo_contratacao_protocolo",
)
CAMPOS_TEMPO_LEXPRE = (
    "media_tempo_protocolado",
    "mediana_tempo_protocolado",
    "comparativo_tempo_medio_protocolado",
    "comparativo_mediana_tempo_protocolado",
)
CAMPOS_EXECUCAO = {
    # (rota da v1, com período?) -> campos de stats
    ("execucao", True): ("total_saida_execucao_periodo", "valor_ted_saida_execucao_periodo"),
    ("execucao_acordos_NG", True): (
        "total_saida_execucao_acordos_periodo_NG",
        "valor_ted_saida_execucao_acordos_periodo_NG",
    ),
    ("execucao", False): ("total_em_execucao", "valor_total_em_execucao"),
    ("execucao_acordos_NG", False): (
        "total_em_execucao_acordos_NG",
        "valor_total_em_execucao_acordos_NG",
    ),
}

QUERIES_LEXFLOW = tuple(
    dict.fromkeys(
        q
        for nome in ("controle_processo_NG", "execucao", "execucao_acordos_NG")
        for q in v1.QUERIES_POR_DASHBOARD[nome]
    )
)


def _campo(resposta: dict[str, Any], nome: str) -> Any:
    if resposta.get(nome) is not None:
        return resposta[nome]
    return (resposta.get("stats") or {}).get(nome)


def _so(resposta: dict[str, Any], campos: tuple[str, ...]) -> dict[str, Any]:
    return {c: _sem_nulos(_campo(resposta, c)) for c in campos}


def filtros_da_pagina(ctx: DashboardContext) -> tuple[str | None, list[str] | None, str | None]:
    """(situação, UFs, fase) nos formatos das rotas da v1."""
    situacao = next(iter(ctx.filters.get("situacao_controle") or []), None)
    situacao = str(situacao).strip().lower() if situacao else None
    if situacao and situacao not in SITUACOES:
        raise DashboardInputError(f"Situação inválida: '{situacao}'. Use ativo ou suspenso.")
    ufs = [str(u).strip().upper() for u in ctx.filters.get("uf_controle") or [] if str(u).strip()]
    fase = next(iter(ctx.filters.get("fase_controle") or []), None)
    fase = str(fase).strip() if fase and str(fase).strip() else None
    return situacao, ufs or None, fase


async def _rota(
    ctx: DashboardContext, copia: Any, nome: str, de: date | None, ate: date | None, **filtros: Any
) -> dict[str, Any]:
    fn = copia.HANDLERS[nome]
    todos = dict.fromkeys(generico_v1._parametros(fn))
    todos.update(filtros)
    resposta = await generico_v1.chamar_v1(ctx, copia, fn, from_date=de, to_date=ate, **todos)
    return resposta.model_dump()


async def _lexpre(ctx: DashboardContext, ufs: list[str] | None) -> dict[str, Any] | None:
    """Os protocolados do LexPre no período (o cálculo do dashboard Protocolo LexPre), com as UFs da página."""
    fonte = ctx.extra_sources.get("lexpre")
    ref = ctx.extra_refs.get("lexpre")
    if fonte is None or ref is None:
        return None  # unidade sem o LexPre ligado: a página soma só o banco legado
    sub = replace(
        ctx,
        source=fonte,
        unit_ref=ref,
        source_db="lexpre",
        filters={"materia": [], "funcionario": [], "area_atuacao_id": [], "uf": ufs or []},
    )
    corpo = await protocolo_lexpre.build(sub)
    stats = corpo.get("stats") or {}
    return {
        "protocolados_total": (stats.get("protocolados_total") or {}).get("total"),
        "valor_causa_protocolado": (stats.get("valor_causa_protocolado") or {}).get("total"),
        # Tempo no setor de Protocolo (entrada → saída da demanda), em dias: o LexPre não tem a data de
        # contratação que o banco legado usa; a página combina os dois (controle.ts).
        **{c: stats.get(c) for c in CAMPOS_TEMPO_LEXPRE},
    }


async def build(ctx: DashboardContext) -> dict:
    if ctx.unit_ref != UNIDADE:
        raise NotReady("Controle de Processos: por enquanto só a NG")
    situacao, ufs, fase = filtros_da_pagina(ctx)
    ini, fim = ctx.period.start, ctx.period.end
    controle = {"situacao": situacao, "uf": ufs}

    corpo: dict[str, Any] = {"unidade": ctx.unit_ref}
    corpo["periodo"] = _so(
        await _rota(ctx, v1, "controle_processo_NG", ini, fim, **controle), CAMPOS_PERIODO
    )
    corpo["historico"] = _so(
        await _rota(ctx, v1, "controle_processo_NG", None, None, **controle), CAMPOS_HISTORICO
    )
    corpo["fase"] = (
        _so(
            await _rota(ctx, v1, "controle_processo_NG", None, None, fase=fase, **controle),
            CAMPOS_FASE,
        )
        if fase
        else None
    )

    # Protocolo do banco NG legado (a v1 não manda a situação; a UF vai como uf_protocolo).
    fonte_ng = ctx.extra_sources.get("ng")
    corpo["protocolo"] = (
        _so(
            await _rota(
                replace(ctx, source=fonte_ng, source_db="ng"),
                v1_ng,
                "protocolo",
                ini,
                fim,
                uf_protocolo=ufs,
            ),
            CAMPOS_PROTOCOLO,
        )
        if fonte_ng is not None
        else None
    )
    corpo["lexpre"] = await _lexpre(ctx, ufs)

    execucao: dict[str, Any] = {}
    for (nome, com_periodo), campos in CAMPOS_EXECUCAO.items():
        de, ate = (ini, fim) if com_periodo else (None, None)
        execucao.update(_so(await _rota(ctx, v1, nome, de, ate, uf=ufs), campos))
    corpo["execucao"] = execucao
    return corpo


MODULE = DashboardModule(
    key="controle-processos",
    source_db="lexflow",
    source_label="LexFlow + Protocolo (NG e LexPre)",
    build=build,
    filters={**FILTROS},
    queries=QUERIES_LEXFLOW,
    extra_queries={
        "ng": tuple(v1_ng.QUERIES_POR_DASHBOARD["protocolo"]),
        "lexpre": (protocolo_lexpre.QUERY,),
    },
)
