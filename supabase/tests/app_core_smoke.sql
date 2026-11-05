-- =============================================================================
-- Teste rápido do schema app (isolamento entre organizações + regra de acesso)
-- Roda dentro de uma transação e desfaz no final (ROLLBACK): não deixa dados.
-- Use SÓ na branch staging (SQL Editor) ou localmente/CI. Esperado: nenhum ERROR.
-- =============================================================================
begin;

-- ---------- dados de teste ----------
insert into auth.users (id, email) values
    ('00000000-0000-0000-0000-0000000000a1', 'admin@a.test'),
    ('00000000-0000-0000-0000-0000000000a2', 'gestor.ng@a.test'),
    ('00000000-0000-0000-0000-0000000000a3', 'protocolo.ng@a.test'),
    ('00000000-0000-0000-0000-0000000000a4', 'semacesso.ng@a.test'),
    ('00000000-0000-0000-0000-0000000000a5', 'inativo@a.test'),
    ('00000000-0000-0000-0000-0000000000a6', 'leitor.ng@a.test'),
    ('00000000-0000-0000-0000-0000000000a7', 'controller.ng@a.test'),
    ('00000000-0000-0000-0000-0000000000b1', 'admin@b.test');

insert into app.organizations (id, slug, name) values
    ('10000000-0000-0000-0000-00000000000a', 'org-a', 'Org A'),
    ('10000000-0000-0000-0000-00000000000b', 'org-b', 'Org B');

insert into app.units (id, org_id, code, name) values
    ('20000000-0000-0000-0000-0000000000a1', '10000000-0000-0000-0000-00000000000a', 'NG', 'Unidade NG'),
    ('20000000-0000-0000-0000-0000000000a2', '10000000-0000-0000-0000-00000000000a', 'LA', 'Unidade LA'),
    ('20000000-0000-0000-0000-0000000000b1', '10000000-0000-0000-0000-00000000000b', 'XX', 'Unidade B');

insert into app.teams (id, org_id, unit_id, name) values
    ('30000000-0000-0000-0000-0000000000a1', '10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'Protocolo'),
    ('30000000-0000-0000-0000-0000000000a2', '10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'Pendências'),
    ('30000000-0000-0000-0000-0000000000a3', '10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a2', 'Protocolo LA'),
    ('30000000-0000-0000-0000-0000000000b1', '10000000-0000-0000-0000-00000000000b', '20000000-0000-0000-0000-0000000000b1', 'Equipe B');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status) values
    ('40000000-0000-0000-0000-0000000000a1', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a1', 'Admin A',    'admin@a.test',        'admin',       'active'),
    ('40000000-0000-0000-0000-0000000000a2', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a2', 'Gestor NG',  'gestor.ng@a.test',    'member',      'active'),
    ('40000000-0000-0000-0000-0000000000a3', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a3', 'Protocolo',  'protocolo.ng@a.test', 'member',      'active'),
    ('40000000-0000-0000-0000-0000000000a4', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a4', 'Sem acesso', 'semacesso.ng@a.test', 'member',      'active'),
    ('40000000-0000-0000-0000-0000000000a5', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a5', 'Inativo',    'inativo@a.test',      'admin',       'disabled'),
    ('40000000-0000-0000-0000-0000000000a6', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a6', 'Leitor',     'leitor.ng@a.test',    'member',      'active'),
    ('40000000-0000-0000-0000-0000000000a7', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a7', 'Controller', 'controller.ng@a.test', 'member',      'active'),
    ('40000000-0000-0000-0000-0000000000b1', '10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-0000000000b1', 'Admin B',    'admin@b.test',        'admin',       'active');

-- cargo POR COMPANHIA (Controller é controller na NG e leitor na LA)
insert into app.membership_units (org_id, unit_id, membership_id, role_key) values
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a2', 'gestor'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a3', 'colaborador'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a4', 'colaborador'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a6', 'leitor'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a7', 'controller'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a2', '40000000-0000-0000-0000-0000000000a7', 'leitor');

insert into app.membership_teams (org_id, team_id, membership_id) values
    ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a3'),
    ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a2', '40000000-0000-0000-0000-0000000000a6'),
    ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a3', '40000000-0000-0000-0000-0000000000a7');

insert into app.org_dashboards (org_id, unit_id, dashboard_key) values
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'protocolo-lexpre'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'pendencias'),
    ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a2', 'protocolo-lexpre'),
    ('10000000-0000-0000-0000-00000000000b', '20000000-0000-0000-0000-0000000000b1', 'protocolo-lexpre');

insert into app.access_rules (org_id, team_id, dashboard_key, scope) values
    ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a1', 'protocolo-lexpre', 'all'),
    ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a2', 'pendencias',       'own'),
    ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a3', 'protocolo-lexpre', 'all');

insert into app.invitations (org_id, email, role_key, token_hash) values
    ('10000000-0000-0000-0000-00000000000a', 'novo@a.test', 'colaborador', 'hash-de-teste');

-- ---------- integridade ----------
do $$
begin
    begin
        -- associação da Org B numa unidade da Org A
        insert into app.membership_units (org_id, unit_id, membership_id) values
            ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000b1');
        raise exception 'FALHOU: aceitou associação de outra organização';
    exception when foreign_key_violation then
        raise notice 'OK: FK composta bloqueia mistura de organizações';
    end;
    begin
        -- regra da Org A apontando para equipe da Org B
        insert into app.access_rules (org_id, team_id, dashboard_key) values
            ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000b1', 'protocolo-lexpre');
        raise exception 'FALHOU: regra aceitou equipe de outra organização';
    exception when foreign_key_violation then
        raise notice 'OK: regra de acesso presa à organização';
    end;
    begin
        insert into app.audit_log (action) values ('teste');
        delete from app.audit_log;
        raise exception 'FALHOU: audit_log aceitou delete';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
        raise notice 'OK: audit_log é somente inserção';
    end;
end $$;

-- ---------- regra de acesso (como a API chamaria) ----------
do $$
declare
    ng uuid := '20000000-0000-0000-0000-0000000000a1';
    la uuid := '20000000-0000-0000-0000-0000000000a2';
    ub uuid := '20000000-0000-0000-0000-0000000000b1';
begin
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a1', la, 'protocolo-lexpre') = 'all', 'admin A vê LA';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a2', ng, 'pendencias') = 'all',       'gestor NG vê tudo da NG';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a2', la, 'protocolo-lexpre') is null,  'gestor NG não vê LA';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a3', ng, 'protocolo-lexpre') = 'all', 'equipe Protocolo vê protocolo';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a3', ng, 'pendencias') is null,       'equipe Protocolo não vê pendências';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a6', ng, 'pendencias') = 'own',       'leitor vê pendências só os seus';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a4', ng, 'protocolo-lexpre') is null, 'sem regra = sem acesso';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a5', ng, 'protocolo-lexpre') is null, 'desativado não vê';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a1', ub, 'protocolo-lexpre') is null, 'admin A não vê Org B';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000b1', ng, 'protocolo-lexpre') is null, 'admin B não vê Org A';
    assert app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a3', ng, 'dashboards.export'),     'colaborador exporta';
    assert not app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a6', ng, 'dashboards.export'), 'leitor não exporta';
    assert not app_private.has_permission('00000000-0000-0000-0000-0000000000a2', '10000000-0000-0000-0000-00000000000a', 'members.manage'),    'gestor não gerencia a organização inteira';
    -- cargo por companhia
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a7', ng, 'pendencias') = 'all',       'controller vê tudo da NG';
    assert app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a7', la, 'protocolo-lexpre') = 'all', 'controller (leitor na LA) vê o que o setor libera';
    assert app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a7', ng, 'unit.members.manage'),     'controller atribui na NG';
    assert not app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a7', la, 'unit.members.manage'), 'controller não atribui na LA';
    assert app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a7', ng, 'dashboards.export'),       'controller exporta na NG';
    assert not app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a7', la, 'dashboards.export'),   'controller não exporta na LA (leitor)';
    assert app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a2', ng, 'unit.members.manage'),     'gestor atribui na NG';
    assert not app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a2', la, 'unit.members.manage'), 'gestor NG não atribui na LA';
    assert app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a1', la, 'unit.members.manage'),     'Desenvolvedor atribui em todas';
    assert not app_private.has_unit_permission('00000000-0000-0000-0000-0000000000a3', ng, 'unit.members.manage'), 'colaborador não atribui';
    raise notice 'OK: regra de acesso a dashboards (23 casos)';
end $$;

-- ---------- RLS: colaborador "Protocolo NG" logado ----------
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a3","role":"authenticated"}', true);

do $$
begin
    assert (select count(*) from app.organizations) = 1, 'deveria ver só a própria organização';
    assert (select count(*) from app.units) = 2,         'deveria ver só as unidades da Org A';
    assert (select count(*) from app.memberships) = 1,   'colaborador vê só a própria associação';
    assert (select count(*) from app.access_rules) = 0,  'colaborador não vê regras de acesso';
    assert (select count(*) from app.invitations) = 0,   'colaborador não vê convites';
    assert (select count(*) from app.my_dashboards()) = 1, 'hub deveria ter 1 dashboard';
    assert (select scope from app.my_dashboards()) = 'all', 'escopo no hub deveria ser all';
    assert app.can_view_dashboard('20000000-0000-0000-0000-0000000000a1', 'protocolo-lexpre'), 'can_view deveria ser true';
    begin
        insert into app.teams (org_id, unit_id, name)
            values ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'Hack');
        raise exception 'FALHOU: usuário logado conseguiu escrever';
    exception when insufficient_privilege then
        raise notice 'OK: usuário logado não escreve';
    end;
    begin
        perform app_private.dashboard_scope('00000000-0000-0000-0000-0000000000a1', '20000000-0000-0000-0000-0000000000a1', 'pendencias');
        raise exception 'FALHOU: usuário logado consultou acesso de outra pessoa';
    exception when insufficient_privilege then
        raise notice 'OK: app_private.dashboard_scope é só da API';
    end;
    raise notice 'OK: RLS do colaborador';
end $$;

-- ---------- RLS: leitor logado (escopo "só os seus") ----------
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a6","role":"authenticated"}', true);
do $$
begin
    assert app.dashboard_scope('20000000-0000-0000-0000-0000000000a1', 'pendencias') = 'own', 'leitor: escopo own';
    raise notice 'OK: escopo só os seus';
end $$;

-- ---------- RLS: admin da Org A ----------
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a1","role":"authenticated"}', true);
do $$
begin
    assert (select count(*) from app.memberships) = 7,  'admin A vê as 7 associações da Org A';
    assert (select count(*) from app.access_rules) = 3, 'admin A vê as regras da Org A';
    assert (select count(*) from app.invitations) = 1,  'admin A vê o convite';
    raise notice 'OK: RLS do admin';
end $$;

-- ---------- RLS: controller da NG (leitor na LA) ----------
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a7","role":"authenticated"}', true);
do $$
begin
    assert (select count(*) from app.memberships) = 5,      'controller vê as associações da NG (e a própria)';
    assert (select count(*) from app.membership_units) = 6, 'controller vê os cargos da NG + o próprio na LA';
    assert (select count(*) from app.access_rules) = 2,     'controller vê só as regras da NG';
    assert (select count(*) from app.my_dashboards()) = 3,  'hub: 2 da NG + 1 da LA';
    raise notice 'OK: RLS do controller por companhia';
end $$;

-- ---------- RLS: admin da Org B ----------
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000b1","role":"authenticated"}', true);
do $$
begin
    assert (select count(*) from app.organizations) = 1, 'admin B vê só Org B';
    assert (select count(*) from app.memberships) = 1,   'admin B vê só associações da Org B';
    assert (select count(*) from app.units where code = 'NG') = 0, 'admin B não vê NG';
    assert (select count(*) from app.invitations) = 0,   'admin B não vê convites da Org A';
    raise notice 'OK: isolamento entre organizações';
end $$;

-- ---------- anon não acessa nada ----------
reset role;
set local role anon;
do $$
begin
    perform 1 from app.units;
    raise exception 'FALHOU: anon leu app.units';
exception when insufficient_privilege then
    raise notice 'OK: anon sem acesso';
end $$;

reset role;
rollback;
