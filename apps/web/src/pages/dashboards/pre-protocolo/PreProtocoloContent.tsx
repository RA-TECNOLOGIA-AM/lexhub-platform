import { useState } from 'react'
import { ChartCard } from '../../../components/charts/ChartCard.tsx'
import { LineChart } from '../../../components/charts/LineChart.tsx'
import { DashSection } from '../../../components/dashboard/DashSection.tsx'
import { DeltaPill, FootRow, HeroStat, MiniStat, StackedRate } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { fmt } from '../../../lib/format.ts'
import type { ContentProps } from '../types.ts'
import { diaCurto, diaLongo, periodo } from '../setor/datas.ts'
import { share } from '../setor/setor.ts'
import {
    SETORES,
    funcionariosDoSetor,
    lerSetor,
    serieDiaria,
    type PreProtocoloResponse,
    type Setor,
} from './setores.ts'

const VS = ' vs mês anterior'

// Número que pode faltar na resposta ('—'), com a contagem animada quando vem.
const valor = (v: number | null, format: (n: number) => string) =>
    v === null ? '—' : <CountUp value={v} format={format} />

// O Pré-protocolo (LexPre): a página "Dashboard Geral Pré Protocolo" da v1 no layout novo, um card por setor
// (Pendência, Org. Documentos, Peticionamento e Protocolo) em cada seção e a produção diária de cada um, com
// o filtro de funcionário no próprio gráfico. Carregar, erros, cabeçalho e período ficam no DashboardView.
export function PreProtocoloContent({ data }: ContentProps<PreProtocoloResponse>) {
    const ler = (s: Setor, campo: string) => lerSetor(data, s.key, campo)
    const totalResolvidos = SETORES.reduce((sum, s) => sum + (ler(s, s.resolvidos) ?? 0), 0)
    const totalRepresados = SETORES.reduce((sum, s) => sum + (ler(s, s.represados) ?? 0), 0)

    return (
        <div className="dsecs">
            <DashSection
                index={1}
                eyebrow="Produtividade"
                title="Resolvidos por setor"
                subtitle="Volume concluído no período e comparativo com o intervalo anterior."
            >
                <div className="grid grid-stat">
                    {SETORES.map((s) => {
                        const resolvidos = ler(s, s.resolvidos)
                        return (
                            <HeroStat
                                key={s.key}
                                label={s.label}
                                icon={s.icon}
                                tone={s.tone}
                                value={valor(resolvidos, fmt.int)}
                                below={<DeltaPill value={ler(s, s.comparativoResolvidos)} suffix={VS} plain />}
                                hint={`Demandas que saíram do setor ${s.label} no período.`}
                                footer={
                                    <FootRow
                                        left="Parte do pré-protocolo"
                                        right={
                                            <span className="num">
                                                {fmt.dec1(share(resolvidos ?? 0, totalResolvidos))}%
                                            </span>
                                        }
                                    />
                                }
                            />
                        )
                    })}
                </div>
            </DashSection>

            <DashSection
                index={2}
                eyebrow="Backlog"
                title="Represados por setor"
                subtitle="Itens pendentes de resolução. Todos os cards são acumulados (sem filtro de data)."
            >
                <div className="grid grid-stat grid-mini grid-mini-stack">
                    {SETORES.map((s) => {
                        const represados = ler(s, s.represados)
                        return (
                            <MiniStat
                                key={s.key}
                                label={s.label}
                                icon="alert"
                                tone={s.tone}
                                value={valor(represados, fmt.int)}
                                below={
                                    <StackedRate
                                        text={`${fmt.dec1(share(represados ?? 0, totalRepresados))}%`}
                                        caption="dos represados"
                                        tone="neutral"
                                    />
                                }
                                hint={`Demandas no setor ${s.label} agora, ainda sem resolução. Não depende do período.`}
                            />
                        )
                    })}
                </div>
            </DashSection>

            <DashSection
                index={3}
                eyebrow="Eficiência"
                title="Tempo médio de resolução"
                subtitle="Tempo médio de processamento no período. Valores menores são melhores."
            >
                <div className="grid grid-stat grid-mini grid-mini-stack">
                    {SETORES.map((s) => (
                        <MiniStat
                            key={s.key}
                            label={s.label}
                            icon="clock"
                            tone="info"
                            value={valor(ler(s, s.tempoMedio), fmt.duracao)}
                            below={
                                <DeltaPill value={ler(s, s.comparativoTempoMedio)} betterWhenDown suffix={VS} plain />
                            }
                            hint={`Tempo médio entre a entrada no setor ${s.label} e a saída, nas demandas que saíram no período.`}
                        />
                    ))}
                </div>
            </DashSection>

            <DashSection
                index={4}
                eyebrow="Evolução diária"
                title="Produção diária por setor"
                subtitle="Filtre cada série por funcionário para comparar individualmente."
            >
                <div className="grid pre-dias">
                    {SETORES.map((s) => (
                        <ProducaoDiaria key={s.key} data={data} setor={s} />
                    ))}
                </div>
            </DashSection>
        </div>
    )
}

// O gráfico diário de um setor, com o filtro de funcionário só dele (como na v1).
function ProducaoDiaria({ data, setor }: { data: PreProtocoloResponse; setor: Setor }) {
    const [funcionario, setFuncionario] = useState('')
    const opcoes = funcionariosDoSetor(data, setor.key)
    const atual = opcoes.includes(funcionario) ? funcionario : '' // a pessoa sumiu do período: volta a "Todos"
    const dias = serieDiaria(data, setor.key, atual)
    const total = dias.reduce((sum, d) => sum + d.value, 0)
    return (
        <ChartCard
            title={setor.label}
            subtitle={`${periodo(data.meta.from, data.meta.to)} · ${fmt.int(total)} no período`}
            action={
                <label className="field-select">
                    <span className="sr-only">Funcionário</span>
                    <select value={atual} onChange={(e) => setFuncionario(e.target.value)}>
                        <option value="">Todos</option>
                        {opcoes.map((nome) => (
                            <option key={nome} value={nome}>
                                {nome}
                            </option>
                        ))}
                    </select>
                </label>
            }
        >
            <LineChart
                height={280}
                area
                labels={dias.map((d) => diaCurto(d.name))}
                tooltip={{ heading: 'Dia', title: (i) => diaLongo(dias[i]?.name) }}
                series={[{ label: atual || setor.label, color: setor.cor, values: dias.map((d) => d.value) }]}
            />
        </ChartCard>
    )
}
