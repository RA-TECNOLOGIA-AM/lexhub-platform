import type { IconName } from './components/ui/Icon.tsx'

// Uma página do app: o item do menu, a rota e o texto do cabeçalho saem daqui.
export type NavItem = {
    key: string
    label: string // texto no menu
    title: string // título da página
    description: string // linha abaixo do título
    icon: IconName
    route: string // padrão da rota; ':org' vira a organização ativa
    active?: (pathname: string) => boolean // quando a regra "começa com a rota" não basta
}

export type NavSection = { title: string; items: NavItem[]; platformOnly?: boolean }

// Módulo: o mapa do app. Menu, breadcrumb e rotas leem esta lista; página nova = um item aqui.
export const NAV_SECTIONS: NavSection[] = [
    {
        title: 'Espaço de trabalho',
        items: [
            {
                key: 'dashboards',
                label: 'Dashboards',
                title: 'Dashboards',
                description: '',
                icon: 'grid',
                route: '/:org/dashboards',
                // Hub e cada dashboard (/:org/:unit/dashboards/:key) contam como "Dashboards".
                active: (pathname) => pathname.includes('/dashboards'),
            },
        ],
    },
    {
        title: 'Administração',
        items: [
            {
                key: 'membros',
                label: 'Membros',
                title: 'Membros',
                description: 'Quem faz parte da organização. Todos entram por convite ou pedido aprovado.',
                icon: 'users',
                route: '/:org/admin/membros',
            },
            {
                key: 'acesso',
                label: 'Acesso',
                title: 'Acesso',
                description:
                    'O papel diz o que a pessoa pode fazer. A equipe e as unidades dizem quais dashboards ela vê.',
                icon: 'shield',
                route: '/:org/admin/acesso',
            },
            {
                key: 'unidades',
                label: 'Unidades e fontes',
                title: 'Unidades e fontes de dados',
                description: 'As unidades da organização e as fontes que alimentam os dashboards.',
                icon: 'plug',
                route: '/:org/admin/unidades',
            },
            {
                key: 'auditoria',
                label: 'Auditoria',
                title: 'Auditoria',
                description: 'Entradas, exportações, mudanças de acesso e sessões de suporte.',
                icon: 'clock',
                route: '/:org/admin/auditoria',
            },
            {
                key: 'plano',
                label: 'Plano e cobrança',
                title: 'Plano e cobrança',
                description: 'O plano da organização, o uso e as faturas.',
                icon: 'receipt',
                route: '/:org/admin/plano',
            },
        ],
    },
    {
        title: 'Plataforma · equipe RA',
        platformOnly: true,
        items: [
            {
                key: 'clientes',
                label: 'Clientes',
                title: 'Clientes',
                description: 'As organizações atendidas pela plataforma.',
                icon: 'building',
                route: '/plataforma/clientes',
            },
        ],
    },
]

// Endereço de verdade de um item: '/:org/admin/membros' -> '/lexgroup/admin/membros'.
export const pathOf = (item: NavItem, org: string) => item.route.replace(':org', org)

// O item da página atual (para marcar o menu e montar o breadcrumb).
export function activeItem(pathname: string, org: string): { section: NavSection; item: NavItem } | null {
    for (const section of NAV_SECTIONS) {
        for (const item of section.items) {
            const isActive = item.active ? item.active(pathname) : pathname.startsWith(pathOf(item, org))
            if (isActive) return { section, item }
        }
    }
    return null
}
