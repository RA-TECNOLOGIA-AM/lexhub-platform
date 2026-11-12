import { v1GenericoModule } from '../v1Generico.ts'
import { MarketingNgContent } from './MarketingNgContent.tsx'

// O dashboard Marketing (banco NG, só a unidade NG): de onde vêm os dados e como mostrar.
export const marketing = v1GenericoModule('marketing', MarketingNgContent)
