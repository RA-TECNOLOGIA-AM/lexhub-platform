import { useState } from 'react'
import type { AdsCapabilityStatus, AdsTokenAccount, AdsTokenInfo } from '../../../types/index.ts'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { accountBlock, dateLabel, money, toggle } from './facebookAds.ts'

const CAPABILITY: Record<AdsCapabilityStatus, { icon: IconName; badge: string; label: string }> = {
    used: { icon: 'check', badge: 'ok', label: 'O LexHub usa' },
    available: { icon: 'info', badge: 'info', label: 'Disponível' },
    warn: { icon: 'alert', badge: 'warn', label: 'Atenção' },
    missing: { icon: 'minus', badge: 'neutral', label: 'Não permitido' },
}

// Módulo: o que o token do Facebook Ads permite: quem é, tipo e validade (quando a API sabe), as permissões
// concedidas e o que dá para fazer com elas (o que o LexHub coleta e o que ainda não).
export function AdsTokenView({ info }: { info: AdsTokenInfo }) {
    const validity =
        info.neverExpires === null
            ? null
            : info.neverExpires
              ? 'Não expira'
              : `Expira em ${dateLabel(info.expiresAt?.slice(0, 10))}`
    return (
        <section className="ads-token" aria-label="O que o token permite">
            <dl className="source-facts">
                <dt>Token de</dt>
                <dd>{info.user?.name ?? 'Usuário sem nome'}</dd>
                <dt>Tipo</dt>
                <dd>
                    {info.tokenType ?? (
                        <span className="muted">
                            A API não sabe (falta FACEBOOK_APP_ID). Token pessoal expira e para de funcionar se a pessoa
                            sair do negócio: prefira um de usuário do sistema.
                        </span>
                    )}
                </dd>
                {validity && (
                    <>
                        <dt>Validade</dt>
                        <dd>{validity}</dd>
                    </>
                )}
                {info.app && (
                    <>
                        <dt>App</dt>
                        <dd>{info.app}</dd>
                    </>
                )}
                <dt>Permissões</dt>
                <dd className="ads-perms">
                    {info.permissions.length === 0
                        ? 'Nenhuma'
                        : info.permissions.map((p) => (
                              <span
                                  key={p.name}
                                  className={`badge ${p.granted ? 'ok' : 'neutral'}`}
                                  title={`${p.name}${p.granted ? '' : ' (recusada ou expirada)'}`}
                              >
                                  {p.label}
                              </span>
                          ))}
                </dd>
            </dl>
            <ul className="ads-caps" aria-label="O que dá para fazer com o token">
                {info.capabilities.map((c) => {
                    const look = CAPABILITY[c.status]
                    return (
                        <li key={c.key} className={`ads-cap is-${c.status}`}>
                            <Icon name={look.icon} size={16} />
                            <span className="ads-check-text">
                                <span>
                                    {c.label} <span className={`badge ${look.badge}`}>{look.label}</span>
                                </span>
                                <span className="muted small">{c.detail}</span>
                            </span>
                        </li>
                    )
                })}
            </ul>
        </section>
    )
}

type AdsAccountPickerProps = {
    accounts: AdsTokenAccount[]
    chosen: string[]
    onChange: (ids: string[]) => void
    disabled?: boolean
}

// Acima disso a lista de contas ganha a busca.
const SEARCH_FROM = 8

// Módulo: as contas de anúncios do token, pelo nome, para marcar uma ou várias (cada uma vira uma fonte).
// As que não dá para escolher ficam na lista, bloqueadas, com o motivo: sem acesso aos relatórios (o negócio
// tem a conta, mas ela não foi atribuída ao usuário do token) ou já conectada em outra fonte.
export function AdsAccountPicker({ accounts, chosen, onChange, disabled = false }: AdsAccountPickerProps) {
    const [search, setSearch] = useState('')
    const free = accounts.filter((a) => accountBlock(a) === null)
    const q = search.trim().toLocaleLowerCase('pt-BR')
    const shown = q
        ? accounts.filter((a) => `${a.name} ${a.id} ${a.business ?? ''}`.toLocaleLowerCase('pt-BR').includes(q))
        : accounts
    return (
        <div className="stack" style={{ gap: 8 }}>
            {free.length > 1 && (
                <div className="ads-campaign-tools">
                    {accounts.length > SEARCH_FROM && (
                        <input
                            className="field connect-grow"
                            type="search"
                            placeholder="Buscar conta"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            aria-label="Buscar conta de anúncios"
                        />
                    )}
                    <button
                        className="btn btn-sm"
                        type="button"
                        disabled={disabled}
                        onClick={() => onChange(free.filter((a) => a.active).map((a) => a.id))}
                    >
                        Marcar as ativas
                    </button>
                    <button className="btn btn-sm" type="button" disabled={disabled} onClick={() => onChange([])}>
                        Limpar
                    </button>
                    <span className="muted small">
                        {chosen.length} de {free.length} disponíve{free.length === 1 ? 'l' : 'is'}
                    </span>
                </div>
            )}
            <div className="card ads-accounts" role="group" aria-label="Contas de anúncios do token">
                {shown.length === 0 && <p className="muted small">Nenhuma conta com esse nome.</p>}
                {shown.map((a) => {
                    const block = accountBlock(a)
                    return (
                        <label key={a.id} className={`ads-account${block ? ' blocked' : ''}`}>
                            <input
                                type="checkbox"
                                checked={chosen.includes(a.id)}
                                disabled={disabled || block !== null}
                                onChange={(e) => onChange(toggle(chosen, a.id, e.target.checked))}
                            />
                            <span className="ads-check-text">
                                <span>
                                    <strong>{a.name}</strong> <span className="muted small">({a.id})</span>
                                </span>
                                <span className="muted small">
                                    {[
                                        a.business,
                                        a.currency,
                                        a.timezone,
                                        `${money(a.spent, a.currency || 'BRL')} gastos no total`,
                                    ]
                                        .filter(Boolean)
                                        .join(' · ')}
                                </span>
                                {block && <span className="small ads-block">{block}</span>}
                            </span>
                            <span className={`badge ${a.active ? 'ok' : 'warn'}`}>
                                {a.active ? 'Ativa' : (a.status ?? 'Parada')}
                            </span>
                        </label>
                    )
                })}
            </div>
        </div>
    )
}
