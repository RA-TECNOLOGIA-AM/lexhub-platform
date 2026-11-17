-- =============================================================================
-- Teste de 20261117100000_conectar_fonte.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Roda num banco vazio (CI) ou no staging: garante a organização 'lexgroup' (a casa), as fontes lexflow e
-- ng dela e uma unidade com o LexFlow 'RJ', criando só o que faltar (tudo desfeito no fim).
-- Cenário: cliente 'org-teste-fonte' com C1 e C2; t1 Dev da LexGroup; t2 Owner do cliente.
-- =============================================================================

begin;

insert into app.organizations (slug, name) values ('lexgroup', 'LexGroup') on conflict (slug) do nothing;
insert into app.data_sources (org_id, key, kind, name, connector)
values (app_private.home_org_id(), 'lexflow', 'flow', 'LexFlow', 'lexflow'),
       (app_private.home_org_id(), 'ng', 'database', 'Sistema jurídico NG', 'internal')
on conflict (org_id, key) do nothing;
-- O escritório 27 do LexFlow é guardado como 'RJ'; no staging ele já é da unidade RJ (o índice barra o repetido).
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000fe004', app_private.home_org_id(), 'TSTRJ', 'Teste RJ', 'America/Manaus');
insert into app.unit_source_refs (unit_id, source, ref)
values ('20000000-0000-4000-8000-0000000fe004', 'lexflow', 'RJ')
on conflict do nothing;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000fe001', 'ti.fonte@exemplo.com'),
       ('00000000-0000-4000-8000-0000000fe002', 'owner.cliente@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000fe001', 'org-teste-fonte', 'Cliente Teste Fonte');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000fe001', '10000000-0000-4000-8000-0000000fe001', 'C1', 'Cliente 1', 'America/Manaus'),
       ('20000000-0000-4000-8000-0000000fe002', '10000000-0000-4000-8000-0000000fe001', 'C2', 'Cliente 2', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000fe001', app_private.home_org_id(),
        '00000000-0000-4000-8000-0000000fe001', 'TI', 'ti.fonte@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000fe002', '10000000-0000-4000-8000-0000000fe001',
        '00000000-0000-4000-8000-0000000fe002', 'Owner Cliente', 'owner.cliente@exemplo.com', 'owner', 'active');

-- Quem gerencia: só Owner/Dev da LexGroup
do $$
begin
    if not app_private.is_source_admin('00000000-0000-4000-8000-0000000fe001') then
        raise exception 'FALHOU: Dev da LexGroup deveria gerenciar fontes';
    end if;
    if app_private.is_source_admin('00000000-0000-4000-8000-0000000fe002') then
        raise exception 'FALHOU: Owner do cliente não deveria gerenciar fontes';
    end if;
    if app_private.is_source_admin(null) then
        raise exception 'FALHOU: sem usuário não gerencia';
    end if;
end $$;

-- Os produtos têm o connector deles (a migration preencheu as fontes que já existiam)
do $$
begin
    if exists (select 1 from app.data_sources where key in ('lexpre', 'lexflow') and connector <> key) then
        raise exception 'FALHOU: connector dos produtos';
    end if;
end $$;

set local role authenticated;

-- Owner do cliente: vê a lista, mas não gerencia e não liga escritório
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fe002","role":"authenticated"}';
do $$
begin
    if (api.list_sources('org-teste-fonte') ->> 'canManageSources')::boolean then
        raise exception 'FALHOU: Owner do cliente não deveria ver canManageSources';
    end if;
    begin
        perform api.link_product_office('org-teste-fonte', 'C1', 'lexpre', '9001');
        raise exception 'FALHOU: Owner do cliente ligou escritório';
    exception when insufficient_privilege then null;
    end;
    begin
        perform app_private.is_source_admin('00000000-0000-4000-8000-0000000fe002');
        raise exception 'FALHOU: authenticated chamou is_source_admin direto';
    exception when insufficient_privilege then null;
    end;
end $$;

-- TI da LexGroup: liga e desliga escritórios na organização do cliente
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fe001","role":"authenticated"}';
do $$
declare
    r jsonb;
begin
    r := api.link_product_office('org-teste-fonte', 'c1', 'lexpre', ' 9001 ');
    if r -> 'unit' ->> 'code' <> 'C1' or jsonb_array_length(r -> 'sources') <> 1
       or r -> 'sources' -> 0 ->> 'id' <> 'lexpre'
       or r -> 'sources' -> 0 ->> 'connector' <> 'lexpre'
       or r -> 'sources' -> 0 ->> 'status' <> 'no_dashboards' then
        raise exception 'FALHOU: ligar LexPre: %', r;
    end if;

    -- A mesma unidade de novo, o mesmo escritório em outra unidade, ref inválida, produto inválido
    begin
        perform api.link_product_office('org-teste-fonte', 'C1', 'lexpre', '9002');
        raise exception 'FALHOU: unidade ligada duas vezes ao LexPre';
    exception when raise_exception then
        if sqlerrm not like 'Esta unidade já está ligada ao LexPre%' then raise; end if;
    end;
    begin
        perform api.link_product_office('org-teste-fonte', 'C2', 'lexpre', '9001');
        raise exception 'FALHOU: escritório em duas unidades';
    exception when raise_exception then
        if sqlerrm not like 'Este escritório já está ligado à unidade Cliente Teste Fonte · C1%' then raise; end if;
    end;
    begin
        perform api.link_product_office('org-teste-fonte', 'C2', 'lexpre', 'abc');
        raise exception 'FALHOU: ref inválida';
    exception when raise_exception then
        if sqlerrm not like 'Escolha um escritório%' then raise; end if;
    end;
    begin
        perform api.link_product_office('org-teste-fonte', 'C2', 'ng', '1');
        raise exception 'FALHOU: banco interno pela tela';
    exception when raise_exception then
        if sqlerrm not like 'Produto inválido%' then raise; end if;
    end;

    -- LexFlow 27 = escritório do RJ da LexGroup (guardado como 'RJ'): barrado pelo índice
    begin
        perform api.link_product_office('org-teste-fonte', 'C2', 'lexflow', '27');
        raise exception 'FALHOU: LexFlow 27 já é do RJ';
    exception when raise_exception then
        if sqlerrm not like 'Este escritório já está ligado à unidade %RJ%' then raise; end if;
    end;
    r := api.link_product_office('org-teste-fonte', 'C2', 'lexflow', '9003');
    if r -> 'sources' -> 0 ->> 'id' <> 'lexflow' then
        raise exception 'FALHOU: ligar LexFlow: %', r;
    end if;

    r := api.unlink_product_office('org-teste-fonte', 'C1', 'lexpre');
    if r -> 'sources' <> '[]'::jsonb then
        raise exception 'FALHOU: desligar LexPre: %', r;
    end if;
    begin
        perform api.unlink_product_office('org-teste-fonte', 'C1', 'lexpre');
        raise exception 'FALHOU: desligou duas vezes';
    exception when raise_exception then
        if sqlerrm not like 'Esta unidade não está ligada%' then raise; end if;
    end;
end $$;

-- Lido como dono das tabelas: auditoria, fonte criada no cliente e as travas da tabela
reset role;
do $$
begin
    if (select count(*) from app.audit_log
        where org_id = '10000000-0000-4000-8000-0000000fe001'
          and action in ('source.office_linked', 'source.office_unlinked')) <> 3 then
        raise exception 'FALHOU: auditoria (2 ligações + 1 desligamento)';
    end if;
    if not exists (select 1 from app.data_sources
                   where org_id = '10000000-0000-4000-8000-0000000fe001' and key = 'lexpre'
                     and connector = 'lexpre' and owner_unit_id is null) then
        raise exception 'FALHOU: fonte LexPre criada na organização do cliente';
    end if;

    -- Fonte de outra organização (o banco ng é da LexGroup): recusado
    begin
        insert into app.unit_source_refs (unit_id, source, ref)
        values ('20000000-0000-4000-8000-0000000fe001', 'ng', 'NG');
        raise exception 'FALHOU: cliente ligado ao banco NG';
    exception when insufficient_privilege then
        if sqlerrm not like 'Esta fonte não é da organização%' then raise; end if;
    end;

    -- Unidade nova da LexGroup também fica fora do banco interno até ser liberada
    insert into app.units (id, org_id, code, name, timezone)
    values ('20000000-0000-4000-8000-0000000fe003', app_private.home_org_id(), 'TSTFONTE', 'Teste', 'America/Manaus');
    begin
        insert into app.unit_source_refs (unit_id, source, ref)
        values ('20000000-0000-4000-8000-0000000fe003', 'ng', 'NG');
        raise exception 'FALHOU: unidade nova da LexGroup ligada ao banco NG';
    exception when insufficient_privilege then
        if sqlerrm not like 'Banco interno não liberado%' then raise; end if;
    end;

    -- Senha nunca no config
    begin
        update app.data_sources set config = '{"password": "x"}'
        where org_id = '10000000-0000-4000-8000-0000000fe001' and key = 'lexpre';
        raise exception 'FALHOU: senha gravada no config';
    exception when check_violation then null;
    end;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
