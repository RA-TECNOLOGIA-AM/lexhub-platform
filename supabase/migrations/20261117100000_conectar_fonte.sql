-- =============================================================================
-- Conectar fonte (PR 1): quem gerencia fontes, travas de NG/LA e ligar escritório do LexPre/LexFlow.
--
-- Spec: docs/superpowers/specs/2026-11-17-conectar-fonte-design.md
-- Regras (Luís, 17/11):
--   * só Owner/Dev da organização LexGroup conectam e gerenciam fontes, em qualquer organização;
--   * NG e LA (bancos internos) só nas unidades liberadas da LexGroup (hoje NG, LA e RJ);
--   * um escritório do LexPre/LexFlow fica ligado a uma unidade só, no banco todo.
-- Aditiva: 2 auxiliares, colunas novas em data_sources e source_sync_runs, 1 tabela, 1 trigger,
-- 1 índice, 2 funções novas; troca app_private.source_item e api.list_sources.
-- Teste: supabase/tests/conectar_fonte_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Quem gerencia fontes: Owner/Dev ativos da LexGroup (o Owner de um cliente não)
-- ---------------------------------------------------------------------------
-- A organização da casa num lugar só (para não espalhar o slug).
create function app_private.home_org_id() returns uuid
language sql stable security definer
set search_path = ''
as $$
    select o.id from app.organizations o where o.slug = 'lexgroup' and o.active;
$$;

create function app_private.is_source_admin(p_user uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select p_user is not null and exists (
        select 1
        from app.memberships m
        where m.org_id = app_private.home_org_id()
          and m.user_id = p_user
          and m.status = 'active'
          and m.role_key in ('owner', 'admin')
    );
$$;

revoke all on function app_private.home_org_id() from public, anon, authenticated;
revoke all on function app_private.is_source_admin(uuid) from public, anon, authenticated;
grant execute on function app_private.is_source_admin(uuid) to service_role; -- a API checa por p_user

-- ---------------------------------------------------------------------------
-- 2. data_sources: como a API conecta (connector) e a configuração sem senha
-- ---------------------------------------------------------------------------
alter table app.data_sources
    add column connector      text not null default 'internal'
        check (connector in ('lexpre', 'lexflow', 'internal', 'postgres', 'mysql', 'sheets')),
    add column config         jsonb not null default '{}'::jsonb,
    add column secret_id      uuid,    -- vault.secrets (Postgres/MySQL, PR 2)
    add column writer_ack     boolean not null default false, -- salvo com usuário que pode escrever
    add column schema_cache   jsonb,   -- {tabela: [[coluna, tipo], ...]} gravado no salvar
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
    -- As 3 planilhas cadastradas antes do Conectar fonte ainda não têm config ('{}').
    add constraint data_sources_sheet_config
        check (connector <> 'sheets' or config = '{}'::jsonb or config ?& array['spreadsheet_id', 'tab']);

update app.data_sources set connector = case
    when key = 'lexpre' then 'lexpre'
    when key = 'lexflow' then 'lexflow'
    when kind = 'sheet' then 'sheets'
    else 'internal'
end;

-- ---------------------------------------------------------------------------
-- 3. Travas: fonte sempre da organização da unidade; banco interno só em unidade liberada
-- ---------------------------------------------------------------------------
create table app.internal_source_units (
    source_id  uuid not null references app.data_sources (id) on delete cascade,
    unit_id    uuid not null references app.units (id) on delete cascade,
    created_at timestamptz not null default now(),
    primary key (source_id, unit_id)
);

alter table app.internal_source_units enable row level security; -- sem policy: só migration
revoke all on app.internal_source_units from public, anon, authenticated;
grant all on app.internal_source_units to service_role;

-- Liberadas hoje: as unidades da LexGroup que já usam o banco (ng: NG e RJ; laadv: LA).
insert into app.internal_source_units (source_id, unit_id)
select ds.id, r.unit_id
from app.data_sources ds
join app.unit_source_refs r on r.source = ds.key
join app.units u on u.id = r.unit_id and u.org_id = ds.org_id
where ds.connector = 'internal'
  and ds.org_id = app_private.home_org_id()
on conflict do nothing;

create function app_private.check_unit_source_ref() returns trigger
language plpgsql security definer
set search_path = ''
as $$
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
        select 1 from app.internal_source_units i
        where i.source_id = v_source.id and i.unit_id = new.unit_id
    ) then
        raise exception using errcode = '42501', message = 'Banco interno não liberado para esta unidade.';
    end if;
    return new;
end;
$$;

revoke all on function app_private.check_unit_source_ref() from public, anon, authenticated;

create trigger unit_source_refs_check before insert or update on app.unit_source_refs
    for each row execute function app_private.check_unit_source_ref();

-- Um escritório do LexPre/LexFlow em uma unidade só, no banco todo (todas as organizações).
create unique index unit_source_refs_product_ref_uq
    on app.unit_source_refs (source, ref)
    where source in ('lexpre', 'lexflow');

-- ---------------------------------------------------------------------------
-- 4. source_sync_runs: tipo da execução e resultado das checagens
-- ---------------------------------------------------------------------------
alter table app.source_sync_runs
    add column run_kind    text not null default 'sync' check (run_kind in ('sync', 'health', 'test')),
    add column checks      jsonb,
    add column duration_ms integer check (duration_ms >= 0);

-- ---------------------------------------------------------------------------
-- 5. source_item: + connector e o status 'no_dashboards' (nenhum dashboard ligado na unidade usa a fonte)
-- ---------------------------------------------------------------------------
create or replace function app_private.source_item(p_source uuid, p_unit uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', ds.key,
        'kind', ds.kind,
        'connector', ds.connector,
        'name', ds.name,
        'detail', ds.detail,
        'group', case when ds.owner_unit_id is null then 'product' else 'connection' end,
        'managedBy', case when ds.owner_unit_id <> p_unit then owner.name end,
        'syncedAt', last_ok.finished_at,
        'rows', last_ok.rows,
        'failures', fails.n,
        -- Falha vem antes de tudo; depois "nenhum dashboard ligado na unidade usa a fonte"; depois o log.
        'status', case
            when exists (select 1 from app.source_sync_runs r where r.source_id = ds.id)
             and (fails.n > 0
                  or last_ok.finished_at is null
                  or last_ok.finished_at < now() - make_interval(mins => 2 * app_private.sync_every_min()))
                then 'late'
            when not exists (
                select 1
                from app.dashboard_sources dsrc
                join app.dashboard_catalog c on c.key = dsrc.dashboard_key and c.active
                join app.org_dashboards od on od.dashboard_key = c.key and od.unit_id = p_unit and od.enabled
                where dsrc.source_key = ds.key
            ) then 'no_dashboards'
            when not exists (select 1 from app.source_sync_runs r where r.source_id = ds.id) then 'waiting'
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

-- ---------------------------------------------------------------------------
-- 6. api.list_sources: + canManageSources (mesmo resultado de 20261113220000_nova_unidade.sql)
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
        'canManageUnits', v_org = any (app_private.my_org_ids_with('units.manage')),
        'canManageSources', app_private.is_source_admin(auth.uid()),
        'units', coalesce((
            select jsonb_agg(app_private.unit_sources_json(u.id) order by u.name)
            from app.units u
            where u.id = any (v_scope)
        ), '[]'::jsonb)
    );
end;
$$;

-- ---------------------------------------------------------------------------
-- 7. Ligar e desligar escritório do LexPre/LexFlow (a tela; a lista de escritórios vem da API)
-- ---------------------------------------------------------------------------
-- Organização + unidade ativas, só para quem gerencia fontes; senão 42501.
create function app_private.require_source_unit(p_org text, p_unit text) returns app.units
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_unit app.units;
begin
    if not app_private.is_source_admin(auth.uid()) then
        raise exception using errcode = '42501', message = 'Só a TI da LexGroup conecta fontes.';
    end if;
    select u.* into v_unit
    from app.units u
    join app.organizations o on o.id = u.org_id and o.active
    where o.slug = lower(trim(p_org)) and u.code = upper(trim(coalesce(p_unit, ''))) and u.active;
    if v_unit.id is null then
        raise exception using errcode = 'P0001', message = 'Unidade não encontrada.';
    end if;
    return v_unit;
end;
$$;

-- Ref do escritório no formato que os dashboards usam. LexPre: o id. LexFlow: os 3 escritórios que os
-- dashboards já conhecem guardam o código da v1 (id_escritorio_assinante 20 = NG, 21 = LA, 27 = RJ),
-- assim o índice único também barra ligar o mesmo escritório pelo id; os novos guardam o id.
create function app_private.product_ref(p_product text, p_ref text) returns text
language sql immutable
set search_path = ''
as $$
    select case
        when p_product = 'lexflow' and trim(p_ref) = '20' then 'NG'
        when p_product = 'lexflow' and trim(p_ref) = '21' then 'LA'
        when p_product = 'lexflow' and trim(p_ref) = '27' then 'RJ'
        else trim(p_ref)
    end;
$$;

revoke all on function app_private.require_source_unit(text, text) from public, anon, authenticated;
revoke all on function app_private.product_ref(text, text) from public, anon, authenticated;

create function api.link_product_office(p_org text, p_unit text, p_product text, p_ref text) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_unit  app.units := app_private.require_source_unit(p_org, p_unit);
    v_ref   text;
    v_label text;
    v_taken text;
begin
    if p_product not in ('lexpre', 'lexflow') then
        raise exception using errcode = 'P0001', message = 'Produto inválido: use LexPre ou LexFlow.';
    end if;
    if coalesce(trim(p_ref), '') !~ '^[0-9]{1,9}$' then
        raise exception using errcode = 'P0001', message = 'Escolha um escritório da lista.';
    end if;
    v_ref := app_private.product_ref(p_product, p_ref);
    v_label := case p_product when 'lexpre' then 'LexPre' else 'LexFlow' end;

    if exists (select 1 from app.unit_source_refs r where r.unit_id = v_unit.id and r.source = p_product) then
        raise exception using errcode = 'P0001', message = format('Esta unidade já está ligada ao %s.', v_label);
    end if;

    -- O cliente novo ganha a fonte do produto na organização dele (a trigger exige a mesma organização).
    insert into app.data_sources (org_id, key, kind, name, detail, connector, created_by)
    values (v_unit.org_id, p_product,
            case p_product when 'lexpre' then 'database' else 'flow' end,
            v_label,
            case p_product when 'lexpre' then 'Comercial e pré-protocolo'
                           else 'Execução, acordos, recursal e publicações' end,
            p_product, auth.uid())
    on conflict (org_id, key) do update set active = true, updated_at = now();

    begin
        insert into app.unit_source_refs (unit_id, source, ref) values (v_unit.id, p_product, v_ref);
    exception when unique_violation then
        select o.name || ' · ' || u.code into v_taken
        from app.unit_source_refs r
        join app.units u on u.id = r.unit_id
        join app.organizations o on o.id = u.org_id
        where r.source = p_product and r.ref = v_ref;
        raise exception using errcode = 'P0001',
            message = format('Este escritório já está ligado à unidade %s.', coalesce(v_taken, 'outra'));
    end;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_unit.org_id, auth.uid(), 'source.office_linked', 'unit', v_unit.id::text,
            jsonb_build_object('unit', v_unit.code, 'product', p_product, 'ref', v_ref, 'office', trim(p_ref)));

    return app_private.unit_sources_json(v_unit.id);
end;
$$;

create function api.unlink_product_office(p_org text, p_unit text, p_product text) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_unit app.units := app_private.require_source_unit(p_org, p_unit);
    v_ref  text;
begin
    if p_product not in ('lexpre', 'lexflow') then
        raise exception using errcode = 'P0001', message = 'Produto inválido: use LexPre ou LexFlow.';
    end if;
    delete from app.unit_source_refs r
    where r.unit_id = v_unit.id and r.source = p_product
    returning r.ref into v_ref;
    if v_ref is null then
        raise exception using errcode = 'P0001', message = 'Esta unidade não está ligada a esse produto.';
    end if;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_unit.org_id, auth.uid(), 'source.office_unlinked', 'unit', v_unit.id::text,
            jsonb_build_object('unit', v_unit.code, 'product', p_product, 'ref', v_ref));

    return app_private.unit_sources_json(v_unit.id);
end;
$$;

revoke all on function api.link_product_office(text, text, text, text) from public, anon;
revoke all on function api.unlink_product_office(text, text, text) from public, anon;
grant execute on function api.link_product_office(text, text, text, text) to authenticated;
grant execute on function api.unlink_product_office(text, text, text) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.unlink_product_office(text, text, text);
-- drop function api.link_product_office(text, text, text, text);
-- drop function app_private.product_ref(text, text);
-- drop function app_private.require_source_unit(text, text);
-- (recriar api.list_sources com o corpo de 20261113220000_nova_unidade.sql)
-- (recriar app_private.source_item com o corpo de 20261113200000_detalhe_fonte.sql)
-- alter table app.source_sync_runs drop column duration_ms, drop column checks, drop column run_kind;
-- drop index app.unit_source_refs_product_ref_uq;
-- drop trigger unit_source_refs_check on app.unit_source_refs;
-- drop function app_private.check_unit_source_ref();
-- drop table app.internal_source_units;
-- alter table app.data_sources drop constraint data_sources_sheet_config, drop constraint data_sources_db_secret,
--     drop constraint data_sources_db_config, drop constraint data_sources_config_no_secret,
--     drop column created_by, drop column config_version, drop column schema_cache, drop column writer_ack,
--     drop column secret_id, drop column config, drop column connector;
-- drop function app_private.is_source_admin(uuid);
-- drop function app_private.home_org_id();
-- =============================================================================
