import {
    Code,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Peticionamento_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'filtro-data', label: 'Filtro de data especial' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'represados', label: 'Processos represados' },
    { id: 'manual-automatico', label: 'Manual vs Automático' },
    { id: 'tempo', label: 'Tempo de produção' },
    { id: 'rankings', label: 'Rankings e agrupamentos' },
    { id: 'reajuizamento', label: 'Reajuizamento' },
    { id: 'comissionamento', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros disponíveis' },
]

export function PeticionamentoNGDoc() {
    return (
        <DocPage
            title="Peticionamento — NG e LARJ"
            tags={['NG', 'LARJ']}
            toc={TOC}
            intro={
                <>
                    O Peticionamento é responsável pela confecção das petições antes do protocolo. Este documento
                    explica como cada métrica do dashboard é calculada, incluindo um ponto importante sobre o filtro de
                    data.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como funciona o setor"
                subtitle="Ciclo de vida de um processo no Peticionamento"
            >
                <InfoBox>
                    O Peticionamento recebe processos do Org Doc e é responsável por confeccionar as petições que serão
                    enviadas ao Protocolo. Uma petição pode ser feita manualmente pelo funcionário ou gerada
                    automaticamente pelo sistema (PET_AUTO). Após confeccionada, o processo vai para o Protocolo com
                    STATUS "PROTOCOLAR".
                </InfoBox>

                <DocCard title="Fluxo do processo">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        {[
                            { label: 'NÃO INICIADO', color: 'bg-slate-500/10 text-slate-500' },
                            { label: '→', color: '' },
                            {
                                label: 'RETORNO PENDÊNCIA',
                                color: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
                            },
                            { label: '→', color: '' },
                            { label: 'REVISÃO', color: 'bg-blue-500/10 text-blue-600 dark:text-blue-400' },
                            { label: '→', color: '' },
                            { label: 'PROTOCOLAR', color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' },
                        ].map((step, i) =>
                            step.color ? <span key={i}>{step.label}</span> : <strong key={i}>{step.label}</strong>,
                        )}
                    </div>
                    <p>
                        O processo entra como <strong>NÃO INICIADO</strong>. Se retornou de Pendências, fica como{' '}
                        <strong>RETORNO PENDÊNCIA</strong>. Após confeccionado e revisado, recebe STATUS{' '}
                        <strong>PROTOCOLAR</strong> e está pronto para o setor de Protocolo.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="filtro-data"
                title="Filtro de data especial"
                subtitle="Por que o Peticionamento usa uma data diferente dos outros setores"
            >
                <WatchBox>
                    <div className="stack">
                        <h3 className="doc-h3">Atenção: o filtro de período usa DATA_CONFECCAO, não SAIDA</h3>
                        <p>
                            Todos os outros setores (Pendências, Org Doc, Protocolo) usam a coluna{' '}
                            <strong>SAIDA</strong> para filtrar o período. No Peticionamento NG, o filtro usa a coluna{' '}
                            <strong>DATA_CONFECCAO</strong> — a data em que a petição foi efetivamente confeccionada.
                        </p>
                        <p>
                            Isso significa que ao selecionar um período, o dashboard mostra as petições{' '}
                            <em>confeccionadas</em> naquele período, independente de quando o processo entrou ou saiu do
                            setor.
                        </p>
                    </div>
                </WatchBox>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores do período"
                subtitle="O que cada número no topo do dashboard representa"
            >
                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Peticionados"
                        what="Quantidade de petições confeccionadas no período."
                        counts="Processos com STATUS = 'PROTOCOLAR' e REAJUIZAMENTO desativado, cuja DATA_CONFECCAO está dentro do período."
                        calc="Contagem direta dos registros que atendem a esses critérios."
                        interpret="Volume de petições produzidas pelo setor. Inclui manuais e automáticas."
                        caveat="Filtra por DATA_CONFECCAO, não por SAIDA."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Taxa de Resolvidos"
                        what="Percentual de processos que foram efetivamente peticionados em relação ao total (peticionados + não peticionados)."
                        counts="Numerador: processos PROTOCOLAR (peticionados). Denominador: total = peticionados + NÃO INICIADO + RETORNO PENDÊNCIA."
                        calc="(Qtd peticionados ÷ (Qtd peticionados + Qtd não peticionados)) × 100"
                        interpret="Quanto mais alta, melhor. Diretamente relacionada ao cálculo de comissão dos funcionários."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em Revisão"
                        what="Processos que estão aguardando revisão antes de serem liberados para protocolo."
                        counts="STATUS = 'REVISÃO' com REAJUIZAMENTO desativado."
                        calc="Contagem simples."
                        interpret="Fila de revisão. Um volume alto pode indicar gargalo no processo de qualidade."
                    />
                    <MetricCard
                        icon="clock"
                        name="Tempo de Confecção"
                        what="Média de dias entre a entrada do processo no setor e a confecção da petição."
                        counts="Processos peticionados no período."
                        calc="DATA_CONFECCAO − ENTRADA (em dias), média de todos os processos."
                        interpret="Agilidade do setor. Quanto menor, mais rápida é a produção de petições."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="represados" title="Processos represados" subtitle="O que está na fila do setor">
                <InfoBox>
                    Represados são processos que ainda não foram peticionados. O dashboard mostra o acumulado total —
                    sem filtro de data.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        icon="xCircle"
                        name="Não Iniciados"
                        what="Processos que chegaram ao Peticionamento mas ainda não foram trabalhados."
                        counts="STATUS = 'NÃO INICIADO' com REAJUIZAMENTO desativado. Sem filtro de data."
                        calc="Contagem simples."
                        interpret="Fila de entrada do setor."
                    />
                    <MetricCard
                        icon="xCircle"
                        name="Retorno Pendência"
                        what="Processos que retornaram do setor de Pendências para o Peticionamento."
                        counts="STATUS = 'RETORNO PENDÊNCIA' com REAJUIZAMENTO desativado. Sem filtro de data."
                        calc="Contagem simples."
                        interpret="Processos que precisaram de ajuste antes de prosseguir. Monitorar para identificar causas de retorno."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="manual-automatico"
                title="Manual vs Automático"
                subtitle="Como o sistema diferencia os dois tipos de confecção"
            >
                <InfoBox>
                    Todo processo com STATUS "PROTOCOLAR" foi peticionado. A diferença entre manual e automático é
                    determinada pelo campo <strong>PET_AUTO</strong> do processo.
                </InfoBox>

                <DocGrid>
                    <DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                            <h3 className="doc-h3">Peticionado Automaticamente</h3>
                        </div>
                        <p>
                            STATUS = 'PROTOCOLAR' + <strong>PET_AUTO = TRUE</strong>. O sistema gerou a petição
                            automaticamente. Não entra no cálculo de comissão.
                        </p>
                    </DocCard>
                    <DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                            <h3 className="doc-h3">Peticionado Manualmente</h3>
                        </div>
                        <p>
                            STATUS = 'PROTOCOLAR' + <strong>PET_AUTO = FALSE</strong>. Um funcionário confeccionou a
                            petição. <strong>Apenas esses entram no cálculo de comissão.</strong>
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tempo" title="Tempo de produção" subtitle="Métricas de prazo do setor">
                <DocGrid>
                    <MetricCard
                        icon="clock"
                        name="Tempo de Confecção"
                        what="Quanto tempo leva desde a entrada até a confecção da petição."
                        counts="Processos peticionados (PROTOCOLAR) no período."
                        calc="DATA_CONFECCAO − ENTRADA (em dias)."
                        interpret="Agilidade interna do setor. Quanto menor, melhor."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Tendência Mensal"
                        what="Evolução do volume de petições confeccionadas ao longo dos meses."
                        counts="Processos peticionados agrupados por DATA_CONTRATACAO (mês de contratação do cliente)."
                        calc="Contagem de peticionados por mês."
                        interpret="Permite identificar sazonalidades e crescimento ou queda no volume de petições."
                    />
                </DocGrid>
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
                            Peticionados e represados agrupados por FUNCIONARIO. Nome normalizado para as duas primeiras
                            palavras em maiúsculo.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por Matéria</p>
                        <p>
                            Agrupado pela matéria normalizada (parte antes do " - "). ESPECIFICA é tratada separadamente
                            no comissionamento.
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
                    Processos com REAJUIZAMENTO ativado são contabilizados separadamente. Os indicadores principais
                    (peticionados, taxa, comissão) consideram apenas processos com REAJUIZAMENTO desativado.
                </InfoBox>
            </DocSection>

            <DocSection
                id="comissionamento"
                title="Comissionamento"
                subtitle="Como a comissão dos funcionários é calculada"
            >
                <InfoBox>
                    A comissão no Peticionamento incide apenas sobre as confecções manuais (PET_AUTO = FALSE). Petições
                    automáticas não geram comissão. O cálculo é feito por funcionário, separando matérias{' '}
                    <strong>ESPECIFICA</strong> (e as da área de atuação <strong>ADMINISTRATIVO</strong>) das demais
                    (chamadas de <strong>Massa</strong>).
                </InfoBox>

                <div className="stack">
                    <DocCard title="Passo 1 — Calcular a taxa de resolução por funcionário">
                        <p>Para cada funcionário, calcula-se a taxa de petições confeccionadas:</p>
                        <WatchBox>
                            <Code>Taxa = (Peticionados do funcionário ÷ Total do funcionário) × 100</Code>
                        </WatchBox>
                    </DocCard>

                    <DocCard title="Passo 2A — Comissão por processos de Massa (qualquer matéria exceto ESPECIFICA e área ADMINISTRATIVO)">
                        <div>
                            <div className="card tblwrap">
                                <table className="tbl">
                                    <thead>
                                        <tr>
                                            <th>Taxa de resolução</th>
                                            <th>Valor por processo manual (Massa)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>98% ou mais</td>
                                            <td>R$ 3,00</td>
                                        </tr>
                                        <tr>
                                            <td>De 85% a 97%</td>
                                            <td>R$ 1,50</td>
                                        </tr>
                                        <tr>
                                            <td>De 70% a 84%</td>
                                            <td>R$ 0,50</td>
                                        </tr>
                                        <tr>
                                            <td>Abaixo de 70%</td>
                                            <td>R$ 0,00 (sem comissão)</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </DocCard>

                    <DocCard title="Passo 2B — Comissão por processos ESPECIFICA">
                        <p>
                            Processos cuja matéria (normalizada) é exatamente <Code>ESPECIFICA</Code>, ou cuja rubrica
                            pertence à área de atuação <Code>ADMINISTRATIVO</Code> (ex.: progressões e gratificações de
                            servidor público), usam a mesma tabela de comissão própria, com valores maiores — igual em
                            todos os escritórios (NG, LA, RJ):
                        </p>

                        <div>
                            <div className="card tblwrap">
                                <table className="tbl">
                                    <thead>
                                        <tr>
                                            <th>Taxa de resolução</th>
                                            <th>Valor por processo manual (ESPECIFICA)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>95% ou mais</td>
                                            <td>R$ 20,00</td>
                                        </tr>
                                        <tr>
                                            <td>De 85% a 94%</td>
                                            <td>R$ 13,00</td>
                                        </tr>
                                        <tr>
                                            <td>De 50% a 84%</td>
                                            <td>R$ 7,00</td>
                                        </tr>
                                        <tr>
                                            <td>Abaixo de 50%</td>
                                            <td>R$ 0,00 (sem comissão)</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </DocCard>

                    <DocCard title="Passo 3 — Comissão total do funcionário">
                        <WatchBox>
                            <Code>Subtotal Massa = Valor Massa × Qtd processos Massa manuais</Code>
                            <Code>Subtotal ESPECIFICA = Valor ESPECIFICA × Qtd processos ESPECIFICA manuais</Code>
                            <Code>Comissão total = Subtotal Massa + Subtotal ESPECIFICA</Code>
                        </WatchBox>
                        <p>
                            Exemplo: funcionário com taxa 90%, 80 processos Massa e 5 ESPECIFICA → (80 × R$1,50) + (5 ×
                            R$13,00) = R$120,00 + R$65,00 = R$185,00
                        </p>
                    </DocCard>
                </div>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como os dados podem ser segmentados">
                <DocGrid>
                    {[
                        {
                            label: 'Período',
                            desc: 'Filtra pela DATA_CONFECCAO (não por SAIDA). Todos os indicadores do período obedecem esse filtro. Os represados não são afetados.',
                        },
                        {
                            label: 'Matéria',
                            desc: "Filtra por tipo de causa. A matéria é normalizada para a parte antes do ' - '. ESPECIFICA é tratada separadamente no comissionamento.",
                        },
                        {
                            label: 'Funcionário',
                            desc: 'Filtra pelos processos atribuídos a um ou mais funcionários específicos.',
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
