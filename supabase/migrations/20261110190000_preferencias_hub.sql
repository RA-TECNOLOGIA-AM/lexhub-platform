-- =============================================================================
-- Preferências do hub, por pessoa em cada organização (pela associação, memberships.id):
--
--   app.dashboard_favorites  dashboards favoritos (estrela no card)
--   app.hub_orders           ordem dos cards que a pessoa arrastou ([] = ordem do catálogo)
--
-- Na v1: public.usuario_dashboard_favorito e public.usuario_dashboard_ordem (não importados:
-- ninguém usa a V2 ainda). Escritas só pela API (service_role); o usuário logado só LÊ as suas.
-- Sair da organização (associação apagada) apaga as preferências junto.
-- =============================================================================

create table app.dashboard_favorites (
    membership_id uuid not null references app.memberships (id) on delete cascade,
    dashboard_key text not null references app.dashboard_catalog (key) on update cascade on delete cascade,
    created_at    timestamptz not null default now(),
    primary key (membership_id, dashboard_key)
);

create table app.hub_orders (
    membership_id uuid primary key references app.memberships (id) on delete cascade,
    keys          text[] not null default '{}' check (cardinality(keys) <= 200),
    updated_at    timestamptz not null default now()
);

create trigger hub_orders_updated_at before update on app.hub_orders
    for each row execute function app.set_updated_at();

-- RLS: cada um lê só as próprias
alter table app.dashboard_favorites enable row level security;
alter table app.hub_orders          enable row level security;

create policy dashboard_favorites_select on app.dashboard_favorites for select to authenticated
    using (membership_id in (select id from app.memberships where user_id = (select auth.uid())));

create policy hub_orders_select on app.hub_orders for select to authenticated
    using (membership_id in (select id from app.memberships where user_id = (select auth.uid())));

revoke all on app.dashboard_favorites, app.hub_orders from public, anon;
grant select on app.dashboard_favorites, app.hub_orders to authenticated;
grant all    on app.dashboard_favorites, app.hub_orders to service_role;
