import {
    DocCallout,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    DocTable,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia trazido da v1: LexHub/src/pages/documentacao/PendenciasIntermediarias_NG.tsx (convertido para as peças da V2).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'dilacao', label: 'Taxa de Dilação' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'graficos', label: 'Gráficos e histórico' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    {
        name: 'Funcionários',
        badge: 'Pessoa',
        desc: 'Restringe às tarefas de um ou mais funcionários (quem encerrou, ou quem está atribuído se ainda aberta). Também é aplicado clicando em "Demandas por funcionário" ou na média diária.',
    },
    {
        name: 'Atividade',
        badge: 'Clique no gráfico',
        desc: 'Filtra por uma ou mais atividades da base (as do setor PENDÊNCIA e "EMENDA - SOLICITAR DOCS COM CLIENTE"). É aplicado clicando no gráfico "Por atividade" e aparece nas etiquetas de filtro.',
    },
    {
        name: 'Situação do processo',
        badge: 'Processo',
        desc: 'Ativo, Suspenso / Sobrestado ou Arquivado — é a situação do processo, não da tarefa. Sem escolha, entram todas.',
    },
]

export function PendenciasIntermediariasNGDoc() {
    return (
        <DocPage
            title="Pendências Intermediárias — NG"
            tags={['NG']}
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Pendências Intermediárias — as tarefas do
                    setor <strong>PENDÊNCIA</strong> da unidade NG, responsável por pedir documentos ao cliente e
                    decidir se um processo segue ou entra em dilação de prazo. O RJ usa exatamente as mesmas regras do
                    NG.
                </>
            }
            header={
                <DocCallout caps title="Cada linha é uma tarefa, não um processo" badge='Setor "PENDÊNCIA"'>
                    <p>
                        Cada linha do dashboard é um agendamento (uma tarefa) do setor "PENDÊNCIA" da NG — não o
                        processo inteiro — mais a atividade <Hl mono>EMENDA - SOLICITAR DOCS COM CLIENTE</Hl>, do setor
                        EMENDA, que desde 24/11/2026 entra na base. Um mesmo processo pode ter várias tarefas ao longo
                        do tempo (pedir documento, avaliar retorno, decidir dilação).
                    </p>
                    <DocGrid cols={2}>
                        <DocMini label="Tarefa encerrada">
                            O responsável exibido é sempre quem <strong>encerrou</strong> a tarefa.
                        </DocMini>
                        <DocMini label="Tarefa aberta">
                            Se ela ainda está aberta, é quem está atualmente <strong>atribuído</strong> a ela.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="A base comum das telas de 'Atividades no período'"
                badge="Alternador no topo"
            >
                <p>O alternador no topo do dashboard troca o eixo de data usado nos cálculos:</p>
                <DocGrid cols={2}>
                    <DocFeature title="Por prazo (padrão)" tone="info" icon="calendar" badge="Padrão" framed>
                        <p>
                            A página abre nesta visão. Todos os cartões olham para o <strong>prazo</strong> da tarefa:
                            entram só as tarefas com prazo dentro do período, não importa quando foram criadas ou
                            concluídas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Concluídas" tone="ok" icon="check-circle" badge="Conclusão" framed>
                        <p>
                            Total/Em andamento usam a data de <strong>criação</strong> da tarefa; Concluídas usa a data
                            em que ela foi <strong>encerrada</strong>.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Indicadores do período"
                subtitle="Os cartões de resumo no topo do dashboard"
                badge="5 cards"
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
                        what="Das tarefas do Total, quantas já foram assumidas por alguém e estão sendo trabalhadas."
                        counts='Apenas os status "Iniciado", "Reaberto" e "Encaminhado" — note que "Recebido" e "Visualizado" NÃO contam aqui.'
                        calc="Subconjunto do Total nesses três status específicos."
                        interpret='Por ser um subconjunto restrito do Total (diferente de outros dashboards da família, onde "Em andamento" cobre todo status ativo), este número é normalmente menor que o Total.'
                        caveat='Diferente de Emendas e Manifestações e de Réplicas: aqui "Recebido" e "Visualizado" ficam fora de "Em andamento".'
                    />
                    <MetricCard
                        icon="alert"
                        name="Vencidas"
                        what="Tarefas ativas cujo prazo já passou, hoje."
                        counts="Tarefas ativas com prazo anterior à data de hoje."
                        calc="Na visão Concluídas, não depende do período filtrado nem de quando a tarefa foi criada — é sempre relativo ao dia de hoje. Na visão Por prazo, conta só as tarefas com prazo dentro do período."
                        interpret="Indicador de urgência: qualquer valor acima de zero merece atenção."
                    />
                    <MetricCard
                        icon="clock"
                        name="Vencem hoje"
                        what="Tarefas ativas cujo prazo é exatamente hoje."
                        counts="Tarefas ativas com prazo igual à data de hoje."
                        calc="Mesma lógica de Vencidas (inclusive a diferença entre as visões), mas comparando prazo = hoje."
                        interpret="Ajuda a priorizar o que precisa ser resolvido ainda no dia."
                    />
                    <MetricCard
                        icon="check"
                        name="Concluídas"
                        what="Tarefas do setor que foram encerradas no período — contagem separada do Total."
                        counts='Status "Encerrado Cumprido" ou "Encerrado Não Cumprido" com data de encerramento no período.'
                        calc="Contagem direta dos registros encerrados no período, independente de quando foram criados."
                        interpret="Mede a produção efetiva de fechamento do setor no período — é o denominador da Taxa de Dilação."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="dilacao"
                title="03 — Taxa de Dilação"
                subtitle="A régua de qualidade do setor — e a base da faixa de comissão"
                tone="violet"
                badge="Quanto menor, melhor"
            >
                <DocCallout tone="violet" icon="percent" title="O que a taxa mede" badge="Taxa de dilação">
                    <p>
                        A <strong>taxa de dilação</strong> mostra, de tudo que o setor encerrou, quanto acabou virando
                        um pedido de dilação de prazo por falta de documento do cliente. Quanto menor essa taxa, melhor
                        a qualidade do trabalho. A taxa de cada funcionário define a faixa da comissão (seção 04).
                    </p>
                </DocCallout>

                <DocGrid cols={2}>
                    <DocFeature title="Como o numerador é encontrado" tone="accent" badge="Numerador">
                        <p>
                            O NG não tem um setor dedicado de "Dilação de Prazo" como a LA — conta-se, em vez disso, um
                            agendamento <Hl mono>MANIFESTAÇÃO - ELABORAR DILAÇÃO</Hl> criado no período <em>somente</em>{' '}
                            quando, no mesmo processo, existe uma tarefa da base encerrada como{' '}
                            <strong>"Encerrado Não Cumprido"</strong>. Dilações sem essa tarefa vieram de outro fluxo e
                            ficam fora.
                        </p>
                        <p>
                            A regra é <strong>por exclusão</strong>: vale qualquer atividade da base, inclusive{' '}
                            <Hl mono>EMENDA - SOLICITAR DOCS COM CLIENTE</Hl>, exceto <Hl mono>SANAR PENDÊNCIA 1G</Hl>.
                            O código não verifica o motivo do encerramento — o motivo "Cliente não respondeu/enviou
                            docs" só explica por que o fluxo cria a dilação. O dono da dilação é quem encerrou o Não
                            Cumprido mais recente antes da criação dela.
                        </p>
                    </DocFeature>
                    <DocFeature title="Denominador" tone="info" badge="Concluídas">
                        <p>
                            O denominador é <strong>todo</strong> o volume encerrado do setor no período — o mesmo
                            número do cartão "Concluídas" acima.
                        </p>
                    </DocFeature>
                </DocGrid>

                <Formula>Taxa de dilação = dilações rastreadas ao setor ÷ Concluídas no período</Formula>

                <h3 className="doc-h3">Faixas</h3>
                <DocTable
                    head={['Faixa', 'Taxa de dilação']}
                    rows={[
                        ['Ouro', 'até 5%'],
                        ['Prata', 'de 5,1% a 10%'],
                        ['Bronze', 'de 10,1% a 15%'],
                        ['Sem faixa', 'acima de 15%, ou sem encerrados no período'],
                    ]}
                />
                <p>A taxa é arredondada para uma casa decimal antes de ser comparada com as faixas.</p>

                <DocCallout tone="info" title="Diferença para a LA">
                    <p>
                        No NG (e no RJ) a regra é <strong>por exclusão</strong>: toda atividade da base, menos Sanar
                        Pendência 1G. Na LA é uma <strong>lista fechada</strong> de duas atividades de pedido de
                        documentos.
                    </p>
                </DocCallout>

                <DocFeature title="Quem aparece na quebra por funcionário" tone="warn" icon="users" framed>
                    <p>
                        A quebra por funcionário só lista quem encerrou no período pelo menos uma tarefa sujeita a
                        dilação (qualquer uma, menos "Sanar Pendência 1G") — quem trabalha só em Sanar Pendência 1G
                        entra nos KPIs gerais, mas fica fora desta régua e da comissão.
                    </p>
                </DocFeature>
            </DocSection>

            <DocSection
                id="comissao"
                title="04 — Comissionamento"
                subtitle="Valor por pendência resolvida, conforme a faixa de cada funcionário"
                tone="ok"
                badge="PDF"
            >
                <DocTable
                    head={['Faixa (taxa individual)', 'Valor por pendência resolvida']}
                    rows={[
                        ['Ouro — até 5%', 'R$ 2,00'],
                        ['Prata — de 5,1% a 10%', 'R$ 1,00'],
                        ['Bronze — de 10,1% a 15%', 'R$ 0,50'],
                        ['Sem faixa — acima de 15% ou sem encerrados', 'R$ 0,00'],
                    ]}
                />
                <Formula>Comissão = pendências resolvidas no período × valor da faixa individual</Formula>
                <DocGrid cols={2}>
                    <DocMini label="Pendência resolvida">
                        Tarefa da base encerrada como <strong>"Encerrado Cumprido"</strong> no período, por quem
                        encerrou.
                    </DocMini>
                    <DocMini label="Quem entra">
                        Quem aparece na quebra por funcionário (seção 03) e resolveu pelo menos uma pendência no
                        período. Sem ninguém, o botão não aparece.
                    </DocMini>
                </DocGrid>
                <p>
                    A faixa é individual: cada funcionário recebe pela própria taxa de dilação. A taxa do setor aparece
                    no relatório só como informação.
                </p>
                <DocCallout tone="info" icon="lock" title="Quem vê">
                    <p>
                        O relatório de comissão (PDF) só aparece para quem tem acesso total à unidade ou à organização.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="graficos"
                title="05 — Gráficos e histórico"
                subtitle="Distribuição do trabalho e evolução no tempo"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Processos por atividade" tone="info" icon="barChart" badge="Processos">
                        <p>
                            Quantos processos distintos passaram por cada atividade do setor no período — conta
                            processos, não tarefas, então um processo com duas tarefas da mesma atividade só aparece uma
                            vez.
                        </p>
                    </DocFeature>
                    <DocFeature title="Demandas por funcionário" tone="accent" icon="users" badge="Tarefas">
                        <p>
                            Tarefas encerradas no período por funcionário, separadas em "Encerrado Cumprido" e
                            "Encerrado Não Cumprido" — mostra volume e qualidade lado a lado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Concluídas por mês / por dia" tone="ok" icon="calendar" badge="Histórico">
                        <p>
                            Histórico de encerramentos ao longo do tempo, com detalhamento por funcionário disponível no
                            drill-down.
                        </p>
                    </DocFeature>
                    <DocFeature title="Média diária por funcionário" tone="violet" icon="trendingUp" badge="Ritmo">
                        <p>
                            Total de tarefas encerradas por funcionário dividido pelo número de dias distintos em que
                            ele encerrou algo, sobre o <strong>histórico todo</strong> (não segue o período nem os
                            filtros) — compara ritmo de produção, não só volume total.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="06 — Filtros disponíveis"
                subtitle="Como personalizar a lista de tarefas"
                badge="Lógica E"
            >
                <DocGrid cols={2}>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} icon="filter" badge={f.badge} badgeMono={false}>
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
                <DocCallout tone="info" title="Os filtros se combinam">
                    <p>
                        Os filtros se combinam em "E" (um registro só aparece se atender a todos os filtros ativos).
                        Clicar numa barra dos gráficos acima aplica o filtro correspondente na página inteira.
                    </p>
                </DocCallout>
            </DocSection>
        </DocPage>
    )
}
