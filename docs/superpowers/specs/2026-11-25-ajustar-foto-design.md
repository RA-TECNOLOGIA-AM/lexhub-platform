# Ajustar foto do perfil — design curto

Data: 25/11/2026 · Branch: `feat/ajustar-foto` · Status: **aprovado pelo Luís**

## Intenção
Ao trocar a foto (Configurações → Perfil ou popover do avatar), a pessoa ajusta o enquadramento antes de
salvar: arrastar para mover e zoom. Copiado do LexFlow, que o Luís acha bonito
(`LexFlowNextBeta/src/components/common/avatar-crop-modal.tsx` + `src/utils/crop-image.ts`).

## Metas / não-metas
- Meta: modal "Ajustar foto do perfil" igual ao do LexFlow (cabeçalho com ✕, título, "Arraste para mover ·
  Scroll para zoom", "Trocar"; área com máscara escura e círculo branco; barra de zoom com ícone, −, slider
  com %, +; "Cancelar" e "Salvar foto").
- Comportamento igual: arrastar (mouse e toque), zoom pela rolagem no ponto do cursor, zoom 1×–4×, a foto
  nunca deixa vazio dentro do círculo.
- Não-metas: reajustar a foto já salva (é um recorte de 256 px), editar nome, Dispositivos.

## Abordagens
1. **Copiar o modal do LexFlow, adaptado (escolhida).** Sem biblioteca; cálculo puro e testável.
2. Biblioteca de recorte (react-easy-crop etc.): dependência nova para algo que o LexFlow já resolveu.
3. Recorte só com zoom pelo slider, sem arrastar: não atende ao pedido.

## Decisões
- `lib/avatarCrop.ts`: `computeMediaSize`, `restrictCropPosition`, `getCropArea`, `zoomAtPoint`,
  `cropDiameter` — portados do LexFlow, com testes.
- `lib/avatarImage.ts`: `toAvatarBlob(file, crop?)` recebe a área escolhida (sem ela, o quadrado do meio,
  como hoje); saída continua **256 px webp** (bucket `avatars`). Decisão do Claude.
- `components/settings/AvatarCropDialog.tsx` + estilos em `settings.css`: `<dialog>` do navegador (abre por
  cima de Configurações), cores por `var(--…)` (segue o tema). Esc/✕/Cancelar fecham sem salvar.
- `hooks/useAvatarUpload.ts`: escolher arquivo → valida → abre o modal; "Trocar" abre o seletor de novo;
  "Salvar foto" corta, envia e fecha; erro aparece no modal. Vale no Perfil e no popover.
- Teclado (acréscimo do Claude): setas movem 10 px; +/− dão zoom.
