type LoadingStateProps = {
    variant?: 'text' | 'dashboard' // 'dashboard' = esqueleto de KPIs + gráficos (como no template)
}

// Um bloco cinza animado do tamanho do conteúdo que vai chegar.
function SkeletonCard({ height }: { height: number }) {
    return (
        <div className="card card-pad">
            <div className="skel" style={{ height }} />
        </div>
    )
}

// Módulo: o "carregando" de qualquer tela. A tela só escolhe o formato.
export function LoadingState({ variant = 'text' }: LoadingStateProps) {
    if (variant === 'text') {
        return (
            <p className="muted" role="status">
                Carregando…
            </p>
        )
    }

    return (
        <div className="stack" aria-busy="true" aria-label="Carregando" style={{ gap: 20 }}>
            <div className="grid grid-kpi">
                {[1, 2, 3, 4].map((i) => (
                    <SkeletonCard key={i} height={64} />
                ))}
            </div>
            <div className="grid grid-2">
                <SkeletonCard height={220} />
                <SkeletonCard height={220} />
            </div>
        </div>
    )
}