import { useState } from 'react'
import { Modal } from '../../../components/ui/Modal.tsx'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Segmented } from '../../../components/ui/Segmented.tsx'
import { contagemAbas, daAba, type Aba } from './rubricas.ts'

type Demanda = {
    id_demanda: number | string
    cliente: string | null
    situacao: 'resolvido' | 'represado'
    protocolado: boolean
    rubricas: string[]
}

type RubricasModalProps = {
    materia: string // o pacote ("RUBRICAS_REUNIDAS")
    demandas: Demanda[]
    filtered: boolean // a matéria já está no filtro da página
    onToggleFilter?: () => void
    onClose: () => void
}

// Módulo: "Rubricas dentro de <pacote>", como na v1. As demandas do pacote no setor (com o período e os
// filtros da página), por aba, e as rubricas que compõem cada uma.
export function RubricasModal({ materia, demandas, filtered, onToggleFilter, onClose }: RubricasModalProps) {
    const [aba, setAba] = useState<Aba>('todos')
    const n = contagemAbas(demandas)
    const shown = daAba(demandas, aba)

    return (
        <Modal
            className="rubricas-dialog"
            title={
                <span className="rubricas-title">
                    <Icon name="layers" size={20} />
                    Rubricas dentro de {materia}
                </span>
            }
            description="Demandas dessa rubrica reunida no setor, com o período e os filtros da página. Represados = no setor agora, independente do período."
            onClose={onClose}
            footer={
                <>
                    {onToggleFilter && (
                        <button className="btn btn-ghost" type="button" onClick={onToggleFilter}>
                            <Icon name="filter" size={16} />
                            {filtered ? 'Tirar o filtro desta matéria' : 'Filtrar a página por esta matéria'}
                        </button>
                    )}
                    <button className="btn btn-info" type="button" onClick={onClose}>
                        Fechar
                    </button>
                </>
            }
        >
            <Segmented
                label="Situação"
                value={aba}
                onChange={setAba}
                options={[
                    { value: 'todos', label: `Todos (${n.todos})` },
                    { value: 'resolvidos', label: `Resolvidos (${n.resolvidos})` },
                    { value: 'represados', label: `Represados (${n.represados})` },
                    { value: 'protocolados', label: `Protocolados (${n.protocolados})` },
                ]}
            />
            <div className="rubricas-table-wrap">
                <table className="rubricas-table">
                    <thead>
                        <tr>
                            <th scope="col">Demanda</th>
                            <th scope="col">Cliente</th>
                            <th scope="col">Situação</th>
                            <th scope="col">Rubricas</th>
                        </tr>
                    </thead>
                    <tbody>
                        {shown.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="muted small">
                                    Nenhuma demanda nesta aba.
                                </td>
                            </tr>
                        ) : (
                            shown.map((d) => (
                                <tr key={d.id_demanda}>
                                    <td className="num strong">#{d.id_demanda}</td>
                                    <td className="rubricas-cliente">{d.cliente ?? '—'}</td>
                                    <td>
                                        <span className="rubricas-status">
                                            <span
                                                className={`pill tone-${d.situacao === 'represado' ? 'accent' : 'warn'}`}
                                            >
                                                {d.situacao === 'represado' ? 'Represado' : 'Resolvido'}
                                            </span>
                                            {d.protocolado && <span className="pill tone-ok">Protocolado</span>}
                                        </span>
                                    </td>
                                    <td>
                                        {d.rubricas.length === 0 ? (
                                            <span className="muted small">Sem rubricas cadastradas</span>
                                        ) : (
                                            <span className="rubricas-chips">
                                                {d.rubricas.map((r) => (
                                                    <span key={r} className="rubrica-chip">
                                                        {r}
                                                    </span>
                                                ))}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </Modal>
    )
}
