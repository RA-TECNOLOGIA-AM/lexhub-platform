import type { Point } from '../../../types/index.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { nomesFuncionarios } from '../setor/setor.ts'

// A Organização de Documentos do banco legado vem de três rotas da v1: /org-documentos (NG) e /org_doc_RJ, com
// os mesmos nomes, e /org_doc_LA, com outros (quase todos com _LA). Aqui as duas viram a forma que a página
// usa. Só lógica pura (testada em
// orgDocumentos.test.ts).

export type LinhaComissaoOrg = {
    funcionario: string
    qtd_resolvidos: number
    valor_causa_gerado: number
    valor_comissao: number
}

export type OrgDocumentosLegado = {
    la: boolean // veio da rota da LA (banco LA)
    resolvidos: number | null // no período: manuais + automáticos
    manuais: number | null
    automaticos: number | null // organizados e peticionados pelo sistema
    reajuizamento: number | null // a LA não separa o reajuizamento
    cancelados: number | null
    mediaTempo: number | null // em dias, como a API manda
    medianaTempo: number | null
    // Agora (não dependem do período): a fila e o que voltou para outros setores.
    represados: number | null
    retornoPendencia: number | null
    retornoConfeccao: number | null // a LA não tem (só o retorno para Pendência)
    comparativo: {
        resolvidos: number | null
        manuais: number | null
        automaticos: number | null
        reajuizamento: number | null
        cancelados: number | null
        mediaTempo: number | null
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
    comissao: LinhaComissaoOrg[]
}

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

function pontos(v: unknown): Point[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((p): p is { name: unknown; value: unknown } => typeof p === 'object' && p !== null)
        .map((p) => ({ name: String(p.name ?? ''), value: numero(p.value) ?? 0 }))
}

function linhasComissao(v: unknown): LinhaComissaoOrg[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((r): r is Record<string, unknown> => typeof r === 'object' && r !== null)
        .map((r) => ({
            funcionario: String(r.funcionario ?? ''),
            qtd_resolvidos: numero(r.qtd_resolvidos) ?? 0,
            valor_causa_gerado: numero(r.valor_causa_gerado) ?? 0,
            valor_comissao: numero(r.valor_comissao) ?? 0,
        }))
}

export function lerOrgDocumentos(data: V1GenericoResponse): OrgDocumentosLegado {
    const d = data as V1GenericoResponse & Record<string, unknown>
    const s = data.stats ?? {}
    const n = (campo: string) => numero(s[campo])
    // Pelo nome da rota: a resposta da v1 traz os campos de todas as rotas (os das outras vêm null).
    const la = data.dashboard ? data.dashboard === 'org_doc_LA' : n('total_organizados_LA') !== null
    if (la) return lerLA(d, n)
    return {
        la,
        resolvidos: n('resolvidos_total'),
        manuais: n('organizados_manualmente'),
        automaticos: n('organizados_e_peticionados_automaticamente'),
        reajuizamento: n('resolvidos_reajuizamento'),
        cancelados: n('cancelados'),
        mediaTempo: n('media_tempo_resolvidos'),
        medianaTempo: n('mediana_tempo_resolvidos'),
        represados: n('nao_organizados'),
        retornoPendencia: n('retorno_pendencia'),
        retornoConfeccao: n('retorno_pet'),
        comparativo: {
            resolvidos: n('comparativo_resolvidos_total'),
            manuais: n('comparativo_organizados_manualmente'),
            automaticos: n('comparativo_organizados_e_peticionados_automaticamente'),
            reajuizamento: n('comparativo_resolvidos_reajuizamento'),
            cancelados: n('comparativo_cancelados'),
            mediaTempo: n('comparativo_tempo_medio_resolvidos_org_doc'),
        },
        porMateria: pontos(d.resolvidos_total_por_materia),
        naoPorMateria: pontos(d.nao_organizados_total_por_materia),
        porFuncionario: pontos(d.resolvidos_por_funcionario),
        naoPorFuncionario: pontos(d.nao_organizados_por_funcionario),
        mediaPorFuncionario: pontos(d.media_resolvidos_por_funcionario),
        valorPorFuncionario: pontos(d.valor_causa_por_funcionario),
        porDia: pontos(d.resolvidos_por_dia_org),
        porMes: pontos(d.resolvidos_total_por_mes),
        naoPorMes: pontos(d.nao_resolvidos_total_por_mes),
        funcionarios: nomes(d.funcionarios_org_doc),
        comissao: linhasComissao(d.comissionamento_por_funcionario),
    }
}

// A rota /org_doc_LA: "organizados" e _LA nos nomes, sem reajuizamento nem retorno para a Confecção.
function lerLA(d: Record<string, unknown>, n: (campo: string) => number | null): OrgDocumentosLegado {
    return {
        la: true,
        resolvidos: n('total_organizados_LA'),
        manuais: n('total_organizados_manualmente_LA'),
        automaticos: n('total_organizados_automaticamente_LA'),
        reajuizamento: null,
        cancelados: n('cancelados_LA'),
        mediaTempo: n('media_tempo_resolvidos_LA'),
        medianaTempo: n('mediana_tempo_resolvidos_LA'),
        represados: n('nao_organizados_LA'),
        retornoPendencia: n('retorno_pendencia_LA'),
        retornoConfeccao: null,
        comparativo: {
            resolvidos: n('comparativo_resolvidos_total_LA'),
            manuais: n('comparativo_organizados_manualmente_LA'),
            automaticos: n('comparativo_organizados_automaticamente_LA'),
            reajuizamento: null,
            cancelados: n('comparativo_cancelados_LA'),
            mediaTempo: null, // a rota da LA não manda
        },
        porMateria: pontos(d.organizados_total_por_materia_LA),
        naoPorMateria: pontos(d.nao_organizados_total_por_materia_LA),
        porFuncionario: pontos(d.organizados_por_funcionario_LA),
        naoPorFuncionario: pontos(d.nao_organizados_por_funcionario_LA),
        mediaPorFuncionario: pontos(d.media_resolvidos_por_funcionario_LA),
        valorPorFuncionario: pontos(d.valor_causa_por_funcionario_LA),
        porDia: pontos(d.resolvidos_por_dia_LA),
        porMes: pontos(d.resolvidos_total_por_mes_LA),
        naoPorMes: pontos(d.nao_organizados_total_por_mes_LA),
        funcionarios: nomes(d.funcionarios_org_doc_LA),
        comissao: linhasComissao(d.comissionamento_org_doc_LA_por_funcionario),
    }
}

function nomes(v: unknown): string[] {
    return Array.isArray(v) ? v.map((x) => String(x).trim()).filter(Boolean) : []
}

// As opções dos filtros, do que veio na resposta (como a v1): funcionários e matérias.
export function opcoesOrgDocumentos(p: OrgDocumentosLegado) {
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
