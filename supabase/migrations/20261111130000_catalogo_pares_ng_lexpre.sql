-- =============================================================================
-- Catálogo em pares, como na v1: cada domínio tem o dashboard do banco NG e o do LexPre.
--
--   <domínio>          banco NG       (v1: /protocolo, /pendencia...)        título "Protocolo"
--   <domínio>-lexpre   banco LexPre   (v1: /protocolo-lexpre...)             título "Protocolo (LexPre)"
--
-- Domínios: Comercial, Comissão Comercial, Marketing, Protocolo, Pendências,
-- Organização de Documentos, Peticionamento. Quando o banco NG for desligado, basta
-- tirar os dashboards de banco NG; os do LexPre seguem.
--
-- Piloto NG (18/11): Protocolo (LexPre) e Pendências (LexPre) abrem; os de banco NG ficam
-- "Em breve" até o dev de dados copiar o cálculo da v1 (aí status = 'available').
-- A "pendencias" que já existia (veio de "pendencias-ng") passa a ser a de banco NG;
-- "pendencias-lexpre" nasce ligada nas mesmas unidades e com as mesmas regras de acesso.
-- =============================================================================

-- Existentes: títulos, fonte e ordem
update app.dashboard_catalog set name = 'Comercial (LexPre)', sort_order = 2 where key = 'comercial-lexpre';
update app.dashboard_catalog set name = 'Comissão Comercial', source = 'NG', sort_order = 3 where key = 'comissao';
update app.dashboard_catalog set source = 'NG', sort_order = 5 where key = 'marketing';
update app.dashboard_catalog set sort_order = 7 where key = 'nps';
update app.dashboard_catalog set name = 'Protocolo (LexPre)', sort_order = 11 where key = 'protocolo-lexpre';
update app.dashboard_catalog
   set name = 'Pendências', source = 'NG', sort_order = 12, status = 'upcoming'
 where key = 'pendencias';
update app.dashboard_catalog set name = 'Organização de Documentos (LexPre)', sort_order = 15 where key = 'org-documentos-lexpre';
update app.dashboard_catalog set name = 'Peticionamento (LexPre)', sort_order = 17 where key = 'peticionamento-lexpre';
update app.dashboard_catalog set sort_order = 18 where key = 'pre-protocolo';

-- Novos: o par que faltava em cada domínio
insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status) values
    ('comercial',         'Comercial',                   'Atendimentos, contratos fechados e conversão.',              'Comercial',         'NG',     1,  'upcoming'),
    ('comissao-lexpre',   'Comissão Comercial (LexPre)', 'Comissão por atendente e por rubrica.',                      'Comercial',         'LexPre', 4,  'upcoming'),
    ('marketing-lexpre',  'Marketing (LexPre)',          'Leads e canais de origem.',                                  'Comercial',         'LexPre', 6,  'upcoming'),
    ('protocolo',         'Protocolo',                   'Protocolados, represados e devoluções do setor Protocolo.',  'Operação jurídica', 'NG',     10, 'upcoming'),
    ('pendencias-lexpre', 'Pendências (LexPre)',         'Pendências abertas, resolvidas e tempo de resolução.',       'Operação jurídica', 'LexPre', 13, 'available'),
    ('org-documentos',    'Organização de Documentos',   'Documentos organizados e devolvidos.',                       'Operação jurídica', 'NG',     14, 'upcoming'),
    ('peticionamento',    'Peticionamento',              'Peticionados, represados e valor de causa.',                 'Operação jurídica', 'NG',     16, 'upcoming')
on conflict (key) do nothing;

-- Pendências (LexPre): ligada onde a Pendências já estava, com as mesmas regras de acesso
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, 'pendencias-lexpre', od.enabled
  from app.org_dashboards od
 where od.dashboard_key = 'pendencias'
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, 'pendencias-lexpre', r.scope, r.created_by
  from app.access_rules r
 where r.dashboard_key = 'pendencias'
on conflict (team_id, dashboard_key) do nothing;
