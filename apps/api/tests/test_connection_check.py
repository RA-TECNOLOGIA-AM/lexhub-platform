import asyncio

import asyncpg

from app.connection_check import DbTarget, check_database

PUBLIC = "8.8.8.8"  # endereço público (não conecta de verdade: a porta e o driver são falsos)


def target(**over) -> DbTarget:
    base = {
        "connector": "postgres",
        "host": PUBLIC,
        "port": 5432,
        "database": "operacao",
        "user": "lexhub_leitura",
        "password": "segredo",
        "ssl": True,
    }
    return DbTarget(**{**base, **over})


async def open_ok(host, port, timeout):
    return None


async def open_closed(host, port, timeout):
    raise ConnectionRefusedError()


class FakeDriver:
    """Banco falso: o que cada etapa devolve ou levanta."""

    def __init__(self, *, login_error=None, peer=(PUBLIC, 5432), tables=None, can_write=False):
        self.login_error = login_error
        self.peer = peer
        self.rows = (
            tables
            if tables is not None
            else [("public.processo", "id", "integer"), ("public.processo", "numero", "text")]
        )
        self.write = can_write
        self.closed = False

    async def connect(self, target, timeout):
        if self.login_error:
            raise self.login_error
        return object()

    def peername(self, conn):
        return self.peer

    async def tables(self, conn):
        return self.rows

    async def sample(self, conn, table):
        return None

    async def can_write(self, conn):
        return self.write

    async def close(self, conn):
        self.closed = True


def run(t, driver, open_port=open_ok, **kw):
    return asyncio.run(check_database(t, driver=driver, open_port=open_port, **kw))


def summary(result):
    return [(c.key, c.ok, c.skipped) for c in result.checks]


def test_tudo_certo_guarda_o_schema_e_fecha_a_conexao():
    driver = FakeDriver()
    r = run(target(), driver)
    assert r.ok and not r.can_write and r.error is None
    assert summary(r) == [
        ("network", True, False),
        ("login", True, False),
        ("read", True, False),
        ("readOnly", True, False),
    ]
    assert r.schema_cache == {"public.processo": [["id", "integer"], ["numero", "text"]]}
    assert r.checks[1].message == "Entrou no banco operacao com SSL"
    assert driver.closed


def test_usuario_que_escreve_e_aviso_nao_erro():
    r = run(target(), FakeDriver(can_write=True))
    assert r.ok and r.can_write
    assert r.checks[3].severity == "warn" and "pode alterar dados" in r.checks[3].message


def test_host_interno_para_na_rede_e_pula_o_resto():
    r = run(target(host="10.0.0.5"), FakeDriver())
    assert not r.ok
    assert summary(r) == [
        ("network", False, False),
        ("login", False, True),
        ("read", False, True),
        ("readOnly", False, True),
    ]
    assert "rede interna" in r.error


def test_porta_fechada_fala_do_firewall():
    r = run(target(), FakeDriver(), open_port=open_closed)
    assert "firewall" in r.error


def test_senha_errada_mensagem_generica():
    r = run(target(), FakeDriver(login_error=asyncpg.InvalidPasswordError("x")))
    assert r.error == "Usuário ou senha recusados pelo banco. Confira e teste de novo."
    assert r.checks[0].ok and not r.checks[1].ok


def test_endereco_conectado_interno_e_recusado_dns_rebinding():
    driver = FakeDriver(peer=("10.1.2.3", 5432))
    r = run(target(), driver)
    assert not r.ok and "rede interna" in r.error
    assert driver.closed


def test_sem_tabelas_visiveis_falha_na_leitura():
    r = run(target(), FakeDriver(tables=[]))
    assert not r.ok and "GRANT SELECT" in r.error
