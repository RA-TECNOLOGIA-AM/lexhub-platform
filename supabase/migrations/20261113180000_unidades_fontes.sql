-- =============================================================================
-- Unidades e fontes: o cadastro das fontes de cada organização, o log de sincronizações e a lista da tela.
--
-- Aditiva: cria 2 tabelas, 2 permissões, 1 auxiliar e 1 função; troca api.my_admin_permissions (ganha 'sources').
-- O front chama pelo schema api (rpc), sem a API em Python. Quem vê (só leitura, nada se edita ainda):
--   * sources.view (Owner, Desenvolvedor): todas as unidades da organização;
--   * unit.sources.view (Gestor, Controller): só as unidades em que têm esse cargo.
-- Tipos de fonte:
--   * produto contratado (LexFlow, LexPre): sem unidade dona; a organização tem porque assinou;
--   * fonte conectada (banco interno, planilha): tem unidade dona. Outra unidade pode usá-la
--     (ex.: LARJ usa o banco NG): na tela dela aparece "gerenciada por" a dona.
-- O status vem do log (app.source_sync_runs), que fica vazio até o worker de sincronização existir.
-- Teste: supabase/tests/unidades_fontes_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Tabelas
-- ---------------------------------------------------------------------------
-- As fontes da organização. key = o nome usado em app.unit_source_refs.source e no .env da API
-- ('lexpre', 'lexflow', 'ng', 'laadv', ...).
create table app.data_sources (
    id            uuid primary key default gen_random_uuid(),
    org_id        uuid not null references app.organizations (id) on delete cascade,
    key           text not null check (key ~ '^[a-z][a-z0-9_]{1,31}$'),
    kind          text not null check (kind in ('database', 'flow', 'finance', 'sheet')), -- define o ícone
    name          text not null check (length(trim(name)) > 0),
    detail        text not null default '',
    owner_unit_id uuid, -- null = produto contratado pela organização
    active        boolean not null default true,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    unique (org_id, key),
    foreign key (org_id, owner_unit_id) references app.units (org_id, id) on delete cascade
);

-- Uma linha por sincronização de uma fonte (o worker grava; a tela só lê pela função).
create table app.source_sync_runs (
    id          bigint generated always as identity primary key,
    source_id   uuid not null references app.data_sources (id) on delete cascade,
    started_at  timestamptz not null default now(),
    finished_at timestamptz, -- null = rodando
    ok          boolean,     -- null = rodando
    rows        integer check (rows >= 0),
    error       text
);

create index source_sync_runs_source_started on app.source_sync_runs (source_id, started_at desc);

-- Sem policy para authenticated: ninguém lê direto; a tela usa api.list_sources (security definer).
alter table app.data_sources enable row level security;
alter table app.source_sync_runs enable row level security;
revoke all on app.data_sources, app.source_sync_runs from public, anon, authenticated;
grant all on app.data_sources, app.source_sync_runs to service_role;

-- ---------------------------------------------------------------------------
-- 2. Permissões
-- ---------------------------------------------------------------------------
insert into app.role_permissions (role_key, permission) values
    ('owner', 'sources.view'),
    ('admin', 'sources.view'),
    ('gestor', 'unit.sources.view'),
    ('controller', 'unit.sources.view')
on conflict do nothing;

-- ---------------------------------------------------------------------------
-- 3. Auxiliar: unidades ativas da organização que quem chama vê nesta tela ('{}' = nenhuma)
-- ---------------------------------------------------------------------------
create function app_private.sources_scope(p_org uuid) returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(u.id), '{}')
    from app.units u
    where u.org_id = p_org
      and u.active
      and (
          p_org = any (app_private.my_org_ids_with('sources.view'))
          or u.id = any (app_private.my_unit_ids_with('unit.sources.view'))
      );
$$;

revoke all on function app_private.sources_scope(uuid) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 4. api.list_sources: as unidades do escopo, cada uma com as fontes que usa (app.unit_source_refs)
-- ---------------------------------------------------------------------------
-- Status de cada fonte, pelo log:
--   waiting = nunca sincronizou; late = falhou depois do último sucesso ou o último sucesso passou de
--   2 intervalos; healthy = o resto. ('pending' = falta autorizar fica para o Conta Azul.)
create function api.list_sources(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org   uuid;
    v_scope uuid[];
    -- Mesmo intervalo que a tela mostra no cabeçalho.
    v_every constant integer := 10;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.sources_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta organização.';
    end if;

    return jsonb_build_object(
        'syncEveryMin', v_every,
        'unitLimit', null, -- o plano ainda não guarda limite de unidades
        'units', coalesce((
            select jsonb_agg(
                jsonb_build_object(
                    'unit', jsonb_build_object('code', u.code, 'name', u.name),
                    'timezone', u.timezone,
                    'dashboards', (select count(*) from app.org_dashboards od
                                   where od.unit_id = u.id and od.enabled),
                    'lastFailure', (
                        select jsonb_build_object('at', r.finished_at, 'source', ds.name, 'message', r.error)
                        from app.unit_source_refs ref
                        join app.data_sources ds on ds.org_id = u.org_id and ds.key = ref.source and ds.active
                        join app.source_sync_runs r on r.source_id = ds.id
                        where ref.unit_id = u.id
                          and r.ok = false
                          and r.finished_at > now() - interval '7 days'
                        order by r.finished_at desc
                        limit 1
                    ),
                    'sources', coalesce((
                        select jsonb_agg(s.item order by s.is_product desc, s.item ->> 'name')
                        from (
                            select ds.owner_unit_id is null as is_product,
                                   jsonb_build_object(
                                       'id', ds.key,
                                       'kind', ds.kind,
                                       'name', ds.name,
                                       'detail', ds.detail,
                                       'group', case when ds.owner_unit_id is null then 'product' else 'connection' end,
                                       'managedBy', case when ds.owner_unit_id <> u.id then owner.name end,
                                       'syncedAt', last_ok.finished_at,
                                       'rows', last_ok.rows,
                                       'failures', fails.n,
                                       'status', case
                                           when not exists (select 1 from app.source_sync_runs r where r.source_id = ds.id)
                                               then 'waiting'
                                           when fails.n > 0
                                             or last_ok.finished_at is null
                                             or last_ok.finished_at < now() - make_interval(mins => 2 * v_every)
                                               then 'late'
                                           else 'healthy'
                                       end
                                   ) as item
                            from app.unit_source_refs ref
                            join app.data_sources ds on ds.org_id = u.org_id and ds.key = ref.source and ds.active
                            left join app.units owner on owner.id = ds.owner_unit_id
                            left join lateral (
                                select r.finished_at, r.rows from app.source_sync_runs r
                                where r.source_id = ds.id and r.ok
                                order by r.finished_at desc limit 1
                            ) last_ok on true
                            cross join lateral (
                                select count(*)::integer as n from app.source_sync_runs r
                                where r.source_id = ds.id and r.ok = false
                                  and (last_ok.finished_at is null or r.finished_at > last_ok.finished_at)
                            ) fails
                            where ref.unit_id = u.id
                        ) s
                    ), '[]'::jsonb)
                )
                order by u.name
            )
            from app.units u
            where u.id = any (v_scope)
        ), '[]'::jsonb)
    );
end;
$$;

revoke all on function api.list_sources(text) from public, anon;
grant execute on function api.list_sources(text) to authenticated;

-- ---------------------------------------------------------------------------
-- 5. Menu: api.my_admin_permissions ganha 'sources' (mesmo corpo de 20261113160000_permissoes_menu.sql)
-- ---------------------------------------------------------------------------
create or replace function api.my_admin_permissions(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null then
        return jsonb_build_object('access', false, 'members', false, 'sources', false);
    end if;
    return jsonb_build_object(
        'access', cardinality(app_private.access_scope(v_org)) > 0,
        'members', cardinality(app_private.members_scope(v_org)) > 0,
        'sources', cardinality(app_private.sources_scope(v_org)) > 0
    );
end;
$$;

-- ---------------------------------------------------------------------------
-- 6. Dados da LexGroup: as fontes e as ligações que faltavam
-- ---------------------------------------------------------------------------
insert into app.data_sources (org_id, key, kind, name, detail, owner_unit_id)
select o.id, v.key, v.kind, v.name, v.detail, u.id
from app.organizations o
cross join (values
    ('lexpre',  'database', 'LexPre',  'Comercial e pré-protocolo',                 null),
    ('lexflow', 'flow',     'LexFlow', 'Execução, acordos, recursal e publicações', null),
    ('ng',      'database', 'Sistema jurídico NG', 'Postgres · somente leitura', 'NG'),
    ('laadv',   'database', 'Sistema jurídico LA', 'Postgres · somente leitura', 'LA'),
    ('sheets_protocolo_passado_ng', 'sheet', 'Planilha do protocolo passado', 'Google Sheets · conta de serviço', 'NG'),
    ('sheets_financeiro_ng',        'sheet', 'Planilha do financeiro',        'Google Sheets · conta de serviço', 'NG'),
    ('sheets_financeiro_la',        'sheet', 'Planilha do financeiro',        'Google Sheets · conta de serviço', 'LA')
) as v (key, kind, name, detail, owner_code)
left join app.units u on u.org_id = o.id and u.code = v.owner_code
where o.slug = 'lexgroup'
on conflict (org_id, key) do nothing;

-- LA -> banco LA; cada planilha -> a unidade dona (ref = código da unidade, como no NG e no LexFlow).
insert into app.unit_source_refs (unit_id, source, ref)
select u.id, v.source, v.ref
from app.units u
join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
join (values
    ('LA', 'laadv',                       'LA'),
    ('NG', 'sheets_protocolo_passado_ng', 'NG'),
    ('NG', 'sheets_financeiro_ng',        'NG'),
    ('LA', 'sheets_financeiro_la',        'LA')
) as v (code, source, ref) on v.code = u.code
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.unit_source_refs where source in ('laadv', 'sheets_protocolo_passado_ng',
--     'sheets_financeiro_ng', 'sheets_financeiro_la');
-- (recriar api.my_admin_permissions com o corpo de 20261113160000_permissoes_menu.sql)
-- drop function api.list_sources(text);
-- drop function app_private.sources_scope(uuid);
-- delete from app.role_permissions where permission in ('sources.view', 'unit.sources.view');
-- drop table app.source_sync_runs;
-- drop table app.data_sources;
-- =============================================================================
