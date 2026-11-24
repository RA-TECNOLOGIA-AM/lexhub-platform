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

// Guia trazido da v1: LexHub/src/pages/documentacao/Peticionamento_LA.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'diferencas', label: 'Diferenças vs NG' },
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'represados', label: 'Processos represados' },
    { id: 'manual-automatico', label: 'Manual vs Automático' },
    { id: 'retorno-protocolo', label: 'Retorno do Protocolo' },
    { id: 'rankings', label: 'Rankings e agrupamentos' },
    { id: 'reajuizamento', label: 'Reajuizamento' },
    { id: 'comissionamento', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros disponíveis' },
]

export function PeticionamentoLADoc() {
    return (
        <DocPage
            title="Peticionamento — LA"
            tags={['LA']}
            toc={TOC}
            intro={
                <>
                    O Peticionamento LA usa o termo "confecção" para as petições produzidas. Os status são diferentes do
                    NG, o filtro de data usa SAIDA (e não DATA_CONFECCAO), e há uma métrica exclusiva de retorno do
                    Protocolo.
                </>
            }
        >
            <DocSection
                id="diferencas"
                title="Diferenças em relação ao NG e LARJ"
                subtitle="O que muda na lógica da LA"
            >
                <DiffBox>
                    <h3 className="doc-h3">As principais diferenças do Peticionamento LA são:</h3>
                    <ul>
                        <li>
                            • Terminologia: a LA usa <strong>"confeccionados"</strong> onde o NG usa "peticionados"
                        </li>
                        <li>
                            • Status represados LA: <strong>PETICIONAMENTO</strong> (NG: NÃO INICIADO, RETORNO
                            PENDÊNCIA)
                        </li>
                        <li>
                            • Status confeccionados LA: <strong>PROTOCOLO ou CONCLUIDO</strong> (NG: PROTOCOLAR)
                        </li>
                        <li>
                            • Filtro de data LA: <strong>SAIDA</strong> (NG usa DATA_CONFECCAO — diferença importante!)
                        </li>
                        <li>
                            • LA tem métrica exclusiva de <strong>retorno do Protocolo</strong> (processos que voltaram
                            do Protocolo para Peticionamento)
                        </li>
                        <li>• Comissão: mesmas faixas e valores que o NG (Massa e ESPECIFICA)</li>
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
                                    <td>Processo confeccionado</td>
                                    <td>STATUS = PROTOCOLAR</td>
                                    <td>STATUS = PROTOCOLO ou CONCLUIDO</td>
                                </tr>
                                <tr>
                                    <td>Processos represados</td>
                                    <td>NÃO INICIADO, RETORNO PENDÊNCIA</td>
                                    <td>STATUS = PETICIONAMENTO</td>
                                </tr>
                                <tr>
                                    <td>Filtro de data</td>
                                    <td>DATA_CONFECCAO</td>
                                    <td>SAIDA</td>
                                </tr>
                                <tr>
                                    <td>Manual vs Auto</td>
                                    <td>Campo PET_AUTO (igual)</td>
                                    <td>Campo PET_AUTO (igual)</td>
                                </tr>
                                <tr>
                                    <td>Comissão (tabelas)</td>
                                    <td>Massa: R$0,50/1,50/3,00 | ESPECIFICA: R$7/13/20</td>
                                    <td>Iguais ao NG</td>
                                </tr>
                                <tr>
                                    <td>Retorno do Protocolo</td>
                                    <td>Não tem</td>
                                    <td>Métrica exclusiva</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </DocCard>
            </DocSection>

            <DocSection
                id="como-funciona"
                title="Como funciona o setor"
                subtitle="Ciclo de vida de um processo no Peticionamento LA"
            >
                <InfoBox>
                    Na LA, o processo que ainda não foi confeccionado fica com STATUS "PETICIONAMENTO". Após ser
                    confeccionado (manual ou automaticamente), recebe STATUS "PROTOCOLO" ou "CONCLUIDO" e uma data de
                    SAIDA é registrada — essa SAIDA é o que delimita o período no dashboard.
                </InfoBox>

                <DocCard title="Fluxo do processo">
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                        {[
                            { label: 'PETICIONAMENTO', color: 'bg-slate-500/10 text-slate-500' },
                            { label: '→', color: '' },
                            {
                                label: 'PROTOCOLO / CONCLUIDO',
                                color: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
                            },
                        ].map((step, i) =>
                            step.color ? <span key={i}>{step.label}</span> : <strong key={i}>{step.label}</strong>,
                        )}
                    </div>
                    <p>
                        STATUS <strong>PETICIONAMENTO</strong> = processo aguardando confecção (represado). Ao ser
                        confeccionado, recebe <strong>PROTOCOLO</strong> ou <strong>CONCLUIDO</strong> com a data de
                        SAIDA.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores do período"
                subtitle="O que cada número no topo do dashboard representa"
            >
                <InfoBox>
                    Na LA, o filtro de período usa a coluna <strong>SAIDA</strong> (diferente do NG que usa
                    DATA_CONFECCAO). Todos os indicadores abaixo filtram pela SAIDA dentro do período selecionado.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Confeccionados"
                        what="Quantidade de petições confeccionadas no período."
                        counts="Processos com STATUS = 'PROTOCOLO' ou 'CONCLUIDO' e REAJUIZAMENTO desativado, cuja SAIDA está dentro do período."
                        calc="Contagem direta dos registros que atendem a esses critérios."
                        interpret="Volume de confecções do setor. Inclui manuais e automáticas."
                        caveat="Na LA o filtro é por SAIDA. No NG é por DATA_CONFECCAO."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Taxa de Resolvidos"
                        what="Percentual de processos confeccionados em relação ao total (confeccionados + não confeccionados)."
                        counts="Numerador: PROTOCOLO/CONCLUIDO. Denominador: confeccionados + STATUS PETICIONAMENTO."
                        calc="(Qtd confeccionados ÷ (Qtd confeccionados + Qtd PETICIONAMENTO)) × 100"
                        interpret="Taxa de resolução do setor. Diretamente usada no cálculo de comissão."
                    />
                    <MetricCard
                        icon="users"
                        name="Confeccionados Manualmente"
                        what="Petições produzidas por um funcionário (não pelo sistema automático)."
                        counts="STATUS PROTOCOLO/CONCLUIDO + PET_AUTO = FALSE."
                        calc="Contagem dos confeccionados com PET_AUTO desativado."
                        interpret="Base para o cálculo de comissão. Apenas confecções manuais geram comissão."
                    />
                    <MetricCard
                        icon="trendingUp"
                        name="Confeccionados Automaticamente"
                        what="Petições geradas automaticamente pelo sistema."
                        counts="STATUS PROTOCOLO/CONCLUIDO + PET_AUTO = TRUE."
                        calc="Contagem dos confeccionados com PET_AUTO ativado."
                        interpret="Volume automatizado. Não gera comissão para funcionários."
                    />
                </DocGrid>
            </DocSection>

            <DocSection id="represados" title="Processos represados" subtitle="Fila de trabalho do setor">
                <DiffBox>
                    <strong>Diferença importante:</strong> na LA o status de represado é <strong>PETICIONAMENTO</strong>{' '}
                    (único status). No NG são dois: NÃO INICIADO e RETORNO PENDÊNCIA. Os represados mostram o acumulado
                    total, sem filtro de data.
                </DiffBox>
                <MetricCard
                    icon="xCircle"
                    name="Não Confeccionados (PETICIONAMENTO)"
                    what="Processos que estão no setor aguardando ser confeccionados."
                    counts="STATUS = 'PETICIONAMENTO' com REAJUIZAMENTO desativado. Sem filtro de data — mostra o total acumulado."
                    calc="Contagem simples de todos os processos nesse status."
                    interpret="Indica o tamanho da fila. Acompanhar em relação ao volume de confeccionados para entender se o setor está progredindo."
                />
            </DocSection>

            <DocSection id="manual-automatico" title="Manual vs Automático" subtitle="Determinado pelo campo PET_AUTO">
                <InfoBox>
                    Igual ao NG: a distinção entre manual e automático é feita pelo campo <strong>PET_AUTO</strong>.
                    Apenas confecções manuais (PET_AUTO = FALSE) entram no cálculo de comissão.
                </InfoBox>
                <DocGrid>
                    <DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                            <h3 className="doc-h3">Confeccionado Automaticamente</h3>
                        </div>
                        <p>
                            STATUS PROTOCOLO/CONCLUIDO + <strong>PET_AUTO = TRUE</strong>. Gerado pelo sistema. Não gera
                            comissão.
                        </p>
                    </DocCard>
                    <DocCard>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                            <h3 className="doc-h3">Confeccionado Manualmente</h3>
                        </div>
                        <p>
                            STATUS PROTOCOLO/CONCLUIDO + <strong>PET_AUTO = FALSE</strong>. Feito por um funcionário.{' '}
                            <strong>Entra no cálculo de comissão.</strong>
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="retorno-protocolo" title="Retorno do Protocolo" subtitle="Métrica exclusiva da LA">
                <DiffBox>
                    <strong>Métrica exclusiva da LA:</strong> o NG não acompanha esse indicador.
                </DiffBox>
                <InfoBox>
                    Na LA, o sistema registra quando um processo entra no setor de Protocolo e quando ele volta para o
                    Peticionamento. Isso permite identificar processos que foram enviados ao Protocolo mas retornaram
                    por algum motivo.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        icon="check"
                        name="Entrada em Protocolo"
                        what="Quantidade de processos que chegaram ao setor de Protocolo vindos do Peticionamento."
                        counts="Processos (únicos) com registro de entrada no Protocolo no log de fases."
                        calc="Contagem de processos únicos com DATA_ENTRADA_PROTOCOLO preenchida."
                        interpret="Indica quantos processos já avançaram para a etapa seguinte."
                    />
                    <MetricCard
                        icon="refresh"
                        name="Retorno do Protocolo"
                        what="Processos que foram ao Protocolo e voltaram para o Peticionamento."
                        counts="Processos em que a última entrada no Peticionamento é posterior à entrada no Protocolo."
                        calc={<>Taxa de retorno = (Qtd retornos ÷ Qtd com entrada em Protocolo) × 100</>}
                        interpret="Uma taxa alta de retorno pode indicar problemas na qualidade das petições confeccionadas, gerando retrabalho no Protocolo."
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
                            Confeccionados e não confeccionados agrupados por FUNCIONARIO. Nome normalizado para as duas
                            primeiras palavras em maiúsculo.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por Matéria</p>
                        <p>
                            Agrupado pela matéria normalizada (parte antes do " - "). ESPECIFICA é tratada separadamente
                            no comissionamento.
                        </p>
                    </DocCard>
                    <DocCard>
                        <p> Por UF</p>
                        <p>
                            A LA permite filtrar e agrupar por estado (UF), permitindo ver a distribuição geográfica das
                            confecções.
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
                    Igual ao NG: processos com REAJUIZAMENTO ativado são contabilizados separadamente e não entram nos
                    indicadores principais.
                </InfoBox>
            </DocSection>

            <DocSection
                id="comissionamento"
                title="Comissionamento"
                subtitle="Como a comissão é calculada — mesmas tabelas do NG"
            >
                <InfoBox>
                    O modelo de comissão da LA é idêntico ao NG: incide apenas sobre confecções manuais (PET_AUTO =
                    FALSE), com tabelas separadas para matérias de Massa e ESPECIFICA. A taxa de resolução é calculada
                    individualmente por funcionário. Peças cuja rubrica pertence à área de atuação{' '}
                    <strong>ADMINISTRATIVO</strong> (ex.: ESPECIFICA ADM, progressões e gratificações de servidor
                    público) usam a mesma tabela de comissão da ESPECIFICA — em todos os escritórios.
                </InfoBox>

                <div className="stack">
                    <DocCard title="Comissão por Massa (qualquer matéria exceto ESPECIFICA e área ADMINISTRATIVO)">
                        <div>
                            <div className="card tblwrap">
                                <table className="tbl">
                                    <thead>
                                        <tr>
                                            <th>Taxa de resolução</th>
                                            <th>Valor por confecção manual (Massa)</th>
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

                    <DocCard title="Comissão por ESPECIFICA (e rubricas da área ADMINISTRATIVO)">
                        <div>
                            <div className="card tblwrap">
                                <table className="tbl">
                                    <thead>
                                        <tr>
                                            <th>Taxa de resolução</th>
                                            <th>Valor por confecção manual (ESPECIFICA)</th>
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

                    <DocCard title="Cálculo total">
                        <DocCard>
                            <Code>Taxa por funcionário = (Confeccionados ÷ Total) × 100</Code>
                            <Code>Subtotal Massa = Valor Massa × Qtd confecções Massa manuais</Code>
                            <Code>Subtotal ESPECIFICA = Valor ESPECIFICA × Qtd confecções ESPECIFICA manuais</Code>
                            <Code>Comissão total = Subtotal Massa + Subtotal ESPECIFICA</Code>
                        </DocCard>
                        <p>
                            Exemplo: taxa 88%, 60 Massa + 3 ESPECIFICA → (60 × R$1,50) + (3 × R$13,00) = R$90 + R$39 =
                            R$129,00
                        </p>
                    </DocCard>
                </div>
            </DocSection>

            <DocSection id="filtros" title="Filtros disponíveis" subtitle="Como os dados podem ser segmentados">
                <DocGrid>
                    {[
                        {
                            label: 'Período',
                            desc: 'Filtra pela coluna SAIDA (diferente do NG que usa DATA_CONFECCAO). Os indicadores do período obedecem esse filtro. Os represados não são afetados.',
                        },
                        {
                            label: 'Matéria',
                            desc: "Filtra por tipo de causa. A matéria é normalizada para a parte antes do ' - '. ESPECIFICA é tratada separadamente no comissionamento.",
                        },
                        {
                            label: 'Funcionário',
                            desc: 'Filtra pelos processos atribuídos a um ou mais funcionários específicos.',
                        },
                        {
                            label: 'UF (Estado)',
                            desc: 'Filtro exclusivo da LA. Permite ver os dados de um estado específico.',
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
