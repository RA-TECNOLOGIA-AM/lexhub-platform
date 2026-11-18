import type { PrevisaoResponse } from '../../pages/dashboards/previsao-individualizada/previsao.ts'
import { metaFor } from './helpers.ts'

// Bundle fictício da Previsão Individualizada (formato da rota da v1 /tcc_previsao_individual): grade pequena de
// combinações com números inventados por uma sequência pseudoaleatória fixa. Só o escritório da unidade (como a API).

const TIPOS = ['INDENIZATÓRIA', 'RECURSO INOMINADO', 'APELAÇÃO CÍVEL', 'CUMPRIMENTO DE SENTENÇA']
const MATERIAS = ['CESTA', 'RMC', 'MORA', 'ANP', 'GASTO_C_CRED', 'SEGURO']
const COMARCAS = ['MANAUS', 'ITACOATIARA', 'PARINTINS', 'MANACAPURU', 'TEFÉ']
const COMPETENCIAS = ['Juizado Especial Cível', 'Vara Cível', 'Turma Recursal']
const FAIXAS = ['Até R$ 10 mil', 'R$ 10 mil – 30 mil', 'R$ 30 mil – 50 mil', 'Acima de R$ 50 mil']
// Fora do "top" do modelo: usa a previsão de "Outros", com o peso próprio.
const GRUPO = { materia: { SEGURO: 'Outros' }, comarca: { TEFÉ: 'Outros' }, competencia: {} }

export function previsaoFor(unit: string): PrevisaoResponse {
    const meta = metaFor(unit, 'LexFlow')
    const esc = ({ NG: 'NG', LA: 'LA', LA_AM: 'LA' } as Record<string, string>)[unit]
    const opcoes = {
        tiposAcao: TIPOS,
        materias: MATERIAS,
        comarcas: COMARCAS,
        competencias: COMPETENCIAS,
        escritorios: esc ? [esc] : [],
        faixasValor: FAIXAS,
    }
    if (!esc) return { meta, opcoes, previsoes: {}, pesos_treino: {} }
    let semente = esc === 'NG' ? 20261118 : 20261119
    const rnd = () => {
        semente = (semente * 1103515245 + 12345) % 2147483648
        return semente / 2147483648
    }
    const int = (a: number, b: number) => Math.round(a + (b - a) * rnd())
    const g = (campo: keyof typeof GRUPO, v: string) => (GRUPO[campo] as Record<string, string>)[v] ?? v

    const previsoes: PrevisaoResponse['previsoes'] = {}
    const pesos: Record<string, number> = {}
    const procedencia: Record<string, number[]> = {}
    const historico: Record<string, number[]> = {}
    for (const t of TIPOS)
        for (const m of MATERIAS)
            for (const c of COMARCAS)
                for (const k of COMPETENCIAS)
                    for (const fx of FAIXAS) {
                        const chaveModelo = [t, g('materia', m), g('comarca', c), g('competencia', k), esc, fx].join(
                            '|',
                        )
                        previsoes[chaveModelo] ??= [
                            int(60, 480),
                            int(80, 700),
                            int(300, 600),
                            int(200, 450),
                            int(200, 400),
                            int(20, 300),
                            int(0, 80),
                            int(0, 120),
                            int(50, 600),
                        ]
                        if (rnd() < 0.35) continue // combinação sem processos de treino
                        const real = [m, c, k, t, esc, fx].join('|')
                        const n = int(1, c === 'MANAUS' ? 220 : 40)
                        pesos[real] = n
                        const j1 = int(0, n)
                        const j2 = int(0, j1)
                        procedencia[real] = [j1, int(0, j1), j2, int(0, j2)]
                        historico[real] = [n, int(0, Math.ceil(n / 25))]
                    }

    const km = (mediana: number) => {
        const linhas: number[][] = []
        for (let t = 0; t <= 1500; t += 15) linhas.push([t, int(0, Math.round(1200 / mediana)), int(0, 2)])
        return linhas
    }
    return {
        meta,
        gerado_em: '2026-11-10',
        modelo: 'XGBoost-AFT (Fase 4/5, num_boost_round=73, + ano de distribuição)',
        n_treino: Object.values(pesos).reduce((a, b) => a + b, 0),
        fracao_extinto_1g_desfavoravel: 0.3,
        opcoes,
        grupo_modelo: GRUPO,
        previsoes,
        pesos_treino: pesos,
        procedencia,
        historico_acordo_pre: historico,
        exibicao: {
            procedencia_1g: 'previsao',
            procedencia_2g: 'previsao',
            acordo_pre: 'previsao',
            acordo_pos: 'previsao',
        },
        km_materia: Object.fromEntries(MATERIAS.map((m, i) => [m, km(200 + 60 * i)])),
        metricas_procedencia: { '1G': { auc_xgb: 0.67, auc_logistica: 0.667 } },
        metricas_procedencia_2g: { modelo: 'xgboost', auc_xgb: 0.68, auc_logistica: 0.744 },
        metricas: {
            cindex: {
                Cox: { teste: 0.6257, ic95_min: 0.6174, ic95_max: 0.6347 },
                RSF_tunada: { teste: 0.6125, ic95_min: 0.6048, ic95_max: 0.6235 },
                XGBoost_AFT: { teste: 0.6463, ic95_min: 0.637, ic95_max: 0.6558 },
            },
            vitorias_pareadas_bootstrap: { xgb_vs_cox_pct: 100, xgb_vs_rsf_pct: 100, rsf_vs_cox_pct: 0 },
            brier_score_integrado: { Cox: 0.201, RSF_tunada: 0.174, XGBoost_AFT: 0.1032 },
            calibracao_90_dias: [
                ...[0.96, 0.9, 0.82, 0.7].map((p, i) => ({
                    modelo: 'Cox',
                    quartil: i + 1,
                    previsto: p,
                    observado: p - 0.2,
                })),
                ...[0.94, 0.88, 0.8, 0.72].map((p, i) => ({
                    modelo: 'RSF_tunada',
                    quartil: i + 1,
                    previsto: p,
                    observado: p - 0.17,
                })),
                ...[0.8, 0.66, 0.55, 0.43].map((p, i) => ({
                    modelo: 'XGBoost_AFT',
                    quartil: i + 1,
                    previsto: p,
                    observado: p - 0.02,
                })),
            ],
        },
    }
}
