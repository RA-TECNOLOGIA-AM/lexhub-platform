-- =============================================================================
-- SÓ PARA O CI: imita as tabelas da V1 (schema public) com dados fictícios,
-- para testar supabase/scripts/import_v1.sql. Estrutura conforme docs/v1_schema_colunas.csv.
-- =============================================================================
create table public.companhia (
    id bigint primary key,
    nome text not null unique,
    sigla text unique,
    ativo boolean not null default true
);
create table public.setor (
    id bigint primary key,
    nome text not null unique,
    ativo boolean not null default true
);
create table public.cargo (
    id bigint primary key,
    nome text not null unique,
    ativo boolean not null default true
);
create table public.usuario (
    id uuid primary key references auth.users (id),
    nome text not null,
    email text not null unique,
    companhia_id bigint references public.companhia (id),
    setor_id bigint not null references public.setor (id),
    cargo_id bigint not null references public.cargo (id),
    ativo boolean not null default true
);
create table public.usuario_companhia (
    usuario_id uuid references public.usuario (id),
    companhia_id bigint references public.companhia (id),
    primary key (usuario_id, companhia_id)
);

insert into public.companhia (id, nome, sigla, ativo) values
    (1, 'Nicolas Gomes', 'NG', true),
    (2, 'LA Advogados AM', 'LAADVAM', true),
    (3, 'LA Advogados RJ', 'LAADVRJ', true),
    (4, 'Escritório MT', 'MT', false),
    (5, 'Sem sigla', null, true);

insert into public.setor (id, nome) values
    (1, 'Protocolo'),
    (2, 'Pendências Iniciais'),
    (3, 'Tecnologia'),
    (4, 'Comercial');

insert into public.cargo (id, nome) values
    (1, 'Desenvolvedor'),
    (2, 'Gestor'),
    (3, 'Colaborador');

insert into auth.users (id, email) values
    ('a0000000-0000-0000-0000-000000000001', 'dev@x.test'),
    ('a0000000-0000-0000-0000-000000000002', 'gestor.ng@x.test'),
    ('a0000000-0000-0000-0000-000000000003', 'protocolo.ng@x.test'),
    ('a0000000-0000-0000-0000-000000000004', 'pendencias.ng@x.test'),
    ('a0000000-0000-0000-0000-000000000005', 'comercial.ng@x.test'),
    ('a0000000-0000-0000-0000-000000000006', 'inativo.ng@x.test'),
    ('a0000000-0000-0000-0000-000000000007', 'protocolo.la@x.test'),
    ('a0000000-0000-0000-0000-000000000008', 'gestor.semunidade@x.test');

insert into public.usuario (id, nome, email, companhia_id, setor_id, cargo_id, ativo) values
    ('a0000000-0000-0000-0000-000000000001', 'Dev',            'dev@x.test',              null, 3, 1, true),
    ('a0000000-0000-0000-0000-000000000002', 'Gestor NG',      'gestor.ng@x.test',        1,    1, 2, true),
    ('a0000000-0000-0000-0000-000000000003', 'Protocolo NG',   'protocolo.ng@x.test',     1,    1, 3, true),
    ('a0000000-0000-0000-0000-000000000004', 'Pendencias NG',  'Pendencias.NG@x.test',    2,    2, 3, true),
    ('a0000000-0000-0000-0000-000000000005', 'Comercial NG',   'comercial.ng@x.test',     1,    4, 3, true),
    ('a0000000-0000-0000-0000-000000000006', 'Inativo NG',     'inativo.ng@x.test',       1,    1, 3, false),
    ('a0000000-0000-0000-0000-000000000007', 'Protocolo LA',   'protocolo.la@x.test',     2,    1, 3, true),
    ('a0000000-0000-0000-0000-000000000008', 'Gestor s/ unid', 'gestor.semunidade@x.test', null, 1, 2, true);

-- "Pendencias NG" tem LA como principal e NG como extra
insert into public.usuario_companhia (usuario_id, companhia_id) values
    ('a0000000-0000-0000-0000-000000000004', 1);
