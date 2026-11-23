"""Nomes e rótulos de texto: as regras comuns das análises (V2).

As cópias da v1 tinham, cada uma, o próprio "nome curto do funcionário/atendente", "matéria", "comarca",
"subfase" e "iniciais". Aqui fica uma de cada regra; onde a v1 tinha regras diferentes (maiúsculas, quantos
nomes, o que fazer com o vazio), elas viram opções.
"""

from typing import Any


def rotulo(valor: Any, vazio: str) -> str:
    """O texto sem espaços nas pontas; None, "" ou só espaços -> `vazio` (comarca, subfase)."""
    if valor is None or valor == "":
        return vazio
    texto = str(valor).strip()
    return texto if texto else vazio


def texto_ou(valor: Any, vazio: str) -> str:
    """Como `rotulo`, mas qualquer valor "falso" (0, False) também vira `vazio` (regra do Pré-protocolo)."""
    texto = str(valor or "").strip()
    return texto if texto else vazio


def materia(valor: Any) -> str:
    """Matéria das análises da v1: o que vem antes de " - " (ex.: "CESTA - Tarifa" -> "CESTA"); vazio ->
    "Sem materia"."""
    if valor is None or valor == "":
        return "Sem materia"
    texto = str(valor).strip()
    if " - " in texto:
        texto = texto.split(" - ", 1)[0].strip()
    return texto if texto else "Sem materia"


def primeiros_nomes(
    nome: str, quantos: int, *, maiusculas: bool = False, ignorar: str | None = None
) -> str:
    """Os `quantos` primeiros nomes (ex.: "Ana Maria Souza", 2 -> "Ana Maria"), em maiúsculas se pedido. Nome
    vazio ou igual a `ignorar` (ex.: "Sem funcionario") volta como veio."""
    if not nome or nome == ignorar:
        return nome
    curto = " ".join(nome.strip().split()[:quantos])
    return curto.upper() if maiusculas else curto


def primeiros_nomes_ou(nome: Any, quantos: int, vazio: str) -> str:
    """Os `quantos` primeiros nomes; vazio (ou só espaços) -> `vazio` (regra do Pré-protocolo)."""
    if not nome or not str(nome).strip():
        return vazio
    return " ".join(str(nome).strip().split()[:quantos])


def iniciais_nome(nome: str) -> str:
    """Iniciais do nome (ex.: "Ana Souza" -> "AS"; um nome só: as duas primeiras letras); vazio -> "—"."""
    partes = [p for p in nome.split() if p]
    if not partes:
        return "—"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return f"{partes[0][0]}{partes[1][0]}".upper()
