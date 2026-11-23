import { describe, expect, it } from 'vitest'
import {
    SELECAO_VAZIA,
    alternarPilula,
    calcular,
    curva,
    disponiveis,
    escolherCenario,
    gradeCurva,
    lerPrevisao,
    lerVitoria,
    medianaKmMaterias,
    nModelo,
    pct1,
    phi,
    quantil,
    type PrevisaoResponse,
} from './previsao.ts'

// O bundle real (gerado pelo modelo-machine-learning/, versionado na API). Os números abaixo são do modelo treinado
// na foto de 19/11/2026; retreinou com outra foto? Atualize-os (com a foto de 10/11 eram os da v1: 125 d e 84 d).
const real = Object.values(
    import.meta.glob('../../../../../api/src/app/analyses/GERAL/data/tcc_previsao_individual.json', {
        eager: true,
        import: 'default',
    }),
)[0] as PrevisaoResponse

// O recorte da API (app/dashboards/previsao_individualizada.py): só o escritório da unidade.
function soDoEscritorio(d: PrevisaoResponse, sigla: string): PrevisaoResponse {
    const filtra = <T>(t: Record<string, T> | undefined) =>
        t && Object.fromEntries(Object.entries(t).filter(([k]) => k.split('|')[4] === sigla))
    return {
        ...d,
        opcoes: { ...d.opcoes, escritorios: [sigla] },
        previsoes: filtra(d.previsoes)!,
        pesos_treino: filtra(d.pesos_treino)!,
        procedencia: filtra(d.procedencia),
        historico_acordo_pre: filtra(d.historico_acordo_pre),
    }
}

describe('cálculo da v1 com o bundle real', () => {
    it('tudo em "Todos" (NG + LA, como a v1 sem filtro): mediana 137 d (65–288)', () => {
        const c = calcular(real, SELECAO_VAZIA)
        expect(c.nTreino).toBe(36851)
        expect(c.diasPrevisto).toBe(137)
        expect(c.faixa).toEqual({ de: 65, ate: 288 })
        expect(c.p1g! * 100).toBeCloseTo(36.1, 1)
        expect(c.valor2g! * 100).toBeCloseTo(37.2, 1)
        expect(c.acordoPos! * 100).toBeCloseTo(8.0, 1)
        expect(c.acordoPre! * 100).toBeCloseTo(2.7, 1)
        expect(c.medianaMateria).toBe(333)
    })

    it('ANP + MANAUS no NG: mediana 94 d (48–187)', () => {
        const c = calcular(soDoEscritorio(real, 'NG'), { ...SELECAO_VAZIA, materias: ['ANP'], comarcas: ['MANAUS'] })
        expect(c.nTreino).toBe(1753)
        expect(c.diasPrevisto).toBe(94)
        expect(c.faixa).toEqual({ de: 48, ate: 187 })
        expect(c.p1g! * 100).toBeCloseTo(6.2, 1)
        expect(c.valor2g! * 100).toBeCloseTo(25.9, 1)
        expect(c.acordoPos! * 100).toBeCloseTo(1.9, 1)
        expect(c.acordoPre! * 100).toBeCloseTo(1.58, 2)
        expect(c.medianaMateria).toBe(255)
    })

    it('LA + Belém: sem processos de treino, sem previsão', () => {
        const c = calcular(soDoEscritorio(real, 'LA'), { ...SELECAO_VAZIA, comarcas: ['BELÉM'] })
        expect(c.nTreino).toBe(0)
        expect(c.diasPrevisto).toBeNull()
        expect(c.p1g).toBeNull()
    })

    it('o modelo distingue 24 matérias, 14 comarcas e 4 competências', () => {
        expect([nModelo(real, 'materia'), nModelo(real, 'comarca'), nModelo(real, 'competencia')]).toEqual([24, 14, 4])
    })

    it('as opções do formulário são só as com treino no escritório', () => {
        const la = disponiveis(soDoEscritorio(real, 'LA'))
        expect(la.comarcas).not.toContain('BELÉM')
        expect(la.materias.length).toBeGreaterThan(0)
    })
})

describe('peças', () => {
    it('lê os formatos do bundle', () => {
        expect(lerPrevisao(undefined)).toBeNull()
        expect(lerPrevisao(90)).toEqual({ dias: 90 })
        const p = lerPrevisao([81, 171, 487, 251, 250, 61, 2, 5, 92])!
        expect(p.p1g).toBeCloseTo(0.171)
        expect(p.p2g).toEqual([0.487, 0.251, 0.25])
        expect(p.acPre).toBeCloseTo(0.0092)
    })

    it('Φ e o quantil de uma log-normal pura voltam a mediana', () => {
        expect(phi(0)).toBeCloseTo(0.5, 6)
        expect(phi(1.96)).toBeCloseTo(0.975, 3)
        const comps = [{ dias: 200, peso: 1, n: 1, esc: 'NG' }]
        expect(quantil(comps, 0.5)).toBe(200)
    })

    it('a KM da matéria', () => {
        const d = {
            km_materia: {
                A: [
                    [10, 1, 0],
                    [20, 1, 0],
                    [30, 1, 0],
                ],
            },
        } as unknown as PrevisaoResponse
        expect(medianaKmMaterias(d, ['A'])).toBe(20)
        expect(medianaKmMaterias(d, ['B'])).toBeNull()
    })

    it('a grade da curva tem 22 pontos entre 420 e 3.000 dias', () => {
        expect(gradeCurva(0).at(-1)).toBe(420)
        expect(gradeCurva(500).at(-1)).toBe(1100)
        expect(gradeCurva(5000).at(-1)).toBe(3000)
        expect(gradeCurva(100)).toHaveLength(22)
    })

    it('a curva começa em 100% e cai até a mediana em ~50%', () => {
        const c = calcular(real, SELECAO_VAZIA)
        const k = curva(c)
        expect(k.caso[0]).toBe(100)
        expect(k.materia[0]).toBe(100)
    })

    it('cenário do 1G', () => {
        const c = { seProcedente: 0.5, seImprocedente: 0.2, seExtinto: 0.1, combinada: 0.3 }
        expect(escolherCenario(c, [], 0.4, 0.3)).toBe(0.3)
        expect(escolherCenario(c, ['Procedente'], 0.4, 0.3)).toBe(0.5)
        expect(escolherCenario(null, ['Procedente'], 0.4, 0.3)).toBeNull()
    })

    it('pílulas: todas marcadas voltam para "Todos"', () => {
        expect(alternarPilula(['a'], 'b', ['a', 'b'])).toEqual([])
        expect(alternarPilula(['a'], 'a', ['a', 'b'])).toEqual([])
        expect(alternarPilula([], 'a', ['a', 'b'])).toEqual(['a'])
    })

    it('formatadores e leitura do bootstrap', () => {
        expect(pct1(0.0125)).toBe('1,3%')
        expect(pct1(0.356)).toBe('36%')
        expect(lerVitoria(100, 'Cox')).toBe('vantagem consistente sobre o Cox')
        expect(lerVitoria(0, 'Cox')).toBe('o Cox é consistentemente melhor')
        expect(lerVitoria(50, 'Cox')).toBe('empate técnico com o Cox')
    })
})
