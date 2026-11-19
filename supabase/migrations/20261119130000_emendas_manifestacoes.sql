-- =============================================================================
-- Emendas e Manifestações (área Jurídico): as páginas da v1 NG/EmendasManifestacoes_NG.tsx e
-- LA/EmendasManifestacoes_LA.tsx, com o cálculo das rotas /emendas_manifestacoes_{NG,LA} sem mudança
-- (app/dashboards/emendas_manifestacoes.py; LexFlow). NG: setor MANIFESTAÇÃO; LA: setor INTERMEDIÁRIAS.
--
--   * novo card no Jurídico, depois de Pendências Intermediárias (sort_order 84);
--   * ligado na NG e no LA (a v1 não tem a página no RJ). Sem regras de acesso por equipe ainda: veem Owner e
--     Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'emendas-manifestacoes',
    'Emendas e Manifestações',
    'Emendas, manifestações e dilações: agenda cumprida, peças por funcionário, comissão e a lista de tarefas.',
    'Jurídico',
    'LexFlow',
    84,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'emendas-manifestacoes', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'emendas-manifestacoes';
-- delete from app.dashboard_catalog where key = 'emendas-manifestacoes';
-- =============================================================================
