"""Configurações das Vinculações (LexFlow, área Estratégico) — a página admin da v1
admin/ConfiguracoesVinculacoesPage.tsx.

v1: GET /admin/configuracoes-vinculacoes e /admin/configuracoes-vinculacoes/export. A query
"configuracoes_vinculacoes" está copiada sem mudança em source_queries.py e o cálculo (como o LexFlow lê cada
vinculação setor + atividade: fluxos de CUMPRIDO / NÃO CUMPRIDO, gatilhos de fase/subfase, campos obrigatórios e os
problemas encontrados) em app/analyses/ADMIN/configuracoes_vinculacoes.py, também sem mudança.

Diferença da v1 (regra da V2: cada unidade vê só o próprio escritório): a v1 mostrava os escritórios assinantes
ativos do LexFlow juntos, com o escritório como filtro da página. Aqui a resposta traz só as vinculações do escritório
da unidade (NG = 20, LA = 21, RJ = 27, como em app/unit_scope.py). O cálculo continua recebendo todas as linhas da
query, porque um encaminhamento para a vinculação de outro escritório é um erro que ele só enxerga com elas.

A página filtra no navegador (setor, status e tipo de problema, como a v1); os mesmos filtros vêm na URL e valem para
a exportação, que na v1 só sabia "todas" ou "só com problemas".
"""

from typing import Any

from app.analyses.ADMIN.configuracoes_vinculacoes import montar_configuracoes_vinculacoes
from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec, NotReady
from app.unit_scope import ESCRITORIO_POR_UNIDADE

QUERY = "configuracoes_vinculacoes"

# Filtros da página (os da v1, menos o escritório: a unidade já é o escritório).
FILTRO_SETOR = "setor_vinculacao"
FILTRO_STATUS = (
    "status_vinculacao"  # ok | incompleta | erro | inativa | todas; sem = as ativas (padrão da v1)
)
FILTRO_PROBLEMA = "problema_vinculacao"  # o TIPO estável do problema (PROBLEMAS_DETALHE[].TIPO)

STATUS_ATIVOS = ("ok", "incompleta", "erro")

# v1: _STATUS_LABEL_CONFIGURACOES_VINCULACOES.
STATUS_LABEL = {
    "ok": "OK",
    "incompleta": "Falta configurar",
    "erro": "Configuração com erro",
    "inativa": "Vinculação inativa",
}

# v1: _CAMPOS_EXPORT_CONFIGURACOES_VINCULACOES + _LABELS_EXPORT_CONFIGURACOES_VINCULACOES, na mesma ordem.
COLUNAS = (
    ("escritorio", "Escritório"),
    ("status", "Status"),
    ("vinculacao_ativa", "Vinculação ativa"),
    ("setor", "Setor"),
    ("atividade", "Atividade"),
    ("tem_configuracao", "Tem configuração"),
    ("configuracao_ativa", "Configuração ativa"),
    ("fase_agendamento", "Fase no agendamento"),
    ("subfase_agendamento", "Subfase no agendamento"),
    ("situacao_agendamento", "Situação no agendamento"),
    ("fase_conclusao", "Fase na conclusão (cumprido)"),
    ("subfase_conclusao", "Subfase na conclusão (cumprido)"),
    ("fase_conclusao_nao_cumprido", "Fase na conclusão (não cumprido)"),
    ("subfase_conclusao_nao_cumprido", "Subfase na conclusão (não cumprido)"),
    ("gatilhos_conclusao", "Gatilhos de encerramento por encaminhamento"),
    ("campos_obrigatorios", "Campos obrigatórios"),
    ("outras_configuracoes", "Outras configurações"),
    ("regra_cumprido", "Regra para cumprido"),
    ("regra_nao_cumprido", "Regra para não cumprido"),
    ("proxima_atividade_cumprido", "Próxima atividade (cumprido)"),
    ("proxima_atividade_nao_cumprido", "Próxima atividade (não cumprido)"),
    ("qtd_problemas", "Qtd. problemas"),
    ("problemas", "Problemas encontrados"),
)


def _escritorio(ctx: DashboardContext) -> int:
    escritorio = ESCRITORIO_POR_UNIDADE.get(ctx.unit_ref)
    if escritorio is None:
        raise NotReady("Configurações das Vinculações existe na NG, no LA e no RJ")
    return escritorio


async def vinculacoes(ctx: DashboardContext) -> list[dict[str, Any]]:
    """As vinculações do escritório da unidade, já avaliadas pelo cálculo da v1 (na ordem dele: erro primeiro)."""
    escritorio = _escritorio(ctx)
    todas = await ctx.remember(("vinculacoes",), lambda: _montar(ctx))
    return [r for r in todas if r["ID_ESCRITORIO_ASSINANTE"] == escritorio]


async def _montar(ctx: DashboardContext) -> list[dict[str, Any]]:
    return montar_configuracoes_vinculacoes(await ctx.source.fetch(QUERY))


async def build(ctx: DashboardContext) -> dict[str, Any]:
    """= GET /admin/configuracoes-vinculacoes da v1, só com o escritório da unidade (sem `atualizado_em`: a V2
    manda a hora do dado em meta.synced_at)."""
    rows = await vinculacoes(ctx)
    return {
        "total": len(rows),
        "total_com_problemas": sum(1 for r in rows if r["QTD_PROBLEMAS"] > 0),
        # Colunas novas de configuracao_atividade que nem o LexFlow rotula ainda e que a auditoria não interpreta.
        "campos_nao_reconhecidos": sorted(
            {o["CAMPO"] for r in rows for o in r["OUTRAS_CONFIGURACOES"] if not o["CONHECIDO"]}
        ),
        "rows": rows,
    }


def _primeiro(ctx: DashboardContext, nome: str) -> str | None:
    valores = [str(v).strip() for v in ctx.filters.get(nome) or [] if str(v).strip()]
    return valores[0] if valores else None


def filtrar(rows: list[dict[str, Any]], ctx: DashboardContext) -> list[dict[str, Any]]:
    """Os filtros da página, como a v1 aplicava no navegador: setor, status (sem = as ativas) e tipo de problema."""
    setor = _primeiro(ctx, FILTRO_SETOR)
    status = _primeiro(ctx, FILTRO_STATUS)
    problema = _primeiro(ctx, FILTRO_PROBLEMA)
    saida = []
    for r in rows:
        if setor and r.get("SETOR") != setor:
            continue
        if status is None and r["STATUS"] not in STATUS_ATIVOS:
            continue
        if status not in (None, "todas") and r["STATUS"] != status:
            continue
        if problema and not any(p["TIPO"] == problema for p in r["PROBLEMAS_DETALHE"]):
            continue
        saida.append(r)
    return saida


def _regra_cumprido(row: dict[str, Any]) -> str:
    """= _regra_cumprido_label da v1."""
    partes = []
    if row.get("REGRA_CUMPRIDO_EXIGE_ANEXO"):
        partes.append("exige anexo")
    if row.get("REGRA_CUMPRIDO_EXIGE_PARECER"):
        partes.append("exige parecer")
    if row.get("REGRA_CUMPRIDO_SEM_EXIGENCIA"):
        partes.append("sem exigência")
    return "; ".join(partes)


def _regra_nao_cumprido(row: dict[str, Any]) -> str:
    """= _regra_nao_cumprido_label da v1."""
    partes = []
    if row.get("REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO"):
        partes.append("exige motivo")
    if row.get("REGRA_NAO_CUMPRIDO_EXIGE_ANEXO"):
        partes.append("exige anexo")
    if row.get("REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO_ANEXO"):
        partes.append("exige motivo + anexo")
    if row.get("REGRA_NAO_CUMPRIDO_NENHUMA_EXIGENCIA"):
        partes.append("sem exigência")
    return "; ".join(partes)


def _gatilho_nc(row: dict[str, Any], campo: str) -> Any:
    """= _gatilho_nc_export da v1: fase/subfase aplicada ao encerrar como NÃO CUMPRIDO (vazio quando não altera)."""
    gatilho = row.get("GATILHO_ENCERRAMENTO_NAO_CUMPRIDO") or {}
    if gatilho.get("ORIGEM") == "nenhum":
        return None
    return gatilho.get(campo)


def _gatilhos_conclusao(row: dict[str, Any]) -> str:
    return "; ".join(
        f"{'Não cumprido' if g.get('FLUXO') == 'nao_cumprido' else 'Cumprido'} · {g['OPCAO']} → "
        f"{' / '.join(x for x in (g.get('FASE'), g.get('SUBFASE')) if x) or 'sem fase/subfase'}"
        + ("" if g.get("ATIVO") else " (inativo)")
        for g in row.get("GATILHOS_CONCLUSAO_POR_ENCAMINHAMENTO") or []
    )


def linha_export(row: dict[str, Any]) -> dict[str, Any]:
    """Uma vinculação nas colunas do export da v1 (export_configuracoes_vinculacoes)."""
    return {
        "escritorio": row.get("ESCRITORIO") or row.get("ID_ESCRITORIO_ASSINANTE"),
        "status": STATUS_LABEL.get(row.get("STATUS"), row.get("STATUS")),
        "vinculacao_ativa": row.get("VINCULACAO_ATIVA"),
        "setor": row.get("SETOR"),
        "atividade": row.get("ATIVIDADE"),
        "tem_configuracao": row.get("TEM_CONFIGURACAO"),
        "configuracao_ativa": row.get("CONFIGURACAO_ATIVA"),
        "fase_agendamento": row.get("FASE_AGENDAMENTO"),
        "subfase_agendamento": row.get("SUBFASE_AGENDAMENTO"),
        "situacao_agendamento": row.get("SITUACAO_AGENDAMENTO"),
        "fase_conclusao": row.get("FASE_CONCLUSAO"),
        "subfase_conclusao": row.get("SUBFASE_CONCLUSAO"),
        "fase_conclusao_nao_cumprido": _gatilho_nc(row, "FASE"),
        "subfase_conclusao_nao_cumprido": _gatilho_nc(row, "SUBFASE"),
        "gatilhos_conclusao": _gatilhos_conclusao(row),
        "campos_obrigatorios": "; ".join(row.get("CAMPOS_OBRIGATORIOS") or []),
        "outras_configuracoes": "; ".join(
            f"{o['LABEL']}: {o['VALOR']}" for o in row.get("OUTRAS_CONFIGURACOES") or []
        ),
        "regra_cumprido": _regra_cumprido(row),
        "regra_nao_cumprido": _regra_nao_cumprido(row),
        "proxima_atividade_cumprido": row.get("PROXIMA_ATIVIDADE_CUMPRIDO") or "",
        "proxima_atividade_nao_cumprido": row.get("PROXIMA_ATIVIDADE_NAO_CUMPRIDO") or "",
        "qtd_problemas": row.get("QTD_PROBLEMAS"),
        "problemas": "; ".join(row.get("PROBLEMAS") or []),
    }


async def export_rows(ctx: DashboardContext) -> list[dict[str, Any]]:
    """As vinculações da tela (com os filtros dela) nas colunas do export da v1."""
    return [linha_export(r) for r in filtrar(await vinculacoes(ctx), ctx)]


EXPORT = ExportSpec(
    fields={slug: slug for slug, _ in COLUNAS},
    labels=dict(COLUNAS),
    sheet_name="Vinculações",
    rows=export_rows,
)

MODULE = DashboardModule(
    key="configuracoes-vinculacoes",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={FILTRO_SETOR: str, FILTRO_STATUS: str, FILTRO_PROBLEMA: str},
    export=EXPORT,
    queries=(QUERY,),
)
