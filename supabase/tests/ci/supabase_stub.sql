-- =============================================================================
-- SÓ PARA O CI: simula o mínimo do Supabase num Postgres puro
-- (papéis anon/authenticated/service_role, auth.users, auth.uid() e auth.jwt()).
-- NUNCA rodar no Supabase de verdade — lá isso já existe.
-- =============================================================================
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
grant anon, authenticated, service_role to current_user;

create schema auth;
-- Só as colunas que as migrations e os testes usam (no Supabase a tabela tem muitas outras).
create table auth.users (
  id                 uuid primary key,
  email              text,
  raw_user_meta_data jsonb default '{}'::jsonb,
  raw_app_meta_data  jsonb default '{}'::jsonb
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
