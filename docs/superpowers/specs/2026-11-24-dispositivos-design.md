# Dispositivos nas Configurações (design curto)

Data: 24/11/2026 · Status: aprovado · Branch: `feat/dispositivos` (da main)

## Por quê

A pessoa não sabe onde a conta dela está aberta (TV da sala, celular, outro computador) e hoje só consegue
"Desconectar outros aparelhos" na tela do QR. Em Configurações ela passa a ver cada aparelho e derrubar um
por um, com efeito em até 1 minuto no aparelho derrubado.

## Objetivos / fora do escopo

- Ver as próprias sessões: navegador e sistema, IP, quando entrou e quando foi a última atividade.
- Desconectar um aparelho, todos os outros, ou este (= sair).
- O aparelho derrubado sai em até 1 minuto e cai no login com o aviso "Você foi desconectado em outro aparelho".
- Fora: ver ou derrubar aparelhos de outra pessoa (inclusive no modo suporte: Configurações é sempre de quem
  está logado), nomear aparelhos, localização pelo IP.
- Anti-objetivo: conseguir apagar a sessão de outra pessoa.

## Abordagens

1. **Sessões do Supabase (`auth.sessions`) por duas funções no banco (escolhida).** Os dados já existem;
   chamadas direto do front, como Aparência e Membros.
2. Tabela própria de aparelhos (como o LexFlow): duplica o que o Supabase já guarda.
3. Pela API em Python: a API hoje não lida com login; seria uma rota a mais sem ganho.

## Como (decidido)

- **Banco (uma migration):**
  - `api.list_my_sessions()` → `id, created_at, last_active_at, user_agent, ip, current`, só as de
    `auth.uid()` que não venceram (`not_after`), a atual primeiro e depois pela última atividade. `current` vem
    do claim `session_id` do token (`auth.jwt()`).
  - `api.revoke_my_session(p_id uuid)` apaga a sessão se for de `auth.uid()` (senão, erro "não encontrada"),
    o que apaga junto os refresh tokens. Grava `auth.session_revoked` em `app.audit_log`, uma linha por
    organização ativa (como o `auth.login`), com IP e navegador no metadata.
  - Ambas `security definer`, só para `authenticated`.
- **Tela:** seção **Dispositivos** no modal de Configurações, depois de Aparência.
  - "Este dispositivo" no topo, sozinho. Os outros agrupados por IP + navegador/sistema (vários logins do
    mesmo aparelho = uma linha, com o total).
  - Cada linha: ícone (computador, celular ou TV), "Chrome · Windows" (`describeUserAgent`), IP e
    "ativo há 5 min".
  - **Desconectar** com confirmação no próprio botão (o 1º clique vira "Confirmar?", o 2º desconecta; volta
    sozinho em alguns segundos). Num grupo, desconecta todas as sessões dele.
  - **Desconectar todos os outros** reaproveita `signOutOthers`. **Sair deste dispositivo** = sair da conta.
- **Até 1 minuto:** o aviso de presença (`usePresenceHeartbeat`, a cada 60 s e ao voltar para a aba) também
  confere `isSessionAlive`. Sessão morta → sai e vai ao login com o aviso.
- **Auditoria:** `auth.session_revoked` → "Desconectou um aparelho" no tipo Entradas.
- **Mock:** algumas sessões falsas em memória; desconectar tira da lista.

## Para quem for construir

- Testes SQL: só lista as próprias; marca a atual; não apaga a de outra pessoa; grava a auditoria.
- A migration só vai para o lexhub-v2 com o OK do Luís; a versão no histórico é acertada depois.
