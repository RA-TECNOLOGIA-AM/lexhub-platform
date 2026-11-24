// Módulo: o cálculo do "Ajustar foto do perfil" (sem React, testado em avatarCrop.test.ts).
// Mesmo cálculo do LexFlow (LexFlowNextBeta/src/utils/crop-image.ts + avatar-crop-modal.tsx):
// a foto é desenhada no centro da área, coberta pelo círculo no zoom 1; `pos` é o deslocamento do arrasto
// (px de tela). Daqui saem o tamanho desenhado, os limites do arrasto e a área recortada na foto original.

export type Size = { width: number; height: number }
export type Point = { x: number; y: number }
export type CropArea = { x: number; y: number; width: number; height: number } // em px da foto original

export const MIN_ZOOM = 1
export const MAX_ZOOM = 4
export const ZOOM_BUTTON_STEP = 0.1
export const ZOOM_WHEEL_STEP = 0.06

// Diâmetro do círculo: 78% do menor lado da área, entre 200 e 300 px (área ainda sem medida = 300).
export function cropDiameter(container: Size): number {
    if (!container.width || !container.height) return 300
    const base = Math.min(container.width, container.height)
    return Math.round(Math.min(Math.max(base * 0.78, 200), 300))
}

export function clampZoom(zoom: number): number {
    return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number(zoom.toFixed(2))))
}

// Tamanho da foto na tela: no zoom 1, o lado menor ocupa exatamente o círculo.
export function computeMediaSize(media: Size, crop: number, zoom: number): Size {
    const scale = Math.max(crop / media.width, crop / media.height) * zoom
    return { width: media.width * scale, height: media.height * scale }
}

// Arrasto limitado: a foto nunca deixa vazio dentro do círculo.
export function restrictPosition(pos: Point, mediaSize: Size, container: Size, crop: number): Point {
    const cropLeft = (container.width - crop) / 2
    const cropTop = (container.height - crop) / 2
    const mediaLeft = (container.width - mediaSize.width) / 2 + pos.x
    const mediaTop = (container.height - mediaSize.height) / 2 + pos.y
    let { x, y } = pos
    if (mediaLeft > cropLeft) x -= mediaLeft - cropLeft
    if (mediaTop > cropTop) y -= mediaTop - cropTop
    if (mediaLeft + mediaSize.width < cropLeft + crop) x += cropLeft + crop - (mediaLeft + mediaSize.width)
    if (mediaTop + mediaSize.height < cropTop + crop) y += cropTop + crop - (mediaTop + mediaSize.height)
    return { x, y }
}

// O pedaço da foto original que está dentro do círculo.
export function getCropArea(media: Size, container: Size, crop: number, zoom: number, pos: Point): CropArea {
    const size = computeMediaSize(media, crop, zoom)
    const mediaLeft = (container.width - size.width) / 2 + pos.x
    const mediaTop = (container.height - size.height) / 2 + pos.y
    const cropLeft = (container.width - crop) / 2
    const cropTop = (container.height - crop) / 2
    const scale = media.width / size.width
    return {
        x: (cropLeft - mediaLeft) * scale,
        y: (cropTop - mediaTop) * scale,
        width: crop * scale,
        height: crop * scale,
    }
}

// Zoom mantendo parado o ponto sob o cursor (rolagem) ou o centro (botões e slider).
export function zoomAtPoint(
    oldZoom: number,
    newZoom: number,
    pos: Point,
    container: Size,
    crop: number,
    media: Size,
    pointer: Point,
): Point {
    const oldSize = computeMediaSize(media, crop, oldZoom)
    const newSize = computeMediaSize(media, crop, newZoom)
    const centerX = container.width / 2
    const centerY = container.height / 2
    const ratioX = (pointer.x - (centerX - oldSize.width / 2 + pos.x)) / oldSize.width
    const ratioY = (pointer.y - (centerY - oldSize.height / 2 + pos.y)) / oldSize.height
    const left = pointer.x - ratioX * newSize.width
    const top = pointer.y - ratioY * newSize.height
    return restrictPosition(
        { x: left - (centerX - newSize.width / 2), y: top - (centerY - newSize.height / 2) },
        newSize,
        container,
        crop,
    )
}

// Área em px inteiros, quadrada e dentro da foto (arredondamentos não podem passar da borda).
export function clampArea(area: CropArea, media: Size): CropArea {
    const size = Math.max(1, Math.min(Math.round(area.width), media.width, media.height))
    const x = Math.min(Math.max(Math.round(area.x), 0), media.width - size)
    const y = Math.min(Math.max(Math.round(area.y), 0), media.height - size)
    return { x, y, width: size, height: size }
}
