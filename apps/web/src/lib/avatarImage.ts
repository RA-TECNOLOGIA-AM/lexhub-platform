// Módulo: prepara a foto de perfil no navegador antes de enviar (área escolhida em "Ajustar foto" ou
// o quadrado do meio, 256 px, webp).
// Assim o bucket guarda arquivos pequenos e iguais, seja qual for a foto escolhida.

import { clampArea, type CropArea } from './avatarCrop.ts'

export const AVATAR_SIZE = 256
const MAX_INPUT_BYTES = 10 * 1024 * 1024 // a foto original; a enviada fica bem menor
const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
export const AVATAR_ACCEPT = ACCEPTED.join(',')

// Mensagem para a pessoa ou null se o arquivo serve.
export function avatarFileError(file: { type: string; size: number }): string | null {
    if (!ACCEPTED.includes(file.type)) return 'Use uma foto JPG, PNG ou WebP.'
    if (file.size > MAX_INPUT_BYTES) return 'A foto pode ter no máximo 10 MB.'
    return null
}

// O maior quadrado no centro da imagem (corta as sobras do lado maior).
export function squareCrop(width: number, height: number): { x: number; y: number; size: number } {
    const size = Math.min(width, height)
    return { x: Math.round((width - size) / 2), y: Math.round((height - size) / 2), size }
}

export async function toAvatarBlob(file: Blob, area?: CropArea): Promise<Blob> {
    const bitmap = await createImageBitmap(file)
    try {
        const media = { width: bitmap.width, height: bitmap.height }
        const center = squareCrop(bitmap.width, bitmap.height)
        const crop = clampArea(area ?? { x: center.x, y: center.y, width: center.size, height: center.size }, media)
        const { x, y } = crop
        const size = crop.width
        const canvas = document.createElement('canvas')
        canvas.width = AVATAR_SIZE
        canvas.height = AVATAR_SIZE
        const ctx = canvas.getContext('2d')
        if (!ctx) throw new Error('canvas')
        ctx.imageSmoothingQuality = 'high'
        ctx.drawImage(bitmap, x, y, size, size, 0, 0, AVATAR_SIZE, AVATAR_SIZE)
        return await new Promise<Blob>((resolve, reject) =>
            canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('webp'))), 'image/webp', 0.85),
        )
    } finally {
        bitmap.close()
    }
}
