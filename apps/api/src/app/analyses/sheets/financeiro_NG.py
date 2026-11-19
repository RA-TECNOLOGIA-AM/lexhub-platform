"""Análise da planilha `financeiro_NG`, aba `REPASSES CLIENTES`.

Combina as estatísticas/metas trimestrais existentes com a análise
preditiva ("onde deveríamos estar hoje?") num único payload.

Backward-compatible: todos os campos que o frontend já consumia
continuam presentes e inalterados. A análise preditiva é entregue
como uma nova chave `predicao` dentro do retorno de
`get_financeiro_NG_faturamento_trimestral_meta`.

Funções públicas
----------------
get_repasses_clientes()
    Linhas brutas da aba.

get_financeiro_NG_stats(amostra)
    Estatísticas genéricas (total de linhas, colunas, amostra).

get_financeiro_NG_entradas_periodo(from_date, to_date)
    Contagem de entradas filtradas por DATA DO TED.

get_financeiro_NG_faturamento_trimestral_meta(year, compare_year, as_of)
    Payload principal — metas trimestrais + acumulado (existente)
    + bloco `predicao` (novo, nunca quebra campos anteriores).

get_financeiro_NG_expectativa_hoje(year, as_of)
    Versão compacta da predição (chatbots / alertas).

get_financeiro_NG_reflexo_financeiro(from_date, to_date)
    Section "Reflexo Financeiro" do dashboard Financeiro (cards + comparativo
    com o mesmo recorte do mês anterior).

get_financeiro_NG_conversao(anos_ajuizamento, anos_financeiro)
    Section "Conversão": receita filtrada por ano de ajuizamento × ano do TED.

get_financeiro_NG_previsao(ajuizado_por_ano)
    Section "Previsão": 4 cenários explicáveis de receita para o próximo ano.
"""
from __future__ import annotations

import calendar
import logging
import math
import re
import statistics
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from app.sheets import fetch_sheet
from app.utils import resolver_periodo_comparativo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SHEET_NAME = "financeiro_NG"
COLUMN_DATA_TED = "DATA DO TED"

_COL_HONO_CANDIDATES = ("HONO", "HONORARIOS", "HONORÁRIOS", "HONORARIO", "HONORÁRIO")
_COL_SUCUMB_CANDIDATES = ("SUCUMBÊNCIA", "SUCUMBENCIA")
_COL_HONO_SUCUMB_CANDIDATES = ("HONO + SUCUMBÊNCIA", "HONO + SUCUMBENCIA")
COLUMN_DATA_AJUIZAMENTO = "DATA AJUIZAMENTO"
COLUMN_REPASSE_CLIENTE = "REPASSE DE CLIENTE"
COLUMN_STATUS = "STATUS"
COLUMN_VALOR_CAUSA = "VALOR DA CAUSA"
COLUMN_ORIGEM = "ORIGEM"

COLUMN_MATERIA = "MATÉRIA"

# Pizza "Receita x Matérias": as N maiores matérias por receita; o resto vira "Outros".
PIZZA_MATERIAS_TOP_N = 8

# Fatias da pizza de origem (MULTA e ORIGEM vazia ficam de fora).
ORIGENS_PIZZA: Tuple[Tuple[str, str], ...] = (
    ("CONDENAÇÃO", "Condenação"),
    ("ACORDO", "Acordo"),
)

# Repasse ainda não pago ao cliente — mesma lista da medida NAO_PAGOS_CLIENTES_VALOR
# do Power BI (PAGAMENTO AGENDADO e STATUS vazio ficam de fora, como lá).
STATUS_CLIENTE_PENDENTE = frozenset({
    "AGUARDANDO PAGAMENTO",
    "AGUARDANDO RETORNO DO CLIENTE",
    "DESCONHECIDO",
    "SEM CONTATO",
    "SEM CONTRATO",
})

# Conversão dias -> meses da mediana de tempo (mês médio do calendário gregoriano).
_DIAS_POR_MES_MEDIO = 30.4375

META_DISTRIBUICAO_TRIMESTRAL: Dict[str, float] = {
    "1T": 0.1610,
    "2T": 0.2295,
    "3T": 0.2929,
    "4T": 0.3166,
}

META_VALORES_TOTAIS: Dict[str, Decimal] = {
    "TRISTE":   Decimal("3502020.14"),
    "BASE":     Decimal("4400000.00"),
    "AVANCADA": Decimal("6000000.00"),
    "SUPER":    Decimal("6900000.00"),
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


_RE_DECIMAL_COM_PONTO = re.compile(r"^-?\d+\.\d{1,2}$")


def _parse_money_flex(value: Any) -> Decimal:
    """Como `_parse_money`, mas aceita também texto com PONTO decimal ("15315.52").

    A coluna `VALOR DA CAUSA` mistura número, "R$ 15.828,52" (BR) e "15315.52"
    (ponto decimal) — `_parse_money` leria o último como 1.531.552.
    """
    if isinstance(value, str):
        s = value.replace("R$", "").replace("\u00a0", " ").strip()
        if "," not in s and _RE_DECIMAL_COM_PONTO.match(s):
            try:
                return Decimal(s)
            except InvalidOperation:
                return Decimal("0")
    return _parse_money(value)


def _normalizar_texto(value: Any) -> str:
    """Caixa alta, sem acento e com espaço/hífen virando "_" (ex.: "Condenação" -> "CONDENACAO")."""
    s = str(value or "").strip().upper()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[\s\-]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")


ANO_AJUIZAMENTO_SEM_DATA = "Sem data"


def _ano_ajuizamento_label(row: Dict[str, Any]) -> str:
    d = _parse_date(row.get(COLUMN_DATA_AJUIZAMENTO))
    return str(d.year) if d else ANO_AJUIZAMENTO_SEM_DATA


def _filtrar_rows_reflexo(
    rows: List[Dict[str, Any]],
    *,
    origens: Optional[List[str]] = None,
    materias: Optional[List[str]] = None,
    anos_ajuizamento: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Filtros clicáveis da página (pizzas de Origem, Matéria e Ano de Ajuizamento).

    Comparação normalizada (sem acento/caixa), então o rótulo exibido no gráfico
    ("Condenação", "ESPECIFICA", "2025", "Sem data") pode ser enviado direto.
    Valores dentro do mesmo filtro são OR; filtros diferentes são AND.
    """
    alvo_origens  = {_normalizar_texto(o) for o in (origens or []) if str(o).strip()}
    alvo_materias = {_normalizar_texto(m) for m in (materias or []) if str(m).strip()}
    alvo_anos     = {_normalizar_texto(a) for a in (anos_ajuizamento or []) if str(a).strip()}
    if not (alvo_origens or alvo_materias or alvo_anos):
        return rows

    filtradas = []
    for row in rows:
        if alvo_origens and _normalizar_texto(row.get(COLUMN_ORIGEM)) not in alvo_origens:
            continue
        if alvo_materias and _normalizar_texto(_normalizar_materia(row.get(COLUMN_MATERIA))) not in alvo_materias:
            continue
        if alvo_anos and _normalizar_texto(_ano_ajuizamento_label(row)) not in alvo_anos:
            continue
        filtradas.append(row)
    return filtradas


def _filtros_opcoes(rows: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Valores disponíveis para o diálogo de filtros (planilha inteira, sem filtro)."""
    materias = sorted({_normalizar_materia(r.get(COLUMN_MATERIA)) for r in rows})
    anos = sorted(
        {_ano_ajuizamento_label(r) for r in rows},
        key=lambda a: (a == ANO_AJUIZAMENTO_SEM_DATA, a),
    )
    return {
        "origens":          [rotulo for _, rotulo in ORIGENS_PIZZA],
        "materias":         materias,
        "anos_ajuizamento": anos,
    }


def _normalizar_materia(value: Any) -> str:
    """Unifica grafias mecânicas da coluna MATÉRIA (acento, espaço, hífen).

    Ex.: "ESPECÍFICA" -> "ESPECIFICA", "COI - BOLETO" -> "COI_BOLETO",
    "SAQUE TERMINAL" -> "SAQUE_TERMINAL". Sinônimos de fato (TIT_CAP x
    "TÍTULO DE CAPTALIZAÇÃO") continuam separados — isso é correção de planilha.
    Vazio ou numérico (ex.: 0.0) vira "SEM MATÉRIA".
    """
    if value is None or isinstance(value, (int, float, Decimal)):
        return "SEM MATÉRIA"
    s = str(value).strip().upper()
    if not s:
        return "SEM MATÉRIA"
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _decimal_to_float_2(v: Decimal) -> float:
    return float(v.quantize(Decimal("0.01")))


# ---------------------------------------------------------------------------
# Helpers — calendário / trimestres
# ---------------------------------------------------------------------------

def _quarter_key(d: date) -> str:
    if d.month <= 3:  return "1T"
    if d.month <= 6:  return "2T"
    if d.month <= 9:  return "3T"
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
    total   = (last - first).days + 1
    return min(elapsed / total, 1.0)


def _ytd_calendar_fraction(year: int, as_of: date) -> float:
    jan1  = date(year, 1, 1)
    dec31 = date(year, 12, 31)
    total_days = (dec31 - jan1).days + 1
    elapsed    = (min(as_of, dec31) - jan1).days + 1
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
        ("SUPER",    float(META_VALORES_TOTAIS["SUPER"])),
        ("AVANCADA", float(META_VALORES_TOTAIS["AVANCADA"])),
        ("BASE",     float(META_VALORES_TOTAIS["BASE"])),
        ("TRISTE",   float(META_VALORES_TOTAIS["TRISTE"])),
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


async def get_financeiro_NG_stats(amostra: int = 5) -> Dict[str, Any]:
    """Estatísticas genéricas da aba `REPASSES CLIENTES`."""
    rows = await get_repasses_clientes()
    colunas: List[str] = list(rows[0].keys()) if rows else []
    return {
        "aba": "REPASSES CLIENTES",
        "total_linhas": len(rows),
        "colunas": colunas,
        "amostra": rows[:max(0, amostra)],
    }


async def get_financeiro_NG_entradas_periodo(
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
    q_atual   = _quarter_key(as_of)
    quarters  = ["1T", "2T", "3T", "4T"]
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

    Campos
    ------
    meta_nivel_usado        : "SUPER"
    frac_trimestre_pct      : % do trimestre corrente já decorrido
    frac_ano_pct            : % do ano já decorrido

    expectativa_hoje
        meta_super_trimestre  Super Meta do trimestre corrente
        frac_dias_trimestre_pct  % de dias corridos no trimestre
        expectativa         Super Meta × frac_dias (esperado até hoje)
        realizado           faturamento do trimestre corrente
        gap                 realizado − expectativa
        gap_pct             gap / expectativa × 100
        status              "acima" | "no_ritmo" | "abaixo" | "sem_dados"
        mensagem            texto PT-BR pronto para UI

    expectativa_ytd         pro-rata YTD (trimestres passados 100 % + atual proporcional)

    projecao_fim_ano
        valor_projetado     ritmo atual extrapolado até 31/dez
        zona_projetada      zona de meta que o projetado atinge
        excede_meta_pct     % vs. Super Meta anual

    ritmo_diario
        dias_restantes      dias restantes no trimestre (a partir de amanhã)
        falta_no_trimestre  quanto falta para bater a Super Meta do trim. atual
        necessario_por_dia  falta ÷ dias_restantes
        atual_por_dia_30d   média dos últimos 30 dias
        diferenca_diaria    necessario − atual  (positivo = ritmo insuficiente)

    por_trimestre           list[dict] com progresso vs. Super Meta trimestral
    """
    META_NIVEL = "SUPER"
    meta_total = META_VALORES_TOTAIS[META_NIVEL]

    # Metas trimestrais BASE (fallback para distribuição percentual se zero)
    metas_trim_base: Dict[str, Decimal] = {}
    for q in ("1T", "2T", "3T", "4T"):
        val = Decimal(str(metas_trim_por_zona.get(META_NIVEL, {}).get(q, 0) or 0))
        metas_trim_base[q] = val if val > 0 else meta_total * Decimal(str(META_DISTRIBUICAO_TRIMESTRAL[q]))

    # ------------------------------------------------------------------
    # 1. Esperado até hoje (trimestre corrente)
    #    expectativa = Super Meta do trimestre × % dias corridos
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 2. Projeção fim do ano
    # ------------------------------------------------------------------
    ytd_frac = _ytd_calendar_fraction(year, as_of)
    projecao_fim_ano = (
        realizado_ytd / Decimal(str(ytd_frac)) if ytd_frac > 0 else Decimal("0")
    )

    # ------------------------------------------------------------------
    # 3. Ritmo diário
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 3b. Ritmo diário — Super Meta anual
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 4. Detalhes por trimestre
    # ------------------------------------------------------------------
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

async def get_financeiro_NG_faturamento_trimestral_meta(
    *,
    year: int,
    compare_year: Optional[int] = None,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """Payload principal para a tela de meta anual (NG).

    Mantém 100 % de compatibilidade com o contrato anterior e adiciona
    a chave `predicao` com a análise preditiva.
    """
    rows = await get_repasses_clientes()
    compare_year = compare_year if compare_year is not None else (year - 1)
    as_of        = as_of or date.today()

    col_hono = _pick_first_existing_column(rows, _COL_HONO_CANDIDATES)
    col_suc  = _pick_first_existing_column(rows, _COL_SUCUMB_CANDIDATES)

    # -----------------------------------------------------------------------
    # Agregação: faturamento trimestral + YTD (planilha lida uma única vez)
    # -----------------------------------------------------------------------
    faturamento: Dict[int, Dict[str, Decimal]] = {
        year:         _zeros_quarters_decimal(),
        compare_year: _zeros_quarters_decimal(),
    }
    total: Dict[int, Decimal]    = {year: Decimal("0"), compare_year: Decimal("0")}
    fat_ytd: Dict[int, Decimal]  = {year: Decimal("0"), compare_year: Decimal("0")}
    faturamento_mensal: Dict[int, Decimal] = {m: Decimal("0") for m in range(1, 13)}

    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_TED))
        if d is None or d.year not in (year, compare_year):
            continue

        hono = _parse_money(row.get(col_hono)) if col_hono else Decimal("0")
        suc  = _parse_money(row.get(col_suc))  if col_suc  else Decimal("0")
        val  = hono + suc
        if val == 0:
            continue

        q = _quarter_key(d)
        faturamento[d.year][q] += val
        total[d.year]          += val
        if d.year == year:
            faturamento_mensal[d.month] += val

        cutoff = as_of if d.year == year else as_of.replace(year=compare_year)
        if d <= cutoff:
            fat_ytd[d.year] += val

    # -----------------------------------------------------------------------
    # Metas por trimestre
    # -----------------------------------------------------------------------
    metas_por_trimestre: Dict[str, Dict[str, Any]] = {}
    _metas_trim_decimal: Dict[str, Dict[str, Decimal]] = {}

    for nome, total_meta in META_VALORES_TOTAIS.items():
        q_values: Dict[str, Decimal] = {
            q: total_meta * Decimal(str(pct))
            for q, pct in META_DISTRIBUICAO_TRIMESTRAL.items()
        }
        _metas_trim_decimal[nome] = q_values
        metas_por_trimestre[nome] = {
            "1T":    _decimal_to_float_2(q_values["1T"]),
            "2T":    _decimal_to_float_2(q_values["2T"]),
            "3T":    _decimal_to_float_2(q_values["3T"]),
            "4T":    _decimal_to_float_2(q_values["4T"]),
            "TOTAL": _decimal_to_float_2(total_meta),
        }

    # -----------------------------------------------------------------------
    # Atingido por trimestre
    # -----------------------------------------------------------------------
    atingido_year: Dict[str, float] = {
        "1T":    _decimal_to_float_2(faturamento[year]["1T"]),
        "2T":    _decimal_to_float_2(faturamento[year]["2T"]),
        "3T":    _decimal_to_float_2(faturamento[year]["3T"]),
        "4T":    _decimal_to_float_2(faturamento[year]["4T"]),
        "TOTAL": _decimal_to_float_2(total[year]),
    }
    atingido_compare: Dict[str, float] = {
        "1T":    _decimal_to_float_2(faturamento[compare_year]["1T"]),
        "2T":    _decimal_to_float_2(faturamento[compare_year]["2T"]),
        "3T":    _decimal_to_float_2(faturamento[compare_year]["3T"]),
        "4T":    _decimal_to_float_2(faturamento[compare_year]["4T"]),
        "TOTAL": _decimal_to_float_2(total[compare_year]),
    }

    # -----------------------------------------------------------------------
    # YTD e zona atual
    # -----------------------------------------------------------------------
    q_atual      = _current_quarter(as_of)
    quarters_ytd = _quarters_up_to(q_atual)
    # `fat_ytd` já respeita o corte por `as_of` (DATA DO TED <= as_of); usar os
    # totais de trimestre inteiro aqui inflaria o acumulado com lançamentos
    # futuros dentro do trimestre em curso.
    ytd_atual    = _decimal_to_float_2(fat_ytd[year])
    ytd_compare  = _decimal_to_float_2(fat_ytd[compare_year])

    # Régua anual / zona: usa os totais anuais (META_VALORES_TOTAIS), não a
    # fração YTD do ano — o marcador é o acumulado realizado vs meta do ano.
    metas_anuais = {
        nome: float(total_meta.quantize(Decimal("0.01")))
        for nome, total_meta in META_VALORES_TOTAIS.items()
    }

    ordem = ["TRISTE", "BASE", "AVANCADA", "SUPER"]
    zona  = "TRISTE"
    for lvl in ordem:
        if ytd_atual >= float(metas_anuais[lvl]):
            zona = lvl

    zona_idx   = ordem.index(zona)
    proximo    = ordem[zona_idx + 1] if zona_idx + 1 < len(ordem) else None
    falta_prox = max((float(metas_anuais[proximo]) - ytd_atual) if proximo else 0.0, 0.0)

    # -----------------------------------------------------------------------
    # Cards por trimestre
    # -----------------------------------------------------------------------
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
        comp_q  = float(atingido_compare[q])
        m_start, m_end = _QUARTER_MONTHS[q]
        atingido_mensal = {
            str(m): _decimal_to_float_2(faturamento_mensal[m])
            for m in range(m_start, m_end + 1)
        }
        cards.append({
            "trimestre":               q,
            "status":                  status,
            "atingido":                atual_q,
            "atingido_compare":        comp_q,
            "variacao_pct_vs_compare": _pct_change(atual_q, comp_q),
            "meta_triste":   float(metas_por_trimestre["TRISTE"][q]),
            "meta_base":     float(metas_por_trimestre["BASE"][q]),
            "meta_avancada": float(metas_por_trimestre["AVANCADA"][q]),
            "meta_super":    float(metas_por_trimestre["SUPER"][q]),
            "atingido_mensal": atingido_mensal,
        })

    # -----------------------------------------------------------------------
    # Bloco preditivo (novo — chave `predicao`)
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Payload final
    # -----------------------------------------------------------------------
    return {
        # ── campos existentes (inalterados) ──────────────────────────────
        "coluna_data":                 COLUMN_DATA_TED,
        "coluna_hono":                 col_hono,
        "coluna_sucumbencia":          col_suc,
        "year":                        year,
        "compare_year":                compare_year,
        "as_of":                       as_of.isoformat(),
        "trimestre_atual":             q_atual,
        "distribuicao_trimestral_pct": META_DISTRIBUICAO_TRIMESTRAL,
        "metas":                       metas_por_trimestre,
        "atingido": {
            str(year):         atingido_year,
            str(compare_year): atingido_compare,
        },
        "ytd": {
            "quarters":                 quarters_ytd,
            "atingido":                 float(Decimal(str(ytd_atual)).quantize(Decimal("0.01"))),
            "atingido_compare":         float(Decimal(str(ytd_compare)).quantize(Decimal("0.01"))),
            "variacao_pct_vs_compare":  _pct_change(ytd_atual, ytd_compare),
            "metas":                    metas_anuais,
            "zona":                     zona,
            "proxima_zona":             proximo,
            "falta_para_proxima_zona":  float(Decimal(str(falta_prox)).quantize(Decimal("0.01"))),
        },
        "cards_trimestre": cards,

        # ── campo novo ───────────────────────────────────────────────────
        "predicao": predicao,
    }


# ---------------------------------------------------------------------------
# Versão compacta (chatbots / alertas)
# ---------------------------------------------------------------------------

async def get_financeiro_NG_expectativa_hoje(
    *,
    year: int,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """Retorna apenas o núcleo preditivo, sem dados de metas completos."""
    payload = await get_financeiro_NG_faturamento_trimestral_meta(year=year, as_of=as_of)
    pred    = payload["predicao"]
    return {
        "as_of":              payload["as_of"],
        "trimestre_atual":    payload["trimestre_atual"],
        "frac_trimestre_pct": pred["frac_trimestre_pct"],
        "frac_ano_pct":       pred["frac_ano_pct"],
        **pred["expectativa_hoje"],
    }

# ---------------------------------------------------------------------------
# Dashboard Financeiro — Section "Reflexo Financeiro"
# ---------------------------------------------------------------------------

def _variacao_vs_mes_anterior(atual: float, anterior: float) -> float:
    """Variação % do período vs. o mesmo recorte do mês anterior.

    Sem base no mês anterior: crescimento a partir do zero é exibido como +100%
    (mesma convenção dos comparativos do LexPre).
    """
    if anterior == 0:
        return 100.0 if atual > 0 else 0.0
    return round(((atual - anterior) / anterior) * 100, 2)


def _valor_receita_row(
    row: Dict[str, Any],
    col_hono_suc: Optional[str],
    col_hono: Optional[str],
    col_suc: Optional[str],
) -> Decimal:
    """Receita da linha = coluna `HONO + SUCUMBÊNCIA`.

    Quando a célula está vazia (fórmula não arrastada na planilha), cai para
    HONORÁRIOS + SUCUMBÊNCIA — mesma soma usada na Meta Anual.
    """
    if col_hono_suc and row.get(col_hono_suc) not in (None, ""):
        return _parse_money(row.get(col_hono_suc))
    hono = _parse_money(row.get(col_hono)) if col_hono else Decimal("0")
    suc  = _parse_money(row.get(col_suc))  if col_suc  else Decimal("0")
    return hono + suc


def _reflexo_financeiro_metricas(
    rows: List[Dict[str, Any]],
    *,
    from_date: Optional[date],
    to_date: Optional[date],
    col_hono_suc: Optional[str],
    col_hono: Optional[str],
    col_suc: Optional[str],
) -> Dict[str, Any]:
    """Agrega as métricas da section num recorte de `DATA DO TED` (inclusive)."""
    fd = from_date or date.min
    td = to_date or date.max

    total_entradas = 0
    valor_receita  = Decimal("0")
    dias_ajuizamento_ted: List[int] = []
    valor_causa = Decimal("0")
    origem: Dict[str, Dict[str, Any]] = {
        chave: {"quantidade": 0, "valor": Decimal("0")} for chave, _ in ORIGENS_PIZZA
    }
    receita_por_materia: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    receita_por_ano_ajuizamento: Dict[Optional[int], Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    receita_por_mes_ajuizamento: Dict[Optional[Tuple[int, int]], Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_TED))
        if d is None or not (fd <= d <= td):
            continue
        receita_row = _valor_receita_row(row, col_hono_suc, col_hono, col_suc)
        total_entradas += 1
        valor_receita  += receita_row
        valor_causa    += _parse_money_flex(row.get(COLUMN_VALOR_CAUSA))

        materia = receita_por_materia[_normalizar_materia(row.get(COLUMN_MATERIA))]
        materia["quantidade"] += 1
        materia["valor"]      += receita_row

        origem_row = str(row.get(COLUMN_ORIGEM) or "").strip().upper()
        if origem_row in origem:
            origem[origem_row]["quantidade"] += 1
            origem[origem_row]["valor"]      += receita_row

        # Linhas sem DATA AJUIZAMENTO (ou com ajuizamento depois do TED, erro de
        # digitação) ficam fora da mediana, mas continuam contando nas entradas.
        d_ajuiz = _parse_date(row.get(COLUMN_DATA_AJUIZAMENTO))
        if d_ajuiz is not None and d_ajuiz <= d:
            dias_ajuizamento_ted.append((d - d_ajuiz).days)

        ano = receita_por_ano_ajuizamento[d_ajuiz.year if d_ajuiz else None]
        ano["quantidade"] += 1
        ano["valor"]      += receita_row

        mes_ajuiz = receita_por_mes_ajuizamento[(d_ajuiz.year, d_ajuiz.month) if d_ajuiz else None]
        mes_ajuiz["quantidade"] += 1
        mes_ajuiz["valor"]      += receita_row

    return {
        "total_entradas": total_entradas,
        "valor_receita":  valor_receita,
        "mediana_dias_ajuizamento_ted": (
            float(statistics.median(dias_ajuizamento_ted)) if dias_ajuizamento_ted else 0.0
        ),
        "valor_causa": valor_causa,
        "origem": origem,
        "receita_por_materia": dict(receita_por_materia),
        "receita_por_ano_ajuizamento": dict(receita_por_ano_ajuizamento),
        "receita_por_mes_ajuizamento": dict(receita_por_mes_ajuizamento),
    }


def _clientes_pendentes(
    rows: List[Dict[str, Any]], status_pendente: FrozenSet[str] = STATUS_CLIENTE_PENDENTE
) -> Dict[str, Any]:
    """Soma de `REPASSE DE CLIENTE` com STATUS pendente — foto atual, sem filtro
    de período (equivale ao `ALL(calendario)` da medida do Power BI)."""
    quantidade = 0
    valor = Decimal("0")
    for row in rows:
        status = str(row.get(COLUMN_STATUS) or "").strip().upper()
        if status not in status_pendente:
            continue
        quantidade += 1
        valor += _parse_money(row.get(COLUMN_REPASSE_CLIENTE))
    return {"valor": _decimal_to_float_2(valor), "quantidade": quantidade}


def _historico_mensal(
    rows: List[Dict[str, Any]],
    col_hono_suc: Optional[str],
    col_hono: Optional[str],
    col_suc: Optional[str],
) -> List[Dict[str, Any]]:
    """Receita, entradas e ticket médio por mês de `DATA DO TED`, histórico
    completo (não depende do filtro de período), em ordem cronológica."""
    por_mes: Dict[Tuple[int, int], Dict[str, Any]] = defaultdict(
        lambda: {"entradas": 0, "receita": Decimal("0")}
    )
    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_TED))
        if d is None:
            continue
        m = por_mes[(d.year, d.month)]
        m["entradas"] += 1
        m["receita"]  += _valor_receita_row(row, col_hono_suc, col_hono, col_suc)

    return [
        {
            "ano":          ano,
            "mes":          mes,
            "entradas":     m["entradas"],
            "receita":      _decimal_to_float_2(m["receita"]),
            "ticket_medio": (
                _decimal_to_float_2(m["receita"] / m["entradas"]) if m["entradas"] else 0.0
            ),
        }
        for (ano, mes), m in sorted(por_mes.items())
    ]


# A section "Evolução" começa em 2023: 2022 só tem ~R$ 21 mil (início da planilha)
# e o crescimento 2022→2023 (+5.930%) achatava a linha dos anos seguintes.
EVOLUCAO_ANO_INICIAL = 2023


@dataclass(frozen=True)
class ConfigFinanceiroEstrategico:
    """O que muda entre os escritórios no dashboard Financeiro Estratégico — o
    resto (colunas, regras de receita, gráficos) é o mesmo nas duas planilhas."""
    sheet_name: str
    status_pendente: FrozenSet[str]
    # Primeiro ano da Evolução e do histórico usado na Previsão.
    ano_inicial: int


FINANCEIRO_ESTRATEGICO_CONFIG: Dict[str, ConfigFinanceiroEstrategico] = {
    "NG": ConfigFinanceiroEstrategico(
        sheet_name="financeiro_NG",
        status_pendente=STATUS_CLIENTE_PENDENTE,
        ano_inicial=EVOLUCAO_ANO_INICIAL,
    ),
    # LA: receita na planilha praticamente só a partir de 2025 (2024 tem 135 TEDs,
    # até 2023 só 19); a planilha do LA tem ainda AGUARDANDO HOMOLOGAÇÃO DO ACORDO
    # e PAGAMENTO AGENDADO como repasse pendente (decisão do usuário, 29/10/2026).
    "LA": ConfigFinanceiroEstrategico(
        sheet_name="financeiro_LA",
        status_pendente=STATUS_CLIENTE_PENDENTE | {
            "AGUARDANDO HOMOLOGAÇÃO DO ACORDO",
            "PAGAMENTO AGENDADO",
        },
        ano_inicial=2025,
    ),
}


def _config_financeiro(escritorio: str) -> ConfigFinanceiroEstrategico:
    try:
        return FINANCEIRO_ESTRATEGICO_CONFIG[escritorio]
    except KeyError:
        raise KeyError(f"Escritório sem Financeiro Estratégico: {escritorio!r}") from None


async def _repasses_do_escritorio(escritorio: str) -> List[Dict[str, Any]]:
    """Linhas da aba `REPASSES CLIENTES` da planilha financeira do escritório."""
    return await fetch_sheet(_config_financeiro(escritorio).sheet_name)


def _evolucao_anual(
    historico_mensal: List[Dict[str, Any]], ano_inicial: int = EVOLUCAO_ANO_INICIAL
) -> List[Dict[str, Any]]:
    """Receita por ANO do TED + crescimento % vs. o ano anterior (section "Evolução").

    crescimento_pct = (receita_ano / receita_ano_anterior − 1) × 100; None no
    primeiro ano exibido (`ano_inicial`) ou quando o anterior não teve receita.
    """
    por_ano: Dict[int, float] = defaultdict(float)
    for m in historico_mensal:
        if m["ano"] >= ano_inicial:
            por_ano[m["ano"]] += m["receita"]
    anos = sorted(por_ano)
    evolucao = []
    for i, ano in enumerate(anos):
        receita = round(por_ano[ano], 2)
        anterior = por_ano[anos[i - 1]] if i > 0 else 0.0
        crescimento = round((receita / anterior - 1) * 100, 2) if anterior > 0 else None
        evolucao.append({"ano": ano, "receita": receita, "crescimento_pct": crescimento})
    return evolucao


def _reflexo_do_mes(
    por_mes: Dict[Optional[Tuple[int, int]], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Receita dos TEDs do período por MÊS DE AJUIZAMENTO (ano/mês da DATA
    AJUIZAMENTO) — "Reflexo do Mês": de quando são os processos que pagaram no
    período. Sem DATA AJUIZAMENTO vem primeiro (ano/mes = None), como o
    "(Em branco)" do Power BI; o resto em ordem cronológica."""
    chaves = sorted(por_mes, key=lambda k: (k is not None, k or (0, 0)))
    return [
        {
            "ano":      k[0] if k else None,
            "mes":      k[1] if k else None,
            "entradas": por_mes[k]["quantidade"],
            "receita":  _decimal_to_float_2(por_mes[k]["valor"]),
        }
        for k in chaves
    ]


def _receita_por_materia_pizza(por_materia: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Top N matérias por receita + "Outros" (soma do resto), maior primeiro."""
    ordenadas = sorted(por_materia.items(), key=lambda kv: kv[1]["valor"], reverse=True)
    fatias = [
        {"name": nome, "value": _decimal_to_float_2(m["valor"]), "quantidade": m["quantidade"]}
        for nome, m in ordenadas[:PIZZA_MATERIAS_TOP_N]
    ]
    resto = ordenadas[PIZZA_MATERIAS_TOP_N:]
    if resto:
        fatias.append({
            "name":       "OUTROS",
            "value":      _decimal_to_float_2(sum((m["valor"] for _, m in resto), Decimal("0"))),
            "quantidade": sum(m["quantidade"] for _, m in resto),
        })
    return [f for f in fatias if f["value"] > 0]


def _receita_por_ano_ajuizamento_pizza(
    por_ano: Dict[Optional[int], Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Receita por ano de DATA AJUIZAMENTO, anos em ordem crescente e "Sem data" por último."""
    anos = sorted(por_ano, key=lambda a: (a is None, a or 0))
    fatias = [
        {
            "name":       str(ano) if ano is not None else ANO_AJUIZAMENTO_SEM_DATA,
            "value":      _decimal_to_float_2(por_ano[ano]["valor"]),
            "quantidade": por_ano[ano]["quantidade"],
        }
        for ano in anos
    ]
    return [f for f in fatias if f["value"] > 0]


def _origem_pizza(origem: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    total = sum(o["quantidade"] for o in origem.values())
    return [
        {
            "name":       rotulo,
            "quantidade": origem[chave]["quantidade"],
            "valor":      _decimal_to_float_2(origem[chave]["valor"]),
            "percentual": round(origem[chave]["quantidade"] / total * 100, 2) if total else 0.0,
        }
        for chave, rotulo in ORIGENS_PIZZA
    ]


async def get_financeiro_NG_reflexo_financeiro(
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    origens: Optional[List[str]] = None,
    materias: Optional[List[str]] = None,
    anos_ajuizamento: Optional[List[str]] = None,
    escritorio: str = "NG",
    ajuizamento_from: Optional[date] = None,
    ajuizamento_to: Optional[date] = None,
) -> Dict[str, Any]:
    """Cards da section "Reflexo Financeiro" (planilha `REPASSES CLIENTES`).

    V2: `ajuizamento_from`/`ajuizamento_to` = o período próprio da section "Reflexo de Ajuizamento" (pela
    DATA AJUIZAMENTO, escolhido na própria section); sem eles, o período da página, como na v1.

    `escritorio` ("NG" ou "LA") escolhe a planilha e as regras próprias
    (`FINANCEIRO_ESTRATEGICO_CONFIG`); o cálculo é o mesmo.

    Base de datas: `DATA DO TED`. Comparativo: mesmo recorte de dia-do-mês um
    mês civil antes (`resolver_periodo_comparativo`); sem `from`/`to`, o
    período atual é o mês corrente até hoje.

    Cards
    -----
    total_entradas  quantidade de linhas (TEDs) no período
    valor_receita   soma de `HONO + SUCUMBÊNCIA` no período
    ticket_medio    valor_receita ÷ total_entradas (0 sem entradas)
    clientes_pendentes  soma de `REPASSE DE CLIENTE` com STATUS pendente (sem período)
    mediana_tempo_ajuizamento_ted  mediana de dias entre DATA AJUIZAMENTO e DATA DO TED
                    dos TEDs do período (+ a mesma em meses)

    Gráficos
    --------
    causa_x_receita  funil: soma de `VALOR DA CAUSA` vs. Valor Total em Receita
    origem           pizza: Condenação × Acordo (quantidade, receita e % pela quantidade)
    receita_por_materia          pizza: receita por MATÉRIA (top N + "Outros")
    receita_por_ano_ajuizamento  pizza: receita por ano de DATA AJUIZAMENTO
    historico_mensal  receita/entradas/ticket por mês do TED (histórico completo,
                    alimenta "Ticket Médio por Mês")
    reflexo_do_mes    receita dos TEDs do PERÍODO agrupada pelo mês de DATA AJUIZAMENTO
    reflexo_ajuizamento  receita/entradas/ticket das linhas com DATA AJUIZAMENTO no
                    período (section "Reflexo de Ajuizamento")
    """
    cfg = _config_financeiro(escritorio)
    rows_todas = await _repasses_do_escritorio(escritorio)
    filtros_opcoes = _filtros_opcoes(rows_todas)
    # Todos os cards e gráficos (inclusive Clientes Pendentes e o histórico mensal)
    # respeitam os filtros clicáveis.
    rows = _filtrar_rows_reflexo(
        rows_todas, origens=origens, materias=materias, anos_ajuizamento=anos_ajuizamento
    )

    col_hono_suc = _pick_first_existing_column(rows_todas, _COL_HONO_SUCUMB_CANDIDATES)
    col_hono     = _pick_first_existing_column(rows_todas, _COL_HONO_CANDIDATES)
    col_suc      = _pick_first_existing_column(rows_todas, _COL_SUCUMB_CANDIDATES)

    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    # V2: o período próprio da section "Reflexo de Ajuizamento" (o comparativo segue a mesma regra).
    if ajuizamento_from and ajuizamento_to:
        aj_inicio, aj_fim, aj_inicio_ant, aj_fim_ant = resolver_periodo_comparativo(
            ajuizamento_from, ajuizamento_to
        )
    else:
        aj_inicio, aj_fim, aj_inicio_ant, aj_fim_ant = (
            inicio_atual, fim_atual, inicio_anterior, fim_anterior
        )
    kwargs_cols = dict(col_hono_suc=col_hono_suc, col_hono=col_hono, col_suc=col_suc)
    atual    = _reflexo_financeiro_metricas(
        rows, from_date=inicio_atual, to_date=fim_atual, **kwargs_cols
    )
    anterior = _reflexo_financeiro_metricas(
        rows, from_date=inicio_anterior, to_date=fim_anterior, **kwargs_cols
    )

    receita_atual    = _decimal_to_float_2(atual["valor_receita"])
    receita_anterior = _decimal_to_float_2(anterior["valor_receita"])

    def _ticket(m: Dict[str, Any]) -> float:
        if m["total_entradas"] == 0:
            return 0.0
        return _decimal_to_float_2(m["valor_receita"] / m["total_entradas"])

    ticket_atual    = _ticket(atual)
    ticket_anterior = _ticket(anterior)

    historico_mensal = _historico_mensal(rows, **kwargs_cols)

    mediana_dias_atual    = atual["mediana_dias_ajuizamento_ted"]
    mediana_dias_anterior = anterior["mediana_dias_ajuizamento_ted"]

    return {
        "coluna_data":   COLUMN_DATA_TED,
        "coluna_receita": col_hono_suc,
        "periodo": {
            "inicio":          inicio_atual.isoformat(),
            "fim":             fim_atual.isoformat(),
            "inicio_anterior": inicio_anterior.isoformat(),
            "fim_anterior":    fim_anterior.isoformat(),
        },
        "total_entradas": {
            "valor":          atual["total_entradas"],
            "valor_anterior": anterior["total_entradas"],
            "comparativo":    _variacao_vs_mes_anterior(
                atual["total_entradas"], anterior["total_entradas"]
            ),
        },
        "valor_receita": {
            "valor":          receita_atual,
            "valor_anterior": receita_anterior,
            "comparativo":    _variacao_vs_mes_anterior(receita_atual, receita_anterior),
        },
        "ticket_medio": {
            "valor":          ticket_atual,
            "valor_anterior": ticket_anterior,
            "comparativo":    _variacao_vs_mes_anterior(ticket_atual, ticket_anterior),
        },
        "clientes_pendentes": _clientes_pendentes(rows, cfg.status_pendente),
        "causa_x_receita": {
            "valor_causa":   _decimal_to_float_2(atual["valor_causa"]),
            "valor_receita": receita_atual,
        },
        "origem": _origem_pizza(atual["origem"]),
        "receita_por_materia": _receita_por_materia_pizza(atual["receita_por_materia"]),
        "receita_por_ano_ajuizamento": _receita_por_ano_ajuizamento_pizza(
            atual["receita_por_ano_ajuizamento"]
        ),
        "historico_mensal": historico_mensal,
        "evolucao_anual": _evolucao_anual(historico_mensal, cfg.ano_inicial),
        "reflexo_do_mes": _reflexo_do_mes(atual["receita_por_mes_ajuizamento"]),
        "filtros_opcoes": filtros_opcoes,
        # Section "Reflexo de Ajuizamento": o período dela (V2) ou o da página, aplicado a DATA AJUIZAMENTO.
        "reflexo_ajuizamento": {
            "periodo": {"inicio": aj_inicio.isoformat(), "fim": aj_fim.isoformat()},
            **_reflexo_ajuizamento(
                rows,
                inicio_atual=aj_inicio,
                fim_atual=aj_fim,
                inicio_anterior=aj_inicio_ant,
                fim_anterior=aj_fim_ant,
                **kwargs_cols,
            ),
        },
        "mediana_tempo_ajuizamento_ted": {
            "dias":             mediana_dias_atual,
            "dias_anterior":    mediana_dias_anterior,
            "meses":            round(mediana_dias_atual / _DIAS_POR_MES_MEDIO, 1),
            "meses_anterior":   round(mediana_dias_anterior / _DIAS_POR_MES_MEDIO, 1),
            "comparativo":      _variacao_vs_mes_anterior(mediana_dias_atual, mediana_dias_anterior),
        },
    }


def _receita_por_ajuizamento(
    rows: List[Dict[str, Any]],
    *,
    from_date: date,
    to_date: date,
    col_hono_suc: Optional[str],
    col_hono: Optional[str],
    col_suc: Optional[str],
) -> Dict[str, Any]:
    """Métricas das linhas com `DATA AJUIZAMENTO` no recorte (inclusive), qualquer
    que seja a data do TED: entradas, receita, mediana de dias ajuizamento→TED e as
    quebras por matéria, origem e ano do TED (pizzas da section)."""
    entradas = 0
    receita = Decimal("0")
    dias: List[int] = []
    por_materia: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    origem: Dict[str, Dict[str, Any]] = {
        chave: {"quantidade": 0, "valor": Decimal("0")} for chave, _ in ORIGENS_PIZZA
    }
    por_ano_ted: Dict[Optional[int], Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    por_mes_ted: Dict[Optional[Tuple[int, int]], Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_AJUIZAMENTO))
        if d is None or not (from_date <= d <= to_date):
            continue
        receita_row = _valor_receita_row(row, col_hono_suc, col_hono, col_suc)
        entradas += 1
        receita += receita_row
        # Mesma regra da mediana do Reflexo Financeiro: sem TED ou TED antes do
        # ajuizamento (erro de digitação) fica fora da mediana.
        d_ted = _parse_date(row.get(COLUMN_DATA_TED))
        if d_ted is not None and d <= d_ted:
            dias.append((d_ted - d).days)

        materia = por_materia[_normalizar_materia(row.get(COLUMN_MATERIA))]
        materia["quantidade"] += 1
        materia["valor"]      += receita_row
        origem_row = str(row.get(COLUMN_ORIGEM) or "").strip().upper()
        if origem_row in origem:
            origem[origem_row]["quantidade"] += 1
            origem[origem_row]["valor"]      += receita_row
        ano = por_ano_ted[d_ted.year if d_ted else None]
        ano["quantidade"] += 1
        ano["valor"]      += receita_row
        mes = por_mes_ted[(d_ted.year, d_ted.month) if d_ted else None]
        mes["quantidade"] += 1
        mes["valor"]      += receita_row
    return {
        "entradas":     entradas,
        "receita":      receita,
        "mediana_dias": float(statistics.median(dias)) if dias else 0.0,
        "por_materia":  por_materia,
        "origem":       origem,
        "por_ano_ted":  por_ano_ted,
        "por_mes_ted":  por_mes_ted,
    }


def _reflexo_ajuizamento(
    rows: List[Dict[str, Any]],
    *,
    inicio_atual: date,
    fim_atual: date,
    inicio_anterior: date,
    fim_anterior: date,
    **kwargs_cols: Optional[str],
) -> Dict[str, Any]:
    """Cards da section "Reflexo de Ajuizamento": mesmas métricas do Reflexo
    Financeiro (receita, entradas, ticket médio), mas o período da página recorta
    `DATA AJUIZAMENTO` em vez de `DATA DO TED`."""
    atual = _receita_por_ajuizamento(
        rows, from_date=inicio_atual, to_date=fim_atual, **kwargs_cols
    )
    anterior = _receita_por_ajuizamento(
        rows, from_date=inicio_anterior, to_date=fim_anterior, **kwargs_cols
    )
    ent_atual, rec_atual, dias_atual = atual["entradas"], atual["receita"], atual["mediana_dias"]
    ent_ant, rec_ant, dias_ant = anterior["entradas"], anterior["receita"], anterior["mediana_dias"]
    receita_atual    = _decimal_to_float_2(rec_atual)
    receita_anterior = _decimal_to_float_2(rec_ant)
    ticket_atual     = _decimal_to_float_2(rec_atual / ent_atual) if ent_atual else 0.0
    ticket_anterior  = _decimal_to_float_2(rec_ant / ent_ant) if ent_ant else 0.0
    return {
        "total_entradas": {
            "valor":          ent_atual,
            "valor_anterior": ent_ant,
            "comparativo":    _variacao_vs_mes_anterior(ent_atual, ent_ant),
        },
        "valor_receita": {
            "valor":          receita_atual,
            "valor_anterior": receita_anterior,
            "comparativo":    _variacao_vs_mes_anterior(receita_atual, receita_anterior),
        },
        "ticket_medio": {
            "valor":          ticket_atual,
            "valor_anterior": ticket_anterior,
            "comparativo":    _variacao_vs_mes_anterior(ticket_atual, ticket_anterior),
        },
        "mediana_tempo_ajuizamento_ted": {
            "dias":           dias_atual,
            "dias_anterior":  dias_ant,
            "meses":          round(dias_atual / _DIAS_POR_MES_MEDIO, 1),
            "meses_anterior": round(dias_ant / _DIAS_POR_MES_MEDIO, 1),
            "comparativo":    _variacao_vs_mes_anterior(dias_atual, dias_ant),
        },
        # Pizzas (só o período atual): receita por matéria, Acordo × Condenação e
        # "Percentual Anual" pelo ano da DATA DO TED ("Sem data" = sem TED).
        "receita_por_materia": _receita_por_materia_pizza(dict(atual["por_materia"])),
        "origem":              _origem_pizza(atual["origem"]),
        "receita_por_ano_ted": _receita_por_ano_ajuizamento_pizza(dict(atual["por_ano_ted"])),
        # Barras "Reflexo do Mês" desta section: receita dos processos ajuizados no
        # período, por mês da DATA DO TED (quando o dinheiro efetivamente caiu).
        "reflexo_do_mes_ted": _reflexo_do_mes(dict(atual["por_mes_ted"])),
    }


# ---------------------------------------------------------------------------
# Dashboard Financeiro — Section "Conversão"
# ---------------------------------------------------------------------------

ANO_EM_BRANCO = "(Em branco)"


def _ano_label(d: Optional[date]) -> str:
    return str(d.year) if d else ANO_EM_BRANCO


def _ordenar_anos(anos: set) -> List[str]:
    """"(Em branco)" primeiro (como no slicer do Power BI), depois anos crescentes."""
    return sorted(anos, key=lambda a: (a != ANO_EM_BRANCO, a))


async def get_financeiro_NG_conversao(
    *,
    anos_ajuizamento: Optional[List[str]] = None,
    anos_financeiro: Optional[List[str]] = None,
    origens: Optional[List[str]] = None,
    materias: Optional[List[str]] = None,
    escritorio: str = "NG",
) -> Dict[str, Any]:
    """Receita de conversão — equivalente à medida RECEITA_CONVERSAO do Power BI.

    Soma `HONO + SUCUMBÊNCIA` das linhas cujo ano de `DATA AJUIZAMENTO` está em
    `anos_ajuizamento` E cujo ano de `DATA DO TED` está em `anos_financeiro`.
    Lista vazia/None = sem filtro naquele eixo; "(Em branco)" = linha sem a data.
    Não usa o período da página (a section tem os próprios seletores de ano);
    os filtros de Origem/Matéria da página se aplicam. Sem o filtro `UF <> "RJ"`
    do DAX: a planilha só tem NG (AM/PA/PB).
    """
    rows_todas = await _repasses_do_escritorio(escritorio)
    rows = _filtrar_rows_reflexo(rows_todas, origens=origens, materias=materias)

    col_hono_suc = _pick_first_existing_column(rows_todas, _COL_HONO_SUCUMB_CANDIDATES)
    col_hono     = _pick_first_existing_column(rows_todas, _COL_HONO_CANDIDATES)
    col_suc      = _pick_first_existing_column(rows_todas, _COL_SUCUMB_CANDIDATES)

    alvo_ajuiz = {str(a).strip() for a in (anos_ajuizamento or []) if str(a).strip()}
    alvo_fin   = {str(a).strip() for a in (anos_financeiro or []) if str(a).strip()}

    opcoes_ajuiz: set = set()
    opcoes_fin: set = set()
    quantidade = 0
    receita = Decimal("0")
    receita_por_materia: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    receita_por_ano_ajuiz: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal("0")}
    )
    for row in rows_todas:
        opcoes_ajuiz.add(_ano_label(_parse_date(row.get(COLUMN_DATA_AJUIZAMENTO))))
        opcoes_fin.add(_ano_label(_parse_date(row.get(COLUMN_DATA_TED))))
    for row in rows:
        ano_ajuiz = _ano_label(_parse_date(row.get(COLUMN_DATA_AJUIZAMENTO)))
        ano_fin   = _ano_label(_parse_date(row.get(COLUMN_DATA_TED)))
        if alvo_ajuiz and ano_ajuiz not in alvo_ajuiz:
            continue
        if alvo_fin and ano_fin not in alvo_fin:
            continue
        receita_row = _valor_receita_row(row, col_hono_suc, col_hono, col_suc)
        quantidade += 1
        receita += receita_row
        materia = receita_por_materia[_normalizar_materia(row.get(COLUMN_MATERIA))]
        materia["quantidade"] += 1
        materia["valor"]      += receita_row
        ano = receita_por_ano_ajuiz[ano_ajuiz]
        ano["quantidade"] += 1
        ano["valor"]      += receita_row

    return {
        "receita":    _decimal_to_float_2(receita),
        "quantidade": quantidade,
        # Pizza "Receita x Matérias" da section (mesmas linhas da receita; top N + Outros).
        "receita_por_materia": _receita_por_materia_pizza(dict(receita_por_materia)),
        # Pizza "Percentual Anual": mesmas linhas por ano de DATA AJUIZAMENTO, com o
        # mesmo rótulo do seletor ("(Em branco)" primeiro) — o clique marca o ano nele.
        "receita_por_ano_ajuizamento": [
            {
                "name":       ano,
                "value":      _decimal_to_float_2(receita_por_ano_ajuiz[ano]["valor"]),
                "quantidade": receita_por_ano_ajuiz[ano]["quantidade"],
            }
            for ano in _ordenar_anos(set(receita_por_ano_ajuiz))
            if receita_por_ano_ajuiz[ano]["valor"] > 0
        ],
        "anos_ajuizamento_opcoes": _ordenar_anos(opcoes_ajuiz),
        "anos_financeiro_opcoes":  _ordenar_anos(opcoes_fin),
    }


# ---------------------------------------------------------------------------
# Dashboard Financeiro — Section "Previsão"
# ---------------------------------------------------------------------------
#
# Quatro cenários simples e explicáveis para a receita do próximo ano (sem
# bibliotecas de ciência de dados — a API não tem numpy/pandas/statsmodels).
# Tudo é calculado com a base inteira (sem filtros da página), pois o cenário
# "por safra" usa o valor ajuizado dos bancos, que não tem Origem/Matéria.
#
#   A. ritmo_medio      — crescimento médio anual dos últimos 2 anos (CAGR)
#   B. ultimo_ano       — repete o crescimento do ano corrente sobre o anterior
#   C. tendencia        — reta de tendência (log) dos últimos 24 meses fechados
#                         × peso histórico de cada mês (sazonalidade)  ← BASE
#   D. safra            — valor ajuizado de cada safra × taxa histórica de
#                         conversão em receita por idade do processo (0, 1, 2 anos)

PREVISAO_CENARIO_BASE = "tendencia"
_PREVISAO_MESES_TENDENCIA = 24
_PREVISAO_LAGS_SAFRA = (0, 1, 2)


def _receita_por_mes_e_safra(
    rows: List[Dict[str, Any]],
    col_hono_suc: Optional[str],
    col_hono: Optional[str],
    col_suc: Optional[str],
) -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], float], List[Tuple[date, float]]]:
    """(receita por (ano, mês) do TED, receita por (ano ajuizamento, ano TED), lista (data TED, receita))."""
    por_mes: Dict[Tuple[int, int], float] = defaultdict(float)
    por_safra: Dict[Tuple[int, int], float] = defaultdict(float)
    teds: List[Tuple[date, float]] = []
    for row in rows:
        d = _parse_date(row.get(COLUMN_DATA_TED))
        if d is None:
            continue
        v = float(_valor_receita_row(row, col_hono_suc, col_hono, col_suc))
        por_mes[(d.year, d.month)] += v
        teds.append((d, v))
        d_ajuiz = _parse_date(row.get(COLUMN_DATA_AJUIZAMENTO))
        if d_ajuiz is not None:
            por_safra[(d_ajuiz.year, d.year)] += v
    return por_mes, por_safra, teds


def _fracao_restante_do_ano(teds: List[Tuple[date, float]], hoje: date, anos_ref: List[int]) -> float:
    """Fração média da receita anual que caiu DEPOIS do dia/mês de `hoje`, nos anos de referência."""
    fracoes = []
    for ano in anos_ref:
        total = sum(v for d, v in teds if d.year == ano)
        if total <= 0:
            continue
        try:
            corte = hoje.replace(year=ano)
        except ValueError:  # 29/02
            corte = date(ano, 2, 28)
        depois = sum(v for d, v in teds if d.year == ano and d > corte)
        fracoes.append(depois / total)
    return sum(fracoes) / len(fracoes) if fracoes else 0.0


def calcular_previsao_receita(
    rows: List[Dict[str, Any]],
    *,
    ajuizado_por_ano: Dict[int, float],
    hoje: Optional[date] = None,
    ano_inicial: int = EVOLUCAO_ANO_INICIAL,
) -> Dict[str, Any]:
    """Previsão da receita do próximo ano em 4 cenários (ver cabeçalho da section).

    `ajuizado_por_ano`: valor de causa ajuizado (LexFlow) por ano de distribuição
    — o mesmo do card "Valor de Causa Ajuizado".
    `ano_inicial`: TEDs anteriores a esse ano ficam fora do histórico (planilha
    ainda incompleta antes dele); com menos de 2 anos fechados, `aviso_historico`
    explica que os cenários são pouco confiáveis.
    """
    hoje = hoje or date.today()
    rows = [
        r for r in rows
        if (d := _parse_date(r.get(COLUMN_DATA_TED))) is not None and d.year >= ano_inicial
    ]
    ano_atual = hoje.year
    ano_previsto = ano_atual + 1

    col_hono_suc = _pick_first_existing_column(rows, _COL_HONO_SUCUMB_CANDIDATES)
    col_hono     = _pick_first_existing_column(rows, _COL_HONO_CANDIDATES)
    col_suc      = _pick_first_existing_column(rows, _COL_SUCUMB_CANDIDATES)
    por_mes, por_safra, teds = _receita_por_mes_e_safra(rows, col_hono_suc, col_hono, col_suc)

    anual: Dict[int, float] = defaultdict(float)
    for (ano, _mes), v in por_mes.items():
        anual[ano] += v

    # ── Ano corrente fechado (estimado) ────────────────────────────────────
    anos_ref = [a for a in (ano_atual - 2, ano_atual - 1) if anual.get(a, 0) > 0]
    fracao_restante = _fracao_restante_do_ano(teds, hoje, anos_ref)
    ytd = anual.get(ano_atual, 0.0)
    atual_estimado = ytd / (1 - fracao_restante) if fracao_restante < 1 else ytd

    cenarios: List[Dict[str, Any]] = []

    def _cenario(cid: str, nome: str, valor: float, premissa: str, explicacao: str, quando: str, detalhe: str) -> None:
        cenarios.append({
            "id":          cid,
            "nome":        nome,
            "valor":       round(max(valor, 0.0), 2),
            "crescimento_pct": round((valor / atual_estimado - 1) * 100, 2) if atual_estimado > 0 else None,
            "premissa":    premissa,
            "explicacao":  explicacao,
            "quando_faz_sentido": quando,
            "detalhe":     detalhe,
        })

    # ── A. Ritmo médio dos últimos 2 anos ──────────────────────────────────
    base_a = anual.get(ano_atual - 2, 0.0)
    if base_a > 0 and atual_estimado > 0:
        cagr = (atual_estimado / base_a) ** 0.5 - 1
        _cenario(
            "ritmo_medio", "Ritmo médio dos últimos 2 anos", atual_estimado * (1 + cagr),
            f"A receita continua crescendo {cagr * 100:.0f}% ao ano, a média de {ano_atual - 2} a {ano_atual}.",
            f"Calculamos quanto a receita cresceu, em média, por ano entre {ano_atual - 2} e {ano_atual} "
            f"e aplicamos o mesmo ritmo em {ano_previsto}.",
            "Quando o crescimento dos últimos anos foi estável e nada mudou na operação.",
            f"Crescimento médio anual (CAGR) {ano_atual - 2}→{ano_atual}: {cagr * 100:.1f}%.",
        )

    # ── B. Repete o crescimento do ano corrente ────────────────────────────
    base_b = anual.get(ano_atual - 1, 0.0)
    if base_b > 0 and atual_estimado > 0:
        cresc = atual_estimado / base_b - 1
        _cenario(
            "ultimo_ano", f"Repete o crescimento de {ano_atual}", atual_estimado * (1 + cresc),
            f"{ano_previsto} cresce os mesmos {cresc * 100:.0f}% que {ano_atual} cresceu sobre {ano_atual - 1}.",
            f"Supomos que {ano_previsto} vai crescer exatamente o mesmo percentual que {ano_atual} "
            f"(estimado fechado) cresceu sobre {ano_atual - 1}.",
            "Quando o ano atual representa bem o momento do escritório.",
            f"Crescimento {ano_atual - 1}→{ano_atual} (estimado): {cresc * 100:.1f}%.",
        )

    # ── C. Tendência mês a mês + sazonalidade (BASE) ───────────────────────
    meses = sorted(k for k in por_mes if k < (hoje.year, hoje.month))[-_PREVISAO_MESES_TENDENCIA:]
    anos_saz = [a for a in (ano_atual - 3, ano_atual - 2, ano_atual - 1) if anual.get(a, 0) > 0]
    if len(meses) >= 12 and anos_saz:
        xs = list(range(len(meses)))
        ys = [math.log(max(por_mes[k], 1.0)) for k in meses]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        a = my - b * mx
        saz = []
        for m in range(1, 13):
            pesos = [por_mes.get((ano, m), 0.0) / (anual[ano] / 12) for ano in anos_saz]
            saz.append(sum(pesos) / len(pesos))
        media_saz = sum(saz) / 12 or 1.0
        saz = [s / media_saz for s in saz]
        ult_ano, ult_mes = meses[-1]
        previsto = 0.0
        for m in range(1, 13):
            passos = (ano_previsto - ult_ano) * 12 + (m - ult_mes)
            previsto += math.exp(a + b * (len(meses) - 1 + passos)) * saz[m - 1]
        ritmo = math.exp(b * 12) - 1
        _cenario(
            "tendencia", "Tendência mês a mês", previsto,
            f"A linha de tendência dos últimos {len(meses)} meses (≈{ritmo * 100:.0f}% ao ano) continua, "
            "com os meses fortes e fracos de sempre.",
            f"Traçamos a linha de tendência da receita mês a mês dos últimos {len(meses)} meses e a "
            f"prolongamos até o fim de {ano_previsto}, respeitando os meses que historicamente pagam "
            "mais ou menos (sazonalidade).",
            "É o cenário mais equilibrado: usa o histórico recente inteiro, não só um ano.",
            f"Ritmo da tendência: {ritmo * 100:.1f}% ao ano · sazonalidade de {anos_saz[0]}–{anos_saz[-1]}.",
        )

    # ── D. Por safra de ajuizamento ─────────────────────────────────────────
    taxas: Dict[int, float] = {}
    for lag in _PREVISAO_LAGS_SAFRA:
        amostras = [
            por_safra.get((k, k + lag), 0.0) / ajuizado_por_ano[k]
            for k in range(ano_atual - 3, ano_atual)
            if k + lag <= ano_atual - 1 and ajuizado_por_ano.get(k, 0) > 0
        ]
        if amostras:
            taxas[lag] = sum(amostras) / len(amostras)
    conferencia = None
    if len(taxas) == len(_PREVISAO_LAGS_SAFRA) and ajuizado_por_ano.get(ano_atual, 0) > 0:
        dias_ano = 366 if calendar.isleap(ano_atual) else 365
        decorrido = (hoje - date(ano_atual, 1, 1)).days + 1
        ajuizado_atual_estimado = ajuizado_por_ano[ano_atual] * dias_ano / decorrido
        partes = {
            0: ajuizado_atual_estimado * taxas[0],  # ajuizado do ano previsto ≈ ano atual
            1: ajuizado_atual_estimado * taxas[1],
            2: ajuizado_por_ano.get(ano_atual - 1, 0.0) * taxas[2],
        }
        _cenario(
            "safra", "Pelos processos já ajuizados", sum(partes.values()),
            f"Os processos ajuizados em {ano_atual - 1} e {ano_atual} viram receita no mesmo ritmo das safras anteriores.",
            "Olhamos quanto do valor de causa costuma virar receita conforme o processo envelhece "
            f"({taxas[0] * 100:.1f}% no ano do ajuizamento, {taxas[1] * 100:.1f}% no ano seguinte e "
            f"{taxas[2] * 100:.1f}% no segundo ano) e aplicamos isso aos processos já ajuizados. Como o "
            "volume ajuizado cresceu muito, este cenário prevê um salto.",
            "Quando o aumento recente de ajuizamentos vai mesmo se transformar em pagamentos.",
            f"Ajuizado {ano_atual - 1}: {_fmt_brl(ajuizado_por_ano.get(ano_atual - 1, 0.0))} · "
            f"{ano_atual} (projetado no ano): {_fmt_brl(ajuizado_atual_estimado)} · "
            f"{ano_previsto} assumido igual a {ano_atual}.",
        )
        # Conferência retroativa: com as mesmas taxas, quanto o modelo "teria previsto"
        # para o ano passado (as taxas usam esse ano, então é uma checagem de aderência).
        alvo = ano_atual - 1
        prev_alvo = sum(ajuizado_por_ano.get(alvo - lag, 0.0) * taxas[lag] for lag in _PREVISAO_LAGS_SAFRA)
        real_alvo = anual.get(alvo, 0.0)
        if real_alvo > 0:
            conferencia = {
                "ano": alvo,
                "previsto": round(prev_alvo, 2),
                "real": round(real_alvo, 2),
                "erro_pct": round((prev_alvo / real_alvo - 1) * 100, 2),
            }

    # ── Rótulos: base fixa; o maior (fora a base) = Otimista, o menor = Conservador ─
    base = next((c for c in cenarios if c["id"] == PREVISAO_CENARIO_BASE), cenarios[0] if cenarios else None)
    outros = [c for c in cenarios if base is None or c["id"] != base["id"]]
    maior = max(outros, key=lambda c: c["valor"]) if outros else None
    menor = min(outros, key=lambda c: c["valor"]) if outros else None
    for c in cenarios:
        if base and c["id"] == base["id"]:
            c["rotulo"] = "Base"
        elif maior is c and (base is None or c["valor"] > base["valor"]):
            c["rotulo"] = "Otimista"
        elif menor is c and (base is None or c["valor"] < base["valor"]):
            c["rotulo"] = "Conservador"
        else:
            c["rotulo"] = "Intermediário"

    valores = [c["valor"] for c in cenarios]
    anos_fechados = len([a for a in anual if a < ano_atual])
    return {
        "data_referencia":   hoje.isoformat(),
        "ano_atual":         ano_atual,
        "ano_previsto":      ano_previsto,
        "receita_anual_real": [
            {"ano": a, "receita": round(v, 2)} for a, v in sorted(anual.items()) if a >= ano_inicial
        ],
        "ano_atual_ate_hoje":   round(ytd, 2),
        "ano_atual_estimado":   round(atual_estimado, 2),
        "fracao_restante_pct":  round(fracao_restante * 100, 2),
        "anos_referencia_fracao": anos_ref,
        "cenarios":          cenarios,
        "cenario_base":      base["id"] if base else None,
        "faixa": {"minimo": round(min(valores), 2), "maximo": round(max(valores), 2)} if valores else None,
        "conferencia_safra": conferencia,
        "taxas_safra_pct":   {str(k): round(v * 100, 2) for k, v in taxas.items()},
        "aviso_historico":   (
            f"A planilha só tem receita confiável a partir de {ano_inicial}: com "
            f"{anos_fechados} ano(s) fechado(s) de histórico, os cenários são uma "
            "estimativa grosseira e ficam mais firmes a cada ano que entra."
            if anos_fechados < 2 else None
        ),
    }


async def get_financeiro_NG_previsao(
    *,
    ajuizado_por_ano: Dict[int, float],
    hoje: Optional[date] = None,
    escritorio: str = "NG",
) -> Dict[str, Any]:
    """Section "Previsão": cenários de receita do próximo ano (base inteira, sem filtros)."""
    rows = await _repasses_do_escritorio(escritorio)
    return calcular_previsao_receita(
        rows,
        ajuizado_por_ano=ajuizado_por_ano,
        hoje=hoje,
        ano_inicial=_config_financeiro(escritorio).ano_inicial,
    )


# ---------------------------------------------------------------------------
# Dashboard Financeiro — Modal "Controle de Clientes" (card Clientes Pendentes)
# ---------------------------------------------------------------------------

COLUMN_CLIENTE = "CLIENTE"
CLIENTE_SEM_NOME = "DESCONHECIDO"


async def get_financeiro_NG_clientes_pendentes(
    *,
    anos: Optional[List[str]] = None,
    meses: Optional[List[int]] = None,
    origens: Optional[List[str]] = None,
    materias: Optional[List[str]] = None,
    anos_ajuizamento: Optional[List[str]] = None,
    escritorio: str = "NG",
) -> Dict[str, Any]:
    """Detalhe do card Clientes Pendentes (réplica do "Controle de Clientes" do
    Power BI): linhas com STATUS pendente, `REPASSE DE CLIENTE` somado.

    `valor_fixo` é a foto inteira (igual ao card, ignora ano/mês); `valor_variavel`,
    `quantidade` e os gráficos respeitam os seletores de ano/mês da DATA DO TED
    ("(Em branco)" = sem TED). Os filtros de Origem/Matéria/Ano de Ajuizamento da
    página se aplicam a tudo, como no card.
    """
    status_pendente = _config_financeiro(escritorio).status_pendente
    rows_todas = await _repasses_do_escritorio(escritorio)
    rows = _filtrar_rows_reflexo(
        rows_todas, origens=origens, materias=materias, anos_ajuizamento=anos_ajuizamento
    )
    pendentes = [
        r for r in rows
        if str(r.get(COLUMN_STATUS) or "").strip().upper() in status_pendente
    ]
    alvo_anos  = {str(a).strip() for a in (anos or []) if str(a).strip()}
    alvo_meses = {int(m) for m in (meses or [])}

    valor_fixo = sum((_parse_money(r.get(COLUMN_REPASSE_CLIENTE)) for r in pendentes), Decimal("0"))
    opcoes_anos: set = set()
    valor = Decimal("0")
    linhas = 0
    clientes: set = set()
    por_status: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"quantidade": 0, "valor": Decimal("0")})
    por_cliente: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"quantidade": 0, "valor": Decimal("0")})
    for r in pendentes:
        d = _parse_date(r.get(COLUMN_DATA_TED))
        ano = _ano_label(d)
        opcoes_anos.add(ano)
        if alvo_anos and ano not in alvo_anos:
            continue
        # Mês só filtra linhas com data (sem TED não tem mês).
        if alvo_meses and (d is None or d.month not in alvo_meses):
            continue
        repasse = _parse_money(r.get(COLUMN_REPASSE_CLIENTE))
        nome = str(r.get(COLUMN_CLIENTE) or "").strip().upper() or CLIENTE_SEM_NOME
        linhas += 1
        valor += repasse
        clientes.add(nome)
        status = por_status[str(r.get(COLUMN_STATUS) or "").strip().upper()]
        status["quantidade"] += 1
        status["valor"]      += repasse
        cliente = por_cliente[nome]
        cliente["quantidade"] += 1
        cliente["valor"]      += repasse

    def _barras(por: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {"name": nome, "value": _decimal_to_float_2(v["valor"]), "quantidade": v["quantidade"]}
            for nome, v in sorted(por.items(), key=lambda kv: kv[1]["valor"], reverse=True)
            if v["valor"] > 0
        ]

    return {
        "valor_fixo":     _decimal_to_float_2(valor_fixo),
        "valor_variavel": _decimal_to_float_2(valor),
        # Igual ao Power BI: conta linhas (TEDs pendentes), não nomes distintos.
        "quantidade":     linhas,
        "quantidade_clientes": len(clientes),
        "por_status":     _barras(por_status),
        "por_cliente":    _barras(por_cliente),
        "anos_opcoes":    _ordenar_anos(opcoes_anos),
    }
