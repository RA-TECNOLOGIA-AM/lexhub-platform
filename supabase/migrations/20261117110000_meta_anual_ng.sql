-- =============================================================================
-- Abre a Meta anual (Financeiro) na NG.
--
-- É a página "Meta Anual" da v1 (rota /meta_anual_NG): faturamento do ano (honorários + sucumbência da
-- planilha do financeiro no Google Sheets, aba REPASSES CLIENTES) contra as metas Triste, Base, Avançada e
-- Super, por ano e por trimestre, e a análise preditiva (app/dashboards/meta_anual.py). A NG já está ligada à
-- planilha (app.unit_source_refs: sheets_financeiro_ng, 20261113180000_unidades_fontes.sql); a LA vem depois.
--
--   * o card passa para a área Financeiro (antes: Estratégico, "Em breve"), ao lado de Despesas;
--   * liga na NG. Sem regras de acesso por equipe ainda: veem Owner e Desenvolvedor (org.dashboards.all);
--     as equipes entram depois, em Acesso, quando a gestão definir quem vê o financeiro.
-- =============================================================================

update app.dashboard_catalog
   set area = 'Financeiro',
       sort_order = 101,
       source = 'Planilha do financeiro',
       description = 'Faturamento do ano contra as metas, por trimestre, e análise preditiva.',
       status = 'available'
 where key = 'meta-anual';

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'meta-anual', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'NG'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards od using app.units u
--  where od.unit_id = u.id and u.code = 'NG' and od.dashboard_key = 'meta-anual';
-- update app.dashboard_catalog
--    set area = 'Estratégico', sort_order = 120, source = 'LexPre', status = 'upcoming',
--        description = 'Meta do ano e quanto já foi atingido.'
--  where key = 'meta-anual';
-- =============================================================================
