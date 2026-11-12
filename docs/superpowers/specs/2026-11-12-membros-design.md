# Membros — lista e convites direto no Supabase

Data: 12/11/2026 · Branch: `feat/membros` · Status: design aprovado em conversa, aguardando revisão do spec

## Objetivo

Trocar o mock da aba **Administração → Membros** por dados reais do Supabase (staging vvhg), sem passar
pela API em Python (pausada desde 11/11). A aba passa a: listar quem faz parte da organização, convidar
pessoas, desativar/reativar membros e cancelar convites. O convite vira acesso quando a pessoa entra
com o Google usando o e-mail convidado.

## Decisões (Luís, 12/11)

1. **Escopo:** lista + convite + situação (desativar/reativar, cancelar convite).
2. **Editar cargos por unidade e equipes fica na aba Acesso**, não em Membros (entrega própria, depois).
3. **Quem gere** segue a regra do banco:
   - Owner e Desenvolvedor (`admin`) — permissão `members.manage`: todas as pessoas e unidades da org.
   - Gestor e Controller — permissão `unit.members.manage`: só pessoas e convites das unidades em que
     têm esse cargo, e só com cargos de unidade (nunca Owner/Desenvolvedor).
   - Os demais não acessam a aba.
4. **Convite = pré-autorização no login.** Não sai e-mail. Quem convida copia o link do LexHub e avisa a
   pessoa; ao entrar com o Google (e-mail verificado), o convite pendente vira associação ativa.

## Fora do escopo

- Editar cargo por unidade e equipes (aba Acesso).
- E-mail automático de convite (precisaria de Edge Function com a service key).
- Limite de assentos: o banco não guarda plano; a cobrança é mock.
- Esconder o item "Membros" do menu para quem não gere: o `/me` vem da API em Python (pausada), que
  não tem esse campo. Por enquanto a página mostra o estado "sem permissão" (403). Quando a API voltar,
  o `/me` ganha `can_manage_members` e o menu passa a esconder o item.

## Modelo de dados (já existe; nada muda nas tabelas)

- `app.memberships` — pessoa na org: `role_key` de nível org (`owner`, `admin` = Desenvolvedor,
  `member`), `status` (`invited` / `active` / `disabled`), `full_name`, `email`, `last_seen_at`.
- `app.membership_units` — cargo **por unidade** (`gestor`, `controller`, `colaborador`, `leitor`).
- `app.membership_teams` — equipes (cada equipe é de uma unidade: `app.teams.unit_id`).
- `app.invitations` — e-mail, `role_key`, `unit_ids[]`, `team_ids[]`, `invited_by`, `expires_at`
  (7 dias), `accepted_at`, `revoked_at`; um pendente por (org, e-mail).

O `role_key` do convite pode ser de nível org (`admin`, só quem tem `members.manage`) ou de unidade
(aplicado a todas as `unit_ids` do convite). `token_hash` é obrigatório na tabela; como o aceite é pelo
e-mail verificado, a função grava um valor aleatório (`gen_random_uuid()::text`, nativo, sem depender do
pgcrypto) só para cumprir a coluna.

## Banco — migration `20261113090000_membros.sql`

Aditiva, com bloco de rollback comentado no fim (padrão das anteriores). Validada antes no vvhg com o
teste que se desfaz sozinho e aplicada só depois do "Aplica".

Todas as funções: schema `api`, `security definer`, `set search_path = ''`, `revoke` de `public`/`anon`,
`grant execute` a `authenticated`. Erros de regra com `raise exception ... using errcode = 'P0001'`
(mensagem em pt-BR); sem permissão com `errcode = '42501'`. Helper novo em `app_private`:

- `app_private.members_scope(p_org uuid) returns uuid[]` — unidades da org que o usuário logado gere:
  todas se tem `members.manage`; senão `my_unit_ids_with('unit.members.manage')` filtrado pela org.
  Vazio → 42501 nas funções abaixo.

| Função | Comportamento |
|---|---|
| `api.list_members(p_org text)` → jsonb | `p_org` = slug. Devolve `{ members, invitations, teams, units, can_invite_admin }`. Owner/Dev veem todos; Gestor/Controller veem membros com ao menos uma unidade no escopo (e só as unidades do escopo de cada um) e convites cujas `unit_ids` cruzam o escopo. |
| `api.invite_members(p_org text, p_emails text[], p_role text, p_units text[], p_teams uuid[])` → jsonb | Normaliza e-mails (trim + lower), cria um convite por e-mail. Recusa: cargo `owner`; `admin` sem `members.manage`; unidade fora do escopo; equipe de unidade não escolhida; cargo de unidade sem unidade. E-mail que já é membro ativo ou já tem convite pendente volta em `skipped` com o motivo, sem erro. Devolve `{ invited: [...], skipped: [{ email, reason }] }`. |
| `api.set_member_status(p_org text, p_member uuid, p_status text)` → jsonb | `active` ↔ `disabled`. Recusa: a si mesmo; membro fora do escopo; Gestor/Controller mexendo em Owner/Dev; desativar o último Owner/Dev ativo da org. |
| `api.revoke_invitation(p_id uuid)` → jsonb | Marca `revoked_at`. Só no escopo de quem chama. |
| `api.accept_my_invitations()` → integer | Usa `auth.jwt()`: só age se o e-mail estiver verificado (`email_verified` no `user_metadata` do Google ou `email_confirmed_at`). Para cada convite pendente e não expirado do e-mail: cria a associação ativa (ou reativa uma `invited` existente), unidades com o cargo e equipes; marca `accepted_at`. Devolve quantos aceitou (0 = nada a fazer). Membro **desativado** não é reativado por convite. |

Auditoria (`app.audit_log`): `member.invited`, `member.disabled`, `member.enabled`,
`invitation.revoked`, `invitation.accepted` — com org, autor e alvo.

## Login

`loadSession` (`apps/web/src/contexts/session.ts`) chama `client.acceptMyInvitations()` antes do
`getMe()`. Qualquer erro dessa chamada é ignorado (o login segue). Assim o convidado cai direto no app,
e o card "sem acesso" / Solicitar acesso fica para quem não tem convite. No mock, a função aceita os
convites em memória do e-mail logado.

## Front

### Contrato (`types/index.ts`)

```ts
export type OrgRoleKey = 'owner' | 'admin' | 'member'
export type UnitRoleKey = 'gestor' | 'controller' | 'colaborador' | 'leitor'
export type MemberStatus = 'active' | 'invited' | 'disabled'

export type Member = {
    id: string
    name: string
    email: string
    org_role: OrgRoleKey
    units: { code: string; role: UnitRoleKey }[]
    teams: string[]
    status: MemberStatus
    last_seen_at: string | null
    security: string | null // 'Google' quando entrou pelo Google
}

export type Invitation = {
    id: string
    email: string
    role: Exclude<OrgRoleKey, 'owner' | 'member'> | UnitRoleKey
    units: string[]
    teams: string[]
    invited_by: string | null
    created_at: string
    expires_at: string
}

export type InviteRequest = { emails: string[]; role: Invitation['role']; units: string[]; teams: string[] }
export type InviteResult = { invited: string[]; skipped: { email: string; reason: string }[] }

export type MembersResponse = {
    members: Member[]
    invitations: Invitation[]
    teams: { id: string; name: string; unit: string }[]
    units: Unit[] // as que quem chama gere
    can_invite_admin: boolean
}
```

O status `requested` sai (pedidos de acesso ficam em Plataforma → Pedidos de acesso).

### DataClient

`listMembers`, `inviteMembers` (devolve `InviteResult`), `setMemberStatus`, `revokeInvitation`,
`acceptMyInvitations`. Módulo novo `services/membersClient.ts` (rpc no schema `api`, mesmo
`toAccessError` do `accessRequests.ts`, movido para um módulo comum `services/rpcError.ts`), espalhado no
`apiClient` no lugar das rotas HTTP. O `mockClient` implementa o mesmo contrato em memória
(`services/mock/members.ts` reescrito no formato novo).

### Tela (`pages/admin/members/`)

- **Cabeçalho:** "N membros ativos" + botão "Convidar pessoas".
- **Lista:** membros e, depois, convites pendentes (linha com o e-mail, "Convite pendente", "Convidado
  por X · vence em N dias"). Coluna **Papel**: Owner/Desenvolvedor pelo papel da org; senão o cargo na
  unidade escolhida no switcher; com "Todas as unidades", o cargo de maior nível e "+N" se houver
  outros. Coluna **Unidades e equipes**, **Situação**, **Segurança**.
- **Filtros** (URL, como hoje): busca, unidade, papel — papel casa com o papel da org ou com o cargo em
  qualquer unidade (na unidade filtrada, quando houver).
- **Painel da pessoa** (clicar na linha, mesmo `with-aside` do convite): dados, cargos por unidade
  (somente leitura), Desativar/Reativar (com confirmação) e o link "Editar cargos e equipes em Acesso".
  Para convite: Cancelar convite e Copiar link.
- **Convite:** opções de cargo Colaborador, Leitor, Gestor, Controller e — só com `can_invite_admin` —
  Desenvolvedor. Unidades = as que quem convida gere; equipes filtradas pelas unidades escolhidas.
  Depois de enviar, o painel mostra o resultado (convidados / pulados com o motivo) e o link do LexHub
  para copiar, com o aviso "Peça para a pessoa entrar com o Google usando este e-mail. O convite vale
  por 7 dias."
- **Sem permissão:** 403 de `list_members` → estado "Você não gere membros nesta organização".

Lógica pura continua em `memberView.ts` / `invite.ts` (testadas com Vitest); componentes só montam.

## Testes

- `supabase/tests/membros_test.sql` (roda no CI e no vvhg, termina com rollback): cria a própria org;
  Dev convida → convidado com e-mail verificado aceita → vira ativo com cargo e equipe; e-mail não
  verificado não aceita; Gestor não convida para unidade alheia nem convida Desenvolvedor; ninguém
  desativa a si mesmo; o último Dev não é desativado; convite expirado/revogado não é aceito.
- Vitest: `memberView` (papel exibido por unidade, filtros), `invite` (validação), `membersClient`
  (mapeamento de erros), `session` (aceitar convite antes do `/me`, erro ignorado).
- Navegador no mock: lista, filtros, convite, desativar/reativar, cancelar convite.
- Modo api no vvhg: Luís testa com uma conta Google convidada.

## Ordem de entrega

1. Migration + teste SQL (validar no vvhg com rollback → "Aplica").
2. Contrato, `membersClient`, mock.
3. Tela (lista, painel, convite) e login.
4. Testes e verificação no mock.
