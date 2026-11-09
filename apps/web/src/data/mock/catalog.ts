import type { DashboardCatalog, DashboardSummary } from '../types.ts'
import { minAgo } from './helpers.ts'

// Unidades mais usadas, para não repetir a lista em cada dashboard.
const ALL = ['NG', 'LA_AM', 'LA_RJ']
const NG_AM = ['NG', 'LA_AM']

type EntryParams = {
    key: string
    title: string
    area: string
    desc: string
    units: string[]
    source?: string // padrão: LexPre
    syncedMin?: number // há quantos minutos sincronizou (padrão: 4)
    maxDelayMin?: number // passou disso = "Fonte atrasada" (padrão: 60)
}

// Módulo: monta uma entrada do catálogo. Só o que muda vem por parâmetro; o resto tem padrão.
function entry({ source = 'LexPre', syncedMin = 4, maxDelayMin = 60, ...d }: EntryParams): DashboardSummary {
    // Mock: o usuário de teste é controller, que exporta e vê comissão em todos os setores.
    return {
        ...d,
        source,
        synced_at: minAgo(syncedMin),
        max_delay_min: maxDelayMin,
        can_export: true,
        can_see_commission: true,
    }
}

// Catálogo que a API devolveria para o usuário logado (app.my_dashboards()).
// A ordem define a ordem das áreas no hub.
export const catalog: DashboardCatalog = {
    available: [
        // Comercial
        entry({
            key: 'comercial-lexpre',
            title: 'Funil comercial',
            area: 'Comercial',
            desc: 'Atendimentos, contratos fechados e conversão.',
            units: ALL,
            syncedMin: 8,
        }),
        entry({
            key: 'comissao',
            title: 'Comissão',
            area: 'Comercial',
            desc: 'Comissão por atendente e por rubrica.',
            units: NG_AM,
            syncedMin: 8,
        }),
        entry({
            key: 'nps',
            title: 'NPS',
            area: 'Comercial',
            desc: 'Satisfação dos clientes.',
            units: NG_AM,
            syncedMin: 180,
        }),
        entry({
            key: 'marketing',
            title: 'Marketing',
            area: 'Comercial',
            desc: 'Leads e canais de origem.',
            units: ['NG'],
            syncedMin: 60,
            maxDelayMin: 120,
        }),

        // Operação jurídica
        entry({
            key: 'protocolo-lexpre',
            title: 'Protocolo',
            area: 'Operação jurídica',
            desc: 'Protocolados, represados e devoluções do setor Protocolo.',
            units: ALL,
        }),
        entry({
            key: 'pendencias',
            title: 'Pendências',
            area: 'Operação jurídica',
            desc: 'Pendências abertas, resolvidas e tempo de resolução.',
            units: ALL,
        }),
        entry({
            key: 'peticionamento-lexpre',
            title: 'Peticionamento',
            area: 'Operação jurídica',
            desc: 'Peticionados, represados e valor de causa.',
            units: ALL,
        }),
        entry({
            key: 'org-documentos-lexpre',
            title: 'Organização de documentos',
            area: 'Operação jurídica',
            desc: 'Documentos organizados e devolvidos.',
            units: ALL,
        }),
        entry({
            key: 'pre-protocolo',
            title: 'Pré-protocolo',
            area: 'Operação jurídica',
            desc: 'Processos em preparação para o protocolo.',
            units: ['NG', 'LA_RJ'],
            syncedMin: 6,
        }),

        // Execução e recursal
        entry({
            key: 'execucao',
            title: 'Execução',
            area: 'Execução e recursal',
            desc: 'Processos em execução e valores.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'acordos',
            title: 'Acordos',
            area: 'Execução e recursal',
            desc: 'Acordos fechados e valores.',
            units: ALL,
            source: 'LexFlow',
            syncedMin: 6,
        }),
        entry({
            key: 'recursal',
            title: 'Recursal',
            area: 'Execução e recursal',
            desc: 'Recursos e julgados.',
            units: NG_AM,
            source: 'LexFlow',
            syncedMin: 6,
        }),

        // Gestão
        entry({
            key: 'estrategico',
            title: 'Estratégico',
            area: 'Gestão',
            desc: 'Visão geral das unidades.',
            units: ['Consolidado'],
            source: '3 unidades',
            syncedMin: 10,
        }),
        entry({
            key: 'despesas',
            title: 'Despesas',
            area: 'Gestão',
            desc: 'Contas a pagar e a receber.',
            units: ['Consolidado'],
            source: 'Conta Azul',
            syncedMin: 12,
        }),
        entry({
            key: 'meta-anual',
            title: 'Meta anual',
            area: 'Gestão',
            desc: 'Meta do ano e quanto já foi atingido.',
            units: NG_AM,
            syncedMin: 60,
            maxDelayMin: 120,
        }),
    ],
    // Todos viraram cards; a seção "Chegando na V2" fica vazia.
    upcoming: [],
}
