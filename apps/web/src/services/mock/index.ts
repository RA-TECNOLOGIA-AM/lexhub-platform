// Porta de entrada do mock: quem está de fora importa daqui, sem saber dos arquivos internos.
export { catalog } from './catalog.ts'
export { pendenciasFor } from './pendencias.ts'
export { protocoloFor } from './protocolo.ts'
export { googleMockEmail, me, meFor, noAccessEmails, orgs, testUsers } from './users.ts'
export { defaultFavorites } from './favorites.ts'
export { createMembersStore, members } from './members.ts'
export { billingFor, plans } from './billing.ts'
export { access } from './access.ts'
export { addAuditEvent, audit } from './audit.ts'
export { clients } from './clients.ts'
export {
    emptyCatalog,
    onboardingAccess,
    onboardingAudit,
    onboardingBilling,
    onboardingMembers,
    onboardingSources,
} from './emptyOrg.ts'
export { sources } from './sources.ts'
export { EXPORT_LABELS, exportRowsFor } from './exportRows.ts'
