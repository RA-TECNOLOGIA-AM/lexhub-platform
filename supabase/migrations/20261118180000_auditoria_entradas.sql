-- =============================================================================
-- Auditoria: entradas (logins) no LexHub.
--
-- Até aqui nada gravava login: o filtro "Entradas" da tela de Auditoria ficava sempre vazio.
-- Cada entrada (Google, senha, QR da TV) cria uma linha em auth.sessions; um trigger copia essa linha para
-- app.audit_log como 'auth.login', uma vez por organização em que a pessoa está ativa (a tela é por organização).
-- A linha de auth.sessions some quando a pessoa sai, por isso a cópia: o histórico fica em app.audit_log.
-- Também atualiza memberships.last_seen_at (a aba Membros já mostra "último acesso", mas ninguém gravava).
--
-- Aditiva: cria app_private.audit_login + trigger em auth.sessions; copia as sessões que já existem.
-- O trigger nunca bloqueia o login: qualquer erro vira só um aviso no log do Postgres.
-- IP e navegador vão nas colunas ip/user_agent e também no metadata (api.list_audit devolve só o metadata).
-- Teste: supabase/tests/auditoria_entradas_test.sql (termina com rollback).
-- =============================================================================

create function app_private.audit_login() returns trigger
language plpgsql security definer
set search_path = ''
as $$
begin
    begin
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata, ip, user_agent, created_at)
        select m.org_id, new.user_id, 'auth.login', 'session', new.id::text,
               jsonb_strip_nulls(jsonb_build_object('ip', host(new.ip), 'userAgent', new.user_agent)),
               new.ip, new.user_agent, coalesce(new.created_at, now())
        from app.memberships m
        where m.user_id = new.user_id and m.status = 'active';

        update app.memberships m
        set last_seen_at = coalesce(new.created_at, now())
        where m.user_id = new.user_id and m.status = 'active';
    exception when others then
        raise warning 'audit_login: % (%)', sqlerrm, sqlstate;
    end;
    return new;
end;
$$;

revoke all on function app_private.audit_login() from public, anon, authenticated;

create trigger audit_login
after insert on auth.sessions
for each row execute function app_private.audit_login();

-- Sessões que já existem (desde a migração para o lexhub-v2): entram no histórico uma vez só.
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata, ip, user_agent, created_at)
select m.org_id, s.user_id, 'auth.login', 'session', s.id::text,
       jsonb_strip_nulls(jsonb_build_object('ip', host(s.ip), 'userAgent', s.user_agent)),
       s.ip, s.user_agent, s.created_at
from auth.sessions s
join app.memberships m on m.user_id = s.user_id and m.status = 'active'
where not exists (
    select 1 from app.audit_log a
    where a.action = 'auth.login' and a.target_id = s.id::text and a.org_id = m.org_id
);

update app.memberships m
set last_seen_at = x.last_at
from (select user_id, max(created_at) as last_at from auth.sessions group by user_id) x
where m.user_id = x.user_id and m.status = 'active'
  and (m.last_seen_at is null or m.last_seen_at < x.last_at);

-- =============================================================================
-- Rollback:
-- drop trigger audit_login on auth.sessions;
-- drop function app_private.audit_login();
-- (os eventos 'auth.login' ficam: app.audit_log é só de inserção)
-- =============================================================================
