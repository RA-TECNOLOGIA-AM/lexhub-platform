import {
    DashLink,
    DocCallout,
    DocChips,
    DocFeature,
    DocGrid,
    DocMini,
    DocPage,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Publicações (LexFlow, NG/LA/RJ). Escrito na V2 a partir do código:
// apps/web/src/pages/dashboards/publicacoes/* (página e contas do navegador),
// apps/api/src/app/dashboards/publicacoes.py (o que a API devolve, quem vê a comissão) e
// apps/api/src/app/analyses/familias/publicacoes.py (as regras de cada número).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'indicadores', label: 'Indicadores do período' },
    { id: 'taxa', label: 'Taxa de resolução' },
    { id: 'linha-do-tempo', label: 'Publicações diárias' },
    { id: 'distribuicao', label: 'Matérias, leitores e tribunais' },
    { id: 'agendamento', label: 'Agendamento após a publicação' },
    { id: 'lista', label: 'Lista de publicações' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
]

export function PublicacoesDoc() {
    return (
        <DocPage
            title="Publicações"
            tags={['NG', 'LA', 'LARJ']}
            note="Dados do LexFlow · mesma lógica nas três unidades"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Publicações: quantas publicações chegaram,
                    quantas foram cumpridas, quanto tempo levou, quem leu cada uma e se o cumprimento gerou um
                    agendamento no processo — que é também o que define a comissão dos leitores.{' '}
                    <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="O caminho de uma publicação" badge="LexFlow">
                    <p>
                        A publicação <strong>chega</strong> no dia em que é disponibilizada, é <strong>lida</strong> por
                        um leitor (fica "Visualizado") e é <strong>cumprida</strong> quando ele conclui o tratamento. Se
                        o cumprimento gerou um agendamento no mesmo processo, a publicação conta como certa para a
                        comissão.
                    </p>
                    <DocGrid>
                        <DocMini label="O que muda entre unidades">
                            No <Hl mono>LA</Hl> a linha do tempo não tem a série "Visualizadas" e a lista mostra{' '}
                            <strong>Tribunal / órgão</strong> no lugar do agendamento. O resto é igual na NG, no LA e no
                            RJ.
                        </DocMini>
                        <DocMini label="Dia de referência">
                            É o <strong>último dia do período</strong> escolhido. Alguns cards olham só para esse dia —
                            o subtítulo da primeira seção do dashboard mostra qual é.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Três situações possíveis e duas datas que decidem em qual período cada publicação entra"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Não visualizado" tone="info" icon="eyeOff" framed>
                        <p>Chegou e ninguém leu ainda. Conta como pendente.</p>
                    </DocFeature>
                    <DocFeature title="Visualizado" tone="warn" icon="eye" framed>
                        <p>Já foi lida, mas ainda não foi cumprida. Também conta como pendente.</p>
                    </DocFeature>
                    <DocFeature title="Cumprido" tone="ok" icon="check-circle" framed>
                        <p>O tratamento foi concluído. Entra nas cumpridas do dia da conclusão.</p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="calendar" title="Qual data cada número usa?">
                    <DocGrid>
                        <DocMini label="Recebidas">
                            Pela <strong>data de disponibilização</strong> — o dia em que a publicação chegou.
                        </DocMini>
                        <DocMini label="Cumpridas">
                            Pela <strong>data de conclusão</strong> — só as que estão com status Cumprido.
                        </DocMini>
                    </DocGrid>
                    <p>
                        Por isso uma publicação que chegou no fim de um mês e foi cumprida no começo do seguinte aparece
                        nas recebidas de um mês e nas cumpridas do outro.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Quem é o leitor" tone="accent" icon="user" badge="Leitor → Responsável">
                        <p>
                            Os números por funcionário usam o <strong>leitor</strong> designado. Quando ele está vazio
                            (cumprimento em lote no LexFlow costuma não preenchê-lo), vale o{' '}
                            <strong>responsável</strong>. Sem nenhum dos dois, aparece como{' '}
                            <strong>"Sem leitor"</strong>. Os nomes aparecem com os dois primeiros nomes, em maiúsculas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Foto de agora × período" tone="info" icon="clock" badge="Atenção">
                        <p>
                            <strong>Pendentes</strong> e <strong>Recebidas hoje</strong> não dependem do período:
                            mostram o estoque de agora e o dia de hoje. Todo o resto segue o período escolhido.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="indicadores"
                title="02 — Indicadores do período"
                subtitle="Recebidas, pendentes, cumpridas e tempos no intervalo selecionado"
            >
                <DocGrid>
                    <MetricCard
                        name="Recebidas no período"
                        icon="inbox"
                        what="Quantas publicações chegaram no período."
                        counts="Publicações com data de disponibilização dentro do período, em qualquer status."
                        calc="Contagem direta."
                        interpret="É o volume de entrada do setor — a base da Taxa de resolução."
                    />
                    <MetricCard
                        name="Pendentes"
                        icon="clock"
                        what="O estoque de publicações ainda não cumpridas, agora."
                        counts='Publicações com status "Visualizado" ou "Não visualizado", de todo o histórico.'
                        calc="Contagem direta. Não depende do período (os filtros da página continuam valendo)."
                        interpret="Quanto menor, melhor: é o trabalho acumulado esperando o leitor."
                    />
                    <MetricCard
                        name="Recebidas hoje"
                        icon="calendar"
                        what="Quantas publicações chegaram hoje."
                        counts="Publicações com data de disponibilização igual à data de hoje (data do servidor, não do fuso da unidade)."
                        calc="Contagem direta, independente do período escolhido."
                        interpret="Mostra a carga do dia, mesmo quando o período olha para o passado."
                    />
                    <MetricCard
                        name="Zerado no período"
                        icon="target"
                        what="Quantas vezes o estoque de pendentes chegou a zero dentro do período."
                        counts="O estoque é reconstruído dia a dia: cada publicação entra no dia em que chegou e sai no dia em que foi cumprida."
                        calc="Conta cada vez que o estoque passa de mais que zero para zero. Dias seguidos zerados contam uma vez só."
                        interpret="Quanto mais vezes, mais vezes a equipe deixou a fila em dia."
                        caveat="Uma publicação que nunca foi cumprida continua no estoque reconstruído para sempre — basta uma assim (com os filtros da página) para o estoque não zerar mais."
                    />
                    <MetricCard
                        name="Cumpridas no mesmo dia"
                        icon="check-circle"
                        what="Quantas publicações chegaram e foram cumpridas no próprio dia de referência."
                        counts="Cumpridas cuja data de disponibilização e data de conclusão são as duas iguais ao dia de referência."
                        calc="Contagem direta. O percentual embaixo é: cumpridas no mesmo dia ÷ chegadas no dia de referência."
                        interpret="Mede a agilidade no dia: 100% quer dizer que tudo o que chegou naquele dia foi cumprido no mesmo dia."
                        caveat="A dica do card também mostra o total de todo o histórico (cumpridas no mesmo dia da chegada, de todas as que têm data de disponibilização), com os mesmos filtros."
                    />
                    <MetricCard
                        name="Cumpridas no período"
                        icon="check"
                        what="Quantas publicações foram cumpridas no período."
                        counts="Publicações com status Cumprido e data de conclusão dentro do período."
                        calc="Contagem direta."
                        interpret="É a produção do setor no período, e o numerador da Taxa de resolução."
                    />
                    <MetricCard
                        name="Tempo médio de tratamento"
                        icon="clock"
                        what="Quanto tempo, em média, uma publicação leva entre chegar e ser cumprida."
                        counts="As cumpridas no período."
                        calc="Média dos dias entre a data de disponibilização e a data de conclusão. Cumprida no mesmo dia conta como zero."
                        interpret="Quanto menor, melhor. É exibido como duração (ex.: '2d 3h')."
                        caveat="As duas datas são dias, sem hora — por isso o valor é sempre uma média de dias inteiros."
                    />
                    <MetricCard
                        name="Cumpridas no dia de referência"
                        icon="check-circle"
                        what="Quantas publicações foram cumpridas no último dia do período."
                        counts="Cumpridas com data de conclusão igual ao dia de referência."
                        calc="Contagem direta."
                        interpret='Com o período terminando hoje, é a produção de hoje (a versão antiga chamava de "Cumpridas hoje").'
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="taxa"
                title="03 — Taxa de resolução"
                subtitle="Quanto do que chegou no período já foi cumprido"
                tone="ok"
                badge="Mínimo 98%"
            >
                <Formula>Taxa de resolução = Cumpridas no período ÷ Recebidas no período</Formula>
                <p>
                    A barra mostra as cumpridas (verde) e as não cumpridas (vermelho), com um traço no{' '}
                    <Hl tone="ok">98%</Hl> — o mínimo para comissionar. O selo ao lado diz <Hl tone="ok">Comissiona</Hl>{' '}
                    quando a taxa é 98% ou mais, <Hl tone="danger">Não comissiona</Hl> abaixo disso e{' '}
                    <strong>Sem dados</strong> quando nada chegou no período.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Datas diferentes em cima e embaixo" tone="warn" icon="alert" framed>
                        <p>
                            As cumpridas contam pela data de conclusão e as recebidas pela data de chegada. Uma
                            publicação que chegou antes do período e foi cumprida dentro dele entra só em cima — por
                            isso a taxa pode passar de 100%.
                        </p>
                    </DocFeature>
                    <DocFeature title="É a taxa do que está filtrado" tone="info" icon="filter" framed>
                        <p>
                            Sem filtro, é a taxa do setor inteiro. Filtrando por um leitor, vira a taxa daquele leitor.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="linha-do-tempo"
                title="04 — Publicações diárias"
                subtitle="Chegadas, cumpridas e atraso ao longo dos dias do período"
            >
                <p>
                    Um gráfico de linhas com um ponto por dia do período. A seção só aparece quando há algum dado no
                    período.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Chegadas" tone="accent" badge="Data de disponibilização">
                        <p>Quantas publicações chegaram em cada dia.</p>
                    </DocFeature>
                    <DocFeature title="Cumpridas" tone="ok" badge="Data de conclusão">
                        <p>Quantas publicações foram cumpridas em cada dia.</p>
                    </DocFeature>
                    <DocFeature title="Visualizadas" tone="info" badge="Só NG e RJ">
                        <p>
                            Pelo dia da leitura: publicações que foram lidas naquele dia e ainda estão só "Visualizado"
                            (não cumpridas).
                        </p>
                    </DocFeature>
                    <DocFeature title="Atraso em dias" tone="danger" badge="Linha tracejada">
                        <p>
                            Não é uma contagem. Nos dias em que ainda existe publicação pendente que chegou naquele dia,
                            mostra quantos dias se passaram até o dia de referência. Dia sem pendente fica em zero. As
                            pendentes são as de agora: com um período que termina no passado, o que chegou depois do dia
                            de referência aparece com atraso zero nesse dia.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="distribuicao"
                title="05 — Matérias, leitores e tribunais"
                subtitle="As publicações recebidas no período por dimensão, e as demandas de cada leitor"
                badge="Clique para filtrar"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Publicações por matéria" icon="layers" badge="Vários valores" badgeTone="accent">
                        <p>
                            Recebidas no período, pela matéria do processo. Sem processo ou sem matéria: "SEM MATERIA".
                            Clicar soma a matéria ao filtro (dá para escolher várias).
                        </p>
                    </DocFeature>
                    <DocFeature title="Publicações por tipo de documento" icon="fileText" badge="Um valor">
                        <p>Recebidas no período, pelo tipo de documento da publicação.</p>
                    </DocFeature>
                    <DocFeature title="Publicações por tribunal" icon="scale" badge="Um valor">
                        <p>
                            Uma rosca com a lista ao lado (quantidade e %). Clicar na fatia ou na linha filtra pelo
                            tribunal; sem tribunal: "SEM TRIBUNAL".
                        </p>
                    </DocFeature>
                    <DocFeature title="Publicações por órgão/vara" icon="building" badge="Um valor">
                        <p>Recebidas no período, pelo órgão de origem da publicação.</p>
                    </DocFeature>
                </DocGrid>
                <DocFeature
                    title="Demandas por funcionário"
                    tone="info"
                    icon="users"
                    badge="Período + estoque atual"
                    badgeTone="info"
                    framed
                    wide
                >
                    <p>
                        Um cartão por leitor, do maior para o menor total. A barra junta duas coisas de tempos
                        diferentes: as <strong>cumpridas no período</strong> e as <strong>pendentes de agora</strong> (o
                        mesmo estoque do card Pendentes, sem período). Clicar no cartão soma o leitor ao filtro.
                    </p>
                </DocFeature>
            </DocSection>

            <DocSection
                id="agendamento"
                title="06 — Agendamento após a publicação finalizada"
                subtitle="Se o cumprimento gerou uma próxima tarefa no processo, e qual"
                tone="violet"
            >
                <p>
                    Para cada publicação <strong>cumprida no período</strong>, o dashboard procura no mesmo processo o
                    primeiro agendamento — de <strong>qualquer setor</strong> — criado no dia da conclusão ou depois.
                    Achou: "com agendamento". Não achou (ou a publicação não tem processo): "sem agendamento". O texto
                    no topo da seção resume os dois números e o percentual que teve agendamento.
                </p>
                <DocGrid cols={3}>
                    <DocFeature title="Por atividade" tone="violet" badge="Um valor">
                        <p>A atividade desse primeiro agendamento, entre as que tiveram agendamento.</p>
                    </DocFeature>
                    <DocFeature title="Por setor" tone="violet" badge="Um valor">
                        <p>O setor de destino desse mesmo agendamento.</p>
                    </DocFeature>
                    <DocFeature title="Com × sem agendamento" tone="violet" badge="Pizza">
                        <p>As duas fatias; clicar numa delas mostra só as publicações com (ou sem) agendamento.</p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="violet" icon="target" title="Por que esta seção importa">
                    <p>
                        É a mesma regra da comissão: cumprida <strong>com</strong> agendamento é uma publicação{' '}
                        <Hl tone="ok">certa</Hl>; <strong>sem</strong> agendamento, <Hl tone="danger">errada</Hl> (ver
                        Seção 08).
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="lista"
                title="07 — Lista de publicações"
                subtitle="As publicações recebidas no período, uma por linha"
            >
                <DocChips
                    label="Colunas"
                    items={[
                        { label: '#' },
                        { label: 'Publicação' },
                        { label: 'Status' },
                        { label: 'Leitor' },
                        { label: 'Setor / atividade (NG e RJ)', tone: 'violet' },
                        { label: 'Tribunal / órgão (LA)', tone: 'info' },
                        { label: 'Recebida em' },
                    ]}
                />
                <DocGrid cols={2}>
                    <DocFeature title="Setor / atividade" tone="violet" badge="NG e RJ" framed>
                        <p>
                            O agendamento <strong>mais recente</strong> criado no processo a partir da conclusão, com a
                            situação dele entre parênteses: cumprido, não cumprido, cancelado ou em andamento. Sem
                            agendamento (ou publicação ainda pendente): "SEM AGENDAMENTO".
                        </p>
                    </DocFeature>
                    <DocFeature title="Tribunal / órgão" tone="info" badge="LA" framed>
                        <p>No LA a coluna mostra o tribunal e o órgão da publicação.</p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={3}>
                    <DocFeature title="Ordem" icon="list">
                        <p>Mais recentes, mais antigas (pela data de chegada) ou pelo número da publicação.</p>
                    </DocFeature>
                    <DocFeature title="Compacta × expandida" icon="maximize">
                        <p>
                            A compacta (padrão) mostra só o tipo de documento; a expandida mostra também a matéria
                            embaixo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Paginação" icon="chevrons">
                        <p>10 publicações por página.</p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="08 — Comissionamento"
                subtitle="Quanto cada leitor ganha (ou perde) pelas publicações cumpridas no período"
                tone="ok"
                badge="+R$ 0,20 · −R$ 0,50"
            >
                <Formula>Comissão do leitor = (certas × R$ 0,20) − (erradas × R$ 0,50)</Formula>
                <DocGrid cols={2}>
                    <DocFeature title="Certa" tone="ok" icon="check-circle" badge="+ R$ 0,20" badgeTone="ok" framed>
                        <p>
                            Cumprida no período <strong>com</strong> um agendamento no mesmo processo, de qualquer
                            setor, criado no dia da conclusão ou depois (a regra da Seção 06).
                        </p>
                    </DocFeature>
                    <DocFeature
                        title="Errada"
                        tone="danger"
                        icon="x-circle"
                        badge="− R$ 0,50"
                        badgeTone="danger"
                        framed
                    >
                        <p>
                            Cumprida no período <strong>sem</strong> nenhum agendamento depois. Desconta do valor — a
                            comissão pode ficar negativa.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={3}>
                    <DocFeature title="Quem recebe" icon="user">
                        <p>
                            O leitor de cada publicação (ou o responsável, quando não há leitor — ver Seção 01).
                            Publicações pendentes não entram.
                        </p>
                    </DocFeature>
                    <DocFeature title="Segue os filtros" icon="filter">
                        <p>O cálculo usa as publicações que sobram depois dos filtros da página.</p>
                    </DocFeature>
                    <DocFeature title="Exemplo" badge="100 lidas" badgeTone="ok">
                        <p>
                            95 certas e 5 erradas: 95 × R$ 0,20 − 5 × R$ 0,50 = <Hl tone="ok">R$ 16,50</Hl>.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Gerar comissão (PDF)" tone="info" icon="shield" badge="Quem gere a unidade">
                        <p>
                            Só quem tem acesso a todos os dashboards da unidade vê o botão. O PDF traz, por leitor:
                            lidas, certas, erradas, valor por certa, valor por errada e a comissão. Para os demais, a
                            comissão nem é enviada pela API.
                        </p>
                    </DocFeature>
                    <DocFeature title="E o mínimo de 98%?" tone="warn" icon="alert" badge="Atenção">
                        <p>
                            O selo "Comissiona" fica no card da Taxa de resolução (Seção 03), calculado sobre o que está
                            filtrado. O valor de cada leitor no PDF é a fórmula acima, sem esse corte.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="09 — Filtros disponíveis"
                subtitle="Como recortar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Período" badge="Calendário" badgeTone="accent">
                        <p>
                            Recebidas pela data de chegada, cumpridas pela data de conclusão. Não muda Pendentes nem
                            Recebidas hoje. O último dia vira o dia de referência.
                        </p>
                    </DocFeature>
                    <DocFeature title="Leitor" badge="Topo + clique · vários" badgeTone="info">
                        <p>
                            Pela janela Filtros ou clicando em Demandas por funcionário. Inclui a opção "Sem leitor". As
                            opções listam os leitores de todo o histórico, sem período nem os outros filtros da página —
                            só o filtro de situação do processo vale aqui.
                        </p>
                    </DocFeature>
                    <DocFeature title="Matéria" badge="Topo + clique · vários" badgeTone="info">
                        <p>Pela janela Filtros ou clicando no gráfico de matérias.</p>
                    </DocFeature>
                    <DocFeature title="Documento, Tribunal, Órgão" badge="Clique · um valor" badgeTone="neutral">
                        <p>Clicando nos gráficos da Seção 05. Clicar em outro valor troca o anterior.</p>
                    </DocFeature>
                    <DocFeature
                        title="Atividade, Setor, Com/sem agendamento"
                        badge="Clique · um valor"
                        badgeTone="violet"
                    >
                        <p>
                            Clicando nos gráficos da Seção 06. Deixam só as publicações cumpridas no período que se
                            encaixam — os outros números da página passam a olhar só para elas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Situação do processo" badge="Ativo · Suspenso · Arquivado" badgeTone="neutral">
                        <p>
                            Sem escolha, entram publicações de processos em qualquer situação (e as sem processo).
                            Escolhendo, ficam só as de processos nas situações marcadas.
                        </p>
                    </DocFeature>
                </DocGrid>
                <p>
                    Os filtros se combinam entre si: cada um recorta o que sobrou do anterior em todo o{' '}
                    <DashLink dashboard="publicacoes">dashboard de Publicações</DashLink>.
                </p>
            </DocSection>
        </DocPage>
    )
}
