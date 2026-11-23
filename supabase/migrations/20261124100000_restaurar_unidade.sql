-- =============================================================================
-- Restaurar unidade excluída (dentro dos 30 dias antes da limpeza de vez)
--
-- 1) api.list_sources ganha deletedUnits: as unidades excluídas pela tela (deleted_at preenchido) que ainda
--    não foram apagadas, com quando e quem excluiu e quando somem de vez. Só para quem gere unidades
--    (Owner/Desenvolvedor da organização e a plataforma); para os outros, [].
--    Unidades desativadas antes desta função (deleted_at nulo, ex.: COMPANHIA DE TESTE) não aparecem.
-- 2) api.restore_unit: volta a unidade (active = true) sem as fontes próprias, que foram apagadas com as
--    senhas na exclusão; os vínculos de dashboards, membros e grupos voltam como estavam.
--    Passou de 30 dias = recusa (a limpeza pode ainda não ter rodado). Auditoria: 'unit.restored'.
-- Teste: supabase/tests/restaurar_unidade_test.sql (termina com rollback).
-- =============================================================================

-- Quem gere as unidades da organização (Owner/Desenvolvedor dela ou a plataforma).
create function app_private.can_manage_units(p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select p_org = any (app_private.my_org_ids_with('units.manage')) or app_private.can_see_clients();
$$;

revoke all on function app_private.can_manage_units(uuid) from public, anon, authenticated;

-- Mesmo corpo de 20261123150000_plataforma_unidades_auditoria.sql + deletedUnits.
create or replace function api.list_sources(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org    uuid;
    v_name   text;
    v_scope  uuid[];
    v_manage boolean;
begin
    select o.id, o.name into v_org, v_name from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.sources_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta organização.';
    end if;
    v_manage := app_private.can_manage_units(v_org);

    return jsonb_build_object(
        'orgName', v_name,
        'syncEveryMin', app_private.sync_every_min(),
        'unitLimit', null, -- o plano ainda não guarda limite de unidades
        'canManageUnits', v_manage,
        'canManageSources', app_private.is_source_admin(auth.uid()),
        'units', coalesce((
            select jsonb_agg(app_private.unit_sources_json(u.id) order by u.name)
            from app.units u
            where u.id = any (v_scope)
        ), '[]'::jsonb),
        'deletedUnits', case when v_manage then coalesce((
            select jsonb_agg(jsonb_build_object(
                       'code', u.code,
                       'name', u.name,
                       'deletedAt', u.deleted_at,
                       'purgeAt', u.deleted_at + interval '30 days',
                       'deletedBy', coalesce(m.full_name, au.email)
                   ) order by u.deleted_at desc)
            from app.units u
            left join app.memberships m on m.org_id = u.org_id and m.user_id = u.deleted_by
            left join auth.users au on au.id = u.deleted_by
            where u.org_id = v_org and not u.active and u.deleted_at is not null
              and u.deleted_at > now() - interval '30 days'
        ), '[]'::jsonb) else '[]'::jsonb end
    );
end;
$$;

create function api.restore_unit(p_org text, p_code text) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_org  uuid;
    v_unit app.units;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not app_private.can_manage_units(v_org) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor restauram unidades.';
    end if;

    select u.* into v_unit from app.units u
    where u.org_id = v_org and u.code = upper(trim(coalesce(p_code, ''))) and not u.active
      and u.deleted_at is not null
    for update;
    if v_unit.id is null then
        raise exception using errcode = 'P0001', message = 'Unidade excluída não encontrada.';
    end if;
    if v_unit.deleted_at <= now() - interval '30 days' then
        raise exception using errcode = 'P0001',
            message = format('O prazo de 30 dias para restaurar %s já passou.', v_unit.name);
    end if;

    update app.units
    set active = true, deleted_at = null, deleted_by = null, updated_at = now()
    where id = v_unit.id;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'unit.restored', 'unit', v_unit.id::text,
            jsonb_build_object('code', v_unit.code, 'name', v_unit.name, 'deletedAt', v_unit.deleted_at));

    return app_private.unit_sources_json(v_unit.id);
end;
$$;

revoke all on function api.restore_unit(text, text) from public, anon;
grant execute on function api.restore_unit(text, text) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.restore_unit(text, text);
-- (recriar api.list_sources com o corpo de 20261123150000_plataforma_unidades_auditoria.sql)
-- drop function app_private.can_manage_units(uuid);
-- =============================================================================
