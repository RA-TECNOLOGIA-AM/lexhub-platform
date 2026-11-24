"""app.analyses.common.conversao e .periodo: conversões e regras de período comuns das análises."""

from datetime import UTC, date, datetime
from decimal import Decimal

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.common import conversao, periodo

NOV = (date(2026, 11, 1), date(2026, 11, 30))


def test_para_data():
    assert conversao.para_data("2026-11-05") == date(2026, 11, 5)
    assert conversao.para_data(datetime(2026, 11, 5, 10)) == date(2026, 11, 5)
    # 23h em UTC já é o dia seguinte em UTC, mas ainda o dia 5 em Manaus
    assert conversao.para_data(datetime(2026, 11, 6, 2, tzinfo=UTC)) == date(2026, 11, 5)
    assert conversao.para_data("") is None
    assert conversao.para_data(None) is None
    assert conversao.para_data("lixo") is None


def test_para_inteiro():
    assert conversao.para_inteiro("21") == 21
    assert conversao.para_inteiro(21) == 21
    assert conversao.para_inteiro("") is None
    assert conversao.para_inteiro("21.0") is None  # int("21.0") falha, como na v1
    assert conversao.para_inteiro(None) is None


def test_para_valor_pt_br():
    assert conversao.para_valor("R$ 1.234,56") == 1234.56
    assert conversao.para_valor("470,00") == 470.0
    assert conversao.para_valor("470.00") == 470.0
    assert conversao.para_valor(Decimal("10.5")) == 10.5
    assert conversao.para_valor("1 234,56") == 1234.56
    assert conversao.para_valor("1 234,56", remover_nbsp=False) == 0.0
    assert conversao.para_valor(None) == 0.0
    assert conversao.para_valor("abc") == 0.0


def test_para_valor_digitos_como_na_v1():
    assert conversao.para_valor_digitos("470,50") == 470.5
    assert conversao.para_valor_digitos("R$ 99") == 99.0
    # milhar em texto (na v1 virava 0)
    assert conversao.para_valor_digitos("1.234,56") == 1234.56
    assert conversao.para_valor_digitos("R$ 1.234.567,89") == 1234567.89
    assert conversao.para_valor_digitos("1.234.567") == 1234567.0
    # formato gravado hoje pelo LexFlow: igual a antes
    assert conversao.para_valor_digitos("1234.56") == 1234.56
    assert conversao.para_valor_digitos(Decimal("1234.56")) == 1234.56


def test_periodo():
    assert periodo.no_periodo(date(2026, 11, 30), *NOV)
    assert not periodo.no_periodo(None, None, None)
    assert periodo.resolver_intervalo(date(2026, 11, 1), None)[1] == date.today()
    assert periodo.resolver_intervalo(None, None) == (None, None)
    linhas = [
        {"A": "2026-10-01", "b": "2026-11-10"},  # a 2ª coluna em minúsculas está no período
        {"A": "2026-10-01", "B": None},
        {"A": "2026-11-02"},
    ]
    filtradas = periodo.filtrar_por_colunas(linhas, ["A", "B"], *NOV, para_data=conversao.para_data)
    assert filtradas == [linhas[0], linhas[2]]
    assert (
        periodo.filtrar_por_colunas(linhas, ["A"], None, None, para_data=conversao.para_data)
        is linhas
    )
    assert periodo.variacao_percentual(15, 10) == 50.0
    assert periodo.variacao_percentual(5, 0) == 0.0
