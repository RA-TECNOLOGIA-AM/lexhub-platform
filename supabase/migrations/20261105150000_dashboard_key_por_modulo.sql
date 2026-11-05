-- =============================================================================
-- Modularização: a chave do dashboard identifica o MÓDULO, nunca a unidade.
-- A unidade vem de app.unit_dashboards (o mesmo módulo é ligado em NG, LA, RJ...).
-- V1 tinha uma página por escritório (Pendencias NG / LA / RJ); na V2 é um módulo só.
-- =============================================================================

update app.dashboards
set key = 'pendencias',
    name = 'Pendências',
    description = 'Pendências iniciais (MVP)'
where key = 'pendencias-ng';

-- Se um dia a chave de um módulo mudar, as tabelas que apontam para ela acompanham.
alter table app.unit_dashboards
    drop constraint unit_dashboards_dashboard_key_fkey,
    add constraint unit_dashboards_dashboard_key_fkey
        foreign key (dashboard_key) references app.dashboards (key)
        on update cascade on delete cascade;

alter table app.dashboard_grants
    drop constraint dashboard_grants_unit_id_dashboard_key_fkey,
    add constraint dashboard_grants_unit_id_dashboard_key_fkey
        foreign key (unit_id, dashboard_key) references app.unit_dashboards (unit_id, dashboard_key)
        on update cascade on delete cascade;
