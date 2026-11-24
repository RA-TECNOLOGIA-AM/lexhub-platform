# Ajustar foto do perfil — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Modal "Ajustar foto do perfil" (copiado do LexFlow) entre escolher o arquivo e enviar a foto.
**Architecture:** Cálculo do recorte puro em `lib/avatarCrop.ts`; `toAvatarBlob` recebe a área; modal `<dialog>` em `components/settings/AvatarCropDialog.tsx`; `useAvatarUpload` abre o modal.
**Tech Stack:** React 19 + Vite + TS, vitest (Node, sem DOM).
**Spec:** `docs/superpowers/specs/2026-11-25-ajustar-foto-design.md`

## Global Constraints
- Sem dependências novas; 4 espaços; `// Módulo:` no topo; só `var(--…)` no CSS.
- Saída 256 px webp. Zoom 1–4; passo dos botões 0.1; passo da rolagem 0.06; diâmetro do círculo = min(max(78% do menor lado, 200), 300).
- Textos: "Ajustar foto do perfil", "Arraste para mover · Scroll para zoom", "Trocar", "Cancelar", "Salvar foto", "Salvando…".
- Luís commita.

## Review Focus
1. Foto muito estreita/alta (ex.: 100×2000) → círculo sempre coberto, recorte dentro da imagem (teste Task 1).
2. Zoom no limite (zoom > 4 ou < 1 pela rolagem) → preso em 1–4 (teste Task 1).
3. Arrastar além da borda → posição limitada, sem vazio (teste Task 1).
4. Recorte com valores fracionários/fora → `toAvatarBlob` limita à imagem (teste Task 1, `clampArea`).
5. Fechar no meio do envio → botões desligados enquanto salva (conferir no navegador, Task 3).

### Task 1: Cálculo do recorte
- Create `apps/web/src/lib/avatarCrop.ts`, `avatarCrop.test.ts`; Modify `lib/avatarImage.ts`.
- Produces: `type Size = { width; height }`, `type Point = { x; y }`, `type CropArea = { x; y; width; height }`;
  `cropDiameter(container: Size): number`; `computeMediaSize(media: Size, crop: number, zoom: number): Size`;
  `restrictPosition(pos: Point, mediaSize: Size, container: Size, crop: number): Point`;
  `getCropArea(media: Size, container: Size, crop: number, zoom: number, pos: Point): CropArea`;
  `zoomAtPoint(oldZoom, newZoom, pos, container, crop, media, pointer: Point): Point`; `clampZoom(z): number`;
  `clampArea(area: CropArea, media: Size): CropArea`; `toAvatarBlob(file: Blob, area?: CropArea): Promise<Blob>`.
- Tests: zoom 1 com foto 400×200 num container 500×360 e círculo 280 → mídia 560×280 e área centrada `{x:100,y:0,width:200,height:200}`; arrastar +1000 em x é limitado (área.x = 0); zoomAtPoint no centro não move; clampZoom(9)=4, clampZoom(0.2)=1; cropDiameter({600,360})=280, ({200,200})=200, ({1000,1000})=300; foto 100×2000 → área quadrada dentro da imagem; clampArea corta área que passa da borda.

### Task 2: Modal
- Create `components/settings/AvatarCropDialog.tsx` (+ estilos em `settings.css`), teste `AvatarCropDialog.test.tsx` (renderToStaticMarkup: título, subtítulo, Trocar, Cancelar, Salvar foto, slider `aria-label="Zoom"`, 0%).
- Props: `{ src: string; busy: boolean; error: string | null; onCancel(): void; onChange(): void; onSave(area: CropArea): void }`.

### Task 3: Ligar no upload
- Modify `hooks/useAvatarUpload.ts`: estado `pending: { file: File; url: string } | null`; `onChange` valida e abre (URL.createObjectURL); `save(area)` → `toAvatarBlob(file, area)` → upload → fecha e revoga a URL; `cancel()`; `choose()` serve para "Trocar". Expor `crop` para quem usa renderizar `<AvatarCropDialog>`.
- Modify `ProfileSection.tsx` e `layout/ProfileMenu.tsx` para renderizar o modal.
- Verificar: testes, tsc, lint, prettier; navegador (mock): escolher foto, arrastar, zoom, salvar, Trocar, Cancelar, tema escuro e celular.
