# Modo suporte "ver como" — plano de implementação

> **Para quem executa:** SUB-SKILL OBRIGATÓRIA: superpowers:subagent-driven-development (recomendada) ou superpowers:executing-plans, tarefa a tarefa. Os passos usam checkbox (`- [ ]`).

**Objetivo:** Owner/Dev navega no hub e nos dashboards como um membro da própria organização, só leitura, com faixa "Vendo como" e auditoria completa.

**Arquitetura:**
- Uma sessão de suporte no banco (`app.support_sessions`, 1 h) é criada pela API.
- O front manda `X-Support-Session` em toda chamada.
- `require_org`/`require_dashboard` validam a sessão e trocam o usuário efetivo pelo do membro.
- Um guarda global recusa toda rota fora de uma lista de permitidas.
- O front esconde admin e escrita e mostra a faixa.

**Stack:** Postgres/Supabase (migrations + testes SQL), FastAPI + asyncpg (pytest), React/Vite (vitest).

**Spec:** `docs/superpowers/specs/2026-11-24-modo-suporte-ver-como-design.md`

## Restrições globais

- Branch `feat/modo-suporte-ver-como`. **Sem commit:** o Luís commita. Cada tarefa termina com uma mensagem de commit sugerida.
- Migration aplicada no lexhub-v2 **só com OK do Luís**; acertar a versão no histórico depois (o MCP grava a hora).
- Indentação de 4 espaços. Textos de tela em pt-BR.
- Motivo: de 5 a 500 caracteres, sem espaços nas pontas. Validade: 1 h a partir do início, sem renovar.
- Quem pode usar: quem tem `org.dashboards.all` na organização (Owner/Dev). O alvo é um membro ativo da mesma organização, diferente de quem pede.
- Auditoria: `support.started`, `support.viewed`, `support.ended`.
  - `actor_user_id` = quem pede; `target_type = 'membership'` (o `list_audit` já resolve o nome); `target_id` = id da membership.
  - metadata: `session`, `reason` (só no started), `unit` e `dashboard` (só no viewed), `end_reason` (só no ended: `'exit' | 'expired'`).
- Erros da API em suporte:
  - 409 `{"detail": "support_expired"}`: sessão vencida ou encerrada;
  - 403 `{"detail": "support_read_only"}`: rota fora da lista;
  - 403 `"Sem acesso"`: sessão de outra pessoa ou organização, ou quem pede deixou de ser Owner/Dev.
- Testes SQL locais: container `lexhub-pgtest`, porta 55432, sempre com `PGCLIENTENCODING=UTF8`.

## Foco da revisão

1. **Quem pede é rebaixado durante a sessão:** a próxima chamada com o cabeçalho dá 403 e encerra a sessão. Teste na Tarefa 3.
2. **Membro desativado durante a sessão:** o hub dele fica vazio, porque `resolve_org` do membro falha. A resposta deve ser 409 `support_expired` (a sessão é encerrada), não um 403 confuso. Teste na Tarefa 3.
3. **Recarregar a aba no meio da sessão:** o modo volta (pelo `sessionStorage`) e a faixa reaparece. Se a sessão venceu nesse meio tempo, o primeiro 409 sai do modo com o aviso. Teste na Tarefa 5.
4. **Cache do hub misturando os dois mundos:** entrar e sair do modo limpa o `withSessionCache`, para não mostrar os cards do Dev como se fossem do membro, nem o contrário. Teste na Tarefa 4.
5. **Exportar ou favoritar pela URL ou por chamada direta:** a API recusa mesmo se o front falhar em esconder. Teste por rota na Tarefa 3.

---

### Task 1: Banco — sessões de suporte, vencimento e permissão do menu

**Arquivos:**
- Criar: `supabase/migrations/20261126100000_modo_suporte_ver_como.sql`
- Criar: `supabase/tests/modo_suporte_ver_como_test.sql`

**Interfaces (produz):**
- Tabela `app.support_sessions` com estas colunas:
  - `id uuid pk default gen_random_uuid()`, `org_id uuid not null → app.organizations on delete cascade`;
  - `actor_user_id uuid not null`, `target_user_id uuid not null`;
  - `target_membership_id uuid not null → app.memberships on delete cascade`;
  - `reason text not null check (char_length(btrim(reason)) between 5 and 500)`;
  - `started_at timestamptz not null default now()`, `expires_at timestamptz not null default now() + interval '1 hour'`;
  - `ended_at timestamptz`, `end_reason text check (end_reason in ('exit','expired'))`;
  - `check (actor_user_id <> target_user_id)`, `check ((ended_at is null) = (end_reason is null))`.
- Índice único parcial `(actor_user_id) where ended_at is null`: uma sessão aberta por pessoa.
- RLS ligada; `revoke all` de `public, anon, authenticated`; `grant select, insert, update` para `service_role`.
- `app_private.close_expired_support_sessions() returns integer`, security definer, `search_path=''`:
  - fecha as sessões com `ended_at is null and expires_at <= now()`, com `end_reason='expired'` e `ended_at=expires_at`;
  - insere um `support.ended` por sessão fechada (actor, org, alvo, metadata `{session, end_reason}`);
  - devolve quantas fechou.
- pg_cron `lexhub-close-support-sessions`, a cada 15 min (`'*/15 * * * *'`), no mesmo bloco `if exists cron` de `20261123140000_excluir_unidade_organizacao.sql:180-188`.
- `api.my_admin_permissions()` redefinida com o corpo de `20261116100000_plano_clientes.sql:315-336`, mais a chave `'support'`:
  - `true` se `app_private.has_org_permission(auth.uid(), v_org, 'org.dashboards.all')`, ou o equivalente usado em `access_scope`;
  - no ramo sem organização, `false`.

- [ ] **Passo 1: Escrever o teste SQL** (`begin … rollback`, padrão de `convite_primeiro_acesso_test.sql`). Cenário: org com Dev `d1`, colaborador `c1` e uma unidade. Casos:
  - inserir sessão `d1→c1` funciona;
  - uma segunda sessão aberta de `d1` dá `unique_violation`;
  - motivo `'abc'` dá `check_violation`;
  - `d1→d1` dá `check_violation`;
  - com `expires_at` no passado, `close_expired_support_sessions()` devolve 1, a sessão fica `end_reason='expired'` e existe 1 `support.ended` com `target_type='membership'`;
  - chamar de novo devolve 0;
  - `api.my_admin_permissions()` como `d1` tem `support = true`; como `c1`, `support = false`;
  - `authenticated` não consegue `select` em `app.support_sessions` (`insufficient_privilege`).
- [ ] **Passo 2: Rodar e ver falhar:** `$env:PGCLIENTENCODING='UTF8'; psql -h localhost -p 55432 -U postgres -f supabase/tests/modo_suporte_ver_como_test.sql`. Esperado: ERROR (a tabela não existe).
- [ ] **Passo 3: Escrever a migration** com as interfaces acima, comentada no estilo das vizinhas (o que é, se é aditiva, como desfazer).
- [ ] **Passo 4: Aplicar a migration no container e rodar o teste.** Esperado: só `NOTICE OK`. Depois, rodar todas as suítes de `supabase/tests` do mesmo jeito: nenhuma regressão.
- [ ] **Passo 5: Mensagem sugerida:** `feat(suporte): sessões de suporte no banco, vencimento por pg_cron e permissão no menu`

### Task 2: API — iniciar e encerrar a sessão

**Arquivos:**
- Criar: `apps/api/src/app/support.py` (repo + modelos)
- Criar: `apps/api/src/app/routes/support.py`
- Modificar: `apps/api/src/app/main.py` (`include_router`, junto dos outros em :202-211)
- Modificar: `apps/api/tests/conftest.py` (`FakeSupportRepo` + override)
- Testar: `apps/api/tests/test_support_sessions.py`

**Interfaces (produz):**
```python
@dataclass(frozen=True)
class SupportSession:
    id: str; org_id: str; actor_user_id: str; target_user_id: str
    target_membership_id: str; expires_at: datetime; ended_at: datetime | None

class SupportRepo(Protocol):
    async def can_support(self, user_id: str, org_id: str) -> bool: ...           # org.dashboards.all
    async def member(self, org_id: str, membership_id: str) -> dict | None: ...    # ativo: {user_id, name, avatar_path, role_label, units:[{code,name}]}
    async def start(self, org_id: str, actor: str, member: dict, reason: str) -> SupportSession: ...  # encerra a aberta anterior ('exit') e cria
    async def get(self, session_id: str) -> SupportSession | None: ...
    async def end(self, session_id: str, end_reason: str) -> bool: ...            # False se já estava encerrada
def get_support_repo(pool = Depends(get_db_pool)) -> SupportRepo
class SupportStartIn(BaseModel): membership_id: UUID; reason: str  # strip; 5..500
class SupportMemberOut(BaseModel): membership_id: str; name: str; avatar_path: str | None; role_label: str; units: list[UnitOut]
class SupportSessionOut(BaseModel): session_id: str; expires_at: datetime; member: SupportMemberOut
```
- `POST /orgs/{org_slug}/support/sessions` → 201 `SupportSessionOut`.
  - Quem não é Owner/Dev recebe 403 "Só Owner e Desenvolvedor usam o modo suporte."; membro de fora, inativo ou a própria pessoa recebe 404 "Membro não encontrado nesta organização."
  - Grava `support.started`. Quando `start` encerra uma sessão anterior, grava também o `support.ended` (`exit`) dela.
- `DELETE /orgs/{org_slug}/support/sessions/{session_id}` → 204.
  - Só o dono da sessão; outra pessoa recebe 404. Grava `support.ended` (`exit`) se `end` devolveu True.
  - É idempotente: sessão já encerrada também dá 204.
- `PgSupportRepo`:
  - `can_support` usa a mesma expressão do `'support'` da Tarefa 1;
  - `member` reaproveita o `member_json`/`role_label` existentes (ver o `support.py` da branch `feat/modo-suporte`, commit 992c870, como referência; não copiar a grade);
  - `units` = unidades ativas em que o membro tem cargo, ou todas as unidades ativas se o cargo de org for owner/admin.

- [ ] **Passo 1: Escrever os testes que falham:**
  - `test_inicia_sessao_201_e_audita`: verificar `support.started` com `metadata.reason` e `target_type == 'membership'`;
  - `test_nao_owner_dev_403`;
  - `test_membro_de_outra_org_404`;
  - `test_ver_a_si_mesmo_404`;
  - `test_motivo_curto_422` (com `"abc"` e `"   abcd  "`);
  - `test_iniciar_de_novo_encerra_a_anterior`: dois `started` e um `ended` com `end_reason == 'exit'`;
  - `test_encerra_204_e_audita`;
  - `test_encerrar_duas_vezes_audita_uma`;
  - `test_encerrar_sessao_de_outro_404`.
- [ ] **Passo 2:** `cd apps/api; python -m pytest tests/test_support_sessions.py -q`. Esperado: FAIL (módulo não existe).
- [ ] **Passo 3:** Implementar `support.py`, `routes/support.py` e o `FakeSupportRepo` (em memória: sessões e membros por org).
- [ ] **Passo 4:** `python -m pytest -q`. Esperado: tudo passa.
- [ ] **Passo 5: Mensagem sugerida:** `feat(suporte): API inicia e encerra a sessão de suporte`

### Task 3: API — usuário efetivo, lista de rotas permitidas e `support.viewed`

**Arquivos:**
- Modificar: `apps/api/src/app/access.py`: `require_org` e `require_dashboard` leem o cabeçalho; `OrgAccess`/`DashboardAccess` ganham `support: SupportContext | None = None`.
- Criar: `apps/api/src/app/support_guard.py`
- Modificar: `apps/api/src/app/main.py`: `FastAPI(dependencies=[Depends(support_guard)])`, ou `dependencies` em cada `include_router`, desde que cubra todas as rotas.
- Modificar: `apps/api/src/app/routes/catalog.py` (`list_dashboards`) e `apps/api/src/app/routes/dashboards.py` (`dashboard_data`, negação)
- Testar: `apps/api/tests/test_support_mode.py`

**Interfaces:**
- Consome: `SupportRepo.get/end/can_support` (Tarefa 2).
- Produz:
```python
SUPPORT_HEADER = "X-Support-Session"
@dataclass(frozen=True)
class SupportContext: session_id: str; actor: CurrentUser; target_membership_id: str
async def resolve_support(request, user: CurrentUser, org_id: str, support: SupportRepo, audit: AccessRepo) -> SupportContext | None
# sem cabeçalho -> None
# sessão inexistente, de outro dono ou de outra org -> 403 "Sem acesso"
# ended_at ou expires_at <= now -> end('expired'); se end() devolveu True, audita support.ended; 409 "support_expired"
# quem pede perdeu org.dashboards.all -> end('exit') + support.ended; 403 "Sem acesso"
SUPPORT_ALLOWED: frozenset[tuple[str, str]]  # (método, path do template da rota)
```
- `SUPPORT_ALLOWED` = `GET /me`, `GET /orgs/{org_slug}/dashboards`, `GET /orgs/{org_slug}/favorites`, `GET /orgs/{org_slug}/hub-order`, `GET /orgs/{org_slug}/units/{unit_code}/dashboards/{dashboard_key}`, `GET …/{dashboard_key}/access`, `GET /orgs/{org_slug}/sources/freshness`, `DELETE /orgs/{org_slug}/support/sessions/{session_id}`, `GET /orgs/{org_slug}/support/sessions/{session_id}/hidden` (Tarefa 7) e `GET /health*`.
- `support_guard(request)`: com o cabeçalho e `(request.method, request.scope["route"].path)` fora da lista, responde 403 `support_read_only`. Sem cabeçalho, não faz nada.
- **Troca do usuário:**
  - `require_org`, com sessão válida, devolve `OrgAccess(user=CurrentUser(user_id=target_user_id, email=None, claims={}), …, support=ctx)`. Se o membro não resolve mais a org (`resolve_org(target)` é None), encerra a sessão (`expired`) e responde 409 `support_expired`.
  - `require_dashboard` faz a mesma troca antes de `resolve_access`.
  - Negação em suporte: 403 **sem** gravar `dashboard.access_denied`.
- **`list_dashboards` em suporte:** zera `can_export`, `can_toggle` e `disabled_units` em toda linha do catálogo.
- **`dashboard_data` em suporte:**
  - `can_export` sai como `False` no `meta`/summary, se existir na resposta.
  - Grava `support.viewed` (actor = quem pede, metadata `{session, unit, dashboard}`) no máximo 1 vez por `(session, unit, dashboard)` a cada 5 min. O dedup fica em memória do processo (`dict` com hora), como o `result_memo`, porque a API roda com um worker.
  - `member_ref` usa `access.user.user_id`, que já é o do membro.

- [ ] **Passo 1: Escrever os testes que falham.** Os fakes da Tarefa 2 e os existentes bastam:
  - `test_catalogo_e_do_membro`: o `catalog_repo` tem linhas diferentes para o Dev e para o membro; com o cabeçalho, vêm as do membro, com `can_export` e `can_toggle` falsos;
  - `test_dashboard_usa_escopo_do_membro`: `repo.scopes[(membro, …)] = 'own'`, o dado vem filtrado pelo `member_ref` do membro;
  - `test_rotas_de_escrita_403_read_only`: parametrizado com `POST favorites`, `DELETE favorites`, `PUT hub-order`, `GET export`, `PUT …/enabled` e `POST support/sessions`. Cada uma dá 403 `support_read_only`;
  - `test_sessao_vencida_409_e_audita_uma_vez` (duas chamadas, um `ended`);
  - `test_sessao_de_outro_403`;
  - `test_dev_rebaixado_403_encerra`;
  - `test_membro_desativado_409`;
  - `test_negacao_em_suporte_nao_audita_access_denied`;
  - `test_viewed_uma_vez_em_5_min` (relógio trocável: `get_today`/`now` injetado como dependency);
  - `test_sem_cabecalho_nada_muda` (smoke de uma rota de escrita).
- [ ] **Passo 2:** `python -m pytest tests/test_support_mode.py -q`. Esperado: FAIL.
- [ ] **Passo 3:** Implementar conforme as interfaces.
- [ ] **Passo 4:** `python -m pytest -q`. Esperado: tudo passa, inclusive `test_access.py` e `test_catalog.py` sem mudança.
- [ ] **Passo 5: Mensagem sugerida:** `feat(suporte): API responde como o membro, só leitura, e registra o que foi aberto`

### Task 4: Front — sessão, cabeçalho e cliente de dados

**Arquivos:**
- Criar: `apps/web/src/lib/supportSession.ts` (+ `.test.ts`)
- Modificar: `apps/web/src/services/http.ts`: opção `getHeaders?: () => Record<string, string>`, aplicada em `send`.
- Modificar: `apps/web/src/services/client.ts`:
  - interface `DataClient` ganha `startSupport` e `endSupport`;
  - a criação do `createHttp` passa `getHeaders: supportHeaders`.
- Modificar: `apps/web/src/services/apiClient.ts`, `apps/web/src/services/mockClient.ts`, `apps/web/src/services/sessionCache.ts`
- Modificar: `apps/web/src/types/index.ts`: `SupportSession`, `AdminPermissions.support`.
- Modificar: `apps/web/src/navigation.ts`: `menuPermissions` com erro devolve `support: false`.
- Testar: `http.test.ts`, `sessionCache.test.ts`, `lib/supportSession.test.ts`

**Interfaces (produz):**
```ts
export type SupportSession = {
    sessionId: string; org: string; expiresAt: string; reason: string
    member: { membershipId: string; name: string; avatarPath: string | null; roleLabel: string; units: Unit[] }
}
// lib/supportSession.ts — memória + sessionStorage 'lexhub.support'
export function getSupport(): SupportSession | null
export function setSupport(s: SupportSession | null): void
export function onSupportChange(fn: (s: SupportSession | null) => void): () => void
export function supportHeaders(): Record<string, string>   // {} ou { 'X-Support-Session': id }
// DataClient
startSupport(org: string, membershipId: string, reason: string): Promise<SupportSession>
endSupport(org: string, sessionId: string): Promise<void>
```
- `withSessionCache`: `startSupport` e `endSupport` chamam `clearAll()` depois de dar certo. Um 409 `support_expired` em qualquer chamada também chama `clearAll()` (ver a Tarefa 5).
- Mock: guarda a sessão; com sessão ativa, `listDashboards` devolve um catálogo reduzido do membro (2 dashboards) com `can_export`/`can_toggle` falsos, e as escritas lançam `DataError(403, 'support_read_only')`. Para simular vencimento, `localStorage['lexhub.mock.supportExpired']='1'` faz a próxima chamada lançar `DataError(409, 'support_expired')`.

- [ ] **Passo 1: Testes que falham:**
  - `http`: com `getHeaders` devolvendo o cabeçalho, ele vai em toda chamada; sem a opção, nada muda;
  - `supportSession`: `set`/`get` sobrevivem a recriar o módulo via `sessionStorage`; `setSupport(null)` limpa; `onSupportChange` avisa;
  - `sessionCache`: `listDashboards` em cache e depois `startSupport` faz a próxima `listDashboards` ir ao cliente; o mesmo para `endSupport`.
- [ ] **Passo 2:** `cd apps/web; npx vitest run src/services src/lib/supportSession.test.ts`. Esperado: FAIL.
- [ ] **Passo 3:** Implementar.
- [ ] **Passo 4:** `npm test` e `npx tsc -b`. Esperado: tudo passa.
- [ ] **Passo 5: Mensagem sugerida:** `feat(web): sessão de suporte no cliente de dados`

### Task 5: Front — modo suporte na tela (faixa, menu, bloqueios)

**Arquivos:**
- Criar: `apps/web/src/contexts/SupportProvider.tsx`, `apps/web/src/contexts/support-context.ts` (`useSupport`)
- Criar: `apps/web/src/components/layout/SupportBanner.tsx` (+ `.test.tsx`); estilos em `styles/app.css`
- Modificar: `apps/web/src/App.tsx`:
  - `SupportProvider` dentro do `AuthProvider`;
  - em suporte, as rotas `/:org/admin/*` e `/plataforma/*` viram `<Navigate to="/:org/dashboards">`.
- Modificar: `apps/web/src/components/layout/AppLayout.tsx`:
  - faixa no topo;
  - em suporte, o menu mostra só a seção "Espaço de trabalho";
  - `units` vem de `support.member.units`;
  - o `OrgSwitcher` não troca de organização: o item de outra org fica escondido.
- Modificar: `apps/web/src/hooks/useLogDashboardView.ts`: não chama nada em suporte.
- Modificar: favoritar e reordenar (`useFavorites`, `useHubOrder` e quem renderiza estrela e arrastar), exportar (`ExportButton`, `julgados-acordaos/DadosFaltando.tsx`), ligar/desligar (`DashboardSwitchMenu`). Em suporte ficam escondidos; no lugar do botão de exportar aparece o texto "Somente leitura no modo suporte".
- Testar: `SupportBanner.test.tsx`, `contexts/support.test.tsx`, `navigation.test.ts`

**Interfaces:**
- Consome: Tarefa 4.
- Produz:
```ts
type SupportState = { session: SupportSession | null; start(membershipId: string, name: string, reason: string): Promise<void>; exit(): Promise<void> }
export function useSupport(): SupportState
```
- `start`: chama `startSupport`, guarda a sessão e navega para `/:org/dashboards`.
- `exit`: chama `endSupport` (falha é ignorada), limpa a sessão e navega para `/:org/admin/membros?m=<membershipId>`, reabrindo a gaveta. Se a página não lê `?m=`, adicionar essa leitura em `MembersPage`.
- Expiração:
  - o provider escuta 409 `support_expired`: um wrapper fino em `client.ts` chama `setSupport(null)` e dispara o aviso "A sessão de suporte venceu", com o mesmo mecanismo de aviso que já existe;
  - além disso, um timer local sai sozinho no `expiresAt`.
- Faixa: "Vendo como **{nome}** · {motivo} · termina em {mm} min · [Sair]", com a foto via `MemberAvatar`, cor de aviso (`--c-warn`/`badge warn`) e `role="status"`. No celular, o texto encolhe para "Vendo como {primeiro nome}" e o botão Sair.

- [ ] **Passo 1: Testes que falham:**
  - a faixa mostra nome e motivo, e Sair chama `exit`;
  - `visibleItems` em suporte devolve só Dashboards e Documentação (adicionar o parâmetro `support` em `navigation.ts`);
  - `useLogDashboardView` não chama `logDashboardView` com sessão ativa;
  - `ExportButton` em suporte mostra o texto de somente leitura;
  - um 409 limpa a sessão;
  - com `sessionStorage` já preenchido ao montar, o provider abre em modo suporte.
- [ ] **Passo 2:** `npx vitest run`. Esperado: FAIL nos novos.
- [ ] **Passo 3:** Implementar.
- [ ] **Passo 4:** `npm test`, `npx tsc -b`, `npm run lint`. Esperado: tudo passa.
- [ ] **Passo 5: Mensagem sugerida:** `feat(web): modo suporte — faixa "Vendo como", menu e ações só leitura`

### Task 6: Front — entrada pela gaveta de Membros e auditoria

**Arquivos:**
- Modificar: `apps/web/src/pages/admin/members/MemberDetail.tsx`: botão "Ver como este membro", só com `perms.support`, membro ativo e `!isSelf`.
- Criar: `apps/web/src/pages/admin/members/SupportReasonDialog.tsx` (+ `.test.tsx`): `<dialog>` no padrão do `ui/Modal.tsx`. Campo "Motivo (ex.: número do chamado)", contador até 500, botão "Começar" desativado com menos de 5 caracteres; Esc fecha.
- Modificar: `apps/web/src/services/auditEvents.ts`:
  - `support.started` → kind `support`, ação "Iniciou suporte", detalhe `como {targetName}: {reason}`;
  - `support.viewed` → "Abriu dashboard em suporte", detalhe `{dashboard} ({unit}) como {targetName}`; o nome do dashboard vem do `dashboardName` já usado em `dashboard.view`;
  - `support.ended` → "Encerrou suporte", detalhe "venceu" ou "saiu".
  - Remover o comentário de :195, já que `kindOptions` passa a incluir `support` naturalmente.
- Modificar: `apps/web/src/services/mockClient.ts`: a auditoria mock grava os três eventos.
- Testar: `auditEvents.test.ts`, `SupportReasonDialog.test.tsx`, `MemberDetail` (botão some para não-Owner/Dev, para si mesmo e para inativo).

- [ ] **Passo 1:** Testes que falham (os listados acima, mais `kindOptions()` contendo `'support'`).
- [ ] **Passo 2:** `npx vitest run src/services/auditEvents.test.ts src/pages/admin/members`. Esperado: FAIL.
- [ ] **Passo 3:** Implementar.
- [ ] **Passo 4:** `npm test`. Esperado: tudo passa.
- [ ] **Passo 5: Conferir no mock (navegador):**
  - gaveta → Ver como → motivo → hub do membro com a faixa;
  - abrir um dashboard;
  - tentar `/lexgroup/admin/membros`, que volta ao hub;
  - Sair, que volta à gaveta;
  - Auditoria mostra os três eventos no filtro Suporte;
  - conferir também no celular e no tema escuro.
- [ ] **Passo 6: Mensagem sugerida:** `feat(web): "Ver como este membro" na gaveta e eventos de suporte na auditoria`

### Task 7: "Por que não aparece" (separável)

**Arquivos:**
- Criar: `supabase/migrations/20261126110000_suporte_explica_acesso.sql`
- Criar: `supabase/tests/suporte_explica_acesso_test.sql`
- Modificar: `apps/api/src/app/support.py`, `apps/api/src/app/routes/support.py`
- Criar: `apps/web/src/pages/dashboards/HiddenForMember.tsx` (+ test); usar em `HubPage.tsx` só em suporte.

**Interfaces:**
- `app_private.dashboard_access_explain(p_user uuid, p_unit uuid, p_dashboard text) returns table (scope text, via text, reason text)`:
  - ponto de partida: o arquivo da branch `feat/modo-suporte` (`git show feat/modo-suporte:supabase/migrations/20261123120000_modo_suporte.sql`);
  - conferir passo a passo contra `app_private.dashboard_access` **de `20261119170000_grupos_acesso.sql`**, que é a definição vigente;
  - `dashboard_access` vira invólucro dela, com a mesma assinatura e zero linhas quando nega.
- `GET /orgs/{org_slug}/support/sessions/{session_id}/hidden?unit=CODE` devolve `[{key, title, area, reason}]`:
  - só os disponíveis na unidade que o membro não vê;
  - `reason` ∈ `org_inactive | dashboard_off | not_member | no_unit_role | no_sector_rule`;
  - exige a sessão válida do chamador.
- Textos (front):
  - `no_unit_role` "Sem cargo nesta unidade";
  - `no_sector_rule` "Os setores dele não têm este dashboard e não há exceção";
  - `dashboard_off` "Desligado nesta unidade";
  - `not_member` "Não é membro ativo";
  - `org_inactive` "Unidade ou organização inativa".
- Bloco recolhível "Dashboards ocultos para {primeiro nome} ({n})" no fim do hub, por unidade selecionada.

- [ ] **Passo 1:** Teste SQL de paridade: para todos os usuários, unidades e dashboards dos cenários de `grupos_acesso_test.sql` e `acesso_test.sql`, `explain` visível ⇔ `dashboard_access` devolve linha, com o mesmo `scope`. Mais um caso por `reason`.
- [ ] **Passo 2:** Rodar e ver falhar (a função não existe).
- [ ] **Passo 3:** Migration. Rodar **todas** as suítes SQL: as de acesso têm que passar sem mudança.
- [ ] **Passo 4:** Testes da API (`test_hidden_exige_sessao`, `test_hidden_lista_motivos`) e do front (lista e textos). Implementar. `python -m pytest -q` e `npm test`.
- [ ] **Passo 5: Mensagem sugerida:** `feat(suporte): hub em suporte mostra por que cada dashboard está oculto`

### Task 8: Verificação final

- [ ] `cd apps/api; python -m pytest -q`; `cd apps/web; npm test; npx tsc -b; npm run lint; npm run format:check; npm run build`. Todas as suítes SQL no `lexhub-pgtest`.
- [ ] Roteiro no mock de ponta a ponta (Tarefa 6, Passo 5) mais o vencimento (`lexhub.mock.supportExpired`).
- [ ] Listar para o Luís:
  - as 2 migrations a aplicar no lexhub-v2 (com OK dele);
  - a ordem de deploy: migrations → API → front, porque o front novo chama rotas novas;
  - o teste em modo api que ele precisa fazer.
