import {
    Code,
    DashLink,
    DocCard,
    DocGrid,
    DocLink,
    DocPage,
    DocSection,
    InfoBox,
    MetricCard,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia de Pendências (LexPre). Texto da v1: LexHub/src/pages/documentacao/Pendencia_Lexpre_NG.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'periodo', label: 'Indicadores do período' },
    { id: 'taxas', label: 'Taxas' },
    { id: 'tempo', label: 'Tempo de resolução' },
    { id: 'rankings', label: 'Por funcionário' },
    { id: 'tendencia', label: 'Tendência e origem' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

const FILTERS = [
    {
        name: 'Período (data de entrada)',
        desc: 'Filtra as pendências pela data em que foram abertas (entrada da visita no setor). Não Resolvidas e Não Resolvidas com atraso não são afetadas por este filtro.',
    },
    {
        name: 'Funcionário',
        desc: 'Restringe a visão a um ou mais funcionários específicos — pelo filtro no topo da página ou clicando diretamente no gráfico de Média por Funcionário.',
    },
    {
        name: 'Área de atuação',
        desc: 'Filtra pela operação vinculada à rubrica da demanda (equivalente à "área de atuação" do dashboard legado).',
    },
]

export function PendenciasLexpreDoc() {
    return (
        <DocPage
            title="Pendências (LexPre)"
            tags={['NG', 'LA']}
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Pendências a partir da nova base de dados
                    (banco <Code>lexpre</Code>), a partir do mesmo log de movimentação de setor usado por{' '}
                    <DocLink to="org-documentos-lexpre">Organização de Documentos</DocLink>,{' '}
                    <DocLink to="peticionamento-lexpre">Peticionamento</DocLink> e{' '}
                    <DocLink to="protocolo-lexpre">Protocolo (LexPre)</DocLink>. A diferença principal: uma demanda pode
                    visitar Pendências várias vezes — mas só a <strong>última visita</strong> de cada uma conta nos
                    números do período (ver "Como o dashboard funciona"). Nenhum conhecimento técnico é necessário.
                </>
            }
            header={
                <InfoBox>
                    Este guia vale para o <DashLink dashboard="pendencias-lexpre">Pendências (LexPre)</DashLink> em
                    todas as unidades: mesma query, mesma fórmula de comissão e as mesmas regras de
                    cancelamento/última-visita descritas abaixo — a única diferença entre as unidades é o escritório (
                    <Code>escritorio_id</Code>) pelo qual os dados são filtrados (troque a unidade no seletor da barra
                    lateral). Tecnicamente isso é possível porque cada escritório tem seu próprio bloco de{' '}
                    <Code>setor_id</Code> no log de movimentação (ex: Pendências é o id 2 no NGAM e o id 10 no LAAM) — o
                    backend já reconhece os dois blocos ao montar os números de cada unidade, então nenhum conceito
                    explicado aqui muda de um escritório pro outro.
                </InfoBox>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Cada visita ao setor é uma pendência própria"
                icon="db"
            >
                <InfoBox>
                    Assim como os outros três dashboards lexpre, este reconstrói entradas e saídas do setor "Pendências"
                    a partir da tabela <Code>log_setor_demanda</Code> (toda vez que uma demanda entra ou sai de um
                    setor, o sistema grava um evento). A diferença é que uma mesma demanda pode cair em Pendências{' '}
                    <strong>várias vezes</strong> ao longo da vida — ela sai de outro setor, resolve algo aqui, volta, e
                    pode cair em Pendências de novo mais tarde por outro motivo. Cada ida ao setor (uma{' '}
                    <strong>visita</strong>: par de entrada + saída) é reconstruída separadamente, mas{' '}
                    <strong>só a última visita de cada demanda entra nos números do período</strong> (Total, Resolvidas,
                    Canceladas, taxas, comissão, produção diária/mensal — ajuste de 18/09/2026). Antes disso, cada ida
                    ao setor contava como uma pendência resolvida separada, o que inflava os números quando a mesma
                    demanda saía e voltava a cair em Pendências mais de uma vez no mesmo recorte de datas.
                </InfoBox>
                <DocCard title="Por que o período usa a data de entrada">
                    <p>
                        Diferente dos outros três dashboards (que filtram pela data de <em>saída</em>), aqui o período
                        filtra pela data em que a pendência foi <strong>aberta</strong> (a entrada da visita). Isso
                        permite que uma pendência aberta dentro do período, mas ainda sem solução, também entre no total
                        do período — é o que torna a Taxa de Não Resolvidos um número útil mesmo dentro de um recorte de
                        datas, igual ao dashboard antigo.
                    </p>
                    <p>
                        Cancelamento é sempre definitivo — uma demanda cancelada não se move mais depois disso. Por
                        isso, apenas a <strong>última visita</strong> de cada demanda pode ser classificada como
                        cancelada. E como só a última visita de cada demanda entra nos números do período, uma visita
                        anterior (seguida de outra ida ao setor) simplesmente não aparece em nenhuma métrica de período
                        — não conta nem como resolvida, nem como cancelada.
                    </p>
                    <p>
                        <strong>Resolvida:</strong> é a última visita da demanda, tem um evento de saída do setor, e não
                        é a visita cancelada.
                    </p>
                    <p>
                        <strong>Não Resolvida (aberta):</strong> a visita ainda não tem saída do setor (sempre é a
                        última visita da demanda — não dá pra reentrar no setor sem antes fechar a visita atual).
                    </p>
                    <p>
                        <strong>Cancelada:</strong> é a última visita da demanda, o status atual dela é "Cancelado",{' '}
                        <strong>e</strong> quem executou o cancelamento pertence de fato ao setor Pendências,{' '}
                        <strong>e</strong> o motivo do cancelamento é um dos aceitos (ver abaixo).
                    </p>
                    <p>
                        Ajuste de 04/09/2026: um cancelamento feito por alguém de FORA da Pendência (outro setor/área
                        agindo diretamente na demanda) não é responsabilidade desse setor e não conta como "Cancelada"
                        aqui — nem no card "Pendências Canceladas", nem na "Taxa de Canceladas". A checagem usa quem de
                        fato executou o evento (não apenas quem estava formalmente responsável pela demanda) contra o
                        cadastro de funcionários alocados no setor Pendências.
                    </p>
                    <p>
                        Ajuste de 02/10/2026: além do setor, o <strong>motivo</strong> do cancelamento também precisa
                        ser um dos dois aceitos — <strong>"Cliente desistiu"</strong> ou{' '}
                        <strong>"Cliente de outro estado"</strong>. Um cancelamento com outro motivo (ex.: "Inexistência
                        processual", "Erro na geração de contrato") não conta mais como "Cancelada" aqui, mesmo feito
                        por alguém do próprio setor Pendências — como a visita já tem uma saída registrada, ela passa a
                        contar como <strong>Resolvida</strong> em vez de desaparecer dos números do período (mesmo
                        efeito que o cancelamento feito fora do setor já tinha). Sem uma saída registrada, a visita
                        continua contando como backlog em aberto de qualquer forma.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="periodo"
                title="Indicadores do período"
                subtitle="Volume e status das pendências no intervalo selecionado"
                icon="check"
            >
                <InfoBox>
                    Total, Resolvidas e Canceladas usam a data de <strong>entrada</strong> da visita para filtrar pelo
                    período — e só consideram a <strong>última visita de cada demanda</strong> (ajuste de 18/09/2026):
                    se uma demanda caiu em Pendências mais de uma vez, só a ida mais recente conta nesses cards, mesmo
                    que uma visita anterior também tenha tido entrada dentro do período selecionado. Não Resolvidas e
                    Não Resolvidas com atraso são sempre o total atual do backlog, independente do período (ver caveat
                    abaixo) — mesmo critério de "Represados" dos outros dashboards lexpre.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Total de Pendências"
                        icon="check"
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
                        caveat="Este e o card de atraso são os únicos que não são afetados pelo filtro de período — mostram sempre o total atual, igual ao dashboard antigo."
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
                        caveat={`Ajuste de 04/09/2026: só conta se quem executou o cancelamento pertence ao setor Pendências — um cancelamento feito por outro setor/área não é contado aqui. Ajuste de 02/10/2026: também só conta se o motivo do cancelamento for "Cliente desistiu" ou "Cliente de outro estado" — outros motivos (ex.: "Inexistência processual") fazem a demanda contar como Resolvida em vez de Cancelada.`}
                    />
                </DocGrid>
                <InfoBox>
                    <strong>Triagem:</strong> passou a mostrar um número real a partir de 24/09/2026 — antes ficava como
                    placeholder (valor 0). No lexpre, Triagem é um setor à parte (não um sub-estado de Pendências), mas
                    como o log de movimentação já traz eventos de todos os setores do escritório, dá pra contar direto
                    quantas demandas estão com o setor atual = Triagem agora (foto do momento, sem filtro de período —
                    mesmo critério de "Não Resolvidas"), sem misturar os dois conceitos.{' '}
                    <strong>Não Resolvidas/Resolvidas de Reajuizamento:</strong> continuam como placeholder — o lexpre
                    ainda não modela o conceito de reajuizamento nas demandas.
                </InfoBox>
            </DocSection>

            <DocSection
                id="taxas"
                title="Taxas do período"
                subtitle="Resolvidos, não resolvidos e canceladas em relação ao total"
                icon="percent"
            >
                <DocGrid>
                    <DocCard title="Taxa de Resolvidos">
                        <p>
                            Resolvidas ÷ Total de Pendências do período (entrada no período), em percentual. Meta de
                            referência: 85%.
                        </p>
                    </DocCard>
                    <DocCard title="Taxa de Não Resolvidos">
                        <p>
                            Do mesmo grupo (entrada no período), quantas ainda estão em aberto ÷ Total do período.
                            Diferente do card de backlog acumulado, este é o "não resolvido" apenas entre as que abriram
                            neste recorte.
                        </p>
                    </DocCard>
                    <DocCard title="Taxa de Canceladas">
                        <p>
                            Canceladas ÷ Total de Pendências do período, em percentual. Meta de referência: máx. 5%.
                            Mesmo filtro de "quem cancelou pertence à Pendência" do card acima — só entra no numerador
                            quando o setor Pendências foi de fato responsável pelo cancelamento.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="tempo"
                title="Tempo de resolução"
                subtitle="Quanto tempo uma pendência leva para ser resolvida"
                icon="trendingUp"
            >
                <DocGrid>
                    <DocCard title="Média de Tempo Resolvidos">
                        <p>
                            Calculado como a diferença entre a entrada e a saída de cada visita resolvida com entrada no
                            período, em dias, e depois a média entre elas. Card mostra comparativo (% vs. mesmo recorte
                            um mês civil antes, cores invertidas — menor tempo é melhor), adicionado em 08/09/2026.
                        </p>
                    </DocCard>
                    <DocCard title="Mediana de Tempo Resolvidos">
                        <p>
                            Mesma base de cálculo da média, mas usando a mediana — menos sensível a casos extremos (uma
                            pendência que ficou muito tempo aberta não distorce o número).
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
                    O responsável de uma visita é sempre o funcionário registrado no momento em que a demanda{' '}
                    <em>entrou</em> em Pendências naquela visita específica — como cada visita já é reconstruída como um
                    par entrada/saída, não é preciso buscar entradas anteriores, ao contrário dos outros três
                    dashboards.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Média Resolvidas por Funcionário">
                        <p>
                            Divide o total de pendências resolvidas pelo funcionário pelo número de dias distintos com
                            resoluções no período. Clicável: filtra o dashboard inteiro pelo funcionário selecionado.
                        </p>
                    </DocCard>
                    <DocCard title="Comissionamento por Funcionário">
                        <p>
                            Mesma fórmula do dashboard antigo: R$ 3,00 por pendência resolvida se a taxa de resolvidos
                            do funcionário for ≥ 97% e a taxa de cancelamento for &lt; 5%; R$ 1,00 se a taxa de
                            resolvidos for ≥ 85%; caso contrário, sem comissão. As taxas usam apenas as visitas fechadas
                            (resolvidas + canceladas) atribuídas ao funcionário no período — visitas ainda abertas não
                            entram no cálculo, e (ajuste de 18/09/2026) só a última visita de cada demanda é
                            considerada, mesmo critério dos cards de Total, Resolvidas e Canceladas.
                        </p>
                        <p>
                            <strong>Cancelamento só conta se for do próprio setor</strong> (ajuste de 04/09/2026, ver
                            seção "Como as pendências são classificadas"): um cancelamento executado por alguém de fora
                            da Pendência não entra na taxa de cancelamento nem reduz a comissão do funcionário — a
                            visita simplesmente não conta como fechada nesse cálculo.
                        </p>
                    </DocCard>
                </DocGrid>
                <DocCard title='Botão "Gerar comissão (PDF)"'>
                    <p>
                        Gera um PDF com o comissionamento por funcionário do período selecionado (funcionário, taxa de
                        resolvidos, taxa de cancelamento, quantidade de resolvidos, valor unitário e comissão) — mesmo
                        botão e mesmo formato de PDF do dashboard Pendências legado. Só aparece para{' '}
                        <strong>Gestor</strong> e <strong>Desenvolvedor</strong> — mesma permissão dos outros 3 setores
                        lexpre (mais restrita que o botão "Exportar", que também é liberado para Colaborador).
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="tendencia"
                title="Tendência e origem"
                subtitle="Evolução ao longo do tempo e de onde vêm as pendências em aberto"
                icon="trendingUp"
            >
                <DocGrid>
                    <DocCard title="Produção Diária">
                        <p>
                            Gráfico de linha com as pendências resolvidas agrupadas pelo dia do evento de saída, dentro
                            do período selecionado — mesmo critério de "última visita de cada demanda" usado nos cards
                            acima.
                        </p>
                    </DocCard>
                    <DocCard title="Origem das Pendências Não Resolvidas">
                        <p>
                            Agrupa o backlog em aberto (acumulado, sem filtro de período) pelo setor de onde a demanda
                            veio antes de cair em Pendências — equivalente direto ao campo "Origem" do dashboard antigo.
                        </p>
                    </DocCard>
                    <DocCard title="Resolvidas Mês a Mês">
                        <p>
                            Visão mensal das resoluções, comparando ano a ano (uma linha por ano). Usa o histórico
                            completo, sem recorte de período, para permitir a comparação entre anos.
                        </p>
                    </DocCard>
                </DocGrid>
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
                    <DocCard title="Triagem é outro setor, sem Reajuizamento">
                        <p>
                            Triagem existe no lexpre como um setor totalmente separado (não um sub-estado de Pendências)
                            — desde 24/09/2026 o card conta quantas demandas estão lá agora (foto do momento),
                            reaproveitando o mesmo log de movimentação, sem misturar os dois conceitos. Reajuizamento
                            ainda não é modelado nas demandas do lexpre, então esses cards continuam zerados.
                        </p>
                    </DocCard>
                    <DocCard title="Sem exclusão por motivo de cancelamento">
                        <p>
                            O dashboard antigo exclui alguns motivos específicos de cancelamento (duplicado, ação
                            inexistente) da taxa de cancelamento. O lexpre ainda não tem esse detalhamento mapeado,
                            então todo cancelamento entra na taxa igualmente.
                        </p>
                    </DocCard>
                    <DocCard title='Sem "Não Resolvidas por Atendente"'>
                        <p>
                            Esse gráfico do dashboard antigo usa o atendente comercial original da demanda, não o
                            responsável pela pendência em si — um conceito diferente do funcionário do setor. Como esse
                            dado comercial não está disponível na mesma consulta usada aqui, o gráfico não entrou nesta
                            versão.
                        </p>
                    </DocCard>
                    <DocCard title="Base de dados nova — números ainda baixos">
                        <p>
                            Como o banco lexpre está em fase inicial de adoção, ainda há poucas (ou nenhuma) pendência
                            que efetivamente passou pelo setor — por isso os indicadores tendem a aparecer zerados até
                            que o fluxo real de trabalho passe a acontecer nessa base.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
