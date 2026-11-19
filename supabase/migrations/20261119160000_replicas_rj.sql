-- =============================================================================
-- Réplicas também no RJ. A v1 não tem a página no RJ: a V2 usa o cálculo do NG sem mudança (mesmo setor RÉPLICA,
-- taxa de procedência pela atividade ELABORAR RÉPLICA e sem comissão), lendo as queries do escritório do RJ (27):
-- agendamentos_setor_replicas_RJ e processos_status_1g_replicas_RJ (app/dashboards/replicas.py).
-- =============================================================================

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'replicas', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'RJ'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards d using app.units u
--  where d.unit_id = u.id and u.code = 'RJ' and d.dashboard_key = 'replicas';
-- =============================================================================
