import { useState } from 'react'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import {
    DocCard,
    DocGrid,
    DocPage,
    DocSection,
    DocSteps,
    type DocStep,
    DocTable,
    InfoBox,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'
import { detectSystem, shortcutRows, type KeySystem } from './atalhos.ts'

// Guia de uso do LexHub para o colaborador: do login à exportação. Sem telas de administração.
// Os textos entre aspas são os rótulos que aparecem nas telas: ao renomear um botão, atualize aqui.

const TOC: TocItem[] = [
    { id: 'entrar', label: 'Entrar no LexHub' },
    { id: 'tv', label: 'Entrar numa TV' },
    { id: 'tela', label: 'Conhecendo a tela' },
    { id: 'hub', label: 'Achar um dashboard' },
    { id: 'ler', label: 'Ler um dashboard' },
    { id: 'filtros', label: 'Período e filtros' },
    { id: 'exportar', label: 'Exportar relatório' },
    { id: 'conta', label: 'Sua conta e aparência' },
    { id: 'atalhos', label: 'Atalhos de teclado' },
    { id: 'problemas', label: 'Quando algo dá errado' },
]

const PROBLEMS = [
    [
        'Este e-mail não tem convite para o LexHub',
        'A conta usada não tem convite. Entre com o e-mail corporativo convidado. Se ainda não pediu, solicite o convite à equipe do LexHub com o seu e-mail corporativo.',
    ],
    [
        'Você ainda não tem acesso',
        'A conta entrou, mas ainda não foi liberada numa organização. Preencha "Escritório ou empresa" e clique em "Solicitar acesso"; a equipe do LexHub aprova. Depois use "Verificar de novo".',
    ],
    ['Sua sessão expirou', 'Entre de novo. Você volta para a página em que estava.'],
    [
        'Você foi desconectado em outro aparelho',
        'Alguém (ou você) usou "Desconectar" em Dispositivos. Entre de novo. Se não foi você, avise a TI.',
    ],
    [
        'Você não tem acesso a este dashboard nesta unidade',
        'O dashboard não está liberado para você nessa unidade. Peça liberação ao gestor da unidade.',
    ],
    [
        'Fonte desligada',
        'A TI desligou a fonte de dados desse dashboard. Os números voltam sozinhos quando ela for religada.',
    ],
    ['Fonte atrasada', 'Os dados estão mais velhos que o normal. Clique em "Atualizar"; se continuar, avise a TI.'],
    ['Em construção', 'O dashboard ainda está sendo trazido da versão antiga. Ele aparece quando ficar pronto.'],
]

const ENTRAR: DocStep[] = [
    {
        title: 'Peça o convite',
        body: (
            <p>
                No 1º acesso, peça o convite à equipe do LexHub informando o seu <strong>e-mail corporativo</strong> (o
                do escritório, ex.: nome@lexgroup.com.br).
            </p>
        ),
    },
    {
        title: 'Entre com a conta corporativa',
        body: (
            <p>
                Clique em <strong>"Entrar com conta corporativa"</strong> e escolha a conta Google convidada. Se
                preferir, use <strong>"ou com e-mail e senha"</strong>, preencha <strong>E-mail</strong> e{' '}
                <strong>Senha</strong> e clique em <strong>"Entrar"</strong>.
            </p>
        ),
    },
    {
        title: 'Escolha a unidade',
        body: <p>No alto do menu lateral, troque entre as unidades que você vê (NG, LAAM, LARJ...).</p>,
    },
]

const TV: DocStep[] = [
    {
        title: 'Na TV',
        body: (
            <p>
                Na tela de login, clique em <strong>"Entrar com QR Code"</strong>. Aparecem um QR Code e um código de 8
                letras (ex.: ABCD-EFGH).
            </p>
        ),
    },
    {
        title: 'No celular',
        body: (
            <p>
                Escaneie o QR Code com o celular em que você já está logado. Ou, no computador, use o ícone{' '}
                <strong>"Conectar uma TV"</strong> no rodapé do menu lateral e digite o código.
            </p>
        ),
    },
    {
        title: 'Autorize',
        body: (
            <p>
                Confira se o código é o mesmo da TV, marque <strong>"Estou na frente da TV..."</strong> e clique em{' '}
                <strong>"Autorizar TV"</strong>. A TV entra sozinha.
            </p>
        ),
    },
]

const EXPORTAR: DocStep[] = [
    {
        title: 'Filtre antes',
        body: <p>Ajuste o período e os filtros: a exportação usa exatamente o que está na tela.</p>,
    },
    {
        title: 'Escolha os campos',
        body: (
            <p>
                Clique em <strong>"Exportar"</strong> e marque os campos que quer no relatório (
                <strong>"Selecionar todos"</strong> / <strong>"Desmarcar todos"</strong>).
            </p>
        ),
    },
    {
        title: 'Baixe',
        body: (
            <p>
                Clique em <strong>"Exportar XLSX"</strong> (abre no Excel) ou <strong>"Exportar CSV"</strong> (texto
                simples, para outros sistemas).
            </p>
        ),
    },
]

const SYSTEM_OPTIONS: { value: KeySystem; label: string }[] = [
    { value: 'windows', label: 'Windows' },
    { value: 'mac', label: 'Mac' },
]

// A tabela de atalhos com as teclas do sistema de quem lê (dá para trocar no seletor).
function Shortcuts() {
    const [system, setSystem] = useState<KeySystem>(() => detectSystem(navigator.userAgent))
    return (
        <>
            <div style={{ display: 'flex' }}>
                <Segmented label="Sistema" options={SYSTEM_OPTIONS} value={system} onChange={setSystem} />
            </div>
            <DocTable head={['Tecla', 'O que faz']} rows={shortcutRows(system)} />
        </>
    )
}

export function GuiaDoUsuarioDoc() {
    return (
        <DocPage
            kicker="Primeiros passos"
            title="Como usar o LexHub"
            toc={TOC}
            intro={
                <>
                    O LexHub reúne os dashboards dos escritórios num lugar só. Este guia mostra o caminho do dia a dia:
                    entrar, achar o dashboard certo, ler os números, filtrar e exportar. Leva uns 5 minutos.
                </>
            }
        >
            <DocSection id="entrar" title="Entrar no LexHub" subtitle="Só entra quem foi convidado" icon="key">
                <DocSteps steps={ENTRAR} />
                <InfoBox>
                    O convite vale só para o e-mail informado: entre sempre com ele. E-mail pessoal (Gmail, Hotmail,
                    etc.) não é liberado. Se recebeu um link de convite, abra-o e entre pela tela{' '}
                    <strong>"Aceitar convite"</strong>.
                </InfoBox>
            </DocSection>

            <DocSection
                id="tv"
                title="Entrar numa TV"
                subtitle="Para deixar um dashboard aberto na TV da sala, sem digitar senha nela"
                icon="tv"
            >
                <DocSteps steps={TV} />
                <InfoBox>
                    A TV entra na <strong>sua conta</strong>: só autorize um código que você está vendo agora numa TV da
                    LexGroup. Se alguém mandou o link ou o código por mensagem ou e-mail, não autorize. O login da TV
                    vale por 24 horas. O QR Code se renova sozinho a cada poucos minutos; se demorar, use o código novo.
                </InfoBox>
            </DocSection>

            <DocSection id="tela" title="Conhecendo a tela" subtitle="Menu à esquerda, ferramentas no topo" icon="grid">
                <DocGrid>
                    <DocCard title="Menu lateral">
                        <p>
                            <strong>Dashboards</strong> e <strong>Documentação</strong> (onde você está). Clique no logo
                            para recolher ou expandir o menu. No celular, o menu abre pelo botão{' '}
                            <strong>"Abrir menu"</strong>.
                        </p>
                    </DocCard>
                    <DocCard title="Seletor de unidade">
                        <p>
                            No alto do menu fica o nome da organização e da unidade (NG, LAAM, LARJ...). Clique para
                            trocar. Se você só vê uma unidade, ele fica fixo.
                        </p>
                    </DocCard>
                    <DocCard title="Barra do topo">
                        <p>
                            <strong>Buscar dashboard</strong>, o sino de <strong>Notificações</strong>,{' '}
                            <strong>Tela cheia</strong>, o botão de modo claro/escuro, a engrenagem de{' '}
                            <strong>Configurações</strong> e a sua foto (mostra o seu perfil).
                        </p>
                    </DocCard>
                    <DocCard title="Sair">
                        <p>
                            O botão <strong>"Sair"</strong> fica no rodapé do menu lateral, ao lado do seu nome.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="hub"
                title="Achar um dashboard"
                subtitle="A tela Dashboards (o hub) mostra só o que está liberado para você"
                icon="search"
            >
                <DocGrid>
                    <DocCard title="Buscar">
                        <p>
                            Digite em <strong>"Buscar dashboard"</strong> parte do nome, da área ou da descrição. Esc
                            limpa a busca.
                        </p>
                    </DocCard>
                    <DocCard title="Filtrar por unidade">
                        <p>
                            Escolha a unidade no seletor do menu lateral. Em <strong>"Todas as unidades"</strong>, cada
                            card mostra em quais unidades está liberado.
                        </p>
                    </DocCard>
                    <DocCard title="Favoritos">
                        <p>
                            Toque na estrela do card ou arraste o card para <strong>"Favoritos"</strong>, que fica
                            sempre no topo. Para tirar, toque na estrela de novo.
                        </p>
                    </DocCard>
                    <DocCard title="Organizar do seu jeito">
                        <p>
                            Arraste os cards para mudar a ordem dentro da seção (no celular, segure o card antes de
                            arrastar). Em <strong>"Visualização"</strong>, escolha <strong>"Quadro"</strong> ou{' '}
                            <strong>"Lista"</strong>. A ordem e os favoritos ficam salvos na sua conta.
                        </p>
                    </DocCard>
                </DocGrid>
                <InfoBox>
                    Embaixo de cada card aparece de quando são os dados: <strong>"Atualizado há 3 min"</strong> está em
                    dia; <strong>"Fonte atrasada"</strong> avisa que os dados estão velhos;{' '}
                    <strong>"Atualiza ao abrir"</strong> busca os dados na hora em que você abre.
                </InfoBox>
            </DocSection>

            <DocSection id="ler" title="Ler um dashboard" subtitle="Cabeçalho, indicadores e gráficos" icon="barChart">
                <DocGrid>
                    <DocCard title="Cabeçalho">
                        <p>
                            Mostra área, unidade, fonte dos dados e a <strong>"Última atualização"</strong> (no horário
                            da unidade). Os dados se atualizam sozinhos a cada 5 minutos; o botão{' '}
                            <strong>"Atualizar"</strong> busca na hora.
                        </p>
                    </DocCard>
                    <DocCard title="Comparação com o mês anterior">
                        <p>
                            Alguns indicadores mostram <strong>▲ ou ▼ X% vs. mês anterior</strong>. Verde é melhora,
                            vermelho é piora (em indicadores de tempo, cair é bom e fica verde).
                        </p>
                    </DocCard>
                    <DocCard title="O que cada número significa">
                        <p>
                            Clique em <strong>"Acessar Documentação"</strong> no cabeçalho para abrir o guia daquele
                            dashboard, com o que cada número mede e como é calculado.
                        </p>
                    </DocCard>
                    <DocCard title="Trocar de unidade">
                        <p>
                            Com o dashboard aberto, o seletor de unidade abre o mesmo dashboard em outra unidade (só
                            lista as unidades em que ele está liberado para você).
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection
                id="filtros"
                title="Período e filtros"
                subtitle="Tudo o que você filtra vale para a página inteira e para a exportação"
                icon="filter"
            >
                <DocGrid>
                    <DocCard title="Período">
                        <p>
                            Clique no botão do período (<strong>"Período padrão"</strong> enquanto você não escolher).
                            Use um atalho (<strong>"Este mês"</strong>, <strong>"Mês passado"</strong>,{' '}
                            <strong>"Últimos 30 dias"</strong>, <strong>"Este ano"</strong>) ou preencha{' '}
                            <strong>De</strong> e <strong>Até</strong> e clique em <strong>"Aplicar"</strong>.
                        </p>
                    </DocCard>
                    <DocCard title="Janela de filtros">
                        <p>
                            Clique em <strong>"Filtros"</strong> (o número ao lado diz quantos estão em uso). Cada
                            marcação vale na hora; dá para buscar dentro da lista de opções.
                        </p>
                    </DocCard>
                    <DocCard title="Clicando nos gráficos">
                        <p>
                            Clique numa barra ou fatia (uma matéria, um funcionário...) para filtrar a página por ela.
                            Clique de novo para tirar.
                        </p>
                    </DocCard>
                    <DocCard title="Tirar filtros">
                        <p>
                            Os filtros em uso aparecem em <strong>"Filtros ativos:"</strong>. Clique no ✕ de um deles ou
                            em <strong>"Limpar todos"</strong>.
                        </p>
                    </DocCard>
                </DocGrid>
                <WatchBox title="Nem todo número muda com o período">
                    <p>
                        Indicadores de estoque (o que está parado hoje) e de histórico completo não dependem do período.
                        O guia de cada dashboard diz quais mudam.
                    </p>
                </WatchBox>
            </DocSection>

            <DocSection
                id="exportar"
                title="Exportar relatório"
                subtitle="Planilha com os dados do dashboard"
                icon="download"
            >
                <DocSteps steps={EXPORTAR} />
                <InfoBox>
                    O botão <strong>"Exportar"</strong> só aparece nos dashboards que o seu cargo pode exportar (em
                    geral, os do seu setor). Toda exportação fica registrada. Se o botão estiver apagado com{' '}
                    <strong>"Sem dados para exportar ainda"</strong>, espere os dados carregarem ou mude o período.
                </InfoBox>
            </DocSection>

            <DocSection
                id="conta"
                title="Sua conta e aparência"
                subtitle="Engrenagem de Configurações, no topo da tela"
                icon="settings"
            >
                <DocGrid>
                    <DocCard title="Perfil">
                        <p>
                            <strong>"Trocar foto"</strong> abre um recorte para ajustar a imagem;{' '}
                            <strong>"Remover foto"</strong> volta às iniciais. Nome, cargo, setor e escritório são
                            definidos pela administração.
                        </p>
                    </DocCard>
                    <DocCard title="Aparência">
                        <p>
                            Escolha o <strong>Modo</strong> (Claro ou Escuro), um tema para cada modo e a{' '}
                            <strong>"Cor de destaque"</strong>. Muda na hora e fica salvo na sua conta, em qualquer
                            aparelho.
                        </p>
                    </DocCard>
                    <DocCard title="Dispositivos">
                        <p>
                            Mostra onde a sua conta está aberta. <strong>"Desconectar"</strong> tira um aparelho (em até
                            1 minuto); <strong>"Desconectar todos os outros"</strong> tira todos menos este. Use se
                            esqueceu a conta aberta em outro computador.
                        </p>
                    </DocCard>
                    <DocCard title="Notificações">
                        <p>
                            O sino mostra avisos novos. Clique num aviso para abri-lo (ele fica lido) ou em{' '}
                            <strong>"Marcar todas como lidas"</strong>.
                        </p>
                    </DocCard>
                </DocGrid>
            </DocSection>

            <DocSection id="atalhos" title="Atalhos de teclado" icon="sliders">
                <Shortcuts />
            </DocSection>

            <DocSection
                id="problemas"
                title="Quando algo dá errado"
                subtitle="A mensagem que aparece e o que fazer"
                icon="alert"
            >
                <DocTable head={['Mensagem', 'O que fazer']} rows={PROBLEMS} />
            </DocSection>
        </DocPage>
    )
}
