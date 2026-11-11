"""Funções e modelos do dashboard_routes.py da v1 usados pelos dashboards LexPre, copiados SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (cópia de 11/11/2026; linha na v1 ao lado de cada um).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# v1: dashboard_routes.py:3121
def _restringir_por_funcionarios_selecionados(
    items: List[Dict[str, Any]],
    funcionarios: Optional[List[str]],
    key: str = "name",
) -> List[Dict[str, Any]]:
    """
    Restringe uma lista de itens agrupados por funcionário (``{"name": ..., ...}``,
    formato de `ChartDataPoint` — ou ``{"funcionario": ..., ...}``, formato das
    linhas de comissionamento, via o parâmetro ``key``) aos nomes efetivamente
    selecionados no filtro da página (quando algum estiver ativo).

    Necessário porque `filter_*_lexpre_por_funcionarios` (org_doc/peticionamento/
    protocolo/pendencia) casa por DEMANDA inteira, não por evento isolado: se
    QUALQUER movimentação da demanda bate com o funcionário filtrado (ex.: ela foi
    devolvida e reatribuída a outra pessoa depois), a demanda inteira — incluindo
    movimentações de OUTROS responsáveis — passa no filtro. Sem este recorte
    adicional nos gráficos "por funcionário", esse outro responsável aparecia como
    uma barra extra mesmo com a página filtrada para uma única pessoa (bug
    reportado em 11/09/2026, ver "Represados"/"Resolvidos"/"Protocolados" e "Valor
    de Causa por Funcionário" no dashboard Org. Documentos LexPre).

    Ajuste de 01/10/2026: o MESMO vazamento existia nas 4 linhas de
    comissionamento por funcionário (Org Doc/Peticionamento/Protocolo/Pendências)
    — elas nunca passavam por este recorte, só os gráficos "por funcionário"
    irmãos (ex.: `valor_causa_*_por_funcionario`) passavam. Usuário reportou: ao
    filtrar só por "Larissa" no Peticionamento, o PDF de comissão veio com uma
    2ª pessoa ("Milena Graça") — demanda com entrada atribuída à Larissa numa
    visita anterior, mas `_funcionario_responsavel` (critério: responsável na
    ÚLTIMA visita) atribuiu a saída final à Milena.
    """
    if not funcionarios:
        return items
    alvos = {str(f).strip() for f in funcionarios if f is not None and str(f).strip()}
    if not alvos:
        return items
    return [item for item in items if str(item.get(key, "")).strip() in alvos]


# v1: dashboard_routes.py:15360
def _filtrar_lexpre_por_ufs(
    rows: List[Dict[str, Any]],
    ufs: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """
    Restringe por uma ou mais UFs do CLIENTE (``customer.uf``) — não confundir
    com escritório: o lexpre só distingue escritório em NGAM/LAAM/LARJ, mas o
    Estratégico Geral pode filtrar NG por sub-escritório de UF (NGAM/NGPA/NGPB),
    e essa UF existe por cliente independente do escritório lexpre. ``None``/
    lista vazia = sem filtro.
    """
    if not ufs:
        return rows
    alvo = {str(u).strip().upper() for u in ufs if str(u).strip()}
    if not alvo:
        return rows
    return [r for r in rows if str(r.get("UF") or "").strip().upper() in alvo]


# v1: dashboard_routes.py:3743
class ChartDataPoint(BaseModel):
    name: str
    value: float
    percent: Optional[float] = None
    valor_causa: Optional[float] = None
    valor_sentenca: Optional[float] = None
    valor_execucao: Optional[float] = None
    id_1g: Optional[int] = None
    id_2g: Optional[int] = None
    tipo: Optional[str] = None
    tempo_medio_dias: Optional[float] = None
    uf: Optional[str] = None
    concluidos: Optional[float] = None
    abertas: Optional[float] = None


# v1: dashboard_routes.py:17130
class ProtocoloLexpreStat(BaseModel):
    total: int = 0
    comparativo: float = 0.0


# v1: dashboard_routes.py:17135
class ProtocoloLexpreValorStat(BaseModel):
    total: float = 0.0
    comparativo: float = 0.0


# v1: dashboard_routes.py:17140
class ProtocoloLexpreNGStats(BaseModel):
    protocolados_total: ProtocoloLexpreStat = ProtocoloLexpreStat()
    valor_causa_protocolado: ProtocoloLexpreValorStat = ProtocoloLexpreValorStat()
    ticket_medio_protocolado: ProtocoloLexpreValorStat = ProtocoloLexpreValorStat()
    media_tempo_protocolado: float = 0.0
    mediana_tempo_protocolado: float = 0.0
    comparativo_tempo_medio_protocolado: float = 0.0
    comparativo_mediana_tempo_protocolado: float = 0.0
    # Acumulado — sempre total, independente do período selecionado.
    represados: int = 0
    devolvido_peticionamento: int = 0
    devolvido_org_doc: int = 0
    devolvido_pendencia: int = 0
    comparativo_devolvido_peticionamento: float = 0.0
    comparativo_devolvido_org_doc: float = 0.0
    comparativo_devolvido_pendencia: float = 0.0


# v1: dashboard_routes.py:17158
class ProtocoloLexpreComissionamentoRow(BaseModel):
    funcionario: str
    qtd_protocolados: int = 0
    valor_comissao: float = 0.0


# v1: dashboard_routes.py:17164
class ProtocoloLexpreNGResponse(BaseModel):
    stats: ProtocoloLexpreNGStats
    protocolados_por_materia: List[ChartDataPoint] = []
    represados_por_materia: List[ChartDataPoint] = []
    protocolados_por_mes: List[ChartDataPoint] = []
    represados_por_mes: List[ChartDataPoint] = []
    protocolados_por_dia: List[ChartDataPoint] = []
    protocolados_por_dia_por_funcionario: Dict[str, List[ChartDataPoint]] = {}
    represados_por_funcionario: List[ChartDataPoint] = []
    protocolados_por_funcionario: List[ChartDataPoint] = []
    media_protocolados_por_funcionario: List[ChartDataPoint] = []
    valor_causa_por_funcionario: List[ChartDataPoint] = []
    comissionamento_por_funcionario: List[ProtocoloLexpreComissionamentoRow] = []
    funcionarios_protocolo: List[str] = []

# v1: dashboard_routes.py:16068
class OrgDocLexpreStat(BaseModel):
    total: int = 0
    comparativo: float = 0.0

# v1: dashboard_routes.py:16073
class OrgDocLexpreComissionamentoRow(BaseModel):
    funcionario: str
    # Quantidade e valor de causa só das demandas que de fato chegaram a ser
    # protocoladas (não de toda demanda "resolvida" pelo Org Doc) — ver
    # `org_doc_lexpre.get_protocolados_por_funcionario` /
    # `get_valor_causa_protocolado_por_funcionario`.
    qtd_protocolados: int = 0
    valor_causa_protocolado: float = 0.0
    valor_comissao: float = 0.0

# v1: dashboard_routes.py:16084
class OrgDocLexpreNGStats(BaseModel):
    resolvidos_total: OrgDocLexpreStat = OrgDocLexpreStat()
    organizados_manualmente: OrgDocLexpreStat = OrgDocLexpreStat()
    organizados_e_peticionados_automaticamente: OrgDocLexpreStat = OrgDocLexpreStat()
    cancelados: OrgDocLexpreStat = OrgDocLexpreStat()
    # Das resolvidas no período, quantas de fato chegaram a ser protocoladas
    # (status atual == "Aguardando Despacho Inicial") — ver `_is_protocolado`.
    protocolados_total: OrgDocLexpreStat = OrgDocLexpreStat()
    media_tempo_resolvidos: float = 0.0
    mediana_tempo_resolvidos: float = 0.0
    comparativo_tempo_medio_resolvidos: float = 0.0
    comparativo_mediana_tempo_resolvidos: float = 0.0
    # Acumulados — sempre totais, independentes do período selecionado.
    represados: int = 0
    devolvido_pendencia: int = 0
    retorno_pendencia: int = 0
    retorno_pet: int = 0
    # Comparativo das devoluções: eventos no período vs mesmo recorte do mês anterior (o card segue total).
    comparativo_devolvido_pendencia: float = 0.0

# v1: dashboard_routes.py:16105
class OrgDocLexpreNGResponse(BaseModel):
    stats: OrgDocLexpreNGStats
    resolvidos_total_por_materia: List[ChartDataPoint] = []
    protocolados_total_por_materia: List[ChartDataPoint] = []
    nao_organizados_total_por_materia: List[ChartDataPoint] = []
    resolvidos_total_por_mes: List[ChartDataPoint] = []
    nao_resolvidos_total_por_mes: List[ChartDataPoint] = []
    resolvidos_por_dia_org: List[ChartDataPoint] = []
    resolvidos_por_dia_por_funcionario_org: Dict[str, List[ChartDataPoint]] = {}
    nao_organizados_por_funcionario: List[ChartDataPoint] = []
    resolvidos_por_funcionario: List[ChartDataPoint] = []
    # Das resolvidas por funcionário, quantas de fato chegaram a ser protocoladas
    # (subconjunto de `resolvidos_por_funcionario`) — ver `_is_protocolado`.
    protocolados_por_funcionario: List[ChartDataPoint] = []
    media_resolvidos_por_funcionario: List[ChartDataPoint] = []
    valor_causa_por_funcionario: List[ChartDataPoint] = []
    # Subconjunto de `valor_causa_por_funcionario` já protocolado de fato (mesmo
    # critério de `protocolados_por_funcionario`/`_is_protocolado`) — o front usa os
    # dois para montar o gráfico empilhado "Valor de Causa por Funcionário"
    # (Protocolado x Não Protocolado, mesmo layout do gráfico "Valor de Causa" do
    # Comercial).
    valor_causa_protocolado_por_funcionario: List[ChartDataPoint] = []
    comissionamento_por_funcionario: List[OrgDocLexpreComissionamentoRow] = []
    funcionarios_org_doc: List[str] = []

# v1: dashboard_routes.py:16575
class PeticionamentoLexpreStat(BaseModel):
    total: int = 0
    comparativo: float = 0.0

# v1: dashboard_routes.py:16580
class PeticionamentoLexpreValorStat(BaseModel):
    total: float = 0.0
    comparativo: float = 0.0

# v1: dashboard_routes.py:16585
class ComissionamentoPeticionamentoLexpreRow(BaseModel):
    funcionario: str
    qtd_acoes_massa: int
    valor_acoes_massa: float
    qtd_x_valor_massa: float
    qtd_acoes_especificas: int
    valor_acoes_especificas: float
    qtd_x_valor_especificas: float
    taxa_resolvidos: Optional[float] = None
    valor_comissao: float

# v1: dashboard_routes.py:16597
class PeticionamentoLexpreNGStats(BaseModel):
    total_peticionados: PeticionamentoLexpreStat = PeticionamentoLexpreStat()
    peticionados_manualmente: PeticionamentoLexpreStat = PeticionamentoLexpreStat()
    peticionados_automaticamente: PeticionamentoLexpreStat = PeticionamentoLexpreStat()
    cancelados: PeticionamentoLexpreStat = PeticionamentoLexpreStat()
    # Das confeccionadas no período, quantas de fato chegaram a ser protocoladas
    # (status atual == "Aguardando Despacho Inicial") — ver `_is_protocolado`.
    protocolados_total: PeticionamentoLexpreStat = PeticionamentoLexpreStat()
    valor_causa_confeccionado: PeticionamentoLexpreValorStat = PeticionamentoLexpreValorStat()
    ticket_medio_confeccionado: PeticionamentoLexpreValorStat = PeticionamentoLexpreValorStat()
    media_tempo_peticionado: float = 0.0
    mediana_tempo_peticionado: float = 0.0
    comparativo_tempo_medio_peticionado: float = 0.0
    comparativo_mediana_tempo_peticionado: float = 0.0
    # Acumulados — sempre totais, independentes do período selecionado.
    represados: int = 0
    retorno_org_doc: int = 0
    retorno_pendencia: int = 0
    comparativo_retorno_org_doc: float = 0.0
    comparativo_retorno_pendencia: float = 0.0

# v1: dashboard_routes.py:16619
class PeticionamentoLexpreNGResponse(BaseModel):
    stats: PeticionamentoLexpreNGStats
    peticionados_por_materia: List[ChartDataPoint] = []
    protocolados_por_materia: List[ChartDataPoint] = []
    represados_por_materia: List[ChartDataPoint] = []
    peticionados_por_mes: List[ChartDataPoint] = []
    represados_por_mes: List[ChartDataPoint] = []
    peticionados_por_dia: List[ChartDataPoint] = []
    peticionados_por_dia_por_funcionario: Dict[str, List[ChartDataPoint]] = {}
    represados_por_funcionario: List[ChartDataPoint] = []
    peticionados_por_funcionario: List[ChartDataPoint] = []
    # Das confeccionadas por funcionário, quantas de fato chegaram a ser
    # protocoladas (subconjunto de `peticionados_por_funcionario`).
    protocolados_por_funcionario: List[ChartDataPoint] = []
    media_peticionado_por_funcionario: List[ChartDataPoint] = []
    valor_causa_por_funcionario: List[ChartDataPoint] = []
    # Subconjunto de `valor_causa_por_funcionario` já protocolado de fato (mesmo
    # critério de `protocolados_por_funcionario`/`_is_protocolado`) — o front usa os
    # dois para montar o gráfico empilhado "Valor de Causa por Funcionário"
    # (Protocolado x Não Protocolado, mesmo layout do gráfico "Valor de Causa" do
    # Comercial).
    valor_causa_protocolado_por_funcionario: List[ChartDataPoint] = []
    comissionamento_por_funcionario: List[ComissionamentoPeticionamentoLexpreRow] = []
    funcionarios_peticionamento: List[str] = []

# v1: dashboard_routes.py:17701
class PendenciaLexpreComissaoRow(BaseModel):
    funcionario: str
    taxa_resolvido: float
    taxa_cancelamento: float
    qtd_resolvido: int
    valor: float
    qtd_x_valor: float
    comissao: float

# v1: dashboard_routes.py:17711
class PendenciaLexpreNGStats(BaseModel):
    pendencias_total: int = 0
    pendencias_resolvidas: int = 0
    pendencias_canceladas: int = 0
    pendencias_taxa_resolvidos: float = 0.0
    pendencias_taxa_nao_resolvidos: float = 0.0
    pendencias_taxa_canceladas: float = 0.0
    media_tempo_resolvidos_pendencia: float = 0.0
    mediana_tempo_resolvidos_pendencia: float = 0.0
    # Variação % vs. mesmo recorte um mês civil antes (ver pendencia_setor_lexpre._comparativo_variacao_percentual).
    comparativo_pendencias_resolvidas: float = 0.0
    comparativo_tempo_medio_resolvidos_pendencia: float = 0.0
    comparativo_mediana_tempo_resolvidos_pendencia: float = 0.0
    # Acumulado — sempre total, independente do período selecionado.
    pendencias_nao_resolvidas: int = 0
    pendencias_nao_resolvidas_com_atraso: int = 0
    # Triagem é outro setor no lexpre, não um sub-estado de Pendências — conta
    # demandas atualmente lá (ver `get_pendencias_triagem`), adicionado em
    # 24/09/2026. Reajuizamento continua sem mapeamento (não existe no lexpre).
    pendencias_triagem: int = 0
    pendencias_nao_resolvidas_reajuizamento: int = 0
    pendencias_resolvidas_reajuizamento: int = 0

# v1: dashboard_routes.py:17735
class PendenciaLexpreNGResponse(BaseModel):
    stats: PendenciaLexpreNGStats
    pendencias_nao_resolvidas_por_origem: List[ChartDataPoint] = []
    pendencias_resolvidas_por_mes: List[ChartDataPoint] = []
    pendencias_resolvidas_por_dia: List[ChartDataPoint] = []
    pendencias_resolvidas_por_dia_por_funcionario: Dict[str, List[ChartDataPoint]] = {}
    media_pendencias_resolvidas_por_funcionario: List[ChartDataPoint] = []
    funcionarios_pendencias: List[str] = []
    comissionamento_pendencias_por_funcionario: List[PendenciaLexpreComissaoRow] = []

# v1: dashboard_routes.py:14872
class ComercialLexpreCanalStat(BaseModel):
    total: int = 0
    comparativo: float = 0.0

# v1: dashboard_routes.py:14877
class ComercialLexpreRatioStat(BaseModel):
    total: float = 0.0
    comparativo: float = 0.0

# v1: dashboard_routes.py:14882
class ComercialLexpreFilaPreProtocoloItem(BaseModel):
    name: str
    total: int = 0
    pendencias: int = 0
    triagem: int = 0
    nao_organizado: int = 0
    nao_confeccionado: int = 0
    nao_protocolado: int = 0
    protocolado: int = 0

# v1: dashboard_routes.py:14893
class ComercialLexpreValorCausaPorAtendenteItem(BaseModel):
    name: str
    protocolado: float = 0.0
    nao_protocolado: float = 0.0
    total: float = 0.0

# v1: dashboard_routes.py:14900
class ComercialLexpreComissionamentoAtendenteRow(BaseModel):
    """Linha do PDF "Gerar comissão" — réplica de `ComissionamentoComercialRow` (banco `ng`), com a coluna `desconto_cancelamentos` a mais."""
    atendente: str
    acoes: int = 0
    comissao_base: float = 0.0
    valor_fm: float = 0.0
    proporcional_am_pa: float = 0.0
    proporcional_pb: float = 0.0
    comissao_com_fm: float = 0.0
    desconto_cancelamentos: float = 0.0

# v1: dashboard_routes.py:14912
class ComercialLexpreNGStats(BaseModel):
    total_leads: int = 0
    clientes_fechados: int = 0
    valor_causa_protocolado_ano: float = 0.0
    ano_meta: int = 2026
    # Seção 02 — Captação por Origem (só atendimentos assinados, filtrados por DATA_ASSINATURA).
    clientes_campanha: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_redes_sociais: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_retorno: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_resgate: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_indicacao: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_site: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_parceiros: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_externos: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    clientes_todos: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    # Cancelados (demandas, não atendimentos), Ações Fechadas e Aproveitamento.
    demandas_canceladas: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    acoes_fechadas: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    rubricas_reunidas_fechadas: int = 0
    taxa_aproveitamento: ComercialLexpreRatioStat = ComercialLexpreRatioStat()
    # Seção 02 · Performance — leads (DATA_ENTRADA), ranking e atividade diária.
    leads_geral: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    leads_campanha: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    taxa_leads_geral: ComercialLexpreRatioStat = ComercialLexpreRatioStat()
    taxa_leads_campanha: ComercialLexpreRatioStat = ComercialLexpreRatioStat()
    ranking_acoes_fechadas_por_atendente: List[ChartDataPoint] = []
    acoes_fechadas_hoje_por_atendente: List[ChartDataPoint] = []
    contratos_fechados_hoje_por_atendente: List[ChartDataPoint] = []
    # Seção 03 · Protocolos e valor de causa (banco lexpre — app.analyses.NG.protocolo_lexpre).
    protocolados: ComercialLexpreCanalStat = ComercialLexpreCanalStat()
    valor_causa_protocolado: ComercialLexpreRatioStat = ComercialLexpreRatioStat()
    ticket_medio_protocolado: ComercialLexpreRatioStat = ComercialLexpreRatioStat()
    tempo_medio_ate_protocolo_horas: float = 0.0
    fila_pre_protocolo_por_atendente: List[ComercialLexpreFilaPreProtocoloItem] = []
    valor_causa_por_atendente: List[ComercialLexpreValorCausaPorAtendenteItem] = []
    # Seção 04 · Distribuição — ações fechadas por rubrica, por canal de origem
    # (chaves: "total" + os mesmos slugs de canal da Seção 02, minúsculos).
    acoes_fechadas_por_rubrica: Dict[str, List[ChartDataPoint]] = {}
    # Seção 05 · Acompanhamento por Atendente — uma linha por atendente + linha "Total"
    # (chaves dinâmicas: atendente, leads_geral, clientes_geral, taxa_geral, e
    # leads_<slug>/clientes_<slug>/taxa_<slug> por canal — ver get_tabela_por_atendente).
    tabela_por_atendente: List[Dict[str, Any]] = []
    totais_tabela_por_atendente: Dict[str, Any] = {}
    # Card "Meta por Atendente" (dentro da Seção 05) — valor de causa protocolado no
    # período de `from`/`to`, por atendente. O front chama o endpoint uma 2ª vez com
    # o período do trimestre/semestre selecionado (independente do filtro de data
    # principal da página) e usa só este campo dessa 2ª resposta.
    valor_causa_protocolado_por_atendente_periodo: Dict[str, float] = {}
    # Seção 02 · Comissão (dashboard Comissão Comercial LexPre) — cálculo e
    # multiplicadores, mesma lógica do dashboard Comissão Comercial legado
    # (app.analyses.NG.comissao_lexpre), usando VALOR_AM (rubricas.valor_rubrica,
    # adicionado em 04/09/2026) já presente na query `comercial_lexpre_NG`.
    comissao_base: float = 0.0
    fator_multiplicador: float = 0.0
    comissao_com_fm: float = 0.0
    # Desconto por cancelamento tardio (04/09/2026, ver comissao_lexpre.py) — demandas
    # cuja comissão já foi contabilizada em um período anterior mas que só foram
    # canceladas dentro do período atual (`public.audit_log`). Vazio (0) sem `from`/`to`
    # definidos. `comissao_com_fm_liquida` = `comissao_com_fm` - `desconto_cancelamentos`
    # (desconto de valor cheio, aplicado depois do FM) — é o valor que efetivamente
    # deve ser distribuído nos proporcionais AM/PA e PB.
    desconto_cancelamentos: float = 0.0
    comissao_com_fm_liquida: float = 0.0
    proporcional_am_pa: float = 0.0
    proporcional_pb: float = 0.0
    # Tabela "Valor das Rubricas" (ações fechadas + VALOR_AM unitário + total, por
    # rubrica) — mesmas chaves de `acoes_fechadas_por_rubrica` ("total" + slugs de
    # canal); itens: {"rubrica": str, "acoes": int, "valor_am": float, "total": float}.
    rubricas_total_tabela: Dict[str, List[Dict[str, Any]]] = {}
    # Base do botão "Gerar comissão (PDF)" — réplica do PDF legado (uma linha por
    # atendente), com a coluna extra `desconto_cancelamentos` (ver comissao_lexpre.py).
    comissionamento_por_atendente: List[ComercialLexpreComissionamentoAtendenteRow] = []

# v1: dashboard_routes.py:14986
class ComercialLexpreNGResponse(BaseModel):
    stats: ComercialLexpreNGStats
