-- =============================================================================
-- Abre o Marketing (LexPre): o cálculo da v1 (/marketing_lexpre_NG e /marketing_lexpre_LA) entrou na API
-- (app/dashboards/marketing_lexpre.py). Ficou "Em breve" em 20261111180000_abrir_dashboards_lexpre.sql
-- porque lê também o banco NG (facebook_ads).
--
--   * status = 'available' (sai de "Chegando na V2");
--   * ligado na NG e na LA, as unidades que tinham a página na v1 (escritórios 1 e 2 do LexPre);
--   * acesso: as mesmas equipes que veem o Comercial (LexPre) em cada unidade (Comercial, Controladoria e
--     Diretoria), mesmo escopo. Owner/admin (Desenvolvedor) já veem tudo pela permissão org.dashboards.all;
--   * fontes lidas (app.dashboard_sources): lexpre e ng (o Facebook Ads); conferido por
--     apps/api/tests/test_dashboard_sources_paridade.py;
--   * o Marketing (banco NG) passa a ler também o LexPre: o comercial da NG foi para o LexPre em set/2026 e a
--     API soma os dois (app/dashboards/marketing_soma_lexpre.py).
--
-- Aditiva e idempotente (on conflict do nothing).
-- =============================================================================

update app.dashboard_catalog
   set status = 'available'
 where key = 'marketing-lexpre';

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'marketing-lexpre', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA')
   and u.active
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, 'marketing-lexpre', r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id and t.active
  join app.org_dashboards od on od.unit_id = t.unit_id
                            and od.dashboard_key = 'marketing-lexpre'
                            and od.enabled
 where r.dashboard_key = 'comercial-lexpre'
on conflict (team_id, dashboard_key) do nothing;

insert into app.dashboard_sources (dashboard_key, source_key)
select v.dashboard_key, v.source_key
  from (values
      ('marketing-lexpre', 'lexpre'),
      ('marketing-lexpre', 'ng'),
      ('marketing', 'lexpre')
  ) as v (dashboard_key, source_key)
  join app.dashboard_catalog c on c.key = v.dashboard_key
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.access_rules where dashboard_key = 'marketing-lexpre';
-- delete from app.org_dashboards where dashboard_key = 'marketing-lexpre';
-- update app.dashboard_catalog set status = 'upcoming' where key = 'marketing-lexpre';
-- delete from app.dashboard_sources where (dashboard_key, source_key) = ('marketing', 'lexpre');
-- (app.dashboard_sources: os pares do marketing-lexpre podem ficar; sem o dashboard ligado não aparecem)
-- =============================================================================
