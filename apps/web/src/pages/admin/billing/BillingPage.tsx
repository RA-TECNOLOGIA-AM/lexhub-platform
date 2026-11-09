import { useState } from 'react'
import { useParams } from 'react-router'
import { DataTable } from '../../../components/ui/DataTable.tsx'
import { Notice } from '../../../components/ui/Notice.tsx'
import { PageHeader } from '../../../components/layout/PageHeader.tsx'
import { ErrorState } from '../../../components/states/ErrorState.tsx'
import { LoadingState } from '../../../components/states/LoadingState.tsx'
import { dataClient } from '../../../services/client.ts'
import { useAsync } from '../../../hooks/useAsync.ts'
import { CurrentPlanCard } from './CurrentPlanCard.tsx'
import { invoiceColumns } from './invoiceColumns.tsx'
import { PlanCard } from './PlanCard.tsx'

// Mudar de plano e baixar nota ainda não existem: os botões aparecem e explicam isso.
const SOON = 'ainda não está disponível. Fale com a equipe RA.'

// A página só junta as peças: busca a cobrança e mostra plano atual, planos e faturas.
export function BillingPage() {
    const { org = '' } = useParams()
    const { data, error } = useAsync(() => dataClient.getBilling(org), [org])
    const [notice, setNotice] = useState<string | null>(null)

    if (error) return <ErrorState error={error} />
    if (!data) return <LoadingState />

    const currentPlan = data.plans.find((p) => p.key === data.current.plan)
    return (
        <>
            <PageHeader
                title="Plano e cobrança"
                description="Os preços ainda serão definidos na fase de descoberta com escritórios. Por isso aparecem como campos em aberto."
            />
            <div className="stack">
                {notice && <Notice message={notice} onClose={() => setNotice(null)} />}
                <CurrentPlanCard
                    current={data.current}
                    planName={currentPlan?.name ?? data.current.plan}
                    usage={data.usage}
                />
                <div className="plan-grid">
                    {data.plans.map((p) => (
                        <PlanCard
                            key={p.key}
                            plan={p}
                            current={data.current.plan}
                            onAction={(label) => setNotice(`${label}: ${SOON}`)}
                        />
                    ))}
                </div>
                <section className="stack" style={{ gap: 10 }} aria-label="Faturas">
                    <h2 className="h2">Faturas</h2>
                    <DataTable
                        columns={invoiceColumns(() => setNotice(`Baixar a NFS-e ${SOON}`))}
                        rows={data.invoices}
                        rowKey={(i) => i.id}
                        empty="Nenhuma fatura ainda."
                    />
                </section>
            </div>
        </>
    )
}
