-- Desenvolvedor (role_key 'admin') também pode pedir chave de API, como o Owner: vale em todas as unidades ativas.
-- Os setores continuam decidindo o alcance (base = equipes da pessoa; sem equipe, pede setores extras).
-- create or replace mantém os grants de 20261126230000_api_publica.sql.

create or replace function app_private.api_key_eligible(p_user uuid, p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select exists (
        select 1 from app.memberships m
        where m.org_id = p_org and m.user_id = p_user and m.status = 'active'
          and (m.role_key in ('owner', 'admin')
               or exists (select 1 from app.membership_units mu
                          join app.units u on u.id = mu.unit_id and u.active
                          where mu.membership_id = m.id and mu.role_key in ('gestor', 'controller')))
    );
$$;

create or replace function app_private.api_key_units(p_membership uuid) returns setof uuid
language sql stable security definer
set search_path = ''
as $$
    select u.id
    from app.memberships m
    join app.units u on u.org_id = m.org_id and u.active
    where m.id = p_membership and m.status = 'active'
      and (m.role_key in ('owner', 'admin')
           or exists (select 1 from app.membership_units mu
                      where mu.membership_id = m.id and mu.unit_id = u.id
                        and mu.role_key in ('gestor', 'controller')));
$$;

-- Mesma função de 20261126230000, só com a mensagem de permissão nova.
create or replace function api.request_api_key(p_org text, p_note text, p_extras jsonb) returns uuid
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org     uuid := app_private.api_key_org(p_org);
    v_m       uuid;
    v_key     uuid;
    v_base    text[];
    v_allowed text[];
    e         jsonb;
    v_setor   text;
    v_just    text;
    v_val     date;
begin
    if not app_private.api_key_eligible(auth.uid(), v_org) then
        raise exception using errcode = '42501',
            message = 'Só Owner, Desenvolvedor, Gestor ou Controller podem pedir chave de API.';
    end if;
    select m.id into v_m from app.memberships m
    where m.org_id = v_org and m.user_id = auth.uid() and m.status = 'active';

    if exists (select 1 from app.api_keys k
               where k.org_id = v_org and k.user_id = auth.uid() and k.status in ('pending', 'active')) then
        raise exception using errcode = 'P0001', message = 'Você já tem uma chave pedida ou ativa nesta organização.';
    end if;

    v_base := app_private.api_key_base_sectors(v_m);
    select coalesce(array_agg(distinct t.name), '{}') into v_allowed
    from app.teams t where t.active and t.unit_id in (select app_private.api_key_units(v_m));

    p_extras := coalesce(p_extras, '[]'::jsonb);
    if jsonb_typeof(p_extras) <> 'array' then
        raise exception using errcode = 'P0001', message = 'Setores extras inválidos.';
    end if;
    if cardinality(v_base) = 0 and jsonb_array_length(p_extras) = 0 then
        raise exception using errcode = 'P0001',
            message = 'Você não tem setor cadastrado: peça ao menos um setor extra.';
    end if;

    insert into app.api_keys (org_id, user_id, membership_id, note)
    values (v_org, auth.uid(), v_m, nullif(trim(p_note), ''))
    returning id into v_key;

    for e in select * from jsonb_array_elements(p_extras) loop
        v_setor := trim(e ->> 'setor');
        v_just  := trim(e ->> 'justificativa');
        begin
            v_val := (e ->> 'validade')::date;
        exception when others then
            raise exception using errcode = 'P0001', message = 'Validade inválida.';
        end;
        if v_setor is null or not (v_setor = any (v_allowed)) then
            raise exception using errcode = 'P0001', message = format('Setor "%s" não disponível.', v_setor);
        end if;
        if v_setor = any (v_base) then
            raise exception using errcode = 'P0001', message = format('"%s" já é um setor seu.', v_setor);
        end if;
        if v_just is null or length(v_just) < 10 then
            raise exception using errcode = 'P0001',
                message = 'A justificativa do setor extra precisa de pelo menos 10 caracteres.';
        end if;
        if v_val is null or v_val <= current_date or v_val > current_date + 365 then
            raise exception using errcode = 'P0001',
                message = 'A validade do setor extra deve ser entre amanhã e 365 dias.';
        end if;
        insert into app.api_key_sectors (key_id, sector_name, justification, expires_at)
        values (v_key, v_setor, v_just, (v_val + 1)::timestamp at time zone 'America/Sao_Paulo');
    end loop;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'api_key.requested', 'api_key', v_key::text,
            jsonb_build_object('extras', p_extras));
    return v_key;
end;
$$;
