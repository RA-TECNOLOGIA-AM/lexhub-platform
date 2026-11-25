"""OrgDoc LexPre + legado: KPIs do período e série mês a mês (NG, LARJ/RJ, LAAM/LA).

Quando o período não tem resolvidos no LexPre, os cards vêm do OrgDoc legado da unidade.
A série "Resolvidos mês a mês" junta legado + LexPre (LexPre prevalece no mês em comum).
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any

from app.analyses import v1_dashboard_generico_la as copia_la
from app.analyses import v1_dashboard_generico_ng as copia_ng
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext
from app.database import SourceUnavailable

# Banco legado -> ref da unidade -> (cópia v1, rota, parâmetro de UF).
# NG e LARJ no banco ng; LAAM no laadv (mesma regra do dashboard OrgDoc legado).
LEGADO_ORG_DOC = {
    "ng": {
        "NG": (copia_ng, "org-documentos", "uf_org_doc"),
        "RJ": (copia_ng, "org_doc_RJ", "uf_org_doc"),
    },
    "laadv": {
        "LA": (copia_la, "org_doc_LA", "uf_org_doc_LA"),
    },
}

EXTRA_QUERIES = {
    "ng": ("setor_org_doc",),
    "laadv": ("setor_org_documentos_LA",),
}

_MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def _numero(stats: dict[str, Any], *campos: str) -> float | None:
    for campo in campos:
        v = stats.get(campo)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def kpis_do_legado(stats: dict[str, Any], *, la: bool) -> dict[str, Any]:
    """KPIs do legado no formato dos cards LexPre (sem represados nem devolvido_pendencia)."""
    if la:
        return {
            "resolvidos_total": {
                "total": int(_numero(stats, "total_organizados_LA") or 0),
                "comparativo": _numero(stats, "comparativo_resolvidos_total_LA") or 0.0,
            },
            "organizados_manualmente": {
                "total": int(_numero(stats, "total_organizados_manualmente_LA") or 0),
                "comparativo": _numero(stats, "comparativo_organizados_manualmente_LA") or 0.0,
            },
            "organizados_e_peticionados_automaticamente": {
                "total": int(_numero(stats, "total_organizados_automaticamente_LA") or 0),
                "comparativo": _numero(stats, "comparativo_organizados_automaticamente_LA") or 0.0,
            },
            "cancelados": {
                "total": int(_numero(stats, "cancelados_LA") or 0),
                "comparativo": _numero(stats, "comparativo_cancelados_LA") or 0.0,
            },
            "media_tempo_resolvidos": _numero(stats, "media_tempo_resolvidos_LA") or 0.0,
            "mediana_tempo_resolvidos": _numero(stats, "mediana_tempo_resolvidos_LA") or 0.0,
            "comparativo_tempo_medio_resolvidos": 0.0,
            "comparativo_mediana_tempo_resolvidos": 0.0,
        }
    return {
        "resolvidos_total": {
            "total": int(_numero(stats, "resolvidos_total") or 0),
            "comparativo": _numero(stats, "comparativo_resolvidos_total") or 0.0,
        },
        "organizados_manualmente": {
            "total": int(_numero(stats, "organizados_manualmente") or 0),
            "comparativo": _numero(stats, "comparativo_organizados_manualmente") or 0.0,
        },
        "organizados_e_peticionados_automaticamente": {
            "total": int(_numero(stats, "organizados_e_peticionados_automaticamente") or 0),
            "comparativo": _numero(stats, "comparativo_organizados_e_peticionados_automaticamente")
            or 0.0,
        },
        "cancelados": {
            "total": int(_numero(stats, "cancelados") or 0),
            "comparativo": _numero(stats, "comparativo_cancelados") or 0.0,
        },
        "media_tempo_resolvidos": _numero(stats, "media_tempo_resolvidos") or 0.0,
        "mediana_tempo_resolvidos": _numero(stats, "mediana_tempo_resolvidos") or 0.0,
        "comparativo_tempo_medio_resolvidos": _numero(
            stats, "comparativo_tempo_medio_resolvidos_org_doc"
        )
        or 0.0,
        "comparativo_mediana_tempo_resolvidos": 0.0,
    }


def periodo_sem_resolvidos_lexpre(stats: dict[str, Any]) -> bool:
    resolvidos = stats.get("resolvidos_total") or {}
    total = resolvidos.get("total") if isinstance(resolvidos, dict) else resolvidos
    return int(total or 0) == 0


def _chave_mes(name: str) -> str | None:
    texto = str(name or "").strip()
    iso = re.fullmatch(r"(\d{4})-(\d{2})", texto)
    if iso:
        return f"{iso.group(1)}-{iso.group(2)}"
    br = re.fullmatch(r"([a-zç]{3})\w*\.?\s+(\d{4})", texto, re.IGNORECASE)
    if not br:
        return None
    mes = _MESES.index(br.group(1).lower()) + 1 if br.group(1).lower() in _MESES else 0
    return f"{br.group(2)}-{mes:02d}" if mes else None


def pontos_mes_a_mes_do_legado(corpo: dict[str, Any], *, la: bool) -> list[dict[str, Any]]:
    chave = "resolvidos_total_por_mes_LA" if la else "resolvidos_total_por_mes"
    saida: list[dict[str, Any]] = []
    for p in corpo.get(chave) or []:
        if not isinstance(p, dict):
            continue
        nome, valor = p.get("name"), p.get("value")
        if nome is None or not isinstance(valor, (int, float)):
            continue
        saida.append({"name": str(nome), "value": int(valor)})
    return saida


def juntar_resolvidos_por_mes(
    lexpre: list[dict[str, Any]], legado: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Une as séries: LexPre prevalece no mês em que as duas têm dado."""
    por_mes: dict[str, dict[str, Any]] = {}
    for origem in (legado, lexpre):
        for p in origem or []:
            chave = _chave_mes(str(p.get("name") or ""))
            if not chave:
                continue
            valor = p.get("value")
            if not isinstance(valor, (int, float)):
                continue
            por_mes[chave] = {"name": str(p["name"]), "value": int(valor)}
    return [por_mes[k] for k in sorted(por_mes)]


async def buscar_org_doc_legado(ctx: DashboardContext) -> dict[str, Any] | None:
    """Resposta do OrgDoc legado da unidade; None se a fonte não estiver ligada ou fora do ar."""
    materia = ctx.filters.get("materia") or None
    funcionario = ctx.filters.get("funcionario") or None
    area = ctx.filters.get("area_atuacao_id") or None
    uf = next(iter(ctx.filters.get("uf") or []), None)

    for db, por_ref in LEGADO_ORG_DOC.items():
        fonte = ctx.extra_sources.get(db)
        ref = ctx.extra_refs.get(db)
        if fonte is None or ref not in por_ref:
            continue
        copia, rota, param_uf = por_ref[ref]
        handler = copia.HANDLERS[rota]
        # None em todo parâmetro da rota: evita default FastAPI `Query(...)` filtrar a base.
        kwargs = {nome: None for nome in generico_v1._parametros(handler)}
        kwargs.update(
            {
                k: v
                for k, v in {
                    "materia": materia,
                    "funcionario": funcionario,
                    "area_atuacao_id": area,
                    param_uf: uf,
                }.items()
                if k in kwargs
            }
        )
        try:
            resposta = await generico_v1.chamar_v1(
                replace(ctx, source=fonte, source_db=db, unit_ref=ref),
                copia,
                handler,
                from_date=ctx.period.start,
                to_date=ctx.period.end,
                **kwargs,
            )
        except SourceUnavailable:
            return None
        corpo = resposta.model_dump() if hasattr(resposta, "model_dump") else dict(resposta)
        la = db == "laadv"
        return {
            "kpis": kpis_do_legado(corpo.get("stats") or {}, la=la),
            "resolvidos_por_mes": pontos_mes_a_mes_do_legado(corpo, la=la),
        }
    return None


def misturar_legado_no_corpo(corpo: dict[str, Any], legado: dict[str, Any]) -> str:
    """Aplica série mês a mês e, se o LexPre não tiver resolvidos no período, os KPIs do legado.

    Devolve `fonte_indicadores`: 'lexpre' ou 'legado'.
    """
    corpo["resolvidos_total_por_mes"] = juntar_resolvidos_por_mes(
        corpo.get("resolvidos_total_por_mes") or [],
        legado["resolvidos_por_mes"],
    )
    kpis = legado["kpis"]
    if periodo_sem_resolvidos_lexpre(corpo.get("stats") or {}) and (
        kpis["resolvidos_total"]["total"] > 0 or kpis["cancelados"]["total"] > 0
    ):
        corpo["stats"] = {**corpo["stats"], **kpis}
        return "legado"
    return "lexpre"
