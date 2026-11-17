import { useState } from 'react'
import { dataClient } from '../services/client.ts'
import { saveFile } from '../lib/download.ts'
import type { ExportFormat } from '../lib/exportFields.ts'
import type { DashboardQuery } from '../types/index.ts'

// Módulo: exportar o relatório do dashboard aberto. Pede o arquivo (com o período e os filtros em uso),
// entrega para o navegador baixar e guarda o aviso que vier (ex.: no mock o XLSX sai como CSV).
// Erro: rejeita, e quem chamou (a janela) mostra a mensagem.
export function useDashboardExport(dashboard: string, query: DashboardQuery) {
    const [notice, setNotice] = useState<string | null>(null)

    // relatorio/opcoes: o relatório escolhido na janela (ex.: Atividades) e o recorte (ex.: { criterio: 'saida' }).
    async function exportReport(
        format: ExportFormat,
        campos: string[],
        relatorio?: string,
        opcoes?: Record<string, string>,
    ) {
        const file = await dataClient.exportDashboard({ ...query, dashboard, format, campos, relatorio, opcoes })
        saveFile(file.blob, file.filename)
        setNotice(file.note ?? null)
    }

    return { exportReport, notice, clearNotice: () => setNotice(null) }
}
