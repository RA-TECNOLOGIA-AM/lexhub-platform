-- =============================================================================
-- Teste de 20261126190000_estrategico_geral.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...'.
--
-- Cenário: org 'org-teste-geral' com U1 e U2; 'd-geral' (scope 'org') e 'd-local' (scope 'unit') ligados nas
-- duas; equipe E1 (U1) que vê tudo (sees_all) e tem exceção pessoal para o d-geral.
--   o1 = Owner · d1 = Desenvolvedor · g1 = Gestor em U1 e U2 · x1 = colaborador em U1 (E1, + exceção)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000e9001', 'owner.geral@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000e9002', 'dev.geral@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000e9003', 'gestor.geral@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000e9004', 'colab.geral@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000e9001', 'org-teste-geral', 'Org Teste Geral');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000e9001', '10000000-0000-4000-8000-0000000e9001', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000e9002', '10000000-0000-4000-8000-0000000e9001', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name, sees_all)
values ('30000000-0000-4000-8000-0000000e9001', '10000000-0000-4000-8000-0000000e9001',
        '20000000-0000-4000-8000-0000000e9001', 'E1', true);

insert into app.dashboard_catalog (key, name, area, active, sort_order, status, scope)
values ('d-geral', 'Dash Geral', 'Estratégico', true, 1, 'available', 'org'),
       ('d-local', 'Dash Local', 'Estratégico', true, 2, 'available', 'unit');
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select '10000000-0000-4000-8000-0000000e9001', u, k, true
from unnest(array['20000000-0000-4000-8000-0000000e9001', '20000000-0000-4000-8000-0000000e9002']::uuid[]) u,
     unnest(array['d-geral', 'd-local']) k;

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000e9001', '10000000-0000-4000-8000-0000000e9001',
        '00000000-0000-4000-8000-0000000e9001', 'Owner Geral', 'owner.geral@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000e9002', '10000000-0000-4000-8000-0000000e9001',
        '00000000-0000-4000-8000-0000000e9002', 'Dev Geral', 'dev.geral@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000e9003', '10000000-0000-4000-8000-0000000e9001',
        '00000000-0000-4000-8000-0000000e9003', 'Gestor Geral', 'gestor.geral@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000e9004', '10000000-0000-4000-8000-0000000e9001',
        '00000000-0000-4000-8000-0000000e9004', 'Colab Geral', 'colab.geral@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000e9001', '20000000-0000-4000-8000-0000000e9001',
        '40000000-0000-4000-8000-0000000e9003', 'gestor'),
       ('10000000-0000-4000-8000-0000000e9001', '20000000-0000-4000-8000-0000000e9002',
        '40000000-0000-4000-8000-0000000e9003', 'gestor'),
       ('10000000-0000-4000-8000-0000000e9001', '20000000-0000-4000-8000-0000000e9001',
        '40000000-0000-4000-8000-0000000e9004', 'colaborador');
insert into app.membership_teams (org_id, team_id, membership_id)
values ('10000000-0000-4000-8000-0000000e9001', '30000000-0000-4000-8000-0000000e9001',
        '40000000-0000-4000-8000-0000000e9004');
insert into app.member_dashboard_grants (membership_id, unit_id, dashboard_key)
values ('40000000-0000-4000-8000-0000000e9004', '20000000-0000-4000-8000-0000000e9001', 'd-geral');

-- Regra de acesso (service_role / dono das funções)
do $$
declare
    owner  uuid := '00000000-0000-4000-8000-0000000e9001';
    dev    uuid := '00000000-0000-4000-8000-0000000e9002';
    gestor uuid := '00000000-0000-4000-8000-0000000e9003';
    colab  uuid := '00000000-0000-4000-8000-0000000e9004';
    u1     uuid := '20000000-0000-4000-8000-0000000e9001';
    u2     uuid := '20000000-0000-4000-8000-0000000e9002';
begin
    -- Owner e Desenvolvedor veem o da organização em todas as unidades
    if app_private.dashboard_scope(owner, u1, 'd-geral') is distinct from 'all'
       or app_private.dashboard_scope(owner, u2, 'd-geral') is distinct from 'all' then
        raise exception 'FALHOU: Owner deveria ver o d-geral';
    end if;
    if app_private.dashboard_scope(dev, u1, 'd-geral') is distinct from 'all'
       or app_private.dashboard_scope(dev, u2, 'd-geral') is distinct from 'all' then
        raise exception 'FALHOU: Desenvolvedor deveria ver o d-geral';
    end if;

    -- Gestor (unit.dashboards.all), setor que vê tudo e exceção da pessoa NÃO liberam o da organização
    if app_private.dashboard_scope(gestor, u1, 'd-geral') is not null then
        raise exception 'FALHOU: Gestor não deveria ver o d-geral';
    end if;
    if app_private.dashboard_scope(colab, u1, 'd-geral') is not null then
        raise exception 'FALHOU: colaborador (setor que vê tudo + exceção) não deveria ver o d-geral';
    end if;
    if (select reason from app_private.dashboard_access_explain(gestor, u1, 'd-geral')) is distinct from 'owner_dev_only' then
        raise exception 'FALHOU: motivo do suporte deveria ser owner_dev_only';
    end if;

    -- O de unidade continua como antes: Gestor e setor que vê tudo liberam
    if app_private.dashboard_scope(gestor, u2, 'd-local') is distinct from 'all' then
        raise exception 'FALHOU: Gestor deveria ver o d-local';
    end if;
    if app_private.dashboard_scope(colab, u1, 'd-local') is distinct from 'all' then
        raise exception 'FALHOU: colaborador deveria ver o d-local pelo setor';
    end if;

    -- O card da migration existe com o escopo certo; o resto do catálogo segue 'unit'
    if (select scope from app.dashboard_catalog where key = 'estrategico-geral') is distinct from 'org'
       or (select scope from app.dashboard_catalog where key = 'estrategico') is distinct from 'unit' then
        raise exception 'FALHOU: escopo do Estratégico Geral / Estratégico';
    end if;
end;
$$;

set local role authenticated;

-- Owner abre o geral: grava 'dashboard.view' com unit 'GERAL'; repetição em < 5 min não grava.
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000e9001","role":"authenticated"}';
do $$
begin
    if not api.log_dashboard_view('org-teste-geral', 'geral', 'd-geral') then
        raise exception 'FALHOU: 1ª abertura do geral deveria gravar';
    end if;
    if api.log_dashboard_view('org-teste-geral', 'GERAL', 'd-geral') then
        raise exception 'FALHOU: repetição em menos de 5 min não deveria gravar';
    end if;
    -- 'geral' só vale para dashboard de scope 'org'
    begin
        perform api.log_dashboard_view('org-teste-geral', 'geral', 'd-local');
        raise exception 'FALHOU: d-local não é da organização';
    exception when invalid_parameter_value then null;
    end;
    -- O de unidade continua pela unidade
    if not api.log_dashboard_view('org-teste-geral', 'U1', 'd-local') then
        raise exception 'FALHOU: abertura do d-local deveria gravar';
    end if;
end;
$$;

-- Gestor não registra abertura do geral (nem pela unidade, nem como 'geral').
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000e9003","role":"authenticated"}';
do $$
begin
    begin
        perform api.log_dashboard_view('org-teste-geral', 'geral', 'd-geral');
        raise exception 'FALHOU: Gestor não deveria abrir o geral';
    exception when insufficient_privilege then null;
    end;
    begin
        perform api.log_dashboard_view('org-teste-geral', 'U1', 'd-geral');
        raise exception 'FALHOU: Gestor não deveria abrir o geral pela unidade';
    exception when insufficient_privilege then null;
    end;
end;
$$;

reset role;

do $$
begin
    if (select count(*) from app.audit_log
        where action = 'dashboard.view' and target_id = 'd-geral' and metadata ->> 'unit' = 'GERAL') <> 1 then
        raise exception 'FALHOU: esperava 1 abertura do geral com unit GERAL';
    end if;
    raise notice 'OK: estrategico_geral';
end;
$$;

rollback;
