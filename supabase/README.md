# Banco da V2 (Supabase)

O banco da V2 usa schemas separados no mesmo projeto Supabase da V1: **`app`** para dados da plataforma,
**`app_private`** para funções internas de autorização e **`api`** para funções chamadas pelo front autenticado. O
schema `public` da V1 não é alterado; os usuários de `auth.users` são reaproveitados.

## Estrutura

As migrations numeradas cobrem o núcleo multi-tenant, papéis e regras por unidade/equipe, catálogo e preferências do
hub, ligações com fontes de dados, dashboards, pedidos de acesso, membros, permissões, unidades/fontes, auditoria,
notificações e endurecimento de segurança. Aplique-as sempre pela ordem do nome.

- `tests/*.sql`: testes do banco, cada um termina com rollback.
- `tests/ci/`: stubs e fixtures usados pelo CI; não aplicar em projeto Supabase.
- `scripts/import_v1.sql`: importa usuários e estrutura de `public` para `app`.
- `scripts/copiar_v1_1_estrutura.sql` e `scripts/copiar_v1_2_dados.sql`: geram scripts para copiar a V1 ao staging.
- `docs/v1_schema_colunas.csv`: referência estrutural da V1, sem dados.

O front usa funções do schema `api` para administração, notificações e pedidos de acesso. No Supabase, inclua `api`
em **Settings → API → Exposed schemas**. As funções verificam o token e as permissões no banco; não conceda ao
front uma chave `service_role`.

## Regra de acesso a dashboard

A pessoa tem **um papel na organização** e **um cargo em cada companhia (unidade)** em que está.
O usuário vê uma companhia por vez (a ativa, `?unit=` na URL).

Papel na organização (`memberships.role_key`):

| Papel na organização | Acesso |
|---|---|
| owner, admin (Desenvolvedor) | Todas as unidades e dashboards; administração da organização. O Owner tem proteções específicas para alterações de acesso. |
| member | O que o cargo e as regras por unidade/equipe permitem. |

Cargo na companhia (`membership_units.role_key`):

| Cargo na unidade | Vê | Exporta | Administração |
|---|---|---|---|
| gestor | Todos os dashboards da unidade | sim | Gere membros e acesso na unidade |
| controller | Todos os dashboards da unidade | sim | Não gere membros nem acesso |
| colaborador | Dashboards liberados pelas regras para suas equipes | sim | não |
| leitor | Dashboards liberados pelas regras para suas equipes | não | não |

Gestor e Controller também podem consultar as fontes das unidades que gerem; Owner/Desenvolvedor têm escopo da
organização. Exemplo: Controller na NG e Leitor na LA. Uma pessoa pode estar em várias equipes de uma unidade.
Membro desativado, usuário de outra organização ou `anon` não recebe acesso. Na importação da V1, a unidade principal
recebe o cargo legado e unidades extras entram como Leitor.

`access_rules.scope`: `all` (todos os registros da unidade) ou `own` (só os do próprio usuário). Nega quando nada casa.

Funções: `app.dashboard_scope(unit, key)`, `app.can_view_dashboard(unit, key)`, `app.my_dashboards()` (usuário logado);
`app_private.dashboard_scope(user, unit, key)`, `app_private.has_permission(user, org, perm)` e `app_private.has_unit_permission(user, unit, perm)` só para a API (service_role).

## Como aplicar (SEMPRE na staging primeiro)

1. No painel, troque de `main` para a branch **staging**.
2. SQL Editor → cole e rode **cada arquivo de `migrations/`, na ordem do nome** (o número no começo é a data/hora).
   Num banco que já tem as anteriores, rode só as novas.
3. Rode os testes SQL relacionados à mudança. O teste de fumaça `tests/app_core_smoke.sql` exibe mensagens `OK: ...`
   quando passa.

Sem acesso ao painel, dá para testar tudo num Postgres local (é o que o CI faz):

```powershell
psql -v ON_ERROR_STOP=1 -f supabase/tests/ci/supabase_stub.sql      # simula auth e papéis do Supabase
Get-ChildItem supabase/migrations/*.sql | Sort-Object Name | ForEach-Object { psql -v ON_ERROR_STOP=1 -f $_.FullName }
Get-ChildItem supabase/tests/*.sql | Sort-Object Name | ForEach-Object { psql -v ON_ERROR_STOP=1 -f $_.FullName }
```

O CI também testa a importação V1 com fixtures próprias. Os arquivos em `tests/ci/` são exclusivos desse ambiente.
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
