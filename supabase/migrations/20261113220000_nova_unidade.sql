-- =============================================================================
-- Nova unidade e fuso: criar unidade e editar nome/fuso na aba Unidades e fontes.
--
-- Aditiva: cria 1 permissão, 2 auxiliares e 2 funções; troca api.list_sources (usa o auxiliar da unidade
-- e ganha 'canManageUnits'). Quem pode: units.manage (Owner, Desenvolvedor). O código da unidade não muda
-- depois de criado: é usado em app.unit_source_refs e na URL. Toda escrita vai para app.audit_log.
-- Teste: supabase/tests/nova_unidade_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Permissão
-- ---------------------------------------------------------------------------
insert into app.role_permissions (role_key, permission) values
    ('owner', 'units.manage'),
    ('admin', 'units.manage')
on conflict do nothing;

-- ---------------------------------------------------------------------------
-- 2. Auxiliares
-- ---------------------------------------------------------------------------
-- Uma unidade no formato da lista (UnitSources no front): a lista e as escritas devolvem o mesmo formato.
create function app_private.unit_sources_json(p_unit uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'unit', jsonb_build_object('code', u.code, 'name', u.name),
        'timezone', u.timezone,
        'dashboards', (select count(*) from app.org_dashboards od where od.unit_id = u.id and od.enabled),
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
    from app.units u
    where u.id = p_unit;
$$;

-- Organização pelo slug, só para quem cria/edita unidades (Owner, Desenvolvedor); senão 42501.
-- Valida nome e fuso (o código é validado só na criação). Mensagens em pt-BR (P0001 = a tela mostra).
create function app_private.require_units_manager(p_org text, p_name text, p_timezone text) returns uuid
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids_with('units.manage'))) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor criam e editam unidades.';
    end if;
    if coalesce(trim(p_name), '') = '' then
        raise exception using errcode = 'P0001', message = 'Informe o nome da unidade.';
    end if;
    if not exists (select 1 from pg_catalog.pg_timezone_names t where t.name = p_timezone)
       or p_timezone !~ '^[A-Za-z_]+(/[A-Za-z0-9_+-]+)+$' then
        raise exception using errcode = 'P0001', message = 'Fuso inválido: escolha um da lista.';
    end if;
    return v_org;
end;
$$;

revoke all on function app_private.unit_sources_json(uuid) from public, anon, authenticated;
revoke all on function app_private.require_units_manager(text, text, text) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. api.list_sources: mesmo resultado de 20261113200000_detalhe_fonte.sql + 'canManageUnits'
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
        'units', coalesce((
            select jsonb_agg(app_private.unit_sources_json(u.id) order by u.name)
            from app.units u
            where u.id = any (v_scope)
        ), '[]'::jsonb)
    );
end;
$$;

-- ---------------------------------------------------------------------------
-- 4. api.create_unit: nova unidade (sem fontes; elas são ligadas depois)
-- ---------------------------------------------------------------------------
create function api.create_unit(p_org text, p_code text, p_name text, p_timezone text) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_org  uuid := app_private.require_units_manager(p_org, p_name, p_timezone);
    v_code text := upper(trim(coalesce(p_code, '')));
    v_id   uuid;
begin
    if v_code !~ '^[A-Z0-9_]{2,16}$' then
        raise exception using errcode = 'P0001',
            message = 'Código inválido: use de 2 a 16 letras maiúsculas, números ou _.';
    end if;
    -- Inclusive as desativadas: o código fica reservado (o histórico da auditoria aponta para ele).
    if exists (select 1 from app.units u where u.org_id = v_org and u.code = v_code) then
        raise exception using errcode = 'P0001', message = format('Já existe uma unidade com o código %s.', v_code);
    end if;

    insert into app.units (org_id, code, name, timezone)
    values (v_org, v_code, trim(p_name), p_timezone)
    returning id into v_id;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'unit.created', 'unit', v_id::text,
            jsonb_build_object('code', v_code, 'name', trim(p_name), 'timezone', p_timezone));

    return app_private.unit_sources_json(v_id);
end;
$$;

-- ---------------------------------------------------------------------------
-- 5. api.update_unit: muda nome e fuso (o código não muda)
-- ---------------------------------------------------------------------------
create function api.update_unit(p_org text, p_code text, p_name text, p_timezone text) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_org  uuid := app_private.require_units_manager(p_org, p_name, p_timezone);
    v_unit app.units;
begin
    select u.* into v_unit from app.units u
    where u.org_id = v_org and u.code = upper(trim(coalesce(p_code, ''))) and u.active
    for update;
    if v_unit.id is null then
        raise exception using errcode = 'P0001', message = 'Unidade não encontrada.';
    end if;

    if v_unit.name is distinct from trim(p_name) or v_unit.timezone is distinct from p_timezone then
        update app.units set name = trim(p_name), timezone = p_timezone, updated_at = now()
        where id = v_unit.id;

        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_org, auth.uid(), 'unit.updated', 'unit', v_unit.id::text,
                jsonb_build_object(
                    'code', v_unit.code,
                    'before', jsonb_build_object('name', v_unit.name, 'timezone', v_unit.timezone),
                    'after', jsonb_build_object('name', trim(p_name), 'timezone', p_timezone)
                ));
    end if;

    return app_private.unit_sources_json(v_unit.id);
end;
$$;

revoke all on function api.create_unit(text, text, text, text) from public, anon;
revoke all on function api.update_unit(text, text, text, text) from public, anon;
grant execute on function api.create_unit(text, text, text, text) to authenticated;
grant execute on function api.update_unit(text, text, text, text) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.update_unit(text, text, text, text);
-- drop function api.create_unit(text, text, text, text);
-- (recriar api.list_sources com o corpo de 20261113200000_detalhe_fonte.sql)
-- drop function app_private.require_units_manager(text, text, text);
-- drop function app_private.unit_sources_json(uuid);
-- delete from app.role_permissions where permission = 'units.manage';
-- =============================================================================
