-- =============================================================================
-- Teste de 20261126100000_modo_suporte_ver_como.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-suporte' com d1 Desenvolvedor, c1 colaborador e uma unidade.
--   Sessão d1 -> c1 funciona; uma segunda aberta, motivo curto e d1 -> d1 são barrados;
--   a sessão vencida é fechada por close_expired_support_sessions() (1 'support.ended', e 0 na 2ª chamada);
--   o menu 'support' é true para d1 e false para c1; 'authenticated' não lê a tabela.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000d1001', 'dev.suporte1@exemplo.com'),
       ('00000000-0000-4000-8000-0000000d1002', 'colab.suporte1@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000d1001', 'org-teste-suporte', 'Org Teste Suporte');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000d1001', '10000000-0000-4000-8000-0000000d1001', 'U1', 'Unidade 1');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000d1001', '10000000-0000-4000-8000-0000000d1001',
        '00000000-0000-4000-8000-0000000d1001', 'Dev Suporte', 'dev.suporte1@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000d1002', '10000000-0000-4000-8000-0000000d1001',
        '00000000-0000-4000-8000-0000000d1002', 'Colab Suporte', 'colab.suporte1@exemplo.com', 'member', 'active');

-- Sessão válida e as barreiras da tabela (como dono: na prática quem escreve é o service_role).
insert into app.support_sessions (id, org_id, actor_user_id, target_user_id, target_membership_id, reason)
values ('70000000-0000-4000-8000-0000000d1001', '10000000-0000-4000-8000-0000000d1001',
        '00000000-0000-4000-8000-0000000d1001', '00000000-0000-4000-8000-0000000d1002',
        '40000000-0000-4000-8000-0000000d1002', 'Chamado 123: tela em branco');

do $$
begin
    begin
        insert into app.support_sessions (org_id, actor_user_id, target_user_id, target_membership_id, reason)
        values ('10000000-0000-4000-8000-0000000d1001', '00000000-0000-4000-8000-0000000d1001',
                '00000000-0000-4000-8000-0000000d1002', '40000000-0000-4000-8000-0000000d1002', 'Outra sessão aberta');
        raise exception 'FALHOU: segunda sessão aberta do mesmo ator deveria dar unique_violation';
    exception when unique_violation then null;
    end;
end $$;

-- Fecha a aberta para testar as checagens abaixo sem esbarrar no índice único.
update app.support_sessions set ended_at = now(), end_reason = 'exit'
where id = '70000000-0000-4000-8000-0000000d1001';

do $$
begin
    begin
        insert into app.support_sessions (org_id, actor_user_id, target_user_id, target_membership_id, reason)
        values ('10000000-0000-4000-8000-0000000d1001', '00000000-0000-4000-8000-0000000d1001',
                '00000000-0000-4000-8000-0000000d1002', '40000000-0000-4000-8000-0000000d1002', 'abc');
        raise exception 'FALHOU: motivo curto deveria dar check_violation';
    exception when check_violation then null;
    end;
    begin
        insert into app.support_sessions (org_id, actor_user_id, target_user_id, target_membership_id, reason)
        values ('10000000-0000-4000-8000-0000000d1001', '00000000-0000-4000-8000-0000000d1001',
                '00000000-0000-4000-8000-0000000d1001', '40000000-0000-4000-8000-0000000d1001', 'Ver como eu mesmo');
        raise exception 'FALHOU: d1 -> d1 deveria dar check_violation';
    exception when check_violation then null;
    end;
end $$;

-- Vencimento: sessão aberta com expires_at no passado.
insert into app.support_sessions (id, org_id, actor_user_id, target_user_id, target_membership_id, reason,
                                  started_at, expires_at)
values ('70000000-0000-4000-8000-0000000d1002', '10000000-0000-4000-8000-0000000d1001',
        '00000000-0000-4000-8000-0000000d1001', '00000000-0000-4000-8000-0000000d1002',
        '40000000-0000-4000-8000-0000000d1002', 'Sessão que vai vencer',
        now() - interval '2 hours', now() - interval '1 hour');

do $$
declare
    v_ended  timestamptz;
    v_reason text;
begin
    if app_private.close_expired_support_sessions() <> 1 then
        raise exception 'FALHOU: deveria fechar 1 sessão vencida';
    end if;
    select ended_at, end_reason into v_ended, v_reason from app.support_sessions
    where id = '70000000-0000-4000-8000-0000000d1002';
    if v_reason is distinct from 'expired' then raise exception 'FALHOU: end_reason deveria ser expired'; end if;
    if v_ended is distinct from (select expires_at from app.support_sessions
                                 where id = '70000000-0000-4000-8000-0000000d1002') then
        raise exception 'FALHOU: ended_at deveria ser o expires_at';
    end if;
    if (select count(*) from app.audit_log
        where action = 'support.ended' and target_type = 'membership'
          and org_id = '10000000-0000-4000-8000-0000000d1001'
          and actor_user_id = '00000000-0000-4000-8000-0000000d1001'
          and target_id = '40000000-0000-4000-8000-0000000d1002'
          and metadata ->> 'session' = '70000000-0000-4000-8000-0000000d1002'
          and metadata ->> 'end_reason' = 'expired') <> 1 then
        raise exception 'FALHOU: deveria haver 1 support.ended da sessão vencida';
    end if;
    if app_private.close_expired_support_sessions() <> 0 then
        raise exception 'FALHOU: segunda chamada deveria devolver 0';
    end if;
end $$;

-- Menu: só quem vê tudo (Dev/Owner) tem 'support'.
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000d1001","role":"authenticated"}';
do $$
begin
    if (api.my_admin_permissions('org-teste-suporte') ->> 'support')::boolean is distinct from true then
        raise exception 'FALHOU: d1 deveria ter support = true';
    end if;
    if (api.my_admin_permissions('org-inexistente') ->> 'support')::boolean is distinct from false then
        raise exception 'FALHOU: sem organização, support deveria ser false';
    end if;
    begin
        perform 1 from app.support_sessions;
        raise exception 'FALHOU: authenticated não deveria ler app.support_sessions';
    exception when insufficient_privilege then null;
    end;
end $$;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000d1002","role":"authenticated"}';
do $$
begin
    if (api.my_admin_permissions('org-teste-suporte') ->> 'support')::boolean is distinct from false then
        raise exception 'FALHOU: c1 deveria ter support = false';
    end if;
end $$;

do $$ begin raise notice 'OK: modo suporte (sessões, vencimento, menu)'; end $$;

rollback;
