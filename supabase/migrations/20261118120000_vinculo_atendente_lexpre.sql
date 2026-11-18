-- =============================================================================
-- Vínculo pessoa -> atendente no LexPre (app.member_source_refs, source = 'lexpre').
--
-- A Comissão Comercial (LexPre) mostra a cada colaborador SÓ a própria comissão (own_rows_only):
-- a API procura o atendente da pessoa aqui. A tabela estava vazia, então a página zerava para todo
-- colaborador. Cópia de usuario_atendente_comercial da v1 (18/11/2026; mesmos user_id, auth.users
-- foi copiado da v1). O ref é o nome do atendente exatamente como vem nas linhas do LexPre.
--
-- Quem gere a unidade (Desenvolvedor/Owner em tudo; Gestor/Controller na unidade) continua vendo a de
-- todos pela permissão do cargo, sem vínculo.
-- =============================================================================

insert into app.member_source_refs (membership_id, source, ref)
select m.id, 'lexpre', v.atendente
  from (values
        ('9c49a5dc-5ce3-4604-b12b-b41e97af6113'::uuid, 'Ana'),
        ('e56dcd9f-4793-4ffe-ad46-0ce6cc5ac589'::uuid, 'Isabelle'),
        ('dc488613-190e-4646-8683-8826f14e5c1b'::uuid, 'Jobson'),
        ('9aa4295a-3fff-4c7e-aab6-7f355842269e'::uuid, 'Luam'),
        ('7f76caf9-441f-46f9-a7ba-754294d16b5a'::uuid, 'Maria Garcez'),
        ('086630a5-b67b-4395-bcea-d79f3e980be6'::uuid, 'Nayla'),
        ('7277323e-1eab-4d2a-abe1-b73734a4d13a'::uuid, 'Patricia'),
        ('1328b35f-b75f-4c50-9ba2-689e5dc5c21d'::uuid, 'Taissa'),
        ('5e83db6c-a37e-4635-8e69-80b4f98aceb2'::uuid, 'Thaís'),
        ('1423dc33-c312-4480-9e0b-edfccdc7a026'::uuid, 'Wellison Alexandre'),
        ('9d37ba75-7b6f-4a12-8cac-5a7c11cc368f'::uuid, 'Yara')
       ) as v (user_id, atendente)
  join app.memberships m on m.user_id = v.user_id and m.status = 'active'
  join app.organizations o on o.id = m.org_id and o.slug = 'lexgroup'
on conflict (membership_id, source) do nothing;

-- Desfazer: delete from app.member_source_refs where source = 'lexpre';
