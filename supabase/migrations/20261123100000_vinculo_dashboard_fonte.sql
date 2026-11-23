-- =============================================================================
-- Vínculo dashboard -> fonte (app.dashboard_sources) igual ao que a API já lê.
--
-- A tabela nasceu (20261113200000_detalhe_fonte.sql) só com o rótulo do catálogo (LexPre, LexFlow, NG);
-- banco LA e planilhas ficaram "para o analista confirmar" e nunca entraram. Resultado: a Planilha do
-- financeiro da LexGroup, lida pela Meta anual e pelo Financeiro Estratégico, aparecia em Unidades e fontes
-- como "Aguardando dashboards".
--
-- Aqui entram TODOS os pares que os módulos da API usam (app/dashboards: source_db, alt_sources e
-- extra_queries); os que já existiam são ignorados (on conflict). A partir de agora o teste
-- apps/api/tests/test_dashboard_sources_paridade.py confere no CI que todo par lido pela API está nesta
-- tabela: dashboard novo sem o vínculo quebra o CI.
--
-- Operações novas não mudam: uma fonte conectada por elas tem chave própria (ex.: gs_mc_1) e segue em
-- "Aguardando dashboards" até o analista escrever o dashboard dela (que, pelo teste, traz o vínculo).
--
-- Aditiva e idempotente (on conflict do nothing); só dashboards que existem no catálogo (FK).
-- Reverter: apagar as linhas abaixo (delete ... where (dashboard_key, source_key) in (...)).
-- =============================================================================

insert into app.dashboard_sources (dashboard_key, source_key)
select v.dashboard_key, v.source_key
from (values
    ('acordos', 'lexflow'),
    ('comercial', 'ng'),
    ('comercial-lexpre', 'laadv'),
    ('comercial-lexpre', 'lexpre'),
    ('comercial-lexpre', 'ng'),
    ('comissao', 'ng'),
    ('comissao-lexpre', 'lexpre'),
    ('controle-processos', 'laadv'),
    ('controle-processos', 'lexflow'),
    ('controle-processos', 'lexpre'),
    ('controle-processos', 'ng'),
    ('emendas-manifestacoes', 'lexflow'),
    ('execucao', 'lexflow'),
    ('execucao-estrategico', 'lexflow'),
    ('financeiro-estrategico', 'lexflow'),
    ('financeiro-estrategico', 'sheets_financeiro_la'),
    ('financeiro-estrategico', 'sheets_financeiro_ng'),
    ('julgados-acordaos', 'lexflow'),
    ('julgados-sentencas', 'lexflow'),
    ('marketing', 'ng'),
    ('meta-anual', 'sheets_financeiro_la'),
    ('meta-anual', 'sheets_financeiro_ng'),
    ('nps', 'ng'),
    ('org-documentos', 'laadv'),
    ('org-documentos', 'ng'),
    ('org-documentos-lexpre', 'lexpre'),
    ('pendencias', 'laadv'),
    ('pendencias', 'ng'),
    ('pendencias-intermediarias', 'lexflow'),
    ('pendencias-lexpre', 'lexpre'),
    ('peticionamento', 'laadv'),
    ('peticionamento', 'ng'),
    ('peticionamento-lexpre', 'lexpre'),
    ('pre-protocolo', 'lexpre'),
    ('previsao-individualizada', 'lexflow'),
    ('protocolo', 'laadv'),
    ('protocolo', 'ng'),
    ('protocolo-lexpre', 'lexpre'),
    ('publicacoes', 'lexflow'),
    ('recursal', 'lexflow'),
    ('replicas', 'lexflow'),
    ('sobrevivencia-processual', 'lexflow'),
    ('tickets', 'ng')
) as v (dashboard_key, source_key)
join app.dashboard_catalog c on c.key = v.dashboard_key
on conflict do nothing;
