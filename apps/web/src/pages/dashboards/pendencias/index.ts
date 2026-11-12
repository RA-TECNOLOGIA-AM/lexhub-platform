import { v1GenericoModule } from '../v1Generico.ts'
import { PendenciasNgContent } from './PendenciasNgContent.tsx'

// O dashboard Pendências (banco NG, unidades NG e RJ): de onde vêm os dados e como mostrar.
export const pendencias = v1GenericoModule('pendencias', PendenciasNgContent)
