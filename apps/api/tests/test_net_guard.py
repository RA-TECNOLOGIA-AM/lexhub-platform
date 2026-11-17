import asyncio

import pytest

from app.net_guard import BlockedHost, HostNotFound, check_peer, is_blocked, resolve_public


@pytest.mark.parametrize(
    "address",
    [
        "10.0.0.5",
        "172.16.3.4",
        "192.168.0.10",
        "127.0.0.1",
        "169.254.169.254",  # metadados da nuvem
        "100.64.1.1",  # CGNAT
        "0.0.0.0",
        "::1",
        "fd00::1",
        "fe80::1%eth0",
        "::ffff:10.0.0.1",  # IPv4 dentro de IPv6
    ],
)
def test_enderecos_internos_bloqueados(address):
    assert is_blocked(address)


@pytest.mark.parametrize("address", ["8.8.8.8", "200.160.2.3", "2001:4860:4860::8888"])
def test_enderecos_publicos_liberados(address):
    assert not is_blocked(address)


def test_resolve_recusa_host_interno_porta_de_sistema_e_nome_inexistente():
    with pytest.raises(BlockedHost):
        asyncio.run(resolve_public("127.0.0.1", 5432))
    with pytest.raises(BlockedHost):
        asyncio.run(resolve_public("localhost", 5432))
    with pytest.raises(BlockedHost):
        asyncio.run(resolve_public("8.8.8.8", 22))
    with pytest.raises(HostNotFound):
        asyncio.run(resolve_public("nao-existe.invalid", 5432))


def test_resolve_aceita_ip_publico_e_libera_interno_so_em_desenvolvimento():
    assert asyncio.run(resolve_public("8.8.8.8", 5432)) == ["8.8.8.8"]
    assert asyncio.run(resolve_public("127.0.0.1", 5432, allow_private=True)) == ["127.0.0.1"]


def test_confere_o_endereco_conectado():
    check_peer(("8.8.8.8", 5432))
    check_peer(("2001:4860:4860::8888", 5432, 0, 0))
    with pytest.raises(BlockedHost):
        check_peer(("10.1.2.3", 5432))
    with pytest.raises(BlockedHost):
        check_peer(None)
