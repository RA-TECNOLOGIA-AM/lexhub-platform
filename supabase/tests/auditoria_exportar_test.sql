-- =============================================================================
-- Teste de 20261118190000_auditoria_exportar.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-audexp'; h1 Desenvolvedor (pode); h2 colaborador (recusado).
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000ae001', 'dev.audexp@exemplo.com'),
       ('00000000-0000-4000-8000-0000000ae002', 'colab.audexp@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000ae001', 'org-teste-audexp', 'Org Teste Exportar');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000ae001', '10000000-0000-4000-8000-0000000ae001',
        '00000000-0000-4000-8000-0000000ae001', 'Dev Exportar', 'dev.audexp@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000ae002', '10000000-0000-4000-8000-0000000ae001',
        '00000000-0000-4000-8000-0000000ae002', 'Colab Exportar', 'colab.audexp@exemplo.com', 'member', 'active');

set local role authenticated;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000ae001","role":"authenticated"}';
do $$
declare e jsonb;
begin
    perform api.log_audit_export('org-teste-audexp', 'login', '', 42);
    e := api.list_audit('org-teste-audexp') -> 'events';
    if jsonb_array_length(e) <> 1 or e -> 0 ->> 'action' <> 'audit.export' or e -> 0 ->> 'actor' <> 'Dev Exportar' then
        raise exception 'FALHOU: evento de exportação: %', e;
    end if;
    if e -> 0 -> 'metadata' <> '{"kind": "login", "rows": 42, "format": "csv"}'::jsonb then
        raise exception 'FALHOU: metadata (pessoa vazia não entra): %', e -> 0 -> 'metadata';
    end if;
end $$;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000ae002","role":"authenticated"}';
do $$
begin
    begin
        perform api.log_audit_export('org-teste-audexp', null, null, 1);
        raise exception 'FALHOU: colaborador não deveria exportar a auditoria';
    exception when insufficient_privilege then null;
    end;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
