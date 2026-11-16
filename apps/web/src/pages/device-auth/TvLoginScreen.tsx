import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { QRCodeSVG } from 'qrcode.react'
import { useAuth } from '../../contexts/auth-context.ts'
import { DataError } from '../../services/errors.ts'
import { dataClient } from '../../services/client.ts'

export function TvLoginScreen() {
    const navigate = useNavigate()
    const { refreshSession } = useAuth()
    const [retry, setRetry] = useState(0)
    const [verificationUri, setVerificationUri] = useState('')
    const [userCode, setUserCode] = useState('')
    const [secondsLeft, setSecondsLeft] = useState<number | null>(null)
    const [error, setError] = useState('')

    useEffect(() => {
        let cancelled = false
        let pollTimer: number | undefined
        let expiryTimer: number | undefined
        let countdownTimer: number | undefined
        let busy = false
        let intervalMs = 5_000
        let deviceCode = ''

        const stopPolling = () => {
            if (pollTimer !== undefined) window.clearInterval(pollTimer)
            pollTimer = undefined
        }

        const poll = async () => {
            if (cancelled || busy) return
            busy = true
            try {
                const result = await dataClient.pollDeviceToken(deviceCode)
                if (cancelled) return
                if (result.status === 'expired_token') {
                    stopPolling()
                    setError('Este código expirou. Gere um novo para entrar.')
                    return
                }
                setError('')
                if (result.status === 'slow_down') {
                    intervalMs += 5_000
                    stopPolling()
                    pollTimer = window.setInterval(() => void poll(), intervalMs)
                    return
                }
                if (result.status === 'approved') {
                    stopPolling()
                    if (expiryTimer !== undefined) window.clearTimeout(expiryTimer)
                    if (countdownTimer !== undefined) window.clearInterval(countdownTimer)
                    await dataClient.setDeviceSession(result)
                    await refreshSession()
                    if (!cancelled) navigate('/', { replace: true })
                }
            } catch (reason) {
                if (!cancelled) {
                    setError(
                        reason instanceof DataError
                            ? reason.message
                            : 'Falha de rede ao consultar a TV. Vamos tentar novamente.',
                    )
                }
            } finally {
                busy = false
            }
        }

        const start = async () => {
            setError('')
            setVerificationUri('')
            setUserCode('')
            try {
                const result = await dataClient.createDeviceCode()
                if (cancelled) return
                deviceCode = result.device_code
                setVerificationUri(result.verification_uri)
                setUserCode(result.user_code)
                intervalMs = result.interval * 1_000
                setSecondsLeft(result.expires_in)
                pollTimer = window.setInterval(() => void poll(), intervalMs)
                expiryTimer = window.setTimeout(() => {
                    stopPolling()
                    setSecondsLeft(0)
                    setError('Este código expirou. Gere um novo para entrar.')
                }, result.expires_in * 1_000)
                countdownTimer = window.setInterval(() => {
                    setSecondsLeft((remaining) => (remaining === null ? null : Math.max(remaining - 1, 0)))
                }, 1_000)
            } catch (reason) {
                if (!cancelled) {
                    setError(
                        reason instanceof DataError
                            ? reason.message
                            : 'Não foi possível iniciar o login. Verifique a conexão e tente novamente.',
                    )
                }
            }
        }

        void start()
        return () => {
            cancelled = true
            stopPolling()
            if (expiryTimer !== undefined) window.clearTimeout(expiryTimer)
            if (countdownTimer !== undefined) window.clearInterval(countdownTimer)
        }
    }, [navigate, refreshSession, retry])

    return (
        <main className="auth">
            <section className="card auth-card" style={{ maxWidth: 480 }}>
                <div className="stack" style={{ gap: 6, textAlign: 'center' }}>
                    <h1 className="h1" style={{ fontSize: 24 }}>
                        Entrar na TV
                    </h1>
                    <p className="muted small">Escaneie o QR Code com o celular e confirme o código.</p>
                </div>

                {verificationUri && (
                    <div className="stack" style={{ alignItems: 'center', gap: 14 }}>
                        <QRCodeSVG value={verificationUri} size={240} level="M" />
                        <div className="stack" style={{ alignItems: 'center', gap: 4 }}>
                            <span className="muted small">Ou acesse lexhub e digite:</span>
                            <strong style={{ fontSize: 24, letterSpacing: 4 }}>{userCode}</strong>
                        </div>
                        <span className="muted small">
                            {secondsLeft === 0
                                ? 'Código expirado'
                                : `Código válido por mais ${Math.ceil((secondsLeft ?? 0) / 60)} min`}
                        </span>
                    </div>
                )}

                {error && (
                    <div className="notice danger" role="alert">
                        {error}
                    </div>
                )}

                {error && (
                    <button className="btn btn-primary btn-block" type="button" onClick={() => setRetry((n) => n + 1)}>
                        Gerar novo QR Code
                    </button>
                )}
            </section>
        </main>
    )
}
