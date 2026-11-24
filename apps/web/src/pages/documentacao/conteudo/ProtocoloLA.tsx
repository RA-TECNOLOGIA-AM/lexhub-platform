import {
    Code,
    DiffBox,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/Protocolo_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'diferencas', label: 'Diferenças vs NG' },
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

export function ProtocoloLADoc() {
    return (
        <DocPage
            title="Protocolo — LA"
            tags={['LA']}
            toc={TOC}
            intro={
                <>
                    O Protocolo LA tem lógica semelhante ao NG, mas com nomes de status diferentes e um modelo de
                    comissionamento escalonado em vez de valor fixo.
                </>
            }
        >
            <DocSection
                id="diferencas"
                title="Diferenças em relação ao NG e LARJ"
                subtitle="O que muda na lógica da LA"
            >
                <DiffBox>
                    <h3 className="doc-h3">A LA usa nomes de status diferentes e um comissionamento escalonado:</h3>
                    <ul>
                        <li>
                            • Status "protocolado" na LA: <strong>CONCLUIDO</strong> (no NG: DISTRIBUÍDO ou PROTOCOLADO)
                        </li>
                        <li>
                            • Status "represado" na LA: <strong>PROTOCOLO</strong> (no NG: NÃO INICIADO, NÃO
                            PROTOCOLADO, PRÉ-PROTOCOLADO)
                        </li>
                        <li>
                            • Comissão LA: escalonada pela taxa de resolução (R$0,50 / R$1,50 / R$3,00 por processo)
                        </li>
                        <li>• Comissão NG: R$ 1,00 fixo por processo + cálculo com Fator Multiplicador por estado</li>
                    </ul>
                </DiffBox>

                <DocCard>
                    <div className="card tblwrap">
                        <table className="tbl">
                            <thead>
                                <tr>
                                    <th>Conceito</th>
                                    <th>NG / LARJ</th>
                                    <th>LA</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Processo protocolado</td>
                                    <td>DISTRIBUÍDO ou PROTOCOLADO</td>
                                    <td>CONCLUIDO</td>
                                </tr>
                                <tr>
                                    <td>Processos represados</td>
                                    <td>NÃO INICIADO, NÃO PROTOCOLADO, PRÉ-PROTOCOLADO</td>
                                    <td>PROTOCOLO</td>
                                </tr>
                                <tr>
                                    <td>Filtro de data</td>
                                    <td>SAIDA</td>
                                    <td>SAIDA (igual)</td>
                                </tr>
                                <tr>
                                    <td>Comissão por processo</td>
                                    <td>R$ 1,00 fixo + FM por estado</td>
                                    <td>Escalonada (R$0,50 / R$1,50 / R$3,00)</td>
                                </tr>
                                <tr>
                                    <td>Meta anual 2026</td>
                                    <td>R$ 300.000.000</td>
                                    <td>R$ 300.000.000 (igual)</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="como-funciona"
                title="Como funciona o setor"
                subtitle="Ciclo de vida de um processo no Protocolo LA"
            >
                <InfoBox>
                    Na LA, os processos chegam ao Protocolo após passarem pelo Org Doc. A diferença está no nome dos
                    status: o processo represado fica com STATUS "PROTOCOLO", e ao ser concluído recebe STATUS
                    "CONCLUIDO" com data de SAIDA registrada. Processos de REAJUIZAMENTO são tratados separadamente.
                </InfoBox>

                <DocCard title="Fluxo do processo">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        {[
                            { label: 'PROTOCOLO', color: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400' },
                            { label: '→', color: '' },
                            { label: 'CONCLUIDO', color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' },
                        ].map((step, i) =>
                            step.color ? <span key={i}>{step.label}</span> : <strong key={i}>{step.label}</strong>,
                        )}
                    </div>
                    <p>
                        O status <strong>PROTOCOLO</strong> representa o processo aguardando ser trabalhado (represado).
                        Ao ser protocolado, recebe o status <strong>CONCLUIDO</strong> e a data de SAIDA é registrada.
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
                        name="Protocolados (CONCLUIDO)"
                        what="Quantidade de processos efetivamente concluídos no período."
                        counts="Processos com STATUS = 'CONCLUIDO' e REAJUIZAMENTO desativado, cuja data de SAIDA está dentro do período."
                        calc="Contagem direta dos registros que atendem a esses critérios."
                        interpret="Equivalent ao 'Protocolados' do NG. Quanto maior, melhor."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Taxa de Protocolados"
                        what="Percentual de processos que chegaram ao setor e foram concluídos."
                        counts="Numerador: processos CONCLUIDO com SAIDA no período. Denominador: processos com ENTRADA no período."
                        calc="(Qtd CONCLUIDO com SAIDA no período ÷ Qtd com ENTRADA no período) × 100"
                        interpret="Taxa de resolução do setor. Diretamente relacionada ao cálculo de comissão."
                    />
                    <MetricCard
                        icon="dollar"
                        name="Valor de Causa Protocolado"
                        what="Soma total do valor das causas dos processos concluídos no período."
                        counts="Processos CONCLUIDO com REAJUIZAMENTO desativado. Para ANP usa DANO_MORAL; demais usam VALOR_DA_CAUSA."
                        calc="Soma dos valores de causa de todos os processos CONCLUIDO."
                        interpret="Acompanha a meta anual de R$ 300 milhões."
                    />
                    <MetricCard
                        icon="barChart"
                        name="Ticket Médio"
                        what="Valor médio de causa por processo concluído."
                        counts="Mesmos processos do Valor de Causa Protocolado."
                        calc="Valor total de causa ÷ Quantidade de processos CONCLUIDO"
                        interpret="Indica o porte médio dos processos atendidos pelo setor."
                    />
                    <MetricCard
                        icon="target"
                        name="Processos Protocolados em 2026"
                        what="Acumulado de valor de causa em 2026, comparado à meta anual."
                        counts="Todos os processos CONCLUIDO com SAIDA em 2026, independente do filtro de período."
                        calc={
                            <>
                                Soma do valor de causa dos processos CONCLUIDO com SAIDA em 2026.
                                <br />
                                Meta: <strong>R$ 300.000.000</strong>
                            </>
                        }
                        interpret="Mostra o progresso anual. Não é afetado pelo filtro de datas."
                        caveat="Este indicador ignora o filtro de período e exibe sempre o acumulado de 2026."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="represados" title="Processos represados" subtitle="Fila de trabalho do setor">
                <DiffBox>
                    <strong>Diferença importante:</strong> na LA existe apenas um status de represado —{' '}
                    <strong>PROTOCOLO</strong>. No NG há três (NÃO INICIADO, NÃO PROTOCOLADO, PRÉ-PROTOCOLADO). Os
                    represados mostram o acumulado total, sem filtro de data.
                </DiffBox>
                <MetricCard
                    icon="xCircle"
                    name="Processos Represados (PROTOCOLO)"
                    what="Processos que estão no setor aguardando ser trabalhados."
                    counts="STATUS = 'PROTOCOLO' com REAJUIZAMENTO desativado. Sem filtro de data — mostra o total acumulado."
                    calc="Contagem simples de todos os processos nesse status."
                    interpret="Indica o tamanho da fila. Um volume alto sem crescimento de protocolados pode indicar gargalo."
                />
            </DocSection>

            <DocSection id="tempo" title="Tempo de produção" subtitle="Métricas de prazo">
                <DocGrid>
                    <MetricCard
                        icon="clock"
                        name="Tempo no Setor"
                        what="Média de dias que um processo fica no Protocolo até ser concluído."
                        counts="Processos CONCLUIDO no período."
                        calc="SAIDA − ENTRADA (em dias), média de todos os processos."
                        interpret="Quanto menor, melhor. Agilidade interna do setor."
                    />
                    <MetricCard
                        icon="clock"
                        name="Tempo da Contratação ao Protocolo"
                        what="Tempo total desde a contratação do cliente até o processo ser concluído."
                        counts="Processos CONCLUIDO com DATA_CONTRATACAO preenchida."
                        calc="SAIDA − DATA_CONTRATACAO (em dias)."
                        interpret="Ciclo completo do cliente. Útil para acompanhar SLAs."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="valor-causa" title="Valor de causa" subtitle="Como o valor das causas é calculado">
                <InfoBox>
                    Igual ao NG: para matéria <strong>ANP</strong> usa-se o campo <strong>DANO_MORAL</strong>; para as
                    demais matérias usa-se <strong>VALOR_DA_CAUSA</strong>. Valores nulos ou zero são desconsiderados. A
                    matéria é normalizada para a parte antes do " - ".
                </InfoBox>
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
                            Protocolados (CONCLUIDO) e represados (PROTOCOLO) agrupados por FUNCIONARIO. Normalizado
                            para as duas primeiras palavras.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por Matéria</p>
                        <p>Agrupado pela matéria normalizada (parte antes do " - ").</p>
                    </DocCard>
                    <DocCard>
                        <p> Por Sistema</p>
                        <p>Agrupado pelo campo SISTEMA (sistema judicial onde o processo foi protocolado).</p>
                    </DocCard>
                    <DocCard>
                        <p> Por Atendente</p>
                        <p>Agrupado pelo responsável pelo atendimento ao cliente.</p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="reajuizamento"
                title="Reajuizamento"
                subtitle="Como processos de reajuizamento são tratados"
            >
                <InfoBox>
                    Igual ao NG: processos com REAJUIZAMENTO ativado são contabilizados separadamente e não entram nos
                    indicadores principais. Eles aparecem em seção própria no dashboard.
                </InfoBox>
            </DocSection>

            <DocSection id="comissionamento" title="Comissionamento" subtitle="Como a comissão é calculada na LA">
                <DiffBox>
                    <strong>Diferença importante:</strong> na LA a comissão é escalonada pela taxa de resolução do
                    funcionário. No NG é um valor fixo de R$ 1,00 por processo.
                </DiffBox>

                <DocCard title="Comissão por processo protocolado (CONCLUIDO) — escalonada pela taxa">
                    <p>
                        A taxa de resolução de cada funcionário é calculada individualmente. Com base nessa taxa,
                        aplica-se um valor unitário por processo protocolado:
                    </p>

                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Taxa de resolução do funcionário</th>
                                        <th>Valor por processo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>97% ou mais</td>
                                        <td>R$ 3,00 por processo</td>
                                    </tr>
                                    <tr>
                                        <td>De 85% a 96%</td>
                                        <td>R$ 1,50 por processo</td>
                                    </tr>
                                    <tr>
                                        <td>Até 84%</td>
                                        <td>R$ 0,50 por processo</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <DocCard>
                        <Code>Comissão = Valor unitário × Qtd de processos CONCLUIDO do funcionário</Code>
                    </DocCard>
                    <p>Exemplo: funcionário com taxa de 90% e 100 processos concluídos → R$ 1,50 × 100 = R$ 150,00</p>
                </DocCard>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como os dados podem ser segmentados">
                <DocGrid>
                    {[
                        {
                            label: 'Período',
                            desc: 'Filtra pela data de SAIDA. Os indicadores do período obedecem esse filtro. Os represados e o acumulado de 2026 não são afetados.',
                        },
                        {
                            label: 'Matéria',
                            desc: "Filtra por tipo de causa. A matéria é normalizada para a parte antes do ' - '.",
                        },
                        {
                            label: 'Funcionário',
                            desc: 'Filtra pelos processos atribuídos a um ou mais funcionários específicos.',
                        },
                        {
                            label: 'Sistema',
                            desc: 'Filtra pelo sistema judicial onde o processo foi concluído (campo SISTEMA).',
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
