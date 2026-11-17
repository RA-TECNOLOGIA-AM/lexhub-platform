-- =============================================================================
-- Execução Estratégico Geral também no LA (LAAM) e no RJ (LARJ): as páginas da v1 LA/ExecucaoEstrategicoGeralLA.tsx
-- e RJ/ExecucaoEstrategicoGeralRJ.tsx, com as rotas /execucao_LA e /execucao_acordos_LA (RJ: _RJ)
-- (app/dashboards/execucao_estrategico.py). O card já existe (20261117200000_execucao_estrategico.sql).
-- =============================================================================

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'execucao-estrategico', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('LA', 'RJ')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards d using app.units u
--  where d.unit_id = u.id and d.dashboard_key = 'execucao-estrategico' and u.code in ('LA', 'RJ');
-- =============================================================================
