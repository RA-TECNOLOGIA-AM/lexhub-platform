-- =============================================================================
-- Teste de 20261118180000_auditoria_entradas.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-entradas'; h1 Desenvolvedor ativo; h2 desativado; h3 sem organização.
--   Uma sessão nova de cada um: só a de h1 vira evento, com IP e navegador, e atualiza o último acesso.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000e1001', 'dev.entradas@exemplo.com'),
       ('00000000-0000-4000-8000-0000000e1002', 'off.entradas@exemplo.com'),
       ('00000000-0000-4000-8000-0000000e1003', 'sem.org@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000e1001', 'org-teste-entradas', 'Org Teste Entradas');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000e1001', '10000000-0000-4000-8000-0000000e1001',
        '00000000-0000-4000-8000-0000000e1001', 'Dev Entradas', 'dev.entradas@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000e1002', '10000000-0000-4000-8000-0000000e1001',
        '00000000-0000-4000-8000-0000000e1002', 'Off Entradas', 'off.entradas@exemplo.com', 'member', 'disabled');

insert into auth.sessions (id, user_id, created_at, updated_at, ip, user_agent)
values ('50000000-0000-4000-8000-0000000e1001', '00000000-0000-4000-8000-0000000e1001', now(), now(),
        '189.10.20.30', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36'),
       ('50000000-0000-4000-8000-0000000e1002', '00000000-0000-4000-8000-0000000e1002', now(), now(), null, null),
       ('50000000-0000-4000-8000-0000000e1003', '00000000-0000-4000-8000-0000000e1003', now(), now(), null, null);

set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000e1001","role":"authenticated"}';
do $$
declare
    e jsonb := api.list_audit('org-teste-entradas') -> 'events';
    seen timestamptz;
begin
    if jsonb_array_length(e) <> 1 then raise exception 'FALHOU: deveria haver 1 entrada (só a ativa): %', e; end if;
    if e -> 0 ->> 'action' <> 'auth.login' or e -> 0 ->> 'actor' <> 'Dev Entradas' then
        raise exception 'FALHOU: evento de entrada: %', e -> 0;
    end if;
    if e -> 0 -> 'metadata' ->> 'ip' <> '189.10.20.30' or e -> 0 -> 'metadata' ->> 'userAgent' not like '%Chrome%' then
        raise exception 'FALHOU: IP/navegador no metadata: %', e -> 0 -> 'metadata';
    end if;
end $$;
reset role;

do $$
begin
    if (select last_seen_at from app.memberships where id = '40000000-0000-4000-8000-0000000e1001') is null then
        raise exception 'FALHOU: último acesso do ativo não foi gravado';
    end if;
    if (select last_seen_at from app.memberships where id = '40000000-0000-4000-8000-0000000e1002') is not null then
        raise exception 'FALHOU: desativado não deveria ganhar último acesso';
    end if;
    if exists (select 1 from app.audit_log where actor_user_id = '00000000-0000-4000-8000-0000000e1003') then
        raise exception 'FALHOU: pessoa sem organização não gera evento';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
