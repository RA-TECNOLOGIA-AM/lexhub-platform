-- =============================================================================
-- Teste de 20261126150000_perfil_senha.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: s1 ativo em uma org, só Google (senha ''); s2 sem organização (senha null).
--   my_password_status: false -> cria senha -> true.
--   Criar grava 1 'auth.password_changed' (kind created); trocar grava outra (kind changed).
--   Update que não mexe na senha não grava nada; s2 troca a senha sem erro e sem linha.
-- =============================================================================

begin;

insert into auth.users (id, email, encrypted_password)
values ('00000000-0000-4000-8000-0000000e5001', 'senha1@exemplo.com', ''),
       ('00000000-0000-4000-8000-0000000e5002', 'senha2@exemplo.com', null);
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000e5001', 'org-teste-senha', 'Org Teste Senha');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000e5001', '10000000-0000-4000-8000-0000000e5001',
        '00000000-0000-4000-8000-0000000e5001', 'Senha Um', 'senha1@exemplo.com', 'member', 'active');

-- Só Google: sem senha.
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000e5001","role":"authenticated"}';
do $$
begin
    if api.my_password_status() then raise exception 'FALHOU: senha vazia deveria ser "sem senha"'; end if;
end $$;
reset role;

-- Cria a senha (o Supabase faz este update quando a pessoa chama updateUser).
update auth.users set encrypted_password = '$2a$10$criada' where id = '00000000-0000-4000-8000-0000000e5001';

set local role authenticated;
do $$
begin
    if not api.my_password_status() then raise exception 'FALHOU: depois de criar deveria ter senha'; end if;
end $$;
reset role;

-- Troca a senha; depois um update que não mexe na senha.
update auth.users set encrypted_password = '$2a$10$trocada' where id = '00000000-0000-4000-8000-0000000e5001';
update auth.users set email = 'senha1.novo@exemplo.com' where id = '00000000-0000-4000-8000-0000000e5001';

-- Sem organização: troca sem erro e sem linha.
update auth.users set encrypted_password = '$2a$10$s2' where id = '00000000-0000-4000-8000-0000000e5002';

do $$
declare
    kinds text[];
begin
    -- Tudo na mesma transação = mesmo created_at: compara em ordem alfabética.
    select array_agg(a.metadata ->> 'kind' order by a.metadata ->> 'kind') into kinds
    from app.audit_log a
    where a.action = 'auth.password_changed' and a.actor_user_id = '00000000-0000-4000-8000-0000000e5001';
    if kinds is distinct from array['changed', 'created'] then
        raise exception 'FALHOU: esperava uma created e uma changed, veio %', kinds;
    end if;

    if exists (
        select 1 from app.audit_log a
        where a.action = 'auth.password_changed' and a.actor_user_id = '00000000-0000-4000-8000-0000000e5002'
    ) then
        raise exception 'FALHOU: sem organização não deveria gravar auditoria';
    end if;

    if exists (
        select 1 from app.audit_log a
        where a.action = 'auth.password_changed'
          and a.actor_user_id = '00000000-0000-4000-8000-0000000e5001'
          and (a.org_id <> '10000000-0000-4000-8000-0000000e5001' or a.target_type <> 'user'
               or a.target_id <> '00000000-0000-4000-8000-0000000e5001')
    ) then
        raise exception 'FALHOU: linha de auditoria com org/alvo errado';
    end if;
end $$;

-- anon não chama.
set local role anon;
do $$
begin
    perform api.my_password_status();
    raise exception 'FALHOU: anon não deveria chamar my_password_status';
exception when insufficient_privilege then
    null;
end $$;
reset role;

do $$ begin raise notice 'OK: perfil_senha'; end $$;

rollback;
