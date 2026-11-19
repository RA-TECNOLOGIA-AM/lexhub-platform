-- =============================================================================
-- Emendas e Manifestações também no RJ. A v1 não tem a página no RJ: a V2 usa o cálculo do NG sem mudança
-- (mesmo setor MANIFESTAÇÃO, com UF, e a mesma comissão: R$ 1,00 por manifestação e R$ 0,50 por dilação), lendo a
-- query do escritório do RJ (27): agendamentos_setor_emendas_manifestacoes_RJ (app/dashboards/emendas_manifestacoes.py).
-- =============================================================================

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'emendas-manifestacoes', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'RJ'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards d using app.units u
--  where d.unit_id = u.id and u.code = 'RJ' and d.dashboard_key = 'emendas-manifestacoes';
-- =============================================================================
