import type { Point } from '../../../types/index.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { nomesFuncionarios } from '../setor/setor.ts'

// O Peticionamento do banco legado vem de três rotas da v1: /peticionamento (NG) e /peticionamento_RJ, com os
// mesmos nomes, e /peticionamento_LA, com outros (quase todos "confeccionados" e com _LA). Aqui as duas viram
// a forma que a página usa. Só lógica pura (testada em peticionamento.test.ts).

// Uma linha do PDF de comissão (as colunas da v1: taxa, massa, específica e o total).
export type LinhaComissaoPet = {
    funcionario: string
    taxa_resolvidos: number | null
    qtd_acoes_massa: number
    valor_acoes_massa: number
    qtd_x_valor_massa: number
    qtd_acoes_especificas: number
    valor_acoes_especificas: number
    qtd_x_valor_especificas: number
    valor_comissao: number
}

export type PeticionamentoLegado = {
    la: boolean // veio da rota da LA (banco LA)
    total: number | null // peticionados no período (manuais + automáticos)
    manuais: number | null
    automaticos: number | null
    revisao: number | null // em revisão agora (não depende do período); a LA não tem
    naoPeticionados: number | null // na fila agora (não depende do período)
    valor: number | null
    ticket: number | null
    mediaTempo: number | null // em dias, como a API manda
    medianaTempo: number | null
    // Só NG/RJ: a LA não separa o reajuizamento.
    reajuizamento: { resolvidos: number | null; naoResolvidos: number | null } | null
    // Só LA: dos que entraram vindos do Protocolo no período, quantos voltaram para ele (o 3º medidor da v1).
    retornoProtocolo: { taxa: number | null; retornos: number | null; entradas: number | null } | null
    taxas: { resolvidos: number | null; naoResolvidos: number | null } // % do total (peticionados + fila)
    comparativo: {
        total: number | null
        manuais: number | null
        automaticos: number | null
        valor: number | null
        ticket: number | null
        mediaTempo: number | null
        medianaTempo: number | null
        reajResolvidos: number | null
        reajNaoResolvidos: number | null
    }
    porMateria: Point[]
    naoPorMateria: Point[]
    porFuncionario: Point[]
    naoPorFuncionario: Point[]
    mediaPorFuncionario: Point[]
    valorPorFuncionario: Point[]
    porDia: Point[]
    porMes: Point[] // histórico todo (a API manda sem o período)
    naoPorMes: Point[]
    funcionarios: string[]
    comissao: LinhaComissaoPet[]
}

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

function pontos(v: unknown): Point[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((p): p is { name: unknown; value: unknown } => typeof p === 'object' && p !== null)
        .map((p) => ({ name: String(p.name ?? ''), value: numero(p.value) ?? 0 }))
}

function linhasComissao(v: unknown): LinhaComissaoPet[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((r): r is Record<string, unknown> => typeof r === 'object' && r !== null)
        .map((r) => ({
            funcionario: String(r.funcionario ?? ''),
            taxa_resolvidos: numero(r.taxa_resolvidos),
            qtd_acoes_massa: numero(r.qtd_acoes_massa) ?? 0,
            valor_acoes_massa: numero(r.valor_acoes_massa) ?? 0,
            qtd_x_valor_massa: numero(r.qtd_x_valor_massa) ?? 0,
            qtd_acoes_especificas: numero(r.qtd_acoes_especificas) ?? 0,
            valor_acoes_especificas: numero(r.valor_acoes_especificas) ?? 0,
            qtd_x_valor_especificas: numero(r.qtd_x_valor_especificas) ?? 0,
            valor_comissao: numero(r.valor_comissao) ?? 0,
        }))
}

export function lerPeticionamento(data: V1GenericoResponse): PeticionamentoLegado {
    const d = data as V1GenericoResponse & Record<string, unknown>
    const s = data.stats ?? {}
    const n = (campo: string) => numero(s[campo])
    // Pelo nome da rota: a resposta da v1 traz os campos de todas as rotas (os das outras vêm null).
    const la = data.dashboard ? data.dashboard === 'peticionamento_LA' : n('total_confeccionados_LA') !== null
    if (la) return lerLA(d, n)
    return {
        la,
        total: n('total_peticionados'),
        manuais: n('peticionados_manualmente'),
        automaticos: n('peticionados_automaticamente'),
        revisao: n('processos_em_revisao'),
        naoPeticionados: n('nao_peticionados'),
        valor: n('valor_causa_confeccionado'),
        ticket: n('ticket_medio_confeccionado'),
        mediaTempo: n('media_tempo_peticionado'),
        medianaTempo: n('mediana_tempo_peticionado'),
        reajuizamento: {
            resolvidos: n('resolvidos_reajuizamento_pet'),
            naoResolvidos: n('nao_resolvidos_reajuizamento'),
        },
        retornoProtocolo: null,
        taxas: {
            resolvidos: n('peticionamento_taxa_resolvidos'),
            naoResolvidos: n('peticionamento_taxa_nao_resolvidos'),
        },
        comparativo: {
            total: n('comparativo_peticionados'),
            manuais: n('comparativo_peticionados_manualmente'),
            automaticos: n('comparativo_peticionados_automaticamente'),
            valor: n('comparativo_valor_causa_confeccionado'),
            ticket: n('comparativo_ticket_medio_confeccionado'),
            mediaTempo: n('comparativo_tempo_medio_peticionado'),
            medianaTempo: n('comparativo_mediana_tempo_pet'),
            reajResolvidos: n('comparativo_peticionados_reajuizamento'),
            reajNaoResolvidos: n('comparativo_nao_peticionados_reajuizamento'),
        },
        porMateria: pontos(d.peticionados_por_materia),
        naoPorMateria: pontos(d.nao_peticionados_por_materia),
        porFuncionario: pontos(d.peticionados_por_funcionario),
        naoPorFuncionario: pontos(d.nao_peticionados_por_funcionario),
        mediaPorFuncionario: pontos(d.media_peticionado_por_funcionario),
        valorPorFuncionario: pontos(d.valor_peticionado_por_funcionario),
        porDia: pontos(d.peticionados_por_dia),
        porMes: pontos(d.peticionados_por_mes),
        naoPorMes: pontos(d.nao_peticionados_por_mes),
        funcionarios: nomes(d.funcionarios_peticionamento),
        comissao: linhasComissao(d.comissionamento_peticionamento_por_funcionario),
    }
}

// A rota /peticionamento_LA: "confeccionados" no lugar de "peticionados", sem revisão nem reajuizamento e com
// a taxa de retorno ao Protocolo.
function lerLA(d: Record<string, unknown>, n: (campo: string) => number | null): PeticionamentoLegado {
    return {
        la: true,
        total: n('total_confeccionados_LA'),
        manuais: n('confeccionados_manualmente_LA'),
        automaticos: n('confeccionados_automaticamente_LA'),
        revisao: null,
        naoPeticionados: n('nao_confeccionados_LA'),
        valor: n('valor_causa_confeccionado_LA'),
        ticket: n('ticket_medio_confeccionado_LA'),
        mediaTempo: n('tempo_medio_confeccao_LA'),
        medianaTempo: n('mediana_tempo_confeccao_LA'),
        reajuizamento: null,
        retornoProtocolo: {
            taxa: n('peticionamento_taxa_retorno_protocolo_LA'),
            retornos: n('peticionamento_qtd_retorno_protocolo_LA'),
            entradas: n('peticionamento_qtd_entrada_protocolo_LA'),
        },
        taxas: {
            resolvidos: n('peticionamento_taxa_resolvidos_LA'),
            naoResolvidos: n('peticionamento_taxa_nao_resolvidos_LA'),
        },
        comparativo: {
            total: n('comparativo_confeccionados_LA'),
            manuais: n('comparativo_confeccionados_manualmente_LA'),
            automaticos: n('comparativo_confeccionados_automaticamente_LA'),
            valor: n('comparativo_valor_causa_confeccionado_LA'),
            ticket: n('comparativo_ticket_medio_confeccionado_LA'),
            mediaTempo: n('comparativo_tempo_medio_confeccionado_LA'),
            medianaTempo: n('comparativo_mediana_tempo_confeccionado_LA'),
            reajResolvidos: null,
            reajNaoResolvidos: null,
        },
        porMateria: pontos(d.confeccionados_por_materia_LA),
        naoPorMateria: pontos(d.nao_confeccionados_por_materia_LA),
        porFuncionario: pontos(d.confeccionados_por_funcionario_LA),
        naoPorFuncionario: pontos(d.nao_confeccionados_por_funcionario_LA),
        mediaPorFuncionario: pontos(d.media_confeccionado_por_funcionario_LA),
        valorPorFuncionario: pontos(d.valor_confeccionado_por_funcionario_LA),
        porDia: pontos(d.confeccionados_por_dia_LA),
        porMes: pontos(d.confeccionados_por_mes_LA),
        naoPorMes: pontos(d.nao_confeccionados_por_mes_LA),
        funcionarios: nomes(d.funcionarios_confeccao_LA),
        comissao: linhasComissao(d.comissionamento_peticionamento_LA_por_funcionario),
    }
}

function nomes(v: unknown): string[] {
    return Array.isArray(v) ? v.map((x) => String(x).trim()).filter(Boolean) : []
}

// As opções dos filtros, do que veio na resposta (como a v1): funcionários e matérias.
export function opcoesPeticionamento(p: PeticionamentoLegado) {
    const unicos = (xs: string[]) =>
        [...new Set(xs.map((x) => x.trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
    return {
        funcionarios: nomesFuncionarios(
            [...p.porFuncionario, ...p.naoPorFuncionario, ...p.mediaPorFuncionario].map((x) => x.name),
            p.funcionarios,
        ),
        materias: unicos([...p.porMateria, ...p.naoPorMateria].map((x) => x.name)),
    }
}
