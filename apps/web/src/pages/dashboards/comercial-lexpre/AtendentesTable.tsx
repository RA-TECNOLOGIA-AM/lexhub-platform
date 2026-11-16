import { useState } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { fmt } from '../../../lib/format.ts'
import { canaisDaTabela, mediaDaColuna } from './comercial.ts'
import type { LinhaAtendente } from './types.ts'

type Ordem = 'leads_geral' | 'clientes_geral' | 'taxa_geral'

const ORDENS: { value: Ordem; label: string }[] = [
    { value: 'leads_geral', label: 'Leads (geral)' },
    { value: 'clientes_geral', label: 'Clientes (geral)' },
    { value: 'taxa_geral', label: '% fechamento (geral)' },
]

// Módulo: "Detalhamento por Atendente" da v1: leads, clientes e % de fechamento no geral e em cada canal.
// Verde = acima da média do time naquela coluna; vermelho = abaixo. Atendente na 1ª coluna fica fixo ao rolar.
export function AtendentesTable({
    linhas,
    totais,
    filteredTo,
    onFilterPerson,
}: {
    linhas: LinhaAtendente[]
    totais?: LinhaAtendente
    filteredTo: string[]
    onFilterPerson?: (name: string) => void
}) {
    const [ordem, setOrdem] = useState<Ordem>('leads_geral')
    if (linhas.length === 0) return <ChartEmpty>Nenhum atendente com lead no período.</ChartEmpty>
    const canais = canaisDaTabela(linhas)
    const ordenadas = [...linhas].sort((a, b) => (Number(b[ordem]) || 0) - (Number(a[ordem]) || 0))
    const colunas = canais.flatMap((c) => [
        { key: `leads_${c.slug}`, canal: c.label, label: 'Lead', taxa: false, first: true },
        { key: `clientes_${c.slug}`, canal: c.label, label: 'Cliente', taxa: false, first: false },
        { key: `taxa_${c.slug}`, canal: c.label, label: '% fecha', taxa: true, first: false },
    ])
    const medias = Object.fromEntries(colunas.map((c) => [c.key, mediaDaColuna(linhas, c.key)]))
    const valor = (v: unknown, taxa: boolean) => (taxa ? fmt.pct(Number(v) || 0) : fmt.int(Number(v) || 0))

    return (
        <div className="at-table-card">
            <div className="meta-card-head">
                <span className="meta-card-title">Detalhamento por Atendente</span>
                <label className="field-select">
                    <span className="sr-only">Ordenar por</span>
                    <select value={ordem} onChange={(e) => setOrdem(e.target.value as Ordem)}>
                        {ORDENS.map((o) => (
                            <option key={o.value} value={o.value}>
                                Ordenar: {o.label}
                            </option>
                        ))}
                    </select>
                </label>
            </div>
            <div className="at-table-wrap">
                <table className="at-table">
                    <thead>
                        <tr>
                            <th rowSpan={2} scope="col" className="at-sticky">
                                Atendente
                            </th>
                            {canais.map((c) => (
                                <th key={c.slug} colSpan={3} scope="colgroup" className="at-group">
                                    {c.label}
                                </th>
                            ))}
                        </tr>
                        <tr>
                            {colunas.map((c) => (
                                <th key={c.key} scope="col" className={c.first ? 'at-first num' : 'num'}>
                                    {c.label}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {ordenadas.map((l, i) => {
                            const nome = String(l.atendente)
                            const ativo = filteredTo.includes(nome)
                            return (
                                <tr key={nome} className={ativo ? 'on' : undefined}>
                                    <th scope="row" className="at-sticky">
                                        <span className="meta-rank num">{i + 1}</span>
                                        {onFilterPerson ? (
                                            <button
                                                type="button"
                                                className="linkbtn at-name"
                                                aria-pressed={ativo}
                                                title={
                                                    ativo
                                                        ? 'Tirar o filtro deste atendente'
                                                        : 'Filtrar por este atendente'
                                                }
                                                onClick={() => onFilterPerson(nome)}
                                            >
                                                {nome}
                                            </button>
                                        ) : (
                                            <span className="at-name">{nome}</span>
                                        )}
                                    </th>
                                    {colunas.map((c) => {
                                        const v = Number(l[c.key]) || 0
                                        const tom =
                                            v === 0 ? '' : v >= medias[c.key] ? ' tone-text-ok' : ' tone-text-danger'
                                        return (
                                            <td key={c.key} className={`num${c.first ? ' at-first' : ''}${tom}`}>
                                                {valor(v, c.taxa)}
                                            </td>
                                        )
                                    })}
                                </tr>
                            )
                        })}
                    </tbody>
                    {totais && (
                        <tfoot>
                            <tr>
                                <th scope="row" className="at-sticky">
                                    Total
                                </th>
                                {colunas.map((c) => (
                                    <td key={c.key} className={`num${c.first ? ' at-first' : ''}`}>
                                        {valor(totais[c.key], c.taxa)}
                                    </td>
                                ))}
                            </tr>
                        </tfoot>
                    )}
                </table>
            </div>
        </div>
    )
}
