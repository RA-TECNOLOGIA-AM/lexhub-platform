import { useState } from 'react'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import {
    Code,
    DocPage,
    DocSection,
    DocSteps,
    type DocStep,
    DocTable,
    InfoBox,
    WatchBox,
    type TocItem,
} from '../components/DocParts.tsx'

// Guia da API pública /v1. Espelha apps/api/src/app/routes/public_auth.py e public_data.py e o script
// apps/api/scripts/api_publica_cliente.py: mudou rota, parâmetro, limite ou mensagem lá, atualize aqui.

const BASE = 'https://api.hub.lexgroup.com.br/v1'

const TOC: TocItem[] = [
    { id: 'quem', label: 'Quem pode usar' },
    { id: 'chave', label: 'Pedir a chave e gerar tokens' },
    { id: 'renovar', label: 'Renovar o access token' },
    { id: 'catalogo', label: 'O que a chave alcança' },
    { id: 'dados', label: 'Buscar os dados' },
    { id: 'exemplos', label: 'Exemplos' },
    { id: 'powerbi', label: 'Power BI e agendamentos' },
    { id: 'erros', label: 'Erros' },
]

const STEPS: DocStep[] = [
    {
        title: 'Peça a chave',
        body: (
            <>
                Em Configurações → "Chave de API", confira os seus setores e, se precisar de outro, use "+ Pedir setor
                extra" com a justificativa e até quando vale (máximo 365 dias). Clique em "Pedir chave de API".
            </>
        ),
    },
    {
        title: 'Espere a aprovação',
        body: (
            <>Um Desenvolvedor aprova em Administração → "Chaves de API" e pode aprovar só parte dos setores extras.</>
        ),
    },
    {
        title: 'Gere os tokens',
        body: (
            <>
                Volte em "Chave de API" e clique em "Gerar tokens". O <Code>access_token</Code> vale 1 semana e o{' '}
                <Code>refresh_token</Code> (começa com <Code>lxr_</Code>) vale 30 dias. Eles aparecem uma vez só: guarde
                como uma senha. Gerar de novo invalida os anteriores.
            </>
        ),
    },
]

const PARAMS: [string, string][] = [
    ['from', 'Data inicial, AAAA-MM-DD (inclusiva). Obrigatória.'],
    ['to', 'Data final, AAAA-MM-DD (inclusiva). Obrigatória. Até 366 dias depois de from.'],
    ['campos', 'Campos a devolver, separados por vírgula ou repetindo o parâmetro. Padrão: todos (ver /catalogo).'],
    ['relatorio', 'Outro relatório do dashboard, quando ele tem mais de um (ver /catalogo). Padrão: o principal.'],
    ['pagina', 'Página, a partir de 1. Padrão: 1.'],
    ['tamanho_pagina', 'Linhas por página, de 1 a 5000. Padrão: 1000.'],
]

const ERRORS: [string, string][] = [
    ['401', 'Access token ausente, vencido ou revogado; ou refresh token inválido, vencido ou já usado.'],
    ['403', 'O dashboard ou a unidade não estão no alcance da chave (setor, cargo ou dashboard desligado).'],
    ['404', 'O dashboard não tem exportação, ou o relatório pedido não existe.'],
    ['400', 'Campo desconhecido em campos.'],
    ['422', 'Período inválido (to antes de from, mais de 366 dias) ou parâmetro fora da faixa.'],
    ['423', 'A fonte do dashboard foi desligada pela TI.'],
    ['429', 'Mais de 60 chamadas por minuto com a mesma chave. Espere e tente de novo.'],
    ['501 / 503', 'O dashboard ainda não tem dados na V2, ou a fonte está fora do ar.'],
]

const EXAMPLES: Record<string, string> = {
    cURL: `curl "${BASE}/orgs/lexgroup/units/NG/dashboards/comercial-lexpre?from=2026-11-01&to=2026-11-26&campos=campanha,assinado" \\
  -H "Authorization: Bearer $LEXHUB_TOKEN"`,
    JavaScript: `const url = new URL("${BASE}/orgs/lexgroup/units/NG/dashboards/comercial-lexpre")
url.search = new URLSearchParams({ from: "2026-11-01", to: "2026-11-26", campos: "campanha,assinado" })
const resp = await fetch(url, { headers: { Authorization: \`Bearer \${process.env.LEXHUB_TOKEN}\` } })
const { dados, paginacao } = await resp.json()`,
    Python: `import json, os, urllib.request

url = "${BASE}/orgs/lexgroup/units/NG/dashboards/comercial-lexpre?from=2026-11-01&to=2026-11-26"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['LEXHUB_TOKEN']}"})
dados = json.load(urllib.request.urlopen(req))["dados"]`,
}

const RESPONSE = `{
  "org": "lexgroup",
  "unidade": "NG",
  "dashboard": "comercial-lexpre",
  "relatorio": "",
  "periodo": { "from": "2026-11-01", "to": "2026-11-26" },
  "campos": ["campanha", "assinado"],
  "paginacao": { "pagina": 1, "tamanho_pagina": 1000, "total": 2, "total_paginas": 1 },
  "dados": [
    { "campanha": "Black Friday", "assinado": true },
    { "campanha": "Indicação", "assinado": false }
  ]
}`

function Block({ children }: { children: string }) {
    return (
        <pre className="doc-pre">
            <code>{children}</code>
        </pre>
    )
}

function Examples() {
    const langs = Object.keys(EXAMPLES)
    const [lang, setLang] = useState(langs[0])
    return (
        <>
            <Segmented
                label="Linguagem"
                value={lang}
                onChange={setLang}
                options={langs.map((l) => ({ value: l, label: l }))}
            />
            <Block>{EXAMPLES[lang]}</Block>
        </>
    )
}

export function ApiPublicaDoc() {
    return (
        <DocPage
            kicker="Integrações"
            title="API pública"
            toc={TOC}
            intro={
                <>
                    Consulte por API os mesmos dados do "Exportar" dos dashboards, para Power BI, planilhas e scripts. A
                    API devolve JSON paginado; o arquivo exportado e a API sempre batem.
                </>
            }
        >
            <DocSection id="quem" title="01 — Quem pode usar">
                <p>
                    Owner da organização, e Gestor ou Controller de alguma unidade. A chave é da pessoa: alcança só os
                    dashboards dos seus setores (e dos setores extras aprovados), nas unidades em que ela tem esse cargo
                    (Owner: todas). Ver tudo na tela não muda isso: na API vale o setor.
                </p>
                <InfoBox>
                    Perdeu o cargo, saiu do setor ou da organização, ou o setor extra venceu: a chave para de alcançar
                    aquilo em até 1 minuto, sem precisar revogar.
                </InfoBox>
            </DocSection>

            <DocSection id="chave" title="02 — Pedir a chave e gerar tokens">
                <DocSteps steps={STEPS} />
            </DocSection>

            <DocSection id="renovar" title="03 — Renovar o access token">
                <p>
                    Quando o access vencer, troque o refresh por um par novo. O refresh enviado deixa de valer:{' '}
                    <strong>guarde sempre o refresh novo da resposta</strong>.
                </p>
                <Block>{`curl -X POST "${BASE}/auth/token" \\
  -H "Content-Type: application/json" \\
  -d '{"refresh_token": "lxr_..."}'`}</Block>
                <WatchBox title="Refresh usado duas vezes">
                    Se um refresh já trocado for usado de novo (inclusive duas renovações ao mesmo tempo), todos os
                    tokens da chave são revogados. Gere novos em Configurações → "Chave de API".
                </WatchBox>
            </DocSection>

            <DocSection id="catalogo" title="04 — O que a chave alcança">
                <p>
                    <Code>GET {BASE}/catalogo</Code> lista, agora, cada unidade e dashboard que a chave alcança, com os
                    relatórios e os campos de cada um.
                </p>
            </DocSection>

            <DocSection id="dados" title="05 — Buscar os dados">
                <p>
                    <Code>
                        GET {BASE}/orgs/{'{org}'}/units/{'{unidade}'}/dashboards/{'{dashboard}'}
                    </Code>
                    , com o cabeçalho <Code>Authorization: Bearer {'<access_token>'}</Code>.
                </p>
                <DocTable head={['Parâmetro', 'O que é']} rows={PARAMS} code={[0]} />
                <p>Resposta:</p>
                <Block>{RESPONSE}</Block>
                <p>
                    Página além do total volta com <Code>dados</Code> vazio. Toda chamada fica na Auditoria em nome do
                    dono da chave.
                </p>
            </DocSection>

            <DocSection id="exemplos" title="06 — Exemplos">
                <Examples />
            </DocSection>

            <DocSection id="powerbi" title="07 — Power BI e agendamentos">
                <p>
                    O Power BI não guarda o refresh novo a cada renovação. Use o script{' '}
                    <Code>api_publica_cliente.py</Code> (só precisa do Python, sem bibliotecas extras): ele renova
                    quando falta menos de 1 hora, grava o refresh novo no arquivo antes de buscar os dados e salva um
                    CSV que o Power BI lê.
                </p>
                <Block>{`python api_publica_cliente.py iniciar --url ${BASE} --refresh lxr_...
python api_publica_cliente.py baixar --org lexgroup --unidade NG --dashboard comercial-lexpre \\
    --de 2026-11-01 --ate 2026-11-26 --saida comercial.csv`}</Block>
                <WatchBox title="Um agendamento por arquivo">
                    Não rode duas cópias do script ao mesmo tempo com o mesmo arquivo de credenciais: as duas renovariam
                    o mesmo refresh, e a chave inteira seria revogada.
                </WatchBox>
            </DocSection>

            <DocSection id="erros" title="08 — Erros">
                <DocTable head={['Status', 'Quando']} rows={ERRORS} code={[0]} />
                <p>
                    A mensagem vem no campo <Code>detail</Code> da resposta.
                </p>
            </DocSection>
        </DocPage>
    )
}
