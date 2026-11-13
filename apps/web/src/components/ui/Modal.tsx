import { useId, useLayoutEffect, useRef, type ReactNode } from 'react'
import { Icon } from './Icon.tsx'

type ModalProps = {
    title: ReactNode
    subtitle?: ReactNode // linha pequena embaixo do título
    description?: ReactNode // parágrafo de orientação embaixo do cabeçalho, na largura toda
    aside?: ReactNode // ao lado do título, antes do fechar (ex.: uma badge)
    className?: string // largura/ajustes da tela que usa
    onClose: () => void
    children: ReactNode // o corpo (rola se passar da altura)
    footer?: ReactNode // botões no rodapé
}

// Módulo: o modal da casa — <dialog> do navegador (foco preso, Esc fecha, fundo escurecido),
// cabeçalho com título e botão de fechar, corpo que rola e rodapé opcional.
// Abre ao montar; quem usa decide quando montar e o que fazer ao fechar (onClose).
// Ao desmontar fecha o <dialog> antes de ele sair da página: o navegador libera a tela e devolve
// o foco ao botão que abriu — por isso os botões do rodapé podem chamar só o onClose de quem usa.
export function Modal({ title, subtitle, description, aside, className, onClose, children, footer }: ModalProps) {
    const dialog = useRef<HTMLDialogElement>(null)
    const titleId = useId()

    useLayoutEffect(() => {
        const element = dialog.current
        element?.showModal()
        return () => element?.close()
    }, [])

    function close() {
        dialog.current?.close()
        onClose()
    }

    return (
        <dialog
            ref={dialog}
            className={`export-dialog ${className ?? ''}`}
            aria-labelledby={titleId}
            onCancel={(event) => {
                event.preventDefault()
                close()
            }}
        >
            <div className="export-head">
                <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'nowrap' }}>
                    <div>
                        <h2 className="h2" id={titleId} style={{ margin: 0 }}>
                            {title}
                        </h2>
                        {subtitle && <span className="muted small">{subtitle}</span>}
                    </div>
                    <div className="row" style={{ flexWrap: 'nowrap' }}>
                        {aside}
                        <button className="iconbtn" type="button" aria-label="Fechar" onClick={close}>
                            <Icon name="close" size={16} />
                        </button>
                    </div>
                </div>
                {description && (
                    <p className="muted small" style={{ margin: '6px 0 0' }}>
                        {description}
                    </p>
                )}
            </div>
            <div className="export-body">{children}</div>
            {footer && <div className="export-foot">{footer}</div>}
        </dialog>
    )
}
