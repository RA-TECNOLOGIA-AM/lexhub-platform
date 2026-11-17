import { useState } from 'react'
import { BarList } from '../../../components/charts/BarList.tsx'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { MiniStat, Pill } from '../../../components/dashboard/StatCard.tsx'
import { Modal } from '../../../components/ui/Modal.tsx'
import { pickSingle } from '../../../lib/filters.ts'
import { fmt } from '../../../lib/format.ts'
import type { DashboardFilters } from '../../../types/index.ts'
import { CardFiltro, ProcessosTabela } from './partes.tsx'
import { CHAVES, numeroCnj, type Setor, type SetorExecucao } from './setorExecucao.ts'

type Props = {
    index: number
    setor: Setor
    dados: SetorExecucao
    filters: DashboardFilters
    setFilters?: (f: DashboardFilters) => void
}

// Seção "Diligências" das páginas da v1 de Execução: quantas vezes a diligência foi feita em cada processo, o
// ranking por colaborador e os alvarás. Clicar num colaborador mostra só os números dele; os cards de alvará
// filtram os gráficos por tipo; "Valor Realizado" abre os processos que somam o valor. Nos Acordos, clicar num
// processo filtra a página por ele, como na v1.
export function DiligenciasSection({ index, setor, dados, filters, setFilters }: Props) {
    const [valorAberto, setValorAberto] = useState(false)
    const k = CHAVES[setor]
    const d = dados.diligencias
    const acordos = setor === 'acordos'
    const rotuloValor = acordos ? 'Valor de alçada final' : 'Valor da execução'
    const colaborador = filters[k.colaborador]?.[0] ?? null
    const tipo = filters[k.tipoDiligencia]?.[0] ?? null
    const processo = filters.numero_processo_execucao_acordos?.[0] ?? null
    const escolher = setFilters && ((key: keyof DashboardFilters, v: string) => setFilters(pickSingle(filters, key, v)))

    // "0001234-56.2024.8.04.0001 · R$ 12.345,67": o nº e o valor, como a v1; o nº cru fica para o filtro.
    const itensProcesso = d.porProcesso.map((p) => ({
        name: `${numeroCnj(p.processo)}${p.valor !== null ? ` · ${fmt.brl(p.valor)}` : ''}`,
        value: p.quantidade,
        cru: p.processo,
    }))
    const rotuloProcesso = new Map(itensProcesso.map((p) => [p.name, p.cru]))
    const processoSelecionado = processo ? itensProcesso.filter((p) => p.cru === processo).map((p) => p.name) : []

    return (
        <DashSection
            index={index}
            eyebrow={acordos ? 'Setor Execução de Acordos' : 'Setor Execução'}
            title="Diligências"
            subtitle={`${d.total === null ? '—' : fmt.int(d.total)} diligência(s) no período · quantas vezes a diligência foi feita em cada processo (pode se repetir) e o ranking por colaborador.`}
        >
            <div className="grid dist-grid">
                <ChartCard
                    className="ex-rolagem"
                    title="Processos com mais diligências"
                    subtitle="Agendamentos de diligência por processo, criados no período"
                    action={acordos && escolher && <Pill tone="accent">Clique para filtrar</Pill>}
                >
                    <BarList
                        items={itensProcesso}
                        wrapNames
                        selected={processoSelecionado}
                        onSelect={
                            acordos && escolher
                                ? (rotulo) => {
                                      const cru = rotuloProcesso.get(rotulo)
                                      if (cru) escolher('numero_processo_execucao_acordos', cru)
                                  }
                                : undefined
                        }
                        selectLabel="Filtrar pelo processo"
                    />
                </ChartCard>
                <ChartCard
                    className="ex-rolagem"
                    title="Ranking de diligências por colaborador"
                    subtitle={
                        tipo
                            ? `Só ${tipo === 'expedicao_alvara' ? 'expedições de alvará' : 'alvarás cumpridos'}`
                            : 'Todas as diligências do período'
                    }
                    action={escolher && <Pill tone="accent">Clique para ver os números</Pill>}
                >
                    <BarList
                        items={d.porColaborador}
                        ranked
                        selected={colaborador ? [colaborador] : []}
                        onSelect={escolher && ((v) => escolher(k.colaborador, v))}
                        selectLabel="Ver os números de"
                    />
                </ChartCard>
            </div>

            <div className="grid grid-stat-3 ex-mt">
                <CardFiltro
                    ativo={tipo === 'expedicao_alvara'}
                    onClick={() => escolher?.(k.tipoDiligencia, 'expedicao_alvara')}
                    rotuloAcao="Filtrar os gráficos pelas diligências de expedição de alvará"
                >
                    <MiniStat
                        label={
                            colaborador ? `Alvarás de expedição · ${colaborador}` : 'Diligências de expedição de alvará'
                        }
                        icon="receipt"
                        tone="accent"
                        value={d.alvaras === null ? '—' : fmt.int(d.alvaras)}
                        below={
                            <span className="muted small">
                                {colaborador ? `encerradas por ${colaborador} no período` : 'criadas no período'}
                            </span>
                        }
                    />
                </CardFiltro>
                <CardFiltro
                    ativo={tipo === 'expedicao_alvara_cumprida'}
                    onClick={() => escolher?.(k.tipoDiligencia, 'expedicao_alvara_cumprida')}
                    rotuloAcao="Filtrar os gráficos pelos alvarás cumpridos"
                >
                    <MiniStat
                        label={colaborador ? `Alvarás cumpridos · ${colaborador}` : 'Expedições de alvará cumpridas'}
                        icon="check-circle"
                        tone="ok"
                        value={d.alvarasCumpridos === null ? '—' : fmt.int(d.alvarasCumpridos)}
                        below={<span className="muted small">encerradas como cumpridas no período</span>}
                    />
                </CardFiltro>
                <CardFiltro onClick={() => setValorAberto(true)} rotuloAcao="Ver os processos do valor realizado">
                    <MiniStat
                        label={colaborador ? `Valor realizado · ${colaborador}` : 'Valor realizado (alvará)'}
                        icon="dollar"
                        tone="ok"
                        value={d.valorRealizado === null ? '—' : fmt.brl(d.valorRealizado)}
                        below={
                            <span className="muted small">
                                {fmt.int(d.processosAlvara.length)} processo(s) · ver lista
                            </span>
                        }
                    />
                </CardFiltro>
            </div>

            {valorAberto && (
                <Modal
                    title={colaborador ? `Valor realizado · ${colaborador}` : 'Valor realizado (alvará)'}
                    subtitle={`${fmt.int(d.processosAlvara.length)} processo(s) com expedição de alvará cumprida no período · ${d.valorRealizado === null ? '—' : fmt.brl(d.valorRealizado)}`}
                    description={`Soma o ${rotuloValor.toLowerCase()} dos processos com pelo menos uma diligência de expedição de alvará cumprida no período, sem repetir o processo.`}
                    className="ex-modal"
                    onClose={() => setValorAberto(false)}
                >
                    <ProcessosTabela processos={d.processosAlvara} rotuloValor={rotuloValor} />
                </Modal>
            )}
        </DashSection>
    )
}
