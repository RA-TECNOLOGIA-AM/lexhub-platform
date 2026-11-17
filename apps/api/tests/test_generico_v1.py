"""generico_v1: os campos do `historico` (a segunda chamada da página da v1, sem período)."""

import asyncio
from contextvars import ContextVar
from datetime import date
from types import SimpleNamespace

from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, Period

_fonte: ContextVar = ContextVar("fonte_teste")


def _copia():
    """Cópia falsa da v1: um handler que responde diferente com e sem período."""

    async def handler(from_date: date | None = None, to_date: date | None = None):
        com_periodo = from_date is not None
        body = {
            "stats": {"total": 3 if com_periodo else 40, "fila": 1 if com_periodo else 9},
            "por_mes": [{"name": "nov 2026", "value": 3}]
            if com_periodo
            else [{"name": "mar 2025", "value": 37}],
        }
        return SimpleNamespace(model_dump=lambda: body)

    return SimpleNamespace(
        HANDLERS={"rota": handler},
        QUERIES_POR_DASHBOARD={"rota": ()},
        usar_fonte=lambda fonte: _fonte.set(fonte),
        _fonte_ctx=_fonte,
    )


def _rodar(historico: tuple[str, ...]) -> dict:
    modulo = generico_v1.modulo(
        key="teste",
        v1_por_unidade={"NG": "rota"},
        descricao_falta="-",
        copia=_copia(),
        historico=historico,
    )
    ctx = DashboardContext(
        source=None,
        unit_ref="NG",
        period=Period(date(2026, 11, 1), date(2026, 11, 17)),
        filters={},
        can_see_commission=True,
    )
    return asyncio.run(modulo.build(ctx))


def test_historico_troca_o_campo_pelo_do_historico_todo():
    body = _rodar(("stats.fila", "por_mes"))
    assert body["stats"] == {"total": 3, "fila": 9}
    assert body["por_mes"] == [{"name": "mar 2025", "value": 37}]


def test_historico_com_outro_nome_mantem_o_do_periodo():
    """ "destino=origem": o mesmo campo com sentido diferente nas duas chamadas fica com os dois valores."""
    body = _rodar(("stats.total_historico=stats.total",))
    assert body["stats"]["total"] == 3  # entrada no período
    assert body["stats"]["total_historico"] == 40  # total de agora
    assert body["stats"]["fila"] == 1


def test_historico_ignora_campo_que_nao_veio():
    body = _rodar(("stats.nao_existe", "nao_existe"))
    assert "nao_existe" not in body["stats"]
    assert "nao_existe" not in body


def test_nome_na_unidade_segue_as_rotas_da_v1():
    from app.dashboards.generico_v1 import nome_na_unidade as n

    assert n("execucao_resolvidos_por_dia_NG", "LA") == "execucao_resolvidos_por_dia_LA"
    assert n("tre", "RJ") == "tre_RJ"
    assert n("total_valor_execucao_vazio_detalhe", "LA") == "total_valor_execucao_vazio_LA_detalhe"
    assert n("total_valor_alcada_final_vazio_acordos_NG_detalhe", "RJ") == (
        "total_valor_alcada_final_vazio_acordos_RJ_detalhe"
    )
    assert n("tre", "NG") == "tre"


def test_historico_por_unidade():
    from app.dashboards.generico_v1 import historico_por_unidade

    h = historico_por_unidade(("stats.total_historico=stats.total", "por_dia_NG"), ("NG", "LA"))
    assert h["NG"] == ("stats.total_historico=stats.total", "por_dia_NG")
    assert h["LA"] == ("stats.total_historico=stats.total_LA", "por_dia_LA")


def test_historico_dict_vale_por_unidade():
    """Com um dict, cada unidade usa a sua lista; unidade fora do dict não traz nada do histórico."""
    body = _rodar({"NG": ("stats.fila",)})
    assert body["stats"]["fila"] == 9
    assert _rodar({"LA": ("stats.fila",)})["stats"]["fila"] == 1
