import { describe, expect, it } from 'vitest'
import { atingimentoPorMeta, compacto, proximaZona, regua, SUPER_VISUAL, zonaDe, type Metas } from './metaAnual.ts'

// As metas anuais da NG na v1 (financeiro_NG.py: META_VALORES_TOTAIS).
const ANO: Metas = { TRISTE: 3_502_020.14, BASE: 4_400_000, AVANCADA: 6_000_000, SUPER: 6_900_000 }

describe('zonas', () => {
    it('a maior meta atingida; abaixo da Triste é Entrada', () => {
        expect(zonaDe(4_907_308.22, ANO)).toBe('BASE')
        expect(zonaDe(1_000, ANO)).toBe('ENTRADA')
        expect(zonaDe(6_900_000, ANO)).toBe('SUPER')
    })

    it('a próxima zona e quanto falta (como na tela: faltam R$ 1,09 mi para a Avançada)', () => {
        const p = proximaZona(4_907_308.22, ANO)
        expect(p.zona).toBe('AVANCADA')
        expect(p.falta).toBeCloseTo(1_092_691.78, 2)
        expect(proximaZona(7_000_000, ANO)).toEqual({ zona: null, falta: 0 })
    })
})

describe('régua', () => {
    it('faixas proporcionais às metas, a Super com largura fixa, somando 100%', () => {
        const r = regua(0, ANO)
        const soma = r.faixas.reduce((s, f) => s + f.largura, 0)
        expect(soma).toBeCloseTo(100, 6)
        expect(r.faixas[0].largura).toBeCloseTo(((3_502_020.14 / 6_900_000) * 100 * 100) / (100 + SUPER_VISUAL), 6)
    })

    it('o marcador anda dentro da faixa da zona e para no começo da Super', () => {
        const base = regua(4_907_308.22, ANO)
        const inicioBase = base.faixas[0].largura + base.faixas[1].largura
        expect(base.marcador).toBeGreaterThan(inicioBase)
        expect(base.marcador).toBeLessThan(inicioBase + base.faixas[2].largura)
        const acima = regua(9_000_000, ANO)
        expect(acima.marcador).toBeCloseTo(100 - acima.faixas[4].largura, 6)
    })
})

describe('atingido por meta e valores curtos', () => {
    it('% atingido (até 100) e o que falta de cada meta', () => {
        const linhas = atingimentoPorMeta(1_072_168.03, {
            TRISTE: 1_108_739.58,
            BASE: 1_393_040,
            AVANCADA: 1_899_600,
            SUPER: 2_184_540,
        })
        expect(linhas.map((l) => Number(l.pct.toFixed(1)))).toEqual([96.7, 77, 56.4, 49.1])
        expect(atingimentoPorMeta(2, ANO)[0].falta).toBeGreaterThan(99)
    })

    it('R$ mi com 2 casas, R$ mil com 1, como a v1', () => {
        expect(compacto(4_907_308.22)).toBe('R$ 4,91 mi')
        expect(compacto(888_686.43)).toBe('R$ 888,7 mil')
        expect(compacto(950)).toBe('R$ 950,00')
    })
})
