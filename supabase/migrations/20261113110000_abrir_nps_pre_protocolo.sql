-- =============================================================================
-- Abre NPS (banco NG) e Pré-protocolo (LexPre) — branch feat/ativar-cards.
--
--   * NPS: cálculo da v1 /nps_NG sem mudança (app/dashboards/nps.py). Só a NG: o NPS da LA na v1 lê o
--     banco LAADV. O catálogo dizia fonte 'LexPre' (do protótipo); a da v1 é o banco NG.
--   * Pré-protocolo (LexPre): a página geral da v1 (PreProtocoloGeralLexpre) junta os 4 dashboards
--     LexPre do setor (app/dashboards/pre_protocolo.py). Abre nas unidades do Protocolo (LexPre): NG, LA, RJ.
--
-- Mesmo molde das anteriores (20261113100000_abrir_dashboards_ng.sql): status = 'available', ligado nas
-- unidades em que o Protocolo (LexPre) está ligado e com as mesmas regras de acesso por equipe (hoje:
-- Controladoria e Diretoria). Owner/admin (Desenvolvedor) já veem tudo pela permissão org.dashboards.all.
-- A ligação unidade -> banco NG (app.unit_source_refs, source = 'ng') já veio na 20261113100000.
-- =============================================================================

update app.dashboard_catalog set source = 'NG' where key = 'nps';

update app.dashboard_catalog
   set status = 'available'
 where key in ('nps', 'pre-protocolo');

with alvo (dashboard_key, unit_code) as (
    select 'nps', 'NG'
    union all
    select 'pre-protocolo', u.code from (values ('NG'), ('LA'), ('RJ')) as u(code)
)
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, a.dashboard_key, od.enabled
  from app.org_dashboards od
  join app.units u on u.id = od.unit_id
  join alvo a on a.unit_code = u.code
 where od.dashboard_key = 'protocolo-lexpre'
on conflict do nothing;

with alvo (dashboard_key, unit_code) as (
    select 'nps', 'NG'
    union all
    select 'pre-protocolo', u.code from (values ('NG'), ('LA'), ('RJ')) as u(code)
)
insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, a.dashboard_key, r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id
  join app.units u on u.id = t.unit_id
  join alvo a on a.unit_code = u.code
 where r.dashboard_key = 'protocolo-lexpre'
on conflict (team_id, dashboard_key) do nothing;
