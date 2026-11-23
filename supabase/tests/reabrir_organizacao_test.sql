-- =============================================================================
-- Teste de 20261124110000_reabrir_organizacao.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: 'org-teste-reabrir' (U1, um membro, um evento) e 'org-teste-vencida' (encerrada há 31 dias);
-- p1 equipe RA (platform_staff); p2 Desenvolvedor do cliente.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-000000000be1', 'ra.reabrir@exemplo.com'),
       ('00000000-0000-4000-8000-000000000be2', 'dev.reabrir@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-000000000be1', 'org-teste-reabrir', 'Org Teste Reabrir'),
       ('10000000-0000-4000-8000-000000000be2', 'org-teste-vencida', 'Org Teste Vencida');
-- No CI a LexGroup não existe (só no Supabase): cria a dona da plataforma para o teste.
insert into app.organizations (slug, name, platform_owner) values ('lexgroup', 'LexGroup', true)
on conflict (slug) do nothing;
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-000000000be1', '10000000-0000-4000-8000-000000000be1', 'U1', 'Unidade 1', 'America/Manaus'),
       ('20000000-0000-4000-8000-000000000be2', '10000000-0000-4000-8000-000000000be2', 'V1', 'Vencida 1', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-000000000be2', '10000000-0000-4000-8000-000000000be1',
        '00000000-0000-4000-8000-000000000be2', 'Dev Reabrir', 'dev.reabrir@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-000000000be3', '10000000-0000-4000-8000-000000000be2',
        '00000000-0000-4000-8000-000000000be2', 'Dev Reabrir', 'dev.reabrir@exemplo.com', 'admin', 'active');
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
values ('10000000-0000-4000-8000-000000000be2', '00000000-0000-4000-8000-000000000be2', 'auth.login', 'session', 's', '{}');
update app.organizations set active = false, closed_at = now() - interval '31 days'
where id = '10000000-0000-4000-8000-000000000be2';

set local role authenticated;

-- Equipe RA: encerra, vê nas encerradas, reabre; a vencida não aparece nem reabre
set local request.jwt.claims =
    '{"sub":"00000000-0000-4000-8000-000000000be1","role":"authenticated","app_metadata":{"platform_staff":true}}';
do $$
declare
    c jsonb;
begin
    perform api.close_organization('org-teste-reabrir', 'Org Teste Reabrir');
    c := api.list_clients();
    if jsonb_array_length(c -> 'closed') <> 1 or c -> 'closed' -> 0 ->> 'slug' <> 'org-teste-reabrir'
       or c -> 'closed' -> 0 ->> 'closedBy' <> 'ra.reabrir@exemplo.com' then
        raise exception 'FALHOU: lista de encerradas (a vencida fica de fora): %', c -> 'closed';
    end if;

    begin
        perform api.reopen_organization('org-teste-vencida');
        raise exception 'FALHOU: reabriu depois de 30 dias';
    exception when raise_exception then
        if sqlerrm not like '%prazo de 30 dias%' then raise; end if;
    end;

    perform api.reopen_organization('ORG-TESTE-REABRIR');
    c := api.list_clients();
    if jsonb_array_length(c -> 'closed') <> 0
       or not exists (select 1 from jsonb_array_elements(c -> 'clients') x where x ->> 'slug' = 'org-teste-reabrir') then
        raise exception 'FALHOU: reaberta deveria voltar para os clientes: %', c;
    end if;
    begin
        perform api.reopen_organization('org-teste-reabrir');
        raise exception 'FALHOU: reabriu organização ativa';
    exception when raise_exception then
        if sqlerrm not like 'Organização encerrada não encontrada%' then raise; end if;
    end;
end $$;

-- Desenvolvedor do cliente: não reabre (é da plataforma) e volta a entrar na organização reaberta
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000be2","role":"authenticated"}';
do $$
begin
    begin
        perform api.reopen_organization('org-teste-vencida');
        raise exception 'FALHOU: Dev do cliente reabriu';
    exception when insufficient_privilege then null;
    end;
    if jsonb_array_length(api.list_sources('org-teste-reabrir') -> 'units') <> 1 then
        raise exception 'FALHOU: Dev deveria ver as unidades da organização reaberta';
    end if;
end $$;

-- Como dona: auditoria continua só inserção; a limpeza apaga a vencida inteira e deixa 'org.purged'
reset role;
do $$
declare
    n integer;
begin
    begin
        delete from app.audit_log where org_id = '10000000-0000-4000-8000-000000000be2';
        raise exception 'FALHOU: auditoria apagada fora da limpeza';
    exception when raise_exception then
        if sqlerrm not like '%somente inserção%' then raise; end if;
    end;
    begin
        perform set_config('app.audit_purge', 'on', true);
        set local role service_role;
        delete from app.audit_log where org_id = '10000000-0000-4000-8000-000000000be2';
        raise exception 'FALHOU: service_role apagou auditoria ligando a variável';
    exception when raise_exception then
        if sqlerrm not like '%somente inserção%' then raise; end if;
    end;
    reset role;
    perform set_config('app.audit_purge', 'off', true);

    n := app_private.purge_closed_orgs();
    if n <> 1 then raise exception 'FALHOU: deveria apagar só a vencida (%)', n; end if;
    if exists (select 1 from app.organizations where id = '10000000-0000-4000-8000-000000000be2')
       or exists (select 1 from app.units where id = '20000000-0000-4000-8000-000000000be2')
       or exists (select 1 from app.memberships where id = '40000000-0000-4000-8000-000000000be3')
       or exists (select 1 from app.audit_log where org_id = '10000000-0000-4000-8000-000000000be2') then
        raise exception 'FALHOU: organização vencida deveria sumir inteira';
    end if;
    if not exists (select 1 from app.audit_log where action = 'org.purged'
                   and target_id = '10000000-0000-4000-8000-000000000be2' and org_id = app_private.home_org_id()) then
        raise exception 'FALHOU: org.purged na auditoria da LexGroup';
    end if;
    if not exists (select 1 from app.organizations where id = '10000000-0000-4000-8000-000000000be1' and active) then
        raise exception 'FALHOU: a reaberta não pode ser apagada';
    end if;
    if not exists (select 1 from app.audit_log where action = 'org.reopened' and org_id = app_private.home_org_id()) then
        raise exception 'FALHOU: org.reopened na auditoria da LexGroup';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
