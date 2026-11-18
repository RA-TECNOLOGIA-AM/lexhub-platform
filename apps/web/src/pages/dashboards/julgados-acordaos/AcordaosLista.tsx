import { useState } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { Pill } from '../../../components/dashboard/StatCard.tsx'
import type { Tone } from '../../../components/dashboard/tone.ts'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { fmt } from '../../../lib/format.ts'
import { Paginador } from '../execucao/partes.tsx'
import { usePagina } from '../execucao/usePagina.ts'
import { dataBr, numeroCnj, ordenarLista, type OrdemLista } from './julgados.ts'
import type { LinhaAcordao } from './types.ts'

// Linhas por página: 10 recolhida; "Expandir" mostra 50 por página (as duas paginadas).
const POR_PAGINA = 10
const POR_PAGINA_EXPANDIDA = 50

// A cor do Status 2G pela categoria (a mesma dos cards: procedente verde, improcedente vermelho, extinto amarelo).
function tomStatus(status: string): Tone {
    const s = status.toLowerCase()
    if (s.includes('improced')) return 'danger'
    if (s.includes('proced')) return 'ok'
    if (s.includes('extin')) return 'warn'
    return 'neutral'
}

// Texto longo numa célula: corta com "…" e mostra o texto inteiro no cursor.
const corta = (texto: string, curta = false) =>
    texto ? (
        <span className={curta ? 'ex-corta ex-corta-curta' : 'ex-corta'} title={texto}>
            {texto}
        </span>
    ) : (
        <span className="muted">—</span>
    )

// Módulo: a lista "Acórdãos no período" (v1: JulgadosAcordaoListaTable), no layout das tabelas da Execução
// Estratégico (cartão, tabela compacta e paginador). A lista inteira vem na resposta: ordenar e paginar é aqui.
// Clicar em "Data do acórdão" troca a ordem (mais recente / mais antiga primeiro).
export function AcordaosLista({ itens }: { itens: LinhaAcordao[] }) {
    const [ordem, setOrdem] = useState<OrdemLista>('data_recente')
    const [expandida, setExpandida] = useState(false)
    const p = usePagina(ordenarLista(itens, ordem), expandida ? POR_PAGINA_EXPANDIDA : POR_PAGINA)

    const trocarOrdem = () => {
        setOrdem((o) => (o === 'data_recente' ? 'data_antiga' : 'data_recente'))
        p.setPagina(0)
    }
    const alternarExpandida = () => {
        setExpandida((e) => !e)
        p.setPagina(0)
    }

    return (
        <ChartCard
            title="Acórdãos no período"
            subtitle={`${fmt.int(itens.length)} ${itens.length === 1 ? 'acórdão' : 'acórdãos'} · clique em “Data do acórdão” para inverter a ordem`}
            action={
                itens.length > POR_PAGINA && (
                    <button type="button" className="btn btn-sm" aria-expanded={expandida} onClick={alternarExpandida}>
                        {expandida ? 'Recolher' : 'Expandir'}
                    </button>
                )
            }
        >
            <div className="ex-lista compacta">
                <DataTable
                    rows={p.itens}
                    rowKey={(r) =>
                        r.id !== null ? String(r.id) : `${r.numero_processo}-${r.data_acordao ?? ''}-${r.relator}`
                    }
                    empty="Não há acórdãos no período selecionado."
                    columns={[
                        {
                            header: 'Nº do processo',
                            render: (r) => <span className="num">{numeroCnj(r.numero_processo)}</span>,
                        },
                        { header: 'Fase', render: (r) => corta(r.fase, true) },
                        { header: 'Subfase', render: (r) => corta(r.subfase, true) },
                        {
                            header: 'Status 2G',
                            render: (r) =>
                                r.status_2g ? (
                                    <Pill tone={tomStatus(r.status_2g)}>{r.status_2g}</Pill>
                                ) : (
                                    <span className="muted">—</span>
                                ),
                        },
                        { header: 'UF', render: (r) => r.uf || '—' },
                        { header: 'Relator', render: (r) => corta(r.relator) },
                        {
                            header: (
                                <button type="button" className="linkbtn" onClick={trocarOrdem}>
                                    Data do acórdão {ordem === 'data_recente' ? '↓' : '↑'}
                                </button>
                            ),
                            render: (r) => <span className="num">{dataBr(r.data_acordao)}</span>,
                        },
                        { header: 'Embargos', render: (r) => corta(r.status_acordao_embargos, true) },
                        {
                            header: 'Data dos embargos',
                            render: (r) => <span className="num">{dataBr(r.data_acordao_embargos)}</span>,
                        },
                    ]}
                />
            </div>
            <Paginador pagina={p.pagina} total={p.total} onChange={p.setPagina} />
        </ChartCard>
    )
}
