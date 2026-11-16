begin;

do $$
begin
    if not has_table_privilege('service_role', 'api.device_auth_sessions', 'select')
       or not has_table_privilege('service_role', 'api.device_auth_sessions', 'insert')
       or not has_table_privilege('service_role', 'api.device_auth_sessions', 'update')
       or not has_table_privilege('service_role', 'api.device_auth_sessions', 'delete') then
        raise exception 'service_role precisa operar na tabela de sessões';
    end if;
    if has_table_privilege('authenticated', 'api.device_auth_sessions', 'select')
       or has_table_privilege('anon', 'api.device_auth_sessions', 'select') then
        raise exception 'usuários do front não podem ler sessões de dispositivos';
    end if;
    if has_function_privilege(
        'authenticated', 'api.approve_device_auth_session(text,uuid)', 'execute'
    ) then
        raise exception 'authenticated não pode chamar funções internas de dispositivo';
    end if;
end;
$$;

insert into auth.users (id, email)
values ('30000000-0000-0000-0000-000000000001', 'device-auth-test@example.com');

set local role service_role;

do $$
declare
    v_device_code text := repeat('a', 64);
    v_user_code   text := repeat('b', 64);
    v_claim_id    uuid := '30000000-0000-0000-0000-000000000002';
    v_result      text;
    v_user_id     uuid;
    v_consumed    boolean;
begin
    if not api.consume_device_auth_rate_limit(repeat('c', 64), 2, 60)
       or not api.consume_device_auth_rate_limit(repeat('c', 64), 2, 60)
       or api.consume_device_auth_rate_limit(repeat('c', 64), 2, 60) then
        raise exception 'o limite por janela não foi aplicado atomicamente';
    end if;

    insert into api.device_auth_sessions (device_code, user_code, expires_at)
    values (v_device_code, v_user_code, clock_timestamp() + interval '10 minutes');

    if api.approve_device_auth_session(v_user_code, '30000000-0000-0000-0000-000000000001') <> 'approved' then
        raise exception 'uma sessão pendente válida deveria ser aprovada';
    end if;

    select c.result, c.user_id into v_result, v_user_id
      from api.claim_device_auth_session(v_device_code, v_claim_id) c;
    if v_result <> 'approved' or v_user_id <> '30000000-0000-0000-0000-000000000001' then
        raise exception 'a sessão aprovada deveria ser reivindicada pelo backend';
    end if;

    -- Em dois comandos: num comando só, o "exists" usa a foto do banco de antes do comando e
    -- ainda enxergaria a linha que a própria função acabou de apagar.
    v_consumed := api.finish_device_auth_session(v_device_code, v_claim_id, true);
    if not v_consumed then
        raise exception 'a sessão aprovada deveria ser consumida';
    end if;
    if exists (select 1 from api.device_auth_sessions where device_code = v_device_code) then
        raise exception 'a sessão consumida deveria ter saído da tabela';
    end if;
    if api.finish_device_auth_session(v_device_code, v_claim_id, true) then
        raise exception 'a sessão aprovada deveria ser consumida uma única vez';
    end if;
end;
$$;

rollback;
