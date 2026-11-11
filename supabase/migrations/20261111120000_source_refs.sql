-- =============================================================================
-- Quem é quem nos bancos de origem: unidade -> id (unit_source_refs) e pessoa -> funcionário (member_source_refs).
-- Unidade da V2 -> id dela em cada banco de origem.
--
-- Na v1 isso era fixo no código (ex.: LexPre ESCRITORIO_NGAM = 1, LAAM = 2, LARJ = 3) e não bate
-- com units.legacy_companhia_id. Aqui fica por dado: unidade nova não precisa de deploy.
--   source  banco de origem, mesmo nome do .env da API ('lexpre', 'lexflow', 'ng', 'laadv')
--   ref     id da unidade naquele banco (texto: cada fonte tem o seu tipo)
-- Escrita só pela API / painel (service_role); membros da organização só leem.
-- =============================================================================

create table app.unit_source_refs (
    unit_id    uuid not null references app.units (id) on delete cascade,
    source     text not null check (source ~ '^[a-z][a-z0-9_]{1,31}$'),
    ref        text not null check (length(trim(ref)) > 0),
    created_at timestamptz not null default now(),
    primary key (unit_id, source)
);

alter table app.unit_source_refs enable row level security;

create policy unit_source_refs_select on app.unit_source_refs for select to authenticated
    using (unit_id in (select u.id from app.units u
                        where u.org_id = any ((select app_private.my_org_ids())::uuid[])));

revoke all on app.unit_source_refs from public, anon;
grant select on app.unit_source_refs to authenticated;
grant all    on app.unit_source_refs to service_role;

-- LexPre da LexGroup: mesmos ids da v1 (protocolo_setor_lexpre.py).
insert into app.unit_source_refs (unit_id, source, ref)
select u.id, 'lexpre', v.ref
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
  join (values ('NG', '1'), ('LA', '2'), ('RJ', '3')) as v (code, ref) on v.code = u.code
on conflict do nothing;

-- =============================================================================
-- Pessoa (associação na organização) -> como ela aparece em cada banco de origem.
--   ref  ex.: no LexPre, o nome do funcionário como vem nas linhas da v1 ("funcionario").
-- Usado para o colaborador ver só a própria comissão (e, no futuro, o escopo 'own').
-- Sem vínculo = vê só o que não depende da pessoa (nunca o de outra pessoa).
-- Preenchido depois (ex.: a partir de usuario_atendente_comercial da v1).
-- =============================================================================

create table app.member_source_refs (
    membership_id uuid not null references app.memberships (id) on delete cascade,
    source        text not null check (source ~ '^[a-z][a-z0-9_]{1,31}$'),
    ref           text not null check (length(trim(ref)) > 0),
    created_at    timestamptz not null default now(),
    primary key (membership_id, source)
);

alter table app.member_source_refs enable row level security;

-- cada um vê o próprio vínculo; quem gerencia membros vê os da sua organização/companhia
create policy member_source_refs_select on app.member_source_refs for select to authenticated
    using (
        membership_id in (select id from app.memberships where user_id = (select auth.uid()))
        or membership_id = any ((select app_private.my_managed_membership_ids())::uuid[])
    );

revoke all on app.member_source_refs from public, anon;
grant select on app.member_source_refs to authenticated;
grant all    on app.member_source_refs to service_role;
