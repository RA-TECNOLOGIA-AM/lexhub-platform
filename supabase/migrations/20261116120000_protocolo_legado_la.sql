-- =============================================================================
-- Abre o Protocolo (banco legado) na LA.
--
-- Na v1 a LA tem a rota /protocolo_LA, no banco LAADV (query setor_protocolo_LA). A API passou a ler esse
-- banco quando a unidade não está ligada ao NG (app/dashboards/protocolo.py, alt_sources): a LA já está
-- ligada ao laadv (app.unit_source_refs, 20261113180000_unidades_fontes.sql).
--
-- Mesmo molde de 20261113100000_abrir_dashboards_ng.sql: liga o dashboard na LA onde o Protocolo (LexPre)
-- está ligado, com as mesmas regras de acesso por equipe. Owner/admin já veem tudo (org.dashboards.all).
-- =============================================================================

-- O card diz de onde vem: NG e RJ no banco NG, LA no banco LA (antes: só 'NG').
update app.dashboard_catalog
   set source = 'NG · LA',
       description = 'Métricas de protocolo, represados e comissionamento do setor (banco legado).'
 where key = 'protocolo';

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, 'protocolo', od.enabled
  from app.org_dashboards od
  join app.units u on u.id = od.unit_id
 where od.dashboard_key = 'protocolo-lexpre'
   and u.code = 'LA'
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, 'protocolo', r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id
  join app.units u on u.id = t.unit_id
 where r.dashboard_key = 'protocolo-lexpre'
   and u.code = 'LA'
on conflict (team_id, dashboard_key) do nothing;

-- =============================================================================
-- Rollback:
-- update app.dashboard_catalog set source = 'NG',
--        description = 'Protocolados, represados e devoluções do setor Protocolo.' where key = 'protocolo';
-- delete from app.access_rules r using app.teams t, app.units u
--  where r.team_id = t.id and t.unit_id = u.id and u.code = 'LA' and r.dashboard_key = 'protocolo';
-- delete from app.org_dashboards od using app.units u
--  where od.unit_id = u.id and u.code = 'LA' and od.dashboard_key = 'protocolo';
-- =============================================================================
