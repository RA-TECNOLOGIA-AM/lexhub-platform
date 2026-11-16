import type { DashboardFilters, DashboardQuery, Point } from '../../types/index.ts'
import type { PeticionamentoLexpreResponse } from '../../pages/dashboards/peticionamento-lexpre/types.ts'
import { funcionarios, metaFor, unitScale } from './helpers.ts'

// Números-base (NG), na ordem de grandeza da v1. As outras unidades são proporcionais (ver unitScale).
const MATERIAS: [string, number, number, number][] = [
    // matéria, peticionados, protocolados, não peticionados
    ['ANP', 50, 46, 18],
    ['CESTA', 28, 26, 14],
    ['RUBRICAS_REUNIDAS', 24, 22, 19],
    ['RUBRICAS_REUNIDAS_IRDR', 18, 17, 8],
    ['JUROS_ABUSIVOS', 5, 5, 6],
    ['PARC_CRED_PESS', 5, 4, 3],
    ['MORA_CRED_PESS', 5, 5, 2],
    ['MORA', 4, 4, 5],
    ['SEGURO', 4, 3, 7],
    ['RMC', 3, 3, 4],
]
// Por pessoa: peticionados, não peticionados, valor confeccionado, parte já protocolada.
const PESSOAS: [number, number, number, number][] = [
    [71, 53, 1706716.3, 1557402.66],
    [54, 51, 1386847.21, 1356353.8],
    [12, 0, 0, 0],
    [8, 0, 0, 0],
    [7, 0, 0, 0],
    [5, 0, 0, 0],
]
type DemandaMock = [number, string, 'resolvido' | 'represado', boolean, string[]]
const REUNIDAS: [string, DemandaMock[]][] = [
    [
        'RUBRICAS_REUNIDAS',
        [
            [4204, 'CIVAL OLIVEIRA DO NASCIMENTO', 'represado', false, ['OP_VENCIDAS', 'CESTA']],
            [4170, 'NELLY AREIZA FILHO', 'represado', false, ['DIVIDA_ATRASO', 'PARC_CRED_PESS', 'EXTRATOMOVIMENTO']],
            [4162, 'OSIVANE GOMES DO NASCIMENTO', 'resolvido', true, ['ANUIDADE', 'PARC_CRED_PESS', 'SAQUE_TERMINAL']],
            [4155, 'DAVID CAVALCANTE BINDA', 'resolvido', true, ['BX_ANT_FIN', 'MORA_CEL', 'PARC_CRED_PESS']],
            [4136, 'CLAUDIOMAR SANTOS DE ARAÚJO', 'resolvido', false, ['EMISSÃO_EXTRATO', 'GASTO_C_CRED', 'ANUIDADE']],
            [
                4103,
                'SILVIO PEREIRA DE OLIVEIRA',
                'represado',
                false,
                ['ANUIDADE', 'MORA_CEL', 'OP_VENCIDAS', 'COBRANCA_IND'],
            ],
        ],
    ],
    [
        'RUBRICAS_REUNIDAS_IRDR',
        [
            [4202, 'LUCYANA GOMES MARREIRO', 'represado', false, ['MORA', 'ENCARGOS_LIMITE_CRED']],
            [4180, 'ANA PAULA DA COSTA MONTEIRO', 'resolvido', true, ['MORA', 'ENC_DESCORBERTOS']],
            [4049, 'SILVANI SANTOS DE LIMA', 'represado', false, ['ENC_DESCORBERTOS', 'ENC_EXC_LIMITE', 'MORA']],
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

// Série mensal determinística, de 'AAAA-MM' até 'AAAA-MM' (inclusive).
function porMes(meses: [string, number][]): Point[] {
    return meses.map(([name, value]) => ({ name, value }))
}

// Resposta fictícia do Peticionamento (LexPre) para uma unidade, já com os filtros aplicados.
export function peticionamentoFor(unit: string, query?: DashboardQuery): PeticionamentoLexpreResponse {
    const f: DashboardFilters = query?.filters ?? {}
    const { count, money, series } = unitScale(unit)
    const nomes = funcionarios.slice(0, PESSOAS.length)
    const kMateria = shareOf(
        MATERIAS.map(([n, p]) => [n, p]),
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
    const lista = (col: 0 | 1 | 2 | 3) =>
        pessoas
            .filter(({ p }) => p[col] > 0)
            .map(({ name, p }) => ({ name, value: col >= 2 ? money(p[col] * kMateria) : count(p[col] * kMateria) }))
    const materias = MATERIAS.filter(([n]) => !f.materia?.length || f.materia.includes(n))
    const porMateria = (col: 1 | 2 | 3) => materias.map((m) => ({ name: m[0], value: count(m[col] * kFunc) }))

    const peticionados = c(157)
    const valor = money(3093563.51 * k)
    return {
        meta: metaFor(unit),
        stats: {
            total_peticionados: { total: peticionados, comparativo: -16.49 },
            peticionados_manualmente: { total: c(33), comparativo: -19.51 },
            peticionados_automaticamente: { total: c(124), comparativo: -15.65 },
            cancelados: { total: c(10), comparativo: -65.52 },
            protocolados_total: { total: c(146), comparativo: -12.4 },
            valor_causa_confeccionado: { total: valor, comparativo: -22.19 },
            ticket_medio_confeccionado: { total: peticionados ? valor / peticionados : 0, comparativo: -6.83 },
            media_tempo_peticionado: peticionados ? (23 * 60 + 2) / 1440 : 0,
            mediana_tempo_peticionado: peticionados ? (14 * 60 + 38) / 1440 : 0,
            comparativo_tempo_medio_peticionado: -50.77,
            comparativo_mediana_tempo_peticionado: -21.79,
            represados: c(104),
            retorno_org_doc: count(76),
            retorno_pendencia: count(82),
            comparativo_retorno_org_doc: 0,
            comparativo_retorno_pendencia: 44.44,
        },
        peticionados_por_materia: porMateria(1),
        protocolados_por_materia: porMateria(2),
        represados_por_materia: porMateria(3),
        peticionados_por_mes: porMes([
            ['2026-09', c(339)],
            ['2026-10', c(450)],
            ['2026-11', c(157)],
        ]),
        represados_por_mes: porMes([['2026-11', c(104)]]),
        peticionados_por_dia: series(8, 6).map((p) => ({ ...p, value: Math.round(p.value * k) })),
        peticionados_por_funcionario: lista(0),
        represados_por_funcionario: lista(1),
        protocolados_por_funcionario: lista(0).map((p) => ({ ...p, value: Math.round(p.value * 0.93) })),
        media_peticionado_por_funcionario: lista(0).map((p) => ({
            name: p.name,
            value: Math.round(p.value / 0.68) / 10,
        })),
        valor_causa_por_funcionario: lista(2),
        valor_causa_protocolado_por_funcionario: lista(3),
        comissionamento_por_funcionario: lista(0).map((p, i) => ({
            funcionario: p.name,
            qtd_acoes_massa: Math.round(p.value * 0.8),
            valor_acoes_massa: i === 0 ? 1.5 : 0.5,
            qtd_x_valor_massa: Math.round(p.value * 0.8) * (i === 0 ? 1.5 : 0.5),
            qtd_acoes_especificas: Math.round(p.value * 0.2),
            valor_acoes_especificas: i === 0 ? 13 : 7,
            qtd_x_valor_especificas: Math.round(p.value * 0.2) * (i === 0 ? 13 : 7),
            taxa_resolvidos: i === 0 ? 87.5 : 72.1,
            valor_comissao:
                Math.round(p.value * 0.8) * (i === 0 ? 1.5 : 0.5) + Math.round(p.value * 0.2) * (i === 0 ? 13 : 7),
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
