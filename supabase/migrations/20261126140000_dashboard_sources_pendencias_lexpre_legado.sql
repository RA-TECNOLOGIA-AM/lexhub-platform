-- =============================================================================
-- Vínculo dashboard -> fonte para o legado (NG e LA) no Pendências LexPre.
--
-- O Pendências LexPre passou a somar as pendências do banco legado da unidade (extra_queries em
-- app/dashboards/pendencias_lexpre.py: setor_pendencias no ng, setor_pendencia_LA no laadv). Sem o vínculo,
-- essas fontes apareceriam em Unidades e fontes como "Aguardando dashboards"
-- (ver apps/api/tests/test_dashboard_sources_paridade.py).
--
-- Aditiva e idempotente (on conflict do nothing); só dashboards que existem no catálogo (FK).
-- Reverter: apagar as linhas abaixo (delete ... where (dashboard_key, source_key) in (...)).
-- =============================================================================

insert into app.dashboard_sources (dashboard_key, source_key)
select v.dashboard_key, v.source_key
from (values
    ('pendencias-lexpre', 'laadv'),
    ('pendencias-lexpre', 'ng')
) as v (dashboard_key, source_key)
join app.dashboard_catalog c on c.key = v.dashboard_key
on conflict do nothing;
