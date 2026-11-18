"""Leva os links das planilhas antigas do .env (GOOGLE_SHEETS_URL_FINANCEIRO_NG/LA) para o banco, cifrados.

Rodar UMA vez, antes do merge/deploy do PR 3 (que tira essas variáveis da API). Seguro de repetir: não
sobrescreve planilha que já tem link no banco. Lê do apps/api/.env (ou das variáveis do ambiente):
  DATABASE_URL       o banco da plataforma (o mesmo da API);
  SOURCE_SECRET_KEY  a MESMA chave que vai na API da VPS (o que for cifrado com outra chave não abre lá);
  GOOGLE_SHEETS_URL_FINANCEIRO_NG / _LA  os links de hoje.

Uso (PowerShell, em apps/api):
  .\\.venv\\Scripts\\python.exe scripts\\migrar_planilhas_env.py            # confere, baixa e grava
  .\\.venv\\Scripts\\python.exe scripts\\migrar_planilhas_env.py --sem-baixar  # grava sem baixar as abas
Não mostra link nem chave na tela.
"""

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)  # o Settings lê o .env da pasta atual

import asyncpg
from dotenv import dotenv_values

import app.main  # noqa: F401  (carrega os módulos na ordem certa: evita import circular)
from app.config import get_settings
from app.legacy_sheets import LEGACY_SHEETS, PgLegacySheetsRepo, migrate
from app.secret_box import SecretBox
from app.sheets import sheet_tabs


def _links() -> dict[str, str]:
    env_file = dotenv_values(ROOT / ".env")
    return {
        key: os.environ.get(var) or env_file.get(var) or "" for key, var in LEGACY_SHEETS.items()
    }


async def main() -> int:
    settings = get_settings()
    if not settings.DATABASE_URL:
        print("Falta DATABASE_URL no .env.")
        return 1
    try:
        box = SecretBox.from_setting(settings.SOURCE_SECRET_KEY)
    except Exception:  # noqa: BLE001
        print("Falta SOURCE_SECRET_KEY no .env (ou ela não é base64 de 32 bytes).")
        return 1
    read = None if "--sem-baixar" in sys.argv else sheet_tabs
    conn = await asyncpg.connect(settings.DATABASE_URL, statement_cache_size=0)
    try:
        async with conn.transaction():
            outcomes = await migrate(PgLegacySheetsRepo(conn), box, _links(), read)
    finally:
        await conn.close()
    for o in outcomes:
        print(f"{o.key}: {o.result}")
    saved = sum(o.saved for o in outcomes)
    done = all(o.saved or o.result.startswith("já estava") for o in outcomes)
    print(f"\n{saved} planilha(s) gravada(s).")
    if done:
        print("Todas no banco: já pode tirar GOOGLE_SHEETS_URL_* do .env e da stack.")
        return 0
    print("Alguma ficou de fora (veja acima): corrija e rode de novo antes do deploy.")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
