from app.dashboards.rubricas_reunidas import componentes_por_demanda, rubricas_reunidas

SETOR = 7


def row(
    demanda, materia="RUBRICAS_REUNIDAS", reunida=True, setor_atual=99, cliente="Fulano", status=1
):
    return {
        "ID_DEMANDA": demanda,
        "MATERIA": materia,
        "RUBRICA_REUNIDA": reunida,
        "SETOR_ATUAL_ID": setor_atual,
        "CLIENTE_NOME": cliente,
        "STATUS_DEMANDA_ID": status,
    }


def em_fila(r):
    return r["SETOR_ATUAL_ID"] == SETOR and r["STATUS_DEMANDA_ID"] != 3


def build(rows, resolvidos=(), protocolados=(), componentes=None):
    return rubricas_reunidas(
        rows,
        resolvidos=set(resolvidos),
        protocolados=set(protocolados),
        em_fila=em_fila,
        componentes=componentes or {},
        normalizar=lambda m: str(m).strip().upper(),
    )


def test_componentes_sem_repetir_e_sem_vazio():
    comp = componentes_por_demanda(
        [
            {"DEMANDA_ID": 1, "RUBRICA_ASSOCIADA_NOME": "MORA"},
            {"DEMANDA_ID": 1, "RUBRICA_ASSOCIADA_NOME": "MORA"},
            {"DEMANDA_ID": 1, "RUBRICA_ASSOCIADA_NOME": "CESTA"},
            {"DEMANDA_ID": 2, "RUBRICA_ASSOCIADA_NOME": None},
        ]
    )
    assert comp == {1: ["MORA", "CESTA"]}


def test_resolvidos_e_represados_com_rubricas_mais_nova_primeiro():
    rows = [
        row(4136, setor_atual=SETOR),  # na fila
        row(4204, setor_atual=SETOR),  # na fila
        row(4180),  # saiu no período
        row(4100),  # nem saiu no período nem está na fila: fora
        row(5000, materia="ANP", reunida=False),  # não é pacote: fora
    ]
    out = build(
        rows, resolvidos={4180}, protocolados={4180}, componentes={4204: ["OP_VENCIDAS", "CESTA"]}
    )
    assert [m["materia"] for m in out] == ["RUBRICAS_REUNIDAS"]
    demandas = out[0]["demandas"]
    assert [d["id_demanda"] for d in demandas] == [4204, 4180, 4136]
    assert demandas[0] == {
        "id_demanda": 4204,
        "cliente": "Fulano",
        "situacao": "represado",
        "protocolado": False,
        "rubricas": ["OP_VENCIDAS", "CESTA"],
    }
    assert demandas[1]["situacao"] == "resolvido" and demandas[1]["protocolado"] is True


def test_uma_linha_por_demanda_mesmo_com_varios_eventos():
    rows = [row(1, setor_atual=SETOR), row(1, setor_atual=SETOR), row(1, setor_atual=SETOR)]
    assert len(build(rows)[0]["demandas"]) == 1


def test_cancelada_na_fila_nao_conta_como_represada():
    assert build([row(1, setor_atual=SETOR, status=3)]) == []


def test_uma_entrada_por_pacote():
    rows = [row(1, setor_atual=SETOR), row(2, materia="RUBRICAS_REUNIDAS_IRDR", setor_atual=SETOR)]
    assert [m["materia"] for m in build(rows)] == ["RUBRICAS_REUNIDAS", "RUBRICAS_REUNIDAS_IRDR"]
