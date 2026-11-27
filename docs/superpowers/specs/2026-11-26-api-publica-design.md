# API pública (chave de API para gestores) — design

Data: 26/11/2026 · Autor: Luís (com Claude)

## Intenção

Os setores precisam consultar os dados do LexHub fora da tela: consultas, análises, BI (Power BI/Excel),
métricas e planejamento. A v1 tinha isso (`api_dashboards/src/app/public_api` + doc
`LexHub/src/pages/documentacao/ApiPublica.tsx`), só para Marketing e Comercial, com escopo e escritório
fixos. A v2 leva a ideia para o modelo novo (org → unidade → setor), começando por Marketing e Comercial
e aberta aos demais setores sem rota nova.

## Metas

- Gestor, Controller ou Owner pede uma chave de API; um Desenvolvedor aprova ou recusa.
- A chave consulta **só o setor do gestor**, e setores extras apenas com aprovação explícita.
- Os dados da API são os mesmos do "Exportar" do dashboard (API e arquivo sempre batem).
- Tokens como na v1: access token curto + refresh token com rotação.
- Revogar (a chave ou só um setor extra) vale na hora.
- Toda chamada é auditada.

## Não-metas

- Escrita pela API (é só leitura).
- Rotas específicas por relatório como na v1 (`/marketing/leads` etc.).
- Compatibilidade de URL com a v1.
- Chave para Colaborador, Leitor, Desenvolvedor ou cliente de sistema sem dono.

## Anti-metas (falharia mesmo funcionando)

- A chave ver algo que o gestor não vê no LexHub.
- Setor extra ficar esquecido para sempre na chave.
- Um segundo caminho de permissão paralelo a Membros/Acesso.
- Org de fora da LexGroup chegar aos bancos NG/LA ([regra dos bancos internos]).

## Regra de negócio

- **Quem pede:** quem é **Gestor** ou **Controller** em alguma unidade da org, ou **Owner** da org. O
  botão "Pedir chave de API" só aparece para eles. Unidades alcançadas: as unidades onde a pessoa é
  Gestor/Controller; para o Owner, todas as unidades da org.
- **Quem aprova:** Desenvolvedor da org. Pedidos pendentes aparecem com selo no menu de administração,
  como os pedidos de acesso. O Dev pode aprovar só parte dos setores extras pedidos.
- **Setor base:** os setores atuais do gestor (`app.membership_teams`), lidos a cada chamada. Se ele sair
  do setor, o acesso base daquele setor cai.
- **Setor extra:** pedido com **justificativa obrigatória** e **validade obrigatória** (padrão 90 dias).
  Fica gravado quem aprovou e quando. Pode ser revogado sozinho, sem derrubar a chave.
- **Alcance da chave** = (setores base + extras vigentes) → dashboards pelo mapa setor→dashboards já
  existente (`20261118110000_acesso_por_setor.sql`), ∩ unidades alcançadas (ver "Quem pede"), ∩ dashboards
  ligados na unidade, ∩ dashboards com exportação. A permissão `unit.dashboards.all` do Gestor **não**
  vale na API: o setor é que filtra. O extra amplia o filtro de setor, nunca passa das unidades do gestor.
- **Fim da chave:** perdeu o cargo (Gestor/Controller/Owner), saiu da org, chave revogada ou token vencido → 401/403 na
  próxima chamada.
- **Sem setor cadastrado** (comum no Owner): a base fica vazia. A tela de pedido avisa e o pedido só pode seguir
  com setores extras (ou o Dev ajusta o setor em Membros).
- Marketing não é setor na v2; está dentro de Comercial. Para o começo, Comercial cobre os dois.

## Abordagens consideradas

- **A) Igual à v1: access 1 semana + refresh 30 dias com rotação — escolhida pelo Luís.** Mais segura
  contra vazamento (token vazado vale pouco; reuso de refresh revoga tudo). Custo aceito: Power BI/Excel
  não guardam o refresh novo sozinhos, então o consumo agendado precisa de um script que renove e guarde
  o par (a v1 já tinha um script pronto em Python, levar para o guia).
- **B) Chave fixa com validade (90 dias).** Mais simples no Power BI, mas um vazamento vale até revogar
  ou vencer. Trocada pela A.
- **C) Pelo Supabase (views/RPC).** Descartada: os dados vêm dos bancos NG/LA via análises em Python,
  fora do alcance do Supabase.

## Como fica (decidido)

- Dentro da API da v2 (`apps/api`), prefixo `/v1`. Nada de serviço separado.
- **Rota genérica por dashboard:**
  `GET /v1/orgs/{org}/units/{unit}/dashboards/{key}?from&to&campos&relatorio&pagina&tamanho_pagina`,
  em JSON, usando as mesmas peças do export (`export.pick_report`, `spec.rows`, `export.pick_fields`,
  ver `routes/dashboards.py` → `dashboard_export`).
- Catálogo: `GET /v1/me` (ou `/v1/catalogo`) lista o que a chave alcança: unidades, dashboards,
  relatórios e campos de cada um.
- Autenticação no modelo da v1 (`api_dashboards/src/app/public_api/tokens.py` e `store.py`):
  - Depois da aprovação, a própria pessoa clica em "Gerar tokens" nas Configurações (o Dev nunca vê os
    tokens) e recebe o par: **access token** (JWT, 1
    semana, assinado com segredo próprio da API pública) + **refresh token** (`lxr_…`, 30 dias). Os dois
    aparecem uma vez só.
  - Rotas de dados: `Authorization: Bearer <access_token>`.
  - `POST /v1/auth/token` com o refresh devolve access novo + refresh novo (mais 30 dias); o anterior
    deixa de valer. Reusar um refresh já trocado (inclusive duas renovações ao mesmo tempo) revoga todos
    os tokens da chave (`tokens_validos_desde`).
  - Refresh guardado só como hash (SHA-256). Access com `iat` anterior a `tokens_validos_desde` é recusado.
  - Permissões **não** vão no token: são lidas do banco a cada chamada (cache curto, ~60 s), então
    revogar chave/setor ou perder o cargo vale sem esperar o access vencer.
- Tabelas novas no schema `app`, com RLS ligado e sem policy para `anon`/`authenticated` (só o backend):
  chave (dono, ativo, `tokens_validos_desde`), refresh tokens (hash, expira, usado, revogado, substituído
  por), setores extras da chave (validade, justificativa, aprovador) e pedidos. Escrita do front via RPCs
  no padrão das migrations da v2, cada uma com rollback.
- Telas: botão/modal "Pedir chave de API" para o Gestor (com setores extras + justificativa + validade) e
  aba "Chaves de API" no admin para o Dev (pendentes, ativas, último uso, revogar chave, revogar extra,
  gerar novos tokens).
- Auditoria: cada chamada grava em `app.audit_log` (ação nova, ex. `api.read`, `actor_user_id` = gestor,
  metadata com chave, dashboard, unidade, período). Pedido, aprovação, recusa e revogação também.
- Doc para o usuário: guia novo em `docs/guia-do-usuario`, no estilo da doc da v1 (cURL, JavaScript,
  Python, Power BI).

## Chamadas minhas (Claude) — conferir

- A chave em si não vence; quem vence são os tokens (access 1 semana, refresh 30 dias). Refresh vencido
  sem uso → pede "Gerar novos tokens" na tela (sem nova aprovação, enquanto a chave estiver ativa).
- Uma chave ativa por pessoa por org; "Gerar novos tokens" revoga os anteriores.
- O guia leva o script de renovação da v1 (Python) adaptado, para quem agenda consumo (Power BI etc.).
- Limites herdados da v1: período ≤ 366 dias, `tamanho_pagina` 1–5000 (padrão 1000), `campos` por
  vírgula ou repetido.
- Formato da resposta igual ao `RespostaDados` da v1 (dados + paginação + total).
- Limite de taxa por chave (sugestão 60 req/min) com 429.
- Cache: o mesmo do dashboard (Redis L2); a API não cria cache próprio.

## Dependências e restrições

- Export de Marketing e Comercial ainda pendente na v2: a API desses setores sai depois ou junto.
- Bancos NG/LA só para orgs da LexGroup (já garantido pelas fontes; a API não pode contornar).
- Migrations aplicadas no lexhub-v2 e com histórico alinhado ([histórico de migrations]).
- CI usa Node 24: testes do front com `NODE_OPTIONS=--no-experimental-webstorage`.

## Deixado para quem constrói

- Nomes exatos das tabelas, RPCs e da ação de auditoria.
- Como reaproveitar `_prepare`/`require_dashboard` sem a sessão do Supabase (a chave resolve para o
  `user_id` do gestor e o alcance é calculado com o filtro de setor acima).
- Layout das telas, seguindo o canvas do protótipo da v2.
