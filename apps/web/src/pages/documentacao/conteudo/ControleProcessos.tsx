import {
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

// Guia do Controle de Processos (LexFlow + Protocolo legado + LexPre, NG/LA/RJ). Escrito na V2 a partir do código:
// apps/web/src/pages/dashboards/controle-processos/* (a esteira e as somas ficam no navegador, controle.ts),
// apps/api/src/app/dashboards/controle_processos.py (as chamadas por unidade) e
// apps/api/src/app/analyses/familias/controle_processo.py (as regras de cada número).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'esteira', label: 'Esteira de trabalho' },
    { id: 'extintos', label: 'Extintos e improcedência' },
    { id: 'permanencia', label: 'Tempo por fase' },
    { id: 'subfases', label: 'Fases e subfases' },
    { id: 'filtros', label: 'Filtros' },
]

const FILTERS = [
    {
        name: 'Período (calendário)',
        badge: 'Só parte da página',
        tone: 'accent' as const,
        desc: 'Vale para Protocolados, Arquivados por procedência, extintos, improcedência e para o tempo médio e mediano por fase. As etapas de estoque (Inicial, Recursal, Trânsito em julgado, Execução ativa), o gráfico mês a mês e as subfases mostram o retrato de agora e não mudam com o período.',
    },
    {
        name: 'Situação',
        badge: 'Uma por vez',
        tone: 'info' as const,
        desc: '"Somente ativos" ou "Somente Suspenso/sobrestado". Sem escolha, entram as duas. Não chega ao Protocolo nem à Execução: com "Suspenso/sobrestado", Protocolados e Execução ativa aparecem zerados, porque esses processos são sempre ativos.',
    },
    {
        name: 'UF',
        badge: 'Só NG e RJ',
        tone: 'violet' as const,
        desc: 'Uma ou várias UFs. Vale para a base do controle, para os protocolados (legado e LexPre) e para a Execução. Não vale para os extintos de 2º grau nem para o tempo médio das subfases. No LA o filtro não aparece, porque a rota do LA não separa por UF.',
    },
    {
        name: 'Fase (seletor do gráfico)',
        badge: 'Seção 05',
        tone: 'ok' as const,
        desc: 'Escolhe a fase cujas subfases aparecem no gráfico "Processos por fase / subfase". O botão "Inspecionar subfases" das etapas da esteira escolhe a fase e rola a página até o gráfico.',
    },
]

export function ControleProcessosDoc() {
    return (
        <DocPage
            title="Controle de Processos"
            tags={['NG', 'LA', 'LARJ']}
            note="Dados do LexFlow, do Protocolo legado e do LexPre · sem exportação e sem comissão"
            toc={TOC}
            intro={
                <>
                    Este guia explica o dashboard de Controle de Processos: a esteira que acompanha a carteira desde o
                    protocolo até o arquivamento, os processos extintos, o tempo que cada fase leva e a distribuição por
                    fase e subfase. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="A esteira de um processo" badge="Fase a fase">
                    <p>
                        O processo é <strong>protocolado</strong>, passa pela fase <strong>Inicial</strong> (1º grau),
                        pode subir para a <strong>Recursal</strong> (2º grau), transita em julgado, entra em{' '}
                        <strong>Execução</strong> e termina <strong>arquivado por procedência</strong>. No caminho, uma
                        parte sai antes: os extintos e os arquivados por improcedência.
                    </p>
                    <DocGrid>
                        <DocMini label="Retrato de agora × período">
                            As etapas de estoque mostram <strong>onde os processos estão hoje</strong>. Protocolados,
                            arquivados por procedência, extintos e tempos seguem o <strong>período escolhido</strong>.
                        </DocMini>
                        <DocMini label="O que muda entre unidades">
                            No <Hl mono>LA</Hl> não há filtro de UF. No <Hl mono>LARJ</Hl> vale o mesmo cálculo da NG,
                            com os processos do escritório do RJ. O resto é igual nas três.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Quatro fontes de dados numa página só, e quais processos entram na base"
            >
                <DocChips
                    label="De onde vêm os números"
                    items={[
                        { label: 'LexFlow · controle de processos', tone: 'accent' },
                        { label: 'Protocolo · banco legado', tone: 'info' },
                        { label: 'Protocolo · LexPre', tone: 'info' },
                        { label: 'LexFlow · Execução e Acordos', tone: 'ok' },
                    ]}
                />
                <DocGrid cols={2}>
                    <DocFeature title="Quem entra na base" tone="accent" icon="layers" framed>
                        <p>
                            Os processos do escritório da unidade com situação <strong>Ativo</strong> ou{' '}
                            <strong>Suspenso/sobrestado</strong>. Arquivados não entram (exceto nos extintos de 2º grau,
                            veja a Seção 03).
                        </p>
                    </DocFeature>
                    <DocFeature title="Cada processo uma vez" tone="info" icon="check-circle" badge="NG e RJ" framed>
                        <p>
                            Um processo com várias partes adversas é contado <strong>uma vez só</strong>, e processos
                            sem número (cadastro incompleto no LexFlow) ficam de fora de todas as contas.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="dollar" title="Que valor aparece em cada número?">
                    <p>
                        Em todo o controle, o valor é o <strong>valor de causa</strong> do processo. As exceções são as
                        etapas que vêm de outros dashboards: Protocolados usa o valor de causa protocolado do Protocolo,
                        e Arquivados por procedência usa o <strong>TED</strong> da Execução Condenação.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Sem exportação" tone="neutral" icon="file-down" framed>
                        <p>O dashboard não tem relatório para baixar.</p>
                    </DocFeature>
                    <DocFeature title="Sem comissão" tone="neutral" icon="dollar" framed>
                        <p>Nenhum número desta página entra em comissionamento.</p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="esteira"
                title="02 — Esteira de trabalho"
                subtitle="A base total e as seis etapas, da esquerda para a direita"
            >
                <p>
                    No alto fica a <strong>Base total</strong>: quantos processos a unidade tem hoje e a soma do valor
                    de causa. Sem situação escolhida, o selo mostra "Todos"; com uma escolhida, mostra qual (Ativo ou
                    Suspenso/Sobrestado). Embaixo, as etapas, cada uma com a quantidade e o valor.
                </p>
                <DocGrid>
                    <MetricCard
                        name="01 · Protocolados (período)"
                        icon="inbox"
                        what="Quantos processos foram protocolados no período."
                        counts="Os protocolados do banco legado da unidade somados aos do LexPre (a mesma conta do dashboard Protocolo LexPre)."
                        calc="Soma das duas fontes, em quantidade e em valor de causa protocolado."
                        interpret="É a entrada da esteira: o que começou a andar no período."
                        caveat='Com a situação "Suspenso/sobrestado", aparece zerado.'
                    />
                    <MetricCard
                        name="02 · Fase Inicial (1G)"
                        icon="briefcase"
                        what="Quantos processos estão hoje na fase Inicial."
                        counts="Processos da base cuja fase atual é Inicial."
                        calc="Contagem e soma do valor de causa. Não depende do período."
                        interpret="O estoque de 1º grau."
                        caveat="Embaixo, Inicial indeferida (log): processos da base que, em algum momento, tiveram o status Inicial Indeferida enquanto estavam na fase Inicial — estejam hoje em qualquer fase."
                    />
                    <MetricCard
                        name="03 · Fase Recursal (2G)"
                        icon="scale"
                        what="Quantos processos estão hoje na fase Recursal."
                        counts="Processos da base cuja fase atual é Recursal."
                        calc="Contagem e soma do valor de causa. Não depende do período."
                        interpret="O estoque em turmas e câmaras."
                        caveat="Embaixo, Recurso não provido (log): processos da base que, em algum momento, tiveram o status Recurso Não Provido enquanto estavam na fase Recursal."
                    />
                    <MetricCard
                        name="04 · Trânsito em julgado"
                        icon="clock"
                        what="Quantos processos estão hoje na fase Trânsito em julgado."
                        counts="Processos da base cuja fase atual é Trânsito em julgado."
                        calc="Contagem e soma do valor de causa. Não depende do período."
                        interpret="Processos que já transitaram e aguardam a liquidação."
                    />
                    <MetricCard
                        name="05 · Execução ativa"
                        icon="target"
                        what="Quantos processos estão hoje em execução."
                        counts="O estoque atual dos dashboards Execução Condenação e Execução Acordos, somados."
                        calc="Soma das quantidades e dos valores dos dois dashboards."
                        interpret="O que está em cumprimento e satisfação agora."
                        caveat='Vem dos dashboards de Execução, não da fase do controle. Com a situação "Suspenso/sobrestado", aparece zerado.'
                    />
                    <MetricCard
                        name="06 · Arquivados procedência"
                        icon="check-circle"
                        what="Quantos processos saíram da Execução no período."
                        counts="As saídas da Execução no período, de Condenação e de Acordos."
                        calc="A quantidade soma Condenação e Acordos. O valor (TED) é só o da Condenação, porque o TED só existe lá."
                        interpret="É o fim da esteira: o que foi recebido e arquivado."
                    />
                </DocGrid>
                <DocCallout tone="info" icon="search" title="Inspecionar subfases">
                    <p>
                        Nas etapas Trânsito em julgado, Execução ativa e Arquivados procedência, o link{' '}
                        <strong>Inspecionar subfases</strong> escolhe aquela fase no gráfico da Seção 05 e rola a página
                        até ele. Só aparece quando a fase existe na base.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="extintos"
                title="03 — Extintos e improcedência"
                subtitle="O que saiu da esteira no período, e a carteira líquida"
            >
                <DocGrid>
                    <MetricCard
                        name="Extintos · 1º grau"
                        icon="briefcase"
                        what="Processos com sentença no período, separados em com mérito e sem mérito."
                        counts="Processos da base (com os filtros de situação e UF) com data de sentença dentro do período."
                        calc='"Com mérito" é qualquer resultado de mérito exceto Extinto Sem Mérito; "sem mérito" é o Extinto Sem Mérito. Embaixo, os com mérito por tipo de sentença, do maior para o menor.'
                        interpret="Quanto da carteira de 1º grau teve sentença no período e de que tipo."
                    />
                    <MetricCard
                        name="Extintos · 2º grau"
                        icon="scale"
                        what="Processos com acórdão no período, separados em com mérito e sem mérito."
                        counts="Processos com data de acórdão dentro do período, em todas as situações — inclusive arquivados."
                        calc="Mesma separação do 1º grau, pelo resultado do acórdão. Embaixo, os com mérito por tipo de acórdão."
                        interpret="Quanto da carteira de 2º grau teve acórdão no período."
                        caveat="Não seguem os filtros de situação e UF (como na versão antiga). É a mesma base do painel de extintos do Recursal, mas aqui o valor é o valor de causa inicial."
                    />
                    <MetricCard
                        name="Taxa de provimento"
                        icon="percent"
                        what="Quanto dos acórdãos do período foi positivo."
                        counts="Os acórdãos do painel Extintos · 2º grau."
                        calc="Positivos ÷ total de acórdãos × 100. Positivos: procedente e parcialmente procedente (com ou sem PE), sentença anulada e extinto sem mérito. Improcedente e improcedente por prescrição/decadência ficam fora do numerador."
                        interpret="Aparece como selo no painel de 2º grau."
                    />
                    <MetricCard
                        name="Improcedência"
                        icon="xCircle"
                        what="Processos arquivados por improcedência."
                        counts="Processos da base que estão hoje na fase Arquivado por improcedência e cuja data de ajuizamento cai no período."
                        calc="Contagem e soma do valor de causa."
                        interpret="O que saiu da carteira por perda."
                        caveat="O período aqui olha a data de ajuizamento do processo, não a data do arquivamento."
                    />
                </DocGrid>
                <DocFeature title="Decréscimo na carteira" tone="ok" icon="dollar" badge="Carteira líquida" framed wide>
                    <Formula>
                        Carteira líquida = Valor protocolado − Extintos sem mérito (1º grau) − Extintos sem mérito (2º
                        grau)
                    </Formula>
                    <p>
                        Tudo em valor de causa, no período. Fica <Hl tone="ok">verde</Hl> quando é positiva ou zero e{' '}
                        <Hl tone="danger">vermelha</Hl> quando é negativa — ou seja, quando os extintos sem mérito
                        somaram mais do que o protocolado.
                    </p>
                </DocFeature>
            </DocSection>

            <DocSection
                id="permanencia"
                title="04 — Tempo médio e mediano por fase"
                subtitle="Quanto tempo os processos levam em cada estágio, frente às metas"
            >
                <p>
                    Quatro cartões, cada um com a <strong>média</strong> e a <strong>mediana</strong> lado a lado e a
                    variação em relação ao mesmo recorte de dias do mês anterior (por exemplo, 01/08–20/08 contra
                    01/07–20/07). Subir é ruim: a variação positiva aparece como piora. Os tempos aparecem como duração
                    (ex.: "204d 11h").
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Protocolo" tone="info" icon="clock" badge="Sem meta">
                        <p>
                            No banco legado, da <strong>contratação</strong> até a saída do protocolo. No LexPre, da{' '}
                            <strong>entrada</strong> até a saída da demanda no setor de Protocolo (o LexPre não tem a
                            data de contratação). Com as duas fontes no período, a média é ponderada pela quantidade de
                            cada uma, e a mediana e a variação são da fonte com mais protocolos. O rodapé diz qual fonte
                            foi usada.
                        </p>
                    </DocFeature>
                    <DocFeature title="Fase Inicial" tone="warn" icon="briefcase" badge="Meta 275d">
                        <p>Do ajuizamento até a saída da fase Inicial.</p>
                    </DocFeature>
                    <DocFeature title="Fase Recursal" tone="violet" icon="scale" badge="Meta 135d">
                        <p>Da entrada até a saída da fase Recursal.</p>
                    </DocFeature>
                    <DocFeature title="Fase Execução" tone="ok" icon="target" badge="Meta 210d">
                        <p>Da entrada até a saída da fase de Execução.</p>
                    </DocFeature>
                </DocGrid>
                <DocCallout tone="warn" icon="calendar" title="Quem entra na conta das fases">
                    <p>
                        Só os processos que <strong>saíram da fase dentro do período</strong>, com entrada e saída
                        válidas e a saída não anterior à entrada. Processos que ainda estão na fase não entram. Valem os
                        filtros de situação e UF.
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Metas e régua" tone="accent" icon="target" framed>
                        <p>
                            As metas são a média dos limites do JEC e da Vara Cível. A régua compara a média com a meta:
                            mostra <Hl tone="ok">Dentro da meta</Hl> quando a média é igual ou menor, e{' '}
                            <Hl tone="warn">Acima da meta</Hl> quando passa.
                        </p>
                    </DocFeature>
                    <DocFeature title="Evolução mensal" tone="info" icon="trendingUp" badge="Histórico completo" framed>
                        <p>
                            O gráfico de baixo mostra o tempo médio mês a mês, pelo mês da saída da fase, com a linha da
                            meta. Clique num cartão de fase (ou use o alternador) para trocar a fase, ou em{' '}
                            <strong>Ver todas (3)</strong> para ver as três lado a lado. Não depende do período.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="subfases"
                title="05 — Fases e subfases"
                subtitle="O detalhamento de uma fase, com quantidade, valor e tempo em cada subfase"
            >
                <p>
                    Escolha uma fase no seletor do gráfico <strong>Processos por fase / subfase</strong>. A lista
                    mostra, para cada subfase, a quantidade de processos, o percentual dentro da fase, o valor de causa
                    e o tempo médio na subfase. É o retrato de agora, com os filtros de situação e UF.
                </p>
                <DocCallout tone="warn" icon="alert" title="Como o tempo médio da subfase é estimado">
                    <p>
                        Vem do histórico de movimentações: cada troca de subfase fecha um trecho, e a média usa só os
                        trechos já fechados. O histórico só registra trocas de <strong>fase</strong>, então uma troca de
                        subfase dentro da mesma fase pode ser percebida com atraso — o que pode aumentar o tempo da
                        subfase anterior. Não segue o filtro de UF.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection id="filtros" title="06 — Filtros disponíveis" subtitle="Ficam na janela Filtros, menos a fase">
                <DocGrid>
                    {FILTERS.map((f) => (
                        <DocFeature key={f.name} title={f.name} tone={f.tone} badge={f.badge} badgeMono={false}>
                            <p>{f.desc}</p>
                        </DocFeature>
                    ))}
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
