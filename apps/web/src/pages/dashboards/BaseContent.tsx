import { StateMessage } from '../../components/states/StateMessage.tsx'

// Módulo: o miolo de um dashboard que ainda não tem conteúdo na V2.
// O cabeçalho (título, unidade, atualização) já vem do DashboardView; só o meio é provisório.
export function BaseContent() {
    return (
        <StateMessage icon="inbox" title="Em construção">
            Os números deste dashboard ainda estão na v1. A página da V2 entra aqui quando eles baterem com a v1.
        </StateMessage>
    )
}
