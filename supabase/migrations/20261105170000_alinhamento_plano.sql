-- =============================================================================
-- Alinha o schema "app" ao modelo do plano (plano-saas-multitenant.md), escopo MVP.
--
--   members / unit_members / team_members -> memberships / membership_units / membership_teams
--   papéis fixos (enum)                    -> app.roles + app.role_permissions
--                                             owner, admin, gestor, colaborador, leitor
--   dashboard_grants (equipe ou membro)    -> app.access_rules (equipe x dashboard, escopo all | own)
--   dashboards / unit_dashboards           -> app.dashboard_catalog / app.org_dashboards
--   novo: app.invitations (entrada por convite), units.timezone
--   funções auxiliares                     -> schema app_private (não exposto)
--   policies no formato  org_id = any((select app_private.my_org_ids()))
--
-- Converte os dados que já existem (staging): Desenvolvedor/admin -> admin,
-- manager de unidade -> gestor, demais -> colaborador; liberações por equipe -> access_rules.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Policies antigas (dependem das funções e colunas que vão mudar)
-- ---------------------------------------------------------------------------
drop policy org_select              on app.organizations;
drop policy units_select            on app.units;
drop policy teams_select            on app.teams;
drop policy members_select          on app.members;
drop policy unit_members_select     on app.unit_members;
drop policy team_members_select     on app.team_members;
drop policy dashboards_select       on app.dashboards;
drop policy unit_dashboards_select  on app.unit_dashboards;
drop policy dashboard_grants_select on app.dashboard_grants;
drop policy audit_log_select        on app.audit_log;

drop function app.my_dashboards();
drop function app.can_view_dashboard(uuid, text);
drop function app.user_can_view_dashboard(uuid, uuid, text);
drop function app.is_org_admin(uuid);
drop function app.is_org_member(uuid);

-- ---------------------------------------------------------------------------
-- 1. Schema das funções auxiliares
-- ---------------------------------------------------------------------------
create schema app_private;
revoke all on schema app_private from public;
grant usage on schema app_private to authenticated, service_role;

-- ---------------------------------------------------------------------------
-- 2. Papéis e permissões
-- ---------------------------------------------------------------------------
create table app.roles (
    key         text primary key check (key ~ '^[a-z][a-z_]{1,31}$'),
    name        text not null,
    description text,
    is_system   boolean not null default true,
    sort_order  int not null default 0
);

create table app.role_permissions (
    role_key   text not null references app.roles (key) on update cascade on delete cascade,
    permission text not null check (permission ~ '^[a-z]+(\.[a-z_]+)+$'),
    primary key (role_key, permission)
);

insert into app.roles (key, name, description, sort_order) values
    ('owner',       'Proprietário',  'Dono da organização: tudo, inclusive cobrança',            1),
    ('admin',       'Administrador', 'Gerencia membros e acessos; vê todos os dashboards',        2),
    ('gestor',      'Gestor',        'Vê todos os dashboards das suas unidades',                  3),
    ('colaborador', 'Colaborador',   'Vê os dashboards liberados para a sua equipe; exporta',     4),
    ('leitor',      'Leitor',        'Vê os dashboards liberados para a sua equipe; não exporta', 5);

-- org.dashboards.all  : vê todos os dashboards de todas as unidades
-- unit.dashboards.all : vê todos os dashboards das unidades em que está
insert into app.role_permissions (role_key, permission) values
    ('owner', 'org.dashboards.all'),
    ('owner', 'dashboards.export'),
    ('owner', 'members.manage'),
    ('owner', 'access.manage'),
    ('owner', 'audit.view'),
    ('owner', 'billing.manage'),
    ('admin', 'org.dashboards.all'),
    ('admin', 'dashboards.export'),
    ('admin', 'members.manage'),
    ('admin', 'access.manage'),
    ('admin', 'audit.view'),
    ('gestor', 'unit.dashboards.all'),
    ('gestor', 'dashboards.export'),
    ('colaborador', 'dashboards.export');

-- ---------------------------------------------------------------------------
-- 3. Unidades: fuso horário
-- ---------------------------------------------------------------------------
alter table app.units
    add column timezone text not null default 'America/Manaus'
        check (timezone ~ '^[A-Za-z_]+(/[A-Za-z0-9_+-]+)+$');

-- ---------------------------------------------------------------------------
-- 4. Catálogo de dashboards
-- ---------------------------------------------------------------------------
alter table app.dashboards rename to dashboard_catalog;
alter table app.dashboard_catalog
    add column level text not null default 'unit' check (level in ('unit', 'org'));

-- ---------------------------------------------------------------------------
-- 5. Regras de acesso (substituem dashboard_grants)
-- ---------------------------------------------------------------------------
create table app.access_rules (
    id            uuid primary key default gen_random_uuid(),
    org_id        uuid not null,
    team_id       uuid not null,
    dashboard_key text not null references app.dashboard_catalog (key) on update cascade on delete cascade,
    scope         text not null default 'all' check (scope in ('all', 'own')),
    created_by    uuid references auth.users (id) on delete set null,
    created_at    timestamptz not null default now(),
    unique (team_id, dashboard_key),
    foreign key (org_id, team_id) references app.teams (org_id, id) on delete cascade
);
comment on column app.access_rules.scope is 'all = todos os registros da unidade; own = só os registros do próprio usuário';

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by, created_at)
select g.org_id, g.team_id, g.dashboard_key, 'all', g.created_by, g.created_at
from app.dashboard_grants g
where g.team_id is not null
on conflict (team_id, dashboard_key) do nothing;

do $$
declare
    n int;
begin
    select count(*) into n from app.dashboard_grants where member_id is not null;
    if n > 0 then
        raise notice 'Atenção: % liberação(ões) individuais (por membro) não existem no modelo novo e foram descartadas', n;
    end if;
end $$;

drop table app.dashboard_grants;

-- ---------------------------------------------------------------------------
-- 6. Dashboards por organização/unidade (unit_id nulo = dashboard de nível organização)
-- ---------------------------------------------------------------------------
alter table app.unit_dashboards rename to org_dashboards;
alter table app.org_dashboards drop constraint unit_dashboards_pkey;
alter table app.org_dashboards add column id uuid not null default gen_random_uuid();
alter table app.org_dashboards add primary key (id);
alter table app.org_dashboards alter column unit_id drop not null;
alter table app.org_dashboards
    add constraint org_dashboards_org_unit_key_uq unique nulls not distinct (org_id, unit_id, dashboard_key);
alter table app.org_dashboards
    drop constraint unit_dashboards_dashboard_key_fkey,
    add constraint org_dashboards_dashboard_key_fkey
        foreign key (dashboard_key) references app.dashboard_catalog (key)
        on update cascade on delete cascade;

-- ---------------------------------------------------------------------------
-- 7. Associações (memberships)
-- ---------------------------------------------------------------------------
alter table app.members rename to memberships;
alter table app.memberships
    add column role_key text references app.roles (key) on update cascade;

update app.memberships m
set role_key = case
    when m.role::text in ('owner', 'admin') then m.role::text
    when exists (
        select 1 from app.unit_members um
        where um.member_id = m.id and um.role = 'manager'
    ) then 'gestor'
    else 'colaborador'
end;

alter table app.memberships alter column role_key set not null;
alter table app.memberships alter column role_key set default 'colaborador';
alter table app.memberships drop column role;

alter table app.unit_members rename to membership_units;
alter table app.membership_units rename column member_id to membership_id;
alter table app.membership_units drop column role;

alter table app.team_members rename to membership_teams;
alter table app.membership_teams rename column member_id to membership_id;

drop type app.org_role;
drop type app.unit_role;

-- ---------------------------------------------------------------------------
-- 8. Convites
-- ---------------------------------------------------------------------------
create table app.invitations (
    id          uuid primary key default gen_random_uuid(),
    org_id      uuid not null references app.organizations (id) on delete cascade,
    email       text not null check (email = lower(email) and position('@' in email) > 1),
    role_key    text not null default 'colaborador' references app.roles (key) on update cascade,
    unit_ids    uuid[] not null default '{}',
    team_ids    uuid[] not null default '{}',
    token_hash  text not null unique,
    invited_by  uuid references auth.users (id) on delete set null,
    expires_at  timestamptz not null default now() + interval '7 days',
    accepted_at timestamptz,
    revoked_at  timestamptz,
    created_at  timestamptz not null default now(),
    check (expires_at > created_at)
);
create unique index invitations_pending_uq
    on app.invitations (org_id, email)
    where accepted_at is null and revoked_at is null;

-- ---------------------------------------------------------------------------
-- 9. Funções auxiliares (app_private)
-- ---------------------------------------------------------------------------
-- Organizações em que o usuário logado é membro ativo
create function app_private.my_org_ids() returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(m.org_id), '{}')
    from app.memberships m
    join app.organizations o on o.id = m.org_id and o.active
    where m.user_id = auth.uid()
      and m.status = 'active';
$$;

-- Organizações em que o usuário logado tem uma permissão (ex.: members.manage)
create function app_private.my_org_ids_with(p_permission text) returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(m.org_id), '{}')
    from app.memberships m
    join app.organizations o on o.id = m.org_id and o.active
    join app.role_permissions rp on rp.role_key = m.role_key and rp.permission = p_permission
    where m.user_id = auth.uid()
      and m.status = 'active';
$$;

-- Permissão de um usuário numa organização (uso da API)
create function app_private.has_permission(p_user uuid, p_org uuid, p_permission text) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select exists (
        select 1
        from app.memberships m
        join app.organizations o on o.id = m.org_id and o.active
        join app.role_permissions rp on rp.role_key = m.role_key and rp.permission = p_permission
        where m.org_id = p_org
          and m.user_id = p_user
          and m.status = 'active'
    );
$$;

-- Regra central: escopo de um usuário num dashboard de uma unidade.
-- Retorna 'all', 'own' ou NULL (sem acesso). Nega quando nada casa.
create function app_private.dashboard_scope(p_user uuid, p_unit uuid, p_dashboard text) returns text
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org        uuid;
    v_membership uuid;
    v_role       text;
    v_scope      text;
begin
    -- organização, unidade e dashboard ativos; dashboard ligado na unidade
    select u.org_id into v_org
    from app.units u
    join app.organizations o      on o.id = u.org_id and o.active
    join app.org_dashboards od    on od.org_id = u.org_id and od.unit_id = u.id
                                 and od.dashboard_key = p_dashboard and od.enabled
    join app.dashboard_catalog d  on d.key = od.dashboard_key and d.active
    where u.id = p_unit and u.active;
    if v_org is null then
        return null;
    end if;

    -- membro ativo da organização
    select m.id, m.role_key into v_membership, v_role
    from app.memberships m
    where m.org_id = v_org and m.user_id = p_user and m.status = 'active';
    if v_membership is null then
        return null;
    end if;

    -- owner / admin: tudo da organização
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_role and rp.permission = 'org.dashboards.all') then
        return 'all';
    end if;

    -- daqui para baixo, só quem está na unidade
    if not exists (select 1 from app.membership_units mu
                   where mu.unit_id = p_unit and mu.membership_id = v_membership) then
        return null;
    end if;

    -- gestor: tudo das suas unidades
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_role and rp.permission = 'unit.dashboards.all') then
        return 'all';
    end if;

    -- colaborador / leitor: regras das suas equipes nesta unidade
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

-- Versões para o usuário logado (sempre auth.uid())
create function app.dashboard_scope(p_unit uuid, p_dashboard text) returns text
language sql stable security definer
set search_path = ''
as $$
    select app_private.dashboard_scope(auth.uid(), p_unit, p_dashboard);
$$;

create function app.can_view_dashboard(p_unit uuid, p_dashboard text) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select app_private.dashboard_scope(auth.uid(), p_unit, p_dashboard) is not null;
$$;

-- Hub: dashboards que o usuário logado pode abrir, com o escopo
create function app.my_dashboards()
returns table (org_id uuid, unit_id uuid, unit_code text, dashboard_key text, dashboard_name text, scope text)
language sql stable security definer
set search_path = ''
as $$
    select x.org_id, x.unit_id, x.unit_code, x.dashboard_key, x.dashboard_name, x.scope
    from (
        select u.org_id, u.id as unit_id, u.code as unit_code, d.key as dashboard_key, d.name as dashboard_name,
               app_private.dashboard_scope(auth.uid(), u.id, d.key) as scope
        from app.org_dashboards od
        join app.units u             on u.id = od.unit_id
        join app.dashboard_catalog d on d.key = od.dashboard_key
        where u.org_id = any (app_private.my_org_ids())
    ) x
    where x.scope is not null
    order by x.unit_code, x.dashboard_name;
$$;

-- ---------------------------------------------------------------------------
-- 10. RLS (formato do plano: (select ...) calculado uma vez por consulta)
-- ---------------------------------------------------------------------------
alter table app.roles            enable row level security;
alter table app.role_permissions enable row level security;
alter table app.access_rules     enable row level security;
alter table app.invitations      enable row level security;

create policy organizations_select on app.organizations for select to authenticated
    using (id = any ((select app_private.my_org_ids())::uuid[]));

create policy units_select on app.units for select to authenticated
    using (org_id = any ((select app_private.my_org_ids())::uuid[]));

create policy teams_select on app.teams for select to authenticated
    using (org_id = any ((select app_private.my_org_ids())::uuid[]));

create policy org_dashboards_select on app.org_dashboards for select to authenticated
    using (org_id = any ((select app_private.my_org_ids())::uuid[]));

-- cada um vê a própria associação; quem gerencia membros vê todas da organização
create policy memberships_select on app.memberships for select to authenticated
    using (
        user_id = (select auth.uid())
        or org_id = any ((select app_private.my_org_ids_with('members.manage'))::uuid[])
    );

create policy membership_units_select on app.membership_units for select to authenticated
    using (
        membership_id in (select id from app.memberships where user_id = (select auth.uid()))
        or org_id = any ((select app_private.my_org_ids_with('members.manage'))::uuid[])
    );

create policy membership_teams_select on app.membership_teams for select to authenticated
    using (
        membership_id in (select id from app.memberships where user_id = (select auth.uid()))
        or org_id = any ((select app_private.my_org_ids_with('members.manage'))::uuid[])
    );

create policy access_rules_select on app.access_rules for select to authenticated
    using (org_id = any ((select app_private.my_org_ids_with('access.manage'))::uuid[]));

create policy invitations_select on app.invitations for select to authenticated
    using (org_id = any ((select app_private.my_org_ids_with('members.manage'))::uuid[]));

create policy audit_log_select on app.audit_log for select to authenticated
    using (org_id = any ((select app_private.my_org_ids_with('audit.view'))::uuid[]));

create policy dashboard_catalog_select on app.dashboard_catalog for select to authenticated
    using (active);

create policy roles_select on app.roles for select to authenticated
    using (true);

create policy role_permissions_select on app.role_permissions for select to authenticated
    using (true);

-- ---------------------------------------------------------------------------
-- 11. Permissões
-- ---------------------------------------------------------------------------
revoke all on all tables    in schema app         from public, anon;
revoke all on all functions in schema app         from public, anon;
revoke all on all functions in schema app_private from public, anon;

grant select on all tables in schema app to authenticated;
grant all    on all tables in schema app to service_role;
grant usage, select on all sequences in schema app to service_role;

-- auxiliares usados nas policies: precisam de execute para authenticated
grant execute on function app_private.my_org_ids()          to authenticated, service_role;
grant execute on function app_private.my_org_ids_with(text) to authenticated, service_role;
-- consultam qualquer usuário: só a API
grant execute on function app_private.has_permission(uuid, uuid, text)  to service_role;
grant execute on function app_private.dashboard_scope(uuid, uuid, text) to service_role;
-- versões do usuário logado
grant execute on function app.dashboard_scope(uuid, text)    to authenticated, service_role;
grant execute on function app.can_view_dashboard(uuid, text) to authenticated, service_role;
grant execute on function app.my_dashboards()                to authenticated, service_role;
