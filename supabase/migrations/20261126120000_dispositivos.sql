-- =============================================================================
-- Dispositivos (Configurações): a pessoa vê onde a conta dela está aberta e derruba um aparelho.
--
-- Usa as sessões que o Supabase já guarda (auth.sessions); nada de tabela nova.
-- 1) api.list_my_sessions(): as sessões de quem chama que não venceram, a atual primeiro (pelo claim
--    session_id do token) e depois pela última atividade.
-- 2) api.revoke_my_session(p_id): apaga uma sessão de quem chama (o Supabase apaga junto os refresh tokens;
--    o aparelho derrubado percebe em até 1 minuto pelo getUser do front). A sessão atual não: para ela o
--    front usa "Sair". Grava 'auth.session_revoked' em app.audit_log, uma linha por organização ativa
--    (como o 'auth.login'), com IP e navegador no metadata.
--
-- Aditiva. Teste: supabase/tests/dispositivos_test.sql (termina com rollback).
-- =============================================================================

create function api.list_my_sessions()
returns table (
    id uuid,
    created_at timestamptz,
    last_active_at timestamptz,
    user_agent text,
    ip text,
    current boolean
)
language sql stable security definer
set search_path = ''
as $$
    select s.id,
           s.created_at,
           greatest(s.created_at, s.updated_at, s.refreshed_at at time zone 'UTC') as last_active_at,
           s.user_agent,
           host(s.ip),
           s.id::text = coalesce(auth.jwt() ->> 'session_id', '') as current
      from auth.sessions s
     where s.user_id = auth.uid()
       and (s.not_after is null or s.not_after > now())
     order by 6 desc, 3 desc nulls last;
$$;

revoke all on function api.list_my_sessions() from public, anon;
grant execute on function api.list_my_sessions() to authenticated;

create function api.revoke_my_session(p_id uuid) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    s auth.sessions%rowtype;
begin
    if p_id::text = coalesce(auth.jwt() ->> 'session_id', '') then
        raise exception 'use_sign_out' using errcode = 'P0001';
    end if;

    select * into s from auth.sessions where id = p_id and user_id = auth.uid();
    if not found then
        raise exception 'session_not_found' using errcode = 'P0002';
    end if;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata, ip, user_agent)
    select m.org_id, s.user_id, 'auth.session_revoked', 'session', s.id::text,
           jsonb_strip_nulls(jsonb_build_object('ip', host(s.ip), 'userAgent', s.user_agent)),
           s.ip, s.user_agent
      from app.memberships m
     where m.user_id = s.user_id and m.status = 'active';

    delete from auth.sessions where id = s.id;
end;
$$;

revoke all on function api.revoke_my_session(uuid) from public, anon;
grant execute on function api.revoke_my_session(uuid) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.revoke_my_session(uuid);
-- drop function api.list_my_sessions();
-- (os eventos 'auth.session_revoked' ficam: app.audit_log é só de inserção)
-- =============================================================================
