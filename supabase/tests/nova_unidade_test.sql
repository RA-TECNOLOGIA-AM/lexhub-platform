-- =============================================================================
-- Teste de 20261113220000_nova_unidade.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-unidade' com U1; g1 Desenvolvedor; g2 Gestor de U1.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-000000000ab1', 'dev.unidade@exemplo.com'),
       ('00000000-0000-4000-8000-000000000ab2', 'gestor.unidade@exemplo.com');
insert into app.organizations (id, slug, name) values ('10000000-0000-4000-8000-000000000ab1', 'org-teste-unidade', 'Org Teste Unidade');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-000000000ab1', '10000000-0000-4000-8000-000000000ab1', 'U1', 'Unidade 1', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-000000000ab1', '10000000-0000-4000-8000-000000000ab1',
        '00000000-0000-4000-8000-000000000ab1', 'Dev', 'dev.unidade@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-000000000ab2', '10000000-0000-4000-8000-000000000ab1',
        '00000000-0000-4000-8000-000000000ab2', 'Gestor', 'gestor.unidade@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-000000000ab1', '20000000-0000-4000-8000-000000000ab1', '40000000-0000-4000-8000-000000000ab2', 'gestor');

set local role authenticated;

-- Desenvolvedor: cria, vê na lista, edita nome/fuso; tudo vai para a auditoria
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ab1","role":"authenticated"}';
do $$
declare
    r jsonb;
    l jsonb;
begin
    if (api.list_sources('org-teste-unidade') ->> 'canManageUnits')::boolean is not true then
        raise exception 'FALHOU: Dev deveria poder gerir unidades';
    end if;

    r := api.create_unit('org-teste-unidade', ' u2 ', '  Unidade 2  ', 'America/Sao_Paulo');
    if r -> 'unit' ->> 'code' <> 'U2' or r -> 'unit' ->> 'name' <> 'Unidade 2'
       or r ->> 'timezone' <> 'America/Sao_Paulo' or r -> 'sources' <> '[]'::jsonb then
        raise exception 'FALHOU: unidade criada: %', r;
    end if;
    l := api.list_sources('org-teste-unidade');
    if jsonb_array_length(l -> 'units') <> 2 then raise exception 'FALHOU: lista deveria ter 2 unidades: %', l; end if;

    r := api.update_unit('org-teste-unidade', 'U2', 'Unidade Dois', 'America/Manaus');
    if r -> 'unit' ->> 'name' <> 'Unidade Dois' or r ->> 'timezone' <> 'America/Manaus' then
        raise exception 'FALHOU: unidade editada: %', r;
    end if;

    -- Código repetido, código inválido, fuso inválido, nome vazio: P0001 com mensagem
    begin
        perform api.create_unit('org-teste-unidade', 'U1', 'Outra', 'America/Manaus');
        raise exception 'FALHOU: código repetido';
    exception when raise_exception then
        if sqlerrm not like 'Já existe uma unidade com o código U1%' then raise; end if;
    end;
    begin
        perform api.create_unit('org-teste-unidade', 'X', 'Curto', 'America/Manaus');
        raise exception 'FALHOU: código curto';
    exception when raise_exception then
        if sqlerrm not like 'Código inválido%' then raise; end if;
    end;
    begin
        perform api.create_unit('org-teste-unidade', 'U3', 'Fuso ruim', 'Marte/Olympus');
        raise exception 'FALHOU: fuso inválido';
    exception when raise_exception then
        if sqlerrm not like 'Fuso inválido%' then raise; end if;
    end;
    begin
        perform api.update_unit('org-teste-unidade', 'U1', '   ', 'America/Manaus');
        raise exception 'FALHOU: nome vazio';
    exception when raise_exception then
        if sqlerrm not like 'Informe o nome%' then raise; end if;
    end;
end $$;

-- Auditoria (lida como dono da tabela): 1 criação e 1 edição com antes/depois
reset role;
do $$
begin
    if (select count(*) from app.audit_log where org_id = '10000000-0000-4000-8000-000000000ab1' and action = 'unit.created') <> 1
       or (select metadata -> 'before' ->> 'name' from app.audit_log
           where org_id = '10000000-0000-4000-8000-000000000ab1' and action = 'unit.updated') <> 'Unidade 2' then
        raise exception 'FALHOU: auditoria';
    end if;
end $$;
set local role authenticated;

-- Gestor: vê a lista sem poder gerir; criar e editar = 42501
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ab2","role":"authenticated"}';
do $$
begin
    if (api.list_sources('org-teste-unidade') ->> 'canManageUnits')::boolean then
        raise exception 'FALHOU: Gestor não deveria gerir unidades';
    end if;
    begin
        perform api.create_unit('org-teste-unidade', 'U9', 'Nove', 'America/Manaus');
        raise exception 'FALHOU: Gestor criou unidade';
    exception when insufficient_privilege then null;
    end;
    begin
        perform api.update_unit('org-teste-unidade', 'U1', 'Renomeada', 'America/Manaus');
        raise exception 'FALHOU: Gestor editou unidade';
    exception when insufficient_privilege then null;
    end;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
