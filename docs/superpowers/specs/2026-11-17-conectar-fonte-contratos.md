# Conectar fonte — revisão técnica, SQL e contratos (PR 0 a PR 2)

Data: 17/11/2026 · Branch: `feat/conectar-fonte` · Status: rascunho para revisão

Complementa [2026-11-17-conectar-fonte-design.md](2026-11-17-conectar-fonte-design.md), que tem as
regras fechadas. Neste documento: os riscos técnicos, o SQL e os contratos da API.

---

## 1. Riscos técnicos e como tratar

### 1.1 Só leitura atrás de pgbouncer (PR 0)

- [database.py:68](../../../apps/api/src/app/database.py) faz `SET default_transaction_read_only = on`
  quando abre a conexão. Atrás de pgbouncer em modo transação, como no LAADV, esse `SET` vale só para
  uma conexão do servidor e se perde.
- **Correção:** `PgSourceFetcher.fetch` roda cada consulta dentro de
  `async with conn.transaction(readonly=True):` (gera `BEGIN READ ONLY`), com `SET LOCAL statement_timeout`.
  O `init` atual continua como camada extra.
- No MySQL (PR 3): `SET TRANSACTION READ ONLY` antes de `START TRANSACTION`, mais `MAX_EXECUTION_TIME`.
- Uma transação somente leitura não segura `dblink` nem funções que abrem outra conexão. A proteção
  real é o usuário do banco. Por isso, usuário com escrita só entra com "Salvar mesmo assim" registrado
  na auditoria.

### 1.2 Quem gerencia fontes

- `app_private.is_source_admin(p_user)` responde "sim" para quem é membro **ativo** da org `lexgroup`
  com cargo `owner` ou `admin`.
- O slug fica num lugar só (`app_private.home_org_id()`), para não espalhar `'lexgroup'` pelo código.
- O Owner de uma organização cliente recebe "não". Não usamos `role_permissions`, porque lá a
  permissão valeria para o Owner de qualquer organização.
- O `is_platform_staff()` (claim no JWT) continua existindo para o Solicitar acesso, mas não é usado aqui.

### 1.3 NG e LA nunca saem da LexGroup

Três camadas:
1. **Na tela:** o conector `internal` não aparece.
2. **No banco:**
   - uma trigger em `unit_source_refs` só aceita uma `source` que exista em `data_sources` **da mesma
     organização da unidade**;
   - para fontes `internal`, exige também uma linha em `app.internal_source_units` (hoje NG, LAAM e LARJ).
3. **Na API:** `DB_NG_ORGS=lexgroup` e `DB_LAADV_ORGS=lexgroup` no `.env`. Antes de buscar, a API recusa
   se a organização da unidade não estiver na lista.

### 1.4 A API não usa `service_role`

- A API conecta pela `DATABASE_URL` (asyncpg no pooler, `statement_cache_size=0`) e lê tabelas `app.*`
  direto (`access.py`, `me.py`, `hub_prefs.py`). Provavelmente o usuário é `postgres`.
- As funções novas seguem o padrão do repositório:
  - `revoke` de `public`, `anon` e `authenticated`;
  - `grant` para `service_role`.
- As funções recebem `p_user` explícito, porque nessa conexão `auth.uid()` é nulo. É o mesmo padrão de
  `has_permission` e `dashboard_scope`.
- **Endurecimento separado** (fora destes PRs): papel `lexhub_api` com `NOBYPASSRLS`. Ele afeta todas as
  rotas da API.
- **Verificar:** se o Supabase registra os parâmetros de consultas lentas nos logs, a senha passada em
  `vault.create_secret($1)` pode aparecer lá. Conferir `log_min_duration_statement`.

### 1.5 SSRF e SSL (PR 2)

1. **Firewall de saída na VPS** (`DOCKER-USER`), o controle principal. Bloqueia endereços privados,
   loopback, link-local e `169.254.169.254` a partir da rede da API.
2. **Antes de conectar:** a API resolve o DNS, recusa se **qualquer** IP for proibido e recusa portas
   abaixo de 1024.
3. **Depois de conectar:** a API confere o IP de fato conectado e aborta, antes de qualquer consulta,
   se ele for proibido. Isso pega DNS rebinding.

A conexão é feita pelo **nome**, então SNI e certificado funcionam normalmente. O SSL é o checkbox da
tela: ligado = `require` (criptografa sem validar o certificado), desligado = `disable`.

**Validação do `peername` com SSL** (asyncpg 0.29+ / aiomysql 0.2):

| Caso | O que acontece | Como tratar |
|---|---|---|
| **asyncpg, SSL ligado.** O asyncpg usa STARTTLS: abre o TCP, manda `SSLRequest` e faz `loop.start_tls`. O transporte final é um `_SSLProtocolTransport`, e `get_extra_info('peername')` repassa o do socket por baixo. | Funciona: `conn._transport.get_extra_info('peername')`. | `_transport` é atributo privado. Isolar num helper `peer_ip(conn)` com teste, que falha alto se o atributo mudar numa atualização. |
| **asyncpg com pool.** A checagem tem de rodar em **cada** conexão nova, não só no teste. | `init=` do pool roda depois do handshake e da autenticação. | Usar `init=` para checar o peer e levantar erro: o pool descarta a conexão. A senha já foi enviada, mas para um host cujo IP só é proibido por rebinding, e o firewall (camada 1) já teria barrado. |
| **asyncpg com `host` resolvendo para vários IPs.** | O asyncpg tenta em sequência e o `peername` mostra o que conectou. | A camada 2 recusa se **qualquer** IP for proibido, e a camada 3 confere o que conectou. |
| **IPv6.** | `peername` vem como tupla de 4 (`host, port, flow, scope`), e o host pode vir `::ffff:10.0.0.1`. | Normalizar com `ipaddress.ip_address(...)` e usar `.ipv4_mapped` antes de checar. |
| **aiomysql.** Faz TLS no próprio socket. O `peername` está em `conn._writer.get_extra_info('peername')` (ou `conn._sock`). Depende da versão. | Funciona, também por atributo privado. | Mesmo helper `peer_ip`, com uma implementação por driver e teste. |
| **Pooler ou proxy na frente** (pgbouncer, ProxySQL, RDS Proxy). | O `peername` é o IP do proxy, que é o que importa para SSRF. | Nada a fazer. |

Resumo: dá para checar o `peername` nos dois drivers, inclusive com SSL, mas só por atributo privado.
Por isso, a camada 3 é defesa extra. A segurança vem do firewall de saída.

### 1.6 Pools e réplicas (PR 2)

- Pools externos com `min_size=0`, `max_size=2` e `max_inactive_connection_lifetime=60`.
- **Invalidação:** pub/sub do Redis para invalidar na hora, mais `config_version` lido junto com a
  credencial e um TTL de 5 min no pool. O pub/sub sozinho perde mensagem quando a réplica está
  reconectando.
- **Cache de dados:** a chave já inclui o `db_name` (= key da fonte). Desconectar apaga as chaves
  daquela fonte, e as `key` geradas **nunca são reaproveitadas**.
- **IP fixo:** fixar a API num nó do Swarm (`node.labels.egress == true`).

---

## 2. SQL (rascunho das migrations)

Convenções do repositório:
- `security definer` com `set search_path = ''`;
- mensagens em pt-BR com `P0001` para a tela mostrar;
- `42501` para sem permissão;
- auditoria em `app.audit_log`.

### PR 1

```sql
-- ---------------------------------------------------------------------------
-- 1. Quem gerencia fontes: Owner/Dev da LexGroup
-- ---------------------------------------------------------------------------
create function app_private.home_org_id() returns uuid
language sql stable security definer set search_path = '' as $$
    select o.id from app.organizations o where o.slug = 'lexgroup' and o.active;
$$;

create function app_private.is_source_admin(p_user uuid) returns boolean
language sql stable security definer set search_path = '' as $$
    select exists (
        select 1
        from app.memberships m
        where m.org_id = app_private.home_org_id()
          and m.user_id = p_user
          and m.status = 'active'
          and m.role_key in ('owner', 'admin')
    );
$$;

revoke all on function app_private.home_org_id() from public, anon;
revoke all on function app_private.is_source_admin(uuid) from public, anon, authenticated;
grant execute on function app_private.home_org_id() to authenticated, service_role;
grant execute on function app_private.is_source_admin(uuid) to service_role;

-- ---------------------------------------------------------------------------
-- 2. data_sources: conector e configuração
-- ---------------------------------------------------------------------------
alter table app.data_sources
    add column connector      text not null default 'internal'
        check (connector in ('lexpre', 'lexflow', 'internal', 'postgres', 'mysql', 'sheets')),
    add column config         jsonb not null default '{}'::jsonb,
    add column secret_id      uuid,
    add column writer_ack     boolean not null default false,
    add column schema_cache   jsonb,
    add column config_version integer not null default 1,
    add column created_by     uuid references auth.users (id);

alter table app.data_sources
    add constraint data_sources_config_no_secret
        check (not (config ?| array['password', 'pass', 'senha', 'secret', 'token'])),
    add constraint data_sources_db_config
        check (connector not in ('postgres', 'mysql')
               or (config ?& array['host', 'port', 'database', 'user', 'ssl']
                   and (config ->> 'port')::int between 1024 and 65535)),
    add constraint data_sources_db_secret
        check ((connector in ('postgres', 'mysql')) = (secret_id is not null)),
    add constraint data_sources_sheet_config
        check (connector <> 'sheets' or config ?& array['spreadsheet_id', 'tab']);

update app.data_sources set connector = case
    when key = 'lexpre' then 'lexpre'
    when key = 'lexflow' then 'lexflow'
    when kind = 'sheet' then 'sheets'
    else 'internal'
end;

-- ---------------------------------------------------------------------------
-- 3. NG e LA só nas unidades liberadas; fonte sempre da mesma organização
-- ---------------------------------------------------------------------------
create table app.internal_source_units (
    source_id  uuid not null references app.data_sources (id) on delete cascade,
    unit_id    uuid not null references app.units (id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (source_id, unit_id)
);
alter table app.internal_source_units enable row level security; -- sem policy: só migration/funções

insert into app.internal_source_units (source_id, unit_id)
select ds.id, u.id
from app.data_sources ds
join app.units u on u.org_id = ds.org_id
where ds.connector = 'internal'
  and ds.org_id = app_private.home_org_id()
  and exists (select 1 from app.unit_source_refs r where r.unit_id = u.id and r.source = ds.key);

create function app_private.check_unit_source_ref() returns trigger
language plpgsql security definer set search_path = '' as $$
declare
    v_source app.data_sources;
begin
    select ds.* into v_source
    from app.units u
    join app.data_sources ds on ds.org_id = u.org_id and ds.key = new.source and ds.active
    where u.id = new.unit_id;
    if v_source.id is null then
        raise exception using errcode = '42501', message = 'Esta fonte não é da organização da unidade.';
    end if;
    if v_source.connector = 'internal' and not exists (
        select 1 from app.internal_source_units i where i.source_id = v_source.id and i.unit_id = new.unit_id
    ) then
        raise exception using errcode = '42501', message = 'Banco interno não liberado para esta unidade.';
    end if;
    return new;
end;
$$;
create trigger unit_source_refs_check before insert or update on app.unit_source_refs
    for each row execute function app_private.check_unit_source_ref();

-- Um escritório do LexPre/LexFlow em uma unidade só, no banco todo
create unique index unit_source_refs_product_ref_uq
    on app.unit_source_refs (source, ref)
    where source in ('lexpre', 'lexflow');

-- ---------------------------------------------------------------------------
-- 4. source_sync_runs: tipo e checagens
-- ---------------------------------------------------------------------------
alter table app.source_sync_runs
    add column run_kind    text not null default 'sync' check (run_kind in ('sync', 'health', 'test')),
    add column checks      jsonb,
    add column duration_ms integer check (duration_ms >= 0);

-- ---------------------------------------------------------------------------
-- 5. Ligar escritório (RPC do front; o front já tem o id/nome vindos da API)
-- ---------------------------------------------------------------------------
-- api.link_product_office(p_org text, p_unit text, p_product text, p_ref text) returns jsonb
--   -> exige is_source_admin(auth.uid()); garante a fonte lexpre/lexflow na org (cria a linha em
--      data_sources se a org ainda não tiver); insert unit_source_refs (o índice único barra duplicado
--      e vira P0001 "Este escritório já está ligado à unidade X."); audit 'source.office_linked';
--      devolve unit_sources_json
-- api.unlink_product_office(p_org text, p_unit text, p_product text) returns jsonb
--   -> audit 'source.office_unlinked'
-- grant execute on function api.link_product_office, api.unlink_product_office to authenticated;

-- list_sources / source_detail: + connector, canManageSources (= is_source_admin(auth.uid())),
-- status derivados 'no_dashboards' e 'no_data'.
```

Atenção ao "a organização ainda não tem a fonte `lexpre`": hoje a linha em `data_sources` existe só
na LexGroup. Para um cliente novo, `link_product_office` cria a fonte do produto na organização dele.
Assim a trigger da mesma organização vale também para o LexPre/LexFlow.

### PR 2

```sql
-- O segredo some junto com a fonte
create function app_private.delete_source_secret() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
    if old.secret_id is not null then
        delete from vault.secrets where id = old.secret_id;
    end if;
    return old;
end;
$$;
create trigger data_sources_delete_secret after delete on app.data_sources
    for each row execute function app_private.delete_source_secret();

-- Funções só da API (grant service_role; revoke public, anon, authenticated)
-- app_private.source_credentials(p_source_key text, p_org uuid)
--     returns table (id uuid, connector text, config jsonb, password text, config_version int)
--     -> fonte ativa da org; senha de vault.decrypted_secrets
-- app_private.connect_source(p_user uuid, p_org uuid, p_unit uuid, p_connector text, p_name text,
--     p_config jsonb, p_secret text, p_writer_ack boolean, p_schema_cache jsonb) returns uuid
--     -> exige is_source_admin(p_user); key gerada ('pg_' / 'my_' / 'gs_' || código da unidade || n,
--        nunca reaproveitada); vault.create_secret(p_secret, 'source:' || id);
--        insert data_sources (owner_unit_id = p_unit) + unit_source_refs (unit, key, '*');
--        audit 'source.connected' (metadata: connector, host, writer_ack; nunca a senha)
-- app_private.set_source_secret(p_user uuid, p_source uuid, p_secret text, p_writer_ack boolean)
--     -> vault.update_secret; config_version + 1; audit 'source.secret_changed'
-- app_private.disconnect_source(p_user uuid, p_source uuid)
--     -> delete unit_source_refs; delete data_sources (a trigger apaga o segredo);
--        audit 'source.disconnected'
-- app_private.record_source_run(p_source uuid, p_kind text, p_ok boolean, p_checks jsonb, p_ms int)
```

---

## 3. Contratos da API

Base: `https://hub-api.lexgroup.com.br`.
- Autenticação: `Authorization: Bearer <JWT do Supabase>`.
- Todas as rotas `/sources` exigem `is_source_admin`. Sem isso: **403**. Organização inexistente dá
  **404**, com a mesma resposta de "sem acesso".
- Erros: seguem o formato atual da API, com `code` estável para o front.
- Checagens no formato `{ "key": "network|login|read|readOnly", "ok": bool, "severity": "error|warn", "message": "pt-BR", "ms": int }`.
  Quando uma checagem falha, as seguintes voltam com `"skipped": true`.

### PR 1

**`GET /orgs/{org}/sources/{product}/offices`**: `product ∈ lexpre | lexflow`

- Faz `select id, nome from escritorio` (LexPre) ou o equivalente no LexFlow, mais a atividade dos
  últimos 30 dias, com 10 min de cache.
- Mostra em qual unidade, de **qualquer** organização, cada escritório já está ligado.

```json
200 { "product": "lexpre",
      "offices": [ { "ref": "4", "name": "Escritório Manaus Centro", "activity30d": 128, "linkedTo": null },
                   { "ref": "1", "name": "Nicolas Gomes", "activity30d": 3412,
                     "linkedTo": { "org": "LexGroup", "unit": "NG" } } ] }
503 { "code": "source_unavailable" }   -- banco do produto fora
```

A ligação é pela RPC `api.link_product_office` (ver o SQL).

### PR 2

**`POST /orgs/{org}/units/{unit}/sources`**: o botão **Testar e salvar** (Postgres; MySQL no PR 3)

```json
{ "connector": "postgres", "name": "Banco Manaus Centro",
  "host": "db.operacao.com.br", "port": 5432, "database": "operacao",
  "user": "lexhub_leitura", "password": "…", "ssl": true, "writerAck": false }

201 { "source": { ...item no formato de list_sources... }, "checks": [...] }
200 { "saved": false, "checks": [...] }                          -- teste falhou: nada gravado
409 { "code": "writer_ack_required", "checks": [...] }           -- pode escrever e writerAck=false
422 { "code": "invalid_input", "fields": { "port": "Use uma porta entre 1024 e 65535" } }
422 { "code": "blocked_host", "message": "Este endereço é de rede interna. Use o endereço público do banco." }
429 { "code": "rate_limited" }                                    -- 10 por minuto por pessoa
```

- A API testa (rede → IP conectado → login → leitura → só leitura), grava o `schema_cache` e chama
  `connect_source`. O teste fica registrado em `source_sync_runs` (`run_kind='test'`).
- Os erros de rede são genéricos. Não repassamos a mensagem do driver.

**`POST /orgs/{org}/sources/{id}/test`** (Testar de novo): usa a credencial do Vault.

```json
200 { "ok": true, "checks": [...] }
```

**`PUT /orgs/{org}/sources/{id}/secret`** (Trocar senha):

```json
{ "password": "…", "writerAck": false }
200 { "source": {...}, "checks": [...] } · 200 { "saved": false, "checks": [...] } · 409 writer_ack_required
```

- Testa com a senha nova antes de trocar.
- Publica a invalidação do pool (pub/sub) e incrementa `config_version`.

**`DELETE /orgs/{org}/sources/{id}`** (Desconectar): `204`.

- Fecha o pool, apaga as chaves de cache da fonte, a fonte e o segredo.
- Fontes `lexpre`, `lexflow` e `internal` não passam por aqui: **409** `{ "code": "not_removable" }`.
  LexPre/LexFlow usam `unlink_product_office`, e NG/LA só por migration.

### PR 3 (adiantado para o front)

**`POST /orgs/{org}/sources/sheets/inspect`**: `{ "url": "https://docs.google.com/spreadsheets/d/…" }`

```json
200 { "spreadsheetId": "1AbC…", "title": "Financeiro MCO", "tabs": ["FINANCEIRO", "PRODUCAO"] }
422 { "code": "invalid_link" } · 403 { "code": "not_shared", "serviceAccount": "lexhub-sync@…" }
```

**Conectar planilha** usa a mesma rota de criar fonte, com
`{ "connector": "sheets", "name": "…", "spreadsheetId": "…", "tab": "FINANCEIRO" }`.

---

## 4. Infra a confirmar

1. Qual usuário está na `DATABASE_URL`.
2. Firewall de saída na VPS e exceções privadas (NG/LA são privados?).
3. Swarm com mais de um nó? Se tiver, fixar a API num nó.
