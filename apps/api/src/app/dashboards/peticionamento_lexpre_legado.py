"""Peticionamento LexPre + legado: KPIs do período e série mês a mês (NG, LARJ/RJ, LAAM/LA).

Quando o período não tem peticionados no LexPre, os cards vêm do Peticionamento legado da unidade.
A série "Peticionados mês a mês" junta legado + LexPre (LexPre prevalece no mês em comum).
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
# NG e LARJ no banco ng; LAAM no laadv (mesma regra do dashboard Peticionamento legado).
LEGADO_PETICIONAMENTO = {
    "ng": {
        "NG": (copia_ng, "peticionamento", "uf_peticionamento"),
        "RJ": (copia_ng, "peticionamento_RJ", "uf_peticionamento"),
    },
    "laadv": {
        "LA": (copia_la, "peticionamento_LA", "uf_peticionamento_LA"),
    },
}

EXTRA_QUERIES = {
    "ng": ("setor_confeccao",),
    "laadv": ("setor_confeccao_LA",),
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

    Cobre o que a página legado tinha nos cards: totais do período, valor, tempos, ticket,
    fila (não peticionados) e, no NG/RJ, revisão. Sem cancelados/protocolados/retornos (só LexPre).

    `stats_fila`: resposta sem período (como a v1), para revisão e fila atuais.
    """
    fila = stats_fila or stats
    if la:
        return {
            "total_peticionados": {
                "total": int(_numero(stats, "total_confeccionados_LA") or 0),
                "comparativo": _numero(stats, "comparativo_confeccionados_LA") or 0.0,
            },
            "peticionados_manualmente": {
                "total": int(_numero(stats, "confeccionados_manualmente_LA") or 0),
                "comparativo": _numero(stats, "comparativo_confeccionados_manualmente_LA") or 0.0,
            },
            "peticionados_automaticamente": {
                "total": int(_numero(stats, "confeccionados_automaticamente_LA") or 0),
                "comparativo": _numero(stats, "comparativo_confeccionados_automaticamente_LA")
                or 0.0,
            },
            "valor_causa_confeccionado": {
                "total": _numero(stats, "valor_causa_confeccionado_LA") or 0.0,
                "comparativo": _numero(stats, "comparativo_valor_causa_confeccionado_LA") or 0.0,
            },
            "ticket_medio_confeccionado": {
                "total": _numero(stats, "ticket_medio_confeccionado_LA") or 0.0,
                "comparativo": _numero(stats, "comparativo_ticket_medio_confeccionado_LA") or 0.0,
            },
            "media_tempo_peticionado": _numero(stats, "tempo_medio_confeccao_LA") or 0.0,
            "mediana_tempo_peticionado": _numero(stats, "mediana_tempo_confeccao_LA") or 0.0,
            "comparativo_tempo_medio_peticionado": _numero(
                stats, "comparativo_tempo_medio_confeccionado_LA"
            )
            or 0.0,
            "comparativo_mediana_tempo_peticionado": _numero(
                stats, "comparativo_mediana_tempo_confeccionado_LA"
            )
            or 0.0,
            "represados": int(_numero(fila, "nao_confeccionados_LA") or 0),
        }
    out: dict[str, Any] = {
        "total_peticionados": {
            "total": int(_numero(stats, "total_peticionados") or 0),
            "comparativo": _numero(stats, "comparativo_peticionados") or 0.0,
        },
        "peticionados_manualmente": {
            "total": int(_numero(stats, "peticionados_manualmente") or 0),
            "comparativo": _numero(stats, "comparativo_peticionados_manualmente") or 0.0,
        },
        "peticionados_automaticamente": {
            "total": int(_numero(stats, "peticionados_automaticamente") or 0),
            "comparativo": _numero(stats, "comparativo_peticionados_automaticamente") or 0.0,
        },
        "valor_causa_confeccionado": {
            "total": _numero(stats, "valor_causa_confeccionado") or 0.0,
            "comparativo": _numero(stats, "comparativo_valor_causa_confeccionado") or 0.0,
        },
        "ticket_medio_confeccionado": {
            "total": _numero(stats, "ticket_medio_confeccionado") or 0.0,
            "comparativo": _numero(stats, "comparativo_ticket_medio_confeccionado") or 0.0,
        },
        "media_tempo_peticionado": _numero(stats, "media_tempo_peticionado") or 0.0,
        "mediana_tempo_peticionado": _numero(stats, "mediana_tempo_peticionado") or 0.0,
        "comparativo_tempo_medio_peticionado": _numero(stats, "comparativo_tempo_medio_peticionado")
        or 0.0,
        "comparativo_mediana_tempo_peticionado": _numero(stats, "comparativo_mediana_tempo_pet")
        or 0.0,
        "represados": int(_numero(fila, "nao_peticionados") or 0),
    }
    revisao = _numero(fila, "processos_em_revisao")
    if revisao is not None:
        out["processos_em_revisao"] = int(revisao)
    return out


def periodo_sem_peticionados_lexpre(stats: dict[str, Any]) -> bool:
    peticionados = stats.get("total_peticionados") or {}
    total = peticionados.get("total") if isinstance(peticionados, dict) else peticionados
    return int(total or 0) == 0


def _chave_mes(name: str) -> str | None:
    texto = str(name or "").strip()
    iso = re.fullmatch(r"(\d{4})-(\d{2})", texto)
    if iso:
        return f"{iso.group(1)}-{iso.group(2)}"
    br = re.fullmatch(r"([a-zç]{3})\w*\.?\s+(\d{4})", texto, re.I)
    if not br:
        return None
    mes = _MESES.index(br.group(1).lower()) + 1 if br.group(1).lower() in _MESES else 0
    return f"{br.group(2)}-{mes:02d}" if mes else None


def pontos_mes_a_mes_do_legado(corpo: dict[str, Any], *, la: bool) -> list[dict[str, Any]]:
    chave = "confeccionados_por_mes_LA" if la else "peticionados_por_mes"
    saida: list[dict[str, Any]] = []
    for p in corpo.get(chave) or []:
        if not isinstance(p, dict):
            continue
        nome, valor = p.get("name"), p.get("value")
        if nome is None or not isinstance(valor, (int, float)):
            continue
        saida.append({"name": str(nome), "value": int(valor)})
    return saida


def juntar_peticionados_por_mes(
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


async def buscar_peticionamento_legado(ctx: DashboardContext) -> dict[str, Any] | None:
    """KPIs do período + série mês a mês do legado; None se a fonte não estiver ligada ou fora do ar.

    A série mês a mês no legado NG/RJ vem do histórico todo (handler sem período), como na página
    legado — o handler com período só devolve o recorte.
    """
    materia = ctx.filters.get("materia") or None
    funcionario = ctx.filters.get("funcionario") or None
    area = ctx.filters.get("area_atuacao_id") or None
    uf = next(iter(ctx.filters.get("uf") or []), None)

    for db, por_ref in LEGADO_PETICIONAMENTO.items():
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
        sub = replace(ctx, source=fonte, source_db=db, unit_ref=ref)

        async def rodar(de, ate):
            return await generico_v1.chamar_v1(
                sub, copia, handler, from_date=de, to_date=ate, **kwargs
            )

        try:
            # Sequencial: chamar_v1 usa ContextVar da fonte.
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
            "peticionados_por_mes": pontos_mes_a_mes_do_legado(corpo_hist, la=la),
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
    """Soma o `total` LexPre + legado; o comparativo permanece o do LexPre."""
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
    """Soma no período o que o legado tinha na seção 01 (volume, valor); ticket e tempos recalculados.

    Fila (represados), cancelados, protocolados e devoluções ficam do LexPre.
    """
    out = {**stats_lexpre}
    n_lex = _total_stat(stats_lexpre, "total_peticionados")
    n_leg = _total_stat(kpis_legado, "total_peticionados")
    n = n_lex + n_leg

    for campo in (
        "total_peticionados",
        "peticionados_manualmente",
        "peticionados_automaticamente",
    ):
        out[campo] = _somar_stat(stats_lexpre, kpis_legado, campo, inteiro=True)

    out["valor_causa_confeccionado"] = _somar_stat(
        stats_lexpre, kpis_legado, "valor_causa_confeccionado", inteiro=False
    )
    valor = _total_stat(out, "valor_causa_confeccionado")
    ticket_lex = (
        stats_lexpre.get("ticket_medio_confeccionado")
        if isinstance(stats_lexpre.get("ticket_medio_confeccionado"), dict)
        else {}
    )
    out["ticket_medio_confeccionado"] = {
        "total": (valor / n) if n else 0.0,
        "comparativo": ticket_lex.get("comparativo"),
    }

    for campo, comp in (
        ("media_tempo_peticionado", "comparativo_tempo_medio_peticionado"),
        ("mediana_tempo_peticionado", "comparativo_mediana_tempo_peticionado"),
    ):
        t_lex = float(stats_lexpre.get(campo) or 0)
        t_leg = float(kpis_legado.get(campo) or 0)
        out[campo] = ((t_lex * n_lex + t_leg * n_leg) / n) if n else 0.0
        if comp in stats_lexpre:
            out[comp] = stats_lexpre[comp]
    return out


def misturar_legado_no_corpo(corpo: dict[str, Any], legado: dict[str, Any]) -> str:
    """Série mês a mês unida; KPIs do período: só legado, só LexPre, ou LexPre + legado.

    Devolve `fonte_indicadores`: 'lexpre' | 'legado' | 'misto'.
    """
    corpo["peticionados_por_mes"] = juntar_peticionados_por_mes(
        corpo.get("peticionados_por_mes") or [],
        legado["peticionados_por_mes"],
    )
    kpis = legado["kpis"]
    stats = corpo.get("stats") or {}
    tem_legado = kpis["total_peticionados"]["total"] > 0 or kpis.get("represados", 0) > 0
    if periodo_sem_peticionados_lexpre(stats):
        if tem_legado:
            corpo["stats"] = {**stats, **kpis}
            return "legado"
        return "lexpre"
    if kpis["total_peticionados"]["total"] > 0:
        corpo["stats"] = acrescentar_kpis_do_legado(stats, kpis)
        return "misto"
    return "lexpre"
