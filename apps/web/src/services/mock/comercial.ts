import type { DashboardQuery } from '../../types/index.ts'
import type {
    ComercialLexpreResponse,
    LinhaAtendente,
    MetaInteligente,
    RubricaValor,
} from '../../pages/dashboards/comercial-lexpre/types.ts'
import { metaFor, unitScale } from './helpers.ts'

// Números-base (NG), na ordem de grandeza da v1. As outras unidades são proporcionais (ver unitScale).
const ATENDENTES = ['Nayla', 'Patricia', 'Isabelle', 'Ana', 'Yara']
const RANKING = [204, 146, 98, 52, 45]
// Fila do pré-protocolo: pendências, triagem, não organizado, não confeccionado, não protocolado, protocolado.
const FILA: number[][] = [
    [19, 0, 59, 53, 3, 550],
    [10, 0, 15, 54, 10, 459],
    [10, 0, 40, 13, 6, 255],
    [8, 0, 8, 33, 0, 132],
    [16, 0, 17, 16, 0, 435],
]
const VALOR = [
    [1_064_793.94, 45_942.37],
    [1_156_134.68, 123_067.34],
    [533_916.84, 67_751.76],
    [639_582.16, 0],
    [238_510.0, 0],
]
// Protocolado por atendente no 4º trimestre (Meta por Atendente).
const TRIMESTRE = [7_173_429.13, 5_380_263.26, 1_958_956.94, 2_899_029.9, 3_390_693.71]
const RUBRICAS: [string, number][] = [
    ['ANP', 65],
    ['PARC_CRED_PESS', 52],
    ['CESTA', 47],
    ['SEGURO', 30],
    ['EMISSÃO_EXTRATO', 29],
    ['GASTO_C_CRED', 28],
    ['ENCARGOS_LIMITE_CRED', 25],
    ['MORA', 24],
    ['JUROS_ABUSIVOS', 21],
    ['SAQUE_TERMINAL', 21],
    ['BX_ANT_FIN', 20],
    ['EXTRATOMOVIMENTO', 18],
    ['COBRANCA_IND', 17],
    ['TIT_CAP', 15],
    ['OP_VENCIDAS', 10],
]
// Tabela por atendente: leads e clientes (geral, campanha, retorno passivo).
const TABELA: [string, number, number, number, number, number, number][] = [
    ['Isabelle', 143, 22, 85, 8, 10, 9],
    ['Nayla', 141, 43, 80, 19, 16, 15],
    ['Ana', 130, 12, 81, 4, 5, 4],
    ['Patricia', 115, 36, 56, 8, 13, 11],
    ['Yara', 64, 8, 33, 2, 6, 5],
]

// VALOR_AM (R$ por ação) de cada rubrica, na ordem de grandeza da v1.
const VALOR_AM: Record<string, number> = {
    ANP: 1,
    PARC_CRED_PESS: 3,
    CESTA: 3,
    SEGURO: 3,
    EMISSÃO_EXTRATO: 2,
    GASTO_C_CRED: 2,
    ENCARGOS_LIMITE_CRED: 2,
    MORA: 2,
    JUROS_ABUSIVOS: 3,
    SAQUE_TERMINAL: 2,
    BX_ANT_FIN: 3,
    EXTRATOMOVIMENTO: 2,
    COBRANCA_IND: 2,
    TIT_CAP: 3,
    OP_VENCIDAS: 2,
}

// Seção 02 da Comissão: base = soma da tabela; FM 3,85; desconto por cancelamento; o líquido vai todo para AM/PA.
function comissao(k: number, tabelas: Record<string, RubricaValor[]>) {
    const base = tabelas.total.reduce((s, r) => s + r.total, 0)
    const fator = 3.85
    const bruta = Math.round(base * fator * 100) / 100
    const desconto = k === 1 ? 13 : 0
    const liquida = bruta - desconto
    return {
        comissao_base: base,
        fator_multiplicador: fator,
        comissao_com_fm: bruta,
        desconto_cancelamentos: desconto,
        comissao_com_fm_liquida: liquida,
        proporcional_am_pa: liquida,
        proporcional_pb: 0,
        rubricas_total_tabela: tabelas,
    }
}

const taxa = (l: number, c: number) => (l > 0 ? Math.round((c / l) * 10000) / 100 : 0)

function linha(nome: string, [lg, cg, lc, cc, lr, cr]: number[]): LinhaAtendente {
    return {
        atendente: nome,
        leads_geral: lg,
        clientes_geral: cg,
        taxa_geral: taxa(lg, cg),
        leads_campanha: lc,
        clientes_campanha: cc,
        taxa_campanha: taxa(lc, cc),
        leads_redes_sociais: 0,
        clientes_redes_sociais: 0,
        taxa_redes_sociais: 0,
        leads_retorno_passivo: lr,
        clientes_retorno_passivo: cr,
        taxa_retorno_passivo: taxa(lr, cr),
    }
}

// A resposta da Meta Inteligente para uma janela (números da v1, com tendências variadas).
function metaInteligente(meses: number): MetaInteligente {
    const base = [1_480_000, 1_150_000, 850_000, 540_000, 490_000]
    const tendencia = [-180_000, -140_000, -120_000, 90_000, -70_000]
    const labels = ['queda forte', 'queda forte', 'queda forte', 'crescimento forte', 'queda forte']
    const soma = base.reduce((a, b) => a + b, 0)
    const atendentes = ATENDENTES.map((nome, i) => {
        const historico = Array.from({ length: meses }, (_, k) => {
            const mes = new Date(2026, 10 - (meses - 1) + k, 1)
            return {
                mes: `${mes.getFullYear()}-${String(mes.getMonth() + 1).padStart(2, '0')}`,
                valor: Math.max(0, base[i] - tendencia[i] * (meses - 1 - k)),
            }
        })
        const projecao = Math.max(0, base[i] + tendencia[i])
        return {
            atendente: nome,
            meses_com_dados: meses,
            historico_mensal: historico,
            media_simples: base[i],
            media_ponderada: base[i],
            tendencia_mensal: tendencia[i],
            tendencia_label: labels[i],
            projecao_proximo_mes: projecao,
            meta_sugerida: projecao * 1.1,
            percentual_da_equipe: Math.round((base[i] / soma) * 1000) / 10,
            meta_proporcional: (12_000_000 * base[i]) / soma,
        }
    })
    return {
        gerado_em: '2026-11-16',
        meses_considerados: meses,
        meta_global: 12_000_000,
        atendentes,
        totais: {
            media_equipe_mes: soma / atendentes.length,
            projecao_total_proximo_mes: atendentes.reduce((s, a) => s + a.projecao_proximo_mes, 0),
            meta_total_sugerida: atendentes.reduce((s, a) => s + a.meta_sugerida, 0),
        },
    }
}

const stat = (total: number, comparativo: number) => ({ total, comparativo })

// Resposta fictícia do Comercial (LexPre) para uma unidade, já com o filtro de atendente aplicado.
export function comercialFor(unit: string, query?: DashboardQuery): ComercialLexpreResponse {
    const { count, money } = unitScale(unit)
    const escolhidos = query?.filters?.atendente_comercial ?? []
    const idx = ATENDENTES.map((_, i) => i).filter((i) => !escolhidos.length || escolhidos.includes(ATENDENTES[i]))
    const k = idx.reduce((s, i) => s + RANKING[i], 0) / RANKING.reduce((a, b) => a + b, 0)
    const c = (v: number) => count(v * k)
    const pontos = (vals: number[]) => idx.map((i) => ({ name: ATENDENTES[i], value: count(vals[i]) }))
    const rubricas = RUBRICAS.map(([name, v]) => ({ name, value: c(v) }))
    const tabela = (fator: number) =>
        RUBRICAS.map(([rubrica, v]) => {
            const acoes = Math.round(c(v) * fator)
            const valor_am = VALOR_AM[rubrica] ?? 1
            return { rubrica, acoes, valor_am, total: acoes * valor_am }
        })
    const rubricasTabela = { total: tabela(1), campanha: tabela(0.6), retorno: tabela(0.3) }

    return {
        meta: metaFor(unit),
        stats: {
            valor_causa_protocolado_ano: money(58_412_300.55 * k),
            ano_meta: 2026,
            clientes_todos: stat(c(121), -1.63),
            clientes_campanha: stat(c(41), -30.51),
            clientes_redes_sociais: stat(0, 0),
            clientes_retorno: stat(c(44), -29.03),
            clientes_resgate: stat(0, 0),
            clientes_indicacao: stat(c(36), 1700),
            clientes_site: stat(0, 0),
            clientes_parceiros: stat(0, 0),
            clientes_externos: stat(0, 0),
            demandas_canceladas: stat(c(10), -80.39),
            acoes_fechadas: stat(c(545), 10.32),
            rubricas_reunidas_fechadas: c(96),
            taxa_aproveitamento: stat(4.5, 11.94),
            leads_geral: stat(c(594), -15.26),
            leads_campanha: stat(c(335), -26.54),
            taxa_leads_geral: stat(19.36, 17.98),
            taxa_leads_campanha: stat(11.64, -5.21),
            ranking_acoes_fechadas_por_atendente: pontos(RANKING),
            acoes_fechadas_hoje_por_atendente: idx.includes(0) ? [{ name: 'Nayla', value: 3 }] : [],
            contratos_fechados_hoje_por_atendente: idx.includes(0) ? [{ name: 'Nayla', value: 1 }] : [],
            protocolados: stat(c(162), -11.96),
            valor_causa_protocolado: stat(money(3_632_937.62 * k), -9.31),
            ticket_medio_protocolado: stat(22_425.54, 3.01),
            tempo_medio_ate_protocolo_horas: 5 * 24 + 3,
            fila_pre_protocolo_por_atendente: idx.map((i) => {
                const [pendencias, triagem, nao_organizado, nao_confeccionado, nao_protocolado, protocolado] =
                    FILA[i].map(count)
                return {
                    name: ATENDENTES[i],
                    pendencias,
                    triagem,
                    nao_organizado,
                    nao_confeccionado,
                    nao_protocolado,
                    protocolado,
                    total: pendencias + triagem + nao_organizado + nao_confeccionado + nao_protocolado + protocolado,
                }
            }),
            valor_causa_por_atendente: idx.map((i) => ({
                name: ATENDENTES[i],
                protocolado: money(VALOR[i][0]),
                nao_protocolado: money(VALOR[i][1]),
                total: money(VALOR[i][0] + VALOR[i][1]),
            })),
            acoes_fechadas_por_rubrica: {
                total: rubricas,
                campanha: rubricas.map((r) => ({ ...r, value: Math.round(r.value * 0.6) })),
                retorno: rubricas.map((r) => ({ ...r, value: Math.round(r.value * 0.3) })),
            },
            tabela_por_atendente: idx.map((i) => linha(TABELA[i][0], TABELA[i].slice(1) as number[])),
            totais_tabela_por_atendente: linha('Total', [594, 121, 335, 41, 51, 44]),
            valor_causa_protocolado_por_atendente_periodo: Object.fromEntries(
                idx.map((i) => [ATENDENTES[i], money(TRIMESTRE[i])]),
            ),
            ...comissao(k, rubricasTabela),
            comissionamento_por_atendente: idx.map((i) => ({
                atendente: ATENDENTES[i],
                acoes: count(RANKING[i]),
                comissao_base: RANKING[i] * 20,
                valor_fm: RANKING[i] * 6,
                proporcional_am_pa: RANKING[i] * 14,
                proporcional_pb: RANKING[i] * 6,
                comissao_com_fm: RANKING[i] * 26,
                desconto_cancelamentos: i === 0 ? 120 : 0,
            })),
            demandas_canceladas_desconto:
                k === 1
                    ? [
                          {
                              atendente: 'Isabelle',
                              materia: 'MORA',
                              cliente: 'Cliente Exemplo',
                              motivo: 'Cliente desistiu',
                              data_cancelamento: '2026-11-10',
                              desconto: 13,
                          },
                      ]
                    : [],
        },
        meta_inteligente: { '3': metaInteligente(3), '6': metaInteligente(6), '12': metaInteligente(12) },
        // O legado entra inteiro (sem os filtros), como na v1.
        valor_causa_protocolado_legado: money(175_694_443.63),
        valor_causa_protocolado_por_atendente_legado: Object.fromEntries(
            ATENDENTES.map((nome, i) => [nome, money(TRIMESTRE[i] * 0.35)]),
        ),
        opcoes_filtro: {
            atendentes: ATENDENTES,
            areas: [
                { id: 1, nome: 'Bancário' },
                { id: 2, nome: 'Consumidor' },
            ],
            ufs: ['AM', 'PA'],
            segmentos: [
                'CAMPANHA',
                'REDES_SOCIAIS',
                'RETORNO',
                'RESGATE',
                'INDICACAO',
                'SITE',
                'PARCEIROS',
                'EXTERNOS',
            ],
        },
    }
}
