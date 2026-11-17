-- =============================================================================
-- Financeiro Estratégico (Financeiro): a página da v1 (FinanceiroEstrategicoNG.tsx; rotas
-- /financeiro_estrategico_<NG|LA>, /conversao, /previsao e /clientes_pendentes) num dashboard só.
--
-- Fontes: a planilha do financeiro da unidade (Google Sheets, aba REPASSES CLIENTES) e o valor de causa
-- ajuizado no LexFlow (app/dashboards/financeiro_estrategico.py). NG e LA já estão ligadas às duas
-- (app.unit_source_refs: sheets_financeiro_ng / sheets_financeiro_la e lexflow).
--
--   * novo card na área Financeiro, ao lado da Meta anual;
--   * ligado na NG e na LA. Como a Meta anual, sem regras de acesso por equipe ainda: veem Owner e
--     Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'financeiro-estrategico',
    'Financeiro Estratégico',
    'Receita, valor protocolado, conversão, evolução e previsão.',
    'Financeiro',
    'Planilha do financeiro + LexFlow',
    102,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'financeiro-estrategico', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'financeiro-estrategico';
-- delete from app.dashboard_catalog where key = 'financeiro-estrategico';
-- =============================================================================
