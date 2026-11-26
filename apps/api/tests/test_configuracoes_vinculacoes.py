"""Configurações das Vinculações: a auditoria da v1 (query e cálculo copiados), só com o escritório da unidade."""

import asyncio
from datetime import date

import pytest

from app.dashboards import DASHBOARDS
from app.dashboards import configuracoes_vinculacoes as m
from app.dashboards.base import DashboardContext, NotReady, Period
from app.source_queries import QUERIES


class Fonte:
    def __init__(self, rows):
        self.rows = rows
        self.pedidas = []

    async def fetch(self, name):
        self.pedidas.append(name)
        return self.rows


def _vinc(id_, escritorio=20, ativa=True, setor="EXECUÇÃO", **config):
    row = {
        "id_vinculacao": id_,
        "id_escritorio_assinante": escritorio,
        "escritorio_ativo": True,
        "escritorio": {20: "NG", 21: "LAADV AM", 27: "LAADV RJ"}.get(escritorio, "TESTE"),
        "vinculacao_ativa": ativa,
        "setor": setor,
        "atividade": f"ATIVIDADE {id_}",
        "id_configuracao": 1000 + id_,
        "configuracao_ativa": True,
        "id_conf_campos_obrigatorios": 1,
        "regra_cumprido_sem_exigencia": True,
        "regra_nao_cumprido_nenhuma_exigencia": True,
        "fluxo_encerramento_cumprido_apenas_encerrar": True,
        "fluxo_encerramento_nao_cumprido_apenas_encerrar": True,
    }
    row.update(config)
    return row


def _ctx(fonte, unit_ref="NG", **filters):
    return DashboardContext(
        source=fonte,
        unit_ref=unit_ref,
        period=Period(date(2026, 11, 1), date(2026, 11, 26)),
        filters={k: [v] for k, v in filters.items()},
        can_see_commission=True,
    )


def test_registrado_no_lexflow_com_a_query_da_v1():
    assert DASHBOARDS["configuracoes-vinculacoes"] is m.MODULE
    assert QUERIES[m.QUERY]["database"] == "lexflow"
    assert m.MODULE.queries == (m.QUERY,)


def test_so_ng_la_e_rj():
    with pytest.raises(NotReady):
        asyncio.run(m.build(_ctx(Fonte([]), "LEXPRE")))


def test_cada_unidade_ve_so_o_proprio_escritorio():
    fonte = Fonte([_vinc(1, 20), _vinc(2, 21), _vinc(3, 27), _vinc(4, 99)])
    for unit, id_ in (("NG", 1), ("LA", 2), ("RJ", 3)):
        body = asyncio.run(m.build(_ctx(fonte, unit)))
        assert [r["ID_VINCULACAO"] for r in body["rows"]] == [id_]
        assert body["total"] == 1
    assert fonte.pedidas == [m.QUERY] * 3


def test_encaminhar_para_outro_escritorio_e_erro_mesmo_recortado():
    # O destino (vinculação 2) é do LA: a NG só vê a 1, mas o cálculo precisa da 2 para dizer que é de outro escritório.
    rows = [
        _vinc(
            1,
            20,
            fluxo_encerramento_cumprido_apenas_encerrar=False,
            fluxo_encerramento_cumprido_encaminhar_agendamento=True,
            encaminhamentos_cumprido_json='[{"id_setor_atividade": 2}]',
        ),
        _vinc(2, 21),
    ]
    body = asyncio.run(m.build(_ctx(Fonte(rows), "NG")))
    (r,) = body["rows"]
    assert r["STATUS"] == "erro"
    assert body["total_com_problemas"] == 1
    assert any(
        p["TIPO"] == "Encaminha para vinculação de outro escritório" for p in r["PROBLEMAS_DETALHE"]
    )


def test_campos_novos_do_lexflow():
    rows = [
        _vinc(1, configuracao_completa={"coluna_nova_lexflow": True, "herdar_prazo_fatal": True})
    ]
    body = asyncio.run(m.build(_ctx(Fonte(rows))))
    assert body["campos_nao_reconhecidos"] == ["coluna_nova_lexflow"]


def test_export_segue_os_filtros_da_tela():
    rows = [
        _vinc(1, setor="EXECUÇÃO"),
        _vinc(2, setor="RECURSOS", id_conf_campos_obrigatorios=None),  # falta configurar
        _vinc(3, setor="RECURSOS", ativa=False),  # inativa: fora do padrão (as ativas)
    ]
    fonte = Fonte(rows)
    todas = asyncio.run(m.export_rows(_ctx(fonte)))
    assert [r["atividade"] for r in todas] == [
        "ATIVIDADE 2",
        "ATIVIDADE 1",
    ]  # erro/incompleta primeiro (v1)
    assert set(todas[0]) == {slug for slug, _ in m.COLUNAS}
    assert todas[0]["status"] == "Falta configurar"
    assert todas[0]["regra_cumprido"] == "sem exigência"

    recursos = asyncio.run(
        m.export_rows(_ctx(fonte, setor_vinculacao="RECURSOS", status_vinculacao="todas"))
    )
    assert [r["atividade"] for r in recursos] == ["ATIVIDADE 2", "ATIVIDADE 3"]

    problema = asyncio.run(
        m.export_rows(
            _ctx(fonte, problema_vinculacao="Nenhum conjunto de campos obrigatórios vinculado")
        )
    )
    assert [r["atividade"] for r in problema] == ["ATIVIDADE 2"]

    ok = asyncio.run(m.export_rows(_ctx(fonte, status_vinculacao="ok")))
    assert [r["atividade"] for r in ok] == ["ATIVIDADE 1"]
