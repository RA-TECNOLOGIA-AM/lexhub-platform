import { v1GenericoModule } from '../v1Generico.ts'
import { PeticionamentoNgContent } from './PeticionamentoNgContent.tsx'

// O dashboard Peticionamento (banco NG, unidades NG e RJ): de onde vêm os dados e como mostrar.
export const peticionamento = v1GenericoModule('peticionamento', PeticionamentoNgContent)
