-- =============================================================================
-- Teste de 20261113230000_auditoria.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-audit' com U1; h1 Desenvolvedor; h2 Gestor de U1.
--   Eventos: exportação feita por h1 (alvo = dashboard), edição de U1 feita por h1, importação sem pessoa,
--   e um evento de OUTRA organização (não pode aparecer).
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-000000000ac1', 'dev.audit@exemplo.com'),
       ('00000000-0000-4000-8000-000000000ac2', 'gestor.audit@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-000000000ac1', 'org-teste-audit', 'Org Teste Audit'),
       ('10000000-0000-4000-8000-000000000ac2', 'org-teste-audit-2', 'Outra Org');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-000000000ac1', '10000000-0000-4000-8000-000000000ac1', 'U1', 'Unidade 1');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-000000000ac1', '10000000-0000-4000-8000-000000000ac1',
        '00000000-0000-4000-8000-000000000ac1', 'Dev Audit', 'dev.audit@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-000000000ac2', '10000000-0000-4000-8000-000000000ac1',
        '00000000-0000-4000-8000-000000000ac2', 'Gestor Audit', 'gestor.audit@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-000000000ac1', '20000000-0000-4000-8000-000000000ac1', '40000000-0000-4000-8000-000000000ac2', 'gestor');

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values ('dash-teste-audit', 'Dashboard Audit', '', 'Teste', 'LexPre', 1, 'available');
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata, created_at)
values ('10000000-0000-4000-8000-000000000ac1', null, 'import.v1', 'organization', null,
        '{"members": 2, "units": 1}', now() - interval '3 days'),
       ('10000000-0000-4000-8000-000000000ac1', '00000000-0000-4000-8000-000000000ac1', 'dashboard.export', 'dashboard',
        'dash-teste-audit', '{"unit": "U1", "rows": 88, "format": "xlsx"}', now() - interval '2 hours'),
       ('10000000-0000-4000-8000-000000000ac1', '00000000-0000-4000-8000-000000000ac1', 'unit.updated', 'unit',
        '20000000-0000-4000-8000-000000000ac1', '{"code": "U1"}', now() - interval '1 hour'),
       ('10000000-0000-4000-8000-000000000ac2', '00000000-0000-4000-8000-000000000ac1', 'unit.updated', 'unit',
        null, '{}', now());

set local role authenticated;

-- Desenvolvedor: os 3 eventos da org, mais recente primeiro, com nome de quem fez e do alvo
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ac1","role":"authenticated"}';
do $$
declare e jsonb := api.list_audit('org-teste-audit') -> 'events';
begin
    if jsonb_array_length(e) <> 3 then raise exception 'FALHOU: deveria ver 3 eventos: %', e; end if;
    if e -> 0 ->> 'action' <> 'unit.updated' or e -> 0 ->> 'targetName' <> 'Unidade 1' or e -> 0 ->> 'actor' <> 'Dev Audit' then
        raise exception 'FALHOU: primeiro evento: %', e -> 0;
    end if;
    if e -> 1 ->> 'targetName' <> 'Dashboard Audit' or (e -> 1 -> 'metadata' ->> 'rows')::int <> 88 then
        raise exception 'FALHOU: exportação: %', e -> 1;
    end if;
    if e -> 2 ->> 'actor' <> 'Sistema' then raise exception 'FALHOU: evento sem pessoa = Sistema: %', e -> 2; end if;
    if jsonb_array_length(api.list_audit('org-teste-audit', 1) -> 'events') <> 1 then
        raise exception 'FALHOU: limite';
    end if;
    if (api.my_admin_permissions('org-teste-audit') ->> 'audit')::boolean is not true then
        raise exception 'FALHOU: menu do Dev deveria mostrar auditoria';
    end if;
end $$;

-- Gestor: recusado e sem o item no menu
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-000000000ac2","role":"authenticated"}';
do $$
begin
    begin
        perform api.list_audit('org-teste-audit');
        raise exception 'FALHOU: Gestor não deveria ver a auditoria';
    exception when insufficient_privilege then null;
    end;
    if (api.my_admin_permissions('org-teste-audit') ->> 'audit')::boolean then
        raise exception 'FALHOU: menu do Gestor não deveria mostrar auditoria';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
