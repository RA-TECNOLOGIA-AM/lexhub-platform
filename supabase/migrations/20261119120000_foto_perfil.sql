-- =============================================================================
-- Foto de perfil: cada pessoa troca a própria foto no cartão de perfil (avatar da topbar).
--   * Bucket público 'avatars' (até 2 MB, webp/jpeg/png); o arquivo fica em '<user_id>/<nome>'.
--     Só o dono grava/apaga a própria pasta. Leitura pela URL pública (a foto aparece para todos).
--   * app.profiles: uma linha por pessoa (não por organização) com o caminho da foto.
--   * api.set_my_avatar(p_path): grava o caminho (null = tirar a foto) e devolve o anterior,
--     para o app apagar o arquivo velho do bucket.
-- O /me (API) lê app.profiles e devolve avatar_path; o front monta a URL pública.
-- Teste: supabase/tests/foto_perfil_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Bucket e regras do storage
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', true, 2097152, array['image/webp', 'image/jpeg', 'image/png'])
on conflict (id) do nothing;

create policy "avatars: dono lê a própria pasta" on storage.objects
    for select to authenticated
    using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "avatars: dono envia na própria pasta" on storage.objects
    for insert to authenticated
    with check (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "avatars: dono apaga da própria pasta" on storage.objects
    for delete to authenticated
    using (bucket_id = 'avatars' and (storage.foldername(name))[1] = auth.uid()::text);

-- ---------------------------------------------------------------------------
-- 2. Perfil (por pessoa)
-- ---------------------------------------------------------------------------
create table app.profiles (
    user_id     uuid primary key references auth.users (id) on delete cascade,
    avatar_path text check (avatar_path ~ '^[0-9a-f-]{36}/[A-Za-z0-9._-]{1,80}$'),
    updated_at  timestamptz not null default now()
);
alter table app.profiles enable row level security;
-- Sem políticas: só pela função abaixo (e a API, que lê com o papel do servidor).
grant all on app.profiles to service_role;

-- ---------------------------------------------------------------------------
-- 3. Trocar a própria foto
-- ---------------------------------------------------------------------------
create function api.set_my_avatar(p_path text) returns text
language plpgsql security definer
set search_path = ''
as $$
declare
    v_uid uuid := auth.uid();
    v_old text;
begin
    if v_uid is null then
        raise exception using errcode = '42501', message = 'Entre para trocar a foto.';
    end if;
    if p_path is not null and split_part(p_path, '/', 1) <> v_uid::text then
        raise exception using errcode = '42501', message = 'Esta foto não é sua.';
    end if;

    select avatar_path into v_old from app.profiles where user_id = v_uid;
    insert into app.profiles (user_id, avatar_path, updated_at)
    values (v_uid, p_path, now())
    on conflict (user_id) do update set avatar_path = excluded.avatar_path, updated_at = now();
    return v_old;
end;
$$;

revoke all on function api.set_my_avatar(text) from public, anon;
grant execute on function api.set_my_avatar(text) to authenticated;

-- Desfazer:
-- drop function api.set_my_avatar(text);
-- drop table app.profiles;
-- drop policy "avatars: dono lê a própria pasta" on storage.objects;
-- drop policy "avatars: dono envia na própria pasta" on storage.objects;
-- drop policy "avatars: dono apaga da própria pasta" on storage.objects;
-- delete from storage.buckets where id = 'avatars';  -- só com o bucket vazio
