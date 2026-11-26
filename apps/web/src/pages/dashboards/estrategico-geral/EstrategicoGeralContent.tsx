import { StateMessage } from '../../../components/states/StateMessage.tsx'
import { useAuth } from '../../../contexts/auth-context.ts'
import { unitLogo, unitName } from '../../../lib/units.ts'
import type { ContentProps } from '../types.ts'
import type { EstrategicoGeralResponse } from './types.ts'

// Módulo: o miolo do Estratégico Geral. Esqueleto: um bloco por unidade, na ordem da API; cada análise
// nova entra dentro do bloco da unidade (unit.data) ou numa seção que compara as unidades.
export function EstrategicoGeralContent({ data }: ContentProps<EstrategicoGeralResponse>) {
    const { me } = useAuth()
    return (
        <div className="estrategico-geral">
            <StateMessage icon="inbox" title="Em construção">
                As análises do Estratégico Geral entram aqui, com as unidades lado a lado.
            </StateMessage>
            <div className="estrategico-geral-units">
                {data.units.map((unit) => {
                    const logo = unitLogo(unit.code)
                    return (
                        <section key={unit.code} className="card estrategico-geral-unit" aria-label={unit.code}>
                            <header className="estrategico-geral-unit-head">
                                {logo && <img src={logo} alt="" aria-hidden="true" width={28} height={28} />}
                                <span className="title">{unitName(unit.code, me?.units ?? [])}</span>
                            </header>
                            <p className="desc">Sem análises ainda.</p>
                        </section>
                    )
                })}
            </div>
        </div>
    )
}
