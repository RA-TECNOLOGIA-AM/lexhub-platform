import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { QRCodeSVG } from 'qrcode.react'
import { useAuth } from '../../contexts/auth-context.ts'
import { tvSession } from '../../contexts/tvSession.ts'
import { dataClient, type DeviceCodeResponse } from '../../services/client.ts'
import { activationAddress } from './activationAddress.ts'
import { startDeviceLogin } from './deviceLogin.ts'

// Tela da TV: mostra o QR e espera alguém aprovar pelo celular.
// O laço (consultas, novas tentativas, QR novo quando vence) fica em deviceLogin.ts.
export function TvLoginScreen() {
    const navigate = useNavigate()
    const { refreshSession } = useAuth()
    const [code, setCode] = useState<DeviceCodeResponse | null>(null)
    const [expiresAt, setExpiresAt] = useState(0)
    const [now, setNow] = useState(() => Date.now())
    const [problem, setProblem] = useState<string | null>(null)
    const address = code ? activationAddress(code.verification_uri) : null

    useEffect(
        () =>
            startDeviceLogin(dataClient, {
                onCode(next) {
                    setCode(next)
                    setExpiresAt(Date.now() + next.expires_in * 1_000)
                    setProblem(null)
                },
                onProblem: setProblem,
                async onApproved(session) {
                    await dataClient.setDeviceSession(session)
                    tvSession.start() // a sessão da TV vale 24 h (ver tvSession.ts)
                    await refreshSession()
                    navigate('/', { replace: true })
                },
            }),
        [navigate, refreshSession],
    )

    // Relógio da contagem: só para o texto "QR novo em X min".
    useEffect(() => {
        const timer = window.setInterval(() => setNow(Date.now()), 1_000)
        return () => window.clearInterval(timer)
    }, [])

    const minutesLeft = Math.max(Math.ceil((expiresAt - now) / 60_000), 0)

    return (
        <main className="auth">
            <section className="card auth-card" style={{ maxWidth: 480 }}>
                <div className="stack" style={{ gap: 6, textAlign: 'center' }}>
                    <h1 className="h1" style={{ fontSize: 24 }}>
                        Entrar na TV
                    </h1>
                    <p className="muted small">Escaneie o QR Code com o celular e confirme o código.</p>
                </div>

                {code ? (
                    <div className="stack" style={{ alignItems: 'center', gap: 14 }}>
                        <QRCodeSVG value={code.verification_uri} size={240} level="M" />
                        <div className="stack" style={{ alignItems: 'center', gap: 4 }}>
                            <span className="muted small">
                                {address ? (
                                    <>
                                        Ou acesse <strong>{address}</strong> e digite:
                                    </>
                                ) : (
                                    'Ou abra a página de ativação do LexHub e digite:'
                                )}
                            </span>
                            <strong style={{ fontSize: 24, letterSpacing: 4 }}>{code.user_code}</strong>
                        </div>
                        <span className="muted small">
                            {minutesLeft > 0
                                ? `Um QR Code novo aparece em ${minutesLeft} min`
                                : 'Gerando um QR Code novo…'}
                        </span>
                    </div>
                ) : (
                    !problem && (
                        <p className="muted small" role="status" style={{ textAlign: 'center' }}>
                            Gerando o QR Code…
                        </p>
                    )
                )}

                {problem && (
                    <div className="notice info" role="status">
                        <div className="small">{problem}</div>
                    </div>
                )}

                <p className="muted small auth-foot">
                    <Link className="linkbtn" to="/login">
                        Voltar ao login
                    </Link>
                </p>
            </section>
        </main>
    )
}
