# Solicitar acesso — plano de implementação

Spec: `docs/superpowers/specs/2026-11-11-acesso-google-design.md` (Entrega 2). Branch: `feat/solicitar-acesso`.
Regras da casa: indentação 4 espaços, módulos com uma responsabilidade (regras de tela em `*View.ts`, testadas sem
React), o Luís faz os commits (o plano sugere a mensagem no fim de cada etapa), migration só com "Aplica".

Pré-requisitos do Luís (painel do staging `vvhgbzjapqcyjbfpndaq`):

- [ ] Settings → API → Exposed schemas: adicionar `api` (antes de testar em modo api, etapa 6).
- [ ] "Aplica" da migration e do `platform_staff` (etapa 2).

---

## Etapa 1 — Migration `app.access_requests` + schema `api`

Arquivo: `supabase/migrations/20261112160000_solicitar_acesso.sql`.

1. `create table app.access_requests` com as colunas do spec, `check` de tamanho em `office` (2–120 após trim) e
   `message` (≤ 500), `check (status in ('pending','approved','rejected'))`; índice único parcial
   `(user_id) where status = 'pending'`; RLS ligada; policy `access_requests_select_own` (`user_id = auth.uid()`).
   Sem policy de escrita.
2. `app_private.is_platform_staff()`: `coalesce((auth.jwt() -> 'app_metadata' ->> 'platform_staff')::boolean, false)`.
3. `create schema api; grant usage on schema api to authenticated;` e as funções (todas `security definer`,
   `set search_path = ''`, `revoke all … from public, anon`, `grant execute … to authenticated`):
   - `api.request_access(p_office text, p_message text) returns app.access_requests`: exige `auth.uid()`; recusa
     (`P0001`, mensagem em pt-BR) se já tem associação `active` ou pedido `pending`; nome/e-mail de `auth.users`
     (`raw_user_meta_data ->> 'full_name'`, cai no e-mail); audita `access_request.created`.
   - `api.my_access_request()`: último pedido do chamador (`order by created_at desc limit 1`).
   - `api.count_pending_access_requests() returns int` (staff).
   - `api.list_access_requests(p_status text)`: `'pending'` ou `'decided'` (approved + rejected), mais recentes
     primeiro (staff).
   - `api.approval_options() returns jsonb`: `[{id, slug, name, units: [{id, code, name}]}]` das organizações e
     unidades ativas (staff).
   - `api.approve_access_request(p_id uuid, p_target jsonb)`: staff; pedido `pending` (`for update`); ramo
     `existing` (valida org ativa, `org_role in ('admin','member')`, unidades da org, `role_key` de nível unit,
     `member` exige ≥ 1 unidade) ou `new` (cria `organizations` + `units`, `org_role in ('owner','admin')`);
     `insert app.memberships (status 'active')` + `app.membership_units`; marca `approved`, `decided_by`,
     `decided_at`, `result_org_id`; audita `access_request.approved` com `org_id`.
   - `api.reject_access_request(p_id uuid, p_note text)`: staff; pedido `pending`; marca `rejected`; audita.
   - Sem staff: `raise exception using errcode = '42501', message = 'Só a equipe RA'`.
4. Rollback no cabeçalho: `drop schema api cascade; drop function app_private.is_platform_staff();
   drop table app.access_requests;`.

Teste: `supabase/tests/solicitar_acesso_test.sql`, um bloco `do $$ … $$` que simula usuários com
`set local request.jwt.claims` / `set local role authenticated` e confere:

- pedido criado; segundo pedido pendente recusado; quem tem associação ativa é recusado;
- não-staff recebe `42501` em list/approve/reject/count;
- aprovar em org existente cria associação ativa + unidades e marca o pedido; aprovar em org nova cria org + unidade +
  associação `owner`; recusar grava a nota; aprovar pedido já decidido falha;
- termina com `raise exception 'OK: …'` para que nada fique gravado.

Validação: rodar migration + teste numa única chamada no vvhg (o `raise` final desfaz tudo); só então pedir o
"Aplica" e aplicar com `apply_migration`.

Commit sugerido: `Banco: pedidos de acesso (app.access_requests) e schema api com as funções de pedir, listar, aprovar
(organização existente ou nova) e recusar, só para a equipe RA; teste com rollback`

## Etapa 2 — Aplicar e marcar a equipe RA

1. "Aplica" → `apply_migration` no vvhg.
2. "Aplica" → `update auth.users set raw_app_meta_data = raw_app_meta_data || '{"platform_staff": true}'` na conta
   @lexgroup do Luís. Ele sai e entra de novo para o token trazer o valor.
3. Conferir com `get_advisors` (security) que nada novo apareceu.

## Etapa 3 — Tipos e cliente de dados

Arquivos: `apps/web/src/types/index.ts`, `services/client.ts`, `services/accessRequests.ts` (novo),
`services/apiClient.ts`, `services/mockClient.ts`, `services/mock/accessRequests.ts` (novo),
`services/sessionCache.ts`.

1. Tipos: `AccessRequest` (`id, email, full_name, office, message, status, created_at, decided_at, decision_note`),
   `AccessRequestStatus`, `ApprovalOrg` (`id, slug, name, units`), `ApprovalTarget` (união `existing` | `new`).
2. `DataClient`: `requestAccess(office, message)`, `getMyAccessRequest()`, `countPendingAccessRequests()`,
   `listAccessRequests(status)`, `getApprovalOptions()`, `approveAccessRequest(id, target)`,
   `rejectAccessRequest(id, note)`.
3. `accessRequests.ts`: `createAccessRequestsClient(supabase)` com `supabase.schema('api').rpc(...)`; erros viram
   `DataError` (`42501` → 403, `P0001` → 409 com a mensagem, schema não exposto `PGRST106` → mensagem clara
   "exponha o schema api no Supabase").
4. `apiClient.ts` espalha esses métodos (`...createAccessRequestsClient(auth)`).
5. Mock: loja em memória (`mock/accessRequests.ts`) com um pedido pendente de exemplo; o mock do `getMe` passa a
   aceitar o usuário sem acesso depois de aprovado (a loja guarda os aprovados).
6. `sessionCache.ts`: nada a guardar; só repassa (o `...client` já cobre).
7. Testes (vitest): `services/accessRequests.test.ts` com um `supabase` falso (rpc chamado com o nome e os
   parâmetros certos; mapeamento de erros) e `services/mock/accessRequests.test.ts` (pedir, duplicado, aprovar,
   recusar).

Commit sugerido: `Front: cliente de dados dos pedidos de acesso (RPC no schema api) e versão em memória no mock`

## Etapa 4 — Card "sem acesso" com o pedido

Arquivos: `pages/login/NoAccessCard.tsx`, `pages/login/noAccessView.ts` (novo) + teste, `pages/LoginPage.tsx`,
`contexts/AuthProvider.tsx` (expor `refreshSession()`), `styles/app.css`.

1. `noAccessView.ts`: `stateOf(request | null)` → `'form' | 'pending' | 'rejected'`; `validateRequest(office,
   message)` (obrigatório, tamanhos do banco); textos ("Pedido enviado em dd/mm…").
2. `NoAccessCard` busca `getMyAccessRequest()` ao abrir e mostra:
   - form: Escritório/empresa + Mensagem + "Enviar pedido";
   - pending: data + "Verificar de novo" (chama `refreshSession()`; aprovado → o `if (me)` do login leva ao hub);
   - rejected: nota + "Pedir de novo" (volta ao form).
3. Verificar no navegador (mock): `sem.acesso@exemplo.com` → form → pendente → aprovar pela página da etapa 5 →
   "Verificar de novo" entra no hub.

Commit sugerido: `Front: pedir acesso no card "sem acesso" (escritório e mensagem), com pedido pendente e recusado`

## Etapa 5 — Plataforma → Pedidos de acesso (com selo)

Arquivos: `navigation.ts` (item `pedidos`, rota `/plataforma/pedidos`, ícone `inbox`, `badge?: 'access-requests'`),
`App.tsx` (`PAGES`), `components/layout/AppLayout.tsx` (mostrar o selo), `hooks/usePendingRequests.ts` (novo),
`pages/platform/requests/` (novo): `AccessRequestsPage.tsx`, `requestColumns.tsx`, `ApprovePanel.tsx`,
`approveView.ts` + teste, `RejectPanel.tsx`.

1. Porteiro igual ao `ClientsPage` (sem `platform_staff` → "Área da equipe RA").
2. Abas Pendentes / Decididos (`PillGroup`), `DataTable` com nome, e-mail, escritório, mensagem, data e ações.
3. `ApprovePanel` (no molde do `InvitePanel`): rádio "Organização existente / Organização nova"; existente: org,
   papel na org, unidades com cargo cada; nova: nome, slug (sugerido a partir do nome), papel, 1ª unidade (código,
   nome, fuso). Regras e montagem do `ApprovalTarget` em `approveView.ts` (testado: slug, código, unidade
   obrigatória para `member`).
4. `RejectPanel`: nota opcional + confirmar.
5. Selo: `usePendingRequests()` busca `countPendingAccessRequests()` só para staff, ao montar o layout e depois de
   cada decisão (evento simples no módulo, ou `version` no contexto); `.nav .count` no CSS.
6. Verificar no navegador (mock): aprovar em org existente e em org nova, recusar, selo diminui.

Commit sugerido: `Front: Plataforma → Pedidos de acesso (aprovar em organização existente ou nova, recusar) com selo de
pendentes no menu`

## Etapa 6 — Verificação final (modo api, staging)

1. `npm test`, `npm run lint`, `npm run build`.
2. Com o schema `api` exposto e a migration aplicada: conta @gmail pede acesso; o Luís (staff) vê o selo, aprova numa
   org; a conta @gmail clica "Verificar de novo" e entra no hub. Conferir a `audit_log`.
3. Atualizar `apps/web/README.md` (mock: pedidos) e `docs/contrato-front-api.md` (funções do schema `api`).
