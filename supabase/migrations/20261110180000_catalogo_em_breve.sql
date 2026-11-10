-- =============================================================================
-- Catálogo do hub: os dashboards que ainda não abrem entram como "Em breve".
--
-- Mesmos títulos, áreas e textos do protótipo (mock do front). status = 'upcoming':
-- aparecem só na seção "Em breve" do hub (título e área), não ficam ligados em nenhuma
-- unidade (app.org_dashboards) e, por isso, dashboard_scope nunca libera acesso a eles.
-- Quando um ficar pronto: status = 'available' e ligar nas unidades.
--
-- sort_order segue a ordem do protótipo: Comercial, Operação jurídica, Execução e recursal, Gestão.
-- =============================================================================

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status) values
    ('comercial-lexpre',      'Funil comercial',           'Atendimentos, contratos fechados e conversão.', 'Comercial',           'LexPre',     1,   'upcoming'),
    ('comissao',              'Comissão',                  'Comissão por atendente e por rubrica.',         'Comercial',           'LexPre',     2,   'upcoming'),
    ('nps',                   'NPS',                       'Satisfação dos clientes.',                      'Comercial',           'LexPre',     3,   'upcoming'),
    ('marketing',             'Marketing',                 'Leads e canais de origem.',                     'Comercial',           'LexPre',     4,   'upcoming'),
    ('peticionamento-lexpre', 'Peticionamento',            'Peticionados, represados e valor de causa.',    'Operação jurídica',   'LexPre',     30,  'upcoming'),
    ('org-documentos-lexpre', 'Organização de documentos', 'Documentos organizados e devolvidos.',          'Operação jurídica',   'LexPre',     40,  'upcoming'),
    ('pre-protocolo',         'Pré-protocolo',             'Processos em preparação para o protocolo.',     'Operação jurídica',   'LexPre',     50,  'upcoming'),
    ('execucao',              'Execução',                  'Processos em execução e valores.',              'Execução e recursal', 'LexFlow',    60,  'upcoming'),
    ('acordos',               'Acordos',                   'Acordos fechados e valores.',                   'Execução e recursal', 'LexFlow',    70,  'upcoming'),
    ('recursal',              'Recursal',                  'Recursos e julgados.',                          'Execução e recursal', 'LexFlow',    80,  'upcoming'),
    ('estrategico',           'Estratégico',               'Visão geral das unidades.',                     'Gestão',              '3 unidades', 90,  'upcoming'),
    ('despesas',              'Despesas',                  'Contas a pagar e a receber.',                   'Gestão',              'Conta Azul', 100, 'upcoming'),
    ('meta-anual',            'Meta anual',                'Meta do ano e quanto já foi atingido.',         'Gestão',              'LexPre',     110, 'upcoming')
on conflict (key) do nothing;
