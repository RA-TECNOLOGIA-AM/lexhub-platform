import type { AuditEvent, AuditResponse } from '../../types/index.ts'

// Os eventos do protótipo (canvas "LexHub v2 — protótipo", tela Auditoria), no horário de Manaus.
export const audit: AuditResponse = {
    events: [
        {
            id: 'ev6',
            at: '2026-10-30T14:02:00-04:00',
            actor: 'Ana Ribeiro',
            kind: 'access',
            action: 'Convidou 2 pessoas',
            detail: 'Colaborador · NG · equipe Protocolo',
        },
        {
            id: 'ev5',
            at: '2026-10-30T13:47:00-04:00',
            actor: 'Suporte RA Tecnologia',
            kind: 'support',
            action: 'Sessão de suporte',
            detail: 'Somente leitura · 1 h · motivo: conferir divergência no Protocolo',
        },
        {
            id: 'ev4',
            at: '2026-10-30T11:20:00-04:00',
            actor: 'Bruno Melo',
            kind: 'export',
            action: 'Exportou dados',
            detail: 'Funil comercial · NG · 1 a 29/10 · 1.184 linhas',
        },
        {
            id: 'ev3',
            at: '2026-10-30T09:05:00-04:00',
            actor: 'Ana Ribeiro',
            kind: 'access',
            action: 'Mudou regra de acesso',
            detail: 'Equipe Comercial passou a ver Marketing',
        },
        {
            id: 'ev2',
            at: '2026-10-29T18:31:00-04:00',
            actor: 'Sistema',
            kind: 'source',
            action: 'Fonte atrasada',
            detail: 'LexPre · escritório 1 · 2 falhas seguidas',
        },
        {
            id: 'ev1',
            at: '2026-10-29T08:12:00-04:00',
            actor: 'Carla Souza',
            kind: 'login',
            action: 'Entrou com Google',
            detail: 'Navegador Chrome · Manaus',
        },
    ],
}

// Evento novo (ex.: uma exportação) entra no topo da lista, como a API fará. Volta ao original no F5.
export function addAuditEvent(event: Omit<AuditEvent, 'id' | 'at'>) {
    audit.events.unshift({ ...event, id: `ev-${Date.now()}`, at: new Date().toISOString() })
}
