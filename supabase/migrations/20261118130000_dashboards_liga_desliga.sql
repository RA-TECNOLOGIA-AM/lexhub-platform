-- =============================================================================
-- Desenvolvedor liga/desliga um dashboard por unidade (app.org_dashboards.enabled).
--
-- Decisões (Luís, 18/11):
--   * por unidade: desliga, por exemplo, o Comercial só na LARJ;
--   * só o Desenvolvedor (papel 'admin'): permissão nova 'dashboards.toggle' (o Owner não ganha);
--   * desligado some do hub e da API para todos; o Desenvolvedor continua vendo o card marcado
--     "Desativado", abre o dashboard e religa pelo menu do card;
--   * vai para a auditoria (dashboard.enabled / dashboard.disabled).
-- O catálogo (apps/api/src/app/catalog.py) manda as unidades desligadas só para quem tem a permissão.
-- Teste: supabase/tests/dashboards_liga_desliga_test.sql (termina com rollback).
-- =============================================================================

insert into app.role_permissions (role_key, permission)
values ('admin', 'dashboards.toggle')
on conflict do nothing;

-- ---------------------------------------------------------------------------
-- Regra central: igual à de 20261105190000_cargo_por_unidade.sql; muda só a primeira consulta
-- (dashboard desligado na unidade continua valendo para quem pode religar).
-- ---------------------------------------------------------------------------
create or replace function app_private.dashboard_scope(p_user uuid, p_unit uuid, p_dashboard text) returns text
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org        uuid;
    v_membership uuid;
    v_org_role   text;
    v_unit_role  text;
    v_scope      text;
begin
    -- organização, companhia e dashboard ativos; dashboard ligado na companhia
    -- (desligado: só para quem pode religar, o Desenvolvedor)
    select u.org_id into v_org
    from app.units u
    join app.organizations o     on o.id = u.org_id and o.active
    join app.org_dashboards od   on od.org_id = u.org_id and od.unit_id = u.id
                                and od.dashboard_key = p_dashboard
                                and (od.enabled
                                     or app_private.has_unit_permission(p_user, u.id, 'dashboards.toggle'))
    join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
    where u.id = p_unit and u.active;
    if v_org is null then
        return null;
    end if;

    -- membro ativo da organização
    select m.id, m.role_key into v_membership, v_org_role
    from app.memberships m
    where m.org_id = v_org and m.user_id = p_user and m.status = 'active';
    if v_membership is null then
        return null;
    end if;

    -- Desenvolvedor (admin) / owner: todas as companhias
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_org_role and rp.permission = 'org.dashboards.all') then
        return 'all';
    end if;

    -- cargo nesta companhia
    select mu.role_key into v_unit_role
    from app.membership_units mu
    where mu.unit_id = p_unit and mu.membership_id = v_membership;
    if v_unit_role is null then
        return null;
    end if;

    -- Gestor / Controller: tudo da companhia
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_unit_role and rp.permission = 'unit.dashboards.all') then
        return 'all';
    end if;

    -- Colaborador / Leitor: regras dos seus setores nesta companhia
    select case
               when bool_or(r.scope = 'all') then 'all'
               when count(*) > 0 then 'own'
           end
      into v_scope
    from app.access_rules r
    join app.teams t             on t.id = r.team_id and t.active and t.unit_id = p_unit
    join app.membership_teams mt on mt.team_id = r.team_id and mt.membership_id = v_membership
    where r.dashboard_key = p_dashboard;

    return v_scope;
end;
$$;

-- ---------------------------------------------------------------------------
-- Ligar/desligar (a API chama com o usuário do token). Devolve o estado final.
-- ---------------------------------------------------------------------------
create function app_private.set_dashboard_enabled(
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
        raise exception using errcode = '42501', message = 'Só o Desenvolvedor liga e desliga dashboards.';
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

revoke all on function app_private.set_dashboard_enabled(uuid, text, text, text, boolean)
    from public, anon, authenticated;
grant execute on function app_private.set_dashboard_enabled(uuid, text, text, text, boolean) to service_role;

-- =============================================================================
-- Rollback:
-- drop function app_private.set_dashboard_enabled(uuid, text, text, text, boolean);
-- (recriar app_private.dashboard_scope como em 20261105190000_cargo_por_unidade.sql)
-- delete from app.role_permissions where permission = 'dashboards.toggle';
-- =============================================================================
