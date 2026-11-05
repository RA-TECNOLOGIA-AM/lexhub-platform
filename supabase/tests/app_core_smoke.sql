-- =============================================================================
-- Teste rápido do schema app (isolamento entre organizações + regra de acesso)
-- Roda tudo dentro de uma transação e desfaz no final (ROLLBACK): não deixa dados.
-- Use SÓ na branch staging (SQL Editor) ou localmente. Saída esperada: "OK: ..." e nenhum erro.
-- =============================================================================
begin;

-- ---------- dados de teste (como postgres / service) ----------
insert into auth.users (id, email) values
  ('00000000-0000-0000-0000-0000000000a1', 'admin@a.test'),
  ('00000000-0000-0000-0000-0000000000a2', 'gestor.ng@a.test'),
  ('00000000-0000-0000-0000-0000000000a3', 'protocolo.ng@a.test'),
  ('00000000-0000-0000-0000-0000000000a4', 'semacesso.ng@a.test'),
  ('00000000-0000-0000-0000-0000000000a5', 'inativo@a.test'),
  ('00000000-0000-0000-0000-0000000000b1', 'admin@b.test');

insert into app.organizations (id, slug, name) values
  ('10000000-0000-0000-0000-00000000000a', 'org-a', 'Org A'),
  ('10000000-0000-0000-0000-00000000000b', 'org-b', 'Org B');

insert into app.units (id, org_id, code, name) values
  ('20000000-0000-0000-0000-0000000000a1', '10000000-0000-0000-0000-00000000000a', 'NG', 'Unidade NG'),
  ('20000000-0000-0000-0000-0000000000a2', '10000000-0000-0000-0000-00000000000a', 'LA', 'Unidade LA'),
  ('20000000-0000-0000-0000-0000000000b1', '10000000-0000-0000-0000-00000000000b', 'XX', 'Unidade B');

insert into app.teams (id, org_id, unit_id, name) values
  ('30000000-0000-0000-0000-0000000000a1', '10000000-0000-0000-0000-00000000000a',
   '20000000-0000-0000-0000-0000000000a1', 'Protocolo');

insert into app.members (id, org_id, user_id, full_name, email, role, status) values
  ('40000000-0000-0000-0000-0000000000a1', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a1', 'Admin A',     'admin@a.test',        'admin',  'active'),
  ('40000000-0000-0000-0000-0000000000a2', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a2', 'Gestor NG',   'gestor.ng@a.test',    'member', 'active'),
  ('40000000-0000-0000-0000-0000000000a3', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a3', 'Protocolo',   'protocolo.ng@a.test', 'member', 'active'),
  ('40000000-0000-0000-0000-0000000000a4', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a4', 'Sem acesso',  'semacesso.ng@a.test', 'member', 'active'),
  ('40000000-0000-0000-0000-0000000000a5', '10000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-0000000000a5', 'Inativo',     'inativo@a.test',      'admin',  'disabled'),
  ('40000000-0000-0000-0000-0000000000b1', '10000000-0000-0000-0000-00000000000b', '00000000-0000-0000-0000-0000000000b1', 'Admin B',     'admin@b.test',        'admin',  'active');

insert into app.unit_members (org_id, unit_id, member_id, role) values
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a2', 'manager'),
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a3', 'member'),
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a4', 'member');

insert into app.team_members (org_id, team_id, member_id) values
  ('10000000-0000-0000-0000-00000000000a', '30000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000a3');

insert into app.unit_dashboards (org_id, unit_id, dashboard_key) values
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'protocolo-lexpre'),
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'pendencias'),
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a2', 'protocolo-lexpre'),
  ('10000000-0000-0000-0000-00000000000b', '20000000-0000-0000-0000-0000000000b1', 'protocolo-lexpre');

insert into app.dashboard_grants (org_id, unit_id, dashboard_key, team_id) values
  ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'protocolo-lexpre',
   '30000000-0000-0000-0000-0000000000a1');

-- ---------- integridade: não dá para misturar organizações ----------
do $$
begin
  begin
    -- membro da Org B numa unidade da Org A
    insert into app.unit_members (org_id, unit_id, member_id) values
      ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', '40000000-0000-0000-0000-0000000000b1');
    raise exception 'FALHOU: aceitou membro de outra organização';
  exception when foreign_key_violation then
    raise notice 'OK: FK composta bloqueia mistura de organizações';
  end;
  begin
    update app.audit_log set action = 'x';
    insert into app.audit_log (action) values ('teste');
    delete from app.audit_log;
    raise exception 'FALHOU: audit_log aceitou delete';
  exception when raise_exception then
    if sqlerrm like 'FALHOU%' then raise; end if;
    raise notice 'OK: audit_log é somente inserção';
  end;
end $$;

-- ---------- regra de acesso ----------
do $$
declare
  ng uuid := '20000000-0000-0000-0000-0000000000a1';
  la uuid := '20000000-0000-0000-0000-0000000000a2';
  ub uuid := '20000000-0000-0000-0000-0000000000b1';
begin
  assert app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a1', la, 'protocolo-lexpre'), 'admin A deveria ver LA';
  assert app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a2', ng, 'pendencias'),    'gestor NG deveria ver tudo de NG';
  assert not app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a2', la, 'protocolo-lexpre'), 'gestor NG não deveria ver LA';
  assert app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a3', ng, 'protocolo-lexpre'),  'equipe Protocolo deveria ver protocolo NG';
  assert not app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a3', ng, 'pendencias'), 'equipe Protocolo não deveria ver pendências';
  assert not app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a4', ng, 'protocolo-lexpre'), 'membro sem liberação não deveria ver';
  assert not app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a5', ng, 'protocolo-lexpre'), 'membro desativado não deveria ver';
  assert not app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a1', ub, 'protocolo-lexpre'), 'admin A não deveria ver Org B';
  assert not app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000b1', ng, 'protocolo-lexpre'), 'admin B não deveria ver Org A';
  raise notice 'OK: regra de acesso a dashboards (9 casos)';
end $$;

-- ---------- RLS: usuário "Protocolo NG" logado ----------
set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000a3","role":"authenticated"}', true);

do $$
begin
  assert (select count(*) from app.organizations) = 1, 'deveria ver só a própria organização';
  assert (select count(*) from app.units) = 2,         'deveria ver só as unidades da Org A';
  assert (select count(*) from app.members) = 1,       'membro comum vê só o próprio cadastro';
  assert (select count(*) from app.dashboard_grants) = 0, 'membro comum não vê liberações';
  assert (select count(*) from app.my_dashboards()) = 1,  'hub deveria ter 1 dashboard';
  assert app.can_view_dashboard('20000000-0000-0000-0000-0000000000a1', 'protocolo-lexpre'), 'can_view deveria ser true';
  begin
    insert into app.teams (org_id, unit_id, name)
      values ('10000000-0000-0000-0000-00000000000a', '20000000-0000-0000-0000-0000000000a1', 'Hack');
    raise exception 'FALHOU: usuário logado conseguiu escrever';
  exception when insufficient_privilege then
    raise notice 'OK: usuário logado não escreve';
  end;
  begin
    perform app.user_can_view_dashboard('00000000-0000-0000-0000-0000000000a1', '20000000-0000-0000-0000-0000000000a1', 'pendencias');
    raise exception 'FALHOU: usuário logado consultou acesso de outra pessoa';
  exception when insufficient_privilege then
    raise notice 'OK: user_can_view_dashboard é só da API';
  end;
  raise notice 'OK: RLS do membro comum';
end $$;

-- ---------- RLS: admin da Org B ----------
select set_config('request.jwt.claims', '{"sub":"00000000-0000-0000-0000-0000000000b1","role":"authenticated"}', true);
do $$
begin
  assert (select count(*) from app.organizations) = 1, 'admin B vê só Org B';
  assert (select count(*) from app.members) = 1,       'admin B vê só membros da Org B';
  assert (select count(*) from app.units where code = 'NG') = 0, 'admin B não vê NG';
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
