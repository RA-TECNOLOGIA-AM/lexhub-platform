import type { PendenciasResponse } from '../types.ts'
import { funcionarios, metaFor, unitScale } from './helpers.ts'

// Números-base (NG) da equipe de Pendências (os 5 primeiros funcionários).
const EQUIPE = funcionarios.slice(0, 5)
const MEDIA_RESOLVIDAS_POR_FUNC = [9.4, 8.1, 7.6, 6.2, 5.0] // média por pessoa: não escala
const TAXA_RESOLVIDO = [98.1, 96.2, 91.0, 86.4, 79.5]
const TAXA_CANCELAMENTO = [1.2, 2.4, 3.1, 6.0, 4.4]
const QTD_RESOLVIDO = [182, 157, 141, 102, 73]

// Resposta fictícia de Pendências para uma unidade.
export function pendenciasFor(unit: string): PendenciasResponse {
    const { count, series, named } = unitScale(unit)

    return {
        meta: metaFor(unit),
        stats: {
            pendencias_total: count(742),
            pendencias_resolvidas: count(655),
            pendencias_canceladas: count(19),
            pendencias_taxa_resolvidos: 88.27,
            pendencias_taxa_nao_resolvidos: 9.16,
            pendencias_taxa_canceladas: 2.56,
            media_tempo_resolvidos_pendencia: 3.1,
            mediana_tempo_resolvidos_pendencia: 2.0,
            comparativo_pendencias_resolvidas: 6.4,
            comparativo_tempo_medio_resolvidos_pendencia: -9.3,
            pendencias_nao_resolvidas: count(68),
            pendencias_nao_resolvidas_com_atraso: count(23),
            pendencias_triagem: count(12),
        },
        pendencias_resolvidas_por_dia: series(30, 8),
        pendencias_nao_resolvidas_por_origem: named([
            ['Organização de documentos', 29],
            ['Peticionamento', 21],
            ['Protocolo', 12],
            ['Triagem', 6],
        ]),
        media_pendencias_resolvidas_por_funcionario: EQUIPE.map((name, i) => ({
            name,
            value: MEDIA_RESOLVIDAS_POR_FUNC[i],
        })),
        comissionamento_pendencias_por_funcionario: EQUIPE.map((funcionario, i) => {
            const tr = TAXA_RESOLVIDO[i]
            const tc = TAXA_CANCELAMENTO[i]
            const q = count(QTD_RESOLVIDO[i])
            // Regra da v1: R$ 3 por resolvida com taxa >= 97% e cancelamento < 5%; R$ 1 com taxa >= 85%.
            const valor = tr >= 97 && tc < 5 ? 3 : tr >= 85 ? 1 : 0
            return {
                funcionario,
                taxa_resolvido: tr,
                taxa_cancelamento: tc,
                qtd_resolvido: q,
                valor,
                qtd_x_valor: q * valor,
                comissao: q * valor,
            }
        }),
    }
}