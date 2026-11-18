-- =============================================================================
-- Publicações (área Jurídico): as páginas da v1 NG/PublicacoesNG.tsx, LA/PublicacoesLA.tsx e RJ/PublicacoesRJ.tsx,
-- com o cálculo das rotas /publicacoes_{NG,LA,RJ} sem mudança (app/dashboards/publicacoes.py; LexFlow).
--
--   * novo card no Jurídico, depois do Recursal (sort_order 82);
--   * ligado na NG, no LA e no RJ (a ligação unidade -> LexFlow já existe, da Execução). Sem regras de acesso por
--     equipe ainda: veem Owner e Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'publicacoes',
    'Publicações',
    'Publicações recebidas, tratadas e pendentes, por leitor, matéria e tribunal, e o agendamento depois.',
    'Jurídico',
    'LexFlow',
    82,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'publicacoes', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA', 'RJ')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'publicacoes';
-- delete from app.dashboard_catalog where key = 'publicacoes';
-- =============================================================================
