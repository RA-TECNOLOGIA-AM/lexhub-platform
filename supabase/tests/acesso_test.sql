-- =============================================================================
-- Teste de 20261113140000_acesso.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
--
-- Cenário: org 'org-teste-acesso' com unidades U1 e U2; equipes E1 (U1) e E2 (U2); regra E1 -> d-um.
--   Dashboards ligados: d-um e d-dois em U1; d-um em U2.
--   o1 = Owner · d1 = Desenvolvedor · g1 = Gestor só em U1
--   x1 = colaborador em U1 (E1) e U2 (E2) · z1 = desativado (leitor em U1)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000c1', 'owner.acesso@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000c2', 'dev.acesso@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000c3', 'gestor.acesso@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000c4', 'colab.acesso@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000c5', 'desativado.acesso@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000a1', 'org-teste-acesso', 'Org Teste Acesso');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-0000000000a1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000a2', '10000000-0000-4000-8000-0000000000a1', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name)
values ('30000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-0000000000a1',
        '20000000-0000-4000-8000-0000000000a1', 'E1'),
       ('30000000-0000-4000-8000-0000000000a2', '10000000-0000-4000-8000-0000000000a1',
        '20000000-0000-4000-8000-0000000000a2', 'E2');
insert into app.teams (id, org_id, unit_id, name, active)
values ('30000000-0000-4000-8000-0000000000a3', '10000000-0000-4000-8000-0000000000a1',
        '20000000-0000-4000-8000-0000000000a1', 'E3 inativa', false);

insert into app.dashboard_catalog (key, name, area, active, sort_order)
values ('d-um', 'Dash Um', 'Teste', true, 1), ('d-dois', 'Dash Dois', 'Teste', true, 2);
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
values ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1', 'd-um', true),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1', 'd-dois', true),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a2', 'd-um', true);
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
values ('10000000-0000-4000-8000-0000000000a1', '30000000-0000-4000-8000-0000000000a1', 'd-um', 'all');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000c1', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000c1', 'Owner Teste', 'owner.acesso@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000000c2', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000c2', 'Dev Teste', 'dev.acesso@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000c3', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000c3', 'Gestor Teste', 'gestor.acesso@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000c4', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000c4', 'Colab Teste', 'colab.acesso@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000c5', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000c5', 'Desativado Teste', 'desativado.acesso@exemplo.com', 'member', 'disabled');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1', '40000000-0000-4000-8000-0000000000c3', 'gestor'),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1', '40000000-0000-4000-8000-0000000000c4', 'colaborador'),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a2', '40000000-0000-4000-8000-0000000000c4', 'colaborador'),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1', '40000000-0000-4000-8000-0000000000c5', 'leitor');
insert into app.membership_teams (org_id, team_id, membership_id)
values ('10000000-0000-4000-8000-0000000000a1', '30000000-0000-4000-8000-0000000000a1', '40000000-0000-4000-8000-0000000000c4'),
       ('10000000-0000-4000-8000-0000000000a1', '30000000-0000-4000-8000-0000000000a2', '40000000-0000-4000-8000-0000000000c4'),
       ('10000000-0000-4000-8000-0000000000a1', '30000000-0000-4000-8000-0000000000a3', '40000000-0000-4000-8000-0000000000c4');

set local role authenticated;

-- ---------- Gestor (g1): só U1 ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000c3","role":"authenticated"}';
do $$
declare r jsonb; ok boolean;
begin
    r := api.access_overview('org-teste-acesso', null);
    if r ->> 'unit' <> 'U1' or jsonb_array_length(r -> 'units') <> 1 then
        raise exception 'FALHOU: Gestor deveria ver só U1: %', r -> 'units';
    end if;
    if (r ->> 'can_set_org_role')::boolean then raise exception 'FALHOU: Gestor não muda papel na org'; end if;
    if not (r -> 'dashboards' @> '[{"key":"d-um","teams":["E1"]}]') or jsonb_array_length(r -> 'dashboards') <> 2 then
        raise exception 'FALHOU: dashboards de U1: %', r -> 'dashboards';
    end if;
    if r -> 'dashboards_by_unit' <> '{"U1":["d-um","d-dois"]}'::jsonb then
        raise exception 'FALHOU: dashboards_by_unit: %', r -> 'dashboards_by_unit';
    end if;
    if not (r -> 'roles' @> '[{"key":"gestor","sees_all":true,"exports":true},{"key":"leitor","sees_all":false,"exports":false}]') then
        raise exception 'FALHOU: roles: %', r -> 'roles';
    end if;
    if exists (select 1 from jsonb_array_elements(r -> 'teams') t where t ->> 'name' = 'E2') then
        raise exception 'FALHOU: Gestor viu equipe de U2';
    end if;

    -- ?unidade= de unidade que ele não gere (link salvo, ou tirou o próprio cargo): cai na primeira gerida
    r := api.access_overview('org-teste-acesso', 'U2');
    if r ->> 'unit' <> 'U1' or exists (select 1 from jsonb_array_elements(r -> 'dashboards') d where d ->> 'key' = 'x') then
        raise exception 'FALHOU: unidade fora do escopo deveria cair em U1: %', r ->> 'unit';
    end if;

    -- x1 em U1 vira leitor, sem E1. U2 (cargo e E2) não pode mudar.
    r := api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                  '[{"code":"U1","role":"leitor"}]', '{}', null);
    if r -> 'units' <> '[{"code":"U1","role":"leitor"}]'::jsonb or r -> 'teams' <> '[]'::jsonb
       or r -> 'team_ids' <> '[]'::jsonb then
        raise exception 'FALHOU: x1 depois do Gestor: %', r;
    end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                           '[{"code":"U2","role":"leitor"}]', '{}', null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor mexeu em U2'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c2',
                                           '[{"code":"U1","role":"leitor"}]', '{}', null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor editou o Desenvolvedor'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                           '[{"code":"U1","role":"leitor"}]', '{}', 'admin');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor mudou papel na org'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                           '[]', array['30000000-0000-4000-8000-0000000000a1'::uuid], null);
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: equipe sem cargo na unidade foi aceita'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c5',
                                           '[{"code":"U1","role":"colaborador"}]', '{}', null);
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: editou membro desativado'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                           '[{"code":"U1","role":"chefe"}]', '{}', null);
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: cargo inválido aceito'; end if;
end $$;

-- ---------- Colaborador: não gere acesso ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000c4","role":"authenticated"}';
do $$
declare ok boolean := false;
begin
    begin perform api.access_overview('org-teste-acesso', null); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: colaborador abriu o Acesso'; end if;
end $$;

-- ---------- Desenvolvedor (d1) ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000c2","role":"authenticated"}';
do $$
declare r jsonb; ok boolean;
begin
    r := api.access_overview('org-teste-acesso', 'U2');
    if jsonb_array_length(r -> 'units') <> 2 or (r ->> 'can_set_org_role')::boolean is not true then
        raise exception 'FALHOU: overview do Dev: %', r;
    end if;
    if r -> 'dashboards_by_unit' <> '{"U1":["d-um","d-dois"],"U2":["d-um"]}'::jsonb then
        raise exception 'FALHOU: dashboards_by_unit do Dev: %', r -> 'dashboards_by_unit';
    end if;

    -- x1: Dev vê U1 e U2; U2 ainda é colaborador com E2 (o Gestor não mexeu)
    r := api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                  '[{"code":"U1","role":"colaborador"},{"code":"U2","role":"colaborador"}]',
                                  array['30000000-0000-4000-8000-0000000000a1'::uuid, '30000000-0000-4000-8000-0000000000a2'::uuid],
                                  'admin');
    if r ->> 'org_role' <> 'admin' or jsonb_array_length(r -> 'units') <> 2 or jsonb_array_length(r -> 'teams') <> 2
       or not (r -> 'team_ids' @> '["30000000-0000-4000-8000-0000000000a2"]') then
        raise exception 'FALHOU: Dev promovendo x1: %', r;
    end if;
    r := api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4',
                                  '[{"code":"U1","role":"colaborador"},{"code":"U2","role":"colaborador"}]',
                                  array['30000000-0000-4000-8000-0000000000a1'::uuid, '30000000-0000-4000-8000-0000000000a2'::uuid],
                                  'member');
    if r ->> 'org_role' <> 'member' then raise exception 'FALHOU: Dev voltando x1 a membro: %', r; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c2', '[]', '{}', 'member');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: Dev mudou o próprio papel'; end if;

    ok := false;
    -- 42501 desde 20261113235900_protege_owner.sql (Dev nem chega a mexer no Owner)
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c1', '[]', '{}', 'member');
    exception when sqlstate '42501' or sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: rebaixou o Owner'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-acesso', '40000000-0000-4000-8000-0000000000c4', '[]', '{}', 'owner');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: promoveu a Owner'; end if;
end $$;

-- ---------- conferências como dono do banco ----------
reset role;
do $$
begin
    if not exists (select 1 from app.membership_teams where membership_id = '40000000-0000-4000-8000-0000000000c4'
                   and team_id = '30000000-0000-4000-8000-0000000000a2') then
        raise exception 'FALHOU: E2 de x1 sumiu';
    end if;
    if not exists (select 1 from app.membership_teams where membership_id = '40000000-0000-4000-8000-0000000000c4'
                   and team_id = '30000000-0000-4000-8000-0000000000a3') then
        raise exception 'FALHOU: salvar tirou x1 da equipe inativa E3 (a tela nem mostra equipes inativas)';
    end if;
    if (select count(*) from app.audit_log where org_id = '10000000-0000-4000-8000-0000000000a1'
          and action = 'member.access_updated') <> 3 then
        raise exception 'FALHOU: auditoria member.access_updated (esperado 3)';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
