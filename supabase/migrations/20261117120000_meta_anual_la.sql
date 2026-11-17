-- =============================================================================
-- Abre a Meta anual (Financeiro) na LA.
--
-- Mesmo cálculo da NG (20261117110000_meta_anual_ng.sql), com a planilha do financeiro da LA (aba REPASSES
-- CLIENTES) e as metas da LA: na v1, a rota /meta_anual_LA (financeiro_LA.py). A API lê a planilha a que a
-- unidade está ligada (app/dashboards/meta_anual.py, alt_sources): a LA já está ligada à sua
-- (app.unit_source_refs: sheets_financeiro_la, 20261113180000_unidades_fontes.sql).
--
-- Como na NG, sem regras de acesso por equipe ainda: veem Owner e Desenvolvedor (org.dashboards.all).
-- =============================================================================

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'meta-anual', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'LA'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards od using app.units u
--  where od.unit_id = u.id and u.code = 'LA' and od.dashboard_key = 'meta-anual';
-- =============================================================================
