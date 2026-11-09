# Contrato front → API (LexHub V2)

Data: 09/11/2026 · Para: quem implementa a API V2 (cards #120 e #123) · Mantido por: front (Luís)

O front já roda inteiro com dados fictícios (`VITE_DATA_SOURCE=mock`). Este documento lista **cada rota que o front
chama no modo `api`**, o formato que ele espera e as **regras que o servidor precisa garantir**. A fonte da verdade dos
formatos é o código: `apps/web/src/types/index.ts` (tipos) e `apps/web/src/services/apiClient.ts` (rotas). O mock
(`apps/web/src/services/mock/`) traz exemplos reais de cada resposta e serve de dado de teste.

## Situação hoje

A API tem só `GET /health`, `GET /health/supabase`, `GET /health/sources` e
`GET /orgs/{org}/units/{unit}/dashboards/{key}/access`. **Nenhuma rota de dados abaixo existe ainda.** No modo `api`,
cada tela sem rota mostra o erro 404 ("Não encontrado").

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

### Nomes dos campos: decisão em aberto

- **`snake_case`, por compatibilidade com a v1:** o catálogo e os dashboards (`synced_at`, `can_export`,
  `max_delay_min`, campos do Protocolo e de Pendências). A conferência v2 × v1 é campo a campo.
- **`camelCase`:** os contratos novos da V2 (`renewsOn`, `paymentMethods`, `monthlyPrice`, `failingSources`,
  `monthlyRevenue`, `canExport` em `User`).

**Proposta:** manter assim, sem renomear nada agora, e na API usar modelos Pydantic com
`alias_generator=to_camel` só nos contratos novos. Se o time preferir um padrão único, o front ajusta os tipos (é
mecânico), mas precisa ser decidido **antes** de implementar as rotas.

## Rotas, em ordem de prioridade para o go-live (18/11)

Legenda: **P1** = sem isso o app não abre · **P2** = tela do MVP · **P3** = tela do MVP só de leitura, pode entrar depois
do go-live com o mock.

| Prioridade | Método e rota                                              | Resposta (tipo em `types/index.ts`) | Tela                                         |
| ---------- | ---------------------------------------------------------- | ----------------------------------- | -------------------------------------------- |
| P1         | `GET /me` · `GET /me?org={slug}`                           | `Me`                                | todas (sessão, menu, seletor de organização) |
| P1         | `GET /orgs/{org}/dashboards`                               | `DashboardCatalog`                  | Hub                                          |
| P1         | `GET /orgs/{org}/units/{unit}/dashboards/protocolo-lexpre` | `ProtocoloResponse`                 | Protocolo (#123)                             |
| P2         | `GET /orgs/{org}/units/{unit}/dashboards/pendencias`       | `PendenciasResponse`                | Pendências                                   |
| P2         | `GET /orgs/{org}/favorites`                                | `string[]` (keys)                   | Hub                                          |
| P2         | `POST /orgs/{org}/favorites/{key}` · `DELETE …/{key}`      | 204                                 | Hub (estrela)                                |
| P2         | `GET /orgs/{org}/members`                                  | `MembersResponse`                   | Membros                                      |
| P2         | `POST /orgs/{org}/invitations`                             | 204 (corpo: `InviteRequest`)        | Membros (convite)                            |
| P3         | `GET /orgs/{org}/access`                                   | `AccessResponse`                    | Acesso                                       |
| P3         | `GET /orgs/{org}/audit`                                    | `AuditResponse`                     | Auditoria                                    |
| P3         | `GET /orgs/{org}/billing`                                  | `BillingResponse`                   | Plano e cobrança                             |
| P3         | `GET /platform/clients`                                    | `ClientsResponse`                   | Clientes (equipe RA)                         |

Dashboards recebem período e filtros na query string, com os nomes da v1:
`?from=YYYY-MM-DD&to=YYYY-MM-DD&materia=ANP&materia=MORA&funcionario=…&uf=…&area_atuacao_id=…` (valor repetido =
vários). Sem `from`/`to`, o servidor usa o período padrão e devolve o período usado em `meta.from`/`meta.to`.

## Regras que o servidor precisa garantir

O front já aplica cada regra abaixo na tela e no mock, mas **isso não protege nada**: alguém pode chamar a API direto.
Cada uma precisa existir no servidor.

### Sessão e organização (`/me`)

- `GET /me` sem `org`: a organização padrão da pessoa (a última usada, ou a primeira).
- `GET /me?org={slug}`: o `me` daquela organização, com as **unidades que a pessoa vê nela**. Se a pessoa não for
  membro, responder **403**. O front mostra "Organização não encontrada".
- `Me.orgs` lista **todas** as organizações da pessoa (o seletor da barra lateral). `Org.sub` é o texto de baixo
  ("Plano Pro · 3 unidades").
- `User.platformStaff = true` só para a equipe RA Tecnologia.

### Rotas `/orgs/{org}/...`

- Membro da organização? Se não, **403**, inclusive para organização inexistente.
- `GET /orgs/{org}/dashboards` devolve **só** os dashboards que a pessoa pode ver (regra de equipe × unidade,
  `app_private.dashboard_scope`). Quem não tem equipe ou unidade **não vê nenhum** (diferente da v1).
- `can_export` e `can_see_commission` em cada dashboard são **decididos pelo servidor**. Regra de exportação:
  colaborador exporta só o próprio setor; admin, dev e controller exportam qualquer um.
- Nos dashboards, `scope = 'own'` (de `require_dashboard`) filtra para os registros da própria pessoa.
  `comissionamento_por_funcionario` só vem para quem tem `can_see_commission`.

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

- Só `platformStaff`; os demais recebem **403**. O front esconde o menu e bloqueia a página, mas a proteção real é esta.
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
        "roleLabel": "Dev · RA",
        "canExport": true,
        "canSeeCommission": true,
        "platformStaff": true
    },
    "org": {
        "slug": "lexgroup",
        "name": "LexGroup",
        "sub": "Plano Pro · 3 unidades"
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
            "sub": "Plano Pro · 3 unidades"
        },
        {
            "slug": "cliente-parceiro",
            "name": "Cliente parceiro",
            "sub": "Implantação · 1 unidade"
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
   usuário sem `platformStaff` em `/plataforma/clientes` → "Área da equipe RA Tecnologia".

## Mudanças neste contrato

O front muda um tipo em `types/index.ts` → atualiza este documento no mesmo commit. A API precisa de um formato
diferente → abrir a conversa antes de implementar, para não divergir.
