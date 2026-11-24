from datetime import date

from app.analyses.NG.comercial_lexpre import STATUS_ASSINADO_ID
from app.analyses.NG.comissao_lexpre import (
    get_desconto_cancelamentos_periodo_anterior,
    listar_demandas_canceladas_desconto,
)

DE = date(2026, 11, 1)
ATE = date(2026, 11, 24)


def demanda(id_demanda, rubrica, valor, assinatura="2026-10-15", atendente="Isabelle Souza", cliente="Maria Lima", reunida=False):
    return {
        "ID_DEMANDA": id_demanda,
        "STATUS_ID": STATUS_ASSINADO_ID,
        "DATA_ASSINATURA": assinatura,
        "ATENDENTE": atendente,
        "CLIENTE": cliente,
        "RUBRICA": rubrica,
        "RUBRICA_REUNIDA": reunida,
        "VALOR_AM": valor,
        "STATUS_DEMANDA_ID": 10,
    }


def cancelada(id_demanda, quando, motivo="Cliente desistiu"):
    return {
        "ID_DEMANDA": id_demanda,
        "DATA_CANCELAMENTO": quando,
        "ESCRITORIO_ID": 1,
        "MOTIVO_CANCELAMENTO": motivo,
    }


def test_lista_materia_dia_e_atendente_das_canceladas_que_geram_desconto():
    rows = [
        demanda(1, "MORA", 13),
        demanda(2, "CESTA", 3, assinatura="2026-11-05", cliente="No período"),  # assinada neste período
        demanda(3, "SEGURO", 1, cliente="Fora"),
    ]
    cancelamentos = [
        cancelada(1, "2026-11-10"),
        cancelada(2, "2026-11-12"),
        cancelada(3, "2026-12-01"),  # cancelada depois do período
    ]
    lista = listar_demandas_canceladas_desconto(rows, cancelamentos, DE, ATE)
    assert lista == [
        {
            "atendente": "Isabelle",
            "materia": "MORA",
            "cliente": "Maria Lima",
            "motivo": "Cliente desistiu",
            "data_cancelamento": "2026-11-10",
            "desconto": 13.0,
        }
    ]
    assert get_desconto_cancelamentos_periodo_anterior(rows, cancelamentos, DE, ATE) == 13.0


def test_pacote_reunido_vira_uma_linha_por_materia():
    rows = [demanda(10, "RUBRICAS_BRADESCO", None, atendente="Ana Paula", cliente="João", reunida=True)]
    lista = listar_demandas_canceladas_desconto(
        rows,
        [cancelada(10, "2026-11-03")],
        DE,
        ATE,
        mapa_reunidas={10: ["SEGURO", "CESTA"]},
        mapa_valor_associada={"SEGURO": 1.0, "CESTA": 3.0},
    )
    assert [(l["materia"], l["desconto"], l["atendente"]) for l in lista] == [
        ("CESTA", 3.0, "Ana"),
        ("SEGURO", 1.0, "Ana"),
    ]
    assert sum(l["desconto"] for l in lista) == get_desconto_cancelamentos_periodo_anterior(
        rows,
        [cancelada(10, "2026-11-03")],
        DE,
        ATE,
        mapa_reunidas={10: ["SEGURO", "CESTA"]},
        mapa_valor_associada={"SEGURO": 1.0, "CESTA": 3.0},
    )


def test_sem_motivo_cadastrado_fica_em_branco():
    rows = [demanda(1, "MORA", 13)]
    lista = listar_demandas_canceladas_desconto(rows, [cancelada(1, "2026-11-10", motivo="")], DE, ATE)
    assert lista[0]["motivo"] == "—"


def test_sem_periodo_nao_lista():
    rows = [demanda(1, "MORA", 13)]
    assert listar_demandas_canceladas_desconto(rows, [cancelada(1, "2026-11-10")], None, None) == []
