import {
    Code,
    DashLink,
    DocCard,
    DocGrid,
    DocLink,
    DocPage,
    DocSection,
    Formula,
    InfoBox,
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

const FILTERS = [
    {
        name: 'Período (data de saída)',
        desc: 'Filtra as demandas confeccionadas pela data do evento de saída do setor. Represados e retornos não são afetados por este filtro.',
    },
    {
        name: 'Funcionário',
        desc: 'Restringe a visão a um ou mais funcionários específicos — pode ser selecionado pelo filtro no topo da página ou clicando diretamente nos gráficos por funcionário.',
    },
    {
        name: 'Matéria',
        desc: 'Filtra por rubrica (matéria jurídica) — pode ser selecionado clicando diretamente nos gráficos de Top 10 por Matéria. Não afeta a taxa de resolução usada no comissionamento.',
    },
    {
        name: 'Área de atuação',
        desc: 'Filtra pela operação vinculada à rubrica da demanda (equivalente à "área de atuação" do dashboard legado).',
    },
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

function TierTable({ valueLabel, tiers }: { valueLabel: string; tiers: [string, string][] }) {
    return (
        <div className="tblwrap">
            <table className="tbl">
                <thead>
                    <tr>
                        <th>Taxa de resolução</th>
                        <th>{valueLabel}</th>
                    </tr>
                </thead>
                <tbody>
                    {tiers.map(([rate, value], i) => (
                        <tr key={rate}>
                            <td>{rate}</td>
                            <td className={i === tiers.length - 1 ? 'muted' : undefined}>
                                {i === tiers.length - 1 ? value : <strong>{value}</strong>}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export function PeticionamentoLexpreDoc() {
    return (
        <DocPage
            title="Peticionamento (LexPre)"
            tags={['NG', 'LA']}
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Peticionamento a partir da nova base de
                    dados (banco <Code>lexpre</Code>). A lógica de negócio é a mesma do dashboard legado (represados,
                    confeccionados, comissão por faixas), mas a fonte dos dados mudou: em vez de uma tabela com uma
                    linha por processo, o lexpre registra cada movimentação de setor como um evento de log — exatamente
                    como no dashboard de{' '}
                    <DocLink to="org-documentos-lexpre">Organização de Documentos (LexPre)</DocLink>. Nenhum
                    conhecimento técnico é necessário.
                </>
            }
            header={
                <InfoBox>
                    Este guia vale para o <DashLink dashboard="peticionamento-lexpre">Peticionamento (LexPre)</DashLink>{' '}
                    em todas as unidades: mesma query, mesma fórmula de comissão por faixas e as mesmas regras descritas
                    abaixo — a única diferença entre as unidades é o escritório (<Code>escritorio_id</Code>) pelo qual
                    os dados são filtrados (troque a unidade no seletor da barra lateral). Cada escritório tem seu
                    próprio bloco de <Code>setor_id</Code> no log de movimentação (Peticionamento é o id 4 no NGAM e o
                    id 12 no LAAM) — o backend já reconhece os dois blocos ao montar os números de cada unidade, então
                    nenhum conceito explicado aqui muda de um escritório pro outro.
                </InfoBox>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Da tabela de status (banco antigo) para o log de movimentação (lexpre)"
                icon="db"
            >
                <InfoBox>
                    No banco antigo (<Code>ng</Code>), cada processo tinha uma linha só, com colunas{' '}
                    <Code>ENTRADA</Code>, <Code>DATA_CONFECCAO</Code> e <Code>STATUS</Code>. No lexpre não existe mais
                    essa tabela: toda vez que uma demanda entra ou sai de um setor, o sistema grava um evento na tabela{' '}
                    <Code>log_setor_demanda</Code> — o mesmo log usado pelo dashboard de Organização de Documentos, aqui
                    recortado para o setor "Peticionamento". O dashboard reconstrói entradas, saídas e o "estado atual"
                    da demanda a partir desses eventos.
                </InfoBox>
                <DocCard title="Como um evento de log é lido">
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10 }}>
                        <div className="stack" style={{ gap: 4 }}>
                            <span className="badge warn">SAÍDA de um setor</span>
                            <span className="muted small">ex.: sai da Organização de Documentos</span>
                        </div>
                        <span className="muted">→</span>
                        <div className="stack" style={{ gap: 4 }}>
                            <span className="badge info">ENTRADA no próximo setor</span>
                            <span className="muted small">ex.: entra em Peticionamento</span>
                        </div>
                    </div>
                    <p>
                        No sistema, uma demanda pode sair do Peticionamento para <strong>qualquer setor</strong> — não
                        só para o Protocolo. Uma saída para Pendências ou para Organização de Documentos é a demanda
                        sendo <strong>devolvida</strong> (algo precisa ser resolvido antes de prosseguir), não uma
                        confecção concluída. Por isso o dashboard só conta como <strong>"peticionado"</strong> a saída
                        cujo destino é o Protocolo; saídas para Pendências ou Organização de Documentos entram nos cards
                        "Retorno Pendência" e "Retorno Org Doc" — ver a seção seguinte.
                    </p>
                    <p>
                        Além disso, uma demanda pode sair do setor mais de uma vez ao longo do tempo (ex.: é devolvida,
                        o problema é resolvido, e ela volta para ser confeccionada de fato). Por isso o dashboard usa
                        sempre a <strong>última saída</strong> de cada demanda do setor; se a demanda voltou e está
                        represada de novo no setor, essa saída antiga não conta nem como peticionada nem como retorno —
                        só aparece em "Não Peticionados".
                    </p>
                    <p>
                        <strong>Peticionados (filtro de datas):</strong> demandas com um evento de <em>saída</em> do
                        setor Peticionamento, com destino Protocolo, dentro do período selecionado.
                    </p>
                    <p>
                        <strong>Não Peticionados e retornos (não filtrados por data):</strong> olham o estado atual da
                        demanda no banco (ou contam eventos de devolução), não um recorte de período — por isso não
                        mudam com o filtro de datas.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="represados"
                title="Não Peticionados e retornos (acumulado total)"
                subtitle="Sempre o total atual — não dependem do filtro de datas"
                icon="barChart"
            >
                <InfoBox>
                    Esses contadores mostram o estoque atual de trabalho e para onde as demandas foram devolvidas. Eles
                    não mudam com o filtro de datas — refletem sempre a situação de agora.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Não Peticionados (Represados)"
                        icon="fileText"
                        what="Total de demandas que estão hoje no setor Peticionamento, aguardando confecção."
                        counts="Demandas (não canceladas) cujo setor atual é Peticionamento, uma por demanda."
                        calc="Contagem direta das demandas ainda no setor. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado."
                        caveat="É o único indicador que não é afetado pelo filtro de período — mostra sempre o total atual."
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
                title="Indicadores do período"
                subtitle="O que saiu do setor dentro do intervalo de datas selecionado"
                icon="check"
            >
                <InfoBox>
                    Estes contadores usam a data do evento de saída do setor para filtrar — mostram apenas as demandas
                    que saíram de Peticionamento dentro do período selecionado no dashboard.
                </InfoBox>
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
                        icon="barChart"
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
                <InfoBox>
                    <strong>Card de Revisão substituído por Cancelados (04/09/2026):</strong> o lexpre não tem hoje um
                    status equivalente a "Revisão" do dashboard legado, então o card placeholder foi substituído por
                    "Cancelados" (que já existia como conceito, só não tinha um card dedicado até então).
                </InfoBox>
            </DocSection>

            <DocSection
                id="tempo"
                title="Tempo de confecção"
                subtitle="Quanto tempo uma demanda fica no setor"
                icon="trendingUp"
            >
                <DocGrid>
                    <DocCard title="Tempo Médio / Mediana Peticionado">
                        <p>
                            Calculado como a diferença entre o evento de entrada no setor e o evento de saída, para as
                            demandas confeccionadas (não canceladas) no período. Quando uma demanda entra mais de uma
                            vez no setor (por causa de um retorno), usa-se sempre a entrada mais recente antes da saída.
                        </p>
                    </DocCard>
                    <DocCard title="Comparativo (Tempo Médio)">
                        <p>
                            Variação percentual do tempo médio de confecção do período selecionado contra o mesmo
                            recorte de dias no mês civil anterior.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="rankings"
                title="Por funcionário"
                subtitle="Distribuição do trabalho e atribuição de responsabilidade"
                icon="users"
            >
                <InfoBox>
                    O lexpre registra o responsável no momento em que a demanda <em>entra</em> no setor, não em que ela
                    sai. Por isso, para todo gráfico "por funcionário" sobre demandas confeccionadas, o dashboard usa o
                    responsável da última entrada da demanda no setor antes da saída.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Demandas por Funcionário">
                        <p>
                            Gráfico empilhado com Não Peticionados (estoque atual), Peticionados (saíram do setor no
                            período, por DATA de saída) e Protocolados (de fato protocolaram no período, por DATA de
                            protocolo — ajuste de 07/10/2026), por funcionário responsável. Os dois recortes de data são
                            diferentes, então "Peticionados" e "Protocolados" não necessariamente se referem às mesmas
                            demandas; o frontend usa <Code>Math.max(0, ...)</Code> ao empilhar para evitar uma fatia
                            negativa no caso raro de "mais protocolado que peticionado" no mesmo recorte.
                        </p>
                    </DocCard>
                    <DocCard title="Média de Peticionado por Funcionário (por dia)">
                        <p>
                            Divide o total de confeccionados pelo número de dias distintos com saídas atribuídas a esse
                            funcionário. Permite comparar produtividade levando em conta dias trabalhados.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de Causa por Funcionário">
                        <p>
                            Gráfico empilhado: valor de causa das demandas confeccionadas (por DATA de saída) e,
                            separadamente, a fatia já protocolada (por DATA de protocolo dentro do período — ajuste de
                            07/10/2026). Para matéria ANP, usa o campo de dano moral; para as demais, usa o valor de
                            causa da demanda.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo" icon="trendingUp">
                <DocGrid>
                    <DocCard title="Produção Diária">
                        <p>
                            Gráfico de linha com as demandas confeccionadas agrupadas por dia do evento de saída. Útil
                            para identificar picos e vales de produtividade dentro do período selecionado.
                        </p>
                    </DocCard>
                    <DocCard title="Não Peticionados por Mês">
                        <p>
                            Agrupa as demandas ainda represadas pelo mês em que entraram no setor pela última vez —
                            ajuda a identificar se o estoque parado é recente ou antigo.
                        </p>
                    </DocCard>
                    <DocCard title="Peticionados Mês a Mês">
                        <p>
                            Visão mensal da produção, comparando ano a ano (uma linha por ano). Usa o histórico
                            completo, sem recorte de período, para permitir a comparação entre anos.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="materias"
                title="Por matéria"
                subtitle="Distribuição das demandas por tipo de matéria jurídica"
                icon="fileText"
            >
                <InfoBox>
                    No lexpre, a matéria vem diretamente da rubrica cadastrada na demanda (ex.: "JUROS_ABUSIVOS", "ANP",
                    "ESPECÍFICA") — já normalizada, sem o sufixo livre que existia no banco antigo. ESPECÍFICA é tratada
                    separadamente no comissionamento (ver seção seguinte).
                </InfoBox>
                <DocGrid>
                    <DocCard title="Top 10 – Peticionados por Matéria">
                        <p>
                            Agrupa as demandas confeccionadas no período pela rubrica. Mostra quais tipos de demanda
                            tiveram maior volume de confecção. O botão de alternância mostra "No Setor" (saíram do
                            Peticionamento no período, por DATA de saída) ou "Protocolados" (de fato protocolaram no
                            período, por DATA de protocolo — ver "Comissionamento"); como os dois usam recortes de data
                            diferentes, uma demanda pode aparecer em um período de "No Setor" e só aparecer em
                            "Protocolados" num período posterior (ou nunca).
                        </p>
                    </DocCard>
                    <DocCard title="Top 10 – Não Peticionados por Matéria">
                        <p>
                            Agrupa as demandas represadas (estoque atual, sem filtro de período) pela rubrica. Útil para
                            priorizar quais tipos de demanda têm maior acúmulo.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="comissao"
                title="Comissionamento"
                subtitle="Como o sistema calcula a comissão de cada funcionário"
                icon="dollar"
            >
                <InfoBox>
                    Mesma fórmula por faixas do dashboard legado — a comissão incide apenas sobre as confecções manuais
                    (peticionamento automático não gera comissão), separando matérias ESPECÍFICA (e a operação
                    Administrativo) das demais (chamadas de Massa). O valor unitário de cada faixa depende da{' '}
                    <strong>taxa de resolução geral</strong> do funcionário — não é filtrado pela matéria selecionada na
                    página.
                </InfoBox>
                <DocCard title="Passo 1 — Taxa de resolução do funcionário">
                    <Formula>
                        Taxa = Protocolados no período ÷ (Protocolados no período + Represados atuais) × 100
                    </Formula>
                    <p>
                        Essa taxa reflete a produtividade GERAL do funcionário (todas as matérias, manual + automático)
                        — não muda quando a página está filtrada por uma matéria específica.
                    </p>
                    <p>
                        <strong>Protocolados (desde 04/09/2026):</strong> das demandas que passaram pelo Peticionamento
                        no período, conta só as que de fato chegaram a ser protocoladas depois (status atual "Aguardando
                        Despacho Inicial") — mesmo critério de ajuste usado no Org Documentos. Uma demanda pode sair
                        "peticionada" do setor (rumo ao Protocolo) e nunca chegar a ser protocolada de fato (parada no
                        Protocolo, cancelada depois, etc.) — essa demanda não entra no numerador da taxa.
                    </p>
                </DocCard>
                <DocCard title="Passo 2A — Comissão por ações de Massa (qualquer matéria exceto ESPECÍFICA/Administrativo)">
                    <TierTable valueLabel="Valor por ação manual (Massa)" tiers={MASSA_TIERS} />
                </DocCard>
                <DocCard title="Passo 2B — Comissão por ações ESPECÍFICA">
                    <p>
                        Demandas cuja rubrica (normalizada) é <Code>ESPECÍFICA</Code>, ou cuja rubrica pertence à
                        operação <Code>Administrativo</Code> (ex.: progressões e gratificações de servidor público),
                        usam esta tabela própria, com valores maiores:
                    </p>
                    <TierTable valueLabel="Valor por ação manual (ESPECÍFICA)" tiers={ESPECIFICA_TIERS} />
                </DocCard>
                <InfoBox>
                    <strong>Ajuste de 01/10/2026 — quantidade paga mudou de "peticionado" pra "protocolado":</strong>{' '}
                    antes, "Qtd de ações Massa/ESPECÍFICA manuais" contava qualquer confecção manual que SAIU do
                    Peticionamento no período (mesmo que ainda não tivesse protocolado). Agora só conta as que de fato
                    PROTOCOLARAM — e o período passou a ser definido pela <strong>data de protocolo</strong>, não mais
                    pela data de saída do Peticionamento. Uma ação peticionada no fim de um mês, mas que só protocola no
                    mês seguinte, agora é paga no mês em que ela REALMENTE protocolou. Isso é por isso que a soma das
                    quantidades de comissão de todos os funcionários costuma ser BEM menor do que o card "Protocolados"
                    da página: esse card conta qualquer demanda (manual <strong>ou automática</strong>) que saiu do
                    setor no período e já está protocolada hoje — a comissão só paga a fatia manual, com protocolo
                    dentro do período exato. Em setembro/2026, por exemplo, de ~335 "Protocolados" do card, ~74% eram
                    confecção automática (nunca gera comissão) e uma fatia pequena protocolou fora do período — sobrando
                    a quantidade que aparece no PDF.
                </InfoBox>
                <DocCard title="Passo 3 — Comissão total do funcionário">
                    <Formula>
                        <div>Subtotal Massa = Valor Massa × Qtd de ações Massa manuais</div>
                        <div>Subtotal ESPECÍFICA = Valor ESPECÍFICA × Qtd de ações ESPECÍFICA manuais</div>
                        <div>Comissão total = Subtotal Massa + Subtotal ESPECÍFICA</div>
                    </Formula>
                    <p>
                        Exemplo: funcionário com taxa 90%, 80 ações de Massa e 5 ESPECÍFICA no período → (80 × R$1,50) +
                        (5 × R$13,00) = R$120,00 + R$65,00 = <strong>R$185,00</strong>.
                    </p>
                </DocCard>
                <DocCard title='Botão "Gerar comissão (PDF)"'>
                    <p>
                        Gera um PDF com o comissionamento por funcionário do período selecionado (funcionário, taxa de
                        resolução, quantidade e valor de ações Massa/ESPECÍFICA e comissão) — mesmo botão e mesmo
                        formato de PDF do dashboard Peticionamento legado. Só aparece para <strong>Gestor</strong> e{' '}
                        <strong>Desenvolvedor</strong> — mesma permissão do dashboard legado (mais restrita que o botão
                        "Exportar", que também é liberado para Colaborador).
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="filtros"
                title="Filtros disponíveis"
                subtitle="Como personalizar a visão do dashboard"
                icon="filter"
            >
                <DocGrid>
                    {FILTERS.map((f) => (
                        <DocCard key={f.name} title={f.name}>
                            <p>{f.desc}</p>
                        </DocCard>
                    ))}
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe, e por quê"
                icon="alert"
            >
                <DocGrid>
                    <DocCard title="Sem Revisão nem Reajuizamento">
                        <p>
                            O lexpre não tem, hoje, um status equivalente a "Revisão" nem um campo equivalente a
                            "REAJUIZAMENTO" do banco antigo. O card "Revisão" foi substituído por "Cancelados"
                            (04/09/2026); os cards de Reajuizamento (Resolvidos/Não Resolvidos e os gauges de taxa)
                            foram removidos até esse conceito existir na nova base.
                        </p>
                    </DocCard>
                    <DocCard title="UF ainda não disponível">
                        <p>
                            O filtro de UF que existe no dashboard legado ainda não tem equivalente aqui — a demanda no
                            lexpre não carrega essa informação diretamente na consulta atual.
                        </p>
                    </DocCard>
                    <DocCard title="Base de dados nova — números ainda baixos">
                        <p>
                            Como o banco lexpre está em fase inicial de adoção, ainda há poucas demandas que
                            efetivamente saíram do setor Peticionamento — por isso os indicadores de "Peticionados"
                            tendem a aparecer zerados ou baixos até que o fluxo real de trabalho passe a acontecer nessa
                            base.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
