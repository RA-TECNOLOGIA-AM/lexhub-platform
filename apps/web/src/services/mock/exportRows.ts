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
    // Recursal (_LABELS_EXPORT_RECURSAL_NG)
    id: 'ID',
    parte_adversa: 'Parte Adversa',
    data_ultima_movimentacao: 'Última Movimentação',
    operacao: 'Operação',
    vara: 'Vara',
    valor_causa_sentenca: 'Valor da Causa (Sentença)',
    valor_causa_acordo: 'Valor da Causa (Acordo)',
    dano_moral_sentenca: 'Dano Moral (Sentença)',
    dano_material_sentenca: 'Dano Material (Sentença)',
    status_1g: 'Status 1º Grau',
    juiz_1g: 'Juiz (1º Grau)',
    status_2g: 'Status 2º Grau',
    decisao: 'Decisão',
    data_sentenca: 'Data da Sentença',
    data_transito_julgado: 'Data Trânsito em Julgado',
    dt_entrada_recursal: 'Data Entrada Recursal',
    dt_saida_recursal: 'Data Saída Recursal',
    atividade_recursos: 'Atividade em Andamento',
    status_agendamento_recursos: 'Status da Atividade',
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
    id: (i) => 900_000 + i,
    parte_adversa: (i) => pick(['Banco Exemplo S.A.', 'Financeira Fictícia S.A.'], i),
    data_ultima_movimentacao: (i) => day(1 + (i % 28)),
    operacao: (i) => pick(['NGAM', 'NGPB'], i),
    vara: (i, f) => pick(f.vara_recursal ?? ['1º vara', '2º vara', '3º vara'], i),
    valor_causa_sentenca: (i) => 8_000 + i * 411,
    valor_causa_acordo: (i) => 6_500 + i * 377,
    dano_moral_sentenca: (i) => 3_000 + i * 90,
    dano_material_sentenca: (i) => 1_200 + i * 45,
    status_1g: (i) => pick(['IMPROCEDENTE', 'PROCEDENTE COM PROVEITO ECONÔMICO'], i),
    juiz_1g: (i, f) => pick(f.juiz_recursal ?? ['Juiz Exemplo Um', 'Juíza Exemplo Dois'], i),
    status_2g: (i) => pick(['IMPROCEDENTE', 'PROCEDENTE (COM PROVEITO ECONÔMICO)'], i),
    decisao: (i) => pick(['Mantido Ganho', 'Mantido Perda', 'Revertido Ganho'], i),
    data_sentenca: (i) => day(1 + (i % 20)),
    data_transito_julgado: (i) => (i % 3 === 0 ? day(5 + (i % 20)) : ''),
    dt_entrada_recursal: (i) => day(1 + (i % 28)),
    dt_saida_recursal: (i) => (i % 4 === 0 ? day(3 + (i % 25)) : ''),
    atividade_recursos: (i) => pick(['ANÁLISE SENTENÇA', 'CONTRARRAZÕES', ''], i),
    status_agendamento_recursos: (i) => pick(['Visualizado', 'Recebido', ''], i),
}

export function exportRowsFor(campos: string[], filters: DashboardFilters = {}): Record<string, string | number>[] {
    return Array.from({ length: ROWS }, (_, i) =>
        Object.fromEntries(campos.map((slug) => [slug, VALUE[slug]?.(i, filters) ?? ''])),
    )
}
