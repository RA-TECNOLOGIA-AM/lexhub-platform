"""Proteção de rede das fontes conectadas pela tela (contra SSRF).

A TI digita host e porta do banco da operação, e é a API que conecta. Sem esta trava, o formulário
viraria uma porta para a rede interna da VPS (outros containers, metadados da nuvem). Três camadas:
  1. firewall de saída na VPS (infra; o controle principal);
  2. `resolve_public` antes de conectar: recusa se QUALQUER endereço do host for interno, e porta < 1024;
  3. `check_peer` depois de conectar: o endereço de fato conectado (pega DNS rebinding).
A conexão continua pelo nome do host, para o SSL funcionar normalmente.
"""

import asyncio
import ipaddress
import socket

# Faixas que a API nunca alcança por uma fonte conectada pela tela (além de privado/loopback/etc.).
_EXTRA_BLOCKED = (
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT
    ipaddress.ip_network("169.254.0.0/16"),  # link-local (metadados da nuvem)
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
)


class BlockedHost(Exception):
    """Endereço de rede interna, reservado ou porta de sistema: a API não conecta."""


class HostNotFound(Exception):
    """O nome do host não resolve para nenhum endereço."""


def is_blocked(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%", 1)[0])  # tira o escopo de IPv6 (fe80::1%eth0)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or any(ip in net for net in _EXTRA_BLOCKED if net.version == ip.version)
    )


async def resolve_public(host: str, port: int, *, allow_private: bool = False) -> list[str]:
    """Endereços do host, se todos forem públicos. Senão BlockedHost; nome que não existe = HostNotFound."""
    if not 1024 <= port <= 65535:
        raise BlockedHost(f"porta {port}")
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HostNotFound(host) from exc
    addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise HostNotFound(host)
    if not allow_private and any(is_blocked(a) for a in addresses):
        raise BlockedHost(host)
    return addresses


def check_peer(peername: object, *, allow_private: bool = False) -> None:
    """Depois de conectar: o endereço do outro lado (`transport.get_extra_info('peername')`)."""
    if not isinstance(peername, tuple) or not peername:
        raise BlockedHost("endereço conectado desconhecido")
    if not allow_private and is_blocked(str(peername[0])):
        raise BlockedHost(str(peername[0]))
