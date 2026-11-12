import { v1GenericoModule } from '../v1Generico.ts'
import { NpsNgContent } from './NpsNgContent.tsx'

// O dashboard NPS (banco NG, só a unidade NG): de onde vêm os dados e como mostrar.
export const nps = v1GenericoModule('nps', NpsNgContent)
