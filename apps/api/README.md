# API Dashboard V2

FastAPI + Supabase. Python 3.12.

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env   # preencher SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY
```

## Rodar

```powershell
python -m uvicorn app.main:app --reload --app-dir src --port 8000
```

- `GET /health` — liveness da API
- `GET /health/supabase` — verifica se o projeto Supabase responde (503 se não)
- `GET /orgs/{org}/units/{UNIDADE}/dashboards/{dashboard}/access` — confere o acesso do usuário logado
  (`{"scope": "all" | "own"}`)
- Docs: http://localhost:8000/docs

## Login, organização e acesso

Toda rota de dashboard usa a dependency `require_dashboard` (`app/access.py`):

| Situação | Resposta |
|---|---|
| Sem `Authorization: Bearer`, token inválido, expirado, de outro projeto ou `alg=none` | 401 |
| Organização/unidade inexistente ou sem regra que libere | 403 (mesma resposta; negação vai para `app.audit_log`) |
| Banco não configurado (`DATABASE_URL` vazio) | 503 |
| Liberado | segue, com `access.scope` = `all` ou `own` |

- O JWT do Supabase é validado **localmente** com as chaves do JWKS do projeto
  (`/auth/v1/.well-known/jwks.json`, em cache; `kid` novo força uma rebusca, no máximo 1/min).
- A regra de acesso é a do banco (`app_private.dashboard_scope`), chamada via `DATABASE_URL`.

Nova rota de dashboard:

```python
@router.get("/{dashboard_key}")
async def meu_dashboard(access: Annotated[DashboardAccess, Depends(require_dashboard)]):
    ...  # access.org_id, access.unit_id, access.scope ('own' = só registros do usuário)
```

## Usar o Supabase numa rota

```python
from typing import Annotated
from fastapi import Depends
from supabase import AsyncClient
from app.supabase_client import get_supabase

@router.get("/exemplo")
async def exemplo(sb: Annotated[AsyncClient, Depends(get_supabase)]):
    res = await sb.table("minha_tabela").select("*").limit(10).execute()
    return res.data
```

O cliente usa `SUPABASE_SECRET_KEY` se definida (ignora RLS); senão a publishable key (respeita RLS).

## Testes / lint

```powershell
python -m pytest -v
python -m ruff check src tests
```

`tests/test_pg_repo.py` roda o SQL real da API contra um Postgres com as migrations. Fica
desligado sem `TEST_DATABASE_URL` (o CI liga). Localmente, num Postgres de teste com
`supabase/tests/ci/supabase_stub.sql` + `supabase/migrations/*.sql` aplicados:

```powershell
$env:TEST_DATABASE_URL = "postgresql://postgres@localhost:54329/postgres"
python -m pytest tests/test_pg_repo.py -v
```
