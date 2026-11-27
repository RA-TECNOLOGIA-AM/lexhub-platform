import {
    Code,
    DashLink,
    DocCallout,
    DocChange,
    DocFeature,
    DocGrid,
    DocLink,
    DocMini,
    DocPage,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia do Protocolo (LexPre). Texto da v1: LexHub/src/pages/documentacao/Protocolo_Lexpre_NG.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'tempo', label: 'Tempo no setor' },
    { id: 'rankings', label: 'Por funcionário' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'materias', label: 'Por matéria' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

export function ProtocoloLexpreDoc() {
    return (
        <DocPage
            title="Protocolo (LexPre)"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Protocolo a partir da nova base de dados
                    (banco <Code>lexpre</Code>), a partir do mesmo log de movimentação de setor usado por{' '}
                    <DocLink to="org-documentos-lexpre">Organização de Documentos</DocLink> e{' '}
                    <DocLink to="peticionamento-lexpre">Peticionamento (LexPre)</DocLink>. A diferença principal: aqui o
                    critério de conclusão é um <strong>status</strong> que a demanda atinge, não o setor para onde ela
                    vai. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Escopo multi-unidade & conclusão por status" badge="R$ 1,00 por protocolado">
                    <p>
                        Este guia vale para o <DashLink dashboard="protocolo-lexpre">Protocolo (LexPre)</DashLink> em
                        todas as unidades (troque a unidade no seletor da barra lateral): mesma query, mesma comissão
                        (R$ 1,00 flat por protocolado) e as mesmas regras descritas abaixo.
                    </p>
                    <DocGrid>
                        <DocMini label="Única diferença entre unidades">
                            O escritório (<Code>escritorio_id</Code>). Cada um tem seu bloco de <Code>setor_id</Code> no
                            log: Protocolo é o <Hl mono>id 5</Hl> no NGAM e o{' '}
                            <Hl tone="info" mono>
                                id 13
                            </Hl>{' '}
                            no LAAM — o backend já reconhece os dois.
                        </DocMini>
                        <DocMini label="Critério de conclusão">
                            A demanda atinge o status <Hl tone="ok">"Aguardando Despacho Inicial"</Hl> — não importa
                            para qual setor ela vai.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Critério de conclusão por status, não por setor de destino"
            >
                <p>
                    Assim como Organização de Documentos e Peticionamento, este dashboard reconstrói entradas e saídas
                    do setor "Protocolo" a partir da tabela <Code>log_setor_demanda</Code> (toda vez que uma demanda
                    entra ou sai de um setor, o sistema grava um evento). A diferença é o critério de conclusão: em vez
                    de checar para qual setor a demanda foi, este dashboard checa o <strong>status</strong> que a
                    demanda atingiu.
                </p>
                <DocCallout tone="warn" icon="flow" title="Por que o critério é diferente aqui?">
                    <p>
                        Depois de protocolada, a demanda é distribuída para a Justiça — não existe um "próximo setor"
                        fixo no sistema para onde ela deveria ir, ao contrário de Organização de Documentos (que sempre
                        segue para Peticionamento) ou Peticionamento (que sempre segue para Protocolo). Por isso, o que
                        marca a conclusão do Protocolo é o <strong>status da demanda</strong> chegar a{' '}
                        <strong>"Aguardando Despacho Inicial"</strong> — o processo foi distribuído e está aguardando a
                        primeira decisão do juiz.
                    </p>
                </DocCallout>
                <DocGrid cols={3}>
                    <DocFeature title="Protocolados" tone="ok" icon="check-circle" badge="Filtro de datas" framed>
                        <p>
                            A <strong>última saída</strong> de cada demanda do setor Protocolo, dentro do período, cuja
                            demanda está com o status "Aguardando Despacho Inicial". Uma por demanda; se ela voltou ao
                            Protocolo, não conta (está represada).
                        </p>
                    </DocFeature>
                    <DocFeature title="Represados" tone="info" icon="clock" badge="Sem filtro de data" framed>
                        <p>
                            Demandas que ainda estão no setor e ainda não atingiram esse status. Olha o estado atual da
                            demanda no banco, não um evento pontual — por isso não muda com o filtro de datas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Devolvidos" tone="danger" icon="undo" badge="Sem filtro de data" framed>
                        <p>
                            Saídas do Protocolo cujo destino (a movimentação pareada) é Peticionamento, Org Doc ou
                            Pendências. Contam no card <strong>"Devolvido p/ &lt;setor&gt;"</strong> — cada devolução
                            conta, mesmo que a demanda depois volte e seja protocolada; mesmo critério de "Devolvido p/
                            Pendência" em Organização de Documentos.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout icon="layers" title="Números somados com o Protocolo legado">
                    <p>
                        Os protocolos da unidade estão nos dois sistemas (o legado até a migração, o LexPre depois). O
                        aviso no topo do dashboard diz qual fonte entrou:
                    </p>
                    <ul>
                        <li>
                            <strong>Sem protocolados no LexPre no período:</strong> volume, valor, ticket, tempos e
                            represados vêm do Protocolo legado. Devoluções continuam do LexPre.
                        </li>
                        <li>
                            <strong>Os dois com protocolados:</strong> Protocolados e Valor de Causa somam; Ticket Médio
                            é recalculado sobre a soma; Média e Mediana de tempo são a média das duas fontes ponderada
                            pelos protocolados. Represados, devoluções e comparativos ficam do LexPre.
                        </li>
                        <li>
                            <strong>Mês a mês:</strong> junta as duas séries — no mês em que as duas têm dado, vale o
                            LexPre (não soma).
                        </li>
                    </ul>
                    <p>
                        Gráficos por funcionário e por matéria e a <strong>comissão</strong> são só do LexPre.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="periodo"
                title="02 — Indicadores do período"
                subtitle="Protocolados, represados, valores e tempos no intervalo selecionado"
                badge="Data de saída"
            >
                <DocCallout icon="calendar" title="Qual data cada card usa?">
                    <p>
                        Os cards de volume e valor usam a data do evento de saída do setor para filtrar — mostram apenas
                        as demandas que saíram do Protocolo dentro do período selecionado. "Represados" é sempre o total
                        atual, independente do período. O comparativo "vs mês anterior" compara com o mesmo recorte de
                        dias um mês civil antes; sem base no mês anterior, um crescimento a partir do zero aparece como
                        +100%.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        name="Protocolados"
                        icon="check"
                        what="Demandas que atingiram o status Aguardando Despacho Inicial no período."
                        counts="A última saída de cada demanda do setor Protocolo, com data no período, cuja demanda está com o status Aguardando Despacho Inicial. Demandas que voltaram ao Protocolo não contam (estão em Represados)."
                        calc="Contagem direta — uma por demanda, mesmo que ela tenha saído do setor mais de uma vez."
                        interpret="Indica o volume total distribuído para a Justiça no período. Use para comparar períodos e medir a capacidade do setor."
                    />
                    <MetricCard
                        name="Represados"
                        icon="xCircle"
                        what="Total de demandas que estão hoje no setor Protocolo, ainda não resolvidas."
                        counts="Demandas (não canceladas) cujo setor atual é Protocolo e cujo status ainda não é Aguardando Despacho Inicial, uma por demanda."
                        calc="Contagem direta das demandas ainda no setor, com status pendente. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado."
                        caveat="É o único indicador que não é afetado pelo filtro de período — mostra sempre o total atual. Não importa se a demanda já foi devolvida e voltou: se ainda não tem o status de conclusão, conta como represada."
                    />
                    <MetricCard
                        name="Valor de Causa Protocolado"
                        icon="dollar"
                        what="Soma do valor de causa das demandas protocoladas no período."
                        counts="Valor de causa das demandas com status Aguardando Despacho Inicial no período. Para matéria ANP, usa o valor do dano moral."
                        calc="Soma direta do valor de causa de cada demanda protocolada no período."
                        interpret="Indica o volume financeiro que foi efetivamente distribuído à Justiça no período."
                    />
                    <MetricCard
                        name="Ticket Médio Protocolado"
                        icon="dollar"
                        what="Valor de causa médio por demanda protocolada no período."
                        counts="Mesma base do card Valor de Causa Protocolado."
                        calc="Valor de Causa Protocolado ÷ Protocolados."
                        interpret="Útil para entender o perfil de valor das demandas que o setor está protocolando."
                    />
                    <MetricCard
                        name="Devolvido p/ Peticionamento / Org Doc / Pendência"
                        icon="undo"
                        what="Demandas devolvidas do Protocolo para um setor anterior, sem ter sido resolvidas."
                        counts="Saídas do setor Protocolo cujo destino (a entrada pareada pelo mesmo evento de movimentação) é Peticionamento, Organização de Documentos ou Pendências."
                        calc="Contagem direta das devoluções por setor de destino — cada devolução conta, mesmo que a mesma demanda seja devolvida mais de uma vez ou seja protocolada depois."
                        interpret="Ajuda a identificar em qual etapa anterior o processo mais volta a precisar de ajuste antes de seguir para o Protocolo."
                        caveat="Valor sempre total, independente do período — mesmo critério de Represados. O comparativo “vs mês anterior” conta só as devoluções ocorridas no período selecionado contra o mesmo recorte do mês anterior (aumento aparece em vermelho)."
                    />
                </DocGrid>
                <DocGrid cols={3}>
                    <DocFeature title="Reajuizamento" tone="violet" badge="Card próprio">
                        <p>
                            As demandas marcadas como reajuizamento aparecem só no card de{' '}
                            <strong>Protocolados/Represados de Reajuizamento</strong> (somado ao reajuizamento do legado
                            NG/RJ quando a página mistura o legado). Elas <strong>não entram</strong> nos totais nem na
                            comissão.
                        </p>
                    </DocFeature>
                    <DocFeature title="Sem card de Cancelados" tone="neutral" badge="Igual ao legado">
                        <p>
                            Uma demanda cancelada é só excluída da contagem de represados, sem um contador dedicado (o
                            legado também não tem esse card em Protocolo).
                        </p>
                    </DocFeature>
                    <DocFeature title="Sem Fator Multiplicador" tone="danger" badge="Outra comissão">
                        <p>
                            A comissão por atingimento de meta anual do legado (com proporcionais AM/PA/PB) é diferente
                            da comissão por protocolado do setor (Seção 05) e depende de metas comerciais anuais que
                            ainda não têm equivalente no lexpre.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection id="tempo" title="03 — Tempo no setor" subtitle="Quanto tempo uma demanda fica no Protocolo">
                <DocGrid cols={2}>
                    <DocFeature title="Média / Mediana de Tempo Protocolado" tone="accent" badge="Entrada → saída">
                        <p>
                            Diferença entre o evento de entrada no setor e o evento de saída, para as demandas
                            protocoladas (status Aguardando Despacho Inicial) no período. Quando uma demanda entra mais
                            de uma vez no setor, usa-se sempre a <strong>entrada mais recente</strong> antes da saída.
                        </p>
                    </DocFeature>
                    <DocFeature title="Comparativo (Média de Tempo)" tone="info" badge="vs mês anterior">
                        <p>
                            Variação percentual do tempo médio no setor do período selecionado contra o mesmo recorte de
                            dias no mês civil anterior.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="rankings"
                title="04 — Por funcionário"
                subtitle="Distribuição do trabalho e atribuição de responsabilidade"
            >
                <DocCallout icon="users" title="De quem é cada demanda protocolada?">
                    <p>
                        O lexpre registra o responsável no momento em que a demanda <em>entra</em> no setor; o evento de
                        saída raramente traz responsável. Por isso, para todo gráfico "por funcionário" sobre demandas
                        protocoladas, vale o responsável da saída quando ela traz um e, senão, o da{' '}
                        <strong>última entrada</strong> da demanda no setor antes da saída. Para os represados, vale o
                        responsável da última entrada no setor.
                    </p>
                </DocCallout>
                <DocGrid cols={3}>
                    <DocFeature title="Demandas por Funcionário" tone="accent" badge="Empilhado">
                        <p>Represados (estoque atual) e Protocolados (no período), por funcionário responsável.</p>
                    </DocFeature>
                    <DocFeature title="Média de Protocolados por Funcionário" tone="info" badge="Por dia">
                        <p>
                            Total de protocolados ÷ número de dias distintos com saídas atribuídas ao funcionário.
                            Compara produtividade levando em conta dias trabalhados.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de Causa por Funcionário" tone="ok" badge="ANP: dano moral">
                        <p>
                            Soma o valor de causa das demandas protocoladas por cada funcionário. Para matéria ANP, usa
                            o dano moral; para as demais, o valor de causa da demanda.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="05 — Comissionamento"
                subtitle="Como o sistema calcula a comissão de cada funcionário"
                tone="ok"
                badge="R$ 1,00 por protocolado"
            >
                <Formula>Comissão = R$ 1,00 × Qtd de protocolados</Formula>
                <p>
                    Mesma fórmula do dashboard legado (protocolo.py, banco <Code>ng</Code>) — taxa fixa por processo
                    protocolado, sem depender do valor de causa. Diferente da comissão do Org Documentos (que também usa
                    valor de causa), aqui <strong>só a quantidade importa</strong>.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Protocolado" tone="ok" icon="check" framed>
                        <p>
                            Mesmo critério do card "Protocolados" — a demanda atingiu o status "Aguardando Despacho
                            Inicial" (equivalente lexpre do STATUS "DISTRIBUÍDO"/"PROTOCOLADO" do banco legado).
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de causa" tone="danger" icon="minus" framed>
                        <p>
                            <strong>Não entra</strong> no cálculo — a comissão depende só da quantidade de demandas
                            protocoladas pelo funcionário no período.
                        </p>
                    </DocFeature>
                    <DocFeature title="Responsável" tone="info" icon="user" framed>
                        <p>
                            O mesmo funcionário dos outros gráficos "por funcionário" — o responsável da saída ou, sem
                            ele, o da última entrada da demanda no setor antes da saída.
                        </p>
                    </DocFeature>
                    <DocFeature title="Base" tone="accent" icon="calendar" framed>
                        <p>
                            As mesmas demandas do card "Protocolados" (status Aguardando Despacho Inicial), filtradas
                            pela <strong>data de saída</strong> no período selecionado.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Exemplo: 150 protocolados" badge="R$ 1,00 × 150" badgeTone="ok">
                        <p>
                            Comissão = <Hl tone="ok">R$ 150,00</Hl> — independente do valor de causa dessas 150
                            demandas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Fica de fora da comissão" tone="danger" icon="ban" framed>
                        <ul>
                            <li>Demandas de reajuizamento (têm card próprio).</li>
                            <li>
                                Protocolos do <strong>banco legado</strong> — a comissão é só do LexPre, mesmo quando os
                                cards somam as duas bases.
                            </li>
                        </ul>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Gestor e Desenvolvedor" tone="info" icon="shield" badge="Veem todos">
                        <p>
                            Veem a comissão de todos os funcionários e o botão <strong>"Gerar comissão (PDF)"</strong>:
                            funcionário, quantidade de protocolados e comissão do período — mesmo formato do Protocolo
                            legado.
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

            <DocSection id="tendencia" title="06 — Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid cols={3}>
                    <DocFeature title="Produção Diária" tone="accent" badge="Dia da saída">
                        <p>
                            Linha com as demandas protocoladas agrupadas por dia do evento de saída. Útil para
                            identificar picos e vales de produtividade dentro do período.
                        </p>
                    </DocFeature>
                    <DocFeature title="Não Protocolados por Mês" tone="info" badge="Última entrada">
                        <p>
                            Agrupa as demandas ainda represadas pelo mês em que entraram no setor pela última vez —
                            mostra se o estoque parado é recente ou antigo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Protocolados Mês a Mês" tone="ok" badge="Ano a ano">
                        <p>
                            Visão mensal da produção, comparada por ano. Usa o histórico completo, sem recorte de
                            período; os meses anteriores ao LexPre vêm do Protocolo legado.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="materias"
                title="07 — Por matéria"
                subtitle="Distribuição das demandas por tipo de matéria jurídica"
                badge="Rubrica já normalizada"
            >
                <p>
                    No lexpre, a matéria vem diretamente da rubrica cadastrada na demanda — já normalizada, sem o sufixo
                    livre que existia no banco antigo.
                </p>
                <DocGrid cols={2}>
                    <DocFeature title="Top 10 – Protocolados por Matéria" tone="ok" badge="No período">
                        <p>
                            Agrupa as demandas protocoladas no período pela rubrica. Mostra quais tipos de demanda
                            tiveram maior volume de protocolo. Clicar numa matéria filtra a página inteira.
                        </p>
                    </DocFeature>
                    <DocFeature title="Principal pendência" tone="info" badge="Estoque atual">
                        <p>
                            No card "Não protocolados por mês", a matéria com mais demandas represadas (sem filtro de
                            período) — útil para priorizar o tipo de demanda com maior acúmulo.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="08 — Filtros disponíveis"
                subtitle="Como personalizar e cruzar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Período" badge="Data de saída" badgeTone="accent">
                        <p>
                            Filtra as demandas protocoladas pela data do evento de saída do setor. Represados não são
                            afetados.
                        </p>
                    </DocFeature>
                    <DocFeature title="Funcionário" badge="Topo + Clique" badgeTone="info">
                        <p>
                            Restringe a visão a um ou mais funcionários — pelo filtro no topo ou clicando nos gráficos{' '}
                            <em>por funcionário</em>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Matéria" badge="Topo + Clique" badgeTone="ok">
                        <p>
                            Filtra por rubrica (matéria jurídica) — pelo filtro no topo ou clicando no Top 10 por
                            Matéria.
                        </p>
                    </DocFeature>
                    <DocFeature title="UF" badge="customer.uf" badgeTone="neutral">
                        <p>Filtra pelo estado do cliente da demanda.</p>
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
                title="09 — Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe e o motivo de cada decisão"
                tone="danger"
            >
                <DocGrid cols={2}>
                    <DocChange
                        status="Não existe"
                        tone="danger"
                        area="Comissão"
                        title="Sem comissionamento por meta anual"
                    >
                        <p>
                            O Fator Multiplicador e os proporcionais AM/PA/PB do legado dependem de uma meta anual de
                            valor de causa (R$ 240 milhões em 2026) e do pool de comissão da Comercial — nenhum dos dois
                            tem equivalente configurado no <Code>lexpre</Code> ainda.
                        </p>
                    </DocChange>
                    <DocChange status="Em evolução" area="Gráficos" title='Sem gráfico "por Sistema"'>
                        <p>
                            O gráfico "por Sistema" (PJE, ESAJ, ...) não entrou: hoje só existe um sistema cadastrado
                            (PROJUDI), então não traria distribuição útil. Reajuizamento tem card próprio, fora dos
                            totais e da comissão.
                        </p>
                    </DocChange>
                    <DocChange status="Igual ao legado" tone="info" area="Cancelamento" title="Sem card de Cancelados">
                        <p>
                            Uma demanda cancelada ainda no setor é só excluída da contagem de Represados, sem um
                            contador dedicado.
                        </p>
                    </DocChange>
                    <DocChange
                        status="Híbrido"
                        tone="ok"
                        area="Totais"
                        title="Cards somam com o legado, a comissão não"
                        framed
                    >
                        <p>
                            Volume, valor e tempos usam o Protocolo legado da unidade (sozinho ou somado ao LexPre,
                            conforme o período); a comissão continua <strong>só do LexPre</strong>.
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
