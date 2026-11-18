"""Execução: os processos em execução com campo do cadastro em branco (a faixa "Atenção" e o relatório em XLSX)."""

import asyncio
import io
from datetime import date

from openpyxl import load_workbook

from app.dashboards import DASHBOARDS, execucao, execucao_export, export
from app.dashboards import execucao_campos as m
from app.dashboards.base import DashboardContext, Period

COMPLETO = {
    "NUMERO_PROCESSO": "0001",
    "VALOR_EXECUCAO": 10.0,
    "DATA_EXECUCAO": date(2026, 1, 2),
    "DATA_TRANSITO_JULGADO": date(2025, 12, 1),
    "DATA_DISTRIBUICAO": date(2024, 1, 1),
    "VALOR_CAUSA": 1000.0,
    "MATERIA": "RMC",
    "COMARCA": "MANAUS",
    "COMPETENCIA": "Juizado Especial Cível",
    "VARA": "1ª Vara",
    "UF": "AM",
    "SUBFASE": "AG. PAGAMENTO",
}


def _ctx(unit_ref="NG", **filters):
    return DashboardContext(
        source=None,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 18)),
        filters=filters,
        can_see_commission=True,
    )


def test_processo_completo_nao_aparece():
    assert m.itens([COMPLETO]) == []


def test_um_item_por_campo_em_branco_com_o_contexto():
    row = {
        **COMPLETO,
        "NUMERO_PROCESSO": "0002",
        "VALOR_EXECUCAO": None,
        "COMARCA": "  ",
        "VARA": "",
    }
    out = m.itens([row])
    assert [i["campo"] for i in out] == ["Valor da execução", "Comarca", "Vara"]
    assert out[0] == {
        "numero_processo": "0002",
        "materia": "RMC",
        "comarca": "",
        "uf": "AM",
        "subfase": "AG. PAGAMENTO",
        "campo": "Valor da execução",
    }


def test_base_e_o_total_em_execucao_com_os_filtros_e_sem_periodo(monkeypatch):
    pedidos = []

    async def linhas(ctx):
        pedidos.append((ctx.export_options, ctx.filters))
        return [{**COMPLETO, "MATERIA": None}]

    monkeypatch.setattr(execucao_export, "_linhas_execucao", linhas)
    out = asyncio.run(m.lista(_ctx(uf=["AM"])))
    assert out == [{"numero_processo": "0001", "campo": "Matéria"}]
    assert pedidos == [({"criterio": "total"}, {"uf": ["AM"]})]


def test_a_resposta_da_execucao_traz_os_campos_faltando(monkeypatch):
    async def v1(ctx):
        return {"stats": {}}

    async def lista(ctx):
        return [{"numero_processo": "1", "campo": "UF"}]

    monkeypatch.setattr(execucao, "_MODULO", type("M", (), {"build": staticmethod(v1)}))
    monkeypatch.setattr(m, "lista", lista)
    body = asyncio.run(execucao.build(_ctx()))
    assert body[m.CHAVE] == [{"numero_processo": "1", "campo": "UF"}]


def test_relatorio_registrado_na_execucao():
    spec = DASHBOARDS["execucao"].export_reports[m.RELATORIO]
    assert spec is m.RELATORIO_SPEC
    assert spec.sheet_by == "campo" and spec.sheet_order == tuple(n for n, _ in m.CAMPOS)
    assert DASHBOARDS["execucao"].export is execucao_export.EXECUCAO


def test_xlsx_uma_aba_por_campo_na_ordem_e_sem_a_coluna_do_campo():
    linhas = m.itens(
        [
            {**COMPLETO, "NUMERO_PROCESSO": "A", "UF": None},
            {**COMPLETO, "NUMERO_PROCESSO": "B", "VALOR_EXECUCAO": None, "UF": ""},
        ]
    )
    spec = m.RELATORIO_SPEC
    wb = load_workbook(io.BytesIO(export.to_xlsx_por_aba(spec, list(spec.fields), linhas, "x")))
    assert [ws.title for ws in wb.worksheets] == ["Valor da execução", "UF"]
    uf = wb["UF"]
    assert [c.value for c in uf[1]] == ["Nº Processo", "Matéria", "Comarca", "UF", "Subfase"]
    assert [r[0].value for r in uf.iter_rows(min_row=2)] == ["A", "B"]


def test_xlsx_sem_linhas_tem_uma_aba_vazia_e_nomes_validos():
    spec = m.RELATORIO_SPEC
    wb = load_workbook(
        io.BytesIO(export.to_xlsx_por_aba(spec, list(spec.fields), [], "Campos em branco"))
    )
    assert [ws.title for ws in wb.worksheets] == ["Campos em branco"]
    assert export._nome_aba("a/b:c?" + "x" * 40) == ("a-b-c-" + "x" * 40)[:31]
