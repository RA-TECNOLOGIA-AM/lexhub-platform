import type { DashboardCatalog } from '../types.ts'
import { minAgo } from './helpers.ts'

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