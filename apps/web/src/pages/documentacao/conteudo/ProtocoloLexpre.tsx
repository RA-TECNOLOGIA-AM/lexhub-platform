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

const FILTERS = [
    {
        name: 'Período (data de saída)',
        desc: 'Filtra as demandas protocoladas pela data do evento de saída do setor. Represados não são afetados por este filtro.',
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

export function ProtocoloLexpreDoc() {
    return (
        <DocPage
            title="Protocolo (LexPre)"
            tags={['NG', 'LA']}
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número e gráfico do dashboard de Protocolo a partir da nova base de dados
                    (banco <Code>lexpre</Code>), a partir do mesmo log de movimentação de setor usado por{' '}
                    <DocLink to="org-documentos-lexpre">Organização de Documentos</DocLink> e{' '}
                    <DocLink to="peticionamento-lexpre">Peticionamento (LexPre)</DocLink>. A diferença principal: aqui o
                    critério de conclusão é um STATUS que a demanda atinge, não o setor para onde ela vai. Nenhum
                    conhecimento técnico é necessário.
                </>
            }
            header={
                <InfoBox>
                    Este guia vale para o <DashLink dashboard="protocolo-lexpre">Protocolo (LexPre)</DashLink> em todas
                    as unidades: mesma query, mesma comissão (R$1,00 flat por protocolado) e as mesmas regras descritas
                    abaixo — a única diferença entre as unidades é o escritório (<Code>escritorio_id</Code>) pelo qual
                    os dados são filtrados (troque a unidade no seletor da barra lateral). Cada escritório tem seu
                    próprio bloco de <Code>setor_id</Code> no log de movimentação (Protocolo é o id 5 no NGAM e o id 13
                    no LAAM) — o backend já reconhece os dois blocos ao montar os números de cada unidade, então nenhum
                    conceito explicado aqui muda de um escritório pro outro.
                </InfoBox>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Critério de conclusão por STATUS, não por setor de destino"
                icon="db"
            >
                <InfoBox>
                    Assim como Organização de Documentos e Peticionamento, este dashboard reconstrói entradas e saídas
                    do setor "Protocolo" a partir da tabela <Code>log_setor_demanda</Code> (toda vez que uma demanda
                    entra ou sai de um setor, o sistema grava um evento). A diferença é o critério de conclusão: em vez
                    de checar para qual setor a demanda foi, este dashboard checa o <strong>status</strong> que a
                    demanda atingiu.
                </InfoBox>
                <DocCard title="Por que o critério é diferente aqui">
                    <p>
                        Depois de protocolada, a demanda é distribuída para a Justiça — não existe um "próximo setor"
                        fixo no sistema para onde ela deveria ir, ao contrário de Organização de Documentos (que sempre
                        segue para Peticionamento) ou Peticionamento (que sempre segue para Protocolo). Por isso, o que
                        marca a conclusão do Protocolo é o <strong>status da demanda</strong> chegar a{' '}
                        <strong>"Aguardando Despacho Inicial"</strong> — o processo foi distribuído e está aguardando a
                        primeira decisão do juiz.
                    </p>
                    <p>
                        Qualquer demanda que ainda está no setor Protocolo e ainda não atingiu esse status é
                        simplesmente considerada <strong>represada</strong> — ainda não foi resolvida. Quando a demanda
                        SAI do Protocolo sem ter sido resolvida (foi devolvida para um setor anterior — Peticionamento,
                        Organização de Documentos ou Pendências), ela sai do estoque de represados e passa a contar no
                        card <strong>"Devolvido p/ &lt;setor&gt;"</strong> correspondente.
                    </p>
                    <p>
                        <strong>Protocolados (filtro de datas):</strong> demandas com um evento de <em>saída</em> do
                        setor Protocolo cujo status chegou a "Aguardando Despacho Inicial", dentro do período
                        selecionado.
                    </p>
                    <p>
                        <strong>Represados (não filtrado por data):</strong> olha o estado atual da demanda no banco,
                        não um evento pontual — por isso não muda com o filtro de datas.
                    </p>
                    <p>
                        <strong>Devolvido p/ Peticionamento / Org Doc / Pendência (não filtrado por data):</strong>{' '}
                        saídas do setor Protocolo cujo destino (a movimentação pareada) é um desses três setores, sem o
                        status de conclusão — cada devolução conta, mesmo critério de "Devolvido p/ Pendência" em
                        Organização de Documentos.
                    </p>
                </DocCard>
            </DocSection>

            <DocSection
                id="periodo"
                title="Indicadores do período"
                subtitle="Protocolados, represados, valores e tempos no intervalo selecionado"
                icon="check"
            >
                <InfoBox>
                    Os cards de volume e valor usam a data do evento de saída do setor para filtrar — mostram apenas as
                    demandas que saíram do Protocolo dentro do período selecionado. "Represados" é sempre o total atual,
                    independente do período (ver abaixo).
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Protocolados"
                        icon="check"
                        what="Demandas que atingiram o status Aguardando Despacho Inicial no período."
                        counts="Saídas do setor no período cujo status da demanda é Aguardando Despacho Inicial."
                        calc="Contagem direta das saídas protocoladas no período."
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
                        icon="xCircle"
                        what="Demandas devolvidas do Protocolo para um setor anterior, sem ter sido resolvidas."
                        counts="Saídas do setor Protocolo cujo destino (a entrada pareada pelo mesmo evento de movimentação) é Peticionamento, Organização de Documentos ou Pendências."
                        calc="Contagem direta das devoluções por setor de destino — cada devolução conta, mesmo que a mesma demanda seja devolvida mais de uma vez."
                        interpret="Ajuda a identificar em qual etapa anterior o processo mais volta a precisar de ajuste antes de seguir para o Protocolo."
                        caveat="Valor sempre total, independente do período — mesmo critério de Represados. O comparativo “vs mês anterior” conta só as devoluções ocorridas no período selecionado contra o mesmo recorte do mês anterior (aumento aparece em vermelho)."
                    />
                </DocGrid>
                <InfoBox>
                    <strong>Protocolados/Represados de Reajuizamento:</strong> ficam como placeholder (valor 0) — o
                    lexpre ainda não modela o conceito de reajuizamento nas demandas, diferente do dashboard legado.{' '}
                    <strong>Sem card de Cancelados:</strong> uma demanda cancelada é só excluída da contagem de
                    represados, sem um contador dedicado (igual ao dashboard legado, que também não tem esse card em
                    Protocolo). <strong>Sem comissão com Fator Multiplicador:</strong> essa fórmula do dashboard legado
                    (por atingimento de meta anual, com proporcionais por estado AM/PA/PB) é uma comissão diferente da
                    comissão por protocolado do próprio setor (ver seção Comissionamento abaixo) — depende de metas
                    comerciais anuais que ainda não têm equivalente configurado no lexpre.
                </InfoBox>
            </DocSection>

            <DocSection
                id="tempo"
                title="Tempo no setor"
                subtitle="Quanto tempo uma demanda fica no Protocolo"
                icon="trendingUp"
            >
                <DocGrid>
                    <DocCard title="Média / Mediana de Tempo Protocolado">
                        <p>
                            Calculado como a diferença entre o evento de entrada no setor e o evento de saída, para as
                            demandas protocoladas (status Aguardando Despacho Inicial) no período. Quando uma demanda
                            entra mais de uma vez no setor, usa-se sempre a entrada mais recente antes da saída.
                        </p>
                    </DocCard>
                    <DocCard title="Comparativo (Média de Tempo)">
                        <p>
                            Variação percentual do tempo médio no setor do período selecionado contra o mesmo recorte de
                            dias no mês civil anterior.
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
                    sai. Por isso, para todo gráfico "por funcionário" sobre demandas protocoladas, o dashboard usa o
                    responsável da última entrada da demanda no setor antes da saída.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Demandas por Funcionário">
                        <p>
                            Gráfico empilhado com Represados (estoque atual) e Protocolados (no período), por
                            funcionário responsável.
                        </p>
                    </DocCard>
                    <DocCard title="Média de Protocolados por Funcionário (por dia)">
                        <p>
                            Divide o total de protocolados pelo número de dias distintos com saídas atribuídas a esse
                            funcionário. Permite comparar produtividade levando em conta dias trabalhados.
                        </p>
                    </DocCard>
                    <DocCard title="Valor de Causa por Funcionário">
                        <p>
                            Soma o valor de causa das demandas protocoladas por cada funcionário. Para matéria ANP, usa
                            o campo de dano moral; para as demais, usa o valor de causa da demanda.
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
                    Mesma fórmula do dashboard legado (protocolo.py, banco <Code>ng</Code>) — taxa fixa por processo
                    protocolado, sem depender do valor de causa. Diferente da comissão do Org Documentos (que também usa
                    valor de causa), aqui só a quantidade importa.
                </InfoBox>
                <DocCard title="Fórmula de comissão">
                    <Formula>Comissão = R$ 1,00 × Qtd de protocolados</Formula>
                    <p>
                        <strong>Protocolado:</strong> mesmo critério usado no card "Protocolados" — a demanda atingiu o
                        status "Aguardando Despacho Inicial" (equivalente lexpre do STATUS "DISTRIBUÍDO"/"PROTOCOLADO"
                        do banco legado).
                    </p>
                    <p>
                        <strong>Valor de causa:</strong> não entra no cálculo — o valor da comissão depende só da
                        quantidade de demandas protocoladas pelo funcionário no período.
                    </p>
                    <p>
                        <strong>Responsável:</strong> o mesmo funcionário usado nos outros gráficos "por funcionário" —
                        o responsável na última entrada da demanda no setor antes da saída.
                    </p>
                    <p>
                        <strong>Base:</strong> apenas demandas protocoladas (não canceladas), filtradas pela data de
                        saída no período selecionado.
                    </p>
                </DocCard>
                <DocCard title="Exemplo prático">
                    <p>
                        Um funcionário protocolou 150 demandas no período. Comissão = R$ 1,00 × 150 ={' '}
                        <strong>R$ 150,00</strong> — independente do valor de causa dessas 150 demandas.
                    </p>
                </DocCard>
                <DocCard title='Botão "Gerar comissão (PDF)"'>
                    <p>
                        Gera um PDF com o comissionamento por funcionário do período selecionado (funcionário,
                        quantidade de protocolados e comissão) — mesmo botão e mesmo formato de PDF do dashboard
                        Protocolo legado. Só aparece para <strong>Gestor</strong> e <strong>Desenvolvedor</strong> —
                        mesma permissão do dashboard legado (mais restrita que o botão "Exportar", que também é liberado
                        para Colaborador).
                    </p>
                </DocCard>
            </DocSection>

            <DocSection id="tendencia" title="Tendência" subtitle="Evolução ao longo do tempo" icon="trendingUp">
                <DocGrid>
                    <DocCard title="Produção Diária">
                        <p>
                            Gráfico de linha com as demandas protocoladas agrupadas por dia do evento de saída. Útil
                            para identificar picos e vales de produtividade dentro do período selecionado.
                        </p>
                    </DocCard>
                    <DocCard title="Não Protocolados por Mês">
                        <p>
                            Agrupa as demandas ainda represadas pelo mês em que entraram no setor pela última vez —
                            ajuda a identificar se o estoque parado é recente ou antigo.
                        </p>
                    </DocCard>
                    <DocCard title="Protocolados Mês a Mês">
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
                    No lexpre, a matéria vem diretamente da rubrica cadastrada na demanda — já normalizada, sem o sufixo
                    livre que existia no banco antigo.
                </InfoBox>
                <DocGrid>
                    <DocCard title="Top 10 – Protocolados por Matéria">
                        <p>
                            Agrupa as demandas protocoladas no período pela rubrica. Mostra quais tipos de demanda
                            tiveram maior volume de protocolo.
                        </p>
                    </DocCard>
                    <DocCard title="Top 10 – Não Protocolados por Matéria">
                        <p>
                            Agrupa as demandas represadas (estoque atual, sem filtro de período) pela rubrica. Útil para
                            priorizar quais tipos de demanda têm maior acúmulo.
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
                    <DocCard title="Sem comissionamento por meta anual">
                        <p>
                            O Fator Multiplicador e os proporcionais AM/PA/PB do dashboard legado dependem de uma meta
                            anual de valor de causa (R$ 240 milhões em 2026) e do pool de comissão da Comercial — nenhum
                            dos dois tem equivalente configurado no lexpre ainda.
                        </p>
                    </DocCard>
                    <DocCard title='Sem Reajuizamento nem "por Sistema"'>
                        <p>
                            O lexpre ainda não modela reajuizamento (cards ficam como placeholder zerado). O gráfico
                            "por Sistema" (PJE, ESAJ, ...) também não entrou nesta versão: hoje só existe um sistema
                            cadastrado (PROJUDI) no lexpre, então o gráfico não traria nenhuma distribuição útil ainda.
                        </p>
                    </DocCard>
                    <DocCard title="Sem card de Cancelados">
                        <p>
                            Uma demanda cancelada ainda no setor é só excluída da contagem de Represados, sem um
                            contador dedicado (igual ao dashboard legado, que também não tem esse card em Protocolo).
                        </p>
                    </DocCard>
                    <DocCard title="Base de dados nova — números ainda baixos">
                        <p>
                            Como o banco lexpre está em fase inicial de adoção, ainda há poucas (ou nenhuma) demanda que
                            efetivamente saiu do setor Protocolo — por isso os indicadores de "Protocolados" tendem a
                            aparecer zerados até que o fluxo real de trabalho passe a acontecer nessa base.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
