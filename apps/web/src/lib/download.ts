// Módulo: entrega um arquivo para o navegador baixar (o "Salvar como" de sempre).
// Recebe o conteúdo (Blob) e o nome; serve para o CSV do mock e para o arquivo que vem da API.
export function saveFile(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.append(link)
    link.click()
    link.remove()
    // Libera a memória depois que o navegador começou o download.
    setTimeout(() => URL.revokeObjectURL(url), 1000)
}
