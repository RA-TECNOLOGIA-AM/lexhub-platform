"""Marketing (banco NG) — dashboard da v1 /marketing_NG, sem mudança. Só existe para a NG na v1.

O cálculo é o da v1, na cópia app/analyses/v1_dashboard_generico_ng.py (handler "marketing_NG") e em
app/analyses/NG/marketing_ng.py. Na v1 a página filtrava clicando nos gráficos e mandava pares
`selection_dim` / `selection_value`; aqui cada dimensão é um filtro da V2 com o sufixo _marketing (os mesmos do
Marketing (LexPre), mais o dispositivo), convertido nos mesmos pares. Vários valores na mesma dimensão = OU.

Novo na V2: desde set/2026 o comercial da NG é registrado no LexPre (o banco NG parou de receber atendimentos em
22/10/2026). A resposta soma os números do Marketing (LexPre) do escritório da NG (marketing_soma_lexpre.py) e diz
em `lexpre` se a soma entrou: {"somado": bool, "motivo": texto quando não entrou}.

Exportação (nova na V2; a v1 não exportava esta página), nas colunas da do Marketing (LexPre):
  * Leads — uma linha por lead (atendimento que entrou no período, com a coluna "Assinado"): os do banco NG
    (actions_NG_2, a base do "Leads" da página, com o perfil e a campanha do cliente) e os do LexPre do escritório
    da NG (o relatório de Leads do Marketing (LexPre)), com a coluna "Base" dizendo de onde veio. Segue o período
    e os filtros da tela.
  * Facebook Ads — o relatório do Marketing (LexPre) do escritório da NG.

Facebook Ads: das contas da Meta conectadas na unidade (app/dashboards/anuncios_meta.py), as mesmas no cálculo
do banco NG e no do LexPre; sem conta conectada, da tabela metrics_ads.facebook_ads do banco NG, como na v1.
"""

from dataclasses import replace
from typing import Any

from app.analyses import v1_dashboard_generico_ng as copia
from app.analyses.NG.marketing_ng import (
    _calc_idade,
    _faixa_etaria,
    _is_truthy,
    _status_protocolo_resolvido,
    _valor_causa_row_analise_thiago,
)
from app.dashboards import generico_v1, marketing_lexpre
from app.dashboards.anuncios_meta import com_anuncios_da_meta
from app.dashboards.base import (
    DashboardContext,
    DashboardInputError,
    DashboardModule,
    ExportSpec,
    NotReady,
)
from app.dashboards.marketing_lexpre import FILTROS as FILTROS_LEXPRE
from app.dashboards.marketing_soma_lexpre import somar_lexpre
from app.database import SourceUnavailable

# Filtro da V2 -> dimensão da v1 (_FIELD_MAP_CLIENTES, _FIELD_MAP_ANALISE_THIAGO e _FIELD_MAP_TRACKEAMENTO).
DIMENSOES = {**FILTROS_LEXPRE, "dispositivo_marketing": "dispositivo"}


def selecao(filters: dict[str, list[str]]) -> tuple[list[str] | None, list[str] | None]:
    """Os pares (dimensão, valor) da v1, um por valor escolhido."""
    dims: list[str] = []
    valores: list[str] = []
    for filtro, dim in DIMENSOES.items():
        for valor in filters.get(filtro) or []:
            if valor:
                dims.append(dim)
                valores.append(str(valor))
    return (dims or None, valores or None)


def contexto_lexpre(ctx: DashboardContext) -> tuple[DashboardContext | None, str | None]:
    """O contexto do Marketing (LexPre) do escritório da unidade (mesmo período, filtros e opções de exportação);
    (None, motivo) sem ele."""
    fonte = ctx.extra_sources.get("lexpre")
    ref = ctx.extra_refs.get("lexpre")
    if fonte is None or ref is None:
        return None, "A unidade não está ligada ao LexPre."
    if ctx.filters.get("dispositivo_marketing"):
        return None, "O LexPre não registra o dispositivo: com esse filtro, só o banco NG."
    return replace(
        ctx,
        source=fonte,
        unit_ref=ref,
        source_db="lexpre",
        # Sem conta da Meta conectada (ctx.ads_sources, que segue no contexto), o Facebook Ads do LexPre vem do
        # banco ng (o mesmo deste dashboard): CAC e ROAS do LexPre precisam dele.
        extra_sources={"ng": ctx.source},
        extra_refs={"ng": ctx.unit_ref},
    ), None


async def lexpre_da_unidade(ctx: DashboardContext) -> tuple[dict | None, str | None]:
    """O Marketing (LexPre) do escritório da unidade, com o mesmo período e filtros; (None, motivo) sem ele."""
    lexpre_ctx, motivo = contexto_lexpre(ctx)
    if lexpre_ctx is None:
        return None, motivo
    try:
        return await marketing_lexpre.build(lexpre_ctx), None
    except SourceUnavailable:
        return None, "LexPre fora do ar: só os números do banco NG."


async def build(ctx: DashboardContext) -> dict:
    if ctx.unit_ref != "NG":
        raise NotReady("Marketing (banco NG) só existe na v1 para a NG")
    dims, valores = selecao(ctx.filters)
    resposta = await generico_v1.chamar_v1(
        # O Facebook Ads das contas da Meta da unidade, se conectadas (senão, o do banco ng).
        replace(ctx, source=com_anuncios_da_meta(ctx)),
        copia,
        copia.HANDLERS["marketing_NG"],
        from_date=ctx.period.start,
        to_date=ctx.period.end,
        selection_dim=dims,
        selection_value=valores,
    )
    corpo = resposta.model_dump()
    lexpre, motivo = await lexpre_da_unidade(ctx)
    if lexpre is None:
        return {**corpo, "lexpre": {"somado": False, "motivo": motivo}}
    return {**somar_lexpre(corpo, lexpre), "lexpre": {"somado": True, "motivo": None}}


# --------------------------------------------------------------------------------------------------------------------
# Exportação (nova na V2): Leads (banco NG + LexPre) e Facebook Ads, nas colunas do Marketing (LexPre).
# --------------------------------------------------------------------------------------------------------------------

BASE_NG = "Banco NG"
BASE_LEXPRE = "LexPre"
CAMPOS_LEADS = {"base": "Base", **marketing_lexpre.CAMPOS_EXPORT_MARKETING_LEXPRE}


def _data(v: Any) -> Any:
    return v.date() if hasattr(v, "date") and callable(v.date) else v


def _juntar(valores: list[Any]) -> str:
    return ", ".join(
        dict.fromkeys(str(v).strip() for v in valores if v is not None and str(v).strip())
    )


def _por_action(rows: list[dict[str, Any]]) -> dict[Any, list[dict[str, Any]]]:
    por: dict[Any, list[dict[str, Any]]] = {}
    for r in rows:
        por.setdefault(r.get("ID_ACTION"), []).append(r)
    return por


# As dimensões dos filtros que só existem na campanha detalhada / processo (Analise_thiago): um lead passa se algum
# processo dele passa. As outras são lidas do próprio lead (atendimento + perfil do cliente).
_DIMS_ANALISE = set(copia._FIELD_MAP_ANALISE_THIAGO) - set(copia._FIELD_MAP_CLIENTES)


def linhas_leads_ng(
    leads: list[dict[str, Any]],
    perfis: list[dict[str, Any]],
    analise: list[dict[str, Any]],
    pares: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Os leads do banco NG (actions_NG_2: atendimentos que entraram no período, a base do "Leads" da página) nas
    colunas do relatório de Leads, com o perfil do cliente (perfil_clientes_NG, só dos atendimentos fechados) e a
    campanha detalhada, demandas e protocolos do atendimento (Analise_thiago, uma linha por processo)."""
    perfil = {a: rs[0] for a, rs in _por_action(perfis).items()}
    processos_por = _por_action(analise)
    pares_lead = [(d, v) for d, v in pares if d not in _DIMS_ANALISE]
    pares_proc = [(d, v) for d, v in pares if d in _DIMS_ANALISE]
    linhas = []
    vistos: set[Any] = set()
    for a in leads:
        action = a.get("ID_ACTION")
        if action in vistos:
            continue
        vistos.add(action)
        p = perfil.get(action, {})
        # O lead com as colunas do perfil, para os filtros da página (_FIELD_MAP_CLIENTES).
        lead = {
            **p,
            "CANAL_AQUISICAO": a.get("CANAL_ATUAL") or p.get("CANAL_AQUISICAO"),
            "TIPO_TRAFEGO": a.get("TIPO_TRAFEGO") or p.get("TIPO_TRAFEGO"),
            "PROPECCAO": a.get("PROSPECCAO") or p.get("PROPECCAO"),
        }
        if pares_lead and not copia.apply_selection_filters(
            [lead], pares_lead, copia._FIELD_MAP_CLIENTES
        ):
            continue
        proc = processos_por.get(action, [])
        if pares_proc and not copia.apply_selection_filters(
            proc, pares_proc, copia._FIELD_MAP_ANALISE_THIAGO
        ):
            continue
        processos = {r.get("ID_PROCESSO"): r for r in proc if r.get("ID_PROCESSO") is not None}
        protocolados = [r for r in processos.values() if _status_protocolo_resolvido(r)]
        idade = _calc_idade(p.get("DATA_NASCIMENTO"))
        assinado = a.get("ASSINADO_EM") is not None and a.get("MOTIVO_ENCERRAMENTO") == 11
        linhas.append(
            {
                "base": BASE_NG,
                "id_action": action,
                "cliente": a.get("CLIENTE"),
                "atendente": a.get("ATENDENTE"),
                "uf": a.get("UF"),
                "data_entrada": _data(a.get("ENTRADA")),
                # O banco NG só traz o id do status: o texto sai do ciclo do atendimento.
                "status": "Assinado"
                if assinado
                else ("Encerrado" if a.get("data_encerramento") else "Em andamento"),
                "assinado": "Sim" if assinado else "Não",
                "data_assinatura": _data(a.get("ASSINADO_EM")) if assinado else None,
                "canal_aquisicao": lead["CANAL_AQUISICAO"],
                "tipo_trafego": lead["TIPO_TRAFEGO"],
                "prospeccao": lead["PROPECCAO"],
                "campanha": a.get("CAMPANHA"),
                "conjunto": _juntar([r.get("NOME_CONJUNTO") for r in proc]),
                "criativo": _juntar([r.get("CRIATIVO") for r in proc]),
                "posicionamento": _juntar([r.get("POSICIONAMENTO") for r in proc]),
                "plataforma_anuncio": p.get("PLATAFORMA"),
                "categoria": None,
                "idade": idade,
                "faixa_etaria": _faixa_etaria(idade) if idade is not None else None,
                "genero": p.get("GENERO"),
                "ocupacao": p.get("OCUPACAO"),
                "media_salarial": p.get("MEDIA_MENSAL"),
                "tipo_residencia": p.get("TIPO_RESIDENCIA"),
                "pessoas_dependentes": p.get("PESSOAS_DEPENDENTES"),
                "triado": ("Sim" if _is_truthy(p.get("RESP_TRIAGEM?")) else "Não") if p else None,
                "qtd_demandas": len(processos),
                "rubricas": _juntar([r.get("RUBRICA") for r in processos.values()]),
                "qtd_protocolados": len(protocolados),
                "valor_causa_protocolado": round(
                    sum(_valor_causa_row_analise_thiago(r) for r in protocolados), 2
                ),
            }
        )
    return linhas


async def export_leads(ctx: DashboardContext) -> list[dict[str, Any]]:
    """Leads da página: banco NG (atendimentos que entraram no período) + LexPre do escritório da NG."""
    if ctx.unit_ref != "NG":
        raise NotReady("Marketing (banco NG) só existe na v1 para a NG")
    dims, valores = selecao(ctx.filters)
    pares = list(zip(dims or [], valores or []))
    # A base do "Leads" da página (v1: pipeline_rows = actions por ENTRADA no período).
    leads = copia._filter_by_columns(
        await ctx.source.fetch("actions_NG_2"), ["ENTRADA"], ctx.period.start, ctx.period.end
    )
    linhas = linhas_leads_ng(
        leads,
        await ctx.source.fetch("perfil_clientes_NG"),
        await ctx.source.fetch("Analise_thiago"),
        pares,
    )
    lexpre_ctx, _ = contexto_lexpre(ctx)
    if lexpre_ctx is not None:
        try:
            linhas += [
                {"base": BASE_LEXPRE, **r} for r in await marketing_lexpre.export_leads(lexpre_ctx)
            ]
        except SourceUnavailable:
            pass  # LexPre fora do ar: o relatório sai só com o banco NG, como a página
    return linhas


async def export_facebook(ctx: DashboardContext) -> list[dict[str, Any]]:
    """O Facebook Ads do Marketing (LexPre) do escritório da NG (contas da Meta da unidade ou banco NG)."""
    if ctx.unit_ref != "NG":
        raise NotReady("Marketing (banco NG) só existe na v1 para a NG")
    lexpre_ctx, motivo = contexto_lexpre(replace(ctx, filters={}))
    if lexpre_ctx is None:
        raise DashboardInputError(f"Relatório do Facebook Ads indisponível: {motivo}")
    return await marketing_lexpre.export_facebook(lexpre_ctx)


FACEBOOK = marketing_lexpre.MODULE.export_reports["facebook"]

MODULE = DashboardModule(
    key="marketing",
    source_db="ng",
    source_label="NG",
    build=build,
    filters=dict.fromkeys(DIMENSOES, str),
    queries=copia.QUERIES_POR_DASHBOARD["marketing_NG"],
    # Novo na V2: o comercial do LexPre (escritório da NG) somado aos números do banco NG.
    extra_queries={"lexpre": marketing_lexpre.QUERIES},
    meta_ads=True,
    export=ExportSpec(
        fields={slug: slug for slug in CAMPOS_LEADS},
        labels=CAMPOS_LEADS,
        sheet_name="Leads",
        rows=export_leads,
        title="Leads",
    ),
    export_reports={"facebook": replace(FACEBOOK, rows=export_facebook)},
)
