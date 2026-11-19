-- =============================================================================
-- Grupos de acesso e dashboards avulsos (spec: docs/superpowers/specs/2026-11-19-grupos-acesso-design.md)
--
-- Acesso de um Colaborador/Leitor a um dashboard numa unidade = UNIÃO de 4 camadas (só libera, nunca nega):
--   1. Dashboards do setor     app.access_rules (já existia)        -> vê e exporta (se o cargo exporta)
--   2. Grupos do setor         app.team_group_grants (novo)         -> vê e exporta (se o cargo exporta)
--      + setor que vê tudo     app.teams.sees_all (novo; Diretoria) -> vê e exporta (se o cargo exporta)
--   3. Grupos extras da pessoa app.member_group_grants (novo)       -> só vê
--   4. Avulsos da pessoa       app.member_dashboard_grants (novo)   -> só vê
-- Tudo por unidade: precisa de cargo na unidade e do dashboard ligado nela, como antes.
-- Owner/Desenvolvedor e Gestor/Controller não mudam: veem e exportam tudo pelo cargo.
--
-- Grupo = coluna do hub, por slug fixo (app.hub_groups). dashboard_catalog.area continua sendo o rótulo.
--
-- Funções:
--   app_private.dashboard_access      nova: (scope, via) — via 'role' | 'sector' | 'personal'
--   app_private.dashboard_scope       mesma assinatura; agora lê dashboard_access
--   app_private.dashboard_can_export  nova: cargo exporta E o acesso vem do cargo ou do setor
--   app_private.member_json           + extra_groups, extra_dashboards
--   api.access_overview               + groups, teams[].sees_all/groups; grade conta grupo e sees_all
--   api.update_member_access          + p_extra_groups, p_extra_dashboards (null = não muda)
--   api.set_team_groups               nova: grupos de um setor (+ sees_all, só Owner/Desenvolvedor)
--
-- Carga (LexGroup): Diretoria vê tudo; Controladoria -> grupo juridico; Publicações, Emendas e
-- Manifestações, Réplicas e Acompanhamento Processual -> cards do Jurídico sem Execução (camada 1).
-- Teste: supabase/tests/grupos_acesso_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Grupos (colunas do hub) com slug fixo
-- ---------------------------------------------------------------------------
create table app.hub_groups (
    slug       text primary key check (slug ~ '^[a-z_]+$'),
    name       text not null unique,
    sort_order integer not null
);
comment on table app.hub_groups is 'Colunas do hub. Permissão usa o slug (fixo); name é o rótulo e pode mudar.';

insert into app.hub_groups (slug, name, sort_order) values
    ('comercial',     'Comercial',     10),
    ('pre_protocolo', 'Pré-protocolo', 20),
    ('tecnologia',    'Tecnologia',    30),
    ('juridico',      'Jurídico',      40),
    ('financeiro',    'Financeiro',    50),
    ('estrategico',   'Estratégico',   60);

alter table app.dashboard_catalog
    add column group_slug text references app.hub_groups (slug) on update cascade;
update app.dashboard_catalog d set group_slug = g.slug from app.hub_groups g where g.name = d.area;

-- Card novo sem group_slug: herda da área (as migrations de card já escrevem area = 'Jurídico'...).
-- Área que não é coluna do hub bate no not null: todo card precisa de grupo.
create function app_private.catalog_group_from_area() returns trigger
language plpgsql
set search_path = ''
as $$
begin
    if new.group_slug is null then
        select g.slug into new.group_slug from app.hub_groups g where g.name = new.area;
    end if;
    return new;
end;
$$;
create trigger catalog_group_from_area
    before insert or update of area, group_slug on app.dashboard_catalog
    for each row execute function app_private.catalog_group_from_area();

alter table app.dashboard_catalog alter column group_slug set not null;

-- ---------------------------------------------------------------------------
-- 2. Camadas novas
-- ---------------------------------------------------------------------------
alter table app.teams add column sees_all boolean not null default false;
comment on column app.teams.sees_all is 'Setor vê (e, se o cargo exporta, exporta) todos os dashboards da unidade. Ex.: Diretoria.';

create table app.team_group_grants (
    org_id     uuid not null,
    team_id    uuid not null,
    group_slug text not null references app.hub_groups (slug) on update cascade,
    created_by uuid references auth.users (id) on delete set null,
    created_at timestamptz not null default now(),
    primary key (team_id, group_slug),
    foreign key (org_id, team_id) references app.teams (org_id, id) on delete cascade
);

create table app.member_group_grants (
    membership_id uuid not null references app.memberships (id) on delete cascade,
    unit_id       uuid not null references app.units (id) on delete cascade,
    group_slug    text not null references app.hub_groups (slug) on update cascade,
    created_by    uuid references auth.users (id) on delete set null,
    created_at    timestamptz not null default now(),
    primary key (membership_id, unit_id, group_slug)
);

create table app.member_dashboard_grants (
    membership_id uuid not null references app.memberships (id) on delete cascade,
    unit_id       uuid not null references app.units (id) on delete cascade,
    dashboard_key text not null references app.dashboard_catalog (key) on update cascade on delete cascade,
    created_by    uuid references auth.users (id) on delete set null,
    created_at    timestamptz not null default now(),
    primary key (membership_id, unit_id, dashboard_key)
);

-- Só as funções SECURITY DEFINER leem e escrevem (RLS ligada, sem policy), como access_rules.
alter table app.hub_groups              enable row level security;
alter table app.team_group_grants       enable row level security;
alter table app.member_group_grants     enable row level security;
alter table app.member_dashboard_grants enable row level security;
revoke all on app.team_group_grants, app.member_group_grants, app.member_dashboard_grants from anon, authenticated;
grant select on app.hub_groups to authenticated;
create policy hub_groups_read on app.hub_groups for select to authenticated using (true);
grant all on app.hub_groups, app.team_group_grants, app.member_group_grants, app.member_dashboard_grants to service_role;

-- ---------------------------------------------------------------------------
-- 3. A regra: de onde vem o acesso
-- ---------------------------------------------------------------------------
-- Sem linha = sem acesso. A primeira camada que libera decide 'via' (só a exportação olha 'via').
create function app_private.dashboard_access(p_user uuid, p_unit uuid, p_dashboard text)
returns table (scope text, via text)
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
    -- organização, companhia e dashboard ativos; dashboard ligado na companhia
    -- (desligado: só para quem pode religar, o Desenvolvedor)
    select u.org_id, d.group_slug into v_org, v_group
    from app.units u
    join app.organizations o     on o.id = u.org_id and o.active
    join app.org_dashboards od   on od.org_id = u.org_id and od.unit_id = u.id
                                and od.dashboard_key = p_dashboard
                                and (od.enabled
                                     or app_private.has_unit_permission(p_user, u.id, 'dashboards.toggle'))
    join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
    where u.id = p_unit and u.active;
    if v_org is null then
        return;
    end if;

    -- membro ativo da organização
    select m.id, m.role_key into v_membership, v_org_role
    from app.memberships m
    where m.org_id = v_org and m.user_id = p_user and m.status = 'active';
    if v_membership is null then
        return;
    end if;

    -- Desenvolvedor (admin) / owner: todas as companhias
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_org_role and rp.permission = 'org.dashboards.all') then
        return query select 'all'::text, 'role'::text;
        return;
    end if;

    -- cargo nesta companhia
    select mu.role_key into v_unit_role
    from app.membership_units mu
    where mu.unit_id = p_unit and mu.membership_id = v_membership;
    if v_unit_role is null then
        return;
    end if;

    -- Gestor / Controller: tudo da companhia
    if exists (select 1 from app.role_permissions rp
               where rp.role_key = v_unit_role and rp.permission = 'unit.dashboards.all') then
        return query select 'all'::text, 'role'::text;
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
        return query select v_scope, 'sector'::text;
        return;
    end if;

    -- Camadas 3 e 4: exceções da pessoa nesta companhia (só visualização)
    if exists (select 1 from app.member_group_grants g
               where g.membership_id = v_membership and g.unit_id = p_unit and g.group_slug = v_group)
       or exists (select 1 from app.member_dashboard_grants g
                  where g.membership_id = v_membership and g.unit_id = p_unit and g.dashboard_key = p_dashboard) then
        return query select 'all'::text, 'personal'::text;
    end if;
end;
$$;

create or replace function app_private.dashboard_scope(p_user uuid, p_unit uuid, p_dashboard text) returns text
language sql stable security definer
set search_path = ''
as $$
    select a.scope from app_private.dashboard_access(p_user, p_unit, p_dashboard) a;
$$;

-- Exporta = o cargo exporta nesta companhia E o acesso vem do cargo ou do setor (exceção da pessoa só vê).
create function app_private.dashboard_can_export(p_user uuid, p_unit uuid, p_dashboard text) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select app_private.has_unit_permission(p_user, p_unit, 'dashboards.export')
       and coalesce((select a.via in ('role', 'sector')
                     from app_private.dashboard_access(p_user, p_unit, p_dashboard) a), false);
$$;

revoke all on function app_private.dashboard_access(uuid, uuid, text)     from public, anon, authenticated;
revoke all on function app_private.dashboard_can_export(uuid, uuid, text) from public, anon, authenticated;
grant execute on function app_private.dashboard_access(uuid, uuid, text)     to service_role;
grant execute on function app_private.dashboard_can_export(uuid, uuid, text) to service_role;

-- ---------------------------------------------------------------------------
-- 4. member_json: exceções da pessoa (só das unidades do escopo)
-- ---------------------------------------------------------------------------
create or replace function app_private.member_json(p_membership uuid, p_scope uuid[])
returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', m.id,
        'name', m.full_name,
        'email', m.email,
        'org_role', m.role_key,
        'units', coalesce((select jsonb_agg(jsonb_build_object('code', u.code, 'role', mu.role_key) order by u.code)
                           from app.membership_units mu join app.units u on u.id = mu.unit_id
                           where mu.membership_id = m.id and mu.unit_id = any (p_scope)), '[]'::jsonb),
        'teams', coalesce((select jsonb_agg(t.name order by t.name)
                           from app.membership_teams mt join app.teams t on t.id = mt.team_id
                           where mt.membership_id = m.id and t.active and t.unit_id = any (p_scope)), '[]'::jsonb),
        'team_ids', coalesce((select jsonb_agg(t.id order by t.name, t.id)
                              from app.membership_teams mt join app.teams t on t.id = mt.team_id
                              where mt.membership_id = m.id and t.active and t.unit_id = any (p_scope)), '[]'::jsonb),
        'extra_groups', coalesce((select jsonb_agg(jsonb_build_object('unit', u.code, 'slug', g.group_slug)
                                                   order by u.code, g.group_slug)
                                  from app.member_group_grants g join app.units u on u.id = g.unit_id
                                  where g.membership_id = m.id and g.unit_id = any (p_scope)), '[]'::jsonb),
        'extra_dashboards', coalesce((select jsonb_agg(jsonb_build_object('unit', u.code, 'key', g.dashboard_key)
                                                       order by u.code, g.dashboard_key)
                                      from app.member_dashboard_grants g join app.units u on u.id = g.unit_id
                                      where g.membership_id = m.id and g.unit_id = any (p_scope)), '[]'::jsonb),
        'status', m.status,
        'last_seen_at', m.last_seen_at,
        'security', case when au.raw_app_meta_data -> 'providers' ? 'google' then 'Google' end
    )
    from app.memberships m
    left join auth.users au on au.id = m.user_id
    where m.id = p_membership;
$$;

-- ---------------------------------------------------------------------------
-- 5. access_overview: grupos, setores com grupos/sees_all; a grade conta as camadas de setor
-- ---------------------------------------------------------------------------
create or replace function api.access_overview(p_org text, p_unit text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org   uuid;
    v_scope uuid[];
    v_unit  app.units;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.access_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não gere acesso nesta organização.';
    end if;

    -- Unidade pedida (?unidade=); se não for uma que quem chama gere (link salvo, ou acabou de tirar
    -- o próprio cargo nela), cai na primeira gerida em vez de esconder a página inteira.
    select * into v_unit from app.units u
    where u.id = any (v_scope)
    order by (u.code = p_unit) desc nulls last, u.code
    limit 1;

    return jsonb_build_object(
        'units', (select jsonb_agg(jsonb_build_object('code', u.code, 'name', u.name) order by u.code)
                  from app.units u where u.id = any (v_scope)),
        'unit', v_unit.code,
        'dashboards', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'key', d.key,
                       'title', d.name,
                       'area', d.area,
                       'group', d.group_slug,
                       -- setores que liberam: regra do card, grupo do setor ou setor que vê tudo
                       'teams', coalesce((select jsonb_agg(t.name order by t.name)
                                          from app.teams t
                                          where t.active and t.unit_id = v_unit.id
                                            and (t.sees_all
                                                 or exists (select 1 from app.access_rules r
                                                            where r.team_id = t.id and r.dashboard_key = d.key)
                                                 or exists (select 1 from app.team_group_grants g
                                                            where g.team_id = t.id and g.group_slug = d.group_slug))),
                                         '[]'::jsonb)
                   ) order by d.sort_order, d.name)
            from app.org_dashboards od
            join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
            where od.unit_id = v_unit.id and od.enabled
        ), '[]'::jsonb),
        'groups', (select jsonb_agg(jsonb_build_object('slug', g.slug, 'name', g.name) order by g.sort_order)
                   from app.hub_groups g),
        'teams', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'id', t.id, 'name', t.name, 'unit', u.code, 'sees_all', t.sees_all,
                       'groups', coalesce((select jsonb_agg(g.group_slug order by g.group_slug)
                                           from app.team_group_grants g where g.team_id = t.id), '[]'::jsonb)
                   ) order by u.code, t.name)
            from app.teams t join app.units u on u.id = t.unit_id
            where t.active and t.unit_id = any (v_scope)
        ), '[]'::jsonb),
        'roles', (
            select jsonb_agg(jsonb_build_object(
                       'key', ro.key,
                       'sees_all', exists (select 1 from app.role_permissions rp
                                           where rp.role_key = ro.key and rp.permission = 'unit.dashboards.all'),
                       'exports', exists (select 1 from app.role_permissions rp
                                          where rp.role_key = ro.key and rp.permission = 'dashboards.export')
                   ) order by ro.sort_order)
            from app.roles ro where ro.level = 'unit'
        ),
        'rules', coalesce((
            select jsonb_agg(jsonb_build_object('team_id', r.team_id, 'dashboard_key', r.dashboard_key))
            from app.access_rules r
            join app.teams t on t.id = r.team_id and t.active and t.unit_id = any (v_scope)
        ), '[]'::jsonb),
        'dashboards_by_unit', (
            select jsonb_object_agg(u.code, coalesce((
                       select jsonb_agg(d.key order by d.sort_order, d.name)
                       from app.org_dashboards od
                       join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
                       where od.unit_id = u.id and od.enabled), '[]'::jsonb))
            from app.units u where u.id = any (v_scope)
        ),
        'titles', coalesce((
            select jsonb_object_agg(x.key, x.name)
            from (select distinct d.key, d.name
                  from app.org_dashboards od
                  join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
                  where od.unit_id = any (v_scope) and od.enabled) x
        ), '{}'::jsonb),
        'group_of', coalesce((
            select jsonb_object_agg(x.key, x.group_slug)
            from (select distinct d.key, d.group_slug
                  from app.org_dashboards od
                  join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
                  where od.unit_id = any (v_scope) and od.enabled) x
        ), '{}'::jsonb),
        'can_set_org_role', v_org = any (app_private.my_org_ids_with('access.manage'))
    );
end;
$$;

-- ---------------------------------------------------------------------------
-- 6. update_member_access: + grupos extras e dashboards avulsos (por unidade)
-- ---------------------------------------------------------------------------
-- p_extra_groups:     [{unit, slug}] estado desejado NAS unidades geridas; null = não muda
-- p_extra_dashboards: [{unit, key}]  idem
-- Sempre: unidade gerida que fica sem cargo perde as exceções dela (como as equipes).
drop function api.update_member_access(text, uuid, jsonb, uuid[], text);
create function api.update_member_access(p_org text, p_member uuid, p_units jsonb, p_teams uuid[], p_org_role text,
                                         p_extra_groups jsonb default null, p_extra_dashboards jsonb default null)
returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org      uuid;
    v_scope    uuid[];
    v_is_admin boolean;
    v_m        app.memberships;
    v_item     jsonb;
    v_unit     uuid;
    v_role     text;
    v_units    uuid[] := '{}';
    v_roles    text[] := '{}';
    v_teams    uuid[] := coalesce(p_teams, '{}');
    v_before   jsonb;
    v_after    jsonb;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.access_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não gere acesso nesta organização.';
    end if;
    v_is_admin := v_org = any (app_private.my_org_ids_with('access.manage'));

    select * into v_m from app.memberships m where m.id = p_member and m.org_id = v_org for update;
    if v_m.id is null or (not v_is_admin and v_m.role_key in ('owner', 'admin')) then
        raise exception using errcode = '42501', message = 'Você não gere o acesso desta pessoa.';
    end if;
    -- Owner: só outro Owner (ou a equipe RA) mexe nos cargos e equipes de um Owner.
    if v_m.role_key = 'owner' and not app_private.can_manage_owners(v_org) then
        raise exception using errcode = '42501', message = 'Só um Owner muda o acesso de outro Owner.';
    end if;
    -- Próprio acesso: Gestor/Controller não muda os próprios cargos e equipes.
    if v_m.user_id = auth.uid() and not v_is_admin then
        raise exception using errcode = '42501', message = 'Você não pode mudar o seu próprio acesso.';
    end if;
    if v_m.status = 'disabled' then
        raise exception using errcode = 'P0001', message = 'Reative a pessoa antes de mudar o acesso.';
    end if;

    -- Papel na organização (Desenvolvedor <-> Membro)
    if p_org_role is not null then
        if not v_is_admin then
            raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor muda o papel na organização.';
        end if;
        if p_org_role not in ('admin', 'member') then
            raise exception using errcode = 'P0001', message = 'Papel na organização inválido.';
        end if;
        if v_m.role_key = 'owner' and p_org_role <> 'owner' then
            raise exception using errcode = 'P0001', message = 'O Owner não muda de papel por aqui.';
        end if;
        if v_m.user_id = auth.uid() and p_org_role <> v_m.role_key then
            raise exception using errcode = 'P0001', message = 'Você não pode mudar o seu próprio papel.';
        end if;
        if v_m.role_key = 'admin' and p_org_role = 'member' and v_m.status = 'active'
           and not exists (select 1 from app.memberships o
                           where o.org_id = v_org and o.id <> v_m.id
                             and o.role_key in ('owner', 'admin') and o.status = 'active') then
            raise exception using errcode = 'P0001',
                message = 'A organização precisa de ao menos um Owner ou Desenvolvedor ativo.';
        end if;
    end if;

    -- Cargos desejados (só unidades do escopo)
    for v_item in select * from jsonb_array_elements(coalesce(p_units, '[]'::jsonb)) loop
        select u.id into v_unit from app.units u
        where u.org_id = v_org and u.active and u.code = v_item ->> 'code';
        if v_unit is null or not (v_unit = any (v_scope)) then
            raise exception using errcode = '42501', message = 'Você não gere acesso nesta unidade.';
        end if;
        v_role := v_item ->> 'role';
        if v_role is null or v_role not in (select ro.key from app.roles ro where ro.level = 'unit') then
            raise exception using errcode = 'P0001', message = 'Cargo inválido.';
        end if;
        if v_unit = any (v_units) then
            raise exception using errcode = 'P0001', message = 'Unidade repetida.';
        end if;
        v_units := v_units || v_unit;
        v_roles := v_roles || v_role;
        v_unit := null;
    end loop;

    -- Equipes desejadas: de unidade do escopo e com cargo nela
    if exists (select 1 from unnest(v_teams) tid
               where not exists (select 1 from app.teams t
                                 where t.id = tid and t.org_id = v_org and t.active and t.unit_id = any (v_scope))) then
        raise exception using errcode = '42501', message = 'Você não gere esta equipe.';
    end if;
    if exists (select 1 from app.teams t where t.id = any (v_teams) and not (t.unit_id = any (v_units))) then
        raise exception using errcode = 'P0001', message = 'Equipe sem cargo na unidade.';
    end if;

    -- Exceções desejadas: unidade do escopo, com cargo nela; grupo e dashboard que existem
    if p_extra_groups is not null then
        if exists (select 1 from jsonb_array_elements(p_extra_groups) e
                   left join app.units u on u.org_id = v_org and u.active and u.code = e ->> 'unit'
                   where u.id is null or not (u.id = any (v_scope))) then
            raise exception using errcode = '42501', message = 'Você não gere acesso nesta unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_groups) e
                   join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                   where not (u.id = any (v_units))) then
            raise exception using errcode = 'P0001', message = 'Grupo extra sem cargo na unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_groups) e
                   where not exists (select 1 from app.hub_groups g where g.slug = e ->> 'slug')) then
            raise exception using errcode = 'P0001', message = 'Grupo inválido.';
        end if;
    end if;
    if p_extra_dashboards is not null then
        if exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                   left join app.units u on u.org_id = v_org and u.active and u.code = e ->> 'unit'
                   where u.id is null or not (u.id = any (v_scope))) then
            raise exception using errcode = '42501', message = 'Você não gere acesso nesta unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                   join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                   where not (u.id = any (v_units))) then
            raise exception using errcode = 'P0001', message = 'Dashboard avulso sem cargo na unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                   join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                   where not exists (select 1 from app.org_dashboards od
                                     where od.unit_id = u.id and od.dashboard_key = e ->> 'key')) then
            raise exception using errcode = 'P0001', message = 'Dashboard avulso não existe nesta unidade.';
        end if;
    end if;

    v_before := app_private.member_json(v_m.id, v_scope);

    -- Cargos: tira das unidades do escopo que não estão na lista; grava os desejados
    delete from app.membership_units mu
     where mu.membership_id = v_m.id and mu.unit_id = any (v_scope) and not (mu.unit_id = any (v_units));
    for i in 1 .. cardinality(v_units) loop
        insert into app.membership_units (org_id, unit_id, membership_id, role_key)
        values (v_org, v_units[i], v_m.id, v_roles[i])
        on conflict (unit_id, membership_id) do update set role_key = excluded.role_key;
    end loop;

    -- Equipes: só as das unidades do escopo
    delete from app.membership_teams mt
     using app.teams t
     where mt.membership_id = v_m.id and t.id = mt.team_id and t.unit_id = any (v_scope)
       and t.active  -- só as equipes que a tela mostra; equipe inativa fica como está
       and not (mt.team_id = any (v_teams));
    insert into app.membership_teams (org_id, team_id, membership_id)
    select v_org, tid, v_m.id from unnest(v_teams) tid
    on conflict do nothing;

    -- Exceções: unidade do escopo sem cargo perde todas; o resto só muda quando veio a lista
    delete from app.member_group_grants g
     where g.membership_id = v_m.id and g.unit_id = any (v_scope) and not (g.unit_id = any (v_units));
    delete from app.member_dashboard_grants g
     where g.membership_id = v_m.id and g.unit_id = any (v_scope) and not (g.unit_id = any (v_units));
    if p_extra_groups is not null then
        delete from app.member_group_grants g
         where g.membership_id = v_m.id and g.unit_id = any (v_scope)
           and not exists (select 1 from jsonb_array_elements(p_extra_groups) e
                           join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                           where u.id = g.unit_id and e ->> 'slug' = g.group_slug);
        insert into app.member_group_grants (membership_id, unit_id, group_slug, created_by)
        select v_m.id, u.id, e ->> 'slug', auth.uid()
        from jsonb_array_elements(p_extra_groups) e
        join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
        on conflict do nothing;
    end if;
    if p_extra_dashboards is not null then
        delete from app.member_dashboard_grants g
         where g.membership_id = v_m.id and g.unit_id = any (v_scope)
           and not exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                           join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                           where u.id = g.unit_id and e ->> 'key' = g.dashboard_key);
        insert into app.member_dashboard_grants (membership_id, unit_id, dashboard_key, created_by)
        select v_m.id, u.id, e ->> 'key', auth.uid()
        from jsonb_array_elements(p_extra_dashboards) e
        join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
        on conflict do nothing;
    end if;

    if p_org_role is not null and p_org_role <> v_m.role_key then
        update app.memberships set role_key = p_org_role where id = v_m.id;
    end if;

    v_after := app_private.member_json(v_m.id, v_scope);
    if v_after <> v_before then
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_org, auth.uid(), 'member.access_updated', 'membership', v_m.id::text,
                jsonb_build_object('before', v_before, 'after', v_after));
    end if;

    return v_after;
end;
$$;

revoke all on function api.update_member_access(text, uuid, jsonb, uuid[], text, jsonb, jsonb) from public, anon;
grant execute on function api.update_member_access(text, uuid, jsonb, uuid[], text, jsonb, jsonb) to authenticated;

-- ---------------------------------------------------------------------------
-- 7. Grupos de um setor (aba Acesso)
-- ---------------------------------------------------------------------------
-- p_groups: estado desejado (slugs). p_sees_all: null = não muda; só Owner/Desenvolvedor muda.
create function api.set_team_groups(p_org text, p_team uuid, p_groups text[], p_sees_all boolean default null)
returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org      uuid;
    v_scope    uuid[];
    v_team     app.teams;
    v_groups   text[] := coalesce(p_groups, '{}');
    v_before   jsonb;
    v_after    jsonb;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.access_scope(v_org) end;

    select * into v_team from app.teams t where t.id = p_team and t.org_id = v_org and t.active for update;
    if v_team.id is null or not (v_team.unit_id = any (v_scope)) then
        raise exception using errcode = '42501', message = 'Você não gere esta equipe.';
    end if;
    if p_sees_all is not null and p_sees_all <> v_team.sees_all
       and not (v_org = any (app_private.my_org_ids_with('access.manage'))) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor muda quem vê tudo.';
    end if;
    if exists (select 1 from unnest(v_groups) s where not exists (select 1 from app.hub_groups g where g.slug = s)) then
        raise exception using errcode = 'P0001', message = 'Grupo inválido.';
    end if;

    v_before := jsonb_build_object(
        'sees_all', v_team.sees_all,
        'groups', coalesce((select jsonb_agg(g.group_slug order by g.group_slug)
                            from app.team_group_grants g where g.team_id = v_team.id), '[]'::jsonb));

    delete from app.team_group_grants g where g.team_id = v_team.id and not (g.group_slug = any (v_groups));
    insert into app.team_group_grants (org_id, team_id, group_slug, created_by)
    select v_org, v_team.id, s, auth.uid() from unnest(v_groups) s
    on conflict do nothing;
    if p_sees_all is not null and p_sees_all <> v_team.sees_all then
        update app.teams set sees_all = p_sees_all, updated_at = now() where id = v_team.id;
    end if;

    v_after := jsonb_build_object(
        'sees_all', coalesce(p_sees_all, v_team.sees_all),
        'groups', coalesce((select jsonb_agg(g.group_slug order by g.group_slug)
                            from app.team_group_grants g where g.team_id = v_team.id), '[]'::jsonb));
    if v_after <> v_before then
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_org, auth.uid(), 'team.access_updated', 'team', v_team.id::text,
                jsonb_build_object('team', v_team.name, 'before', v_before, 'after', v_after));
    end if;

    return jsonb_build_object('id', v_team.id) || v_after;
end;
$$;

revoke all on function api.set_team_groups(text, uuid, text[], boolean) from public, anon;
grant execute on function api.set_team_groups(text, uuid, text[], boolean) to authenticated;

-- ---------------------------------------------------------------------------
-- 8. Carga inicial (LexGroup), combinada em 19/11/2026
-- ---------------------------------------------------------------------------
-- Diretoria vê tudo da unidade (inclusive grupos e cards que vierem depois)
update app.teams t set sees_all = true
  from app.organizations o
 where o.id = t.org_id and o.slug = 'lexgroup' and t.name = 'Diretoria';

-- Controladoria: a coluna Jurídico inteira
insert into app.team_group_grants (org_id, team_id, group_slug)
select t.org_id, t.id, 'juridico'
  from app.teams t
  join app.organizations o on o.id = t.org_id and o.slug = 'lexgroup'
 where t.name = 'Controladoria' and t.active
on conflict do nothing;

-- Células do Jurídico: só os cards da rotina, sem Execução (execucao, acordos)
with mapa (setor, dashboard_key) as (
    values
        ('Publicações', 'publicacoes'),
        ('Emendas e Manifestações', 'emendas-manifestacoes'),
        ('Réplicas', 'replicas'),
        ('Acompanhamento Processual', 'publicacoes'),
        ('Acompanhamento Processual', 'pendencias-intermediarias'),
        ('Acompanhamento Processual', 'emendas-manifestacoes'),
        ('Acompanhamento Processual', 'replicas'),
        ('Acompanhamento Processual', 'recursal'),
        ('Acompanhamento Processual', 'julgados-sentencas'),
        ('Acompanhamento Processual', 'julgados-acordaos')
)
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
select t.org_id, t.id, m.dashboard_key, 'all'
  from app.teams t
  join app.organizations o on o.id = t.org_id and o.slug = 'lexgroup'
  join mapa m on m.setor = t.name
  join app.org_dashboards od on od.unit_id = t.unit_id
                            and od.dashboard_key = m.dashboard_key
                            and od.enabled
 where t.active
on conflict (team_id, dashboard_key) do nothing;

-- =============================================================================
-- Desfazer (rodar à mão):
-- delete from app.access_rules r using app.teams t
--  where t.id = r.team_id and r.created_at::date = '2026-11-19'
--    and t.name in ('Publicações', 'Emendas e Manifestações', 'Réplicas', 'Acompanhamento Processual');
-- drop function api.set_team_groups(text, uuid, text[], boolean);
-- drop function api.update_member_access(text, uuid, jsonb, uuid[], text, jsonb, jsonb);
--   e recriar com o corpo de 20261113235950_seguranca_membros.sql (+ grants);
-- recriar api.access_overview e app_private.member_json como em 20261113140000_acesso.sql;
-- recriar app_private.dashboard_scope como em 20261118130000_dashboards_liga_desliga.sql;
-- drop function app_private.dashboard_can_export(uuid, uuid, text);
-- drop function app_private.dashboard_access(uuid, uuid, text);
-- drop table app.member_dashboard_grants, app.member_group_grants, app.team_group_grants;
-- alter table app.teams drop column sees_all;
-- drop trigger catalog_group_from_area on app.dashboard_catalog;
-- drop function app_private.catalog_group_from_area();
-- alter table app.dashboard_catalog drop column group_slug;
-- drop table app.hub_groups;
-- =============================================================================
