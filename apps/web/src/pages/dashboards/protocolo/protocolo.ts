import type { Point } from '../../../types/index.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { nomesFuncionarios } from '../setor/setor.ts'

// O Protocolo do banco legado vem de três rotas da v1: /protocolo (NG) e /protocolo_RJ, com os mesmos nomes,
// e /protocolo_LA, com outros nomes (quase todos com _LA). Aqui as duas viram uma forma só, a que a página
// usa. Só lógica pura (testada em protocolo.test.ts).

export type LinhaComissao = { funcionario: string; qtd_protocolados: number; valor_comissao: number }

export type ProtocoloLegado = {
    la: boolean // veio da rota da LA (banco LA)
    protocolados: number | null
    represados: number | null // ainda no setor, sem protocolo (não depende do período)
    valorCausa: number | null
    ticket: number | null
    mediaTempo: number | null // em dias, como a API manda
    medianaTempo: number | null
    comparativo: {
        protocolados: number | null
        valorCausa: number | null
        ticket: number | null
        mediaTempo: number | null
        medianaTempo: number | null
    }
    // Só NG/RJ: a LA não separa o reajuizamento.
    reajuizamento: { protocolados: number | null; represados: number | null } | null
    // Só LA: entradas no setor no período e a taxa de saída (protocolados ÷ entradas), o medidor da v1.
    taxa: { valor: number | null; entradas: number | null } | null
    porMateria: Point[]
    naoPorMateria: Point[]
    porFuncionario: Point[]
    naoPorFuncionario: Point[]
    mediaPorFuncionario: Point[]
    valorPorFuncionario: Point[]
    porSistema: Point[]
    porDia: Point[]
    porMes: Point[] // histórico todo (a API manda sem o período)
    naoPorMes: Point[]
    funcionarios: string[]
    comissao: LinhaComissao[]
}

type Bruto = V1GenericoResponse & Record<string, unknown>

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

function pontos(v: unknown): Point[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((p): p is { name: unknown; value: unknown } => typeof p === 'object' && p !== null)
        .map((p) => ({ name: String(p.name ?? ''), value: numero(p.value) ?? 0 }))
}

// O primeiro campo que veio (a rota da NG às vezes manda o ticket com outro nome).
const primeiro = (...vs: (number | null)[]) => vs.find((v) => v !== null) ?? null

export function lerProtocolo(data: V1GenericoResponse): ProtocoloLegado {
    const d = data as Bruto
    const s = data.stats ?? {}
    const n = (campo: string) => numero(s[campo])
    // Pelo nome da rota. Não dá para olhar se o campo _LA existe: a resposta da v1 traz todos os campos de
    // todas as rotas (os das outras vêm null).
    const la = data.dashboard ? data.dashboard === 'protocolo_LA' : n('protocolos_resolvidos_LA') !== null

    if (la) {
        return {
            la,
            protocolados: n('protocolos_resolvidos_LA'),
            represados: n('protocolos_represados_LA'),
            valorCausa: n('valor_causa_protocolado_LA'),
            ticket: n('ticket_medio_protocolos_resolvidos_LA'),
            mediaTempo: n('media_tempo_protocolo_LA'),
            medianaTempo: n('mediana_tempo_protocolo_LA'),
            comparativo: {
                protocolados: n('comparativo_protocolos_resolvidos_LA'),
                valorCausa: n('comparativo_valor_causa_protocolado_LA'),
                ticket: n('comparativo_ticket_medio_protocolos_resolvidos_LA'),
                mediaTempo: n('comparativo_tempo_medio_protocolos_resolvidos_LA'),
                medianaTempo: n('comparativo_mediana_tempo_protocolos_resolvidos_LA'),
            },
            reajuizamento: null,
            taxa: { valor: n('taxa_protocolados_LA'), entradas: n('entradas_protocolo_LA') },
            porMateria: pontos(d.protocolados_por_materia_LA),
            naoPorMateria: pontos(d.represados_protocolo_por_materia_LA),
            porFuncionario: pontos(d.protocololados_por_funcionario_LA), // sic: o nome é esse na v1
            naoPorFuncionario: pontos(d.represados_protocolo_por_funcionario_LA),
            mediaPorFuncionario: pontos(d.media_protocolados_por_funcionario_LA),
            valorPorFuncionario: pontos(d.valor_causa_protocolo_por_funcionario_LA),
            porSistema: pontos(d.protocolados_por_sistema_LA),
            porDia: pontos(d.protocolados_por_dia_LA),
            porMes: pontos(d.protocolados_por_mes_LA),
            naoPorMes: pontos(d.represados_por_mes_LA),
            funcionarios: nomes(d.funcionarios_protocolo_LA),
            comissao: linhasComissao(d.comissionamento_protocolo_LA_por_funcionario),
        }
    }

    const protocolados = n('protocolos_resolvidos')
    const valorCausa = n('valor_causa_protocolo_novo')
    return {
        la,
        protocolados,
        represados: n('nao_protocolados'),
        valorCausa,
        // Igual à v1: o ticket do servidor; sem ele, valor de causa ÷ protocolados.
        ticket: primeiro(
            n('ticket_medio_protocolos_resolvidos'),
            n('ticket_medio_protocolado'),
            protocolados && valorCausa !== null ? valorCausa / protocolados : null,
        ),
        mediaTempo: n('media_tempo_protocolado'),
        medianaTempo: n('mediana_tempo_protocolado'),
        comparativo: {
            protocolados: n('comparativo_protocolos_resolvidos'),
            valorCausa: n('comparativo_valor_causa_protocolo'),
            ticket: primeiro(
                n('comparativo_ticket_medio_protocolos_resolvidos'),
                n('comparativo_ticket_medio_protocolado'),
            ),
            mediaTempo: n('comparativo_tempo_medio_protocolos_resolvidos'),
            medianaTempo: null, // a rota da NG não manda
        },
        reajuizamento: {
            protocolados: n('protocolados_de_reajuizamento'),
            represados: n('nao_protocolados_de_reajuizamento'),
        },
        taxa: null,
        porMateria: pontos(d.protocolados_por_materia),
        naoPorMateria: pontos(d.nao_protocolados_por_materia),
        porFuncionario: pontos(d.protocolados_por_funcionario),
        naoPorFuncionario: pontos(d.nao_protocolados_por_funcionario),
        mediaPorFuncionario: pontos(d.media_protocolados_por_funcionario),
        valorPorFuncionario: pontos(d.valor_causa_protocolo_novo_por_funcionario),
        porSistema: pontos(d.protocolados_por_sistema),
        porDia: pontos(d.protocolados_por_dia),
        porMes: pontos(d.protocolados_por_mes),
        naoPorMes: pontos(d.nao_protocolados_por_mes),
        funcionarios: nomes(d.funcionarios_protocolo),
        comissao: linhasComissao(d.comissionamento_protocolo_por_funcionario),
    }
}

function nomes(v: unknown): string[] {
    return Array.isArray(v) ? v.map((x) => String(x).trim()).filter(Boolean) : []
}

function linhasComissao(v: unknown): LinhaComissao[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((r): r is Record<string, unknown> => typeof r === 'object' && r !== null)
        .map((r) => ({
            funcionario: String(r.funcionario ?? ''),
            qtd_protocolados: numero(r.qtd_protocolados) ?? 0,
            valor_comissao: numero(r.valor_comissao) ?? 0,
        }))
}

// As opções dos filtros, do que veio na resposta (a v1 também montava assim): funcionários do setor,
// matérias protocoladas ou na fila e os sistemas de protocolo.
export function opcoesProtocolo(p: ProtocoloLegado) {
    const unicos = (xs: string[]) =>
        [...new Set(xs.map((x) => x.trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
    return {
        funcionarios: nomesFuncionarios(
            [...p.porFuncionario, ...p.naoPorFuncionario, ...p.mediaPorFuncionario].map((x) => x.name),
            p.funcionarios,
        ),
        materias: unicos([...p.porMateria, ...p.naoPorMateria].map((x) => x.name)),
        sistemas: unicos(p.porSistema.map((x) => x.name)),
    }
}
