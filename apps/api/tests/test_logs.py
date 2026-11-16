import io
import logging

from app.logs import TerminalFormatter, configure_logging, scope_of, seconds


def test_escopo_curto_por_logger():
    assert scope_of("app.database") == "bancos"
    assert scope_of("app.analyses.v1_dashboard_generico") == "cálculo"
    assert scope_of("app.requests") == "http"
    assert scope_of("uvicorn.error") == "uvicorn"
    assert scope_of("algo.desconhecido") == "desconhecido"


def test_duracao_legivel():
    assert seconds(0.084) == "0,08s"
    assert seconds(1.42) == "1,4s"
    assert seconds(30.0) == "30s"
    assert seconds(125) == "2min 05s"
    assert seconds(300) == "5min"


def test_formato_sem_cor_tem_hora_nivel_escopo_e_mensagem():
    record = logging.LogRecord(
        "app.database", logging.WARNING, __file__, 1, "ng: %s", ("caiu",), None
    )
    line = TerminalFormatter(color=False).format(record)
    assert "\033[" not in line
    assert "AVISO" in line and "bancos" in line and line.endswith("ng: caiu")


def test_configurar_de_novo_nao_duplica_o_handler():
    stream = io.StringIO()
    configure_logging("INFO", stream=stream)
    configure_logging("DEBUG", stream=stream)
    marked = [h for h in logging.getLogger().handlers if getattr(h, "_lexhub_terminal", False)]
    assert len(marked) == 1
    assert logging.getLogger().level == logging.DEBUG
    assert logging.getLogger("uvicorn.access").disabled
    configure_logging("INFO")


def _http_lines(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == "app.requests"]


def test_requisicao_sem_login_aparece_como_401(client, caplog):
    caplog.set_level(logging.INFO, logger="app.requests")
    client.get("/me")
    lines = _http_lines(caplog)
    assert any("401" in line and "sessão (login)" in line and "sem login" in line for line in lines)


def test_requisicao_logada_mostra_quem_pediu(client, signer, caplog):
    caplog.set_level(logging.INFO, logger="app.requests")
    client.get("/me", headers={"Authorization": f"Bearer {signer.token()}"})
    assert any("piloto@lexgroup.test" in line for line in _http_lines(caplog))


def test_dashboard_tem_linha_de_carregando_e_de_resultado(client, signer, caplog):
    caplog.set_level(logging.INFO, logger="app.requests")
    client.get(
        "/orgs/lexgroup/units/NG/dashboards/protocolo?from=2026-11-01&to=2026-11-16",
        headers={"Authorization": f"Bearer {signer.token()}"},
    )
    lines = _http_lines(caplog)
    assert any("carregando dashboard protocolo · NG" in line for line in lines)
    assert any("dashboard protocolo · NG (01/11 a 16/11)" in line for line in lines)


def test_health_fica_em_debug(client, caplog):
    caplog.set_level(logging.INFO, logger="app.requests")
    client.get("/health")
    assert _http_lines(caplog) == []
