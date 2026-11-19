# Auditoria: dashboards abertos + filtro de período

Data: 19/11/2026 · Aprovado pelo Luís

## Por quê

Owner e Dev querem ver quais colaboradores abriram cada dashboard (e quando), para saber o que é usado. Hoje a
auditoria registra entradas, exportações e acessos negados, mas abrir um dashboard não gera registro.

## Objetivos

- Novo tipo de evento na Auditoria: **"Dashboards abertos"** (`dashboard.view`), uma linha por abertura:
  `Ana Souza · Abriu dashboard · Comercial (LexPre) · NG`.
- O tipo atual "Acesso" passa a se chamar **"Mudanças de acesso"** (mesmo conteúdo), para não confundir.
- Novo filtro **Período** (7 dias por padrão; 30, 90 dias ou datas livres), filtrado no banco.

## Não objetivos

- Resumo por dashboard ("12 de 18 abriram", "nunca abriu") — fica para depois (opção B).
- Tempo de uso / tempo na página.

## Anti-objetivos

- Uma TV ou alguém mexendo em filtros não pode encher a auditoria de linhas iguais.
- O registro nunca pode impedir o dashboard de abrir.

## Abordagens

- **A (escolhida): eventos na Auditoria existente.** Reaproveita tela, filtros e export; contar é manual.
- **B: tela de resumo por dashboard.** Responde direto quem usa e quem nunca abriu; mais trabalho. Depois, sobre o
  mesmo registro.
- Registro pela **API** (na chamada de dados) foi descartado: ela é chamada a cada troca de período/filtro e na
  atualização automática, e não distingue abertura de atualização.

## Como (decidido)

- **Registro pelo front**: ao abrir o dashboard (`DashboardView`, uma vez por org/unidade/dashboard), chamada
  "dispara e esquece" a `api.log_dashboard_view(p_org, p_unit, p_dashboard)`. Falha é ignorada.
- `api.log_dashboard_view` (security definer): só membro ativo da organização; dashboard tem de existir no catálogo;
  unidade da org. **Ignora repetição**: mesma pessoa + dashboard + unidade em menos de 5 minutos não grava (F5,
  clique duplo, StrictMode). Grava `audit_log` com `action = 'dashboard.view'`, `target_type = 'dashboard'`,
  `target_id = chave`, `metadata = {org, unit}`.
- Na TV (login por QR) a abertura conta para quem aprovou.
- **`api.list_audit` com filtros no banco**: ganha `p_from`, `p_to` (timestamptz) e `p_kinds` (lista de actions,
  opcional). Até 2000 eventos por consulta; a tela avisa quando bate o limite ("estreite o período"). Motivo: hoje
  ela devolve só os últimos 500 eventos e o filtro é no navegador; com as aberturas, a janela viraria 2–3 dias.
- O Export CSV continua exportando o que está na tela.

## Para quem constrói decidir

- Formato exato do campo Período (select + datas), seguindo o padrão visual dos filtros da Auditoria.
- Como mapear "tipo" do filtro para a lista de actions enviada ao banco.
- Índice extra no `audit_log` se a consulta da repetição ficar lenta (hoje há `(org_id, created_at desc)`).
