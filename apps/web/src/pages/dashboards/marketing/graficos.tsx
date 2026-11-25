import { BarList } from '../../../components/charts/BarList.tsx'
import { ColumnChart } from '../../../components/charts/ColumnChart.tsx'
import { PieChart } from '../../../components/charts/PieChart.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters, Point } from '../../../types/index.ts'
import { DIMENSOES, porFaixaEtaria, type Dimensao } from './marketingComum.ts'

export type Fmt = (v: number) => string

// Os gráficos de distribuição; com `dim`, clicar numa barra/fatia liga o filtro daquela dimensão.
export function graficos(filters: DashboardFilters, onToggleFilter?: (key: Dimensao, value: string) => void) {
    const clique = (dim: Dimensao) => ({
        selected: filters[dim] ?? [],
        onSelect: onToggleFilter && ((name: string) => onToggleFilter(dim, name)),
        selectLabel: `Filtrar por ${DIMENSOES[dim].toLowerCase()}`,
    })
    return {
        clique,
        barras: (items: Point[], dim?: Dimensao, format: Fmt = fmt.int) => (
            <BarList items={items} format={format} showShare valueOutside {...(dim ? clique(dim) : {})} />
        ),
        rosca: (items: Point[], centerLabel: string, dim?: Dimensao, format: Fmt = fmt.int) => (
            <PieChart
                items={items}
                format={format}
                centerLabel={centerLabel}
                labels
                labelsTwoLines
                legendWhenNarrow
                max={8}
                {...(dim ? clique(dim) : {})}
            />
        ),
        faixaEtaria: (items: Point[]) => {
            const pts = porFaixaEtaria(items)
            return (
                <ColumnChart
                    height={260}
                    categories={pts.map((p) => p.name)}
                    series={[{ label: 'Clientes', color: 'var(--chart-1)', values: pts.map((p) => p.value) }]}
                    caption="Faixa etária"
                    {...clique('faixa_etaria_marketing')}
                />
            )
        },
    }
}
