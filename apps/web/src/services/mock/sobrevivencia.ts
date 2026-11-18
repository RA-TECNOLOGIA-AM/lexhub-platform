import type { SobrevivenciaResponse } from '../../pages/dashboards/sobrevivencia-processual/sobrevivencia.ts'
import { metaFor } from './helpers.ts'

// Coorte fictícia da Sobrevivência Processual (formato colunar da rota da v1 /tcc_sobrevivencia_processual): 3.000
// processos inventados, gerados por uma sequência pseudoaleatória fixa (o mesmo resultado sempre). NG e LA/AM, cada um
// só com o próprio escritório (como a API).

const N = 3000 // por escritório
const TIPO_ACAO = ['PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL', 'PROCEDIMENTO COMUM CÍVEL', 'AGRAVO INTERNO']
const MATERIA = ['CESTA', 'RMC', 'MORA', 'ANP', 'GASTO_C_CRED', 'PARC_CRED_PESS', 'ESPECIFICA']
const COMARCA = ['MANAUS', 'ITACOATIARA', 'PARINTINS', 'MANACAPURU', 'TEFÉ', 'COARI', 'HUMAITÁ']
const COMPETENCIA = ['Juizado Especial Cível', 'Vara Cível', 'Turma Recursal', 'Câmara Cível']
const FASE = ['EXECUÇÃO', 'RECURSAL', 'INICIAL', 'ARQUIVADO']
const SUBFASE = ['AG. SENTENÇA', 'AG. JULGAMENTO', 'AG. PAGAMENTO', 'ARQUIVADO PROCEDENTE', 'AG. CONTRARRAZÕES']
const JUIZ = ['Juiz Exemplo Um', 'Juíza Exemplo Dois', 'Juiz Exemplo Três', 'Juíza Exemplo Quatro']
const RELATOR = ['Desembargador Alfa', 'Desembargadora Beta', 'Desembargador Gama']

export function sobrevivenciaFor(unit: string): SobrevivenciaResponse {
    const meta = metaFor(unit, 'LexFlow')
    const escritorio = ({ NG: 'NG', LA: 'LA', LA_AM: 'LA' } as Record<string, string>)[unit]
    if (!escritorio) return { meta }
    let semente = escritorio === 'NG' ? 20261118 : 20261119
    const aleatorio = () => {
        semente = (semente * 1103515245 + 12345) % 2147483648
        return semente / 2147483648
    }
    const escolhe = (n: number, peso = 1.6) => Math.min(n - 1, Math.floor(n * aleatorio() ** peso))
    const col = (): (number | null)[] => []
    const r = {
        escritorio: col(),
        duracao_e1: col(),
        evento_e1: col(),
        tipo_evento_e1: col(),
        tipo_acordo: col(),
        duracao_acordo: col(),
        tipo_acao: col(),
        materia: col(),
        comarca: col(),
        competencia: col(),
        fase: col(),
        subfase: col(),
        juiz_1g: col(),
        relator_2g: col(),
        tipo_evento_e2: col(),
        duracao_e2: col(),
        evento_sentenca: col(),
        sentenca_favoravel: col(),
        sentenca_improcedente: col(),
        sentenca_extinta: col(),
        duracao_sentenca: col(),
        evento_acordao: col(),
        acordao_favoravel: col(),
        acordao_improcedente: col(),
        acordao_extinto: col(),
        duracao_acordao: col(),
    }
    for (let i = 0; i < N; i++) {
        const materia = escolhe(MATERIA.length)
        const lento = 1 + materia * 0.12
        const evento = aleatorio() < 0.78 ? 1 : 0
        const tipo = evento === 0 ? 0 : aleatorio() < 0.18 ? 1 : aleatorio() < 0.55 ? 2 : 3 // censurado, acordo, favorável, sem proveito
        const durE1 = Math.round((120 + 700 * aleatorio() ** 1.4) * lento)
        const temSentenca = tipo >= 2 || (tipo === 0 && aleatorio() < 0.2)
        const durSent = temSentenca ? Math.round(durE1 * (0.7 + 0.3 * aleatorio())) : durE1
        const temAcordao = tipo >= 2 && aleatorio() < 0.45
        const elegivel = tipo === 1 || tipo === 2
        const pago = elegivel && aleatorio() < 0.62
        r.escritorio.push(0)
        r.duracao_e1.push(durE1)
        r.evento_e1.push(evento)
        r.tipo_evento_e1.push(tipo)
        r.tipo_acordo.push(tipo === 1 ? 0 : aleatorio() < 0.05 ? 1 : null)
        r.duracao_acordo.push(tipo === 1 ? durE1 : null)
        r.tipo_acao.push(escolhe(TIPO_ACAO.length, 2))
        r.materia.push(materia)
        r.comarca.push(escolhe(COMARCA.length, 2.2))
        r.competencia.push(escolhe(COMPETENCIA.length))
        r.fase.push(escolhe(FASE.length))
        r.subfase.push(escolhe(SUBFASE.length))
        r.juiz_1g.push(temSentenca ? escolhe(JUIZ.length) : null)
        r.relator_2g.push(temAcordao ? escolhe(RELATOR.length) : null)
        r.tipo_evento_e2.push(elegivel ? (pago ? 0 : 1) : null)
        r.duracao_e2.push(elegivel ? Math.round(60 + 420 * aleatorio() ** 1.3) : null)
        r.evento_sentenca.push(temSentenca ? 1 : 0)
        r.sentenca_favoravel.push(temSentenca && tipo === 2 ? 1 : 0)
        r.sentenca_improcedente.push(temSentenca && tipo === 3 && aleatorio() < 0.7 ? 1 : 0)
        r.sentenca_extinta.push(temSentenca && tipo === 3 && aleatorio() < 0.2 ? 1 : 0)
        r.duracao_sentenca.push(durSent)
        r.evento_acordao.push(temAcordao ? 1 : 0)
        r.acordao_favoravel.push(temAcordao && aleatorio() < 0.5 ? 1 : 0)
        r.acordao_improcedente.push(temAcordao && aleatorio() < 0.3 ? 1 : 0)
        r.acordao_extinto.push(temAcordao && aleatorio() < 0.08 ? 1 : 0)
        r.duracao_acordao.push(temAcordao ? durE1 : Math.round(durE1 * 0.9))
    }
    return {
        meta,
        gerado_em: '2026-11-18',
        escritorio_dict: [escritorio],
        tipo_acao_dict: TIPO_ACAO,
        materia_dict: MATERIA,
        comarca_dict: COMARCA,
        competencia_dict: COMPETENCIA,
        fase_dict: FASE,
        subfase_dict: SUBFASE,
        juiz_1g_dict: JUIZ,
        relator_2g_dict: RELATOR,
        tipo_evento_e1_dict: [
            'CENSURADO',
            'ACORDO',
            'MERITO_FAVORAVEL_COM_PROVEITO',
            'MERITO_SEM_PROVEITO_OU_DESFAVORAVEL',
        ],
        tipo_evento_e2_dict: ['PAGO', 'CENSURADO_PAGAMENTO'],
        tipo_acordo_dict: ['PRE_SENTENCA', 'POS_SENTENCA'],
        registros: r,
    }
}
