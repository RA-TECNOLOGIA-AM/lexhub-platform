import type { Meta } from '../../../types/index.ts'

// Resposta de GET .../dashboards/meta-anual: o payload da rota /meta_anual_NG da v1 (em `data`), sem mudança.

export type Zona = 'TRISTE' | 'BASE' | 'AVANCADA' | 'SUPER'
export type ZonaUI = 'ENTRADA' | Zona // abaixo da Triste = Entrada (como a página da v1)
export type Trimestre = '1T' | '2T' | '3T' | '4T'

export type CardTrimestre = {
    trimestre: Trimestre
    status: 'concluido' | 'em_curso' | 'a_iniciar'
    atingido: number
    atingido_compare: number // o mesmo trimestre do ano anterior
    variacao_pct_vs_compare: number | null
    meta_triste: number
    meta_base: number
    meta_avancada: number
    meta_super: number
    atingido_mensal: Record<string, number> // '10' -> outubro
}

export type PredicaoTrimestre = {
    trimestre: Trimestre
    status: 'futuro' | 'concluido' | 'em_curso'
    meta: number // a Super Meta do trimestre
    expectativa_ate_hoje: number
    realizado: number
    gap: number
    gap_pct: number | null
    frac_decorrida_pct: number
    falta: number
    atingido_pct: number
    distancia_pct: number
    meta_atingida: boolean
}

export type Predicao = {
    meta_nivel_usado: string
    frac_trimestre_pct: number
    frac_ano_pct: number
    expectativa_hoje: {
        meta_super_trimestre: number
        frac_dias_trimestre_pct: number
        expectativa: number
        realizado: number
        gap: number
        gap_pct: number | null
        status: 'acima' | 'no_ritmo' | 'abaixo' | 'sem_dados'
        mensagem: string
    }
    expectativa_ytd: { expectativa: number; realizado: number; gap: number; gap_pct: number | null }
    projecao_fim_ano: {
        valor_projetado: number
        meta_referencia: number
        zona_projetada: ZonaUI
        excede_meta_pct: number | null
    }
    ritmo_diario: {
        dias_restantes: number
        falta_no_trimestre: number
        necessario_por_dia: number
        atual_por_dia_30d: number
        diferenca_diaria: number
    }
    super_meta_anual: {
        meta: number
        realizado_ytd: number
        expectativa_ytd: number
        gap_ytd: number
        gap_ytd_pct: number | null
        falta: number
        atingido_pct: number
        distancia_pct: number
        frac_ano_pct: number
        meta_atingida: boolean
    }
    ritmo_diario_anual: {
        dias_restantes: number
        falta_no_ano: number
        necessario_por_dia: number
        necessario_por_mes: number
        necessario_por_semestre: number
        atual_por_dia_30d: number
        atual_por_mes_30d: number
        atual_por_semestre_30d: number
        diferenca_diaria: number
    }
    por_trimestre: PredicaoTrimestre[]
}

export type MetaAnualData = {
    year: number
    compare_year: number
    as_of: string // 'AAAA-MM-DD'
    trimestre_atual: Trimestre
    metas: Record<Zona, Record<Trimestre | 'TOTAL', number>>
    ytd: {
        quarters: Trimestre[] // os trimestres até o atual
        atingido: number
        atingido_compare: number // o ano anterior até o mesmo dia
        variacao_pct_vs_compare: number | null
        metas: Record<Zona, number> // anuais
        zona: Zona
        proxima_zona: Zona | null
        falta_para_proxima_zona: number
    }
    cards_trimestre: CardTrimestre[]
    predicao?: Predicao | null
}

export type MetaAnualResponse = { meta: Meta; data?: MetaAnualData }
