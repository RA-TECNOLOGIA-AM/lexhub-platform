# Configurações + Aparência — design

Data: 23/11/2026 · Branch sugerida: `feat/configuracoes-aparencia` · Status: **para revisão do Luís**

## 1. Intenção

Dar a cada pessoa a opção de **personalizar o LexHub**, no mesmo modelo do LexFlow: um botão de
engrenagem na topbar abre um modal de **Configurações** com menu lateral. Esta entrega traz o
modal e a seção **Aparência** completa (modo claro/escuro, galeria de temas por modo e cor de
destaque). O **Perfil** entra só com o que já existe hoje. A escolha fica **salva na conta** e
acompanha a pessoa em qualquer aparelho.

Referências:
- Telas de Configurações do LexFlow enviadas pelo Luís em 23/11 (Perfil, Aparência).
- Código do LexFlow (`C:\workspace\LexFlowNextBeta`): `src/design-system/theme-engine.ts`
  (motor OKLCH + temas + destaques), `src/design-system/theme.ts`, `src/lib/theme-document.ts`
  (aplicar no `<html>`, localStorage), `src/contexts/theme-context.tsx`,
  `src/components/common/theme-picker.tsx` (galeria e destaque).

## 2. Metas, não-metas, anti-metas

**Metas**
- Engrenagem na topbar → modal de Configurações (menu à esquerda, conteúdo à direita, X para fechar).
- Aparência igual à do LexFlow: Modo (Claro/Escuro), Cor de destaque ("Do tema" + 14 cores fixas
  + cor livre), galerias "Tema claro" e "Tema escuro" com miniaturas.
- Escolha salva na conta (`app.profiles`); localStorage como cópia para aplicar antes do React.
- Perfil (leitura + foto): avatar com troca de foto, nome, e-mail, cargo/setor/escritório.

**Não-metas (próximas entregas, uma de cada vez)**
- Editar nome, e-mail ou senha; verificação em duas etapas (MFA).
- Dispositivos (sessões ativas) e Companhias (organizações).
- Notificações no modal (fica de fora de vez, pedido do Luís).

**Anti-metas**
- Um tema deixar os dashboards ilegíveis (status ok/aviso/erro, foco, gráficos).
- A tela piscar com o tema errado ao abrir ou ao logar.
- Regressão no visual atual de quem não mexer em nada.

## 3. Abordagens consideradas

1. **Cada tema com todos os ~40 tokens no CSS.** Controle total, mas 30+ × 40 valores à mão.
   Descartada.
2. **Cada tema com ~8 cores-base em TS e o resto calculado.** Escala bem; risco de contraste nas
   cores de status e gráficos. Descartada.
3. **Híbrido — escolhida pelo Luís (23/11).** Status, foco, link, toast, loader e gráficos
   continuam vindo do **modo base** (claro/escuro atual, já testado). Cada tema troca só a **parte
   neutra** (fundos, superfícies, bordas, texto, barra lateral) e o **destaque**.

Depois de escolhida a 3, o Luís pediu o design-system do LexFlow como referência. Ele já faz
exatamente a 3: cada tema nasce de **duas cores** (`bg` e `accent`) e o motor calcula todas as
cores neutras em **OKLCH**, com limites de luminosidade e contraste. Então o "como derivar" deixa
de ser `color-mix()` e passa a ser **o motor do LexFlow portado**.

## 4. Decisões

### 4.1 Topbar e modal
- Engrenagem (ícone `settings`) na topbar, entre o sol/lua e o avatar. O sol/lua **continua**
  como atalho do modo (chamada do Claude).
- Modal largo (~1140 × 830 no desktop) com menu lateral "CONFIGURAÇÕES" → **Minha conta**:
  Perfil, Aparência. **Organização**/Dispositivos/Companhias **não aparecem** até existirem
  (chamada do Claude: nada de "em breve").
- Usa o `<dialog>` do `ui/Modal.tsx` ou um `SettingsDialog` com a mesma mecânica (builder decide).
- Abre em Perfil; seção em estado local (não na URL). Parâmetro opcional para abrir em Aparência.
- Celular (< 768px): tela cheia; o menu vira abas no topo.
- Mudanças aplicam na hora (sem Salvar), como no LexFlow.

### 4.2 Perfil (só leitura + foto)
- Cartão com avatar grande (câmera troca a foto; "Remover" se houver foto), nome e e-mail.
- Linhas de leitura: Nome de exibição, E-mail, Cargo, Setor, Escritório (sem "Editar").
- Reaproveita `avatarImage.ts` / `profileClient.ts` / `setAvatarPath`. Popover do avatar continua.

### 4.3 Motor de temas (`lib/themeEngine.ts`, portado do LexFlow)
Copiar e adaptar de `theme-engine.ts` (4 espaços, comentários do padrão do repo, testes):
- `oklchToHex`, `hexToOklch`, `accentForWhiteText`, `contrastWithWhite`, `buildSemanticColors`.
- `THEME_SEEDS` com **os mesmos ids, nomes, `bg`, `accent` e `contrast` do LexFlow**
  (15 claros, 27 escuros — inclui Noctis Lux, Everforest, Alto Contraste, SynthWave 84,
  Gruvbox Dark, Meia-noite, que não apareciam nos prints).
- `THEME_ACCENTS` igual ao LexFlow: Do tema, Índigo, Azul, Ciano, Petróleo, Verde, Oliva, Cobre,
  Laranja, Vermelho, Rosa, Magenta, Violeta, Ardósia, Grafite (todas passam 4.5:1 com branco) +
  cor livre em hex.
- **Exceção LexHub:** `light-default` ("Claro Padrão") e `dark-default` ("Escuro Padrão") **não
  passam pelo motor**: são o claro atual e o Carvão quente do `tokens.css`, com o laranja/âmbar
  da marca como destaque "Do tema". Escolher um deles = nenhuma variável inline (zero regressão).
  Os outros 40 temas usam o motor.

### 4.4 Ligação motor → tokens do LexHub (`lib/appearance.ts`)
`buildSemanticColors` devolve os nomes do LexFlow; o LexHub mapeia para os seus tokens:

| LexFlow (semântico) | LexHub (`tokens.css`) |
|---|---|
| background.primary | `--bg` |
| surface.secondary (escuro) / surface.elevated (claro) | `--surface` |
| background.tertiary / surface.tertiary | `--surface-2`, `--surface-3` |
| border.secondary / border.primary | `--border`, `--border-strong`, `--divider` |
| text.primary / secondary / tertiary / disabled | `--text`, `--text-2`, `--text-muted`, `--text-faint` |
| background.secondary (moldura) | `--side-bg` (+ `--side-hover`/`--side-active` 1–2 passos acima) |
| text.secondary / tertiary sobre a moldura | `--side-text`, `--side-label` |

Os detalhes finos (qual passo vira `--border-hover`, `--chip`, `--skel-mid`, `--card-muted`) ficam
com o builder, validando visualmente nos dois modos. A barra lateral hoje é sempre escura no claro
— nos temas claros do motor ela fica clara como no LexFlow; os `#fff` fixos da sidebar em
`tokens.css`/`app.css` viram tokens (`--side-*`).

- `<html data-theme="light|dark">` continua escolhendo o **modo base**; o tema escreve as variáveis
  acima em `document.documentElement.style`. Status/foco/link/toast/loader **não** são tocados.
- Função pura `resolveAppearance(prefs, systemDark) → { mode, vars }` (testada); `applyAppearance`
  só escreve no DOM e remove as variáveis que não valem mais.

### 4.5 Cor de destaque (como no LexFlow)
- Uma escolha só para os dois modos: `'tema'` | id de preset | `#rrggbb` livre.
  `resolveAccentHex` do LexFlow decide o hex. **O mesmo hex vale no claro e no escuro** — os
  presets já passam 4.5:1 com texto branco e o destaque de cada tema passa por
  `accentForWhiteText`.
- Aplicação: `--accent` = hex; `--accent-hover` e `--accent-soft` derivados (OKLCH ou
  `color-mix`); `--on-accent` = branco sempre que o destaque não for o "Do tema" dos dois padrões
  (estes mantêm o `--on-accent` atual).
- Cor livre com contraste < 4.5:1 com branco: aviso discreto abaixo da faixa ("Texto pode ficar
  difícil de ler nos botões"), como o `contrastWithWhite` do LexFlow permite. Não bloqueia.
- Faixa abaixo das bolinhas: nome + hex do destaque ativo (em "Do tema", o hex do tema atual).
- Miniaturas da galeria: cores do próprio tema + destaque resolvido (fixo = todas iguais;
  "Do tema" = cada uma a sua), usando o `preview` do `theme.ts` do LexFlow.

### 4.6 Gráficos
- **Gráficos não seguem o tema nem o destaque.** Hoje `--chart-1: var(--accent)` (`app.css:2451`);
  passa a apontar para um token fixo da marca por modo (`--chart-brand`: `#B35500` claro,
  `#F5A04A` escuro). Assim uma série nunca colide com `--chart-3` (azul) etc.
- Favoritos/`--fav` também ficam fixos. Outros usos de `var(--accent)` em gráficos/dashboards o
  builder revisa (grep) e decide caso a caso: se é "marca do dado", vira `--chart-brand`;
  se é "UI selecionada", segue o destaque.

### 4.7 Onde fica salvo
- **Migration** `2026112x_aparencia.sql` — colunas em `app.profiles`, todas nulas = sem escolha:
  - `theme_mode text check (theme_mode in ('light','dark'))` — nulo = segue o sistema
  - `theme_light text check (theme_light ~ '^[a-z0-9-]{1,40}$')`
  - `theme_dark text check (theme_dark ~ '^[a-z0-9-]{1,40}$')`
  - `theme_accent text check (theme_accent ~ '^([a-z]{1,20}|#[0-9a-f]{6})$')`
  Id desconhecido no front cai no padrão (como o `LEGACY_THEME_MAP` do LexFlow).
- **RPC** `api.set_my_appearance(p_mode, p_light, p_dark, p_accent)` — security definer, upsert na
  linha do `auth.uid()` (padrão de `api.set_my_avatar`), grava as 4 de uma vez.
  Teste `supabase/tests/aparencia_test.sql` (rollback). Aplicar no lexhub-v2 só com o OK do Luís.
- **/me** (`me.py`): devolve `appearance: { mode, light, dark, accent }` (já faz
  `left join app.profiles`). Atualizar `test_me.py` e o tipo `User`.
- **Cliente**: `dataClient.setMyAppearance(...)` no Supabase (profileClient) e no mock.
- **Cópia local** `localStorage['lexhub.appearance']`: preferência + variáveis já resolvidas.
  O script do `index.html` lê essa chave (fallback na antiga `lexhub.theme`) e aplica
  `data-theme` + variáveis antes do React.

### 4.8 Sincronização
- Ao chegar o `/me`: conta com alguma escolha → **a conta manda** (sobrescreve local e reaplica).
  Conta vazia → vale o local (inclui `lexhub.theme` antigo), e **não** é enviado sozinho.
- Cada mudança (modal ou sol/lua): aplica na hora, grava local, chama a RPC (a última escolha
  vence se a pessoa clicar rápido). Falhou: mantém na tela e avisa "Não foi possível salvar na
  sua conta".
- Escolher Claro ou Escuro fixa o modo; não há opção "Sistema" na tela (igual ao LexFlow).
- Sair da conta não limpa a cópia local. O login (`.auth`) continua com o laranja da marca.
- `useTheme` vira `useAppearance`; `ThemeToggle` só alterna o modo.

## 5. Restrições
- Toda cor nova em CSS via `var(--…)`; nada de cor fixa (regra do modo noturno).
- Indentação 4 espaços; comentário de responsabilidade em cada módulo.
- Luís faz commits; nada de commit/push pelo Claude.
- `VITE_DATA_SOURCE=mock` funciona (aparência em memória).

## 6. Fica para o builder
- Ícones novos (`settings`, `camera`, `palette`, `user`) no `ui/Icon.tsx`.
- Passos finos do mapeamento motor → tokens secundários (§4.4) e conferência visual por tema.
- `Modal.tsx` reaproveitado ou `SettingsDialog` próprio.
- Revisão dos usos de `var(--accent)` em gráficos (§4.6).
