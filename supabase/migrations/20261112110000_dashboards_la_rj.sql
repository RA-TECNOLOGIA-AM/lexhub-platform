-- =============================================================================
-- Liga os dashboards LexPre e LexFlow também nas unidades LA e RJ.
--
-- Até aqui estavam só na NG (molde do piloto: tudo copiado do Protocolo (LexPre)). As fontes já
-- conhecem LA e RJ (app.unit_source_refs: LexPre LA=2, RJ=3; LexFlow LA, RJ) e a API calcula para elas
-- com o mesmo código da v1 (rotas -la/-rj, _LA/_RJ).
--   * org_dashboards: LA e RJ ligadas; Recursal só LA (a v1 não tem Recursal do RJ).
--   * access_rules: as mesmas equipes que hoje veem na NG (Controladoria e Diretoria), as da própria
--     unidade (equipe é por unidade), mesmo escopo.
-- Owner/admin (Desenvolvedor) já veem tudo pela permissão org.dashboards.all.
-- =============================================================================

with alvo (dashboard_key, unit_code) as (
    select k.key, u.code
      from (values ('protocolo-lexpre'), ('pendencias-lexpre'), ('comercial-lexpre'), ('comissao-lexpre'),
                   ('org-documentos-lexpre'), ('peticionamento-lexpre'), ('execucao'), ('acordos')) as k(key)
     cross join (values ('LA'), ('RJ')) as u(code)
    union all
    select 'recursal', 'LA'
)
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, a.dashboard_key, true
  from alvo a
  join app.units u on u.code = a.unit_code and u.active
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
on conflict do nothing;

-- Regras: para cada dashboard, as equipes (por nome) que o veem na NG, agora as da LA/RJ.
insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, t_destino.id, r.dashboard_key, r.scope, r.created_by
  from app.access_rules r
  join app.teams t_ng       on t_ng.id = r.team_id
  join app.units u_ng       on u_ng.id = t_ng.unit_id and u_ng.code = 'NG'
  join app.org_dashboards od on od.org_id = r.org_id and od.dashboard_key = r.dashboard_key
  join app.units u_destino  on u_destino.id = od.unit_id and u_destino.code in ('LA', 'RJ')
  join app.teams t_destino  on t_destino.org_id = r.org_id and t_destino.unit_id = u_destino.id
                           and t_destino.name = t_ng.name and t_destino.active
 where r.dashboard_key in ('protocolo-lexpre', 'pendencias-lexpre', 'comercial-lexpre', 'comissao-lexpre',
                           'org-documentos-lexpre', 'peticionamento-lexpre', 'execucao', 'acordos', 'recursal')
on conflict (team_id, dashboard_key) do nothing;
