# Protocolo unificado (V2) — design

Data: 2026-11-09 · Card: #121 (front completo com mocks, até 12/11) · Dados: **mock**

## Objetivo

Uma página de Protocolo na V2 que junta:

- o **conteúdo** dos dois dashboards da v1 — "Protocolo" (base antiga) e "Protocolo (LexPre)";
- as **ideias e o visual** do protótipo da V2 (artefato "LexHub v2 — app navegável").

A página é a referência para os próximos dashboards: os módulos criados aqui (gráficos, seções,
tabela, filtros) são reaproveitados por Peticionamento, Organização de documentos e os demais.

## Decisões

| # | Decisão |
|---|---|
| 1 | **Fonte: só LexPre.** O contrato segue `ProtocoloLexpreNGResponse` da v1 (`api_dashboards/src/app/dashboard_routes.py`). A base antiga sai; os cards **de reajuizamento** ficam fora. |
| 2 | **Visual: protótipo da V2.** Tema claro, `tokens.css`, cards brancos, cor de destaque `--accent`, títulos em caixa normal. A v1 entra **só como fonte de conteúdo** (quais números e gráficos existem), nunca como estilo — inclusive blocos numerados e "Ocultar", que ganham o visual do protótipo. |
| 3 | Entram do protótipo, mesmo sem cálculo na v1: **metas nos KPIs** e **Pendências mais antigas**. Viram campos novos no contrato (a API terá de calcular). |
| 4 | Escopo desta rodada: KPIs, gráficos, tabela, **filtros**, **comissionamento e exportar**, **seções recolhíveis**. |
| 5 | Gráficos: **módulos próprios com Recharts por dentro** (abordagem A). Só `components/charts/` importa o Recharts. Listas simples (Top 10, por responsável) em CSS (`.hbar` do template). |
| 6 | Regra de exportação (definida em 09/11): colaborador exporta só o próprio setor; admin, dev e controller exportam qualquer setor. **Quem aplica é o servidor**; o front só obedece a `can_export`. |

## 1. A página, de cima para baixo

**Cabeçalho** (protótipo): `← Dashboards`, título "Protocolo · Nicolas Gomes", selo
"Atualizado há X · LexPre · fuso America/Manaus", pílulas de unidade. À direita: **período**,
**Filtros**, **Exportar** (se `can_export`), **Gerar comissão (PDF)** (se `can_see_commission`).
Abaixo do cabeçalho, as etiquetas dos filtros ativos.

Blocos numerados e recolhíveis:

| Bloco | Conteúdo | Depende do período? |
|---|---|---|
| 01 · No período | Protocolados, Valor de causa, Ticket médio, Tempo médio até protocolar (Meta: até 3 dias), Mediana do tempo, Protocolados no prazo (Meta: 90%). Cada um com "▲ x% vs. mês anterior". | sim |
| 02 · Situação atual | Represados, Devolvido p/ Peticionamento, p/ Org. documentos, p/ Pendência (com comparativo). | não |
| 03 · Por matéria e por funcionário | Top 10 protocolados por matéria; Top 10 represados por matéria; Por responsável (protocolados × represados, empilhado); Média de protocolados por funcionário (com linha de meta); Valor de causa por funcionário. Clicar numa matéria ou funcionário filtra a página. | sim |
| 04 · Produção | Protocolados por dia (colunas, como no protótipo); Represados por mês de entrada. | sim |
| 05 · Mês a mês | Protocolados por mês, uma linha por ano. | não (série histórica) |
| 06 · Pendências mais antigas | Processo, etapa, responsável, "parado há" (selo: ≥ 10 dias vermelho, ≥ 5 amarelo, senão cinza). | não |
| 07 · Comissionamento | Tabela por funcionário (qtd. protocolados, valor da comissão). Só com `can_see_commission`. | sim |

Cores dos gráficos: uma série = `--accent`; séries extras (empilhado, anos) em tons neutros dos
tokens, com o ano atual sempre em `--accent`. Cores que precisam ser distinguidas diferem também
em luminosidade.

## 2. Contrato de dados (`data/types.ts`)

Nomes da v1 (LexPre) para a conferência v2 × v1 campo a campo; o que é novo da V2 fica agrupado.

```ts
export type ProtocoloResponse = {
    meta: Meta
    stats: {
        // já existentes
        protocolados_total: WithComparison
        valor_causa_protocolado: WithComparison
        ticket_medio_protocolado: WithComparison
        media_tempo_protocolado: number
        mediana_tempo_protocolado: number
        comparativo_tempo_medio_protocolado: number | null
        comparativo_mediana_tempo_protocolado: number | null
        represados: number
        devolvido_peticionamento: number
        devolvido_org_doc: number
        devolvido_pendencia: number
        // novos, da v1
        comparativo_devolvido_peticionamento: number | null
        comparativo_devolvido_org_doc: number | null
        comparativo_devolvido_pendencia: number | null
    }
    // já existentes
    protocolados_por_dia: Point[]
    protocolados_por_materia: Point[]
    protocolados_por_funcionario: Point[]
    represados_por_funcionario: Point[]
    // novos, da v1
    represados_por_materia: Point[]
    media_protocolados_por_funcionario: Point[]
    valor_causa_por_funcionario: Point[]
    protocolados_por_mes: Point[] // name = 'AAAA-MM'
    represados_por_mes: Point[] // name = 'AAAA-MM'
    // opcional: a API só envia com permissão
    comissionamento_por_funcionario?: { funcionario: string; qtd_protocolados: number; valor_comissao: number }[]
    // novos, da V2
    protocolados_no_prazo: { taxa: number; comparativo: number | null } // taxa em %
    metas: { tempo_medio_dias: number; no_prazo_pct: number; protocolados_por_funcionario: number }
    pendencias_mais_antigas: { processo: string; etapa: string; responsavel: string; dias_parado: number }[]
    opcoes_filtro: { materias: string[]; funcionarios: string[]; ufs: string[]; areas: { id: number; nome: string }[] }
}
```

`DashboardQuery` ganha os filtros com os nomes dos parâmetros da v1:

```ts
export type DashboardFilters = { materia?: string[]; funcionario?: string[]; area_atuacao_id?: string[]; uf?: string[] }
export type DashboardQuery = { org: string; unit: string; from?: string; to?: string; filters?: DashboardFilters }
```

`DashboardSummary` (catálogo) ganha `can_export: boolean` e `can_see_commission: boolean`, por dashboard.

**Mock:** `protocoloFor(unit, query)` gera todos os campos por unidade com `unitScale`. Filtros
reduzem os números de forma determinística (sem `Math.random`), para o efeito ser visível. O
controller de teste recebe `can_export` e `can_see_commission` verdadeiros em todos os dashboards.

## 3. Módulos

**`components/charts/`** — o único lugar que importa o Recharts.

| Módulo | Responsabilidade | Parâmetros |
|---|---|---|
| `ChartCard` | Moldura: título, subtítulo, "Não há dados" quando vazio | `title`, `subtitle?`, `empty`, `children` |
| `ColumnChart` | Colunas verticais; empilhadas com `stacked` | `series: { name; data: Point[] }[]`, `stacked?`, `format?` |
| `BarChart` | Barras horizontais, com linha de referência opcional | `data`, `reference?: { value; label }`, `format?` |
| `LineChart` | Linhas suaves com tooltip, várias séries | `series`, `format?` |
| `RankList` | Top N em CSS (`.hbar`), clicável | `data`, `selected?`, `onSelect?`, `format?` |
| `chartTheme.ts` | Cores (dos tokens), fonte, formatação pt-BR | — |

**`components/`**

- `DashboardSection` — bloco numerado e recolhível: `number`, `kicker`, `title`, `description?`, `children`. Estado de recolhido local (`useState`).
- `KpiSection` → **`KpiGrid`** (só a grade); o título passa ao `DashboardSection`.
- `Kpi` ganha `meta?` ("Meta: até 3 dias").
- `DataTable` — tabela genérica a partir de colunas `{ header; render; align? }`.
- `PeriodPicker`, `FilterPanel`, `ActiveFilters` (ver seção 4).

**`dashboards/protocolo/`**

- `ProtocoloContent.tsx` — só monta os blocos 01–07 com os módulos.
- `view.ts` — funções puras: lista de KPIs a partir de `stats`/`metas`; séries do mês a mês por ano; tom do "parado há".

## 4. Filtros e fluxo de dados

- Tudo na URL: `?de=AAAA-MM-DD&ate=AAAA-MM-DD&materia=ANP&materia=MORA&funcionario=...&uf=AM&area=3`. Sem período = mês atual.
- `hooks/useDashboardFilters` — lê/escreve os parâmetros; devolve período, filtros, `set`, `toggle`, `clear`. Genérico.
- `DashboardModule` ganha `filters: { param; label; options: (data) => string[] | {value; label}[] }[]`.
- `DashboardView` lê os filtros, chama `fetch` com eles, desenha `PeriodPicker`/`FilterPanel`/`ActiveFilters` e passa `toggle` ao `Content` (filtro cruzado: clicar em "ANP" → `toggle('materia', 'ANP')`).
- Ao trocar filtro, os dados anteriores ficam na tela (esmaecidos) até os novos chegarem.
- As pílulas de unidade preservam os filtros (`location.search`).
- Sem dados após filtrar: cada `ChartCard` mostra "Não há dados". Erros 401/403/404: `ErrorState` existente.

## 5. Comissão, exportar e permissões

- Botões e bloco 07 seguem `can_export` / `can_see_commission` do catálogo (decididos pelo servidor).
- **Exportar:** `DataClient.exportDashboard(key, query): Promise<Blob>` (v1: `/protocolo-lexpre/export`). Mock gera CSV com linhas fictícias do período e filtros. `lib/download.ts` — `downloadBlob(blob, nome)`.
- **Gerar comissão (PDF):** mock usa `window.print()` com folha de impressão que mostra só o bloco 07 ("Salvar como PDF"). Na API, PDF gerado no servidor; a troca fica no `DataClient`.

## 6. Testes

- **Vitest** (nova dependência de desenvolvimento) nas funções puras: `protocolo/view.ts`; leitura/escrita de `useDashboardFilters` (incluindo valores repetidos); gerador do mock (filtros reduzem, unidades escalam).
- Navegador: todos os blocos; filtro cruzado; F5 mantém filtros; troca de unidade mantém filtros; Exportar baixa CSV; comissão abre a impressão; sem permissão os botões somem.
- `npx tsc -b`, `npm run lint`, `npm run format:check` limpos.

## Fora desta rodada

- Cards de reajuizamento (base antiga).
- Filtro por sistema (base antiga).
- `protocolados_por_dia_por_funcionario` da v1 (sem uso na página).
- PDF de comissão real e exportação real (dependem da API, #120/#123).
- Preferência de seção recolhida guardada entre visitas.

## Ordem de construção

1. Contrato + mock (`types.ts`, `mock/protocolo.ts`, `DashboardSummary` com permissões).
2. `DashboardSection`, `KpiGrid`, `Kpi.meta`, `DataTable` — blocos 01, 02, 06.
3. Recharts + `components/charts/` — blocos 03, 04, 05.
4. `useDashboardFilters`, `PeriodPicker`, `FilterPanel`, `ActiveFilters`, filtro cruzado.
5. Exportar, comissão (bloco 07 e impressão).
6. Vitest + testes das funções puras; README do `apps/web` atualizado.

Cada etapa deixa a página funcionando.
