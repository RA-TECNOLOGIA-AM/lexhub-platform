import { InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { AgendamentosSecao } from '../setor/AgendamentosSecao.tsx'
import {
    ROTULO_FAIXA,
    lerIntermediarias,
    type Dilacao,
    type PendenciasIntermediariasResponse,
} from './intermediarias.ts'

// A atividade que entra na dilação, como a nota do card da v1 (NG: todas menos SANAR PENDÊNCIA 1G; LA: as duas de
// documentos).
const NOTA_DILACAO = {
    NG: 'Atividades do setor e Emenda - Solicitar Docs com Cliente, exceto Sanar Pendência 1G',
    LA: 'Solicitar Docs do Cliente · Solicitar Docs de Hipossuficiência do Cliente para Recurso',
    RJ: 'Atividades do setor e Emenda - Solicitar Docs com Cliente, exceto Sanar Pendência 1G', // a regra do NG
}

// Pendências Intermediárias (NG e LA): a seção única da página da v1 no layout da V2, com a troca Por prazo |
// Concluídas. Cliques em "Por atividade", "Demandas por funcionário" e na média filtram a página (vão na URL e na API,
// como os filtros da v1); o histórico "mês a mês" segue o filtro de funcionário somando as séries de cada um.
export function IntermediariasContent({
    data,
    filters = {},
    onToggleFilter,
}: ContentProps<PendenciasIntermediariasResponse>) {
    const p = lerIntermediarias(data)
    return (
        <div className="dsecs">
            <AgendamentosSecao
                eyebrow="Pendências Intermediárias"
                setorNome="Pendências Intermediárias"
                visoes={p.visoes}
                filters={filters}
                onToggleFilter={onToggleFilter}
                chaves={{ funcionario: 'funcionario_intermediarias', atividade: 'atividade_intermediarias' }}
                bloco={<DilacaoCard d={p.dilacao} nota={NOTA_DILACAO[p.unidade]} />}
                textos={{
                    emAndamento: 'Iniciado, Reaberto ou Encaminhado',
                    porAtividade: (porPrazo) =>
                        `Processos distintos por atividade, ${porPrazo ? 'com prazo' : 'criados'} no período`,
                    media: (porPrazo) =>
                        `Encerradas ÷ dias com ${porPrazo ? 'prazo' : 'conclusão'}, histórico todo · clique para filtrar`,
                }}
            />
        </div>
    )
}

// O card de dilação da v1: a taxa do setor no período, a faixa e o medidor de 0 a 20%+.
function DilacaoCard({ d, nota }: { d: Dilacao; nota: string }) {
    const semDados = d.taxa === null || !d.totalEncerrados
    const faixa = semDados ? null : d.faixa
    const selo = semDados ? 'Sem dados' : faixa ? `Faixa ${ROTULO_FAIXA[faixa]}` : 'Fora das faixas'
    const classe = semDados ? 'sem' : (faixa ?? 'fora')
    const posicao = Math.min((d.taxa ?? 0) / 20, 1) * 100
    return (
        <div className={`card pi-dil pi-${classe}`}>
            <div className="pi-dil-info">
                <div className="pi-dil-topo">
                    <span className="hero-l">
                        Dilações no período{' '}
                        <InfoTip text="Dilações de prazo pedidas no período ÷ atividades encerradas no período. Faixas: até 5% Ouro, até 10% Prata, até 15% Bronze; acima, fora das faixas." />
                    </span>
                    <span className={`pi-selo pi-${classe}`}>{selo}</span>
                </div>
                <div className="pi-dil-valor">
                    <strong className="num">{semDados ? '—' : `${fmt.dec1(d.taxa ?? 0)}%`}</strong>
                    <span className="muted small">
                        {d.count === null ? '—' : fmt.int(d.count)} dilações de{' '}
                        {d.totalEncerrados === null ? '—' : fmt.int(d.totalEncerrados)} encerradas
                    </span>
                </div>
                <span className="muted small">{nota}</span>
            </div>
            <div className="pi-dil-escala">
                <div className="pi-medidor" aria-hidden="true">
                    <span className="z ouro" />
                    <span className="z prata" />
                    <span className="z bronze" />
                    <span className="z fora" />
                    {!semDados && <i style={{ left: `${posicao}%` }} />}
                </div>
                <div className="pi-medidor-leg muted small num" aria-hidden="true">
                    <span>0%</span>
                    <span>5%</span>
                    <span>10%</span>
                    <span>15%</span>
                    <span>20%+</span>
                </div>
            </div>
        </div>
    )
}
