import type { Point } from '../../../types/index.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { nomeNaUnidade, unidadeAcordos, type Unidade } from '../execucao/unidade.ts'
import {
    comarcas,
    lerSetor,
    numero,
    pontos,
    processosLista,
    type Comarcas,
    type ProcessoLista,
    type SetorExecucao,
} from '../execucao/setorExecucao.ts'

// A Execução Acordos: as rotas da v1 /execucao_acordos_NG, _LA e _RJ e as páginas NG/ExecucaoAcordos.tsx,
// LA/ExecucaoAcordosLA.tsx e RJ/ExecucaoAcordosRJ.tsx (as mesmas seções). Os nomes abaixo são os da NG e passam por
// nomeNaUnidade. O estoque de
// agora, as distribuições e o "mês a mês" (que a página lia da chamada sem data) a API já manda trocados pelos
// do histórico (dashboards/acordos.py). Só lógica pura (testada em execucaoAcordos.test.ts).

export type Acordos = {
    unidade: Unidade
    // Seção 01: fechamento de acordo (processos ainda negociando; histórico todo)
    fechamentoPorSubfase: Point[]
    valorFechamentoPorSubfase: Point[]
    // Seção 02: indicadores
    totalEmExecucao: number | null // agora
    valorTotal: number | null // agora (valor de alçada final)
    entradas: number | null // no período (data da execução, etiqueta Acordo)
    valorEntradas: number | null
    pagos: number | null // no período (data do pagamento do acordo)
    valorPagos: number | null
    mediaTempo: number | null // dias, da execução ao pagamento
    medianaTempo: number | null
    estoqueInicial: number | null
    tre: number | null
    semValor: { total: number; processos: string[] } // sem valor de alçada final (o aviso da v1)
    // Seção 03: distribuições (histórico todo)
    valorPorSubfase: Point[]
    porSubfase: Point[]
    porSentenca: Point[] // Pré x Pós-Sentença
    porMateria: Point[]
    porTipoAcao: Point[] // Judicial x Extrajudicial
    comarca: Record<'total' | 'entrada' | 'saida', Comarcas>
    // Seções 04 e 05: "mês a mês" (histórico todo)
    entradasPorMes: Point[]
    pagosPorMes: Point[]
    valorEntradasPorMes: Point[]
    valorPagosPorMes: Point[]
    // Seção 08: as execuções de acordo do período
    listas: Record<'entrada' | 'saida' | 'total', ProcessoLista[]>
    opcoes: { ufs: string[]; comarcas: string[]; materias: string[]; subfases: string[] }
    setor: SetorExecucao
}

const lista = (v: unknown): string[] => (Array.isArray(v) ? v.map((x) => String(x ?? '').trim()).filter(Boolean) : [])

const processosSemValor = (v: unknown): string[] =>
    Array.isArray(v)
        ? v
              .map((x) =>
                  typeof x === 'object' && x !== null
                      ? String((x as Record<string, unknown>).numero_processo ?? '')
                      : String(x ?? ''),
              )
              .map((x) => x.trim())
              .filter(Boolean)
        : []

export function lerAcordos(data: V1GenericoResponse): Acordos {
    const u = unidadeAcordos(data) ?? 'NG'
    const dados = data as V1GenericoResponse & Record<string, unknown>
    const stats = data.stats ?? {}
    const d = (campo: string) => dados[nomeNaUnidade(campo, u)]
    const s = (campo: string) => stats[nomeNaUnidade(campo, u)]
    const n = (campo: string) => numero(s(campo))
    const comarca = (modo: 'total' | 'entrada' | 'saida') =>
        comarcas(d(`execucao_acordos_por_comarca_${modo}_NG`), d(`execucao_acordos_valor_por_comarca_${modo}_NG`))
    return {
        unidade: u,
        fechamentoPorSubfase: pontos(d('fechamento_acordo_por_subfase_NG')),
        valorFechamentoPorSubfase: pontos(d('valor_fechamento_acordo_por_subfase_NG')),
        totalEmExecucao: n('total_em_execucao_acordos_NG'),
        valorTotal: n('valor_total_em_execucao_acordos_NG'),
        entradas: n('total_entrada_execucao_acordos_periodo_NG'),
        valorEntradas: n('valor_entrada_execucao_acordos_periodo_NG'),
        pagos: n('total_saida_execucao_acordos_periodo_NG'),
        valorPagos: n('valor_saida_execucao_acordos_periodo_NG'),
        mediaTempo: n('media_tempo_execucao_acordos_NG'),
        medianaTempo: n('mediana_tempo_execucao_acordos_NG'),
        estoqueInicial: n('estoque_inicial_execucao_acordos_NG'),
        tre: n('tre_execucao_acordos_NG'),
        semValor: {
            total: n('total_valor_alcada_final_vazio_acordos_NG') ?? 0,
            processos: processosSemValor(s('total_valor_alcada_final_vazio_acordos_NG_detalhe')),
        },
        valorPorSubfase: pontos(d('valor_execucao_acordos_por_subfase_NG')),
        porSubfase: pontos(d('execucao_acordos_por_subfase_NG')),
        porSentenca: pontos(d('execucao_acordos_por_sentenca_NG')),
        porMateria: pontos(d('execucao_acordos_por_materia_NG')),
        porTipoAcao: pontos(d('execucao_acordos_por_tipo_acao_NG')),
        comarca: { total: comarca('total'), entrada: comarca('entrada'), saida: comarca('saida') },
        entradasPorMes: pontos(d('quantidade_entrada_execucao_acordos_por_mes_NG')),
        pagosPorMes: pontos(d('quantidade_saida_execucao_acordos_por_mes_NG')),
        valorEntradasPorMes: pontos(d('valor_entrada_execucao_acordos_por_mes_NG')),
        valorPagosPorMes: pontos(d('valor_saida_execucao_acordos_por_mes_NG')),
        listas: {
            entrada: processosLista(d('execucao_acordos_lista_entrada_NG')),
            saida: processosLista(d('execucao_acordos_lista_saida_NG')),
            total: processosLista(d('execucao_acordos_lista_total_NG')),
        },
        opcoes: {
            ufs: lista(s('execucao_acordos_uf_opcoes_NG')),
            comarcas: lista(s('execucao_acordos_comarca_opcoes_NG')),
            materias: lista(s('execucao_acordos_materia_opcoes_NG')),
            subfases: lista(s('execucao_acordos_subfase_opcoes_NG')),
        },
        setor: lerSetor(dados, 'acordos', u),
    }
}
