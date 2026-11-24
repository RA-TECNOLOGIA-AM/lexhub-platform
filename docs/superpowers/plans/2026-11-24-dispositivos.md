# Dispositivos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Luís pediu sem subagentes). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Seção Dispositivos em Configurações: listar as próprias sessões, desconectar uma/um grupo/todas as outras/esta, e o aparelho derrubado sai em até 1 minuto.

**Architecture:** Duas funções `api.*` sobre `auth.sessions`, chamadas direto do front (`createRpc`). Seção nova no `SECTIONS` do `SettingsDialog`. O `usePresenceHeartbeat` passa a conferir `isSessionAlive` e, se morta, sai para `/login?estado=desconectado`.

**Tech Stack:** Postgres/Supabase (migration + teste SQL em transação), React/TS, vitest.

**Spec:** `docs/superpowers/specs/2026-11-24-dispositivos-design.md`

## Global Constraints

- Indentação 4 espaços; comentários em pt-BR no estilo "Módulo: ...".
- Sem commits (o Luís commita). Migration só no lexhub-v2 com OK do Luís.
- Testes que tocam Web Storage: `vi.stubGlobal('sessionStorage', memoryStorage())`; rodar `NODE_OPTIONS=--no-experimental-webstorage npx vitest run`.
- Textos: "Este dispositivo", "Desconectar", "Confirmar?", "Desconectar todos os outros", "Sair deste dispositivo", "Você foi desconectado em outro aparelho.", auditoria "Desconectou um aparelho" (tipo `login`).

## Review Focus

1. Revogar o id de outra pessoa (ou inexistente) → erro, nada apagado, nada auditado.
2. Token sem `session_id` (service/anon) → `current` false em tudo, sem erro.
3. Rede caída no heartbeat → `isSessionAlive` devolve true (não desloga por falha de rede).
4. Vários logins do mesmo navegador/IP → uma linha com o total; desconectar apaga todas.
5. A sessão atual nunca entra num grupo nem pode ser "revogada" pela função (só "Sair").

---

### Task 1: Migration + teste SQL

**Files:**
- Create: `supabase/migrations/20261126120000_dispositivos.sql`
- Test: `supabase/tests/dispositivos_test.sql`

**Interfaces — Produces:**
- `api.list_my_sessions() returns table(id uuid, created_at timestamptz, last_active_at timestamptz, user_agent text, ip text, current boolean)`; `last_active_at = coalesce(refreshed_at, updated_at, created_at)`; `ip = host(ip)`; filtro `user_id = auth.uid() and (not_after is null or not_after > now())`; ordem `current desc, last_active_at desc`; `current = id::text = auth.jwt()->>'session_id'`.
- `api.revoke_my_session(p_id uuid) returns void`: se `p_id` é a sessão atual → `raise 'use_sign_out'`; se não é de `auth.uid()` → `raise 'session_not_found'` (errcode P0002); senão insere `auth.session_revoked` (target_type `session`, target_id id, metadata `{ip, userAgent}`, uma linha por membership ativa) e apaga de `auth.sessions`.
- Ambas `security definer`, `search_path = ''`, revoke de public/anon, grant a authenticated.

- [ ] Teste (transação + rollback, `set local role authenticated` + `request.jwt.claims` com `sub` e `session_id`): lista só as 2 sessões de u1 (não a de u2), a atual primeiro com `current`; revogar a de u2 → erro `session_not_found`; revogar a atual → `use_sign_out`; revogar a outra de u1 → some de `auth.sessions` e 1 linha `auth.session_revoked`; claims sem `session_id` → nenhuma `current`.
- [ ] Rodar no lexhub-pgtest (falha), escrever a migration, rodar de novo: só `OK`.

### Task 2: Cliente de dados

**Files:** `apps/web/src/types/index.ts`, `services/client.ts`, `services/devicesClient.ts` (novo), `services/apiClient.ts`, `services/mockClient.ts`, `services/auditEvents.ts`; teste `services/mockDevices.test.ts`.

**Produces:**
- `type DeviceSession = { id: string; createdAt: string; lastActiveAt: string; userAgent: string | null; ip: string | null; current: boolean }`
- `DataClient.listMySessions(): Promise<DeviceSession[]>`, `DataClient.revokeMySession(id: string): Promise<void>`.
- Mock: 4 sessões (atual Chrome·Windows; 2 do mesmo Android/IP; 1 TV) em memória; revoke remove; `signOutOthers` deixa só a atual.
- `auditEvents`: `'auth.session_revoked': { kind: 'login', action: 'Desconectou um aparelho', detail: userAgent · ip }`.

- [ ] Teste do mock: lista 4 com a atual primeiro; revoke tira 1; signOutOthers deixa 1. Teste em `auditEvents.test` do rótulo.

### Task 3: Agrupamento (lógica pura)

**Files:** `apps/web/src/components/settings/devices.ts` + `devices.test.ts`.

**Produces:**
- `type DeviceKind = 'computer' | 'phone' | 'tv'`; `deviceKind(ua: string | null): DeviceKind` (TV = `describeUserAgent` "TV (QR)"; Android/iOS = phone; resto computer).
- `type DeviceGroup = { key: string; ids: string[]; label: string; ip: string | null; kind: DeviceKind; lastActiveAt: string; current: boolean }`
- `groupSessions(sessions: DeviceSession[]): DeviceGroup[]` — a atual sozinha e primeiro; as outras agrupadas por `ip + describeUserAgent` (label "Aparelho desconhecido" se null), `lastActiveAt` = o maior, ordem por ele desc.

- [ ] Testes: atual primeiro e sozinha mesmo com outra igual; 2 Android mesmo IP = 1 grupo com 2 ids; kinds; ordem.

### Task 4: Seção Dispositivos

**Files:** `components/settings/DevicesSection.tsx` + teste, `SettingsDialog.tsx` (item `dispositivos`, ícone novo), `components/ui/Icon.tsx` (ícones `monitor`, `phone`, `tv`), `settings.css`.

- Carrega `listMySessions`; estados carregando/erro/lista. Linha: ícone, label (+ "· N sessões" se >1), IP, "ativo há …" (formatador relativo existente em Membros, se houver; senão um local).
- Botão de linha: 1º clique → "Confirmar?" (volta em 4 s), 2º → revoga cada id e recarrega. Linha atual: "Sair deste dispositivo" → `useAuth().signOut()`.
- "Desconectar todos os outros" (só se houver outros), com a mesma confirmação → `signOutOthers` e recarrega.
- [ ] Teste de render (`renderToStaticMarkup` de uma view pura `DevicesList` com grupos): "Este dispositivo", label, contagem.

### Task 5: Saída em até 1 minuto

**Files:** `hooks/usePresenceHeartbeat.ts` (+ teste se existir padrão), `components/layout/AppLayout.tsx`, `pages/LoginPage.tsx`.

- `usePresenceHeartbeat(enabled, onSessionGone: () => void)`: a cada batida, também `dataClient.isSessionAlive()`; false → `onSessionGone()` uma vez.
- AppLayout: `onSessionGone` = `leaveSupport` + `dataClient.signOut()` + `window.location.replace('/login?estado=desconectado')` (exposto pelo AuthProvider como `signOutGone()`).
- LoginPage: `estado=desconectado` → "Você foi desconectado em outro aparelho."
- [ ] Teste: com isSessionAlive=false chama onSessionGone 1 vez.

### Task 6: Verificação

- [ ] `pnpm`/`npx` vitest (com a flag), oxlint, prettier, tsc; teste SQL.
- [ ] Navegador (mock, porta 5181): abrir Configurações → Dispositivos, desconectar grupo, "todos os outros".
