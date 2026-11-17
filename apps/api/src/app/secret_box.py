"""Cifra dos segredos das fontes conectadas pela tela (senha do banco, link da planilha).

AES-256-GCM com a chave de 32 bytes do `.env` da API (SOURCE_SECRET_KEY, em base64). O banco guarda só
o texto cifrado: 'v1:' + base64(nonce de 12 bytes + cifrado + etiqueta). Sem a chave não se lê nada, e a
etiqueta do GCM recusa qualquer texto alterado. 'v1' deixa trocar o formato no futuro sem perder os antigos.

Gerar uma chave (PowerShell, na pasta apps/api):
    .\\.venv\\Scripts\\python.exe -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
Trocar a chave depois = as fontes salvas com a antiga param de abrir (a TI salva a senha de novo).
"""

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PREFIX = "v1:"
# Liga o cifrado a este uso: um texto cifrado de outro sistema com a mesma chave não abre aqui.
_AAD = b"lexhub-source-secret-v1"
_NONCE_SIZE = 12


class SecretKeyMissing(Exception):
    """SOURCE_SECRET_KEY vazia: conectar banco e planilha pela tela fica desligado."""


class SecretUnreadable(Exception):
    """Texto cifrado que não abre com a chave atual (chave trocada ou dado corrompido)."""


class SecretBox:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("A chave precisa ter 32 bytes (AES-256)")
        self._aead = AESGCM(key)

    @classmethod
    def from_setting(cls, value: str) -> "SecretBox":
        """A chave do .env (base64 de 32 bytes). Vazia = SecretKeyMissing; inválida = ValueError."""
        if not value.strip():
            raise SecretKeyMissing("SOURCE_SECRET_KEY não está definida no .env da API")
        try:
            key = base64.b64decode(value.strip(), validate=True)
        except binascii.Error as exc:
            raise ValueError("SOURCE_SECRET_KEY não é base64 válido") from exc
        return cls(key)

    def encrypt(self, plain: str) -> str:
        nonce = os.urandom(_NONCE_SIZE)
        sealed = self._aead.encrypt(nonce, plain.encode("utf-8"), _AAD)
        return PREFIX + base64.b64encode(nonce + sealed).decode("ascii")

    def decrypt(self, token: str) -> str:
        if not token.startswith(PREFIX):
            raise SecretUnreadable("Formato de segredo desconhecido")
        try:
            raw = base64.b64decode(token[len(PREFIX) :], validate=True)
            return self._aead.decrypt(raw[:_NONCE_SIZE], raw[_NONCE_SIZE:], _AAD).decode("utf-8")
        except (binascii.Error, InvalidTag, ValueError) as exc:
            raise SecretUnreadable("O segredo não abre com a chave atual") from exc
