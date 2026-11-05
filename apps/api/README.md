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
- Docs: http://localhost:8000/docs

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
