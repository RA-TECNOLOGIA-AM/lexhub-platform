import type { DataClient, DeviceSession } from './client.ts'
import { actorsOf } from '../pages/admin/audit/auditView.ts'
import { DataError } from './errors.ts'
import {
    addAuditEvent,
    EXPORT_LABELS,
    exportRowsFor,
    createAccessRequestsStore,
    createNotificationsStore,
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
    peticionamentoFor,
    orgDocumentosFor,
    comercialFor,
    sources,
    testUsers,
} from './mock/index.ts'
import type { DashboardCatalog, DashboardQuery, Meta } from '../types/index.ts'
import { metaFor } from './mock/helpers.ts'
import { orgDocumentosLegadoFor } from './mock/orgDocumentosLegado.ts'
import { pendenciasLegadoFor } from './mock/pendenciasLegado.ts'
import { financeiroEstrategicoFor } from './mock/financeiroEstrategico.ts'
import { acordosFor, execucaoFor } from './mock/execucao.ts'
import { execucaoEstrategicoFor } from './mock/execucaoEstrategico.ts'
import { ticketsFor } from './mock/tickets.ts'
import { recursalFor } from './mock/recursal.ts'
import { publicacoesFor } from './mock/publicacoes.ts'
import { intermediariasFor } from './mock/intermediarias.ts'
import { emendasFor } from './mock/emendas.ts'
import { replicasFor } from './mock/replicas.ts'
import { controleFor } from './mock/controle.ts'
import { sobrevivenciaFor } from './mock/sobrevivencia.ts'
import { previsaoFor } from './mock/previsao.ts'
import { julgadosAcordaosFor } from './mock/julgadosAcordaos.ts'
import { julgadosSentencasFor } from './mock/julgadosSentencas.ts'
import { metaAnualFor } from './mock/metaAnual.ts'
import { preProtocoloFor } from './mock/preProtocolo.ts'
import { peticionamentoLegadoFor } from './mock/peticionamentoLegado.ts'
import { protocoloLegadoFor } from './mock/protocoloLegado.ts'
import { sourceDetailFor } from './mock/sourceDetail.ts'
import { createUnitIn, updateUnitIn } from './mock/units.ts'
import { linkOfficeIn, productOffices } from './mock/offices.ts'
import {
    changeSecretIn,
    connectIn,
    disconnectIn,
    EGRESS_IP_EXEMPLO,
    inspectSheetIn,
    requireSourceOn,
    retestIn,
    setEnabledIn,
} from './mock/connections.ts'
import { toCsv } from '../lib/csv.ts'
import { periodLabel } from '../lib/period.ts'

// Simula a rede: um pouco de espera faz o "carregando" aparecer de verdade.
const LATENCY_MS = 300
const wait = () => new Promise((resolve) => setTimeout(resolve, LATENCY_MS))

// Devolve uma cópia: assim uma tela que altere o objeto não estraga o mock das outras.
const copy = <T>(value: T): T => structuredClone(value)

// Sessão fictícia: fica no sessionStorage (sobrevive ao F5, some ao fechar a aba).
const SESSION_KEY = 'lexhub.mock.session'
// Dashboards abertos (mock): última abertura por unidade/dashboard, para ignorar repetição em < 5 min.
const VIEW_REPEAT_MS = 5 * 60 * 1000
const lastViews = new Map<string, number>()

// Foto de perfil do mock (data URL), no localStorage.
const AVATAR_KEY = 'lexhub.mock.avatar'

// Favoritos: ficam no localStorage (sobrevivem a fechar a aba, como na API ficarão no banco).
const FAVORITES_KEY = 'lexhub.mock.favorites'

// Ordem do hub: no localStorage, uma por organização (cada org tem o seu catálogo).
const hubOrderKey = (org: string) => `lexhub.mock.hubOrder.${org}`

// Dashboards desligados por unidade (o usuário do mock é Desenvolvedor): no localStorage, como "key:unidade".
const DASHBOARDS_OFF_KEY = 'lexhub.mock.dashboardsOff'
function dashboardsOff(): string[] {
    try {
        return JSON.parse(localStorage.getItem(DASHBOARDS_OFF_KEY) ?? '[]') as string[]
    } catch {
        return []
    }
}
// O catálogo como a API manda para o Dev: as unidades desligadas marcadas e o menu de ligar/desligar.
function catalogForDev(): DashboardCatalog {
    const off = dashboardsOff()
    return {
        ...catalog,
        available: catalog.available.map((d) => ({
            ...d,
            disabled_units: d.units.filter((u) => off.includes(`${d.key}:${u}`)),
            can_toggle: true,
        })),
    }
}

// Membros do mock: a lista muda com os convites (volta ao original no F5).
const memberStore = createMembersStore({ name: me.user.name, email: '' })
// Acesso do mock: grava na mesma loja de Membros.
const accessStore = createAccessStore(memberStore)

// Pedidos de acesso do mock: em memória (voltam ao exemplo no F5).
const accessRequests = createAccessRequestsStore()
// Notificações do mock: em memória (somem no F5). Aprovar um pedido avisa quem pediu (como o gatilho do banco).
const notifications = createNotificationsStore()

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
    requireSourceOn(dashboardKey, query.unit)
    const data = build(query.unit, query)
    data.meta.from = query.from ?? data.meta.from
    data.meta.to = query.to ?? data.meta.to
    return data
}

// Dashboards que têm resposta fictícia completa no mock (key -> montagem).
const MOCK_COMPLETO: Record<string, (unit: string, query: DashboardQuery) => unknown> = {
    'peticionamento-lexpre': peticionamentoFor,
    'org-documentos-lexpre': orgDocumentosFor,
    'comercial-lexpre': comercialFor,
    'comissao-lexpre': comercialFor, // a v1 usava o mesmo endpoint do Comercial
    protocolo: protocoloLegadoFor,
    peticionamento: peticionamentoLegadoFor,
    'org-documentos': orgDocumentosLegadoFor,
    pendencias: pendenciasLegadoFor,
    'pre-protocolo': preProtocoloFor,
    'meta-anual': metaAnualFor,
    'financeiro-estrategico': financeiroEstrategicoFor,
    execucao: execucaoFor,
    acordos: acordosFor,
    'execucao-estrategico': execucaoEstrategicoFor,
    tickets: ticketsFor,
    recursal: recursalFor,
    publicacoes: publicacoesFor,
    'pendencias-intermediarias': intermediariasFor,
    'emendas-manifestacoes': emendasFor,
    replicas: replicasFor,
    'controle-processos': controleFor,
    'sobrevivencia-processual': sobrevivenciaFor,
    'previsao-individualizada': previsaoFor,
    'julgados-acordaos': julgadosAcordaosFor,
    'julgados-sentencas': julgadosSentencasFor,
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
        async signInWithGoogle(_returnTo) {
            await wait()
            sessionStorage.setItem(SESSION_KEY, googleMockEmail)
            return 'signed-in'
        },

        async signOut() {
            sessionStorage.removeItem(SESSION_KEY)
        },

        // No mock não há outros aparelhos: só confirma.
        async signOutOthers() {
            await wait()
        },
        async isSessionAlive() {
            return sessionStorage.getItem(SESSION_KEY) !== null
        },

        async getSessionEmail() {
            return sessionStorage.getItem(SESSION_KEY)
        },

        async getSessionAccessToken() {
            throw new DataError(501, 'Login por dispositivo só está disponível no modo API.')
        },

        async createDeviceCode() {
            throw new DataError(501, 'Login por dispositivo só está disponível no modo API.')
        },

        async pollDeviceToken() {
            throw new DataError(501, 'Login por dispositivo só está disponível no modo API.')
        },

        async authorizeDevice() {
            throw new DataError(501, 'Login por dispositivo só está disponível no modo API.')
        },

        async setDeviceSession(_session: DeviceSession) {
            throw new DataError(501, 'Login por dispositivo só está disponível no modo API.')
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
            const result = copy(found)
            result.user.avatar_path = localStorage.getItem(AVATAR_KEY)
            return result
        },

        async listDashboards(org) {
            await wait()
            requireSession()
            return copy(requireOrg(org) ? catalogForDev() : emptyCatalog)
        },

        async setDashboardEnabled(org, unit, dashboardKey, enabled) {
            await wait()
            requireSession()
            const dash = catalog.available.find((d) => d.key === dashboardKey)
            if (!requireOrg(org) || !dash?.units.includes(unit)) {
                throw new DataError(404, 'Este dashboard não existe nesta unidade.')
            }
            const id = `${dashboardKey}:${unit}`
            const others = dashboardsOff().filter((x) => x !== id)
            localStorage.setItem(DASHBOARDS_OFF_KEY, JSON.stringify(enabled ? others : [...others, id]))
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
            return billingFor(used)
        },

        async getAccessOverview(org, unit) {
            await wait()
            requireSession()
            return requireOrg(org) ? accessStore.overview(unit) : copy(onboardingAccess)
        },

        // O mock entra como Desenvolvedor da LexGroup: gere acesso e membros e vê fontes, auditoria, cobrança e clientes.
        async getMyAdminPermissions(org) {
            requireSession()
            requireOrg(org)
            return { access: true, members: true, sources: true, audit: true, billing: true, clients: true }
        },

        async updateMemberAccess(org, memberId, update) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Você não gere o acesso desta pessoa.')
            return accessStore.update(memberId, update, sessionStorage.getItem(SESSION_KEY) ?? '')
        },

        async setTeamGroups(org, teamId, groups, seesAll) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Você não gere esta equipe.')
            accessStore.setTeamGroups(teamId, groups, seesAll)
        },

        // Filtra como o banco: período [from, to), tipo e pessoa (datas comparadas como instantes, não como texto).
        // actors = quem aparece no período/tipo, antes do filtro de pessoa.
        async getAudit(org, query) {
            await wait()
            requireSession()
            const all = requireOrg(org) ? audit : onboardingAudit
            const time = (iso: string) => new Date(iso).getTime()
            const events = all.events.filter(
                (e) =>
                    (!query.from || time(e.at) >= time(query.from)) &&
                    (!query.to || time(e.at) < time(query.to)) &&
                    (!query.kind || e.kind === query.kind),
            )
            return copy({
                events: events.filter((e) => !query.actor || e.actor === query.actor),
                truncated: false,
                actors: actorsOf(events),
            })
        },

        // Como o banco: a mesma pessoa/dashboard/unidade em menos de 5 min não grava de novo.
        async logDashboardView(org, unit, dashboardKey) {
            requireSession()
            if (!requireOrg(org)) return
            const key = `${unit}/${dashboardKey}`
            const last = lastViews.get(key) ?? 0
            if (Date.now() - last < VIEW_REPEAT_MS) return
            lastViews.set(key, Date.now())
            const name = catalog.available.find((d) => d.key === dashboardKey)?.title ?? dashboardKey
            addAuditEvent({
                actor: 'Você',
                email: sessionStorage.getItem(SESSION_KEY) || null,
                kind: 'view',
                action: 'Abriu dashboard',
                detail: `${name} · ${unit}`,
            })
        },

        async logAuditExport(org, filter, rows) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Só Owner ou Desenvolvedor exportam a auditoria.')
            addAuditEvent({
                actor: 'Você',
                email: sessionStorage.getItem(SESSION_KEY) || null,
                kind: 'export',
                action: 'Exportou a auditoria',
                detail: [`${rows} eventos`, filter.kind, filter.actor, 'CSV'].filter(Boolean).join(' · '),
            })
        },

        async getSources(org) {
            await wait()
            requireSession()
            return copy(requireOrg(org) ? sources : onboardingSources)
        },

        // No mock, a "hora do cache" é a syncedAt das fontes fictícias (a API real lê a memória do processo).
        async getSourcesFreshness(org, keys) {
            await wait()
            requireSession()
            const all = (requireOrg(org) ? sources : onboardingSources).units.flatMap((u) => u.sources)
            return Object.fromEntries(
                keys.map((key) => {
                    const s = all.find((x) => x.id === key)
                    const fetchedAt = s?.syncedAt ?? null
                    const error = s && s.failures > 0 ? 'SourceUnavailable' : null
                    return [
                        key,
                        { fetchedAt, cacheMin: key === 'lexflow' ? 15 : 5, error, errorAt: error ? fetchedAt : null },
                    ]
                }),
            )
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

        // O mock entra como Desenvolvedor da LexGroup: conecta fontes em qualquer organização.
        async listProductOffices(product) {
            await wait()
            requireSession()
            return copy(productOffices[product])
        },

        async linkProductOffice(org, unit, product, ref) {
            await wait()
            requireSession()
            const own = requireOrg(org)
            return copy(linkOfficeIn(own ? sources : onboardingSources, own ? 'LexGroup' : org, unit, product, ref))
        },

        async getConnectInfo() {
            await wait()
            requireSession()
            return { ready: true, egressIp: EGRESS_IP_EXEMPLO }
        },

        async inspectSheet(url) {
            await wait()
            requireSession()
            return inspectSheetIn(url)
        },

        async connectSource(org, unit, input) {
            await wait()
            requireSession()
            return copy(connectIn(requireOrg(org) ? sources : onboardingSources, unit, input))
        },

        async retestSource(org, source) {
            await wait()
            requireSession()
            requireOrg(org)
            return retestIn(source)
        },

        async changeSourceSecret(org, source, input) {
            await wait()
            requireSession()
            return copy(changeSecretIn(requireOrg(org) ? sources : onboardingSources, source, input))
        },

        async disconnectSource(org, source) {
            await wait()
            requireSession()
            disconnectIn(requireOrg(org) ? sources : onboardingSources, source)
        },

        async setSourceEnabled(org, source, enabled) {
            await wait()
            requireSession()
            return copy(setEnabledIn(requireOrg(org) ? sources : onboardingSources, source, enabled))
        },

        // Mesma regra da API: só a equipe RA (platform_staff) vê os clientes.
        async listClients() {
            await wait()
            requireSession()
            if (!me.user.platform_staff) throw new DataError(403, 'Só a equipe RA Tecnologia vê os clientes')
            return copy(clients)
        },

        // No mock: as fontes fictícias com falha seguida, na LexGroup (as outras organizações não têm fontes).
        async getFailingSources() {
            await wait()
            requireSession()
            if (!me.user.platform_staff) throw new DataError(403, 'Só a TI da LexGroup vê as fontes dos clientes')
            const all = sources.units.flatMap((u) => u.sources)
            const failing = [...new Set(all.filter((s) => s.failures > 0 && s.status !== 'disabled').map((s) => s.id))]
            return { lexgroup: failing }
        },

        getProtocolo: (query) => dashboardResponse('protocolo-lexpre', query, protocoloFor),
        getPendencias: (query) => dashboardResponse('pendencias-lexpre', query, pendenciasFor),
        // Sem números fictícios: as telas novas mostram 0/—; os números de verdade vêm da API.
        getDashboardData: <T extends { meta: Meta }>(dashboardKey: string, query: DashboardQuery) =>
            dashboardResponse(dashboardKey, query, (unit, q) => {
                // Dashboards com dados fictícios completos; os demais, só o `meta` e `stats` vazio.
                const completo = MOCK_COMPLETO[dashboardKey]
                return (completo ? completo(unit, q) : { meta: metaFor(unit), stats: {} }) as unknown as T
            }),

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
            const approved = accessRequests.approve(who(), id, target)
            // O mock só tem a organização principal com dados: o link leva para ela.
            notifications.add(approved.email, {
                kind: 'access_request.approved',
                title: 'Seu acesso foi aprovado',
                body: `Você agora faz parte de ${me.org.name}.`,
                link: `/${me.org.slug}/dashboards`,
            })
            return approved
        },
        async rejectAccessRequest(id, note) {
            await wait()
            return accessRequests.reject(who(), id, note)
        },

        async listMyNotifications() {
            await wait()
            return notifications.list(who().email)
        },
        async markNotificationsRead(ids) {
            notifications.markRead(who().email, ids)
        },

        // Foto de perfil: no mock, a própria imagem (data URL) fica no localStorage e vira o avatar_path.
        async uploadMyAvatar(image) {
            await wait()
            requireSession()
            const path = await new Promise<string>((resolve, reject) => {
                const reader = new FileReader()
                reader.onload = () => resolve(String(reader.result))
                reader.onerror = () => reject(new DataError(0, 'Não foi possível ler a foto.'))
                reader.readAsDataURL(image)
            })
            localStorage.setItem(AVATAR_KEY, path)
            return path
        },
        async removeMyAvatar() {
            await wait()
            requireSession()
            localStorage.removeItem(AVATAR_KEY)
        },
        avatarUrl: (path) => path,

        // Mesmas regras da API: sessão, organização, unidade liberada e can_export; registra na Auditoria.
        // No mock o arquivo é sempre CSV (gerar XLSX exige biblioteca); com a API, vem o formato pedido.
        async exportDashboard({ org, unit, dashboard, format, campos, from, to, filters }) {
            await wait()
            requireSession()
            if (!requireOrg(org)) throw new DataError(403, 'Você não tem acesso a este dashboard nesta unidade')
            checkAccess(dashboard, unit)
            const summary = catalog.available.find((d) => d.key === dashboard)
            if (!summary?.can_export) throw new DataError(403, 'Você não pode exportar este dashboard')

            // Relatório com partes (ex.: 'condenacao.numero_processo'): no mock, o campo sem o prefixo, num CSV só.
            const base = campos.map((slug) => slug.slice(slug.indexOf('.') + 1))
            const columns = base.map((slug) => ({ key: slug, label: EXPORT_LABELS[slug] ?? slug }))
            const rows = exportRowsFor(base, filters)
            const period = from && to ? periodLabel({ from, to }) : 'período padrão'
            addAuditEvent({
                actor: me.user.name,
                email: sessionStorage.getItem(SESSION_KEY) || null,
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
