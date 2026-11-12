import { v1GenericoModule } from '../v1Generico.ts'
import { ComissaoNgContent } from './ComissaoNgContent.tsx'

// O dashboard Comissão Comercial (banco NG, unidades NG e RJ): de onde vêm os dados e como mostrar.
export const comissao = v1GenericoModule('comissao', ComissaoNgContent)
