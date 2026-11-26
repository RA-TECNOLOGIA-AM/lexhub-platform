import type { ExportReport } from '../../../lib/exportFields.ts'
import { marketingExport } from '../marketing-lexpre/exportFields.ts'

// Os relatórios do Marketing (banco NG): os do Marketing (LexPre), com a coluna "Base" (Banco NG | LexPre) no de
// Leads, que junta os leads dos dois bancos como a página (app/dashboards/marketing.py, CAMPOS_LEADS). O Facebook Ads
// é o do Marketing (LexPre) do escritório da NG.
export const marketingNgExport: ExportReport[] = marketingExport.map((r) =>
    r.key === null
        ? {
              ...r,
              groups: r.groups.map((g, i) =>
                  i === 0 ? { ...g, fields: [{ slug: 'base', label: 'Base' }, ...g.fields] } : g,
              ),
          }
        : r,
)
