"""Correções da V2 sobre o cálculo copiado da v1: séries mês a mês em ordem cronológica e o comparativo de
tempo do Controle de Processos com o período atual resolvido como o anterior."""

from datetime import date, timedelta

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.LA import controle_processo_LA as la
from app.analyses.NG import controle_processo_NG as ng
from app.analyses.NG import execucao
from app.utils import _shift_months, ordem_mes


def test_ordem_mes_e_cronologica():
    nomes = ["ago 2025", "abr 2025", "jan 2026", "jan 2025", "dez 2024"]
    ordenados = [i["name"] for i in sorted(({"name": n} for n in nomes), key=ordem_mes)]
    assert ordenados == ["dez 2024", "jan 2025", "abr 2025", "ago 2025", "jan 2026"]


def test_ordem_mes_nome_fora_do_formato_vai_para_o_fim():
    itens = [{"name": "Sem data"}, {"name": "fev 2025"}, {"name": "jan 2025"}]
    assert [i["name"] for i in sorted(itens, key=ordem_mes)] == ["jan 2025", "fev 2025", "Sem data"]


def _controle(saida: date, dias: int, escritorio: int = 20) -> dict:
    return {
        "ID_ESCRITORIO": escritorio,
        "DATA_AJUIZAMENTO": (saida - timedelta(days=dias)).isoformat(),
        "DT_SAIDA_INICIAL": saida.isoformat(),
    }


def test_serie_mensal_do_controle_em_ordem_cronologica():
    linhas = [
        _controle(date(2025, 8, 10), 30),
        _controle(date(2025, 4, 10), 20),
        _controle(date(2025, 1, 10), 10),
    ]
    serie = ng.get_media_tempo_dias_fase_inicial_por_mes_NG(linhas)
    assert [p["name"] for p in serie] == ["jan 2025", "abr 2025", "ago 2025"]
    assert [p["value"] for p in serie] == [10.0, 20.0, 30.0]


def test_series_mensais_da_execucao_em_ordem_cronologica():
    # Nenhuma série "por mês" das análises fica em ordem alfabética (verificação pelo código-fonte).
    import inspect

    for nome, fn in inspect.getmembers(execucao, inspect.isfunction):
        if "por_mes" in nome and fn.__module__ == execucao.__name__:
            assert 'key=lambda x: x["name"]' not in inspect.getsource(fn), nome


def _comparativo_sem_periodo(mod, sufixo: str, escritorio: int):
    hoje = date.today()
    este_mes = hoje.replace(day=1)
    mes_passado = _shift_months(este_mes, -1)
    linhas = [
        _controle(este_mes, 10, escritorio),  # no mês corrente
        _controle(mes_passado, 5, escritorio),  # no mesmo recorte do mês anterior
        # histórico antigo: fica fora dos dois períodos
        _controle(date(2020, 3, 1), 1000, escritorio),
    ]
    media = getattr(mod, f"get_comparativo_media_tempo_dias_fase_inicial_{sufixo}")
    mediana = getattr(mod, f"get_comparativo_mediana_tempo_dias_fase_inicial_{sufixo}")
    # atual = 10 dias (só o mês corrente), anterior = 5 dias: +100%. Na v1, o atual sem período era o histórico
    # inteiro (média de 10, 5 e 1000 dias).
    assert media(linhas) == 100.0
    assert mediana(linhas) == 100.0
    # Com período, nada muda: o resolver devolve o próprio período.
    assert media(linhas, from_date=este_mes, to_date=hoje) == 100.0


def test_comparativo_do_controle_sem_periodo_usa_o_mes_corrente_ng():
    _comparativo_sem_periodo(ng, "NG", 20)


def test_comparativo_do_controle_sem_periodo_usa_o_mes_corrente_la():
    _comparativo_sem_periodo(la, "LA", 21)
