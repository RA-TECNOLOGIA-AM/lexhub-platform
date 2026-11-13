-- =============================================================================
-- Teste de 20261113160000_permissoes_menu.sql (com o "sources" de 20261113180000_unidades_fontes.sql). Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-menu' com U1; d1 Desenvolvedor, g1 Gestor de U1, x1 Colaborador de U1.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000d1', 'dev.menu@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000d2', 'gestor.menu@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000d3', 'colab.menu@exemplo.com');
insert into app.organizations (id, slug, name) values ('10000000-0000-4000-8000-0000000000d1', 'org-teste-menu', 'Org Teste Menu');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000d1', '10000000-0000-4000-8000-0000000000d1', 'U1', 'Unidade 1');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000d1', '10000000-0000-4000-8000-0000000000d1',
        '00000000-0000-4000-8000-0000000000d1', 'Dev', 'dev.menu@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000d2', '10000000-0000-4000-8000-0000000000d1',
        '00000000-0000-4000-8000-0000000000d2', 'Gestor', 'gestor.menu@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000d3', '10000000-0000-4000-8000-0000000000d1',
        '00000000-0000-4000-8000-0000000000d3', 'Colab', 'colab.menu@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000d1', '20000000-0000-4000-8000-0000000000d1', '40000000-0000-4000-8000-0000000000d2', 'gestor'),
       ('10000000-0000-4000-8000-0000000000d1', '20000000-0000-4000-8000-0000000000d1', '40000000-0000-4000-8000-0000000000d3', 'colaborador');

set local role authenticated;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000d1","role":"authenticated"}';
do $$ begin
    if api.my_admin_permissions('org-teste-menu') <> '{"access":true,"members":true,"sources":true,"audit":true}'::jsonb then
        raise exception 'FALHOU: Dev: %', api.my_admin_permissions('org-teste-menu');
    end if;
end $$;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000d2","role":"authenticated"}';
do $$ begin
    if api.my_admin_permissions('org-teste-menu') <> '{"access":true,"members":true,"sources":true,"audit":false}'::jsonb then
        raise exception 'FALHOU: Gestor: %', api.my_admin_permissions('org-teste-menu');
    end if;
end $$;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000d3","role":"authenticated"}';
do $$ begin
    if api.my_admin_permissions('org-teste-menu') <> '{"access":false,"members":false,"sources":false,"audit":false}'::jsonb then
        raise exception 'FALHOU: Colaborador: %', api.my_admin_permissions('org-teste-menu');
    end if;
    -- Organização de que não faz parte (ou que não existe): tudo falso, sem erro
    if api.my_admin_permissions('nao-existe') <> '{"access":false,"members":false,"sources":false,"audit":false}'::jsonb then
        raise exception 'FALHOU: org inexistente';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
