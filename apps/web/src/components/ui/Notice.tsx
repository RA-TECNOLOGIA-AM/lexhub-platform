import { Icon } from './Icon.tsx'

type NoticeProps = {
    message: string
    onClose: () => void // clique no X
}

// Módulo: aviso informativo com botão de fechar (ex.: "ainda não está disponível").
// Quem usa guarda a mensagem no estado e decide quando mostrar.
export function Notice({ message, onClose }: NoticeProps) {
    return (
        <div className="notice info" role="status">
            <Icon name="info" size={18} />
            <span style={{ flex: 1 }}>{message}</span>
            <button className="iconbtn" type="button" aria-label="Fechar aviso" onClick={onClose}>
                <Icon name="close" size={16} />
            </button>
        </div>
    )
}
