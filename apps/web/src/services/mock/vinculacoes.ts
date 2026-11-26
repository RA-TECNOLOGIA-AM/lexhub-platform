import type {
    Fluxo,
    Problema,
    StatusVinculacao,
    Vinculacao,
    VinculacoesResponse,
} from '../../pages/dashboards/configuracoes-vinculacoes/vinculacoes.ts'
import { metaFor } from './helpers.ts'

// Vinculações fictícias (formato da rota /admin/configuracoes-vinculacoes da v1): setores e atividades inventados,
// com os casos que a página mostra (OK, falta configurar, erro, inativa, gatilho herdado, destino quebrado).
// Cada unidade vê só o próprio escritório, como a API.

const ESCRITORIO: Record<string, { id: number; nome: string }> = {
    NG: { id: 20, nome: 'NG' },
    LA_AM: { id: 21, nome: 'LAADV AM' },
    LA_RJ: { id: 27, nome: 'LAADV RJ' },
}

const SETORES: Record<string, string[]> = {
    EXECUÇÃO: ['CÁLCULO', 'CONFECÇÃO CS', 'ALVARÁ', 'DILIGÊNCIA', 'PAGAMENTO'],
    RECURSOS: ['ANALISAR SENTENÇA', 'ELABORAR RECURSO', 'CONTRARRAZÕES', 'EMBARGOS'],
    INTERMEDIÁRIAS: ['EMENDA', 'MANIFESTAÇÃO', 'DILAÇÃO DE PRAZO'],
    PROTOCOLO: ['PROTOCOLAR INICIAL', 'CONFERIR DISTRIBUIÇÃO'],
    CONTROLADORIA: ['CONFERIR PRAZO', 'REVISAR AGENDA', 'ARQUIVAR'],
}

const encerra: Fluxo = { MODO: 'encerra', MODO_LABEL: 'Apenas encerrar', DESTINOS: [] }

const encaminha = (texto: string, id: number, quebrado = false): Fluxo => ({
    MODO: 'encaminha',
    MODO_LABEL: 'Encaminhar',
    DESTINOS: [
        {
            ID_VINCULACAO: id,
            MOTIVO: null,
            QTD_DIAS: 1,
            SITUACAO: quebrado ? 'inativa' : 'ok',
            TEXTO: quebrado ? `${texto} (INATIVA) (1d)` : `${texto} (1d)`,
        },
    ],
})

const comMotivo = (destinos: [string, string, number | null][]): Fluxo => ({
    MODO: 'encaminha_com_motivo',
    MODO_LABEL: 'Encaminhar com motivo',
    DESTINOS: destinos.map(([motivo, texto, id]) => ({
        ID_VINCULACAO: id,
        MOTIVO: motivo,
        QTD_DIAS: id === null ? null : 2,
        SITUACAO: id === null ? 'sem_destino' : 'ok',
        TEXTO: id === null ? `${motivo} → Apenas encerra` : `${motivo} → ${texto} (2d)`,
    })),
})

const P = {
    camposObrigatorios: {
        NIVEL: 'incompleta',
        TIPO: 'Nenhum conjunto de campos obrigatórios vinculado',
        MENSAGEM: 'Nenhum conjunto de campos obrigatórios vinculado',
    },
    regraNc: {
        NIVEL: 'incompleta',
        TIPO: 'Regra de NÃO CUMPRIDO não definida (motivo/anexo/sem exigência)',
        MENSAGEM: 'Regra de NÃO CUMPRIDO não definida (motivo/anexo/sem exigência)',
    },
    destinoInativo: {
        NIVEL: 'erro',
        TIPO: 'Encaminha para vinculação inativa',
        MENSAGEM: 'CUMPRIDO encaminha para vinculação INATIVA: EXECUÇÃO · ARQUIVAR (INATIVA) (1d)',
    },
    herdado: {
        NIVEL: 'erro',
        TIPO: 'Não cumprido herda o gatilho de encerramento do cumprido',
        MENSAGEM:
            'Ao encerrar como NÃO CUMPRIDO o processo vai para a fase/subfase do gatilho de encerramento (EXECUÇÃO / AG. PAGAMENTO) — não há opção ativa de Não Cumprido na aba Trigger de Encerramento',
    },
} satisfies Record<string, Problema>

function resumo(f: Fluxo) {
    if (f.DESTINOS.length === 0) return f.MODO_LABEL
    return `${f.MODO_LABEL}: ${f.DESTINOS.map((d) => d.TEXTO).join('; ')}`
}

export function vinculacoesFor(unit: string): VinculacoesResponse {
    const meta = metaFor(unit, 'LexFlow')
    const escritorio = ESCRITORIO[unit]
    if (!escritorio) return { meta }
    const rows: Vinculacao[] = []
    let id = escritorio.id * 100
    let i = 0
    for (const [setor, atividades] of Object.entries(SETORES)) {
        for (const atividade of atividades) {
            id += 1
            i += 1
            const ativa = i % 11 !== 0
            const problemas: Problema[] = []
            let cumprido: Fluxo = encerra
            let naoCumprido: Fluxo = encerra
            let herdado = false
            if (i % 4 === 0) cumprido = encaminha('CONTROLADORIA · CONFERIR PRAZO', escritorio.id * 100 + 15)
            if (i % 5 === 0) {
                naoCumprido = comMotivo([
                    ['Falta documento', 'INTERMEDIÁRIAS · EMENDA', escritorio.id * 100 + 10],
                    ['Cliente desistiu', '', null],
                ])
            }
            if (i % 6 === 0) problemas.push(P.camposObrigatorios)
            if (i % 9 === 0) problemas.push(P.regraNc)
            if (i % 7 === 0) {
                cumprido = encaminha('CONTROLADORIA · ARQUIVAR', escritorio.id * 100 + 17, true)
                problemas.push(P.destinoInativo)
            }
            if (i % 8 === 0) {
                herdado = true
                problemas.push(P.herdado)
            }
            const efetivos = ativa ? problemas : []
            const erros = efetivos.filter((p) => p.NIVEL === 'erro').length
            const status: StatusVinculacao = !ativa
                ? 'inativa'
                : erros > 0
                  ? 'erro'
                  : efetivos.length > 0
                    ? 'incompleta'
                    : 'ok'
            const faseConclusao = setor === 'EXECUÇÃO' ? 'EXECUÇÃO' : null
            const subfaseConclusao = setor === 'EXECUÇÃO' ? 'AG. PAGAMENTO' : null
            rows.push({
                ID_VINCULACAO: id,
                ID_ESCRITORIO_ASSINANTE: escritorio.id,
                ESCRITORIO: escritorio.nome,
                VINCULACAO_ATIVA: ativa,
                SETOR: setor,
                ATIVIDADE: atividade,
                VINCULACAO: `${setor} · ${atividade}`,
                STATUS: status,
                TEM_CONFIGURACAO: true,
                CONFIGURACAO_ATIVA: true,
                FASE_AGENDAMENTO: i % 3 === 0 ? setor : null,
                SUBFASE_AGENDAMENTO: i % 3 === 0 ? `AG. ${atividade}` : null,
                SITUACAO_AGENDAMENTO: null,
                GATILHO_AGENDAMENTO_ATIVO: i % 3 === 0,
                GATILHO_ENCERRAMENTO_CUMPRIDO: {
                    ORIGEM: faseConclusao || herdado ? 'flat' : 'nenhum',
                    ATIVO: !!faseConclusao || herdado,
                    FASE: faseConclusao ?? (herdado ? 'EXECUÇÃO' : null),
                    SUBFASE: subfaseConclusao ?? (herdado ? 'AG. PAGAMENTO' : null),
                    QTD_SLOTS_ATIVOS: 0,
                },
                GATILHO_ENCERRAMENTO_NAO_CUMPRIDO: herdado
                    ? { ORIGEM: 'flat', ATIVO: true, FASE: 'EXECUÇÃO', SUBFASE: 'AG. PAGAMENTO', QTD_SLOTS_ATIVOS: 0 }
                    : { ORIGEM: 'nenhum', ATIVO: false, FASE: null, SUBFASE: null, QTD_SLOTS_ATIVOS: 0 },
                GATILHOS_CONCLUSAO_POR_ENCAMINHAMENTO: [],
                CAMPOS_OBRIGATORIOS: i % 6 === 0 ? [] : ['numero_processo', 'parecer', 'valor'],
                QTD_CAMPOS_OBRIGATORIOS: i % 6 === 0 ? 0 : 3,
                REGRA_CUMPRIDO_EXIGE_ANEXO: i % 2 === 0,
                REGRA_CUMPRIDO_EXIGE_PARECER: false,
                REGRA_CUMPRIDO_SEM_EXIGENCIA: i % 2 !== 0,
                REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO: i % 9 !== 0,
                REGRA_NAO_CUMPRIDO_EXIGE_ANEXO: false,
                REGRA_NAO_CUMPRIDO_EXIGE_MOTIVO_ANEXO: false,
                REGRA_NAO_CUMPRIDO_NENHUMA_EXIGENCIA: false,
                FLUXO_CUMPRIDO: cumprido,
                FLUXO_NAO_CUMPRIDO: naoCumprido,
                PROXIMA_ATIVIDADE_CUMPRIDO: resumo(cumprido),
                PROXIMA_ATIVIDADE_NAO_CUMPRIDO: resumo(naoCumprido),
                QTD_PROBLEMAS: efetivos.length,
                QTD_ERROS: erros,
                PROBLEMAS: efetivos.map((p) => p.MENSAGEM),
                PROBLEMAS_DETALHE: efetivos,
                OUTRAS_CONFIGURACOES:
                    i === 2
                        ? [
                              {
                                  CAMPO: 'herdar_prazo_fatal',
                                  LABEL: 'Herdar prazo fatal',
                                  VALOR: 'Sim',
                                  CONHECIDO: true,
                              },
                              {
                                  CAMPO: 'prioridade_fila',
                                  LABEL: 'Prioridade fila',
                                  VALOR: 'alta',
                                  CONHECIDO: false,
                              },
                          ]
                        : [],
                CONFIGURACAO_ATUALIZADO_EM: '2026-11-20T14:32:00-04:00',
            })
        }
    }
    const ordem: Record<StatusVinculacao, number> = { erro: 0, incompleta: 1, ok: 2, inativa: 3 }
    rows.sort((a, b) => ordem[a.STATUS] - ordem[b.STATUS] || b.QTD_PROBLEMAS - a.QTD_PROBLEMAS)
    return {
        meta,
        total: rows.length,
        total_com_problemas: rows.filter((r) => r.QTD_PROBLEMAS > 0).length,
        campos_nao_reconhecidos: ['prioridade_fila'],
        rows,
    }
}
