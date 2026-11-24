import { useState, type CSSProperties } from 'react'
import { useParams } from 'react-router'
import { Icon } from '../../../components/ui/Icon.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { saveFile } from '../../../lib/download.ts'
import { fmt } from '../../../lib/format.ts'
import { dataClient } from '../../../services/client.ts'
import { SUPPORT_READ_ONLY } from '../../../lib/supportSession.ts'
import { useSupportSession } from '../../../contexts/support-context.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { contarPorCampo, numeroCnj } from './julgados.ts'
import type { DadoFaltando } from './types.ts'
import './DadosFaltando.css'

// Módulo: a faixa "Atenção" da v1 (DadosFaltandoBanner): os avisos de qualidade dos dados (do histórico todo, não
// só do período) passando em letreiro; clicar abre o modal com cada processo e a informação que falta preencher.
// Sem aviso, não mostra nada. Quem pediu menos movimento no sistema vê os avisos parados, um embaixo do outro.
// base: de quem é a base no texto ('acórdãos'; no Julgados Sentenças, 'sentenças').
// relatorio: o relatório do dashboard (?relatorio=) que baixa a lista em XLSX, uma aba por informação faltando
// (ex.: 'campos-faltando' na Execução), com os filtros da página; sem = o modal não tem o botão.
export function DadosFaltando({
    avisos,
    itens,
    base = 'acórdãos',
    relatorio,
    filters,
}: {
    avisos: string[]
    itens: DadoFaltando[]
    base?: string
    relatorio?: string
    filters?: DashboardFilters
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
            {aberto && (
                <DadosFaltandoModal
                    itens={itens}
                    base={base}
                    relatorio={relatorio}
                    filters={filters}
                    onClose={() => setAberto(false)}
                />
            )}
        </>
    )
}

function DadosFaltandoModal({
    itens,
    base,
    relatorio,
    filters,
    onClose,
}: {
    itens: DadoFaltando[]
    base: string
    relatorio?: string
    filters?: DashboardFilters
    onClose: () => void
}) {
    const { org = '', unit = '', dashboardKey = '' } = useParams()
    const [campo, setCampo] = useState<string | null>(null)
    const [baixando, setBaixando] = useState(false)
    const [erro, setErro] = useState<string | null>(null)
    const support = useSupportSession() // modo suporte: baixar o relatório é exportar (só leitura)
    const campos = contarPorCampo(itens)
    const visiveis = campo ? itens.filter((i) => i.campo === campo) : itens

    // O relatório para preencher: uma aba por informação faltando (o servidor monta, com os filtros da página).
    async function baixar() {
        if (!relatorio) return
        setBaixando(true)
        setErro(null)
        try {
            const file = await dataClient.exportDashboard({
                org,
                unit,
                filters,
                dashboard: dashboardKey,
                format: 'xlsx',
                campos: [],
                relatorio,
            })
            saveFile(file.blob, file.filename)
        } catch (e) {
            setErro(e instanceof Error ? e.message : 'Não foi possível gerar o relatório.')
        } finally {
            setBaixando(false)
        }
    }

    return (
        <Modal
            title="Processos com informação faltando"
            subtitle={`${fmt.int(visiveis.length)}${campo ? ` de ${fmt.int(itens.length)}` : ''} ocorrência${visiveis.length === 1 ? '' : 's'} em toda a base de ${base} (sem o filtro de período) — preencha esses campos no sistema de origem.`}
            className="jl-modal"
            onClose={onClose}
            footer={
                relatorio && itens.length > 0 && support ? (
                    <span className="muted small">{SUPPORT_READ_ONLY}</span>
                ) : relatorio && itens.length > 0 ? (
                    <>
                        {erro && (
                            <span className="small tone-text-danger jl-erro" role="alert">
                                {erro}
                            </span>
                        )}
                        <button type="button" className="btn btn-info" disabled={baixando} onClick={baixar}>
                            <Icon name="download" size={16} />
                            {baixando ? 'Gerando…' : 'Baixar relatório (XLSX)'}
                        </button>
                    </>
                ) : undefined
            }
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
