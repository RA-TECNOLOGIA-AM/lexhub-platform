-- =============================================================================
-- Owners: Nicolas Gomes e Marcelo Pontes passam de Desenvolvedor (admin) para Owner na LexGroup.
--
-- Só mexe em associações que já existem (os dois já são membros ativos); não cria ninguém.
-- Em banco sem essas pessoas (CI), não faz nada.
-- =============================================================================

with alvo as (
    update app.memberships m
       set role_key = 'owner'
      from app.organizations o
     where o.id = m.org_id
       and o.slug = 'lexgroup'
       and lower(m.email) in ('drnicolas.gomes@nicolasgomesadv.com.br', 'marcelo.pontes@lexgroup.com.br')
       and m.role_key <> 'owner'
    returning m.id, m.org_id, m.email
)
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
select a.org_id, null, 'member.access_updated', 'membership', a.id::text,
       jsonb_build_object('email', a.email, 'role_key', 'owner', 'via', 'migration 20261118150000')
from alvo a;

-- =============================================================================
-- Rollback (rodar à mão se precisar desfazer):
-- update app.memberships m set role_key = 'admin'
--   from app.organizations o
--  where o.id = m.org_id and o.slug = 'lexgroup'
--    and lower(m.email) in ('drnicolas.gomes@nicolasgomesadv.com.br', 'marcelo.pontes@lexgroup.com.br');
-- =============================================================================
