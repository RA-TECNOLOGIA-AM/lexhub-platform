import { describe, expect, it } from 'vitest'
import {
    ajustarKM,
    amostrarGrade,
    medianaDireta,
    medianaKM,
    sobrevivenciaEm,
    testeLogRank,
    type Observacao,
} from './kaplanMeier.ts'

const obs = (xs: [number, 0 | 1][]): Observacao[] => xs.map(([duracao, evento]) => ({ duracao, evento }))

describe('Kaplan-Meier', () => {
    // 5 processos, um censurado no dia 3: S = 0,8 · 0,6 · (censura) · 0,3 · 0 (conta à mão)
    const curva = ajustarKM(
        obs([
            [1, 1],
            [2, 1],
            [3, 0],
            [4, 1],
            [5, 1],
        ]),
    )
    it('produto-limite com censura', () => {
        expect(curva.n).toBe(5)
        expect(sobrevivenciaEm(curva, 0)).toBe(1)
        expect(sobrevivenciaEm(curva, 1)).toBeCloseTo(0.8)
        expect(sobrevivenciaEm(curva, 2.5)).toBeCloseTo(0.6)
        expect(sobrevivenciaEm(curva, 3)).toBeCloseTo(0.6)
        expect(sobrevivenciaEm(curva, 4)).toBeCloseTo(0.3)
        expect(sobrevivenciaEm(curva, 99)).toBeCloseTo(0)
        expect(amostrarGrade(curva, [0, 2, 4])).toEqual([1, expect.closeTo(0.6), expect.closeTo(0.3)])
    })
    it('mediana: primeiro dia com S(t) <= 0,5; sem chegar lá, null', () => {
        expect(medianaKM(curva)).toBe(4)
        expect(
            medianaDireta(
                obs([
                    [1, 1],
                    [2, 0],
                    [3, 0],
                ]),
            ),
        ).toBeNull()
        expect(medianaKM(ajustarKM([]))).toBeNull()
    })
})

describe('log-rank', () => {
    it('dois grupos separados: o mesmo qui-quadrado de survdiff / lifelines (5,05; p ≈ 0,025)', () => {
        const r = testeLogRank([
            obs([
                [1, 1],
                [2, 1],
                [3, 1],
            ]),
            obs([
                [4, 1],
                [5, 1],
                [6, 1],
            ]),
        ])!
        expect(r.df).toBe(1)
        expect(r.chi2).toBeCloseTo(5.0517, 3)
        expect(r.pValor).toBeCloseTo(0.0246, 3)
        expect(r.observadoPorGrupo).toEqual([3, 3])
    })
    it('grupos iguais: sem diferença (p = 1)', () => {
        const g = obs([
            [1, 1],
            [2, 1],
            [3, 0],
        ])
        const r = testeLogRank([g, g])!
        expect(r.chi2).toBeCloseTo(0)
        expect(r.pValor).toBeCloseTo(1)
    })
})
