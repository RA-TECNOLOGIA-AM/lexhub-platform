# Auditoria: dashboards abertos + filtro de período — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** registrar cada abertura de dashboard na Auditoria (`dashboard.view`) e filtrar a Auditoria por período e tipo no banco.

**Architecture:** uma migration cria `api.log_dashboard_view` (grava com repetição < 5 min ignorada) e troca `api.list_audit` por uma versão com `p_from/p_to/p_actions`. O front chama o log ao abrir o dashboard (hook próprio) e a Auditoria ganha o campo Período, que vai para a URL e para a consulta.

**Tech Stack:** Postgres 17 / Supabase (plpgsql, testes SQL com rollback), React 19 + TypeScript, Vitest.

**Spec:** `docs/superpowers/specs/2026-11-19-auditoria-dashboards-abertos-design.md`

## Global Constraints

- Evento: `action = 'dashboard.view'`, `target_type = 'dashboard'`, `target_id = <chave>`, `metadata = {org, unit}`.
- Repetição: mesma pessoa + dashboard + unidade em **menos de 5 minutos** não grava.
- O registro nunca impede o dashboard de abrir (falha ignorada no front).
- Rótulos: tipo novo **"Dashboards abertos"**, ação **"Abriu dashboard"**; "Acesso" vira **"Mudanças de acesso"**.
- Período padrão **7 dias**; opções 7, 30, 90 dias e datas livres. Até **2000** eventos por consulta; acima disso a tela avisa.
- Indentação 4 espaços; código e comentários em pt-BR, no estilo dos arquivos vizinhos.

## Review Focus

- F5 / StrictMode / clique duplo no mesmo dashboard → uma linha só (teste SQL de repetição).
- Mesma pessoa abrindo o mesmo dashboard em **outra unidade** dentro de 5 min → duas linhas (teste SQL).
- Pessoa de fora da org, unidade de outra org ou chave inexistente → recusado, nada gravado (teste SQL).
- Tipo "Outros" e "Nunca acessou" não mandam lista de actions ao banco (teste do mapeamento).
- Período inválido na URL (`?de=lixo`) → volta para 7 dias, sem quebrar a tela (teste de `filterFromParams`).

---

### Task 1: Migration + teste SQL

**Files:**
- Create: `supabase/migrations/20261119210000_auditoria_dashboards_abertos.sql`
- Create: `supabase/tests/auditoria_dashboards_abertos_test.sql`

**Interfaces:**
- Produces: `api.log_dashboard_view(p_org text, p_unit text, p_dashboard text) returns boolean` (true = gravou, false = repetição); `api.list_audit(p_org text, p_from timestamptz default null, p_to timestamptz default null, p_actions text[] default null, p_limit integer default 2000) returns jsonb` → `{events: [...mesmo formato de hoje], truncated: boolean}`. `null` = sem limite naquele lado / sem filtro de action.

- [ ] **Step 1: Teste SQL** (padrão de `auditoria_exportar_test.sql`: `begin` … `rollback`, `raise exception 'FALHOU: …'`). Cenário: org A com unidades `NG` e `LA`, dashboard do catálogo; Dev (audit.view) e colaborador; org B com unidade `XX`. Casos:
  - colaborador: `log_dashboard_view('org-a','NG',key)` = true; de novo = false; com `'LA'` = true → 2 linhas `dashboard.view`.
  - unidade de outra org, chave inexistente e não-membro → erro, nada gravado.
  - Dev: `list_audit` com `p_actions = '{dashboard.view}'` → só as 2; com `p_from = now() + interval '1 day'` → 0; com `p_limit = 1` → 1 evento e `truncated = true`; sem filtros → inclui tudo e `truncated = false`.
  - colaborador chamando `list_audit` → 42501.
- [ ] **Step 2: Rodar contra o banco sem a migration → falha** (função não existe). Banco de teste: `docker run -d --name pg-audit -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:17`, depois `supabase/tests/ci/supabase_stub.sql` + migrations em ordem, como o `ci.yml`.
- [ ] **Step 3: Migration.** `log_dashboard_view`: security definer, `search_path = ''`; org ativa por slug e `v_org = any(app_private.my_org_ids())` senão 42501; unidade por `upper(trim(p_unit))` na org e chave em `app.dashboard_catalog`, senão 22023; repetição = `exists` em `app.audit_log` (org, `auth.uid()`, action, target_id, `metadata->>'unit'`, `created_at > now() - interval '5 minutes'`). `list_audit`: `drop function api.list_audit(text, integer)` e recriar com os novos parâmetros, mesmo corpo de `20261119090000_auditoria_email.sql` + `where` de período/actions, busca `limit + 1` para saber `truncated`. Grants como os vizinhos (`revoke … from public, anon; grant … to authenticated`). Bloco de Rollback no fim.
- [ ] **Step 4: Rodar migration + teste → passa** (só os avisos `OK`). Rodar também os outros `supabase/tests/*.sql` (o de exportar chama `list_audit('org')`).
- [ ] **Step 5: Commit** `feat(auditoria): registro de dashboard aberto e list_audit com período/tipo`.

### Task 2: Cliente de dados (tipos, eventos, Supabase, mock)

**Files:**
- Modify: `apps/web/src/types/index.ts` (`AuditKind` + `'view'`; `AuditResponse` + `truncated: boolean`; tipo `AuditQuery`)
- Modify: `apps/web/src/pages/admin/audit/auditView.ts` (`KIND`: `view: { label: 'Dashboards abertos', badge: 'badge info' }`, `access.label = 'Mudanças de acesso'`)
- Modify: `apps/web/src/services/auditEvents.ts` (regra `dashboard.view`; export `actionsOf`)
- Modify: `apps/web/src/services/client.ts`, `auditClient.ts`, `mockClient.ts`
- Test: `auditEvents.test.ts`, `auditClient.test.ts`

**Interfaces:**
- Consumes: Task 1 (`list_audit`, `log_dashboard_view`).
- Produces:
  - `type AuditQuery = { from: string | null; to: string | null; kind: AuditKind | '' }` (ISO).
  - `actionsOf(kind: AuditKind | ''): string[] | null` — actions de `EVENTS` com aquele kind; `''` e `'other'` → `null`.
  - `DataClient.getAudit(org: string, query: AuditQuery): Promise<AuditResponse>`
  - `DataClient.logDashboardView(org: string, unit: string, dashboardKey: string): Promise<void>`

- [ ] **Step 1: Testes.** `toAuditEvent` de `dashboard.view` com `targetName 'Comercial (LexPre)'`, `metadata {unit:'NG'}` → `{kind:'view', action:'Abriu dashboard', detail:'Comercial (LexPre) · NG'}`. `actionsOf('view')` = `['dashboard.view']`; `actionsOf('other')` e `actionsOf('')` = `null`. `getAudit('lexgroup', {from:'A', to:'B', kind:'view'})` chama `list_audit` com `{p_org, p_from:'A', p_to:'B', p_actions:['dashboard.view']}` e devolve `truncated`; `logDashboardView('lexgroup','NG','comercial')` chama `log_dashboard_view` com `{p_org, p_unit, p_dashboard}`. Atualizar o teste atual de `list_audit` para os args novos.
- [ ] **Step 2: `npm test` → falham.**
- [ ] **Step 3: Implementar.** Mock: `getAudit` filtra a lista do mock por período/kind e devolve `truncated:false`; `logDashboardView` adiciona evento `view` no store (sem repetição em 5 min).
- [ ] **Step 4: `npm test` + `npx tsc -b` → passam** (o `AuditPage` ainda chama `getAudit(org)`: ajustar a chamada nesta task para `{from:null,to:null,kind:''}` só para compilar; Task 3 troca).
- [ ] **Step 5: Commit** `feat(auditoria): cliente com período/tipo e registro de dashboard aberto`.

### Task 3: Filtro Período na Auditoria

**Files:**
- Modify: `apps/web/src/pages/admin/audit/auditView.ts`, `AuditFilters.tsx`, `AuditPage.tsx`
- Test: `apps/web/src/pages/admin/audit/auditView.test.ts`

**Interfaces:**
- Consumes: `AuditQuery`, `getAudit(org, query)` (Task 2).
- Produces: `AuditFilter` ganha `period: '7' | '30' | '90' | 'custom'`, `de: string`, `ate: string` (`'YYYY-MM-DD'`); `queryFromFilter(f: AuditFilter, now?: Date): AuditQuery`.

- [ ] **Step 1: Testes.** URL `?periodo=30` ↔ filtro (ida e volta); sem `periodo` → `'7'`; `?periodo=custom&de=lixo` → `'7'`; `queryFromFilter({period:'7'}, new Date('2026-11-19T12:00:00-04:00'))` → `from` = 7 dias antes, `to: null`; custom `de 2026-11-01 ate 2026-11-10` → `from 2026-11-01T00:00:00-04:00`, `to 2026-11-11T00:00:00-04:00` (fim inclusivo, fuso Manaus); kind `'nunca'` → `kind ''` na query.
- [ ] **Step 2: `npm test` → falham.**
- [ ] **Step 3: Implementar.** `AuditFilters`: select "Período" (Últimos 7 dias / 30 dias / 90 dias / Escolher datas) e, em custom, dois `<input type="date">` com rótulos "De" e "Até". `AuditPage`: `useAsync(() => dataClient.getAudit(org, queryFromFilter(filter)), [org, período, de, ate, kind])`; `truncated` → `<Notice>` "Mostrando os 2000 eventos mais recentes. Estreite o período para ver o resto."; descrição do cabeçalho passa a citar dashboards abertos.
- [ ] **Step 4: `npm test`, `npx tsc -b`, `npx oxlint`, `prettier --check` → passam.**
- [ ] **Step 5: Commit** `feat(auditoria): filtro de período e tipo Dashboards abertos`.

### Task 4: Registrar a abertura no dashboard

**Files:**
- Create: `apps/web/src/hooks/useLogDashboardView.ts`
- Modify: `apps/web/src/pages/dashboards/DashboardView.tsx`

**Interfaces:**
- Consumes: `dataClient.logDashboardView` (Task 2).
- Produces: `useLogDashboardView(org: string, unit: string, dashboardKey: string): void`.

- [ ] **Step 1: Implementar** o hook: `useEffect` com deps `[org, unit, dashboardKey]`, chama `logDashboardView` e engole o erro (`.catch(() => {})`). Chamar no topo do `DashboardView` com `module.key`. Sem teste unitário (não há testing-library); prova no passo 2.
- [ ] **Step 2: Verificar no navegador (modo mock):** abrir um dashboard, trocar período/filtro, voltar ao hub e abrir de novo, abrir em outra unidade → Auditoria com "Dashboards abertos" mostra 2 linhas (mesma unidade em < 5 min conta uma vez); Período "Escolher datas" filtra; topbar/console sem erro.
- [ ] **Step 3: Commit** `feat(dashboards): registra a abertura na auditoria`.

### Task 5: Banco do lexhub-v2 (com o Luís)

- [ ] **Step 1:** Com OK do Luís, aplicar a migration no lexhub-v2 e acertar a versão no histórico para `20261119210000` (regra de `lexhub-migration-history`). Conferir `list_migrations` = arquivos.
- [ ] **Step 2:** Rodar o teste SQL no lexhub-v2 dentro de transação com rollback.
