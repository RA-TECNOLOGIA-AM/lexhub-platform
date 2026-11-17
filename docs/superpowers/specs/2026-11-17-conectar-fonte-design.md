# Conectar fonte — ligar uma unidade aos dados dela

Data: 17/11/2026 · Branch: `feat/conectar-fonte` · Status: estrutura fechada em conversa, em revisão

Detalhes técnicos (SQL e contratos): [2026-11-17-conectar-fonte-contratos.md](2026-11-17-conectar-fonte-contratos.md).

Protótipos (dados fictícios, anteriores às decisões finais):
- explicação: https://claude.ai/artifact/DMfqwemqs2dhfigvU6hPwj
- simulador: https://claude.ai/artifact/16dUANsRQjYa4H469WpCrZ

## Objetivo

Hoje o botão **Conectar fonte** da aba Unidades e fontes só mostra um aviso, e a ligação
unidade → banco (`app.unit_source_refs`) é feita à mão, por migration. Esta entrega faz isso pela tela:
a TI da LexGroup liga uma unidade ao LexPre/LexFlow, a um banco próprio (Postgres ou MySQL) ou a uma
planilha Google, e os dashboards aparecem quando ligados àquela fonte.

## Regras (Luís, 17/11)

1. **Unidade = escritório.** Ela nasce sem fonte: aparece como "Nenhuma fonte ligada" e não tem
   dashboards. A regra que já existe ("o dashboard aparece se a unidade tem a fonte dele") esconde tudo.
2. **Só Owner/Dev da organização LexGroup conectam e gerenciam fontes, em qualquer organização.**
   - O Owner de uma organização cliente **não** conecta. Gestor e Controller também não.
   - Todos eles veem o status das fontes das suas unidades.
   - Sem link para TI externa e sem envio para aprovação: mais simples e mais seguro.
3. **A TI da LexGroup abre qualquer organização pela tela Clientes** (modo suporte, auditado) para
   conectar as fontes do cliente.
4. **NG e LA (bancos internos) são só da LexGroup**, nas unidades NG, LAAM e LARJ.
   - Não aparecem na tela.
   - Nunca ficam disponíveis para outra organização nem para uma unidade nova.
   - Liberar uma unidade nova da LexGroup exige migration.
5. **LexPre/LexFlow:**
   - a lista vem direto do banco do produto (`select id, nome from escritorio`), com o acesso que já existe
     no `.env`;
   - não precisa de chave cliente → escritório, porque só a TI da LexGroup vê a lista;
   - um escritório só pode estar ligado a uma unidade (índice único global).
6. **Credenciais nunca no `.env`.** A configuração fica em `app.data_sources.config` (sem senha) e a
   senha no **Supabase Vault**. O `.env` continua com os 4 bancos fixos e as chaves da plataforma.
7. **Quem fala com o banco da operação é a API**, a partir do IP fixo da VPS. O navegador nunca fala.
8. **Banco próprio não traz dashboards prontos.** A fonte fica "Aguardando dashboards" até o analista
   escrever as queries (`"database": "<key da fonte>"`) e ligar os dashboards.
9. **Data Studio:** não há API que devolva os dados de um relatório. Conectamos a fonte que está por
   trás dele.

## Processo

| Situação | O que a TI da LexGroup faz |
|---|---|
| Operação no LexPre/LexFlow | Cria a unidade → Conectar fonte → LexPre/LexFlow → escolhe o escritório. Os dashboards aparecem na hora. |
| Operação com banco próprio | Pede ao cliente o usuário `lexhub_leitura` (o SQL fica na tela) e a liberação do IP → preenche → **Testar e salvar**. A fonte fica "Aguardando dashboards". |
| Planilha | Compartilha a planilha com a conta de serviço → cola o link → escolhe a aba → **Conectar planilha**. |
| Depois | O analista escreve as queries e liga os dashboards à fonte. |

Em organização cliente, a TI entra pela tela **Clientes → Abrir organização** antes de começar.

## Telas

### Conectar fonte (só Owner/Dev da LexGroup)

**Passo 1, escolher o tipo:** LexPre, LexFlow, Postgres, MySQL ou Google Planilhas.
- LexPre/LexFlow ficam bloqueados se a unidade já tiver aquele produto.

**LexPre / LexFlow:** lista de escritórios do banco do produto.
- Cada um mostra a atividade dos últimos 30 dias.
- Os que já estão em outra unidade ficam bloqueados, com "Ligado à unidade X".
- Botão **Ligar escritório**.

**Postgres / MySQL:**
- Box retrátil "Como pedir o acesso ao cliente", com o IP de saída e o SQL do `lexhub_leitura`, ambos
  com botão de copiar.
- No topo, **URL de conexão** (`postgresql://…` ou `mysql://…`): ao colar, preenche os campos.
- Divisor **ou preencha**.
- **IP ou nome do host** + **Porta (opcional)**, com placeholder 5432 ou 3306.
- **Banco de dados**.
- **Nome de usuário** + **Senha**, com ícone de olho para revelar.
- **Ativar SSL** (checkbox): ligado = `require`, desligado = `disable`.
- Rodapé com um botão só, **Testar e salvar**:
  - **teste falhou:** mostra as checagens (rede, login, leitura, só leitura) e não salva;
  - **usuário pode escrever:** mostra o aviso e o botão vira **Salvar mesmo assim**, registrado na
    auditoria;
  - **tudo ok:** salva, fecha e a fonte aparece como "Aguardando dashboards".

**Google Planilhas:**
1. Caixa com o e-mail da conta de serviço + **Copiar e-mail**, com o texto "Compartilhe sua planilha
   como Leitor com este e-mail".
2. **Link da planilha**. Ao colar, a API valida o acesso e lista as abas. Se a planilha não estiver
   compartilhada, aparece "compartilhe com {e-mail}".
3. **Aba dos dados**: dropdown habilitado depois da validação.
4. Botão **Conectar planilha**.

### Aba Unidades e fontes
- **Estado vazio** "Nenhuma fonte ligada", com o botão (só para a TI da LexGroup).
- **Selos novos:** "Aguardando dashboards" e "Sem dados ainda".
- **Detalhe da fonte:**
  - configuração mascarada: usuário sim, senha "••••";
  - para a TI da LexGroup: **Testar de novo**, **Trocar senha** e **Desconectar** (com confirmação na
    própria tela).

### Clientes → Abrir organização (modo suporte)
- A TI da LexGroup abre a organização do cliente sem ser membro dela.
- Uma faixa no topo avisa "Você está na organização X como suporte", com o botão Sair.
- Entrar e sair ficam na auditoria **da organização do cliente** (`support.opened` / `support.closed`).
- O que fica liberado: as páginas de administração (Unidades e fontes) e os dashboards dessa
  organização, para conferir se apareceram.

## Ordem de entrega (um PR cada)

| PR | Conteúdo |
|----|----------|
| **0** | Só leitura por transação nos 4 bancos atuais. Corrige o LAADV atrás do PgBouncer, onde o `SET` de sessão pode se perder. |
| **1** | `is_source_admin` (Owner/Dev da LexGroup), travas de NG/LA, colunas novas de `data_sources`, a lista de escritórios e a ligação LexPre/LexFlow, a unidade sem fonte e o assistente com o primeiro passo. |
| **2** | Vault, `ConnectionProvider` (bancos do `.env` + fontes cadastradas), conector Postgres com teste e proteção de rede, e o gerenciamento (testar de novo, trocar senha, desconectar). |
| **3** | MySQL, Google Planilhas e o `schema_cache` com amostra de 5 linhas para Dev. |
| **4** | Modo suporte: a TI da LexGroup abre qualquer organização pela tela Clientes. |
| **5** | Checagem de saúde a cada 10 min (trava por fonte) e notificações quando o estado muda. |

O PR 1 já funciona para as unidades da própria LexGroup. Para conectar fontes de clientes, é preciso
o PR 4.

## Infra a confirmar

1. **Usuário da `DATABASE_URL`.** As funções novas seguem o padrão atual (`grant` para `service_role`,
   `revoke` de `authenticated`). O papel `lexhub_api` é um endurecimento separado.
2. **Firewall de saída na VPS** (`DOCKER-USER`) e as exceções privadas, se existirem.
3. **Swarm com mais de um nó?** Se tiver, fixar a API num nó para o IP liberado continuar válido.

## Fora desta entrega

- Incorporar relatório do Data Studio (iframe).
- Envio de credenciais pelo gestor ou por TI externa.
- Túnel SSH ou banco em rede fechada.
- Outros conectores (Meta, Conta Azul, SQL Server).
- Tela para o analista escrever queries (continua em `source_queries.py`).
- Migrar os 4 bancos do `.env` para o Vault.
