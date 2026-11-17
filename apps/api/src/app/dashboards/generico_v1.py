"""Molde para os dashboards "genéricos" da v1 (Execução, Acordos e Recursal no LexFlow; Protocolo,
Peticionamento, Org. de Documentos e Pendências no banco NG).

Na v1 cada unidade tem a sua rota e o seu ramo em `_get_dashboard_response` (ex.: Execução:
/execucao para NG, /execucao_LA, /execucao_RJ), todos copiados sem mudança em
app/analyses/v1_dashboard_generico.py (LexFlow) e v1_dashboard_generico_ng.py (banco NG, gerado por
scripts/copiar_v1/gerar_generico.py). Aqui só a entrada muda:

    v1                                         aqui
    rota por unidade (/execucao_LA)        ->  unidade -> ref no LexFlow (app.unit_source_refs: "NG", "LA", "RJ")
                                               -> nome do dashboard na v1 (`v1_por_unidade`)
    parâmetros da rota (Query)             ->  ctx.filters, com os mesmos nomes; lista ou um valor,
                                               como a anotação do handler da v1
    from / to                              ->  ctx.period
    situacao_processo (middleware da v1)   ->  filtro situacao_processo (mesmo ContextVar da v1)
    fetch_data_with_cache                  ->  ctx.source (cache de 5 min da V2), por usar_fonte

A resposta é a mesma DashboardResponse da v1 (model_dump). As opções dos filtros já vêm dentro de
`stats`, como na v1 (ex.: execucao_uf_opcoes_NG).
"""

import inspect
import typing
from collections.abc import Callable
from datetime import date
from types import ModuleType
from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.analyses.situacao_processo import _situacoes_processo_ctx, parse_situacoes_processo
from app.dashboards.base import (
    AltSource,
    DashboardContext,
    DashboardInputError,
    DashboardModule,
    NotReady,
)

FILTRO_SITUACAO = "situacao_processo"  # v1: PARAM_SITUACAO_PROCESSO, lido pelo middleware


def _e_lista(anotacao: Any) -> bool:
    """Optional[List[x]] na rota da v1 = aceita vários valores; Optional[x] = um só."""
    return any(typing.get_origin(a) is list for a in (anotacao, *typing.get_args(anotacao)))


def _tipo(anotacao: Any) -> type:
    """int se a rota da v1 recebe números (ex.: id_1g do Recursal); senão str."""
    for a in (anotacao, *typing.get_args(anotacao)):
        for b in (a, *typing.get_args(a)):
            if b is int:
                return int
    return str


def _parametros(handler: Callable) -> dict[str, inspect.Parameter]:
    return {
        n: p
        for n, p in inspect.signature(handler).parameters.items()
        if n not in ("from_date", "to_date")
    }


def _filtros(copia: ModuleType, nomes_v1: list[str]) -> dict[str, type]:
    """Os parâmetros das rotas da v1 do dashboard (todas as unidades) + situacao_processo."""
    filtros: dict[str, type] = {}
    for nome in nomes_v1:
        for n, p in _parametros(copia.HANDLERS[nome]).items():
            filtros.setdefault(n, _tipo(p.annotation))
    filtros[FILTRO_SITUACAO] = str
    return filtros


def _lado(resposta: dict, campo: str) -> tuple[dict, str]:
    """ "stats.x" -> (resposta["stats"], "x"); "x" -> (resposta, "x"). Cria `stats` se faltar."""
    if campo.startswith("stats."):
        if resposta.get("stats") is None:
            resposta["stats"] = {}
        return resposta["stats"], campo[6:]
    return resposta, campo


async def chamar_v1(
    ctx: DashboardContext, copia: ModuleType, fn: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """Roda uma função da cópia da v1 (ex.: as linhas de uma exportação) com a fonte do pedido e o recorte de
    situação do processo dos filtros, como o cálculo do dashboard."""
    try:
        situacao = parse_situacoes_processo(ctx.filters.get(FILTRO_SITUACAO, []))
    except ValueError as exc:
        raise DashboardInputError(str(exc)) from None
    token_fonte = copia.usar_fonte(ctx.source)
    token_situacao = _situacoes_processo_ctx.set(situacao)
    try:
        return await fn(*args, **kwargs)
    finally:
        _situacoes_processo_ctx.reset(token_situacao)
        copia._fonte_ctx.reset(token_fonte)


def nome_na_unidade(nome: str, unidade: str) -> str:
    """Nome de um campo da rota NG da v1 na rota da unidade (_LA, _RJ): a regra das rotas da Execução.

    "x_NG" -> "x_LA"; "x_NG_detalhe" / "x_detalhe" -> "x_LA_detalhe"; sem sufixo ("tre") -> "tre_LA".
    """
    if unidade == "NG":
        return nome
    if nome.endswith("_NG"):
        return f"{nome[:-3]}_{unidade}"
    if nome.endswith("_NG_detalhe"):
        return f"{nome[: -len('_NG_detalhe')]}_{unidade}_detalhe"
    if nome.endswith("_detalhe"):
        return f"{nome[: -len('_detalhe')]}_{unidade}_detalhe"
    return f"{nome}_{unidade}"


def historico_por_unidade(
    campos_ng: tuple[str, ...], unidades: tuple[str, ...]
) -> dict[str, tuple[str, ...]]:
    """O `historico` de cada unidade a partir do da NG ("stats.x" e "destino=origem": só a origem muda de nome)."""

    def traduz(campo: str, u: str) -> str:
        para, _, de = campo.partition("=")
        if de:
            return f"{para}={traduz(de, u)}"
        prefixo = "stats." if campo.startswith("stats.") else ""
        return prefixo + nome_na_unidade(campo.removeprefix("stats."), u)

    return {u: tuple(traduz(c, u) for c in campos_ng) for u in unidades}


def modulo(
    key: str,
    v1_por_unidade: dict[str, str],
    descricao_falta: str,
    copia: ModuleType = v1,
    source_db: str = "lexflow",
    source_label: str = "LexFlow",
    alternativas: dict[str, tuple[ModuleType, str]] | None = None,
    commission_fields: tuple[str, ...] = (),
    historico: tuple[str, ...] | dict[str, tuple[str, ...]] = (),
) -> DashboardModule:
    """DashboardModule de um dashboard genérico da v1.

    `v1_por_unidade`: ref da unidade na fonte -> nome do dashboard na v1. `copia`: o módulo com a cópia
    da v1 (v1_dashboard_generico = LexFlow; v1_dashboard_generico_ng = banco NG), lido pelo banco `source_db`.
    `alternativas`: outros bancos (banco -> (cópia, rótulo)) para as unidades sem `source_db`, ex.: a LA,
    que na v1 tem as rotas _LA no banco laadv. `commission_fields`: as listas de comissão da resposta (quem
    não gere a unidade recebe só a própria linha). `historico`: campos que vêm do histórico todo (o mesmo
    handler sem período), como os gráficos "mês a mês", que na v1 a página buscava numa chamada sem data;
    "stats.<campo>" para um número de dentro de `stats`; "<destino>=<origem>" grava com outro nome, quando o
    mesmo campo tem sentido diferente nas duas chamadas (ex.: na Execução, `total_em_execucao` com período é
    a entrada do período e sem período é o total em execução). Um dict ({ref da unidade: campos}) quando os
    nomes mudam por unidade (ver `historico_por_unidade`).
    """
    alternativas = alternativas or {}
    copias = {source_db: copia, **{db: c for db, (c, _) in alternativas.items()}}

    async def build(ctx: DashboardContext) -> dict:
        copia = copias.get(ctx.source_db, copias[source_db])
        nome = v1_por_unidade.get(ctx.unit_ref)
        if nome is None or nome not in copia.HANDLERS:
            raise NotReady(descricao_falta)
        handler = copia.HANDLERS[nome]
        kwargs: dict[str, Any] = {}
        for n, p in _parametros(handler).items():
            valores = ctx.filters.get(n, [])
            kwargs[n] = (valores or None) if _e_lista(p.annotation) else next(iter(valores), None)
        try:
            situacao = parse_situacoes_processo(ctx.filters.get(FILTRO_SITUACAO, []))
        except ValueError as exc:
            raise DashboardInputError(str(exc)) from None

        async def rodar(de: date | None, ate: date | None) -> dict:
            token_fonte = copia.usar_fonte(ctx.source)
            token_situacao = _situacoes_processo_ctx.set(situacao)
            try:
                response = await handler(from_date=de, to_date=ate, **kwargs)
            finally:
                _situacoes_processo_ctx.reset(token_situacao)
                copia._fonte_ctx.reset(token_fonte)
            return response.model_dump()

        body = await rodar(ctx.period.start, ctx.period.end)
        # Um tuple vale para todas as unidades; um dict, por ref da unidade (os nomes da v1 mudam: _NG, _LA, _RJ).
        campos_hist = historico.get(ctx.unit_ref, ()) if isinstance(historico, dict) else historico
        if campos_hist:
            # Os mesmos filtros, sem período (na v1, a segunda chamada da página sem data).
            todo = await rodar(None, None)
            for campo in campos_hist:
                # "destino=origem": grava com outro nome; "stats.x" = um campo de dentro de stats
                para, _, de = campo.partition("=")
                origem, nome_origem = _lado(todo, de or para)
                destino, nome_destino = _lado(body, para)
                if nome_origem in origem:
                    destino[nome_destino] = origem[nome_origem]
        return body

    def nomes_de(c: ModuleType) -> list[str]:
        return [n for n in dict.fromkeys(v1_por_unidade.values()) if n in c.HANDLERS]

    def queries_de(c: ModuleType) -> tuple[str, ...]:
        return tuple(dict.fromkeys(q for n in nomes_de(c) for q in c.QUERIES_POR_DASHBOARD[n]))

    filtros: dict[str, type] = {}
    for c in copias.values():
        for n, t in _filtros(c, nomes_de(c)).items():
            filtros.setdefault(n, t)
    return DashboardModule(
        key=key,
        source_db=source_db,
        source_label=source_label,
        build=build,
        filters=filtros,
        queries=queries_de(copia),
        alt_sources={
            db: AltSource(rotulo, queries_de(c)) for db, (c, rotulo) in alternativas.items()
        },
        commission_fields=commission_fields,
    )
