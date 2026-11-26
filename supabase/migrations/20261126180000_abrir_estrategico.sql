-- =============================================================================
-- Estratégico (área Estratégico): a página da v1 GERAL/Estrategico.tsx, agora com dados
-- (app/dashboards/estrategico.py). O card existia desde 20261110180000 como "Em breve" ('upcoming').
--
--   * status 'available', com descrição e fonte do que a página mostra: Comercial e Protocolo (bancos legados e
--     LexPre) e o Jurídico do LexFlow;
--   * ligado na NG, no LA e no RJ: cada unidade vê só os próprios números (na v1 a página juntava os escritórios,
--     com o filtro de escritório; na NG os escritórios NGAM/NGPA/NGPB viram o filtro de UF);
--   * fontes lidas (app.dashboard_sources): lexflow, ng, laadv e lexpre; conferido por
--     apps/api/tests/test_dashboard_sources_paridade.py;
--   * sem regras de acesso por equipe: veem Owner e Desenvolvedor (org.dashboards.all) e quem já vê tudo da
--     unidade pelo cargo ou pelo setor (Diretoria). As equipes entram depois, em Acesso.
-- =============================================================================

update app.dashboard_catalog
   set status = 'available',
       description = 'Comercial, protocolo e jurídico da unidade: contratos e ações fechadas, represados, protocolados, valor de causa e o avanço nas fases.',
       source = 'LexFlow, legado e LexPre'
 where key = 'estrategico';

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select u.org_id, u.id, 'estrategico', true
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
 where u.code in ('NG', 'LA', 'RJ')
on conflict do nothing;

insert into app.dashboard_sources (dashboard_key, source_key)
values
    ('estrategico', 'lexflow'),
    ('estrategico', 'ng'),
    ('estrategico', 'laadv'),
    ('estrategico', 'lexpre')
on conflict do nothing;

-- =============================================================================
-- Rollback:
-- delete from app.dashboard_sources where dashboard_key = 'estrategico';
-- delete from app.org_dashboards where dashboard_key = 'estrategico';
-- update app.dashboard_catalog
--    set status = 'upcoming', description = 'Visão geral das unidades.', source = '3 unidades'
--  where key = 'estrategico';
-- =============================================================================
