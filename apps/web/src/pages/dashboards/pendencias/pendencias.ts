import type { PendenciasResponse, Point } from '../../../types/index.ts'
import type { V1GenericoResponse } from '../v1Stats.ts'
import { nomesFuncionarios } from '../setor/setor.ts'

// As Pendências do banco legado vêm de três rotas da v1: /pendencias (NG) e /pendencias_RJ, com os mesmos
// nomes da página das Pendências (LexPre), e /pendencia_LA, com _LA nos nomes e sem reajuizamento nem os
// comparativos. Aqui a resposta vira a das Pendências (LexPre), e a página é a mesma. Só lógica pura (testada
// em pendencias.test.ts).

type Comissao = PendenciasResponse['comissionamento_pendencias_por_funcionario'][number]

const numero = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

function pontos(v: unknown): Point[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((p): p is { name: unknown; value: unknown } => typeof p === 'object' && p !== null)
        .map((p) => ({ name: String(p.name ?? ''), value: numero(p.value) ?? 0 }))
}

function linhasComissao(v: unknown): Comissao[] {
    if (!Array.isArray(v)) return []
    return v
        .filter((r): r is Record<string, unknown> => typeof r === 'object' && r !== null)
        .map((r) => ({
            funcionario: String(r.funcionario ?? ''),
            taxa_resolvido: numero(r.taxa_resolvido) ?? 0,
            taxa_cancelamento: numero(r.taxa_cancelamento) ?? 0,
            qtd_resolvido: numero(r.qtd_resolvido) ?? 0,
            valor: numero(r.valor) ?? 0,
            qtd_x_valor: numero(r.qtd_x_valor) ?? 0,
            comissao: numero(r.comissao) ?? 0,
        }))
}

const nomes = (v: unknown): string[] => (Array.isArray(v) ? v.map((x) => String(x).trim()).filter(Boolean) : [])

// Veio da rota da LA (banco LA)? Pela rota (`dashboard`): a resposta da v1 traz os campos de todas as rotas
// (os das outras vêm null).
export const pendenciasDaLA = (data: V1GenericoResponse): boolean =>
    data.dashboard ? data.dashboard === 'pendencia_LA' : numero(data.stats?.pendencias_total_LA) !== null

// A resposta da rota da v1 (NG, RJ ou LA) no formato das Pendências (LexPre).
export function lerPendencias(data: V1GenericoResponse): PendenciasResponse {
    const d = data as V1GenericoResponse & Record<string, unknown>
    const s = data.stats ?? {}
    const la = pendenciasDaLA(data)
    const sufixo = la ? '_LA' : ''
    const n = (campo: string) => numero(s[`${campo}${sufixo}`]) ?? 0
    const nulo = (campo: string) => numero(s[campo])
    const lista = (campo: string) => pontos(d[`${campo}${sufixo}`])
    const funcionarios = nomes(d[`funcionarios_pendencias${sufixo}`])
    const media = lista('media_pendencias_resolvidas_por_funcionario')
    return {
        meta: data.meta,
        stats: {
            pendencias_total: n('pendencias_total'),
            pendencias_resolvidas: n('pendencias_resolvidas'),
            pendencias_canceladas: n('pendencias_canceladas'),
            pendencias_taxa_resolvidos: n('pendencias_taxa_resolvidos'),
            pendencias_taxa_nao_resolvidos: n('pendencias_taxa_nao_resolvidos'),
            pendencias_taxa_canceladas: n('pendencias_taxa_canceladas'),
            media_tempo_resolvidos_pendencia: n('media_tempo_resolvidos_pendencia'),
            mediana_tempo_resolvidos_pendencia: n('mediana_tempo_resolvidos_pendencia'),
            // A rota da LA não manda comparativos; a da NG, só estes dois.
            comparativo_pendencias_resolvidas: la ? null : nulo('comparativo_pendencias_resolvidas'),
            comparativo_tempo_medio_resolvidos_pendencia: la
                ? null
                : nulo('comparativo_tempo_medio_pendencias_resolvidas'),
            comparativo_mediana_tempo_resolvidos_pendencia: null,
            pendencias_nao_resolvidas: n('pendencias_nao_resolvidas'),
            pendencias_nao_resolvidas_com_atraso: n('pendencias_nao_resolvidas_com_atraso'),
            pendencias_triagem: n('pendencias_triagem'),
            // A LA não separa o reajuizamento: os campos ficam de fora (a página esconde os dois cards).
            ...(la
                ? {}
                : {
                      pendencias_nao_resolvidas_reajuizamento: n('pendencias_nao_resolvidas_reajuizamento'),
                      pendencias_resolvidas_reajuizamento: n('pendencias_resolvidas_reajuizamento'),
                  }),
        },
        pendencias_resolvidas_por_dia: lista('pendencias_resolvidas_por_dia'),
        pendencias_resolvidas_por_mes: lista('pendencias_resolvidas_por_mes'),
        pendencias_nao_resolvidas_por_origem: lista('pendencias_nao_resolvidas_por_origem'),
        media_pendencias_resolvidas_por_funcionario: media,
        comissionamento_pendencias_por_funcionario: linhasComissao(
            d[la ? 'comissionamento_pendencias_LA_por_funcionario' : 'comissionamento_pendencias_por_funcionario'],
        ),
        opcoes_filtro: {
            funcionarios: nomesFuncionarios(
                media.map((p) => p.name),
                funcionarios,
            ),
        },
    }
}
