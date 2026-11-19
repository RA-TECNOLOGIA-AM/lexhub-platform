-- =============================================================================
-- Réplicas (área Jurídico): as páginas da v1 NG/Replicas_NG.tsx e LA/Replicas_LA.tsx, com o cálculo das rotas
-- /replicas_{NG,LA} sem mudança (app/dashboards/replicas.py; LexFlow). NG: setor RÉPLICA; LA: setor RÉPLICAS.
--
--   * novo card no Jurídico, depois de Emendas e Manifestações (sort_order 86 — o 85 é o dos Julgados Sentenças);
--   * ligado na NG e no LA (a v1 não tem a página no RJ). Sem regras de acesso por equipe ainda: veem Owner e
--     Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'replicas',
    'Réplicas',
    'Réplicas por prazo e concluídas, taxa de procedência (1G) dos processos com réplica, demandas por funcionário e a lista de tarefas.',
    'Jurídico',
    'LexFlow',
    86,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'replicas', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'replicas';
-- delete from app.dashboard_catalog where key = 'replicas';
-- =============================================================================
