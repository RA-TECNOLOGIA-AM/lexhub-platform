-- =============================================================================
-- Julgados Sentenças (Jurídico, LexFlow): as páginas da v1 julgados_sentenca_{NG,LA,RJ}.tsx (rotas
-- /julgados_<NG|LA|RJ> e /export) num dashboard só. O cálculo é a cópia da v1
-- (app/dashboards/julgados_sentencas.py), sobre a mesma query `julgados` dos Julgados Acórdãos.
--
--   * novo card na área Jurídico, logo antes dos Julgados Acórdãos (1º grau, depois 2º grau);
--   * ligado na NG, na LA e no RJ (a v1 tem as três rotas);
--   * regras de acesso: em cada unidade, as mesmas equipes e o mesmo escopo dos Julgados Acórdãos
--     (que copiou as da Execução). Owner e Desenvolvedor já veem tudo (org.dashboards.all).
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'julgados-sentencas',
    'Julgados Sentenças',
    'Resultados de sentença (1º grau) no período.',
    'Jurídico',
    'LexFlow',
    85,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'julgados-sentencas', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA', 'RJ')
   and u.active
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, 'julgados-sentencas', r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id and t.active
  join app.units u on u.id = t.unit_id and u.code in ('NG', 'LA', 'RJ')
 where r.dashboard_key = 'julgados-acordaos'
on conflict (team_id, dashboard_key) do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.access_rules where dashboard_key = 'julgados-sentencas';
-- delete from app.org_dashboards where dashboard_key = 'julgados-sentencas';
-- delete from app.dashboard_catalog where key = 'julgados-sentencas';
-- =============================================================================
