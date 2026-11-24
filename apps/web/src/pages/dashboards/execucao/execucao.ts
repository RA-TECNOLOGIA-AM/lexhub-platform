import { fmt } from '../../../lib/format.ts'
import type { Point } from '../../../types/index.ts'
import { contarPorCampo } from '../julgados-acordaos/julgados.ts'
import type { DadoFaltando } from '../julgados-acordaos/types.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { nomeNaUnidade, unidadeExecucao, type Unidade } from './unidade.ts'
import { comarcas, lerSetor, numero, pontos, type Comarcas, type SetorExecucao } from './setorExecucao.ts'

// A Execução Condenação: as rotas da v1 /execucao (NG), /execucao_LA e /execucao_RJ e as páginas NG/Execucao.tsx,
// LA/Execucao_LA.tsx e RJ/ExecucaoRJ.tsx (as mesmas seções; a LA sem Diligências). Os nomes abaixo são os da NG e
// passam por nomeNaUnidade. Os campos que a página lia da
// chamada sem data (o estoque de agora, as distribuições e o "mês a mês") a API já manda trocados pelos do
// histórico (dashboards/execucao.py); o total em execução de agora vem em `total_em_execucao_historico`.
// Só lógica pura (testada em execucao.test.ts).

export type Execucao = {
    unidade: Unidade // de que rota da v1 veio (a LA não tem Diligências)
    // Seção 01: indicadores
    totalEmExecucao: number | null // agora (não depende do período)
    valorTotal: number | null // agora: valor em aberto (remanescente quando já caiu o incontroverso)
    valorRemanescente: number | null // agora
    entradas: number | null // no período (data da execução)
    valorEntradas: number | null
    saidas: number | null // no período (compensação do alvará)
    saidasIncontroverso: number | null
    valorSaidas: number | null
    valorTed: number | null
    valorIncontroverso: number | null
    mediaTempo: number | null // dias
    medianaTempo: number | null
    estoqueInicial: number | null
    tre: number | null
    semValor: { total: number; processos: string[] } // processos sem valor da execução (o aviso da v1)
    // V2: os processos em execução agora com campo do cadastro em branco (sem o filtro de período), um item por
    // campo: a faixa "Atenção" dos Julgados (app/dashboards/execucao_campos.py).
    camposFaltando: DadoFaltando[]
    // Seção 02: distribuições (histórico todo)
    valorPorSubfase: Point[]
    porSubfase: Point[]
    porMateria: Point[]
    comarca: Record<'total' | 'entrada' | 'saida', Comarcas>
    remanescentePorMes: Point[]
    // Seções 03 e 04: "mês a mês" (histórico todo)
    entradasPorMes: Point[]
    valorEntradasPorMes: Point[]
    valorSaidasPorMes: Point[]
    // As opções dos filtros (da base inteira, antes dos filtros)
    opcoes: { ufs: string[]; comarcas: string[]; materias: string[]; subfases: string[] }
    setor: SetorExecucao
}

const lista = (v: unknown): string[] => (Array.isArray(v) ? v.map((x) => String(x ?? '').trim()).filter(Boolean) : [])

// Os nomes dos processos sem valor (a lista do aviso): a v1 manda objetos ou textos.
function semValorProcessos(v: unknown): string[] {
    if (!Array.isArray(v)) return []
    return v
        .map((x) =>
            typeof x === 'object' && x !== null
                ? String((x as Record<string, unknown>).numero_processo ?? (x as Record<string, unknown>).name ?? '')
                : String(x ?? ''),
        )
        .map((x) => x.trim())
        .filter(Boolean)
}

// Os itens {numero_processo, campo} da API; o que vier sem número ou sem campo fica de fora. (Também nos Acordos.)
export function camposFaltando(v: unknown): DadoFaltando[] {
    if (!Array.isArray(v)) return []
    return v.flatMap((x) => {
        const r = (x ?? {}) as Record<string, unknown>
        const numero = String(r.numero_processo ?? '').trim()
        const campo = String(r.campo ?? '').trim()
        return numero && campo ? [{ numero_processo: numero, campo }] : []
    })
}

// Como cada campo aparece na frase do aviso ("sem a data da execução"); os três últimos são dos Acordos.
const NO_AVISO: Record<string, string> = {
    'Valor da execução': 'o valor da execução',
    'Data da execução': 'a data da execução',
    'Data do trânsito em julgado': 'a data do trânsito em julgado',
    'Data de distribuição': 'a data de distribuição',
    'Valor da causa': 'o valor da causa',
    Matéria: 'a matéria',
    Comarca: 'a comarca',
    Competência: 'a competência',
    Vara: 'a vara',
    UF: 'a UF',
    Subfase: 'a subfase',
    'Valor de alçada final': 'o valor de alçada final',
    'Data do acordo fechado': 'a data do acordo fechado',
}

// Os avisos da faixa "Atenção", do campo com mais processos ao com menos (o mesmo padrão dos Julgados).
// onde: como a frase chama a base ('em execução'; nos Acordos, 'em acordo').
export function avisosCamposFaltando(itens: DadoFaltando[], onde = 'em execução'): string[] {
    return contarPorCampo(itens).map(
        ([campo, n]) => `Existem ${fmt.int(n)} processo(s) ${onde} sem ${NO_AVISO[campo] ?? `o campo "${campo}"`}!`,
    )
}

export function lerExecucao(data: V1GenericoResponse): Execucao {
    const u = unidadeExecucao(data) ?? 'NG'
    const dados = data as V1GenericoResponse & Record<string, unknown>
    const stats = data.stats ?? {}
    const d = (campo: string) => dados[nomeNaUnidade(campo, u)]
    const s = (campo: string) => stats[nomeNaUnidade(campo, u)]
    const n = (campo: string) => numero(s(campo))
    return {
        unidade: u,
        totalEmExecucao: n('total_em_execucao_historico'),
        valorTotal: n('valor_total_em_execucao'),
        valorRemanescente: n('valor_remanescente_em_execucao'),
        entradas: n('total_em_execucao'),
        valorEntradas: n('valor_em_execucao'),
        saidas: n('total_saida_execucao_periodo'),
        saidasIncontroverso: n('total_incontroverso_saida_execucao_periodo'),
        valorSaidas: n('valor_execucao_saida_periodo'),
        valorTed: n('valor_ted_saida_execucao_periodo'),
        valorIncontroverso: n('valor_incontroverso_saida_execucao_periodo'),
        mediaTempo: n('media_tempo_execucao'),
        medianaTempo: n('mediana_tempo_execucao'),
        estoqueInicial: n('estoque_inicial'),
        tre: n('tre'),
        semValor: {
            total: n('total_valor_execucao_vazio') ?? 0,
            processos: semValorProcessos(s('total_valor_execucao_vazio_detalhe')),
        },
        camposFaltando: camposFaltando(dados.campos_faltando),
        valorPorSubfase: pontos(d('valor_execucao_por_subfase')),
        porSubfase: pontos(d('execucao_por_subfase')),
        porMateria: pontos(d('execucao_por_materia')),
        comarca: {
            total: comarcas(d('execucao_por_comarca_total'), d('execucao_valor_por_comarca_total')),
            entrada: comarcas(d('execucao_por_comarca_entrada'), d('execucao_valor_por_comarca_entrada')),
            saida: comarcas(d('execucao_por_comarca_saida'), d('execucao_valor_por_comarca_saida')),
        },
        remanescentePorMes: pontos(d('valor_remanescente_por_mes')),
        entradasPorMes: pontos(d('quantidade_entrada_execucao_por_mes')),
        valorEntradasPorMes: pontos(d('valor_entrada_execucao_por_mes')),
        valorSaidasPorMes: pontos(d('valor_execucao_saida_periodo_por_mes')),
        opcoes: {
            ufs: lista(s('execucao_uf_opcoes_NG')),
            comarcas: lista(s('execucao_comarca_opcoes_NG')),
            materias: lista(s('execucao_materia_opcoes_NG')),
            subfases: lista(s('execucao_subfase_opcoes_NG')),
        },
        setor: lerSetor(dados, 'condenacao', u),
    }
}
