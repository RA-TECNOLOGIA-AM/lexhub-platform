import { v1GenericoModule } from '../v1Generico.ts'
import { OrgDocumentosNgContent } from './OrgDocumentosNgContent.tsx'

// O dashboard Organização de documentos (banco NG, unidades NG e RJ): de onde vêm os dados e como mostrar.
export const orgDocumentos = v1GenericoModule('org-documentos', OrgDocumentosNgContent)
