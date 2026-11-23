-- =============================================================================
-- Plataforma gere as unidades de qualquer cliente + Auditoria por organização e unidade
--
-- 1) Owner/Desenvolvedor da LexGroup e equipe RA (app_private.can_see_clients) veem e gerem as unidades e
--    fontes de qualquer organização ativa SEM ser membro dela: criar, editar e excluir unidade (conectar fonte
--    já era da TI da LexGroup). Dados do cliente (dashboards, membros) continuam só para membros. Cada ação
--    vai para a auditoria daquela organização, com a pessoa da plataforma como autora (aparece pelo e-mail).
-- 2) api.list_audit ganha p_unit (código) e devolve units (todas as unidades da organização, excluídas
--    também) e orgs (só para a plataforma: todas as organizações, encerradas também; null para os outros).
--    A plataforma audita qualquer organização, inclusive encerrada.
--    Evento "da unidade": metadata.unit = código (dashboards, fontes), alvo = a unidade (unit.*), ou
--    metadata.units com o código (convite). Entradas e mudanças de membro não têm unidade: saem do filtro.
-- 3) api.log_audit_export ganha p_unit e segue a mesma regra de quem pode (a exportação fica na organização
--    auditada).
-- Teste: supabase/tests/plataforma_unidades_auditoria_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Unidades e fontes: a plataforma entra em qualquer organização ativa
-- ---------------------------------------------------------------------------
create or replace function app_private.sources_scope(p_org uuid) returns uuid[]
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
          or app_private.can_see_clients()
      );
$$;

-- Mesmo corpo de 20261113220000_nova_unidade.sql + a plataforma.
create or replace function app_private.require_units_manager(p_org text, p_name text, p_timezone text) returns uuid
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null
       or not (v_org = any (app_private.my_org_ids_with('units.manage')) or app_private.can_see_clients()) then
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

-- Mesmo corpo de 20261123140000_excluir_unidade_organizacao.sql + a plataforma.
create or replace function app_private.require_unit_to_delete(p_org text, p_code text) returns app.units
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org  uuid;
    v_unit app.units;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null
       or not (v_org = any (app_private.my_org_ids_with('units.manage')) or app_private.can_see_clients()) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor excluem unidades.';
    end if;
    select u.* into v_unit from app.units u
    where u.org_id = v_org and u.code = upper(trim(coalesce(p_code, ''))) and u.active;
    if v_unit.id is null then
        raise exception using errcode = 'P0001', message = 'Unidade não encontrada.';
    end if;
    return v_unit;
end;
$$;

-- Mesmo corpo de 20261123140000_excluir_unidade_organizacao.sql; canManageUnits inclui a plataforma.
create or replace function api.list_sources(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org   uuid;
    v_name  text;
    v_scope uuid[];
begin
    select o.id, o.name into v_org, v_name from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.sources_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta organização.';
    end if;

    return jsonb_build_object(
        'orgName', v_name,
        'syncEveryMin', app_private.sync_every_min(),
        'unitLimit', null, -- o plano ainda não guarda limite de unidades
        'canManageUnits', v_org = any (app_private.my_org_ids_with('units.manage')) or app_private.can_see_clients(),
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
-- 2. Auditoria: organização (plataforma) e unidade
-- ---------------------------------------------------------------------------
-- A organização que a pessoa pode auditar: a dela com audit.view (ativa) ou, para a plataforma, qualquer
-- uma (encerrada também). Senão 42501.
create function app_private.audit_org(p_org text) returns uuid
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org    uuid;
    v_active boolean;
begin
    select o.id, o.active into v_org, v_active from app.organizations o where o.slug = lower(trim(p_org));
    if v_org is null
       or not ((v_active and v_org = any (app_private.my_org_ids_with('audit.view'))) or app_private.can_see_clients()) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor veem a auditoria.';
    end if;
    return v_org;
end;
$$;

revoke all on function app_private.audit_org(text) from public, anon, authenticated;

drop function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, integer);

-- Mesmo corpo de 20261119210000_auditoria_dashboards_abertos.sql + p_unit, units e orgs.
create function api.list_audit(
    p_org text,
    p_from timestamptz default null,
    p_to timestamptz default null,
    p_actions text[] default null,
    p_exclude_actions text[] default null,
    p_actor text default null,
    p_unit text default null,
    p_limit integer default 2000
) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org     uuid := app_private.audit_org(p_org);
    v_limit   integer := greatest(1, least(coalesce(p_limit, 2000), 2000));
    v_unit    text := nullif(upper(trim(coalesce(p_unit, ''))), '');
    v_unit_id text;
    v_events  jsonb;
    v_count   integer;
    v_actors  jsonb;
begin
    if v_unit is not null then
        select u.id::text into v_unit_id from app.units u where u.org_id = v_org and u.code = v_unit;
    end if;

    with base as (
        select l.*,
               coalesce(m.full_name, au.email, 'Sistema') as actor_name,
               au.email as actor_email
        from app.audit_log l
        left join app.memberships m on m.org_id = l.org_id and m.user_id = l.actor_user_id
        left join auth.users au on au.id = l.actor_user_id
        where l.org_id = v_org
          and (p_from is null or l.created_at >= p_from)
          and (p_to is null or l.created_at < p_to)
          and (p_actions is null or l.action = any (p_actions))
          and (p_exclude_actions is null or not (l.action = any (p_exclude_actions)))
          and (v_unit is null
               or l.metadata ->> 'unit' = v_unit
               or (l.target_type = 'unit' and (l.target_id = v_unit_id or l.metadata ->> 'code' = v_unit))
               or (jsonb_typeof(l.metadata -> 'units') = 'array' and l.metadata -> 'units' ? v_unit))
    ),
    page as (
        select b.*, row_number() over (order by b.created_at desc, b.id desc) as rn
        from base b
        where p_actor is null or b.actor_name = p_actor
        order by b.created_at desc, b.id desc
        limit v_limit + 1
    )
    select coalesce(jsonb_agg(
               jsonb_build_object(
                   'id', a.id::text,
                   'at', a.created_at,
                   'action', a.action,
                   'actor', a.actor_name,
                   'actorEmail', a.actor_email,
                   'targetType', a.target_type,
                   'targetId', a.target_id,
                   'targetName', case a.target_type
                       when 'dashboard' then (select c.name from app.dashboard_catalog c where c.key = a.target_id)
                       when 'unit' then (select u.name from app.units u where u.id::text = a.target_id)
                       when 'membership' then (select tm.full_name from app.memberships tm where tm.id::text = a.target_id)
                   end,
                   'metadata', a.metadata
               )
               order by a.created_at desc, a.id desc
           ) filter (where a.rn <= v_limit), '[]'::jsonb),
           count(*),
           (select coalesce(jsonb_agg(x.actor_name order by x.actor_name), '[]'::jsonb)
              from (select distinct b.actor_name from base b) x)
      into v_events, v_count, v_actors
    from page a;

    return jsonb_build_object(
        'events', v_events,
        'truncated', v_count > v_limit,
        'actors', v_actors,
        -- Todas as unidades, excluídas também (a auditoria delas continua consultável).
        'units', coalesce((
            select jsonb_agg(jsonb_build_object('code', u.code, 'name', u.name, 'deleted', not u.active)
                             order by not u.active, u.name)
            from app.units u where u.org_id = v_org
        ), '[]'::jsonb),
        -- Só a plataforma troca de organização (encerradas também).
        'orgs', case when app_private.can_see_clients() then coalesce((
            select jsonb_agg(jsonb_build_object('slug', o.slug, 'name', o.name, 'closed', not o.active)
                             order by not o.active, o.name)
            from app.organizations o
        ), '[]'::jsonb) end
    );
end;
$$;

revoke all on function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, text, integer) from public, anon;
grant execute on function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, text, integer) to authenticated;

drop function api.log_audit_export(text, text, text, integer);

-- Mesmo corpo de 20261118190000_auditoria_exportar.sql + p_unit e a regra de app_private.audit_org.
create function api.log_audit_export(p_org text, p_kind text, p_actor text, p_rows integer, p_unit text default null)
returns void
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org uuid := app_private.audit_org(p_org);
begin
    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'audit.export', 'organization', v_org::text,
            jsonb_strip_nulls(jsonb_build_object(
                'kind', nullif(trim(p_kind), ''),
                'actor', nullif(trim(p_actor), ''),
                'unit', nullif(upper(trim(coalesce(p_unit, ''))), ''),
                'rows', greatest(coalesce(p_rows, 0), 0),
                'format', 'csv'
            )));
end;
$$;

revoke all on function api.log_audit_export(text, text, text, integer, text) from public, anon;
grant execute on function api.log_audit_export(text, text, text, integer, text) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.log_audit_export(text, text, text, integer, text);
--   e recriar api.log_audit_export(text, text, text, integer) com o corpo de 20261118190000_auditoria_exportar.sql
-- drop function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, text, integer);
--   e recriar a de 7 parâmetros com o corpo de 20261119210000_auditoria_dashboards_abertos.sql
-- drop function app_private.audit_org(text);
-- recriar api.list_sources e app_private.require_unit_to_delete com o corpo de 20261123140000_excluir_unidade_organizacao.sql
-- recriar app_private.require_units_manager com o corpo de 20261113220000_nova_unidade.sql
-- recriar app_private.sources_scope com o corpo de 20261113180000_unidades_fontes.sql
-- =============================================================================
