-- =============================================================================
-- Controle de Processos também no LA (LAAM) e no RJ (LARJ) — app/dashboards/controle_processos.py:
--   * LA: a rota da v1 do LA (/controle_processo_LA; sem filtro de UF, como a página dela), o Protocolo do banco
--     LAADV (/protocolo_LA), a Execução e os Acordos do LA e o LexPre (escritório 2);
--   * RJ: a v1 não tem a página — o cálculo do NG sem mudança, com a base no escritório 27 e o histórico de subfases
--     do RJ (query log_subfase_processual_RJ), o Protocolo do banco NG (/protocolo_RJ), a Execução e os Acordos do
--     RJ e o LexPre (escritório 3).
-- As ligações das unidades a esses bancos já existem (app.unit_source_refs).
-- =============================================================================

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'controle-processos', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('LA', 'RJ')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards d using app.units u
--  where d.unit_id = u.id and u.code in ('LA', 'RJ') and d.dashboard_key = 'controle-processos';
-- =============================================================================
