"""Análise da planilha `financeiro_LA`, aba `REPASSES CLIENTES`.

Combina as estatísticas/metas trimestrais existentes com a análise
preditiva ("onde deveríamos estar hoje?") num único payload.

Backward-compatible: todos os campos que o frontend já consumia
continuam presentes e inalterados. A análise preditiva é entregue
como uma nova chave `predicao` dentro do retorno de
`get_financeiro_LA_faturamento_trimestral_meta`.

Funções públicas
----------------
get_repasses_clientes()
    Linhas brutas da aba.

get_financeiro_LA_stats(amostra)
    Estatísticas genéricas (total de linhas, colunas, amostra).

get_financeiro_LA_entradas_periodo(from_date, to_date)
    Contagem de entradas filtradas por DATA DO TED.

get_financeiro_LA_faturamento_trimestral_meta(year, compare_year, as_of)
    Payload principal — metas trimestrais + acumulado (existente)
    + bloco `predicao` (novo, nunca quebra campos anteriores).

get_financeiro_LA_expectativa_hoje(year, as_of)
    Versão compacta da predição (chatbots / alertas).
"""
from __future__ import annotations

import calendar
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from app.sheets import fetch_sheet

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SHEET_NAME = "financeiro_LA"
COLUMN_DATA_TED = "DATA DO TED"

_COL_HONO_CANDIDATES = ("HONO", "HONORARIOS", "HONORÁRIOS", "HONORARIO", "HONORÁRIO")
_COL_SUCUMB_CANDIDATES = ("SUCUMBÊNCIA", "SUCUMBENCIA")

META_DISTRIBUICAO_TRIMESTRAL: Dict[str, float] = {
    "1T": 0.1610,
    "2T": 0.2295,
    "3T": 0.2929,
    "4T": 0.3166,
}

META_VALORES_TOTAIS: Dict[str, Decimal] = {
    "TRISTE":   Decimal("5587319.30"),
    "BASE":     Decimal("7000000.00"),
    "AVANCADA": Decimal("9500000.00"),
    "SUPER":    Decimal("11000000.00"),
}

_QUARTER_MONTHS: Dict[str, Tuple[int, int]] = {
    "1T": (1, 3),
    "2T": (4, 6),
    "3T": (7, 9),
    "4T": (10, 12),
}

_DIAS_POR_MES_RITMO = 30
_DIAS_POR_SEMESTRE_RITMO = 180


# ---------------------------------------------------------------------------
# Helpers — parsing
# ---------------------------------------------------------------------------

def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    raw = str(value).strip()
    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        pass

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    return None


def _pick_first_existing_column(
    rows: List[Dict[str, Any]], candidates: Tuple[str, ...]
) -> Optional[str]:
    if not rows:
        return None
    keys = rows[0].keys()
    for c in candidates:
        if c in keys:
            return c
    normalized = {str(k).strip().upper(): k for k in keys}
    for c in candidates:
        k = normalized.get(str(c).strip().upper())
        if k is not None:
            return str(k)
    return None


def _parse_money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return Decimal("0")

    s = str(value).strip()
    if not s:
        return Decimal("0")

    s = s.replace("R$", "").replace("\u00a0", " ").strip()
    s = s.replace(".", "").replace(",", ".")
    cleaned = "".join(ch for ch in s if ch.isdigit() or ch in "+.-")
    if cleaned in ("", "+", "-", ".", "+.", "-."):
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _decimal_to_float_2(v: Decimal) -> float:
    return float(v.quantize(Decimal("0.01")))


# ---------------------------------------------------------------------------
# Helpers — calendário / trimestres
# ---------------------------------------------------------------------------

def _quarter_key(d: date) -> str:
    if d.month <= 3:
        return "1T"
    if d.month <= 6:
        return "2T"
    if d.month <= 9:
        return "3T"
    return "4T"


def _quarter_index(q: str) -> int:
    return {"1T": 1, "2T": 2, "3T": 3, "4T": 4}.get(q, 0)


def _quarters_up_to(q: str) -> List[str]:
    idx = _quarter_index(q)
    return [x for x in ("1T", "2T", "3T", "4T") if _quarter_index(x) <= idx]


def _quarter_date_range(year: int, quarter: str) -> Tuple[date, date]:
    m_start, m_end = _QUARTER_MONTHS[quarter]
    first = date(year, m_start, 1)
    last_day = calendar.monthrange(year, m_end)[1]
    return first, date(year, m_end, last_day)


def _progress_fraction_in_quarter(as_of: date) -> float:
    q = _quarter_key(as_of)
    first, last = _quarter_date_range(as_of.year, q)
    elapsed = (as_of - first).days + 1
    total = (last - first).days + 1
    return min(elapsed / total, 1.0)


def _ytd_calendar_fraction(year: int, as_of: date) -> float:
    jan1 = date(year, 1, 1)
    dec31 = date(year, 12, 31)
    total_days = (dec31 - jan1).days + 1
    elapsed = (min(as_of, dec31) - jan1).days + 1
    return min(elapsed / total_days, 1.0)


# ---------------------------------------------------------------------------
# Helpers — outros
# ---------------------------------------------------------------------------

def _current_quarter(as_of: date) -> str:
    return _quarter_key(as_of)


def _pct_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def _zeros_quarters_decimal() -> Dict[str, Decimal]:
    return {"1T": Decimal("0"), "2T": Decimal("0"), "3T": Decimal("0"), "4T": Decimal("0")}


def _zona_from_value(valor: float) -> str:
    for nome, threshold in [
        ("SUPER", float(META_VALORES_TOTAIS["SUPER"])),
        ("AVANCADA", float(META_VALORES_TOTAIS["AVANCADA"])),
        ("BASE", float(META_VALORES_TOTAIS["BASE"])),
        ("TRISTE", float(META_VALORES_TOTAIS["TRISTE"])),
    ]:
        if valor >= threshold:
            return nome
    return "ABAIXO_TRISTE"


def _fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------------------
# Funções de acesso à planilha
# ---------------------------------------------------------------------------

async def get_repasses_clientes() -> List[Dict[str, Any]]:
    """Retorna as linhas brutas da aba `REPASSES CLIENTES`."""
    return await fetch_sheet(SHEET_NAME)


async def get_financeiro_LA_stats(amostra: int = 5) -> Dict[str, Any]:
    """Estatísticas genéricas da aba `REPASSES CLIENTES`."""
    rows = await get_repasses_clientes()
    colunas: List[str] = list(rows[0].keys()) if rows else []
    return {
        "aba": "REPASSES CLIENTES",
        "total_linhas": len(rows),
        "colunas": colunas,
        "amostra": rows[:max(0, amostra)],
    }


async def get_financeiro_LA_entradas_periodo(
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Conta entradas no período filtrando por `DATA DO TED` (inclusive)."""
    rows = await get_repasses_clientes()

    if not from_date and not to_date:
        return len(rows)

    fd = from_date or date.min
    td = to_date or date.max

    count = 0
    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_TED))
        if d is None:
            continue
        if fd <= d <= td:
            count += 1

    return count


# ---------------------------------------------------------------------------
# Lógica preditiva
# ---------------------------------------------------------------------------

def _expectativa_super_meta_trimestre(
    meta_super: Decimal,
    *,
    as_of: date,
    quarter: str,
    year: int,
) -> Tuple[Decimal, float]:
    """Esperado até hoje = Super Meta do trimestre × (% de dias corridos no trimestre)."""
    q_first, q_last = _quarter_date_range(year, quarter)

    if as_of < q_first:
        return Decimal("0"), 0.0
    if as_of > q_last:
        frac = 1.0
    else:
        frac = _progress_fraction_in_quarter(as_of)

    expectativa = meta_super * Decimal(str(frac))
    return expectativa, round(frac * 100, 1)


def _expected_ytd_linear(
    meta_total: Decimal,
    as_of: date,
    metas_trim: Optional[Dict[str, Decimal]] = None,
) -> Decimal:
    """Expectativa YTD linear: trimestres passados a 100 %, trimestre atual
    proporcional ao dia do calendário."""
    q_atual = _quarter_key(as_of)
    quarters = ["1T", "2T", "3T", "4T"]
    idx_atual = quarters.index(q_atual)

    expected = Decimal("0")
    for i, q in enumerate(quarters):
        meta_q = (
            metas_trim.get(q, meta_total * Decimal(str(META_DISTRIBUICAO_TRIMESTRAL[q])))
            if metas_trim
            else meta_total * Decimal(str(META_DISTRIBUICAO_TRIMESTRAL[q]))
        )
        if i < idx_atual:
            expected += meta_q
        elif i == idx_atual:
            frac = Decimal(str(_progress_fraction_in_quarter(as_of)))
            expected += meta_q * frac
    return expected


def _build_predicao_block(
    *,
    as_of: date,
    year: int,
    faturamento: Dict[int, Dict[str, Decimal]],
    fat_ytd: Dict[int, Decimal],
    rows: List[Dict[str, Any]],
    col_hono: Optional[str],
    col_suc: Optional[str],
    metas_trim_por_zona: Dict[str, Dict[str, Decimal]],
) -> Dict[str, Any]:
    """Calcula e retorna o bloco `predicao` embutido no payload principal.

    Âncora de meta: SUPER (objetivo trimestral de referência).
    """
    META_NIVEL = "SUPER"
    meta_total = META_VALORES_TOTAIS[META_NIVEL]

    metas_trim_base: Dict[str, Decimal] = {}
    for q in ("1T", "2T", "3T", "4T"):
        val = Decimal(str(metas_trim_por_zona.get(META_NIVEL, {}).get(q, 0) or 0))
        metas_trim_base[q] = val if val > 0 else meta_total * Decimal(str(META_DISTRIBUICAO_TRIMESTRAL[q]))

    q_atual           = _quarter_key(as_of)
    meta_q_atual      = metas_trim_base[q_atual]
    realizado_q_atual = faturamento[year][q_atual]
    expectativa_trim, frac_dias_pct = _expectativa_super_meta_trimestre(
        meta_q_atual, as_of=as_of, quarter=q_atual, year=year,
    )
    gap_trim    = realizado_q_atual - expectativa_trim
    gap_pct     = _pct_change(float(realizado_q_atual), float(expectativa_trim))

    TOLERANCIA = 2.0
    if gap_pct is None:
        status = "sem_dados"
    elif gap_pct >= TOLERANCIA:
        status = "acima"
    elif gap_pct >= -TOLERANCIA:
        status = "no_ritmo"
    else:
        status = "abaixo"

    gap_f    = float(gap_trim.quantize(Decimal("0.01")))
    data_str = as_of.strftime("%d/%m/%Y")
    if status == "acima":
        mensagem = (
            f"✅ Em {data_str} ({q_atual}), o trimestre está {_fmt_brl(abs(gap_f))} "
            f"acima do esperado até hoje (Super Meta × {frac_dias_pct:.1f}% dos dias)."
        )
    elif status == "no_ritmo":
        mensagem = (
            f"🟡 Em {data_str} ({q_atual}), o trimestre está no ritmo esperado "
            f"(diferença de {_fmt_brl(abs(gap_f))})."
        )
    elif status == "abaixo":
        mensagem = (
            f"🔴 Em {data_str} ({q_atual}), o trimestre está {_fmt_brl(abs(gap_f))} "
            f"abaixo do esperado até hoje (Super Meta × {frac_dias_pct:.1f}% dos dias)."
        )
    else:
        mensagem = "Sem dados suficientes para análise."

    expectativa_ytd = _expected_ytd_linear(meta_total, as_of, metas_trim_base)
    realizado_ytd   = fat_ytd[year]
    gap_ytd         = realizado_ytd - expectativa_ytd
    gap_ytd_pct     = _pct_change(float(realizado_ytd), float(expectativa_ytd))

    ytd_frac = _ytd_calendar_fraction(year, as_of)
    projecao_fim_ano = (
        realizado_ytd / Decimal(str(ytd_frac)) if ytd_frac > 0 else Decimal("0")
    )

    falta_trimestre   = max(meta_q_atual - realizado_q_atual, Decimal("0"))

    _, last_q        = _quarter_date_range(year, q_atual)
    dias_restantes   = (last_q - as_of).days
    ritmo_necessario = (
        falta_trimestre / Decimal(str(dias_restantes))
        if dias_restantes > 0
        else Decimal("0")
    )

    cutoff_30d = as_of - timedelta(days=30)
    soma_30d   = Decimal("0")
    for r in rows:
        d_row = _parse_date(r.get(COLUMN_DATA_TED))
        if d_row is None or d_row.year != year:
            continue
        if cutoff_30d < d_row <= as_of:
            hono = _parse_money(r.get(col_hono)) if col_hono else Decimal("0")
            suc  = _parse_money(r.get(col_suc))  if col_suc  else Decimal("0")
            soma_30d += hono + suc

    ritmo_atual_diario = soma_30d / Decimal("30")

    falta_ano          = max(meta_total - realizado_ytd, Decimal("0"))
    dec31              = date(year, 12, 31)
    dias_restantes_ano = max((dec31 - as_of).days, 0)
    ritmo_necessario_ano = (
        falta_ano / Decimal(str(dias_restantes_ano))
        if dias_restantes_ano > 0
        else Decimal("0")
    )
    if meta_total > 0:
        atingido_ano_pct = round(min(100.0, float(realizado_ytd / meta_total * 100)), 1)
    else:
        atingido_ano_pct = 0.0
    distancia_ano_pct = round(max(0.0, 100.0 - atingido_ano_pct), 1)

    por_trimestre = []
    for q in ("1T", "2T", "3T", "4T"):
        q_first, q_last = _quarter_date_range(year, q)

        if as_of < q_first:
            q_status = "futuro"
        elif as_of > q_last:
            q_status = "concluido"
        else:
            q_status = "em_curso"

        meta_q = metas_trim_base[q]

        expect_parcial, frac_decorrida = _expectativa_super_meta_trimestre(
            meta_q, as_of=as_of, quarter=q, year=year,
        )
        if q_status == "concluido":
            expect_parcial = meta_q
            frac_decorrida = 100.0

        real_q = faturamento[year][q]
        gap_q  = real_q - expect_parcial
        falta_meta = max(meta_q - real_q, Decimal("0"))
        if meta_q > 0:
            atingido_pct = round(min(100.0, float(real_q / meta_q * 100)), 1)
        else:
            atingido_pct = 0.0
        distancia_pct = round(max(0.0, 100.0 - atingido_pct), 1)

        por_trimestre.append({
            "trimestre":            q,
            "status":               q_status,
            "meta":                 _decimal_to_float_2(meta_q),
            "expectativa_ate_hoje": _decimal_to_float_2(expect_parcial),
            "realizado":            _decimal_to_float_2(real_q),
            "gap":                  _decimal_to_float_2(gap_q),
            "gap_pct":              _pct_change(float(real_q), float(expect_parcial)),
            "frac_decorrida_pct":   frac_decorrida,
            "falta":                _decimal_to_float_2(falta_meta),
            "atingido_pct":         atingido_pct,
            "distancia_pct":        distancia_pct,
            "meta_atingida":        real_q >= meta_q,
        })

    return {
        "meta_nivel_usado":   META_NIVEL,
        "frac_trimestre_pct": round(_progress_fraction_in_quarter(as_of) * 100, 1),
        "frac_ano_pct":       round(_ytd_calendar_fraction(year, as_of) * 100, 1),

        "expectativa_hoje": {
            "meta_super_trimestre":    _decimal_to_float_2(meta_q_atual),
            "frac_dias_trimestre_pct": frac_dias_pct,
            "expectativa":             _decimal_to_float_2(expectativa_trim),
            "realizado":               _decimal_to_float_2(realizado_q_atual),
            "gap":                     _decimal_to_float_2(gap_trim),
            "gap_pct":                 gap_pct,
            "status":                  status,
            "mensagem":                mensagem,
        },

        "expectativa_ytd": {
            "expectativa": _decimal_to_float_2(expectativa_ytd),
            "realizado":   _decimal_to_float_2(realizado_ytd),
            "gap":         _decimal_to_float_2(gap_ytd),
            "gap_pct":     gap_ytd_pct,
        },

        "projecao_fim_ano": {
            "valor_projetado":  _decimal_to_float_2(projecao_fim_ano),
            "meta_referencia":  _decimal_to_float_2(meta_total),
            "zona_projetada":   _zona_from_value(float(projecao_fim_ano)),
            "excede_meta_pct":  _pct_change(float(projecao_fim_ano), float(meta_total)),
        },

        "ritmo_diario": {
            "dias_restantes":     dias_restantes,
            "falta_no_trimestre": _decimal_to_float_2(falta_trimestre),
            "necessario_por_dia": _decimal_to_float_2(ritmo_necessario),
            "atual_por_dia_30d":  _decimal_to_float_2(ritmo_atual_diario),
            "diferenca_diaria":   _decimal_to_float_2(ritmo_necessario - ritmo_atual_diario),
        },

        "super_meta_anual": {
            "meta":            _decimal_to_float_2(meta_total),
            "realizado_ytd":   _decimal_to_float_2(realizado_ytd),
            "expectativa_ytd": _decimal_to_float_2(expectativa_ytd),
            "gap_ytd":         _decimal_to_float_2(gap_ytd),
            "gap_ytd_pct":     gap_ytd_pct,
            "falta":           _decimal_to_float_2(falta_ano),
            "atingido_pct":    atingido_ano_pct,
            "distancia_pct":   distancia_ano_pct,
            "frac_ano_pct":    round(_ytd_calendar_fraction(year, as_of) * 100, 1),
            "meta_atingida":   realizado_ytd >= meta_total,
        },

        "ritmo_diario_anual": {
            "dias_restantes":          dias_restantes_ano,
            "falta_no_ano":            _decimal_to_float_2(falta_ano),
            "necessario_por_dia":      _decimal_to_float_2(ritmo_necessario_ano),
            "necessario_por_mes":      _decimal_to_float_2(
                ritmo_necessario_ano * Decimal(str(_DIAS_POR_MES_RITMO))
            ),
            "necessario_por_semestre": _decimal_to_float_2(
                ritmo_necessario_ano * Decimal(str(_DIAS_POR_SEMESTRE_RITMO))
            ),
            "atual_por_dia_30d":       _decimal_to_float_2(ritmo_atual_diario),
            "atual_por_mes_30d":       _decimal_to_float_2(
                ritmo_atual_diario * Decimal(str(_DIAS_POR_MES_RITMO))
            ),
            "atual_por_semestre_30d":  _decimal_to_float_2(
                ritmo_atual_diario * Decimal(str(_DIAS_POR_SEMESTRE_RITMO))
            ),
            "diferenca_diaria":        _decimal_to_float_2(
                ritmo_necessario_ano - ritmo_atual_diario
            ),
        },

        "por_trimestre": por_trimestre,
    }


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

async def get_financeiro_LA_faturamento_trimestral_meta(
    *,
    year: int,
    compare_year: Optional[int] = None,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """Payload principal para a tela de meta anual (LA).

    Mantém compatibilidade com o contrato anterior e adiciona `predicao`.
    """
    rows = await get_repasses_clientes()
    compare_year = compare_year if compare_year is not None else (year - 1)
    as_of = as_of or date.today()

    col_hono = _pick_first_existing_column(rows, _COL_HONO_CANDIDATES)
    col_suc = _pick_first_existing_column(rows, _COL_SUCUMB_CANDIDATES)

    faturamento: Dict[int, Dict[str, Decimal]] = {
        year: _zeros_quarters_decimal(),
        compare_year: _zeros_quarters_decimal(),
    }
    total: Dict[int, Decimal] = {year: Decimal("0"), compare_year: Decimal("0")}
    fat_ytd: Dict[int, Decimal] = {year: Decimal("0"), compare_year: Decimal("0")}
    faturamento_mensal: Dict[int, Decimal] = {m: Decimal("0") for m in range(1, 13)}

    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_TED))
        if d is None or d.year not in (year, compare_year):
            continue

        hono = _parse_money(row.get(col_hono)) if col_hono else Decimal("0")
        suc = _parse_money(row.get(col_suc)) if col_suc else Decimal("0")
        val = hono + suc
        if val == 0:
            continue

        q = _quarter_key(d)
        faturamento[d.year][q] += val
        total[d.year] += val
        if d.year == year:
            faturamento_mensal[d.month] += val

        cutoff = as_of if d.year == year else as_of.replace(year=compare_year)
        if d <= cutoff:
            fat_ytd[d.year] += val

    metas_por_trimestre: Dict[str, Dict[str, Any]] = {}
    _metas_trim_decimal: Dict[str, Dict[str, Decimal]] = {}

    for nome, total_meta in META_VALORES_TOTAIS.items():
        q_values: Dict[str, Decimal] = {
            q: total_meta * Decimal(str(pct))
            for q, pct in META_DISTRIBUICAO_TRIMESTRAL.items()
        }
        _metas_trim_decimal[nome] = q_values
        metas_por_trimestre[nome] = {
            "1T": _decimal_to_float_2(q_values["1T"]),
            "2T": _decimal_to_float_2(q_values["2T"]),
            "3T": _decimal_to_float_2(q_values["3T"]),
            "4T": _decimal_to_float_2(q_values["4T"]),
            "TOTAL": _decimal_to_float_2(total_meta),
        }

    atingido_year: Dict[str, float] = {
        "1T": _decimal_to_float_2(faturamento[year]["1T"]),
        "2T": _decimal_to_float_2(faturamento[year]["2T"]),
        "3T": _decimal_to_float_2(faturamento[year]["3T"]),
        "4T": _decimal_to_float_2(faturamento[year]["4T"]),
        "TOTAL": _decimal_to_float_2(total[year]),
    }
    atingido_compare: Dict[str, float] = {
        "1T": _decimal_to_float_2(faturamento[compare_year]["1T"]),
        "2T": _decimal_to_float_2(faturamento[compare_year]["2T"]),
        "3T": _decimal_to_float_2(faturamento[compare_year]["3T"]),
        "4T": _decimal_to_float_2(faturamento[compare_year]["4T"]),
        "TOTAL": _decimal_to_float_2(total[compare_year]),
    }

    q_atual = _current_quarter(as_of)
    quarters_ytd = _quarters_up_to(q_atual)
    # `fat_ytd` já respeita o corte por `as_of` (DATA DO TED <= as_of); usar os
    # totais de trimestre inteiro aqui inflaria o acumulado com lançamentos
    # futuros dentro do trimestre em curso.
    ytd_atual = _decimal_to_float_2(fat_ytd[year])
    ytd_compare = _decimal_to_float_2(fat_ytd[compare_year])

    ytd_pct = float(sum(META_DISTRIBUICAO_TRIMESTRAL[q] for q in quarters_ytd))
    metas_ytd = {
        nome: float((total_meta * Decimal(str(ytd_pct))).quantize(Decimal("0.01")))
        for nome, total_meta in META_VALORES_TOTAIS.items()
    }

    ordem = ["TRISTE", "BASE", "AVANCADA", "SUPER"]
    zona = "TRISTE"
    for lvl in ordem:
        if ytd_atual >= float(metas_ytd[lvl]):
            zona = lvl

    zona_idx = ordem.index(zona)
    proximo = ordem[zona_idx + 1] if zona_idx + 1 < len(ordem) else None
    falta_prox = max((float(metas_ytd[proximo]) - ytd_atual) if proximo else 0.0, 0.0)

    cards = []
    idx_atual = _quarter_index(q_atual)
    for q in ("1T", "2T", "3T", "4T"):
        idx = _quarter_index(q)
        if idx < idx_atual:
            status = "concluido"
        elif idx == idx_atual:
            status = "em_curso"
        else:
            status = "a_iniciar"

        atual_q = float(atingido_year[q])
        comp_q = float(atingido_compare[q])
        m_start, m_end = _QUARTER_MONTHS[q]
        atingido_mensal = {
            str(m): _decimal_to_float_2(faturamento_mensal[m])
            for m in range(m_start, m_end + 1)
        }
        cards.append({
            "trimestre": q,
            "status": status,
            "atingido": atual_q,
            "atingido_compare": comp_q,
            "variacao_pct_vs_compare": _pct_change(atual_q, comp_q),
            "meta_triste": float(metas_por_trimestre["TRISTE"][q]),
            "meta_base": float(metas_por_trimestre["BASE"][q]),
            "meta_avancada": float(metas_por_trimestre["AVANCADA"][q]),
            "meta_super": float(metas_por_trimestre["SUPER"][q]),
            "atingido_mensal": atingido_mensal,
        })

    predicao = _build_predicao_block(
        as_of=as_of,
        year=year,
        faturamento=faturamento,
        fat_ytd=fat_ytd,
        rows=rows,
        col_hono=col_hono,
        col_suc=col_suc,
        metas_trim_por_zona=_metas_trim_decimal,
    )

    return {
        "coluna_data": COLUMN_DATA_TED,
        "coluna_hono": col_hono,
        "coluna_sucumbencia": col_suc,
        "year": year,
        "compare_year": compare_year,
        "as_of": as_of.isoformat(),
        "trimestre_atual": q_atual,
        "distribuicao_trimestral_pct": META_DISTRIBUICAO_TRIMESTRAL,
        "metas": metas_por_trimestre,
        "atingido": {
            str(year): atingido_year,
            str(compare_year): atingido_compare,
        },
        "ytd": {
            "quarters": quarters_ytd,
            "atingido": float(Decimal(str(ytd_atual)).quantize(Decimal("0.01"))),
            "atingido_compare": float(Decimal(str(ytd_compare)).quantize(Decimal("0.01"))),
            "variacao_pct_vs_compare": _pct_change(ytd_atual, ytd_compare),
            "metas": {k: float(v) for k, v in metas_ytd.items()},
            "zona": zona,
            "proxima_zona": proximo,
            "falta_para_proxima_zona": float(Decimal(str(falta_prox)).quantize(Decimal("0.01"))),
        },
        "cards_trimestre": cards,
        "predicao": predicao,
    }


async def get_financeiro_LA_expectativa_hoje(
    *,
    year: int,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """Retorna apenas o núcleo preditivo, sem dados de metas completos."""
    payload = await get_financeiro_LA_faturamento_trimestral_meta(year=year, as_of=as_of)
    pred = payload["predicao"]
    return {
        "as_of": payload["as_of"],
        "trimestre_atual": payload["trimestre_atual"],
        "frac_trimestre_pct": pred["frac_trimestre_pct"],
        "frac_ano_pct": pred["frac_ano_pct"],
        **pred["expectativa_hoje"],
    }
