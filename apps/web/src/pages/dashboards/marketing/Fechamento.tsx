import type { CSSProperties } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { RoscaLegenda } from './RoscaLegenda.tsx'
import {
    comoNg,
    participacao,
    rubricasComparadas,
    type Dimensao,
    type Leitor,
    type RubricaComparada,
} from './marketingComum.ts'

const pct1 = (v: number) => `${fmt.dec1(v)}%`

type Campanha = {
    sigla?: string // 'RA' | 'NG'; sem = campanha única (LexPre)
    tone: Tone
    conversao: number
    fechados: number
    protocolados: number
    valorCausa: number
    ticket: number
    destaque: boolean // a campanha com mais clientes fechados ganha a borda
}

function PainelCampanha({ c }: { c: Campanha }) {
    const sufixo = c.sigla ? ` ${c.sigla}` : ''
    const boxes: { label: string; value: number; format: (v: number) => string; cor: string }[] = [
        { label: `Fechados${sufixo}`, value: c.fechados, format: fmt.int, cor: 'var(--text)' },
        { label: `Protocolados${sufixo}`, value: c.protocolados, format: fmt.int, cor: 'var(--ok)' },
        { label: 'Valor de causa', value: c.valorCausa, format: fmt.brl, cor: 'var(--c-info)' },
        { label: 'Ticket médio', value: c.ticket, format: fmt.brl, cor: 'var(--accent)' },
    ]
    return (
        <div className={`card mkt-camp tone-${c.tone}${c.destaque ? ' destaque' : ''}`}>
            <div className="mkt-camp-head">
                <span className="mkt-camp-nome">
                    {c.sigla && <span className="mkt-camp-sigla num">{c.sigla}</span>}
                    <strong>{`Campanha${sufixo}`}</strong>
                </span>
                <Pill tone={c.conversao > 0 ? 'ok' : 'neutral'}>{`Conversão: ${pct1(c.conversao)}`}</Pill>
            </div>
            <div className="mkt-camp-boxes">
                {boxes.map((b) => (
                    <div key={b.label} className="mkt-camp-box">
                        <span className="mkt-camp-box-l">{b.label}</span>
                        <strong
                            className="num"
                            style={{ color: b.value > 0 ? b.cor : 'var(--text-muted)' } as CSSProperties}
                        >
                            <CountUp value={b.value} format={b.format} />
                        </strong>
                    </div>
                ))}
            </div>
        </div>
    )
}

// Comparativo por rubrica: campanha e protocolado lado a lado (os dois gráficos de rubrica da v1 numa tabela).
function TabelaRubricas(p: {
    linhas: RubricaComparada[]
    comRa: boolean
    selected: string[]
    onSelect?: (name: string) => void
}) {
    const maxCamp = Math.max(0, ...p.linhas.map((l) => l.campanha.ng + l.campanha.ra))
    const maxProt = Math.max(0, ...p.linhas.map((l) => l.protocolado.ng + l.protocolado.ra))
    const isSel = (name: string) => p.selected.some((s) => s.toUpperCase() === name.toUpperCase())
    const celula = (v: { ng: number; ra: number }, max: number, cor: string) => (
        <span className="mkt-rub-cel">
            <span className="mkt-trilho">
                <span style={{ '--w': `${participacao(v.ng + v.ra, max)}%`, '--cor': cor } as CSSProperties} />
            </span>
            <strong className="num" style={{ color: cor === 'var(--ok-dot)' ? 'var(--ok)' : undefined }}>
                {fmt.int(p.comRa ? v.ng : v.ng + v.ra)}
            </strong>
            {p.comRa && <span className="num muted small">(RA: {fmt.int(v.ra)})</span>}
        </span>
    )
    if (p.linhas.length === 0) return <p className="chart-empty muted small">Sem dados no período.</p>
    return (
        <div className="mkt-rub" role="table" aria-label="Comparativo por rubrica">
            <div className="mkt-rub-linha mkt-rub-cab" role="row">
                <span role="columnheader">Rubrica</span>
                <span role="columnheader">{p.comRa ? 'Campanha (NG / RA)' : 'Campanha'}</span>
                <span role="columnheader">{p.comRa ? 'Protocolado (NG / RA)' : 'Protocolado'}</span>
                <span role="columnheader">Relação prot. / camp.</span>
            </div>
            {p.linhas.map((l) => (
                <button
                    key={l.name}
                    type="button"
                    role="row"
                    disabled={!p.onSelect}
                    aria-pressed={p.onSelect ? isSel(l.name) : undefined}
                    aria-label={`Filtrar pela rubrica ${l.name}`}
                    className={`mkt-rub-linha${p.selected.length > 0 && !isSel(l.name) ? ' dim' : ''}`}
                    onClick={() => p.onSelect?.(l.name)}
                >
                    <span role="cell" className="mkt-rub-nome num" title={l.name}>
                        {l.name}
                    </span>
                    <span role="cell">{celula(l.campanha, maxCamp, 'var(--c-info)')}</span>
                    <span role="cell">{celula(l.protocolado, maxProt, 'var(--ok-dot)')}</span>
                    <span role="cell" className="mkt-rub-rel num tone-text-accent">
                        {l.campanha.ng + l.campanha.ra > 0 ? `${Math.round(l.relacao)}%` : '—'}
                    </span>
                </button>
            ))}
        </div>
    )
}

type FechamentoProps = {
    ler: Leitor
    index: number
    raNg: boolean // Marketing (banco NG): as campanhas RA e NG; LexPre: uma campanha só
    filters: DashboardFilters
    onToggleFilter?: (key: Dimensao, value: string) => void
}

// 04 · Fechamento de campanhas: os painéis de cada campanha, as roscas por campanha e o comparativo por rubrica.
// A rubrica clicada só recorta esta seção (como na v1).
export function Fechamento({ ler, index, raNg, filters, onToggleFilter }: FechamentoProps) {
    const { n, serie, rubricasRaNg } = ler
    const campanhas: Campanha[] = raNg
        ? (['ra', 'ng'] as const).map((c) => ({
              sigla: c.toUpperCase(),
              tone: c === 'ra' ? 'danger' : 'info',
              conversao: n(`conversao_${c}`),
              fechados: n(`campanha_${c}`),
              protocolados: n(`protocolados_${c}`),
              valorCausa: n(`valor_causa_${c}`),
              ticket: n(`ticket_medio_${c}`),
              destaque: n(`campanha_${c}`) >= n(`campanha_${c === 'ra' ? 'ng' : 'ra'}`) && n(`campanha_${c}`) > 0,
          }))
        : [
              {
                  tone: 'accent',
                  conversao: n('conversao_campanha'),
                  fechados: n('campanha'),
                  protocolados: n('protocolados_campanha'),
                  valorCausa: n('valor_causa_campanha'),
                  ticket: n('ticket_medio_campanha'),
                  destaque: false,
              },
          ]
    const linhas = raNg
        ? rubricasComparadas(rubricasRaNg('rubrica_campanha'), rubricasRaNg('rubrica_protocolado'))
        : rubricasComparadas(comoNg(serie('rubrica_campanha')), comoNg(serie('rubrica_protocolado')))
    const rubrica: Dimensao = 'rubrica_marketing'

    return (
        <DashSection
            index={index}
            eyebrow="Fechamento Campanhas"
            title={raNg ? 'Fechamento de campanhas (RA × NG)' : 'Fechamento de campanhas'}
            subtitle="Clientes fechados, conversão, protocolados e valor de causa. Clique numa rubrica para filtrar esta seção."
        >
            <div className={raNg ? 'mkt-grid-2' : undefined}>
                {campanhas.map((c) => (
                    <PainelCampanha key={c.sigla ?? 'campanha'} c={c} />
                ))}
            </div>
            <div className="mkt-grid-3 grid-mini">
                <ChartCard title="Total de clientes" subtitle="Por campanha vs. base geral">
                    <RoscaLegenda items={serie('total_clientes_campanha')} centerLabel="clientes" />
                </ChartCard>
                <ChartCard title="Protocolo resolvido" subtitle="Por campanha vs. base geral">
                    <RoscaLegenda items={serie('protocolo_resolvido_total')} centerLabel="protocolados" />
                </ChartCard>
                <ChartCard title="Valor de causa" subtitle="Por campanha vs. base geral">
                    <RoscaLegenda
                        items={serie('valor_causa_total')}
                        centerLabel="valor causa"
                        format={fmt.brlShort}
                        centerFormat={fmt.brlShort}
                    />
                </ChartCard>
            </div>
            <div className="grid-mini">
                <ChartCard
                    title={
                        raNg ? 'Comparativo por rubrica — campanha & protocolado (RA × NG)' : 'Comparativo por rubrica'
                    }
                    subtitle="Clique em qualquer rubrica abaixo para filtrar os indicadores desta seção"
                >
                    <TabelaRubricas
                        linhas={linhas}
                        comRa={raNg}
                        selected={filters[rubrica] ?? []}
                        onSelect={onToggleFilter && ((name) => onToggleFilter(rubrica, name))}
                    />
                </ChartCard>
            </div>
        </DashSection>
    )
}
