import type { CSSProperties } from 'react'
import { InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import { progressoMeta } from './comercial.ts'

type MetaAnualProps = {
    lexpre: number // valor de causa protocolado no ano, no LexPre
    legado: number | null // o mesmo no banco legado (antes da migração); null = sem legado ligado/fora do ar
    meta: number
    ano: number
}

const MARCOS = [25, 50, 75]
const inteiro = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 })

// Módulo: o card "Meta <ano>" do topo do Comercial da v1. À esquerda o valor protocolado no ano, a meta, o %
// atingido e quanto falta; à direita a barra do ano (0 → meta, marcos de 25%) com o foguete onde o valor está.
// Como na v1, soma o LexPre com o banco legado.
export function MetaAnual({ lexpre, legado, meta, ano }: MetaAnualProps) {
    const valor = lexpre + (legado ?? 0)
    const { pct, faltam } = progressoMeta(valor, meta)
    const origem =
        legado === null
            ? `Só o LexPre (${fmt.brl(lexpre)}): o banco legado não está ligado a esta unidade ou está fora do ar agora.`
            : `LexPre ${fmt.brl(lexpre)} + legado ${fmt.brl(legado)}.`
    return (
        <section className="card meta-anual" aria-label={`Meta ${ano}`}>
            <div className="ma-info">
                <div className="ma-tags">
                    <span className="ma-chip">
                        <Icon name="trend-up" size={14} />
                        Meta {ano}
                    </span>
                    <span className="ma-caption">
                        Valor de causa protocolado ({legado === null ? 'LexPre' : 'LexPre + legado'})
                    </span>
                    <InfoTip
                        text={`Valor de causa protocolado no ano todo, contra a meta anual da empresa (R$ 270 mi, a mesma da v1). Não depende do período escolhido; os filtros valem para o LexPre (o legado entra inteiro, como na v1). ${origem}`}
                    />
                </div>
                <div className="ma-valor num">
                    <span className="ma-moeda">R$</span>
                    <CountUp value={valor} format={(v) => inteiro.format(v)} />
                </div>
                <p className="ma-de">
                    de <strong className="num">{fmt.brlShort(meta)}</strong> previstos para o ano
                </p>
                <div className="ma-pills">
                    <span className="ma-pill ok num">
                        <Icon name="check-circle" size={15} />
                        {fmt.dec1(pct)}% atingido
                    </span>
                    <span className="ma-pill num">
                        Faltam <strong>{fmt.brlShort(faltam)}</strong>
                    </span>
                </div>
            </div>
            <div className="ma-barra">
                <div className="ma-escala num" aria-hidden="true">
                    <span>R$ 0</span>
                    {MARCOS.map((m) => (
                        <span key={m} style={{ left: `${m}%` } as CSSProperties}>
                            {m}%
                        </span>
                    ))}
                    <span>{fmt.brlShort(meta)}</span>
                </div>
                <div
                    className="ma-trilho"
                    role="progressbar"
                    aria-label="Progresso anual"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(pct * 100) / 100}
                >
                    <span className="ma-preenchido" style={{ '--w': `${pct}%` } as CSSProperties} />
                    {MARCOS.map((m) => (
                        <span key={m} className="ma-marco" style={{ left: `${m}%` }} />
                    ))}
                    <span className="ma-foguete" style={{ '--w': `${pct}%` } as CSSProperties}>
                        <Icon name="rocket" size={15} />
                    </span>
                </div>
                <div className="ma-rodape">
                    <span>Progresso anual</span>
                    <strong className="num">{fmt.dec2(pct)}%</strong>
                </div>
            </div>
        </section>
    )
}
