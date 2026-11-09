# LexHub Platform (V2)

Monorepo do LexHub V2: SaaS multi-tenant de dashboards (organização > unidade > equipe > membro).
O front só fala com a API; a API decide o acesso e lê o banco.

```
apps/
  api/        FastAPI (Python 3.12)            -> Google Cloud Run
  web/        React + Vite + TypeScript        -> Vercel        (em construção, dados fictícios)
workers/      sync dos bancos de origem -> Supabase staging (a criar)
supabase/
  migrations/ schema "app" (V2) — aplicar SEMPRE na branch staging primeiro
  tests/      testes do banco (rodam e desfazem tudo)
docs/         referências (estrutura da V1) e desenhos/planos (docs/superpowers/)
```

## Pré-requisitos

| Ferramenta | Versão | Para quê |
|---|---|---|
| Git | qualquer recente | clonar |
| Node.js + npm | 22.12+, 24 ou 26 (testado com 26) | front (`apps/web`) |
| Python | 3.12 | API (`apps/api`) |
| `psql` (PostgreSQL 17) | opcional | testar as migrations localmente |
| `make` | opcional | atalhos da API |

Editor sugerido: VS Code, com as extensões recomendadas do repositório (aparecem ao abrir a pasta).

## Primeiros passos (quem acabou de clonar)

Os comandos são do PowerShell, a partir da raiz do repositório.

**Front (não precisa de API nem banco: roda com dados fictícios)**

```powershell
cd apps\web
npm ci
npm run dev    # http://localhost:5173 · login: controller@lexgroup.com.br / lexhub123
```

**API**

```powershell
cd apps\api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q                         # não precisa de .env
Copy-Item .env.example .env                 # para rodar: pedir as chaves do staging a quem administra o Supabase
python -m uvicorn app.main:app --reload --app-dir src --port 8000
```

Detalhes: [apps/web/README.md](apps/web/README.md) · [apps/api/README.md](apps/api/README.md) ·
[supabase/README.md](supabase/README.md).

## Banco

Projeto Supabase `lexhub` (mesmo da V1). A V2 vive no schema `app`; o `public` é da V1 e não é alterado.
Detalhes e como aplicar: [supabase/README.md](supabase/README.md).

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em todo push na `main` e em todo PR:

- **API:** ruff + pytest (com Postgres e as migrations).
- **Banco:** migrations + testes do banco + teste da importação V1.
- **Front:** tipos, Oxlint, Prettier, Vitest e build.

## Regras do repositório

- Nunca versionar `.env`, dumps ou backups (ver `.gitignore`). Modelos de configuração ficam em `.env.example`.
- Mudança de banco = nova migration em `supabase/migrations/` + teste em `supabase/tests/`.
- Quebras de linha: CRLF na cópia de trabalho, LF no repositório (`.editorconfig` + `.gitattributes`).
