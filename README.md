# LexHub Platform (V2)

Monorepo do LexHub V2: SaaS multi-tenant de dashboards (organização > unidade > equipe > membro).
O front só fala com a API; a API decide o acesso e lê o banco.

```
apps/
  api/        FastAPI (Python 3.12)            -> Google Cloud Run
  web/        React + Vite + TypeScript        -> Vercel        (em construção, dados fictícios)
workers/      sync dos bancos de origem -> raw_* (a criar)
supabase/
  migrations/ schema "app" (V2) — aplicar SEMPRE na branch staging primeiro
  tests/      testes do banco (rodam e desfazem tudo)
docs/         referências (ex.: estrutura da V1)
```

## Banco

Projeto Supabase `lexhub` (mesmo da V1). A V2 vive no schema `app`; o `public` é da V1 e não é alterado.
Detalhes e como aplicar: [supabase/README.md](supabase/README.md).

## API

Setup e execução: [apps/api/README.md](apps/api/README.md).

## Front

Setup e execução: [apps/web/README.md](apps/web/README.md).

## Regras do repositório

- Nunca versionar `.env`, dumps ou backups (ver `.gitignore`).
- Mudança de banco = nova migration em `supabase/migrations/` + teste em `supabase/tests/`.
