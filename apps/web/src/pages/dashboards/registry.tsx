import type { ComponentType } from 'react'
import type { Meta } from '../../types/index.ts'
import { DashboardView } from './DashboardView.tsx'
import type { DashboardModule } from './types.ts'
// Pares como na v1: <domínio> = banco NG, <domínio>-lexpre = banco LexPre (uma pasta por key).
import { comercial } from './comercial/index.ts'
import { comercialLexpre } from './comercial-lexpre/index.ts'
import { comissao } from './comissao/index.ts'
import { comissaoLexpre } from './comissao-lexpre/index.ts'
import { marketing } from './marketing/index.ts'
import { marketingLexpre } from './marketing-lexpre/index.ts'
import { nps } from './nps/index.ts'
import { protocolo } from './protocolo/index.ts'
import { protocoloLexpre } from './protocolo-lexpre/index.ts'
import { pendencias } from './pendencias/index.ts'
import { pendenciasLexpre } from './pendencias-lexpre/index.ts'
import { orgDocumentos } from './org-documentos/index.ts'
import { orgDocumentosLexpre } from './org-documentos-lexpre/index.ts'
import { peticionamento } from './peticionamento/index.ts'
import { peticionamentoLexpre } from './peticionamento-lexpre/index.ts'
import { preProtocolo } from './pre-protocolo/index.ts'
import { execucao } from './execucao/index.ts'
import { acordos } from './acordos/index.ts'
import { recursal } from './recursal/index.ts'
import { estrategico } from './estrategico/index.ts'
import { despesas } from './despesas/index.ts'
import { metaAnual } from './meta-anual/index.ts'

// Transforma um módulo de dashboard numa página pronta (que não recebe parâmetros).
function toPage<T extends { meta: Meta }>(module: DashboardModule<T>): ComponentType {
    return function DashboardModulePage() {
        return <DashboardView module={module} />
    }
}

// Todos os dashboards que já têm página na V2, pela key. Dashboard novo = uma linha aqui.
export const DASHBOARD_PAGES: Record<string, ComponentType> = {
    [comercial.key]: toPage(comercial),
    [comercialLexpre.key]: toPage(comercialLexpre),
    [comissao.key]: toPage(comissao),
    [comissaoLexpre.key]: toPage(comissaoLexpre),
    [marketing.key]: toPage(marketing),
    [marketingLexpre.key]: toPage(marketingLexpre),
    [nps.key]: toPage(nps),
    [protocolo.key]: toPage(protocolo),
    [protocoloLexpre.key]: toPage(protocoloLexpre),
    [pendencias.key]: toPage(pendencias),
    [pendenciasLexpre.key]: toPage(pendenciasLexpre),
    [orgDocumentos.key]: toPage(orgDocumentos),
    [orgDocumentosLexpre.key]: toPage(orgDocumentosLexpre),
    [peticionamento.key]: toPage(peticionamento),
    [peticionamentoLexpre.key]: toPage(peticionamentoLexpre),
    [preProtocolo.key]: toPage(preProtocolo),
    [execucao.key]: toPage(execucao),
    [acordos.key]: toPage(acordos),
    [recursal.key]: toPage(recursal),
    [estrategico.key]: toPage(estrategico),
    [despesas.key]: toPage(despesas),
    [metaAnual.key]: toPage(metaAnual),
}
