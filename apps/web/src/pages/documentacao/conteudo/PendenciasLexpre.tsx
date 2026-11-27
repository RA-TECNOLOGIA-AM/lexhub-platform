import {
    Code,
    DashLink,
    DocCallout,
    DocChange,
    DocFeature,
    DocGrid,
    DocLink,
    DocMini,
    DocNote,
    DocPage,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Pendências (LexPre). Texto da v1: LexHub/src/pages/documentacao/Pendencia_Lexpre_NG.tsx.
// Comissionamento: apps/api/src/app/analyses/NG/pendencia_setor_lexpre.py (get_pendencias_comissionamento_por_funcionario).

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'taxas', label: 'Taxas' },
    { id: 'tempo', label: 'Tempo de resolução' },
    { id: 'rankings', label: 'Por funcionário' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'tendencia', label: 'Tendência e origem' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

export function PendenciasLexpreDoc() {
    return (
        <DocPage
            title="Pendências (LexPre)"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Pendências a partir da nova base de dados
                    (banco <Code>lexpre</Code>), a partir do mesmo log de movimentação de setor usado por{' '}
                    <DocLink to="org-documentos-lexpre">Organização de Documentos</DocLink>,{' '}
                    <DocLink to="peticionamento-lexpre">Peticionamento</DocLink> e{' '}
                    <DocLink to="protocolo-lexpre">Protocolo (LexPre)</DocLink>. A diferença principal: uma demanda pode
                    visitar Pendências várias vezes — mas só a <strong>última visita</strong> de cada uma conta nos
                    números do período. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Escopo multi-unidade & regra da última visita">
                    <p>
                        Este guia vale para o <DashLink dashboard="pendencias-lexpre">Pendências (LexPre)</DashLink> em
                        todas as unidades (troque a unidade no seletor da barra lateral): mesma query, mesma fórmula de
                        comissão e as mesmas regras de cancelamento e última visita descritas abaixo.
                    </p>
                    <DocGrid>
                        <DocMini label="Única diferença entre unidades">
                            O escritório (<Code>escritorio_id</Code>). Cada um tem seu bloco de <Code>setor_id</Code> no
                            log: Pendências é o <Hl mono>id 2</Hl> no NGAM e o{' '}
                            <Hl tone="info" mono>
                                id 10
                            </Hl>{' '}
                            no LAAM — o backend já reconhece os dois.
                        </DocMini>
                        <DocMini label="Regra de ouro">
                            Uma demanda pode cair em Pendências várias vezes, mas só a <strong>última visita</strong>{' '}
                            entra nos números do período — inclusive na comissão.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Cada visita ao setor é reconstruída; só a última de cada demanda conta"
            >
                <p>
                    Assim como os outros três dashboards lexpre, este reconstrói entradas e saídas do setor "Pendências"
                    a partir da tabela <Code>log_setor_demanda</Code> (toda vez que uma demanda entra ou sai de um
                    setor, o sistema grava um evento). Cada ida ao setor — uma <strong>visita</strong>, o par entrada +
                    saída — é reconstruída separadamente, mas <strong>só a última visita de cada demanda</strong> entra
                    nos números do período (Total, Resolvidas, Canceladas, taxas, comissão, produção diária).
                </p>
                <DocGrid cols={3}>
                    <DocFeature title="Resolvida" tone="ok" icon="check-circle" framed>
                        <p>
                            É a última visita da demanda, tem um evento de saída do setor e <strong>não</strong> é a
                            visita cancelada.
                        </p>
                    </DocFeature>
                    <DocFeature title="Não Resolvida (aberta)" tone="info" icon="clock" framed>
                        <p>
                            A visita ainda não tem saída do setor (é sempre a última — não dá para reentrar no setor sem
                            fechar a visita atual).
                        </p>
                    </DocFeature>
                    <DocFeature title="Cancelada" tone="danger" icon="x-circle" framed>
                        <p>
                            É a última visita, o status da demanda é "Cancelado", <strong>quem cancelou</strong> é do
                            setor Pendências <strong>e</strong> o <strong>motivo</strong> é um dos aceitos.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout
                    tone="warn"
                    icon="calendar"
                    title="Por que o período usa a data de entrada (e não a de saída)?"
                >
                    <p>
                        Diferente dos outros três dashboards, aqui o período filtra pela data em que a pendência foi{' '}
                        <strong>aberta</strong> (a entrada da visita). Assim uma pendência aberta no período, mas ainda
                        sem solução, também entra no total — é o que torna a Taxa de Não Resolvidos útil mesmo dentro de
                        um recorte de datas, igual ao dashboard antigo.
                    </p>
                    <p>
                        Cancelamento é sempre definitivo, por isso só a última visita pode ser cancelada. Uma visita
                        anterior (seguida de outra ida ao setor) não aparece em nenhuma métrica de período — nem como
                        resolvida, nem como cancelada.
                    </p>
                </DocCallout>
                <DocNote date="18/09/2026">
                    Passou a valer a regra da <strong>última visita</strong>. Antes, cada ida ao setor contava como uma
                    pendência resolvida separada, o que inflava os números quando a mesma demanda saía e voltava a cair
                    em Pendências no mesmo recorte de datas.
                </DocNote>
                <DocNote date="04/09/2026">
                    Cancelamento feito por alguém de <strong>fora da Pendência</strong> (outro setor agindo diretamente
                    na demanda) deixou de contar como "Cancelada". A checagem usa quem de fato executou o evento, contra
                    o cadastro de funcionários alocados no setor Pendências.
                </DocNote>
                <DocNote date="02/10/2026">
                    O <strong>motivo</strong> também passou a valer: só <Hl tone="ok">"Cliente desistiu"</Hl> e{' '}
                    <Hl tone="ok">"Cliente de outro estado"</Hl> contam como cancelamento da Pendência. Com outro motivo
                    (ex.: "Inexistência processual") — ou cancelada fora do setor — a visita que já tem saída conta como{' '}
                    <strong>Resolvida</strong>; sem saída, continua no backlog em aberto.
                </DocNote>
                <DocCallout icon="layers" title="Números somados com o banco legado">
                    <p>
                        As pendências da unidade estão nos dois sistemas (o legado até a migração, o LexPre depois),
                        então os cards somam os dois: volume do período e fila de agora somam direto; taxas e tempos são
                        a <strong>média ponderada</strong> das duas fontes; o "mês a mês" soma mês a mês. Os
                        comparativos "vs mês anterior" vêm do LexPre.{' '}
                        <strong>A comissão não soma: é calculada só com as pendências do LexPre</strong> (ver Seção 06).
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="periodo"
                title="02 — Indicadores do período"
                subtitle="Volume e status das pendências no intervalo selecionado"
                badge="Data de entrada"
            >
                <DocGrid>
                    <MetricCard
                        name="Total de Pendências"
                        icon="layers"
                        what="Quantas pendências foram abertas no período selecionado."
                        counts="Última visita de cada demanda ao setor Pendências, cuja entrada caiu no período — resolvida, cancelada ou ainda em aberto."
                        calc="Contagem direta dessas visitas."
                        interpret="Indica o volume de demandas que precisaram de atenção do setor no período."
                    />
                    <MetricCard
                        name="Pendências Não Resolvidas"
                        icon="xCircle"
                        what="Total de pendências ainda em aberto, agora."
                        counts="Visitas sem evento de saída e não canceladas, somando todo o histórico."
                        calc="Contagem direta do backlog atual — não filtrado por período."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado."
                        caveat="Este e o card de atraso são os únicos que não são afetados pelo filtro de período — mostram sempre o total atual, igual ao dashboard antigo (mesmo critério de 'Represados' dos outros dashboards lexpre)."
                    />
                    <MetricCard
                        name="Pendência Não Resolvida > 5 Dias"
                        icon="alert"
                        what="Pendências em aberto que já passaram do prazo esperado de resolução."
                        counts="Do backlog atual (Não Resolvidas), quantas têm entrada há mais de 5 dias."
                        calc="Diferença entre hoje e a data de entrada de cada pendência aberta, contando as maiores que 5 dias."
                        interpret="Indicador de atraso e possíveis gargalos. Valor sempre total, não filtrado por período."
                    />
                    <MetricCard
                        name="Pendências Resolvidas"
                        icon="check"
                        what="Pendências que foram resolvidas com sucesso no período."
                        counts="Última visita de cada demanda, com entrada no período, cuja saída não foi por cancelamento."
                        calc="Contagem direta das visitas resolvidas com entrada no período."
                        interpret="Quanto maior, melhor — mostra a capacidade de resolução da equipe no período."
                        caveat="Card mostra comparativo (% vs. mesmo recorte um mês civil antes) — adicionado em 08/09/2026, mesma lógica já usada em Org Doc/Peticionamento/Protocolo (LexPre)."
                    />
                    <MetricCard
                        name="Pendências Canceladas"
                        icon="xCircle"
                        what="Pendências canceladas no período."
                        counts="Última visita de cada demanda, com entrada no período, cuja demanda foi cancelada pelo setor Pendências com um motivo aceito."
                        calc="Contagem direta das visitas canceladas com entrada no período."
                        interpret="Ajuda a identificar se o cancelamento está concentrado em algum período."
                        caveat={`Só conta se quem executou o cancelamento pertence ao setor Pendências (04/09/2026) e se o motivo for "Cliente desistiu" ou "Cliente de outro estado" (02/10/2026) — fora disso, a demanda conta como Resolvida.`}
                    />
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Triagem" tone="info" badge="Foto do momento">
                        <p>
                            Número real desde 24/09/2026. No lexpre, Triagem é um <strong>setor à parte</strong> (não um
                            sub-estado de Pendências): o card conta quantas demandas estão com o setor atual = Triagem
                            agora, sem filtro de período — mesmo critério de "Não Resolvidas".
                        </p>
                    </DocFeature>
                    <DocFeature title="Reajuizamento" tone="violet" badge="Cards próprios">
                        <p>
                            As demandas marcadas como reajuizamento aparecem só nos cards{' '}
                            <strong>Não Resolvidas/Resolvidas de Reajuizamento</strong>, somadas ao reajuizamento do
                            legado quando houver. Elas <strong>não entram</strong> nos totais nem na comissão.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="taxas"
                title="03 — Taxas do período"
                subtitle="Resolvidos, não resolvidos e canceladas em relação ao total"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Taxa de Resolvidos" badge="Meta: 85%" badgeTone="ok">
                        <p>Resolvidas ÷ Total de Pendências do período (entrada no período), em percentual.</p>
                    </DocFeature>
                    <DocFeature title="Taxa de Não Resolvidos" badge="Só do recorte" badgeTone="info">
                        <p>
                            Do mesmo grupo (entrada no período), quantas ainda estão em aberto ÷ Total do período.
                            Diferente do card de backlog acumulado, é o "não resolvido" só entre as que abriram neste
                            recorte.
                        </p>
                    </DocFeature>
                    <DocFeature title="Taxa de Canceladas" badge="Máx.: 5%" badgeTone="danger">
                        <p>
                            Canceladas ÷ Total de Pendências do período. Mesmo filtro de setor e motivo do card de
                            Canceladas — só entra no numerador quando a Pendência foi de fato responsável pelo
                            cancelamento.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="tempo"
                title="04 — Tempo de resolução"
                subtitle="Quanto tempo uma pendência leva para ser resolvida"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Média de Tempo Resolvidos" tone="accent" badge="Em dias">
                        <p>
                            Diferença entre a entrada e a saída de cada visita resolvida com entrada no período, e
                            depois a média entre elas. O comparativo (% vs. mesmo recorte um mês antes) tem as cores
                            invertidas — <strong>menor tempo é melhor</strong>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Mediana de Tempo Resolvidos" tone="info" badge="Robusta a extremos">
                        <p>
                            Mesma base da média, mas usando a mediana — uma pendência que ficou muito tempo aberta não
                            distorce o número.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="rankings"
                title="05 — Por funcionário"
                subtitle="Distribuição do trabalho e atribuição de responsabilidade"
            >
                <DocCallout icon="users" title="De quem é cada pendência?">
                    <p>
                        O responsável é o funcionário registrado na própria visita — normalmente o do momento em que a
                        demanda <em>entrou</em> em Pendências (o evento de saída raramente traz responsável; quando
                        traz, vale o da saída). Como cada visita já é um par entrada/saída, não é preciso buscar
                        entradas anteriores, ao contrário dos outros três dashboards.
                    </p>
                </DocCallout>
                <MetricCard
                    name="Média Resolvidas por Funcionário"
                    icon="users"
                    what="Quantas pendências cada funcionário resolve, em média, por dia trabalhado."
                    counts="Pendências resolvidas atribuídas ao funcionário no período."
                    calc="Total de resolvidas do funcionário ÷ número de dias distintos com resoluções no período."
                    interpret="Mostra o ritmo individual contra a meta diária do setor. Clicável: filtra o dashboard inteiro pelo funcionário selecionado."
                />
            </DocSection>

            <DocSection
                id="comissao"
                title="06 — Comissionamento"
                subtitle="Quanto cada funcionário recebe por pendência resolvida, e em que faixa ele cai"
                tone="ok"
                badge="R$ 3 · R$ 1 · R$ 0 por resolvida"
            >
                <Formula>Comissão do funcionário = Pendências resolvidas no período × valor da faixa</Formula>
                <p>
                    A faixa é decidida pelas duas taxas <strong>do próprio funcionário</strong> no período, e o valor
                    dela vale para <strong>todas</strong> as resoluções — não é escalonado (quem cai na faixa de R$ 3
                    recebe R$ 3 por cada uma, desde a primeira).
                </p>
                <DocGrid cols={3}>
                    <DocFeature title="Faixa cheia" tone="ok" icon="star" badge="R$ 3,00 / resolvida" framed>
                        <p>
                            Taxa de resolvido <Hl tone="ok">≥ 97%</Hl> <strong>e</strong> taxa de cancelamento{' '}
                            <Hl tone="ok">&lt; 5%</Hl>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Faixa base" tone="accent" icon="check" badge="R$ 1,00 / resolvida" framed>
                        <p>
                            Taxa de resolvido <Hl>≥ 85%</Hl> (e abaixo da faixa cheia).
                        </p>
                    </DocFeature>
                    <DocFeature title="Sem comissão" tone="danger" icon="minus" badge="R$ 0" framed>
                        <p>
                            Taxa de resolvido <Hl tone="danger">abaixo de 85%</Hl>.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid>
                    <MetricCard
                        name="Taxa de resolvido e taxa de cancelamento (do funcionário)"
                        icon="percent"
                        what="As duas taxas que definem a faixa de comissão de cada funcionário."
                        counts="Só as visitas FECHADAS atribuídas ao funcionário — resolvidas + canceladas — entre as últimas visitas de cada demanda com entrada no período."
                        calc="Taxa de resolvido = resolvidas ÷ (resolvidas + canceladas). Taxa de cancelamento = canceladas ÷ (resolvidas + canceladas). As duas somam 100%."
                        interpret="Visitas ainda abertas não entram na conta: elas ainda não têm desfecho, então não ajudam nem atrapalham a taxa."
                        caveat="Como as duas taxas somam 100%, quem tem ≥ 97% de resolvido já tem no máximo 3% de cancelamento — na prática, a condição de cancelamento < 5% da faixa cheia sempre é cumprida junto."
                    />
                    <MetricCard
                        name="O que conta como resolvida para a comissão"
                        icon="check"
                        what="Quais pendências entram na quantidade multiplicada pelo valor da faixa."
                        counts="As mesmas Resolvidas do card do período: última visita de cada demanda, com entrada no período, com saída do setor e não cancelada pela Pendência."
                        calc={
                            <>
                                Uma demanda cancelada <strong>fora do setor</strong> ou com motivo diferente de "Cliente
                                desistiu"/"Cliente de outro estado" <strong>conta como resolvida</strong> (e entra na
                                comissão) se a visita já tinha saída; sem saída, fica em aberto e fica de fora.
                            </>
                        }
                        interpret="O funcionário só é penalizado (cancelamento na taxa) pelos cancelamentos que são responsabilidade da própria Pendência."
                    />
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Fica de fora da comissão" tone="danger" icon="ban" framed>
                        <ul>
                            <li>Visitas ainda abertas (sem saída do setor).</li>
                            <li>Visitas anteriores da mesma demanda (só a última conta).</li>
                            <li>Demandas de reajuizamento (têm cards próprios).</li>
                            <li>
                                Pendências do <strong>banco legado</strong> — a comissão é só do LexPre, mesmo quando os
                                cards somam as duas bases.
                            </li>
                        </ul>
                    </DocFeature>
                    <DocFeature title="O valor do período pode mudar depois" tone="warn" icon="clock" framed>
                        <p>
                            O período filtra pela <strong>data de entrada</strong>. Uma pendência aberta no mês e
                            resolvida só no mês seguinte entra na comissão do mês em que <strong>abriu</strong> — então
                            a comissão de um período fechado ainda pode subir enquanto houver pendências dele em aberto.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={3}>
                    <DocFeature title="Exemplo: 98 resolvidas, 2 canceladas" badge="98% · 2%" badgeTone="ok">
                        <p>
                            Faixa cheia: 98 × R$ 3,00 = <Hl tone="ok">R$ 294,00</Hl>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Exemplo: 90 resolvidas, 10 canceladas" badge="90% · 10%" badgeTone="accent">
                        <p>
                            Faixa base: 90 × R$ 1,00 = <Hl>R$ 90,00</Hl>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Exemplo: 40 resolvidas, 10 canceladas" badge="80% · 20%" badgeTone="danger">
                        <p>
                            Abaixo de 85%: <Hl tone="danger">sem comissão</Hl>, mesmo com 40 resolvidas.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Gestor e Desenvolvedor" tone="info" icon="shield" badge="Veem todos">
                        <p>
                            Veem a comissão de todos os funcionários e o botão <strong>"Gerar comissão (PDF)"</strong>:
                            funcionário, taxa de resolvido, taxa de cancelamento, resolvidas, R$ por resolvida e
                            comissão do período — mesmo formato do dashboard Pendências legado.
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
                id="tendencia"
                title="07 — Tendência e origem"
                subtitle="Evolução ao longo do tempo e de onde vêm as pendências em aberto"
            >
                <DocGrid cols={3}>
                    <DocFeature title="Produção Diária" tone="accent" badge="Dia da saída">
                        <p>
                            Linha com as pendências resolvidas agrupadas pelo dia do evento de saída, dentro do período
                            — mesmo critério de "última visita de cada demanda" dos cards.
                        </p>
                    </DocFeature>
                    <DocFeature title="Origem das Não Resolvidas" tone="info" badge="Sem período">
                        <p>
                            Agrupa o backlog em aberto (acumulado) pelo setor de onde a demanda veio antes de cair em
                            Pendências — equivalente direto ao campo "Origem" do dashboard antigo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Resolvidas Mês a Mês" tone="ok" badge="Ano a ano">
                        <p>
                            Visão mensal das resoluções, uma linha por ano. Usa o histórico completo, sem recorte de
                            período, para permitir a comparação entre anos.
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
                <DocGrid cols={3}>
                    <DocFeature title="Período" badge="Data de entrada" badgeTone="accent">
                        <p>
                            Filtra as pendências pela data em que foram <strong>abertas</strong>. Não Resolvidas e Não
                            Resolvidas com atraso não são afetadas.
                        </p>
                    </DocFeature>
                    <DocFeature title="Funcionário" badge="Topo + Clique" badgeTone="info">
                        <p>
                            Restringe a visão a um ou mais funcionários — pelo filtro no topo ou clicando no gráfico de{' '}
                            <em>Média por Funcionário</em>.
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
                title="09 — Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe e o motivo de cada decisão"
                tone="danger"
            >
                <DocGrid cols={2}>
                    <DocChange status="Outro setor" tone="info" area="Triagem" title="Triagem é um setor à parte">
                        <p>
                            No lexpre, Triagem é um setor separado (não um sub-estado de Pendências) — o card conta
                            quantas demandas estão lá agora, reaproveitando o mesmo log, sem misturar os dois conceitos.
                        </p>
                    </DocChange>
                    <DocChange status="Regra própria" area="Cancelamento" title="Motivos de cancelamento diferentes">
                        <p>
                            O legado exclui alguns motivos (duplicado, ação inexistente) da taxa de cancelamento. O
                            lexpre faz o caminho inverso: só <strong>"Cliente desistiu"</strong> e{' '}
                            <strong>"Cliente de outro estado"</strong> contam como cancelamento da Pendência.
                        </p>
                    </DocChange>
                    <DocChange
                        status="Não existe"
                        tone="danger"
                        area="Gráficos"
                        title='Sem "Não Resolvidas por Atendente"'
                    >
                        <p>
                            Esse gráfico do legado usa o atendente comercial original da demanda, não o responsável pela
                            pendência — um conceito diferente, e esse dado não está na consulta usada aqui.
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
                            Volume, fila, taxas e mês a mês somam o banco legado da unidade; a comissão continua{' '}
                            <strong>só do LexPre</strong> (o legado tem a própria comissão no dashboard Pendências).
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
