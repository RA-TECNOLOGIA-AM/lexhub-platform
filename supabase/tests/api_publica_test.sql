-- =============================================================================
-- Teste de 20261126230000_api_publica.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR. Falhou = ERROR 'FALHOU: ...'.
--
-- Cenário: org 'org-teste-api' com U1 e U2. Setores: Comercial (U1 e U2) e Protocolo (U1).
-- Regras: Comercial -> d-com (U1 e U2) e d-off (desligado em U1); Protocolo -> d-prot (U1).
--   o1 = Owner (sem setor) · d1 = Desenvolvedor · g1 = Gestor em U1, setor Comercial U1 · c1 = colaborador U1
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000a7001', 'owner.api@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000a7002', 'dev.api@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000a7003', 'gestor.api@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000a7004', 'colab.api@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000a7001', 'org-teste-api', 'Org Teste API');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000a7001', '10000000-0000-4000-8000-0000000a7001', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000a7002', '10000000-0000-4000-8000-0000000a7001', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name)
values ('30000000-0000-4000-8000-0000000a7001', '10000000-0000-4000-8000-0000000a7001',
        '20000000-0000-4000-8000-0000000a7001', 'Comercial'),
       ('30000000-0000-4000-8000-0000000a7002', '10000000-0000-4000-8000-0000000a7001',
        '20000000-0000-4000-8000-0000000a7002', 'Comercial'),
       ('30000000-0000-4000-8000-0000000a7003', '10000000-0000-4000-8000-0000000a7001',
        '20000000-0000-4000-8000-0000000a7001', 'Protocolo');

insert into app.dashboard_catalog (key, name, area, active, sort_order, status)
values ('d-com', 'Dash Comercial', 'Comercial', true, 1, 'available'),
       ('d-prot', 'Dash Protocolo', 'Comercial', true, 2, 'available'),
       ('d-off', 'Dash Desligado', 'Comercial', true, 3, 'available');
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
values ('10000000-0000-4000-8000-0000000a7001', '20000000-0000-4000-8000-0000000a7001', 'd-com', true),
       ('10000000-0000-4000-8000-0000000a7001', '20000000-0000-4000-8000-0000000a7002', 'd-com', true),
       ('10000000-0000-4000-8000-0000000a7001', '20000000-0000-4000-8000-0000000a7001', 'd-prot', true),
       ('10000000-0000-4000-8000-0000000a7001', '20000000-0000-4000-8000-0000000a7001', 'd-off', false);
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
values ('10000000-0000-4000-8000-0000000a7001', '30000000-0000-4000-8000-0000000a7001', 'd-com', 'all'),
       ('10000000-0000-4000-8000-0000000a7001', '30000000-0000-4000-8000-0000000a7002', 'd-com', 'all'),
       ('10000000-0000-4000-8000-0000000a7001', '30000000-0000-4000-8000-0000000a7001', 'd-off', 'all'),
       ('10000000-0000-4000-8000-0000000a7001', '30000000-0000-4000-8000-0000000a7003', 'd-prot', 'all');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000a7001', '10000000-0000-4000-8000-0000000a7001',
        '00000000-0000-4000-8000-0000000a7001', 'Owner API', 'owner.api@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000a7002', '10000000-0000-4000-8000-0000000a7001',
        '00000000-0000-4000-8000-0000000a7002', 'Dev API', 'dev.api@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000a7003', '10000000-0000-4000-8000-0000000a7001',
        '00000000-0000-4000-8000-0000000a7003', 'Gestor API', 'gestor.api@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000a7004', '10000000-0000-4000-8000-0000000a7001',
        '00000000-0000-4000-8000-0000000a7004', 'Colab API', 'colab.api@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000a7001', '20000000-0000-4000-8000-0000000a7001',
        '40000000-0000-4000-8000-0000000a7003', 'gestor'),
       ('10000000-0000-4000-8000-0000000a7001', '20000000-0000-4000-8000-0000000a7001',
        '40000000-0000-4000-8000-0000000a7004', 'colaborador');
insert into app.membership_teams (org_id, team_id, membership_id)
values ('10000000-0000-4000-8000-0000000a7001', '30000000-0000-4000-8000-0000000a7001',
        '40000000-0000-4000-8000-0000000a7003'),
       ('10000000-0000-4000-8000-0000000a7001', '30000000-0000-4000-8000-0000000a7001',
        '40000000-0000-4000-8000-0000000a7004');

-- Elegibilidade
do $$
begin
    if not app_private.api_key_eligible('00000000-0000-4000-8000-0000000a7003', '10000000-0000-4000-8000-0000000a7001')
       or not app_private.api_key_eligible('00000000-0000-4000-8000-0000000a7001', '10000000-0000-4000-8000-0000000a7001')
       or not app_private.api_key_eligible('00000000-0000-4000-8000-0000000a7002', '10000000-0000-4000-8000-0000000a7001') then
        raise exception 'FALHOU: Gestor, Owner e Desenvolvedor deveriam poder pedir';
    end if;
    if app_private.api_key_eligible('00000000-0000-4000-8000-0000000a7004', '10000000-0000-4000-8000-0000000a7001') then
        raise exception 'FALHOU: Colaborador não deveria poder pedir';
    end if;
end;
$$;

set local role authenticated;

-- Gestor: elegibilidade, validações e pedido com extra Protocolo
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000a7003","role":"authenticated"}';
do $$
declare
    v jsonb := api.api_key_eligibility('org-teste-api');
begin
    if not (v ->> 'eligible')::boolean or v -> 'base_sectors' <> '["Comercial"]'::jsonb
       or not (v -> 'sectors') @> '["Comercial", "Protocolo"]'::jsonb then
        raise exception 'FALHOU: elegibilidade do Gestor: %', v;
    end if;
    begin
        perform api.request_api_key('org-teste-api', null,
            jsonb_build_array(jsonb_build_object('setor', 'Protocolo', 'justificativa', 'curta',
                                                 'validade', current_date + 30)));
        raise exception 'FALHOU: justificativa curta deveria falhar';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
    begin
        perform api.request_api_key('org-teste-api', null,
            jsonb_build_array(jsonb_build_object('setor', 'Protocolo', 'justificativa', 'Automação de metas do mês',
                                                 'validade', current_date + 366)));
        raise exception 'FALHOU: validade > 365 dias deveria falhar';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
    begin
        perform api.request_api_key('org-teste-api', null,
            jsonb_build_array(jsonb_build_object('setor', 'Comercial', 'justificativa', 'Automação de metas do mês',
                                                 'validade', current_date + 30)));
        raise exception 'FALHOU: setor base como extra deveria falhar';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
    perform api.request_api_key('org-teste-api', 'Power BI do Comercial',
        jsonb_build_array(jsonb_build_object('setor', 'Protocolo', 'justificativa', 'Automação de metas do mês',
                                             'validade', current_date + 30)));
    begin
        perform api.request_api_key('org-teste-api', null, '[]'::jsonb);
        raise exception 'FALHOU: segundo pedido deveria falhar';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
    begin
        perform api.list_api_keys('org-teste-api', 'all');
        raise exception 'FALHOU: Gestor não deveria listar chaves';
    exception when insufficient_privilege then null;
    end;
    if (api.my_admin_permissions('org-teste-api') ->> 'api_keys')::boolean then
        raise exception 'FALHOU: Gestor não deveria ver Chaves de API no menu';
    end if;
    if (api.my_api_key('org-teste-api') ->> 'status') <> 'pending' then
        raise exception 'FALHOU: my_api_key deveria mostrar o pedido pendente';
    end if;
end;
$$;

-- Tabelas fechadas para o front
do $$
begin
    perform 1 from app.api_keys;
    raise exception 'FALHOU: authenticated não deveria ler app.api_keys';
exception when insufficient_privilege then null;
end;
$$;

-- Colaborador não pede
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000a7004","role":"authenticated"}';
do $$
begin
    perform api.request_api_key('org-teste-api', null, '[]'::jsonb);
    raise exception 'FALHOU: Colaborador não deveria pedir';
exception when insufficient_privilege then null;
end;
$$;

-- Owner sem setor: precisa de extra
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000a7001","role":"authenticated"}';
do $$
begin
    begin
        perform api.request_api_key('org-teste-api', null, '[]'::jsonb);
        raise exception 'FALHOU: Owner sem setor e sem extra deveria falhar';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
    perform api.request_api_key('org-teste-api', null,
        jsonb_build_array(jsonb_build_object('setor', 'Comercial', 'justificativa', 'Planejamento anual da diretoria',
                                             'validade', current_date + 90)));
end;
$$;

-- Desenvolvedor: pendentes, aprova o Gestor com Protocolo e o Owner com Comercial
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000a7002","role":"authenticated"}';
do $$
declare
    k_g uuid := (select (x ->> 'id')::uuid from jsonb_array_elements(api.list_api_keys('org-teste-api', 'pending')) x
                 where x ->> 'user_email' = 'gestor.api@exemplo.com');
    k_o uuid := (select (x ->> 'id')::uuid from jsonb_array_elements(api.list_api_keys('org-teste-api', 'pending')) x
                 where x ->> 'user_email' = 'owner.api@exemplo.com');
begin
    if not (api.my_admin_permissions('org-teste-api') ->> 'api_keys')::boolean then
        raise exception 'FALHOU: Desenvolvedor deveria ver Chaves de API no menu';
    end if;
    if api.count_pending_api_keys('org-teste-api') <> 2 then
        raise exception 'FALHOU: deveriam ser 2 pendentes';
    end if;
    perform api.decide_api_key(k_g, true, array['Protocolo'], null);
    perform api.decide_api_key(k_o, true, array['Comercial'], null);
    begin
        perform api.decide_api_key(k_g, false, null, null);
        raise exception 'FALHOU: decidir de novo deveria falhar';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
end;
$$;

reset role;

-- Alcance
do $$
declare
    k_g uuid := (select id from app.api_keys where user_id = '00000000-0000-4000-8000-0000000a7003');
    k_o uuid := (select id from app.api_keys where user_id = '00000000-0000-4000-8000-0000000a7001');
    u1  uuid := '20000000-0000-4000-8000-0000000a7001';
    u2  uuid := '20000000-0000-4000-8000-0000000a7002';
begin
    if app_private.api_key_scope(k_g, u1, 'd-com') is distinct from 'all' then
        raise exception 'FALHOU: Gestor deveria ver d-com em U1 pelo setor base';
    end if;
    if app_private.api_key_scope(k_g, u2, 'd-com') is not null then
        raise exception 'FALHOU: Gestor não é Gestor em U2';
    end if;
    if app_private.api_key_scope(k_g, u1, 'd-prot') is distinct from 'all' then
        raise exception 'FALHOU: extra Protocolo aprovado deveria liberar d-prot';
    end if;
    if app_private.api_key_scope(k_g, u1, 'd-off') is not null then
        raise exception 'FALHOU: dashboard desligado não deveria aparecer';
    end if;
    if app_private.api_key_scope(k_o, u2, 'd-com') is distinct from 'all' then
        raise exception 'FALHOU: Owner com extra Comercial deveria ver d-com em U2';
    end if;
    if app_private.api_key_scope(k_o, u1, 'd-prot') is not null then
        raise exception 'FALHOU: Owner não pediu Protocolo';
    end if;

    -- extra vencido some sem job
    update app.api_key_sectors set expires_at = now() - interval '1 minute'
     where key_id = k_g and sector_name = 'Protocolo';
    if app_private.api_key_scope(k_g, u1, 'd-prot') is not null then
        raise exception 'FALHOU: extra vencido não deveria valer';
    end if;
    update app.api_key_sectors set expires_at = now() + interval '1 day'
     where key_id = k_g and sector_name = 'Protocolo';

    -- rebaixado a colaborador: a chave para de valer
    update app.membership_units set role_key = 'colaborador'
     where membership_id = '40000000-0000-4000-8000-0000000a7003';
    if app_private.api_key_scope(k_g, u1, 'd-com') is not null then
        raise exception 'FALHOU: Gestor rebaixado não deveria alcançar nada';
    end if;
    update app.membership_units set role_key = 'gestor'
     where membership_id = '40000000-0000-4000-8000-0000000a7003';

    -- tirado do setor: o base cai
    delete from app.membership_teams where membership_id = '40000000-0000-4000-8000-0000000a7003';
    if app_private.api_key_scope(k_g, u1, 'd-com') is not null then
        raise exception 'FALHOU: fora do setor Comercial, d-com não deveria valer';
    end if;
end;
$$;

-- Revogar setor e chave (Desenvolvedor)
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000a7002","role":"authenticated"}';
do $$
declare
    k_g uuid := (select (x ->> 'id')::uuid from jsonb_array_elements(api.list_api_keys('org-teste-api', 'active')) x
                 where x ->> 'user_email' = 'gestor.api@exemplo.com');
begin
    perform api.revoke_api_key_sector(k_g, 'Protocolo');
    perform api.revoke_api_key(k_g);
    if (select count(*) from jsonb_array_elements(api.list_api_keys('org-teste-api', 'closed'))) <> 1 then
        raise exception 'FALHOU: deveria haver 1 chave encerrada';
    end if;
end;
$$;
reset role;

do $$
declare
    k_g uuid := (select id from app.api_keys where user_id = '00000000-0000-4000-8000-0000000a7003');
begin
    if app_private.api_key_scope(k_g, '20000000-0000-4000-8000-0000000a7001', 'd-prot') is not null then
        raise exception 'FALHOU: chave revogada não deveria alcançar nada';
    end if;
    if (select tokens_valid_since from app.api_keys where id = k_g) is null then
        raise exception 'FALHOU: revogar deveria marcar tokens_valid_since';
    end if;
    if (select count(*) from app.audit_log where target_type = 'api_key' and target_id = k_g::text) < 4 then
        raise exception 'FALHOU: pedido, aprovação, revogação de setor e de chave deveriam estar na auditoria';
    end if;
    raise notice 'OK: api_publica';
end;
$$;

-- 20261127140000: na auditoria, o evento da chave mostra o dono (Gestor), não quem aprovou.
select set_config('teste.k_g', id::text, true) from app.api_keys
 where user_id = '00000000-0000-4000-8000-0000000a7003';
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000a7001","role":"authenticated"}';
do $$
declare
    v jsonb := api.list_audit('org-teste-api', p_actions => array['api_key.approved']);
    k_g text := current_setting('teste.k_g');
    nome text;
begin
    select e ->> 'targetName' into nome
      from jsonb_array_elements(v -> 'events') e where e ->> 'targetId' = k_g;
    if nome is distinct from 'Gestor API' then
        raise exception 'FALHOU: aprovação da chave do Gestor deveria trazer "Gestor API" (veio %)', nome;
    end if;
    raise notice 'OK: auditoria mostra o dono da chave';
end;
$$;
reset role;

rollback;
