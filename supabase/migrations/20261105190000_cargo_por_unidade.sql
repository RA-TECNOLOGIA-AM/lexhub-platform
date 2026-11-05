-- =============================================================================
-- Cargo por companhia (unidade)
--
-- Regra de negócio (05/11/2026):
--   * Cada companhia (unidade) é independente; o usuário vê uma companhia por vez.
--   * Desenvolvedor (papel "admin" da organização) acessa todas as companhias.
--   * Os demais cargos são POR COMPANHIA: a mesma pessoa pode ser Controller na NG
--     e Leitor na LA. Pode estar em mais de um setor (equipe) em cada companhia.
--   * Quem atribui cargos/setores numa companhia: Controller, Gestor ou Desenvolvedor dela.
--
-- Modelo:
--   app.roles.level            'org'  -> owner, admin (Desenvolvedor), member (sem papel global)
--                              'unit' -> gestor, controller, colaborador, leitor
--   app.memberships.role_key   só papéis de nível org
--   app.membership_units.role_key  papel naquela companhia
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Nível dos papéis + novos papéis
-- ---------------------------------------------------------------------------
alter table app.roles
    add column level text not null default 'unit' check (level in ('org', 'unit'));
update app.roles set level = 'org' where key in ('owner', 'admin');

insert into app.roles (key, name, description, level, sort_order) values
    ('member',     'Membro',     'Sem papel na organização inteira; o acesso vem do cargo em cada companhia', 'org',  3),
    ('controller', 'Controller', 'Vê tudo da companhia, exporta e atribui cargos/setores nela',               'unit', 5);

update app.roles set sort_order = 1 where key = 'owner';
update app.roles set sort_order = 2 where key = 'admin';
update app.roles set sort_order = 4, description = 'Vê tudo da companhia, exporta e atribui cargos/setores nela' where key = 'gestor';
update app.roles set sort_order = 6 where key = 'colaborador';
update app.roles set sort_order = 7, description = 'Vê o que o setor libera; somente leitura (não exporta)' where key = 'leitor';
update app.roles set name = 'Desenvolvedor', description = 'Acesso a todas as companhias da organização; gerencia membros e acessos' where key = 'admin';

alter table app.roles add constraint roles_key_level_uq unique (key, level);

-- permissões de nível companhia
insert into app.role_permissions (role_key, permission) values
    ('owner',      'unit.members.manage'),
    ('owner',      'unit.access.manage'),
    ('admin',      'unit.members.manage'),
    ('admin',      'unit.access.manage'),
    ('gestor',     'unit.members.manage'),
    ('gestor',     'unit.access.manage'),
    ('controller', 'unit.dashboards.all'),
    ('controller', 'dashboards.export'),
    ('controller', 'unit.members.manage'),
    ('controller', 'unit.access.manage')
on conflict do nothing;

-- ---------------------------------------------------------------------------
-- 2. Cargo em cada companhia
-- ---------------------------------------------------------------------------
alter table app.membership_units add column role_key text;

update app.membership_units mu
set role_key = case
    when m.role_key in ('gestor', 'colaborador', 'leitor') then m.role_key
    else 'colaborador'
end
from app.memberships m
where m.id = mu.membership_id;

alter table app.membership_units alter column role_key set not null;
alter table app.membership_units alter column role_key set default 'leitor';
alter table app.membership_units
    add column role_level text not null generated always as ('unit') stored;
alter table app.membership_units
    add constraint membership_units_role_fkey
        foreign key (role_key, role_level) references app.roles (key, level);

-- ---------------------------------------------------------------------------
-- 3. Papel na organização: só owner / admin / member
-- ---------------------------------------------------------------------------
update app.memberships set role_key = 'member' where role_key not in ('owner', 'admin');

alter table app.memberships drop constraint memberships_role_key_fkey;
alter table app.memberships alter column role_key set default 'member';
alter table app.memberships
    add column role_level text not null generated always as ('org') stored;
alter table app.memberships
    add constraint memberships_role_fkey
        foreign key (role_key, role_level) references app.roles (key, level);

comment on column app.invitations.role_key is
    'Papel do convidado: de nível org (admin) vale na organização; de nível unit vale nas companhias de unit_ids';

-- ---------------------------------------------------------------------------
-- 4. Funções auxiliares
-- ---------------------------------------------------------------------------
-- Permissão numa companhia: vem do papel na organização OU do cargo naquela companhia
create function app_private.has_unit_permission(p_user uuid, p_unit uuid, p_permission text) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select exists (
        select 1
        from app.units u
        join app.organizations o on o.id = u.org_id and o.active
        join app.memberships m   on m.org_id = u.org_id and m.user_id = p_user and m.status = 'active'
        where u.id = p_unit
          and u.active
          and (
              exists (select 1 from app.role_permissions rp
                      where rp.role_key = m.role_key and rp.permission = p_permission)
              or exists (select 1
                         from app.membership_units mu
                         join app.role_permissions rp on rp.role_key = mu.role_key and rp.permission = p_permission
                         where mu.membership_id = m.id and mu.unit_id = u.id)
          )
    );
$$;

-- Companhias em que o usuário logado tem uma permissão
create function app_private.my_unit_ids_with(p_permission text) returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(distinct u.id), '{}')
    from app.memberships m
    join app.organizations o on o.id = m.org_id and o.active
    join app.units u         on u.org_id = m.org_id
    where m.user_id = auth.uid()
      and m.status = 'active'
      and (
          exists (select 1 from app.role_permissions rp
                  where rp.role_key = m.role_key and rp.permission = p_permission)
          or exists (select 1
                     from app.membership_units mu
                     join app.role_permissions rp on rp.role_key = mu.role_key and rp.permission = p_permission
                     where mu.membership_id = m.id and mu.unit_id = u.id)
      );
$$;

-- Associações que o usuário logado pode ver/gerenciar (admin: toda a org; gestor/controller: as da sua companhia)
create function app_private.my_managed_membership_ids() returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(distinct x.id), '{}')
    from (
        select m2.id
        from app.memberships m2
        where m2.org_id = any (app_private.my_org_ids_with('members.manage'))
        union
        select mu.membership_id
        from app.membership_units mu
        where mu.unit_id = any (app_private.my_unit_ids_with('unit.members.manage'))
    ) x;
$$;

-- Regra central (substitui a versão anterior)
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
    select u.org_id into v_org
    from app.units u
    join app.organizations o     on o.id = u.org_id and o.active
    join app.org_dashboards od   on od.org_id = u.org_id and od.unit_id = u.id
                                and od.dashboard_key = p_dashboard and od.enabled
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
-- 5. RLS: gestor/controller enxergam a gestão da SUA companhia
-- ---------------------------------------------------------------------------
drop policy memberships_select       on app.memberships;
drop policy membership_units_select  on app.membership_units;
drop policy membership_teams_select  on app.membership_teams;
drop policy access_rules_select      on app.access_rules;
drop policy invitations_select       on app.invitations;

create policy memberships_select on app.memberships for select to authenticated
    using (
        user_id = (select auth.uid())
        or id = any ((select app_private.my_managed_membership_ids())::uuid[])
    );

create policy membership_units_select on app.membership_units for select to authenticated
    using (
        membership_id in (select id from app.memberships where user_id = (select auth.uid()))
        or unit_id = any ((select app_private.my_unit_ids_with('unit.members.manage'))::uuid[])
    );

create policy membership_teams_select on app.membership_teams for select to authenticated
    using (
        membership_id in (select id from app.memberships where user_id = (select auth.uid()))
        or team_id in (
            select t.id from app.teams t
            where t.unit_id = any ((select app_private.my_unit_ids_with('unit.members.manage'))::uuid[])
        )
    );

create policy access_rules_select on app.access_rules for select to authenticated
    using (
        team_id in (
            select t.id from app.teams t
            where t.unit_id = any ((select app_private.my_unit_ids_with('unit.access.manage'))::uuid[])
        )
    );

create policy invitations_select on app.invitations for select to authenticated
    using (
        org_id = any ((select app_private.my_org_ids_with('members.manage'))::uuid[])
        or unit_ids && (select app_private.my_unit_ids_with('unit.members.manage'))::uuid[]
    );

-- ---------------------------------------------------------------------------
-- 6. Permissões
-- ---------------------------------------------------------------------------
revoke all on function app_private.has_unit_permission(uuid, uuid, text) from public, anon;
revoke all on function app_private.my_unit_ids_with(text)                from public, anon;
revoke all on function app_private.my_managed_membership_ids()           from public, anon;

grant execute on function app_private.my_unit_ids_with(text)               to authenticated, service_role;
grant execute on function app_private.my_managed_membership_ids()          to authenticated, service_role;
grant execute on function app_private.has_unit_permission(uuid, uuid, text) to service_role;
