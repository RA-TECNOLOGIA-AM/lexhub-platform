import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, HeroStat, MiniStat } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import type { IconName } from '../../../components/ui/Icon.tsx'
import { topN } from '../../../lib/charts.ts'
import { fmt } from '../../../lib/format.ts'
import type { WithComparison } from '../../../types/index.ts'
import { share } from '../setor/setor.ts'
import type { ComercialLexpreResponse } from './types.ts'

// Os 8 canais de origem dos contratos, na ordem da v1 (campo `clientes_<slug>` da API).
const CANAIS: { slug: string; label: string; icon: IconName }[] = [
    { slug: 'campanha', label: 'Campanha', icon: 'target' },
    { slug: 'redes_sociais', label: 'Redes sociais', icon: 'users' },
    { slug: 'retorno', label: 'Retorno', icon: 'undo' },
    { slug: 'resgate', label: 'Resgate', icon: 'refresh' },
    { slug: 'externos', label: 'Externos', icon: 'building' },
    { slug: 'indicacao', label: 'Indicação', icon: 'users' },
    { slug: 'site', label: 'Site', icon: 'flow' },
    { slug: 'parceiros', label: 'Parceiros', icon: 'briefcase' },
]

// Seção 01 · Captação (grade da v1), a mesma no Comercial e na Comissão Comercial (LexPre).
export function CaptacaoSection({ stats: s }: { stats: ComercialLexpreResponse['stats'] }) {
    const canal = (slug: string) => s[`clientes_${slug}` as keyof typeof s] as WithComparison | undefined
    const contratos = s.clientes_todos.total
    const principalCanal = topN(
        CANAIS.map((c) => ({ name: c.label, value: canal(c.slug)?.total ?? 0 })),
        1,
    )[0]

    return (
        <DashSection
            index={1}
            eyebrow="Captação"
            title="Origem dos contratos"
            subtitle="Clientes que assinaram contrato no período, por canal de origem."
        >
            {/* Grade da v1: 8 canais (4 × 2), Total contratos e Ações fechadas altos (2 linhas) e,
                entre eles, Cancelados sobre Aproveitamento. */}
            <div className="grid captacao-grid grid-mini-stack">
                {CANAIS.map((c) => {
                    const v = canal(c.slug)
                    return (
                        <MiniStat
                            key={c.slug}
                            label={c.label}
                            icon={c.icon}
                            tone="neutral"
                            value={<CountUp value={v?.total ?? 0} format={fmt.int} />}
                            below={<DeltaPill value={v?.comparativo ?? null} suffix="vs mês anterior" plain />}
                            hint={`Contratos assinados no período vindos de ${c.label.toLowerCase()}.`}
                        />
                    )
                })}
                <HeroStat
                    className="cap-alto cap-total"
                    label="Total contratos"
                    icon="sheet"
                    tone="accent"
                    value={<CountUp value={contratos} format={fmt.int} />}
                    below={<DeltaPill value={s.clientes_todos.comparativo} suffix="vs mês anterior" plain />}
                    hint="Clientes que assinaram contrato no período (todos os canais)."
                    footer={
                        principalCanal?.value ? (
                            <span className="cap-nota">
                                Principal canal:{' '}
                                <strong className="tone-text-accent">
                                    {principalCanal.name} ({fmt.dec1(share(principalCanal.value, contratos))}%)
                                </strong>
                            </span>
                        ) : undefined
                    }
                />
                <MiniStat
                    className="cap-cancelados"
                    label="Cancelados"
                    icon="x-circle"
                    tone="danger"
                    value={<CountUp value={s.demandas_canceladas.total} format={fmt.int} />}
                    below={
                        <DeltaPill
                            value={s.demandas_canceladas.comparativo}
                            betterWhenDown
                            suffix="vs mês anterior"
                            plain
                        />
                    }
                    hint="Demandas canceladas no período."
                />
                <MiniStat
                    className="cap-aproveitamento"
                    label="Aproveitamento"
                    icon="percent"
                    tone="info"
                    value={<CountUp value={s.taxa_aproveitamento.total} format={fmt.dec2} />}
                    below={<DeltaPill value={s.taxa_aproveitamento.comparativo} suffix="vs mês anterior" plain />}
                    hint="Ações fechadas por contrato no período (razão, não %)."
                />
                <HeroStat
                    className="cap-alto cap-acoes"
                    label="Ações fechadas"
                    icon="scale"
                    tone="ok"
                    value={<CountUp value={s.acoes_fechadas.total} format={fmt.int} />}
                    below={<DeltaPill value={s.acoes_fechadas.comparativo} suffix="vs mês anterior" plain />}
                    hint="Ações (rubricas) fechadas nos contratos do período; rubrica reunida conta cada componente."
                    footer={
                        <span className="cap-nota">
                            <strong className="num">{fmt.int(s.rubricas_reunidas_fechadas)}</strong> rubricas reunidas
                        </span>
                    }
                />
            </div>
        </DashSection>
    )
}
