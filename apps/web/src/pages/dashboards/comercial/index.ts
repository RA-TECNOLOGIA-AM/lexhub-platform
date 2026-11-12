import { v1GenericoModule } from '../v1Generico.ts'
import { ComercialNgContent } from './ComercialNgContent.tsx'

// O dashboard Comercial (banco NG, unidades NG e RJ): de onde vêm os dados e como mostrar.
export const comercial = v1GenericoModule('comercial', ComercialNgContent)
