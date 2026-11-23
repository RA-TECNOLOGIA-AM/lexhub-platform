# Configurações + Aparência — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Engrenagem na topbar → modal de Configurações (Perfil só leitura + foto; Aparência com
modo, 42 temas e cor de destaque), com a escolha salva na conta e aplicada antes do React.

**Architecture:** O motor de temas do LexFlow (OKLCH, `bg` + `accent` por tema) é portado para
`lib/themeEngine.ts`. `lib/appearance.ts` (puro) transforma a preferência em `data-theme` +
variáveis CSS inline sobre os tokens do LexHub; Claro/Escuro Padrão não escrevem nada.
A preferência vive em `app.profiles` (RPC `api.set_my_appearance`, lida pelo `/me`) e numa cópia
no localStorage lida pelo `index.html`. Um `AppearanceProvider` dentro do `AuthProvider` concilia
conta × cópia local e salva cada mudança.

**Tech Stack:** React 19 + Vite + TS (vitest, oxlint, prettier), FastAPI + asyncpg (pytest),
Supabase/Postgres.

**Spec:** `docs/superpowers/specs/2026-11-23-configuracoes-aparencia-design.md`
Referência de código: `C:\workspace\LexFlowNextBeta\src\design-system\theme-engine.ts`,
`theme.ts`, `src\lib\theme-document.ts`, `src\components\common\theme-picker.tsx`.

## Global Constraints

- Indentação 4 espaços; cada módulo novo abre com comentário `// Módulo: …` (padrão do repo).
- Toda cor em CSS via `var(--…)`; nenhuma cor fixa nova (exceto valores dentro dos temas em TS).
- Claro Padrão (`light-default`) e Escuro Padrão (`dark-default`) = visual atual, **nenhuma
  variável inline**.
- Status (`--ok*`, `--warn*`, `--info*`, `--danger*`), `--focus`, `--link*`, `--toast-*`,
  `--loader-*`, `--fav*` e cores de gráfico **nunca** são escritos pelo tema.
- Um destaque só para os dois modos: `'tema'` | id de preset | `#rrggbb`.
- `VITE_DATA_SOURCE=mock` precisa funcionar.
- **Commits:** o Luís faz. No fim de cada task: `git status` + sugerir a mensagem; não commitar.
- **Migration no lexhub-v2:** só aplicar com o OK explícito do Luís.
- Branch: `feat/configuracoes-aparencia` (criar a partir da `main` antes da Task 1).
- **Sem dependências novas.** O vitest roda em Node (sem jsdom/Testing Library): componentes
  se testam com `renderToStaticMarkup` (como `Freshness.test.tsx`); lógica com estado fica em
  módulos puros testáveis; interação é conferida no navegador (Task 8). `applyAppearance`
  recebe um `root` falso nos testes (`{ dataset: {}, style: { setProperty, removeProperty } }`).

## Review Focus

1. **Id de tema/destaque inválido ou removido** (no banco ou no localStorage) → cai no padrão,
   sem quebrar a tela. Teste na Task 4.
2. **localStorage bloqueado/corrompido** (aba privada, JSON quebrado) → `index.html` e
   `appearance.ts` seguem com o padrão, sem exceção. Testes nas Tasks 4 e 5.
3. **Cliques rápidos entre temas** → a última escolha é a que fica no banco. Teste na Task 5.
4. **Conta com escolha × cópia local diferente** (outro aparelho) → a conta manda ao chegar o
   `/me`; conta vazia não sobrescreve o local. Teste na Task 4 (`pickAppearance`).
5. **Trocar de tema engine → padrão** remove todas as variáveis inline (não sobra `--bg` do
   Dracula no Claro Padrão). Teste na Task 4.

---

### Task 1: Migration + RPC da aparência

**Files:**
- Create: `supabase/migrations/20261125100000_aparencia.sql`
- Create: `supabase/tests/aparencia_test.sql`

**Interfaces:**
- Produces: colunas `app.profiles.theme_mode`, `theme_light`, `theme_dark`, `theme_accent`
  (todas `text null`); `api.set_my_appearance(p_mode text, p_light text, p_dark text, p_accent text) returns void`.

- [ ] **Step 1: Escrever o teste SQL** no formato de `supabase/tests/foto_perfil_test.sql`
  (`begin` … `rollback`, `set local role authenticated` + `request.jwt.claims`). Casos:
  - grava as 4 colunas para o `auth.uid()` (upsert sem linha prévia e com linha da foto, sem
    apagar `avatar_path`);
  - `p_mode = 'sepia'` → erro de check; `p_light = 'Dracula!'` → erro; `p_accent = '#12345'` →
    erro; `p_accent = 'azul'` e `'#2563eb'` → ok;
  - todos nulos → ok (volta a "sem escolha");
  - sem login (`auth.uid()` nulo) → erro `42501`.
- [ ] **Step 2: Escrever a migration**: `alter table app.profiles add column …` com os checks da
  spec §4.7 (`theme_mode in ('light','dark')`; ids `^[a-z0-9-]{1,40}$`; accent
  `^([a-z]{1,20}|#[0-9a-f]{6})$`). Função `security definer`, `set search_path = ''`, upsert em
  `app.profiles` (mesmo padrão de `api.set_my_avatar`), `revoke … from public, anon`,
  `grant execute … to authenticated`. Comentário de cabeçalho + bloco "Desfazer".
- [ ] **Step 3: Validar localmente** se houver Supabase local (`supabase db reset` + rodar o
  teste com `psql`); sem ambiente local, revisar com o Luís e **pedir OK** para aplicar no
  lexhub-v2 (MCP `apply_migration`, depois acertar a versão no histórico — ver memória
  "Histórico de migrations"). Esperado: teste termina sem `ERROR`.
- [ ] **Step 4:** `git status`; sugerir `feat(db): aparência do usuário em app.profiles`.

### Task 2: `/me` devolve a aparência

**Files:**
- Modify: `apps/api/src/app/me.py` (`MembershipRow`, `UserOut`, montagem do `MeOut`, `_MEMBERSHIPS_SQL`, `PgMeRepo`)
- Test: `apps/api/tests/test_me.py`

**Interfaces:**
- Consumes: colunas da Task 1.
- Produces: `user.appearance = { "mode": str|None, "light": str|None, "dark": str|None, "accent": str|None }` no JSON do `/me`.

- [ ] **Step 1: Testes que falham** em `test_me.py`:
  - `test_admin_formato_completo`: o dicionário esperado ganha
    `"appearance": {"mode": None, "light": None, "dark": None, "accent": None}`;
  - novo `test_aparencia_salva`: `MembershipRow(..., appearance=AppearanceRow(mode="dark", light="light-github", dark="dark-dracula", accent="azul"))` → `user["appearance"] == {"mode": "dark", "light": "light-github", "dark": "dark-dracula", "accent": "azul"}`.
- [ ] **Step 2:** `cd apps/api; python -m pytest tests/test_me.py -q` → FAIL.
- [ ] **Step 3: Implementar**: `@dataclass(frozen=True) class AppearanceRow` (4 campos `str | None = None`), `MembershipRow.appearance: AppearanceRow = AppearanceRow()`, `class AppearanceOut(BaseModel)`, `UserOut.appearance: AppearanceOut`; SQL seleciona `p.theme_mode, p.theme_light, p.theme_dark, p.theme_accent`.
- [ ] **Step 4:** pytest de novo → PASS (toda a suíte: `python -m pytest -q`).
- [ ] **Step 5:** `git status`; sugerir `feat(api): /me devolve a aparência`.

### Task 3: Tipos e cliente (`setMyAppearance`)

**Files:**
- Modify: `apps/web/src/types/index.ts`, `services/client.ts`, `services/profileClient.ts`, `services/mockClient.ts`
- Test: `services/profileClient.test.ts`

**Interfaces:**
- Produces:
  ```ts
  export type ThemeMode = 'light' | 'dark'
  export type Appearance = { mode: ThemeMode | null; light: string | null; dark: string | null; accent: string | null }
  // User ganha: appearance: Appearance
  // DataClient ganha: setMyAppearance(appearance: Appearance): Promise<void>
  ```

- [ ] **Step 1: Teste que falha** em `profileClient.test.ts` (usar o `fakeSupabase` já usado
  ali): `setMyAppearance({ mode: 'dark', light: null, dark: 'dark-nord', accent: '#2563eb' })`
  chama a RPC `set_my_appearance` com `{ p_mode: 'dark', p_light: null, p_dark: 'dark-nord', p_accent: '#2563eb' }`.
- [ ] **Step 2:** `npm test -- profileClient` → FAIL.
- [ ] **Step 3: Implementar** no `profileClient` (via `createRpc`) e no `mockClient` (guarda em
  `localStorage['lexhub.mock.appearance']` e devolve no `getMe`, como o `AVATAR_KEY`). Onde o
  front monta `User` em testes/fixtures, incluir `appearance` com tudo `null`.
- [ ] **Step 4:** `npm test` e `npx tsc -b` → PASS.
- [ ] **Step 5:** `git status`; sugerir `feat(web): cliente da aparência`.

### Task 4: Motor de temas + `appearance.ts`

**Files:**
- Create: `apps/web/src/lib/themeEngine.ts`, `lib/themeEngine.test.ts`
- Create: `apps/web/src/lib/appearance.ts`, `lib/appearance.test.ts`
- Modify: `apps/web/src/styles/app.css` (`--chart-1`, `--pie-1`), `styles/tokens.css` (`--chart-brand`, tokens da sidebar)

**Interfaces:**
- Produces (`themeEngine.ts`), portado do LexFlow `theme-engine.ts` + `theme.ts`:
  ```ts
  export type ThemePreset = { id: string; name: string; mode: ThemeMode; hue: number; chroma: number; base: number; contrast: number; accent: string }
  export const THEME_PRESETS: ThemePreset[]          // 15 claros + 27 escuros, ids/nomes/bg/accent/contrast do LexFlow
  export const THEME_ACCENTS: readonly { id: string; name: string; hex: string | null }[] // igual ao LexFlow
  export const DEFAULT_THEME: Record<ThemeMode, string> // { light: 'light-default', dark: 'dark-default' }
  export function buildSemanticColors(p: ThemePreset): SemanticColors
  export function resolveAccentHex(accent: string | null, themeAccent: string): string
  export function contrastWithWhite(hex: string): number
  export function isValidThemeId(id: string | null | undefined, mode: ThemeMode): boolean
  export function isValidAccentId(id: string | null | undefined): boolean
  export function themePreview(id: string): { bg: string; sidebar: string; card: string; text: string; border: string; accent: string }
  ```
  `light-default`/`dark-default` ficam em `THEME_PRESETS` só com nome e `accent` (`#B35500` /
  `#F5A04A`, sem `accentForWhiteText`); `themePreview` deles usa os hex atuais do `tokens.css`
  (claro: bg `#F4F5F7`, sidebar `#11151A`, card `#FFFFFF`, text `#15181D`, border `#E3E6EB`;
  escuro: bg `#14110E`, sidebar `#0F0C0A`, card `#1C1814`, text `#F2EBE3`, border `#2F2922`).
- Produces (`appearance.ts`):
  ```ts
  export const APPEARANCE_KEY = 'lexhub.appearance'
  export const MANAGED_VARS: readonly string[] // todas as variáveis que o tema pode escrever
  export type ResolvedAppearance = { mode: ThemeMode; themeId: string; accentHex: string; vars: Record<string, string> }
  export function normalizeAppearance(a: Partial<Appearance> | null | undefined): Appearance // ids inválidos → null
  export function resolveAppearance(a: Appearance, systemDark: boolean): ResolvedAppearance
  export function pickAppearance(local: Appearance, account: Appearance): Appearance // conta com algo não nulo manda
  export function readCachedAppearance(storage?: Pick<Storage, 'getItem'> | null): Appearance // inclui fallback 'lexhub.theme'
  export function cacheAppearance(a: Appearance, storage?: Pick<Storage, 'setItem'> | null): void
  export function applyAppearance(r: ResolvedAppearance, root?: HTMLElement): void
  ```
  Cache gravado: `{ prefs: Appearance, light: Record<string,string>, dark: Record<string,string> }`
  (vars já resolvidas dos dois modos, para o `index.html` não precisar do motor).

- [ ] **Step 1: Testes que falham** — `themeEngine.test.ts`:
  - `THEME_PRESETS` tem 15 `light` e 27 `dark`, ids únicos, inclui `dark-dracula` (`bg #282a36`);
  - todo `THEME_ACCENTS` com hex tem `contrastWithWhite(hex) >= 4.5`;
  - todo preset do motor (≠ defaults): `contrastWithWhite(accent) >= 4.5`;
  - para todo preset do motor, contraste texto.primary × background.primary ≥ 4.5 (função de
    contraste local no teste);
  - `resolveAccentHex('tema', '#abcdef') === '#abcdef'`; `('azul', x) === '#2563eb'`;
    `('#E11D48', x) === '#e11d48'`; `('xyz', '#abcdef') === '#abcdef'`.
- [ ] **Step 2: Testes que falham** — `appearance.test.ts`:
  - padrão (`all null`, `systemDark=false`) → `{ mode: 'light', themeId: 'light-default', vars: {} }`;
    `systemDark=true` → `mode: 'dark'`, `vars: {}`;
  - `{ mode: 'dark', dark: 'dark-dracula' }` → `vars['--bg']` definido, nenhuma chave fora de
    `MANAGED_VARS`, nenhuma chave de status (`--ok`, `--danger`, `--focus`, `--link`);
  - `{ accent: 'azul' }` no Claro Padrão → `vars['--accent'] === '#2563eb'`,
    `vars['--on-accent'] === '#ffffff'`, e só variáveis de destaque;
  - `normalizeAppearance({ light: 'nao-existe', accent: '#12' })` → `light: null, accent: null`;
  - `applyAppearance`: aplicar Dracula e depois o padrão deixa `root.style` sem nenhuma
    `MANAGED_VARS` e `root.dataset.theme === 'light'`;
  - `readCachedAppearance` com JSON quebrado → tudo `null`; só `lexhub.theme = 'dark'` → `mode: 'dark'`;
    storage que lança → tudo `null`;
  - `pickAppearance(local, accountAllNull) === local`; `pickAppearance(local, { …, dark: 'dark-nord' })` → conta.
- [ ] **Step 3:** `npm test -- themeEngine appearance` → FAIL.
- [ ] **Step 4: Implementar `themeEngine.ts`** copiando as funções OKLCH, `buildSemanticColors`,
  `THEME_SEEDS`, `THEME_ACCENTS`, `accentForWhiteText` do LexFlow (adaptar para 4 espaços, sem
  dependência de `colorPalettes`: `border.error` não é usado). Sem lógica nova.
- [ ] **Step 5: Implementar `appearance.ts`**. Mapeamento semântico → tokens (spec §4.4):
  `--bg`=background.primary; `--surface`= surface.elevated (claro) / surface.secondary (escuro);
  `--surface-2`=background.tertiary; `--surface-3`=surface.tertiary; `--border`=border.secondary;
  `--border-strong`=border.primary; `--divider`=border.secondary; `--text`/`--text-2`/
  `--text-muted`/`--text-faint` = text.primary/secondary/tertiary/disabled; `--side-bg`=
  background.secondary; `--side-text`=text.secondary; `--side-label`=text.tertiary;
  `--side-hover`/`--side-active`=surface.tertiary/surface.elevated; `--chip`=surface.tertiary;
  `--on-chip`=text.primary; `--skel-mid`=surface.tertiary; `--card-muted`=surface.primary;
  `--border-hover`=text.disabled. Destaque (sempre que ≠ "Do tema" de um padrão): `--accent`,
  `--accent-hover` (L −0.06 em OKLCH), `--accent-soft` (`color-mix(in srgb, <accent> 14%, var(--surface))`),
  `--on-accent: #ffffff`. Ajustes visuais finos ficam para a Task 8.
- [ ] **Step 6: CSS**: em `tokens.css`, `--chart-brand: #B35500` (claro) / `#F5A04A` (escuro);
  em `app.css`, `--chart-1` e `--pie-1` passam a `var(--chart-brand)`. `hubView.ts` Favoritos →
  `var(--chart-brand)`. Revisar `RecursalContent.tsx:400` e `TicketsContent.tsx:188,375`: cor de
  dado → `var(--chart-brand)`. Cores `#fff` de texto sobre a sidebar/`.org` → `var(--on-chip)`
  ou `var(--side-text)` conforme o fundo.
- [ ] **Step 7:** `npm test` + `npx tsc -b` + `npm run lint` → PASS.
- [ ] **Step 8:** `git status`; sugerir `feat(web): motor de temas do LexFlow e aparência`.

### Task 5: Aplicar antes do React + `AppearanceProvider`

**Files:**
- Modify: `apps/web/index.html` (script do tema)
- Create: `apps/web/src/lib/appearanceSaver.ts`, `lib/appearanceSaver.test.ts`
- Create: `apps/web/src/contexts/appearance-context.ts`, `contexts/AppearanceProvider.tsx`
- Modify: `apps/web/src/App.tsx` (montar dentro do `AuthProvider`), `components/layout/ThemeToggle.tsx`
- Delete: `apps/web/src/hooks/useTheme.ts`, `lib/theme.ts`, `lib/theme.test.ts` (substituídos)

**Interfaces:**
- Consumes: Task 3 (`dataClient.setMyAppearance`, `me.user.appearance`), Task 4 (`appearance.ts`).
- Produces:
  ```ts
  export type AppearanceContextValue = {
      appearance: Appearance
      resolved: ResolvedAppearance
      setMode(mode: ThemeMode): void
      setTheme(mode: ThemeMode, id: string): void
      setAccent(accent: string): void
      saveError: string | null
  }
  export function useAppearance(): AppearanceContextValue
  // lib/appearanceSaver.ts
  export function createAppearanceSaver(
      send: (a: Appearance) => Promise<void>,
      onError: (message: string | null) => void,
  ): (a: Appearance) => Promise<void>
  ```

- [ ] **Step 1: Testes que falham** (`appearanceSaver.test.ts`, com `send` falso controlado
  por promessas):
  - três chamadas seguidas → `send` recebe a 1ª, e só depois que ela resolve recebe a 3ª
    (a 2ª, que ficou na fila, é descartada: só a mais nova espera); nunca dois envios ao mesmo tempo;
  - `send` rejeita → `onError('Não foi possível salvar na sua conta.')`; o próximo sucesso →
    `onError(null)`.
  A conciliação conta × local já está coberta pelos testes de `pickAppearance` (Task 4).
- [ ] **Step 2:** `npm test -- appearanceSaver` → FAIL.
- [ ] **Step 3: Implementar** o saver e o provider: estado inicial = `readCachedAppearance()`;
  quando `me` chega/muda, `pickAppearance(local, me.user.appearance)` (sem enviar); a cada
  mudança `applyAppearance(resolveAppearance(...))` + `cacheAppearance`; mudanças da pessoa vão
  pelo saver; segue o `prefers-color-scheme` ao vivo só quando `mode === null`.
  `ThemeToggle` usa `useAppearance().setMode(oposto)`.
- [ ] **Step 4: `index.html`**: ler `lexhub.appearance` (`JSON.parse` em `try`), escolher o modo
  (`prefs.mode` ou `matchMedia`), `dataset.theme = modo` e `style.setProperty` de cada entrada de
  `cache[modo]`; sem cache, a regra antiga de `lexhub.theme`. Sem exceção em nenhum caso.
- [ ] **Step 5:** `npm test` + `npx tsc -b` + `npm run lint` → PASS.
- [ ] **Step 6:** `git status`; sugerir `feat(web): aparência salva na conta e aplicada antes do React`.

### Task 6: Modal de Configurações + Perfil

**Files:**
- Create: `apps/web/src/components/settings/SettingsButton.tsx`, `SettingsDialog.tsx`, `ProfileSection.tsx`, `settings.css`
- Modify: `components/layout/AppLayout.tsx` (botão entre `ThemeToggle` e `ProfileMenu`), `components/ui/Icon.tsx` (`settings`, `camera`, `palette`, `user`, `check`, `plus` — só os que faltam)
- Test: `components/settings/SettingsDialog.test.tsx`

**Interfaces:**
- Consumes: `useAuth()` (`me.user`, `setAvatarPath`), `dataClient.getSessionEmail`, `uploadMyAvatar`, `removeMyAvatar`, `avatarImage.ts`.
- Produces: `<SettingsDialog initialSection?: 'perfil' | 'aparencia' onClose={() => void} />`;
  seções registradas num array `{ id, label, icon, group: 'Minha conta', render }` (Aparência
  entra na Task 7).

- [ ] **Step 1: Testes que falham** (`renderToStaticMarkup` do `SettingsDialog` com um `user`
  de exemplo, `initialSection='perfil'`): título "Meu Perfil"; menu com "Perfil" e "Minha conta",
  sem "Notificações", "Dispositivos", "Companhias"; o Perfil mostra nome, Cargo, Setor,
  Escritório e nenhum botão "Editar". (Abrir pela engrenagem e Esc fechar → Task 8.)
- [ ] **Step 2:** `npm test -- SettingsDialog` → FAIL.
- [ ] **Step 3: Implementar**: `<dialog>` com a mecânica do `ui/Modal.tsx` (`showModal` no
  `useLayoutEffect`, `onCancel`), layout de duas colunas (menu 226px | conteúdo), cabeçalho com
  título da seção + X; < 768px tela cheia com o menu em abas no topo. `ProfileSection` extrai a
  lógica de troca/remoção de foto do `ProfileMenu` para um hook `useAvatarUpload()` em
  `hooks/useAvatarUpload.ts`, usado pelos dois.
- [ ] **Step 4:** `npm test` + `npx tsc -b` + `npm run lint` → PASS.
- [ ] **Step 5:** `git status`; sugerir `feat(web): modal de configurações com perfil`.

### Task 7: Seção Aparência

**Files:**
- Create: `apps/web/src/components/settings/AppearanceSection.tsx`, `ThemeCard.tsx`, `AccentPicker.tsx`
- Modify: `SettingsDialog.tsx` (registrar a seção), `settings.css`
- Test: `components/settings/AppearanceSection.test.tsx`

**Interfaces:**
- Consumes: `useAppearance()` (Task 5), `THEME_PRESETS`, `THEME_ACCENTS`, `themePreview`, `resolveAccentHex`, `contrastWithWhite` (Task 4).

- [ ] **Step 1: Testes que falham** (`renderToStaticMarkup` da seção com um
  `AppearanceContextValue` fixo passado por prop ou provider de teste):
  - mostra "Modo", "Cor de destaque", "Tema claro" (15 cartões), "Tema escuro" (27 cartões);
  - com `dark: 'dark-dracula'`, o cartão "Dracula" tem `aria-pressed="true"` e os outros escuros não;
  - com `accent: null` no Claro Padrão a faixa mostra "Do tema" e `#B35500`; com `'azul'`,
    "Azul" e `#2563eb`;
  - `accent: '#ffff00'` mostra "Texto pode ficar difícil de ler nos botões"; `'#2563eb'` não.
  (Cliques chamando `setMode`/`setTheme`/`setAccent` → conferidos na Task 8.)
- [ ] **Step 2:** `npm test -- AppearanceSection` → FAIL.
- [ ] **Step 3: Implementar** no layout das referências: cartões de modo (miniatura + ícone
  sol/lua + check), grade de bolinhas (Do tema = meia/meia, `+` abre `<input type="color">`),
  faixa nome + hex, galerias em grade de 4 colunas (2 no celular). `ThemeCard` desenha a
  miniatura só com `themePreview(id)` + destaque resolvido (inline style, sem depender das
  variáveis da página). `saveError` aparece como aviso discreto no topo da seção.
- [ ] **Step 4:** `npm test` + `npx tsc -b` + `npm run lint` + `npm run format:check` → PASS.
- [ ] **Step 5:** `git status`; sugerir `feat(web): seção aparência com temas e destaque`.

### Task 8: Verificação no navegador

- [ ] **Step 1:** subir o front em modo mock (`preview_start`) e abrir Configurações → Aparência.
- [ ] **Step 2:** percorrer os temas: Claro Padrão e Escuro Padrão idênticos ao visual de antes
  (comparar screenshot com a `main`); 4–5 temas por modo (GitHub Light, Solarized Light,
  Dracula, Nord, Shades of Purple, Alto Contraste) num dashboard com gráfico: texto legível,
  barra lateral legível, gráficos com as cores da marca, status inalterados. Ajustar o
  mapeamento da Task 4 Step 5 se algo ficar feio (e o teste correspondente).
- [ ] **Step 3:** recarregar com um tema do motor → sem piscar claro; console sem erros.
- [ ] **Step 3b:** interações: engrenagem abre, Esc e X fecham e devolvem o foco; clicar
  Escuro/Dracula/Azul aplica na hora; sol/lua da topbar troca o modo e o modal acompanha;
  clicar 5 temas seguidos e recarregar → fica o último.
- [ ] **Step 4:** celular (375px): modal em tela cheia, abas no topo, galeria em 2 colunas.
- [ ] **Step 5:** em modo api (com a migration aplicada, após OK do Luís): trocar o tema,
  abrir em outra aba anônima/aparelho → mesmo tema.
- [ ] **Step 6:** `npm test`, `npm run build`, `python -m pytest -q` → tudo verde; `git status`
  e mensagem final sugerida ao Luís.
