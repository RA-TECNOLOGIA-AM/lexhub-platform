-- =============================================================================
-- Recursal: a página da v1 inteira (NG/Recursal.tsx, LA/Recursal_LA.tsx, RJ/Recursal_RJ.tsx) na V2
-- (app/dashboards/recursal.py), agora também no RJ (a v1 ganhou /recursal_RJ).
--
--   * descrição do card com o que a página mostra;
--   * ligado no RJ (LARJ), com as mesmas regras de acesso por equipe da NG e do LA (Análise de Recurso,
--     Controladoria e Diretoria), para as equipes do RJ com esses nomes.
--   A ligação RJ -> LexFlow (app.unit_source_refs, source = 'lexflow') já existe (Execução do RJ).
-- =============================================================================

update app.dashboard_catalog
   set description = 'Estoque e entradas na fase recursal, decisões 1º × 2º grau, magistrados e atividades do setor.'
 where key = 'recursal';

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'recursal', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'RJ'
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select distinct on (rj.id) r.org_id, rj.id, 'recursal', r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id
  join app.units u on u.id = t.unit_id and u.code = 'NG'
  join app.units urj on urj.org_id = u.org_id and urj.code = 'RJ'
  join app.teams rj on rj.unit_id = urj.id and rj.name = t.name
 where r.dashboard_key = 'recursal'
on conflict (team_id, dashboard_key) do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.access_rules r using app.teams t, app.units u
--  where r.team_id = t.id and t.unit_id = u.id and u.code = 'RJ' and r.dashboard_key = 'recursal';
-- delete from app.org_dashboards d using app.units u
--  where d.unit_id = u.id and u.code = 'RJ' and d.dashboard_key = 'recursal';
-- update app.dashboard_catalog set description = 'Recursos e julgados.' where key = 'recursal';
-- =============================================================================
