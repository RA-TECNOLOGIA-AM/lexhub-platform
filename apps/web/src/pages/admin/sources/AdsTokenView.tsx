import type { AdsCapabilityStatus, AdsTokenAccount, AdsTokenInfo } from '../../../types/index.ts'
import { Icon, type IconName } from '../../../components/ui/Icon.tsx'
import { dateLabel, money } from './facebookAds.ts'

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
                {info.tokenType && (
                    <>
                        <dt>Tipo</dt>
                        <dd>{info.tokenType}</dd>
                    </>
                )}
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
    chosen: string | null
    onChoose: (account: AdsTokenAccount) => void
    disabled?: boolean
}

// Módulo: as contas de anúncios que o token acessa, pelo nome (a ativa primeiro). Escolher preenche o ID.
export function AdsAccountPicker({ accounts, chosen, onChoose, disabled = false }: AdsAccountPickerProps) {
    return (
        <div className="card connect-offices ads-accounts" role="radiogroup" aria-label="Contas de anúncios do token">
            {accounts.map((a) => (
                <button
                    key={a.id}
                    type="button"
                    role="radio"
                    aria-checked={chosen === a.id}
                    className="source source-btn connect-office"
                    disabled={disabled}
                    onClick={() => onChoose(a)}
                >
                    <div className="source-name">
                        <span className="unit-name">
                            {a.name} <span className="muted small">({a.id})</span>
                        </span>
                        <span className="muted small">
                            {[a.business, a.currency, a.timezone, `${money(a.spent, a.currency)} gastos no total`]
                                .filter(Boolean)
                                .join(' · ')}
                        </span>
                    </div>
                    <span className={`badge ${a.active ? 'ok' : 'warn'}`}>
                        {a.active ? 'Ativa' : (a.status ?? 'Parada')}
                    </span>
                </button>
            ))}
        </div>
    )
}
