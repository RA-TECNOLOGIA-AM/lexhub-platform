-- =============================================================================
-- O Owner também liga/desliga dashboard por unidade (antes só o Desenvolvedor).
--
-- Decisão (Luís, 26/11): o Owner ganha 'dashboards.toggle'. Com isso ele também vê o card
-- "Desativado", abre o dashboard desligado e religa (dashboard_scope e o catálogo já olham a permissão).
-- Muda também a mensagem de recusa de app_private.set_dashboard_enabled.
-- Teste: supabase/tests/dashboards_liga_desliga_test.sql (termina com rollback).
-- =============================================================================

insert into app.role_permissions (role_key, permission)
values ('owner', 'dashboards.toggle')
on conflict do nothing;

create or replace function app_private.set_dashboard_enabled(
    p_user uuid, p_org text, p_unit text, p_dashboard text, p_enabled boolean
) returns boolean
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_unit app.units;
    v_od   app.org_dashboards;
begin
    if p_enabled is null then
        raise exception using errcode = 'P0001', message = 'Informe se o dashboard fica ligado ou desligado.';
    end if;

    select u.* into v_unit
    from app.units u
    join app.organizations o on o.id = u.org_id and o.active
    where o.slug = p_org and u.code = p_unit and u.active;
    if v_unit.id is null or not app_private.has_unit_permission(p_user, v_unit.id, 'dashboards.toggle') then
        raise exception using errcode = '42501', message = 'Só o Owner ou o Desenvolvedor liga e desliga dashboards.';
    end if;

    select od.* into v_od
    from app.org_dashboards od
    join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
    where od.unit_id = v_unit.id and od.dashboard_key = p_dashboard
    for update of od;
    if v_od.id is null then
        raise exception using errcode = 'P0001', message = 'Este dashboard não existe nesta unidade.';
    end if;

    if v_od.enabled is distinct from p_enabled then
        update app.org_dashboards set enabled = p_enabled, updated_at = now() where id = v_od.id;

        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_unit.org_id, p_user,
                case when p_enabled then 'dashboard.enabled' else 'dashboard.disabled' end,
                'dashboard', p_dashboard,
                jsonb_build_object('unit', v_unit.code, 'from', v_od.enabled, 'to', p_enabled));
    end if;
    return p_enabled;
end;
$$;

-- =============================================================================
-- Rollback:
-- delete from app.role_permissions where role_key = 'owner' and permission = 'dashboards.toggle';
-- (recriar app_private.set_dashboard_enabled como em 20261118130000_dashboards_liga_desliga.sql)
-- =============================================================================
