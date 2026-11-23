"""app.analyses.common.atividades: as regras comuns das atividades (agendamentos do LexFlow)."""

from datetime import date, timedelta

import app.dashboards  # noqa: F401  (carrega os módulos na ordem certa; evita import circular)
from app.analyses.common import atividades
from app.analyses.common.periodo import no_periodo

HOJE = date(2026, 11, 20)
LEITOR = atividades.Leitor(
    criacao=lambda r: r.get("criacao"),
    conclusao=lambda r: r.get("conclusao"),
    prazo=lambda r: r.get("prazo"),
    status=lambda r: r.get("status"),
    funcionario_encerramento=lambda r: r.get("encerrador"),
)
STATUS = atividades.Status(
    inativo=frozenset({"Cancelado", "Encerrado Cumprido"}),
    em_andamento=frozenset({"Iniciado"}),
    encerrado=frozenset({"Encerrado Cumprido"}),
)
NOV = (date(2026, 11, 1), date(2026, 11, 30))


def tarefa(**kw):
    return {"status": "Iniciado", "criacao": date(2026, 11, 5), "prazo": None, **kw}


def test_no_periodo():
    assert no_periodo(date(2026, 11, 5), *NOV)
    assert not no_periodo(date(2026, 10, 31), *NOV)
    assert no_periodo(date(2026, 1, 1), None, None)
    assert not no_periodo(None, None, None)
    assert no_periodo(date(2026, 12, 1), date(2026, 11, 1), None)


def test_situacao_por_periodo():
    s = atividades.situacao(tarefa(prazo=HOJE - timedelta(days=1)), LEITOR, STATUS, *NOV, ref=HOJE)
    assert s == {"em_andamento": True, "vencida": True, "vence_hoje": False, "concluida": False}
    # vencida conta mesmo criada fora do período; em andamento não
    antiga = tarefa(criacao=date(2026, 1, 1), prazo=HOJE)
    s = atividades.situacao(antiga, LEITOR, STATUS, *NOV, ref=HOJE)
    assert s == {"em_andamento": False, "vencida": False, "vence_hoje": True, "concluida": False}
    fechada = tarefa(status="Encerrado Cumprido", conclusao=date(2026, 11, 10), prazo=HOJE)
    s = atividades.situacao(fechada, LEITOR, STATUS, *NOV, ref=HOJE)
    assert s == {"em_andamento": False, "vencida": False, "vence_hoje": False, "concluida": True}


def test_incluir_na_lista():
    assert atividades.incluir_na_lista(tarefa(), LEITOR, STATUS, *NOV, ref=HOJE)
    antiga_vencida = tarefa(criacao=date(2026, 1, 1), prazo=HOJE - timedelta(days=3))
    assert atividades.incluir_na_lista(antiga_vencida, LEITOR, STATUS, *NOV, ref=HOJE)
    antiga_futura = tarefa(criacao=date(2026, 1, 1), prazo=HOJE + timedelta(days=3))
    assert not atividades.incluir_na_lista(antiga_futura, LEITOR, STATUS, *NOV, ref=HOJE)
    fechada_fora = tarefa(
        criacao=date(2026, 1, 1), status="Encerrado Cumprido", conclusao=date(2026, 10, 1)
    )
    assert not atividades.incluir_na_lista(fechada_fora, LEITOR, STATUS, *NOV, ref=HOJE)


def test_situacao_por_prazo():
    fora = tarefa(prazo=date(2026, 12, 5))
    s = atividades.situacao_por_prazo(fora, LEITOR, STATUS, *NOV, ref=HOJE)
    assert s == dict.fromkeys(("em_andamento", "vencida", "vence_hoje", "concluida"), False)
    assert not atividades.incluir_na_lista_por_prazo(fora, LEITOR, *NOV)
    hoje = tarefa(prazo=HOJE)
    s = atividades.situacao_por_prazo(hoje, LEITOR, STATUS, *NOV, ref=HOJE)
    assert s == {"em_andamento": True, "vencida": False, "vence_hoje": True, "concluida": False}


def test_encerrados_e_media_por_funcionario():
    linhas = [
        tarefa(status="Encerrado Cumprido", conclusao=date(2026, 11, 3), encerrador="Ana"),
        tarefa(status="Encerrado Cumprido", conclusao=date(2026, 11, 3), encerrador="Ana"),
        tarefa(status="Encerrado Cumprido", conclusao=date(2026, 11, 4), encerrador="Ana"),
        tarefa(status="Encerrado Cumprido", conclusao=date(2026, 11, 4), encerrador=None),
        tarefa(status="Encerrado Cumprido", conclusao=date(2026, 10, 4), encerrador="Bia"),
        tarefa(status="Iniciado", conclusao=date(2026, 11, 4)),
    ]
    enc = atividades.encerrados_no_periodo(linhas, LEITOR, STATUS, *NOV)
    assert len(enc) == 4
    com = atividades.encerrados_no_periodo(linhas, LEITOR, STATUS, *NOV, exigir_encerrador=True)
    assert len(com) == 3
    media = atividades.media_concluidas_por_funcionario(
        com, lambda r: r["conclusao"], lambda r: r["encerrador"]
    )
    assert media == [{"name": "Ana", "value": 1.5}]


def test_nome_em_conjunto():
    assert atividades.nome_em_conjunto("Ana", None)
    assert atividades.nome_em_conjunto("ANA", frozenset({"ana"}))
    assert not atividades.nome_em_conjunto("Bia", frozenset({"ana"}))
