import { InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { AgendamentosSecao } from '../setor/AgendamentosSecao.tsx'
import { lerReplicas, type Procedencia, type ReplicasResponse } from './replicas.ts'

// Réplicas (NG e LA): a seção da página da v1 (a mesma das Pendências Intermediárias e de Emendas e Manifestações),
// com o card de taxa de procedência (1G) dos processos com réplica no lugar do bloco do setor.
export function ReplicasContent({ data, filters = {}, onToggleFilter }: ContentProps<ReplicasResponse>) {
    const r = lerReplicas(data)
    return (
        <div className="dsecs">
            <AgendamentosSecao
                eyebrow="Réplicas"
                setorNome="Réplicas"
                visoes={r.visoes}
                filters={filters}
                onToggleFilter={onToggleFilter}
                chaves={{ funcionario: 'funcionario_replicas', atividade: 'atividade_replicas' }}
                bloco={<ProcedenciaCard p={r.procedencia} unidade={r.unidade} />}
                textos={{
                    emAndamento: 'Recebido, Visualizado, Iniciado, Reaberto ou Encaminhado',
                    porAtividade: (porPrazo) =>
                        `Encerradas por atividade, com ${porPrazo ? 'prazo' : 'conclusão'} no período · clique para filtrar`,
                    media: (porPrazo) =>
                        `Encerradas ÷ dias com ${porPrazo ? 'prazo' : 'conclusão'}, histórico todo · clique para filtrar`,
                }}
            />
        </div>
    )
}

// "Taxa de procedência (1G) — processos com réplica apresentada" da v1: dos processos com réplica criada no período,
// quantos já têm sentença de 1º grau e, desses, quantos foram procedentes (com ou sem proveito, total ou parcial).
function ProcedenciaCard({ p, unidade }: { p: Procedencia; unidade: 'NG' | 'LA' | 'RJ' }) {
    const temDados = (p.decididos ?? 0) > 0
    const pos = temDados ? Math.min(Math.max(p.taxa ?? 0, 0), 100) : 0
    return (
        <div className={`card pi-dil em-agenda pi-${temDados ? 'neutra' : 'sem'}`}>
            <div className="pi-dil-info">
                <div className="pi-dil-topo">
                    <span className="hero-l">
                        Taxa de procedência (1G) — processos com réplica apresentada{' '}
                        <InfoTip
                            text={`Processos com réplica criada no período (${unidade !== 'LA' ? 'atividades ELABORAR RÉPLICA, SIMPLES ou ESPECÍFICA' : 'qualquer atividade do setor'}), com os filtros da página. Decididos: já têm status de 1º grau; procedentes: procedente ou parcialmente procedente, com ou sem proveito econômico. O status é o atual do processo.`}
                        />
                    </span>
                    <span className={`pi-selo pi-${temDados ? 'neutra' : 'sem'}`}>{temDados ? '1G' : 'Sem dados'}</span>
                </div>
                <div className="pi-dil-valor">
                    <strong className="num">{temDados ? `${fmt.dec1(p.taxa ?? 0)}%` : '—'}</strong>
                    <span className="muted small">
                        {fmt.int(p.procedentes ?? 0)} procedente(s) de {fmt.int(p.decididos ?? 0)} decidido(s) ·{' '}
                        {fmt.int(p.totalProcessos ?? 0)} processo(s) com réplica, {fmt.int(p.pendentes ?? 0)} sem
                        decisão
                    </span>
                </div>
            </div>
            <div className="pi-dil-escala">
                <div className="em-barra" aria-hidden="true">
                    <span style={{ width: `${pos}%` }} />
                </div>
                <div className="pi-medidor-leg muted small num" aria-hidden="true">
                    <span>0%</span>
                    <span>50%</span>
                    <span>100%</span>
                </div>
            </div>
        </div>
    )
}
