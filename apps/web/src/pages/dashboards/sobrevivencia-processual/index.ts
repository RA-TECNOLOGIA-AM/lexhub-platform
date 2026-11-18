import { dataClient } from '../../../services/client.ts'
import type { DashboardModule } from '../types.ts'
import { SobrevivenciaContent } from './SobrevivenciaContent.tsx'
import type { SobrevivenciaResponse } from './sobrevivencia.ts'

// Sobrevivência Processual (TCC, área Estratégico): a coorte do estudo (NG + LA/AM) com Kaplan-Meier no navegador.
// Os filtros ficam na própria página (escritório e cliques nos gráficos), como na v1.
export const sobrevivenciaProcessual: DashboardModule<SobrevivenciaResponse> = {
    key: 'sobrevivencia-processual',
    fetch: (query) => dataClient.getDashboardData<SobrevivenciaResponse>('sobrevivencia-processual', query),
    Content: SobrevivenciaContent,
}
