-- =============================================================================
-- Detalhe da fonte: o modal que abre ao clicar numa fonte em Unidades e fontes.
--
-- Aditiva: cria app.dashboard_sources (dashboard -> fontes que usa), 2 auxiliares e api.source_detail;
-- troca api.list_sources para usar o mesmo auxiliar da linha (a regra do status fica num lugar só).
-- Quem vê: a mesma regra da lista (app_private.sources_scope). Só leitura.
-- Teste: supabase/tests/detalhe_fonte_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Dashboard -> fontes (um dashboard pode usar mais de uma; o catálogo é o mesmo para todas as organizações)
-- ---------------------------------------------------------------------------
create table app.dashboard_sources (
    dashboard_key text not null references app.dashboard_catalog (key) on delete cascade,
    source_key    text not null check (source_key ~ '^[a-z][a-z0-9_]{1,31}$'), -- app.data_sources.key
    created_at    timestamptz not null default now(),
    primary key (dashboard_key, source_key)
);

alter table app.dashboard_sources enable row level security;
revoke all on app.dashboard_sources from public, anon, authenticated;
grant all on app.dashboard_sources to service_role;

-- Ponto de partida: o rótulo que o catálogo já tinha. Banco LA e planilhas entram quando o analista confirmar.
insert into app.dashboard_sources (dashboard_key, source_key)
select c.key, case c.source when 'LexPre' then 'lexpre' when 'LexFlow' then 'lexflow' when 'NG' then 'ng' end
from app.dashboard_catalog c
where c.source in ('LexPre', 'LexFlow', 'NG')
on conflict do nothing;

-- ---------------------------------------------------------------------------
-- 2. Auxiliares
-- ---------------------------------------------------------------------------
-- Intervalo da sincronização (minutos): o cabeçalho da tela e a regra de "atrasada" usam o mesmo número.
create function app_private.sync_every_min() returns integer
language sql immutable
set search_path = ''
as $$ select 10 $$;

-- Uma fonte vista de uma unidade, no formato da lista (DataSource no front).
-- Status pelo log: waiting = nunca sincronizou; late = falhou depois do último sucesso ou o último
-- sucesso passou de 2 intervalos; healthy = o resto.
create function app_private.source_item(p_source uuid, p_unit uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', ds.key,
        'kind', ds.kind,
        'name', ds.name,
        'detail', ds.detail,
        'group', case when ds.owner_unit_id is null then 'product' else 'connection' end,
        'managedBy', case when ds.owner_unit_id <> p_unit then owner.name end,
        'syncedAt', last_ok.finished_at,
        'rows', last_ok.rows,
        'failures', fails.n,
        'status', case
            when not exists (select 1 from app.source_sync_runs r where r.source_id = ds.id) then 'waiting'
            when fails.n > 0
              or last_ok.finished_at is null
              or last_ok.finished_at < now() - make_interval(mins => 2 * app_private.sync_every_min())
                then 'late'
            else 'healthy'
        end
    )
    from app.data_sources ds
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
    where ds.id = p_source;
$$;

revoke all on function app_private.sync_every_min() from public, anon, authenticated;
revoke all on function app_private.source_item(uuid, uuid) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. api.list_sources: mesmo resultado de 20261113180000_unidades_fontes.sql, agora com os auxiliares
-- ---------------------------------------------------------------------------
create or replace function api.list_sources(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org   uuid;
    v_scope uuid[];
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.sources_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta organização.';
    end if;

    return jsonb_build_object(
        'syncEveryMin', app_private.sync_every_min(),
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
                        select jsonb_agg(item order by ds.owner_unit_id is not null, ds.name)
                        from app.unit_source_refs ref
                        join app.data_sources ds on ds.org_id = u.org_id and ds.key = ref.source and ds.active
                        cross join lateral app_private.source_item(ds.id, u.id) item
                        where ref.unit_id = u.id
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

-- ---------------------------------------------------------------------------
-- 4. api.source_detail: uma fonte vista de uma unidade (o modal)
-- ---------------------------------------------------------------------------
-- Recusa (42501) unidade fora do escopo; fonte que a unidade não usa = P0001 (a tela mostra a mensagem).
create function api.source_detail(p_org text, p_unit text, p_source text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org    uuid;
    v_unit   app.units;
    v_source app.data_sources;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    select u.* into v_unit from app.units u
    where u.org_id = v_org and u.code = p_unit
      and u.id = any (app_private.sources_scope(v_org));
    if v_unit.id is null then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta unidade.';
    end if;

    select ds.* into v_source
    from app.unit_source_refs ref
    join app.data_sources ds on ds.org_id = v_org and ds.key = ref.source and ds.active
    where ref.unit_id = v_unit.id and ref.source = p_source;
    if v_source.id is null then
        raise exception using errcode = 'P0001', message = 'Esta unidade não usa essa fonte.';
    end if;

    return jsonb_build_object(
        'unit', jsonb_build_object('code', v_unit.code, 'name', v_unit.name),
        'source', app_private.source_item(v_source.id, v_unit.id),
        'owner', (select jsonb_build_object('code', o.code, 'name', o.name)
                  from app.units o where o.id = v_source.owner_unit_id),
        -- Os dashboards ativos desta unidade que usam a fonte
        'dashboards', coalesce((
            select jsonb_agg(jsonb_build_object('key', c.key, 'name', c.name) order by c.sort_order, c.name)
            from app.dashboard_sources dsrc
            join app.dashboard_catalog c on c.key = dsrc.dashboard_key and c.active
            join app.org_dashboards od on od.dashboard_key = c.key and od.unit_id = v_unit.id and od.enabled
            where dsrc.source_key = v_source.key
        ), '[]'::jsonb),
        -- As 10 últimas sincronizações (a fonte é uma só para todas as unidades que a usam)
        'runs', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'startedAt', r.started_at, 'finishedAt', r.finished_at,
                       'ok', r.ok, 'rows', r.rows, 'error', r.error
                   ) order by r.started_at desc)
            from (select * from app.source_sync_runs
                  where source_id = v_source.id
                  order by started_at desc limit 10) r
        ), '[]'::jsonb)
    );
end;
$$;

revoke all on function api.source_detail(text, text, text) from public, anon;
grant execute on function api.source_detail(text, text, text) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.source_detail(text, text, text);
-- (recriar api.list_sources com o corpo de 20261113180000_unidades_fontes.sql)
-- drop function app_private.source_item(uuid, uuid);
-- drop function app_private.sync_every_min();
-- drop table app.dashboard_sources;
-- =============================================================================
