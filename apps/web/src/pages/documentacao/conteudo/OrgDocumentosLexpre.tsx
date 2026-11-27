import {
    Code,
    DashLink,
    DocCallout,
    DocChange,
    DocFeature,
    DocGrid,
    DocMini,
    DocNote,
    DocPage,
    DocPanel,
    DocRelation,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Organização de Documentos (LexPre). Texto da v1: LexHub/src/pages/documentacao/OrgDoc_Lexpre_NG.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'represados', label: 'Represados e devoluções' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'tempo', label: 'Tempo de resolução' },
    { id: 'rankings', label: 'Por funcionário' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'materias', label: 'Por matéria' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

export function OrgDocumentosLexpreDoc() {
    return (
        <DocPage
            title="Organização de Documentos (LexPre)"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Organização de Documentos a partir da nova
                    base de dados (banco <Code>lexpre</Code>). A lógica de negócio é a mesma do dashboard legado
                    (represados, resolvidos, comissão), mas a fonte dos dados mudou: em vez de uma tabela com uma linha
                    por processo, o lexpre registra cada movimentação de setor como um evento de log.{' '}
                    <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Escopo multi-unidade & fórmula compartilhada">
                    <p>
                        Este guia vale para o{' '}
                        <DashLink dashboard="org-documentos-lexpre">Organização de Documentos (LexPre)</DashLink> em
                        todas as unidades (troque a unidade no seletor da barra lateral): mesma query, mesma fórmula de
                        comissão e as mesmas regras descritas abaixo.
                    </p>
                    <DocGrid>
                        <DocMini label="Única diferença entre unidades">
                            O escritório (<Code>escritorio_id</Code>). Cada um tem seu bloco de <Code>setor_id</Code> no
                            log: Organização de Documentos é o <Hl mono>id 3</Hl> no NGAM e o{' '}
                            <Hl tone="info" mono>
                                id 11
                            </Hl>{' '}
                            no LAAM — o backend já reconhece os dois.
                        </DocMini>
                        <DocMini label="Comissão">
                            <Hl tone="ok" mono>
                                R$ 0,60
                            </Hl>{' '}
                            por protocolado a cada <strong>R$ 1 milhão</strong> de valor de causa — igual em todas as
                            unidades.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Da tabela de status (banco antigo) para o log de movimentação (lexpre)"
            >
                <DocPanel>
                    <p>
                        No banco antigo (<Code>ng</Code>), cada processo tinha uma linha só, com colunas{' '}
                        <Code>ENTRADA</Code>, <Code>SAIDA</Code> e <Code>STATUS</Code>. No lexpre não existe mais essa
                        tabela: toda vez que uma demanda entra ou sai de um setor, o sistema grava um evento na tabela{' '}
                        <Code>log_setor_demanda</Code>. O dashboard reconstrói entradas, saídas e o "estado atual" da
                        demanda a partir desses eventos.
                    </p>
                    <DocRelation
                        cardinality="1 movimentação"
                        caption="mesmo movimentacao_id"
                        left={{
                            name: 'SAÍDA de um setor',
                            badge: 'ex.: sai da Triagem',
                            tone: 'warn',
                            children: <>O evento que fecha a passagem da demanda pelo setor anterior.</>,
                        }}
                        right={{
                            name: 'ENTRADA no próximo setor',
                            badge: 'ex.: entra em Org. Documentos',
                            tone: 'info',
                            children: <>O evento que abre a passagem da demanda pelo setor seguinte.</>,
                        }}
                    />
                    <p>
                        As duas linhas nascem juntas (mesmo <Code>movimentacao_id</Code>) e representam uma única
                        movimentação. É por isso que o dashboard consegue saber "de qual setor a demanda veio" (para
                        identificar retornos) e "quem era o responsável" no momento de cada evento.
                    </p>
                </DocPanel>
                <DocGrid cols={2}>
                    <DocFeature title="Resolvidos" tone="ok" icon="calendar" badge="Filtro de datas" framed>
                        <p>
                            Demandas cuja <strong>última saída</strong> do setor (uma por demanda) foi para{' '}
                            <strong>Peticionamento ou Protocolo</strong> dentro do período selecionado. Saída para
                            Pendências é <strong>devolução</strong>, não resolução; e a demanda que voltou para a
                            Organização de Documentos não conta como resolvida — ela está represada de novo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Represados e devoluções" tone="info" icon="layers" badge="Sem filtro" framed>
                        <p>
                            Olham o <strong>estado atual</strong> da demanda (ou todo o histórico de devoluções), não o
                            recorte de datas — por isso o número do card não muda com o filtro de período.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="represados"
                title="02 — Represados e devoluções (acumulado total)"
                subtitle="Sempre o total atual — não dependem do filtro de datas"
                badge="Foto de agora"
            >
                <DocGrid>
                    <MetricCard
                        name="Represados"
                        icon="fileText"
                        what="Total de demandas que estão hoje no setor Organização de Documentos, aguardando ação."
                        counts="Demandas (não canceladas) cujo setor atual é Organização de Documentos, uma por demanda."
                        calc="Contagem direta das demandas ainda no setor. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado. O selo '% na fila' é represados ÷ (resolvidos no período + represados)."
                        caveat="Não é afetado pelo filtro de período — mostra sempre o total atual. Uma demanda de rubricas reunidas (pacote) conta como 1, não uma por rubrica do pacote."
                    />
                    <MetricCard
                        name="Devolvido p/ Pendência"
                        icon="undo"
                        what="Demandas que a Organização de Documentos devolveu para o setor Pendências."
                        counts="Eventos de saída do setor cuja movimentação pareada entrou em Pendências — cada devolução conta, mesmo que a mesma demanda tenha sido devolvida mais de uma vez."
                        calc="O card mostra o total histórico (sem filtro de período). O comparativo conta só as devoluções dentro do período contra o mesmo recorte do mês anterior, e o card fica em 'Atenção' quando elas subiram."
                        interpret="Devoluções frequentes indicam demandas que chegam ao setor com pendências a resolver antes de seguir."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="periodo"
                title="03 — Indicadores do período"
                subtitle="O que saiu do setor dentro do intervalo de datas selecionado"
                badge="Data de saída"
            >
                <DocGrid>
                    <MetricCard
                        name="Resolvido Manualmente"
                        icon="user"
                        what="Demandas organizadas por um funcionário de forma manual."
                        counts="Demandas resolvidas (última saída para Peticionamento ou Protocolo) no período, não canceladas, com peticionamento automático desativado (pet_auto = falso)."
                        calc="Contagem dessas saídas no período com pet_auto = falso."
                        interpret="Representa o trabalho manual do setor. Um bom número aqui indica alta produtividade da equipe."
                    />
                    <MetricCard
                        name="Resolvido Automaticamente"
                        icon="refresh"
                        what="Demandas organizadas e já encaminhadas para peticionamento de forma automática pelo sistema."
                        counts="Demandas resolvidas (última saída para Peticionamento ou Protocolo) no período, não canceladas, com peticionamento automático ativado (pet_auto = verdadeiro)."
                        calc="Contagem dessas saídas no período com pet_auto = verdadeiro."
                        interpret="Automações ajudam a aumentar o volume processado sem sobrecarregar a equipe. Quanto maior, mais eficiente o fluxo automatizado."
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="xCircle"
                        what="Demandas que foram encerradas sem organização."
                        counts="Demandas com status Cancelado cuja última saída do setor caiu no período (aqui sem exigir destino — o cancelamento não leva a demanda para outro setor)."
                        calc="Contagem dos cancelamentos dentro do período."
                        interpret="Cancelamentos podem indicar demandas inviáveis ou com erros. Monitore para identificar padrões."
                    />
                    <MetricCard
                        name="Total Resolvidos"
                        icon="check"
                        what="Soma de todas as demandas concluídas no período — tanto manuais quanto automáticas."
                        counts="Demandas não canceladas cuja última saída do setor, no período, foi para Peticionamento ou Protocolo."
                        calc="Resolvido Manualmente + Resolvido Automaticamente."
                        interpret="Indica o volume total produzido no período. Use para comparar períodos e medir a capacidade do setor."
                    />
                    <MetricCard
                        name="Protocolados (dentro de Total resolvidos)"
                        icon="check-circle"
                        what="Quantas demandas resolvidas pela Organização de Documentos de fato protocolaram no período."
                        counts="Demandas resolvidas pelo setor (em qualquer data de saída) com data de protocolo dentro do período e status atual 'Aguardando Despacho Inicial'."
                        calc="Contagem direta; o card mostra também a fatia sobre o Total resolvidos."
                        interpret="Mede quanto do trabalho do setor já virou protocolo. É a mesma base da comissão (Seção 08)."
                        caveat="Ancorado na data de PROTOCOLO desde 07/10/2026: uma demanda que saiu do setor em setembro e só protocolou em outubro conta em outubro. Por isso o número não é necessariamente menor que o Total resolvidos do mesmo período."
                    />
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Comparativo em todos os cards" tone="info" badge="vs. mês anterior">
                        <p>
                            Total resolvidos, Manual, Automático, Cancelados, Protocolados e Devolvido p/ Pendência
                            mostram a variação contra o mesmo recorte de dias no mês civil anterior. Sem base no período
                            anterior, o crescimento a partir do zero aparece como +100%.
                        </p>
                    </DocFeature>
                    <DocFeature title="Reajuizamento" tone="violet" badge="Cards próprios">
                        <p>
                            As demandas marcadas como reajuizamento ficam fora de todos os totais e da comissão e
                            aparecem só no quadro de reajuizamento (<strong>Resolvidos</strong> no período e{' '}
                            <strong>Represados</strong> agora).
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="layers" title="Quando os números vêm do banco legado">
                    <p>
                        Se o LexPre não tiver <strong>nenhum resolvido no período</strong>, os cards do período (Total
                        resolvidos, Manual, Automático, Cancelados e os tempos) passam a mostrar os números do OrgDoc{' '}
                        <strong>legado</strong> da unidade — o subtítulo da seção avisa. Represados e devoluções
                        continuam do LexPre (fila atual). Os números <strong>não se somam</strong>: é uma fonte ou a
                        outra. A comissão é sempre só do LexPre.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection id="tempo" title="04 — Tempo de resolução" subtitle="Quanto tempo uma demanda fica no setor">
                <DocGrid cols={2}>
                    <DocFeature title="Tempo Médio / Mediana Resolvidos" tone="accent" badge="Entrada → saída">
                        <p>
                            Diferença entre o evento de entrada no setor e o evento de saída, para as demandas
                            resolvidas (não canceladas, com saída para Peticionamento ou Protocolo) no período. Quando
                            uma demanda entra mais de uma vez no setor (por causa de um retorno), usa-se sempre a{' '}
                            <strong>entrada mais recente</strong> antes da saída.
                        </p>
                    </DocFeature>
                    <DocFeature title="Comparativo (Média e Mediana)" tone="info" badge="vs. mês anterior">
                        <p>
                            Variação percentual da média e da mediana do período selecionado contra o mesmo recorte de
                            dias no mês civil anterior. Aqui <strong>subir é pior</strong>: o tempo aumentou.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="rankings"
                title="05 — Por funcionário"
                subtitle="Distribuição do trabalho e atribuição de responsabilidade"
            >
                <DocCallout icon="users" title="Quem estava com a demanda quando ela foi resolvida?">
                    <p>
                        O lexpre registra o responsável no momento em que a demanda <em>entra</em> no setor; o evento de
                        saída normalmente não traz responsável. Por isso, para todo gráfico "por funcionário" sobre
                        demandas resolvidas, vale o responsável da <strong>última entrada</strong> da demanda no setor
                        antes da saída — ou o da própria saída, quando ela trouxer um.
                    </p>
                </DocCallout>
                <DocGrid cols={3}>
                    <DocFeature title="Desempenho por funcionário" tone="accent" badge="Clicável">
                        <p>
                            Resolvidos (no período) e represados (estoque atual) de cada funcionário, contra a meta
                            diária. Clicar numa pessoa filtra a página inteira por ela.
                        </p>
                    </DocFeature>
                    <DocFeature title="Média de Resolvidos por Funcionário" tone="info" badge="Por dia">
                        <p>
                            Total de resolvidos ÷ número de dias distintos com saídas atribuídas ao funcionário. Compara
                            produtividade levando em conta dias trabalhados.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de Causa por Funcionário" tone="ok" badge="ANP: dano moral">
                        <p>
                            Soma o valor de causa das demandas resolvidas por cada funcionário, com a parte já{' '}
                            <strong>protocolada</strong> em destaque. Para matéria ANP, usa o campo de dano moral; para
                            as demais, o valor de causa da demanda.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="06 — Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid cols={3}>
                    <DocFeature title="Produção Diária" tone="accent" badge="Dia da saída">
                        <p>
                            Demandas resolvidas agrupadas por dia do evento de saída. Útil para identificar picos e
                            vales de produtividade dentro do período selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Represados por Mês de Entrada" tone="info" badge="Sem período">
                        <p>
                            Agrupa as demandas ainda represadas pelo mês em que entraram no setor pela última vez —
                            mostra se o estoque parado é recente ou antigo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Resolvidos Mês a Mês" tone="ok" badge="Ano a ano">
                        <p>
                            Visão mensal da produção, uma linha por ano. Usa o histórico completo, sem recorte de
                            período, para permitir a comparação entre anos.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="materias"
                title="07 — Por matéria"
                subtitle="Distribuição das demandas por tipo de matéria jurídica"
            >
                <DocCallout icon="fileText" title="De onde vem a matéria">
                    <p>
                        No lexpre, a matéria vem diretamente da rubrica cadastrada na demanda (ex.:{' '}
                        <Code>JUROS_ABUSIVOS</Code>, <Code>ANP</Code>, <Code>SEGURO</Code>) — já normalizada, sem o
                        sufixo livre que existia no banco antigo (ex.: <Code>BX_ANT_FIN - BANCO BRADESCO</Code>).
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Top 10 – Resolvidos por Matéria" tone="accent" badge="No Setor · Protocolados">
                        <p>
                            Agrupa as demandas resolvidas no período pela rubrica. O botão de alternância mostra{' '}
                            <strong>"No Setor"</strong> (saíram do Org Doc no período, por data de saída) ou{' '}
                            <Hl tone="ok">"Protocolados"</Hl> (de fato protocolaram no período, por data de protocolo —
                            ver Seção 08). Como os recortes de data são diferentes, uma demanda pode aparecer em "No
                            Setor" num período e só em "Protocolados" num período posterior (ou nunca). Clicar numa
                            matéria filtra a página; clicar num pacote de <strong>rubricas reunidas</strong> abre a
                            lista das rubricas dentro dele.
                        </p>
                    </DocFeature>
                    <DocFeature title="Top 10 – Represados por Matéria" tone="info" badge="Sem período">
                        <p>
                            Agrupa as demandas represadas (estoque atual) pela rubrica. Útil para priorizar quais tipos
                            de demanda têm maior acúmulo.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="08 — Comissionamento"
                subtitle="Como o sistema calcula a comissão de cada funcionário"
                tone="ok"
                badge="R$ 0,60 por protocolado a cada R$ 1 mi"
            >
                <Formula>Comissão = R$ 0,60 × Qtd de protocolados × (Valor de causa protocolado / 1.000.000)</Formula>
                <p>
                    Mesma fórmula do dashboard legado — o valor depende tanto da quantidade de demandas quanto do valor
                    das causas delas. Mas só contam demandas que de fato chegaram a ser <strong>protocoladas</strong>,
                    não qualquer demanda que o Org Doc marcou como "resolvida".
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Qtd de protocolados" tone="ok" icon="check" badge="Data de protocolo" framed>
                        <p>
                            Das demandas resolvidas pelo funcionário (saíram do Org Doc rumo a Peticionamento ou
                            Protocolo, em qualquer data), conta só as que têm a{' '}
                            <strong>data de protocolo dentro do período</strong> e status atual "Aguardando Despacho
                            Inicial" — ou seja, que de fato protocolaram nesse período.
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Valor de causa protocolado"
                        tone="info"
                        icon="dollar"
                        badge="ANP: dano moral"
                        framed
                    >
                        <p>
                            Soma o valor de causa só das mesmas demandas protocoladas contadas ao lado. Para matéria
                            ANP, usa o campo de dano moral; para as demais, o valor de causa da demanda. Demandas sem
                            valor de causa não contribuem.
                        </p>
                    </DocFeature>
                    <DocFeature title="Base do cálculo" tone="accent" icon="users">
                        <p>
                            Apenas demandas não canceladas, resolvidas pelo setor —{' '}
                            <strong>manuais e automáticas</strong> — e atribuídas ao funcionário responsável; quantidade
                            e valor de causa "protocolado" são filtrados pela <strong>data de protocolo</strong> (não
                            pela data de saída do setor) no período selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Fica de fora" tone="danger" icon="ban" framed>
                        <p>
                            Demanda que nunca chega a protocolar (parada em Peticionamento, cancelada depois etc.) não
                            entra nunca. Demanda que saiu do Org Doc num mês e só protocolou no seguinte entra no mês em
                            que <strong>realmente protocolou</strong>. Também ficam de fora o reajuizamento e as
                            demandas do banco legado.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocFeature title="Exemplo prático" tone="ok" badge="R$ 150,00">
                    <p>
                        Um funcionário organizou 100 pastas no mês. Dessas, só 50 já foram protocoladas naquele período,
                        somando R$ 5.000.000,00 de valor de causa — as outras 50 ainda estão em Peticionamento (ou em
                        outra etapa), sem contar nem na quantidade nem no valor de causa. Comissão = R$ 0,60 × 50 ×
                        (5.000.000 ÷ 1.000.000) = R$ 0,60 × 50 × 5 = <Hl tone="ok">R$ 150,00</Hl> (não R$ 300,00, que
                        seria o resultado se as 100 pastas organizadas contassem).
                    </p>
                </DocFeature>
                <DocNote date="03/09/2026">
                    Mudança de regra simulada para o dashboard Org Documentos legado (banco <Code>ng</Code>): não pagar
                    comissão sobre demandas (nem sobre o valor de causa delas) que podem nunca chegar a ser protocoladas
                    — aplicada aqui só ao lexpre.
                </DocNote>
                <DocNote date="04/09/2026">
                    Refinada para também restringir a <strong>quantidade</strong> (não só o valor de causa) aos casos de
                    fato protocolados.
                </DocNote>
                <DocNote date="07/10/2026">
                    A demanda passa a entrar no comissionamento do mês em que <strong>realmente protocolou</strong>, não
                    no mês em que saiu do setor.
                </DocNote>
                <DocGrid cols={2}>
                    <DocFeature title="Gestor e Desenvolvedor" tone="info" icon="shield" badge="Veem todos">
                        <p>
                            Veem a comissão de todos os funcionários e o botão <strong>"Gerar comissão (PDF)"</strong>{' '}
                            (funcionário, quantidade de protocolados, valor de causa protocolado e comissão) — mesmo
                            botão e mesmo formato de PDF do dashboard Org Documentos legado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Demais cargos" tone="neutral" icon="user" badge="Só a própria linha">
                        <p>
                            Veem só a <strong>própria</strong> comissão, pelo vínculo entre a pessoa e o funcionário no
                            LexPre. Sem esse vínculo cadastrado, a comissão aparece vazia — é o comportamento esperado,
                            não um erro.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="09 — Filtros disponíveis"
                subtitle="Como personalizar e cruzar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Período" badge="Data de saída" badgeTone="accent">
                        <p>
                            Filtra as demandas resolvidas pela data do evento de saída do setor (Protocolados e
                            comissão: pela data de protocolo). Represados e o total de devoluções não são afetados.
                        </p>
                    </DocFeature>
                    <DocFeature title="Funcionário" badge="Topo + Clique" badgeTone="info">
                        <p>
                            Restringe a visão a um ou mais funcionários — pelo filtro no topo ou clicando nos gráficos{' '}
                            <em>"por funcionário"</em>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Matéria" badge="Topo + Clique" badgeTone="ok">
                        <p>
                            Filtra por rubrica (matéria jurídica) — pelo filtro no topo ou clicando no gráfico de Top 10
                            por Matéria.
                        </p>
                    </DocFeature>
                    <DocFeature title="UF" badge="customer.uf" badgeTone="neutral">
                        <p>
                            Filtra pelo estado do cliente da demanda. O filtro só aparece quando há UFs cadastradas nas
                            demandas da unidade.
                        </p>
                    </DocFeature>
                    <DocFeature title="Área de atuação" badge="public.area_atuacao" badgeTone="neutral">
                        <p>
                            Filtra pela operação vinculada à rubrica da demanda (equivalente à "área de atuação" do
                            dashboard legado).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="10 — Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe e o motivo de cada decisão"
                tone="danger"
            >
                <DocGrid cols={3}>
                    <DocChange status="Cards próprios" tone="violet" area="Demandas" title="Reajuizamento separado">
                        <p>
                            No legado, "Resolvidos Reajuizamento" era um card do dashboard. No LexPre, as demandas de
                            reajuizamento ficam <strong>fora dos totais e da comissão</strong>, num quadro próprio de
                            resolvidos e represados.
                        </p>
                    </DocChange>
                    <DocChange status="Mais estrito" tone="info" area="Resolvidos" title="Resolvido exige destino">
                        <p>
                            Só conta como resolvida a saída para <strong>Peticionamento ou Protocolo</strong>; a saída
                            para Pendências vira o card <strong>Devolvido p/ Pendência</strong>.
                        </p>
                    </DocChange>
                    <DocChange status="Reserva" tone="ok" area="Dados" title="Legado quando o LexPre está vazio" framed>
                        <p>
                            Sem resolvidos no LexPre no período, os cards do período mostram o OrgDoc{' '}
                            <strong>legado</strong> da unidade; o "Resolvidos mês a mês" junta as duas bases (o LexPre
                            prevalece no mês em comum).
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
