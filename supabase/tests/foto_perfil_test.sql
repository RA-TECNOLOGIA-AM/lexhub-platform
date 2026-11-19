-- =============================================================================
-- Teste de 20261119120000_foto_perfil.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: u1 põe uma foto, troca (recebe o caminho velho), tenta gravar na pasta de u2 e tira a foto.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000f1', 'u1.foto@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000f2', 'u2.foto@exemplo.com');

set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000f1","role":"authenticated"}';

do $$
begin
    if api.set_my_avatar('00000000-0000-4000-8000-0000000000f1/a.webp') is not null then
        raise exception 'FALHOU: primeira foto não tem anterior';
    end if;
    if api.set_my_avatar('00000000-0000-4000-8000-0000000000f1/b.webp')
       <> '00000000-0000-4000-8000-0000000000f1/a.webp' then
        raise exception 'FALHOU: trocar deveria devolver o caminho anterior';
    end if;

    begin
        perform api.set_my_avatar('00000000-0000-4000-8000-0000000000f2/x.webp');
        raise exception 'FALHOU: não pode usar a pasta de outra pessoa';
    exception when insufficient_privilege then null;
    end;

    -- Leitura/gravação direta na tabela: proibida (só pela função)
    begin
        perform 1 from app.profiles;
        raise exception 'FALHOU: não deveria ler app.profiles direto';
    exception when insufficient_privilege then null;
    end;

    if api.set_my_avatar(null) <> '00000000-0000-4000-8000-0000000000f1/b.webp' then
        raise exception 'FALHOU: tirar a foto deveria devolver o caminho anterior';
    end if;
end $$;

reset role;
do $$
begin
    if (select avatar_path from app.profiles where user_id = '00000000-0000-4000-8000-0000000000f1') is not null then
        raise exception 'FALHOU: a foto deveria ter saído';
    end if;
    raise notice 'OK: foto_perfil';
end $$;

rollback;
