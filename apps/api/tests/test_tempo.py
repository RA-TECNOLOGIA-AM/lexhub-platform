"""app.analyses.common.tempo: o cálculo comum de tempo médio e mediana entre duas datas (regras da v1)."""

from datetime import date

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.common import periodo, tempo

ENTRADA = tempo.coluna("ENTRADA")
SAIDA = tempo.coluna("SAIDA")


def test_duracoes_em_dias_de_calendario_e_so_maiores_que_zero():
    linhas = [
        {"ENTRADA": "2025-01-01", "SAIDA": "2025-01-11"},  # 10
        {"ENTRADA": "2025-01-05", "SAIDA": "2025-01-05"},  # 0: fica fora
        {"ENTRADA": "2025-01-10", "SAIDA": "2025-01-01"},  # negativo: fora
        {"ENTRADA": None, "SAIDA": "2025-01-01"},  # sem entrada
        {"ENTRADA": "lixo", "SAIDA": "2025-01-01"},  # data inválida
        {"entrada": "2025-02-01", "saida": "2025-02-04"},  # chaves em minúsculas: 3
    ]
    assert tempo.duracoes(linhas, ENTRADA, SAIDA) == [10.0, 3.0]
    assert tempo.duracoes(linhas, ENTRADA, SAIDA, aceita_zero=True) == [10.0, 0.0, 3.0]


def test_periodo_recorta_pela_saida():
    linhas = [
        {"ENTRADA": "2024-12-01", "SAIDA": "2025-01-10"},  # sai em janeiro: entra
        # entrou em janeiro, saiu em fevereiro: fora
        {"ENTRADA": "2025-01-02", "SAIDA": "2025-02-10"},
        {"ENTRADA": "2025-01-02", "SAIDA": None},
    ]
    jan = (date(2025, 1, 1), date(2025, 1, 31))
    assert tempo.duracoes(linhas, ENTRADA, SAIDA, de=jan[0], ate=jan[1]) == [40.0]
    assert tempo.duracoes(linhas, ENTRADA, SAIDA, de=date(2025, 2, 1)) == [39.0]


def test_media_mediana_e_vazio():
    assert tempo.media([10.0, 3.0, 4.0]) == 5.67
    assert tempo.mediana([10.0, 3.0, 4.0]) == 4.0
    assert tempo.mediana([10.0, 3.0, 4.0, 1.0]) == 3.5
    assert tempo.media([]) == 0.0
    assert tempo.mediana([]) == 0.0
    assert tempo.media([], vazio=None) is None


def test_variacao_percentual():
    assert periodo.variacao_percentual(15, 10) == 50.0
    assert periodo.variacao_percentual(5, 10) == -50.0
    assert periodo.variacao_percentual(5, 0) == 0.0
    assert periodo.variacao_percentual(5, 0, sem_base=100.0) == 100.0


def test_unidades_dias_com_fracao_e_horas():
    linhas = [{"E": "2025-01-01T00:00:00", "S": "2025-01-02T12:00:00"}]
    entrada, saida = tempo.coluna("E", com_hora=True), tempo.coluna("S", com_hora=True)
    assert tempo.duracoes(linhas, entrada, saida, unidade="dias_fracao") == [1.5]
    assert tempo.duracoes(linhas, entrada, saida, unidade="horas") == [36.0]
    # LexPre: média e mediana em horas, divididas por 24 no fim
    assert tempo.media([36.0, 12.0], divisor=24) == 1.0
    assert tempo.mediana([36.0], divisor=24) == 1.5


def test_periodo_por_outra_leitura_da_data():
    # Controle de Processos: a duração usa data e hora; o período, só a data da saída
    linhas = [{"E": "2025-01-01T10:00:00", "S": "2025-01-31T22:00:00"}]
    entrada, saida = tempo.coluna("E", com_hora=True), tempo.coluna("S", com_hora=True)
    jan = {"de": date(2025, 1, 1), "ate": date(2025, 1, 31)}
    assert tempo.duracoes(
        linhas, entrada, saida, data_periodo=tempo.coluna("S"), unidade="dias_fracao", **jan
    ) == [30.5]


def test_duracoes_por_grupo():
    linhas = [
        {"ENTRADA": "2025-01-01", "SAIDA": "2025-01-11", "C": "A"},
        {"ENTRADA": "2025-01-01", "SAIDA": "2025-01-05", "C": "B"},
        {"ENTRADA": "2025-01-01", "SAIDA": "2025-01-03", "C": "A"},
        {"ENTRADA": "2025-01-01", "SAIDA": "2025-01-09", "C": None},  # None é um grupo
        {"ENTRADA": "2025-01-01", "SAIDA": "2025-01-20", "C": "X"},  # FORA: fica de fora
    ]
    grupos = tempo.duracoes_por_grupo(
        linhas, ENTRADA, SAIDA, lambda p, _saida: tempo.FORA if p["C"] == "X" else p["C"]
    )
    assert grupos == {"A": [10.0, 2.0], "B": [4.0], None: [8.0]}
    meses = tempo.duracoes_por_grupo(linhas, ENTRADA, SAIDA, lambda _p, saida: saida.month)
    assert meses == {1: [10.0, 4.0, 2.0, 8.0, 19.0]}


def test_variacao_sem_base_so_com_valor_atual():
    assert periodo.variacao_percentual(0, 0, sem_base=100.0) == 0.0
    assert periodo.variacao_percentual(3, None) == 0.0
