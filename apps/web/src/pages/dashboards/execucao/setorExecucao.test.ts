import { describe, expect, it } from 'vitest'
import {
    CHAVES,
    diasDoMes,
    diasPorMes,
    filtrosPagina,
    filtrosSetor,
    lerSetor,
    mesesComDias,
    numeroCnj,
    tomStatus,
} from './setorExecucao.ts'

const condenacao = {
    stats: {
        total_atividades_execucao_NG: 40,
        atividades_execucao_vencidas_NG: 4,
        total_por_prazo_execucao_NG: 25,
        por_prazo_concluidas_execucao_NG: 20,
        total_diligencias_execucao_NG: 12,
        cumpridas_diligencias_expedicao_alvara_execucao_NG: 3,
        valor_diligencias_expedicao_alvara_execucao_NG: 1500.5,
    },
    execucao_processos_por_atividade_NG: [{ name: 'CÁLCULO', value: 7 }],
    execucao_processos_por_atividade_por_prazo_NG: [{ name: 'PRAZO', value: 2 }],
    execucao_demandas_por_funcionario_NG: [
        { name: 'Ana', total: 9, encerrado_cumprido: 7, encerrado_nao_cumprido: 2, recebido: 0 },
    ],
    execucao_atividades_lista_NG: [
        {
            id: 81,
            status: 'Encerrado Cumprido',
            descricao: 'Calcular',
            funcionario: 'Ana',
            funcionario_atribuido: 'Bia',
            funcionario_encerramento: 'Ana',
            encerrado_pelo_responsavel: false,
            pessoa_setor: 'EXECUÇÃO',
            atividade: 'CÁLCULO',
            numero_processo: '00012345620248040001',
            prazo: '2026-11-10',
            vencida: true,
        },
    ],
    execucao_atividades_lista_filtros_opcoes_NG: {
        funcionarios: ['Ana', 'Bia'],
        atividades: ['CÁLCULO'],
        status: ['Encerrado Cumprido'],
        situacoes: [{ id: 'vencidas', label: 'Vencidas' }],
    },
    execucao_atrasos_detalhamento_NG: {
        total: 4,
        buckets: [{ dias: 1, label: '1 dia', descricao: 'venceu ontem', count: 3, pct: 75 }],
    },
    execucao_diligencias_por_processo_NG: [{ name: '00012345620248040001', value: 2, valor_execucao: 900 }],
    execucao_diligencias_por_funcionario_NG: [{ name: 'Ana', total: 5 }],
    execucao_diligencias_expedicao_alvara_processos_NG: [
        { numero_processo: '1', uf: 'AM', subfase: 'ALVARÁ', data_execucao: '2026-01-02', valor_execucao: 900 },
    ],
}

describe('lerSetor', () => {
    it('lê as atividades das duas visões e as diligências da Execução Condenação', () => {
        const s = lerSetor(condenacao, 'condenacao')
        expect(s.atividades.concluidas.total).toBe(40)
        expect(s.atividades.concluidas.vencidas).toBe(4)
        expect(s.atividades.concluidas.emAndamento).toBeNull()
        expect(s.atividades.por_prazo.total).toBe(25)
        expect(s.atividades.por_prazo.concluidas).toBe(20)
        expect(s.atividades.concluidas.porAtividade).toEqual([{ name: 'CÁLCULO', value: 7 }])
        expect(s.atividades.por_prazo.porAtividade).toEqual([{ name: 'PRAZO', value: 2 }])
        expect(s.atividades.concluidas.porFuncionario).toEqual([
            { name: 'Ana', total: 9, cumpridas: 7, naoCumpridas: 2 },
        ])
        expect(s.diligencias.total).toBe(12)
        expect(s.diligencias.alvarasCumpridos).toBe(3)
        expect(s.diligencias.valorRealizado).toBe(1500.5)
        expect(s.diligencias.porProcesso).toEqual([{ processo: '00012345620248040001', valor: 900, quantidade: 2 }])
        expect(s.diligencias.porColaborador).toEqual([{ name: 'Ana', value: 5 }])
        expect(s.diligencias.processosAlvara[0]).toMatchObject({ uf: 'AM', valor: 900, dataExecucao: '2026-01-02' })
        expect(s.atrasos).toEqual({
            total: 4,
            faixas: [{ dias: 1, label: '1 dia', descricao: 'venceu ontem', quantidade: 3, pct: 75 }],
        })
    })

    it('na tarefa, o responsável é o atribuído e "encerrado por" só aparece quando foi outra pessoa', () => {
        const [t] = lerSetor(condenacao, 'condenacao').atividades.concluidas.lista
        expect(t).toMatchObject({ id: '81', responsavel: 'Bia', encerradoPor: 'Ana', vencida: true, concluida: false })
    })

    it('nos Acordos, lê os nomes com execucao_acordos e o que falta vira null/[]', () => {
        const s = lerSetor(
            {
                stats: { total_atividades_execucao_acordos_NG: 8, total_diligencias_execucao_acordos_NG: 2 },
                execucao_acordos_processos_por_atividade_NG: [{ name: 'MINUTA', value: 3 }],
            },
            'acordos',
        )
        expect(s.atividades.concluidas.total).toBe(8)
        expect(s.atividades.concluidas.porAtividade).toEqual([{ name: 'MINUTA', value: 3 }])
        expect(s.diligencias.total).toBe(2)
        expect(s.diligencias.porProcesso).toEqual([])
        expect(s.atrasos).toEqual({ total: 0, faixas: [] })
    })
})

describe('produção diária', () => {
    const dias = [
        { name: '2026-10-30', value: 2 },
        { name: '2026-11-03', value: 4 },
        { name: '2026-11-01', value: 1 },
        { name: 'x', value: 9 },
    ]
    it('soma os dias por mês no formato da v1', () => {
        expect(diasPorMes(dias)).toEqual([
            { name: 'out 2026', value: 2 },
            { name: 'nov 2026', value: 5 },
        ])
    })
    it('lista os meses (mais recente primeiro) e os dias de um mês em ordem', () => {
        expect(mesesComDias(dias)).toEqual(['2026-11', '2026-10'])
        expect(diasDoMes(dias, '2026-11').map((d) => d.name)).toEqual(['2026-11-01', '2026-11-03'])
    })
})

describe('numeroCnj', () => {
    it('formata o nº com 20 dígitos e deixa os outros como vieram', () => {
        expect(numeroCnj('00012345620248040001')).toBe('0001234-56.2024.8.04.0001')
        expect(numeroCnj('123')).toBe('123')
        expect(numeroCnj(null)).toBe('—')
    })
})

describe('filtros', () => {
    it('os da seção são inline, com as chaves do setor; tipo de diligência e colaborador são de um valor só', () => {
        const campos = filtrosSetor('condenacao', lerSetor(condenacao, 'condenacao'))
        expect(campos.every((c) => c.inline)).toBe(true)
        expect(campos.map((c) => c.key)).toEqual(Object.values(CHAVES.condenacao))
        const funcionario = campos.find((c) => c.key === 'funcionario_execucao')
        expect(funcionario?.options.map((o) => o.value)).toEqual(['Ana', 'Bia'])
        expect(campos.find((c) => c.key === 'situacao_execucao')?.options).toEqual([
            { value: 'vencidas', label: 'Vencidas' },
        ])
        expect(campos.filter((c) => c.single).map((c) => c.key)).toEqual([
            'diligencia_tipo_execucao',
            'diligencia_colaborador_execucao',
        ])
        expect(filtrosSetor('acordos', lerSetor({}, 'acordos')).map((c) => c.key)).toEqual(
            Object.values(CHAVES.acordos),
        )
    })

    it('os da página vêm em ordem alfabética e sem repetição', () => {
        const [uf, , materia] = filtrosPagina({
            ufs: ['PA', 'AM', 'AM'],
            comarcas: [],
            materias: ['RMC', 'ANP'],
            subfases: [],
        })
        expect(uf.options.map((o) => o.value)).toEqual(['AM', 'PA'])
        expect(materia.options.map((o) => o.value)).toEqual(['ANP', 'RMC'])
    })
})

describe('tomStatus', () => {
    it('Visualizado laranja, Cumprido verde, Não cumprido vermelho; o resto neutro', () => {
        expect(tomStatus('Visualizado')).toBe('accent')
        expect(tomStatus('Encerrado Cumprido')).toBe('ok')
        expect(tomStatus('Encerrado Não Cumprido')).toBe('danger')
        expect(tomStatus('ENCERRADO NAO CUMPRIDO')).toBe('danger')
        expect(tomStatus('Recebido')).toBe('neutral')
        expect(tomStatus('')).toBe('neutral')
    })
})
