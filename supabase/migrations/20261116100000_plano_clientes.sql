-- =============================================================================
-- Plano e cobrança + Clientes (plataforma): as duas telas leem o Supabase direto (sem a API em Python).
--
-- Aditiva: cria 3 tabelas (planos, assinatura de cada organização, faturas), 1 coluna
-- (organizations.platform_owner), 2 permissões, 4 auxiliares e 2 funções; troca api.my_admin_permissions
-- (ganha 'billing' e 'clients', para o menu esconder as abas).
-- Os planos são para as operações novas que entrarem. A LexGroup (NG, LAAM, LARJ...) já é Pro, sem teto.
-- Quem vê (Owner e Desenvolvedor, porque são eles que dão acesso às operações):
--   * api.get_billing: billing.view (Owner, Desenvolvedor) da organização, ou a equipe RA (platform_staff);
--   * api.list_clients: clients.view (Owner, Desenvolvedor) da organização dona da plataforma (LexGroup),
--     ou a equipe RA. Owner de uma operação cliente NÃO vê as outras (isolamento entre clientes).
-- Preços ainda em descoberta: monthly_price/amount null = "a definir" (a tela mostra [PREÇO]/[VALOR]).
-- Os limites ficam na assinatura (copiados do plano), para um contrato poder fugir da tabela
-- (Enterprise sempre; ou um Pro com mais assentos). Limite null = sem teto. Uso (assentos, unidades,
-- fontes) é contado ao vivo. Sem assinatura = em implantação ('onboarding'), com os limites do Starter.
-- Teste: supabase/tests/plano_clientes_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Tabelas
-- ---------------------------------------------------------------------------
-- O catálogo de planos (o mesmo para todas as organizações). Limites = o padrão da tabela.
create table app.plans (
    key            text primary key check (key in ('starter', 'pro', 'enterprise')),
    name           text not null,
    monthly_price  numeric(12, 2) check (monthly_price >= 0), -- null = ainda não definido
    custom         boolean not null default false,            -- true = "Sob consulta"
    tagline        text not null default '',
    features       text[] not null default '{}',
    seat_limit     integer not null check (seat_limit > 0),
    unit_limit     integer not null check (unit_limit > 0),
    source_limit   integer not null check (source_limit > 0),
    history_months integer not null check (history_months > 0),
    sort_order     integer not null default 0
);

-- A assinatura de cada organização (uma por organização). plan_key null = em implantação.
create table app.subscriptions (
    org_id          uuid primary key references app.organizations (id) on delete cascade,
    plan_key        text references app.plans (key) on update cascade,
    status          text not null default 'active' check (status in ('active', 'past_due', 'canceled')),
    renews_on       date not null default (date_trunc('month', now()) + interval '1 month')::date,
    seat_limit      integer check (seat_limit > 0),     -- null = sem teto
    unit_limit      integer check (unit_limit > 0),     -- null = sem teto
    source_limit    integer check (source_limit > 0),   -- null = sem teto
    history_months  integer check (history_months > 0), -- null = sem teto
    payment_methods text[] not null default '{boleto,PIX}',
    gateway         text, -- null = gateway ainda não escolhido
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- As faturas (uma por mês). Ficam vazias até a cobrança existir.
create table app.invoices (
    id         uuid primary key default gen_random_uuid(),
    org_id     uuid not null references app.organizations (id) on delete cascade,
    month      date not null check (extract(day from month) = 1), -- 1º dia do mês de referência
    amount     numeric(12, 2) check (amount >= 0),                -- null = valor ainda não definido
    status     text not null default 'open' check (status in ('paid', 'open', 'overdue')),
    nfse       text not null default 'pending' check (nfse in ('issued', 'pending')),
    created_at timestamptz not null default now(),
    unique (org_id, month)
);

create trigger set_updated_at before update on app.subscriptions
    for each row execute function app.set_updated_at();

-- Sem policy para authenticated: ninguém lê direto; as telas usam as funções (security definer).
alter table app.plans enable row level security;
alter table app.subscriptions enable row level security;
alter table app.invoices enable row level security;
revoke all on app.plans, app.subscriptions, app.invoices from public, anon, authenticated;
grant all on app.plans, app.subscriptions, app.invoices to service_role;

-- ---------------------------------------------------------------------------
-- 2. Dados: os planos do protótipo e a assinatura das organizações que já existem
-- ---------------------------------------------------------------------------
insert into app.plans (key, name, monthly_price, custom, tagline, features,
                       seat_limit, unit_limit, source_limit, history_months, sort_order) values
    ('starter', 'Starter', null, false, 'Um escritório começando a medir a operação',
     array['1 unidade e 10 assentos', '3 fontes de dados', 'Catálogo essencial de dashboards', '12 meses de histórico'],
     10, 1, 3, 12, 1),
    ('pro', 'Pro', null, false, 'Grupos com várias unidades e equipes',
     array['Até 5 unidades e 60 assentos', '15 fontes de dados', 'Catálogo completo e consolidados', '24 meses de histórico'],
     60, 5, 15, 24, 2),
    -- Enterprise: os limites daqui são só o ponto de partida; o contrato define os da assinatura.
    ('enterprise', 'Enterprise', null, true, 'Redes de escritórios e departamentos jurídicos',
     array['Unidades e assentos sob medida', 'Login corporativo (SSO)', 'Papéis personalizados', 'SLA e implantação dedicada'],
     200, 20, 50, 60, 3);

-- A organização dona da plataforma: o Owner e o Desenvolvedor dela veem a tela Clientes.
alter table app.organizations add column platform_owner boolean not null default false;
update app.organizations set platform_owner = true where slug = 'lexgroup';

-- LexGroup no Pro, sem teto (já usa mais que a tabela do Pro: 74 assentos em 16/11).
-- As outras organizações (se houver) ficam em implantação, com os limites do Starter.
insert into app.subscriptions (org_id, plan_key, seat_limit, unit_limit, source_limit, history_months)
select o.id, 'pro', null, null, null, null
from app.organizations o
where o.slug = 'lexgroup'
on conflict (org_id) do nothing;

insert into app.subscriptions (org_id, plan_key, seat_limit, unit_limit, source_limit, history_months)
select o.id, null, p.seat_limit, p.unit_limit, p.source_limit, p.history_months
from app.organizations o
cross join app.plans p
where p.key = 'starter' and o.slug <> 'lexgroup'
on conflict (org_id) do nothing;

-- ---------------------------------------------------------------------------
-- 3. Permissões: ver Plano e cobrança (Owner já tinha billing.manage, que ninguém usa ainda) e Clientes
-- ---------------------------------------------------------------------------
insert into app.role_permissions (role_key, permission) values
    ('owner', 'billing.view'),
    ('admin', 'billing.view'),
    ('owner', 'clients.view'),
    ('admin', 'clients.view')
on conflict do nothing;

-- ---------------------------------------------------------------------------
-- 4. Auxiliares
-- ---------------------------------------------------------------------------
-- A assinatura da organização; sem linha = em implantação com os limites do Starter.
create function app_private.subscription_of(p_org uuid)
returns table (plan_key text, status text, renews_on date, seat_limit integer, unit_limit integer,
               source_limit integer, history_months integer, payment_methods text[], gateway text,
               monthly_price numeric)
language sql stable security definer
set search_path = ''
as $$
    -- Com assinatura, os limites dela (null = sem teto); sem assinatura, os do Starter.
    select s.plan_key,
           coalesce(s.status, 'active'),
           coalesce(s.renews_on, (date_trunc('month', now()) + interval '1 month')::date),
           case when s.org_id is null then st.seat_limit else s.seat_limit end,
           case when s.org_id is null then st.unit_limit else s.unit_limit end,
           case when s.org_id is null then st.source_limit else s.source_limit end,
           case when s.org_id is null then st.history_months else s.history_months end,
           coalesce(s.payment_methods, '{boleto,PIX}'),
           s.gateway,
           p.monthly_price
    from app.plans st
    left join app.subscriptions s on s.org_id = p_org
    left join app.plans p on p.key = s.plan_key
    where st.key = 'starter';
$$;

-- O que a organização usa agora: membros ativos (convite pendente não ocupa assento),
-- unidades ativas e fontes ativas.
create function app_private.usage_of(p_org uuid)
returns table (seats integer, units integer, sources integer)
language sql stable security definer
set search_path = ''
as $$
    select (select count(*)::integer from app.memberships m where m.org_id = p_org and m.status = 'active'),
           (select count(*)::integer from app.units u where u.org_id = p_org and u.active),
           (select count(*)::integer from app.data_sources d where d.org_id = p_org and d.active);
$$;

-- Fontes atrasadas ou com falha agora. Mesma regra do status 'late' de api.list_sources
-- (já sincronizou alguma vez, e: falhou depois do último sucesso ou o último sucesso passou de 20 min).
create function app_private.failing_sources_of(p_org uuid) returns integer
language sql stable security definer
set search_path = ''
as $$
    select count(*)::integer
    from app.data_sources ds
    left join lateral (
        select max(r.finished_at) as at from app.source_sync_runs r where r.source_id = ds.id and r.ok
    ) last_ok on true
    where ds.org_id = p_org
      and ds.active
      and exists (select 1 from app.source_sync_runs r where r.source_id = ds.id)
      and (
          last_ok.at is null
          or last_ok.at < now() - interval '20 minutes'
          or exists (select 1 from app.source_sync_runs r
                     where r.source_id = ds.id and r.ok = false and r.finished_at > last_ok.at)
      );
$$;

-- Vê a tela Clientes: equipe RA, ou Owner/Desenvolvedor ativo da organização dona da plataforma.
-- Não depende da organização aberta na tela (Clientes fica fora dela, em /plataforma).
create function app_private.can_see_clients() returns boolean
language sql stable security definer
set search_path = ''
as $$
    select app_private.is_platform_staff()
        or exists (
            select 1 from app.organizations o
            where o.platform_owner and o.id = any (app_private.my_org_ids_with('clients.view'))
        );
$$;

revoke all on function app_private.subscription_of(uuid) from public, anon, authenticated;
revoke all on function app_private.can_see_clients() from public, anon;
grant execute on function app_private.can_see_clients() to authenticated;
revoke all on function app_private.usage_of(uuid) from public, anon, authenticated;
revoke all on function app_private.failing_sources_of(uuid) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 5. api.get_billing: a tela Plano e cobrança (formato BillingResponse do front)
-- ---------------------------------------------------------------------------
create function api.get_billing(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
    s     record;
    u     record;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids_with('billing.view'))
                             or app_private.is_platform_staff()) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor veem o plano e a cobrança.';
    end if;

    select * into s from app_private.subscription_of(v_org);
    select * into u from app_private.usage_of(v_org);

    return jsonb_build_object(
        'current', jsonb_build_object(
            'plan', coalesce(s.plan_key, 'onboarding'),
            'status', s.status,
            'renewsOn', s.renews_on,
            'paymentMethods', to_jsonb(s.payment_methods),
            'gateway', s.gateway
        ),
        'usage', jsonb_build_array(
            jsonb_build_object('key', 'seats', 'label', 'Assentos', 'used', u.seats, 'total', s.seat_limit),
            jsonb_build_object('key', 'units', 'label', 'Unidades', 'used', u.units, 'total', s.unit_limit),
            jsonb_build_object('key', 'sources', 'label', 'Fontes de dados', 'used', u.sources, 'total', s.source_limit),
            -- Histórico: a janela que o plano guarda (os dados vêm da v1, então ela já está cheia).
            -- Sem teto, a linha nem aparece (não há janela para mostrar).
            jsonb_build_object('key', 'history', 'label', 'Histórico', 'used', s.history_months,
                               'total', s.history_months, 'unit', 'meses')
        ) - case when s.history_months is null then 3 else 99 end,
        'plans', (
            select jsonb_agg(jsonb_build_object(
                'key', p.key, 'name', p.name, 'monthlyPrice', p.monthly_price, 'custom', p.custom,
                'tagline', p.tagline, 'features', to_jsonb(p.features)
            ) order by p.sort_order)
            from app.plans p
        ),
        'invoices', coalesce((
            select jsonb_agg(jsonb_build_object(
                'id', i.id::text, 'month', to_char(i.month, 'YYYY-MM'), 'amount', i.amount,
                'status', i.status, 'nfse', i.nfse
            ) order by i.month desc)
            from app.invoices i
            where i.org_id = v_org
        ), '[]'::jsonb)
    );
end;
$$;

revoke all on function api.get_billing(text) from public, anon;
grant execute on function api.get_billing(text) to authenticated;

-- ---------------------------------------------------------------------------
-- 6. api.list_clients: a tela Clientes (formato ClientsResponse do front)
-- ---------------------------------------------------------------------------
create function api.list_clients() returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
begin
    if not app_private.can_see_clients() then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor da LexGroup veem os clientes.';
    end if;

    return (
        select jsonb_build_object(
            'clients', coalesce(jsonb_agg(c.item order by c.name), '[]'::jsonb),
            -- Receita: soma dos planos ativos com preço. Algum plano ativo sem preço = ainda não dá para somar.
            'monthlyRevenue', case
                when bool_or(c.paying and c.price is null) then null
                when bool_or(c.paying) then sum(c.price) filter (where c.paying)
            end
        )
        from (
            select o.name,
                   s.plan_key is not null and s.status = 'active' as paying,
                   s.monthly_price as price,
                   jsonb_build_object(
                       'slug', o.slug,
                       'name', o.name,
                       'sub', u.units || case when u.units = 1 then ' unidade' else ' unidades' end
                              || ' · cliente desde ' || to_char(o.created_at, 'MM/YYYY'),
                       'plan', coalesce(s.plan_key, 'onboarding'),
                       'seats', jsonb_build_object('used', u.seats, 'total', s.seat_limit),
                       'failingSources', app_private.failing_sources_of(o.id),
                       'billing', case
                           when s.status = 'past_due'
                             or exists (select 1 from app.invoices i where i.org_id = o.id and i.status = 'overdue')
                               then 'overdue'
                           when s.plan_key is null then 'onboarding_paid'
                           else 'ok'
                       end
                   ) as item
            from app.organizations o
            cross join lateral app_private.subscription_of(o.id) s
            cross join lateral app_private.usage_of(o.id) u
            where o.active
        ) c
    );
end;
$$;

revoke all on function api.list_clients() from public, anon;
grant execute on function api.list_clients() to authenticated;

-- ---------------------------------------------------------------------------
-- 7. Menu: api.my_admin_permissions ganha 'billing' e 'clients' (mesmo corpo de 20261113230000_auditoria.sql)
-- ---------------------------------------------------------------------------
create or replace function api.my_admin_permissions(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null then
        return jsonb_build_object('access', false, 'members', false, 'sources', false, 'audit', false,
                                  'billing', false, 'clients', app_private.can_see_clients());
    end if;
    return jsonb_build_object(
        'access', cardinality(app_private.access_scope(v_org)) > 0,
        'members', cardinality(app_private.members_scope(v_org)) > 0,
        'sources', cardinality(app_private.sources_scope(v_org)) > 0,
        'audit', v_org = any (app_private.my_org_ids_with('audit.view')),
        'billing', v_org = any (app_private.my_org_ids_with('billing.view')) or app_private.is_platform_staff(),
        'clients', app_private.can_see_clients()
    );
end;
$$;

-- =============================================================================
-- Rollback:
-- (recriar api.my_admin_permissions com o corpo de 20261113230000_auditoria.sql)
-- drop function api.list_clients();
-- drop function api.get_billing(text);
-- drop function app_private.can_see_clients();
-- drop function app_private.failing_sources_of(uuid);
-- drop function app_private.usage_of(uuid);
-- drop function app_private.subscription_of(uuid);
-- delete from app.role_permissions where permission in ('billing.view', 'clients.view');
-- alter table app.organizations drop column platform_owner;
-- drop table app.invoices; drop table app.subscriptions; drop table app.plans;
-- =============================================================================
