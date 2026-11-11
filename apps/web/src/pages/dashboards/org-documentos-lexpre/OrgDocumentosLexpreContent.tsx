import { Delta } from '../../../components/dashboard/Delta.tsx'
import { Kpi } from '../../../components/dashboard/Kpi.tsx'
import { KpiSection } from '../../../components/dashboard/KpiSection.tsx'
import { fmt, show } from '../../../lib/format.ts'
import type { OrgDocumentosLexpreResponse } from './types.ts'

// Só o que é da Organização de documentos: os KPIs. Carregar, erros e cabeçalho ficam no DashboardView.
// Qualquer campo pode faltar (ex.: mock): show() mostra '—' e o Delta some.
export function OrgDocumentosLexpreContent({ data }: { data: OrgDocumentosLexpreResponse }) {
    const s = data.stats ?? {}

    return (
        <>
            <KpiSection
                id="periodo"
                title="No período"
                subtitle="Saídas do setor no período, com comparativo ao mês anterior."
            >
                <Kpi
                    label="Total resolvidos"
                    value={show(s.resolvidos_total?.total, fmt.int)}
                    note={<Delta value={s.resolvidos_total?.comparativo ?? null} />}
                />
                <Kpi
                    label="Resolvido manualmente"
                    value={show(s.organizados_manualmente?.total, fmt.int)}
                    note={<Delta value={s.organizados_manualmente?.comparativo ?? null} />}
                />
                <Kpi
                    label="Resolvido automaticamente"
                    value={show(s.organizados_e_peticionados_automaticamente?.total, fmt.int)}
                    note={<Delta value={s.organizados_e_peticionados_automaticamente?.comparativo ?? null} />}
                />
                <Kpi
                    label="Cancelados"
                    value={show(s.cancelados?.total, fmt.int)}
                    note={<Delta value={s.cancelados?.comparativo ?? null} />}
                />
                <Kpi
                    label="Protocolados"
                    value={show(s.protocolados_total?.total, fmt.int)}
                    note={<Delta value={s.protocolados_total?.comparativo ?? null} />}
                />
                <Kpi
                    label="Tempo médio resolvidos"
                    value={show(s.media_tempo_resolvidos, fmt.dias)}
                    note={<Delta value={s.comparativo_tempo_medio_resolvidos ?? null} betterWhenDown />}
                />
                <Kpi
                    label="Mediana de tempo resolvidos"
                    value={show(s.mediana_tempo_resolvidos, fmt.dias)}
                    note={<Delta value={s.comparativo_mediana_tempo_resolvidos ?? null} betterWhenDown />}
                />
            </KpiSection>

            <KpiSection id="agora" title="Situação atual do setor" subtitle="Não dependem do período selecionado.">
                <Kpi label="Represados" value={show(s.represados, fmt.int)} note="Ainda no setor" />
                <Kpi
                    label="Devolvido p/ Pendência"
                    value={show(s.devolvido_pendencia, fmt.int)}
                    note={<Delta value={s.comparativo_devolvido_pendencia ?? null} betterWhenDown />}
                />
                <Kpi
                    label="Retornos de Pendências"
                    value={show(s.retorno_pendencia, fmt.int)}
                    note="Entradas vindas de Pendências"
                />
                <Kpi
                    label="Retornos do Peticionamento"
                    value={show(s.retorno_pet, fmt.int)}
                    note="Entradas vindas do Peticionamento"
                />
            </KpiSection>
        </>
    )
}
