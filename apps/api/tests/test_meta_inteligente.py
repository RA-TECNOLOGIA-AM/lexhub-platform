"""Meta inteligente (cópia da v1): média ponderada, tendência, classificação e distribuição da meta."""

from app.analyses.NG.ml.meta_inteligente import (
    _calcular_tendencia_linear,
    _classificar_tendencia,
    _media_movel_ponderada,
    calcular_meta_inteligente_por_atendente,
)


def reg(atendente, data, valor):
    """Uma demanda protocolada no formato de get_registros_para_meta_inteligente."""
    return {"ATENDENTE": atendente, "SAIDA": data, "VALOR_DA_CAUSA": valor}


def test_media_ponderada_pesa_mais_os_meses_recentes():
    assert _media_movel_ponderada([100.0, 200.0, 300.0]) == (100 + 400 + 900) / 6
    assert _media_movel_ponderada([]) == 0.0


def test_tendencia_linear_e_classificacao():
    assert _calcular_tendencia_linear([100.0, 200.0, 300.0]) == 100.0
    assert _calcular_tendencia_linear([5.0]) == 0.0
    assert _classificar_tendencia(15.0, 100.0) == "crescimento forte"
    assert _classificar_tendencia(-4.0, 100.0) == "queda moderada"
    assert _classificar_tendencia(1.0, 100.0) == "estável"
    assert _classificar_tendencia(10.0, 0.0) == "estável"


def test_meta_por_atendente_com_tendencia_stretch_e_meta_global():
    registros = [
        reg("Ana", "2026-09-10", 100_000),
        reg("Ana", "2026-10-10", 200_000),
        reg("Ana", "2026-11-10", 300_000),
        reg("Bia", "2026-10-05", 50_000),
        reg("Bia", "2026-11-05", 50_000),
        reg("Caio", "2026-11-01", 999_999),  # 1 mês só: sem meta confiável
    ]
    out = calcular_meta_inteligente_por_atendente(
        registros, meses_historico=3, meta_global_periodo=1_000_000
    )
    nomes = [a["atendente"] for a in out["atendentes"]]
    assert nomes == ["Ana", "Bia"]  # maior média ponderada primeiro; Caio fora
    ana = out["atendentes"][0]
    assert ana["media_ponderada"] == round((100_000 + 400_000 + 900_000) / 6, 2)
    assert ana["tendencia_label"] == "crescimento forte"
    assert ana["projecao_proximo_mes"] == round(ana["media_ponderada"] + 100_000, 2)
    assert abs(ana["meta_sugerida"] - ana["projecao_proximo_mes"] * 1.10) < 0.02  # projeção + 10%
    assert round(sum(a["percentual_da_equipe"] for a in out["atendentes"])) == 100
    # A meta global é repartida pela participação: as partes somam a meta toda.
    assert abs(sum(a["meta_proporcional"] for a in out["atendentes"]) - 1_000_000) < 1
    assert out["totais"]["meta_total_sugerida"] == round(
        sum(a["meta_sugerida"] for a in out["atendentes"]), 2
    )


def test_sem_registros():
    out = calcular_meta_inteligente_por_atendente([])
    assert out["atendentes"] == [] and out["totais"] == {}
