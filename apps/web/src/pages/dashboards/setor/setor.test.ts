import { describe, expect, it } from 'vitest'
import {
    devolucoes,
    filaTone,
    funcionarios,
    initials,
    isPlaceholder,
    leituraDevolucao,
    mesParcial,
    nomesFuncionarios,
    share,
} from './setor.ts'

describe('funcionarios', () => {
    it('junta as listas por pessoa, maior total primeiro', () => {
        const rows = funcionarios({
            feitos: [
                { name: 'Ana', value: 10 },
                { name: 'Raimunda Moura', value: 168 },
            ],
            pendentes: [
                { name: 'Raimunda Moura', value: 1 },
                { name: 'Bia', value: 2 },
            ],
            media: [{ name: 'Raimunda Moura', value: 21 }],
            valor: [{ name: 'Raimunda Moura', value: 5907062.43 }],
        })
        expect(rows.map((r) => r.name)).toEqual(['Raimunda Moura', 'Ana', 'Bia'])
        expect(rows[0]).toEqual({
            name: 'Raimunda Moura',
            feitos: 168,
            pendentes: 1,
            mediaDiaria: 21,
            valorCausa: 5907062.43,
            valorSecundario: null,
        })
        expect(rows[2]).toMatchObject({ feitos: 0, pendentes: 2, mediaDiaria: null })
    })

    it('valor secundário (ex.: protocolado) quando o setor tem', () => {
        const [row] = funcionarios({
            feitos: [{ name: 'Milena Graça', value: 71 }],
            pendentes: [],
            media: [],
            valor: [{ name: 'Milena Graça', value: 1706716.3 }],
            valorSecundario: [{ name: 'Milena Graça', value: 1557402.66 }],
        })
        expect(row.valorSecundario).toBe(1557402.66)
    })
})

describe('devolucoes', () => {
    it('total e % de cada setor', () => {
        const d = devolucoes([
            { key: 'peticionamento', label: 'Peticionamento', value: 110 },
            { key: 'org_doc', label: 'Org Doc', value: 105 },
            { key: 'pendencia', label: 'Pendência', value: 0 },
        ])
        expect(d.total).toBe(215)
        expect(d.partes.map((p) => Math.round(p.pct * 10) / 10)).toEqual([51.2, 48.8, 0])
    })

    it('sem devolução: tudo 0%', () => {
        const d = devolucoes([{ key: 'org_doc', label: 'Org Doc', value: 0 }])
        expect(d.partes[0].pct).toBe(0)
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
    it('iniciais, %, fila, placeholder e mês parcial', () => {
        expect(initials('Raimunda Moura')).toBe('RM')
        expect(initials('Ana')).toBe('A')
        expect(share(1, 169)).toBeCloseTo(0.59, 2)
        expect(share(1, 0)).toBe(0)
        expect([filaTone(0.6), filaTone(7), filaTone(39.8)]).toEqual(['ok', 'warn', 'danger'])
        expect(isPlaceholder('Sem matéria')).toBe(true)
        expect(isPlaceholder('ANP')).toBe(false)
        expect(mesParcial(2026, new Date(2026, 10, 13))).toBe(10)
        expect(mesParcial(2025, new Date(2026, 10, 13))).toBeNull()
    })
})

describe('nomesFuncionarios', () => {
    it('nomes curtos dos gráficos + da lista completa só quem não está neles', () => {
        expect(
            nomesFuncionarios(
                ['Millena de', 'Larissa dos', 'Millena de'],
                ['Millena de Souza Sá Graça', 'Larissa dos Santos', 'Elizabeth Alves'],
            ),
        ).toEqual(['Elizabeth Alves', 'Larissa dos', 'Millena de'])
    })
})
