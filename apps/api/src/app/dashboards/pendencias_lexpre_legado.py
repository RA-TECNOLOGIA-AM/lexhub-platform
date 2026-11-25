"""Pendências LexPre + legado: KPIs, origem das não resolvidas e série mês a mês (NG, LARJ/RJ, LAAM/LA).

As pendências da unidade estão nos dois sistemas (o legado até a migração, o LexPre depois), então tudo soma:
- volume do período (total, resolvidas, canceladas, triagem, reajuizamento) e a fila de agora (não resolvidas,
  as com mais de 5 dias e a origem delas);
- taxas e tempos: média das duas fontes ponderada pelo total / pelas resolvidas de cada uma;
- "Resolvidas mês a mês": soma mês a mês (no mês da virada as duas têm resolvidas, e são pendências diferentes).
Comparativos "vs mês anterior" ficam do LexPre; só com o legado no período, vêm do legado.

Como no dashboard Pendências (legado), a fila, a origem e o mês a mês vêm do histórico todo (chamada sem data).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from app.analyses import v1_dashboard_generico_la as copia_la
from app.analyses import v1_dashboard_generico_ng as copia_ng
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext
from app.dashboards.protocolo_lexpre_legado import _chave_mes, _dump, _kwargs_handler_legado
from app.database import SourceUnavailable

# Banco legado -> ref da unidade -> (cópia v1, rota, parâmetro de UF).
# NG e LARJ no banco ng; LAAM no laadv (mesma regra do dashboard Pendências legado).
LEGADO_PENDENCIAS = {
    "ng": {
        "NG": (copia_ng, "pendencias", "uf_pendencias"),
        "RJ": (copia_ng, "pendencias_RJ", "uf_pendencias"),
    },
    "laadv": {
        "LA": (copia_la, "pendencia_LA", "uf_pendencia_LA"),
    },
}

EXTRA_QUERIES = {
    "ng": ("setor_pendencias",),
    "laadv": ("setor_pendencia_LA",),
}

# Contagens que somam direto (período e fila).
_CONTAGENS = (
    "pendencias_total",
    "pendencias_resolvidas",
    "pendencias_canceladas",
    "pendencias_triagem",
    "pendencias_nao_resolvidas",
    "pendencias_nao_resolvidas_com_atraso",
    "pendencias_nao_resolvidas_reajuizamento",
    "pendencias_resolvidas_reajuizamento",
)
# Taxas (% do total do período) e tempos (das resolvidas): média ponderada.
_TAXAS = ("pendencias_taxa_resolvidos", "pendencias_taxa_nao_resolvidos", "pendencias_taxa_canceladas")
_TEMPOS = ("media_tempo_resolvidos_pendencia", "mediana_tempo_resolvidos_pendencia")
_COMPARATIVOS = (
    "comparativo_pendencias_resolvidas",
    "comparativo_tempo_medio_resolvidos_pendencia",
    "comparativo_mediana_tempo_resolvidos_pendencia",
)


def _num(d: dict[str, Any], campo: str) -> float | None:
    v = d.get(campo)
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def kpis_do_legado(
    stats_periodo: dict[str, Any], stats_hist: dict[str, Any], *, la: bool
) -> dict[str, Any]:
    """Stats do legado com os nomes do Pendências LexPre (a LA vem com sufixo _LA)."""
    suf = "_LA" if la else ""

    def periodo(campo: str) -> float | None:
        return _num(stats_periodo, campo + suf)

    def fila(campo: str) -> float | None:
        return _num(stats_hist, campo + suf)

    out: dict[str, Any] = {}
    for campo in ("pendencias_total", "pendencias_resolvidas", "pendencias_canceladas", "pendencias_triagem"):
        out[campo] = int(periodo(campo) or 0)
    for campo in ("pendencias_nao_resolvidas", "pendencias_nao_resolvidas_com_atraso"):
        out[campo] = int(fila(campo) or 0)
    for campo in (*_TAXAS, *_TEMPOS):
        out[campo] = periodo(campo) or 0.0
    if not la:
        # Reajuizamento e comparativos: só NG/RJ têm.
        for campo in ("pendencias_nao_resolvidas_reajuizamento", "pendencias_resolvidas_reajuizamento"):
            v = periodo(campo)
            if v is not None:
                out[campo] = int(v)
        out["comparativo_pendencias_resolvidas"] = periodo("comparativo_pendencias_resolvidas")
        out["comparativo_tempo_medio_resolvidos_pendencia"] = periodo(
            "comparativo_tempo_medio_pendencias_resolvidas"
        )
    return out


def _pontos(corpo: dict[str, Any], chave: str) -> list[dict[str, Any]]:
    saida: list[dict[str, Any]] = []
    for p in corpo.get(chave) or []:
        if isinstance(p, dict) and p.get("name") is not None and isinstance(p.get("value"), (int, float)):
            saida.append({"name": str(p["name"]), "value": int(p["value"])})
    return saida


def somar_por_mes(lexpre: list[dict[str, Any]], legado: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Soma as duas séries mês a mês (nome no formato do LexPre: 'nov 2026')."""
    por_mes: dict[str, dict[str, Any]] = {}
    for origem in (legado, lexpre):
        for p in origem or []:
            chave = _chave_mes(str(p.get("name") or ""))
            valor = p.get("value")
            if not chave or not isinstance(valor, (int, float)):
                continue
            atual = por_mes.setdefault(chave, {"name": str(p["name"]), "value": 0})
            atual["name"] = str(p["name"])
            atual["value"] += int(valor)
    return [por_mes[k] for k in sorted(por_mes)]


def somar_por_origem(lexpre: list[dict[str, Any]], legado: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Soma as origens das não resolvidas pelo nome; maior primeiro."""
    por_nome: dict[str, int] = {}
    for origem in (lexpre, legado):
        for p in origem or []:
            nome, valor = p.get("name"), p.get("value")
            if nome is None or not isinstance(valor, (int, float)):
                continue
            por_nome[str(nome)] = por_nome.get(str(nome), 0) + int(valor)
    return [{"name": n, "value": v} for n, v in sorted(por_nome.items(), key=lambda x: -x[1])]


async def buscar_pendencias_legado(ctx: DashboardContext) -> dict[str, Any] | None:
    """KPIs, origem e série mês a mês do legado; None se a fonte não estiver ligada ou fora do ar."""
    funcionario = ctx.filters.get("funcionario") or None
    area = ctx.filters.get("area_atuacao_id") or None
    # A casca entrega listas; uf_pendencias / uf_pendencia_LA na v1 são texto (uma UF).
    uf = next(iter(ctx.filters.get("uf") or []), None)

    for db, por_ref in LEGADO_PENDENCIAS.items():
        fonte = ctx.extra_sources.get(db)
        ref = ctx.extra_refs.get(db)
        if fonte is None or ref not in por_ref:
            continue
        copia, rota, param_uf = por_ref[ref]
        handler = copia.HANDLERS[rota]
        kwargs = _kwargs_handler_legado(
            handler,
            materia=None,
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
            periodo = _dump(await rodar(ctx.period.start, ctx.period.end))
            historico = _dump(await rodar(None, None))
        except SourceUnavailable:
            return None
        la = db == "laadv"
        suf = "_LA" if la else ""
        return {
            "kpis": kpis_do_legado(
                periodo.get("stats") or {}, historico.get("stats") or {}, la=la
            ),
            "por_origem": _pontos(historico, "pendencias_nao_resolvidas_por_origem" + suf),
            "por_mes": _pontos(historico, "pendencias_resolvidas_por_mes" + suf),
        }
    return None


def somar_kpis(lexpre: dict[str, Any], legado: dict[str, Any]) -> dict[str, Any]:
    """Stats do LexPre + legado (ver docstring do módulo)."""
    out = {**lexpre}
    for campo in _CONTAGENS:
        if campo in lexpre or campo in legado:
            out[campo] = int(lexpre.get(campo) or 0) + int(legado.get(campo) or 0)

    def ponderar(campo: str, peso: str) -> float:
        p_lex = float(lexpre.get(peso) or 0)
        p_leg = float(legado.get(peso) or 0)
        n = p_lex + p_leg
        if not n:
            return 0.0
        v = (float(lexpre.get(campo) or 0) * p_lex + float(legado.get(campo) or 0) * p_leg) / n
        return round(v, 2)

    for campo in _TAXAS:
        out[campo] = ponderar(campo, "pendencias_total")
    for campo in _TEMPOS:
        # Mediana: aproximação (mediana de cada fonte ponderada pelas resolvidas).
        out[campo] = ponderar(campo, "pendencias_resolvidas")

    if not lexpre.get("pendencias_total"):
        # Sem pendências no LexPre no período: o "vs mês anterior" é o do legado.
        for campo in _COMPARATIVOS:
            out[campo] = legado.get(campo)
    return out


def misturar_legado_no_corpo(corpo: dict[str, Any], legado: dict[str, Any]) -> str:
    """Soma o legado no corpo do Pendências LexPre. Devolve `fonte_indicadores`: 'lexpre' | 'legado' | 'misto'."""
    kpis = legado["kpis"]
    tem_legado = bool(
        kpis.get("pendencias_total") or kpis.get("pendencias_nao_resolvidas") or legado["por_mes"]
    )
    if not tem_legado:
        return "lexpre"
    stats = corpo.get("stats") or {}
    tem_lexpre = bool(stats.get("pendencias_total") or stats.get("pendencias_nao_resolvidas"))

    corpo["stats"] = somar_kpis(stats, kpis)
    corpo["pendencias_nao_resolvidas_por_origem"] = somar_por_origem(
        corpo.get("pendencias_nao_resolvidas_por_origem") or [], legado["por_origem"]
    )
    corpo["pendencias_resolvidas_por_mes"] = somar_por_mes(
        corpo.get("pendencias_resolvidas_por_mes") or [], legado["por_mes"]
    )
    return "misto" if tem_lexpre else "legado"
