import type { ProtocoloResponse } from '../types.ts'
import { funcionarios, metaFor, unitScale } from './helpers.ts'

// Números-base (NG). As outras unidades são proporcionais (ver unitScale).
const PROTOCOLADOS_POR_FUNC = [312, 268, 231, 198, 161, 114]
const REPRESADOS_POR_FUNC = [21, 18, 17, 15, 14, 11]

// Resposta fictícia do Protocolo para uma unidade.
export function protocoloFor(unit: string): ProtocoloResponse {
    const { count, money, series, named } = unitScale(unit)
    const porFunc = PROTOCOLADOS_POR_FUNC.map(count)

    return {
        meta: metaFor(unit),
        stats: {
            protocolados_total: { total: count(1284), comparativo: 8.2 },
            valor_causa_protocolado: { total: money(18432750.4), comparativo: 5.1 },
            ticket_medio_protocolado: { total: 14355.72, comparativo: -2.8 },
            media_tempo_protocolado: 2.4,
            mediana_tempo_protocolado: 1.6,
            comparativo_tempo_medio_protocolado: -12.0,
            comparativo_mediana_tempo_protocolado: -6.5,
            represados: count(96),
            devolvido_peticionamento: count(41),
            devolvido_org_doc: count(17),
            devolvido_pendencia: count(23),
        },
        protocolados_por_dia: series(58, 14),
        protocolados_por_materia: named([
            ['Bancário - empréstimo', 412],
            ['Consumidor - telefonia', 287],
            ['Aéreo - atraso de voo', 214],
            ['Previdenciário', 163],
            ['Bancário - cartão', 121],
            ['Outras', 87],
        ]),
        protocolados_por_funcionario: funcionarios.map((name, i) => ({ name, value: porFunc[i] })),
        represados_por_funcionario: named(funcionarios.map((name, i): [string, number] => [name, REPRESADOS_POR_FUNC[i]])),
        comissionamento_por_funcionario: funcionarios.map((name, i) => ({
            funcionario: name,
            qtd_protocolados: porFunc[i],
            valor_comissao: porFunc[i] * 1.0,
        })),
    }
}