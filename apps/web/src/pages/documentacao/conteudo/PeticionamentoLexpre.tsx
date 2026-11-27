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
    DocRelation,
    DocSection,
    DocTable,
    Formula,
    Hl,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Peticionamento (LexPre). Texto da v1: LexHub/src/pages/documentacao/Peticionamento_Lexpre_NG.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'represados', label: 'Represados e retornos' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'tempo', label: 'Tempo de confecção' },
    { id: 'rankings', label: 'Por funcionário' },
    { id: 'tendencia', label: 'Tendência' },
    { id: 'materias', label: 'Por matéria' },
    { id: 'comissao', label: 'Comissionamento' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

// Faixas de comissão por taxa de resolução (Passo 2A e 2B).
const MASSA_TIERS: [string, string][] = [
    ['≥ 98%', 'R$ 3,00'],
    ['≥ 85%', 'R$ 1,50'],
    ['≥ 70%', 'R$ 0,50'],
    ['< 70%', 'R$ 0,00'],
]

const ESPECIFICA_TIERS: [string, string][] = [
    ['≥ 95%', 'R$ 20,00'],
    ['≥ 85%', 'R$ 13,00'],
    ['≥ 50%', 'R$ 7,00'],
    ['< 50%', 'R$ 0,00'],
]

export function PeticionamentoLexpreDoc() {
    return (
        <DocPage
            title="Peticionamento (LexPre)"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Peticionamento a partir da nova base de
                    dados (banco <Code>lexpre</Code>). A lógica de negócio é a mesma do dashboard legado (represados,
                    confeccionados, comissão por faixas), mas a fonte dos dados mudou: em vez de uma tabela com uma
                    linha por processo, o lexpre registra cada movimentação de setor como um evento de log — exatamente
                    como no dashboard de{' '}
                    <DocLink to="org-documentos-lexpre">Organização de Documentos (LexPre)</DocLink>.{' '}
                    <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Escopo multi-unidade & fórmula por faixas">
                    <p>
                        Este guia vale para o{' '}
                        <DashLink dashboard="peticionamento-lexpre">Peticionamento (LexPre)</DashLink> em todas as
                        unidades (troque a unidade no seletor da barra lateral): mesma query, mesma fórmula de comissão
                        por faixas e as mesmas regras descritas abaixo.
                    </p>
                    <DocGrid>
                        <DocMini label="Única diferença entre unidades">
                            O escritório (<Code>escritorio_id</Code>) pelo qual os dados são filtrados.
                        </DocMini>
                        <DocMini label="Bloco de setor no log">
                            Peticionamento é o <Hl mono>id 4</Hl> no NGAM, o{' '}
                            <Hl tone="info" mono>
                                id 12
                            </Hl>{' '}
                            no LAAM e o{' '}
                            <Hl tone="violet" mono>
                                id 157
                            </Hl>{' '}
                            no LARJ — o backend já reconhece os blocos, então nenhum conceito muda de um escritório pro
                            outro.
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
                <p>
                    No banco antigo (<Code>ng</Code>), cada processo tinha uma linha só, com colunas{' '}
                    <Code>ENTRADA</Code>, <Code>DATA_CONFECCAO</Code> e <Code>STATUS</Code>. No lexpre não existe mais
                    essa tabela: toda vez que uma demanda entra ou sai de um setor, o sistema grava um evento na tabela{' '}
                    <Code>log_setor_demanda</Code> — o mesmo log usado pelo dashboard de Organização de Documentos, aqui
                    recortado para o setor "Peticionamento". O dashboard reconstrói entradas, saídas e o "estado atual"
                    da demanda a partir desses eventos.
                </p>
                <DocRelation
                    cardinality="→"
                    caption="como um evento é lido"
                    left={{
                        name: 'SAÍDA de um setor',
                        tone: 'warn',
                        children: 'ex.: sai da Organização de Documentos',
                    }}
                    right={{
                        name: 'ENTRADA no próximo setor',
                        tone: 'info',
                        children: 'ex.: entra em Peticionamento',
                    }}
                />
                <DocGrid cols={3}>
                    <DocFeature title="Peticionado" tone="ok" icon="check-circle" badge="Destino Protocolo" framed>
                        <p>
                            Só conta como <strong>"peticionado"</strong> a saída do setor cujo destino é o{' '}
                            <strong>Protocolo</strong>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Devolvida" tone="warn" icon="undo" badge="Pendências / Org Doc" framed>
                        <p>
                            Uma demanda pode sair do Peticionamento para <strong>qualquer setor</strong>. Saída para
                            Pendências ou Organização de Documentos é a demanda sendo <strong>devolvida</strong> (algo
                            precisa ser resolvido antes), não uma confecção concluída — entra nos cards "Retorno
                            Pendência" e "Retorno Org Doc" (Seção 02).
                        </p>
                    </DocFeature>
                    <DocFeature title="Última saída" tone="info" icon="history" badge="Uma por demanda" framed>
                        <p>
                            Uma demanda pode sair do setor mais de uma vez. O dashboard usa sempre a{' '}
                            <strong>última saída</strong>; se ela voltou e está represada de novo, a saída antiga não
                            conta nem como peticionada nem como retorno — só aparece em "Não Peticionados".
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature title="Peticionados" tone="accent" badge="Filtro de datas">
                        <p>
                            Demandas com um evento de <em>saída</em> do setor Peticionamento, com destino Protocolo,
                            dentro do período selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Não Peticionados e retornos" tone="info" badge="Sem filtro de datas">
                        <p>
                            Olham o estado atual da demanda no banco (ou contam eventos de devolução), não um recorte de
                            período — por isso não mudam com o filtro de datas.
                        </p>
                    </DocFeature>
                </DocGrid>
                <DocCallout icon="layers" title="Números somados com o Peticionamento legado">
                    <p>
                        Os indicadores do período juntam o banco <Code>lexpre</Code> e o Peticionamento legado da
                        unidade (o subtítulo da seção no dashboard diz qual fonte entrou):
                    </p>
                    <ul>
                        <li>
                            <strong>Sem peticionados no LexPre no período:</strong> os cards vêm inteiros do legado
                            (volume, fila, tempos e valores); as devoluções continuam do LexPre.
                        </li>
                        <li>
                            <strong>Com peticionados nos dois:</strong> Total, Manual, Automático e Valor Confeccionado{' '}
                            <strong>somam</strong>; Ticket Médio é refeito (valor somado ÷ peticionados somados) e os
                            tempos viram a média ponderada pelos peticionados de cada base. Não Peticionados,
                            Cancelados, Protocolados e devoluções ficam só do LexPre, e os comparativos "vs mês
                            anterior" também.
                        </li>
                        <li>
                            <strong>Peticionados Mês a Mês:</strong> une as duas séries; no mês em que as duas têm dado,
                            vale o do LexPre.
                        </li>
                    </ul>
                    <p>
                        Os gráficos por funcionário, por matéria e a <strong>comissão</strong> são calculados só com o
                        LexPre.
                    </p>
                </DocCallout>
            </DocSection>

            <DocSection
                id="represados"
                title="02 — Não Peticionados e retornos (acumulado total)"
                subtitle="Sempre o total atual — não dependem do filtro de datas"
                badge="Foto de agora"
            >
                <DocCallout icon="info" title="Estoque atual e devoluções">
                    <p>
                        Esses contadores mostram o estoque atual de trabalho e para onde as demandas foram devolvidas.
                        Eles não mudam com o filtro de datas — refletem sempre a situação de agora.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        name="Não Peticionados (Represados)"
                        icon="fileText"
                        what="Total de demandas que estão hoje no setor Peticionamento, aguardando confecção."
                        counts="Demandas (não canceladas) cujo setor atual é Peticionamento, uma por demanda."
                        calc="Contagem direta das demandas ainda no setor. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado."
                        caveat="Como os retornos, não é afetado pelo filtro de período — mostra sempre o total atual. Quando o período não tem peticionados no LexPre, o número vem do Peticionamento legado (ver Seção 01)."
                    />
                    <MetricCard
                        name="Retorno Org Doc"
                        icon="flow"
                        what="Demandas devolvidas do Peticionamento para Organização de Documentos."
                        counts="Eventos de saída do setor cuja movimentação pareada tem destino Organização de Documentos."
                        calc="Contagem dos eventos de saída identificados com destino Organização de Documentos (não deduplicado: cada devolução conta)."
                        interpret="Volumes altos podem indicar que documentos chegam incompletos ou incorretos ao Peticionamento, exigindo reorganização."
                        caveat="O valor do card é sempre o total (não muda com o filtro de datas); o comparativo “vs mês anterior” conta só as devoluções ocorridas no período selecionado contra o mesmo recorte do mês anterior (aumento aparece em vermelho)."
                    />
                    <MetricCard
                        name="Retorno Pendência"
                        icon="flow"
                        what="Demandas devolvidas do Peticionamento para Pendências."
                        counts="Eventos de saída do setor cuja movimentação pareada tem destino Pendências."
                        calc="Contagem dos eventos de saída identificados com destino Pendências (não deduplicado: cada devolução conta)."
                        interpret="Retornos frequentes podem indicar pendências que surgem durante a confecção e precisam ser resolvidas antes de prosseguir."
                        caveat="O valor do card é sempre o total (não muda com o filtro de datas); o comparativo “vs mês anterior” conta só as devoluções ocorridas no período selecionado contra o mesmo recorte do mês anterior (aumento aparece em vermelho)."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="periodo"
                title="03 — Indicadores do período"
                subtitle="O que saiu do setor dentro do intervalo de datas selecionado"
                tone="ok"
                badge="Data de saída"
            >
                <DocCallout icon="calendar" title="Filtrados pela data do evento de saída">
                    <p>
                        Estes contadores usam a data do evento de saída do setor para filtrar — mostram apenas as
                        demandas que saíram de Peticionamento dentro do período selecionado no dashboard.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        name="Peticionados Manualmente"
                        icon="check"
                        what="Demandas confeccionadas por um funcionário de forma manual."
                        counts="Demandas não canceladas, com peticionamento automático desativado (pet_auto = falso), que saíram do setor no período."
                        calc="Contagem das saídas do setor no período com pet_auto = falso."
                        interpret="Representa o trabalho manual do setor. É a base do comissionamento por funcionário."
                    />
                    <MetricCard
                        name="Peticionados Automaticamente"
                        icon="check"
                        what="Demandas peticionadas de forma automática pelo sistema."
                        counts="Demandas não canceladas, com peticionamento automático ativado (pet_auto = verdadeiro), que saíram do setor no período."
                        calc="Contagem das saídas do setor no período com pet_auto = verdadeiro."
                        interpret="Automações ajudam a aumentar o volume processado sem sobrecarregar a equipe."
                    />
                    <MetricCard
                        name="Total Peticionados"
                        icon="fileText"
                        what="Soma de todas as demandas confeccionadas no período — tanto manuais quanto automáticas."
                        counts="Demandas não canceladas que saíram do setor no período."
                        calc="Peticionados Manualmente + Peticionados Automaticamente."
                        interpret="Indica o volume total produzido no período. Use para comparar períodos e medir a capacidade do setor."
                        caveat={`O card também mostra "Protocolados" (linha secundária): das demandas que passaram pelo Peticionamento, quantas de fato protocolaram dentro do período (data de protocolo no período e status atual "Aguardando Despacho Inicial") — não é a mesma coisa que "confeccionada", já que uma demanda pode sair do Peticionamento num mês e só protocolar em outro (ou nunca).`}
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="xCircle"
                        what="Demandas canceladas que saíram do setor no período."
                        counts="Saídas do setor no período com status Cancelado — usa as saídas sem o filtro de destino Protocolo, já que um cancelamento não tem destino pareado."
                        calc="Contagem direta das saídas canceladas no período."
                        interpret="Ajuda a identificar se o cancelamento está concentrado em algum período."
                    />
                    <MetricCard
                        name="Taxa de Resolvidos"
                        icon="pieChart"
                        what="Gráfico de pizza com a proporção entre resolvidos e não resolvidos."
                        counts="Resolvidos = Total Peticionados do período; Não Resolvidos = Não Peticionados (demandas atualmente no setor, sem filtro de período)."
                        calc="Resolvidos ÷ (Resolvidos + Não Resolvidos), e o complemento para Não Resolvidos."
                        interpret="Quanto maior a fatia de resolvidos, menor a fila do setor em relação ao que foi produzido no período."
                    />
                    <MetricCard
                        name="Valor Confeccionado"
                        icon="dollar"
                        what="Soma do valor de causa das demandas confeccionadas no período."
                        counts="Valor de causa das demandas peticionadas (não canceladas) no período. Para matéria ANP, usa o valor do dano moral."
                        calc="Soma direta do valor de causa de cada demanda confeccionada no período."
                        interpret="Indica o volume financeiro que passou pelo setor no período."
                    />
                    <MetricCard
                        name="Ticket Médio"
                        icon="dollar"
                        what="Valor de causa médio por demanda confeccionada no período."
                        counts="Mesma base do card Valor Confeccionado."
                        calc="Valor Confeccionado ÷ Total Peticionados."
                        interpret="Útil para entender o perfil de valor das demandas que o setor está confeccionando."
                    />
                </DocGrid>
                <DocNote date="04/09/2026">
                    <strong>Card de Revisão substituído por Cancelados:</strong> o lexpre não tem hoje um status
                    equivalente a "Revisão" do dashboard legado, então o card placeholder foi substituído por
                    "Cancelados" (que já existia como conceito, só não tinha um card dedicado até então). Exceção:
                    quando os números do período vêm inteiros do legado, o card volta a ser <strong>Revisão</strong>{' '}
                    (total atual do legado), como na página antiga.
                </DocNote>
                <DocFeature title="Reajuizamento" tone="violet" badge="Cards próprios">
                    <p>
                        As demandas marcadas como reajuizamento aparecem só no resumo de reajuizamento do setor —{' '}
                        <strong>Peticionados</strong> (no período) e <strong>Não peticionados</strong> (agora). Elas{' '}
                        <strong>não entram</strong> nos totais nem na comissão.
                    </p>
                </DocFeature>
            </DocSection>

            <DocSection id="tempo" title="04 — Tempo de confecção" subtitle="Quanto tempo uma demanda fica no setor">
                <DocGrid cols={2}>
                    <DocFeature title="Tempo Médio / Mediana Peticionado" tone="accent" badge="Entrada → saída">
                        <p>
                            Diferença entre o evento de entrada no setor e o evento de saída, para as demandas
                            confeccionadas (não canceladas) no período. Quando uma demanda entra mais de uma vez no
                            setor (por causa de um retorno), usa-se sempre a <strong>entrada mais recente</strong> antes
                            da saída.
                        </p>
                    </DocFeature>
                    <DocFeature title="Comparativo (média e mediana)" tone="info" badge="vs mês anterior">
                        <p>
                            Variação percentual do tempo médio e da mediana de confecção do período selecionado contra o
                            mesmo recorte de dias no mês civil anterior — menor tempo é melhor.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="rankings"
                title="05 — Por funcionário"
                subtitle="Distribuição do trabalho e atribuição de responsabilidade"
            >
                <DocCallout icon="users" title="De quem é cada demanda confeccionada?">
                    <p>
                        O lexpre registra o responsável no momento em que a demanda <em>entra</em> no setor; o evento de
                        saída normalmente não traz responsável. Por isso, para todo gráfico "por funcionário" (e para a
                        comissão), o dashboard usa o responsável da <strong>última entrada</strong> da demanda no setor
                        antes da saída — ou o da própria saída, quando ela traz um.
                    </p>
                </DocCallout>
                <DocGrid cols={3}>
                    <DocFeature title="Demandas por Funcionário" tone="accent" badge="Empilhado">
                        <p>
                            Não Peticionados (estoque atual), Peticionados (saíram do setor no período, por DATA de
                            saída, manuais + automáticos) e Protocolados (confecções <strong>manuais</strong> que de
                            fato protocolaram no período, por DATA de protocolo — o mesmo critério da comissão, ajuste
                            de 01/10/2026), por funcionário responsável. Os dois recortes de data são diferentes, então
                            "Peticionados" e "Protocolados" não necessariamente se referem às mesmas demandas; o
                            frontend usa <Code>Math.max(0, ...)</Code> ao empilhar para evitar uma fatia negativa no
                            caso raro de "mais protocolado que peticionado" no mesmo recorte.
                        </p>
                    </DocFeature>
                    <DocFeature title="Média de Peticionado por Funcionário" tone="info" badge="Por dia">
                        <p>
                            Divide o total de confeccionados pelo número de dias distintos com saídas atribuídas a esse
                            funcionário. Permite comparar produtividade levando em conta dias trabalhados.
                        </p>
                    </DocFeature>
                    <DocFeature title="Valor de Causa por Funcionário" tone="ok" badge="Empilhado">
                        <p>
                            Valor de causa das demandas confeccionadas (por DATA de saída) e, separadamente, a fatia já
                            protocolada (por DATA de protocolo dentro do período — ajuste de 07/10/2026). Para matéria
                            ANP, usa o campo de dano moral; para as demais, usa o valor de causa da demanda.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="06 — Tendência" subtitle="Evolução ao longo do tempo">
                <DocGrid cols={3}>
                    <DocFeature title="Produção Diária" tone="accent" badge="Dia da saída">
                        <p>
                            Linha com as demandas confeccionadas agrupadas por dia do evento de saída. Útil para
                            identificar picos e vales de produtividade dentro do período selecionado.
                        </p>
                    </DocFeature>
                    <DocFeature title="Não Peticionados por Mês" tone="info" badge="Mês da entrada">
                        <p>
                            Agrupa as demandas ainda represadas pelo mês em que entraram no setor pela última vez —
                            ajuda a identificar se o estoque parado é recente ou antigo.
                        </p>
                    </DocFeature>
                    <DocFeature title="Peticionados Mês a Mês" tone="ok" badge="Ano a ano">
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
                        <Code>JUROS_ABUSIVOS</Code>, <Code>ANP</Code>, <Code>ESPECÍFICA</Code>) — já normalizada, sem o
                        sufixo livre que existia no banco antigo. ESPECÍFICA é tratada separadamente no comissionamento
                        (Seção 08).
                    </p>
                </DocCallout>
                <DocGrid cols={2}>
                    <DocFeature title="Top 10 – Peticionados por Matéria" tone="accent" badge="No Setor · Protocolados">
                        <p>
                            Agrupa as demandas confeccionadas no período pela rubrica. O botão de alternância mostra "No
                            Setor" (saíram do Peticionamento no período, por DATA de saída) ou "Protocolados" (de fato
                            protocolaram no período, por DATA de protocolo — ver Seção 08); como os dois usam recortes
                            de data diferentes, uma demanda pode aparecer em um período de "No Setor" e só aparecer em
                            "Protocolados" num período posterior (ou nunca).
                        </p>
                        <p>
                            Clicar numa matéria filtra a página; clicar num <strong>pacote de rubricas reunidas</strong>{' '}
                            abre a lista das rubricas de cada demanda do pacote, em vez de filtrar.
                        </p>
                    </DocFeature>
                    <DocFeature title="Top 10 – Não Peticionados por Matéria" tone="info" badge="Estoque atual">
                        <p>
                            Agrupa as demandas represadas (sem filtro de período) pela rubrica. Útil para priorizar
                            quais tipos de demanda têm maior acúmulo.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="08 — Comissionamento"
                subtitle="Como o sistema calcula a comissão de cada funcionário"
                tone="ok"
                badge="Só confecção manual"
            >
                <DocCallout icon="dollar" title="Mesma fórmula por faixas do dashboard legado">
                    <p>
                        A comissão incide apenas sobre as <strong>confecções manuais</strong> (peticionamento automático
                        não gera comissão), separando matérias ESPECÍFICA (e a operação Administrativo) das demais
                        (chamadas de Massa). O valor unitário de cada faixa depende da{' '}
                        <strong>taxa de resolução geral</strong> do funcionário — não é filtrado pela matéria
                        selecionada na página.
                    </p>
                </DocCallout>
                <DocFeature title="Passo 1 — Taxa de resolução do funcionário" tone="accent" badge="Geral">
                    <Formula>
                        Taxa = Peticionadas no período já protocoladas ÷ (Peticionadas no período já protocoladas +
                        Represados atuais) × 100
                    </Formula>
                    <p>
                        Essa taxa reflete a produtividade GERAL do funcionário (todas as matérias, manual + automático)
                        — não muda quando a página está filtrada por uma matéria específica.
                    </p>
                    <p>
                        <strong>Numerador (desde 04/09/2026):</strong> das demandas que saíram do Peticionamento rumo ao
                        Protocolo no período (pela <strong>data de saída</strong>), conta só as que de fato chegaram a
                        ser protocoladas (status atual "Aguardando Despacho Inicial") — mesmo critério usado no Org
                        Documentos. Uma demanda pode sair "peticionada" do setor e nunca chegar a ser protocolada
                        (parada no Protocolo, cancelada depois etc.) — essa demanda não entra no numerador.{' '}
                        <strong>Denominador:</strong> soma as demandas do funcionário que estão hoje represadas no
                        setor. A taxa continua ancorada na data de saída; só a <em>quantidade paga</em> (Passo 3) usa a
                        data de protocolo.
                    </p>
                </DocFeature>
                <DocGrid cols={2}>
                    <DocFeature title="Passo 2A — Ações de Massa" tone="info" icon="layers" badge="Massa" framed>
                        <p>Qualquer matéria exceto ESPECÍFICA/Administrativo.</p>
                        <DocTable head={['Taxa de resolução', 'Valor por ação manual']} rows={MASSA_TIERS} />
                    </DocFeature>
                    <DocFeature title="Passo 2B — Ações ESPECÍFICA" tone="violet" icon="star" badge="ESPECÍFICA" framed>
                        <p>
                            Rubrica (normalizada) <Code>ESPECÍFICA</Code>, ou rubrica da operação{' '}
                            <Code>Administrativo</Code> (ex.: progressões e gratificações de servidor público) — tabela
                            própria, com valores maiores.
                        </p>
                        <DocTable head={['Taxa de resolução', 'Valor por ação manual']} rows={ESPECIFICA_TIERS} />
                    </DocFeature>
                </DocGrid>
                <DocFeature title="Passo 3 — Comissão total do funcionário" tone="ok" badge="Soma das duas">
                    <Formula>
                        <div>Subtotal Massa = Valor Massa × Qtd de ações Massa manuais</div>
                        <div>Subtotal ESPECÍFICA = Valor ESPECÍFICA × Qtd de ações ESPECÍFICA manuais</div>
                        <div>Comissão total = Subtotal Massa + Subtotal ESPECÍFICA</div>
                    </Formula>
                    <p>
                        Exemplo: funcionário com taxa 90%, 80 ações de Massa e 5 ESPECÍFICA no período → (80 × R$1,50) +
                        (5 × R$13,00) = R$120,00 + R$65,00 = <Hl tone="ok">R$185,00</Hl>.
                    </p>
                </DocFeature>
                <DocNote date="01/10/2026">
                    <strong>A quantidade paga mudou de "peticionado" para "protocolado":</strong> antes, "Qtd de ações
                    Massa/ESPECÍFICA manuais" contava qualquer confecção manual que SAIU do Peticionamento no período
                    (mesmo que ainda não tivesse protocolado). Agora só conta as que de fato PROTOCOLARAM — e o período
                    passou a ser definido pela <strong>data de protocolo</strong>, não mais pela data de saída do
                    Peticionamento. Uma ação peticionada no fim de um mês, mas que só protocola no mês seguinte, agora é
                    paga no mês em que ela REALMENTE protocolou.
                </DocNote>
                <DocCallout
                    tone="warn"
                    icon="alert"
                    title='Por que a soma da comissão é bem menor que o card "Protocolados"?'
                >
                    <p>
                        Desde 07/10/2026 o card e a comissão usam o mesmo recorte (data de protocolo dentro do período e
                        status "Aguardando Despacho Inicial"), mas o card conta confecções manuais{' '}
                        <strong>e automáticas</strong> — a comissão só paga a fatia manual. Em setembro/2026, por
                        exemplo, ~74% dos ~335 "Protocolados" do card eram confecção automática (nunca gera comissão).
                    </p>
                </DocCallout>
                <DocFeature
                    title='Botão "Gerar comissão (PDF)"'
                    tone="info"
                    icon="shield"
                    badge="Gestor e Desenvolvedor"
                >
                    <p>
                        Gera um PDF com o comissionamento por funcionário do período selecionado (funcionário, taxa de
                        resolução, quantidade e valor de ações Massa/ESPECÍFICA e comissão) — mesmo botão e mesmo
                        formato de PDF do dashboard Peticionamento legado. Só aparece para <strong>Gestor</strong> e{' '}
                        <strong>Desenvolvedor</strong> — mesma permissão do dashboard legado (mais restrita que o botão
                        "Exportar", que também é liberado para Colaborador).
                    </p>
                    <p>
                        Os demais cargos veem só a <strong>própria</strong> linha de comissão, pelo vínculo entre a
                        pessoa e o funcionário no LexPre; sem esse vínculo cadastrado, a comissão aparece vazia.
                    </p>
                </DocFeature>
                <DocFeature title="Fica de fora da comissão" tone="danger" icon="ban" framed>
                    <ul>
                        <li>Peticionamento automático e demandas canceladas.</li>
                        <li>Confecções manuais que ainda não protocolaram, ou que protocolaram fora do período.</li>
                        <li>Demandas de reajuizamento (têm cards próprios).</li>
                        <li>
                            Peticionados do <strong>banco legado</strong> — a comissão é só do LexPre, mesmo quando os
                            cards somam as duas bases.
                        </li>
                    </ul>
                </DocFeature>
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
                            Filtra as demandas confeccionadas pela data do evento de saída do setor. Represados e
                            retornos não são afetados por este filtro.
                        </p>
                    </DocFeature>
                    <DocFeature title="Funcionário" badge="Topo + Clique" badgeTone="info">
                        <p>
                            Restringe a visão a um ou mais funcionários — pelo filtro no topo da página ou clicando
                            diretamente nos gráficos por funcionário.
                        </p>
                    </DocFeature>
                    <DocFeature title="Matéria" badge="Clique no Top 10" badgeTone="ok">
                        <p>
                            Filtra por rubrica (matéria jurídica), pelo seletor no topo ou clicando nos gráficos de Top
                            10 por Matéria. <strong>Não afeta</strong> a taxa de resolução usada no comissionamento.
                        </p>
                    </DocFeature>
                    <DocFeature title="Área de atuação" badge="public.area_atuacao" badgeTone="neutral">
                        <p>
                            Filtra pela operação vinculada à rubrica da demanda (equivalente à "área de atuação" do
                            dashboard legado).
                        </p>
                    </DocFeature>
                    <DocFeature title="UF" badge="customer.uf" badgeTone="neutral" wide>
                        <p>
                            Filtra pelo estado do cliente (<Code>customer.uf</Code>), o mesmo catálogo dos outros
                            dashboards lexpre. Só aparece quando há clientes com UF preenchida na unidade.
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
                    <DocChange status="Não existe" tone="danger" area="Status" title="Sem Revisão no LexPre">
                        <p>
                            O lexpre não tem, hoje, um status equivalente a "Revisão" do banco antigo — o card foi
                            substituído por "Cancelados" (04/09/2026) e só volta quando os números vêm inteiros do
                            legado.
                        </p>
                    </DocChange>
                    <DocChange
                        status="Cards próprios"
                        tone="violet"
                        area="Reajuizamento"
                        title="Reajuizamento separado"
                    >
                        <p>
                            As demandas de reajuizamento ficam fora dos totais e da comissão e aparecem num resumo
                            próprio (peticionados no período e não peticionados agora).
                        </p>
                    </DocChange>
                    <DocChange status="Híbrido" tone="ok" area="Totais" title="Cards somam com o legado" framed>
                        <p>
                            Volume, valor e tempos do período somam o Peticionamento legado da unidade (ver Seção 01); a
                            comissão continua <strong>só do LexPre</strong>.
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
