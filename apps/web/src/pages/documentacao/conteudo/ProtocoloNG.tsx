import {
    Code,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Protocolo_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'represados', label: 'Processos represados' },
    { id: 'tempo', label: 'Tempo de produção' },
    { id: 'valor-causa', label: 'Valor de causa' },
    { id: 'rankings', label: 'Rankings e agrupamentos' },
    { id: 'reajuizamento', label: 'Reajuizamento' },
    { id: 'comissionamento', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros disponíveis' },
]

export function ProtocoloNGDoc() {
    return (
        <DocPage
            title="Protocolo — NG e LARJ"
            tags={['NG', 'LARJ']}
            toc={TOC}
            intro={
                <>
                    O setor de Protocolo recebe os processos organizados pelo Org Doc e os protocola nos sistemas
                    judiciais. Este documento explica como cada número do dashboard é calculado.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como funciona o setor"
                subtitle="Ciclo de vida de um processo no Protocolo"
            >
                <InfoBox>
                    O Protocolo é o último passo antes do processo chegar ao sistema judicial. Os processos chegam do
                    Org Doc já organizados e precisam ser distribuídos ou protocolados. Processos com REAJUIZAMENTO
                    ativado são tratados separadamente e não entram nos totais principais.
                </InfoBox>

                <DocCard title="Fluxo do processo">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        {[
                            { label: 'NÃO INICIADO', color: 'bg-slate-500/10 text-slate-500' },
                            { label: '→', color: '' },
                            {
                                label: 'PRÉ-PROTOCOLADO',
                                color: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
                            },
                            { label: '→', color: '' },
                            {
                                label: 'DISTRIBUÍDO / PROTOCOLADO',
                                color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
                            },
                        ].map((step, i) =>
                            step.color ? <span key={i}>{step.label}</span> : <strong key={i}>{step.label}</strong>,
                        )}
                    </div>
                    <p>
                        O status <strong>NÃO PROTOCOLADO</strong> indica um processo que entrou mas ainda não foi
                        processado. <strong>PRÉ-PROTOCOLADO</strong> está em preparação. Ao ser efetivado, o processo
                        recebe o status <strong>DISTRIBUÍDO</strong> ou <strong>PROTOCOLADO</strong> e uma data de saída
                        (SAIDA) é registrada — essa data é o que delimita o período no dashboard.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores do período"
                subtitle="O que cada número no topo do dashboard representa"
            >
                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Protocolados"
                        what="Quantidade de processos efetivamente protocolados no período selecionado."
                        counts="Processos com STATUS igual a 'DISTRIBUÍDO' ou 'PROTOCOLADO' e REAJUIZAMENTO desativado, cuja data de SAIDA está dentro do período."
                        calc="Contagem direta dos registros que atendem a esses critérios."
                        interpret="Quanto maior, melhor. Indica o volume de trabalho concluído pelo setor no período."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Taxa de Protocolados"
                        what="Percentual de processos que chegaram ao setor e foram protocolados."
                        counts="Numerador: protocolados no período (SAIDA). Denominador: processos que entraram no setor no mesmo período (ENTRADA)."
                        calc="(Qtd protocolados com SAIDA no período ÷ Qtd com ENTRADA no período) × 100"
                        interpret="Uma taxa alta indica que o setor está dando conta do volume de entrada. Abaixo de 80% merece atenção."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor de Causa Protocolado"
                        what="Soma total do valor das causas dos processos protocolados no período."
                        counts="Processos protocolados (DISTRIBUÍDO/PROTOCOLADO) com REAJUIZAMENTO desativado. Para matéria ANP, usa o campo DANO_MORAL; demais matérias usam VALOR_DA_CAUSA."
                        calc="Soma dos valores de causa de todos os processos protocolados."
                        interpret="Acompanhar junto com a meta anual de R$ 300 milhões. Serve como base para o comissionamento comercial."
                    />
                    <MetricCard
                        icon="barChart"
                        name="Ticket Médio"
                        what="Valor médio de causa por processo protocolado."
                        counts="Mesmos processos do indicador de Valor de Causa Protocolado."
                        calc="Valor total de causa protocolado ÷ Quantidade de processos protocolados"
                        interpret="Indica o porte médio dos processos. Um ticket médio alto junto com menos processos pode significar foco em causas de maior valor."
                    />
                    <MetricCard
                        icon="target"
                        name="Processos Protocolados em 2026"
                        what="Volume total de valor de causa protocolado no ano de 2026, comparado à meta anual."
                        counts="Todos os processos protocolados (DISTRIBUÍDO/PROTOCOLADO) com SAIDA em 2026, independente do período selecionado no filtro."
                        calc={
                            <>
                                Soma do valor de causa dos processos protocolados com SAIDA em 2026.
                                <br />
                                Meta anual: <strong>R$ 300.000.000</strong>
                            </>
                        }
                        interpret="Acompanhar o progresso relativo à meta anual do escritório. Esse indicador não é afetado pelo filtro de datas — mostra sempre o ano completo."
                        caveat="Este indicador ignora o filtro de período e sempre exibe o acumulado de 2026 completo."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="represados" title="Processos represados" subtitle="O que está parado no setor">
                <InfoBox>
                    Represados são processos que estão no setor mas ainda não foram protocolados. Diferente dos
                    indicadores do período (que filtram por SAIDA), os represados mostram o acumulado total —
                    independente de quando o processo entrou.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        icon="xCircle"
                        name="Não Iniciados"
                        what="Processos que chegaram ao Protocolo mas ainda não foram trabalhados."
                        counts="STATUS = 'NÃO INICIADO' com REAJUIZAMENTO desativado."
                        calc="Contagem simples."
                        interpret="Fila de entrada do setor. Um número alto pode indicar gargalo de recebimento."
                    />
                    <MetricCard
                        icon="xCircle"
                        name="Não Protocolados"
                        what="Processos que foram identificados como pendentes de protocolo."
                        counts="STATUS = 'NÃO PROTOCOLADO' com REAJUIZAMENTO desativado."
                        calc="Contagem simples."
                        interpret="Processos que foram verificados e identificados como ainda não protocolados."
                    />
                    <MetricCard
                        icon="clock"
                        name="Pré-Protocolados"
                        what="Processos em fase de preparação para o protocolo."
                        counts="STATUS = 'PRÉ-PROTOCOLADO' com REAJUIZAMENTO desativado."
                        calc="Contagem simples."
                        interpret="Processos em andamento. Um volume alto aqui, com poucos saindo como protocolados, pode indicar demora no processamento."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="tempo" title="Tempo de produção" subtitle="Métricas de prazo do setor">
                <DocGrid>
                    <MetricCard
                        icon="clock"
                        name="Tempo no Setor"
                        what="Quanto tempo em média um processo fica dentro do Protocolo até ser protocolado."
                        counts="Processos protocolados no período."
                        calc="SAIDA − ENTRADA (em dias), calculado para cada processo e depois tirada a média."
                        interpret="Quanto menor, melhor. Indica a agilidade interna do setor."
                    />
                    <MetricCard
                        icon="clock"
                        name="Tempo da Contratação ao Protocolo"
                        what="Quanto tempo leva desde a contratação do cliente até o protocolo do processo."
                        counts="Processos protocolados no período que têm DATA_CONTRATACAO preenchida."
                        calc="SAIDA − DATA_CONTRATACAO (em dias)."
                        interpret="Métrica do ciclo completo. Útil para acompanhar SLAs com clientes. Um valor alto pode indicar gargalos em setores anteriores (Pendências, Org Doc, Peticionamento)."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="valor-causa" title="Valor de causa" subtitle="Como o valor das causas é calculado">
                <InfoBox>
                    O valor de causa muda de campo dependendo da matéria do processo. Para processos de matéria{' '}
                    <strong>ANP</strong>, usa-se o campo <strong>DANO_MORAL</strong>. Para todas as outras matérias,
                    usa-se o campo <strong>VALOR_DA_CAUSA</strong>. Processos com valor nulo ou zero são desconsiderados
                    do somatório.
                </InfoBox>
                <DocCard title="Normalização da matéria">
                    <p>
                        A matéria de um processo pode vir no formato <Code>BX_ANT_FIN - BANCO BRADESCO</Code>. Para fins
                        de agrupamento e cálculo, apenas a parte antes do " - " é utilizada: <Code>BX_ANT_FIN</Code>.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="rankings"
                title="Rankings e agrupamentos"
                subtitle="Como os processos são agrupados nos gráficos"
            >
                <DocGrid>
                    <DocCard>
                        <p> Por Funcionário</p>
                        <p>
                            Protocolados e represados agrupados por FUNCIONARIO. O nome é normalizado para as duas
                            primeiras palavras em maiúsculo.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por Matéria</p>
                        <p>
                            Agrupado pela matéria normalizada (parte antes do " - "). Mostra quais tipos de causa têm
                            mais volume.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por Sistema</p>
                        <p>
                            Agrupado pelo campo SISTEMA. Útil para entender em qual sistema judicial cada processo está
                            sendo protocolado.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por Atendente</p>
                        <p>
                            Agrupado pelo responsável pelo atendimento ao cliente. Mostra distribuição comercial por
                            atendente.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="reajuizamento"
                title="Reajuizamento"
                subtitle="Como processos de reajuizamento são tratados"
            >
                <InfoBox>
                    Processos com o campo REAJUIZAMENTO ativado seguem o mesmo fluxo de status, mas são contabilizados
                    separadamente. Os indicadores principais (protocolados, represados, valor de causa, comissão)
                    consideram apenas processos com REAJUIZAMENTO desativado. Os processos de reajuizamento aparecem em
                    seção própria no dashboard.
                </InfoBox>
            </DocSection>

            <DocSection
                id="comissionamento"
                title="Comissionamento"
                subtitle="Como a comissão dos funcionários é calculada"
            >
                <InfoBox>
                    O Protocolo NG/LARJ possui dois tipos de comissão: uma comissão direta por processo protocolado, e
                    uma comissão proporcional ao valor de causa por estado (utilizada para análise comercial).
                </InfoBox>

                <div className="stack">
                    <DocCard title="Comissão por processo protocolado">
                        <p>
                            Cada processo protocolado (STATUS = DISTRIBUÍDO ou PROTOCOLADO) vale{' '}
                            <strong>R$ 1,00</strong> de comissão para o funcionário responsável. É uma taxa fixa,
                            independente do valor da causa.
                        </p>
                        <DocCard>
                            <Code>Comissão = R$ 1,00 × Qtd de processos protocolados</Code>
                        </DocCard>
                        <p>Exemplo: funcionário com 150 processos protocolados → R$ 150,00</p>
                    </DocCard>

                    <DocCard title="Comissão com Fator Multiplicador — por estado (AM, PA, PB)">
                        <p>
                            Para o acompanhamento comercial, existe um cálculo adicional que considera o valor de causa
                            total e distribui a comissão proporcionalmente por estado. O Fator Multiplicador (FM) é
                            aplicado sobre a comissão base.
                        </p>

                        <div>
                            <div className="card tblwrap">
                                <table className="tbl">
                                    <thead>
                                        <tr>
                                            <th>Valor total de causa</th>
                                            <th>Fator Multiplicador (FM)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Acima de R$ 4.000.000</td>
                                            <td>4,0 (fixo)</td>
                                        </tr>
                                        <tr>
                                            <td>Entre R$ 2.500.000 e R$ 4.000.000</td>
                                            <td>Valor total ÷ 1.000.000</td>
                                        </tr>
                                        <tr>
                                            <td>Abaixo de R$ 2.500.000</td>
                                            <td>1,0 (sem multiplicador)</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <DocCard>
                            <Code>Comissão base = Valor de causa ÷ 1.000.000</Code>
                            <Code>Comissão com FM = FM × Comissão base</Code>
                            <Code>Comissão por estado = (Valor do estado ÷ Total) × Comissão com FM</Code>
                        </DocCard>
                        <p>
                            Essa comissão é dividida proporcionalmente entre os estados (AM, PA, PB) de acordo com o
                            valor de causa de cada um.
                        </p>
                    </DocCard>
                </div>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como os dados podem ser segmentados">
                <DocGrid>
                    {[
                        {
                            label: 'Período',
                            desc: 'Filtra pela data de SAIDA do processo. Todos os indicadores do período (protocolados, taxa, valor de causa, ticket médio) obedecem esse filtro. Os represados e o indicador de 2026 não são afetados.',
                        },
                        {
                            label: 'Matéria',
                            desc: "Filtra por tipo de causa (ex: BX_ANT_FIN, ANP). A matéria é normalizada para a parte antes do ' - '.",
                        },
                        {
                            label: 'Funcionário',
                            desc: 'Filtra pelos processos atribuídos a um ou mais funcionários específicos.',
                        },
                        {
                            label: 'Sistema',
                            desc: 'Filtra pelo sistema judicial onde o processo foi protocolado (campo SISTEMA).',
                        },
                    ].map((f) => (
                        <DocCard>
                            <p>{f.label}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
