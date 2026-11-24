# Modo suporte: ver como um membro (design)

Data: 24/11/2026 · Status: rascunho · Branch: `feat/modo-suporte-ver-como` (da main cf29b0c)

Substitui a etapa 1 (`feat/modo-suporte`, commit WIP 992c870), que foi parada por ser redundante com a
aba Acesso. Dela aproveitamos só a ideia da função que explica por que um dashboard está oculto.

## Por quê

Chamados do tipo "não estou vendo o dashboard X" ou "meu número está errado". Hoje o Owner/Dev precisa
ler as regras de acesso à mão e não consegue ver os números como a pessoa vê. O modo suporte deixa o
Owner/Dev navegar no hub e nos dashboards **como o membro**, com os dados dele, sem mexer na conta nem
na sessão dele, e com tudo registrado na auditoria.

## Objetivos

- Owner/Dev escolhe um membro **da organização ativa**, informa o motivo e passa a ver o hub e os
  dashboards exatamente como o membro: os mesmos cards, as mesmas unidades e os mesmos números, inclusive
  o escopo "só os próprios" ligado ao funcionário dele na fonte.
- Uma faixa fixa no topo, "Vendo como Fulano · motivo · Sair", fica visível em todas as telas do modo.
- Nada é gravado como o membro.
- A auditoria conta a história completa: quem, como quem, por quê, o que abriu e quando saiu.

## Fora do escopo (agora)

- Suporte em outra organização (a partir de Clientes, sem ser membro). O modelo de sessão já deixa o
  caminho aberto.
- Telas de administração vistas como o membro.
- Avisar o membro de que alguém está vendo como ele.

## Anti-objetivos

- Qualquer escrita feita como o membro: favoritar, reordenar, exportar, ligar/desligar dashboard.
- Mostrar algo diferente do que o membro vê de fato. A troca de usuário acontece na API, nunca só no front.
- Login real como o membro (token dele) ou qualquer coisa que use `auth.uid()` como o membro.
- Gestor, Controller ou Colaborador conseguirem usar o modo.

## Abordagens consideradas

1. **Sessão de suporte no banco (escolhida).** Iniciar cria uma linha com quem pede, o membro, o motivo e
   a validade. O front manda o id da sessão em cada chamada, e a API troca o usuário efetivo depois de
   validar a sessão. Tem prazo, motivo único e início/fim na auditoria.
2. **Cabeçalho sem sessão.** Menor, mas sem prazo nem "encerrou", e o motivo ficaria sem registro ou
   repetido em cada chamada.
3. **Token do membro.** Descartada: daria escrita real e acesso às telas de admin como ele.

## Como (decidido)

### Banco (uma migration)

- Tabela `app.support_sessions`:
  - `id uuid`, `org_id`, `actor_user_id`, `target_user_id`, `target_membership_id`, `reason text`
    (5 a 500 caracteres);
  - `started_at`, `expires_at` (início + 1 h), `ended_at`, `end_reason` (`'exit' | 'expired'`).
  - RLS ligada, sem acesso para `authenticated`: só a API (service_role) lê e escreve.
- Job pg_cron a cada 15 min, no mesmo padrão da limpeza de unidades arquivadas: fecha as sessões vencidas
  sem `ended_at` (`end_reason = 'expired'`) e grava `support.ended`. Assim, a sessão abandonada (aba
  fechada) também tem fim na auditoria.
- Auditoria: `support.started`, `support.viewed` (dashboard aberto como o membro) e `support.ended`. Todos
  têm `actor_user_id` = quem pede, e `target_type = 'membership'` com `target_id` = membership do membro, a
  sessão e a unidade/dashboard no metadata. O `list_audit` resolve o nome do membro alvo.

### API

- `POST /orgs/{org}/support/sessions` com `{ membership_id, reason }`.
  - Só para Owner/Dev (`org.dashboards.all`) da organização; os demais recebem 403.
  - O membro precisa estar ativo, na mesma organização, e não pode ser quem pede.
  - Encerra uma sessão aberta anterior da mesma pessoa, cria a nova e grava `support.started`.
  - Devolve `{ session_id, expires_at, member: { name, avatar_path, role_label, units } }`; as
    `units` são as do membro, para o seletor de unidade e o hub.
- `DELETE /orgs/{org}/support/sessions/{id}` encerra a sessão (`exit`) e grava `support.ended`.
- **Usuário efetivo.** Um cabeçalho `X-Support-Session` é lido num único ponto, junto do usuário atual.
  - Com o cabeçalho, a API valida a sessão: existe, é de quem chama, está na organização da rota, não
    terminou e não venceu, e quem chama ainda é Owner/Dev.
  - Sessão vencida: grava `support.ended (expired)` uma vez e responde 409 `support_expired`.
  - Sessão válida: as rotas de leitura (catálogo do hub, favoritos e ordem, dashboard e meta) usam o
    `user_id` do membro em tudo, inclusive `resolve_access` e `member_ref` do escopo "só os próprios".
- **Bloqueio de escrita.** Com o cabeçalho, as rotas que escrevem respondem 403 `support_read_only`:
  exportar, favoritar, reordenar e ligar/desligar dashboard. Rotas que o modo não usa também respondem
  403. É uma lista explícita do que é permitido, não do que é proibido.
- **Abertura de dashboard em suporte.**
  - Hoje o `dashboard.view` é gravado pelo front (`api.log_dashboard_view`, com o token de quem está logado).
  - Em suporte, o front **não** chama essa RPC, para a abertura não entrar como sendo de quem pede.
  - Quem grava é a API, no `GET` do dashboard: um `support.viewed` por sessão + unidade + dashboard a cada
    5 min, a mesma janela do `log_dashboard_view`. Assim, trocar de filtro ou período não enche a auditoria.
- O 403 de dashboard negado em suporte não grava `dashboard.access_denied` em nome do membro.

### Front

- Botão **"Ver como este membro"** na gaveta do membro (Membros), só para Owner/Dev. Ele abre um modal que
  pede o motivo (ex.: número do chamado) e inicia a sessão.
- Um provider de suporte guarda a sessão em memória e em `sessionStorage`, para sobreviver a um recarregar
  na mesma aba; ele some ao fechar a aba.
  - Durante a sessão, o cliente HTTP manda `X-Support-Session`.
  - O hub e os dashboards usam as unidades e o nome do membro no lugar do `/me`.
- **Faixa "Vendo como Fulano"** fixa no topo, com foto, motivo, tempo restante e botão **Sair**. Sair
  encerra a sessão e volta à gaveta do membro.
- No modo suporte:
  - o menu mostra só Dashboards e Documentação;
  - as rotas de admin redirecionam ao hub;
  - exportar, favoritar, reordenar e ligar/desligar ficam escondidos ou desativados, com o aviso
    "Somente leitura no modo suporte";
  - Configurações e notificações continuam sendo as de quem pede.
- Resposta 409 `support_expired`: encerra o modo e mostra "A sessão de suporte venceu".
- Auditoria: volta o tipo **Suporte** no filtro, com rótulos para os três eventos ("Iniciou suporte como
  Fulano: motivo", "Abriu Comercial (NG) como Fulano", "Encerrou suporte").

### Por que não aparece (última parte, separável)

- No hub em suporte, um bloco "Dashboards ocultos para Fulano" lista os dashboards da unidade que o membro
  não vê, com o motivo em português: sem cargo nesta unidade, setor sem regra, desligado na unidade.
- Usa a função `app_private.dashboard_access_explain` da etapa 1 (branch `feat/modo-suporte`).
  - Ela é conferida contra a definição vigente da `dashboard_access`, que é a de
    `20261119170000_grupos_acesso.sql`; nenhuma migration posterior mexe nela.
  - A `dashboard_access` passa a ser um invólucro dela, para a explicação nunca divergir.
- Se essa parte atrasar, as anteriores já entregam o modo.

## Escolhas minhas (corrija se quiser)

- Validade de 1 h, sem renovar; para continuar, inicia de novo com motivo.
- Pode ver como qualquer membro ativo, inclusive Owner/Dev, menos a si mesmo.
- Uma sessão ativa por pessoa: iniciar outra encerra a anterior.
- O membro não é avisado.
- A Documentação continua acessível no modo (não depende do usuário).

## Para quem for construir

- Layout da faixa e do modal no padrão do "card padrão"; a faixa usa a cor de aviso, para não ser
  confundida com o app normal.
- O modo mock do front precisa simular sessão, membro e escopos.
- Testes:
  - API: sessão de outra pessoa, de outra organização, vencida, encerrada; quem pede rebaixado durante a
    sessão; cada rota de escrita bloqueada; `member_ref` usando o membro.
  - SQL: explain = dashboard_access para todos os casos das suítes existentes.
- A migration só vai para o lexhub-v2 com o OK do Luís; a versão no histórico é acertada depois.
