"""Regras da auditoria de Configurações das Vinculações (espelham o LexFlow)."""
import json

from app.analyses.ADMIN.configuracoes_vinculacoes import montar_configuracoes_vinculacoes


def _vinc(id_, escritorio=20, ativa=True, setor="EXECUÇÃO", atividade=None, escritorio_ativo=True, **config):
    row = {
        "id_vinculacao": id_,
        "id_escritorio_assinante": escritorio,
        "escritorio_ativo": escritorio_ativo,
        "escritorio": {20: "NG", 21: "LAADV AM", 27: "LAADV RJ"}.get(escritorio, "TESTE"),
        "vinculacao_ativa": ativa,
        "setor": setor,
        "atividade": atividade or f"ATIVIDADE {id_}",
    }
    if config:
        row.update(
            {
                "id_configuracao": 1000 + id_,
                "configuracao_ativa": True,
                "id_conf_campos_obrigatorios": 1,
                "regra_cumprido_sem_exigencia": True,
                "regra_nao_cumprido_nenhuma_exigencia": True,
                "fluxo_encerramento_cumprido_apenas_encerrar": True,
                "fluxo_encerramento_nao_cumprido_apenas_encerrar": True,
            }
        )
        row.update(config)
    return row


def _por_id(rows):
    return {r["ID_VINCULACAO"]: r for r in rows}


def _duplo(lista):
    # jsonb gravado como string JSON e devolvido como texto pelo asyncpg
    return json.dumps(json.dumps(lista))


def test_le_encaminhamentos_duplamente_codificados():
    rows = [
        _vinc(1, fluxo_encerramento_cumprido_apenas_encerrar=False,
              fluxo_encerramento_cumprido_encaminhar_agendamento=True,
              encaminhamentos_cumprido_json=_duplo([{"id_setor_atividade": 2, "qtd_dias": 5}])),
        _vinc(2, config_vazia=None),
    ]
    r = _por_id(montar_configuracoes_vinculacoes(rows))[1]
    assert r["FLUXO_CUMPRIDO"]["MODO"] == "encaminha"
    assert [d["ID_VINCULACAO"] for d in r["FLUXO_CUMPRIDO"]["DESTINOS"]] == [2]
    assert r["STATUS"] == "ok"


def test_flag_controladoria_e_a_opcao_encaminhar_do_nao_cumprido():
    rows = [
        _vinc(1, fluxo_encerramento_nao_cumprido_apenas_encerrar=False,
              fluxo_encerramento_nao_cumprido_controladoria=True,
              encaminhamentos_nao_cumprido_json=_duplo([{"id_setor_atividade": 2, "qtd_dias": 1}])),
        _vinc(2, config_vazia=None),
    ]
    fluxo = _por_id(montar_configuracoes_vinculacoes(rows))[1]["FLUXO_NAO_CUMPRIDO"]
    assert fluxo["MODO"] == "encaminha"
    assert "Controladoria" not in json.dumps(fluxo, ensure_ascii=False)
    assert fluxo["DESTINOS"][0]["ID_VINCULACAO"] == 2


def test_encaminhar_sem_destino_fica_incompleta():
    rows = [_vinc(1, fluxo_encerramento_cumprido_apenas_encerrar=False,
                  fluxo_encerramento_cumprido_encaminhar_agendamento=True)]
    r = montar_configuracoes_vinculacoes(rows)[0]
    assert r["STATUS"] == "incompleta"
    assert any(p["TIPO"] == '"Encaminhar" marcado sem destino' for p in r["PROBLEMAS_DETALHE"])


def test_destino_de_outro_escritorio_e_inativo_sao_erro():
    rows = [
        _vinc(1, escritorio=27, fluxo_encerramento_cumprido_apenas_encerrar=False,
              fluxo_encerramento_cumprido_encaminhar_agendamento=True,
              encaminhamentos_cumprido_json=_duplo([{"id_setor_atividade": 2}]),
              fluxo_encerramento_nao_cumprido_apenas_encerrar=False,
              fluxo_encerramento_nao_cumprido_controladoria=True,
              encaminhamentos_nao_cumprido_json=_duplo([{"id_setor_atividade": 3}])),
        _vinc(2, escritorio=20),
        _vinc(3, escritorio=27, ativa=False),
    ]
    r = _por_id(montar_configuracoes_vinculacoes(rows))[1]
    assert r["STATUS"] == "erro"
    tipos = {p["TIPO"] for p in r["PROBLEMAS_DETALHE"]}
    assert "Encaminha para vinculação de outro escritório" in tipos
    assert "Encaminha para vinculação inativa" in tipos


def test_com_motivo_usa_flag_por_lado_e_nao_o_global():
    rows = [
        _vinc(1, encaminhamento_automatico_ativo=False,
              fluxo_encerramento_cumprido_apenas_encerrar=False,
              fluxo_encerramento_cumprido_encaminhamento_com_motivo=True,
              encaminhamentos_automaticos_cumprido_json=json.dumps(
                  [{"id_setor_atividade": 2, "qtd_dias": 1, "motivo": "ACORDO"}])),
        _vinc(2, config_vazia=None),
    ]
    fluxo = _por_id(montar_configuracoes_vinculacoes(rows))[1]["FLUXO_CUMPRIDO"]
    assert fluxo["MODO"] == "encaminha_com_motivo"
    assert fluxo["DESTINOS"][0]["MOTIVO"] == "ACORDO"


def test_apenas_encerrar_tem_precedencia():
    rows = [_vinc(1, fluxo_encerramento_cumprido_apenas_encerrar=True,
                  encaminhamentos_automaticos_cumprido_json=json.dumps(
                      [{"id_setor_atividade": 99, "motivo": "X"}]))]
    r = montar_configuracoes_vinculacoes(rows)[0]
    assert r["FLUXO_CUMPRIDO"]["MODO"] == "encerra"
    assert r["STATUS"] == "ok"


def test_inativa_nao_conta_como_problema_e_situacao_vale_como_gatilho():
    rows = [
        _vinc(1, ativa=False),  # sem configuração, mas inativa
        _vinc(2, trigger_criacao_ativo=True, trigger_criacao_situacao_id=5),
    ]
    por_id = _por_id(montar_configuracoes_vinculacoes(rows))
    assert por_id[1]["STATUS"] == "inativa" and por_id[1]["QTD_PROBLEMAS"] == 0
    assert por_id[2]["STATUS"] == "ok"


def test_gatilho_de_conclusao_por_encaminhamento_substitui_flat():
    slots = [{"kind": "apenas_encerrar", "ativo": True, "fase_id": 8, "fase": "EXECUÇÃO",
              "status_processual_id": None, "subfase": None}]
    rows = [_vinc(1, trigger_conclusao_ativo=True, triggers_conclusao_slots=json.dumps(slots))]
    r = montar_configuracoes_vinculacoes(rows)[0]
    assert r["STATUS"] == "ok"
    assert r["FASE_CONCLUSAO"] == "EXECUÇÃO"


def test_escritorio_vem_da_tabela_e_inativo_fica_de_fora():
    rows = [
        _vinc(1, escritorio=99, config_vazia=None),  # escritório novo, ativo
        _vinc(2, escritorio=21, escritorio_ativo=False, config_vazia=None),
    ]
    ids = {r["ID_VINCULACAO"] for r in montar_configuracoes_vinculacoes(rows)}
    assert ids == {1}


def test_campo_novo_do_lexflow_aparece_automaticamente():
    completa = {
        "id": 1, "ativo": True, "regra_cumprido_sem_exigencia": True,
        "herdar_prazo_fatal": True,
        "trigger_movimentacao_ativo": False, "trigger_movimentacao_qualquer_evento": True,
        "campo_inventado_amanha": "valor X",
        "nova_regra_ativo": False, "nova_regra_prazo": 5,
    }
    rows = [_vinc(1, configuracao_completa=json.dumps(completa))]
    outras = {o["CAMPO"]: o for o in montar_configuracoes_vinculacoes(rows)[0]["OUTRAS_CONFIGURACOES"]}
    assert set(outras) == {"herdar_prazo_fatal", "campo_inventado_amanha"}
    assert outras["herdar_prazo_fatal"]["CONHECIDO"] is True
    assert outras["campo_inventado_amanha"]["CONHECIDO"] is False
    assert outras["campo_inventado_amanha"]["VALOR"] == "valor X"


def test_slots_do_nao_cumprido_ficam_separados_do_cumprido():
    # Ticket 871 do LexFlow: slot com fluxo=nao_cumprido; slot legado sem fluxo = cumprido.
    slots = [
        {"kind": "apenas_encerrar", "ativo": True, "fase_id": 8, "fase": "EXECUÇÃO",
         "status_processual_id": None, "subfase": None},
        {"kind": "apenas_encerrar", "fluxo": "nao_cumprido", "ativo": True, "fase_id": 9, "fase": "RECURSAL",
         "status_processual_id": None, "subfase": None},
    ]
    rows = [_vinc(1, trigger_conclusao_ativo=True, trigger_conclusao_fase_id=8, fase_conclusao="EXECUÇÃO",
                  triggers_conclusao_slots=json.dumps(slots))]
    r = montar_configuracoes_vinculacoes(rows)[0]
    assert r["STATUS"] == "ok"
    assert r["FASE_CONCLUSAO"] == "EXECUÇÃO"
    assert r["GATILHO_ENCERRAMENTO_NAO_CUMPRIDO"]["ORIGEM"] == "slots"
    assert r["GATILHO_ENCERRAMENTO_NAO_CUMPRIDO"]["FASE"] == "RECURSAL"
    assert [g["FLUXO"] for g in r["GATILHOS_CONCLUSAO_POR_ENCAMINHAMENTO"]] == ["cumprido", "nao_cumprido"]


def test_nao_cumprido_sem_slot_ativo_herda_o_flat_e_e_erro():
    slots = [{"kind": "apenas_encerrar", "ativo": True, "fase_id": 8, "fase": "EXECUÇÃO",
              "status_processual_id": None, "subfase": None}]
    rows = [_vinc(1, trigger_conclusao_ativo=True, trigger_conclusao_fase_id=8, fase_conclusao="EXECUÇÃO",
                  triggers_conclusao_slots=json.dumps(slots))]
    r = montar_configuracoes_vinculacoes(rows)[0]
    assert r["STATUS"] == "erro"
    assert r["GATILHO_ENCERRAMENTO_NAO_CUMPRIDO"]["ORIGEM"] == "flat"
    assert r["GATILHO_ENCERRAMENTO_NAO_CUMPRIDO"]["FASE"] == "EXECUÇÃO"
    assert [p["TIPO"] for p in r["PROBLEMAS_DETALHE"]] == ["Não cumprido herda o gatilho de encerramento do cumprido"]


def test_slot_orfao_compara_com_o_fluxo_do_proprio_slot():
    slots = [{"kind": "encaminhamento", "fluxo": "nao_cumprido", "id_setor_atividade": 2, "ativo": True,
              "fase_id": 8, "fase": "EXECUÇÃO", "status_processual_id": None, "subfase": None}]
    rows = [
        _vinc(1, fluxo_encerramento_nao_cumprido_apenas_encerrar=False,
              fluxo_encerramento_nao_cumprido_controladoria=True,
              encaminhamentos_nao_cumprido_json=_duplo([{"id_setor_atividade": 2, "qtd_dias": 1}]),
              triggers_conclusao_slots=json.dumps(slots)),
        _vinc(2, config_vazia=None),
    ]
    r = _por_id(montar_configuracoes_vinculacoes(rows))[1]
    assert r["STATUS"] == "ok", r["PROBLEMAS"]
