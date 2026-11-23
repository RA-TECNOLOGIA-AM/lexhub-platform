import { ConfirmDeleteDialog } from '../../../components/ui/ConfirmDeleteDialog.tsx'
import { useAsync } from '../../../hooks/useAsync.ts'
import { dataClient } from '../../../services/client.ts'
import { unitDeletionView } from './unitDeletion.ts'

type DeleteUnitDialogProps = {
    org: string
    unit: { code: string; name: string }
    onDeleted: () => void
    onClose: () => void
}

// Módulo: excluir unidade = busca o impacto no banco e abre a confirmação (o banco confere tudo de novo).
export function DeleteUnitDialog({ org, unit, onDeleted, onClose }: DeleteUnitDialogProps) {
    const { data, error } = useAsync(() => dataClient.getUnitDeletionImpact(org, unit.code), [org, unit.code])
    return (
        <ConfirmDeleteDialog
            title={`Excluir ${unit.name}`}
            name={unit.name}
            nameLabel="o nome da unidade"
            confirmLabel="Excluir unidade"
            impact={data && unitDeletionView(data)}
            loadError={error?.message}
            onConfirm={async (typed) => {
                await dataClient.deleteUnit(org, unit.code, typed)
                onDeleted()
            }}
            onClose={onClose}
        />
    )
}
