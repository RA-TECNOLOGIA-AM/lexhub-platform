import { useState, type CSSProperties, type KeyboardEvent, type MouseEvent } from 'react'
import { InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import { hojeEmManaus, progressoMeta, ritmoMeta } from './comercial.ts'
import { RitmoMetaModal } from './RitmoMetaModal.tsx'

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
// Como na v1, soma o LexPre com o banco legado. O ritmo (V2): a meta distribuída linearmente pelos dias do ano diz
// quanto já deveria estar protocolado hoje — um traço na barra e, à direita, o esperado e a diferença. O card inteiro
// abre o modal com o detalhe (o "i" só explica).
export function MetaAnual({ lexpre, legado, meta, ano }: MetaAnualProps) {
    const valor = lexpre + (legado ?? 0)
    const { pct, faltam } = progressoMeta(valor, meta)
    const r = ritmoMeta(valor, meta, ano, hojeEmManaus())
    const atrasado = r.diferenca < 0
    const [ritmoAberto, setRitmoAberto] = useState(false)
    const comRitmo = r.decorridos > 0 && r.restantes > 0 // o ano em curso (antes ou depois dele, não há "hoje")
    const abrir = (e: MouseEvent<HTMLElement>) => {
        if ((e.target as HTMLElement).closest('.tip')) return
        setRitmoAberto(true)
    }
    const tecla = (e: KeyboardEvent<HTMLElement>) => {
        if (e.target !== e.currentTarget || (e.key !== 'Enter' && e.key !== ' ')) return
        e.preventDefault()
        setRitmoAberto(true)
    }
    const origem =
        legado === null
            ? `Só o LexPre (${fmt.brl(lexpre)}): o banco legado não está ligado a esta unidade ou está fora do ar agora.`
            : `LexPre ${fmt.brl(lexpre)} + legado ${fmt.brl(legado)}.`
    return (
        <>
            <section
                className="card meta-anual ma-clicavel"
                aria-label={`Meta ${ano}: ver o ritmo da meta`}
                role="button"
                tabIndex={0}
                aria-haspopup="dialog"
                title="Clique para ver o ritmo da meta: esperado até hoje, comparativo e média diária necessária"
                onClick={abrir}
                onKeyDown={tecla}
            >
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
                        {comRitmo && (
                            <span
                                className="ma-esperado"
                                style={{ '--w': `${Math.min(100, r.pctEsperado)}%` } as CSSProperties}
                                title={`Esperado até hoje: ${fmt.brl(r.esperado)} (${fmt.dec2(r.pctEsperado)}%)`}
                            />
                        )}
                        <span className="ma-foguete" style={{ '--w': `${pct}%` } as CSSProperties}>
                            <Icon name="rocket" size={15} />
                        </span>
                    </div>
                    <div className="ma-rodape">
                        {comRitmo ? (
                            <span className={`ma-ritmo num ${atrasado ? 'atrasado' : 'adiantado'}`}>
                                <Icon name="clock" size={15} />
                                Esperado hoje <strong>{fmt.brlShort(r.esperado)}</strong>
                                <span className="ma-ritmo-dif">
                                    {atrasado ? '−' : '+'}
                                    {fmt.brlShort(Math.abs(r.diferenca))}
                                </span>
                            </span>
                        ) : (
                            <span />
                        )}
                        <span className="ma-progresso num">
                            Progresso anual <strong>{fmt.dec2(pct)}%</strong>
                            {comRitmo && (
                                <span className="ma-legenda-esperado">
                                    <span aria-hidden="true" /> esperado hoje{' '}
                                    <strong>{fmt.dec2(r.pctEsperado)}%</strong>
                                </span>
                            )}
                        </span>
                    </div>
                </div>
            </section>
            {/* Fora do card: um clique dentro do modal (até o de fechar) não pode chegar ao clique do card. */}
            {ritmoAberto && <RitmoMetaModal r={r} meta={meta} onClose={() => setRitmoAberto(false)} />}
        </>
    )
}
