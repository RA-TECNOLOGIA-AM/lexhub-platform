import type { ReactNode } from 'react'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import type { resumo } from './sobrevivencia.ts'

type Resumo = ReturnType<typeof resumo>
const pctFmt = (v: number) => `${fmt.dec1(v)}%`
// Percentual que "vai carregando" (CountUp), como os outros números do diagrama; sem valor, '—'.
const pct = (v: number | null) => (v === null ? '—' : <CountUp value={v} format={pctFmt} />)

// O diagrama de fluxo da v1 (DiagramaFluxo): distribuição (t = 0) → Estágio 1 (com a instância 1G e a 2G, cada uma
// com o acordo, que disputa com a decisão, e a decisão) → só acordo e mérito favorável seguem → Estágio 2 (pagamento).
export function Fluxo({ r }: { r: Resumo }) {
    return (
        <div className="flx">
            <div className="flx-inicio">
                <span className="flx-ponto" /> <strong>Distribuição</strong> · <span className="num">t = 0</span>
                <span className="flx-sep" /> <span className="muted">Início da observação</span>
            </div>
            <Seta cor="var(--c-info)" />

            <section className="flx-bloco flx-e1">
                <header>
                    <span className="flx-badge">Estágio 1</span>
                    <strong className="flx-titulo">
                        Distribuição → mérito/acordo <span className="muted">(qualquer desfecho)</span>
                    </strong>
                    <span className="muted small flx-dir">
                        <span className="flx-ponto" /> Macro-indicadores da coorte
                    </span>
                </header>
                <div className="flx-kpis">
                    <Kpi icon="scale" rotulo="Coorte analisada" nota="Processos analisados">
                        <CountUp value={r.coorte} format={fmt.int} />
                    </Kpi>
                    <Kpi
                        icon="clock"
                        rotulo="Mediana geral até mérito/acordo"
                        nota="Tempo mediano até o 1º evento"
                        tom="violeta"
                    >
                        <Dias v={r.medianaGeral} />
                    </Kpi>
                    <Kpi
                        icon="check-circle"
                        rotulo="Mérito favorável c/ proveito"
                        nota="Habilitados ao Estágio 2 (c/ acordos)"
                        tom="ok"
                        dica="Percentual da coorte cujo desfecho de mérito foi favorável com proveito econômico. Esses processos, junto com os acordos, seguem para o Estágio 2."
                    >
                        <span className="tone-text-ok">{pct(r.pctMeritoFavoravel)}</span>
                    </Kpi>
                </div>
            </section>

            {/* do Estágio 1 para as duas instâncias */}
            <div className="flx-ramos">
                <svg className="flx-linhas" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M50 0 L50 50" className="l-info" />
                    <path d="M24 50 C21 50 20 70 20 100" className="l-info" />
                    <path d="M76 50 C79 50 80 70 80 100" className="l-violeta" />
                </svg>
                <div className="flx-legenda">
                    <span className="tone-text-warn">
                        <Icon name="flow" size={13} /> <strong>Risco competitivo:</strong>
                    </span>{' '}
                    Acordo disputa com a decisão da instância
                    <span className="flx-sep" />
                    <span className="flx-violeta">
                        <strong>» Fluxo sequencial:</strong>
                    </span>{' '}
                    Instância 1G → Instância 2G
                </div>
            </div>

            <div className="flx-instancias">
                <section className="flx-bloco flx-1g">
                    <header>
                        <span className="flx-ponto" /> <strong>Instância 1G (1º grau)</strong>
                        <span className="flx-tag">Fase inicial</span>
                    </header>
                    <div className="flx-cards">
                        <Acordo
                            titulo="Acordo pré-sentença (1G)"
                            badge="Risco Comp. 1G"
                            a={r.acordoPre}
                            rodape="Antes da 1ª decisão"
                        />
                        <Decisao
                            titulo="Sentença (1G)"
                            badge="1ª Decisão"
                            icon="scale"
                            d={r.sentenca}
                            rodape="Sobre julgadas 1G"
                            acao={<span className="flx-violeta">2G →</span>}
                            classe="flx-c-info"
                        />
                    </div>
                </section>
                <div className="flx-seq" aria-hidden="true">
                    <span>Fluxo sequencial</span>
                    <strong>⟶</strong>
                    <span className="muted">Recurso 2G</span>
                </div>
                <section className="flx-bloco flx-2g">
                    <header>
                        <span className="flx-ponto" /> <strong>Instância 2G (2º grau)</strong>
                        <span className="flx-tag">Fase recursal</span>
                    </header>
                    <div className="flx-cards">
                        <Acordo
                            titulo="Acordo pós-sentença"
                            badge="Risco Comp. 2G"
                            a={r.acordoPos}
                            rodape="Após 1ª decisão (2G/Exec.)"
                        />
                        <Decisao
                            titulo="Acórdão de mérito (2G)"
                            badge="2ª Instância"
                            icon="building"
                            d={r.acordao}
                            rodape="Sobre julgados 2G"
                            acao={<span className="tone-text-ok">Estágio 2 ↓</span>}
                            classe="flx-c-violeta"
                        />
                    </div>
                </section>
            </div>

            {/* as instâncias convergem para o Estágio 2 */}
            <div className="flx-converge">
                <svg className="flx-linhas" viewBox="0 0 100 60" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M14 0 C14 40 50 30 50 60" className="l-warn" />
                    <path d="M36 0 C36 40 50 30 50 60" className="l-ok" />
                    <path d="M64 0 C64 40 50 30 50 60" className="l-warn" />
                    <path d="M86 0 C86 40 50 30 50 60" className="l-ok" />
                </svg>
            </div>
            <div className="flx-pilula">
                <span className="flx-ponto ok" /> Apenas <strong>acordo</strong> e{' '}
                <strong className="tone-text-ok">mérito favorável com proveito</strong> seguem para o Estágio 2 —
                improcedentes e extinções encerram ↓
            </div>
            <Seta cor="var(--ok-dot)" />

            <section className="flx-bloco flx-e2">
                <div>
                    <header>
                        <span className="flx-badge ok">Estágio 2</span>
                        <strong className="flx-titulo tone-text-ok">Mérito favorável/acordo → pagamento efetivo</strong>
                    </header>
                    <p>
                        Conversão financeira efetiva entre os processos que obtiveram êxito no Estágio 1 (acordos
                        pré/pós-sentença ou decisões de mérito favoráveis com proveito econômico).
                    </p>
                </div>
                <div className="flx-taxa">
                    <Anel valor={r.estagio2.taxa ?? 0} />
                    <div>
                        <span className="muted small">Taxa de pagamento efetivo</span>
                        <strong className="num flx-taxa-v">
                            {pct(r.estagio2.taxa)} <span className="flx-conv">Convertidos</span>
                        </strong>
                        <span className="muted small">
                            {fmt.int(r.estagio2.pagos)} de {fmt.int(r.estagio2.elegiveis)} elegíveis do Estágio 1
                        </span>
                    </div>
                </div>
            </section>
        </div>
    )
}

function Seta({ cor }: { cor: string }) {
    return (
        <span className="flx-seta" style={{ color: cor }} aria-hidden="true">
            ▼
        </span>
    )
}

function Dias({ v }: { v: number | null }) {
    return v === null ? (
        <span className="muted">Não atingida</span>
    ) : (
        <>
            <CountUp value={v} format={fmt.int} /> <span className="flx-un">dias</span>
        </>
    )
}

function Kpi({
    icon,
    rotulo,
    nota,
    tom = 'info',
    dica,
    children,
}: {
    icon: IconName
    rotulo: string
    nota: string
    tom?: 'info' | 'violeta' | 'ok'
    dica?: string
    children: ReactNode
}) {
    return (
        <div className={`flx-kpi t-${tom}`} title={dica}>
            <span className="flx-ico">
                <Icon name={icon} size={18} />
            </span>
            <div>
                <span className="muted small">
                    {rotulo} {dica && <Icon name="info" size={12} />}
                </span>
                <strong className="num flx-kpi-v">{children}</strong>
                <span className={`small ${tom === 'ok' ? 'tone-text-ok' : 'muted'}`}>{nota}</span>
            </div>
        </div>
    )
}

function Acordo({
    titulo,
    badge,
    a,
    rodape,
}: {
    titulo: string
    badge: string
    a: { pct: number | null; mediana: number | null }
    rodape: string
}) {
    return (
        <div className="flx-card flx-c-warn">
            <div className="flx-card-topo">
                <strong>{titulo}</strong>
                <span className="flx-mini">{badge}</span>
            </div>
            <div className="flx-linha">
                <span className="flx-ico">
                    <Icon name="clock" size={15} />
                </span>
                <div>
                    <span className="muted small">Mediana</span>
                    <strong className="num">
                        <Dias v={a.mediana} />
                    </strong>
                </div>
            </div>
            <div className="flx-linha">
                <span className="flx-ico warn">
                    <Icon name="users" size={15} />
                </span>
                <div>
                    <span className="muted small">% da coorte</span>
                    <strong className="num tone-text-warn">{pct(a.pct)}</strong>
                </div>
            </div>
            <div className="flx-rodape">
                <span className="muted">{rodape}</span>
                <span className="tone-text-ok">Estágio 2 ↓</span>
            </div>
        </div>
    )
}

function Decisao({
    titulo,
    badge,
    icon,
    d,
    rodape,
    acao,
    classe,
}: {
    titulo: string
    badge: string
    icon: IconName
    d: { mediana: number | null; favoravel: number | null; improcedente: number | null; extinta: number | null }
    rodape: string
    acao: ReactNode
    classe: string
}) {
    const soma = (d.favoravel ?? 0) + (d.improcedente ?? 0) + (d.extinta ?? 0)
    const escala = soma > 100 ? 100 / soma : 1
    return (
        <div className={`flx-card ${classe}`}>
            <div className="flx-card-topo">
                <strong>{titulo}</strong>
                <span className="flx-mini">{badge}</span>
            </div>
            <div className="flx-linha">
                <span className="flx-ico">
                    <Icon name={icon} size={15} />
                </span>
                <div>
                    <span className="muted small">Mediana (qualquer)</span>
                    <strong className="num">
                        <Dias v={d.mediana} />
                    </strong>
                </div>
            </div>
            <span className="flx-barra" aria-hidden="true">
                <span className="fav" style={{ width: `${(d.favoravel ?? 0) * escala}%` }} />
                <span className="imp" style={{ width: `${(d.improcedente ?? 0) * escala}%` }} />
                <span className="ext" style={{ width: `${(d.extinta ?? 0) * escala}%` }} />
            </span>
            <div className="flx-desf">
                <span className="fav">
                    Favorável <strong className="num">{pct(d.favoravel)}</strong>
                </span>
                <span className="imp">
                    Improced. <strong className="num">{pct(d.improcedente)}</strong>
                </span>
                <span>
                    Extinção <strong className="num">{pct(d.extinta)}</strong>
                </span>
            </div>
            <div className="flx-rodape">
                <span className="muted">{rodape}</span>
                {acao}
            </div>
        </div>
    )
}

// O anel da taxa de pagamento (v1: SVG 88×88, raio 32, traço 7).
function Anel({ valor }: { valor: number }) {
    const c = 2 * Math.PI * 32
    const v = Math.max(0, Math.min(100, valor))
    return (
        <svg className="flx-anel" viewBox="0 0 88 88" aria-hidden="true">
            <circle cx="44" cy="44" r="32" className="fundo" />
            <circle
                cx="44"
                cy="44"
                r="32"
                className="valor"
                strokeDasharray={`${(v / 100) * c} ${c}`}
                transform="rotate(-90 44 44)"
            />
            <foreignObject x="30" y="30" width="28" height="28">
                <span className="flx-anel-ico">
                    <Icon name="dollar" size={18} />
                </span>
            </foreignObject>
        </svg>
    )
}
