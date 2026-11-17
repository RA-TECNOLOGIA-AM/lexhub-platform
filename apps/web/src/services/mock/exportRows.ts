import type { DashboardFilters } from '../../types/index.ts'
import { funcionarios } from './helpers.ts'

// Linhas fictícias da exportação no mock: uma por demanda, como o relatório da v1.
// Rótulos = cópia de _LABELS_EXPORT_* da v1, para o cabeçalho sair igual ao do servidor.
export const EXPORT_LABELS: Record<string, string> = {
    id_demanda: 'ID da Demanda',
    numero_processo: 'Número do Processo',
    cliente_nome: 'Nome do Cliente',
    funcionario: 'Funcionário Responsável',
    materia: 'Matéria',
    situacao: 'Situação',
    status_demanda: 'Status da Demanda',
    setor_atual: 'Setor Atual',
    origem: 'Origem',
    area_atuacao: 'Área de Atuação',
    valor_causa: 'Valor de Causa (R$)',
    dano_moral: 'Dano Moral (R$)',
    data_entrada: 'Data de Entrada',
    data_saida: 'Data de Saída',
    // Julgados Acórdãos (_LABELS_EXPORT_JULGADOS_ACORDAO_NG)
    competencia: 'Competência',
    comarca: 'Comarca',
    uf: 'UF',
    fase: 'Fase',
    subfase: 'Subfase',
    camara_turma: 'Câmara/Turma',
    relator_2g: 'Relator (2G)',
    merito_2g: 'Acórdão de Mérito',
    motivo_extincao: 'Motivo da Extinção',
    data_ajuizamento: 'Data de Distribuição',
    data_acordao: 'Data do Acórdão',
    valor_acordao: 'Valor do Acórdão',
    data_acordao_embargos: 'Data do Acórdão de Embargos',
    status_acordao_embargos: 'Status do Acórdão de Embargos',
    resultado_embargos_estimado: 'Status Resultante dos Embargos',
}

const ROWS = 25
const CLIENTES = ['Maria Souza', 'João Lima', 'Ana Castro', 'Pedro Alves', 'Luiza Rocha']
const MATERIAS = ['ANP', 'RUBRICAS_REUNIDAS', 'CESTA', 'SVA', 'MORA']
const AREAS = ['Bancário', 'Consumidor', 'Previdenciário']

const pick = <T>(list: T[], i: number): T => list[i % list.length]
const day = (n: number) => `2026-10-${String(n).padStart(2, '0')}`

// O valor de cada campo na linha i. Com filtro aplicado, usa só os valores filtrados (como o servidor faria).
const VALUE: Record<string, (i: number, f: DashboardFilters) => string | number> = {
    id_demanda: (i) => 50_000 + i,
    numero_processo: (i) => `${String(1000 + i).padStart(7, '0')}-45.2026.8.04.0001`,
    cliente_nome: (i) => pick(CLIENTES, i),
    funcionario: (i, f) => pick(f.funcionario ?? funcionarios, i),
    materia: (i, f) => pick(f.materia ?? MATERIAS, i),
    situacao: (i) => pick(['Ativo', 'Suspenso'], i),
    status_demanda: (i) => pick(['Protocolado', 'Represado', 'Devolvido'], i),
    setor_atual: (i) => pick(['Protocolo', 'Peticionamento', 'Pendência'], i),
    origem: (i) => pick(['Protocolo', 'Org. de documentos'], i),
    area_atuacao: (i) => pick(AREAS, i),
    valor_causa: (i) => 10_000 + i * 731,
    dano_moral: (i) => 5_000 + i * 113,
    data_entrada: (i) => day(1 + (i % 28)),
    data_saida: (i) => day(2 + (i % 27)),
    competencia: (i) => pick(['Cível', 'Juizado Especial Cível', 'Consumidor'], i),
    comarca: (i, f) => pick(f.comarca_julgados ?? ['Manaus', 'Parintins', 'Itacoatiara'], i),
    uf: (i, f) => pick(f.uf_julgados ?? ['AM'], i),
    fase: (i) => pick(['Recursal', 'Trânsito em julgado'], i),
    subfase: (i) => pick(['Aguardando trânsito em julgado', 'Arquivado'], i),
    camara_turma: (i) => `${1 + (i % 3)}ª Câmara Cível`,
    relator_2g: (i, f) => pick(f.relator_julgados ?? ['Ana Paula Ribeiro', 'Flávia Nogueira', 'Roberta Sales'], i),
    merito_2g: (i) => pick(['Procedente', 'Improcedente', 'Extinto sem resolução de mérito'], i),
    motivo_extincao: (i) => pick(['', 'Ilegitimidade passiva', ''], i),
    data_ajuizamento: (i) => `2024-0${1 + (i % 9)}-15`,
    data_acordao: (i) => day(1 + (i % 28)),
    valor_acordao: (i) => `R$ ${(5_000 + i * 317).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
    data_acordao_embargos: (i) => (i % 4 === 0 ? day(10 + (i % 18)) : ''),
    status_acordao_embargos: (i) => (i % 4 === 0 ? 'REJEITADOS' : ''),
    resultado_embargos_estimado: (i) => (i % 4 === 0 ? 'Status Mantido' : ''),
}

export function exportRowsFor(campos: string[], filters: DashboardFilters = {}): Record<string, string | number>[] {
    return Array.from({ length: ROWS }, (_, i) =>
        Object.fromEntries(campos.map((slug) => [slug, VALUE[slug]?.(i, filters) ?? ''])),
    )
}
