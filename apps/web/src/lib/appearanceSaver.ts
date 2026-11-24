// Módulo: a fila que salva a aparência na conta (testado em appearanceSaver.test.ts).
// A tela muda na hora; o envio vai atrás. Um envio por vez, e quem clica rápido entre temas não gera
// uma chamada por clique: enquanto um envio está no ar, só a escolha mais nova espera a vez.
// Assim a última escolha é sempre a última gravada.

import type { Appearance } from '../types/index.ts'

export const SAVE_ERROR = 'Não foi possível salvar na sua conta.'

export function createAppearanceSaver(
    send: (appearance: Appearance) => Promise<void>, // grava na conta (dataClient.setMyAppearance)
    onError: (message: string | null) => void, // aviso para a tela; null = salvou (limpa o aviso)
): (appearance: Appearance) => Promise<void> {
    let pending: Appearance | null = null
    let draining: Promise<void> | null = null

    async function drain() {
        while (pending) {
            const next = pending
            pending = null
            try {
                await send(next)
                onError(null)
            } catch {
                onError(SAVE_ERROR)
            }
        }
        draining = null
    }

    // Resolve quando a fila esvazia (esta escolha, ou uma mais nova, já foi enviada).
    return (appearance) => {
        pending = appearance
        draining ??= drain()
        return draining
    }
}
