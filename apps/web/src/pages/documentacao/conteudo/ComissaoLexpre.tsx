import {
    Code,
    DashLink,
    DocCallout,
    DocChange,
    DocChips,
    DocFeature,
    DocGrid,
    DocLink,
    DocMini,
    DocPage,
    DocPanel,
    DocSection,
    Formula,
    Hl,
    MetricCard,
    type DocChip,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia da Comissão Comercial (LexPre). Texto da v1: LexHub/src/pages/documentacao/Comissao_Comercial_Lexpre.tsx.

const TOC: TocItem[] = [
    { id: 'como-funciona', label: 'Como funciona' },
    { id: 'visao-atendente', label: 'Visão por atendente' },
    { id: 'captacao', label: 'Captação por Origem' },
    { id: 'comissao', label: 'Cálculo e multiplicadores' },
    { id: 'detalhamento', label: 'Detalhamento' },
    { id: 'filtros', label: 'Filtros' },
    { id: 'limitacoes', label: 'Diferenças para o legado' },
]

// Campos de comissão que já vêm prontos na resposta do Comercial (LexPre).
const CAMPOS: DocChip[] = [
    { label: 'Comissão base', tone: 'accent' },
    { label: 'Fator Multiplicador', tone: 'ok' },
    { label: 'Proporcional AM/PA', tone: 'info' },
    { label: 'Proporcional PB', tone: 'info' },
    { label: 'Desconto de cancelamento tardio', tone: 'danger' },
]

// Os cards da Captação por Origem, iguais aos do Comercial (LexPre).
const CARDS_CAPTACAO: DocChip[] = [
    { label: 'Campanha', tone: 'accent' },
    { label: 'Redes Sociais' },
    { label: 'Retorno' },
    { label: 'Resgate' },
    { label: 'Indicação' },
    { label: 'Site' },
    { label: 'Parceiros', tone: 'info' },
    { label: 'Externos', tone: 'violet' },
    { label: 'Total Contratos' },
    { label: 'Ações Fechadas' },
    { label: 'Cancelados' },
    { label: 'Protocolados', tone: 'ok' },
]

export function ComissaoLexpreDoc() {
    return (
        <DocPage
            title="Comissão Comercial (LexPre)"
            tags={['NG', 'LA']}
            note={
                <>
                    Banco <Code>lexpre</Code> — base nova, em construção
                </>
            }
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número do dashboard de Comissão Comercial a partir da nova base de dados
                    (banco <Code>lexpre</Code>). Ele consome exatamente a mesma consulta do dashboard{' '}
                    <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink> — não existe um endpoint próprio de
                    comissão — e só exibe, numa página separada, os campos de comissão que já vêm calculados nessa
                    resposta. <strong>Nenhum conhecimento técnico é necessário.</strong>
                </>
            }
            header={
                <DocCallout caps title="Escopo multi-unidade & mesma consulta do Comercial">
                    <p>
                        Este guia vale para a{' '}
                        <DashLink dashboard="comissao-lexpre">Comissão Comercial (LexPre)</DashLink> em todas as
                        unidades (troque a unidade no seletor da barra lateral). Mesma query, mesma fórmula de comissão
                        e as mesmas regras descritas abaixo, igual ao dashboard irmão{' '}
                        <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink>.
                    </p>
                    <DocGrid>
                        <DocMini label="Endpoint compartilhado">
                            <Code>/comercial-lexpre</Code> no NG e <Code>/comercial-lexpre-la</Code> no LA — o mesmo do
                            dashboard Comercial.
                        </DocMini>
                        <DocMini label="Única diferença entre unidades">
                            O escritório (<Code>escritorio_id</Code>) pelo qual os dados são filtrados.
                        </DocMini>
                    </DocGrid>
                </DocCallout>
            }
        >
            <DocSection
                id="como-funciona"
                title="01 — Como o dashboard funciona"
                subtitle="Mesma fonte de dados do Comercial (LexPre), só a exibição muda"
            >
                <DocPanel>
                    <DocChips label="Campos que já vêm prontos:" items={CAMPOS} />
                    <p>
                        Este dashboard <strong>não tem endpoint nem cálculo próprios</strong> — ele consome a resposta
                        de <Code>/comercial-lexpre</Code> (ou <Code>/comercial-lexpre-la</Code>) e exibe, além da
                        Captação por Origem (idêntica ao dashboard Comercial), os campos de comissão que já vêm prontos
                        nessa mesma resposta. Qualquer ajuste feito no backend do Comercial (LexPre) — período, filtros,
                        escritório — se reflete <Hl tone="ok">automaticamente</Hl> aqui, sem precisar duplicar lógica.
                    </p>
                </DocPanel>
            </DocSection>

            <DocSection
                id="visao-atendente"
                title="02 — Visão por atendente"
                subtitle="Cada atendente comercial vê só a própria comissão — Gestor e Desenvolvedor continuam vendo tudo"
                badge="Restrição só nesta página"
            >
                <DocCallout tone="info" icon="shield" title="Por que o Comercial (LexPre) continua mostrando tudo?">
                    <p>
                        Essa restrição é exclusiva desta página (Comissão Comercial). O dashboard{' '}
                        <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink> — mesmo usando os mesmos endpoints
                        por trás — continua mostrando a empresa inteira para qualquer atendente, sem restrição: uma
                        atendente pode ver os números da outra lá normalmente (ranking, leaderboard etc.). A diferença é
                        um parâmetro extra (<Code>escopo_proprio</Code>) que só esta página envia.
                    </p>
                </DocCallout>
                <DocGrid>
                    <MetricCard
                        name="Quem vê o quê"
                        icon="shield"
                        what="Nesta página (Comissão Comercial) — todos os KPIs e gráficos desta doc, não só a comissão — a resposta é filtrada pela identidade de quem está logado."
                        counts="Gestor e Desenvolvedor continuam vendo a empresa inteira, sem nenhuma restrição. Qualquer outro cargo (ex.: Colaborador do setor Comercial) vê só as próprias ações, leads, valor de causa e comissão — só aqui, não no dashboard Comercial geral."
                        calc="O backend recorta a base de dados pelo nome do atendente vinculado ao login ANTES de calcular qualquer métrica — por isso tudo deriva do mesmo recorte: pool de comissão, Fator Multiplicador, rubricas, captação por origem etc."
                        interpret="Um atendente comum logando nesta página vê exatamente os mesmos cards e gráficos de sempre — só que com os próprios números, como se fosse o único atendente da empresa."
                    />
                    <MetricCard
                        name="Como o vínculo é criado"
                        icon="users"
                        what="O vínculo entre o login do atendente e o nome usado nos dados de comissão."
                        counts="Criado automaticamente na tela de Usuários: ao cadastrar ou editar alguém com Setor = Comercial e Cargo = Colaborador, aparece um campo 'Nome do atendente (comissão)' — preenchendo, o vínculo é salvo junto com o usuário."
                        calc="Precisa ser o primeiro nome exatamente como aparece nos dados de comissão (ex.: 'Patricia Castro' → 'Patricia'). Deixar em branco, ou mudar o setor/cargo da pessoa depois, remove o vínculo automaticamente."
                        interpret="Sem vínculo cadastrado, um atendente do Comercial vê a página inteira zerada (nega por padrão) — não é um erro, é o comportamento esperado até o vínculo ser preenchido."
                        caveat="Lacuna conhecida: a restrição depende de o navegador mandar o token de sessão para o backend (o app já faz isso automaticamente). Uma chamada à API feita por fora do app, sem esse token, ainda devolve os dados sem restrição — não é uma garantia criptográfica, é proteção ao nível da aplicação."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="captacao"
                title="03 — Captação por Origem"
                subtitle="Os mesmos cards da Captação por Origem do dashboard Comercial (LexPre)"
                badge="Réplica do Comercial"
            >
                <DocPanel>
                    <DocChips label="12 cards replicados:" items={CARDS_CAPTACAO} />
                    <p>
                        Réplica exata da Captação por Origem do dashboard{' '}
                        <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink> — veja a doc do Comercial para o
                        detalhamento de cada card. Aqui ela serve de <strong>contexto</strong> (quanto foi captado)
                        antes dos cards de comissão.
                    </p>
                </DocPanel>
            </DocSection>

            <DocSection
                id="comissao"
                title="04 — Cálculo e multiplicadores"
                subtitle="Base de comissão, Fator Multiplicador e proporcionais aplicados no período"
                tone="ok"
                badge="FM: de R$ 2,5 mi a R$ 4 mi protocolados"
            >
                <Formula>
                    Comissão com FM (líquida) = Comissão Base × Fator Multiplicador − desconto de cancelamento tardio
                </Formula>
                <DocGrid>
                    <MetricCard
                        name="Comissão Base"
                        icon="dollar"
                        what="O valor bruto de comissão gerado pelas ações fechadas no período, antes de qualquer multiplicador."
                        counts="Soma do VALOR_AM (valor de comissão fixo cadastrado por rubrica, em rubricas.valor_rubrica) de todas as ações fechadas no período."
                        calc="Soma direta — rubricas sem valor cadastrado ainda entram na soma como R$ 0."
                        interpret="É o ponto de partida do cálculo — sem essa base, o Fator Multiplicador não tem sobre o que atuar."
                    />
                    <MetricCard
                        name="Valor FM (Fator Multiplicador)"
                        icon="trendingUp"
                        what="O multiplicador aplicado sobre a Comissão Base, de acordo com o volume protocolado no período."
                        counts="Baseado no valor de causa protocolado no período (mesma métrica do card 'Valor de Causa Protocolado' do Comercial)."
                        calc="Começa a contar a partir de R$2,5 milhões protocolados no período, com limite em R$4 milhões — quando esse teto é atingido, o fator trava em 4."
                        interpret="Funciona como um incentivo escalonado: quanto mais valor de causa protocolado no período, maior o multiplicador (até o teto)."
                    />
                    <MetricCard
                        name="Proporcional AM/PA e Proporcional PB"
                        icon="pieChart"
                        what="Como o pool de comissão (já com FM aplicado) é repartido entre os estados AM/PA e PB."
                        counts="Valor de causa protocolado em cada grupo de estados, dentro do período."
                        calc={
                            <>
                                A fatia da <strong>PB</strong> é calculada primeiro, pela razão entre o valor de causa
                                protocolado na PB e o total do período. O que sobra do pool líquido vai inteiro para{' '}
                                <strong>AM/PA</strong>.
                            </>
                        }
                        interpret="Mostra como o mesmo pool de comissão se divide geograficamente, sem que a soma dos dois ultrapasse a Comissão com FM líquida."
                    />
                    <MetricCard
                        name="Comissão com FM (líquida)"
                        icon="dollar"
                        what="O valor final do pool de comissão do período, já líquido de descontos."
                        counts="Comissão Base × Fator Multiplicador, menos o desconto de cancelamentos tardios do período."
                        calc="Comissão com FM bruta (mostrada como referência no detalhe do card) menos o desconto — sem um novo FM aplicado sobre o valor descontado."
                        interpret="É esse valor líquido que os cards Proporcional AM/PA e Proporcional PB repartem entre si."
                        caveat="Desconto de cancelamento tardio: demandas comissionadas num período anterior e canceladas dentro deste período têm o valor cheio já pago descontado aqui (via public.audit_log), sem novo FM sobre o desconto. Sem um período (from/to) selecionado, o desconto não é calculado (fica em R$ 0) e o valor exibido é igual ao bruto."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="detalhamento"
                title="05 — Protocoladas, rubricas e distribuição"
                subtitle="Valor de causa por atendente, tabela de rubricas e visão consolidada"
            >
                <DocGrid>
                    <MetricCard
                        name="Protocoladas Valor de Causa (por atendente)"
                        icon="barChart"
                        what="Quanto de valor de causa cada atendente protocolou no período."
                        counts="Valor de causa das demandas protocoladas no período, agrupado por atendente."
                        calc="Gráfico de barras horizontais, clicável — clicar num atendente filtra a página inteira por ele."
                        interpret="Ranking individual de contribuição para o volume protocolado (e, por consequência, para o Fator Multiplicador)."
                    />
                    <MetricCard
                        name="Rubricas Total / Valor das Rubricas"
                        icon="pieChart"
                        what="Como as ações fechadas do período se distribuem entre rubricas, e o valor de comissão (VALOR_AM) de cada uma."
                        counts="Ações fechadas no período por rubrica; o seletor 'Origem' no cabeçalho restringe a um canal específico em vez do total."
                        calc="Pizza (Rubricas Total) + tabela ordenável (Valor das Rubricas) com ações, valor AM unitário e total por rubrica."
                        interpret="Ajuda a identificar quais rubricas geram mais volume de comissão, não só mais ações."
                    />
                </DocGrid>
                <DocGrid cols={2}>
                    <DocFeature
                        title="Clique na pizza filtra a página inteira"
                        tone="accent"
                        badge="Cross-filter Donut"
                    >
                        <p>
                            Clicar numa fatia de <strong>"Rubricas Total"</strong> filtra a{' '}
                            <strong>página inteira</strong> (comissão, captação, tabelas) por aquela rubrica.
                        </p>
                    </DocFeature>
                    <DocFeature title="Corrigido em 24/09/2026" tone="info" badge="Histórico">
                        <p>
                            Antes, o clique só recortava a tabela "Valor das Rubricas" logo abaixo, deixando o resto da
                            página sem refletir a seleção.
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="06 — Filtros disponíveis"
                subtitle="Como personalizar e cruzar a visão do dashboard"
                tone="info"
            >
                <DocGrid cols={2}>
                    <DocFeature title="Período" badge="Duplo eixo" badgeTone="accent">
                        <p>
                            Filtra a comissão base, o FM e os proporcionais pelo mesmo recorte de{' '}
                            <strong>data de assinatura</strong>/<Hl tone="ok">data de protocolo</Hl> usado no Comercial
                            (LexPre).
                        </p>
                    </DocFeature>
                    <DocFeature title="Funcionários" badge="Topo + Clique" badgeTone="info">
                        <p>
                            Restringe a visão a um ou mais atendentes — pelo filtro no topo da página ou clicando no
                            gráfico <em>"Protocoladas Valor de Causa"</em>.
                        </p>
                    </DocFeature>
                    <DocFeature title="Área de atuação / UF" badge="Catálogos lexpre" badgeTone="neutral">
                        <p>
                            Mesmos catálogos compartilhados dos outros dashboards lexpre (via{' '}
                            <Code>public.area_atuacao</Code> e <Code>customer.uf</Code>).
                        </p>
                    </DocFeature>
                    <DocFeature title="Rubrica" badge="Cross-filter Donut" badgeTone="accent">
                        <p>
                            Clicar numa fatia do gráfico <strong>"Rubricas total"</strong> filtra a página inteira por
                            aquela rubrica (ajuste de 24/09/2026).
                        </p>
                    </DocFeature>
                </DocGrid>
            </DocSection>

            <DocSection
                id="limitacoes"
                title="07 — Diferenças para o dashboard legado (banco ng)"
                subtitle="O que já existe, o que ainda não existe e o motivo de cada decisão"
                tone="danger"
            >
                <DocGrid cols={2}>
                    <DocChange
                        status="Pool agregado"
                        tone="info"
                        area="Comissão"
                        title="Mecanismo de comissão diferente dos outros setores"
                    >
                        <p>
                            O Comercial LexPre (NG e LA) usa um <strong>pool agregado</strong> (Comissão Base × FM,
                            repartido por estado), diferente do mecanismo por funcionário usado em outros setores lexpre
                            (Org Doc, Peticionamento, Protocolo, Pendências), que calculam comissão individual por
                            atendente/funcionário com faixas próprias.
                        </p>
                    </DocChange>
                    <DocChange status="Em consolidação" area="Dados" title="Base de dados nova">
                        <p>
                            Como o banco <Code>lexpre</Code> está em fase inicial de adoção, o Fator Multiplicador e os
                            proporcionais por estado tendem a aparecer <strong>baixos ou zerados</strong> até que o
                            volume protocolado real passe a acontecer nessa base.
                        </p>
                    </DocChange>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
