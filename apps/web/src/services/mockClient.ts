import type { DataClient } from './client.ts'
import { DataError } from './errors.ts'
import {
    addAuditEvent,
    EXPORT_LABELS,
    exportRowsFor,
    createAccessRequestsStore,
    googleMockEmail,
    noAccessEmails,
    createAccessStore,
    audit,
    billingFor,
    catalog,
    clients,
    createMembersStore,
    defaultFavorites,
    emptyCatalog,
    me,
    meFor,
    onboardingAccess,
    onboardingAudit,
    onboardingBilling,
    onboardingMembers,
    onboardingSources,
    pendenciasFor,
    protocoloFor,
    sources,
    testUsers,
} from './mock/index.ts'
import type { DashboardQuery, Meta } from '../types/index.ts'
import { metaFor } from './mock/helpers.ts'
import { sourceDetailFor } from './mock/sourceDetail.ts'
import { createUnitIn, updateUnitIn } from './mock/units.ts'
import { toCsv } from '../lib/csv.ts'
import { periodLabel } from '../lib/period.ts'

// Simula a rede: um pouco de espera faz o "carregando" aparecer de verdade.
const LATENCY_MS = 300
const wait = () => new Promise((resolve) => setTimeout(resolve, LATENCY_MS))

// Devolve uma cópia: assim uma tela que altere o objeto não estraga o mock das outras.
const copy = <T>(value: T): T => structuredClone(value)

// Sessão fictícia: fica no sessionStorage (sobrevive ao F5, some ao fechar a aba).
const SESSION_KEY = 'lexhub.mock.session'

// Favoritos: ficam no localStorage (sobrevivem a fechar a aba, como na API ficarão no banco).
const FAVORITES_KEY = 'lexhub.mock.favorites'

// Ordem do hub: no localStorage, uma por organização (cada org tem o seu catálogo).
const hubOrderKey = (org: string) => `lexhub.mock.hubOrder.${org}`

// Membros do mock: a lista muda com os convites (volta ao original no F5).
const memberStore = createMembersStore({ name: me.user.name, email: '' })
// Acesso do mock: grava na mesma loja de Membros.
const accessStore = createAccessStore(memberStore)

// Pedidos de acesso do mock: em memória (voltam ao exemplo no F5).
const accessRequests = createAccessRequestsStore()

function requireSession() {
    if (sessionStorage.getItem(SESSION_KEY) === null) {
        throw new DataError(401, 'Sessão expirada ou inexistente')
    }
}

// Logado, mas sem organização (e ainda não aprovado num pedido de acesso).
const withoutAccess = (email: string) => noAccessEmails.includes(email) && !accessRequests.approved(email)

// Quem está logado, do jeito que a loja de pedidos precisa (o banco tira isso do token).
function who() {
    requireSession()
    const email = sessionStorage.getItem(SESSION_KEY) ?? ''
    const blocked = withoutAccess(email)
    return {
        email,
        name: blocked ? 'Pessoa sem acesso' : me.user.name,
        staff: !blocked && me.user.platform_staff,
        hasAccess: !blocked,
    }
}

// Mesma regra da API: organização de que a pessoa não faz parte = 403.
// Devolve true para a organização principal (LexGroup), a única com os dados completos do mock.
function requireOrg(org: string): boolean {
    if (!meFor(org)) throw new DataError(403, 'Você não faz parte desta organização')
    return org === me.org.slug
}

// Mesma regra da API: dashboard fora das unidades liberadas = 403.
function checkAccess(dashboardKey: string, unit: string) {
    const dash = catalog.available.find((d) => d.key === dashboardKey)
    if (!dash || !dash.units.includes(unit)) {
        throw new DataError(403, 'Você não tem acesso a este dashboard nesta unidade')
    }
}

// Módulo: o caminho de toda resposta de dashboard no mock (como a API fará):
// espera, confere sessão (401) e acesso (403), monta os dados da unidade e aplica o período.
// Parâmetros: a key do dashboard, a consulta e a função que monta os dados de uma unidade.
async function dashboardResponse<T extends { meta: Meta }>(
    dashboardKey: string,
    query: DashboardQuery,
    build: (unit: string, query: DashboardQuery) => T,
): Promise<T> {
    await wait()
    requireSession()
    checkAccess(dashboardKey, query.unit)
    const data = build(query.unit, query)
    data.meta.from = query.from ?? data.meta.from
    data.meta.to = query.to ?? data.meta.to
    return data
}

export function createMockClient(): DataClient {
    return {
        // Confere contra os usuários de teste de mock/users.ts (o Supabase fará isso de verdade).
        async signIn(email, password) {
            await wait()
            const ok = testUsers.some((u) => u.email === email.trim().toLowerCase() && u.password === password)
            if (!ok) {
                throw new DataError(401, 'E-mail ou senha incorretos.')
            }
            sessionStorage.setItem(SESSION_KEY, email)
        },

        // Sem Google de verdade: entra direto com a conta de mock/users.ts (sem sair do app).
        async signInWithGoogle() {
            await wait()
            sessionStorage.setItem(SESSION_KEY, googleMockEmail)
            return 'signed-in'
        },

        async signOut() {
            sessionStorage.removeItem(SESSION_KEY)
        },

        async getSessionEmail() {
            return sessionStorage.getItem(SESSION_KEY)
        },

        async getMe(org) {
            await wait()
            requireSession()
            // Mesma regra da API: logado, mas sem nenhuma organização = 403.
            if (withoutAccess(sessionStorage.getItem(SESSION_KEY) ?? '')) {
                throw new DataError(403, 'Sem acesso')
            }
            const found = meFor(org ?? me.org.slug)
            if (!found) throw new DataError(403, 'Você não faz parte desta organização')
            return copy(found)
        },

        async listDashboards(org) {
            await wait()
            requireSession()
            return copy(requireOrg(org) ? catalog : emptyCatalog)
        },

        async listMembers(org) {
            await wait()
            requireSession()
            if (requireOrg(org)) return memberStore.list()
            return onboardingMembers(sessionStorage.getItem(SESSION_KEY) ?? '', me.user.name)
        },

        async inviteMembers(org, invite) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(400, 'No mock, convites só funcionam na LexGroup.')
            return memberStore.invite(invite)
        },

        async setMemberStatus(org, memberId, status) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Você não gere este membro.')
            return memberStore.setStatus(memberId, status, sessionStorage.getItem(SESSION_KEY) ?? '')
        },

        async revokeInvitation(id) {
            await wait()
            requireSession()
            memberStore.revoke(id)
        },

        // Como api.accept_my_invitations: convites do e-mail da sessão viram membro ativo.
        async acceptMyInvitations() {
            const email = sessionStorage.getItem(SESSION_KEY)
            return email ? memberStore.accept(email) : 0
        },

        async listFavorites() {
            await wait()
            requireSession()
            const saved = localStorage.getItem(FAVORITES_KEY)
            return saved ? (JSON.parse(saved) as string[]) : [...defaultFavorites]
        },

        async setFavorite(org, dashboardKey, favorite) {
            const current = await this.listFavorites(org)
            const next = favorite ? [...new Set([...current, dashboardKey])] : current.filter((k) => k !== dashboardKey)
            localStorage.setItem(FAVORITES_KEY, JSON.stringify(next))
        },

        async getHubOrder(org) {
            await wait()
            requireSession()
            const saved = localStorage.getItem(hubOrderKey(org))
            return saved ? (JSON.parse(saved) as string[]) : []
        },

        async setHubOrder(org, keys) {
            requireSession()
            localStorage.setItem(hubOrderKey(org), JSON.stringify(keys))
        },

        // Assentos lidos de Membros (ativos + convites pendentes, sobre a base de 37 do protótipo):
        // convidar alguém muda o número aqui também.
        async getBilling(org) {
            await wait()
            requireSession()
            if (!requireOrg(org)) return copy(onboardingBilling)
            const list = memberStore.list()
            const used = 37 + list.members.filter((m) => m.status === 'active').length + list.invitations.length
            return billingFor({ used, total: 60 })
        },

        async getAccessOverview(org, unit) {
            await wait()
            requireSession()
            return requireOrg(org) ? accessStore.overview(unit) : copy(onboardingAccess)
        },

        // O mock entra como Desenvolvedor: gere acesso e membros e vê as fontes e a auditoria.
        async getMyAdminPermissions(org) {
            requireSession()
            requireOrg(org)
            return { access: true, members: true, sources: true, audit: true }
        },

        async updateMemberAccess(org, memberId, update) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Você não gere o acesso desta pessoa.')
            return accessStore.update(memberId, update, sessionStorage.getItem(SESSION_KEY) ?? '')
        },

        async getAudit(org) {
            await wait()
            requireSession()
            return copy(requireOrg(org) ? audit : onboardingAudit)
        },

        async getSources(org) {
            await wait()
            requireSession()
            return copy(requireOrg(org) ? sources : onboardingSources)
        },

        async getSourceDetail(org, unit, source) {
            await wait()
            requireSession()
            const detail = sourceDetailFor(requireOrg(org) ? sources : onboardingSources, catalog, unit, source)
            if (!detail) throw new DataError(409, 'Esta unidade não usa essa fonte.')
            return copy(detail)
        },

        // O mock entra como Desenvolvedor: pode criar e editar unidades.
        async createUnit(org, unit) {
            await wait()
            requireSession()
            return copy(createUnitIn(requireOrg(org) ? sources : onboardingSources, unit))
        },

        async updateUnit(org, unit) {
            await wait()
            requireSession()
            return copy(updateUnitIn(requireOrg(org) ? sources : onboardingSources, unit))
        },

        // Mesma regra da API: só a equipe RA (platform_staff) vê os clientes.
        async listClients() {
            await wait()
            requireSession()
            if (!me.user.platform_staff) throw new DataError(403, 'Só a equipe RA Tecnologia vê os clientes')
            return copy(clients)
        },

        getProtocolo: (query) => dashboardResponse('protocolo-lexpre', query, protocoloFor),
        getPendencias: (query) => dashboardResponse('pendencias-lexpre', query, pendenciasFor),
        // Sem números fictícios: as telas novas mostram 0/—; os números de verdade vêm da API.
        getDashboardData: <T extends { meta: Meta }>(dashboardKey: string, query: DashboardQuery) =>
            dashboardResponse(dashboardKey, query, (unit) => ({ meta: metaFor(unit), stats: {} }) as unknown as T),

        // Pedidos de acesso: mesmas regras das funções do schema api (ver mock/accessRequests.ts).
        async requestAccess(office, message) {
            await wait()
            return accessRequests.request(who(), office, message)
        },
        async getMyAccessRequest() {
            await wait()
            return accessRequests.mine(who())
        },
        async countPendingAccessRequests() {
            return accessRequests.count(who())
        },
        async listAccessRequests(status) {
            await wait()
            return accessRequests.list(who(), status)
        },
        async getApprovalOptions() {
            await wait()
            return accessRequests.options(who())
        },
        async approveAccessRequest(id, target) {
            await wait()
            return accessRequests.approve(who(), id, target)
        },
        async rejectAccessRequest(id, note) {
            await wait()
            return accessRequests.reject(who(), id, note)
        },

        // Mesmas regras da API: sessão, organização, unidade liberada e can_export; registra na Auditoria.
        // No mock o arquivo é sempre CSV (gerar XLSX exige biblioteca); com a API, vem o formato pedido.
        async exportDashboard({ org, unit, dashboard, format, campos, from, to, filters }) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Você não tem acesso a este dashboard nesta unidade')
            checkAccess(dashboard, unit)
            const summary = catalog.available.find((d) => d.key === dashboard)
            if (!summary?.can_export) throw new DataError(403, 'Você não pode exportar este dashboard')

            const columns = campos.map((slug) => ({ key: slug, label: EXPORT_LABELS[slug] ?? slug }))
            const rows = exportRowsFor(campos, filters)
            const period = from && to ? periodLabel({ from, to }) : 'período padrão'
            addAuditEvent({
                actor: me.user.name,
                kind: 'export',
                action: 'Exportou dados',
                detail: `${summary.title} · ${unit} · ${period} · ${rows.length} linhas · ${format.toUpperCase()}`,
            })
            return {
                blob: new Blob([toCsv(columns, rows)], { type: 'text/csv;charset=utf-8' }),
                filename: `${dashboard}_${unit}.csv`,
                note:
                    format === 'xlsx'
                        ? 'No modo de teste o XLSX sai como CSV. O XLSX de verdade vem da API.'
                        : undefined,
            }
        },
    }
}
