-- =============================================================================
-- Áreas do hub reorganizadas. Ordem das seções (HUB_AREAS em apps/web/src/lib/hubOrder.ts):
--   Comercial · Pré-protocolo · Tecnologia · Jurídico · Financeiro · Estratégico
--
--   Comercial      Comercial, Comissão Comercial, Marketing e NPS (LexPre e NG): não muda
--   Pré-protocolo  ex-"Operação jurídica": Pré-protocolo (geral) primeiro, depois Pendências,
--                  Organização de Documentos, Peticionamento e Protocolo (LexPre e NG)
--   Jurídico       ex-"Execução e recursal": Execução, Acordos e Recursal
--   Financeiro     Despesas (ex-"Gestão")
--   Estratégico    Estratégico e Meta anual (ex-"Gestão")
--   Tecnologia     ainda sem dashboards (as análises vão ser migradas)
-- =============================================================================

update app.dashboard_catalog set area = 'Pré-protocolo' where area = 'Operação jurídica';

-- Ordem dentro de Pré-protocolo: o geral, depois cada setor (par LexPre + NG lado a lado)
update app.dashboard_catalog c
   set sort_order = v.sort_order
  from (values
        ('pre-protocolo',         10),
        ('pendencias-lexpre',     11),
        ('pendencias',            12),
        ('org-documentos-lexpre', 13),
        ('org-documentos',        14),
        ('peticionamento-lexpre', 15),
        ('peticionamento',        16),
        ('protocolo-lexpre',      17),
        ('protocolo',             18)
       ) as v(key, sort_order)
 where c.key = v.key;

update app.dashboard_catalog set area = 'Jurídico' where key in ('execucao', 'acordos', 'recursal');
update app.dashboard_catalog set area = 'Financeiro', sort_order = 100 where key = 'despesas';
update app.dashboard_catalog set area = 'Estratégico', sort_order = 110 where key = 'estrategico';
update app.dashboard_catalog set area = 'Estratégico', sort_order = 120 where key = 'meta-anual';
