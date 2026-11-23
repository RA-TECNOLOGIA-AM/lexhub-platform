-- =============================================================================
-- Teste de 20261123140000_excluir_unidade_organizacao.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-excluir' com U1, U2 (com fonte própria) e U3 travada; g1 Desenvolvedor;
-- g2 Gestor de U1; g3 equipe RA (platform_staff). A dona da plataforma é a org 'lexgroup' das migrations.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-000000000ec1', 'dev.excluir@exemplo.com'),
       ('00000000-0000-4000-8000-000000000ec2', 'gestor.excluir@exemplo.com'),
       ('00000000-0000-4000-8000-000000000ec3', 'ra.excluir@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-000000000ec1', 'org-teste-excluir', 'Org Teste Excluir');
-- No CI a LexGroup não existe (só no Supabase): cria a dona da plataforma para o teste.
insert into app.organizations (slug, name, platform_owner) values ('lexgroup', 'LexGroup', true)
on conflict (slug) do nothing;
insert into app.units (id, org_id, code, name, timezone, deletion_locked)
values ('20000000-0000-4000-8000-000000000ec1', '10000000-0000-4000-8000-000000000ec1', 'U1', 'Unidade 1', 'America/Manaus', false),
       ('20000000-0000-4000-8000-000000000ec2', '10000000-0000-4000-8000-000000000ec1', 'U2', 'Unidade 2', 'America/Manaus', false),
       ('20000000-0000-4000-8000-000000000ec3', '10000000-0000-4000-8000-000000000ec1', 'U3', 'Unidade 3', 'America/Manaus', true);
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-000000000ec1', '10000000-0000-4000-8000-000000000ec1',
        '00000000-0000-4000-8000-000000000ec1', 'Dev', 'dev.excluir@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-000000000ec2', '10000000-0000-4000-8000-000000000ec1',
        '00000000-0000-4000-8000-000000000ec2', 'Gestor', 'gestor.excluir@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-000000000ec1', '20000000-0000-4000-8000-000000000ec1', '40000000-0000-4000-8000-000000000ec2', 'gestor'),
       ('10000000-0000-4000-8000-000000000ec1', '20000000-0000-4000-8000-000000000ec2', '40000000-0000-4000-8000-000000000ec2', 'gestor');
-- Fonte só da U2 (planilha) e a ref dela
insert into app.data_sources (id, org_id, key, kind, name, owner_unit_id, connector)
values ('30000000-0000-4000-8000-000000000ec2', '10000000-0000-4000-8000-000000000ec1', 'planilha_u2_teste', 'sheet',
        'Planilha U2', '20000000-0000-4000-8000-000000000ec2', 'sheets');
insert into app.unit_source_refs (unit_id, source, ref)
values ('20000000-0000-4000-8000-000000000ec2', 'planilha_u2_teste', 'planilha_u2_teste');

-- As travas da LexGroup vieram da migration
do $$
begin
    if exists (select 1 from app.units u join app.organizations o on o.id = u.org_id
               where o.platform_owner and u.code in ('NG', 'LA', 'RJ') and not u.deletion_locked) then
        raise exception 'FALHOU: NG/LA/RJ da LexGroup deveriam estar travadas';
    end if;
end $$;

set local role authenticated;

-- Gestor: não vê o impacto nem exclui (42501)
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ec2","role":"authenticated"}';
do $$
begin
    begin
        perform api.unit_deletion_impact('org-teste-excluir', 'U2');
        raise exception 'FALHOU: Gestor viu o impacto';
    exception when insufficient_privilege then null;
    end;
    begin
        perform api.delete_unit('org-teste-excluir', 'U2', 'Unidade 2');
        raise exception 'FALHOU: Gestor excluiu unidade';
    exception when insufficient_privilege then null;
    end;
    begin
        perform api.close_organization('org-teste-excluir', 'Org Teste Excluir');
        raise exception 'FALHOU: Gestor encerrou organização';
    exception when insufficient_privilege then null;
    end;
end $$;

-- Desenvolvedor: impacto, nome errado, trava, exclui U2, última unidade
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ec1","role":"authenticated"}';
do $$
declare
    i jsonb;
    l jsonb;
begin
    if api.list_sources('org-teste-excluir') ->> 'orgName' <> 'Org Teste Excluir' then
        raise exception 'FALHOU: orgName na lista de fontes';
    end if;

    i := api.unit_deletion_impact('org-teste-excluir', 'u2');
    if (i ->> 'sources')::int <> 1 or (i ->> 'members')::int <> 1 or (i ->> 'locked')::boolean
       or (i ->> 'lastUnit')::boolean then
        raise exception 'FALHOU: impacto da U2: %', i;
    end if;
    if not (api.unit_deletion_impact('org-teste-excluir', 'U3') ->> 'locked')::boolean then
        raise exception 'FALHOU: U3 deveria aparecer travada';
    end if;

    begin
        perform api.delete_unit('org-teste-excluir', 'U2', 'Outra coisa');
        raise exception 'FALHOU: excluiu com nome errado';
    exception when raise_exception then
        if sqlerrm not like 'Digite o nome da unidade%' then raise; end if;
    end;
    begin
        perform api.delete_unit('org-teste-excluir', 'U3', 'Unidade 3');
        raise exception 'FALHOU: excluiu unidade travada';
    exception when raise_exception then
        if sqlerrm not like '%não pode ser excluída%' then raise; end if;
    end;

    perform api.delete_unit('org-teste-excluir', 'U2', '  unidade 2 ');
    l := api.list_sources('org-teste-excluir');
    if jsonb_array_length(l -> 'units') <> 2 or l::text like '%"U2"%' then
        raise exception 'FALHOU: U2 deveria sumir da lista: %', l;
    end if;
    begin
        perform api.unit_deletion_impact('org-teste-excluir', 'U2');
        raise exception 'FALHOU: U2 arquivada ainda acha impacto';
    exception when raise_exception then
        if sqlerrm not like 'Unidade não encontrada%' then raise; end if;
    end;

    -- Sobra U1 + U3 (travada). Destrava U3 de mentira não dá pela api; exclui U1 e a U3 vira a última.
    perform api.delete_unit('org-teste-excluir', 'U1', 'Unidade 1');
    if not (api.unit_deletion_impact('org-teste-excluir', 'U3') ->> 'lastUnit')::boolean then
        raise exception 'FALHOU: U3 deveria ser a última';
    end if;
end $$;

-- Como dono da tabela: senha/fonte da U2 apagada na hora, unidade arquivada, auditoria, limpeza de 30 dias
reset role;
do $$
declare
    n integer;
begin
    if exists (select 1 from app.data_sources where id = '30000000-0000-4000-8000-000000000ec2')
       or exists (select 1 from app.unit_source_refs where unit_id = '20000000-0000-4000-8000-000000000ec2') then
        raise exception 'FALHOU: fonte da U2 deveria sair na hora';
    end if;
    if (select active or deleted_at is null or deleted_by is null from app.units
        where id = '20000000-0000-4000-8000-000000000ec2') then
        raise exception 'FALHOU: U2 deveria estar arquivada';
    end if;
    if (select count(*) from app.audit_log where org_id = '10000000-0000-4000-8000-000000000ec1'
        and action = 'unit.deleted') <> 2 then
        raise exception 'FALHOU: auditoria da exclusão';
    end if;
    if exists (select 1 from app.memberships where id = '40000000-0000-4000-8000-000000000ec2') is not true then
        raise exception 'FALHOU: o membro continua na organização';
    end if;

    -- Antes de 30 dias nada sai; depois, sai (e a travada nunca)
    if app_private.purge_deleted_units() <> 0 then raise exception 'FALHOU: limpou antes de 30 dias'; end if;
    update app.units set deleted_at = now() - interval '31 days'
    where id in ('20000000-0000-4000-8000-000000000ec1', '20000000-0000-4000-8000-000000000ec2');
    n := app_private.purge_deleted_units();
    if n <> 2 or exists (select 1 from app.units where id = '20000000-0000-4000-8000-000000000ec2') then
        raise exception 'FALHOU: limpeza de 30 dias (%)', n;
    end if;
    begin
        delete from app.units where id = '20000000-0000-4000-8000-000000000ec3';
        raise exception 'FALHOU: delete direto de unidade travada';
    exception when raise_exception then
        if sqlerrm not like '%não pode ser excluída%' then raise; end if;
    end;
end $$;
set local role authenticated;

-- Encerrar organização: Dev da organização não pode; equipe RA pode; a dona da plataforma nunca
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ec1","role":"authenticated"}';
do $$
begin
    begin
        perform api.org_closure_impact('org-teste-excluir');
        raise exception 'FALHOU: Dev de cliente viu o impacto do encerramento';
    exception when insufficient_privilege then null;
    end;
end $$;

set local request.jwt.claims =
    '{"sub":"00000000-0000-4000-8000-000000000ec3","role":"authenticated","app_metadata":{"platform_staff":true}}';
do $$
declare
    i jsonb;
    c jsonb;
begin
    c := api.list_clients();
    if not exists (select 1 from jsonb_array_elements(c -> 'clients') x
                   where x ->> 'slug' = 'org-teste-excluir' and (x ->> 'canClose')::boolean
                     and jsonb_array_length(x -> 'units') = 1) then
        raise exception 'FALHOU: cliente com unidades e canClose: %', c;
    end if;
    if exists (select 1 from jsonb_array_elements(c -> 'clients') x
               where x ->> 'slug' = 'lexgroup' and (x ->> 'canClose')::boolean) then
        raise exception 'FALHOU: LexGroup não pode aparecer como encerrável';
    end if;

    i := api.org_closure_impact('org-teste-excluir');
    if (i ->> 'units')::int <> 1 or (i ->> 'members')::int <> 2 then
        raise exception 'FALHOU: impacto do encerramento: %', i;
    end if;
    begin
        perform api.close_organization('org-teste-excluir', 'errado');
        raise exception 'FALHOU: encerrou com nome errado';
    exception when raise_exception then
        if sqlerrm not like 'Digite o nome da organização%' then raise; end if;
    end;
    begin
        perform api.close_organization('lexgroup', 'LexGroup');
        raise exception 'FALHOU: encerrou a dona da plataforma';
    exception when raise_exception then
        if sqlerrm not like '%dona da plataforma%' then raise; end if;
    end;

    perform api.close_organization('org-teste-excluir', 'org teste excluir');
    c := api.list_clients();
    if exists (select 1 from jsonb_array_elements(c -> 'clients') x where x ->> 'slug' = 'org-teste-excluir') then
        raise exception 'FALHOU: organização encerrada ainda na lista';
    end if;
end $$;

reset role;
do $$
begin
    if (select active or closed_at is null from app.organizations where slug = 'org-teste-excluir') then
        raise exception 'FALHOU: organização deveria estar encerrada';
    end if;
    if not exists (select 1 from app.audit_log where action = 'org.closed'
                   and target_id = '10000000-0000-4000-8000-000000000ec1'
                   and org_id = app_private.home_org_id()) then
        raise exception 'FALHOU: auditoria do encerramento na LexGroup';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
