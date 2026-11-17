import { useState } from 'react'
import { Icon } from '../../../components/ui/Icon.tsx'
import { fmt } from '../../../lib/format.ts'
import {
    ITENS_POR_PAGINA,
    ORDENS_LISTA,
    dataBr,
    numeroCnj,
    ordenarLista,
    paginas,
    type OrdemLista,
} from './julgados.ts'
import type { LinhaAcordao } from './types.ts'

const COLUNAS = [
    'Nº Processo',
    'Fase',
    'Subfase',
    'Status 2G',
    'UF',
    'Relator',
    'Data do Acórdão',
    'Status do Acórdão de Embargos',
    'Data do Acórdão de Embargos',
]

// Módulo: a lista "Acórdãos no período" da v1 (JulgadosAcordaoListaTable): as mesmas colunas, a ordem pela data
// do acórdão e 15 por página. A lista inteira vem na resposta: ordenar e paginar é aqui, sem ir à API.
export function AcordaosLista({ itens }: { itens: LinhaAcordao[] }) {
    const [ordem, setOrdem] = useState<OrdemLista>('data_recente')
    // A página vale para a lista em que foi escolhida: chegou outra (período, filtro, Atualizar), volta à 1ª (v1).
    const [paginaDe, setPaginaDe] = useState({ itens, n: 1 })
    const pagina = paginaDe.itens === itens ? paginaDe.n : 1
    const setPagina = (n: number) => setPaginaDe({ itens, n })

    const linhas = ordenarLista(itens, ordem)
    const total = linhas.length
    const totalPaginas = Math.max(1, Math.ceil(total / ITENS_POR_PAGINA))
    const atual = Math.min(pagina, totalPaginas)
    const inicio = (atual - 1) * ITENS_POR_PAGINA
    const visiveis = linhas.slice(inicio, inicio + ITENS_POR_PAGINA)

    return (
        <section className="card jl-lista" aria-labelledby="jl-lista-titulo">
            <div className="jl-lista-head">
                <h3 className="jl-lista-titulo" id="jl-lista-titulo">
                    <Icon name="scale" size={16} />
                    Acórdãos no período
                </h3>
            </div>
            <div className="jl-lista-bar">
                <span className="muted small num">
                    {fmt.int(total)} {total === 1 ? 'acórdão' : 'acórdãos'}
                </span>
                <label className="field-select jl-ordenar">
                    <span className="muted small">Ordenar:</span>
                    <select
                        value={ordem}
                        onChange={(e) => {
                            setOrdem(e.target.value as OrdemLista)
                            setPagina(1)
                        }}
                    >
                        {ORDENS_LISTA.map((o) => (
                            <option key={o.value} value={o.value}>
                                {o.label}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            <div className="tblwrap">
                <table className="tbl jl-tbl">
                    <thead>
                        <tr>
                            {COLUNAS.map((c) => (
                                <th key={c} scope="col">
                                    {c}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {visiveis.length === 0 ? (
                            <tr>
                                <td colSpan={COLUNAS.length} className="muted jl-vazio">
                                    Não há acórdãos no período selecionado.
                                </td>
                            </tr>
                        ) : (
                            visiveis.map((r, i) => (
                                <tr key={r.id ?? `${r.numero_processo}-${inicio + i}`}>
                                    <td className="num nowrap jl-processo">{numeroCnj(r.numero_processo)}</td>
                                    <td>{r.fase}</td>
                                    <td>{r.subfase}</td>
                                    <td>{r.status_2g}</td>
                                    <td className="nowrap">{r.uf}</td>
                                    <td>{r.relator}</td>
                                    <td className="num nowrap">{dataBr(r.data_acordao)}</td>
                                    <td>{r.status_acordao_embargos}</td>
                                    <td className="num nowrap">{dataBr(r.data_acordao_embargos)}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {total > 0 && (
                <nav className="jl-pager" aria-label="Páginas da lista de acórdãos">
                    <span className="muted small num">
                        {fmt.int(inicio + 1)}–{fmt.int(Math.min(inicio + ITENS_POR_PAGINA, total))} de {fmt.int(total)}
                    </span>
                    <span className="jl-pager-btns">
                        <button
                            type="button"
                            className="btn btn-sm"
                            disabled={atual <= 1}
                            onClick={() => setPagina(atual - 1)}
                        >
                            Anterior
                        </button>
                        {paginas(atual, totalPaginas).map((n) => (
                            <button
                                key={n}
                                type="button"
                                className={n === atual ? 'btn btn-sm on' : 'btn btn-sm'}
                                aria-current={n === atual ? 'page' : undefined}
                                aria-label={`Página ${n}`}
                                onClick={() => setPagina(n)}
                            >
                                {n}
                            </button>
                        ))}
                        <button
                            type="button"
                            className="btn btn-sm"
                            disabled={atual >= totalPaginas}
                            onClick={() => setPagina(atual + 1)}
                        >
                            Próxima
                        </button>
                    </span>
                </nav>
            )}
        </section>
    )
}
