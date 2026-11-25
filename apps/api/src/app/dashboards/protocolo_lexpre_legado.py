"""Protocolo LexPre + legado: KPIs do período e série mês a mês (NG, LARJ/RJ, LAAM/LA).

Quando o período não tem protocolados no LexPre, os cards vêm do Protocolo legado.
Quando os dois têm dado no período, volume e valor somam (misto).
A série "Protocolados mês a mês" junta legado + LexPre (LexPre prevalece no mês em comum).
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

# Banco legado -> ref da unidade -> (cópia v1, rota, parâmetro de UF ou None).
# NG e LARJ no banco ng; LAAM no laadv. A LA não filtra por UF na rota da v1.
LEGADO_PROTOCOLO = {
    "ng": {
        "NG": (copia_ng, "protocolo", "uf_protocolo"),
        "RJ": (copia_ng, "protocolo_RJ", "uf_protocolo"),
    },
    "laadv": {
        "LA": (copia_la, "protocolo_LA", None),
    },
}

EXTRA_QUERIES = {
    "ng": ("setor_protocolo", "comercial_geral_NG"),
    "laadv": ("setor_protocolo_LA", "comercial_geral_LA"),
}

_MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def _numero(stats: dict[str, Any], *campos: str) -> float | None:
    for campo in campos:
        v = stats.get(campo)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def kpis_do_legado(
    stats: dict[str, Any],
    *,
    la: bool,
    stats_fila: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """KPIs do legado no formato da seção 01 do LexPre.

    Cobre protocolados, valor, ticket, tempos, fila e (NG/RJ) reajuizamento.
    Devoluções ficam só no LexPre.
    """
    fila = stats_fila or stats
    if la:
        protocolados = int(_numero(stats, "protocolos_resolvidos_LA") or 0)
        valor = _numero(stats, "valor_causa_protocolado_LA") or 0.0
        ticket = _numero(stats, "ticket_medio_protocolos_resolvidos_LA")
        if ticket is None:
            ticket = (valor / protocolados) if protocolados else 0.0
        return {
            "protocolados_total": {
                "total": protocolados,
                "comparativo": _numero(stats, "comparativo_protocolos_resolvidos_LA") or 0.0,
            },
            "valor_causa_protocolado": {
                "total": valor,
                "comparativo": _numero(stats, "comparativo_valor_causa_protocolado_LA") or 0.0,
            },
            "ticket_medio_protocolado": {
                "total": ticket,
                "comparativo": _numero(stats, "comparativo_ticket_medio_protocolos_resolvidos_LA")
                or 0.0,
            },
            "media_tempo_protocolado": _numero(stats, "media_tempo_protocolo_LA") or 0.0,
            "mediana_tempo_protocolado": _numero(stats, "mediana_tempo_protocolo_LA") or 0.0,
            "comparativo_tempo_medio_protocolado": _numero(
                stats, "comparativo_tempo_medio_protocolos_resolvidos_LA"
            )
            or 0.0,
            "comparativo_mediana_tempo_protocolado": _numero(
                stats, "comparativo_mediana_tempo_protocolos_resolvidos_LA"
            )
            or 0.0,
            "represados": int(_numero(fila, "protocolos_represados_LA") or 0),
        }

    protocolados = int(_numero(stats, "protocolos_resolvidos") or 0)
    valor = _numero(stats, "valor_causa_protocolo_novo") or 0.0
    ticket = _numero(
        stats, "ticket_medio_protocolos_resolvidos", "ticket_medio_protocolado"
    )
    if ticket is None:
        ticket = (valor / protocolados) if protocolados else 0.0
    out: dict[str, Any] = {
        "protocolados_total": {
            "total": protocolados,
            "comparativo": _numero(stats, "comparativo_protocolos_resolvidos") or 0.0,
        },
        "valor_causa_protocolado": {
            "total": valor,
            "comparativo": _numero(stats, "comparativo_valor_causa_protocolo") or 0.0,
        },
        "ticket_medio_protocolado": {
            "total": ticket,
            "comparativo": _numero(
                stats,
                "comparativo_ticket_medio_protocolos_resolvidos",
                "comparativo_ticket_medio_protocolado",
            )
            or 0.0,
        },
        "media_tempo_protocolado": _numero(stats, "media_tempo_protocolado") or 0.0,
        "mediana_tempo_protocolado": _numero(stats, "mediana_tempo_protocolado") or 0.0,
        "comparativo_tempo_medio_protocolado": _numero(
            stats, "comparativo_tempo_medio_protocolos_resolvidos"
        )
        or 0.0,
        "comparativo_mediana_tempo_protocolado": 0.0,
        "represados": int(_numero(fila, "nao_protocolados") or 0),
    }
    reaj = _numero(stats, "protocolados_de_reajuizamento")
    if reaj is not None:
        out["protocolados_de_reajuizamento"] = int(reaj)
    reaj_fila = _numero(fila, "nao_protocolados_de_reajuizamento")
    if reaj_fila is not None:
        out["represados_de_reajuizamento"] = int(reaj_fila)
    return out


def periodo_sem_protocolados_lexpre(stats: dict[str, Any]) -> bool:
    protocolados = stats.get("protocolados_total") or {}
    total = protocolados.get("total") if isinstance(protocolados, dict) else protocolados
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
    chave = "protocolados_por_mes_LA" if la else "protocolados_por_mes"
    saida: list[dict[str, Any]] = []
    for p in corpo.get(chave) or []:
        if not isinstance(p, dict):
            continue
        nome, valor = p.get("name"), p.get("value")
        if nome is None or not isinstance(valor, (int, float)):
            continue
        saida.append({"name": str(nome), "value": int(valor)})
    return saida


def juntar_protocolados_por_mes(
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


def _dump(resposta: Any) -> dict[str, Any]:
    return resposta.model_dump() if hasattr(resposta, "model_dump") else dict(resposta)


def _kwargs_handler_legado(
    handler: Any,
    *,
    materia: Any,
    funcionario: Any,
    area: Any,
    uf: Any,
    param_uf: str | None,
) -> dict[str, Any]:
    """Todos os parâmetros da rota v1, com None no lugar do default `Query(...)`.

    Sem isso, parâmetros não passados (ex.: `sistema` no Protocolo) ficam com o objeto
    Query do FastAPI e filtram a base inteira para zero.
    """
    kwargs = {nome: None for nome in generico_v1._parametros(handler)}
    kwargs.update(
        {
            k: v
            for k, v in {
                "materia": materia,
                "funcionario": funcionario,
                "area_atuacao_id": area,
                **({param_uf: uf} if param_uf else {}),
            }.items()
            if k in kwargs
        }
    )
    return kwargs


async def buscar_protocolo_legado(ctx: DashboardContext) -> dict[str, Any] | None:
    """KPIs do período + série mês a mês do legado; None se a fonte não estiver ligada ou fora do ar."""
    materia = ctx.filters.get("materia") or None
    funcionario = ctx.filters.get("funcionario") or None
    area = ctx.filters.get("area_atuacao_id") or None
    # uf_protocolo na v1 é lista; vazio → None (sem filtro).
    uf = ctx.filters.get("uf") or None

    for db, por_ref in LEGADO_PROTOCOLO.items():
        fonte = ctx.extra_sources.get(db)
        ref = ctx.extra_refs.get(db)
        if fonte is None or ref not in por_ref:
            continue
        copia, rota, param_uf = por_ref[ref]
        handler = copia.HANDLERS[rota]
        kwargs = _kwargs_handler_legado(
            handler,
            materia=materia,
            funcionario=funcionario,
            area=area,
            uf=uf,
            param_uf=param_uf,
        )
        sub = replace(ctx, source=fonte, source_db=db, unit_ref=ref)

        async def rodar(de, ate, sub=sub, copia=copia, handler=handler, kwargs=kwargs):
            return await generico_v1.chamar_v1(
                sub, copia, handler, from_date=de, to_date=ate, **kwargs
            )

        try:
            # Sequencial: chamar_v1 usa ContextVar da fonte; gather em paralelo corrompe o token.
            periodo = await rodar(ctx.period.start, ctx.period.end)
            historico = await rodar(None, None)
        except SourceUnavailable:
            return None
        la = db == "laadv"
        corpo_periodo = _dump(periodo)
        corpo_hist = _dump(historico)
        return {
            "kpis": kpis_do_legado(
                corpo_periodo.get("stats") or {},
                la=la,
                stats_fila=corpo_hist.get("stats") or {},
            ),
            "protocolados_por_mes": pontos_mes_a_mes_do_legado(corpo_hist, la=la),
        }
    return None


def _total_stat(stats: dict[str, Any], campo: str) -> float:
    v = stats.get(campo)
    if isinstance(v, dict):
        n = v.get("total")
        return float(n) if isinstance(n, (int, float)) else 0.0
    return float(v) if isinstance(v, (int, float)) else 0.0


def _somar_stat(
    lexpre: dict[str, Any], legado: dict[str, Any], campo: str, *, inteiro: bool = True
) -> dict[str, Any]:
    a = lexpre.get(campo) if isinstance(lexpre.get(campo), dict) else {}
    b = legado.get(campo) if isinstance(legado.get(campo), dict) else {}
    total = float(a.get("total") or 0) + float(b.get("total") or 0)
    return {
        "total": int(total) if inteiro else total,
        "comparativo": a.get("comparativo"),
    }


def acrescentar_kpis_do_legado(
    stats_lexpre: dict[str, Any], kpis_legado: dict[str, Any]
) -> dict[str, Any]:
    """Soma no período volume e valor do legado; ticket e tempos recalculados.

    Fila (represados) e devoluções ficam do LexPre.
    """
    out = {**stats_lexpre}
    n_lex = _total_stat(stats_lexpre, "protocolados_total")
    n_leg = _total_stat(kpis_legado, "protocolados_total")
    n = n_lex + n_leg

    out["protocolados_total"] = _somar_stat(
        stats_lexpre, kpis_legado, "protocolados_total", inteiro=True
    )
    out["valor_causa_protocolado"] = _somar_stat(
        stats_lexpre, kpis_legado, "valor_causa_protocolado", inteiro=False
    )
    valor = _total_stat(out, "valor_causa_protocolado")
    ticket_lex = (
        stats_lexpre.get("ticket_medio_protocolado")
        if isinstance(stats_lexpre.get("ticket_medio_protocolado"), dict)
        else {}
    )
    out["ticket_medio_protocolado"] = {
        "total": (valor / n) if n else 0.0,
        "comparativo": ticket_lex.get("comparativo"),
    }

    for campo, comp in (
        ("media_tempo_protocolado", "comparativo_tempo_medio_protocolado"),
        ("mediana_tempo_protocolado", "comparativo_mediana_tempo_protocolado"),
    ):
        t_lex = float(stats_lexpre.get(campo) or 0)
        t_leg = float(kpis_legado.get(campo) or 0)
        out[campo] = ((t_lex * n_lex + t_leg * n_leg) / n) if n else 0.0
        if comp in stats_lexpre:
            out[comp] = stats_lexpre[comp]

    # Reajuizamento: LexPre não tem; traz o do legado quando existir.
    for campo in ("protocolados_de_reajuizamento", "represados_de_reajuizamento"):
        if campo in kpis_legado:
            out[campo] = kpis_legado[campo]
    return out


def misturar_legado_no_corpo(corpo: dict[str, Any], legado: dict[str, Any]) -> str:
    """Série mês a mês unida; KPIs: só legado, só LexPre, ou LexPre + legado.

    Devolve `fonte_indicadores`: 'lexpre' | 'legado' | 'misto'.
    """
    corpo["protocolados_por_mes"] = juntar_protocolados_por_mes(
        corpo.get("protocolados_por_mes") or [],
        legado["protocolados_por_mes"],
    )
    kpis = legado["kpis"]
    stats = corpo.get("stats") or {}
    tem_legado = kpis["protocolados_total"]["total"] > 0 or kpis.get("represados", 0) > 0
    if periodo_sem_protocolados_lexpre(stats):
        if tem_legado:
            corpo["stats"] = {**stats, **kpis}
            return "legado"
        return "lexpre"
    if kpis["protocolados_total"]["total"] > 0:
        corpo["stats"] = acrescentar_kpis_do_legado(stats, kpis)
        return "misto"
    return "lexpre"
