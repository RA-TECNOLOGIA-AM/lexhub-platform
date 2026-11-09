import { Icon } from '../../../components/ui/Icon.tsx'
import type { TeamRule } from '../../../types/index.ts'

type TeamRulesProps = {
    rules: TeamRule[]
    onNewRule: () => void // clique em "Nova regra" (por enquanto só mostra um aviso)
}

// Módulo: "Dashboards por equipe". Um card por regra e o aviso de quem fica sem nada.
export function TeamRules({ rules, onNewRule }: TeamRulesProps) {
    return (
        <section className="card card-pad stack access-main" style={{ gap: 12 }} aria-label="Dashboards por equipe">
            <div className="row" style={{ justifyContent: 'space-between' }}>
                <h2 className="h2">Dashboards por equipe</h2>
                <button className="btn" type="button" onClick={onNewRule}>
                    <Icon name="plus" size={16} />
                    Nova regra
                </button>
            </div>
            {rules.map((r) => (
                <article key={r.team} className="rule">
                    <div className="row" style={{ justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 600 }}>Equipe {r.team}</span>
                        <span className="muted small">{r.people} pessoas</span>
                    </div>
                    <span className="muted small">Nas unidades em que a pessoa estiver, vê:</span>
                    <div className="tags">
                        {r.all ? (
                            <span className="tag">Todos os dashboards das suas unidades</span>
                        ) : (
                            r.dashboards.map((d) => (
                                <span key={d} className="tag">
                                    {d}
                                </span>
                            ))
                        )}
                    </div>
                    {r.scope && <span className="small">{r.scope}</span>}
                </article>
            ))}
            <p className="rule-warning">
                Quem não tem equipe ou unidade não vê nenhum dashboard. Na v1, essas pessoas veem tudo.
            </p>
        </section>
    )
}
