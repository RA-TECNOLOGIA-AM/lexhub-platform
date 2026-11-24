-- Membros: "Visto há" passa a contar qualquer atividade registrada na Auditoria.
--
-- Antes, memberships.last_seen_at só mudava no login (trigger em auth.sessions) e, desde 24/11, pelo
-- heartbeat api.touch_presence. Como a sessão se renova sozinha (refresh token), quem não entrava de novo
-- ficava com a data do último login, mesmo abrindo dashboards e exportando todo dia: Membros dizia
-- "Visto há 6 dias" enquanto a Auditoria mostrava a pessoa ativa ontem.
--
-- 1) Trigger after insert em app.audit_log: o evento de quem agiu (actor_user_id) adianta o last_seen_at
--    dele naquela organização. Nunca volta no tempo e nunca bloqueia a gravação da auditoria (erro vira warning).
-- 2) Backfill: last_seen_at = o mais recente entre o atual e o último evento da pessoa na organização.

create or replace function app_private.touch_seen_from_audit() returns trigger
language plpgsql security definer
set search_path = ''
as $$
begin
    if new.actor_user_id is not null and new.org_id is not null then
        update app.memberships
           set last_seen_at = new.created_at
         where user_id = new.actor_user_id
           and org_id = new.org_id
           and (last_seen_at is null or last_seen_at < new.created_at);
    end if;
    return null;
exception when others then
    raise warning 'touch_seen_from_audit: %', sqlerrm;
    return null;
end;
$$;

revoke all on function app_private.touch_seen_from_audit() from public, anon, authenticated;

drop trigger if exists touch_seen_from_audit on app.audit_log;
create trigger touch_seen_from_audit
    after insert on app.audit_log
    for each row execute function app_private.touch_seen_from_audit();

update app.memberships m
   set last_seen_at = a.last_audit
  from (select actor_user_id, org_id, max(created_at) as last_audit
          from app.audit_log
         where actor_user_id is not null and org_id is not null
         group by actor_user_id, org_id) a
 where a.actor_user_id = m.user_id
   and a.org_id = m.org_id
   and (m.last_seen_at is null or m.last_seen_at < a.last_audit);
