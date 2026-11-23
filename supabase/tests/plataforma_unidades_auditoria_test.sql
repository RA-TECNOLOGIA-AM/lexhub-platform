-- =============================================================================
-- Teste de 20261123150000_plataforma_unidades_auditoria.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: cliente 'org-teste-plat' com U1 e U2; p1 Desenvolvedor do cliente; p2 equipe RA (platform_staff),
-- sem associação; 'org-teste-plat-fechada' encerrada, com um evento.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-000000000fa1', 'dev.plat@exemplo.com'),
       ('00000000-0000-4000-8000-000000000fa2', 'ra.plat@exemplo.com');
insert into app.organizations (id, slug, name, active)
values ('10000000-0000-4000-8000-000000000fa1', 'org-teste-plat', 'Org Teste Plat', true),
       ('10000000-0000-4000-8000-000000000fa2', 'org-teste-plat-fechada', 'Org Teste Fechada', false);
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-000000000fa1', '10000000-0000-4000-8000-000000000fa1', 'U1', 'Unidade 1', 'America/Manaus'),
       ('20000000-0000-4000-8000-000000000fa2', '10000000-0000-4000-8000-000000000fa1', 'U2', 'Unidade 2', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-000000000fa1', '10000000-0000-4000-8000-000000000fa1',
        '00000000-0000-4000-8000-000000000fa1', 'Dev Plat', 'dev.plat@exemplo.com', 'admin', 'active');
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
values ('10000000-0000-4000-8000-000000000fa1', '00000000-0000-4000-8000-000000000fa1', 'dashboard.view',
        'dashboard', 'x', '{"unit": "U1"}'),
       ('10000000-0000-4000-8000-000000000fa1', '00000000-0000-4000-8000-000000000fa1', 'dashboard.view',
        'dashboard', 'x', '{"unit": "U2"}'),
       ('10000000-0000-4000-8000-000000000fa1', '00000000-0000-4000-8000-000000000fa1', 'member.invited',
        'invitation', 'y', '{"units": ["U1"]}'),
       ('10000000-0000-4000-8000-000000000fa1', '00000000-0000-4000-8000-000000000fa1', 'auth.login',
        'session', 'z', '{}'),
       ('10000000-0000-4000-8000-000000000fa2', null, 'import.v1', 'organization', 'w', '{"units": 1}');

set local role authenticated;

-- Desenvolvedor do cliente: filtro de unidade, sem lista de organizações, não audita outra organização
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000fa1","role":"authenticated"}';
do $$
declare
    r jsonb;
begin
    r := api.list_audit('org-teste-plat');
    if jsonb_array_length(r -> 'events') <> 4 or r -> 'orgs' <> 'null'::jsonb
       or jsonb_array_length(r -> 'units') <> 2 then
        raise exception 'FALHOU: auditoria do Dev do cliente: %', r;
    end if;
    r := api.list_audit('org-teste-plat', p_unit => 'u1');
    if jsonb_array_length(r -> 'events') <> 2 then
        raise exception 'FALHOU: filtro U1 (dashboard + convite): %', r -> 'events';
    end if;
    begin
        perform api.list_audit('org-teste-plat-fechada');
        raise exception 'FALHOU: Dev do cliente auditou outra organização';
    exception when insufficient_privilege then null;
    end;
end $$;

-- Plataforma, sem ser membro: vê e gere as unidades, audita qualquer organização (encerrada também)
set local request.jwt.claims =
    '{"sub":"00000000-0000-4000-8000-000000000fa2","role":"authenticated","app_metadata":{"platform_staff":true}}';
do $$
declare
    l jsonb;
    r jsonb;
begin
    l := api.list_sources('org-teste-plat');
    if jsonb_array_length(l -> 'units') <> 2 or not (l ->> 'canManageUnits')::boolean then
        raise exception 'FALHOU: plataforma deveria ver e gerir as unidades: %', l;
    end if;
    perform api.create_unit('org-teste-plat', 'U3', 'Unidade 3', 'America/Manaus');
    perform api.update_unit('org-teste-plat', 'U3', 'Unidade Três', 'America/Manaus');
    perform api.delete_unit('org-teste-plat', 'U2', 'Unidade 2');

    r := api.list_audit('org-teste-plat', p_actions => '{unit.created,unit.updated,unit.deleted}');
    if jsonb_array_length(r -> 'events') <> 3
       or exists (select 1 from jsonb_array_elements(r -> 'events') e where e ->> 'actor' <> 'ra.plat@exemplo.com') then
        raise exception 'FALHOU: ações da plataforma na auditoria do cliente, pelo e-mail: %', r -> 'events';
    end if;
    -- A unidade excluída continua no filtro (marcada) e acha os eventos dela.
    if not exists (select 1 from jsonb_array_elements(r -> 'units') u
                   where u ->> 'code' = 'U2' and (u ->> 'deleted')::boolean) then
        raise exception 'FALHOU: U2 excluída deveria aparecer no filtro: %', r -> 'units';
    end if;
    r := api.list_audit('org-teste-plat', p_unit => 'U2');
    if jsonb_array_length(r -> 'events') <> 2 then
        raise exception 'FALHOU: eventos da U2 (abertura + exclusão): %', r -> 'events';
    end if;

    r := api.list_audit('org-teste-plat-fechada');
    if jsonb_array_length(r -> 'events') <> 1
       or not exists (select 1 from jsonb_array_elements(r -> 'orgs') o
                      where o ->> 'slug' = 'org-teste-plat-fechada' and (o ->> 'closed')::boolean) then
        raise exception 'FALHOU: plataforma audita organização encerrada: %', r;
    end if;
    perform api.log_audit_export('org-teste-plat-fechada', '', '', 1, 'u1');
    begin
        perform api.list_sources('org-teste-plat-fechada');
        raise exception 'FALHOU: unidades de organização encerrada';
    exception when insufficient_privilege then null;
    end;
end $$;

reset role;
do $$
begin
    if (select metadata ->> 'unit' from app.audit_log
        where org_id = '10000000-0000-4000-8000-000000000fa2' and action = 'audit.export') is distinct from 'U1' then
        raise exception 'FALHOU: exportação registrada na organização auditada, com a unidade';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
