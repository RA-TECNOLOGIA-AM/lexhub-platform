import { DeltaPill, FootRow, HeroStat, Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import { deltaTone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { fmt } from '../../../lib/format.ts'
import { leituraDevolucao, type Devolucoes } from './setor.ts'

// Módulo: as peças da seção "Devolução" dos dashboards de setor.

// Nome por extenso de cada destino (no texto da faixa).
const EXTENSO: Record<string, string> = {
    peticionamento: 'Peticionamento',
    org_doc: 'Organização Documental',
    pendencia: 'Pendência',
}

// Faixa com o total de devoluções e a barra dividida por destino.
export function DevolucaoResumo({ dev }: { dev: Devolucoes }) {
    const partes = dev.partes.map((p) => `${EXTENSO[p.key] ?? p.label} (${fmt.dec1(p.pct)}%)`)
    const texto = partes.length > 1 ? `${partes.slice(0, -1).join(', ')} e ${partes[partes.length - 1]}` : partes[0]
    return (
        <div className="card dev-sum">
            <ToneIcon icon="undo" tone="accent" />
            <div className="dev-sum-text">
                <span className="dev-sum-title">
                    <span className="hero-l">Total de devoluções ativas:</span>
                    <strong className="num">
                        <CountUp value={dev.total} format={fmt.int} />
                    </strong>
                    <Pill>Escopo global (independe do filtro de data)</Pill>
                </span>
                <span className="muted small">Distribuição proporcional entre {texto}.</span>
            </div>
            {dev.total > 0 && (
                <div className="dev-bar">
                    <div className="dev-bar-labels num">
                        {dev.partes
                            .filter((p) => p.value > 0)
                            .map((p) => (
                                <span key={p.key} className={`dev-${p.key}`}>
                                    {p.label}: {fmt.dec1(p.pct)}%
                                </span>
                            ))}
                    </div>
                    <div className="split" aria-hidden="true">
                        {dev.partes.map((p) => (
                            <span key={p.key} className={`dev-${p.key}`} style={{ flexGrow: p.value }} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

// Um card de devolução: borda e frase pela variação (devolver mais é ruim).
export function DevolucaoCard({
    label,
    value,
    comparativo,
    hint,
}: {
    label: string
    value: number
    comparativo: number | null
    hint: string
}) {
    // Sem comparativo (ex.: o banco legado só tem o acumulado): diz que é o total, sem "vs mês anterior".
    const leitura =
        comparativo === null && value > 0
            ? { text: 'Total acumulado', tone: 'neutral' as const }
            : leituraDevolucao(value, comparativo)
    return (
        <HeroStat
            label={label}
            icon="x-circle"
            tone={value === 0 ? 'neutral' : deltaTone(comparativo, true)}
            outline
            value={<CountUp value={value} format={fmt.int} />}
            aside={<DeltaPill value={comparativo} betterWhenDown />}
            hint={hint}
            footer={
                <FootRow
                    left={<span className={`tone-text-${leitura.tone}`}>{leitura.text}</span>}
                    right={comparativo === null ? undefined : 'vs mês anterior'}
                />
            }
        />
    )
}

// "Ganho de velocidade" quando o tempo caiu; "Perda" quando subiu.
export function Velocidade({ value }: { value: number | null }) {
    if (!value) return <span className="muted">Sem variação</span>
    return value < 0 ? (
        <span className="tone-text-ok">Ganho de velocidade</span>
    ) : (
        <span className="tone-text-danger">Perda de velocidade</span>
    )
}
