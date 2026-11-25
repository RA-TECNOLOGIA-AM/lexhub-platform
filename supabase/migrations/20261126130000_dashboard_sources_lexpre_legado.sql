-- =============================================================================
-- Vínculo dashboard -> fonte para os indicadores legados (NG e LA) dos painéis LexPre.
--
-- Protocolo, Peticionamento e Org. documentos LexPre passaram a ler também os bancos legados ng e laadv
-- (extra_queries em app/dashboards/{protocolo,peticionamento,org_documentos}_lexpre.py). Sem o vínculo, essas fontes apareceriam em
-- Unidades e fontes como "Aguardando dashboards" (ver apps/api/tests/test_dashboard_sources_paridade.py).
--
-- Aditiva e idempotente (on conflict do nothing); só dashboards que existem no catálogo (FK).
-- Reverter: apagar as linhas abaixo (delete ... where (dashboard_key, source_key) in (...)).
-- =============================================================================

insert into app.dashboard_sources (dashboard_key, source_key)
select v.dashboard_key, v.source_key
from (values
    ('org-documentos-lexpre', 'laadv'),
    ('org-documentos-lexpre', 'ng'),
    ('peticionamento-lexpre', 'laadv'),
    ('peticionamento-lexpre', 'ng'),
    ('protocolo-lexpre', 'laadv'),
    ('protocolo-lexpre', 'ng')
) as v (dashboard_key, source_key)
join app.dashboard_catalog c on c.key = v.dashboard_key
on conflict do nothing;
