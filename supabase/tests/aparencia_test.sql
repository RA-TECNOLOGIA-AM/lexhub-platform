-- =============================================================================
-- Teste de 20261125100000_aparencia.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: a1 (sem linha em app.profiles) salva a aparência; a2 já tem foto e salva a aparência
-- sem perder a foto; valores fora do formato são recusados; tudo nulo volta a "sem escolha";
-- sem login, recusado.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000a1', 'a1.aparencia@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000a2', 'a2.aparencia@exemplo.com');
insert into app.profiles (user_id, avatar_path)
values ('00000000-0000-4000-8000-0000000000a2', '00000000-0000-4000-8000-0000000000a2/foto.webp');

-- a1: primeira escolha (cria a linha)
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a1","role":"authenticated"}';

do $$
begin
    perform api.set_my_appearance('dark', 'light-github', 'dark-dracula', 'azul');
    perform api.set_my_appearance('light', 'light-github', 'dark-dracula', '#2563eb');

    -- Fora do formato: recusado pelo check (e a escolha anterior fica)
    begin
        perform api.set_my_appearance('sepia', null, null, null);
        raise exception 'FALHOU: modo "sepia" deveria ser recusado';
    exception when check_violation then null;
    end;
    begin
        perform api.set_my_appearance('light', 'Dracula!', null, null);
        raise exception 'FALHOU: id de tema com maiúscula/símbolo deveria ser recusado';
    exception when check_violation then null;
    end;
    begin
        perform api.set_my_appearance('light', null, null, '#12345');
        raise exception 'FALHOU: hex curto deveria ser recusado';
    exception when check_violation then null;
    end;
    begin
        perform api.set_my_appearance('light', null, null, '#2563EB');
        raise exception 'FALHOU: hex com maiúscula deveria ser recusado (o front grava minúsculo)';
    exception when check_violation then null;
    end;

    -- Leitura direta da tabela: proibida (só pela função e pelo /me)
    begin
        perform 1 from app.profiles;
        raise exception 'FALHOU: não deveria ler app.profiles direto';
    exception when insufficient_privilege then null;
    end;
end $$;

-- a2: já tinha foto
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a2","role":"authenticated"}';
do $$
begin
    perform api.set_my_appearance(null, null, 'dark-nord', 'tema');
end $$;

-- Sem login
set local request.jwt.claims = '{"role":"authenticated"}';
do $$
begin
    begin
        perform api.set_my_appearance('dark', null, null, null);
        raise exception 'FALHOU: sem login deveria ser recusado';
    exception when insufficient_privilege then null;
    end;
end $$;

reset role;
do $$
declare
    r record;
begin
    select * into r from app.profiles where user_id = '00000000-0000-4000-8000-0000000000a1';
    if r.theme_mode is distinct from 'light' or r.theme_light is distinct from 'light-github'
       or r.theme_dark is distinct from 'dark-dracula' or r.theme_accent is distinct from '#2563eb' then
        raise exception 'FALHOU: a1 deveria ter a última escolha válida (light, light-github, dark-dracula, #2563eb), tem %', r;
    end if;

    select * into r from app.profiles where user_id = '00000000-0000-4000-8000-0000000000a2';
    if r.avatar_path is distinct from '00000000-0000-4000-8000-0000000000a2/foto.webp' then
        raise exception 'FALHOU: salvar a aparência não pode apagar a foto';
    end if;
    if r.theme_mode is not null or r.theme_light is not null
       or r.theme_dark is distinct from 'dark-nord' or r.theme_accent is distinct from 'tema' then
        raise exception 'FALHOU: a2 deveria ter (null, null, dark-nord, tema), tem %', r;
    end if;
end $$;

-- Tudo nulo = volta a "sem escolha"
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a1","role":"authenticated"}';
do $$
begin
    perform api.set_my_appearance(null, null, null, null);
end $$;

reset role;
do $$
begin
    if exists (select 1 from app.profiles
                where user_id = '00000000-0000-4000-8000-0000000000a1'
                  and num_nonnulls(theme_mode, theme_light, theme_dark, theme_accent) > 0) then
        raise exception 'FALHOU: tudo nulo deveria limpar a aparência';
    end if;
    raise notice 'OK: aparencia';
end $$;

rollback;
