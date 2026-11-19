-- =============================================================================
-- Auditoria: dashboards abertos + filtro de período/tipo no banco.
--
-- 1) api.log_dashboard_view: o front chama ao abrir um dashboard (hub, menu, busca, link). Grava
--    'dashboard.view' em app.audit_log. A mesma pessoa abrindo o mesmo dashboard na mesma unidade em menos de
--    5 minutos NÃO grava de novo (F5, clique duplo, duas abas): devolve false. Trocar período/filtro não chama.
--    Só grava dashboard que a pessoa pode ver (app_private.dashboard_access: org/unidade/dashboard ativos e
--    ligados, cargo, setor ou exceção). Sem acesso = 42501, nada gravado: link para dashboard de fora do setor
--    não vira "Abriu dashboard", e ninguém enche a auditoria (que não se apaga) com chaves aleatórias.
-- 2) api.list_audit ganha período (p_from/p_to), tipo (p_actions, ou p_exclude_actions para "Outros") e pessoa
--    (p_actor, o nome mostrado na tela) e devolve { events, truncated, actors }. actors = quem aparece no período
--    e tipo (sem o filtro de pessoa, sem limite), para o campo Pessoa listar todo mundo.
--    Antes trazia só os últimos 500 eventos e o filtro era no navegador: com as aberturas, a janela viraria
--    2-3 dias. truncated = havia mais eventos que p_limit no filtro (a tela pede para estreitar o período).
--
-- Quem pode: log_dashboard_view = membro ativo da organização; list_audit = audit.view (Owner, Desenvolvedor).
-- Teste: supabase/tests/auditoria_dashboards_abertos_test.sql (termina com rollback).
-- =============================================================================

create function api.log_dashboard_view(p_org text, p_unit text, p_dashboard text) returns boolean
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org uuid;
    v_unit_id uuid;
    v_unit text;
    v_key text := trim(p_dashboard);
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids())) then
        raise exception using errcode = '42501', message = 'Você não é membro desta organização.';
    end if;

    select u.id, u.code into v_unit_id, v_unit from app.units u where u.org_id = v_org and u.code = upper(trim(p_unit));
    if v_unit is null or not exists (select 1 from app.dashboard_catalog c where c.key = v_key) then
        raise exception using errcode = '22023', message = 'Unidade ou dashboard desconhecido.';
    end if;

    if not exists (select 1 from app_private.dashboard_access(auth.uid(), v_unit_id, v_key)) then
        raise exception using errcode = '42501', message = 'Sem acesso a este dashboard nesta unidade.';
    end if;

    -- Duas chamadas ao mesmo tempo (duas abas, efeito duplo do React) não podem as duas passar pela checagem
    -- abaixo: a trava (até o fim da transação) põe uma atrás da outra, e a segunda já vê a linha da primeira.
    perform pg_advisory_xact_lock(hashtextextended('dashboard.view:' || auth.uid() || ':' || v_unit_id || ':' || v_key, 0));

    -- Repetição: mesma pessoa, dashboard e unidade nos últimos 5 minutos.
    if exists (
        select 1 from app.audit_log a
        where a.org_id = v_org
          and a.actor_user_id = auth.uid()
          and a.action = 'dashboard.view'
          and a.target_id = v_key
          and a.metadata ->> 'unit' = v_unit
          and a.created_at > now() - interval '5 minutes'
    ) then
        return false;
    end if;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'dashboard.view', 'dashboard', v_key,
            jsonb_build_object('org', lower(trim(p_org)), 'unit', v_unit));
    return true;
end;
$$;

revoke all on function api.log_dashboard_view(text, text, text) from public, anon;
grant execute on function api.log_dashboard_view(text, text, text) to authenticated;

-- list_audit com filtros: a assinatura muda, então sai a antiga (chamadas só com p_org continuam valendo).
drop function api.list_audit(text, integer);

-- p_from/p_to: null = sem limite daquele lado; p_actions: null = todos os tipos; p_exclude_actions: tipos que
-- ficam de fora ("Outros" = tudo menos os conhecidos); p_actor: null = todas as pessoas.
create function api.list_audit(
    p_org text,
    p_from timestamptz default null,
    p_to timestamptz default null,
    p_actions text[] default null,
    p_exclude_actions text[] default null,
    p_actor text default null,
    p_limit integer default 2000
) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
    v_limit integer := greatest(1, least(coalesce(p_limit, 2000), 2000));
    v_events jsonb;
    v_count integer;
    v_actors jsonb;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids_with('audit.view'))) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor veem a auditoria.';
    end if;

    -- Eventos do período e tipo, com o nome de quem fez (é por ele que a tela filtra a pessoa).
    with base as (
        select l.*,
               -- Quem fez: o nome na organização; sem associação, o e-mail; sem pessoa, o sistema.
               coalesce(m.full_name, au.email, 'Sistema') as actor_name,
               au.email as actor_email
        from app.audit_log l
        left join app.memberships m on m.org_id = l.org_id and m.user_id = l.actor_user_id
        left join auth.users au on au.id = l.actor_user_id
        where l.org_id = v_org
          and (p_from is null or l.created_at >= p_from)
          and (p_to is null or l.created_at < p_to)
          and (p_actions is null or l.action = any (p_actions))
          and (p_exclude_actions is null or not (l.action = any (p_exclude_actions)))
    ),
    -- Busca um a mais que o limite: se vier, havia mais eventos no filtro (truncated).
    page as (
        select b.*, row_number() over (order by b.created_at desc, b.id desc) as rn
        from base b
        where p_actor is null or b.actor_name = p_actor
        order by b.created_at desc, b.id desc
        limit v_limit + 1
    )
    select coalesce(jsonb_agg(
               jsonb_build_object(
                   'id', a.id::text,
                   'at', a.created_at,
                   'action', a.action,
                   'actor', a.actor_name,
                   'actorEmail', a.actor_email,
                   'targetType', a.target_type,
                   'targetId', a.target_id,
                   'targetName', case a.target_type
                       when 'dashboard' then (select c.name from app.dashboard_catalog c where c.key = a.target_id)
                       when 'unit' then (select u.name from app.units u where u.id::text = a.target_id)
                       when 'membership' then (select tm.full_name from app.memberships tm where tm.id::text = a.target_id)
                   end,
                   'metadata', a.metadata
               )
               order by a.created_at desc, a.id desc
           ) filter (where a.rn <= v_limit), '[]'::jsonb),
           count(*),
           -- Pessoas do período/tipo inteiro (sem o filtro de pessoa nem o limite), em ordem alfabética.
           (select coalesce(jsonb_agg(x.actor_name order by x.actor_name), '[]'::jsonb)
              from (select distinct b.actor_name from base b) x)
      into v_events, v_count, v_actors
    from page a;

    return jsonb_build_object('events', v_events, 'truncated', v_count > v_limit, 'actors', v_actors);
end;
$$;

revoke all on function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, integer) from public, anon;
grant execute on function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, integer) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.log_dashboard_view(text, text, text);
-- drop function api.list_audit(text, timestamptz, timestamptz, text[], text[], text, integer);
-- e recriar api.list_audit(text, integer) com o corpo de 20261119090000_auditoria_email.sql.
-- =============================================================================
