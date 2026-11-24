-- =============================================================================
-- Modo suporte "ver como", parte final: por que um dashboard está oculto para o membro.
--
-- app_private.dashboard_access_explain passa a ser a ÚNICA implementação da regra de acesso a um
-- dashboard numa unidade. Ela devolve sempre uma linha:
--   visível: scope ('all' | 'own') e via ('role' | 'sector' | 'personal'), reason nulo;
--   oculto:  scope e via nulos, reason = onde a regra parou:
--     org_inactive    organização (ou unidade) inativa
--     dashboard_off   dashboard fora do catálogo ou desligado na unidade (e a pessoa não pode religar)
--     not_member      sem membership ativa na organização (desativado ou de fora)
--     no_unit_role    sem cargo nesta unidade
--     no_sector_rule  nenhum setor dela tem o dashboard, e não há exceção
-- app_private.dashboard_access vira um invólucro dela (mesma assinatura e resultado de antes: zero linhas
-- quando nega), então a explicação mostrada no suporte nunca diverge do que a pessoa vê de fato.
-- Etapas conferidas contra 20261119170000_grupos_acesso.sql (definição vigente; nada depois mexe nela).
-- A única diferença de ordem: 'membro ativo' vem antes de 'desligado' — as duas só negam, a regra não muda.
-- Usada pela API (GET /orgs/{org}/support/sessions/{id}/hidden), via service_role.
-- =============================================================================

create function app_private.dashboard_access_explain(p_user uuid, p_unit uuid, p_dashboard text)
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

create or replace function app_private.dashboard_access(p_user uuid, p_unit uuid, p_dashboard text)
returns table (scope text, via text)
language sql stable security definer
set search_path = ''
as $$
    select e.scope, e.via
    from app_private.dashboard_access_explain(p_user, p_unit, p_dashboard) e
    where e.scope is not null;
$$;

revoke all on function app_private.dashboard_access_explain(uuid, uuid, text) from public, anon, authenticated;
revoke all on function app_private.dashboard_access(uuid, uuid, text)         from public, anon, authenticated;
grant execute on function app_private.dashboard_access_explain(uuid, uuid, text) to service_role;
grant execute on function app_private.dashboard_access(uuid, uuid, text)         to service_role;

-- Desfazer: recriar app_private.dashboard_access com o corpo de 20261119170000_grupos_acesso.sql e
-- drop function app_private.dashboard_access_explain(uuid, uuid, text);
