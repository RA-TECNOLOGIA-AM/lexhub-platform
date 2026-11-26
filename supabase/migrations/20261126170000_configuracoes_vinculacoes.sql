-- =============================================================================
-- Configurações das Vinculações (área Estratégico): a página admin da v1 admin/ConfiguracoesVinculacoesPage.tsx —
-- a auditoria das vinculações (setor + atividade) do LexFlow: o que cada uma faz no CUMPRIDO e no NÃO CUMPRIDO,
-- os gatilhos de fase/subfase, os campos obrigatórios e o que falta configurar ou aponta para o lugar errado
-- (app/dashboards/configuracoes_vinculacoes.py; query e cálculo da v1 sem mudança).
--
--   * novo card no Estratégico, depois da Previsão Individualizada (sort_order 150);
--   * ligado na NG, no LA e no RJ: cada unidade vê só as vinculações do seu escritório no LexFlow
--     (20, 21 e 27). A ligação unidade -> LexFlow já existe (20261112090000_unit_source_refs_lexflow.sql);
--   * sem regras de acesso por equipe: na v1 era uma página de administração, então só veem Owner e
--     Desenvolvedor (org.dashboards.all). As equipes entram depois, em Acesso, se for o caso;
--   * fonte lida (app.dashboard_sources): lexflow; conferido por apps/api/tests/test_dashboard_sources_paridade.py.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'configuracoes-vinculacoes',
    'Configurações das Vinculações',
    'Auditoria das vinculações (setor + atividade) do LexFlow: fluxos de cumprido e não cumprido, gatilhos de fase/subfase e o que falta configurar.',
    'Estratégico',
    'LexFlow',
    150,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'configuracoes-vinculacoes', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA', 'RJ')
on conflict do nothing;

insert into app.dashboard_sources (dashboard_key, source_key)
values ('configuracoes-vinculacoes', 'lexflow')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.dashboard_sources where dashboard_key = 'configuracoes-vinculacoes';
-- delete from app.org_dashboards where dashboard_key = 'configuracoes-vinculacoes';
-- delete from app.dashboard_catalog where key = 'configuracoes-vinculacoes';
-- =============================================================================
