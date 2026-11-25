import type { CSSProperties } from 'react'
import { ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { fmt } from '../../../lib/format.ts'
import type { Faixa } from './marketingComum.ts'

const pct0 = (v: number) => `${Math.round(v)}%`
const ALTURA_MAX = 120 // px da coluna maior

// Média salarial mensal: uma coluna por faixa respondida, com o número e o % de quem respondeu em cima. A faixa
// com mais clientes vai em laranja (destaque); as outras, em azul. "Não informado" fica fora das colunas.
export function ColunasSalario({ faixas }: { faixas: Faixa[] }) {
    const max = Math.max(0, ...faixas.map((f) => f.value))
    if (max === 0) return <ChartEmpty />
    return (
        <div className="mkt-colunas" role="list">
            {faixas.map((f) => (
                <div
                    key={f.name}
                    role="listitem"
                    aria-label={`${f.name}: ${fmt.int(f.value)} (${pct0(f.share)})`}
                    className={f.value === max ? 'mkt-coluna destaque' : 'mkt-coluna'}
                >
                    <div className="mkt-coluna-area">
                        <span className="mkt-coluna-v num">{fmt.int(f.value)}</span>
                        <span className="mkt-coluna-pct num">{pct0(f.share)}</span>
                        <span
                            className="mkt-coluna-barra"
                            style={{ height: Math.max(6, Math.round((f.value / max) * ALTURA_MAX)) }}
                        />
                    </div>
                    <span className="mkt-coluna-l num" title={f.name}>
                        {f.rotulo}
                    </span>
                </div>
            ))}
        </div>
    )
}

// Pessoas dependentes: um bloco por resposta (número, % e a barra), o mais comum em destaque. Clicar filtra a página.
export function GradeDependentes({
    itens,
    selected = [],
    onSelect,
    selectLabel = 'Filtrar por',
    linha = false,
}: {
    itens: Faixa[]
    selected?: string[]
    onSelect?: (name: string) => void
    selectLabel?: string
    linha?: boolean // todos os blocos numa linha só (card na largura inteira)
}) {
    const max = Math.max(0, ...itens.map((i) => i.value))
    if (max === 0) return <ChartEmpty />
    const isSel = (name: string) => selected.some((s) => s.toUpperCase() === name.toUpperCase())
    return (
        <div className={linha ? 'mkt-dep linha' : 'mkt-dep'}>
            {itens.map((i) => (
                <button
                    key={i.name}
                    type="button"
                    disabled={!onSelect}
                    aria-pressed={onSelect ? isSel(i.name) : undefined}
                    aria-label={`${onSelect ? `${selectLabel} ` : ''}${i.name}: ${fmt.int(i.value)} (${pct0(i.share)})`}
                    title={i.name}
                    className={[
                        'mkt-dep-item',
                        i.value === max ? 'destaque' : '',
                        selected.length > 0 && !isSel(i.name) ? 'dim' : '',
                    ]
                        .filter(Boolean)
                        .join(' ')}
                    onClick={() => onSelect?.(i.name)}
                >
                    <span className="mkt-dep-top">
                        <span className="mkt-dep-l">{i.rotulo}</span>
                        <span className="num muted">{pct0(i.share)}</span>
                    </span>
                    <strong className="mkt-dep-v num">{fmt.int(i.value)}</strong>
                    <span className="mkt-dep-barra" aria-hidden="true">
                        <span style={{ '--w': `${(i.value / max) * 100}%` } as CSSProperties} />
                    </span>
                </button>
            ))}
        </div>
    )
}
