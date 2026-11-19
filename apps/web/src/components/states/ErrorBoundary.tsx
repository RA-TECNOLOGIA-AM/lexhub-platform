import { Component, type ErrorInfo, type ReactNode } from 'react'
import { isChunkLoadError } from './chunkError.ts'
import { StateMessage } from './StateMessage.tsx'

type ErrorBoundaryProps = {
    children: ReactNode
    resetKey?: string // quando muda (ex.: outra rota), a tela tenta renderizar de novo
    title?: string // título do cartão de erro
}

type ErrorBoundaryState = { error: Error | null; resetKey?: string }

// Módulo: segura erro de render dos filhos e mostra um cartão, sem derrubar o resto do app.
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    state: ErrorBoundaryState = { error: null, resetKey: this.props.resetKey }

    static getDerivedStateFromError(error: unknown): Partial<ErrorBoundaryState> {
        return { error: error instanceof Error ? error : new Error(String(error)) }
    }

    // Mudou a rota: limpa o erro para a página nova renderizar.
    static getDerivedStateFromProps(props: ErrorBoundaryProps, state: ErrorBoundaryState) {
        return props.resetKey !== state.resetKey ? { error: null, resetKey: props.resetKey } : null
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error('[ErrorBoundary]', error, info.componentStack)
    }

    render() {
        const { error } = this.state
        if (!error) return this.props.children

        if (isChunkLoadError(error)) {
            return (
                <StateMessage
                    icon="alert"
                    title="Saiu uma versão nova do LexHub"
                    action={
                        <button className="btn btn-primary" type="button" onClick={() => window.location.reload()}>
                            Recarregar a página
                        </button>
                    }
                    alert
                >
                    Recarregue para baixar a versão atual.
                </StateMessage>
            )
        }

        return (
            <StateMessage
                icon="alert"
                title={this.props.title ?? 'Algo deu errado nesta tela'}
                action={
                    <button className="btn" type="button" onClick={() => this.setState({ error: null })}>
                        Tentar de novo
                    </button>
                }
                alert
            >
                O resto do LexHub continua funcionando. Se o erro voltar, avise o time de dev.
            </StateMessage>
        )
    }
}
