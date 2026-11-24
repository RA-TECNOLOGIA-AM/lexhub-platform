"""Acordos: os processos em acordo agora com campo do cadastro em branco (a faixa "Atenção", como na Execução)."""

import asyncio
from datetime import date

from app.dashboards import DASHBOARDS, acordos, execucao_export
from app.dashboards import acordos_campos as m
from app.dashboards.base import DashboardContext, Period

COMPLETO = {
    "NUMERO_PROCESSO": "0001",
    "VALOR_ALCADA_FINAL": 5000.0,
    "DATA_ACORDO_FECHADO": date(2026, 10, 1),
    "DATA_EXECUCAO": date(2026, 10, 5),
    "DATA_DISTRIBUICAO": date(2025, 1, 1),
    "MATERIA": "RMC",
    "COMARCA": "MANAUS",
    "COMPETENCIA": "Juizado Especial Cível",
    "VARA": "1ª Vara",
    "UF": "AM",
    "SUBFASE": "AG. PAGAMENTO ACORDO",
    # Eventos posteriores e negociação: vazios são o normal e não entram no aviso.
    "DATA_ACORDO_HOMOLOGADO": None,
    "DATA_PAGAMENTO_ACORDO": None,
    "DATA_EXPEDICAO_ALVARA_ACORDO": None,
    "VALOR_PROPOSTA_RECEBIDA": None,
}


def _ctx(**filters):
    return DashboardContext(
        source=None,
        unit_ref="NG",
        period=Period(date(2026, 11, 1), date(2026, 11, 24)),
        filters=filters,
        can_see_commission=True,
    )


def test_so_os_campos_do_acordo():
    assert m.execucao_campos.itens([COMPLETO], m.CAMPOS) == []
    row = {**COMPLETO, "VALOR_ALCADA_FINAL": None, "DATA_ACORDO_FECHADO": " ", "VARA": ""}
    campos = [i["campo"] for i in m.execucao_campos.itens([row], m.CAMPOS)]
    assert campos == ["Valor de alçada final", "Data do acordo fechado", "Vara"]


def test_base_e_o_total_em_acordo_com_os_filtros_e_sem_periodo(monkeypatch):
    pedidos = []

    async def linhas(ctx):
        pedidos.append((ctx.export_options, ctx.filters))
        return [{**COMPLETO, "DATA_EXECUCAO": None}]

    monkeypatch.setattr(execucao_export, "_linhas_acordos", linhas)
    assert asyncio.run(m.lista(_ctx(uf=["AM"]))) == [
        {"numero_processo": "0001", "campo": "Data da execução"}
    ]
    assert pedidos == [({"criterio": "total"}, {"uf": ["AM"]})]


def test_a_resposta_dos_acordos_traz_os_campos_faltando(monkeypatch):
    async def v1(ctx):
        return {"stats": {}}

    async def lista(ctx):
        return [{"numero_processo": "1", "campo": "UF"}]

    monkeypatch.setattr(acordos, "_MODULO", type("M", (), {"build": staticmethod(v1)}))
    monkeypatch.setattr(m, "lista", lista)
    body = asyncio.run(acordos.build(_ctx()))
    assert body[m.CHAVE] == [{"numero_processo": "1", "campo": "UF"}]


def test_relatorio_registrado_nos_acordos():
    mod = DASHBOARDS["acordos"]
    spec = mod.export_reports[m.RELATORIO]
    assert spec is m.RELATORIO_SPEC
    assert spec.sheet_by == "campo" and spec.sheet_order == tuple(n for n, _ in m.CAMPOS)
    assert spec.rows is m._linhas
    assert set(mod.export_reports) == {"atividades", m.RELATORIO}
    assert mod.export is execucao_export.ACORDOS
