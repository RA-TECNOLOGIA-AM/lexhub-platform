import csv
import importlib.util
import json
import pathlib
from datetime import UTC, datetime, timedelta

import pytest

_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "api_publica_cliente.py"
_spec = importlib.util.spec_from_file_location("api_publica_cliente", _PATH)
cliente = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cliente)

NOW = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
BASE = "https://api.exemplo/v1"


def _cred(tmp_path, **over) -> pathlib.Path:
    data = {
        "base_url": BASE,
        "refresh_token": "lxr_velho",
        "access_token": "acc_velho",
        "access_expires_at": (NOW + timedelta(days=3)).isoformat(),
        **over,
    }
    path = tmp_path / "lexhub_api.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class FakeHttp:
    """Responde por URL; guarda a ordem das chamadas e o que o arquivo tinha em cada uma."""

    def __init__(self, cred_path, responses):
        self.cred_path = cred_path
        self.responses = responses
        self.calls = []

    def __call__(self, method, url, headers, body):
        snapshot = json.loads(self.cred_path.read_text(encoding="utf-8"))
        self.calls.append((method, url, headers, body, snapshot))
        for prefix, (status, payload) in self.responses.items():
            if url.startswith(prefix):
                result = payload(len(self.calls)) if callable(payload) else payload
                return status, result
        raise AssertionError(f"URL inesperada: {url}")


NEW_TOKENS = {
    "access_token": "acc_novo",
    "access_expires_at": (NOW + timedelta(days=7)).isoformat(),
    "refresh_token": "lxr_novo",
    "refresh_expires_at": (NOW + timedelta(days=30)).isoformat(),
    "token_type": "Bearer",
}


def _page(pagina, total_paginas, dados):
    return {
        "campos": ["id", "nome"],
        "paginacao": {
            "pagina": pagina,
            "tamanho_pagina": 2,
            "total": 3,
            "total_paginas": total_paginas,
        },
        "dados": dados,
    }


def test_access_valido_nao_renova(tmp_path):
    path = _cred(tmp_path)
    http = FakeHttp(path, {})
    assert cliente.access_token(path, http, NOW) == "acc_velho"
    assert http.calls == []


def test_regrava_o_refresh_novo_antes_de_pedir_os_dados(tmp_path):
    path = _cred(tmp_path, access_expires_at=(NOW + timedelta(minutes=30)).isoformat())
    http = FakeHttp(
        path,
        {
            f"{BASE}/auth/token": (200, NEW_TOKENS),
            f"{BASE}/orgs/": (200, _page(1, 1, [{"id": 1, "nome": "a"}])),
        },
    )
    saida = tmp_path / "dados.csv"
    cliente.baixar(
        path, "lexgroup", "NG", "comercial-lexpre", "2026-11-01", "2026-11-26", saida, http, NOW
    )
    renew, data = http.calls
    assert renew[1] == f"{BASE}/auth/token" and json.loads(renew[3]) == {
        "refresh_token": "lxr_velho"
    }
    # Quando pediu os dados, o arquivo já tinha o refresh novo.
    assert data[4]["refresh_token"] == "lxr_novo"
    assert data[2]["Authorization"] == "Bearer acc_novo"
    assert json.loads(path.read_text(encoding="utf-8"))["refresh_token"] == "lxr_novo"


def test_falha_na_renovacao_nao_mexe_no_arquivo(tmp_path):
    path = _cred(tmp_path, access_expires_at=(NOW - timedelta(minutes=1)).isoformat())
    before = path.read_text(encoding="utf-8")
    http = FakeHttp(path, {f"{BASE}/auth/token": (401, {"detail": "Refresh token já usado"})})
    with pytest.raises(cliente.ApiError) as exc:
        cliente.access_token(path, http, NOW)
    assert "Refresh token já usado" in str(exc.value)
    assert path.read_text(encoding="utf-8") == before


def test_baixar_junta_todas_as_paginas_em_csv(tmp_path):
    path = _cred(tmp_path)
    pages = {
        2: _page(1, 2, [{"id": 1, "nome": "a"}, {"id": 2, "nome": "b"}]),
        3: _page(2, 2, [{"id": 3, "nome": "c"}]),
    }
    http = FakeHttp(path, {f"{BASE}/orgs/": (200, lambda n: pages[n + 1])})
    saida = tmp_path / "dados.csv"
    total = cliente.baixar(
        path, "lexgroup", "NG", "comercial-lexpre", "2026-11-01", "2026-11-26", saida, http, NOW
    )
    assert total == 3
    assert "pagina=2" in http.calls[1][1]
    with saida.open(encoding="utf-8-sig", newline="") as f:
        assert list(csv.reader(f)) == [["id", "nome"], ["1", "a"], ["2", "b"], ["3", "c"]]
