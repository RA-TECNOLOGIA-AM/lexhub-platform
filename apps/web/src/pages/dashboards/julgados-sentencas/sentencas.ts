import { fmt } from '../../../lib/format.ts'
import type { JulgadosSentencas } from './fields.ts'
import type { LinhaSentenca } from './types.ts'

// As contas próprias da tela do Julgados Sentenças, sem React (testadas em sentencas.test.ts). O resto (categorias,
// embargos, histórico por ano, taxa e mapas) é igual ao do Julgados Acórdãos e vem de ../julgados-acordaos/julgados.ts.

// ---------- Faixa "Atenção" (dados faltando) ----------

// As mensagens da página da v1 (julgados_sentenca_NG.tsx), na mesma ordem; só as que têm processo.
export function avisosSentencas(n: JulgadosSentencas['n']): string[] {
    const q = (v: number | null) => fmt.int(v ?? 0)
    const regras: [number | null, string][] = [
        [
            n.meritoSemData,
            `Existem ${q(n.meritoSemData)} processo(s) com mérito da sentença lançado e sem a data da sentença — não entram em nenhuma contagem!`,
        ],
        [
            n.dataSemMerito,
            `Existem ${q(n.dataSemMerito)} processo(s) com data da sentença e sem o mérito lançado — entram no total sem classificação!`,
        ],
        [n.semJuiz, `Existem ${q(n.semJuiz)} processo(s) sentenciado(s) sem o nome do juiz!`],
        [n.semMateria, `Existem ${q(n.semMateria)} processo(s) sentenciado(s) sem a matéria!`],
        [n.semComarca, `Existem ${q(n.semComarca)} processo(s) sentenciado(s) sem a comarca!`],
        [n.semCompetencia, `Existem ${q(n.semCompetencia)} processo(s) sentenciado(s) sem a competência!`],
        [n.semUf, `Existem ${q(n.semUf)} processo(s) sentenciado(s) sem a UF!`],
        [
            n.semValorPe,
            `Existem ${q(n.semValorPe)} processo(s) sentenciado(s) procedente(s) com proveito econômico sem o valor da sentença!`,
        ],
    ]
    return regras.filter(([v]) => (v ?? 0) > 0).map(([, msg]) => msg)
}

// ---------- Lista "Sentenças no período" ----------

export type OrdemLista = 'data_recente' | 'data_antiga'

// Pela data da sentença (mais recente ou mais antiga primeiro); sem data vai para o fim.
export function ordenarSentencas(itens: LinhaSentenca[], ordem: OrdemLista): LinhaSentenca[] {
    const sinal = ordem === 'data_recente' ? -1 : 1
    return [...itens].sort((a, b) => {
        if (!a.data_sentenca && !b.data_sentenca) return 0
        if (!a.data_sentenca) return 1
        if (!b.data_sentenca) return -1
        return sinal * a.data_sentenca.localeCompare(b.data_sentenca)
    })
}
