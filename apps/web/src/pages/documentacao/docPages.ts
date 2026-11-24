import type { ComponentType } from 'react'
import { lazyNamed } from '../../lib/lazyNamed.ts'

// Módulo: o conteúdo de cada guia, pelo slug do registro (docRegistry.ts).
// Slug sem conteúdo aqui = a página mostra "Em construção".
// Cada guia é carregado sob demanda (lazy): o texto só é baixado quando a pessoa abre o guia.
// Assim o cabeçalho do dashboard pode perguntar "este guia existe?" sem trazer os textos junto.
export const DOC_PAGES: Record<string, ComponentType> = {
    'guia-do-usuario': lazyNamed(() => import('./conteudo/GuiaDoUsuario.tsx'), 'GuiaDoUsuarioDoc'),
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
}
