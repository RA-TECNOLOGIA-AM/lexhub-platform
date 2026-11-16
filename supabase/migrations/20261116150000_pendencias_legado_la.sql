-- =============================================================================
-- Abre as Pendências (banco legado) na LA.
--
-- Na v1 a LA tem a rota /pendencia_LA, no banco LAADV (query setor_pendencia_LA). A API lê esse banco
-- quando a unidade não está ligada ao NG (app/dashboards/pendencias.py, alt_sources), como o Protocolo
-- (20261116120000_protocolo_legado_la.sql). A LA já está ligada ao laadv (app.unit_source_refs).
--
-- Liga o dashboard na LA onde as Pendências (LexPre) estão ligadas, com as mesmas regras de acesso
-- por equipe. Owner/admin já veem tudo (org.dashboards.all).
-- =============================================================================

-- O card diz de onde vem: NG e RJ no banco NG, LA no banco LA (antes: só 'NG').
update app.dashboard_catalog
   set source = 'NG · LA',
       description = 'Métricas de volume, taxas, SLA e produtividade do setor (banco legado).'
 where key = 'pendencias';

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, 'pendencias', od.enabled
  from app.org_dashboards od
  join app.units u on u.id = od.unit_id
 where od.dashboard_key = 'pendencias-lexpre'
   and u.code = 'LA'
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, 'pendencias', r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id
  join app.units u on u.id = t.unit_id
 where r.dashboard_key = 'pendencias-lexpre'
   and u.code = 'LA'
on conflict (team_id, dashboard_key) do nothing;

-- =============================================================================
-- Rollback:
-- update app.dashboard_catalog set source = 'NG',
--        description = 'Pendências abertas, resolvidas e tempo de resolução.' where key = 'pendencias';
-- delete from app.access_rules r using app.teams t, app.units u
--  where r.team_id = t.id and t.unit_id = u.id and u.code = 'LA' and r.dashboard_key = 'pendencias';
-- delete from app.org_dashboards od using app.units u
--  where od.unit_id = u.id and u.code = 'LA' and od.dashboard_key = 'pendencias';
-- =============================================================================
