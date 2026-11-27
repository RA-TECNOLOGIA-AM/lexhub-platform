import type { ComponentType } from 'react'
import { lazyNamed } from '../../lib/lazyNamed.ts'

// Módulo: o conteúdo de cada guia, pelo slug do registro (docRegistry.ts).
// Slug sem conteúdo aqui = a página mostra "Em construção".
// Cada guia é carregado sob demanda (lazy): o texto só é baixado quando a pessoa abre o guia.
// Assim o cabeçalho do dashboard pode perguntar "este guia existe?" sem trazer os textos junto.
export const DOC_PAGES: Record<string, ComponentType> = {
    'guia-do-usuario': lazyNamed(() => import('./conteudo/GuiaDoUsuario.tsx'), 'GuiaDoUsuarioDoc'),
    'api-publica': lazyNamed(() => import('./conteudo/ApiPublica.tsx'), 'ApiPublicaDoc'),
    'protocolo-lexpre': lazyNamed(() => import('./conteudo/ProtocoloLexpre.tsx'), 'ProtocoloLexpreDoc'),
    'pendencias-lexpre': lazyNamed(() => import('./conteudo/PendenciasLexpre.tsx'), 'PendenciasLexpreDoc'),
    'org-documentos-lexpre': lazyNamed(() => import('./conteudo/OrgDocumentosLexpre.tsx'), 'OrgDocumentosLexpreDoc'),
    'peticionamento-lexpre': lazyNamed(() => import('./conteudo/PeticionamentoLexpre.tsx'), 'PeticionamentoLexpreDoc'),
    'comercial-lexpre': lazyNamed(() => import('./conteudo/ComercialLexpre.tsx'), 'ComercialLexpreDoc'),
    'comissao-lexpre': lazyNamed(() => import('./conteudo/ComissaoLexpre.tsx'), 'ComissaoLexpreDoc'),
    execucao: lazyNamed(() => import('./conteudo/Execucao.tsx'), 'ExecucaoDoc'),
    acordos: lazyNamed(() => import('./conteudo/Acordos.tsx'), 'AcordosDoc'),
    'recursal-ng': lazyNamed(() => import('./conteudo/RecursalNG.tsx'), 'RecursalNGDoc'),
    'recursal-la': lazyNamed(() => import('./conteudo/RecursalLA.tsx'), 'RecursalLADoc'),
    'julgados-acordaos': lazyNamed(() => import('./conteudo/JulgadosAcordaos.tsx'), 'JulgadosAcordaosDoc'),
    'protocolo-ng': lazyNamed(() => import('./conteudo/ProtocoloNG.tsx'), 'ProtocoloNGDoc'),
    'protocolo-la': lazyNamed(() => import('./conteudo/ProtocoloLA.tsx'), 'ProtocoloLADoc'),
    'pendencias-ng': lazyNamed(() => import('./conteudo/PendenciasNG.tsx'), 'PendenciasNGDoc'),
    'pendencias-la': lazyNamed(() => import('./conteudo/PendenciasLA.tsx'), 'PendenciasLADoc'),
    'org-documentos-ng': lazyNamed(() => import('./conteudo/OrgDocumentosNG.tsx'), 'OrgDocumentosNGDoc'),
    'org-documentos-la': lazyNamed(() => import('./conteudo/OrgDocumentosLA.tsx'), 'OrgDocumentosLADoc'),
    'peticionamento-ng': lazyNamed(() => import('./conteudo/PeticionamentoNG.tsx'), 'PeticionamentoNGDoc'),
    'peticionamento-la': lazyNamed(() => import('./conteudo/PeticionamentoLA.tsx'), 'PeticionamentoLADoc'),
    'pendencias-intermediarias-ng': lazyNamed(
        () => import('./conteudo/PendenciasIntermediariasNG.tsx'),
        'PendenciasIntermediariasNGDoc',
    ),
    'pendencias-intermediarias-la': lazyNamed(
        () => import('./conteudo/PendenciasIntermediariasLA.tsx'),
        'PendenciasIntermediariasLADoc',
    ),
    'emendas-manifestacoes-ng': lazyNamed(
        () => import('./conteudo/EmendasManifestacoesNG.tsx'),
        'EmendasManifestacoesNGDoc',
    ),
    'emendas-manifestacoes-la': lazyNamed(
        () => import('./conteudo/EmendasManifestacoesLA.tsx'),
        'EmendasManifestacoesLADoc',
    ),
    'replicas-la': lazyNamed(() => import('./conteudo/ReplicasLA.tsx'), 'ReplicasLADoc'),
    'julgados-sentencas': lazyNamed(() => import('./conteudo/JulgadosSentencas.tsx'), 'JulgadosSentencasDoc'),
    'marketing-lexpre': lazyNamed(() => import('./conteudo/MarketingLexpre.tsx'), 'MarketingLexpreDoc'),
    'marketing-ng': lazyNamed(() => import('./conteudo/MarketingNg.tsx'), 'MarketingNgDoc'),
    'execucao-estrategico': lazyNamed(() => import('./conteudo/ExecucaoEstrategico.tsx'), 'ExecucaoEstrategicoDoc'),
    'sobrevivencia-processual': lazyNamed(
        () => import('./conteudo/SobrevivenciaProcessual.tsx'),
        'SobrevivenciaProcessualDoc',
    ),
}
