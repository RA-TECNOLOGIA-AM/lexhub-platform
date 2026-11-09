import type { DashboardFilters, DashboardQuery, Point, ProtocoloResponse } from '../types.ts'
import { funcionarios, metaFor, unitScale } from './helpers.ts'

// Números-base (NG). As outras unidades são proporcionais (ver unitScale).
// Matérias com os nomes da v1 (LexPre); a soma bate com os 1.284 protocolados.
const MATERIAS: [string, number][] = [
    ['ANP', 412],
    ['RUBRICAS_REUNIDAS', 198],
    ['RUBRICAS_REUNIDAS_IRDR', 141],
    ['CESTA', 137],
    ['SVA', 96],
    ['PARC_CRED_PESS', 88],
    ['JUROS_ABUSIVOS', 74],
    ['MORA', 61],
    ['MORA_CRED_PESS', 43],
    ['ESPECIFICA', 34],
]
const REPRESADOS_POR_MATERIA = [28, 17, 12, 10, 8, 7, 6, 4, 3, 1]
const PROTOCOLADOS_POR_FUNC = [312, 268, 231, 198, 161, 114] // soma 1.284
const REPRESADOS_POR_FUNC = [21, 18, 17, 15, 14, 11]
const UFS: [string, number][] = [
    ['AM', 0.7],
    ['PA', 0.2],
    ['RR', 0.1],
]
const AREAS = [
    { id: 1, nome: 'Bancário' },
    { id: 2, nome: 'Consumidor' },
    { id: 3, nome: 'Previdenciário' },
]
const AREA_PESO: [string, number][] = [
    ['1', 0.5],
    ['2', 0.3],
    ['3', 0.2],
]
// Processo, etapa e dias parado; o responsável é o funcionário da mesma posição.
const PENDENCIAS: [string, string, number][] = [
    ['0000123-45.2026.8.04.0001', 'Juntada de documentos', 14],
    ['0000456-78.2026.8.04.0001', 'Assinatura do cliente', 12],
    ['0000789-01.2026.8.04.0001', 'Revisão da peça', 9],
    ['0000234-56.2026.8.04.0001', 'Cálculo', 6],
    ['0000567-89.2026.8.04.0001', 'Procuração', 4],
    ['0000890-12.2026.8.04.0001', 'Comprovante de residência', 3],
]

// Fração escolhida de uma lista: sem filtro = 1; com filtro = soma dos escolhidos / total (0 se nenhum existe).
function shareOf(items: [string, number][], chosen?: string[]): number {
    if (!chosen?.length) return 1
    const total = items.reduce((sum, [, v]) => sum + v, 0)
    const picked = items.filter(([name]) => chosen.includes(name)).reduce((sum, [, v]) => sum + v, 0)
    return picked / total
}

// Série mensal determinística, de 'AAAA-MM' até 'AAAA-MM' (inclusive).
function porMes(inicio: string, fim: string, base: number, amp: number): Point[] {
    const out: Point[] = []
    let [y, m] = inicio.split('-').map(Number)
    const [fy, fm] = fim.split('-').map(Number)
    for (let i = 0; y < fy || (y === fy && m <= fm); i++) {
        const value = Math.max(0, Math.round(base + amp * Math.sin(i * 0.9)))
        out.push({ name: `${y}-${String(m).padStart(2, '0')}`, value })
        m++
        if (m > 12) {
            m = 1
            y++
        }
    }
    return out
}

// Resposta fictícia do Protocolo para uma unidade, já com os filtros aplicados.
export function protocoloFor(unit: string, query?: DashboardQuery): ProtocoloResponse {
    const f: DashboardFilters = query?.filters ?? {}
    const { count, money, series } = unitScale(unit)
    const funcItems = funcionarios.map((name, i): [string, number] => [name, PROTOCOLADOS_POR_FUNC[i]])

    // Quanto cada filtro deixa passar (1 = tudo, 0 = nada).
    const kMateria = shareOf(MATERIAS, f.materia)
    const kFunc = shareOf(funcItems, f.funcionario)
    const kResto = shareOf(UFS, f.uf) * shareOf(AREA_PESO, f.area_atuacao_id)
    const k = kMateria * kFunc * kResto

    // Lista nome + valor: escala pela unidade e pelos outros filtros; com filtro na própria lista, só os escolhidos.
    const list = (items: [string, number][], factor: number, chosen?: string[]): Point[] =>
        items
            .filter(([name]) => !chosen?.length || chosen.includes(name))
            .map(([name, v]) => ({ name, value: count(v * factor) }))
    const scaled = (points: Point[]) => points.map((p) => ({ ...p, value: Math.round(p.value * k) }))

    const protocolados = count(1284 * k)
    const valorCausa = money(18432750.4 * k)
    const tempo = (v: number) => (protocolados ? v : 0) // sem protocolados, não há tempo
    const porFunc = list(funcItems, kMateria * kResto, f.funcionario)

    return {
        meta: metaFor(unit),
        stats: {
            protocolados_total: { total: protocolados, comparativo: 8.2 },
            valor_causa_protocolado: { total: valorCausa, comparativo: 5.1 },
            ticket_medio_protocolado: { total: protocolados ? valorCausa / protocolados : 0, comparativo: -2.8 },
            media_tempo_protocolado: tempo(2.4),
            mediana_tempo_protocolado: tempo(1.6),
            comparativo_tempo_medio_protocolado: -12.0,
            comparativo_mediana_tempo_protocolado: -6.5,
            represados: count(96 * k),
            devolvido_peticionamento: count(41 * k),
            devolvido_org_doc: count(17 * k),
            devolvido_pendencia: count(23 * k),
            comparativo_devolvido_peticionamento: -16.7,
            comparativo_devolvido_org_doc: -9.1,
            comparativo_devolvido_pendencia: 0,
        },
        protocolados_por_dia: scaled(series(58, 14)),
        protocolados_por_materia: list(MATERIAS, kFunc * kResto, f.materia),
        represados_por_materia: list(
            MATERIAS.map(([name], i): [string, number] => [name, REPRESADOS_POR_MATERIA[i]]),
            kFunc * kResto,
            f.materia,
        ),
        protocolados_por_funcionario: porFunc,
        represados_por_funcionario: list(
            funcionarios.map((name, i): [string, number] => [name, REPRESADOS_POR_FUNC[i]]),
            kMateria * kResto,
            f.funcionario,
        ),
        media_protocolados_por_funcionario: porFunc.map((p) => ({ name: p.name, value: Math.round(p.value / 21) })),
        valor_causa_por_funcionario: porFunc.map((p) => ({ name: p.name, value: Math.round(p.value * 14355.72) })),
        protocolados_por_mes: scaled(porMes('2024-01', '2026-10', count(1100), count(250))),
        represados_por_mes: scaled(porMes('2026-05', '2026-10', count(14), count(6))),
        comissionamento_por_funcionario: porFunc.map((p) => ({
            funcionario: p.name,
            qtd_protocolados: p.value,
            valor_comissao: p.value * 1.0,
        })),
        protocolados_no_prazo: { taxa: protocolados ? 93 : 0, comparativo: protocolados ? 1.5 : null },
        metas: { tempo_medio_dias: 3, no_prazo_pct: 90, protocolados_por_funcionario: 20 },
        pendencias_mais_antigas: PENDENCIAS.map(([processo, etapa, dias], i) => ({
            processo,
            etapa,
            responsavel: funcionarios[i],
            dias_parado: dias,
        })).filter((p) => !f.funcionario?.length || f.funcionario.includes(p.responsavel)),
        opcoes_filtro: {
            materias: MATERIAS.map(([name]) => name),
            funcionarios,
            ufs: UFS.map(([uf]) => uf),
            areas: AREAS,
        },
    }
}
