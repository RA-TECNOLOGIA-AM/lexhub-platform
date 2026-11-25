import type { ContentProps } from '../types.ts'
import { Aquisicao } from '../marketing/Aquisicao.tsx'
import { FacebookAds } from '../marketing/FacebookAds.tsx'
import { Fechamento } from '../marketing/Fechamento.tsx'
import { Organico } from '../marketing/Organico.tsx'
import { Performance } from '../marketing/Performance.tsx'
import { PerfilTriados } from '../marketing/PerfilTriados.tsx'
import { lerMarketing, type MarketingLexpreResponse } from './marketingLexpre.ts'

// O Marketing (LexPre): as 7 seções da página da v1, com os mesmos blocos do Marketing (banco NG). Aqui há uma
// campanha só (anúncio) e não há dispositivo nem funil de pipeline. Carregar, erros, cabeçalho, período e as
// etiquetas de filtro ficam no DashboardView; clicar numa barra/fatia liga o filtro daquela dimensão.
export function MarketingLexpreContent({ data, filters = {}, onToggleFilter }: ContentProps<MarketingLexpreResponse>) {
    const ler = lerMarketing(data)
    const filtro = { filters, onToggleFilter }
    return (
        <div className="dsecs">
            <PerfilTriados ler={ler} {...filtro} />
            <FacebookAds ler={ler} index={3} />
            <Fechamento ler={ler} index={4} raNg={false} {...filtro} />
            <Aquisicao ler={ler} index={5} {...filtro} />
            <Performance
                ler={ler}
                index={6}
                campos={{
                    sufixo: '',
                    leads: 'leads_campanha',
                    clientes: 'campanha',
                    acoes: 'acoes_campanha',
                    conversao: 'conversao_campanha',
                    cpl: 'cpl_campanha',
                    valorCausa: 'valor_causa_campanha',
                    ticket: 'ticket_medio_campanha',
                    rubricas: 'rubrica_campanha',
                }}
                {...filtro}
            />
            <Organico ler={ler} index={7} sufixo="" {...filtro} />
        </div>
    )
}
