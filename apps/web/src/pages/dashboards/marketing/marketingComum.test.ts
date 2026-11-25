import { describe, expect, it } from 'vitest'
import { FILTER_KEYS } from '../../../lib/dashboardQuery.ts'
import {
    DIMENSOES,
    comoNg,
    funilAnuncio,
    funilPipeline,
    rubricasComparadas,
    semUtm,
    variacaoSobre,
    dependentes,
    duplicadoPorGenero,
    faixasSalariais,
    filtrosDeClique,
    leitor,
    lider,
    porFaixaEtaria,
    rotuloSalario,
    semResposta,
    versus,
} from './marketingComum.ts'

describe('leitor da resposta da v1', () => {
    const ler = leitor(
        { p_total: 12, p_media: null },
        {
            p_genero: [
                { name: 'FEMININO', value: 7 },
                { name: '', value: 1 },
            ],
            p_rubrica_campanha: [{ name: 'MORA', ra: 2, ng: 5 }],
            p_investimento_cliques_leads: [{ name: '01/11', investimento: 10.5, cliques: 3, leads: 1 }],
        },
        'p_',
    )

    it('número sem o prefixo; ausente ou null vira 0, como a v1', () => {
        expect(ler.n('total')).toBe(12)
        expect(ler.n('media')).toBe(0)
        expect(ler.n('nao_existe')).toBe(0)
    })

    it('séries: sem nome some; ausente = []', () => {
        expect(ler.serie('genero')).toEqual([{ name: 'FEMININO', value: 7 }])
        expect(ler.serie('ocupacao')).toEqual([])
        expect(ler.rubricasRaNg('rubrica_campanha')).toEqual([{ name: 'MORA', ra: 2, ng: 5 }])
        expect(ler.investimento).toEqual([{ name: '01/11', investimento: 10.5, cliques: 3, leads: 1 }])
    })

    it('resposta vazia não quebra', () => {
        const vazio = leitor(undefined, {}, 'p_')
        expect(vazio.temDados).toBe(false)
        expect(vazio.serie('genero')).toEqual([])
        expect(vazio.investimento).toEqual([])
    })

    it('rótulos das etiquetas: os nomes dos gráficos + o já escolhido', () => {
        const [genero, rubrica] = filtrosDeClique(ler, ['genero_marketing', 'rubrica_marketing'], {
            genero_marketing: ['OUTRO'],
        })
        expect(genero.options.map((o) => o.value)).toEqual(['OUTRO', 'FEMININO'])
        expect(rubrica.options.map((o) => o.value)).toEqual(['MORA'])
        expect(genero.fromChart).toBe(true)
    })
})

it('toda dimensão é um filtro conhecido da URL', () => {
    for (const dim of Object.keys(DIMENSOES)) expect(FILTER_KEYS).toContain(dim)
})

it('faixa etária na ordem da idade', () => {
    const pts = porFaixaEtaria([
        { name: '45+', value: 9 },
        { name: '18-24', value: 2 },
        { name: '25-34', value: 5 },
    ])
    expect(pts.map((p) => p.name)).toEqual(['18-24', '25-34', '45+'])
})

describe('selos e notas de Perfil e Triados', () => {
    it('líder da série com o % no total; série vazia = null', () => {
        expect(
            lider([
                { name: 'anuncio_ng', value: 89 },
                { name: 'resgate', value: 52 },
                { name: 'retorno', value: 118 - 52 - 9 },
            ]),
        ).toMatchObject({ name: 'anuncio_ng', value: 89 })
        expect(lider([])).toBeNull()
        expect(lider([{ name: 'x', value: 0 }])).toBeNull()
    })

    it('não informado no total', () => {
        expect(
            semResposta([
                { name: 'Não informado', value: 144 },
                { name: 'Até 2500', value: 112 },
            ]),
        ).toBeCloseTo(56.25)
        expect(semResposta([{ name: 'Até 2500', value: 67 }])).toBe(0)
    })

    it('"ativa" e "ativo" = o mesmo valor escrito de dois jeitos', () => {
        const dup = duplicadoPorGenero([
            { name: 'passiva', value: 163 },
            { name: 'ativa', value: 52 },
            { name: 'ativo', value: 44 },
        ])
        expect(dup?.nomes).toEqual(['ativa', 'ativo'])
        expect(dup?.share).toBeCloseTo((96 / 259) * 100)
        expect(
            duplicadoPorGenero([
                { name: 'passiva', value: 1 },
                { name: 'ativa', value: 1 },
            ]),
        ).toBeNull()
    })

    it('"Orgânico vs. Pago"', () => {
        expect(
            versus([
                { name: 'orgânico', value: 2 },
                { name: 'PAGO', value: 1 },
            ]),
        ).toBe('Orgânico vs. Pago')
    })
})

describe('média salarial e pessoas dependentes', () => {
    it('rótulos curtos das faixas salariais', () => {
        expect(rotuloSalario('Até 2500')).toBe('Até 2,5k')
        expect(rotuloSalario('De 2.500 a 5.000')).toBe('2,5k – 5k')
        expect(rotuloSalario('De 5.000 a 10.000')).toBe('5k – 10k')
        expect(rotuloSalario('Acima de 10.000')).toBe('10k+')
        expect(rotuloSalario('Outra resposta')).toBe('Outra resposta')
    })

    it('faixas em ordem, % sobre quem respondeu; não informado à parte, % sobre o total', () => {
        const { faixas, naoInformado } = faixasSalariais([
            { name: 'Não informado', value: 144 },
            { name: 'De 2.500 a 5.000', value: 34 },
            { name: 'Acima de 10.000', value: 4 },
            { name: 'Até 2500', value: 67 },
            { name: 'De 5.000 a 10.000', value: 10 },
        ])
        expect(faixas.map((f) => f.rotulo)).toEqual(['Até 2,5k', '2,5k – 5k', '5k – 10k', '10k+'])
        expect(Math.round(faixas[0].share)).toBe(58)
        expect(naoInformado.value).toBe(144)
        expect(Math.round(naoInformado.share)).toBe(56)
    })

    it('dependentes em ordem, "Acima de 6 pessoas" = "6+ dep."', () => {
        const itens = dependentes([
            { name: '5 pessoas', value: 24 },
            { name: 'Acima de 6 pessoas', value: 13 },
            { name: '1 pessoa', value: 11 },
            { name: 'Não informado', value: 2 },
        ])
        expect(itens.map((i) => i.rotulo)).toEqual(['1 dep.', '5 dep.', '6+ dep.', 'Não informado'])
        expect(itens[0].name).toBe('1 pessoa') // o filtro usa o nome original
    })
})

describe('Facebook Ads, Fechamento e Aquisição', () => {
    it('funil do anúncio: taxa sobre a etapa anterior e largura sobre a 1ª', () => {
        const [cliques, pageview, leads, clientes] = funilAnuncio([
            { nome: 'Cliques', valor: 1000 },
            { nome: 'Pageview', valor: 800 },
            { nome: 'Leads', valor: 80 },
            { nome: 'Clientes', valor: 20 },
        ])
        expect(cliques.taxa).toBe(100)
        expect(pageview.taxa).toBe(80)
        expect(leads.taxa).toBe(10)
        expect(clientes.taxa).toBe(25)
        expect(clientes.largura).toBe(2)
    })

    it('funil de pipeline: zeradas agrupadas, ASSINADO = Fechado / cliente, conversão final', () => {
        const f = funilPipeline([
            { name: 'ONBOARDING', value: 0 },
            { name: 'ETAPA 1', value: 0 },
            { name: 'EM ASSINATURA', value: 567 },
            { name: 'ASSINADO', value: 562 },
        ])
        expect(f.zeradas.map((e) => e.name)).toEqual(['ONBOARDING', 'ETAPA 1'])
        expect(f.ativas.map((e) => e.name)).toEqual(['EM ASSINATURA', 'Fechado / cliente'])
        expect(f.conversao?.taxa).toBeCloseTo(99.1, 1)
        expect(funilPipeline([]).conversao).toBeNull()
    })

    it('comparativo por rubrica junta campanha e protocolado; relação = prot ÷ camp', () => {
        const linhas = rubricasComparadas(
            [
                { name: 'CESTA', ra: 0, ng: 144 },
                { name: 'MORA', ra: 1, ng: 80 },
            ],
            [
                { name: 'CESTA', ra: 0, ng: 154 },
                { name: 'ANP', ra: 0, ng: 3 },
            ],
        )
        expect(linhas.map((l) => l.name)).toEqual(['CESTA', 'MORA', 'ANP'])
        expect(Math.round(linhas[0].relacao)).toBe(107)
        expect(linhas[1].protocolado).toEqual({ ng: 0, ra: 0 })
        expect(linhas[2].relacao).toBe(0) // sem campanha: sem base
        expect(comoNg([{ name: 'X', value: 2 }])).toEqual([{ name: 'X', ra: 0, ng: 2 }])
    })

    it('sem UTM: "(Em branco)" no total', () => {
        const r = semUtm([
            { name: '(Em branco)', value: 315 },
            { name: 'Reels', value: 221 },
        ])
        expect(r.value).toBe(315)
        expect(r.total).toBe(536)
        expect(r.share).toBeCloseTo(58.8, 1)
        expect(variacaoSobre(295.3, 374.92)).toBeCloseTo(-21.2, 1)
        expect(variacaoSobre(1, 0)).toBeNull()
    })
})
