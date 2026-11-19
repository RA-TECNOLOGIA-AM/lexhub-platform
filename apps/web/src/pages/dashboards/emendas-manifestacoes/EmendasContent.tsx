import { DeltaPill, InfoTip, MiniStat } from '../../../components/dashboard/StatCard.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { AgendamentosSecao } from '../setor/AgendamentosSecao.tsx'
import {
    COR_GERA,
    COR_NAO_GERA,
    ROTULO_FAIXA,
    agendaAgregada,
    coresAtividades,
    lerEmendas,
    type Agenda,
    type EmendasResponse,
} from './emendas.ts'

// Emendas e Manifestações (NG e LA): a seção da página da v1 (a mesma das Pendências Intermediárias), com o bloco
// de comissão no lugar da dilação: a agenda cumprida (NG: informativa, com as peças e o comparativo; LA: a faixa
// da comissão) e o "Por atividade" pintado pelo que gera comissão.
export function EmendasContent({ data, filters = {}, onToggleFilter }: ContentProps<EmendasResponse>) {
    const e = lerEmendas(data)
    const funcionarios = filters.funcionario_emendas_manifestacoes ?? []
    const agenda = agendaAgregada(e.comissao, funcionarios)
    const cores = {
        ...coresAtividades(e.visoes.por_prazo.porAtividade, e.regra),
        ...coresAtividades(e.visoes.concluidas.porAtividade, e.regra),
    }
    return (
        <div className="dsecs">
            <AgendamentosSecao
                eyebrow="Emendas e Manifestações"
                setorNome="Emendas e Manifestações"
                visoes={e.visoes}
                filters={filters}
                onToggleFilter={onToggleFilter}
                chaves={{
                    funcionario: 'funcionario_emendas_manifestacoes',
                    atividade: 'atividade_emendas_manifestacoes',
                }}
                outrosFiltros={(filters.uf_emendas_manifestacoes ?? []).length}
                bloco={
                    e.regra === 'NG' ? (
                        <div className="grid em-ng">
                            <AgendaCard a={agenda} />
                            <MiniStat
                                label="Manifestações no período"
                                icon="sheet"
                                tone="ok"
                                value={fmt.int(agenda.manifestacoes)}
                                hint="Peças de Manifestação produzidas (Encerrado Cumprido, prazo no período), comparadas aos mesmos dias do mês anterior."
                                below={<DeltaPill value={e.comparativo.manifestacoes} suffix="vs mês anterior" />}
                            />
                            <MiniStat
                                label="Dilações no período"
                                icon="clock"
                                tone="info"
                                value={fmt.int(agenda.dilacoes)}
                                hint="Peças de Dilação produzidas (Encerrado Cumprido, prazo no período), comparadas aos mesmos dias do mês anterior."
                                below={<DeltaPill value={e.comparativo.dilacoes} suffix="vs mês anterior" />}
                            />
                        </div>
                    ) : (
                        <AgendaCard a={agenda} faixas />
                    )
                }
                textos={{
                    emAndamento: 'Recebido, Visualizado, Iniciado, Reaberto ou Encaminhado',
                    porAtividade: (porPrazo) =>
                        `Encerradas por atividade, com ${porPrazo ? 'prazo' : 'conclusão'} no período · clique para filtrar`,
                    media: (porPrazo) =>
                        `Encerradas ÷ dias com ${porPrazo ? 'prazo' : 'conclusão'}, no período · clique para filtrar`,
                }}
                coresAtividade={cores}
                legendaAtividade={
                    <span className="em-legenda small">
                        <i style={{ background: COR_GERA }} /> Gera comissão
                        <i style={{ background: COR_NAO_GERA }} /> Não gera
                    </span>
                }
            />
        </div>
    )
}

// "Agenda cumprida no período" da v1: agendamentos com prazo no período já encerrados ÷ todos (encerrados + em
// aberto). No LA é o que define a faixa da comissão (85% e 97%); no NG é informativa (o NG paga valor fixo).
function AgendaCard({ a, faixas = false }: { a: Agenda; faixas?: boolean }) {
    const classe = !a.temDados
        ? 'sem'
        : !faixas
          ? 'neutra'
          : !a.elegivel
            ? 'fora'
            : a.faixa === 'faixa_2'
              ? 'ouro'
              : 'prata'
    const selo = !a.temDados ? 'Sem dados' : !a.elegivel ? 'Não elegível' : a.faixa ? ROTULO_FAIXA[a.faixa] : ''
    const pos = Math.min(Math.max(a.percentual, 0), 100)
    return (
        <div className={`card pi-dil em-agenda pi-${classe}`}>
            <div className="pi-dil-info">
                <div className="pi-dil-topo">
                    <span className="hero-l">
                        Agenda cumprida no período — {a.rotulo}{' '}
                        <InfoTip
                            text={
                                faixas
                                    ? 'Agendamentos com prazo no período já encerrados (cumpridos ou não) ÷ todos com prazo no período. Abaixo de 85%: não elegível à comissão; de 85%: Faixa 1; de 97%: Faixa 2. No PDF, a faixa é a de cada funcionário.'
                                    : 'Agendamentos com prazo no período já encerrados (cumpridos ou não) ÷ todos com prazo no período. Informativo: no NG a comissão é por peça, com valor fixo.'
                            }
                        />
                    </span>
                    {faixas && <span className={`pi-selo pi-${classe}`}>{selo}</span>}
                </div>
                <div className="pi-dil-valor">
                    <strong className="num">{a.temDados ? `${fmt.dec1(a.percentual)}%` : '—'}</strong>
                    <span className="muted small">
                        {fmt.int(a.finalizada)} de {fmt.int(a.total)} agendamentos
                        {faixas &&
                            ` · ${fmt.int(a.manifestacoes)} ${a.manifestacoes === 1 ? 'manifestação' : 'manifestações'} · ${fmt.int(a.dilacoes)} ${a.dilacoes === 1 ? 'dilação' : 'dilações'}`}
                    </span>
                </div>
            </div>
            <div className="pi-dil-escala">
                {faixas ? (
                    <>
                        <div className="pi-medidor em-medidor-la" aria-hidden="true">
                            <span className="z fora" />
                            <span className="z prata" />
                            <span className="z ouro" />
                            {a.temDados && <i style={{ left: `${pos}%` }} />}
                        </div>
                        <div className="em-leg-la muted small num" aria-hidden="true">
                            <span style={{ left: '0%' }}>0%</span>
                            <span style={{ left: '85%' }}>85%</span>
                            <span style={{ left: '97%' }}>97%</span>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="em-barra" aria-hidden="true">
                            <span style={{ width: `${a.temDados ? pos : 0}%` }} />
                        </div>
                        <div className="pi-medidor-leg muted small num" aria-hidden="true">
                            <span>0%</span>
                            <span>50%</span>
                            <span>100%</span>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
