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

const FILTERS = [
    {
        name: 'Período',
        desc: 'Filtra a comissão base, o FM e os proporcionais pelo mesmo recorte de data de assinatura/protocolo usado no Comercial (LexPre).',
    },
    {
        name: 'Funcionários',
        desc: "Restringe a visão a um ou mais atendentes — pelo filtro no topo da página ou clicando no gráfico 'Protocoladas Valor de Causa'.",
    },
    {
        name: 'Área de atuação / UF',
        desc: 'Mesmos catálogos compartilhados dos outros dashboards lexpre (via public.area_atuacao e customer.uf).',
    },
    {
        name: 'Rubrica',
        desc: "Clicar numa fatia do gráfico 'Rubricas total' filtra a página inteira por aquela rubrica (ajuste de 24/09/2026).",
    },
]

export function ComissaoLexpreDoc() {
    return (
        <DocPage
            title="Comissão Comercial (LexPre)"
            tags={['NG', 'LA']}
            note="Banco lexpre — base nova, em construção"
            toc={TOC}
            intro={
                <>
                    Este guia explica cada número do dashboard de Comissão Comercial a partir da nova base de dados
                    (banco <Code>lexpre</Code>). Ele consome exatamente a mesma consulta do dashboard{' '}
                    <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink> — não existe um endpoint próprio de
                    comissão — e só exibe, numa página separada, os campos de comissão que já vêm calculados nessa
                    resposta. Nenhum conhecimento técnico é necessário.
                </>
            }
            header={
                <InfoBox>
                    Este guia vale para a <DashLink dashboard="comissao-lexpre">Comissão Comercial (LexPre)</DashLink>{' '}
                    em todas as unidades (troque a unidade no seletor da barra lateral). Mesma query (
                    <Code>/comercial-lexpre</Code> ou <Code>/comercial-lexpre-la</Code>), mesma fórmula de comissão e as
                    mesmas regras descritas abaixo — a única diferença entre as unidades é o escritório (
                    <Code>escritorio_id</Code>) pelo qual os dados são filtrados, igual ao dashboard Comercial (LexPre)
                    irmão.
                </InfoBox>
            }
        >
            <DocSection
                id="como-funciona"
                title="Como o dashboard funciona"
                subtitle="Mesma fonte de dados do Comercial (LexPre), só a exibição muda"
                icon="db"
            >
                <InfoBox>
                    Este dashboard não tem endpoint nem cálculo próprios — ele consome a resposta de{' '}
                    <Code>/comercial-lexpre</Code> (ou <Code>/comercial-lexpre-la</Code>) e exibe, além da Seção 01
                    (Captação, idêntica ao dashboard Comercial), os campos de comissão que já vêm prontos nessa mesma
                    resposta: comissão base, Fator Multiplicador, proporcionais por estado e desconto de cancelamento
                    tardio. Qualquer ajuste feito no backend do Comercial (LexPre) — período, filtros, escritório — se
                    reflete automaticamente aqui, sem precisar duplicar lógica.
                </InfoBox>
            </DocSection>

            <DocSection
                id="visao-atendente"
                title="Visão por atendente"
                subtitle="Cada atendente comercial vê só a própria comissão — Gestor/Desenvolvedor continuam vendo tudo"
                icon="shield"
            >
                <InfoBox>
                    Essa restrição é exclusiva desta página (Comissão Comercial). O dashboard{' '}
                    <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink> — mesmo usando os mesmos endpoints por
                    trás — continua mostrando a empresa inteira pra qualquer atendente, sem restrição: uma atendente
                    pode ver os números da outra lá normalmente (ranking, leaderboard, etc.). A diferença é um parâmetro
                    extra (<Code>escopo_proprio</Code>) que só esta página envia.
                </InfoBox>
                <DocGrid>
                    <MetricCard
                        name="Quem vê o quê"
                        icon="shield"
                        what="Nesta página (Comissão Comercial) — todos os KPIs e gráficos desta doc, não só a comissão — a resposta é filtrada pela identidade de quem está logado."
                        counts="Gestor e Desenvolvedor continuam vendo a empresa inteira, sem nenhuma restrição. Qualquer outro cargo (ex.: Colaborador do setor Comercial) vê só as próprias ações, leads, valor de causa e comissão — só aqui, não no dashboard Comercial geral."
                        calc="O backend recorta a base de dados pelo nome do atendente vinculado ao login ANTES de calcular qualquer métrica — por isso tudo deriva do mesmo recorte: pool de comissão, Fator Multiplicador, rubricas, captação por origem, etc."
                        interpret="Um atendente comum logando nesta página vê exatamente os mesmos cards e gráficos de sempre — só que com os próprios números, como se fosse o único atendente da empresa."
                    />
                    <MetricCard
                        name="Como o vínculo é criado"
                        icon="shield"
                        what="O vínculo entre o login do atendente e o nome usado nos dados de comissão."
                        counts="Criado automaticamente na tela de Usuários: ao cadastrar ou editar alguém com Setor = Comercial e Cargo = Colaborador, aparece um campo 'Nome do atendente (comissão)' — preenchendo, o vínculo é salvo junto com o usuário."
                        calc="Precisa ser o primeiro nome exatamente como aparece nos dados de comissão (ex.: 'Patricia Castro' → 'Patricia'). Deixar em branco, ou mudar o setor/cargo da pessoa depois, remove o vínculo automaticamente."
                        interpret="Sem vínculo cadastrado, um atendente do Comercial vê a página inteira zerada (nega por padrão) — não é um erro, é o comportamento esperado até o vínculo ser preenchido."
                        caveat="Lacuna conhecida: a restrição depende de o navegador mandar o token de sessão pro backend (o app já faz isso automaticamente). Uma chamada à API feita por fora do app, sem esse token, ainda devolve os dados sem restrição — não é uma garantia criptográfica, é proteção ao nível da aplicação."
                    />
                </DocGrid>
            </DocSection>

            <DocSection
                id="captacao"
                title="Captação por Origem"
                subtitle="Mesma Seção 01 do dashboard Comercial (LexPre)"
                icon="grid"
            >
                <InfoBox>
                    Réplica exata da Seção 01 do dashboard <DocLink to="comercial-lexpre">Comercial (LexPre)</DocLink> —
                    Campanha, Redes Sociais, Retorno, Resgate, Total Contratos, Cancelados, Ações Fechadas, Externos,
                    Indicação, Site, Parceiros e Protocolados. Ver a doc do Comercial para o detalhamento de cada card;
                    aqui ela serve de contexto (quanto foi captado) antes dos cards de comissão.
                </InfoBox>
            </DocSection>

            <DocSection
                id="comissao"
                title="Cálculo e multiplicadores"
                subtitle="Base de comissão, Fator Multiplicador e proporcionais aplicados no período"
                icon="dollar"
            >
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
                        icon="dollar"
                        what="O multiplicador aplicado sobre a Comissão Base, de acordo com o volume protocolado no período."
                        counts="Baseado no valor de causa protocolado no período (mesma métrica do card 'Valor de Causa Protocolado' do Comercial)."
                        calc="Começa a contar a partir de R$2,5 milhões protocolados no período, com limite em R$4 milhões — quando esse teto é atingido, o fator trava em 4."
                        interpret="Funciona como um incentivo escalonado: quanto mais valor de causa protocolado no período, maior o multiplicador (até o teto)."
                    />
                    <MetricCard
                        name="Proporcional AM/PA e Proporcional PB"
                        icon="dollar"
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
                title="Protocoladas, rubricas e distribuição"
                subtitle="Valor de causa por atendente, tabela de rubricas e visão consolidada"
                icon="pieChart"
            >
                <DocGrid>
                    <MetricCard
                        name="Protocoladas Valor de Causa (por atendente)"
                        icon="pieChart"
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
                        caveat="Corrigido em 24/09/2026: clicar numa fatia da pizza agora filtra a PÁGINA INTEIRA (comissão, captação, tabelas) por aquela rubrica — antes só recortava a tabela 'Valor das Rubricas' logo abaixo, deixando o resto da página sem refletir a seleção."
                    />
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
                    <DocCard title="Mecanismo de comissão diferente do dashboard Comercial legado">
                        <p>
                            O Comercial LexPre (NG e LA) usa um pool agregado (Comissão Base × FM, repartido por
                            estado), diferente do mecanismo por funcionário usado em outros setores lexpre (Org Doc,
                            Peticionamento, Protocolo, Pendências), que calculam comissão individual por
                            atendente/funcionário com faixas próprias.
                        </p>
                    </DocCard>
                    <DocCard title="Base de dados nova — números ainda em consolidação">
                        <p>
                            Como o banco lexpre está em fase inicial de adoção, o Fator Multiplicador e os proporcionais
                            por estado tendem a aparecer baixos ou zerados até que o volume protocolado real passe a
                            acontecer nessa base.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>
        </DocPage>
    )
}
