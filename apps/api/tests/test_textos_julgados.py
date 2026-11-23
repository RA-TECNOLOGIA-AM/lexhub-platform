"""app.analyses.common.textos e .julgados: nomes, rótulos e leitores comuns."""

from datetime import date

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.common import julgados, textos


def test_rotulos():
    assert textos.rotulo("  Manaus ", "Sem comarca") == "Manaus"
    assert textos.rotulo("   ", "Sem comarca") == "Sem comarca"
    assert textos.rotulo(0, "Sem comarca") == "0"
    assert textos.texto_ou(0, "Sem matéria") == "Sem matéria"
    assert textos.materia("CESTA - Tarifa") == "CESTA"
    assert textos.materia(None) == "Sem materia"


def test_nomes():
    assert textos.primeiros_nomes("ana maria souza", 2) == "ana maria"
    assert textos.primeiros_nomes("ana maria souza", 2, maiusculas=True) == "ANA MARIA"
    assert (
        textos.primeiros_nomes("Sem funcionario", 2, ignorar="Sem funcionario") == "Sem funcionario"
    )
    assert textos.primeiros_nomes("", 2) == ""
    assert textos.primeiros_nomes_ou("   ", 1, "Sem atendente") == "Sem atendente"
    assert textos.primeiros_nomes_ou("Bruno Lima", 1, "Sem atendente") == "Bruno"
    assert textos.iniciais_nome("Ana Souza") == "AS"
    assert textos.iniciais_nome("ana") == "AN"
    assert textos.iniciais_nome("") == "—"


def test_julgados_base_e_leitores():
    linhas = [
        {
            "ID_ESCRITORIO": 20,
            "NUMERO_PROCESSO": "0001234-11.2025.8.04.0001",
            "COMARCA": " Manaus ",
        },
        {"ID_ESCRITORIO": 21, "NUMERO_PROCESSO": "0001235-11.2025.8.04.0001", "COMARCA": None},
    ]
    assert julgados.base(linhas, 20) == [linhas[0]]
    assert julgados.base(linhas, 21) == [linhas[1]]
    assert julgados.comarca(linhas[1]) == "Sem comarca"
    assert julgados.data_ajuizamento({"DATA_AJUIZAMENTO": "2025-03-10"}) == date(2025, 3, 10)
    assert julgados.ano_ajuizamento({}) == "Sem data de ajuizamento"
