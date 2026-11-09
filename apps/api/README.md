# API Dashboard V2

FastAPI + Supabase. Precisa do **Python 3.12** (ver `.python-version`). Tudo é rodado **dentro de `apps/api`**.

## Setup

```powershell
cd apps\api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env   # preencher SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY (e DATABASE_URL para as rotas de dashboard)
```

No Linux/macOS: `python3.12 -m venv .venv` e `source .venv/bin/activate`.
Se o PowerShell bloquear o `Activate.ps1`: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (uma vez).

O `.env` nunca é versionado: cada pessoa pede as chaves do projeto **staging** a quem administra o Supabase.
Sem `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY` a API **não sobe** (erro de validação do `config.py`).
Com eles e sem `DATABASE_URL`, sobe, o `/health` responde e as rotas de dashboard devolvem 503.
Os testes (`pytest`) não precisam de `.env`.

| Variável | Obrigatória | Para quê |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` | sim | validar o login (JWKS) e o `/health/supabase` |
| `DATABASE_URL` | para dashboards | regra de acesso (`app_private.dashboard_scope`) e auditoria |
| `SUPABASE_SECRET_KEY` | não | acesso server-side que ignora RLS |
| `SUPABASE_JWT_SECRET` | não | só projetos com segredo JWT legado (HS256) |
| `CORS_ORIGINS` | para o front | origens liberadas, separadas por vírgula; o `.env.example` já traz `http://localhost:5173` (vazio = nenhuma) |

## Rodar

```powershell
python -m uvicorn app.main:app --reload --app-dir src --port 8000
```

Com `make` instalado, os atalhos do [`Makefile`](Makefile) fazem o mesmo no Windows e no Linux:
`make setup`, `make run`, `make dev-test` (sobe a API, testa `/health` e derruba), `make test`, `make lint`, `make check`.

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
