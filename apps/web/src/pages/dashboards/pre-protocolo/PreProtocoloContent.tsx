import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import { lerSetor, SETORES, type PreProtocoloResponse } from './setores.ts'

// Só o que é do Pré-protocolo (LexPre): os KPIs da página "Dashboard Geral Pré Protocolo (LexPre)" da v1
// (Produtividade, Backlog e Eficiência), um cartão por setor. Carregar, erros e cabeçalho ficam no DashboardView.
export function PreProtocoloContent({ data }: { data: PreProtocoloResponse }) {
    return (
        <>
            <KpiSection id="resolvidos" title="Resolvidos por setor" subtitle="Saídas de cada setor no período.">
                {SETORES.map((s) => (
                    <Kpi
                        key={s.key}
                        label={s.label}
                        value={show(lerSetor(data, s.key, s.resolvidos), fmt.int)}
                        note={<Delta value={lerSetor(data, s.key, s.comparativoResolvidos)} />}
                    />
                ))}
            </KpiSection>

            <KpiSection id="represados" title="Represados por setor" subtitle="Não dependem do período selecionado.">
                {SETORES.map((s) => (
                    <Kpi key={s.key} label={s.label} value={show(lerSetor(data, s.key, s.represados), fmt.int)} />
                ))}
            </KpiSection>

            <KpiSection id="tempo" title="Tempo médio de resolução" subtitle="Dias no setor até a saída, no período.">
                {SETORES.map((s) => (
                    <Kpi
                        key={s.key}
                        label={s.label}
                        value={show(lerSetor(data, s.key, s.tempoMedio), fmt.dias)}
                        note={<Delta value={lerSetor(data, s.key, s.comparativoTempoMedio)} betterWhenDown />}
                    />
                ))}
            </KpiSection>
        </>
    )
}
