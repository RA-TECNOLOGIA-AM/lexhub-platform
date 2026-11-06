import type { DashboardCatalog, Me, PendenciasResponse, Point, ProtocoloResponse } from './types.ts'

// Dados FICTÍCIOS no formato das respostas da API (ver types.ts).

const now = Date.now()
const minAgo = (m: number) => new Date(now - m * 60_000).toISOString()

// Série diária determinística (dias úteis de outubro/2026), sem Math.random.
function porDia(base: number, amp: number, dias: number): Point[] {
    const out: Point[] = []
    for (let d = 1; d <= dias; d++) {
        const wd = new Date(2026, 9, d).getDay()
        if (wd === 0 || wd === 6) continue
        const v = Math.round(base + amp * Math.sin(d * 1.7) + (d % 5) * 2)
        out.push({ name: String(d).padStart(2, '0') + '/10', value: Math.max(0, v) })
    }
    return out
}

const funcionarios = ['Carla Souza', 'Bruno Melo', 'Diego Rocha', 'Fernanda Lopes', 'Gabriel Torres', 'Helena Dias']
const protocoladosPorFunc = [312, 268, 231, 198, 161, 114]

export const me: Me = {
    user: { name: 'Luís Tápia', initials: 'LT', roleLabel: 'Controller · NG', canExport: true, canSeeCommission: true },
    org: { slug: 'lexgroup', name: 'LexGroup', sub: 'Piloto V2 · 1 unidade' },
    units: [
        { code: 'NG', name: 'Nicolas Gomes' },
        { code: 'LA_AM', name: 'Luis Albert AM' },
        { code: 'LA_RJ', name: 'Luis Albert RJ' },
    ],
}

// Catálogo que a API devolveria para o usuário logado (app.my_dashboards()).
export const catalog: DashboardCatalog = {
    available: [
        {
            key: 'protocolo-lexpre', title: 'Protocolo', area: 'Operação jurídica',
            desc: 'Protocolados, represados e devoluções do setor Protocolo.',
            units: ['NG', 'LA_AM', 'LA_RJ'], source: 'LexPre', synced_at: minAgo(4), max_delay_min: 60,
        },
        {
            key: 'pendencias', title: 'Pendências', area: 'Operação jurídica',
            desc: 'Pendências abertas, resolvidas e tempo de resolução.',
            units: ['NG', 'LA_AM', 'LA_RJ'], source: 'LexPre', synced_at: minAgo(4), max_delay_min: 60,
        },
    ],
    // Só para comunicar o roteiro no hub; não são clicáveis.
    upcoming: [
        { title: 'Peticionamento', area: 'Operação jurídica' },
        { title: 'Organização de documentos', area: 'Operação jurídica' },
        { title: 'Execução', area: 'Execução e recursal' },
        { title: 'Comercial', area: 'Comercial' },
    ],
}

// "Tamanho" de cada unidade no mock: trocar de unidade muda os números (NG = base).
const UNIT_SIZE: Record<string, number> = { NG: 1, LA_AM: 0.62, LA_RJ: 0.38 }

// Protocolo de uma unidade. Contagens e valores escalam com o tamanho; tempos e % não.
export function protocoloFor(unit: string): ProtocoloResponse {
    const k = UNIT_SIZE[unit] ?? 1
    const n = (v: number) => Math.round(v * k)
    const porFunc = protocoladosPorFunc.map(n)
    return {
        meta: { unit, from: '2026-10-01', to: '2026-10-31', source: 'LexPre', synced_at: minAgo(4) },
        stats: {
            protocolados_total: { total: n(1284), comparativo: 8.2 },
            valor_causa_protocolado: { total: 18432750.4 * k, comparativo: 5.1 },
            ticket_medio_protocolado: { total: 14355.72, comparativo: -2.8 },
            media_tempo_protocolado: 2.4,
            mediana_tempo_protocolado: 1.6,
            comparativo_tempo_medio_protocolado: -12.0,
            comparativo_mediana_tempo_protocolado: -6.5,
            represados: n(96),
            devolvido_peticionamento: n(41),
            devolvido_org_doc: n(17),
            devolvido_pendencia: n(23),
        },
        protocolados_por_dia: porDia(58 * k, 14 * k, 31),
        protocolados_por_materia: [
            { name: 'Bancário - empréstimo', value: n(412) },
            { name: 'Consumidor - telefonia', value: n(287) },
            { name: 'Aéreo - atraso de voo', value: n(214) },
            { name: 'Previdenciário', value: n(163) },
            { name: 'Bancário - cartão', value: n(121) },
            { name: 'Outras', value: n(87) },
        ],
        protocolados_por_funcionario: funcionarios.map((name, i) => ({ name, value: porFunc[i] })),
        represados_por_funcionario: funcionarios.map((name, i) => ({ name, value: n([21, 18, 17, 15, 14, 11][i]) })),
        comissionamento_por_funcionario: funcionarios.map((name, i) => ({
            funcionario: name,
            qtd_protocolados: porFunc[i],
            valor_comissao: porFunc[i] * 1.0,
        })),
    }
}

export const pendencias: PendenciasResponse = {
    meta: { unit: 'NG', from: '2026-10-01', to: '2026-10-31', source: 'LexPre', synced_at: minAgo(4) },
    stats: {
        pendencias_total: 742,
        pendencias_resolvidas: 655,
        pendencias_canceladas: 19,
        pendencias_taxa_resolvidos: 88.27,
        pendencias_taxa_nao_resolvidos: 9.16,
        pendencias_taxa_canceladas: 2.56,
        media_tempo_resolvidos_pendencia: 3.1,
        mediana_tempo_resolvidos_pendencia: 2.0,
        comparativo_pendencias_resolvidas: 6.4,
        comparativo_tempo_medio_resolvidos_pendencia: -9.3,
        pendencias_nao_resolvidas: 68,
        pendencias_nao_resolvidas_com_atraso: 23,
        pendencias_triagem: 12,
    },
    pendencias_resolvidas_por_dia: porDia(30, 8, 31),
    pendencias_nao_resolvidas_por_origem: [
        { name: 'Organização de documentos', value: 29 },
        { name: 'Peticionamento', value: 21 },
        { name: 'Protocolo', value: 12 },
        { name: 'Triagem', value: 6 },
    ],
    media_pendencias_resolvidas_por_funcionario: funcionarios
        .slice(0, 5)
        .map((n, i) => ({ name: n, value: [9.4, 8.1, 7.6, 6.2, 5.0][i] })),
    comissionamento_pendencias_por_funcionario: funcionarios.slice(0, 5).map((n, i) => {
        const tr = [98.1, 96.2, 91.0, 86.4, 79.5][i]
        const tc = [1.2, 2.4, 3.1, 6.0, 4.4][i]
        const q = [182, 157, 141, 102, 73][i]
        const valor = tr >= 97 && tc < 5 ? 3 : tr >= 85 ? 1 : 0
        return { funcionario: n, taxa_resolvido: tr, taxa_cancelamento: tc, qtd_resolvido: q, valor, qtd_x_valor: q * valor, comissao: q * valor }
    }),
}
// Usuários de teste do mock (só existem aqui, no navegador).
// No Supabase, cada um vira um usuário de verdade em Authentication > Users.
export const testUsers = [{ email: 'controller@lexgroup.com.br', password: 'lexhub123' }]