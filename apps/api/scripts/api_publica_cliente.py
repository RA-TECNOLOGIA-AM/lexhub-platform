"""Cliente da API pública do LexHub (/v1): renova os tokens sozinho e baixa um dashboard para CSV.

Feito para rodar agendado (Power BI, Agendador de Tarefas): só usa a biblioteca padrão do Python.

1. No LexHub, Configurações -> Chave de API -> "Gerar tokens". Guarde o refresh token.
2. Crie o arquivo de credenciais (uma vez):
       python api_publica_cliente.py iniciar --url https://api.hub.lexgroup.com.br/v1 --refresh lxr_...
3. Baixe os dados (renova o access quando faltar menos de 1 hora para vencer):
       python api_publica_cliente.py baixar --org lexgroup --unidade NG --dashboard comercial-lexpre \\
           --de 2026-11-01 --ate 2026-11-26 --saida comercial.csv

O refresh token muda a cada renovação: o script grava o novo no arquivo ANTES de pedir os dados. Se o mesmo
refresh for usado duas vezes, o LexHub revoga todos os tokens da chave (gere novos na tela). Não rode duas
cópias do script ao mesmo tempo com o mesmo arquivo, e guarde o arquivo como uma senha.
"""

import argparse
import csv
import json
import os
import pathlib
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

# (método, url, cabeçalhos, corpo) -> (status, json)
Http = Callable[[str, str, dict[str, str], str | None], tuple[int, dict]]

RENEW_BEFORE = timedelta(hours=1)
PAGE_SIZE = 5000


class ApiError(Exception):
    """Resposta de erro da API (a mensagem vem do campo `detail`)."""


def urllib_http(
    method: str, url: str, headers: dict[str, str], body: str | None
) -> tuple[int, dict]:
    data = body.encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except ValueError:
            return exc.code, {"detail": exc.reason}


def _check(status: int, payload: dict) -> dict:
    if status >= 400:
        raise ApiError(f"{status}: {payload.get('detail', payload)}")
    return payload


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: pathlib.Path, data: dict) -> None:
    """Grava num arquivo temporário e troca de uma vez (nunca deixa o arquivo pela metade)."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".lexhub_api_", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def renew(path: pathlib.Path, http: Http) -> dict:
    cred = _load(path)
    status, payload = http(
        "POST",
        f"{cred['base_url']}/auth/token",
        {"Content-Type": "application/json"},
        json.dumps({"refresh_token": cred["refresh_token"]}),
    )
    tokens = _check(status, payload)
    cred.update(
        refresh_token=tokens["refresh_token"],
        access_token=tokens["access_token"],
        access_expires_at=tokens["access_expires_at"],
    )
    _save(path, cred)
    return cred


def access_token(path: pathlib.Path, http: Http = urllib_http, now: datetime | None = None) -> str:
    """O access token do arquivo; renova antes se faltar menos de 1 hora (ou se não houver)."""
    now = now or datetime.now(UTC)
    cred = _load(path)
    expires = cred.get("access_expires_at")
    if (
        not cred.get("access_token")
        or not expires
        or datetime.fromisoformat(expires) - now < RENEW_BEFORE
    ):
        cred = renew(path, http)
    return cred["access_token"]


def baixar(
    path: pathlib.Path,
    org: str,
    unidade: str,
    dashboard: str,
    de: str,
    ate: str,
    saida: pathlib.Path,
    http: Http = urllib_http,
    now: datetime | None = None,
    campos: str | None = None,
    relatorio: str | None = None,
) -> int:
    """Baixa todas as páginas do dashboard e grava um CSV (UTF-8 com BOM, abre certo no Excel)."""
    token = access_token(path, http, now)
    base = _load(path)["base_url"]
    rows: list[dict] = []
    header: list[str] = []
    pagina = 1
    while True:
        params = {"from": de, "to": ate, "pagina": pagina, "tamanho_pagina": PAGE_SIZE}
        if campos:
            params["campos"] = campos
        if relatorio:
            params["relatorio"] = relatorio
        url = f"{base}/orgs/{org}/units/{unidade}/dashboards/{dashboard}?{urllib.parse.urlencode(params)}"
        body = _check(*http("GET", url, {"Authorization": f"Bearer {token}"}, None))
        header = body["campos"]
        rows.extend(body["dados"])
        if pagina >= body["paginacao"]["total_paginas"]:
            break
        pagina += 1
    with saida.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows([[r.get(c, "") for c in header] for r in rows])
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--credenciais", default="lexhub_api.json", type=pathlib.Path)
    sub = parser.add_subparsers(dest="comando", required=True)
    ini = sub.add_parser("iniciar", help="cria o arquivo de credenciais")
    ini.add_argument("--url", required=True, help="ex.: https://api.hub.lexgroup.com.br/v1")
    ini.add_argument("--refresh", required=True, help="refresh token (lxr_...) gerado no LexHub")
    bx = sub.add_parser("baixar", help="baixa um dashboard para CSV")
    for name in ("org", "unidade", "dashboard", "de", "ate"):
        bx.add_argument(f"--{name}", required=True)
    bx.add_argument("--saida", required=True, type=pathlib.Path)
    bx.add_argument("--campos", help="separados por vírgula (padrão: todos)")
    bx.add_argument("--relatorio")
    args = parser.parse_args()

    if args.comando == "iniciar":
        _save(
            args.credenciais.resolve(),
            {"base_url": args.url.rstrip("/"), "refresh_token": args.refresh},
        )
        access_token(args.credenciais.resolve())
        print(f"Credenciais gravadas em {args.credenciais}. Guarde esse arquivo como uma senha.")
        return
    total = baixar(
        args.credenciais.resolve(),
        args.org,
        args.unidade,
        args.dashboard,
        args.de,
        args.ate,
        args.saida,
        campos=args.campos,
        relatorio=args.relatorio,
    )
    print(f"{total} linhas gravadas em {args.saida}.")


if __name__ == "__main__":
    try:
        main()
    except ApiError as exc:
        raise SystemExit(f"Erro da API: {exc}") from None
