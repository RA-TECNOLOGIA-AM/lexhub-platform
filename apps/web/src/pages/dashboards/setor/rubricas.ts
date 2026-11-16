// As abas do modal "Rubricas dentro de <pacote>" (sem React; testado em rubricas.test.ts).

export type Aba = 'todos' | 'resolvidos' | 'represados' | 'protocolados'

type Demanda = { situacao: 'resolvido' | 'represado'; protocolado: boolean }

const NA_ABA: Record<Aba, (d: Demanda) => boolean> = {
    todos: () => true,
    resolvidos: (d) => d.situacao === 'resolvido',
    represados: (d) => d.situacao === 'represado',
    protocolados: (d) => d.protocolado,
}

// As demandas de uma aba.
export const daAba = <T extends Demanda>(demandas: T[], aba: Aba): T[] => demandas.filter(NA_ABA[aba])

// Quantas demandas cada aba tem (o número entre parênteses).
export function contagemAbas(demandas: Demanda[]): Record<Aba, number> {
    return {
        todos: demandas.length,
        resolvidos: daAba(demandas, 'resolvidos').length,
        represados: daAba(demandas, 'represados').length,
        protocolados: daAba(demandas, 'protocolados').length,
    }
}

// O que a API manda em `rubricas_reunidas` (Peticionamento e Org. Documentos): por matéria reunida (pacote),
// as demandas resolvidas no período ou represadas agora, com o cliente e as rubricas de cada uma.
export type DemandaReunida = {
    id_demanda: number | string
    cliente: string | null
    situacao: 'resolvido' | 'represado'
    protocolado: boolean
    rubricas: string[]
}

export type RubricaReunida = { materia: string; demandas: DemandaReunida[] }
