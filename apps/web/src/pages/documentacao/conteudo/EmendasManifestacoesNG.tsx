import {
    DiffBox,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/EmendasManifestacoes_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'atividades', label: 'Classificação de atividades' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'uf', label: 'Filtro de UF' },
    { id: 'filtros', label: 'Demais filtros' },
]

export function EmendasManifestacoesNGDoc() {
    return (
        <DocPage
            title="Emendas e Manifestações — NG"
            tags={['NG']}
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número, gráfico e regra de comissão do dashboard de Emendas e Manifestações
                    do NG — as tarefas do setor <strong>MANIFESTAÇÃO</strong>, réplica mais enxuta do dashboard
                    equivalente da LA.
                </>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="O setor MANIFESTAÇÃO e a diferença para a LA"
            >
                <InfoBox>
                    Cada linha é uma tarefa (agendamento) do setor "MANIFESTAÇÃO" do NG. O responsável exibido é sempre
                    quem
                    <strong> encerrou</strong> a tarefa; se ainda estiver aberta, é quem está <strong>atribuído</strong>{' '}
                    a ela no momento.
                </InfoBox>
                <DiffBox>
                    O setor do NG tem apenas <strong>5 atividades</strong> — bem menos que o setor "INTERMEDIÁRIAS" da
                    LA (18 atividades). Existe também um setor separado "EMENDA - SOLICITAR DOCS COM CLIENTE" (etapa
                    preparatória, equivalente a "Avaliar Manifestação" na LA), que foi deliberadamente deixado fora
                    deste dashboard.
                </DiffBox>
                <DocCard title="Duas visões da mesma tela">
                    <DocGrid>
                        <DocCard title="Concluídas (padrão)">
                            <p>
                                Total/Em andamento usam a data de <strong>criação</strong>; Concluídas usa a data de
                                <strong> encerramento</strong>.
                            </p>
                        </DocCard>
                        <DocCard title="Por prazo">
                            <p>
                                Todos os cartões passam a olhar para o <strong>prazo</strong> da tarefa — é também o
                                eixo usado pelo comissionamento.
                            </p>
                        </DocCard>
                    </DocGrid>
                </DocCard>
            </DocSection>

            <DocSection
                id="indicadores"
                title="Indicadores do período"
                subtitle="Os cartões de resumo no topo do dashboard"
            >
                <DocGrid>
                    <MetricCard
                        icon="fileText"
                        name="Total"
                        what="Volume de tarefas ativas do setor abertas no período."
                        counts='Tarefas que não estão em "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado" nem "Concluído".'
                        calc="Contagem das tarefas ativas cuja data de criação cai dentro do período selecionado."
                        interpret="Mostra o volume de entrada de trabalho no setor durante o período."
                    />
                    <MetricCard
                        icon="clock"
                        name="Em andamento"
                        what="Das tarefas do Total, quantas estão em algum status ativo."
                        counts='Qualquer status ativo: "Recebido", "Visualizado", "Iniciado", "Reaberto" ou "Encaminhado".'
                        calc="Como o Total já exclui as encerradas/canceladas, este número normalmente coincide com o Total."
                        interpret="Não é um alerta de atraso — é só a confirmação de que a tarefa segue ativa."
                    />
                    <MetricCard
                        icon="alert"
                        name="Vencidas"
                        what="Tarefas ativas cujo prazo já passou, hoje."
                        counts="Tarefas ativas com prazo anterior à data de hoje, independente de quando foram criadas."
                        calc="Comparação direta com a data de hoje — não depende do período filtrado."
                        interpret="Indicador de urgência: qualquer valor acima de zero merece atenção."
                    />
                    <MetricCard
                        icon="clock"
                        name="Vencem hoje"
                        what="Tarefas ativas cujo prazo é exatamente hoje."
                        counts="Tarefas ativas com prazo igual à data de hoje."
                        calc="Mesma lógica de Vencidas, comparando prazo = hoje."
                        interpret="Ajuda a priorizar o que precisa ser resolvido ainda no dia."
                    />
                    <MetricCard
                        icon="check"
                        name="Concluídas"
                        what="Tarefas encerradas no período — contagem separada do Total."
                        counts='Status "Encerrado Cumprido" ou "Encerrado Não Cumprido" com data de encerramento no período.'
                        calc="Contagem direta dos registros encerrados no período."
                        interpret="Mede a produção efetiva de fechamento do setor."
                    />
                </DocGrid>
                <p>
                    Os cartões de "Manifestações no período" e "Dilações no período" mostram também a variação
                    percentual em relação ao período anterior de mesma duração.
                </p>
            </DocSection>

            <DocSection
                id="atividades"
                title="Classificação de atividades"
                subtitle="Quais atividades geram peça remunerada"
            >
                <DocCard>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Categoria</th>
                                        <th>Atividades</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Manifestação</td>
                                        <td>
                                            Todas as demais atividades do setor — ex.: Protocolar Emenda · Protocolar
                                            Emenda Fatal · Manifestação Simples · Manifestação Específica · Manifestação
                                            - Provas · Manifestação → Conexão/Aditamento · Manifestação → Alegações
                                            Finais · Elaborar Manifestação - Pedido de Providências. Atividade nova
                                            cadastrada no setor já entra automaticamente.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Dilação</td>
                                        <td>Elaborar Dilação</td>
                                    </tr>
                                    <tr>
                                        <td>Não comissionável</td>
                                        <td>Análise de Manifestação (e o nome antigo, Elaborar Manifestação)</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>

                <DiffBox>
                    Desde 02/10/2026 a regra é por <strong>exclusão</strong>: a única atividade que não gera comissão é
                    "Análise de Manifestação" (nome antigo: "Elaborar Manifestação"); todas as outras do setor
                    comissionam — Elaborar Dilação como Dilação, o resto como Manifestação. Antes era uma lista fechada,
                    e atividades novas do catálogo (Manifestação Simples, Provas, etc.) ficavam de fora sem ninguém
                    perceber.
                </DiffBox>
            </DocSection>

            <DocSection id="comissao" title="Comissionamento" subtitle="Valor fixo por peça, sem faixa">
                <InfoBox>
                    Diferente da LA, o NG <strong>não usa faixas</strong> de agenda cumprida. Toda peça "Encerrado
                    Cumprido" com prazo no período vale o mesmo valor, sem gatilho mínimo. O percentual de agenda
                    cumprida continua calculado e exibido, mas é só informativo — não muda o valor pago.
                </InfoBox>

                <DocCard>
                    <div>
                        <h3 className="doc-h3">Valores fixos</h3>
                    </div>
                    <div>
                        <div className="card tblwrap">
                            <table className="tbl">
                                <thead>
                                    <tr>
                                        <th>Peça</th>
                                        <th>Valor</th>
                                        <th>Gatilho de agenda</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Manifestação</td>
                                        <td>R$ 1,00</td>
                                        <td rowSpan={2}>Nenhum — sempre elegível</td>
                                    </tr>
                                    <tr>
                                        <td>Dilação</td>
                                        <td>R$ 0,50</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </DocCard>
                <p>
                    Mesma regra de peça paga da LA: só conta como peça quem foi encerrado como "Encerrado Cumprido" com
                    prazo no período. Validado com dados reais: 250 manifestações e 24 dilações em julho/2026.
                </p>
            </DocSection>

            <DocSection id="uf" title="Filtro de UF" subtitle="Recurso exclusivo deste dashboard">
                <InfoBox>
                    UF não é um campo nativo da base de agendamentos — vem de uma consulta adicional ao cadastro do
                    processo. É por isso que o filtro de UF existe só aqui, e não nos outros três dashboards da família
                    (a LA não pediu esse filtro).
                </InfoBox>
                <p>
                    A tabela de comissão por funcionário também é quebrada por UF — cada funcionário mostra quantas
                    manifestações e dilações produziu em cada estado. Distribuição real observada (jul/2026): AM
                    concentra a maior parte do volume, com PB e PA bem menores.
                </p>
            </DocSection>

            <DocSection id="filtros" title="Demais filtros" subtitle="Como personalizar a lista de tarefas">
                <DocGrid>
                    {[
                        { name: 'Funcionário', desc: 'Restringe às tarefas de um ou mais funcionários.' },
                        { name: 'Atividade', desc: 'Filtra por uma ou mais das atividades do setor.' },
                        { name: 'Status', desc: 'Filtra pelo status bruto da tarefa.' },
                        {
                            name: 'Situação',
                            desc: 'Filtra pelas categorias calculadas: em andamento, vencidas, vencem hoje, concluídas.',
                        },
                    ].map((f) => (
                        <DocCard>
                            <p>{f.name}</p>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
                <p>A tabela de tarefas também mostra o número do processo (formato CNJ) quando disponível.</p>
            </DocSection>
        </DocPage>
    )
}
