-- API pública: guarda o IP do último uso da chave, ao lado de last_used_at.
--   * Só o último (sobrescreve a cada leitura), não um histórico: o mínimo para o Dev vigiar a chave
--     sem ver o token (LGPD, necessidade). O histórico completo já fica no audit_log ('api.read').
--   * text, não inet: a API grava request.client.host como veio (atrás do Traefik, com proxy-headers).
--   * api_key_json passa a devolver 'last_used_ip' (tela do Dev e Configurações do dono).

alter table app.api_keys add column last_used_ip text check (char_length(last_used_ip) <= 64);
comment on column app.api_keys.last_used_ip is 'IP da última leitura pela API pública (só o último).';

create or replace function app_private.api_key_json(p_key uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', k.id,
        'user_name', m.full_name,
        'user_email', m.email,
        'status', k.status,
        'note', k.note,
        'decision_note', k.decision_note,
        'requested_at', k.requested_at,
        'decided_at', k.decided_at,
        'revoked_at', k.revoked_at,
        'last_used_at', k.last_used_at,
        'last_used_ip', k.last_used_ip,
        'sectors',
            coalesce((select jsonb_agg(jsonb_build_object('setor', b, 'base', true, 'status', 'approved')
                                       order by b)
                      from unnest(app_private.api_key_base_sectors(k.membership_id)) b), '[]'::jsonb)
            || coalesce((select jsonb_agg(jsonb_build_object(
                                    'setor', s.sector_name, 'base', false, 'status', s.status,
                                    'justificativa', s.justification, 'expires_at', s.expires_at)
                                order by s.sector_name)
                         from app.api_key_sectors s where s.key_id = k.id), '[]'::jsonb)
    )
    from app.api_keys k
    join app.memberships m on m.id = k.membership_id
    where k.id = p_key;
$$;

-- Desfazer:
-- (recriar api_key_json sem 'last_used_ip', como na 20261126230000)
-- alter table app.api_keys drop column last_used_ip;
