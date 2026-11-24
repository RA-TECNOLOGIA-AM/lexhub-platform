import { describe, expect, it } from 'vitest'
import {
    clampArea,
    clampZoom,
    computeMediaSize,
    cropDiameter,
    getCropArea,
    restrictPosition,
    zoomAtPoint,
} from './avatarCrop.ts'

const container = { width: 500, height: 360 }
const media = { width: 400, height: 200 }
const crop = 280

describe('avatarCrop (mesmo cálculo do LexFlow)', () => {
    it('zoom 1: a foto cobre o círculo pelo lado menor', () => {
        expect(computeMediaSize(media, crop, 1)).toEqual({ width: 560, height: 280 })
    })

    it('sem arrastar: recorta o quadrado do meio', () => {
        expect(getCropArea(media, container, crop, 1, { x: 0, y: 0 })).toEqual({
            x: 100,
            y: 0,
            width: 200,
            height: 200,
        })
    })

    it('arrastar além da borda fica preso (nunca sobra vazio no círculo)', () => {
        const size = computeMediaSize(media, crop, 1)
        const pos = restrictPosition({ x: 1000, y: -500 }, size, container, crop)
        const area = getCropArea(media, container, crop, 1, pos)
        expect(area.x).toBeCloseTo(0)
        expect(area.y).toBeCloseTo(0)
    })

    it('zoom no centro não move a foto; zoom fica entre 1 e 4', () => {
        expect(zoomAtPoint(1, 2, { x: 0, y: 0 }, container, crop, media, { x: 250, y: 180 })).toEqual({ x: 0, y: 0 })
        expect(clampZoom(9)).toBe(4)
        expect(clampZoom(0.2)).toBe(1)
        expect(clampZoom(1.234)).toBe(1.23)
    })

    it('diâmetro do círculo: 78% do menor lado, entre 200 e 300', () => {
        expect(cropDiameter({ width: 600, height: 360 })).toBe(281)
        expect(cropDiameter({ width: 200, height: 200 })).toBe(200)
        expect(cropDiameter({ width: 1000, height: 1000 })).toBe(300)
        expect(cropDiameter({ width: 0, height: 0 })).toBe(300)
    })

    it('foto muito alta e estreita: recorte quadrado dentro da imagem', () => {
        const tall = { width: 100, height: 2000 }
        const area = getCropArea(tall, container, crop, 1, { x: 0, y: 0 })
        expect(area.width).toBeCloseTo(100)
        expect(area.height).toBeCloseTo(100)
        expect(area.x).toBeCloseTo(0)
        expect(area.y).toBeCloseTo(950)
    })

    it('clampArea: área que passa da borda volta para dentro da imagem', () => {
        expect(clampArea({ x: -3.2, y: 190.7, width: 200.4, height: 200.4 }, media)).toEqual({
            x: 0,
            y: 0,
            width: 200,
            height: 200,
        })
    })
})
