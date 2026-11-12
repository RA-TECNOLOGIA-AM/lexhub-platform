import type { ComponentType } from 'react'
import { AcordosDoc } from './conteudo/Acordos.tsx'
import { ComercialLexpreDoc } from './conteudo/ComercialLexpre.tsx'
import { ComissaoLexpreDoc } from './conteudo/ComissaoLexpre.tsx'
import { ExecucaoDoc } from './conteudo/Execucao.tsx'
import { OrgDocumentosLexpreDoc } from './conteudo/OrgDocumentosLexpre.tsx'
import { PendenciasLexpreDoc } from './conteudo/PendenciasLexpre.tsx'
import { PeticionamentoLexpreDoc } from './conteudo/PeticionamentoLexpre.tsx'
import { ProtocoloLexpreDoc } from './conteudo/ProtocoloLexpre.tsx'
import { RecursalLADoc } from './conteudo/RecursalLA.tsx'
import { RecursalNGDoc } from './conteudo/RecursalNG.tsx'

// Módulo: o conteúdo de cada guia, pelo slug do registro (docRegistry.ts).
// Slug sem conteúdo aqui = a página mostra "Em construção".
export const DOC_PAGES: Record<string, ComponentType> = {
    'protocolo-lexpre': ProtocoloLexpreDoc,
    'pendencias-lexpre': PendenciasLexpreDoc,
    'org-documentos-lexpre': OrgDocumentosLexpreDoc,
    'peticionamento-lexpre': PeticionamentoLexpreDoc,
    'comercial-lexpre': ComercialLexpreDoc,
    'comissao-lexpre': ComissaoLexpreDoc,
    execucao: ExecucaoDoc,
    acordos: AcordosDoc,
    'recursal-ng': RecursalNGDoc,
    'recursal-la': RecursalLADoc,
}
