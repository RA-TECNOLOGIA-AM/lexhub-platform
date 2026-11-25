import type { ReactNode } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { InfoTip, Pill, ToneIcon } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters, Point } from '../../../types/index.ts'
import { graficos } from './graficos.tsx'
import { RoscaLegenda } from './RoscaLegenda.tsx'
import { ColunasSalario, GradeDependentes } from './SalarioDependentes.tsx'
import {
    duplicadoPorGenero,
    lider,
    dependentes,
    faixasSalariais,
    totalDe,
    versus,
    type Dimensao,
    type Leitor,
} from './marketingComum.ts'

const ANCORA_PERFIL = 'mkt-perfil'
const ANCORA_TRIADOS = 'mkt-triados'

const pct1 = (v: number) => `${fmt.dec1(v)}%`
const rolarPara = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

// Card de destaque: rótulo com selo, o número grande com uma legenda ao lado e o ícone à direita.
function Destaque(props: {
    label: string
    selo?: ReactNode
    value: number
    format: (v: number) => string
    legenda?: ReactNode
    icon: IconName
    tone: Tone
    hint: string
}) {
    return (
        <div className={`card hero tone-${props.tone} mkt-destaque`}>
            <div className="mkt-destaque-txt">
                <div className="mkt-destaque-top">
                    <span className="hero-l">{props.label}</span>
                    {props.selo}
                    <InfoTip text={props.hint} />
                </div>
                <div className="mkt-destaque-mid">
                    <span className="hero-v num">
                        <CountUp value={props.value} format={props.format} />
                    </span>
                    {props.legenda && <span className="mkt-destaque-legenda">{props.legenda}</span>}
                </div>
            </div>
            <ToneIcon icon={props.icon} tone={props.tone} />
        </div>
    )
}

const nota = (texto: string) => <span className="mkt-nota">{texto}</span>

// Média salarial mensal: as faixas respondidas em colunas; "Não informado" no selo e numa linha embaixo.
function CardSalario({ pts }: { pts: Point[] }) {
    const { faixas, naoInformado } = faixasSalariais(pts)
    const resumo = `${fmt.int(naoInformado.value)} (${Math.round(naoInformado.share)}%)`
    return (
        <ChartCard
            title="Média salarial mensal"
            action={
                naoInformado.value > 0 ? (
                    <Pill>{`Não informado: ${resumo}`}</Pill>
                ) : (
                    <span className="mkt-nota tone-text-ok">100% preenchido</span>
                )
            }
            footer={
                naoInformado.value > 0 && (
                    <div className="mkt-sem-renda">
                        <span>
                            <span className="dot" aria-hidden="true" />
                            Sem renda informada (pré-triagem)
                        </span>
                        <span className="num">{resumo}</span>
                    </div>
                )
            }
        >
            <ColunasSalario faixas={faixas} />
        </ChartCard>
    )
}

// Nota da prospecção: aviso quando o mesmo valor veio de dois jeitos ("ativa" e "ativo"); senão, os valores.
const notaProspeccao = (pts: Point[]) => {
    const dup = duplicadoPorGenero(pts)
    return dup ? (
        <Pill tone="warn">
            Unificar "{dup.nomes[0]}" + "{dup.nomes[1]}" ({fmt.dec1(dup.share).replace(/,0$/, '')}%)
        </Pill>
    ) : (
        nota(versus(pts))
    )
}

type PerfilTriadosProps = {
    ler: Leitor
    filters: DashboardFilters
    onToggleFilter?: (key: Dimensao, value: string) => void
    dispositivo?: boolean // Marketing (banco NG): os gráficos de dispositivo (o LexPre não tem)
}

// A faixa de resumo (base -> triados) e as seções 01 Perfil de clientes e 02 Triados, iguais nas duas páginas do
// Marketing. Clicar numa barra, fatia ou item da legenda liga o filtro da dimensão, que vale para as duas seções.
export function PerfilTriados({ ler, filters, onToggleFilter, dispositivo = false }: PerfilTriadosProps) {
    const { n, serie } = ler
    const { clique, barras, faixaEtaria } = graficos(filters, onToggleFilter)
    const rosca = (items: Point[], centro: string, dim: Dimensao) => (
        <RoscaLegenda items={items} centerLabel={centro} {...clique(dim)} />
    )

    const clientes = n('total_clientes')
    const triados = n('triados_total_clientes')
    const taxaResposta = clientes > 0 ? (triados / clientes) * 100 : 0
    const mediaIdade = n('media_idade')
    const mediaIdadeTriados = n('triados_media_idade')
    const difIdade = Math.round((mediaIdadeTriados - mediaIdade) * 10) / 10

    const canal = lider(serie('origem'))
    const canalTriados = lider(serie('triados_origem'))
    const faixa = lider(serie('faixa_etaria'))
    const canais = serie('origem').length

    const prospeccaoESalario = (
        <>
            <ChartCard title="Prospecção" action={notaProspeccao(serie('prospeccao'))}>
                {barras(serie('prospeccao'), 'prospeccao_marketing')}
            </ChartCard>
            <CardSalario pts={serie('faixa_salarial')} />
        </>
    )

    return (
        <>
            <div className="card mkt-resumo">
                <div className="mkt-resumo-etapa tone-accent">
                    <span className="mkt-resumo-num num">01</span>
                    <span>
                        <span className="mkt-resumo-l">Base de clientes</span>
                        <strong className="num">{fmt.int(clientes)}</strong>
                    </span>
                </div>
                <Icon name="arrowRight" size={16} />
                <div className="mkt-resumo-etapa tone-info">
                    <span className="mkt-resumo-num num">02</span>
                    <span>
                        <span className="mkt-resumo-l">Responderam triagem</span>
                        <strong className="num mkt-resumo-v-info">{fmt.int(triados)}</strong>
                    </span>
                </div>
                <span className="mkt-resumo-sep" aria-hidden="true" />
                <Pill tone="ok">{pct1(taxaResposta)} taxa de resposta</Pill>
                <span className="mkt-nota">Clique em qualquer barra ou fatia abaixo para filtrar ambas as seções</span>
                <nav className="mkt-resumo-nav" aria-label="Ir para a seção">
                    <button type="button" className="pill tone-accent" onClick={() => rolarPara(ANCORA_PERFIL)}>
                        01 · Perfil de Clientes
                    </button>
                    <button type="button" className="pill tone-info" onClick={() => rolarPara(ANCORA_TRIADOS)}>
                        02 · Triados
                    </button>
                </nav>
            </div>

            <DashSection
                index={1}
                anchor={ANCORA_PERFIL}
                eyebrow="Perfil de clientes"
                title="Perfil de clientes"
                subtitle={`${fmt.int(clientes)} cliente(s): idade, gênero, ocupação, canais de aquisição e faixa salarial.`}
            >
                <div className="mkt-grid-2">
                    <Destaque
                        label="Clientes"
                        selo={<Pill tone="accent">Base ativa</Pill>}
                        value={clientes}
                        format={fmt.int}
                        legenda={
                            canal && (
                                <>
                                    Predomínio:{' '}
                                    <b className="tone-text-accent">
                                        {canal.name} ({pct1(canal.share)})
                                    </b>
                                </>
                            )
                        }
                        icon="users"
                        tone="accent"
                        hint="Clientes assinados no período. Predomínio = o canal de aquisição com mais clientes."
                    />
                    <Destaque
                        label="Média de idade"
                        selo={faixa && <Pill tone="info">{`${pct1(faixa.share)} têm ${faixa.name} anos`}</Pill>}
                        value={mediaIdade}
                        format={fmt.dec1}
                        legenda="anos"
                        icon="user"
                        tone="info"
                        hint="Idade média dos clientes, pela data de nascimento. O selo mostra a faixa etária com mais clientes."
                    />
                </div>
                <div className="mkt-grid-3 grid-mini">
                    <ChartCard title="Faixa etária" action={nota('Clique para filtrar')}>
                        {faixaEtaria(serie('faixa_etaria'))}
                    </ChartCard>
                    <ChartCard
                        title="Canal de aquisição"
                        action={canais > 0 && <Pill tone="accent">{`${canais} canais`}</Pill>}
                    >
                        {rosca(serie('origem'), 'clientes', 'canal_aquisicao_marketing')}
                    </ChartCard>
                    <ChartCard title="Gênero" action={nota('Distribuição')}>
                        {rosca(serie('genero'), 'clientes', 'genero_marketing')}
                    </ChartCard>
                </div>
                <div className="mkt-grid-2 grid-mini">
                    <ChartCard title="Tipo de tráfego" action={nota(versus(serie('tipo_trafego')))}>
                        {barras(serie('tipo_trafego'), 'tipo_trafego_marketing')}
                    </ChartCard>
                    <ChartCard title="Ocupação" action={nota(`${fmt.int(totalDe(serie('ocupacao')))} respondentes`)}>
                        {barras(serie('ocupacao'), 'ocupacao_marketing')}
                    </ChartCard>
                    {!dispositivo && prospeccaoESalario}
                </div>
                {/* Marketing (banco NG): Prospecção, Média salarial e Dispositivo (rosca, como Gênero) na mesma linha. */}
                {dispositivo && (
                    <div className="mkt-grid-3 grid-mini">
                        {prospeccaoESalario}
                        <ChartCard title="Dispositivo" action={nota('Distribuição')}>
                            {rosca(serie('dispositivo'), 'clientes', 'dispositivo_marketing')}
                        </ChartCard>
                    </div>
                )}
            </DashSection>

            <DashSection
                index={2}
                anchor={ANCORA_TRIADOS}
                eyebrow="Triagem"
                title="Triados"
                subtitle={`${fmt.int(triados)} cliente(s) responderam à triagem: idade, moradia, tráfego e dependentes.`}
            >
                <div className="mkt-grid-2">
                    <Destaque
                        label="Clientes triados"
                        selo={<Pill tone="ok">{`${pct1(taxaResposta)} da base total`}</Pill>}
                        value={triados}
                        format={fmt.int}
                        legenda={
                            canalTriados && (
                                <>
                                    Canal líder:{' '}
                                    <b className="tone-text-accent">
                                        {canalTriados.name} ({pct1(canalTriados.share)})
                                    </b>
                                </>
                            )
                        }
                        icon="check-circle"
                        tone="info"
                        hint="Clientes que responderam à triagem (pesquisa socioeconômica)."
                    />
                    <Destaque
                        label="Média de idade (triados)"
                        selo={
                            mediaIdade > 0 &&
                            mediaIdadeTriados > 0 && (
                                <Pill tone="accent">
                                    {`${difIdade > 0 ? '+' : ''}${fmt.dec1(difIdade)} anos vs. base geral`}
                                </Pill>
                            )
                        }
                        value={mediaIdadeTriados}
                        format={fmt.dec1}
                        legenda="anos"
                        icon="user"
                        tone="accent"
                        hint="Idade média dos clientes triados, comparada com a de todos os clientes do período."
                    />
                </div>
                {/* Pessoas dependentes: os blocos numa linha inteira, logo abaixo dos cards de destaque. */}
                <div className="grid-mini">
                    <ChartCard title="Pessoas dependentes" action={nota('Composição familiar')}>
                        <GradeDependentes
                            linha
                            itens={dependentes(serie('triados_pessoas_dependentes'))}
                            {...clique('pessoas_dependentes_marketing')}
                        />
                    </ChartCard>
                </div>
                <div className="mkt-grid-3 grid-mini">
                    <ChartCard title="Faixa etária (triados)" action={nota('Clique para filtrar')}>
                        {faixaEtaria(serie('triados_faixa_etaria'))}
                    </ChartCard>
                    <ChartCard
                        title="Canal de aquisição (triados)"
                        action={triados > 0 && <Pill tone="ok">{`Total: ${fmt.int(triados)}`}</Pill>}
                    >
                        {rosca(serie('triados_origem'), 'triados', 'canal_aquisicao_marketing')}
                    </ChartCard>
                    <ChartCard title="Gênero (triados)" action={nota('Distribuição')}>
                        {rosca(serie('triados_genero'), 'triados', 'genero_marketing')}
                    </ChartCard>
                </div>
                {/* Residência, Dispositivo (só no banco NG) e Média salarial; sem o Dispositivo, as duas dividem a linha. */}
                <div className={dispositivo ? 'mkt-grid-3 grid-mini' : 'mkt-grid-2 grid-mini'}>
                    <ChartCard title="Tipo de residência" action={nota(`${fmt.int(triados)} triados`)}>
                        {barras(serie('triados_tipo_residencia'), 'tipo_residencia_marketing')}
                    </ChartCard>
                    {dispositivo && (
                        <ChartCard title="Dispositivo (triados)" action={nota(versus(serie('triados_dispositivo')))}>
                            {barras(serie('triados_dispositivo'), 'dispositivo_marketing')}
                        </ChartCard>
                    )}
                    <CardSalario pts={serie('triados_faixa_salarial')} />
                </div>
                <div className="mkt-grid-3 grid-mini">
                    <ChartCard title="Ocupação" action={nota(`${fmt.int(triados)} triados`)}>
                        {barras(serie('triados_ocupacao'), 'ocupacao_marketing')}
                    </ChartCard>
                    <ChartCard title="Tipo de tráfego (triados)" action={nota(versus(serie('triados_tipo_trafego')))}>
                        {barras(serie('triados_tipo_trafego'), 'tipo_trafego_marketing')}
                    </ChartCard>
                    <ChartCard title="Prospecção (triados)" action={notaProspeccao(serie('triados_prospeccao'))}>
                        {barras(serie('triados_prospeccao'), 'prospeccao_marketing')}
                    </ChartCard>
                </div>
            </DashSection>
        </>
    )
}
