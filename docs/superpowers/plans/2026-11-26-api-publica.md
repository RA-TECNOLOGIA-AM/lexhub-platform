# API pública (chave de API) — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gestor, Controller ou Owner pede uma chave de API, um Dev aprova, e a pessoa consulta por `/v1`
os mesmos dados do "Exportar" dos dashboards dos seus setores, com tokens no modelo da v1.

**Architecture:** Tabelas e regra de alcance no Supabase (schema `app` + função `app_private`), pedidos e
aprovação por RPCs do schema `api` chamadas pelo front (padrão de `accessRequests.ts`). Tokens e dados
na API em Python (`apps/api`): emissão/rotação de tokens e rota genérica `/v1/.../dashboards/{key}` que
monta um `DashboardAccess` a partir da chave e reaproveita `_prepare`/`_run`/`export` de `routes/dashboards.py`.

**Tech Stack:** Postgres/Supabase (migrations SQL), FastAPI + asyncpg + PyJWT (pytest), React + Vite + TS (vitest).

**Spec:** `docs/superpowers/specs/2026-11-26-api-publica-design.md`

## Global Constraints

- Branch: `feat/api-publica`. **O Luís faz commits e push**: no fim de cada tarefa, parar e sugerir a
  mensagem de commit; nunca rodar `git commit`/`git push`.
- Comandos em PowerShell. Indentação de 4 espaços (Python, TS e SQL). Textos de tela e mensagens de erro em pt-BR.
- Migration nova: `supabase/migrations/20261126230000_api_publica.sql`, aditiva, com bloco
  `-- Desfazer:` no fim. Aplicar no lexhub-v2 só com OK do Luís; depois acertar a versão no histórico
  (o MCP grava a hora como versão).
- Tabelas novas: RLS ligado, sem policy, `revoke all ... from anon, authenticated`. Front só via RPC `api.*`.
- Quem pede: org role `owner`, ou unit role `gestor`/`controller` em ao menos uma unidade. Quem aprova:
  org role `admin` (Desenvolvedor).
- Access token: JWT HS256, `PUBLIC_API_JWT_SECRET`, TTL `PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS = 604800`.
- Refresh token: prefixo `lxr_`, 30 dias (`PUBLIC_API_REFRESH_TOKEN_TTL_DAYS = 30`), só SHA-256 no banco.
- Reuso de refresh já trocado revoga todos os tokens da chave (`tokens_valid_since = now()`).
- Access com `iat < tokens_valid_since` → 401.
- Permissão lida do banco a cada chamada, cache ≤ 60 s.
- Setor extra: justificativa obrigatória (≥ 10 caracteres), `expires_at` obrigatório, padrão 90 dias, máximo 365.
- Uma chave não revogada por pessoa por org.
- Limites: período ≤ 366 dias; `tamanho_pagina` 1–5000 (padrão 1000); `pagina` ≥ 1; `campos` por vírgula
  ou repetido; 60 req/min por chave → 429.
- Toda chamada `/v1` de dados grava `app.audit_log` com ação `api.read`.
- Testes do web: `$env:NODE_OPTIONS='--no-experimental-webstorage'; npm test` (em `apps/web`).

## Review Focus

1. Duas renovações simultâneas com o mesmo refresh → só uma recebe tokens; a outra revoga tudo (401 nas duas depois).
2. Gestor tirado do setor, rebaixado a Colaborador ou desligado depois de pegar os tokens → 403 na próxima chamada (≤ 60 s).
3. Setor extra vencido → some do alcance sem job: a função compara `expires_at > now()`.
4. Dashboard desligado na unidade, de escopo `org` (Estratégico Geral) ou sem exportação → 403/404, nunca dados.
5. `pagina` além do total → `dados: []` com `total` certo, não erro.

---

### Task 1: Migration — tabelas, alcance da chave e RPCs

**Files:**
- Create: `supabase/migrations/20261126230000_api_publica.sql`

**Interfaces:**
- Produces (tabelas):
  - `app.api_keys(id uuid pk, org_id uuid, user_id uuid, membership_id uuid, status text check in
    ('pending','active','rejected','revoked'), note text, requested_at, decided_by uuid, decided_at,
    revoked_by uuid, revoked_at, tokens_valid_since timestamptz, last_used_at timestamptz)`;
    unique parcial `(org_id, user_id) where status in ('pending','active')`.
  - `app.api_key_sectors(id uuid pk, key_id uuid fk cascade, sector_name text, justification text,
    expires_at timestamptz, status text check in ('pending','approved','rejected','revoked'),
    decided_by uuid, decided_at, unique (key_id, sector_name))`.
  - `app.api_refresh_tokens(id uuid pk, key_id uuid fk cascade, token_hash text unique, created_at,
    expires_at, used_at, revoked_at, replaced_by uuid)`.
- Produces (funções):
  - `app_private.api_key_scope(p_key uuid, p_unit uuid, p_dashboard text) returns text` — `'all'`,
    `'own'` ou `null`.
  - `app_private.api_key_sector_names(p_key uuid) returns text[]` — setores base (nomes dos `app.teams`
    da pessoa via `membership_teams`, ativos) ∪ extras `approved` com `expires_at > now()`.
  - RPCs `security definer` no schema `api`, todas conferindo `auth.uid()`:
    - `api.api_key_eligibility(p_org text) returns jsonb` → `{eligible bool, base_sectors text[], sectors text[]}`
      (`sectors` = nomes de setores ativos das unidades alcançáveis, para o seletor de extras).
    - `api.request_api_key(p_org text, p_note text, p_extras jsonb) returns uuid` — `p_extras` =
      `[{"setor": text, "justificativa": text, "validade": date}]`.
    - `api.my_api_key(p_org text) returns jsonb` — chave da pessoa (sem hash), setores e status.
    - `api.list_api_keys(p_org text, p_status text) returns jsonb` (Dev).
    - `api.count_pending_api_keys(p_org text) returns int` (Dev).
    - `api.decide_api_key(p_key uuid, p_approve bool, p_sectors_approved text[], p_note text) returns jsonb` (Dev).
    - `api.revoke_api_key(p_key uuid) returns void` (Dev ou o dono).
    - `api.revoke_api_key_sector(p_key uuid, p_sector text) returns void` (Dev).
  - Cada RPC de escrita grava `app.audit_log` com `api_key.requested|approved|rejected|revoked|sector_revoked`.

`api_key_scope` reproduz as camadas 1 e 2 de `app_private.dashboard_access_explain`
(`20261126190000_estrategico_geral.sql`), trocando "times da pessoa nesta unidade" por "times ativos desta
unidade cujo `name` está em `api_key_sector_names(p_key)`". Antes disso, devolve `null` se: chave não
`active`; org ou unidade inativa ou de outra org; membership não `active`; pessoa sem org role `owner` e
sem unit role `gestor`/`controller` em `p_unit`; dashboard não ligado (`od.enabled`) ou catálogo inativo;
`dashboard_catalog.scope = 'org'`. A permissão `unit.dashboards.all` **não** entra.

- [ ] **Step 1: Escrever a migration** com tabelas, índices (`api_keys(org_id, status)`,
  `api_refresh_tokens(key_id)`), RLS/revoke, as duas funções `app_private`, as RPCs e o bloco `-- Desfazer:`
  (drop das RPCs, funções e tabelas, nessa ordem).

- [ ] **Step 2: Validar no lexhub-v2 numa transação desfeita** (com OK do Luís), via `execute_sql`:
  `begin; <migration>; <cenários>; rollback;`. Cenários com um gestor real do Comercial LAAM:
  - `api_key_scope` = `'all'` para `comercial` na unidade dele, e `null` para `protocolo`.
  - Com extra `Protocolo` aprovado e `expires_at = now() + 1 day` → `protocolo` vira `'all'`; com
    `expires_at = now() - 1 day` → `null`.
  - Dashboard com `od.enabled = false` → `null`; `estrategico-geral` → `null`.
  - Membership em `membership_units` trocada para `colaborador` → `null`.

  Expected: todos os resultados como listados; nenhum erro.

- [ ] **Step 3: Aplicar no lexhub-v2** com `apply_migration` e acertar a versão para `20261126230000`
  em `supabase_migrations.schema_migrations`. Conferir que o teste de paridade de migrations do CI (se
  houver lista de versões) não quebra.

- [ ] **Step 4: Parar para o Luís commitar.** Sugestão: `feat(api-publica): tabelas, alcance por setor e RPCs da chave de API`

---

### Task 2: Tokens e configuração

**Files:**
- Create: `apps/api/src/app/public_api/__init__.py`, `apps/api/src/app/public_api/tokens.py`
- Modify: `apps/api/src/app/config.py`, `apps/api/.env.example`
- Test: `apps/api/tests/test_public_api_tokens.py`

**Interfaces:**
- Produces:
  - `Settings.PUBLIC_API_JWT_SECRET: str = ""`, `PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS: int = 604800`,
    `PUBLIC_API_REFRESH_TOKEN_TTL_DAYS: int = 30`.
  - `REFRESH_PREFIX = "lxr_"`
  - `class InvalidAccessToken(Exception)`
  - `@dataclass(frozen=True) class AccessClaims: key_id: str; issued_at: datetime; expires_at: datetime`
  - `issue_access_token(key_id: str, secret: str, ttl_s: int, now: datetime) -> tuple[str, datetime]`
  - `verify_access_token(token: str, secret: str, now: datetime) -> AccessClaims`
  - `new_refresh_token() -> str` · `hash_refresh_token(token: str) -> str`

Claims do JWT: `sub=key_id`, `iat`, `exp`, `typ="lxh_access"`, `jti` aleatório. Sem setores no token
(permissão vem do banco). Usar `jwt` (PyJWT, já é dependência) com `algorithms=["HS256"]`.

- [ ] **Step 1: Testes que falham**

```python
def test_access_token_ida_e_volta():
    tok, exp = issue_access_token("k1", "s" * 32, 604800, NOW)
    claims = verify_access_token(tok, "s" * 32, NOW)
    assert claims.key_id == "k1" and exp == NOW + timedelta(seconds=604800)

def test_access_token_vencido():
    tok, _ = issue_access_token("k1", "s" * 32, 60, NOW)
    with pytest.raises(InvalidAccessToken):
        verify_access_token(tok, "s" * 32, NOW + timedelta(seconds=61))

def test_access_token_outro_segredo_ou_typ():
    tok, _ = issue_access_token("k1", "s" * 32, 60, NOW)
    with pytest.raises(InvalidAccessToken):
        verify_access_token(tok, "x" * 32, NOW)
    supabase_like = jwt.encode({"sub": "k1", "exp": NOW + timedelta(seconds=60)}, "s" * 32, "HS256")
    with pytest.raises(InvalidAccessToken):
        verify_access_token(supabase_like, "s" * 32, NOW)

def test_refresh_token_formato_e_hash():
    t = new_refresh_token()
    assert t.startswith("lxr_") and len(t) >= 40
    assert hash_refresh_token(t) == hashlib.sha256(t.encode()).hexdigest()
    assert new_refresh_token() != t
```

- [ ] **Step 2: Rodar e ver falhar** — `cd apps/api; .\.venv\Scripts\python -m pytest tests/test_public_api_tokens.py -q` → ImportError.
- [ ] **Step 3: Implementar** `tokens.py` e os campos do `Settings` (+ linhas comentadas no `.env.example`).
- [ ] **Step 4: Rodar de novo** → 4 passed.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): tokens de acesso e refresh`

---

### Task 3: Repositório da chave e rotação do refresh

**Files:**
- Create: `apps/api/src/app/public_api/store.py`, `apps/api/src/app/public_api/service.py`
- Test: `apps/api/tests/test_public_api_service.py` (com `FakeApiKeyRepo` em memória no próprio teste)

**Interfaces:**
- Consumes: Task 1 (tabelas, `app_private.api_key_scope`), Task 2 (tokens).
- Produces:
  - `@dataclass(frozen=True) class ApiKey: id: str; org_id: str; user_id: str; status: str; tokens_valid_since: datetime | None`
  - `class ApiKeyRepo(Protocol)`:
    - `get_key(key_id) -> ApiKey | None`
    - `get_active_key_for(user_id, org_slug) -> ApiKey | None`
    - `get_refresh(token_hash) -> RefreshRow | None` (`id, key_id, expires_at, used_at, revoked_at`)
    - `consume_refresh(refresh_id) -> bool` (UPDATE condicional `used_at is null and revoked_at is null`)
    - `insert_refresh(key_id, token_hash, expires_at) -> str`
    - `mark_replaced(refresh_id, new_id) -> None`
    - `revoke_all(key_id, now) -> None` (revoga refresh vivos + `tokens_valid_since = now`)
    - `touch_last_used(key_id, now) -> None`
    - `scope(key_id, unit_id, dashboard_key) -> str | None` (chama `app_private.api_key_scope`)
    - `reachable(key_id) -> list[Reachable]` (`org_slug, unit_code, unit_id, dashboard_key`; os pares com scope não nulo)
  - `PgApiKeyRepo(pool)` e `get_api_key_repo` (Depends), no padrão de `PgAccessRepo` em `app/access.py`.
  - `service.py`:
    - `@dataclass(frozen=True) class TokenPair: access_token: str; access_expires_at: datetime; refresh_token: str; refresh_expires_at: datetime`
    - `async def issue_pair(repo, key: ApiKey, settings, now) -> TokenPair` — chama `revoke_all` antes
      (gerar novos tokens invalida os anteriores).
    - `async def rotate(repo, refresh_token: str, settings, now) -> TokenPair` — levanta
      `RefreshRejected(reason)` com `reason in {"invalido","vencido","reuso","chave_inativa"}`; em
      `"reuso"` chama `revoke_all` antes de levantar.
    - `async def authenticate(repo, access_token: str, settings, now) -> ApiKey` — levanta
      `InvalidAccessToken` se o token não confere, a chave não está `active` ou `iat < tokens_valid_since`.
      Cache de `get_key` por 60 s (dict com monotonic, como na v1).

- [ ] **Step 1: Testes que falham**

```python
async def test_rotate_troca_e_invalida_o_anterior(): ...
    # pair1 = issue_pair; pair2 = rotate(pair1.refresh) → refresh diferente; rotate(pair1.refresh) → RefreshRejected("reuso")

async def test_reuso_revoga_tudo():
    # depois do reuso: rotate(pair2.refresh) → RefreshRejected("invalido" ou "reuso"); authenticate(pair2.access) → InvalidAccessToken

async def test_concorrencia_so_um_consome():
    # duas rotate() com o mesmo refresh via asyncio.gather → exatamente 1 TokenPair e 1 RefreshRejected

async def test_refresh_vencido():
    # rotate com now > expires_at → RefreshRejected("vencido")

async def test_issue_pair_invalida_tokens_antigos():
    # pair1; issue_pair de novo; authenticate(pair1.access) → InvalidAccessToken

async def test_chave_revogada_recusa_access():
    # repo.status = "revoked" e cache vencido → authenticate → InvalidAccessToken
```

  O `FakeApiKeyRepo.consume_refresh` deve ser atômico (um `asyncio.Lock`) para o teste de concorrência
  provar a lógica do serviço, não o fake.

- [ ] **Step 2: Rodar e ver falhar** — `.\.venv\Scripts\python -m pytest tests/test_public_api_service.py -q`.
- [ ] **Step 3: Implementar** `store.py` (SQL em constantes, como em `access.py`) e `service.py`.
- [ ] **Step 4: Rodar de novo** → todos passam.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): chave, rotação do refresh e autenticação`

---

### Task 4: Rotas de token

**Files:**
- Create: `apps/api/src/app/routes/public_auth.py`
- Modify: `apps/api/src/app/main.py` (incluir os dois routers)
- Test: `apps/api/tests/test_public_api_auth_routes.py`

**Interfaces:**
- Consumes: Task 3 (`issue_pair`, `rotate`, `get_api_key_repo`), `get_current_user` de `app/auth.py`, `audit_entry`.
- Produces:
  - `POST /orgs/{org_slug}/api-key/tokens` (login do Supabase): 404 se a pessoa não tem chave `active`
    na org; senão `TokenPair` (JSON: `access_token, access_expires_at, refresh_token, refresh_expires_at,
    token_type: "Bearer"`). Audita `api_key.tokens_issued`.
  - `POST /v1/auth/token` body `{"refresh_token": str}` → mesmo JSON; 401 com `detail` em pt-BR por
    `reason`. Em `"reuso"`, audita `api_key.refresh_reuse`.
  - Dependency `require_api_key(request) -> ApiKey` (lê `Authorization: Bearer`, chama `authenticate`,
    401 `"Access token inválido"`), usada na Task 5.

- [ ] **Step 1: Testes que falham** (TestClient + `dependency_overrides` com o fake da Task 3):
  - `test_tokens_sem_chave_ativa_404`, `test_tokens_emite_par_e_audita`.
  - `test_auth_token_rotaciona`, `test_auth_token_reuso_401_e_revoga`, `test_auth_token_corpo_invalido_422`.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** as rotas e `require_api_key`; CORS não muda (consumo é servidor a servidor).
- [ ] **Step 4: Rodar** → passam; rodar a suíte toda `.\.venv\Scripts\python -m pytest -q` → sem regressão.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): rotas de emissão e renovação de tokens`

---

### Task 5: Rota de dados `/v1` e catálogo

**Files:**
- Create: `apps/api/src/app/routes/public_data.py`, `apps/api/src/app/public_api/rate_limit.py`
- Modify: `apps/api/src/app/main.py`; `apps/api/src/app/routes/dashboards.py` (só se precisar expor
  `_prepare`/`_run` sem underscore — preferir importar como estão)
- Test: `apps/api/tests/test_public_api_data.py`

**Interfaces:**
- Consumes: `require_api_key` (Task 4), `ApiKeyRepo.scope/reachable/touch_last_used` (Task 3),
  `_prepare`, `_run` de `routes/dashboards.py`, `export.pick_report/pick_fields/table` de `app/dashboards/export.py`.
- Produces:
  - `GET /v1/catalogo` → `{"acesso": [{"org", "unidade", "dashboard", "relatorios": [{"chave", "campos": [...]}]}]}`.
  - `GET /v1/orgs/{org_slug}/units/{unit_code}/dashboards/{dashboard_key}` com `from`, `to` (obrigatórios),
    `campos`, `relatorio`, `pagina=1`, `tamanho_pagina=1000` → `{"dados": [...], "pagina", "tamanho_pagina",
    "total", "total_paginas", "campos": [...]}` (forma do `RespostaDados` da v1; cada linha é um objeto
    `{campo: valor}`).
  - `RateLimiter(limit=60, window_s=60).hit(key_id: str, now: float) -> bool` (janela deslizante em memória).

Fluxo da rota: rate limit (429 `"Limite de 60 chamadas por minuto"`) → resolver org/unidade/`unit_id` da
chave → `repo.scope(...)`; `null` → 403 `"Sem acesso a este dashboard pela chave"` + audita
`api.access_denied` → montar `DashboardAccess(user=CurrentUser(user_id=key.user_id, email=None, claims={}),
scope=..., can_export=True, can_see_commission=<has_unit_permission do dono>, ...)` → `_prepare` →
`pick_report` (sem export → 404) → `pick_fields` → `_run(spec.rows(ctx))` → `table` → paginar →
`touch_last_used` → audita `api.read` (`actor_user_id` = dono, metadata: `key_id, org, unit, dashboard,
relatorio, from, to, pagina, total`). Validação: `to - from > 366 dias` ou `from > to` → 422.
Dashboards com `spec.parts` (vários arquivos): 422 `"Use o parâmetro relatorio"` listando as partes.

- [ ] **Step 1: Testes que falham** (fakes de repo, fonte e módulo de dashboard, como em `tests/test_dashboard_export.py`):
  - `test_dados_pagina_1_e_total`, `test_pagina_alem_do_total_vem_vazia` (Review Focus 5).
  - `test_campos_por_virgula_e_repetidos_sao_iguais`.
  - `test_sem_scope_403_e_audita` (Review Focus 2 e 4), `test_dashboard_sem_export_404`.
  - `test_periodo_maior_que_366_dias_422`, `test_tamanho_pagina_5001_422`.
  - `test_rate_limit_61a_chamada_429`.
  - `test_audita_api_read_com_dono_da_chave`.
  - `test_catalogo_lista_so_o_alcancavel`.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** `rate_limit.py` e `public_data.py`.
- [ ] **Step 4: Rodar** → passam; suíte toda sem regressão; `ruff check src tests` limpo.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): rota de dados /v1 e catálogo`

---

### Task 6: Front — cliente da chave de API

**Files:**
- Create: `apps/web/src/services/apiKeysClient.ts`, `apps/web/src/services/apiKeysClient.test.ts`
- Modify: `apps/web/src/services/client.ts` (interface `DataClient`), `apps/web/src/services/mockClient.ts`
  (mock com estado em memória), `apps/web/src/types/index.ts`

**Interfaces:**
- Consumes: RPCs da Task 1; `POST /orgs/{org}/api-key/tokens` da Task 4 via `apiClient.ts`.
- Produces (no `DataClient`):
  - `getApiKeyEligibility(org: string): Promise<ApiKeyEligibility>`
  - `requestApiKey(org: string, note: string, extras: ApiKeyExtraRequest[]): Promise<string>`
  - `getMyApiKey(org: string): Promise<ApiKeyInfo | null>`
  - `issueApiKeyTokens(org: string): Promise<ApiKeyTokens>`
  - `listApiKeys(org: string, status: ApiKeyStatus | 'all'): Promise<ApiKeyInfo[]>`
  - `countPendingApiKeys(org: string): Promise<number>`
  - `decideApiKey(id: string, approve: boolean, sectors: string[], note: string): Promise<ApiKeyInfo>`
  - `revokeApiKey(id: string): Promise<void>` · `revokeApiKeySector(id: string, sector: string): Promise<void>`
  - Tipos: `ApiKeyStatus = 'pending'|'active'|'rejected'|'revoked'`; `ApiKeyExtraRequest = {setor, justificativa, validade}`;
    `ApiKeySector = {setor, base: boolean, status, justificativa?, expiresAt?}`;
    `ApiKeyInfo = {id, userName, userEmail, status, note, requestedAt, decidedAt?, lastUsedAt?, sectors: ApiKeySector[]}`;
    `ApiKeyTokens = {accessToken, accessExpiresAt, refreshToken, refreshExpiresAt}`.

- [ ] **Step 1: Testes que falham** em `apiKeysClient.test.ts`, no estilo de `accessRequests.test.ts`
  (`fakeSupabase`): cada método chama a RPC certa com os parâmetros `p_*` certos; `issueApiKeyTokens`
  faz `POST /orgs/lexgroup/api-key/tokens`.
- [ ] **Step 2: Rodar e ver falhar** — `cd apps/web; $env:NODE_OPTIONS='--no-experimental-webstorage'; npx vitest run src/services/apiKeysClient.test.ts`.
- [ ] **Step 3: Implementar** o cliente, ligar no `DataClient` e no mock.
- [ ] **Step 4: Rodar** → passa; `npm run lint` e `npx tsc -b` limpos.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): cliente da chave de API no front`

---

### Task 7: Front — seção "Chave de API" nas Configurações

**Files:**
- Create: `apps/web/src/components/settings/ApiKeySection.tsx`, `ApiKeySection.test.tsx`
- Modify: `apps/web/src/components/settings/SettingsDialog.tsx` (nova seção, só se `eligible`)

**Interfaces:**
- Consumes: Task 6.

Estados da seção:
- **Sem chave:** setores base (ou o aviso "Você não tem setor cadastrado; peça setores extras ou fale com
  um Desenvolvedor"), lista de extras (setor, justificativa, validade com padrão hoje + 90 dias, máximo
  365), campo de observação e botão "Pedir chave de API".
- **Pendente:** "Aguardando aprovação de um Desenvolvedor".
- **Ativa:** setores (base e extras com validade) e botão "Gerar tokens". Os tokens aparecem uma vez,
  com copiar e o aviso "Guarde agora. Gerar de novo invalida os anteriores." Link para o guia.
- **Recusada/revogada:** motivo e botão para pedir de novo.

- [ ] **Step 1: Testes que falham**: não aparece para não elegível; pedido sem setor base exige ao menos
  um extra; extra sem justificativa ou com validade > 365 dias bloqueia o envio; "Gerar tokens" mostra
  os tokens uma vez e some ao fechar.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** no estilo de `DevicesSection.tsx` (tokens e CSS de `settings.css`).
- [ ] **Step 4: Rodar** → passa; conferir no navegador em modo mock (`VITE_DATA_SOURCE=mock`), claro e escuro.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): pedir chave e gerar tokens nas Configurações`

---

### Task 8: Front — aba "Chaves de API" no admin

**Files:**
- Create: `apps/web/src/pages/admin/api-keys/ApiKeysPage.tsx`, `ApiKeysPage.test.tsx`
- Modify: `apps/web/src/navigation.ts` (item `chaves-api`, rota `/:org/admin/chaves-api`, `requires`
  igual ao de quem aprova pedidos de acesso na org, badge `'api-keys'`), `apps/web/src/App.tsx` (rota
  lazy), `apps/web/src/components/layout/AppLayout.tsx` (selo com `countPendingApiKeys`),
  `apps/web/src/navigation.test.ts`

**Interfaces:**
- Consumes: Task 6.

Tela no padrão mestre-detalhe de Membros: abas Pendentes / Ativas / Encerradas. Na gaveta do pedido:
pessoa, cargo, setores base, extras pedidos (cada um com justificativa, validade e marcar/desmarcar),
observação, Aprovar e Recusar. Na gaveta da ativa: último uso, setores com "Revogar setor" nos extras e
"Revogar chave" (confirmação).

- [ ] **Step 1: Testes que falham**: item de menu só para Dev; selo mostra pendentes; aprovar envia só
  os extras marcados; revogar setor chama `revokeApiKeySector` e mantém a chave.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Rodar** → passa; suíte do web toda; conferir no navegador (mock) desktop e 375 px.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `feat(api-publica): aba Chaves de API no admin`

---

### Task 9: Guia do usuário e script de renovação

**Files:**
- Create: `apps/web/src/pages/documentacao/guias/api-publica.md` (ou o formato dos 28 guias atuais),
  `apps/api/scripts/api_publica_cliente.py`
- Modify: registro dos guias (o equivalente ao `docRegistry` da v2)

**Interfaces:**
- Consumes: rotas das Tasks 4 e 5.

Conteúdo do guia (base: `LexHub/src/pages/documentacao/ApiPublica.tsx` da v1, adaptado): quem pode pedir
e como; "Gerar tokens"; renovar com `POST /v1/auth/token` e por que guardar sempre o refresh novo; o que
o reuso faz; `/v1/catalogo`; rota de dados com parâmetros, limites, paginação e erros
(401/403/404/422/423/429/501/503); exemplos em cURL, JavaScript e Python; Power BI com o script.

O script (`api_publica_cliente.py`, adaptado do script da v1): lê o refresh de um arquivo local, renova,
regrava o par no mesmo arquivo antes de usar o access, e baixa um dashboard para CSV. Só stdlib + `requests`.

- [ ] **Step 1: Teste do script** em `apps/api/tests/test_api_publica_cliente.py`: com `requests` mockado,
  regrava o arquivo com o refresh novo **antes** de pedir os dados, e não regrava se a renovação falhar.
- [ ] **Step 2: Rodar e ver falhar.**
- [ ] **Step 3: Implementar** o script e escrever o guia.
- [ ] **Step 4: Rodar** → passa; abrir o guia no navegador (mock) e conferir os exemplos contra as rotas reais.
- [ ] **Step 5: Parar para o Luís commitar.** Sugestão: `docs(api-publica): guia de uso e script de renovação`

---

## Fora deste plano

- Export de Marketing e Comercial na v2: é ele que libera dados reais desses setores. A API funciona com
  qualquer dashboard que já tenha exportação.
- Aviso de token perto de vencer, por e-mail ou notificação.
