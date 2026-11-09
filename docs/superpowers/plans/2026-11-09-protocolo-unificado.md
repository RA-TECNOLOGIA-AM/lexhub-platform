# Protocolo unificado (V2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Neste projeto:** o Luís digita o código (está aprendendo React) e o Claude explica cada passo e confere. **Commits são feitos pelo Luís**; o passo "Commit" de cada tarefa traz só a mensagem sugerida.

**Goal:** Página de Protocolo da V2 com o conteúdo do Protocolo (LexPre) da v1 e o visual do protótipo V2 — KPIs com metas, gráficos, pendências mais antigas, filtros na URL, comissionamento e exportar — tudo em mock.

**Architecture:** O contrato `ProtocoloResponse` cresce com os campos da v1 LexPre e os novos da V2; o mock gera tudo por unidade e filtro. As telas montam módulos genéricos (`DashboardSection`, `KpiGrid`, `DataTable`, `components/charts/*`, filtros), e só `components/charts/` conhece o Recharts. Filtros vivem na URL e passam pelo `DashboardView` até o `fetch` e o `Content`.

**Tech Stack:** React 19, React Router 8, TypeScript 7, Vite 8, Recharts (nova), Vitest (nova, dev), Oxlint, Prettier.

**Spec:** `docs/superpowers/specs/2026-11-09-protocolo-unificado-design.md`

## Global Constraints

- Todos os comandos rodam em `apps\web` (PowerShell); antes de cada commit: `npx tsc -b`, `npm run lint`, `npm run format:check` sem erro.
- Prettier: 4 espaços, sem `;`, aspas simples, até 120 colunas, CRLF.
- Visual: protótipo da V2 (`tokens.css`, `--accent`, tema claro, títulos em caixa normal). A v1 é só fonte de conteúdo.
- Nomes de campos: os da v1 `ProtocoloLexpreNGResponse`; o que é novo da V2 fica em `protocolados_no_prazo`, `metas`, `pendencias_mais_antigas`, `opcoes_filtro`.
- Metas do mock: `tempo_medio_dias: 3`, `no_prazo_pct: 90`, `protocolados_por_funcionario: 20`.
- Selo "parado há": `>= 10` dias → `badge danger`; `>= 5` → `badge warn`; senão `badge neutral`.
- Parâmetros da URL: `de`, `ate` (AAAA-MM-DD), `materia`, `funcionario`, `uf`, `area` (repetidos para vários). Sem período = mês atual.
- Só `src/components/charts/` importa `recharts`.
- Telas só falam com dados via `dataClient`. Sem `Math.random` no mock.
- Cada módulo novo tem o comentário de cabeçalho "Módulo: … Parâmetros: … Esconde: …" como os existentes.

## Review Focus

1. Filtro que zera os dados (funcionário que não existe na unidade) → KPIs mostram 0 (nunca `NaN`/`Infinity` no ticket médio ou na taxa) e cada gráfico mostra "Não há dados".
2. URL com período inválido (`de` depois de `ate`, data mal escrita) → volta para o mês atual, sem quebrar.
3. CSV com vírgula, aspas ou acento em matéria/funcionário → campos escapados e BOM UTF-8, para o Excel abrir os acentos.
4. Usuário sem `can_see_commission` → nem botão "Gerar comissão" nem bloco 07, mesmo que o campo venha na resposta.
5. Filtros trocados rápido → a resposta atrasada não sobrescreve a nova (proteção `ignore` do `useAsync`); dados antigos ficam esmaecidos, sem voltar ao esqueleto.

---

### Task 1: Vitest, contrato e mock do Protocolo

**Files:**
- Modify: `apps/web/package.json` (scripts `test`, `test:watch`; devDependency `vitest`)
- Modify: `apps/web/src/data/types.ts` (`ProtocoloResponse`, `DashboardFilters`, `DashboardQuery`, `DashboardSummary`)
- Modify: `apps/web/src/data/mock/protocolo.ts`
- Modify: `apps/web/src/data/mock/catalog.ts` (`entry()` preenche permissões)
- Modify: `apps/web/src/data/mockClient.ts` (`dashboardResponse` passa a `query` ao `build`)
- Test: `apps/web/src/data/mock/protocolo.test.ts`

**Interfaces:**
- Produces:
  - `type DashboardFilters = { materia?: string[]; funcionario?: string[]; area_atuacao_id?: string[]; uf?: string[] }`
  - `type DashboardQuery = { org: string; unit: string; from?: string; to?: string; filters?: DashboardFilters }`
  - `DashboardSummary` + `can_export: boolean; can_see_commission: boolean`
  - `Meta` + `timezone: string` — `metaFor` usa `America/Manaus` para NG e LA_AM, `America/Sao_Paulo` para LA_RJ
  - `ProtocoloResponse` exatamente como na seção 2 da spec.
  - `protocoloFor(unit: string, query?: DashboardQuery): ProtocoloResponse`
  - `dashboardResponse(key, query, build: (unit: string, query: DashboardQuery) => T)`

- [ ] **Step 1:** `npm install -D vitest`; em `package.json`, `"test": "vitest run"` e `"test:watch": "vitest"`. Vitest roda em ambiente `node` (só funções puras), sem config extra.
- [ ] **Step 2: Write the failing tests** em `protocolo.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { protocoloFor } from './protocolo.ts'

const q = (filters = {}) => ({ org: 'lexgroup', unit: 'NG', filters })

describe('protocoloFor', () => {
    it('traz metas fixas do mock', () => {
        expect(protocoloFor('NG').metas).toEqual({ tempo_medio_dias: 3, no_prazo_pct: 90, protocolados_por_funcionario: 20 })
    })
    it('LA_RJ é menor que NG nas contagens', () => {
        expect(protocoloFor('LA_RJ').stats.protocolados_total.total).toBeLessThan(protocoloFor('NG').stats.protocolados_total.total)
    })
    it('filtro de matéria reduz os protocolados', () => {
        const all = protocoloFor('NG', q()).stats.protocolados_total.total
        const one = protocoloFor('NG', q({ materia: ['ANP'] })).stats.protocolados_total.total
        expect(one).toBeLessThan(all)
        expect(one).toBeGreaterThan(0)
    })
    it('funcionário inexistente zera tudo sem NaN', () => {
        const r = protocoloFor('NG', q({ funcionario: ['Ninguém'] }))
        expect(r.stats.protocolados_total.total).toBe(0)
        expect(Number.isFinite(r.stats.ticket_medio_protocolado.total)).toBe(true)
        expect(r.protocolados_por_dia.every((p) => p.value === 0)).toBe(true)
    })
    it('mês a mês usa name AAAA-MM', () => {
        expect(protocoloFor('NG').protocolados_por_mes.every((p) => /^\d{4}-\d{2}$/.test(p.name))).toBe(true)
    })
    it('opções de filtro listam as matérias da resposta', () => {
        const r = protocoloFor('NG')
        expect(r.opcoes_filtro.materias).toEqual(r.protocolados_por_materia.map((p) => p.name))
    })
})
```

- [ ] **Step 3:** `npm test` → FAIL (`metas` inexistente / assinatura).
- [ ] **Step 4: Implement.** Tipos da spec em `types.ts`. Em `protocolo.ts`: matérias com nomes da v1 (`ANP`, `RUBRICAS_REUNIDAS`, `RUBRICAS_REUNIDAS_IRDR`, `CESTA`, `SVA`, `PARC_CRED_PESS`, `JUROS_ABUSIVOS`, `MORA`, `MORA_CRED_PESS`, `ESPECIFICA`); um fator `share` = fração das matérias/funcionários escolhidos (1 sem filtro, 0 se nenhum existe) aplicado a contagens, valores e séries; ticket = valor/qtd com guarda para 0; `protocolados_por_mes` de 2024-01 até 2026-10 e `represados_por_mes` dos últimos 6 meses; `pendencias_mais_antigas` com 6 linhas (dias 14, 12, 9, 6, 4, 3); `opcoes_filtro.ufs = ['AM', 'PA', 'RR']`, `areas` com 3 itens. `catalog.ts`: `entry()` define `can_export: true, can_see_commission: true`. `mockClient.ts`: `build(query.unit, query)`; `getPendencias` ignora o 2º argumento.
- [ ] **Step 5:** `npm test` → PASS; `npx tsc -b` sem erro (o `ProtocoloContent` atual continua compilando).
- [ ] **Step 6: Commit** — `Front: contrato do Protocolo (v1 LexPre + metas, no prazo, pendências, opções de filtro), mock com filtros e Vitest`

### Task 2: Seções, KPIs, tabela — blocos 01, 02 e 06

**Files:**
- Create: `apps/web/src/components/DashboardSection.tsx`
- Create: `apps/web/src/components/DataTable.tsx`
- Rename: `apps/web/src/components/KpiSection.tsx` → `KpiGrid.tsx`
- Modify: `apps/web/src/components/Kpi.tsx` (prop `meta?`)
- Modify: `apps/web/src/dashboards/pendencias/PendenciasContent.tsx` (usa `DashboardSection` + `KpiGrid`)
- Create: `apps/web/src/dashboards/protocolo/view.ts`
- Modify: `apps/web/src/dashboards/protocolo/ProtocoloContent.tsx`
- Modify: `apps/web/src/styles/app.css`
- Test: `apps/web/src/dashboards/protocolo/view.test.ts`

**Interfaces:**
- Consumes: `ProtocoloResponse` (Task 1).
- Produces:
  - `DashboardSection({ number: string; kicker: string; title: string; description?: string; children: ReactNode })` — botão "Ocultar"/"Mostrar" com `aria-expanded` e `aria-controls`.
  - `KpiGrid({ children: ReactNode })`
  - `Kpi` + `meta?: ReactNode`
  - `type Column<T> = { header: string; render: (row: T) => ReactNode; align?: 'left' | 'right' }`; `DataTable<T>({ columns: Column<T>[]; rows: T[]; rowKey: (row: T) => string; empty?: string })`
  - `staleBadge(dias: number): 'badge danger' | 'badge warn' | 'badge neutral'`
  - `seriesByYear(points: Point[]): { name: string; data: Point[] }[]` — uma série por ano (`name` = '2024'…), `data` com `name` = mês abreviado ('jan'…'dez'), 12 pontos (mês sem dado = 0, menos meses futuros do ano corrente, que ficam de fora).

- [ ] **Step 1: Write the failing tests** em `view.test.ts`:

```ts
it('staleBadge', () => {
    expect(staleBadge(12)).toBe('badge danger')
    expect(staleBadge(10)).toBe('badge danger')
    expect(staleBadge(9)).toBe('badge warn')
    expect(staleBadge(5)).toBe('badge warn')
    expect(staleBadge(4)).toBe('badge neutral')
})
it('seriesByYear separa por ano e nomeia os meses', () => {
    const s = seriesByYear([{ name: '2025-01', value: 5 }, { name: '2025-03', value: 7 }, { name: '2026-01', value: 9 }])
    expect(s.map((x) => x.name)).toEqual(['2025', '2026'])
    expect(s[0].data[0]).toEqual({ name: 'jan', value: 5 })
    expect(s[0].data[1]).toEqual({ name: 'fev', value: 0 })
    expect(s[0].data).toHaveLength(12)
})
```

- [ ] **Step 2:** `npm test` → FAIL.
- [ ] **Step 3: Implement** `view.ts`, os módulos e os blocos: 01 "No período" (6 KPIs; tempo médio com `meta="Meta: até {metas.tempo_medio_dias} dias"`; no prazo = `fmt.pct(taxa)` com `meta="Meta: {no_prazo_pct}%"`), 02 "Situação atual" (4 KPIs com `Delta`; devoluções com `betterWhenDown`), 06 "Pendências mais antigas" (`DataTable`; processo em `var(--mono)`; selo de `staleBadge`). CSS: cabeçalho da seção com o número em chip (`--surface-3`, `--r-md`), kicker `--fs-xs` `--text-muted`, botão `.btn`. Pendências passa a usar `DashboardSection` (01 "No período", 02 "Situação atual").
- [ ] **Step 4:** `npm test` → PASS; `npx tsc -b`, `npm run lint` limpos; no navegador, Protocolo mostra 01, 02 e 06, "Ocultar" recolhe e o leitor de tela recebe `aria-expanded`; Pendências igual a antes.
- [ ] **Step 5: Commit** — `Front: DashboardSection, KpiGrid, Kpi com meta e DataTable; Protocolo com blocos 01, 02 e 06`

### Task 3: Gráficos — blocos 03, 04 e 05

**Files:**
- Modify: `apps/web/package.json` (dependency `recharts`)
- Create: `apps/web/src/components/charts/chartTheme.ts`, `ChartCard.tsx`, `ColumnChart.tsx`, `BarChart.tsx`, `LineChart.tsx`, `RankList.tsx`
- Modify: `apps/web/src/dashboards/protocolo/ProtocoloContent.tsx`, `apps/web/src/styles/app.css`

**Interfaces:**
- Consumes: `seriesByYear` (Task 2), `Point` (types).
- Produces:
  - `type Series = { name: string; data: Point[] }`
  - `ChartCard({ title: string; subtitle?: string; empty: boolean; children: ReactNode })` — vazio mostra "Não há dados".
  - `ColumnChart({ series: Series[]; stacked?: boolean; format?: (v: number) => string; height?: number })`
  - `BarChart({ data: Point[]; reference?: { value: number; label: string }; format?: (v: number) => string })`
  - `LineChart({ series: Series[]; format?: (v: number) => string })`
  - `RankList({ data: Point[]; limit?: number; selected?: string[]; onSelect?: (name: string) => void; format?: (v: number) => string })` — usa `.hbars/.hbar`; com `onSelect`, cada linha é `<button aria-pressed>`.
  - `chartTheme`: `seriesColor(index: number, total: number): string` — a última série (ano atual / principal) é `--accent` (#B35500); as demais em neutros que diferem em luminosidade (`#8A93A0`, `#C9CED6`); eixos `--text-faint`, grade `--divider`, fonte Inter 12px; tooltip com `fmt`.

- [ ] **Step 1:** `npm install recharts`.
- [ ] **Step 2: Implement** os módulos (Recharts `ResponsiveContainer` + `BarChart`/`LineChart` com `type="monotone"`, `ReferenceLine` tracejada na meta). Blocos: 03 (grid 2–3 colunas: Top 10 protocolados por matéria e Top 10 represados por matéria em `RankList`; Por responsável em `ColumnChart stacked` com séries "Protocolados" e "Represados"; Média por funcionário em `BarChart` com `reference={{ value: metas.protocolados_por_funcionario, label: 'Meta: 20' }}`; Valor de causa por funcionário em `BarChart` com `fmt.brlShort`), 04 (Protocolados por dia `ColumnChart`, subtítulo com o período; Represados por mês `ColumnChart`), 05 (`LineChart` com `seriesByYear(protocolados_por_mes)`). `empty` = todos os valores 0 ou lista vazia.
- [ ] **Step 3:** `npx tsc -b`, `npm run lint`, `npm run format:check`; `rg recharts src` mostra só `src/components/charts/`.
- [ ] **Step 4:** Navegador: blocos 03–05 com cores do protótipo; tooltip em pt-BR; em largura de celular (375 px) os cards empilham sem rolagem horizontal da página.
- [ ] **Step 5: Commit** — `Front: módulos de gráfico (Recharts escondido em components/charts) e blocos 03 a 05 do Protocolo`

### Task 4: Filtros na URL e filtro cruzado

**Files:**
- Create: `apps/web/src/lib/filters.ts` (funções puras de URL)
- Create: `apps/web/src/hooks/useDashboardFilters.ts`
- Create: `apps/web/src/components/filters/PeriodPicker.tsx`, `FilterPanel.tsx`, `ActiveFilters.tsx`
- Modify: `apps/web/src/dashboards/types.ts`, `DashboardView.tsx`, `apps/web/src/components/DashboardHeader.tsx`
- Modify: `apps/web/src/dashboards/protocolo/index.ts`, `ProtocoloContent.tsx`
- Test: `apps/web/src/lib/filters.test.ts`

**Interfaces:**
- Consumes: `DashboardFilters`, `DashboardQuery` (Task 1); `RankList.onSelect` (Task 3).
- Produces:
  - `type Period = { from: string; to: string }`
  - `FILTER_PARAMS = { materia: 'materia', funcionario: 'funcionario', area_atuacao_id: 'area', uf: 'uf' } as const`
  - `parseFilters(params: URLSearchParams, today: Date): { period: Period; filters: DashboardFilters }`
  - `withPeriod(params: URLSearchParams, period: Period): URLSearchParams`
  - `withToggled(params: URLSearchParams, key: keyof DashboardFilters, value: string): URLSearchParams`
  - `withCleared(params: URLSearchParams): URLSearchParams` — mantém só o período.
  - `useDashboardFilters(): { period: Period; filters: DashboardFilters; setPeriod(p: Period): void; toggle(key: keyof DashboardFilters, value: string): void; clear(): void }`
  - `type FilterDef<T> = { key: keyof DashboardFilters; label: string; options: (data: T) => { value: string; label: string }[] }`
  - `DashboardModule<T>` + `filters?: FilterDef<T>[]`; `Content: ComponentType<{ data: T; filters: ReturnType<typeof useDashboardFilters> }>`

- [ ] **Step 1: Write the failing tests** em `filters.test.ts`:

```ts
const today = new Date(2026, 10, 9) // 09/11/2026
it('sem período usa o mês atual', () => {
    expect(parseFilters(new URLSearchParams(''), today).period).toEqual({ from: '2026-11-01', to: '2026-11-30' })
})
it('período inválido volta para o mês atual', () => {
    expect(parseFilters(new URLSearchParams('de=2026-10-31&ate=2026-10-01'), today).period.from).toBe('2026-11-01')
    expect(parseFilters(new URLSearchParams('de=abc&ate=2026-10-01'), today).period.from).toBe('2026-11-01')
})
it('lê valores repetidos', () => {
    expect(parseFilters(new URLSearchParams('materia=ANP&materia=MORA&area=3'), today).filters)
        .toEqual({ materia: ['ANP', 'MORA'], area_atuacao_id: ['3'] })
})
it('toggle liga e desliga sem mexer no resto', () => {
    const on = withToggled(new URLSearchParams('de=2026-10-01&ate=2026-10-31'), 'materia', 'ANP')
    expect(on.getAll('materia')).toEqual(['ANP'])
    expect(withToggled(on, 'materia', 'ANP').getAll('materia')).toEqual([])
    expect(on.get('de')).toBe('2026-10-01')
})
it('clear mantém só o período', () => {
    expect(withCleared(new URLSearchParams('de=2026-10-01&ate=2026-10-31&uf=AM')).toString()).toBe('de=2026-10-01&ate=2026-10-31')
})
```

- [ ] **Step 2:** `npm test` → FAIL.
- [ ] **Step 3: Implement** `lib/filters.ts`, o hook (`useSearchParams` + funções puras; `replace: false` para o voltar do navegador desfazer) e os componentes: `PeriodPicker` (botão `.btn` com ícone de calendário e "1 a 30 de out. de 2026"; painel com "Este mês", "Mês anterior", "Últimos 30 dias" e dois `<input type="date">` com `<label>`; fecha com Esc e clique fora), `FilterPanel` (botão "Filtros" com contador; painel com um grupo de checkboxes por `FilterDef`), `ActiveFilters` (etiquetas `.tag` com botão "×" `aria-label="Tirar {label}: {valor}"` e "Limpar filtros"). `DashboardView`: query inclui `from`, `to`, `filters`; deps `[module, org, unit, searchParams.toString()]`; com `loading` e dados antigos, o conteúdo recebe `style={{ opacity: 0.55 }}` e `aria-busy`. `DashboardHeader`: pílulas de unidade com `to` + `location.search`; recebe `actions?: ReactNode` à direita do título; depois do selo de atualização, "· fuso {meta.timezone}". Protocolo: `filters` com Matéria, Funcionário, Área (`{ value: String(id), label: nome }`), UF; `RankList` de matéria e de funcionário com `selected` e `onSelect` → `filters.toggle`.
- [ ] **Step 4:** `npm test` → PASS; checagens limpas; navegador: escolher matéria no painel e clicar "ANP" no Top 10 dão o mesmo resultado; F5 e voltar mantêm/desfazem; trocar de unidade mantém filtros; funcionário inexistente mostra "Não há dados" e KPIs 0.
- [ ] **Step 5: Commit** — `Front: filtros na URL (período, matéria, funcionário, área, UF), painel, etiquetas e filtro cruzado no Protocolo`

### Task 5: Exportar e comissionamento

**Files:**
- Create: `apps/web/src/lib/csv.ts`, `apps/web/src/lib/download.ts`
- Modify: `apps/web/src/data/client.ts`, `apps/web/src/data/mockClient.ts`
- Modify: `apps/web/src/dashboards/DashboardView.tsx`, `apps/web/src/dashboards/protocolo/ProtocoloContent.tsx`
- Modify: `apps/web/src/components/Icon.tsx` (ícones `download`, `file`, `calendar`, `filter`), `apps/web/src/styles/app.css` (`@media print`)
- Test: `apps/web/src/lib/csv.test.ts`

**Interfaces:**
- Consumes: `can_export`, `can_see_commission` (Task 1); `DashboardHeader.actions` (Task 4); `DataTable` (Task 2).
- Produces:
  - `toCsv(header: string[], rows: (string | number)[][]): string` — separador `;` (Excel pt-BR), CRLF, BOM `﻿` no início, campo com `;`, `"` ou quebra de linha entre aspas e `"` dobrado.
  - `downloadBlob(blob: Blob, filename: string): void`
  - `DataClient.exportDashboard(key: string, query: DashboardQuery): Promise<Blob>`
  - `DashboardModule<T>.Content: ComponentType<{ data: T; filters: ReturnType<typeof useDashboardFilters>; summary: DashboardSummary }>`

- [ ] **Step 1: Write the failing tests** em `csv.test.ts`:

```ts
it('começa com BOM e usa ; e CRLF', () => {
    expect(toCsv(['a', 'b'], [[1, 2]])).toBe('﻿a;b\r\n1;2\r\n')
})
it('escapa ; aspas e acentos', () => {
    expect(toCsv(['matéria'], [['Bancário; cartão'], ['dito "x"']])).toBe('﻿matéria\r\n"Bancário; cartão"\r\n"dito ""x"""\r\n')
})
```

- [ ] **Step 2:** `npm test` → FAIL.
- [ ] **Step 3: Implement.** Mock `exportDashboard`: espera, sessão, acesso, `can_export` (senão `DataError(403)`), gera linhas fictícias (processo, matéria, funcionário, data de protocolo, valor de causa) respeitando período e filtros, devolve `new Blob([toCsv(...)], { type: 'text/csv;charset=utf-8' })`. `DashboardView` monta `actions`: período, filtros, "Exportar" só com `summary.can_export` (nome `protocolo-lexpre_NG_2026-10-01_2026-10-31.csv`), "Gerar comissão (PDF)" só com `summary.can_see_commission` (chama `window.print()` após marcar `document.body.dataset.print = 'comissao'`, limpo no `afterprint`). `Content` recebe `summary` para o bloco 07 aparecer só com `can_see_commission` **e** o campo presente. `@media print` com `body[data-print='comissao']` esconde tudo menos a seção 07.
- [ ] **Step 4:** `npm test` → PASS; checagens limpas; navegador: Exportar baixa o CSV e ele abre no Excel com acentos; Gerar comissão abre a impressão só com a tabela; com `can_export: false` e `can_see_commission: false` no `catalog.ts` (teste manual, depois desfazer) botões e bloco 07 somem.
- [ ] **Step 5: Commit** — `Front: Exportar (CSV no mock) e comissionamento (bloco 07 e impressão), seguindo as permissões do catálogo`

### Task 6: README e verificação final

**Files:**
- Modify: `apps/web/README.md` (módulos novos, filtros na URL, permissões por dashboard, `npm test`, favoritos no `localStorage`, estado do #121)

- [ ] **Step 1:** Atualizar o README: tabela de comandos com `npm test`; seção "Gráficos" (só `components/charts/` importa Recharts); seção "Filtros" (parâmetros da URL); roteiro "Para criar um dashboard novo" com `filters` e `view.ts`; checklist do #121.
- [ ] **Step 2:** `npm test`, `npx tsc -b`, `npm run lint`, `npm run format:check`, `npm run build` — todos sem erro.
- [ ] **Step 3:** Navegador, roteiro completo dos 5 itens da Review Focus.
- [ ] **Step 4: Commit** — `Front: README do apps/web (gráficos, filtros, permissões, testes)`
