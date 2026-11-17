import base64
import os

import pytest

from app.secret_box import SecretBox, SecretKeyMissing, SecretUnreadable

KEY = base64.b64encode(os.urandom(32)).decode()


def test_cifra_e_decifra_e_cada_vez_sai_diferente():
    box = SecretBox.from_setting(KEY)
    a, b = box.encrypt("s3nh@"), box.encrypt("s3nh@")
    assert a.startswith("v1:") and a != b  # nonce novo a cada vez
    assert "s3nh@" not in a
    assert box.decrypt(a) == box.decrypt(b) == "s3nh@"


def test_formato_bate_com_a_regra_do_banco():
    # data_sources.secret_ciphertext ~ '^v1:[A-Za-z0-9+/]+={0,2}$'
    import re

    token = SecretBox.from_setting(KEY).encrypt("x" * 50)
    assert re.fullmatch(r"v1:[A-Za-z0-9+/]+={0,2}", token)


def test_outra_chave_ou_texto_alterado_nao_abre():
    box = SecretBox.from_setting(KEY)
    token = box.encrypt("senha")
    other = SecretBox(os.urandom(32))
    with pytest.raises(SecretUnreadable):
        other.decrypt(token)
    tampered = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    with pytest.raises(SecretUnreadable):
        box.decrypt(tampered)
    with pytest.raises(SecretUnreadable):
        box.decrypt("senha-aberta")


def test_chave_vazia_ou_de_tamanho_errado():
    with pytest.raises(SecretKeyMissing):
        SecretBox.from_setting("  ")
    with pytest.raises(ValueError):
        SecretBox.from_setting(base64.b64encode(os.urandom(16)).decode())
    with pytest.raises(ValueError):
        SecretBox.from_setting("não é base64!")
