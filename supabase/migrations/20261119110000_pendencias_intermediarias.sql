-- =============================================================================
-- Pendências Intermediárias (área Jurídico): as páginas da v1 NG/PendenciasIntermediarias_NG.tsx e
-- LA/PendenciasIntermediarias_LA.tsx, com o cálculo das rotas /pendencias_intermediarias_{NG,LA} sem mudança
-- (app/dashboards/pendencias_intermediarias.py; LexFlow).
--
--   * novo card no Jurídico, depois de Publicações (sort_order 83);
--   * ligado na NG e no LA (a v1 não tem a página no RJ). Sem regras de acesso por equipe ainda: veem Owner e
--     Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'pendencias-intermediarias',
    'Pendências Intermediárias',
    'Agendamentos do setor de Pendências: por prazo e concluídas, dilações de prazo, demandas por funcionário e a lista de tarefas.',
    'Jurídico',
    'LexFlow',
    83,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'pendencias-intermediarias', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'pendencias-intermediarias';
-- delete from app.dashboard_catalog where key = 'pendencias-intermediarias';
-- =============================================================================
