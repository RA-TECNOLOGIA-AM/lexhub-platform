// Módulo: os atalhos de teclado do guia de uso, escritos com as teclas de cada sistema.
// Sem React (testado em atalhos.test.ts). Atalho novo no app = uma linha aqui.

export type KeySystem = 'windows' | 'mac'

// Mac, iPhone e iPad usam Cmd/Option; o resto (Windows, Linux, ChromeOS, Android) usa Ctrl/Alt.
export function detectSystem(userAgent: string): KeySystem {
    return /Mac OS X|Macintosh|iPhone|iPad|iPod/.test(userAgent) ? 'mac' : 'windows'
}

type Shortcut = { keys: Record<KeySystem, string>; what: string }

const SHORTCUTS: Shortcut[] = [
    {
        keys: { windows: 'Esc', mac: 'Esc' },
        what: 'Fecha menus e janelas (Filtros, Exportar, Configurações) e limpa a busca.',
    },
    {
        keys: { windows: 'Enter ou espaço num gráfico', mac: 'Return ou espaço num gráfico' },
        what: 'Seleciona a barra ou a fatia em foco (o mesmo que clicar).',
    },
    {
        keys: { windows: '← e → num gráfico de linha', mac: '← e → num gráfico de linha' },
        what: 'Percorrem os pontos.',
    },
    {
        keys: { windows: 'Espaço, setas, espaço (no hub)', mac: 'Espaço, setas, espaço (no hub)' },
        what: 'Pega um card, move e solta. Esc cancela.',
    },
    { keys: { windows: 'Ctrl + clique', mac: '⌘ Command + clique' }, what: 'Abre o link numa nova aba.' },
    {
        keys: { windows: 'F11', mac: '⌃ Control + ⌘ Command + F' },
        what: 'Tela cheia, se o botão "Tela cheia" não funcionar no seu navegador.',
    },
]

// As linhas da tabela (tecla, o que faz) no sistema escolhido.
export const shortcutRows = (system: KeySystem): string[][] => SHORTCUTS.map((s) => [s.keys[system], s.what])
