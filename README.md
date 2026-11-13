# LexHub Platform

Monorepo da plataforma multi-organização de dashboards. A hierarquia de acesso é organização, unidade, equipe e membro; as permissões são verificadas no servidor, não apenas no menu do front.

## Mapa do repositório

| Caminho | Responsabilidade |
|---|---|
| [`apps/web/`](apps/web/README.md) | Aplicação React, rotas, dashboards e telas de administração. O modo `mock` roda sem serviços externos. |
| [`apps/api/`](apps/api/README.md) | API FastAPI para sessão `/me`, catálogo, preferências do hub, acesso e dados/exportação de dashboards. |
| [`supabase/`](supabase/README.md) | Migrations e testes dos schemas `app`, `app_private` e `api`, além dos scripts de importação da V1. |
| [`apps/web/template/`](apps/web/template/README.md) | Protótipo HTML/CSS/JS de referência, separado da aplicação React. |
| `docs/` | Contratos, referências da V1 e especificações. |
| `workers/` | Diretório reservado; ainda não há worker implementado. |

No modo `api`, a autenticação do front usa Supabase Auth. Dados de dashboard e algumas operações do hub passam pela API Python; operações de administração, notificações e pedidos de acesso usam funções autorizadas do schema `api` no Supabase. A API consulta os bancos operacionais configurados em modo somente leitura.

## Pré-requisitos

| Ferramenta | Versão | Uso |
|---|---|---|
| Git | versão recente | Clonar o repositório |
| Node.js + npm | 22.12+, 24 ou 26+ | Front (`apps/web`; Node 25 não é suportado pelo Vitest) |
| Python | 3.12 | API (`apps/api`) |
| PostgreSQL/`psql` | 17 | Opcional; testes locais de migrations e integração |
| `make` | Opcional | Atalhos da API |

## Primeiros passos

Os comandos abaixo usam PowerShell a partir da raiz.

### Front em modo mock

Não requer API, banco ou variáveis de ambiente:

```powershell
cd apps\web
npm ci
npm run dev
```

Abra http://localhost:5173. Credencial de teste: `controller@lexgroup.com.br` / `lexhub123`. O modo mock é o padrão; detalhes e outros usuários estão em [apps/web/README.md](apps/web/README.md).

### API

```powershell
cd apps\api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
Copy-Item .env.example .env
# Preencha as credenciais de desenvolvimento/staging antes de iniciar a API.
python -m uvicorn app.main:app --reload --app-dir src --port 8000
```

Os testes unitários não precisam de `.env`. Para usar os endpoints protegidos, configure o Supabase, `DATABASE_URL` e as fontes de dados necessárias. Consulte [apps/api/README.md](apps/api/README.md).

## Banco de dados

As migrations da V2 vivem em `supabase/migrations/`; o projeto também contém dados da V1 no schema `public`. A V2 usa schemas separados e não deve alterar o schema `public`. Aplique e valide migrations primeiro em staging. Veja [supabase/README.md](supabase/README.md).

## Verificações e CI

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em PRs e em pushes para `main`:

- **API:** Ruff e Pytest, incluindo testes contra PostgreSQL com as migrations.
- **Banco:** migrations, testes SQL e importação V1 → V2.
- **Front:** TypeScript, Oxlint, Prettier, Vitest e build.

## Regras do repositório

- Não versione `.env`, credenciais, dumps ou backups. Use os arquivos `.env.example` como modelos; nunca coloque segredos em variáveis `VITE_*`.
- Mudanças no banco exigem uma migration nova e testes SQL relacionados.
- Preserve as regras de formatação e fim de linha configuradas em `.editorconfig` e `.gitattributes`.
