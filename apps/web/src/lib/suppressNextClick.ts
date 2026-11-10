// Módulo: cancela o próximo clique da página (só ele).
// Para que serve: ao soltar um card arrastado, o navegador dispara um "click" nele; sem isto, o link abriria o dashboard.
// Se nenhum clique vier (arraste pelo teclado), a trava some sozinha no próximo ciclo.
export function suppressNextClick() {
    const cancel = (event: MouseEvent) => {
        event.preventDefault()
        event.stopPropagation()
    }
    window.addEventListener('click', cancel, { capture: true, once: true })
    setTimeout(() => window.removeEventListener('click', cancel, { capture: true }), 0)
}
