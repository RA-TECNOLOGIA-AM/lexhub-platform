-- =============================================================================
-- Sobrevivência Processual também no LA (LAAM). Regra de negócio de 18/11/2026: cada unidade vê só o próprio
-- escritório (a NG vê a NG e o LA vê o LA). A API recorta a coorte do estudo pela unidade
-- (app/dashboards/sobrevivencia_processual.py) e a página não tem mais o filtro de escritório da v1.
-- O RJ ficou fora do estudo do TCC (não tem coorte).
-- =============================================================================

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'sobrevivencia-processual', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'LA'
on conflict do nothing;

update app.dashboard_catalog
   set description = 'Tempo até mérito, acordo e pagamento (Kaplan-Meier) e os gargalos por matéria, comarca e competência, do escritório da unidade.'
 where key = 'sobrevivencia-processual';

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards d using app.units u
--  where d.unit_id = u.id and u.code = 'LA' and d.dashboard_key = 'sobrevivencia-processual';
-- =============================================================================
