-- =============================================================================
-- Modo suporte "ver como": Owner/Desenvolvedor navega como um membro, com motivo e prazo.
-- Esta migration é só o banco (a API vem depois). Aditiva: tabela nova, função nova e o menu
-- ganha a chave 'support'. Nada existente muda de comportamento.
--   1. app.support_sessions: uma sessão por vez por pessoa, com motivo e vencimento (1 hora).
--      Só o service_role (a API) lê e grava; authenticated não enxerga a tabela.
--   2. app_private.close_expired_support_sessions(): fecha as vencidas e registra 'support.ended'.
--   3. pg_cron a cada 15 min (o Postgres do CI não tem pg_cron: lá só pula).
--   4. api.my_admin_permissions ganha 'support' (quem vê tudo na organização: Owner e Desenvolvedor).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Sessões de suporte
-- ---------------------------------------------------------------------------
create table app.support_sessions (
    id                   uuid primary key default gen_random_uuid(),
    org_id               uuid not null references app.organizations (id) on delete cascade,
    actor_user_id        uuid not null,
    target_user_id       uuid not null,
    target_membership_id uuid not null references app.memberships (id) on delete cascade,
    reason               text not null check (char_length(btrim(reason)) between 5 and 500),
    started_at           timestamptz not null default now(),
    expires_at           timestamptz not null default now() + interval '1 hour',
    ended_at             timestamptz,
    end_reason           text check (end_reason in ('exit', 'expired')),
    check (actor_user_id <> target_user_id),
    check ((ended_at is null) = (end_reason is null))
);

-- Uma sessão aberta por pessoa.
create unique index support_sessions_one_open_idx on app.support_sessions (actor_user_id) where ended_at is null;
-- Para a limpeza achar as abertas que venceram.
create index support_sessions_open_expires_idx on app.support_sessions (expires_at) where ended_at is null;

alter table app.support_sessions enable row level security;
revoke all on app.support_sessions from public, anon, authenticated;
grant select, insert, update on app.support_sessions to service_role;

-- ---------------------------------------------------------------------------
-- 2. Vencimento: fecha as sessões abertas que passaram do prazo
-- ---------------------------------------------------------------------------
create function app_private.close_expired_support_sessions() returns integer
language plpgsql security definer
set search_path = ''
as $$
declare
    v_count integer;
begin
    with closed as (
        update app.support_sessions s
        set ended_at = s.expires_at, end_reason = 'expired'
        where s.ended_at is null and s.expires_at <= now()
        returning s.id, s.org_id, s.actor_user_id, s.target_membership_id
    ), logged as (
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        select c.org_id, c.actor_user_id, 'support.ended', 'membership', c.target_membership_id::text,
               jsonb_build_object('session', c.id, 'end_reason', 'expired')
        from closed c
        returning 1
    )
    select count(*) into v_count from closed;
    return v_count;
end;
$$;

revoke all on function app_private.close_expired_support_sessions() from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. A cada 15 minutos. O Postgres do CI não tem pg_cron: lá só pula.
-- ---------------------------------------------------------------------------
do $$
begin
    if exists (select 1 from pg_catalog.pg_available_extensions where name = 'pg_cron') then
        create extension if not exists pg_cron with schema pg_catalog;
        perform cron.schedule('lexhub-close-support-sessions', '*/15 * * * *',
                              'select app_private.close_expired_support_sessions()');
    end if;
end;
$$;

-- ---------------------------------------------------------------------------
-- 4. Menu: api.my_admin_permissions ganha 'support' (mesmo corpo de 20261116100000_plano_clientes.sql)
-- ---------------------------------------------------------------------------
create or replace function api.my_admin_permissions(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null then
        return jsonb_build_object('access', false, 'members', false, 'sources', false, 'audit', false,
                                  'billing', false, 'clients', app_private.can_see_clients(), 'support', false);
    end if;
    return jsonb_build_object(
        'access', cardinality(app_private.access_scope(v_org)) > 0,
        'members', cardinality(app_private.members_scope(v_org)) > 0,
        'sources', cardinality(app_private.sources_scope(v_org)) > 0,
        'audit', v_org = any (app_private.my_org_ids_with('audit.view')),
        'billing', v_org = any (app_private.my_org_ids_with('billing.view')) or app_private.is_platform_staff(),
        'clients', app_private.can_see_clients(),
        'support', v_org = any (app_private.my_org_ids_with('org.dashboards.all'))
    );
end;
$$;

-- =============================================================================
-- Rollback:
-- (recriar api.my_admin_permissions com o corpo de 20261116100000_plano_clientes.sql)
-- select cron.unschedule('lexhub-close-support-sessions');   -- só onde há pg_cron
-- drop function app_private.close_expired_support_sessions();
-- drop table app.support_sessions;
