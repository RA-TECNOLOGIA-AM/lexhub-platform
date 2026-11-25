# Perfil: criar e alterar senha — design

Data: 25/11/2026 · Branch: `feat/perfil-senha`

## Por quê

Quem entra por convite só consegue entrar pelo Google. O Luís quer que qualquer pessoa possa criar uma senha
no Perfil e, a partir daí, entrar também com e-mail e senha, como no LexFlow. Hoje, no lexhub-v2, só 1 das 97
contas tem senha.

## Objetivo

- Configurações → Perfil ganha o bloco **Senha**, para todo mundo:
  - sem senha: "Não definida", com o botão **Criar senha**;
  - com senha: "••••••", com o botão **Alterar senha**.
- O botão abre dois campos (nova senha + confirmar), com o olho para mostrar a senha, e os botões Salvar e Cancelar.
- Toda troca ou criação de senha vai para a auditoria.

## Fora do escopo

- Editar o nome: continua com o admin (opção B).
- Editar o e-mail: não pode.
- 2FA: fica para uma entrega separada, depois desta.
- Tela "esqueci a senha".
- Remover a aba Pedidos de acesso: vai numa branch separada.

## Abordagens

1. **Só front.** Chama `updateUser` direto, como o LexFlow. Não sabe se a conta tem senha e não grava auditoria.
2. **Front + migration pequena (escolhida).** Uma função informa se a conta tem senha e a auditoria registra a troca.

## Como

- **Banco** (migration `20261126150000_perfil_senha.sql`):
  - `api.my_password_status()` devolve `boolean`: se `auth.users.encrypted_password` do próprio usuário não está
    vazio. É `security definer`, só para `authenticated`.
  - Trigger `after update of encrypted_password` em `auth.users`: quando a senha muda, grava
    `auth.password_changed` em `app.audit_log`, uma linha por organização ativa (o mesmo padrão do `auth.login`),
    com `metadata.kind` = `created` ou `changed`. Erro no trigger só gera warning e nunca bloqueia a troca.
    **Decisão do Claude:** usar trigger em vez de RPC chamada pelo front. A auditoria não depende do cliente e
    também pega a troca feita por outro caminho, como a recuperação de senha.
- **Front:**
  - `dataClient.getPasswordStatus()` e `dataClient.setPassword(pw)`, com `auth.updateUser({ password })`, e o mock
    equivalente.
  - O bloco fica no `ProfileSection`. A validação é a do LexFlow: campos preenchidos, senhas iguais e no mínimo
    6 caracteres. O erro do Supabase, por exemplo uma senha fraca, aparece na tela.
  - Auditoria: rótulo "Senha criada" ou "Senha alterada" em `auditEvents.ts`.
- **Senha atual:** não é pedida, igual ao LexFlow. A sessão já está aberta e a ação fica na auditoria.

## Para o executor decidir

- O texto exato das mensagens e o layout fino, seguindo o `settings.css`.
- Se o Supabase recusar com `reauthentication_needed` ("Secure password change" ligado), mostrar
  "Entre de novo para trocar a senha".
