-- =============================================================================
-- SÓ PARA O CI: simula o mínimo do Supabase num Postgres puro
-- (papéis anon/authenticated/service_role, auth.users, auth.uid() e auth.jwt()).
-- NUNCA rodar no Supabase de verdade — lá isso já existe.
-- =============================================================================
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
-- Papel que o Supabase Auth usa para chamar os Auth Hooks.
create role supabase_auth_admin nologin;
grant anon, authenticated, service_role to current_user;

create schema auth;
-- Só as colunas que as migrations e os testes usam (no Supabase a tabela tem muitas outras).
create table auth.users (
  id                 uuid primary key,
  email              text,
  raw_user_meta_data jsonb default '{}'::jsonb,
  raw_app_meta_data  jsonb default '{}'::jsonb
);

-- Identidades de login (Google etc.): o banco confere e-mail verificado por aqui, não pelo user_metadata.
create table auth.identities (
  id            uuid primary key default gen_random_uuid(),
  provider_id   text not null,
  user_id       uuid not null references auth.users (id) on delete cascade,
  identity_data jsonb not null,
  provider      text not null
);

-- Sessões de login: a auditoria de entradas tem um trigger nesta tabela.
create table auth.sessions (
  id         uuid primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz,
  updated_at timestamptz,
  ip         inet,
  user_agent text
);

create function auth.uid() returns uuid
language sql stable
as $$
  select nullif(current_setting('request.jwt.claims', true)::json ->> 'sub', '')::uuid
$$;

-- O token inteiro (ex.: app_metadata.platform_staff), como o Supabase devolve.
create function auth.jwt() returns jsonb
language sql stable
as $$
  select coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb
$$;

grant usage on schema auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
grant execute on function auth.jwt() to anon, authenticated, service_role;
