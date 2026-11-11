-- =============================================================================
-- Abre os dashboards LexFlow que ganharam o cálculo da v1 (branch feat/dashboards-lexflow-v1):
-- Execução, Acordos e Recursal.
--
-- Mesmo molde de 20261111180000_abrir_dashboards_lexpre.sql:
--   * status = 'available' (sai de "Chegando na V2");
--   * ligado nas mesmas unidades em que o Protocolo (LexPre) está ligado (hoje: NG, o piloto);
--   * mesmas regras de acesso por equipe do Protocolo (LexPre) (hoje: Controladoria e Diretoria).
-- Owner/admin (Desenvolvedor) já veem tudo pela permissão org.dashboards.all.
-- Precisa da ligação unidade -> LexFlow (20261112090000_unit_source_refs_lexflow.sql).
-- Outras equipes (ex.: Execução, Análise de Recurso) e as unidades LA e RJ entram depois,
-- quando o analista validar os números e a gestão definir quem vê cada um.
-- =============================================================================

update app.dashboard_catalog
   set status = 'available'
 where key in ('execucao', 'acordos', 'recursal');

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, k.key, od.enabled
  from app.org_dashboards od
 cross join (values ('execucao'), ('acordos'), ('recursal')) as k(key)
 where od.dashboard_key = 'protocolo-lexpre'
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, k.key, r.scope, r.created_by
  from app.access_rules r
 cross join (values ('execucao'), ('acordos'), ('recursal')) as k(key)
 where r.dashboard_key = 'protocolo-lexpre'
on conflict (team_id, dashboard_key) do nothing;
