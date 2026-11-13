import { describe, expect, it } from 'vitest'
import { devolucoes, funcionarios, initials, isPlaceholder, leituraDevolucao, mesParcial, share } from './charts.ts'

describe('funcionarios', () => {
    it('junta as listas por pessoa, maior total primeiro', () => {
        const rows = funcionarios({
            protocolados_por_funcionario: [
                { name: 'Ana', value: 10 },
                { name: 'Raimunda Moura', value: 168 },
            ],
            represados_por_funcionario: [
                { name: 'Raimunda Moura', value: 1 },
                { name: 'Bia', value: 2 },
            ],
            media_protocolados_por_funcionario: [{ name: 'Raimunda Moura', value: 21 }],
            valor_causa_por_funcionario: [{ name: 'Raimunda Moura', value: 5907062.43 }],
        })
        expect(rows.map((r) => r.name)).toEqual(['Raimunda Moura', 'Ana', 'Bia'])
        expect(rows[0]).toEqual({
            name: 'Raimunda Moura',
            protocolados: 168,
            represados: 1,
            mediaDiaria: 21,
            valorCausa: 5907062.43,
        })
        expect(rows[2]).toMatchObject({ protocolados: 0, represados: 2, mediaDiaria: null })
    })
})

describe('devolucoes', () => {
    it('total e % de cada setor', () => {
        const d = devolucoes({ devolvido_peticionamento: 110, devolvido_org_doc: 105, devolvido_pendencia: 0 })
        expect(d.total).toBe(215)
        expect(d.partes.map((p) => Math.round(p.pct * 10) / 10)).toEqual([51.2, 48.8, 0])
    })

    it('sem devolução: tudo 0%', () => {
        const d = devolucoes({ devolvido_peticionamento: 0, devolvido_org_doc: 0, devolvido_pendencia: 0 })
        expect(d.partes.every((p) => p.pct === 0)).toBe(true)
    })
})

describe('leituraDevolucao', () => {
    it('a frase segue a variação', () => {
        expect(leituraDevolucao(110, 214.29)).toEqual({ text: 'Aumento crítico de devolução', tone: 'danger' })
        expect(leituraDevolucao(105, -72.5)).toEqual({ text: 'Forte queda nas devoluções', tone: 'ok' })
        expect(leituraDevolucao(0, 0).text).toBe('Nenhuma devolução pendente')
        expect(leituraDevolucao(5, 10).tone).toBe('danger')
        expect(leituraDevolucao(5, null).tone).toBe('neutral')
    })
})

describe('auxiliares', () => {
    it('iniciais, %, placeholder e mês parcial', () => {
        expect(initials('Raimunda Moura')).toBe('RM')
        expect(initials('Ana')).toBe('A')
        expect(share(1, 169)).toBeCloseTo(0.59, 2)
        expect(share(1, 0)).toBe(0)
        expect(isPlaceholder('Sem matéria')).toBe(true)
        expect(isPlaceholder('ANP')).toBe(false)
        expect(mesParcial(2026, new Date(2026, 10, 13))).toBe(10)
        expect(mesParcial(2025, new Date(2026, 10, 13))).toBeNull()
    })
})
