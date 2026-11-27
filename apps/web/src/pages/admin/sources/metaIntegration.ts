import type { MetaIntegration, MetaIntegrationInput, MetaOrigin } from '../../../types/index.ts'

// Módulo: as regras da tela Integração Meta, sem React (testadas em metaIntegration.test.ts).

// O que a pessoa escolheu para a chave secreta: manter a salva, trocar por outra ou apagar.
export type SecretChoice = 'keep' | 'replace' | 'remove'

export type MetaDraft = {
    appId: string
    secretChoice: SecretChoice
    secret: string // só vale com secretChoice 'replace'
    graphVersion: string
    syncPaused: boolean
}

export function draftFrom(meta: MetaIntegration): MetaDraft {
    return {
        appId: meta.appId ?? '',
        // Sem chave (ou uma que não abre), o campo já vem aberto para digitar.
        secretChoice: meta.hasAppSecret && !meta.secretUnreadable ? 'keep' : 'replace',
        secret: '',
        graphVersion: meta.graphVersion,
        syncPaused: meta.syncPaused,
    }
}

// O ID do app é só número (até 25 dígitos): o resto some enquanto a pessoa digita ou cola.
export const normalizeAppId = (v: string) => v.replace(/\D/g, '').slice(0, 25)

// O corpo do PUT: appSecret null = manter, '' = apagar, texto = trocar.
export function inputFrom(draft: MetaDraft): MetaIntegrationInput {
    const appId = draft.appId.trim()
    let appSecret: string | null = null
    if (draft.secretChoice === 'remove') appSecret = ''
    else if (draft.secretChoice === 'replace' && draft.secret.trim()) appSecret = draft.secret.trim()
    return { appId, appSecret, graphVersion: draft.graphVersion, syncPaused: draft.syncPaused }
}

// O que impede salvar (a API confere de novo). null = pode.
export function validateMeta(draft: MetaDraft): string | null {
    const appId = draft.appId.trim()
    if (appId && !/^\d{5,25}$/.test(appId)) return 'O ID do app tem de 5 a 25 números.'
    if (!appId && draft.secretChoice === 'replace' && draft.secret.trim()) {
        return 'Informe o ID do app junto com a chave.'
    }
    return null
}

// Testar pede o ID e uma chave: a digitada ou a salva.
export function canTest(draft: MetaDraft, meta: MetaIntegration): boolean {
    if (!/^\d{5,25}$/.test(draft.appId.trim())) return false
    if (draft.secretChoice === 'replace') return draft.secret.trim().length > 0 || meta.hasAppSecret
    return draft.secretChoice === 'keep' && meta.hasAppSecret
}

// Mudou algo em relação ao que está em uso?
export function isDirty(draft: MetaDraft, meta: MetaIntegration): boolean {
    return (
        draft.appId.trim() !== (meta.appId ?? '') ||
        draft.graphVersion !== meta.graphVersion ||
        draft.syncPaused !== meta.syncPaused ||
        draft.secretChoice === 'remove' ||
        (draft.secretChoice === 'replace' && draft.secret.trim().length > 0)
    )
}

// De onde vem o valor em uso, para a linha embaixo do campo.
export function originNote(origin: MetaOrigin, field: 'appId' | 'appSecret' | 'graphVersion'): string {
    if (origin === 'tela') return 'Salvo aqui.'
    if (origin === 'servidor') {
        return 'Vem do .env do servidor (reserva). Salvar aqui passa a valer o daqui.'
    }
    if (origin === 'padrão') return 'O padrão da API.'
    return field === 'appId' ? 'Sem app: a API não sabe o tipo nem a validade dos tokens.' : 'Sem chave salva.'
}

// Depois de salvar: o aviso na página.
export function savedNotice(before: MetaIntegration, after: MetaIntegration): string {
    if (before.syncPaused !== after.syncPaused) {
        return after.syncPaused
            ? 'Coleta do Facebook Ads pausada para todas as contas. O que já foi guardado fica.'
            : 'Coleta do Facebook Ads retomada: ela traz os dias que faltaram.'
    }
    return 'Integração Meta salva. Vale na hora para os testes e na próxima rodada da coleta.'
}

// "27/11/2026, 14:05, por Ana"
export function updatedLabel(meta: MetaIntegration): string | null {
    if (!meta.updatedAt) return null
    const when = new Date(meta.updatedAt).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
    return meta.updatedBy ? `${when}, por ${meta.updatedBy}` : when
}
