import type { Unit } from '../types/index.ts'

// Módulo: o nome de uma unidade para mostrar na tela.
// 'NG' -> 'Nicolas Gomes' (das unidades da pessoa). Unidade que não é física ('Consolidado') ou
// desconhecida mostra o próprio código, para nunca sumir da tela.
export const unitName = (code: string, units: Unit[]): string => units.find((u) => u.code === code)?.name ?? code
