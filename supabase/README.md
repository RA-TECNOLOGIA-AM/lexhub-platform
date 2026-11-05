# Banco da V2 (Supabase)

Tabelas da V2 ficam no schema **`app`**, no mesmo projeto Supabase da V1 (`eatdloxpywxvuqtovgln`).
O schema `public` (V1) não é tocado. Usuários do login (`auth.users`) são reaproveitados.

## Estrutura

```
supabase/
  migrations/20261105120000_app_core.sql   organização > unidade > equipe > membro, dashboards, liberações, auditoria, RLS
  tests/app_core_smoke.sql                 teste de isolamento e regra de acesso (roda e desfaz tudo)
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

Não rodar nada destes arquivos na `main` sem passar pela staging.
