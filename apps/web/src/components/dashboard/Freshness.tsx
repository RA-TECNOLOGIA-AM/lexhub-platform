import { minutesSince, timeAgo } from '../../lib/format.ts'

type FreshnessProps = {
    syncedAt: string
    source: string
    maxDelayMin?: number
}

// Verde: "Atualizado há 4 min · LexPre".
// Amarelo (passou do limite): "Fonte atrasada · há 3 h · LexPre".
export function Freshness({ syncedAt, source, maxDelayMin = 60 }: FreshnessProps) {
    const late = minutesSince(syncedAt) > maxDelayMin
    return (
        <span className={late ? 'fresh late' : 'fresh'}>
            {late ? 'Fonte atrasada · ' : 'Atualizado '}
            {timeAgo(syncedAt)} · {source}
        </span>
    )
}
