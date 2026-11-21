import { minutesSince, timeAgo } from '../../lib/format.ts'

type FreshnessProps = {
    syncedAt: string | null
    source: string
    maxDelayMin?: number
}

// Verde: "Atualizado há 4 min · LexPre".
// Amarelo (passou do limite): "Fonte atrasada · há 3 h · LexPre".
// Neutro (syncedAt null): "Atualiza ao abrir · LexPre". A API só busca a fonte quando alguém abre o dashboard
// (sem aquecedor no LexFlow e no LexPre, por causa do egress do Supabase): não ter hora no hub não é atraso.
export function Freshness({ syncedAt, source, maxDelayMin = 60 }: FreshnessProps) {
    if (syncedAt === null) {
        return <span className="fresh">Atualiza ao abrir · {source}</span>
    }
    const late = minutesSince(syncedAt) > maxDelayMin
    return (
        <span className={late ? 'fresh late' : 'fresh'}>
            {late ? 'Fonte atrasada · ' : 'Atualizado '}
            {timeAgo(syncedAt)} · {source}
        </span>
    )
}
