import { PageHeader } from '../components/PageHeader.tsx'
import { StateMessage } from '../components/states/StateMessage.tsx'
import type { NavItem } from '../navigation.ts'

// Página do menu que ainda não tem conteúdo: o cabeçalho de verdade e um aviso.
// Cada página nova troca este componente pelo dela, no App.tsx.
export function ComingSoonPage({ item }: { item: NavItem }) {
    return (
        <>
            <PageHeader title={item.title} description={item.description} />
            <StateMessage icon={item.icon} title="Em construção">
                Esta página segue o protótipo e entra nos próximos passos.
            </StateMessage>
        </>
    )
}
