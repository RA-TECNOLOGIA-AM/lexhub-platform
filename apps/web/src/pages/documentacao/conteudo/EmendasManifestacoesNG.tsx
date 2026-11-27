import {
    DocCallout,
    DocChange,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    Hl,
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
    { id: 'graficos', label: 'Gráficos' },
    { id: 'filtros', label: 'Demais filtros' },
]

const FILTERS = [
    {
        name: 'Funcionários',
        badge: 'Pessoas',
        desc: 'Restringe às tarefas de um ou mais funcionários. Também é aplicado clicando em "Demandas por funcionário" ou na média diária.',
    },
    {
        name: 'Atividade',
        badge: 'Clique no gráfico',
        desc: 'Filtra por uma ou mais atividades do setor. É aplicado clicando no gráfico "Por atividade" e aparece nas etiquetas de filtro.',
    },
    {
        name: 'Situação do processo',
        badge: 'Processo',
        desc: 'Ativo, Suspenso / Sobrestado ou Arquivado — é a situação do processo, não da tarefa. Sem escolha, entram todas.',
    },
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
                    equivalente da LA. O RJ usa as mesmas regras do NG, com uma diferença na Dilação (seção 03).
                </>
            }
            header={
                <DocCallout caps title="Uma linha, uma tarefa do setor MANIFESTAÇÃO" badge="Setor MANIFESTAÇÃO">
                    <p>
                        Cada linha é uma tarefa (agendamento) do setor "MANIFESTAÇÃO" do NG. O responsável exibido
                        depende de a tarefa estar encerrada ou não:
                    </p>
                    <DocGrid cols={2}>
                        <DocMini label="Tarefa encerrada">
                            O responsável é sempre quem <Hl>encerrou</Hl> a tarefa.
                        </DocMini>
                        <DocMini label="Tarefa ainda aberta">
                            O responsável é quem está <Hl tone="info">atribuído</Hl> a ela no momento.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="O setor MANIFESTAÇÃO e a diferença para a LA"
            >
                <DocCallout tone="violet" icon="layers" title="Diferença para a LA" badge="Setor MANIFESTAÇÃO">
                    <p>
                        O dashboard pega todas as atividades <Hl mono>MANIFESTAÇÃO - …</Hl> do NG — o setor é mais
                        enxuto que o "INTERMEDIÁRIAS" da LA. A atividade "EMENDA - SOLICITAR DOCS COM CLIENTE" (do setor
                        EMENDA, etapa preparatória, equivalente a "Avaliar Manifestação" na LA) fica fora deste
                        dashboard; desde 24/11/2026 ela entra em Pendências Intermediárias NG.
                    </p>
                </DocCallout>
                <h3 className="doc-h3">Duas visões da mesma tela</h3>
                <DocGrid cols={2}>
                    <DocFeature title="Por prazo (padrão)" tone="info" icon="calendar" badge="Padrão" framed>
                        <p>
                            A página abre nesta visão. Todos os cartões olham para o <strong>prazo</strong> da tarefa —
                            é também o eixo usado pelo comissionamento.
                        </p>
                    </DocFeature>
                    <DocFeature title="Concluídas" tone="ok" icon="check-circle" badge="Conclusão" framed>
                        <p>
                            Total/Em andamento usam a data de <strong>criação</strong>; Concluídas usa a data de
                            <strong> encerramento</strong>.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Indicadores do período"
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
                        calc="Na visão Concluídas, é comparação direta com a data de hoje e não depende do período filtrado. Na visão Por prazo, conta só as tarefas com prazo dentro do período."
                        interpret="Indicador de urgência: qualquer valor acima de zero merece atenção."
                    />
                    <MetricCard
                        icon="clock"
                        name="Vencem hoje"
                        what="Tarefas ativas cujo prazo é exatamente hoje."
                        counts="Tarefas ativas com prazo igual à data de hoje."
                        calc="Mesma lógica de Vencidas (inclusive a diferença entre as visões), comparando prazo = hoje."
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
            </DocSection>

            <DocSection
                id="atividades"
                title="03 — Classificação de atividades"
                subtitle="Quais atividades geram peça remunerada"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Manifestação" tone="ok" icon="fileText" badge="Comissiona" framed>
                        <p>
                            Todas as demais atividades do setor — ex.: Protocolar Emenda · Protocolar Emenda Fatal ·
                            Manifestação Simples · Manifestação Específica · Manifestação - Provas · Manifestação →
                            Conexão/Aditamento · Manifestação → Alegações Finais · Elaborar Manifestação - Pedido de
                            Providências. Atividade nova cadastrada no setor já entra automaticamente.
                        </p>
                    </DocFeature>
                    <DocFeature title="Dilação" tone="info" icon="clock" badge="Comissiona" framed>
                        <p>Elaborar Dilação. No RJ, "Manifestar Dilação de Prazo" também conta como Dilação.</p>
                    </DocFeature>
                    <DocFeature title="Não comissionável" tone="neutral" icon="ban" badge="Sem comissão" framed>
                        <p>Análise de Manifestação (e o nome antigo, Elaborar Manifestação)</p>
                    </DocFeature>
                </DocGrid>
                <DocChange status="02/10/2026" area="Regra de classificação" title="Regra por exclusão" framed>
                    <p>
                        Desde 02/10/2026 a regra é por <strong>exclusão</strong>: a única atividade que não gera
                        comissão é "Análise de Manifestação" (nome antigo: "Elaborar Manifestação"); todas as outras do
                        setor comissionam — Elaborar Dilação como Dilação, o resto como Manifestação. Antes era uma
                        lista fechada, e atividades novas do catálogo (Manifestação Simples, Provas, etc.) ficavam de
                        fora sem ninguém perceber.
                    </p>
                </DocChange>
            </DocSection>

            <DocSection
                id="comissao"
                title="04 — Comissionamento"
                subtitle="Valor fixo por peça, sem faixa"
                tone="ok"
                badge="Sem faixa"
            >
                <DocCallout tone="info" title="O NG não usa faixas" badge="Sem gatilho mínimo">
                    <p>
                        Diferente da LA, o NG <strong>não usa faixas</strong> de agenda cumprida. Toda peça "Encerrado
                        Cumprido" com prazo no período vale o mesmo valor, sem gatilho mínimo. O percentual de agenda
                        cumprida continua calculado e exibido, mas é só informativo — não muda o valor pago.
                    </p>
                </DocCallout>
                <h3 className="doc-h3">Valores fixos</h3>
                <DocGrid cols={3}>
                    <DocFeature title="Manifestação" tone="ok" icon="dollar" badge="R$ 1,00" framed>
                        <p>Por peça encerrada como "Encerrado Cumprido" com prazo no período.</p>
                    </DocFeature>
                    <DocFeature title="Dilação" tone="info" icon="dollar" badge="R$ 0,50" framed>
                        <p>Por peça encerrada como "Encerrado Cumprido" com prazo no período.</p>
                    </DocFeature>
                    <DocFeature title="Gatilho de agenda" tone="neutral" icon="target" badge="Nenhum">
                        <p>Nenhum — sempre elegível.</p>
                    </DocFeature>
                </DocGrid>
                <p>
                    Mesma regra de peça paga da LA: só conta como peça quem foi encerrado como "Encerrado Cumprido" com
                    prazo no período. Validado com dados reais: 250 manifestações e 24 dilações em julho/2026.
                </p>
                <h3 className="doc-h3">Cartões ao lado da agenda</h3>
                <DocGrid cols={2}>
                    <MetricCard
                        icon="fileText"
                        name="Manifestações no período"
                        what="Peças de Manifestação produzidas no período — a base da comissão."
                        counts='Tarefas de Manifestação encerradas como "Encerrado Cumprido" com prazo no período.'
                        calc="A variação compara com os mesmos dias do mês civil anterior (ex.: 1 a 15 deste mês contra 1 a 15 do mês passado)."
                        interpret="Mostra o volume pago e se ele subiu ou caiu em relação ao mês anterior."
                    />
                    <MetricCard
                        icon="clock"
                        name="Dilações no período"
                        what="Peças de Dilação produzidas no período."
                        counts='Tarefas de Dilação encerradas como "Encerrado Cumprido" com prazo no período.'
                        calc="Mesma comparação com os mesmos dias do mês civil anterior."
                        interpret="Mesmo uso do cartão de Manifestações, para as dilações."
                    />
                </DocGrid>
                <DocCallout tone="info" icon="lock" title="Quem vê">
                    <p>
                        O relatório de comissão (PDF) só aparece para quem tem acesso total à unidade ou à organização.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="uf"
                title="05 — Filtro de UF"
                subtitle="Recurso exclusivo deste dashboard"
                tone="violet"
                badge="NG e RJ"
            >
                <DocCallout tone="violet" icon="pin" title="Por que o filtro de UF só existe aqui">
                    <p>
                        UF não é um campo nativo da base de agendamentos — vem de uma consulta adicional ao cadastro do
                        processo. É por isso que o filtro de UF existe só no NG (e no RJ, que usa a mesma regra), e não
                        na LA nem nos outros dois dashboards da família (Pendências Intermediárias e Réplicas).
                    </p>
                </DocCallout>
                <p>
                    A tabela de comissão por funcionário também é quebrada por UF — cada funcionário mostra quantas
                    manifestações e dilações produziu em cada estado. Distribuição real observada (jul/2026): AM
                    concentra a maior parte do volume, com PB e PA bem menores.
                </p>
            </DocSection>

            <DocSection id="graficos" title="06 — Gráficos" subtitle="Distribuição do trabalho e ritmo">
                <DocGrid cols={2}>
                    <DocFeature title="Por atividade" tone="info" icon="barChart" badge="Clicável">
                        <p>
                            Tarefas encerradas por atividade, com prazo (ou conclusão, na visão Concluídas) no período.
                            As barras são pintadas conforme a atividade gera ou não comissão. Clicar filtra a página.
                        </p>
                    </DocFeature>
                    <DocFeature title="Demandas por funcionário" tone="accent" icon="users" badge="Clicável">
                        <p>Tarefas encerradas no período por funcionário. Clicar filtra a página pela pessoa.</p>
                    </DocFeature>
                    <DocFeature title="Concluídas mês a mês / por dia" tone="ok" icon="calendar" badge="Histórico">
                        <p>Histórico de encerramentos, com o detalhe por dia de cada mês.</p>
                    </DocFeature>
                    <DocFeature title="Média diária por funcionário" tone="violet" icon="trendingUp" badge="Período">
                        <p>
                            Encerradas ÷ dias com prazo (ou conclusão) <strong>dentro do período</strong> — aqui a média
                            segue o período, diferente de Pendências Intermediárias e Réplicas.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="07 — Demais filtros"
                subtitle="Como personalizar a lista de tarefas"
                tone="info"
            >
                <DocGrid cols={2}>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} badge={f.badge} badgeTone="info">
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
                <p>A tabela de tarefas também mostra o número do processo (formato CNJ) quando disponível.</p>
            </DocSection>
        </DocPage>
    )
}
