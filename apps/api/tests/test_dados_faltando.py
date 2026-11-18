"""O relatório da faixa "Atenção" nos Julgados (Acórdãos e Sentenças): os itens do modal, uma aba por campo."""

import asyncio
import io
from datetime import date

import pytest
from openpyxl import load_workbook

from app.dashboards import DASHBOARDS, dados_faltando, export
from app.dashboards import julgados_acordaos as ja
from app.dashboards import julgados_sentencas as js
from app.dashboards.base import DashboardContext, Period


def _ctx(unit_ref="LA", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters=filters,
        can_see_commission=True,
    )


def test_enriquecer_com_materia_comarca_e_uf():
    processos = [
        {"NUMERO_PROCESSO": "1", "MATERIA": "RMC", "COMARCA": "MANAUS", "UF": "am"},
        {"NUMERO_PROCESSO": "1", "MATERIA": "OUTRA"},
    ]
    itens = [{"numero_processo": "1", "campo": "Relator"}, {"numero_processo": "9", "campo": "UF"}]
    assert dados_faltando.enriquecer(itens, processos) == [
        {
            "numero_processo": "1",
            "materia": "RMC",
            "comarca": "MANAUS",
            "uf": "AM",
            "campo": "Relator",
        },
        {"numero_processo": "9", "materia": "", "comarca": "", "uf": "", "campo": "UF"},
    ]


@pytest.mark.parametrize("key", ["julgados-acordaos", "julgados-sentencas", "execucao"])
def test_relatorio_em_todos_os_dashs_com_a_faixa(key):
    spec = DASHBOARDS[key].export_reports[dados_faltando.RELATORIO]
    assert spec.sheet_by == "campo"


@pytest.mark.parametrize("mod", [ja, js])
def test_linhas_sao_as_da_faixa_da_v1_sem_periodo(monkeypatch, mod):
    chamadas = []

    async def processos(ctx):
        return [{"NUMERO_PROCESSO": "7", "MATERIA": "CESTA", "COMARCA": "TEFÉ", "UF": "AM"}]

    def faixa(rows, from_date, to_date):
        chamadas.append((len(rows), from_date, to_date))
        return [{"numero_processo": "7", "campo": "Matéria"}]

    monkeypatch.setattr(mod, "_processos", processos)
    monkeypatch.setitem(mod._DADOS_FALTANDO, "LA", faixa)
    out = asyncio.run(mod.campos_faltando_rows(_ctx()))
    assert chamadas == [(1, None, None)]
    assert out == [
        {
            "numero_processo": "7",
            "materia": "CESTA",
            "comarca": "TEFÉ",
            "uf": "AM",
            "campo": "Matéria",
        }
    ]


def test_abas_com_nome_curto_para_os_campos_longos():
    spec = DASHBOARDS["julgados-acordaos"].export_reports[dados_faltando.RELATORIO]
    linhas = [
        {"numero_processo": "1", "campo": "Mérito do acórdão (data lançada)"},
        {"numero_processo": "2", "campo": "Relator"},
    ]
    wb = load_workbook(io.BytesIO(export.to_xlsx_por_aba(spec, list(spec.fields), linhas, "x")))
    assert [ws.title for ws in wb.worksheets] == ["Relator", "Sem mérito do acórdão"]
    assert [c.value for c in wb["Relator"][1]] == ["Nº Processo", "Matéria", "Comarca", "UF"]
