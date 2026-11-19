import type { EmendasResponse } from '../../pages/dashboards/emendas-manifestacoes/emendas.ts'
import { intermediariasFor } from './intermediarias.ts'

// Emendas e Manifestações fictícias (NG e LA), no formato da resposta da V2 (app/dashboards/emendas_manifestacoes.py).
// Mesma estrutura das Pendências Intermediárias fictícias, com os nomes deste dashboard, as atividades do setor
// (NG: MANIFESTAÇÃO; LA: INTERMEDIÁRIAS), a comissão por funcionário e, no NG, a UF e o comparativo.

const ATIVIDADES = {
    NG: ['ELABORAR DILAÇÃO', 'EMENDA À INICIAL', 'MANIFESTAÇÃO SOBRE CONTESTAÇÃO', 'ANÁLISE DE MANIFESTAÇÃO'],
    LA: ['MANIFESTAÇÃO (5D)', 'EMENDA À INICIAL', 'DILAÇÃO DE PRAZO', 'AVALIAR MANIFESTAÇÃO (INT)'],
}

export function emendasFor(unit: string): EmendasResponse {
    const base = intermediariasFor(unit)
    if (!('stats' in base)) return base
    const u = base.unidade === 'LA' ? 'LA' : 'NG' // o RJ segue as regras do NG
    const renomeia = (k: string) => k.replace('intermediarias', 'emendas_manifestacoes')
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(base)) {
        if (k === 'stats' || k.startsWith('dilacoes_')) continue
        out[renomeia(k)] = v
    }
    const atividades = ATIVIDADES[u]
    const porAtividade = atividades.map((name, i) => ({ name, value: [44, 31, 18, 9][i] }))
    out.emendas_manifestacoes_processos_por_atividade_NG = porAtividade
    out.emendas_manifestacoes_processos_por_atividade_por_prazo_NG = porAtividade.map((p) => ({
        ...p,
        value: p.value + 2,
    }))
    for (const lista of ['emendas_manifestacoes_atividades_lista_NG', 'emendas_manifestacoes_por_prazo_lista_NG']) {
        out[lista] = (out[lista] as Record<string, unknown>[]).map((t, i) => ({
            ...t,
            atividade: atividades[i % atividades.length],
            pessoa_setor: `${u === 'NG' ? 'MANIFESTAÇÃO' : 'INTERMEDIÁRIAS'} - ${atividades[i % atividades.length]}`,
            numero_processo: `0${String(600000 + i * 7919).padStart(6, '0')}${String(10 + i).slice(-2)}20268040001`,
        }))
    }
    const stats = Object.fromEntries(
        Object.entries(base.stats ?? {})
            .filter(([k]) => !k.startsWith('dilacoes_'))
            .map(([k, v]) => [renomeia(k), v]),
    )
    const pessoas = ['Ana Ribeiro', 'Bruno Lima', 'Carla Souza', 'Diego Prado']
    const agenda = [
        [96, 100],
        [88, 100],
        [79, 100],
        [99, 100],
    ]
    out.emendas_manifestacoes_comissionamento_por_funcionario_NG = pessoas.map((funcionario, i) => {
        const [fin, tot] = agenda[i]
        const pct = Math.round((fin / tot) * 1000) / 10
        const faixa = u === 'LA' ? (pct >= 97 ? 'faixa_2' : pct >= 85 ? 'faixa_1' : null) : null
        const elegivel = u === 'NG' || faixa !== null
        const vm = u === 'NG' ? 1 : faixa === 'faixa_2' ? 1.5 : faixa === 'faixa_1' ? 1 : 0
        const vd = u === 'NG' ? 0.5 : faixa === 'faixa_2' ? 0.5 : faixa === 'faixa_1' ? 0.25 : 0
        const qm = [62, 48, 35, 71][i]
        const qd = [6, 3, 9, 2][i]
        return {
            funcionario,
            agenda_finalizada: fin,
            agenda_total: tot,
            agenda_percentual: pct,
            elegivel,
            ...(faixa ? { faixa } : {}),
            qtd_manifestacao: qm,
            valor_manifestacao: vm,
            qtd_x_valor_manifestacao: qm * vm,
            qtd_dilacao: qd,
            valor_dilacao: vd,
            qtd_x_valor_dilacao: qd * vd,
            valor_comissao: qm * vm + qd * vd,
            ...(u === 'NG'
                ? {
                      resolvidos_por_uf: [
                          { uf: 'AM', qtd_manifestacao: qm - 5, qtd_dilacao: qd - 1, qtd_total: qm + qd - 6 },
                          { uf: 'PA', qtd_manifestacao: 5, qtd_dilacao: 1, qtd_total: 6 },
                      ],
                  }
                : {}),
        }
    })
    return {
        ...(out as Record<string, unknown>),
        meta: base.meta,
        unidade: base.unidade,
        stats: {
            ...stats,
            ...(u === 'NG'
                ? {
                      comparativo_qtd_manifestacoes_emendas_manifestacoes_NG: -12.4,
                      comparativo_qtd_dilacoes_emendas_manifestacoes_NG: 37.5,
                      emendas_manifestacoes_uf_opcoes_NG: ['AM', 'PA', 'PB'],
                  }
                : {}),
        },
    }
}
