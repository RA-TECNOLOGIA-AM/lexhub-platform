import type { ExportReport } from '../../../lib/exportFields.ts'

// Espelha `CAMPOS_EXPORT` e `CAMPOS_EXPORT_FACEBOOK` (app/analyses/NG/marketing_lexpre.py, cópia da v1). Mudou no
// servidor? Muda aqui também: a API só aceita campos da lista dela.
export const marketingExport: ExportReport[] = [
    {
        key: null,
        title: 'Leads',
        groups: [
            {
                group: 'Atendimento',
                fields: [
                    { slug: 'id_action', label: 'ID do Atendimento' },
                    { slug: 'cliente', label: 'Nome do Cliente' },
                    { slug: 'atendente', label: 'Atendente' },
                    { slug: 'uf', label: 'UF' },
                    { slug: 'data_entrada', label: 'Data de Entrada' },
                    { slug: 'status', label: 'Status do Atendimento' },
                    { slug: 'assinado', label: 'Assinado' },
                    { slug: 'data_assinatura', label: 'Data de Assinatura' },
                ],
            },
            {
                group: 'Origem e rastreio',
                fields: [
                    { slug: 'canal_aquisicao', label: 'Canal de Aquisição' },
                    { slug: 'tipo_trafego', label: 'Tipo de Tráfego' },
                    { slug: 'prospeccao', label: 'Prospecção' },
                    { slug: 'campanha', label: 'Campanha' },
                    { slug: 'conjunto', label: 'Conjunto' },
                    { slug: 'criativo', label: 'Criativo' },
                    { slug: 'posicionamento', label: 'Posicionamento (original)' },
                    { slug: 'plataforma_anuncio', label: 'Posicionamento' },
                    { slug: 'categoria', label: 'Categoria' },
                ],
            },
            {
                group: 'Perfil',
                fields: [
                    { slug: 'idade', label: 'Idade' },
                    { slug: 'faixa_etaria', label: 'Faixa Etária' },
                    { slug: 'genero', label: 'Gênero' },
                    { slug: 'ocupacao', label: 'Ocupação' },
                    { slug: 'media_salarial', label: 'Média Salarial Mensal' },
                    { slug: 'tipo_residencia', label: 'Tipo de Residência' },
                    { slug: 'pessoas_dependentes', label: 'Pessoas Dependentes' },
                    { slug: 'triado', label: 'Respondeu a Triagem' },
                ],
            },
            {
                group: 'Demandas',
                fields: [
                    { slug: 'qtd_demandas', label: 'Qtd. Demandas' },
                    { slug: 'rubricas', label: 'Rubricas' },
                    { slug: 'qtd_protocolados', label: 'Qtd. Protocolados' },
                    { slug: 'valor_causa_protocolado', label: 'Valor de Causa Protocolado (R$)' },
                ],
            },
        ],
    },
    {
        key: 'facebook',
        title: 'Facebook Ads',
        options: [
            {
                key: 'detalhamento',
                label: 'Detalhamento',
                choices: [
                    { value: 'anuncio', label: 'Por anúncio' },
                    { value: 'conjunto', label: 'Por conjunto' },
                    { value: 'campanha', label: 'Por campanha' },
                    { value: 'dia', label: 'Por dia e anúncio' },
                    {
                        value: 'total',
                        label: 'Só o total',
                        note: 'Só período e unidade valem aqui; os filtros clicados na página não, como na v1.',
                    },
                ],
            },
        ],
        groups: [
            {
                group: 'Anúncio',
                fields: [
                    { slug: 'data', label: 'Data' },
                    { slug: 'conta', label: 'Conta' },
                    { slug: 'id_conta', label: 'ID da Conta' },
                    { slug: 'campanha', label: 'Campanha' },
                    { slug: 'campaign_id', label: 'ID da Campanha' },
                    { slug: 'conjunto', label: 'Conjunto' },
                    { slug: 'adset_id', label: 'ID do Conjunto' },
                    { slug: 'anuncio', label: 'Anúncio' },
                    { slug: 'ad_id', label: 'ID do Anúncio' },
                ],
            },
            {
                group: 'Métricas',
                fields: [
                    { slug: 'primeiro_dia', label: 'Primeiro Dia' },
                    { slug: 'ultimo_dia', label: 'Último Dia' },
                    { slug: 'valor_gasto', label: 'Valor Gasto (R$)' },
                    { slug: 'alcance', label: 'Alcance (soma diária)' },
                    { slug: 'impressoes', label: 'Impressões' },
                    { slug: 'cliques', label: 'Cliques no Link' },
                    { slug: 'pageview', label: 'Pageview' },
                    { slug: 'leads_facebook', label: 'Leads (Facebook)' },
                    { slug: 'cadastros', label: 'Cadastros' },
                    { slug: 'leads_lexpre', label: 'Leads (LexPre)' },
                    { slug: 'assinados_lexpre', label: 'Clientes Assinados (LexPre)' },
                    { slug: 'cpl', label: 'CPL (R$)' },
                    { slug: 'cac', label: 'CAC (R$)' },
                ],
            },
        ],
    },
]
