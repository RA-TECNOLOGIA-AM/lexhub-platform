-- =============================================================================
-- Teste de 20261124100000_restaurar_unidade.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-restaurar' com U1, U2 e U3 (desativada antes, sem deleted_at); g1 Desenvolvedor;
-- g2 Gestor de U1.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-000000000ad1', 'dev.restaurar@exemplo.com'),
       ('00000000-0000-4000-8000-000000000ad2', 'gestor.restaurar@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-000000000ad1', 'org-teste-restaurar', 'Org Teste Restaurar');
insert into app.units (id, org_id, code, name, timezone, active)
values ('20000000-0000-4000-8000-000000000ad1', '10000000-0000-4000-8000-000000000ad1', 'U1', 'Unidade 1', 'America/Manaus', true),
       ('20000000-0000-4000-8000-000000000ad2', '10000000-0000-4000-8000-000000000ad1', 'U2', 'Unidade 2', 'America/Manaus', true),
       ('20000000-0000-4000-8000-000000000ad3', '10000000-0000-4000-8000-000000000ad1', 'U3', 'Unidade 3', 'America/Manaus', false);
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-000000000ad1', '10000000-0000-4000-8000-000000000ad1',
        '00000000-0000-4000-8000-000000000ad1', 'Dev Restaurar', 'dev.restaurar@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-000000000ad2', '10000000-0000-4000-8000-000000000ad1',
        '00000000-0000-4000-8000-000000000ad2', 'Gestor', 'gestor.restaurar@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-000000000ad1', '20000000-0000-4000-8000-000000000ad1', '40000000-0000-4000-8000-000000000ad2', 'gestor'),
       ('10000000-0000-4000-8000-000000000ad1', '20000000-0000-4000-8000-000000000ad2', '40000000-0000-4000-8000-000000000ad2', 'gestor');

set local role authenticated;

-- Desenvolvedor: exclui U2, vê na lista de excluídas (com quem e quando), restaura
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ad1","role":"authenticated"}';
do $$
declare
    l jsonb;
    r jsonb;
begin
    perform api.delete_unit('org-teste-restaurar', 'U2', 'Unidade 2');
    l := api.list_sources('org-teste-restaurar');
    if jsonb_array_length(l -> 'deletedUnits') <> 1
       or l -> 'deletedUnits' -> 0 ->> 'code' <> 'U2'
       or l -> 'deletedUnits' -> 0 ->> 'deletedBy' <> 'Dev Restaurar'
       or (l -> 'deletedUnits' -> 0 ->> 'purgeAt') is null then
        raise exception 'FALHOU: U2 na lista de excluídas (U3 antiga não): %', l -> 'deletedUnits';
    end if;

    begin
        perform api.restore_unit('org-teste-restaurar', 'U3');
        raise exception 'FALHOU: restaurou unidade desativada antes (sem deleted_at)';
    exception when raise_exception then
        if sqlerrm not like 'Unidade excluída não encontrada%' then raise; end if;
    end;

    r := api.restore_unit('org-teste-restaurar', 'u2');
    if r -> 'unit' ->> 'code' <> 'U2' then raise exception 'FALHOU: retorno da restauração: %', r; end if;
    l := api.list_sources('org-teste-restaurar');
    if jsonb_array_length(l -> 'units') <> 2 or jsonb_array_length(l -> 'deletedUnits') <> 0 then
        raise exception 'FALHOU: U2 deveria voltar para a lista: %', l;
    end if;
    begin
        perform api.restore_unit('org-teste-restaurar', 'U2');
        raise exception 'FALHOU: restaurou unidade ativa';
    exception when raise_exception then
        if sqlerrm not like 'Unidade excluída não encontrada%' then raise; end if;
    end;

    -- Exclui de novo para os casos abaixo
    perform api.delete_unit('org-teste-restaurar', 'U2', 'Unidade 2');
end $$;

-- Gestor: não vê excluídas nem restaura
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ad2","role":"authenticated"}';
do $$
begin
    if jsonb_array_length(api.list_sources('org-teste-restaurar') -> 'deletedUnits') <> 0 then
        raise exception 'FALHOU: Gestor viu unidades excluídas';
    end if;
    begin
        perform api.restore_unit('org-teste-restaurar', 'U2');
        raise exception 'FALHOU: Gestor restaurou unidade';
    exception when insufficient_privilege then null;
    end;
end $$;

-- Prazo vencido (a limpeza ainda não rodou): some da lista e não restaura
reset role;
update app.units set deleted_at = now() - interval '31 days' where id = '20000000-0000-4000-8000-000000000ad2';
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ad1","role":"authenticated"}';
do $$
begin
    if jsonb_array_length(api.list_sources('org-teste-restaurar') -> 'deletedUnits') <> 0 then
        raise exception 'FALHOU: unidade vencida ainda na lista';
    end if;
    begin
        perform api.restore_unit('org-teste-restaurar', 'U2');
        raise exception 'FALHOU: restaurou depois de 30 dias';
    exception when raise_exception then
        if sqlerrm not like '%prazo de 30 dias%' then raise; end if;
    end;
end $$;

reset role;
do $$
begin
    if (select count(*) from app.audit_log where org_id = '10000000-0000-4000-8000-000000000ad1'
        and action = 'unit.restored') <> 1 then
        raise exception 'FALHOU: auditoria da restauração';
    end if;
    -- Os vínculos de membro voltam com a unidade (a exclusão não mexe neles)
    if not exists (select 1 from app.membership_units where unit_id = '20000000-0000-4000-8000-000000000ad2') then
        raise exception 'FALHOU: vínculo do membro deveria continuar';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
