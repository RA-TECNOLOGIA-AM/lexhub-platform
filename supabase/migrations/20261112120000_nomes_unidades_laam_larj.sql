-- =============================================================================
-- Nome de exibição das unidades LA e RJ como a empresa chama: LAAM e LARJ (era "LUIS ALBERT AM" e
-- "LUIS ALBERT RJ", vindos da v1). Só o nome (o que o seletor de unidade e as telas mostram); o código
-- (LA, RJ), usado nas URLs, nas ligações com as fontes e nas regras, não muda.
-- =============================================================================

update app.units u
   set name = v.nome
  from app.organizations o,
       (values ('LA', 'LAAM'), ('RJ', 'LARJ')) as v (code, nome)
 where o.id = u.org_id
   and o.slug = 'lexgroup'
   and u.code = v.code;
