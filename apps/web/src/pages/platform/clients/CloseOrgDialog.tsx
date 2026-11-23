import { ConfirmDeleteDialog } from '../../../components/ui/ConfirmDeleteDialog.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import type { PlatformClient } from '../../../types/index.ts'
import { orgClosureView } from './orgClosure.ts'

type CloseOrgDialogProps = {
    client: PlatformClient
    onClosed: () => void
    onClose: () => void
}

// Módulo: encerrar organização = busca o impacto no banco e abre a confirmação (o banco confere tudo de novo).
export function CloseOrgDialog({ client, onClosed, onClose }: CloseOrgDialogProps) {
    const { data, error } = useAsync(() => dataClient.getOrgClosureImpact(client.slug), [client.slug])
    return (
        <ConfirmDeleteDialog
            title={`Encerrar ${client.name}`}
            name={client.name}
            nameLabel="o nome da organização"
            confirmLabel="Encerrar organização"
            impact={data && orgClosureView(data)}
            loadError={error?.message}
            onConfirm={async (typed) => {
                await dataClient.closeOrganization(client.slug, typed)
                onClosed()
            }}
            onClose={onClose}
        />
    )
}
