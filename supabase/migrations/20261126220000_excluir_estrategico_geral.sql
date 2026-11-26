-- =============================================================================
-- Exclui o Estratégico Geral (dashboard da organização, scope 'org'), criado em 20261126190000_estrategico_geral.sql.
-- Ele só mostrava "Em construção"; os Estratégicos de cada unidade ('estrategico') não mudam.
--
--   * tira 'estrategico-geral' de tudo que aponta para app.dashboard_catalog (regras, favoritos, exceções, fontes,
--     unidades e ordem do hub) e do catálogo;
--   * app_private.dashboard_access_explain volta a ser a de 20261126110000_suporte_explica_acesso.sql (sem a etapa
--     "Dashboard da organização" e o motivo 'owner_dev_only'). app_private.dashboard_scope e dashboard_access usam
--     essa função e não mudam;
--   * api.log_dashboard_view volta a ser a de 20261119210000_auditoria_dashboards_abertos.sql (sem a unidade 'geral');
--   * a coluna app.dashboard_catalog.scope sai (só o Estratégico Geral usava 'org'). As funções acima são trocadas
--     antes, porque liam a coluna.
-- create or replace mantém os grants das duas funções. Linhas antigas de app.audit_log (unit 'GERAL') ficam: a
-- tabela é só inserção.
-- =============================================================================

-- 1. Dados do dashboard ----------------------------------------------------------------------------------

delete from app.access_rules            where dashboard_key = 'estrategico-geral';
delete from app.dashboard_favorites     where dashboard_key = 'estrategico-geral';
delete from app.member_dashboard_grants where dashboard_key = 'estrategico-geral';
delete from app.dashboard_sources       where dashboard_key = 'estrategico-geral';
delete from app.org_dashboards          where dashboard_key = 'estrategico-geral';
update app.hub_orders set keys = array_remove(keys, 'estrategico-geral') where 'estrategico-geral' = any (keys);
delete from app.dashboard_catalog       where key = 'estrategico-geral';

-- 2. Acesso: sem a etapa do dashboard da organização (= 20261126110000_suporte_explica_acesso.sql) --------

create or replace function app_private.dashboard_access_explain(p_user uuid, p_unit uuid, p_dashboard text)
returns table (scope text, via text, reason text)
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org        uuid;
    v_group      text;
    v_membership uuid;
    v_org_role   text;
    v_unit_role  text;
    v_scope      text;
begin
    -- organização e unidade ativas
    select u.org_id into v_org
    from app.units u
    join app.organizations o on o.id = u.org_id and o.active
    where u.id = p_unit and u.active;
    if v_org is null then
        return query select null::text, null::text, 'org_inactive'::text;
        return;
    end if;

    -- membro ativo da organização. Vem antes do "desligado" (as duas etapas só negam, então a regra não muda):
    -- assim um membro desativado aparece no suporte com um motivo só, em todos os dashboards.
    select m.id, m.role_key into v_membership, v_org_role
    from app.memberships m
    where m.org_id = v_org and m.user_id = p_user and m.status = 'active';
    if v_membership is null then
        return query select null::text, null::text, 'not_member'::text;
        return;
    end if;

    -- dashboard ativo e ligado na unidade (desligado: só para quem pode religar, o Desenvolvedor)
    select d.group_slug into v_group
    from app.org_dashboards od
    join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
    where od.org_id = v_org and od.unit_id = p_unit and od.dashboard_key = p_dashboard
      and (od.enabled or app_private.has_unit_permission(p_user, p_unit, 'dashboards.toggle'));
    if v_group is null then
        return query select null::text, null::text, 'dashboard_off'::text;
        return;
    end if;

    -- Desenvolvedor (admin) / owner: todas as companhias
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_org_role and rp.permission = 'org.dashboards.all') then
        return query select 'all'::text, 'role'::text, null::text;
        return;
    end if;

    -- cargo nesta companhia
    select mu.role_key into v_unit_role
    from app.membership_units mu
    where mu.unit_id = p_unit and mu.membership_id = v_membership;
    if v_unit_role is null then
        return query select null::text, null::text, 'no_unit_role'::text;
        return;
    end if;

    -- Gestor / Controller: tudo da companhia
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_unit_role and rp.permission = 'unit.dashboards.all') then
        return query select 'all'::text, 'role'::text, null::text;
        return;
    end if;

    -- Camadas 1 e 2: setores da pessoa nesta companhia (regra do card, grupo do setor, setor que vê tudo)
    select case
               when bool_or(x.s = 'all') then 'all'
               when count(*) > 0 then 'own'
           end
      into v_scope
    from (
        select r.scope as s
        from app.access_rules r
        join app.teams t             on t.id = r.team_id and t.active and t.unit_id = p_unit
        join app.membership_teams mt on mt.team_id = t.id and mt.membership_id = v_membership
        where r.dashboard_key = p_dashboard
        union all
        select 'all'
        from app.teams t
        join app.membership_teams mt on mt.team_id = t.id and mt.membership_id = v_membership
        where t.active and t.unit_id = p_unit
          and (t.sees_all
               or exists (select 1 from app.team_group_grants g
                          where g.team_id = t.id and g.group_slug = v_group))
    ) x;
    if v_scope is not null then
        return query select v_scope, 'sector'::text, null::text;
        return;
    end if;

    -- Camadas 3 e 4: exceções da pessoa nesta companhia (só visualização)
    if exists (select 1 from app.member_group_grants g
               where g.membership_id = v_membership and g.unit_id = p_unit and g.group_slug = v_group)
       or exists (select 1 from app.member_dashboard_grants g
                  where g.membership_id = v_membership and g.unit_id = p_unit and g.dashboard_key = p_dashboard) then
        return query select 'all'::text, 'personal'::text, null::text;
        return;
    end if;

    return query select null::text, null::text, 'no_sector_rule'::text;
end;
$$;

-- 3. Auditoria: sem a unidade 'geral' (= 20261119210000_auditoria_dashboards_abertos.sql) ----------------

create or replace function api.log_dashboard_view(p_org text, p_unit text, p_dashboard text) returns boolean
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org uuid;
    v_unit_id uuid;
    v_unit text;
    v_key text := trim(p_dashboard);
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids())) then
        raise exception using errcode = '42501', message = 'Você não é membro desta organização.';
    end if;

    select u.id, u.code into v_unit_id, v_unit from app.units u where u.org_id = v_org and u.code = upper(trim(p_unit));
    if v_unit is null or not exists (select 1 from app.dashboard_catalog c where c.key = v_key) then
        raise exception using errcode = '22023', message = 'Unidade ou dashboard desconhecido.';
    end if;

    if not exists (select 1 from app_private.dashboard_access(auth.uid(), v_unit_id, v_key)) then
        raise exception using errcode = '42501', message = 'Sem acesso a este dashboard nesta unidade.';
    end if;

    -- Duas chamadas ao mesmo tempo (duas abas, efeito duplo do React) não podem as duas passar pela checagem
    -- abaixo: a trava (até o fim da transação) põe uma atrás da outra, e a segunda já vê a linha da primeira.
    perform pg_advisory_xact_lock(hashtextextended('dashboard.view:' || auth.uid() || ':' || v_unit_id || ':' || v_key, 0));

    -- Repetição: mesma pessoa, dashboard e unidade nos últimos 5 minutos.
    if exists (
        select 1 from app.audit_log a
        where a.org_id = v_org
          and a.actor_user_id = auth.uid()
          and a.action = 'dashboard.view'
          and a.target_id = v_key
          and a.metadata ->> 'unit' = v_unit
          and a.created_at > now() - interval '5 minutes'
    ) then
        return false;
    end if;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'dashboard.view', 'dashboard', v_key,
            jsonb_build_object('org', lower(trim(p_org)), 'unit', v_unit));
    return true;
end;
$$;

-- 4. Escopo do dashboard ---------------------------------------------------------------------------------

alter table app.dashboard_catalog drop column scope;

-- =============================================================================
-- Rollback: reaplicar 20261126190000_estrategico_geral.sql (coluna scope, catálogo, unidades e as duas funções).
-- =============================================================================
