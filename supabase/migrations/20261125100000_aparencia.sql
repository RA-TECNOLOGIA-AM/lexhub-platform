-- =============================================================================
-- Aparência por pessoa: o tema que cada um escolhe em Configurações → Aparência, salvo na conta
-- (vale em qualquer aparelho). Mesmo modelo do LexFlow: modo + tema claro + tema escuro + destaque.
--   * Colunas novas em app.profiles (uma linha por pessoa, criada pela foto de perfil):
--       theme_mode   'light' | 'dark'      nulo = segue o sistema
--       theme_light  id do tema claro      nulo = Claro Padrão   (ex.: 'light-github')
--       theme_dark   id do tema escuro     nulo = Escuro Padrão  (ex.: 'dark-dracula')
--       theme_accent 'tema' | id de cor | '#rrggbb' (minúsculo)  nulo = Do tema
--     O banco só confere o formato; a lista de temas vive no front (lib/themeEngine.ts),
--     e id que o front não conhece cai no padrão.
--   * api.set_my_appearance(...): grava as 4 de uma vez na linha de quem está logado.
-- O /me (API) lê essas colunas (já faz left join em app.profiles) e devolve user.appearance.
-- Teste: supabase/tests/aparencia_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Colunas
-- ---------------------------------------------------------------------------
alter table app.profiles
    add column theme_mode   text check (theme_mode in ('light', 'dark')),
    add column theme_light  text check (theme_light ~ '^[a-z0-9-]{1,40}$'),
    add column theme_dark   text check (theme_dark ~ '^[a-z0-9-]{1,40}$'),
    add column theme_accent text check (theme_accent ~ '^([a-z]{1,20}|#[0-9a-f]{6})$');

-- ---------------------------------------------------------------------------
-- 2. Salvar a própria aparência
-- ---------------------------------------------------------------------------
create function api.set_my_appearance(p_mode text, p_light text, p_dark text, p_accent text) returns void
language plpgsql security definer
set search_path = ''
as $$
declare
    v_uid uuid := auth.uid();
begin
    if v_uid is null then
        raise exception using errcode = '42501', message = 'Entre para salvar a aparência.';
    end if;

    insert into app.profiles (user_id, theme_mode, theme_light, theme_dark, theme_accent, updated_at)
    values (v_uid, p_mode, p_light, p_dark, p_accent, now())
    on conflict (user_id) do update
        set theme_mode   = excluded.theme_mode,
            theme_light  = excluded.theme_light,
            theme_dark   = excluded.theme_dark,
            theme_accent = excluded.theme_accent,
            updated_at   = now();
end;
$$;

revoke all on function api.set_my_appearance(text, text, text, text) from public, anon;
grant execute on function api.set_my_appearance(text, text, text, text) to authenticated;

-- Desfazer:
-- drop function api.set_my_appearance(text, text, text, text);
-- alter table app.profiles
--     drop column theme_mode, drop column theme_light, drop column theme_dark, drop column theme_accent;
