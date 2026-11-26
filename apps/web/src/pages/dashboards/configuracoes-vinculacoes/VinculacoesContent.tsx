import { useState, type CSSProperties, type ReactNode } from 'react'
import { ChartCard, ChartEmpty } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { Paginador } from '../execucao/partes.tsx'
import { usePagina } from '../execucao/usePagina.ts'
import type { ContentProps } from '../types.ts'
import {
    DESTINO_QUEBRADO,
    MODO_TONE,
    STATUS_META,
    doSetor,
    filtrarLista,
    gatilhoDoFluxo,
    lerFiltros,
    pct,
    rankingProblemas,
    regraCumprido,
    regraNaoCumprido,
    saudePorSetor,
    semDestino,
    slotsDoFluxo,
    totais,
    type FiltroStatus,
    type Fluxo,
    type FluxoEncerramento,
    type StatusVinculacao,
    type Vinculacao,
    type VinculacoesResponse,
} from './vinculacoes.ts'

const POR_PAGINA = 15

const ICONE_STATUS: Record<StatusVinculacao, IconName> = {
    ok: 'check-circle',
    incompleta: 'clock',
    erro: 'x-circle',
    inativa: 'minus',
}

// Configurações das Vinculações (LexFlow): as seções da página admin da v1 no layout da V2. Os cards de status, a
// saúde por setor e o ranking de problemas filtram a lista (de novo, para tirar o filtro); clicar numa vinculação
// abre o detalhe, lido como o LexFlow executa o encerramento.
export function VinculacoesContent({ data, filters = {}, onFiltersChange }: ContentProps<VinculacoesResponse>) {
    const rows = data.rows ?? []
    const f = lerFiltros(filters)
    const [busca, setBusca] = useState('')
    const [detalhe, setDetalhe] = useState<Vinculacao | null>(null)

    const escopo = doSetor(rows, f.setor)
    const t = totais(escopo)
    const ranking = rankingProblemas(escopo)
    const saude = saudePorSetor(rows)
    const lista = filtrarLista(escopo, f, busca)
    const pagina = usePagina(lista, POR_PAGINA)
    const camposNovos = data.campos_nao_reconhecidos ?? []

    // Troca um filtro de valor único (null tira); `extra` = outros que mudam junto (ex.: status limpa o problema).
    const trocar = (mudancas: Partial<Record<keyof DashboardFilters, string | null>>) => {
        if (!onFiltersChange) return
        const next: DashboardFilters = { ...filters }
        for (const [k, v] of Object.entries(mudancas) as [keyof DashboardFilters, string | null][]) {
            if (v === null) delete next[k]
            else next[k] = [v]
        }
        onFiltersChange(next)
        pagina.setPagina(0)
    }
    const filtrarStatus = (s: FiltroStatus) =>
        trocar({ status_vinculacao: f.status === s || s === 'ativas' ? null : s, problema_vinculacao: null })
    const filtrarSetor = (s: string) => trocar({ setor_vinculacao: f.setor === s ? null : s })
    const filtrarProblema = (tipo: string) =>
        trocar({ problema_vinculacao: f.problema === tipo ? null : tipo, status_vinculacao: null })

    if (rows.length === 0) {
        return (
            <ChartCard title="Vinculações">
                <ChartEmpty>Nenhuma vinculação do LexFlow para este escritório.</ChartEmpty>
            </ChartCard>
        )
    }

    const kpis: { key: FiltroStatus; label: string; valor: number; status?: StatusVinculacao; sub: string }[] = [
        { key: 'ativas', label: 'Vinculações ativas', valor: t.ativas, sub: 'a base da auditoria' },
        { key: 'ok', label: 'OK', valor: t.ok, status: 'ok', sub: `${pct(t.ok, t.ativas)}% das ativas` },
        {
            key: 'incompleta',
            label: 'Falta configurar',
            valor: t.incompleta,
            status: 'incompleta',
            sub: `${pct(t.incompleta, t.ativas)}% das ativas`,
        },
        { key: 'erro', label: 'Com erro', valor: t.erro, status: 'erro', sub: `${pct(t.erro, t.ativas)}% das ativas` },
        { key: 'inativa', label: 'Inativas', valor: t.inativa, status: 'inativa', sub: 'fora da auditoria' },
    ]

    return (
        <div className="dsecs">
            {camposNovos.length > 0 && (
                <div className="vc-aviso" role="status">
                    <Icon name="info" size={16} />
                    <div>
                        <strong>
                            O LexFlow tem {fmt.int(camposNovos.length)} campo(s) de configuração novo(s) ainda não
                            auditado(s)
                        </strong>
                        <p className="muted small">
                            Eles já aparecem no detalhe de cada vinculação (“Outras configurações”) e na exportação, mas
                            o painel ainda não sabe dizer se estão certos ou errados:{' '}
                            <span className="vc-mono">{camposNovos.join(', ')}</span>
                        </p>
                    </div>
                </div>
            )}

            <DashSection
                index={1}
                eyebrow="Visão geral"
                title="Saúde das vinculações"
                subtitle={
                    f.setor
                        ? `Setor ${f.setor}. Clique num card para filtrar a lista pelo status.`
                        : 'Todas as vinculações (setor + atividade) do escritório. Clique num card para filtrar a lista pelo status.'
                }
            >
                <div className="vc-kpis">
                    {kpis.map((k) => {
                        const tone = k.status ? STATUS_META[k.status].tone : 'accent'
                        const ativo = f.status === k.key && !(k.key === 'ativas' && f.problema)
                        return (
                            <button
                                key={k.key}
                                type="button"
                                className={`card vc-kpi tone-${tone}`}
                                aria-pressed={ativo}
                                onClick={() => filtrarStatus(k.key)}
                            >
                                <span className="vc-kpi-l">
                                    <Icon name={k.status ? ICONE_STATUS[k.status] : 'flow'} size={15} />
                                    {k.label}
                                </span>
                                <span className="vc-kpi-v num">{fmt.int(k.valor)}</span>
                                <span className="muted small">{k.sub}</span>
                            </button>
                        )
                    })}
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Onde ajustar"
                title="Setores e problemas"
                subtitle="Só as vinculações ativas. Clique num setor ou num problema para filtrar a lista (de novo, para tirar)."
            >
                <div className="grid dist-grid">
                    <ChartCard
                        title="Saúde por setor"
                        subtitle="Do setor com mais erros para o com menos"
                        tag={f.setor ? <Pill tone="accent">Filtrando: {f.setor}</Pill> : undefined}
                    >
                        {saude.length === 0 ? (
                            <ChartEmpty>Nenhuma vinculação ativa.</ChartEmpty>
                        ) : (
                            <ul className="vc-saude" role="list">
                                {saude.map((s) => {
                                    const selecionado = f.setor === s.nome
                                    return (
                                        <li key={s.nome} className={f.setor && !selecionado ? 'dim' : undefined}>
                                            <button
                                                type="button"
                                                aria-pressed={selecionado}
                                                onClick={() => filtrarSetor(s.nome)}
                                            >
                                                <span className="vc-saude-head">
                                                    <strong>{s.nome}</strong>
                                                    <span className="muted small num">
                                                        <span className="tone-text-ok">{pct(s.ok, s.total)}% OK</span>
                                                        {s.incompleta > 0 && (
                                                            <> · {fmt.int(s.incompleta)} falta configurar</>
                                                        )}
                                                        {s.erro > 0 && (
                                                            <>
                                                                {' · '}
                                                                <span className="tone-text-danger">
                                                                    {fmt.int(s.erro)} com erro
                                                                </span>
                                                            </>
                                                        )}
                                                        {' · '}
                                                        {fmt.int(s.total)} ativas
                                                    </span>
                                                </span>
                                                <span className="vc-barra" aria-hidden="true">
                                                    {(['ok', 'incompleta', 'erro'] as const).map((st) =>
                                                        s[st] > 0 ? (
                                                            <span
                                                                key={st}
                                                                style={
                                                                    {
                                                                        flexGrow: s[st],
                                                                        background: STATUS_META[st].cor,
                                                                    } as CSSProperties
                                                                }
                                                            />
                                                        ) : null,
                                                    )}
                                                </span>
                                            </button>
                                        </li>
                                    )
                                })}
                            </ul>
                        )}
                        <ul className="chart-legend" role="list">
                            {(['ok', 'incompleta', 'erro'] as const).map((st) => (
                                <li key={st}>
                                    <span className="chart-key" style={{ background: STATUS_META[st].cor }} />
                                    {STATUS_META[st].label}
                                </li>
                            ))}
                        </ul>
                    </ChartCard>

                    <ChartCard
                        title="O que precisa de ajuste"
                        subtitle="Vinculações ativas por tipo de problema; erros primeiro"
                        tag={f.problema ? <Pill tone="accent">Filtrando por problema</Pill> : undefined}
                    >
                        {ranking.length === 0 ? (
                            <p className="vc-tudo-ok">
                                <Icon name="check-circle" size={16} />
                                Nenhum problema encontrado nesse recorte.
                            </p>
                        ) : (
                            <ul className="vc-ranking" role="list">
                                {ranking.map((p) => {
                                    const selecionado = f.problema === p.tipo
                                    const tone = STATUS_META[p.nivel].tone
                                    return (
                                        <li key={p.tipo} className={f.problema && !selecionado ? 'dim' : undefined}>
                                            <button
                                                type="button"
                                                aria-pressed={selecionado}
                                                onClick={() => filtrarProblema(p.tipo)}
                                            >
                                                <span className={`vc-ranking-ico tone-${tone}`} aria-hidden="true">
                                                    <Icon
                                                        name={selecionado ? 'check-circle' : ICONE_STATUS[p.nivel]}
                                                        size={15}
                                                    />
                                                </span>
                                                <span className="vc-ranking-tipo">{p.tipo}</span>
                                                <Pill tone={tone}>{fmt.int(p.vinculacoes)}</Pill>
                                            </button>
                                        </li>
                                    )
                                })}
                            </ul>
                        )}
                    </ChartCard>
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Lista"
                title="Vinculações"
                subtitle="O que cada vinculação faz ao agendar, ao concluir e no cumprido / não cumprido. Clique no nome para ver o detalhe."
            >
                <ChartCard
                    title={`${fmt.int(lista.length)} ${lista.length === 1 ? 'vinculação encontrada' : 'vinculações encontradas'}`}
                    subtitle={f.problema ? `Problema: ${f.problema}` : undefined}
                    action={
                        <label className="fmenu-search vc-busca">
                            <Icon name="search" size={16} />
                            <span className="sr-only">Buscar vinculações</span>
                            <input
                                type="search"
                                placeholder="Buscar setor, atividade ou destino..."
                                value={busca}
                                onChange={(e) => {
                                    setBusca(e.target.value)
                                    pagina.setPagina(0)
                                }}
                            />
                        </label>
                    }
                >
                    <div className="vc-lista">
                        <DataTable
                            rows={pagina.itens}
                            rowKey={(r) => String(r.ID_VINCULACAO)}
                            rowClassName={(r) => `vc-linha vc-linha-${r.STATUS}`}
                            empty="Nenhuma vinculação encontrada com esses filtros."
                            columns={[
                                { header: 'Status', render: (r) => <StatusPill status={r.STATUS} /> },
                                {
                                    header: 'Setor · Atividade',
                                    render: (r) => (
                                        <button type="button" className="linkbtn vc-nome" onClick={() => setDetalhe(r)}>
                                            <strong>{r.SETOR}</strong>
                                            <span className="muted small">{r.ATIVIDADE}</span>
                                        </button>
                                    ),
                                },
                                { header: 'Ao agendar', render: (r) => <Agendamento r={r} /> },
                                { header: 'Ao concluir', render: (r) => <Encerramento r={r} /> },
                                { header: 'Cumprido →', render: (r) => <FluxoCelula fluxo={r.FLUXO_CUMPRIDO} /> },
                                {
                                    header: 'Não cumprido →',
                                    render: (r) => <FluxoCelula fluxo={r.FLUXO_NAO_CUMPRIDO} />,
                                },
                                { header: 'Problemas', render: (r) => <Problemas r={r} /> },
                            ]}
                        />
                    </div>
                    <Paginador pagina={pagina.pagina} total={pagina.total} onChange={pagina.setPagina} />
                </ChartCard>
            </DashSection>

            {detalhe && <Detalhe r={detalhe} onClose={() => setDetalhe(null)} />}
        </div>
    )
}

function StatusPill({ status }: { status: StatusVinculacao }) {
    const meta = STATUS_META[status]
    return (
        <Pill tone={meta.tone}>
            <Icon name={ICONE_STATUS[status]} size={12} />
            {meta.label}
        </Pill>
    )
}

const Nada = ({ children = '—' }: { children?: string }) => <span className="muted small">{children}</span>

function Agendamento({ r }: { r: Vinculacao }) {
    const { FASE_AGENDAMENTO: fase, SUBFASE_AGENDAMENTO: subfase, SITUACAO_AGENDAMENTO: situacao } = r
    if (!fase && !subfase && !situacao) return <Nada>Não altera</Nada>
    return (
        <div className="vc-celula">
            {fase && <strong>{fase}</strong>}
            {subfase && <span className="muted">{subfase}</span>}
            {situacao && <span className="muted">Situação: {situacao}</span>}
            {r.GATILHO_AGENDAMENTO_ATIVO === false && <Pill tone="neutral">gatilho desligado</Pill>}
        </div>
    )
}

// Fase/subfase aplicada ao encerrar por um fluxo (ticket 871 do LexFlow: o não cumprido também aplica).
function Conclusao({ r, fluxo }: { r: Vinculacao; fluxo: FluxoEncerramento }) {
    const g = gatilhoDoFluxo(r, fluxo)
    if (!g) return <Nada />
    if (g.ORIGEM === 'slots' && !g.FASE && !g.SUBFASE) {
        return (
            <div className="vc-celula">
                <strong>Varia por encaminhamento</strong>
                <span className="muted">{fmt.int(g.QTD_SLOTS_ATIVOS)} gatilho(s): ver o detalhe</span>
            </div>
        )
    }
    if (!g.FASE && !g.SUBFASE) return <Nada>Não altera</Nada>
    return (
        <div className="vc-celula">
            {g.FASE && <strong>{g.FASE}</strong>}
            {g.SUBFASE && <span className="muted">{g.SUBFASE}</span>}
            {g.ORIGEM === 'nenhum' && !g.ATIVO && <Pill tone="neutral">gatilho desligado</Pill>}
            {fluxo === 'nao_cumprido' && g.ORIGEM === 'flat' && <Pill tone="danger">herdado do cumprido</Pill>}
        </div>
    )
}

// Coluna "Ao concluir": o cumprido e, quando o não cumprido também mexe na ficha, uma linha com ele.
function Encerramento({ r }: { r: Vinculacao }) {
    const nc = r.GATILHO_ENCERRAMENTO_NAO_CUMPRIDO
    return (
        <div className="vc-celula">
            <Conclusao r={r} fluxo="cumprido" />
            {nc && nc.ORIGEM !== 'nenhum' && (
                <span className="vc-nc small">
                    <strong>Não cumprido:</strong>{' '}
                    {nc.ORIGEM === 'slots' && !nc.FASE && !nc.SUBFASE
                        ? 'varia por encaminhamento'
                        : [nc.FASE, nc.SUBFASE].filter(Boolean).join(' / ')}
                    {nc.ORIGEM === 'flat' && <span className="tone-text-danger"> (herdado)</span>}
                </span>
            )}
        </div>
    )
}

function FluxoCelula({ fluxo, completo = false }: { fluxo: Fluxo; completo?: boolean }) {
    const destinos = completo ? fluxo.DESTINOS : fluxo.DESTINOS.slice(0, 2)
    return (
        <div className="vc-celula" title={fluxo.DESTINOS.map((d) => d.TEXTO).join('\n') || undefined}>
            <span>
                <Pill tone={MODO_TONE[fluxo.MODO]}>{fluxo.MODO_LABEL}</Pill>
            </span>
            {semDestino(fluxo) && <span className="tone-text-warn small">Sem destino definido</span>}
            {destinos.map((d, i) => {
                const quebrado = DESTINO_QUEBRADO.has(d.SITUACAO)
                return (
                    <span
                        key={i}
                        className={
                            quebrado ? 'vc-destino tone-text-danger' : d.SITUACAO === 'sem_destino' ? 'muted' : ''
                        }
                    >
                        {quebrado && <Icon name="alert" size={12} />} {d.TEXTO}
                    </span>
                )
            })}
            {!completo && fluxo.DESTINOS.length > 2 && (
                <span className="muted small">+{fmt.int(fluxo.DESTINOS.length - 2)} outro(s)</span>
            )}
        </div>
    )
}

function Problemas({ r }: { r: Vinculacao }) {
    const incompletos = r.QTD_PROBLEMAS - r.QTD_ERROS
    if (r.QTD_PROBLEMAS === 0) return <Nada />
    return (
        <div className="vc-problemas" title={r.PROBLEMAS.join('\n')}>
            {r.QTD_ERROS > 0 && <Pill tone="danger">{fmt.int(r.QTD_ERROS)} erro(s)</Pill>}
            {incompletos > 0 && <Pill tone="warn">{fmt.int(incompletos)} pendente(s)</Pill>}
        </div>
    )
}

function GatilhosDetalhe({ r, fluxo }: { r: Vinculacao; fluxo: FluxoEncerramento }) {
    const slots = slotsDoFluxo(r, fluxo)
    const g = gatilhoDoFluxo(r, fluxo)
    return (
        <div className="vc-celula">
            {slots.length > 0 && (
                <ul className="vc-slots" role="list">
                    {slots.map((s, i) => (
                        <li key={i} className={s.ATIVO ? undefined : 'dim'}>
                            <strong>{s.OPCAO}</strong>
                            <span className="muted">
                                {s.ATIVO
                                    ? [s.FASE, s.SUBFASE].filter(Boolean).join(' / ') ||
                                      'Ativo, sem fase/subfase (não altera)'
                                    : 'Gatilho desligado'}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
            {(slots.length === 0 || g?.ORIGEM !== 'slots') && <Conclusao r={r} fluxo={fluxo} />}
            {fluxo === 'nao_cumprido' && g?.ORIGEM === 'flat' && (
                <p className="small tone-text-danger">
                    Sem opção ativa de Não Cumprido na aba “Trigger de Encerramento” do LexFlow: desde o ticket 871 o
                    encerramento não cumprido aplica a fase/subfase do gatilho geral (a mesma do cumprido).
                </p>
            )}
        </div>
    )
}

function Detalhe({ r, onClose }: { r: Vinculacao; onClose: () => void }) {
    return (
        <Modal
            title={r.VINCULACAO}
            subtitle={`Vinculação #${r.ID_VINCULACAO}${r.ESCRITORIO ? ` · ${r.ESCRITORIO}` : ''}`}
            aside={<StatusPill status={r.STATUS} />}
            className="vc-modal"
            onClose={onClose}
        >
            <div className="vc-detalhe">
                {!r.TEM_CONFIGURACAO && (
                    <p>
                        <Pill tone="warn">Sem configuração</Pill>
                    </p>
                )}
                {(['erro', 'incompleta'] as const).map((nivel) => {
                    const itens = r.PROBLEMAS_DETALHE.filter((p) => p.NIVEL === nivel)
                    if (itens.length === 0) return null
                    return (
                        <div key={nivel} className={`vc-caixa tone-${STATUS_META[nivel].tone}`}>
                            <strong>
                                <Icon name={ICONE_STATUS[nivel]} size={15} />
                                {nivel === 'erro' ? 'Configuração com erro' : 'Falta configurar'}
                            </strong>
                            <ul>
                                {itens.map((p, i) => (
                                    <li key={i}>{p.MENSAGEM}</li>
                                ))}
                            </ul>
                        </div>
                    )
                })}

                <div className="vc-par">
                    <Bloco titulo="Próxima atividade: CUMPRIDO">
                        <FluxoCelula fluxo={r.FLUXO_CUMPRIDO} completo />
                    </Bloco>
                    <Bloco titulo="Próxima atividade: NÃO CUMPRIDO">
                        <FluxoCelula fluxo={r.FLUXO_NAO_CUMPRIDO} completo />
                    </Bloco>
                </div>
                <div className="vc-par">
                    <Bloco titulo="Ao agendar (gatilho de criação)">
                        <Agendamento r={r} />
                    </Bloco>
                </div>
                <div className="vc-par">
                    <Bloco titulo="Ao concluir como cumprido">
                        <GatilhosDetalhe r={r} fluxo="cumprido" />
                    </Bloco>
                    <Bloco titulo="Ao concluir como não cumprido">
                        <GatilhosDetalhe r={r} fluxo="nao_cumprido" />
                    </Bloco>
                </div>
                <div className="vc-par">
                    <Bloco titulo="Regra para cumprido">
                        <span className="muted">{regraCumprido(r)}</span>
                    </Bloco>
                    <Bloco titulo="Regra para não cumprido">
                        <span className="muted">{regraNaoCumprido(r)}</span>
                    </Bloco>
                </div>
                <Bloco titulo={`Campos obrigatórios (${fmt.int(r.QTD_CAMPOS_OBRIGATORIOS)})`}>
                    {r.CAMPOS_OBRIGATORIOS.length > 0 ? (
                        <div className="vc-tags">
                            {r.CAMPOS_OBRIGATORIOS.map((c) => (
                                <Pill key={c}>{c}</Pill>
                            ))}
                        </div>
                    ) : (
                        <span className="muted">Nenhum campo obrigatório configurado.</span>
                    )}
                </Bloco>
                {r.OUTRAS_CONFIGURACOES.length > 0 && (
                    <Bloco titulo="Outras configurações">
                        <dl className="vc-outras">
                            {r.OUTRAS_CONFIGURACOES.map((o) => (
                                <div key={o.CAMPO}>
                                    <dt className="muted small">
                                        {o.LABEL} {!o.CONHECIDO && <Pill tone="info">novo</Pill>}
                                    </dt>
                                    <dd>{o.VALOR}</dd>
                                </div>
                            ))}
                        </dl>
                    </Bloco>
                )}
                {r.CONFIGURACAO_ATUALIZADO_EM && (
                    <p className="muted small">
                        Configuração alterada pela última vez em{' '}
                        {new Date(r.CONFIGURACAO_ATUALIZADO_EM).toLocaleString('pt-BR')}
                    </p>
                )}
            </div>
        </Modal>
    )
}

function Bloco({ titulo, children }: { titulo: string; children: ReactNode }) {
    return (
        <section className="vc-bloco">
            <h3 className="vc-bloco-t">{titulo}</h3>
            {children}
        </section>
    )
}
