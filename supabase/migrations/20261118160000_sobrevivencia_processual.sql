-- =============================================================================
-- Sobrevivência Processual (área Estratégico): a página da v1 GERAL/TccSobrevivenciaProcessual.tsx (estudo do TCC),
-- com a coorte da rota /tcc_sobrevivencia_processual da v1 (app/dashboards/sobrevivencia_processual.py; LexFlow).
--
--   * novo card no Estratégico, depois da Execução Estratégico Geral (sort_order 130);
--   * ligado só na NG: a coorte é a do estudo (NG + LA/AM juntos, com o escritório como filtro da própria página).
--     Sem regras de acesso por equipe ainda: veem Owner e Desenvolvedor (org.dashboards.all).
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'sobrevivencia-processual',
    'Sobrevivência Processual',
    'Tempo até mérito, acordo e pagamento (Kaplan-Meier) e os gargalos por matéria, comarca e competência.',
    'Estratégico',
    'LexFlow',
    130,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'sobrevivencia-processual', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'NG'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'sobrevivencia-processual';
-- delete from app.dashboard_catalog where key = 'sobrevivencia-processual';
-- =============================================================================
