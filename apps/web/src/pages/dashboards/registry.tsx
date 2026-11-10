import type { ComponentType } from 'react'
import type { Meta } from '../../types/index.ts'
import { DashboardView } from './DashboardView.tsx'
import { protocolo } from './protocolo/index.ts'
import type { DashboardModule } from './types.ts'
import { pendencias } from './pendencias/index.ts'
import { comercial } from './comercial/index.ts'
import { comissao } from './comissao/index.ts'
import { nps } from './nps/index.ts'
import { marketing } from './marketing/index.ts'
import { peticionamento } from './peticionamento/index.ts'
import { orgDocumentos } from './org-documentos/index.ts'
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
    [protocolo.key]: toPage(protocolo),
    [pendencias.key]: toPage(pendencias),
    [comercial.key]: toPage(comercial),
    [comissao.key]: toPage(comissao),
    [nps.key]: toPage(nps),
    [marketing.key]: toPage(marketing),
    [peticionamento.key]: toPage(peticionamento),
    [orgDocumentos.key]: toPage(orgDocumentos),
    [preProtocolo.key]: toPage(preProtocolo),
    [execucao.key]: toPage(execucao),
    [acordos.key]: toPage(acordos),
    [recursal.key]: toPage(recursal),
    [estrategico.key]: toPage(estrategico),
    [despesas.key]: toPage(despesas),
    [metaAnual.key]: toPage(metaAnual),
}
