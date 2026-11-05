-- =============================================================================
-- LexHub V2 — núcleo multi-tenant (schema "app")
--
-- Hierarquia: organização > unidade > equipe > membro
--   V1 public.companhia -> app.units      (legacy_companhia_id)
--   V1 public.setor     -> app.teams      (legacy_setor_id)
--   V1 public.usuario   -> app.members    (user_id = auth.users.id, reaproveitado)
--   V1 public.cargo     -> app.members.role / app.unit_members.role
--   V1 dashboardAccess.ts (front) -> app.dashboard_grants + app.user_can_view_dashboard (servidor)
--
-- Regras:
--   * Fica num schema próprio: não toca em nada do "public" (V1 continua igual).
--   * Datas sempre timestamptz (V1 usava horário de Manaus sem fuso).
--   * FKs compostas (org_id, id) garantem que nada liga dados de organizações diferentes.
--   * RLS ligado em todas as tabelas; usuário logado só LÊ. Escritas: service_role (API).
-- =============================================================================

create schema if not exists app;

revoke all on schema app from public;
grant usage on schema app to authenticated, service_role;

-- ---------------------------------------------------------------------------
-- Tipos
-- ---------------------------------------------------------------------------
create type app.org_role      as enum ('owner', 'admin', 'member');
create type app.unit_role     as enum ('manager', 'member');
create type app.member_status as enum ('invited', 'active', 'disabled');

-- ---------------------------------------------------------------------------
-- updated_at automático
-- ---------------------------------------------------------------------------
create function app.set_updated_at() returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------------
-- Organizações (tenant)
-- ---------------------------------------------------------------------------
create table app.organizations (
  id         uuid primary key default gen_random_uuid(),
  slug       text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
  name       text not null check (length(trim(name)) > 0),
  active     boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Unidades (escritórios: NG, LA, RJ...)
-- ---------------------------------------------------------------------------
create table app.units (
  id                  uuid primary key default gen_random_uuid(),
  org_id              uuid not null references app.organizations (id) on delete cascade,
  code                text not null check (code ~ '^[A-Z0-9_]{2,16}$'),
  name                text not null check (length(trim(name)) > 0),
  active              boolean not null default true,
  legacy_companhia_id bigint,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  unique (org_id, code),
  unique (org_id, id)
);

-- ---------------------------------------------------------------------------
-- Equipes (setores dentro de uma unidade)
-- ---------------------------------------------------------------------------
create table app.teams (
  id              uuid primary key default gen_random_uuid(),
  org_id          uuid not null,
  unit_id         uuid not null,
  name            text not null check (length(trim(name)) > 0),
  active          boolean not null default true,
  legacy_setor_id bigint,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (unit_id, name),
  unique (org_id, id),
  unique (unit_id, id),
  foreign key (org_id, unit_id) references app.units (org_id, id) on delete cascade
);

-- ---------------------------------------------------------------------------
-- Membros (pessoa dentro de uma organização)
-- ---------------------------------------------------------------------------
create table app.members (
  id           uuid primary key default gen_random_uuid(),
  org_id       uuid not null references app.organizations (id) on delete cascade,
  user_id      uuid not null references auth.users (id) on delete cascade,
  full_name    text not null check (length(trim(full_name)) > 0),
  email        text not null check (position('@' in email) > 1),
  role         app.org_role not null default 'member',
  status       app.member_status not null default 'invited',
  last_seen_at timestamptz,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  unique (org_id, user_id),
  unique (org_id, id)
);
create index members_user_id_idx on app.members (user_id);
create unique index members_org_email_uq on app.members (org_id, lower(email));

-- Membro em unidade (manager = "Gestor" da V1 naquela unidade)
create table app.unit_members (
  org_id     uuid not null,
  unit_id    uuid not null,
  member_id  uuid not null,
  role       app.unit_role not null default 'member',
  created_at timestamptz not null default now(),
  primary key (unit_id, member_id),
  foreign key (org_id, unit_id)   references app.units (org_id, id)   on delete cascade,
  foreign key (org_id, member_id) references app.members (org_id, id) on delete cascade
);
create index unit_members_member_idx on app.unit_members (member_id);

-- Membro em equipe
create table app.team_members (
  org_id     uuid not null,
  team_id    uuid not null,
  member_id  uuid not null,
  created_at timestamptz not null default now(),
  primary key (team_id, member_id),
  foreign key (org_id, team_id)   references app.teams (org_id, id)   on delete cascade,
  foreign key (org_id, member_id) references app.members (org_id, id) on delete cascade
);
create index team_members_member_idx on app.team_members (member_id);

-- ---------------------------------------------------------------------------
-- Dashboards
-- ---------------------------------------------------------------------------
-- Catálogo do produto (global, igual para todas as organizações)
create table app.dashboards (
  key         text primary key check (key ~ '^[a-z0-9][a-z0-9-]{1,62}$'),
  name        text not null,
  description text,
  active      boolean not null default true,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- Quais dashboards cada unidade contratou/ligou
create table app.unit_dashboards (
  org_id        uuid not null,
  unit_id       uuid not null,
  dashboard_key text not null references app.dashboards (key) on delete cascade,
  enabled       boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  primary key (unit_id, dashboard_key),
  foreign key (org_id, unit_id) references app.units (org_id, id) on delete cascade
);

-- Quem vê o quê: liberação para uma equipe OU para um membro, dentro de uma unidade
create table app.dashboard_grants (
  id            uuid primary key default gen_random_uuid(),
  org_id        uuid not null,
  unit_id       uuid not null,
  dashboard_key text not null,
  team_id       uuid,
  member_id     uuid,
  created_by    uuid references auth.users (id) on delete set null,
  created_at    timestamptz not null default now(),
  check (num_nonnulls(team_id, member_id) = 1),
  foreign key (org_id, unit_id)   references app.units (org_id, id) on delete cascade,
  foreign key (unit_id, dashboard_key)
    references app.unit_dashboards (unit_id, dashboard_key) on delete cascade,
  foreign key (unit_id, team_id)  references app.teams (unit_id, id) on delete cascade,
  foreign key (org_id, member_id) references app.members (org_id, id) on delete cascade
);
create unique index dashboard_grants_team_uq
  on app.dashboard_grants (unit_id, dashboard_key, team_id) where team_id is not null;
create unique index dashboard_grants_member_uq
  on app.dashboard_grants (unit_id, dashboard_key, member_id) where member_id is not null;

-- ---------------------------------------------------------------------------
-- Auditoria (só inserção)
-- ---------------------------------------------------------------------------
create table app.audit_log (
  id            bigint generated always as identity primary key,
  org_id        uuid references app.organizations (id) on delete set null,
  actor_user_id uuid,
  action        text not null,
  target_type   text,
  target_id     text,
  metadata      jsonb not null default '{}'::jsonb,
  ip            inet,
  user_agent    text,
  created_at    timestamptz not null default now()
);
create index audit_log_org_created_idx on app.audit_log (org_id, created_at desc);

create function app.audit_log_immutable() returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception 'app.audit_log é somente inserção';
end;
$$;

create trigger audit_log_no_update before update or delete on app.audit_log
  for each row execute function app.audit_log_immutable();

-- triggers de updated_at
create trigger set_updated_at before update on app.organizations   for each row execute function app.set_updated_at();
create trigger set_updated_at before update on app.units           for each row execute function app.set_updated_at();
create trigger set_updated_at before update on app.teams           for each row execute function app.set_updated_at();
create trigger set_updated_at before update on app.members         for each row execute function app.set_updated_at();
create trigger set_updated_at before update on app.dashboards      for each row execute function app.set_updated_at();
create trigger set_updated_at before update on app.unit_dashboards for each row execute function app.set_updated_at();

-- ---------------------------------------------------------------------------
-- Funções de acesso (security definer: leem sem passar pelo RLS, sem recursão)
-- ---------------------------------------------------------------------------
create function app.is_org_member(p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1
    from app.members m
    join app.organizations o on o.id = m.org_id and o.active
    where m.org_id = p_org
      and m.user_id = auth.uid()
      and m.status = 'active'
  );
$$;

create function app.is_org_admin(p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1
    from app.members m
    join app.organizations o on o.id = m.org_id and o.active
    where m.org_id = p_org
      and m.user_id = auth.uid()
      and m.status = 'active'
      and m.role in ('owner', 'admin')
  );
$$;

-- Regra central de acesso a dashboard (uso interno / API com service_role)
--   1. organização, unidade e dashboard ativos; dashboard ligado na unidade
--   2. membro ativo da organização
--   3. owner/admin da organização -> vê tudo da organização
--      manager da unidade          -> vê tudo da unidade
--      member da unidade           -> só se liberado para ele ou para uma equipe dele
create function app.user_can_view_dashboard(p_user uuid, p_unit uuid, p_dashboard text)
returns boolean
language sql stable security definer
set search_path = ''
as $$
  select exists (
    select 1
    from app.units u
    join app.organizations o  on o.id = u.org_id and o.active
    join app.unit_dashboards ud on ud.unit_id = u.id and ud.dashboard_key = p_dashboard and ud.enabled
    join app.dashboards d     on d.key = ud.dashboard_key and d.active
    join app.members m        on m.org_id = u.org_id and m.user_id = p_user and m.status = 'active'
    where u.id = p_unit
      and u.active
      and (
        m.role in ('owner', 'admin')
        or exists (
          select 1 from app.unit_members um
          where um.unit_id = u.id and um.member_id = m.id and um.role = 'manager'
        )
        or (
          exists (
            select 1 from app.unit_members um
            where um.unit_id = u.id and um.member_id = m.id
          )
          and exists (
            select 1 from app.dashboard_grants g
            where g.unit_id = u.id
              and g.dashboard_key = p_dashboard
              and (
                g.member_id = m.id
                or g.team_id in (
                  select tm.team_id
                  from app.team_members tm
                  join app.teams t on t.id = tm.team_id and t.active
                  where tm.member_id = m.id
                )
              )
          )
        )
      )
  );
$$;

-- Versão para o usuário logado (sempre auth.uid(), não dá para consultar outra pessoa)
create function app.can_view_dashboard(p_unit uuid, p_dashboard text) returns boolean
language sql stable security definer
set search_path = ''
as $$
  select app.user_can_view_dashboard(auth.uid(), p_unit, p_dashboard);
$$;

-- Hub: dashboards que o usuário logado pode abrir
create function app.my_dashboards()
returns table (org_id uuid, unit_id uuid, unit_code text, dashboard_key text, dashboard_name text)
language sql stable security definer
set search_path = ''
as $$
  select u.org_id, u.id, u.code, d.key, d.name
  from app.unit_dashboards ud
  join app.units u      on u.id = ud.unit_id
  join app.dashboards d on d.key = ud.dashboard_key
  where app.user_can_view_dashboard(auth.uid(), u.id, d.key)
  order by u.code, d.name;
$$;

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------
alter table app.organizations    enable row level security;
alter table app.units            enable row level security;
alter table app.teams            enable row level security;
alter table app.members          enable row level security;
alter table app.unit_members     enable row level security;
alter table app.team_members     enable row level security;
alter table app.dashboards       enable row level security;
alter table app.unit_dashboards  enable row level security;
alter table app.dashboard_grants enable row level security;
alter table app.audit_log        enable row level security;

create policy org_select on app.organizations for select to authenticated
  using (app.is_org_member(id));

create policy units_select on app.units for select to authenticated
  using (app.is_org_member(org_id));

create policy teams_select on app.teams for select to authenticated
  using (app.is_org_member(org_id));

-- cada um vê o próprio cadastro; admin vê todos da organização
create policy members_select on app.members for select to authenticated
  using (user_id = auth.uid() or app.is_org_admin(org_id));

create policy unit_members_select on app.unit_members for select to authenticated
  using (
    app.is_org_admin(org_id)
    or member_id in (select id from app.members where user_id = auth.uid())
  );

create policy team_members_select on app.team_members for select to authenticated
  using (
    app.is_org_admin(org_id)
    or member_id in (select id from app.members where user_id = auth.uid())
  );

create policy dashboards_select on app.dashboards for select to authenticated
  using (active);

create policy unit_dashboards_select on app.unit_dashboards for select to authenticated
  using (app.is_org_member(org_id));

create policy dashboard_grants_select on app.dashboard_grants for select to authenticated
  using (app.is_org_admin(org_id));

create policy audit_log_select on app.audit_log for select to authenticated
  using (app.is_org_admin(org_id));

-- ---------------------------------------------------------------------------
-- Permissões
-- ---------------------------------------------------------------------------
revoke all on all tables    in schema app from public, anon;
revoke all on all functions in schema app from public, anon;

grant select on all tables in schema app to authenticated;
grant all    on all tables in schema app to service_role;
grant usage, select on all sequences in schema app to service_role;

grant execute on function app.is_org_member(uuid)                     to authenticated, service_role;
grant execute on function app.is_org_admin(uuid)                      to authenticated, service_role;
grant execute on function app.can_view_dashboard(uuid, text)          to authenticated, service_role;
grant execute on function app.my_dashboards()                         to authenticated, service_role;
grant execute on function app.user_can_view_dashboard(uuid, uuid, text) to service_role;

-- ---------------------------------------------------------------------------
-- Catálogo inicial (dashboards do MVP)
-- ---------------------------------------------------------------------------
insert into app.dashboards (key, name, description) values
  ('protocolo-lexpre', 'Protocolo LexPre', 'Protocolos do LexPre (MVP)'),
  ('pendencias-ng',    'Pendências NG',    'Pendências da unidade NG (MVP)');
