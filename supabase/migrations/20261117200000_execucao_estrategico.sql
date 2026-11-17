-- =============================================================================
-- Execução Estratégico Geral (Estratégico): a página da v1 (NG/ExecucaoEstrategicoGeral.tsx), que junta a
-- Execução Condenação e a Execução Acordos (rotas /execucao e /execucao_acordos_NG) com o filtro
-- Ambos / Condenação / Acordos, mais a Confecção CS e os Alvarás Expedidos (app/dashboards/execucao_estrategico.py).
--
--   * novo card na área Estratégico, depois do Estratégico e da Meta anual;
--   * ligado só na NG por enquanto (LA e RJ depois). Como os outros do Estratégico, sem regras de acesso por
--     equipe ainda: veem Owner e Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'execucao-estrategico',
    'Execução Estratégico Geral',
    'Condenação e acordos juntos: estoque, entradas, saídas, valores, Confecção CS e alvarás.',
    'Estratégico',
    'LexFlow',
    125,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'execucao-estrategico', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'NG'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'execucao-estrategico';
-- delete from app.dashboard_catalog where key = 'execucao-estrategico';
-- =============================================================================
