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
