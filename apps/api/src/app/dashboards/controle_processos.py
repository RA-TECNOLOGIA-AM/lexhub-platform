"""Controle de Processos (NG, LA e RJ) — a página da v1 NG/ControleProcessos.tsx (área Jurídico).

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

Por unidade (ROTAS), sempre com os nomes da NG na resposta:
  NG — /controle_processo_NG, Protocolo do banco NG (/protocolo), /execucao e /execucao_acordos_NG;
  LA — /controle_processo_LA (a rota da v1 do LA; sem filtro de UF, como a página dela), Protocolo do banco LAADV
       (/protocolo_LA), /execucao_LA e /execucao_acordos_LA;
  RJ — a v1 não tem a página: o cálculo do NG sem mudança, com a base no escritório 27 (_escritorio_ctx, nota "V2:"
       em analyses/NG/controle_processo_NG.py) e o histórico de subfases do RJ (log_subfase_processual_RJ);
       Protocolo do banco NG (/protocolo_RJ), /execucao_RJ e /execucao_acordos_RJ.
  O LexPre entra nas três (escritório da unidade no LexPre: app.unit_source_refs).
"""

from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.analyses import v1_dashboard_generico_la as v1_la
from app.analyses import v1_dashboard_generico_ng as v1_ng
from app.analyses.NG import controle_processo_NG as controle_ng
from app.dashboards import generico_v1, protocolo_lexpre
from app.dashboards.base import DashboardContext, DashboardInputError, DashboardModule, NotReady
from app.dashboards.pendencias_intermediarias import _FonteRJ, _sem_nulos
from app.unit_scope import com_recorte


@dataclass(frozen=True)
class Rota:
    controle: str  # a rota da v1 do controle de processos
    nomes: str  # o sufixo dos campos que ela devolve ("NG" | "LA")
    protocolo: tuple[Any, str, str]  # (cópia da v1, rota, banco) do Protocolo legado
    execucao: tuple[str, str]  # (Condenação, Acordos)
    uf: bool  # a rota do controle aceita UF (a do LA não)
    escritorio: int | None = None  # RJ: o escritório da base no cálculo do NG
    queries_rj: dict[str, str] | None = None  # RJ: query do NG -> a do RJ


ROTAS = {
    "NG": Rota(
        "controle_processo_NG",
        "NG",
        (v1_ng, "protocolo", "ng"),
        ("execucao", "execucao_acordos_NG"),
        True,
    ),
    "LA": Rota(
        "controle_processo_LA",
        "LA",
        (v1_la, "protocolo_LA", "laadv"),
        ("execucao_LA", "execucao_acordos_LA"),
        False,
    ),
    "RJ": Rota(
        "controle_processo_NG",
        "NG",
        (v1_ng, "protocolo_RJ", "ng"),
        ("execucao_RJ", "execucao_acordos_RJ"),
        True,
        escritorio=27,
        queries_rj={"log_subfase_processual": "log_subfase_processual_RJ"},
    ),
}
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


# O nome de cada campo do Protocolo legado na rota de cada unidade: o NG e o RJ (/protocolo_RJ) usam os mesmos;
# a rota do LA (/protocolo_LA, banco LAADV) tem outros.
def _campos_protocolo(unidade: str) -> dict[str, str]:
    if unidade == "LA":
        return {
            "protocolos_resolvidos": "protocolos_resolvidos_LA",
            "valor_causa_protocolo_novo": "valor_causa_protocolado_LA",
            **{c: f"{c}_LA" for c in CAMPOS_PROTOCOLO[2:]},
        }
    return {c: c for c in CAMPOS_PROTOCOLO}


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
        [
            *(
                q
                for r in ROTAS.values()
                for nome in (r.controle, *r.execucao)
                for q in v1.QUERIES_POR_DASHBOARD[nome]
            ),
            *(q for r in ROTAS.values() for q in (r.queries_rj or {}).values()),
        ]
    )
)


def _campo(resposta: dict[str, Any], nome: str) -> Any:
    if resposta.get(nome) is not None:
        return resposta[nome]
    return (resposta.get("stats") or {}).get(nome)


def _so(resposta: dict[str, Any], campos: tuple[str, ...], nomes: str = "NG") -> dict[str, Any]:
    """Os campos (nomes da NG), lidos pelo nome da rota de onde vieram (`nomes`: o sufixo dela)."""
    return {
        c: _sem_nulos(
            _campo(resposta, generico_v1.nome_na_unidade(c, nomes) if nomes != "NG" else c)
        )
        for c in campos
    }


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


async def _controle(
    ctx: DashboardContext, r: Rota, de: date | None, ate: date | None, **filtros: Any
) -> Any:
    """A rota do controle da unidade (no RJ, a do NG com o escritório 27 e o histórico de subfases do RJ)."""
    if r.escritorio is None:
        return await _rota(ctx, v1, r.controle, de, ate, **filtros)
    token = controle_ng._escritorio_ctx.set(r.escritorio)
    try:
        sub = replace(ctx, source=_FonteRJ(ctx.source, r.queries_rj or {}))
        return await _rota(sub, v1, r.controle, de, ate, **filtros)
    finally:
        controle_ng._escritorio_ctx.reset(token)


async def build(ctx: DashboardContext) -> dict:
    r = ROTAS.get(ctx.unit_ref)
    if r is None:
        raise NotReady("Controle de Processos existe na NG, no LA e no RJ")
    u = ctx.unit_ref
    situacao, ufs, fase = filtros_da_pagina(ctx)
    if not r.uf:
        ufs = None  # a rota do LA não filtra por UF (como a página dela na v1)
    ini, fim = ctx.period.start, ctx.period.end
    controle: dict[str, Any] = {"situacao": situacao, **({"uf": ufs} if r.uf else {})}

    corpo: dict[str, Any] = {"unidade": u, "tem_uf": r.uf}
    corpo["periodo"] = _so(await _controle(ctx, r, ini, fim, **controle), CAMPOS_PERIODO, r.nomes)
    corpo["historico"] = _so(
        await _controle(ctx, r, None, None, **controle), CAMPOS_HISTORICO, r.nomes
    )
    corpo["fase"] = (
        _so(await _controle(ctx, r, None, None, fase=fase, **controle), CAMPOS_FASE, r.nomes)
        if fase
        else None
    )

    # Protocolo do banco legado da unidade (a v1 não manda a situação; a UF vai como uf_protocolo, onde existe).
    copia, rota_protocolo, banco = r.protocolo
    fonte_legado = ctx.extra_sources.get(banco)
    if fonte_legado is not None:
        params = generico_v1._parametros(copia.HANDLERS[rota_protocolo])
        resposta = await _rota(
            replace(ctx, source=fonte_legado, source_db=banco),
            copia,
            rota_protocolo,
            ini,
            fim,
            **({"uf_protocolo": ufs} if "uf_protocolo" in params else {}),
        )
        corpo["protocolo"] = {c: _campo(resposta, nome) for c, nome in _campos_protocolo(u).items()}
    else:
        corpo["protocolo"] = None
    corpo["lexpre"] = await _lexpre(ctx, ufs)

    execucao: dict[str, Any] = {}
    condenacao, acordos = r.execucao
    for (nome_ng, com_periodo), campos in CAMPOS_EXECUCAO.items():
        nome = condenacao if nome_ng == "execucao" else acordos
        de, ate = (ini, fim) if com_periodo else (None, None)
        execucao.update(_so(await _rota(ctx, v1, nome, de, ate, uf=ufs), campos, u))
    corpo["execucao"] = execucao
    return corpo


MODULE = DashboardModule(
    key="controle-processos",
    source_db="lexflow",
    source_label="LexFlow + Protocolo (legado e LexPre)",
    build=build,
    filters={**FILTROS},
    queries=QUERIES_LEXFLOW,
    extra_queries={
        "ng": tuple(
            dict.fromkeys(
                q for n in ("protocolo", "protocolo_RJ") for q in v1_ng.QUERIES_POR_DASHBOARD[n]
            )
        ),
        "laadv": tuple(v1_la.QUERIES_POR_DASHBOARD["protocolo_LA"]),
        "lexpre": (protocolo_lexpre.QUERY,),
    },
)

# Só as linhas da unidade da tela nas queries que trazem todos os escritórios (app/unit_scope.py).
MODULE = replace(MODULE, unit_scoped=com_recorte(MODULE.queries))
