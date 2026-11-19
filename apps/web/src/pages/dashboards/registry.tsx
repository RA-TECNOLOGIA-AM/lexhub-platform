import { lazy, type ComponentType } from 'react'
import type { Meta } from '../../types/index.ts'
import { DashboardView } from './DashboardView.tsx'
import type { DashboardModule } from './types.ts'

// Transforma um módulo de dashboard numa página pronta (que não recebe parâmetros).
function toPage<T extends { meta: Meta }>(module: DashboardModule<T>): ComponentType {
    return function DashboardModulePage() {
        return <DashboardView module={module} />
    }
}

// Página carregada sob demanda: o módulo (e os gráficos dele) só é baixado quando o dashboard abre.
// `pick` escolhe o export do index.ts da pasta (ex.: (m) => m.comercialLexpre).
function lazyDashboard<M, T extends { meta: Meta }>(
    loader: () => Promise<M>,
    pick: (m: M) => DashboardModule<T>,
): ComponentType {
    return lazy(async () => ({ default: toPage(pick(await loader())) }))
}

// Todos os dashboards que já têm página na V2, pela key (a mesma do módulo e da pasta).
// Pares como na v1: <domínio> = banco NG, <domínio>-lexpre = banco LexPre.
// Dashboard novo = uma linha aqui. O import() precisa ser literal para o Vite gerar o chunk.
export const DASHBOARD_PAGES: Record<string, ComponentType> = {
    comercial: lazyDashboard(
        () => import('./comercial/index.ts'),
        (m) => m.comercial,
    ),
    'comercial-lexpre': lazyDashboard(
        () => import('./comercial-lexpre/index.ts'),
        (m) => m.comercialLexpre,
    ),
    comissao: lazyDashboard(
        () => import('./comissao/index.ts'),
        (m) => m.comissao,
    ),
    'comissao-lexpre': lazyDashboard(
        () => import('./comissao-lexpre/index.ts'),
        (m) => m.comissaoLexpre,
    ),
    marketing: lazyDashboard(
        () => import('./marketing/index.ts'),
        (m) => m.marketing,
    ),
    'marketing-lexpre': lazyDashboard(
        () => import('./marketing-lexpre/index.ts'),
        (m) => m.marketingLexpre,
    ),
    nps: lazyDashboard(
        () => import('./nps/index.ts'),
        (m) => m.nps,
    ),
    protocolo: lazyDashboard(
        () => import('./protocolo/index.ts'),
        (m) => m.protocolo,
    ),
    'protocolo-lexpre': lazyDashboard(
        () => import('./protocolo-lexpre/index.ts'),
        (m) => m.protocoloLexpre,
    ),
    pendencias: lazyDashboard(
        () => import('./pendencias/index.ts'),
        (m) => m.pendencias,
    ),
    'pendencias-lexpre': lazyDashboard(
        () => import('./pendencias-lexpre/index.ts'),
        (m) => m.pendenciasLexpre,
    ),
    'org-documentos': lazyDashboard(
        () => import('./org-documentos/index.ts'),
        (m) => m.orgDocumentos,
    ),
    'org-documentos-lexpre': lazyDashboard(
        () => import('./org-documentos-lexpre/index.ts'),
        (m) => m.orgDocumentosLexpre,
    ),
    peticionamento: lazyDashboard(
        () => import('./peticionamento/index.ts'),
        (m) => m.peticionamento,
    ),
    'peticionamento-lexpre': lazyDashboard(
        () => import('./peticionamento-lexpre/index.ts'),
        (m) => m.peticionamentoLexpre,
    ),
    'pre-protocolo': lazyDashboard(
        () => import('./pre-protocolo/index.ts'),
        (m) => m.preProtocolo,
    ),
    execucao: lazyDashboard(
        () => import('./execucao/index.ts'),
        (m) => m.execucao,
    ),
    acordos: lazyDashboard(
        () => import('./acordos/index.ts'),
        (m) => m.acordos,
    ),
    tickets: lazyDashboard(
        () => import('./tickets/index.ts'),
        (m) => m.tickets,
    ),
    'execucao-estrategico': lazyDashboard(
        () => import('./execucao-estrategico/index.ts'),
        (m) => m.execucaoEstrategico,
    ),
    'sobrevivencia-processual': lazyDashboard(
        () => import('./sobrevivencia-processual/index.ts'),
        (m) => m.sobrevivenciaProcessual,
    ),
    'previsao-individualizada': lazyDashboard(
        () => import('./previsao-individualizada/index.ts'),
        (m) => m.previsaoIndividualizada,
    ),
    replicas: lazyDashboard(
        () => import('./replicas/index.ts'),
        (m) => m.replicas,
    ),
    'emendas-manifestacoes': lazyDashboard(
        () => import('./emendas-manifestacoes/index.ts'),
        (m) => m.emendasManifestacoes,
    ),
    'pendencias-intermediarias': lazyDashboard(
        () => import('./pendencias-intermediarias/index.ts'),
        (m) => m.pendenciasIntermediarias,
    ),
    publicacoes: lazyDashboard(
        () => import('./publicacoes/index.ts'),
        (m) => m.publicacoes,
    ),
    recursal: lazyDashboard(
        () => import('./recursal/index.ts'),
        (m) => m.recursal,
    ),
    'julgados-sentencas': lazyDashboard(
        () => import('./julgados-sentencas/index.ts'),
        (m) => m.julgadosSentencas,
    ),
    'julgados-acordaos': lazyDashboard(
        () => import('./julgados-acordaos/index.ts'),
        (m) => m.julgadosAcordaos,
    ),
    estrategico: lazyDashboard(
        () => import('./estrategico/index.ts'),
        (m) => m.estrategico,
    ),
    despesas: lazyDashboard(
        () => import('./despesas/index.ts'),
        (m) => m.despesas,
    ),
    'meta-anual': lazyDashboard(
        () => import('./meta-anual/index.ts'),
        (m) => m.metaAnual,
    ),
    'financeiro-estrategico': lazyDashboard(
        () => import('./financeiro-estrategico/index.ts'),
        (m) => m.financeiroEstrategico,
    ),
}
