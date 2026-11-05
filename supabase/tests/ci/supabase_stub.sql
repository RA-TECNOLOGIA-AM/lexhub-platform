-- =============================================================================
-- SÓ PARA O CI: simula o mínimo do Supabase num Postgres puro
-- (papéis anon/authenticated/service_role, auth.users e auth.uid()).
-- NUNCA rodar no Supabase de verdade — lá isso já existe.
-- =============================================================================
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
grant anon, authenticated, service_role to current_user;

create schema auth;
create table auth.users (id uuid primary key, email text);

create function auth.uid() returns uuid
language sql stable
as $$
  select nullif(current_setting('request.jwt.claims', true)::json ->> 'sub', '')::uuid
$$;

grant usage on schema auth to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
