-- =============================================================================
-- Controle de Processos (área Jurídico): a página da v1 NG/ControleProcessos.tsx — a esteira de trabalho
-- (protocolados → inicial → recursal → execução → arquivados por procedência), os extintos, a permanência por fase
-- e as subfases (app/dashboards/controle_processos.py). Junta LexFlow (controle, Execução e Acordos), o banco NG
-- legado (Protocolo) e o LexPre (Protocolo); as ligações da unidade a esses bancos já existem.
--
--   * novo card no Jurídico, depois de Réplicas (sort_order 87);
--   * ligado só na NG por enquanto (a página do LA vem depois). Sem regras de acesso por equipe ainda: veem Owner e
--     Desenvolvedor (org.dashboards.all); as equipes entram depois, em Acesso.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'controle-processos',
    'Controle de Processos',
    'Esteira de trabalho (protocolados, inicial, recursal, execução e arquivados), extintos, permanência por fase e subfases.',
    'Jurídico',
    'LexFlow',
    87,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'controle-processos', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code = 'NG'
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'controle-processos';
-- delete from app.dashboard_catalog where key = 'controle-processos';
-- =============================================================================
