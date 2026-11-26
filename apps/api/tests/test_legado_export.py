"""Exportação do Protocolo, Peticionamento, Org. de Documentos e Pendências (banco legado), como na v1."""

import asyncio
from datetime import date

import pytest

# isort: off
# app.dashboards antes da cópia da v1: carrega app.sources sem import circular
from app.dashboards import DASHBOARDS
from app.analyses import v1_legado_export as v1

# isort: on
from app.dashboards.base import DashboardContext, Period
from app.dashboards.export import pick_report

# dashboard -> (prefixo dos campos na v1, aba do XLSX)
CASOS = {
    "protocolo": ("PROTOCOLO", "Protocolo"),
    "peticionamento": ("PETICIONAMENTO", "Peticionamento"),
    "org-documentos": ("ORG_DOC", "Org Doc"),
    "pendencias": ("PENDENCIAS", "Pendências"),
}


class _Fonte:
    async def fetch(self, query_name):
        return []


def _ctx(unit_ref, **filters):
    return DashboardContext(
        source=_Fonte(),
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 26)),
        filters=filters,
        can_see_commission=True,
    )


@pytest.mark.parametrize("key", CASOS)
def test_campos_e_aba_da_v1_por_unidade(key):
    prefixo, aba = CASOS[key]
    module = DASHBOARDS[key]
    for unit in ("NG", "RJ"):
        spec = pick_report(module, None, unit)
        assert spec.fields == getattr(v1, f"_CAMPOS_EXPORT_{prefixo}_NG")
        assert spec.labels == getattr(v1, f"_LABELS_EXPORT_{prefixo}_NG")
        assert spec.sheet_name == aba
    la = pick_report(module, None, "LA")
    assert la.fields == getattr(v1, f"_CAMPOS_EXPORT_{prefixo}_LA")
    assert la.labels == getattr(v1, f"_LABELS_EXPORT_{prefixo}_LA")
    assert la.sheet_name == f"{aba} LA"


def test_ng_tira_o_rj_e_o_rj_fica_so_com_ele(monkeypatch):
    pedidos = []

    async def linhas(*args, excluir_rj):
        pedidos.append((args, excluir_rj))
        return [{"NOME": "x"}]

    monkeypatch.setattr(v1, "_rows_protocolo_filtradas", linhas)
    spec = DASHBOARDS["protocolo"].export
    filtros = {
        "materia": ["Bancário"],
        "funcionario": ["Ana"],
        "sistema": ["PJe"],
        "uf_protocolo": ["AM"],
    }
    assert asyncio.run(spec.rows(_ctx("NG", **filtros))) == [{"NOME": "x"}]
    asyncio.run(spec.rows(_ctx("RJ")))
    (args_ng, excluir_ng), (args_rj, excluir_rj) = pedidos
    de, ate = date(2026, 11, 1), date(2026, 11, 26)
    # sistema é um valor só na rota da v1; os outros, listas; sem filtro = None
    assert args_ng == (de, ate, ["Bancário"], ["Ana"], "PJe", ["AM"], None) and excluir_ng is True
    assert args_rj == (de, ate, None, None, None, None, None) and excluir_rj is False


def test_la_usa_a_rota_da_la(monkeypatch):
    pedidos = []

    async def linhas(*args):
        pedidos.append(args)
        return []

    monkeypatch.setattr(v1, "_rows_pendencias_la_filtradas", linhas)
    spec = pick_report(DASHBOARDS["pendencias"], None, "LA")
    asyncio.run(
        spec.rows(_ctx("LA", funcionario=["Bia"], uf_pendencia_LA=["AM"], area_atuacao_id=[3]))
    )
    assert pedidos == [(date(2026, 11, 1), date(2026, 11, 26), ["Bia"], "AM", [3])]
