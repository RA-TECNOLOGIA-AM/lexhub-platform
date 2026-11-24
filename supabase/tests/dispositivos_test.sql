-- =============================================================================
-- Teste de 20261126120000_dispositivos.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: u1 com 3 sessões (a atual s1, s2 ativa, s3 vencida) e u2 com s4; u1 ativo em uma org.
--   list_my_sessions: só s1 e s2, s1 primeiro e marcada como atual; sem session_id no token, nenhuma atual.
--   revoke_my_session: s4 (de u2) -> session_not_found; s1 (a atual) -> use_sign_out;
--   s2 -> some e grava 1 'auth.session_revoked'.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000e1001', 'disp1@exemplo.com'),
       ('00000000-0000-4000-8000-0000000e1002', 'disp2@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000e1001', 'org-teste-disp', 'Org Teste Dispositivos');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000e1001', '10000000-0000-4000-8000-0000000e1001',
        '00000000-0000-4000-8000-0000000e1001', 'Disp Um', 'disp1@exemplo.com', 'member', 'active');

-- O trigger de login (auth.login) roda aqui; tudo bem.
insert into auth.sessions (id, user_id, created_at, updated_at, refreshed_at, not_after, ip, user_agent)
values ('50000000-0000-4000-8000-0000000e1001', '00000000-0000-4000-8000-0000000e1001',
        now() - interval '2 days', now() - interval '2 days', (now() - interval '1 hour') at time zone 'UTC', null,
        '10.0.0.1', 'Mozilla/5.0 (Windows NT 10.0) Chrome/120'),
       ('50000000-0000-4000-8000-0000000e1002', '00000000-0000-4000-8000-0000000e1001',
        now() - interval '1 day', now() - interval '5 minutes', null, null,
        '10.0.0.2', 'Mozilla/5.0 (Linux; Android 14) Chrome/120'),
       ('50000000-0000-4000-8000-0000000e1003', '00000000-0000-4000-8000-0000000e1001',
        now() - interval '9 days', now() - interval '9 days', null, now() - interval '1 day',
        '10.0.0.3', 'velha'),
       ('50000000-0000-4000-8000-0000000e1004', '00000000-0000-4000-8000-0000000e1002',
        now(), now(), null, null, '10.0.0.4', 'de outra pessoa');

set local role authenticated;
set local request.jwt.claims =
    '{"sub":"00000000-0000-4000-8000-0000000e1001","role":"authenticated","session_id":"50000000-0000-4000-8000-0000000e1001"}';

do $$
declare ids uuid[]; cur boolean[]; ip1 text;
begin
    select array_agg(id order by ord), array_agg(current order by ord)
      into ids, cur
      from (select *, row_number() over () as ord from api.list_my_sessions()) x;
    if ids is distinct from array['50000000-0000-4000-8000-0000000e1001', '50000000-0000-4000-8000-0000000e1002']::uuid[] then
        raise exception 'FALHOU: deveria listar s1 (atual) e s2, nessa ordem: %', ids;
    end if;
    if cur is distinct from array[true, false] then raise exception 'FALHOU: atual errada: %', cur; end if;
    select ip into ip1 from api.list_my_sessions() where current;
    if ip1 <> '10.0.0.1' then raise exception 'FALHOU: ip sem máscara esperado: %', ip1; end if;

    begin
        perform api.revoke_my_session('50000000-0000-4000-8000-0000000e1004');
        raise exception 'FALHOU: apagou a sessão de outra pessoa';
    exception when others then
        if sqlerrm <> 'session_not_found' then raise; end if;
    end;
    begin
        perform api.revoke_my_session('50000000-0000-4000-8000-0000000e1001');
        raise exception 'FALHOU: revogou a sessão atual';
    exception when others then
        if sqlerrm <> 'use_sign_out' then raise; end if;
    end;

    perform api.revoke_my_session('50000000-0000-4000-8000-0000000e1002');
    if exists (select 1 from api.list_my_sessions() where id = '50000000-0000-4000-8000-0000000e1002') then
        raise exception 'FALHOU: s2 continua na lista';
    end if;
end $$;

-- Sem session_id no token: nenhuma atual, sem erro.
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000e1001","role":"authenticated"}';
do $$
begin
    if exists (select 1 from api.list_my_sessions() where current) then
        raise exception 'FALHOU: sem session_id não há sessão atual';
    end if;
end $$;

reset role;
do $$
declare n int;
begin
    if exists (select 1 from auth.sessions where id = '50000000-0000-4000-8000-0000000e1002') then
        raise exception 'FALHOU: s2 não foi apagada';
    end if;
    if not exists (select 1 from auth.sessions where id = '50000000-0000-4000-8000-0000000e1004') then
        raise exception 'FALHOU: s4 (de outra pessoa) sumiu';
    end if;
    select count(*) into n from app.audit_log
     where action = 'auth.session_revoked' and target_id = '50000000-0000-4000-8000-0000000e1002'
       and org_id = '10000000-0000-4000-8000-0000000e1001'
       and metadata ->> 'ip' = '10.0.0.2';
    if n <> 1 then raise exception 'FALHOU: esperava 1 auth.session_revoked, veio %', n; end if;
    raise notice 'OK: dispositivos';
end $$;

rollback;
