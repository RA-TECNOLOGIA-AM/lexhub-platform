import { describe, expect, it } from 'vitest'
import type { JulgadosSentencas } from './fields.ts'
import { avisosSentencas, ordenarSentencas } from './sentencas.ts'
import type { LinhaSentenca } from './types.ts'

const linha = (numero: string, data: string | null): LinhaSentenca => ({
    id: null,
    numero_processo: numero,
    fase: '',
    subfase: '',
    status_1g: '',
    uf: '',
    juiz: '',
    data_sentenca: data,
    status_sentenca_embargos: '',
    data_sentenca_embargos: null,
})

describe('Julgados Sentenças: contas da tela', () => {
    it('avisos da faixa "Atenção": só os que têm processo, na ordem da v1', () => {
        const n = { meritoSemData: 2, semJuiz: 0, semUf: 1 } as unknown as JulgadosSentencas['n']
        expect(avisosSentencas(n)).toEqual([
            'Existem 2 processo(s) com mérito da sentença lançado e sem a data da sentença — não entram em nenhuma contagem!',
            'Existem 1 processo(s) sentenciado(s) sem a UF!',
        ])
    })

    it('ordena pela data da sentença; sem data vai para o fim', () => {
        const itens = [linha('a', '2026-10-01'), linha('b', null), linha('c', '2026-10-05')]
        expect(ordenarSentencas(itens, 'data_recente').map((r) => r.numero_processo)).toEqual(['c', 'a', 'b'])
        expect(ordenarSentencas(itens, 'data_antiga').map((r) => r.numero_processo)).toEqual(['a', 'c', 'b'])
    })
})
