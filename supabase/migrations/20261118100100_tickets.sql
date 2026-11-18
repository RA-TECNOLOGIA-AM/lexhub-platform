-- =============================================================================
-- Tickets (área Tecnologia): a página da v1 NG/Tickets.tsx, com o cálculo da rota /tickets da v1 sem mudança
-- (app/dashboards/tickets.py; banco NG, tabela Log_tickets_discord).
--
--   * primeiro card da área Tecnologia (entre Pré-protocolo e Jurídico);
--   * ligado só na NG, como na v1: a tabela já traz os três servidores do Discord (NG, LA-AM e LA-RJ), que
--     são um filtro da própria página. Sem regras de acesso por equipe ainda: veem Owner e Desenvolvedor
--     (org.dashboards.all); as equipes entram depois, em Acesso.
--   A ligação unidade -> banco NG (app.unit_source_refs, source = 'ng') já existe (20261113100000).
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'tickets',
    'Tickets',
    'Chamados de suporte do Discord: fila, SLA, categorias e servidores.',
    'Tecnologia',
    'NG',
    40,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'tickets', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'NG'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'tickets';
-- delete from app.dashboard_catalog where key = 'tickets';
-- =============================================================================
