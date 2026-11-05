# Banco da V2 (Supabase)

Tabelas da V2 ficam no schema **`app`**, no mesmo projeto Supabase da V1 (`eatdloxpywxvuqtovgln`).
O schema `public` (V1) não é tocado. Usuários do login (`auth.users`) são reaproveitados.

## Estrutura

```
supabase/
  migrations/20261105120000_app_core.sql   organização > unidade > equipe > membro, dashboards, liberações, auditoria, RLS
  tests/app_core_smoke.sql                 teste de isolamento e regra de acesso (roda e desfaz tudo)
  tests/ci/                                só para o CI (simula Supabase e V1) — não rodar no Supabase
  scripts/import_v1.sql                    importa usuários/estrutura da V1 (public) para o app
  scripts/copiar_v1_1_estrutura.sql        gera (na main) o script que recria as tabelas da V1 no staging
  scripts/copiar_v1_2_dados.sql            gera (na main) o script que copia os dados da V1 para o staging
docs/v1_schema_colunas.csv                 estrutura da V1 (referência, sem dados)
```

## Regra de acesso a dashboard

| Quem | Vê |
|---|---|
| owner/admin da organização | todos os dashboards de todas as unidades da organização |
| manager da unidade (o "Gestor" da V1) | todos os dashboards ligados naquela unidade |
| member da unidade | só os liberados para ele ou para uma equipe dele (`dashboard_grants`) |
| membro `disabled`, outra organização, `anon` | nada |

Funções: `app.can_view_dashboard(unit, key)` e `app.my_dashboards()` (usuário logado);
`app.user_can_view_dashboard(user, unit, key)` só para a API (service_role).

## Como aplicar (SEMPRE na staging primeiro)

1. No painel, troque de `main` para a branch **staging**.
2. SQL Editor → cole o conteúdo de `migrations/20261105120000_app_core.sql` → Run.
3. Cole `tests/app_core_smoke.sql` → Run. Esperado: mensagens `OK: ...` e nenhum erro.
4. Só depois de validado, aplicar na `main` (produção).

Migrations: nunca direto na `main` sem passar pela staging.
Exceção: `scripts/import_v1.sql` só funciona na `main` (é onde estão os dados da V1) — por isso ele roda primeiro em modo ensaio.

## Importar usuários e estrutura da V1

`scripts/import_v1.sql` lê o `public` (V1) e preenche o `app`. Não altera nada da V1.

1. Precisa do schema `app` já criado no mesmo banco (migration aplicada).
2. Rode como está: é um **ensaio** (termina em `rollback`) e mostra um relatório.
3. Relatório certo → troque a última linha por `commit;` e rode de novo.
4. Pode repetir: atualiza sem duplicar (sobrescreve papel/status com os valores da V1).

## Copiar a V1 para o staging (sem tocar na produção)

Os dois scripts rodam na **main**, mas só LEEM: cada um devolve uma célula com outro script,
que é o que roda no **staging**. Os scripts gerados têm trava: se rodados na produção, param sem fazer nada.

1. main: rodar `copiar_v1_1_estrutura.sql` → copiar a célula `script` → staging: colar e rodar.
2. main: rodar `copiar_v1_2_dados.sql`     → copiar a célula `script` → staging: colar e rodar.
3. staging: rodar `import_v1.sql` (ensaio; depois `commit;`).

Não são copiados: segredos (tokens/configs da Conta Azul, refresh tokens da API pública),
financeiro da Conta Azul e histórico de login. Usuários do login vão sem senha.
Para refazer a cópia, comece de novo pelo passo 1.
