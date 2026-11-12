import {
    Code,
    DashLink,
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    Formula,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Organização de Documentos (LexPre). Texto da v1: LexHub/src/pages/documentacao/OrgDoc_Lexpre_NG.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'represados', label: 'Represados e retornos' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'tempo', label: 'Tempo de resolução' },
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
        desc: 'Filtra as demandas resolvidas pela data do evento de saída do setor. Represados e retornos não são afetados por este filtro.',
    },
    {
        name: 'Funcionário',
        desc: 'Restringe a visão a um ou mais funcionários específicos — pode ser selecionado pelo filtro no topo da página ou clicando diretamente nos gráficos por funcionário.',
    },
    {
        name: 'Matéria',
        desc: 'Filtra por rubrica (matéria jurídica) — pode ser selecionado clicando diretamente nos gráficos de Top 10 por Matéria.',
    },
    {
        name: 'Área de atuação',
        desc: 'Filtra pela operação vinculada à rubrica da demanda (equivalente à "área de atuação" do dashboard legado).',
    },
]

export function OrgDocumentosLexpreDoc() {
    return (
        <DocPage
            title="Organização de Documentos (LexPre)"
            tags={['NG', 'LA']}
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Organização de Documentos a partir da nova
                    base de dados (banco <Code>lexpre</Code>). A lógica de negócio é a mesma do dashboard legado
                    (represados, resolvidos, comissão), mas a fonte dos dados mudou: em vez de uma tabela com uma linha
                    por processo, o lexpre registra cada movimentação de setor como um evento de log. Nenhum
                    conhecimento técnico é necessário.
                </>
            }
            header={
                <InfoBox>
                    Este guia vale para o{' '}
                    <DashLink dashboard="org-documentos-lexpre">Organização de Documentos (LexPre)</DashLink> em todas
                    as unidades: mesma query, mesma fórmula de comissão (R$0,60 por protocolado a cada R$1 milhão de
                    valor de causa) e as mesmas regras descritas abaixo — a única diferença entre as unidades é o
                    escritório (<Code>escritorio_id</Code>) pelo qual os dados são filtrados (troque a unidade no
                    seletor da barra lateral). Cada escritório tem seu próprio bloco de <Code>setor_id</Code> no log de
                    movimentação (Organização de Documentos é o id 3 no NGAM e o id 11 no LAAM) — o backend já reconhece
                    os dois blocos ao montar os números de cada unidade, então nenhum conceito explicado aqui muda de um
                    escritório pro outro.
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
                    <Code>ENTRADA</Code>, <Code>SAIDA</Code> e <Code>STATUS</Code>. No lexpre não existe mais essa
                    tabela: toda vez que uma demanda entra ou sai de um setor, o sistema grava um evento na tabela{' '}
                    <Code>log_setor_demanda</Code>. O dashboard reconstrói entradas, saídas e o "estado atual" da
                    demanda a partir desses eventos.
                </InfoBox>
                <DocCard title="Como um evento de log é lido">
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 10 }}>
                        <div className="stack" style={{ gap: 4 }}>
                            <span className="badge warn">SAÍDA de um setor</span>
                            <span className="muted small">ex.: sai da Triagem</span>
                        </div>
                        <span className="muted">→</span>
                        <div className="stack" style={{ gap: 4 }}>
                            <span className="badge info">ENTRADA no próximo setor</span>
                            <span className="muted small">ex.: entra em Organização de Documentos</span>
                        </div>
                    </div>
                    <p>
                        As duas linhas acima nascem juntas (mesmo <Code>movimentacao_id</Code>) e representam uma única
                        movimentação. É por isso que o dashboard consegue saber "de qual setor a demanda veio" (para
                        identificar retornos) e "quem era o responsável" no momento de cada evento.
                    </p>
                    <p>
                        <strong>Resolvidos (filtro de datas):</strong> demandas com um evento de <em>saída</em> do setor
                        Organização de Documentos dentro do período selecionado.
                    </p>
                    <p>
                        <strong>Represados e retornos (não filtrados por data):</strong> olham o estado atual da demanda
                        no banco, não um evento pontual — por isso não mudam com o filtro de período.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="represados"
                title="Represados e retornos (acumulado total)"
                subtitle="Sempre o total atual — não dependem do filtro de datas"
                icon="barChart"
            >
                <InfoBox>
                    Esses contadores mostram o estoque atual de trabalho e de onde ele veio. Eles não mudam com o filtro
                    de datas — refletem sempre a situação de agora.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Represados"
                        icon="fileText"
                        what="Total de demandas que estão hoje no setor Organização de Documentos, aguardando ação."
                        counts="Demandas (não canceladas) cujo setor atual é Organização de Documentos, uma por demanda."
                        calc="Contagem direta das demandas ainda no setor. Este contador NÃO é filtrado por data."
                        interpret="Quanto menor, melhor. Representa o estoque de trabalho acumulado."
                        caveat="É o único indicador que não é afetado pelo filtro de período — mostra sempre o total atual."
                    />
                    <MetricCard
                        name="Retorno Pendência"
                        icon="flow"
                        what="Demandas que entraram no setor vindas do setor Pendências."
                        counts="Eventos de entrada no setor cuja movimentação pareada saiu do setor Pendências."
                        calc="Contagem dos eventos de entrada identificados como vindos de Pendências."
                        interpret="Retornos frequentes podem indicar que as demandas chegam incompletas para Organização de Documentos, gerando retrabalho."
                    />
                    <MetricCard
                        name="Retorno Confecção"
                        icon="flow"
                        what="Demandas que entraram no setor vindas do setor Peticionamento."
                        counts="Eventos de entrada no setor cuja movimentação pareada saiu do setor Peticionamento."
                        calc="Contagem dos eventos de entrada identificados como vindos de Peticionamento."
                        interpret="Um número alto pode indicar que os documentos não estavam prontos para peticionamento quando foram enviados."
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
                    que saíram de Organização de Documentos dentro do período selecionado no dashboard.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Resolvido Manualmente"
                        icon="check"
                        what="Demandas organizadas por um funcionário de forma manual."
                        counts="Demandas não canceladas, com peticionamento automático desativado (pet_auto = falso), que saíram do setor no período."
                        calc="Contagem das saídas do setor no período com pet_auto = falso."
                        interpret="Representa o trabalho manual do setor. Um bom número aqui indica alta produtividade da equipe."
                    />
                    <MetricCard
                        name="Resolvido Automaticamente"
                        icon="check"
                        what="Demandas organizadas e já encaminhadas para peticionamento de forma automática pelo sistema."
                        counts="Demandas não canceladas, com peticionamento automático ativado (pet_auto = verdadeiro), que saíram do setor no período."
                        calc="Contagem das saídas do setor no período com pet_auto = verdadeiro."
                        interpret="Automações ajudam a aumentar o volume processado sem sobrecarregar a equipe. Quanto maior, mais eficiente o fluxo automatizado."
                    />
                    <MetricCard
                        name="Cancelados"
                        icon="xCircle"
                        what="Demandas que foram encerradas sem organização."
                        counts="Demandas com status Cancelado que saíram do setor no período."
                        calc="Contagem dos cancelamentos dentro do período."
                        interpret="Cancelamentos podem indicar demandas inviáveis ou com erros. Monitore para identificar padrões."
                    />
                    <MetricCard
                        name="Total Resolvidos"
                        icon="fileText"
                        what="Soma de todas as demandas concluídas no período — tanto manuais quanto automáticas."
                        counts="Demandas não canceladas que saíram do setor no período."
                        calc="Resolvido Manualmente + Resolvido Automaticamente."
                        interpret="Indica o volume total produzido no período. Use para comparar períodos e medir a capacidade do setor."
                    />
                </DocGrid>
                <InfoBox>
                    <strong>Sem card de Reajuizamento:</strong> o banco lexpre ainda não modela o conceito de
                    reajuizamento nas demandas — diferente do dashboard legado, este dashboard não tem (por enquanto) um
                    contador equivalente a "Resolvidos Reajuizamento".
                </InfoBox>
            </DocSection>

            <DocSection
                id="tempo"
                title="Tempo de resolução"
                subtitle="Quanto tempo uma demanda fica no setor"
                icon="trendingUp"
            >
                <DocGrid>
                    <DocCard title="Tempo Médio / Mediana Resolvidos">
                        <p>
                            Calculado como a diferença entre o evento de entrada no setor e o evento de saída, para as
                            demandas resolvidas (não canceladas) no período. Quando uma demanda entra mais de uma vez no
                            setor (por causa de um retorno), usa-se sempre a entrada mais recente antes da saída.
                        </p>
                    </DocCard>
                    <DocCard title="Comparativo (Tempo Médio)">
                        <p>
                            Variação percentual do tempo médio de resolução do período selecionado contra o mesmo
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
                    sai. Por isso, para todo gráfico "por funcionário" sobre demandas resolvidas, o dashboard usa o
                    responsável da última entrada da demanda no setor antes da saída — é como se perguntássemos "quem
                    estava com essa demanda quando ela foi resolvida?".
                </InfoBox>
                <DocGrid>
                    <DocCard title="Demandas por Funcionário">
                        <p>
                            Gráfico empilhado com Represados (estoque atual) e Resolvidos (no período), por funcionário
                            responsável.
                        </p>
                    </DocCard>
                    <DocCard title="Média de Resolvidos por Funcionário (por dia)">
                        <p>
                            Divide o total de resolvidos pelo número de dias distintos com saídas atribuídas a esse
                            funcionário. Permite comparar produtividade levando em conta dias trabalhados.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de Causa por Funcionário">
                        <p>
                            Soma o valor de causa das demandas resolvidas por cada funcionário. Para matéria ANP, usa o
                            campo de dano moral; para as demais, usa o valor de causa da demanda.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo" icon="trendingUp">
                <DocGrid>
                    <DocCard title="Produção Diária">
                        <p>
                            Gráfico de linha com as demandas resolvidas agrupadas por dia do evento de saída. Útil para
                            identificar picos e vales de produtividade dentro do período selecionado.
                        </p>
                    </DocCard>
                    <DocCard title="Represados por Mês de Entrada">
                        <p>
                            Agrupa as demandas ainda represadas pelo mês em que entraram no setor pela última vez —
                            ajuda a identificar se o estoque parado é recente ou antigo.
                        </p>
                    </DocCard>
                    <DocCard title="Resolvidos Mês a Mês">
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
                    "SEGURO") — já normalizada, sem o sufixo livre que existia no banco antigo (ex.: "BX_ANT_FIN - BANCO
                    BRADESCO").
                </InfoBox>
                <DocGrid>
                    <DocCard title="Top 10 – Resolvidos por Matéria">
                        <p>
                            Agrupa as demandas resolvidas no período pela rubrica. Mostra quais tipos de demanda tiveram
                            maior volume de resolução. O botão de alternância mostra "No Setor" (saíram do Org Doc no
                            período, por DATA de saída) ou "Protocolados" (de fato protocolaram no período, por DATA de
                            protocolo — ver "Comissionamento"); como os dois usam recortes de data diferentes, uma
                            demanda pode aparecer em um período de "No Setor" e só aparecer em "Protocolados" num
                            período posterior (ou nunca).
                        </p>
                    </DocCard>
                    <DocCard title="Top 10 – Represados por Matéria">
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
                    Mesma fórmula do dashboard legado — o valor depende tanto da quantidade de demandas quanto do valor
                    das causas dessas demandas. Desde 04/09/2026, porém, tanto a quantidade quanto o valor de causa
                    somados na fórmula só contam demandas que de fato chegaram a ser <strong>protocoladas</strong>{' '}
                    depois — não qualquer demanda que o Org Doc marcou como "resolvida".
                </InfoBox>
                <DocCard title="Fórmula de comissão">
                    <Formula>
                        Comissão = R$ 0,60 × Qtd de protocolados × (Valor de causa protocolado / 1.000.000)
                    </Formula>
                    <p>
                        <strong>Qtd de protocolados:</strong> das demandas resolvidas pelo funcionário (saíram do Org
                        Doc rumo a Peticionamento ou Protocolo, em qualquer data), conta só as que têm a{' '}
                        <strong>data de protocolo dentro do período selecionado</strong> e status atual "Aguardando
                        Despacho Inicial" — ou seja, que de fato protocolaram NESSE período. Uma demanda que saiu do Org
                        Doc num mês mas só protocolou no mês seguinte entra no comissionamento do mês em que ela
                        REALMENTE protocolou, não no mês em que saiu do setor (ajuste de 07/10/2026). Uma demanda que
                        nunca chega a protocolar (parada em Peticionamento, cancelada depois, etc.) não entra nunca.
                    </p>
                    <p>
                        <strong>Valor de causa protocolado:</strong> soma o valor de causa só das mesmas demandas já
                        protocoladas contadas acima.
                    </p>
                    <p>
                        <strong>Valor de causa:</strong> para demandas com matéria ANP, usa o campo de dano moral. Para
                        todas as demais matérias, usa o valor de causa da demanda.
                    </p>
                    <p>
                        <strong>Demandas sem valor de causa</strong> não contribuem para o cálculo.
                    </p>
                    <p>
                        <strong>Base:</strong> apenas demandas não canceladas, atribuídas ao funcionário na entrada no
                        setor; a quantidade e o valor de causa "protocolado" são filtrados pela data de protocolo (não
                        pela data de saída do setor) no período selecionado.
                    </p>
                </DocCard>
                <DocCard title="Exemplo prático">
                    <p>
                        Um funcionário organizou 100 pastas no mês. Dessas, só 50 já foram protocoladas naquele período,
                        somando R$ 5.000.000,00 de valor de causa — as outras 50 ainda estão em Peticionamento (ou em
                        outra etapa), sem contar nem na quantidade nem no valor de causa. Comissão = R$ 0,60 × 50 ×
                        (5.000.000 ÷ 1.000.000) = R$ 0,60 × 50 × 5 = <strong>R$ 150,00</strong> (não R$ 300,00, que
                        seria o resultado se as 100 pastas organizadas contassem).
                    </p>
                </DocCard>
                <DocCard title="Por que essa mudança">
                    <p>
                        O objetivo é não pagar comissão sobre demandas (nem sobre o valor de causa delas) que podem
                        nunca chegar a ser protocoladas — mesma mudança de regra simulada para o dashboard Org
                        Documentos legado (banco <Code>ng</Code>) em 03/09/2026, aplicada aqui só ao lexpre, e refinada
                        em 04/09/2026 para também restringir a quantidade (não só o valor de causa) aos casos de fato
                        protocolados.
                    </p>
                </DocCard>
                <DocCard title='Botão "Gerar comissão (PDF)"'>
                    <p>
                        Gera um PDF com o comissionamento por funcionário do período selecionado (funcionário, valor de
                        causa protocolado, quantidade de protocolados e comissão) — mesmo botão e mesmo formato de PDF
                        do dashboard Org Documentos legado. Só aparece para <strong>Gestor</strong> e{' '}
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
                    <DocCard title="Sem Reajuizamento">
                        <p>
                            O lexpre não tem, hoje, um campo equivalente ao "REAJUIZAMENTO" do banco antigo. O card
                            "Resolvidos Reajuizamento" foi removido até esse conceito existir na nova base.
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
                            efetivamente saíram do setor Organização de Documentos — por isso os indicadores de
                            "Resolvidos" tendem a aparecer zerados ou baixos até que o fluxo real de trabalho passe a
                            acontecer nessa base.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
