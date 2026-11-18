-- =============================================================================
-- Previsão Individualizada (área Estratégico): a página da v1 GERAL/TccPrevisaoIndividualizada.tsx (Fase 6 do TCC),
-- com o bundle estático do XGBoost-AFT gerado por modelo-machine-learning/ (app/dashboards/previsao_individualizada.py;
-- não consulta o LexFlow).
--
--   * novo card no Estratégico, depois da Sobrevivência Processual (sort_order 140);
--   * ligado na NG e no LA: cada unidade vê só o próprio escritório (regra de 18/11/2026), recortado na API.
--     O RJ ficou fora do estudo do TCC. Sem regras de acesso por equipe ainda: veem Owner e Desenvolvedor.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values (
    'previsao-individualizada',
    'Previsão Individualizada',
    'Tempo previsto até mérito/acordo e pagamento, chance de procedência e de acordo para uma combinação de processo (modelo XGBoost-AFT do estudo do TCC).',
    'Estratégico',
    'LexFlow',
    140,
    'available'
)
on conflict (key) do nothing;

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'previsao-individualizada', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.org_dashboards where dashboard_key = 'previsao-individualizada';
-- delete from app.dashboard_catalog where key = 'previsao-individualizada';
-- =============================================================================
