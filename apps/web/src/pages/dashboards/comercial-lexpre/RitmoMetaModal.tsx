import type { CSSProperties } from 'react'
import { Modal } from '../../../components/ui/Modal.tsx'
import { fmt } from '../../../lib/format.ts'
import type { RitmoMeta } from './comercial.ts'

const inteiro = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })
const milhoes = (v: number) =>
    `R$ ${new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v / 1e6)} mi`
const pct2 = (v: number) => `${fmt.dec2(v)}%`
const dataBr = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}`
// '0,98 ponto percentual' / '2,50 pontos percentuais'
const pontos = (v: number) => `${fmt.dec2(Math.abs(v))} ${Math.abs(v) >= 2 ? 'pontos percentuais' : 'ponto percentual'}`
const metaPorExtenso = (meta: number) =>
    meta >= 1e6 ? `R$ ${new Intl.NumberFormat('pt-BR').format(meta / 1e6)} milhões` : inteiro.format(meta)

// A frase final: atrasado, no ritmo ou adiantado, e quanto a média diária precisa mudar para fechar o ano.
function conclusao(r: RitmoMeta, meta: number): string {
    const alvo = `alcançar os ${metaPorExtenso(meta)} até 31/12`
    if (r.faltam === 0) return `a meta do ano já foi atingida (${pct2(r.pctRealizado)}).`
    if (r.novaMedia === null || r.variacao === null) return `o ano terminou com ${pct2(r.pctRealizado)} da meta.`
    const quanto = `${fmt.dec1(Math.abs(r.variacao) * 100)}%`
    if (r.diferenca < 0) {
        const intensidade = Math.abs(r.pontos) < 2 ? 'ligeiramente atrasado' : 'atrasado'
        return `o time está ${intensidade} em relação ao ritmo linear da meta anual. Para recuperar o atraso e ${alvo}, precisará produzir aproximadamente ${quanto} acima da média diária planejada.`
    }
    return `o time está adiantado em relação ao ritmo linear da meta anual. Mantendo ${quanto} abaixo da média diária planejada já é possível ${alvo}.`
}

// Módulo: o modal "Ritmo da meta" do card Meta <ano> do Comercial: a meta distribuída linearmente pelos dias do ano
// (a regra do dashboard Meta anual), o esperado até hoje contra o realizado e o ritmo diário para fechar o ano.
export function RitmoMetaModal({ r, meta, onClose }: { r: RitmoMeta; meta: number; onClose: () => void }) {
    const atrasado = r.diferenca < 0
    const largura = (v: number) => ({ '--w': `${Math.min(100, Math.max(0, v))}%` }) as CSSProperties
    return (
        <Modal title={`Ritmo da meta ${r.ano}`} className="ritmo-modal" onClose={onClose}>
            <div className="ritmo">
                <p>
                    Considerando a meta de <strong>{metaPorExtenso(meta)} em valor de causas ajuizadas</strong>,
                    distribuída linearmente pelos {r.diasNoAno} dias de {r.ano}, com prazo final em 31/12/{r.ano}:
                </p>

                <div className="ritmo-esperado">
                    <span className="muted small">Meta esperada até hoje — {dataBr(r.hoje)}</span>
                    <strong className="num">{inteiro.format(r.esperado)}</strong>
                    <span className="ritmo-chip ok num">{pct2(r.pctEsperado)} da meta anual</span>
                </div>

                <h3 className="ritmo-titulo">Comparativo com o realizado</h3>
                <div className="ritmo-cards">
                    <div className="ritmo-card">
                        <span className="muted small">Realizado</span>
                        <strong className="num">{milhoes(r.realizado)}</strong>
                        <span className="muted small num">{pct2(r.pctRealizado)} da meta</span>
                    </div>
                    <div className={`ritmo-card ${atrasado ? 'deficit' : 'superavit'}`}>
                        <span className="muted small">{atrasado ? 'Déficit atual' : 'Adiantamento atual'}</span>
                        <strong className="num">{milhoes(Math.abs(r.diferenca))}</strong>
                        <span className="muted small num">{pontos(r.pontos)}</span>
                    </div>
                </div>
                <div className="ritmo-barras">
                    <div className="ritmo-barra-linha">
                        <span>Esperado</span>
                        <span className="num">{pct2(r.pctEsperado)}</span>
                    </div>
                    <span className="ritmo-barra esperado" style={largura(r.pctEsperado)} aria-hidden="true" />
                    <div className="ritmo-barra-linha">
                        <span>Realizado</span>
                        <span className="num">{pct2(r.pctRealizado)}</span>
                    </div>
                    <span className="ritmo-barra realizado" style={largura(r.pctRealizado)} aria-hidden="true" />
                </div>

                <h3 className="ritmo-titulo">Ritmo necessário para concluir a meta</h3>
                <table className="tbl ritmo-tbl">
                    <thead>
                        <tr>
                            <th scope="col">Indicador</th>
                            <th scope="col" className="num">
                                Valor
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Dias decorridos (incluindo hoje)</td>
                            <td className="num">{r.decorridos}</td>
                        </tr>
                        <tr>
                            <td>Dias restantes após hoje</td>
                            <td className="num">{r.restantes}</td>
                        </tr>
                        <tr>
                            <td>Média diária planejada</td>
                            <td className="num">{inteiro.format(r.mediaPlanejada)}</td>
                        </tr>
                        <tr>
                            <td>Valor restante para atingir a meta</td>
                            <td className="num">{inteiro.format(r.faltam)}</td>
                        </tr>
                        <tr className="ritmo-destaque">
                            <td>Nova média diária necessária</td>
                            <td className="num">{r.novaMedia === null ? '—' : inteiro.format(r.novaMedia)}</td>
                        </tr>
                    </tbody>
                </table>

                <p>
                    <strong>Conclusão:</strong> {conclusao(r, meta)}
                </p>
            </div>
        </Modal>
    )
}
