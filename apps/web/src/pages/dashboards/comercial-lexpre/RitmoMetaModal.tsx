import type { CSSProperties } from 'react'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { fmt } from '../../../lib/format.ts'
import { projecaoPrevia, type RitmoMeta, type StatusRitmo } from './comercial.ts'
import type { PreviaRepresados } from './types.ts'

const inteiro = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const dec2 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const milhoes = (v: number) => `R$ ${dec2.format(v / 1e6)} mi`
const sinal = (v: number) => (v < 0 ? '−' : '+')
const pct2 = (v: number) => `${fmt.dec2(v)}%`
const pp = (v: number) => `${sinal(v)}${fmt.dec2(Math.abs(v))} p.p.`
const dataBr = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`
const metaPorExtenso = (meta: number) =>
    meta >= 1e6 ? `R$ ${new Intl.NumberFormat('pt-BR').format(meta / 1e6)} milhões` : inteiro.format(meta)
const largura = (v: number) => ({ '--w': `${Math.min(100, Math.max(0, v))}%` }) as CSSProperties

// O selo do título: onde o time está contra o esperado de hoje.
const STATUS: Record<StatusRitmo, { rotulo: string; tom: 'ok' | 'warn' | 'danger' }> = {
    atingida: { rotulo: 'Meta atingida', tom: 'ok' },
    adiantado: { rotulo: 'No ritmo', tom: 'ok' },
    ligeiramente_atrasado: { rotulo: 'Ligeiramente atrasado', tom: 'warn' },
    atrasado: { rotulo: 'Atrasado', tom: 'danger' },
}

// A frase final: atrasado, no ritmo ou adiantado, e quanto a média diária precisa mudar para fechar o ano.
function Conclusao({ r, meta }: { r: RitmoMeta; meta: number }) {
    if (r.faltam === 0) return <>a meta do ano já foi atingida ({pct2(r.pctRealizado)}).</>
    if (r.novaMedia === null || r.variacao === null) return <>o ano terminou com {pct2(r.pctRealizado)} da meta.</>
    const quanto = `${fmt.dec1(Math.abs(r.variacao) * 100)}%`
    const alvo = (
        <>
            alcançar os <strong className="num">{metaPorExtenso(meta)}</strong> até 31/12
        </>
    )
    if (r.diferenca < 0) {
        return (
            <>
                o time está {r.status === 'atrasado' ? 'atrasado' : 'ligeiramente atrasado'} em relação ao ritmo linear
                da meta anual (<span className="ritmo-neg num">{pp(r.pontos)}</span>). Para recuperar o atraso e {alvo},
                precisará produzir aproximadamente <span className="ritmo-alerta num">{quanto} acima</span> da média
                diária planejada (<strong className="num">{inteiro.format(r.novaMedia)}/dia</strong>).
            </>
        )
    }
    return (
        <>
            o time está à frente do ritmo linear da meta anual (<span className="ritmo-pos num">{pp(r.pontos)}</span>).
            Mantendo uma média até <span className="ritmo-pos num">{quanto} abaixo</span> da planejada (
            <strong className="num">{inteiro.format(r.novaMedia)}/dia</strong>) já é possível {alvo}.
        </>
    )
}

// Módulo: o modal "Ritmo da meta" do card Meta <ano> do Comercial: a meta distribuída linearmente pelos dias do ano
// (a regra do dashboard Meta anual), o esperado até hoje contra o realizado e o ritmo diário para fechar o ano.
// Os setores do Pré-protocolo na prévia, na ordem da página dele.
const SETORES_PREVIA: { key: keyof PreviaRepresados['represados']; label: string }[] = [
    { key: 'pendencias', label: 'Pendência' },
    { key: 'org_documentos', label: 'Org. Documentos' },
    { key: 'peticionamento', label: 'Peticionamento' },
    { key: 'protocolo', label: 'Protocolo' },
]

export function RitmoMetaModal({
    r,
    meta,
    previa,
    onClose,
}: {
    r: RitmoMeta
    meta: number
    previa?: PreviaRepresados // V2: o que ainda pode ser protocolado; sem = o bloco não aparece
    onClose: () => void
}) {
    const atrasado = r.diferenca < 0
    const status = STATUS[r.status]
    const pctFalta = Math.max(0, 100 - r.pctRealizado)
    const acrescimo = r.novaMedia === null ? null : r.novaMedia - r.mediaPlanejada
    return (
        <Modal
            className="ritmo-modal"
            title={
                <span className="ritmo-head">
                    <span className="tone-icon tone-accent" aria-hidden="true">
                        <Icon name="target" size={18} />
                    </span>
                    Ritmo da meta {r.ano}
                    <span className={`ritmo-selo tone-${status.tom} num`}>
                        {status.rotulo}
                        {r.status !== 'atingida' && ` (${pp(r.pontos)})`}
                    </span>
                </span>
            }
            subtitle={
                <>
                    Meta anual de <strong className="num">{inteiro.format(meta)}</strong> (linear · {r.diasNoAno} dias)
                    · Corte em <strong className="num">{dataBr(r.hoje)}</strong> · Prazo{' '}
                    <strong className="num">31/12/{r.ano}</strong>
                </>
            }
            onClose={onClose}
        >
            <div className="ritmo">
                {/* Os três números: o que deveria estar protocolado hoje, o que está, e a diferença. */}
                <div className="ritmo-cards">
                    <div className="card ritmo-card">
                        <span className="ritmo-card-l">
                            Esperado até hoje <span className="ritmo-dot esperado" aria-hidden="true" />
                        </span>
                        <strong className="ritmo-card-v num">{milhoes(r.esperado)}</strong>
                        <span className="muted small num">{inteiro.format(r.esperado)}</span>
                        <span className="ritmo-card-pe">
                            <span className="ritmo-chip tone-ok num">{pct2(r.pctEsperado)} da meta</span>
                            <span className="muted small num">
                                {r.decorridos} de {r.diasNoAno} dias
                            </span>
                        </span>
                    </div>
                    <div className="card ritmo-card">
                        <span className="ritmo-card-l">
                            Realizado <span className="ritmo-dot realizado" aria-hidden="true" />
                        </span>
                        <strong className="ritmo-card-v num">{milhoes(r.realizado)}</strong>
                        <span className="muted small num">{inteiro.format(r.realizado)}</span>
                        <span className="ritmo-card-pe">
                            <span className="ritmo-chip tone-warn num">{pct2(r.pctRealizado)} da meta</span>
                            <span className="muted small">Atingido no ano</span>
                        </span>
                    </div>
                    <div className={`card ritmo-card ${atrasado ? 'deficit' : 'superavit'}`}>
                        <span className="ritmo-card-l">
                            {atrasado ? 'Déficit atual' : 'Adiantamento atual'}{' '}
                            <span className={`ritmo-dot ${atrasado ? 'deficit' : 'esperado'}`} aria-hidden="true" />
                        </span>
                        <strong className="ritmo-card-v num">
                            {sinal(r.diferenca)}
                            {milhoes(Math.abs(r.diferenca))}
                        </strong>
                        <span className="muted small num">
                            {sinal(r.diferenca)}
                            {inteiro.format(Math.abs(r.diferenca))}
                        </span>
                        <span className="ritmo-card-pe">
                            <span className={`ritmo-chip ${atrasado ? 'tone-danger' : 'tone-ok'} num`}>
                                {pp(r.pontos)} vs. esperado
                            </span>
                            <span className="muted small num">
                                {fmt.dec1(Math.abs(r.dias))} dia{Math.abs(r.dias) >= 2 ? 's' : ''} de{' '}
                                {atrasado ? 'atraso' : 'folga'}
                            </span>
                        </span>
                    </div>
                </div>

                {/* A barra do ano: o realizado preenchido e o traço do esperado de hoje. */}
                <div className="card ritmo-ano">
                    <div className="ritmo-ano-topo">
                        <span className="ritmo-legenda num">
                            <span className="ritmo-dot realizado quadrado" aria-hidden="true" />
                            Realizado: <strong>{pct2(r.pctRealizado)}</strong>
                            <span className="ritmo-traco" aria-hidden="true" />
                            Esperado hoje: <strong>{pct2(r.pctEsperado)}</strong>
                        </span>
                        <span className="muted small num">Meta: {milhoes(meta)} (100%)</span>
                    </div>
                    <div
                        className="ritmo-trilho"
                        role="img"
                        aria-label={`Realizado ${pct2(r.pctRealizado)} da meta; esperado hoje ${pct2(r.pctEsperado)}`}
                    >
                        <span className="ritmo-preenchido" style={largura(r.pctRealizado)} />
                        <span className="ritmo-marca" style={largura(r.pctEsperado)}>
                            <span className="ritmo-marca-tag num">{pct2(r.pctEsperado)}</span>
                        </span>
                    </div>
                    <div className="ritmo-ano-pe muted small num">
                        <span>01/01/{r.ano} (0%)</span>
                        <span>
                            Faltam <strong>{inteiro.format(r.faltam)}</strong> ({pct2(pctFalta)})
                        </span>
                        <span>31/12/{r.ano} (100%)</span>
                    </div>
                </div>

                <h3 className="ritmo-titulo">Ritmo necessário para concluir a meta</h3>
                <div className="ritmo-grade">
                    <div className="card ritmo-bloco">
                        <div className="ritmo-cal">
                            <span className="ritmo-cal-topo num">
                                Calendário {r.ano}
                                <span>
                                    <strong>{r.decorridos}d</strong>
                                    <span className="muted"> / {r.restantes}d restantes</span>
                                </span>
                            </span>
                            <span className="ritmo-cal-barra" style={largura((r.decorridos / r.diasNoAno) * 100)} />
                            <span className="muted small num">
                                Decorridos (com hoje) · <span className="ritmo-info">{r.restantes} dias corridos</span>{' '}
                                até 31/12
                            </span>
                        </div>
                        <div className="ritmo-restante">
                            <span>
                                <span className="muted small">Valor restante para a meta</span>
                                <strong className="num">{inteiro.format(r.faltam)}</strong>
                            </span>
                            <span className="ritmo-chip num">{pct2(pctFalta)}</span>
                        </div>
                    </div>
                    <div className="card ritmo-bloco">
                        <div className="ritmo-medias">
                            <div className="ritmo-media">
                                <span className="ritmo-card-l">Média diária planejada</span>
                                <strong className="num">{inteiro.format(r.mediaPlanejada)}</strong>
                                <span className="muted small">Base linear ({r.diasNoAno} dias)</span>
                            </div>
                            <div className={`ritmo-media nova ${atrasado ? 'acima' : 'abaixo'}`}>
                                <span className="ritmo-card-l">Nova média necessária</span>
                                <strong className="num">
                                    {r.novaMedia === null ? '—' : inteiro.format(r.novaMedia)}
                                </strong>
                                {r.variacao !== null && acrescimo !== null && (
                                    <span className="small num">
                                        <Icon name={acrescimo >= 0 ? 'trend-up' : 'trend-down'} size={13} />{' '}
                                        {sinal(r.variacao)}
                                        {fmt.dec1(Math.abs(r.variacao) * 100)}% ({sinal(acrescimo)}
                                        {inteiro.format(Math.abs(acrescimo))}/dia)
                                    </span>
                                )}
                            </div>
                        </div>
                        {r.variacao !== null && (
                            <div className="ritmo-aceleracao small num">
                                <span className="muted">
                                    {r.variacao >= 0 ? 'Aceleração' : 'Folga'} diária nos próximos{' '}
                                    <strong>{r.restantes} dias</strong>:
                                </span>
                                <strong className={r.variacao >= 0 ? 'ritmo-alerta' : 'ritmo-pos'}>
                                    {sinal(r.variacao)}
                                    {fmt.dec1(Math.abs(r.variacao) * 100)}%
                                </strong>
                            </div>
                        )}
                    </div>
                </div>

                {previa && <Previa previa={previa} r={r} meta={meta} />}

                <div className="card ritmo-conclusao">
                    <span className="tone-icon tone-accent" aria-hidden="true">
                        <Icon name="info" size={16} />
                    </span>
                    <p>
                        <strong>Conclusão:</strong> <Conclusao r={r} meta={meta} />
                    </p>
                </div>
            </div>
        </Modal>
    )
}

// O bloco "Prévia dos represados": o que já está nos setores do Pré-protocolo × o ticket médio protocolado dos
// últimos 3 meses dá uma ideia, em valor, de quanto ainda pode ser protocolado nos próximos dias.
function Previa({ previa, r, meta }: { previa: PreviaRepresados; r: RitmoMeta; meta: number }) {
    const p = projecaoPrevia(previa.valor, r, meta)
    return (
        <>
            <h3 className="ritmo-titulo">Prévia do que pode entrar</h3>
            <div className="card ritmo-previa">
                <div className="ritmo-previa-setores">
                    <span className="ritmo-card-l">
                        Represados no Pré-protocolo <strong className="num">{fmt.int(previa.total_represados)}</strong>
                    </span>
                    <div className="ritmo-previa-lista">
                        {SETORES_PREVIA.map((s) => (
                            <span key={s.key} className="ritmo-previa-setor">
                                <span className="muted small">{s.label}</span>
                                <strong className="num">{fmt.int(previa.represados[s.key])}</strong>
                            </span>
                        ))}
                    </div>
                </div>
                <span className="ritmo-previa-op muted" aria-hidden="true">
                    ×
                </span>
                <div className="ritmo-media">
                    <span className="ritmo-card-l">Ticket médio protocolado</span>
                    <strong className="num">{inteiro.format(previa.ticket_medio)}</strong>
                    <span className="muted small num">
                        Últimos 3 meses ({dataBr(previa.de)} a {dataBr(previa.ate)})
                    </span>
                </div>
                <span className="ritmo-previa-op muted" aria-hidden="true">
                    =
                </span>
                {/* Verde: é o que ainda pode entrar (e, atrasados, mostra se cobriria o déficit de hoje). */}
                <div className="ritmo-media ritmo-pode-entrar">
                    <span className="ritmo-card-l">Pode entrar</span>
                    <strong className="num">{milhoes(previa.valor)}</strong>
                    {r.diferenca < 0 && (
                        <span className="small num">
                            {previa.valor >= -r.diferenca
                                ? `cobre o déficit atual (${milhoes(-r.diferenca)})`
                                : `cobre ${pct2((previa.valor / -r.diferenca) * 100)} do déficit atual`}
                        </span>
                    )}
                    <span className="small num">
                        {p.cobreFalta === null
                            ? 'meta já atingida'
                            : p.fechaMeta
                              ? 'cobre tudo o que falta para a meta'
                              : `${pct2(p.cobreFalta)} do que falta para a meta`}
                    </span>
                </div>
            </div>
            <p className="muted small">
                Se tudo o que está represado for protocolado, o ano chega a{' '}
                <strong className="num">{pct2(p.pctComPrevia)}</strong> da meta ({milhoes(r.realizado + previa.valor)}).
                Prévia: cada processo represado no valor do ticket médio protocolado dos últimos 3 meses.
            </p>
        </>
    )
}
