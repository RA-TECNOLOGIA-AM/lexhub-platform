import { Icon } from '../../../components/ui/Icon.tsx'
import type { ContentProps } from '../types.ts'
import { Aquisicao } from './Aquisicao.tsx'
import { FacebookAds } from './FacebookAds.tsx'
import { Fechamento } from './Fechamento.tsx'
import { Organico } from './Organico.tsx'
import { Performance } from './Performance.tsx'
import { PerfilTriados } from './PerfilTriados.tsx'
import { lerMarketingNg, type MarketingNgResponse } from './marketingNg.ts'

// O Marketing (banco NG): as 7 seções da página da v1 (MarketingNG.tsx) no layout novo. Carregar, erros, cabeçalho,
// período e as etiquetas de filtro ficam no DashboardView; clicar numa barra/fatia liga o filtro daquela dimensão
// (como o drill-down da v1: vários valores na mesma dimensão = OU, dimensões diferentes = E).
export function MarketingNgContent({ data, filters = {}, onToggleFilter }: ContentProps<MarketingNgResponse>) {
    const ler = lerMarketingNg(data)
    const filtro = { filters, onToggleFilter }
    return (
        <div className="dsecs">
            {data.lexpre &&
                (data.lexpre.somado ? (
                    <p className="mkt-fonte" role="note">
                        <Icon name="db" size={15} />
                        <span>
                            Números somados: <strong>banco NG</strong> (atendimentos até out/2026) +{' '}
                            <strong>LexPre</strong> (escritório NG, onde o comercial é registrado desde set/2026). Funil
                            de pipeline e dispositivo: só o banco NG.
                        </span>
                    </p>
                ) : (
                    <p className="mkt-fonte aviso" role="note">
                        <Icon name="alert" size={15} />
                        <span>Só o banco NG (atendimentos até out/2026): {data.lexpre.motivo ?? 'sem o LexPre.'}</span>
                    </p>
                ))}
            <PerfilTriados ler={ler} {...filtro} dispositivo />
            <FacebookAds ler={ler} index={3} />
            <Fechamento ler={ler} index={4} raNg {...filtro} />
            <Aquisicao ler={ler} index={5} {...filtro} />
            <Performance
                ler={ler}
                index={6}
                campos={{
                    sufixo: ' NG',
                    codigo: 'ANUNCIO_NG',
                    leads: 'leads_ng',
                    clientes: 'campanha_ng',
                    acoes: 'acoes_ng',
                    conversao: 'conversao_ng',
                    cpl: 'cpl_ng',
                    valorCausa: 'valor_causa_ng',
                    ticket: 'ticket_medio_ng',
                    rubricas: 'ind_rubricas',
                }}
                {...filtro}
            />
            <Organico ler={ler} index={7} sufixo=" NG" {...filtro} />
        </div>
    )
}
