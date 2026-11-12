import { v1GenericoModule } from '../v1Generico.ts'
import { ProtocoloNgContent } from './ProtocoloNgContent.tsx'

// O dashboard Protocolo (banco NG, unidades NG e RJ): de onde vêm os dados e como mostrar.
export const protocolo = v1GenericoModule('protocolo', ProtocoloNgContent)
