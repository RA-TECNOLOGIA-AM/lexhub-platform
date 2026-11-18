import { useState, type CSSProperties } from 'react'
import { Modal } from '../../../components/ui/Modal.tsx'
import { fmt } from '../../../lib/format.ts'
import { contarPorCampo, numeroCnj } from './julgados.ts'
import type { DadoFaltando } from './types.ts'

// Módulo: a faixa "Atenção" da v1 (DadosFaltandoBanner): os avisos de qualidade dos dados (do histórico todo, não
// só do período) passando em letreiro; clicar abre o modal com cada processo e a informação que falta preencher.
// Sem aviso, não mostra nada. Quem pediu menos movimento no sistema vê os avisos parados, um embaixo do outro.
// base: de quem é a base no texto ('acórdãos'; no Julgados Sentenças, 'sentenças').
export function DadosFaltando({
    avisos,
    itens,
    base = 'acórdãos',
}: {
    avisos: string[]
    itens: DadoFaltando[]
    base?: string
}) {
    const [aberto, setAberto] = useState(false)
    if (avisos.length === 0) return null

    return (
        <>
            <button
                type="button"
                className="jl-atencao"
                title={`Toda a base de ${base}, sem o filtro de período. Clique para ver os processos e a informação que falta preencher`}
                onClick={() => setAberto(true)}
            >
                <span className="jl-letreiro" style={{ '--dur': `${14 * avisos.length}s` } as CSSProperties}>
                    {avisos.map((a) => (
                        <span key={a}>⚠️ Atenção ⚠️! {a}</span>
                    ))}
                </span>
            </button>
            {aberto && <DadosFaltandoModal itens={itens} base={base} onClose={() => setAberto(false)} />}
        </>
    )
}

function DadosFaltandoModal({ itens, base, onClose }: { itens: DadoFaltando[]; base: string; onClose: () => void }) {
    const [campo, setCampo] = useState<string | null>(null)
    const campos = contarPorCampo(itens)
    const visiveis = campo ? itens.filter((i) => i.campo === campo) : itens

    return (
        <Modal
            title="Processos com informação faltando"
            subtitle={`${fmt.int(visiveis.length)}${campo ? ` de ${fmt.int(itens.length)}` : ''} ocorrência${visiveis.length === 1 ? '' : 's'} em toda a base de ${base} (sem o filtro de período) — preencha esses campos no sistema de origem.`}
            className="jl-modal"
            onClose={onClose}
        >
            {campos.length > 1 && (
                <div className="pills jl-campos" role="group" aria-label="Informação faltando">
                    <button type="button" className="pill" aria-pressed={campo === null} onClick={() => setCampo(null)}>
                        Todos ({fmt.int(itens.length)})
                    </button>
                    {campos.map(([nome, n]) => (
                        <button
                            key={nome}
                            type="button"
                            className="pill"
                            aria-pressed={campo === nome}
                            onClick={() => setCampo(campo === nome ? null : nome)}
                        >
                            {nome} ({fmt.int(n)})
                        </button>
                    ))}
                </div>
            )}
            <div className="tblwrap jl-modal-tbl">
                <table className="tbl">
                    <thead>
                        <tr>
                            <th scope="col">Nº Processo</th>
                            <th scope="col">Informação faltando</th>
                        </tr>
                    </thead>
                    <tbody>
                        {visiveis.length === 0 ? (
                            <tr>
                                <td colSpan={2} className="muted jl-vazio">
                                    Nenhum processo com informação faltando.
                                </td>
                            </tr>
                        ) : (
                            visiveis.map((item, i) => (
                                <tr key={`${item.numero_processo}-${item.campo}-${i}`}>
                                    <td className="num nowrap jl-processo">{numeroCnj(item.numero_processo)}</td>
                                    <td>{item.campo}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </Modal>
    )
}
