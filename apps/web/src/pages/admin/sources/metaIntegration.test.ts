import { describe, expect, it } from 'vitest'
import type { MetaIntegration } from '../../../types/index.ts'
import {
    canTest,
    draftFrom,
    inputFrom,
    isDirty,
    normalizeAppId,
    originNote,
    savedNotice,
    updatedLabel,
    validateMeta,
} from './metaIntegration.ts'

const meta = (over: Partial<MetaIntegration> = {}): MetaIntegration => ({
    appId: '1234567890',
    hasAppSecret: true,
    secretUnreadable: false,
    graphVersion: 'v26.0',
    versions: ['v24.0', 'v25.0', 'v26.0'],
    syncPaused: false,
    syncAvailable: true,
    origin: { appId: 'tela', appSecret: 'tela', graphVersion: 'tela' },
    updatedAt: null,
    updatedBy: null,
    ...over,
})

describe('Integração Meta: rascunho e corpo do PUT', () => {
    it('com chave salva, começa mantendo; sem chave (ou ilegível), o campo já vem aberto', () => {
        expect(draftFrom(meta()).secretChoice).toBe('keep')
        expect(draftFrom(meta({ hasAppSecret: false })).secretChoice).toBe('replace')
        expect(draftFrom(meta({ secretUnreadable: true })).secretChoice).toBe('replace')
        expect(draftFrom(meta({ appId: null })).appId).toBe('')
    })

    it('appSecret: null mantém, vazio apaga, texto troca (campo aberto e vazio = manter)', () => {
        const d = draftFrom(meta())
        expect(inputFrom(d)).toEqual({ appId: '1234567890', appSecret: null, graphVersion: 'v26.0', syncPaused: false })
        expect(inputFrom({ ...d, secretChoice: 'remove' }).appSecret).toBe('')
        expect(inputFrom({ ...d, secretChoice: 'replace', secret: '  abc  ' }).appSecret).toBe('abc')
        expect(inputFrom({ ...d, secretChoice: 'replace', secret: ' ' }).appSecret).toBeNull()
    })

    it('ID só com números; chave nova pede o ID', () => {
        expect(normalizeAppId(' 123-456 abc 789 ')).toBe('123456789')
        const d = draftFrom(meta())
        expect(validateMeta(d)).toBeNull()
        expect(validateMeta({ ...d, appId: '123' })).toMatch(/5 a 25/)
        expect(validateMeta({ ...d, appId: '', secretChoice: 'replace', secret: 'x' })).toMatch(/ID do app/)
        expect(validateMeta({ ...d, appId: '', secretChoice: 'remove' })).toBeNull()
    })

    it('testar pede ID e uma chave (a digitada ou a salva)', () => {
        const d = draftFrom(meta())
        expect(canTest(d, meta())).toBe(true)
        expect(canTest({ ...d, appId: '12' }, meta())).toBe(false)
        expect(canTest({ ...d, secretChoice: 'remove' }, meta())).toBe(false)
        const none = meta({ hasAppSecret: false })
        expect(canTest(draftFrom(none), none)).toBe(false)
        expect(canTest({ ...draftFrom(none), secret: 'abc' }, none)).toBe(true)
    })

    it('só salva quando algo mudou', () => {
        const d = draftFrom(meta())
        expect(isDirty(d, meta())).toBe(false)
        expect(isDirty({ ...d, syncPaused: true }, meta())).toBe(true)
        expect(isDirty({ ...d, graphVersion: 'v25.0' }, meta())).toBe(true)
        expect(isDirty({ ...d, secretChoice: 'replace', secret: '' }, meta())).toBe(false)
        expect(isDirty({ ...d, secretChoice: 'replace', secret: 'nova' }, meta())).toBe(true)
        expect(isDirty({ ...d, secretChoice: 'remove' }, meta())).toBe(true)
    })
})

describe('Integração Meta: textos', () => {
    it('de onde vem cada campo', () => {
        expect(originNote('tela', 'appId')).toBe('Salvo aqui.')
        expect(originNote('servidor', 'appSecret')).toMatch(/\.env do servidor/)
        expect(originNote('padrão', 'graphVersion')).toBe('O padrão da API.')
        expect(originNote('nenhum', 'appSecret')).toMatch(/^Sem chave/)
    })

    it('aviso depois de salvar: pausa e retomada têm o seu', () => {
        expect(savedNotice(meta(), meta({ syncPaused: true }))).toMatch(/pausada/)
        expect(savedNotice(meta({ syncPaused: true }), meta())).toMatch(/retomada/)
        expect(savedNotice(meta(), meta({ graphVersion: 'v25.0' }))).toMatch(/salva/)
    })

    it('última alteração: data e quem', () => {
        expect(updatedLabel(meta())).toBeNull()
        const label = updatedLabel(meta({ updatedAt: '2026-11-27T14:05:00-04:00', updatedBy: 'Ana' }))
        expect(label).toMatch(/27\/11\/2026/)
        expect(label).toMatch(/por Ana$/)
    })
})
