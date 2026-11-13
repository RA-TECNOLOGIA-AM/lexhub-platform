"""Sobe a API, espera ficar pronta, faz requisições de teste e derruba o servidor.

Uso: make dev-test [PORT=8000]  (ou: python scripts/dev_test.py [porta])
A porta vem do argumento, senão de DEV_TEST_PORT, senão 8000.
Funciona igual no Windows e no Linux.
"""

import os
import socket
import subprocess
import sys
import time

import httpx

HOST = os.getenv("DEV_TEST_HOST", "127.0.0.1")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv("DEV_TEST_PORT", "8000"))
BASE_URL = f"http://{HOST}:{PORT}"
STARTUP_TIMEOUT = 20
ENDPOINTS = ["/health", "/health/supabase"]


def port_in_use() -> bool:
    """True se já tem alguém escutando na porta (senão testaríamos o servidor errado)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((HOST, PORT)) == 0


def wait_until_ready(proc: subprocess.Popen) -> str:
    """Devolve 'ready', 'exited' (a API caiu ao subir) ou 'timeout'."""
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return "exited"
        try:
            httpx.get(f"{BASE_URL}/health", timeout=1)
            # Confere que quem respondeu foi o nosso processo, e não outro que subiu na porta.
            return "ready" if proc.poll() is None else "exited"
        except httpx.HTTPError:
            time.sleep(0.3)
    return "timeout"


def main() -> int:
    if port_in_use():
        print(
            f"A porta {PORT} já está em uso por outro processo. "
            f"Feche-o ou use outra porta: make dev-test PORT=8001",
            file=sys.stderr,
        )
        return 1

    env = {**os.environ, "PYTHONPATH": "src"}
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)]
    proc = subprocess.Popen(cmd, env=env)
    try:
        status = wait_until_ready(proc)
        if status == "exited":
            print(
                f"A API encerrou ao subir (código {proc.returncode}). Veja o erro acima; "
                "se for 'Field required', falta preencher o .env.",
                file=sys.stderr,
            )
            return 1
        if status == "timeout":
            print(f"A API não respondeu em {STARTUP_TIMEOUT}s.", file=sys.stderr)
            return 1
        failed = False
        for path in ENDPOINTS:
            r = httpx.get(f"{BASE_URL}{path}", timeout=10)
            print(f"GET {path} -> {r.status_code} {r.text}")
            failed |= r.status_code >= 400
        return 1 if failed else 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
