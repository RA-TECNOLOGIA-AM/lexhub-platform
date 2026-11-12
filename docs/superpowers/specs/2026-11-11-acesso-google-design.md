# Acesso pelo Google: espelho da v1 e Solicitar acesso — design

Data: 11/11/2026 · Status: **desenho aprovado em conversa; spec aguardando revisão** · Base: `main` com o PR #5
(login com Google e tela "sem acesso") já mergeado.

## Contexto

- O login com Google funciona no staging (Supabase branch `vvhgbzjapqcyjbfpndaq`, client OAuth "LexHub Auth" do GCP
  `lexhub-v2`). Quem entra sem associação ativa recebe 403 no `/me` e vê o card "Você ainda não tem acesso".
- O staging tem o **espelho da v1**: 87 associações em `app.memberships` (74 ativas, 13 desativadas), domínios
  @luisalbertadv (46), @lexgroup (23) e @nicolasgomesadv (18). **73 das ativas são "cascas"**: o usuário do Auth nunca
  entrou, não tem senha nem outro login. Nenhum e-mail aparece em mais de um usuário; ninguém está em duas organizações.
- O Supabase liga o login Google ao usuário que já existe com o mesmo e-mail, inclusive nas cascas (ver Entrega 1).
- O schema `app` **não** está exposto na API REST (só `public` e `graphql_public`).
- Nenhum usuário do staging tem `platform_staff` no `app_metadata`.
- A API em Python continua rodando (login, `/me`, dashboards). A integração de dados está pausada.

Decisões do Luís (11/11): quem pede **não** escolhe a organização; ele define na aprovação, porque "operação" =
escritório = **organização** (SaaS), com uma ou mais unidades. Ele mesmo aprova. Aviso **só por selo** no menu (sem
e-mail). O pedido leva **escritório + mensagem**.

## Entrega 1: claim do espelho — **cancelada (12/11)**

Não é necessária. O `auth.users` tem e-mail único (`users_email_partial_key`), então o Supabase nunca cria um usuário
novo para o e-mail de uma casca: ele liga a identidade Google ao usuário que já existe. Teste real em 12/11: um colega
do espelho (usuário criado em 25/03, na importação da v1, sem e-mail confirmado) entrou pelo Google, o Supabase ligou o
Google a esse usuário e confirmou o e-mail, e ele caiu na própria associação ativa, sem usuário duplicado.

Ou seja: **quem está no espelho com associação ativa já entra pelo Google hoje**, sem mudança. Desativados continuam
sem acesso (403 → card "sem acesso").

## Entrega 2: Solicitar acesso (`feat/solicitar-acesso`)

### Banco (migration aditiva, com rollback)

`app.access_requests`:

| coluna | tipo / regra |
|---|---|
| `id` | uuid pk |
| `user_id` | uuid → `auth.users`, not null |
| `email`, `full_name` | text, copiados do Auth na criação |
| `office` | text not null, 2–120 caracteres (trim) |
| `message` | text null, até 500 caracteres |
| `status` | `pending` / `approved` / `rejected` |
| `decided_by`, `decided_at` | quem decidiu e quando |
| `decision_note` | text null (nota da recusa) |
| `result_org_id` | uuid → `app.organizations`, null (onde entrou) |
| `created_at` | timestamptz |

- Índice único parcial: um `pending` por `user_id`.
- RLS ligada: `select` só do próprio pedido. **Sem** policies de escrita: tudo passa pelas funções.

Schema **`api`** (novo, **exposto** na API REST), só com funções `security definer`, `search_path = ''`,
`grant execute` para `authenticated`:

| função | quem pode | faz |
|---|---|---|
| `request_access(p_office, p_message)` | logado **sem** associação ativa e sem pedido pendente | cria o pedido; audita `access_request.created` |
| `my_access_request()` | logado | último pedido do chamador (status, datas, nota) ou nada |
| `count_pending_access_requests()` | equipe RA | número do selo |
| `list_access_requests(p_status)` | equipe RA | pedidos (pendentes ou decididos) |
| `approval_options()` | equipe RA | organizações ativas com as suas unidades, para o formulário |
| `approve_access_request(p_id, p_target jsonb)` | equipe RA | aprova numa transação (abaixo) |
| `reject_access_request(p_id, p_note)` | equipe RA | recusa; audita `access_request.rejected` |

Equipe RA = `coalesce((auth.jwt() -> 'app_metadata' ->> 'platform_staff')::boolean, false)`, a mesma regra que a API
usa. Quem não tem a permissão recebe erro (`42501`).

`p_target` da aprovação:

- organização existente: `{"kind": "existing", "org_id": "...", "org_role": "admin" | "member",
  "units": [{"unit_id": "...", "role_key": "gestor" | "controller" | "colaborador" | "leitor"}]}`.
  Com `member`, pelo menos uma unidade é obrigatória;
- organização nova: `{"kind": "new", "name": "...", "slug": "...", "org_role": "owner" | "admin",
  "unit": {"code": "...", "name": "...", "timezone": "America/Manaus"}}`.

A aprovação cria a associação `active` (nome e e-mail do pedido) e os `membership_units`, marca o pedido como
`approved` com `result_org_id` e audita `access_request.approved` (com `org_id`). O pedido precisa estar `pending`;
qualquer falha desfaz tudo.

**Rollback:** `drop schema api cascade; drop table app.access_requests;`.

**Fora da migration:** marcar a conta @lexgroup do Luís com `platform_staff = true` (`update auth.users set
raw_app_meta_data = raw_app_meta_data || '{"platform_staff": true}'`), aplicado só depois do "Aplica". O token só traz
o valor novo depois de sair e entrar de novo.

**Painel (Luís):** no staging, em Settings → API → Exposed schemas, adicionar `api`.

### Front

- **Cliente de dados:** módulo `services/accessRequests.ts` com `supabase.schema('api').rpc(...)`, encaixado no
  `apiClient`; versão em memória no mock (pedido, aprovação e recusa funcionando sem banco). Métodos novos no
  `DataClient`: `requestAccess`, `getMyAccessRequest`, `countPendingAccessRequests`, `listAccessRequests`,
  `getApprovalOptions`, `approveAccessRequest`, `rejectAccessRequest`.
- **Card "sem acesso"** (`pages/login/NoAccessCard.tsx`), com três estados:
  - sem pedido: campos Escritório/empresa (obrigatório) e Mensagem (opcional), e o botão "Enviar pedido";
  - pendente: "Pedido enviado em dd/mm, aguardando aprovação" e o botão "Verificar de novo" (refaz a sessão; aprovado
    → hub);
  - recusado: mostra a nota e o botão "Pedir de novo".
- **Plataforma → Pedidos de acesso** (`/plataforma/pedidos`, item novo na seção `platformOnly` com selo do número de
  pendentes):
  - abas Pendentes e Decididos;
  - tabela com nome, e-mail, escritório, mensagem e data;
  - painel lateral de aprovação (no estilo do `InvitePanel`) com "Organização existente / Organização nova";
  - recusa com nota.
- **Selo:** `NavItem` ganha `badge` opcional; a contagem é buscada ao abrir o app (só para a equipe RA) e depois de
  cada decisão.
- **Testes (vitest, sem React):** regras de cada estado do card, validação do formulário de aprovação (unidade
  obrigatória para `member`, slug válido) e o cliente em memória do mock.

### Fora do escopo

E-mail de aviso, equipes na aprovação (ajustáveis depois em Membros), limpeza das cascas antigas e convites.

## Ordem de amanhã

1. Revisar este spec.
2. Entrega 1 (claim): migration + validação com rollback → "Aplica" → teste com um colega do espelho.
3. Plano de implementação da Entrega 2 (writing-plans) → execução.
