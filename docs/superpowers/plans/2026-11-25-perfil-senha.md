# Perfil: criar e alterar senha — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** bloco Senha em Configurações → Perfil (criar/alterar), com status vindo do banco e auditoria por trigger.

**Architecture:** migration com `api.my_password_status()` + trigger em `auth.users` que grava `auth.password_changed`;
front chama `auth.updateUser({ password })` e a RPC pelo `profileClient`; mock equivalente; UI num componente próprio
dentro do `ProfileSection`.

**Tech Stack:** Postgres/Supabase (plpgsql), React + Vite + Vitest, supabase-js.

**Spec:** `docs/superpowers/specs/2026-11-25-perfil-senha-design.md`

## Global Constraints

- Indentação de 4 espaços; textos em pt-BR com acento.
- Não commitar: o Luís commita (deixar mensagem sugerida). Migration só é aplicada no lexhub-v2 com OK dele.
- Testes web: `NODE_OPTIONS=--no-experimental-webstorage npx vitest run` em `apps/web`.
- Validação da senha no front: campos preenchidos, iguais, mínimo 6 caracteres (como no LexFlow).
- Senha atual não é pedida.

## Review Focus

- Pessoa só do Google (senha vazia `''` ou `null` em `encrypted_password`) → status "Não definida" (teste SQL cobre os dois).
- Pessoa sem organização ativa troca a senha → troca acontece, nenhuma linha de auditoria, nenhum erro (teste SQL).
- Update em `auth.users` que não mexe na senha (ex.: `last_sign_in_at`) → nenhuma linha de auditoria (teste SQL).
- Supabase recusa (`weak_password`, `same_password`, `reauthentication_needed`) → mensagem em pt-BR na tela, campos mantidos (teste do client).
- Depois de criar a senha, o bloco passa para "Alterar senha" sem recarregar a página (teste da UI).

---

### Task 1: Migration (status + trigger de auditoria)

**Files:**
- Create: `supabase/migrations/20261126150000_perfil_senha.sql`
- Create: `supabase/tests/perfil_senha_test.sql`
- Modify: `supabase/tests/ci/supabase_stub.sql` (coluna `encrypted_password varchar` em `auth.users`)

**Interfaces:**
- Produces: `api.my_password_status() returns boolean` (security definer, `set search_path = ''`, grant só a
  `authenticated`); `app_private.audit_password_changed()` + trigger `audit_password_changed`
  `after update of encrypted_password on auth.users for each row when (old.encrypted_password is distinct from new.encrypted_password)`.
  Insere em `app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)` uma linha por
  `app.memberships` ativa: `'auth.password_changed'`, `'user'`, `new.id::text`,
  `{"kind": "created"|"changed"}` (`created` quando o antigo era null ou `''`). Corpo em `begin … exception when others then raise warning` como `app_private.audit_login`.

- [ ] **Step 1: Escrever `perfil_senha_test.sql`** (begin … rollback; padrão de `dispositivos_test.sql`). Cenário: u1 ativo
  em 1 org com `encrypted_password = ''`, u2 sem org com `null`.
  - como u1: `api.my_password_status()` = false;
  - `update auth.users set encrypted_password = 'x' where id = u1` → 1 linha `auth.password_changed` com `metadata->>'kind' = 'created'`; status = true;
  - novo update para `'y'` → mais 1 linha com `kind = 'changed'`;
  - update de `email` de u1 sem mexer na senha → total continua 2;
  - update da senha de u2 (`null` → `'z'`) → sem erro e 0 linhas para u2;
  - termina com `raise notice 'OK: perfil_senha'`.
- [ ] **Step 2: Rodar no Postgres local (container `lexhub-pgtest`, porta 55432, `PGCLIENTENCODING=UTF8`)** stub + migrations + o teste. Esperado: ERROR (função não existe).
- [ ] **Step 3: Escrever a migration** (cabeçalho com o porquê; como reverter em comentário).
- [ ] **Step 4: Rodar de novo stub + todas as migrations + todos os `supabase/tests/*.sql`.** Esperado: sem ERROR, `OK: perfil_senha`.
- [ ] **Step 5: Não commitar;** anotar mensagem sugerida `feat(db): status da senha e auditoria da troca`.

### Task 2: Cliente de dados (api + mock)

**Files:**
- Modify: `apps/web/src/services/client.ts` (perto de `setMyAppearance`)
- Modify: `apps/web/src/services/profileClient.ts` (+ `profileClient.test.ts`)
- Modify: `apps/web/src/services/mockClient.ts` (implementação + lista de nomes perto da linha 906)

**Interfaces:**
- Produces: `getPasswordStatus(): Promise<boolean>` (RPC `my_password_status`) e
  `setPassword(password: string): Promise<void>` (`supabase.auth.updateUser({ password })`). Erros viram `DataError`:
  `weak_password` → `'Senha fraca. Use mais caracteres, com letras e números.'`;
  `same_password` → `'A nova senha é igual à atual.'`;
  `reauthentication_needed` → `'Entre de novo para trocar a senha.'`;
  outros → `'Não foi possível salvar a senha. Tente de novo.'`.
  Mock: começa `false`, `setPassword` grava `true` em memória (o mesmo estado que o resto do mock usa).

- [ ] **Step 1: Testes em `profileClient.test.ts`:** `getPasswordStatus` chama rpc `my_password_status` e devolve o boolean;
  `setPassword('abc123')` chama `updateUser({ password: 'abc123' })`; com erro `{ code: 'weak_password' }` rejeita com a
  mensagem de senha fraca; com `{ code: 'same_password' }` e `{ code: 'reauthentication_needed' }` idem; código
  desconhecido → mensagem genérica. Teste do mock: `getPasswordStatus()` false → `setPassword('abc123')` → true.
- [ ] **Step 2: Rodar** `npx vitest run src/services/profileClient.test.ts`. Esperado: FAIL.
- [ ] **Step 3: Implementar** (incluir as duas no `Pick` de `ProfileClient`).
- [ ] **Step 4: Rodar de novo + `npx tsc -b`.** Esperado: PASS, sem erro de tipo.
- [ ] **Step 5: Não commitar;** mensagem sugerida `feat(web): cliente de senha do perfil`.

### Task 3: Rótulo na Auditoria

**Files:**
- Modify: `apps/web/src/services/auditEvents.ts` (+ `auditEvents.test.ts`)

**Interfaces:**
- Produces: regra `'auth.password_changed'`: `kind: 'login'`, `action` = `'Criou a senha'` se `metadata.kind === 'created'`,
  senão `'Alterou a senha'`; `detail` vazio.

- [ ] **Step 1: Teste** com os dois `kind` e as ações esperadas.
- [ ] **Step 2: Rodar** — FAIL. **Step 3: Implementar** (se `Rule.action` for string fixa, permitir função ou duas linhas; manter o padrão do arquivo). **Step 4: Rodar** — PASS.
- [ ] **Step 5: Não commitar;** mensagem sugerida `feat(web): auditoria mostra troca de senha`.

### Task 4: Bloco Senha no Perfil

**Files:**
- Create: `apps/web/src/components/settings/PasswordBlock.tsx` (+ `PasswordBlock.test.tsx`)
- Modify: `apps/web/src/components/settings/ProfileSection.tsx` (render depois dos campos de nome/e-mail)
- Modify: `apps/web/src/components/settings/settings.css` (só se faltar estilo)

**Interfaces:**
- Consumes: `dataClient.getPasswordStatus`, `dataClient.setPassword` (Task 2); `PasswordInput` já usado no `LoginPage`.
- Produces: `PasswordBlock()` sem props.

Comportamento: rótulo "Senha"; valor "Não definida" + botão "Criar senha", ou "••••••••" + "Alterar senha"; enquanto
carrega, "—". Botão abre "Nova senha" e "Confirmar nova senha" + Salvar/Cancelar. Erros de validação no front:
`'Preencha os dois campos.'`, `'As senhas não coincidem.'`, `'A senha precisa ter pelo menos 6 caracteres.'`. Sucesso:
fecha, status vira true, mostra `'Senha salva. Você já pode entrar com e-mail e senha.'`. Erro do client aparece com
`role="alert"` e os campos ficam.

- [ ] **Step 1: Testes** (padrão de `DevicesSection.test.tsx`, client mockado): sem senha mostra "Não definida" e "Criar senha";
  senhas diferentes → alerta e `setPassword` não chamado; "12345" → alerta de 6 caracteres; sucesso → `setPassword` com a
  senha, aviso de sucesso e botão vira "Alterar senha"; `setPassword` rejeita `DataError('Senha fraca…')` → alerta com o
  texto e campos continuam abertos; Cancelar fecha sem chamar nada.
- [ ] **Step 2: Rodar** — FAIL. **Step 3: Implementar** e trocar o aviso do rodapé do Perfil para não dizer que só a foto é editável. **Step 4: Rodar a suíte web inteira + `npx tsc -b` + `npm run build`.** Esperado: tudo verde.
- [ ] **Step 5: Conferir no navegador (mock):** claro e escuro, celular; criar → vira "Alterar senha".
- [ ] **Step 6: Não commitar;** mensagem sugerida `feat(settings): criar e alterar senha no perfil`.

### Depois das tasks

- Pedir OK do Luís para aplicar a migration no lexhub-v2 (e acertar a versão no histórico, ver memória de migrations).
- Luís testa em modo api: conta só Google → criar senha → sair → entrar com e-mail e senha; ver "Criou a senha" na Auditoria.
