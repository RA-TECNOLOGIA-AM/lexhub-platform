"""Sobe a API, espera ficar pronta, faz requisições de teste e derruba o servidor.

Uso: make dev-test  (ou: python scripts/dev_test.py)
Funciona igual no Windows e no Linux.
"""

import os
import subprocess
import sys
import time

import httpx

HOST = os.getenv("DEV_TEST_HOST", "127.0.0.1")
PORT = int(os.getenv("DEV_TEST_PORT", "8000"))
BASE_URL = f"http://{HOST}:{PORT}"
STARTUP_TIMEOUT = 20
ENDPOINTS = ["/health", "/health/supabase"]


def wait_until_ready(proc: subprocess.Popen) -> bool:
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            httpx.get(f"{BASE_URL}/health", timeout=1)
            return True
        except httpx.HTTPError:
            time.sleep(0.3)
    return False


def main() -> int:
    env = {**os.environ, "PYTHONPATH": "src"}
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)]
    proc = subprocess.Popen(cmd, env=env)
    try:
        if not wait_until_ready(proc):
            print(f"API não respondeu em {STARTUP_TIMEOUT}s.", file=sys.stderr)
            return 1
        failed = False
        for path in ENDPOINTS:
            r = httpx.get(f"{BASE_URL}{path}", timeout=10)
            print(f"GET {path} -> {r.status_code} {r.text}")
            failed |= r.status_code >= 400
        return 1 if failed else 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
