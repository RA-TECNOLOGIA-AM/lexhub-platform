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
  not_after  timestamptz,
  refreshed_at timestamp, -- sem fuso (UTC), como no Supabase
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

-- Storage (buckets e arquivos): só o que as migrations usam (ex.: bucket 'avatars' da foto de perfil).
create schema storage;
create table storage.buckets (
  id                 text primary key,
  name               text not null,
  public             boolean default false,
  file_size_limit    bigint,
  allowed_mime_types text[]
);
create table storage.objects (
  id        uuid primary key default gen_random_uuid(),
  bucket_id text references storage.buckets (id),
  name      text,
  owner     uuid
);
alter table storage.objects enable row level security;

-- Pastas do caminho, sem o nome do arquivo: 'a/b/c.png' -> {a,b} (igual ao do Supabase).
create function storage.foldername(name text) returns text[]
language sql immutable
as $$
  select (string_to_array(name, '/'))[1:array_length(string_to_array(name, '/'), 1) - 1]
$$;

grant usage on schema storage to anon, authenticated, service_role;
grant select, insert, update, delete on storage.objects to authenticated, service_role;
grant select on storage.buckets to anon, authenticated, service_role;
grant execute on function storage.foldername(text) to anon, authenticated, service_role;
