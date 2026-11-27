import { InfoTip } from '../../../components/dashboard/StatCard.tsx'
import { CountUp } from '../../../components/ui/CountUp.tsx'
import { fmt } from '../../../lib/format.ts'

// Reajuizamentos do LexPre (demandas.reajuizamento): ficam fora de todo total e da comissão do setor e aparecem
// só neste card. A API calcula com a mesma regra do setor, só nas demandas de reajuizamento
// (app/dashboards/reajuizamento_lexpre.py).
export const HINT_FORA_DA_COMISSAO = 'Não entra nos totais nem na comissão do setor.'

type Props = {
    // `periodo`: número do período (ex.: "Peticionados"); `fila`: o de agora (ex.: "Não peticionados").
    // `quando`: o que vai entre parênteses no rótulo (padrão: "período" e "agora").
    periodo: { label: string; value: number | undefined; hint: string; quando?: string }
    fila: { label: string; value: number | undefined; hint: string; quando?: string }
}

// Um card só, compacto: "Reajuizamento (separado do total)" com o número do período e o da fila lado a lado.
// Fica na fileira de baixo da seção 01 dos setores LexPre (Org. Documentos, Peticionamento, Pendências).
export function ReajuizamentoResumo({ setor, periodo, fila }: Props & { setor: string }) {
    return (
        <div className="card mini reaj-resumo">
            <div className="reaj-top">
                <span className="hero-l">
                    Reajuizamento (separado do total)
                    <span className="mini-l-tip">
                        <InfoTip text={`${periodo.hint} ${fila.hint} ${HINT_FORA_DA_COMISSAO}`} />
                    </span>
                </span>
                <span className="muted reaj-setor">{setor}</span>
            </div>
            <div className="reaj-cols">
                <div className="fstack">
                    <span className="reaj-l">
                        {periodo.label} ({periodo.quando ?? 'período'})
                    </span>
                    <span className="mini-v num">
                        <CountUp value={periodo.value ?? 0} format={fmt.int} />
                    </span>
                </div>
                <div className="fstack">
                    <span className="reaj-l">
                        {fila.label} ({fila.quando ?? 'agora'})
                    </span>
                    <span className="mini-v num">
                        <CountUp value={fila.value ?? 0} format={fmt.int} />
                    </span>
                </div>
            </div>
        </div>
    )
}
