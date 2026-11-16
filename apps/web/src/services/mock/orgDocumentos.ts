import type { DashboardFilters, DashboardQuery } from '../../types/index.ts'
import type { OrgDocumentosLexpreResponse } from '../../pages/dashboards/org-documentos-lexpre/types.ts'
import { funcionarios, metaFor, unitScale } from './helpers.ts'

// Números-base (NG), na ordem de grandeza da v1. As outras unidades são proporcionais (ver unitScale).
const MATERIAS: [string, number, number, number][] = [
    // matéria, resolvidos, protocolados, represados
    ['ANP', 69, 40, 0],
    ['RUBRICAS_REUNIDAS', 66, 31, 4],
    ['CESTA', 45, 22, 0],
    ['RUBRICAS_REUNIDAS_IRDR', 30, 15, 0],
    ['JUROS_ABUSIVOS', 16, 8, 3],
    ['SEGURO', 12, 6, 0],
    ['MORA', 10, 5, 0],
    ['MORA_CRED_PESS', 10, 5, 0],
    ['ESPECIFICA', 9, 4, 0],
    ['RCC', 6, 3, 0],
]
// Por pessoa: resolvidos, represados, valor de causa, parte já protocolada, protocolados.
const PESSOAS: [number, number, number, number, number][] = [
    [66, 4, 5075261.41, 1549145.0, 90],
    [89, 3, 4210377.12, 1385210.4, 58],
]
type DemandaMock = [number, string, 'resolvido' | 'represado', boolean, string[]]
// Pacotes (rubrica reunida) do setor: demanda, cliente, situação, protocolada no período e as rubricas.
const REUNIDAS: [string, DemandaMock[]][] = [
    [
        'RUBRICAS_REUNIDAS',
        [
            [4210, 'MARIA DAS GRAÇAS PEREIRA', 'represado', false, ['ANUIDADE', 'TARIFA_CESTA', 'SEGURO_PRESTAMISTA']],
            [4198, 'JOSÉ RIBAMAR COSTA', 'represado', false, ['MORA_CEL', 'PARC_CRED_PESS']],
            [4176, 'FRANCISCA ALVES DE SOUZA', 'resolvido', true, ['EMISSÃO_EXTRATO', 'GASTO_C_CRED']],
            [4151, 'RAIMUNDO NONATO LIMA', 'resolvido', false, ['OP_VENCIDAS', 'CESTA', 'ANUIDADE']],
        ],
    ],
    [
        'RUBRICAS_REUNIDAS_IRDR',
        [
            [4188, 'ANTÔNIA FERREIRA DOS SANTOS', 'resolvido', true, ['MORA', 'ENCARGOS_LIMITE_CRED']],
            [4120, 'PEDRO HENRIQUE MATOS', 'resolvido', false, ['ENC_DESCORBERTOS', 'ENC_EXC_LIMITE']],
        ],
    ],
]
const AREAS = [
    { id: 1, nome: 'Bancário' },
    { id: 2, nome: 'Consumidor' },
]

// Fração escolhida de uma lista: sem filtro = 1; com filtro = soma dos escolhidos / total.
function shareOf(items: [string, number][], chosen?: string[]): number {
    if (!chosen?.length) return 1
    const total = items.reduce((sum, [, v]) => sum + v, 0)
    return items.filter(([n]) => chosen.includes(n)).reduce((sum, [, v]) => sum + v, 0) / total
}

// Resposta fictícia da Organização de documentos (LexPre) para uma unidade, já com os filtros aplicados.
export function orgDocumentosFor(unit: string, query?: DashboardQuery): OrgDocumentosLexpreResponse {
    const f: DashboardFilters = query?.filters ?? {}
    const { count, money, series } = unitScale(unit)
    const nomes = funcionarios.slice(0, PESSOAS.length)
    const kMateria = shareOf(
        MATERIAS.map(([n, r]) => [n, r]),
        f.materia,
    )
    const kFunc = shareOf(
        nomes.map((n, i) => [n, PESSOAS[i][0]]),
        f.funcionario,
    )
    const k = kMateria * kFunc
    const c = (v: number) => count(v * k)
    const pessoas = nomes
        .map((name, i) => ({ name, p: PESSOAS[i] }))
        .filter(({ name }) => !f.funcionario?.length || f.funcionario.includes(name))
    const lista = (col: 0 | 1 | 2 | 3 | 4) =>
        pessoas
            .filter(({ p }) => p[col] > 0)
            .map(({ name, p }) => ({
                name,
                value: col === 2 || col === 3 ? money(p[col] * kMateria) : count(p[col] * kMateria),
            }))
    const materias = MATERIAS.filter(([n]) => !f.materia?.length || f.materia.includes(n))
    const porMateria = (col: 1 | 2 | 3) =>
        materias.filter((m) => m[col] > 0).map((m) => ({ name: m[0], value: count(m[col] * kFunc) }))

    return {
        meta: metaFor(unit),
        stats: {
            resolvidos_total: { total: c(303), comparativo: 33.48 },
            organizados_manualmente: { total: c(63), comparativo: 3.28 },
            organizados_e_peticionados_automaticamente: { total: c(240), comparativo: 44.58 },
            cancelados: { total: c(21), comparativo: -59.62 },
            protocolados_total: { total: c(148), comparativo: 12.1 },
            media_tempo_resolvidos: 2 + 10 / 24,
            mediana_tempo_resolvidos: 2 + 2 / 24,
            comparativo_tempo_medio_resolvidos: 54.43,
            comparativo_mediana_tempo_resolvidos: 57.14,
            represados: c(7),
            devolvido_pendencia: count(506),
            comparativo_devolvido_pendencia: 120.34,
        },
        resolvidos_total_por_materia: porMateria(1),
        protocolados_total_por_materia: porMateria(2),
        nao_organizados_total_por_materia: porMateria(3),
        resolvidos_total_por_mes: [
            { name: '2026-09', value: c(371) },
            { name: '2026-10', value: c(493) },
            { name: '2026-11', value: c(303) },
        ],
        nao_resolvidos_total_por_mes: [{ name: '2026-11', value: c(7) }],
        resolvidos_por_dia_org: series(18, 10).map((p) => ({ ...p, value: Math.round(p.value * k) })),
        resolvidos_por_funcionario: lista(0),
        nao_organizados_por_funcionario: lista(1),
        protocolados_por_funcionario: lista(4),
        media_resolvidos_por_funcionario: lista(0).map((p) => ({
            name: p.name,
            value: Math.round(p.value / 0.42) / 10,
        })),
        valor_causa_por_funcionario: lista(2),
        valor_causa_protocolado_por_funcionario: lista(3),
        comissionamento_por_funcionario: pessoas.map(({ name, p }) => ({
            funcionario: name,
            qtd_protocolados: count(p[4] * kMateria),
            valor_causa_protocolado: money(p[3] * kMateria),
            valor_comissao: count(p[4] * kMateria) * 1.5,
        })),
        // Pacotes (rubrica reunida): as demandas e as rubricas de cada uma (o modal da v1).
        rubricas_reunidas: REUNIDAS.filter(([m]) => !f.materia?.length || f.materia.includes(m)).map(
            ([materia, demandas]) => ({
                materia,
                demandas: demandas.map(([id, cliente, situacao, protocolado, rubricas]) => ({
                    id_demanda: id,
                    cliente,
                    situacao,
                    protocolado,
                    rubricas,
                })),
            }),
        ),
        opcoes_filtro: {
            materias: MATERIAS.map(([n]) => n),
            funcionarios: nomes,
            ufs: [],
            areas: AREAS,
        },
    }
}
