import { DataError } from '../../services/errors.ts'
import type { DashboardCatalog, Meta } from '../../types/index.ts'
import type { Period } from '../../lib/period.ts'

// Módulo: o "meta" de um dashboard que ainda não tem dados próprios na V2, montado a partir do catálogo.
// É o que o cabeçalho precisa: unidade, fonte, quando atualizou e o período escolhido. O fuso fica vazio (sem dados ainda).
// period: o escolhido na tela (vazio = sem período ainda).
export function baseMeta(catalog: DashboardCatalog, key: string, unit: string, period: Partial<Period> = {}): Meta {
    const summary = catalog.available.find((d) => d.key === key)
    // Mesma regra da API: dashboard inexistente ou unidade não liberada = 403 (não revela o que existe).
    if (!summary || !summary.units.includes(unit)) {
        throw new DataError(403, 'Você não tem acesso a este dashboard nesta unidade')
    }
    return {
        unit,
        from: period.from ?? '',
        to: period.to ?? '',
        source: summary.source,
        synced_at: summary.synced_at,
        timezone: '',
    }
}
