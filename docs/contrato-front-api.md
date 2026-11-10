# Contrato front → API (LexHub V2)

Data: 09/11/2026 · Para: quem implementa a API V2 (cards #120 e #123) · Mantido por: front (Luís)

O front já roda inteiro com dados fictícios (`VITE_DATA_SOURCE=mock`). Este documento lista **cada rota que o front
chama no modo `api`**, o formato que ele espera e as **regras que o servidor precisa garantir**. A fonte da verdade dos
formatos é o código: `apps/web/src/types/index.ts` (tipos) e `apps/web/src/services/apiClient.ts` (rotas). O mock
(`apps/web/src/services/mock/`) traz exemplos reais de cada resposta e serve de dado de teste.

## Situação hoje

Prontas (10/11): `GET /me`, `GET /orgs/{org}/dashboards`, favoritos (`GET`, `POST` e `DELETE /orgs/{org}/favorites`) e
ordem dos cards (`GET` e `PUT /orgs/{org}/hub-order`), além de `GET /health`, `GET /health/supabase`,
`GET /health/sources` e `GET /orgs/{org}/units/{unit}/dashboards/{key}/access`. **As demais rotas de dados abaixo ainda
não existem.** No modo `api`, cada tela sem rota mostra o erro 404 ("Não encontrado").

## Convenções (valem para todas as rotas)

| Assunto                     | Regra                                                                                                                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Login                       | Supabase Auth no front. Toda chamada leva `Authorization: Bearer <access_token>`; a API valida pelo JWKS (já implementado em `app/auth.py`).                                         |
| Organização                 | Sempre pelo **slug** na URL (`/orgs/lexgroup/...`), nunca pelo id.                                                                                                                   |
| Unidade                     | Pelo **código** (`NG`, `LA_AM`, `LA_RJ`). `['*']` numa lista de unidades = todas.                                                                                                    |
| Erros                       | Corpo `{"detail": "mensagem em português"}`. O front mostra o `detail` quando o status não tem tela própria.                                                                         |
| 401                         | Sem token ou token inválido/expirado. O front leva ao login e, depois, de volta para a mesma página.                                                                                 |
| 403                         | Sem permissão **ou** recurso inexistente: **a mesma resposta** para os dois casos, para não revelar o que existe (padrão do `require_dashboard`). Toda negação vai para a auditoria. |
| 404                         | Rota inexistente.                                                                                                                                                                    |
| 409                         | Conflito de dados (ex.: e-mail que já é membro).                                                                                                                                     |
| Datas                       | ISO 8601 com fuso (`2026-10-30T14:02:00-04:00`); só data: `YYYY-MM-DD`; mês: `YYYY-MM`. O front formata.                                                                             |
| Valores ainda não definidos | `null` (preços, valores de fatura, receita). O front mostra `[PREÇO]`, `[VALOR]`, `R$ [—]`.                                                                                          |
| Corpo vazio                 | `204 No Content` em escritas sem resposta (favoritos, convite).                                                                                                                      |

### Nomes dos campos: `snake_case` em tudo (decidido em 10/11)

Igual à v1, para a conferência v2 × v1 ser campo a campo, e também nos contratos novos da V2. `User` já está assim
(`role_label`, `can_export`, `can_see_commission`, `platform_staff`). Ainda em camelCase no front, a trocar quando a
rota for feita: `renewsOn`, `paymentMethods`, `monthlyPrice` (cobrança), `failingSources` e `monthlyRevenue`
(clientes) e `syncedAt` (fontes).

## Rotas, em ordem de prioridade para o go-live (18/11)

Legenda: **P1** = sem isso o app não abre · **P2** = tela do MVP · **P3** = tela do MVP só de leitura, pode entrar depois
do go-live com o mock.

| Prioridade | Método e rota                                              | Resposta (tipo em `types/index.ts`) | Tela                                         |
| ---------- | ---------------------------------------------------------- | ----------------------------------- | -------------------------------------------- |
| P1         | `GET /me` · `GET /me?org={slug}`                           | `Me`                                | todas (sessão, menu, seletor de organização) |
| P1         | `GET /orgs/{org}/dashboards`                               | `DashboardCatalog`                  | Hub                                          |
| P1         | `GET /orgs/{org}/units/{unit}/dashboards/protocolo-lexpre` | `ProtocoloResponse`                 | Protocolo (#123)                             |
| P2         | `GET /orgs/{org}/units/{unit}/dashboards/pendencias`       | `PendenciasResponse`                | Pendências                                   |
| P2         | `GET /orgs/{org}/units/{unit}/dashboards/{key}/export`     | arquivo CSV ou XLSX                 | Exportar (Protocolo e Pendências)            |
| P2         | `GET /orgs/{org}/favorites`                                | `string[]` (keys)                   | Hub                                          |
| P2         | `POST /orgs/{org}/favorites/{key}` · `DELETE …/{key}`      | 204                                 | Hub (estrela)                                |
| P3         | `GET /orgs/{org}/hub-order` · `PUT …` (corpo: `string[]`)  | `string[]` (keys) · 204             | Hub (arrastar cards)                         |
| P2         | `GET /orgs/{org}/members`                                  | `MembersResponse`                   | Membros                                      |
| P2         | `POST /orgs/{org}/invitations`                             | 204 (corpo: `InviteRequest`)        | Membros (convite)                            |
| P3         | `GET /orgs/{org}/access`                                   | `AccessResponse`                    | Acesso                                       |
| P3         | `GET /orgs/{org}/audit`                                    | `AuditResponse`                     | Auditoria                                    |
| P3         | `GET /orgs/{org}/sources`                                  | `SourcesResponse`                   | Unidades e fontes                            |
| P3         | `GET /orgs/{org}/billing`                                  | `BillingResponse`                   | Plano e cobrança                             |
| P3         | `GET /platform/clients`                                    | `ClientsResponse`                   | Clientes (equipe RA)                         |

Dashboards recebem período e filtros na query string, com os nomes da v1:
`?from=YYYY-MM-DD&to=YYYY-MM-DD&materia=ANP&materia=MORA&funcionario=…&uf=…&area_atuacao_id=…` (valor repetido =
vários). Sem `from`/`to`, o servidor usa o período padrão e devolve o período usado em `meta.from`/`meta.to`.

## Regras que o servidor precisa garantir

O front já aplica cada regra abaixo na tela e no mock, mas **isso não protege nada**: alguém pode chamar a API direto.
Cada uma precisa existir no servidor.

### Sessão e organização (`/me`)

- `GET /me` sem `org`: a organização padrão da pessoa (a última usada, `memberships.last_seen_at`; enquanto nada
  grava esse campo, a primeira por nome).
- `GET /me?org={slug}`: o `me` daquela organização, com as **unidades que a pessoa vê nela**. Se a pessoa não for
  membro, responder **403**. O front mostra "Organização não encontrada".
- `Me.orgs` lista **todas** as organizações da pessoa (o seletor da barra lateral). `Org.sub` é o texto de baixo:
  por enquanto só as unidades ("3 unidades"), porque o plano ainda não existe no banco.
- `Me.units`: owner e admin veem todas as unidades ativas; os demais, as unidades em que têm cargo.
- `User.role_label`: owner/admin mostram o papel da organização ("Desenvolvedor"); os demais, os cargos nas unidades
  ("Gestor · Leitor").
- `User.can_export` e `User.can_see_commission` vêm das permissões (`app.role_permissions`): exporta quem tem
  `dashboards.export`; vê comissão quem tem `org.dashboards.all` ou `unit.dashboards.all` (owner, admin, gestor e
  controller, como Gestor e Desenvolvedor na v1).
- `User.platform_staff = true` só para a equipe RA Tecnologia: vem de `app_metadata.platform_staff` no token do
  Supabase Auth (só a chave secreta altera; `user_metadata` não vale).
- Negação (`?org=` de que não é membro, inexistente ou pessoa sem organização): **403** `Sem acesso`, auditado como
  `org.access_denied`.

### Rotas `/orgs/{org}/...`

- Membro da organização? Se não, **403**, inclusive para organização inexistente.
- `GET /orgs/{org}/dashboards` devolve **só** os dashboards que a pessoa pode ver (regra de equipe × unidade,
  `app_private.dashboard_scope`). Quem não tem equipe ou unidade **não vê nenhum** (diferente da v1).
- `can_export` e `can_see_commission` em cada dashboard são **decididos pelo servidor**. Regra de exportação:
  colaborador exporta só o próprio setor; admin, dev e controller exportam qualquer um. Calculados por unidade
  (`app_private.has_unit_permission`); num card com várias unidades, só vêm `true` se valerem em **todas** (o botão
  nunca aparece numa unidade em que a API negaria).
- Favoritos e ordem dos cards são por pessoa em cada organização (`app.dashboard_favorites`, `app.hub_orders`). Só
  favorita o que a pessoa consegue abrir (mesma regra do catálogo); inexistente, "em breve" ou sem acesso = **403**,
  auditado. Favoritar de novo ou desfavoritar o que não estava marcado não é erro (204). A ordem é salva inteira (até 200
  keys; repetidas contam só na primeira posição).
- `synced_at` vem `null` enquanto a fonte não sincronizou (o cache de 5 min ainda não existe); o card mostra
  "Aguardando sincronização". `upcoming` = dashboards do catálogo com `status = 'upcoming'`.
- Nos dashboards, `scope = 'own'` (de `require_dashboard`) filtra para os registros da própria pessoa.
  `comissionamento_por_funcionario` só vem para quem tem `can_see_commission`.

### Opções dos filtros (`opcoes_filtro`)

- Calculadas pela API junto com o dashboard: valores distintos de matéria, funcionário, UF e área nos dados da
  **unidade e do período**, **antes** de aplicar os filtros (marcar "ANP" não pode esconder as outras matérias).
- Os filtros seguem os parâmetros da v1 (Protocolo LexPre: `materia`, `funcionario`, `area_atuacao_id`, `uf`).
- O front só exibe; não calcula opções nem números (igual à v1, onde a API faz tudo: funções `filter_*` por
  dashboard e opções na resposta ou em `GET /<dashboard>/filtros/opcoes`).

### Exportar (`.../dashboards/{key}/export`)

- Parâmetros como na v1: `?format=csv|xlsx&campos=id_demanda&campos=materia&from=&to=&<filtros>`. O arquivo sai
  com o período e os filtros pedidos, colunas na ordem de `campos`, cabeçalho com os rótulos da v1 (`_LABELS_EXPORT_*`).
- Gerado pelo servidor (openpyxl no XLSX, como na v1), com as mesmas queries e funções `filter_*` do dashboard.
- **403** sem `can_export`, fora da regra do setor ou sem acesso à unidade. Só aceita `campos` da lista do servidor
  (`_CAMPOS_EXPORT_*`); campo desconhecido = **400**.
- Toda exportação vai para a **auditoria** (quem, dashboard, unidade, período, filtros, quantas linhas, formato). A v1
  não registra.
- Nome do arquivo no `Content-Disposition` (o front usa `{key}_{unit}.{format}` se não vier).

### Convite (`POST /orgs/{org}/invitations`)

Corpo:

```json
{
    "emails": ["fernanda@lexgroup.com.br"],
    "role": "colaborador",
    "units": ["NG"],
    "team": "Protocolo"
}
```

- Quem pode convidar: owner e admin em qualquer unidade; gestor só nas unidades dele (matriz "Convidar e gerir
  membros: Da unidade").
- `role` nunca é `owner`, e `units` não pode ser vazio (400).
- E-mail que já é membro: **409**, com `detail` = `"Já faz parte da organização: a@x.com, b@x.com"`. O painel mostra
  esse texto.
- Gera evento de auditoria (`kind: "access"`, "Convidou N pessoas").
- Revalidar no servidor o que o front já valida (e-mails válidos, pelo menos um e-mail e uma unidade).

### Plataforma (`/platform/clients`)

- Só `platform_staff`; os demais recebem **403**. O front esconde o menu e bloqueia a página, mas a proteção real é esta.
- Sessão de suporte (ação futura): somente leitura, motivo obrigatório (pelo menos 10 caracteres, visível ao
  cliente), MFA, expira em 1 hora e fica registrada na auditoria do cliente.

### Auditoria

- `GET /orgs/{org}/audit`: mais recente primeiro, guardado por pelo menos 6 meses.
- `kind` ∈ `login | export | access | support | source`.
- Toda exportação precisa gerar um evento. Por isso o "Exportar CSV" da auditoria fica no servidor, e não no navegador.

### Acesso

- `matrix` = a tabela `app.role_permissions` vista por papel. As `key` que o front usa no simulador são `export`
  (pode exportar) e `team_data` (vê dados da equipe toda). As demais são só exibição: `view`, `members`, `sources`,
  `finance`, `billing`.
- `rules` = `app.access_rules` agrupadas por equipe. `all: true` quando a equipe vê todos os dashboards das suas
  unidades (Diretoria).

## Exemplos de resposta

Os exemplos completos estão no mock, e cada arquivo é a resposta inteira de uma rota:

| Rota                     | Exemplo                                                                                |
| ------------------------ | -------------------------------------------------------------------------------------- |
| `/me`                    | `services/mock/users.ts` (`meFor('lexgroup')`)                                         |
| `/orgs/{org}/dashboards` | `services/mock/catalog.ts`                                                             |
| Protocolo / Pendências   | `services/mock/protocolo.ts`, `services/mock/pendencias.ts`                            |
| `/orgs/{org}/members`    | `services/mock/members.ts`                                                             |
| `/orgs/{org}/access`     | `services/mock/access.ts`                                                              |
| `/orgs/{org}/audit`      | `services/mock/audit.ts`                                                               |
| `/orgs/{org}/billing`    | `services/mock/billing.ts` (`billingFor`) e `emptyOrg.ts` (organização em implantação) |
| `/platform/clients`      | `services/mock/clients.ts`                                                             |

Exemplo curto de `GET /me?org=lexgroup`:

```json
{
    "user": {
        "name": "Luís Tápia",
        "initials": "LT",
        "role_label": "Desenvolvedor",
        "can_export": true,
        "can_see_commission": true,
        "platform_staff": true
    },
    "org": {
        "slug": "lexgroup",
        "name": "LexGroup",
        "sub": "3 unidades"
    },
    "units": [
        { "code": "NG", "name": "Nicolas Gomes" },
        { "code": "LA_AM", "name": "Luis Albert AM" },
        { "code": "LA_RJ", "name": "Luis Albert RJ" }
    ],
    "orgs": [
        {
            "slug": "lexgroup",
            "name": "LexGroup",
            "sub": "3 unidades"
        },
        {
            "slug": "cliente-parceiro",
            "name": "Cliente parceiro",
            "sub": "1 unidade"
        }
    ]
}
```

## Como testar a integração

1. No `apps/web/.env.local`: `VITE_DATA_SOURCE=api` e `VITE_BASE_API_URL=http://localhost:8000`, com as chaves do
   Supabase.
2. Subir a API (`apps/api`, ver o README) com `CORS_ORIGINS=http://localhost:5173`.
3. Abrir cada tela da tabela acima. Rota pronta = a tela igual à do mock; rota faltando = "Não encontrado".
4. Conferir os erros: sem login → tela de login; outra organização na URL → "Organização não encontrada";
   usuário sem `platform_staff` em `/plataforma/clientes` → "Área da equipe RA Tecnologia".

## Mudanças neste contrato

O front muda um tipo em `types/index.ts` → atualiza este documento no mesmo commit. A API precisa de um formato
diferente → abrir a conversa antes de implementar, para não divergir.
