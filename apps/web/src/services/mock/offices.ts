import type { DataSource, ProductKey, ProductOffices, SourcesResponse, UnitSources } from '../../types/index.ts'
import { DataError } from '../errors.ts'

// Conectar fonte no mock: os escritórios do LexPre e do LexFlow (GET /sources/{product}/offices) e a
// ligação (api.link_product_office, migration 20261117100000_conectar_fonte.sql), com as mesmas regras.
// Os ids 1/2/3 (LexPre) e 20/21/27 (LexFlow) são os da LexGroup; os outros são fictícios.

const LABEL: Record<ProductKey, string> = { lexpre: 'LexPre', lexflow: 'LexFlow' }

const lexgroup = (unit: string, unitName: string) => ({ org: 'LexGroup', unit, unitName })

export const productOffices: Record<ProductKey, ProductOffices> = {
    lexpre: {
        product: 'lexpre',
        activityLabel: 'movimentações nos últimos 30 dias',
        offices: [
            { ref: '5', name: 'Escritório Belém', activity: 0, linkedTo: null },
            { ref: '4', name: 'Escritório Manaus Centro', activity: 128, linkedTo: null },
            { ref: '2', name: 'LA Advocacia', activity: 2087, linkedTo: lexgroup('LA_AM', 'Luis Albert AM') },
            { ref: '3', name: 'LA Rio de Janeiro', activity: 941, linkedTo: lexgroup('LA_RJ', 'Luis Albert RJ') },
            { ref: '1', name: 'Nicolas Gomes', activity: 3412, linkedTo: lexgroup('NG', 'Nicolas Gomes') },
        ],
    },
    lexflow: {
        product: 'lexflow',
        activityLabel: 'processos',
        offices: [
            { ref: '31', name: 'Escritório Manaus Centro', activity: 54, linkedTo: null },
            { ref: '21', name: 'LA Advocacia', activity: 870, linkedTo: lexgroup('LA_AM', 'Luis Albert AM') },
            { ref: '27', name: 'LA Rio de Janeiro', activity: 402, linkedTo: lexgroup('LA_RJ', 'Luis Albert RJ') },
            { ref: '20', name: 'Nicolas Gomes', activity: 1230, linkedTo: lexgroup('NG', 'Nicolas Gomes') },
        ],
    },
}

// A fonte do produto como a lista mostra logo depois de ligar: ainda sem dashboard ligado na unidade.
const productSource = (product: ProductKey): DataSource => ({
    id: product,
    connector: product,
    kind: product === 'lexpre' ? 'database' : 'flow',
    group: 'product',
    name: LABEL[product],
    detail: product === 'lexpre' ? 'Comercial e pré-protocolo' : 'Execução, acordos, recursal e publicações',
    managedBy: null,
    syncedAt: null,
    rows: null,
    failures: 0,
    status: 'no_dashboards',
})

export function linkOfficeIn(
    data: SourcesResponse,
    orgName: string,
    unitCode: string,
    product: ProductKey,
    ref: string,
): UnitSources {
    const unit = data.units.find((u) => u.unit.code === unitCode)
    if (!unit) throw new DataError(409, 'Unidade não encontrada.')
    if (unit.sources.some((s) => s.id === product)) {
        throw new DataError(409, `Esta unidade já está ligada ao ${LABEL[product]}.`)
    }
    const office = productOffices[product].offices.find((o) => o.ref === ref)
    if (!office) throw new DataError(409, 'Escolha um escritório da lista.')
    if (office.linkedTo) {
        throw new DataError(
            409,
            `Este escritório já está ligado à unidade ${office.linkedTo.org} · ${office.linkedTo.unit}.`,
        )
    }
    office.linkedTo = { org: orgName, unit: unit.unit.code, unitName: unit.unit.name }
    unit.sources.push(productSource(product))
    return unit
}
