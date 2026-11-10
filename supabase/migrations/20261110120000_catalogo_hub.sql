-- =============================================================================
-- Catálogo do hub: o que cada card mostra (DashboardSummary do front).
--
--   area          seção do hub ("Operação jurídica")
--   source        fonte dos dados ("LexPre")
--   max_delay_min passou disso sem sincronizar = "Fonte atrasada"
--   sort_order    ordem no hub (das áreas e dos cards dentro delas)
--   status        available = abre; upcoming = "Em breve" (só título e área)
--
-- synced_at não fica aqui: vem do cache de 5 min (por fonte e unidade).
-- =============================================================================

alter table app.dashboard_catalog
    add column area          text,
    add column source        text not null default 'LexPre',
    add column max_delay_min int  not null default 60 check (max_delay_min > 0),
    add column sort_order    int  not null default 0,
    add column status        text not null default 'available'
        check (status in ('available', 'upcoming'));

-- Textos iguais aos do hub (o card mostra name como título e description embaixo)
update app.dashboard_catalog
set name        = 'Protocolo',
    description = 'Protocolados, represados e devoluções do setor Protocolo.',
    area        = 'Operação jurídica',
    sort_order  = 10
where key = 'protocolo-lexpre';

update app.dashboard_catalog
set name        = 'Pendências',
    description = 'Pendências abertas, resolvidas e tempo de resolução.',
    area        = 'Operação jurídica',
    sort_order  = 20
where key = 'pendencias';

-- Card sem área ficaria sem seção no hub: obrigatória daqui em diante.
update app.dashboard_catalog set area = 'Outros' where area is null;

alter table app.dashboard_catalog
    alter column area set not null,
    add constraint dashboard_catalog_area_ck check (length(trim(area)) > 0);