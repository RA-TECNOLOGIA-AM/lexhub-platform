import type { DataSource, SourceFreshness, SourcesFreshness, SourceStatus, UnitSources } from '../../../types/index.ts'

// Módulo: a hora e o status de cada fonte a partir do registro de leituras da API (memória + Redis,
// o mesmo que dá a hora ao card do hub). Sem React; testado em sourceFreshness.test.ts.
// O resto da fonte (nome, dono, configuração) continua vindo de api.list_sources.
//
// O status diz se a fonte RESPONDE, não se alguém a usou há pouco: a API só lê a fonte quando alguém
// abre um dashboard, então "faz tempo que ninguém abriu" não é problema da fonte. A hora fica como
// informação ("há 3 h · cache de 15 min").

// Esses status são configuração, não leitura: o servidor decide e o registro não muda.
const KEEP: ReadonlySet<SourceStatus> = new Set(['disabled', 'pending', 'no_dashboards'])

function statusFrom(f: SourceFreshness): SourceStatus {
    if (f.error) return 'failing' // a tentativa mais recente falhou
    if (f.fetchedAt === null) return 'on_open' // ainda não foi lida
    return 'healthy' // a última tentativa deu certo, seja quando for
}

// Uma fonte com a hora do registro (a linha da lista e o topo do modal usam a mesma regra).
// Sem registro para ela (undefined) = fica como veio do Supabase.
export function sourceWithFreshness(source: DataSource, f: SourceFreshness | undefined): DataSource {
    if (!f || source.status === 'disabled') return source
    return {
        ...source,
        syncedAt: f.fetchedAt,
        rows: null, // o registro não guarda a contagem da fonte inteira
        failures: f.error ? 1 : 0,
        cacheMin: f.cacheMin,
        status: KEEP.has(source.status) ? source.status : statusFrom(f),
    }
}

// A falha mais recente entre a do Supabase e as do registro.
function lastFailure(unit: UnitSources, fresh: SourcesFreshness): UnitSources['lastFailure'] {
    let last = unit.lastFailure
    for (const s of unit.sources) {
        const f = fresh[s.id]
        if (!f?.error || !f.errorAt || s.status === 'disabled') continue
        if (!last || Date.parse(f.errorAt) > Date.parse(last.at)) {
            last = { at: f.errorAt, source: s.name, message: `falha ao ler (${f.error})` }
        }
    }
    return last
}

// A unidade com a hora do registro em cada fonte. fresh null (a API não respondeu) = fica como veio.
export function withFreshness(unit: UnitSources, fresh: SourcesFreshness | null): UnitSources {
    if (!fresh) return unit
    return {
        ...unit,
        sources: unit.sources.map((s) => sourceWithFreshness(s, fresh[s.id])),
        lastFailure: lastFailure(unit, fresh),
    }
}
