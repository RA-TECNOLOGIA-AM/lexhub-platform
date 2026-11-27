"""Análises de Perfil de Clientes / Marketing — banco lexpre (escritórios NGAM e LAAM).

Fonte: perfil_clientes_lexpre (atendimentos assinados: status_id = 6 com data_assinatura).
A query não filtra escritório — ela é compartilhada com o outro escritório.
Cada análise daqui restringe as linhas ao escritório do dashboard (NGAM=1 ou LAAM=2) antes de contar.

Espelha as métricas de marketing_ng.py que leem perfil_clientes_NG. Todas as
métricas usam o total de linhas dessa coorte (COUNTROWS), sem deduplicação por cliente.

Colunas equivalentes à query antiga (banco ng):

    DATA_NASCIMENTO      -> NASCIMENTO
    CANAL_AQUISICAO      -> CANAL_AQUISICAO
    GENERO               -> GENERO
    TIPO_TRAFEGO         -> TIPO_TRAFEGO
    PROPECCAO            -> PROSPECCAO
    OCUPACAO             -> PS_OCUPACAO            (pesquisa socioeconômica)
    MEDIA_MENSAL         -> PS_MEDIA_GANHO_MENSAL
    TIPO_RESIDENCIA      -> PS_RESIDENCIA
    PESSOAS_DEPENDENTES  -> PS_TOTAL_DEPENDENTES
    RESP_TRIAGEM?        -> qualquer campo PS_* preenchido

DISPOSITIVO não existe em perfil_clientes_lexpre, então não há gráfico de dispositivo.
"""
import unicodedata
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.utils import parse_date_from_db
from app.analyses.NG.marketing_ng import _categoria_criativo, _posicionamento_padronizado
from app.analyses.NG.comercial_lexpre import (
    _canal_aquisicao_bate,
    _expandir_ids_para_contagem,
    _is_assinado,
    filter_comercial_lexpre_por_escritorio,
    get_acoes_fechadas,
    get_acoes_fechadas_por_rubrica,
    get_clientes_por_canal,
    get_clientes_todos,
    get_leads_campanha_periodo,
    get_taxa_leads_campanha,
)
from app.analyses.NG.protocolo_lexpre import _demanda_valida
from app.analyses.NG.protocolo_lexpre import _valor_causa_protocolado as _valor_causa_protocolado_demanda
from app.analyses.NG.protocolo_setor_lexpre import (
    SETOR_PROTOCOLO_IDS,
    _filter_saidas_by_date_range,
    _filtrar_protocolados_reais,
    _normalizar_materia,
    _saidas_setor,
    filter_protocolo_lexpre_por_escritorio,
    get_protocolados_total,
    get_ticket_medio_protocolado,
    get_valor_causa_protocolado,
)


# public.escritorio (lexpre): 1 = NGAM, 2 = LAAM. As queries não filtram escritório;
# o recorte é feito aqui, nas funções de entrada (parâmetro `escritorio_id`), e os
# helpers internos recebem as linhas já recortadas. As chaves de resposta mantêm o
# prefixo `marketing_lexpre_ng_` nos dois escritórios (mesmo payload, igual às
# outras réplicas LA do lexpre).
ESCRITORIO_NGAM = 1
ESCRITORIO_LAAM = 2

# Campos do JSONB pesquisa_socioeconomica.respostas. Preenchido = respondeu a triagem.
_CAMPOS_PESQUISA = (
    "PS_RESIDENCIA",
    "PS_OCUPACAO",
    "PS_ESCOLARIDADE",
    "PS_PRIMEIRO_NOME",
    "PS_UNICO_PROVEDOR",
    "PS_MEDIA_GANHO_MENSAL",
    "PS_CARTEIRA_ASSINADA",
    "PS_TOTAL_DEPENDENTES",
)


def _escritorio_id(row: Dict[str, Any]) -> Optional[int]:
    raw = row.get("escritorio_id")
    if raw is None:
        raw = row.get("ESCRITORIO_ID")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _somente_escritorio(rows: List[Dict[str, Any]], escritorio_id: int) -> List[Dict[str, Any]]:
    """Mantém só o escritório informado. As queries trazem todos de propósito."""
    return [r for r in rows if _escritorio_id(r) == escritorio_id]


def _calc_idade(nascimento: Any) -> Optional[int]:
    d = parse_date_from_db(nascimento)
    if not d:
        return None
    hoje = date.today()
    idade = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
    return idade if 0 <= idade <= 120 else None


def _faixa_etaria(idade: int) -> str:
    if idade < 18:
        return "< 18"
    if idade <= 24:
        return "18-24"
    if idade <= 34:
        return "25-34"
    if idade <= 44:
        return "35-44"
    return "45+"


def _contagem(
    rows: List[Dict[str, Any]],
    campo: str,
    *,
    incluir_vazios: bool = False,
    rotulo_vazio: str = "Não informado",
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rows:
        val = r.get(campo)
        nome = str(val).strip() if val is not None else ""
        if not nome:
            if not incluir_vazios:
                continue
            nome = rotulo_vazio
        counts[nome] = counts.get(nome, 0) + 1
    return counts


def _to_chart(counts: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"name": k, "value": v}
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


def _canal_aquisicao(row: Dict[str, Any]) -> str:
    v = row.get("CANAL_AQUISICAO") or row.get("canal_aquisicao")
    return str(v or "").strip().upper()


def _respondeu_pesquisa(row: Dict[str, Any]) -> bool:
    """Triagem respondida: a pesquisa socioeconômica tem ao menos um campo preenchido.

    No banco ng isso era o booleano RESP_TRIAGEM? (customers.respondeu_form_socio).
    No lexpre a pesquisa é o JSONB pesquisa_socioeconomica.respostas; o LEFT JOIN
    deixa todos os PS_* nulos quando o atendimento não tem pesquisa.
    """
    for campo in _CAMPOS_PESQUISA:
        val = row.get(campo)
        if val is not None and str(val).strip():
            return True
    return False


# ─── Métricas escalares ───────────────────────────────────────────────────────

def get_total_clientes(rows: List[Dict[str, Any]]) -> int:
    """TOTAL_CLIENTES = COUNTROWS dos atendimentos (já recortados por `apply_selection_filters`)."""
    return len(rows)


def get_media_idade(rows: List[Dict[str, Any]]) -> float:
    idades = [
        i for i in (_calc_idade(r.get("NASCIMENTO")) for r in rows)
        if i is not None
    ]
    return round(sum(idades) / len(idades), 2) if idades else 0.0


def get_marketing_lexpre_ng_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "marketing_lexpre_ng_total_clientes": get_total_clientes(rows),
        "marketing_lexpre_ng_media_idade": get_media_idade(rows),
    }


def filtrar_triados(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """TRIADOS = atendimentos com pesquisa socioeconômica respondida."""
    return [r for r in rows if _respondeu_pesquisa(r)]


# ─── Agrupamentos / gráficos ──────────────────────────────────────────────────

def group_faixa_etaria(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        idade = _calc_idade(r.get("NASCIMENTO"))
        if idade is None:
            continue
        faixa = _faixa_etaria(idade)
        counts[faixa] = counts.get(faixa, 0) + 1
    return _to_chart(counts)


def group_genero(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "GENERO"))


def group_origem(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Canal de aquisição do atendimento (gráfico de Origem)."""
    return _to_chart(_contagem(rows, "CANAL_AQUISICAO"))


def group_ocupacao(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "PS_OCUPACAO"))


def group_tipo_trafego(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "TIPO_TRAFEGO"))


def group_prospeccao(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "PROSPECCAO"))


def group_faixa_salarial(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Distribuição por faixa de média salarial mensal (pesquisa socioeconômica).

    PS_MEDIA_GANHO_MENSAL é resposta categórica do formulário, não um valor
    numérico livre. Sem resposta entra em "Não informado" para bater com
    TOTAL_CLIENTES = COUNTROWS.
    """
    return _to_chart(_contagem(rows, "PS_MEDIA_GANHO_MENSAL", incluir_vazios=True))


def group_tipo_residencia(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "PS_RESIDENCIA", incluir_vazios=True))


def group_pessoas_dependentes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """PS_TOTAL_DEPENDENTES é resposta categórica do formulário (ex.: "2 pessoas")."""
    return _to_chart(_contagem(rows, "PS_TOTAL_DEPENDENTES", incluir_vazios=True))


# ─── Filtros interativos (drill-down por clique nos gráficos) ────────────────

def _extrair_faixa_etaria(row: Dict[str, Any]) -> Optional[str]:
    idade = _calc_idade(row.get("NASCIMENTO"))
    return _faixa_etaria(idade) if idade is not None else None


_FIELD_MAP_CLIENTES: Dict[str, Callable[[Dict[str, Any]], Optional[str]]] = {
    "faixa_etaria": _extrair_faixa_etaria,
    "canal_aquisicao": _canal_aquisicao,
    "genero": lambda r: r.get("GENERO"),
    "tipo_trafego": lambda r: r.get("TIPO_TRAFEGO"),
    "ocupacao": lambda r: r.get("PS_OCUPACAO"),
    "prospeccao": lambda r: r.get("PROSPECCAO"),
    "tipo_residencia": lambda r: r.get("PS_RESIDENCIA"),
    "pessoas_dependentes": lambda r: r.get("PS_TOTAL_DEPENDENTES"),
}


def apply_selection_filters(
    rows: List[Dict[str, Any]],
    filters: List[Tuple[str, str]],
    field_map: Dict[str, Callable[[Dict[str, Any]], Optional[str]]],
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Filtra `rows` pelos pares (dimensão, valor) do drill-down interativo.

    Múltiplos valores na MESMA dimensão = OR; dimensões DIFERENTES = AND.
    Uma dimensão sem entrada em `field_map` é ignorada.
    O recorte de escritório vale mesmo sem drill-down.
    """
    rows = _somente_escritorio(rows, escritorio_id)
    if not filters:
        return rows
    by_dim: Dict[str, Set[str]] = {}
    for dim, value in filters:
        by_dim.setdefault(str(dim), set()).add(str(value).strip().upper())
    result = rows
    for dim, values in by_dim.items():
        extractor = field_map.get(dim)
        if extractor is None:
            continue
        result = [r for r in result if str(extractor(r) or "").strip().upper() in values]
    return result


# ─── Facebook Ads × comercial lexpre (CAC, ROAS, leads, indicação, retorno) ──
# Cliques, pageview, leads de anúncio e valor gasto vêm da query facebook_ads
# (banco ng, metrics_ads.facebook_ads) — a mesma do marketing_NG.
# O denominador do CAC, o valor de causa do ROAS, clientes de campanha, leads,
# indicação e retorno vêm de comercial_lexpre_NG, restritos ao escritório.
# O join atendimento×demandas repete o atendimento; contagens usam ID_ACTION distinto.

def _sem_acento(valor: Any) -> str:
    texto = str(valor or "").strip().upper()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


def _canal_comercial(row: Dict[str, Any]) -> str:
    return _sem_acento(row.get("CANAL_AQUISICAO") or row.get("canal_aquisicao"))


def _prospeccao_comercial(row: Dict[str, Any]) -> str:
    return _sem_acento(row.get("PROSPECCAO") or row.get("PROPECCAO") or row.get("prospeccao"))


def _e_campanha(row: Dict[str, Any]) -> bool:
    """Campanha no lexpre é canal_aquisicao = anúncio (também aceita ANUNCIO_NG)."""
    return _canal_comercial(row) in {"ANUNCIO", "ANUNCIO_NG"}


def _e_indicacao(row: Dict[str, Any]) -> bool:
    return _canal_comercial(row).startswith("INDICA")


def _e_retorno(row: Dict[str, Any]) -> bool:
    return _canal_comercial(row) == "RETORNO"


def _assinado(row: Dict[str, Any]) -> bool:
    """Cliente assinado: status_id = 6 com data_assinatura — mesma regra do Comercial LexPre.

    motivo_id = 4 não serve: só é preenchido quando o atendimento é encerrado depois
    da assinatura (29/09/2026: 158 de 172 assinados NGAM estavam com motivo_id nulo).
    """
    return _is_assinado(row)


def _como_data(valor: Any) -> Optional[date]:
    bruto = parse_date_from_db(valor)
    if isinstance(bruto, datetime):
        return bruto.date()
    if isinstance(bruto, date):
        return bruto
    return None


def _no_periodo(
    row: Dict[str, Any],
    coluna: str,
    from_date: Optional[date],
    to_date: Optional[date],
    *,
    exigir_data: bool,
) -> bool:
    dia = _como_data(row.get(coluna))
    if dia is None:
        return not exigir_data and not from_date and not to_date
    if not from_date and not to_date:
        return True
    if from_date and to_date:
        return from_date <= dia <= to_date
    if from_date:
        return dia >= from_date
    return dia <= to_date


def _ids_distintos(
    rows: List[Dict[str, Any]],
    predicado: Callable[[Dict[str, Any]], bool],
) -> Set[Any]:
    ids: Set[Any] = set()
    for row in rows:
        if not predicado(row):
            continue
        id_action = row.get("ID_ACTION")
        if id_action is not None:
            ids.add(id_action)
    return ids


def _parse_numero(valor_raw: Any) -> Optional[float]:
    """Converte número/Decimal ou string pt-BR/en-US (ex.: "1.500,00") para float."""
    if valor_raw is None:
        return None
    if isinstance(valor_raw, (int, float)):
        return float(valor_raw)
    valor_str = str(valor_raw).strip().replace("R$", "").replace(" ", "").replace(" ", "")
    if not valor_str:
        return None
    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str:
        valor_str = valor_str.replace(",", ".")
    try:
        return float(valor_str)
    except (ValueError, TypeError):
        return None


def _sum_int(rows: List[Dict[str, Any]], campo: str) -> int:
    total = 0
    for row in rows:
        val = _parse_numero(row.get(campo))
        if val is None:
            continue
        total += int(round(val))
    return total


def _sum_float(rows: List[Dict[str, Any]], campo: str) -> float:
    total = 0.0
    for row in rows:
        val = _parse_numero(row.get(campo))
        if val is None:
            continue
        total += val
    return total


def _divide(numerador: float, denominador: float) -> float:
    return numerador / denominador if denominador else 0.0


def get_facebook_ads_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Cliques, pageview e leads somados de metrics_ads.facebook_ads."""
    return {
        "marketing_lexpre_ng_facebook_cliques": _sum_int(rows, "cliques_no_link"),
        "marketing_lexpre_ng_facebook_pageview": _sum_int(rows, "landing_page_view"),
        "marketing_lexpre_ng_facebook_leads": _sum_int(rows, "leads"),
    }


def group_investimento_cliques_leads(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Investimento (valor_gasto), cliques e leads por dia (facebook_ads.date)."""
    por_dia: Dict[Any, Dict[str, float]] = {}
    for row in rows:
        dia = _como_data(row.get("date"))
        if dia is None:
            continue
        bucket = por_dia.setdefault(dia, {"investimento": 0.0, "cliques": 0.0, "leads": 0.0})
        investimento = _parse_numero(row.get("valor_gasto"))
        if investimento is not None:
            bucket["investimento"] += investimento
        cliques = _parse_numero(row.get("cliques_no_link"))
        if cliques is not None:
            bucket["cliques"] += cliques
        leads = _parse_numero(row.get("leads"))
        if leads is not None:
            bucket["leads"] += leads

    return [
        {
            "name": dia.strftime("%d/%m"),
            "investimento": round(bucket["investimento"], 2),
            "cliques": int(round(bucket["cliques"])),
            "leads": int(round(bucket["leads"])),
        }
        for dia, bucket in sorted(por_dia.items())
    ]


def get_clientes_campanha(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Atendimentos assinados de campanha, pela DATA_ASSINATURA no período."""
    return len(_ids_distintos(
        rows,
        lambda row: (
            _assinado(row)
            and _e_campanha(row)
            and _no_periodo(row, "DATA_ASSINATURA", from_date, to_date, exigir_data=True)
        ),
    ))


def get_leads(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Leads distintos (atendimentos) com DATA_ENTRADA no período."""
    return len(_ids_distintos(
        rows,
        lambda row: _no_periodo(row, "DATA_ENTRADA", from_date, to_date, exigir_data=False),
    ))


def _leads_canal_prospeccao(
    rows: List[Dict[str, Any]],
    canal_ok: Callable[[Dict[str, Any]], bool],
    prospeccao: str,
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    alvo = _sem_acento(prospeccao)
    return len(_ids_distintos(
        rows,
        lambda row: (
            canal_ok(row)
            and _prospeccao_comercial(row) == alvo
            and _no_periodo(row, "DATA_ENTRADA", from_date, to_date, exigir_data=False)
        ),
    ))


def get_indicacao_ativa(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    return _leads_canal_prospeccao(rows, _e_indicacao, "ATIVA", from_date, to_date)


def get_indicacao_passiva(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    return _leads_canal_prospeccao(rows, _e_indicacao, "PASSIVA", from_date, to_date)


def get_retorno_ativa(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    return _leads_canal_prospeccao(rows, _e_retorno, "ATIVA", from_date, to_date)


def get_retorno_passiva(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    return _leads_canal_prospeccao(rows, _e_retorno, "PASSIVA", from_date, to_date)


def _ids_assinados_canal_por_entrada(
    rows: List[Dict[str, Any]],
    canal_ok: Callable[[Dict[str, Any]], bool],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Set[Any]:
    """Assinados do canal com DATA_ENTRADA no período — coorte do CAC/ROAS de campanha."""
    return _ids_distintos(
        rows,
        lambda row: (
            _assinado(row)
            and canal_ok(row)
            and _no_periodo(row, "DATA_ENTRADA", from_date, to_date, exigir_data=False)
        ),
    )


def _valor_causa_protocolado(
    rows: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    ids_permitidos: Optional[Set[Any]] = None,
) -> float:
    """Soma o valor de causa (ANP -> DANO_MORAL) das demandas com DATA_PROTOCOLO no período.

    Deduplica por ID_DEMANDA. Se `ids_permitidos` vier preenchido, só entram
    demandas cujo atendimento está nesse conjunto (cruzamento do ROAS de campanha).
    """
    vistos: Set[Any] = set()
    total = 0.0
    for row in rows:
        if not _no_periodo(row, "DATA_PROTOCOLO", from_date, to_date, exigir_data=True):
            continue
        if ids_permitidos is not None and row.get("ID_ACTION") not in ids_permitidos:
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in vistos:
            continue
        vistos.add(id_demanda)
        valor = _valor_causa_protocolado_demanda(row)
        if valor > 0:
            total += valor
    return total


def get_marketing_lexpre_ng_aquisicao_stats(
    comercial_rows: List[Dict[str, Any]],
    facebook_ads_rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    escritorio_id: int = ESCRITORIO_NGAM,
) -> Dict[str, Any]:
    """CAC/ROAS cruzam valor gasto do Facebook com clientes e valor de causa do lexpre.

    CAC campanha = valor gasto / assinados de campanha que entraram no período.
    CAC geral = valor gasto / (campanha + indicação), mesma coorte de entrada.
    ROAS campanha = valor de causa protocolado desses clientes de campanha / valor gasto.
    ROAS geral = valor de causa protocolado de todo o escritório no período / valor gasto.
    `facebook_ads_rows` já vem recortado pela conta/campanhas do escritório (rota).
    """
    comercial_rows = _somente_escritorio(comercial_rows, escritorio_id)
    valor_gasto = _sum_float(facebook_ads_rows, "valor_gasto")
    ids_campanha = _ids_assinados_canal_por_entrada(comercial_rows, _e_campanha, from_date, to_date)
    ids_indicacao = _ids_assinados_canal_por_entrada(comercial_rows, _e_indicacao, from_date, to_date)
    valor_causa_campanha = _valor_causa_protocolado(comercial_rows, from_date, to_date, ids_campanha)
    valor_causa_geral = _valor_causa_protocolado(comercial_rows, from_date, to_date)

    return {
        "marketing_lexpre_ng_facebook_valor_gasto": valor_gasto,
        "marketing_lexpre_ng_facebook_cac_campanha": _divide(valor_gasto, len(ids_campanha)),
        "marketing_lexpre_ng_facebook_cac_geral": _divide(valor_gasto, len(ids_campanha) + len(ids_indicacao)),
        "marketing_lexpre_ng_facebook_roas_campanha": _divide(valor_causa_campanha, valor_gasto),
        "marketing_lexpre_ng_facebook_roas_geral": _divide(valor_causa_geral, valor_gasto),
        "marketing_lexpre_ng_clientes_campanha": get_clientes_campanha(comercial_rows, from_date, to_date),
        "marketing_lexpre_ng_leads": get_leads(comercial_rows, from_date, to_date),
        "marketing_lexpre_ng_indicacao_ativa": get_indicacao_ativa(comercial_rows, from_date, to_date),
        "marketing_lexpre_ng_indicacao_passiva": get_indicacao_passiva(comercial_rows, from_date, to_date),
        "marketing_lexpre_ng_retorno_ativa": get_retorno_ativa(comercial_rows, from_date, to_date),
        "marketing_lexpre_ng_retorno_passiva": get_retorno_passiva(comercial_rows, from_date, to_date),
    }


# ─── Fechamento Campanhas (Seção 04) ─────────────────────────────────────────
# Diferente do marketing_NG (RA x NG), no lexpre a campanha é um canal único
# (canal_aquisicao = "anúncio" — a Campanha RA foi descontinuada), então a seção
# compara Campanha x Total. As regras são as mesmas dos dashboards lexpre que já
# mostram esses números, para os valores baterem entre páginas:
#   - Clientes / conversão / ações por rubrica: Comercial LexPre (DATA_ASSINATURA,
#     assinado = status_id 6; leads da conversão por DATA_ENTRADA).
#   - Protocolados / valor de causa / ticket médio: dashboard Protocolo LexPre
#     (protocolo_setor_lexpre.py — log de setor: última saída do Protocolo com
#     status "Aguardando Despacho Inicial", pela data da saída; 1 por demanda).
#     O canal vem do comercial, cruzando por ID_DEMANDA.
#     Não usar protocolo_lexpre.py (DATA_PROTOCOLO) aqui: ele expande rubricas
#     reunidas por componente e conta demanda devolvida ao Protocolo — em set/2026
#     dava 497 protocolados contra 270 do dashboard Protocolo (29/09/2026).
# Ticket médio = valor de causa protocolado ÷ protocolados (regra do lexpre), não
# ÷ ações fechadas como no marketing_NG.

def _somente_campanha_comercial(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if _canal_aquisicao_bate(r, "CAMPANHA")]


def _saidas_protocoladas_periodo(
    log_rows: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    escritorio_id: int,
) -> List[Dict[str, Any]]:
    """Saídas protocoladas do escritório no período — mesmo recorte do dashboard Protocolo LexPre."""
    rows = filter_protocolo_lexpre_por_escritorio(log_rows, escritorio_id=escritorio_id)
    saidas = _filtrar_protocolados_reais(_saidas_setor(rows, SETOR_PROTOCOLO_IDS))
    if not from_date and not to_date:
        return saidas
    return _filter_saidas_by_date_range(saidas, from_date or date.min, to_date or date.max)


def _group_protocolados_por_rubrica(saidas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Protocolados por rubrica (MATERIA do log) — soma bate com o card Protocolados."""
    contagem: Dict[str, int] = {}
    for row in saidas:
        nome = _normalizar_materia(row.get("MATERIA"))
        contagem[nome] = contagem.get(nome, 0) + 1
    itens = [{"name": nome, "value": valor} for nome, valor in contagem.items()]
    itens.sort(key=lambda x: x["value"], reverse=True)
    return itens


def _escritorio_por_rubrica(
    comercial_rows: List[Dict[str, Any]],
    rubrica: Optional[List[str]],
    mapa_reunidas: Optional[Dict[Any, List[str]]],
    escritorio_id: int,
) -> List[Dict[str, Any]]:
    """Linhas do comercial do escritório, recortadas pelo drill-down de rubrica (OR).

    Os gráficos de clientes mostram os componentes de rubrica reunida e o de
    protocolados mostra o pacote (MATERIA do log) — o clique casa com os dois.
    """
    rows = filter_comercial_lexpre_por_escritorio(comercial_rows, escritorio_id=escritorio_id)
    if not rubrica:
        return rows
    alvos = {str(v).strip().upper() for v in rubrica}

    def _tem_rubrica(row: Dict[str, Any]) -> bool:
        nomes = {str(row.get("RUBRICA") or "").strip().upper()}
        nomes.update(n.strip().upper() for _id, n in _expandir_ids_para_contagem(row, mapa_reunidas))
        return bool(nomes & alvos)

    return [r for r in rows if _tem_rubrica(r)]


def get_fechamento_campanhas(
    comercial_rows: List[Dict[str, Any]],
    log_setor_rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[Any, List[str]]] = None,
    rubrica: Optional[List[str]] = None,
    escritorio_id: int = ESCRITORIO_NGAM,
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """Stats e gráficos da Seção 04. `rubrica` = drill-down do gráfico de rubrica (OR)."""
    rows = _escritorio_por_rubrica(comercial_rows, rubrica, mapa_reunidas, escritorio_id)
    ids_demandas = {r.get("ID_DEMANDA") for r in rows if r.get("ID_DEMANDA") is not None}
    ids_campanha = {
        r.get("ID_DEMANDA") for r in _somente_campanha_comercial(rows) if r.get("ID_DEMANDA") is not None
    }
    saidas = [
        s for s in _saidas_protocoladas_periodo(log_setor_rows, from_date, to_date, escritorio_id)
        if s.get("ID_DEMANDA") in ids_demandas
    ]
    saidas_campanha = [s for s in saidas if s.get("ID_DEMANDA") in ids_campanha]

    clientes_campanha = get_clientes_por_canal(rows, "CAMPANHA", from_date, to_date)
    # Ações = demandas não canceladas de clientes de campanha (regra do Comercial LexPre,
    # reunidas contam por componente) — usadas no % Aproveitamento da Seção 06.
    acoes_campanha = get_acoes_fechadas(
        _somente_campanha_comercial(rows), from_date, to_date, mapa_reunidas
    )
    protocolados_campanha = get_protocolados_total(saidas_campanha)
    valor_causa_campanha = get_valor_causa_protocolado(saidas_campanha)

    stats = {
        "marketing_lexpre_ng_campanha": clientes_campanha,
        "marketing_lexpre_ng_conversao_campanha": get_taxa_leads_campanha(rows, from_date, to_date),
        "marketing_lexpre_ng_protocolados_campanha": protocolados_campanha,
        "marketing_lexpre_ng_valor_causa_campanha": valor_causa_campanha,
        "marketing_lexpre_ng_ticket_medio_campanha": get_ticket_medio_protocolado(saidas_campanha),
        "marketing_lexpre_ng_leads_campanha": get_leads_campanha_periodo(rows, from_date, to_date),
        "marketing_lexpre_ng_acoes_campanha": acoes_campanha,
        "marketing_lexpre_ng_aproveitamento_campanha": (
            round(acoes_campanha / clientes_campanha, 2) if clientes_campanha else 0.0
        ),
    }
    charts = {
        "marketing_lexpre_ng_total_clientes_campanha": [
            {"name": "Campanha", "value": clientes_campanha},
            {"name": "Total", "value": get_clientes_todos(rows, from_date, to_date)},
        ],
        "marketing_lexpre_ng_protocolo_resolvido_total": [
            {"name": "Campanha", "value": protocolados_campanha},
            {"name": "Total", "value": get_protocolados_total(saidas)},
        ],
        "marketing_lexpre_ng_valor_causa_total": [
            {"name": "Campanha", "value": valor_causa_campanha},
            {"name": "Total", "value": get_valor_causa_protocolado(saidas)},
        ],
        "marketing_lexpre_ng_rubrica_campanha": get_acoes_fechadas_por_rubrica(
            rows, "CAMPANHA", from_date, to_date, mapa_reunidas
        ),
        "marketing_lexpre_ng_rubrica_protocolado": _group_protocolados_por_rubrica(saidas_campanha),
    }
    return stats, charts


# ─── Análise de Aquisição (Seção 05) ─────────────────────────────────────────
# No lexpre não há tabela de trackeamento: os campos de rastreio do anúncio
# (posicionamento, campanha, conjunto, criativo) ficam no próprio atendimento.
# Trackeamento = atendimentos do escritório com DATA_ENTRADA no período (equivalente à
# DATA_TRACKEAMENTO do legado); Fechamento = os desses que assinaram
# (status_id 6 + data_assinatura) — mesma coorte de entrada, como no marketing_NG.
# Categoria (Stories/Reels/Feed) e posicionamento usam a padronização do legado.

_FIELD_MAP_AQUISICAO: Dict[str, Callable[[Dict[str, Any]], Optional[str]]] = {
    "categoria": _categoria_criativo,
    "posicionamento": _posicionamento_padronizado,
    "campanha": lambda r: r.get("NOME_CAMPANHA"),
    "conjunto": lambda r: r.get("NOME_CONJUNTO"),
    "criativo": lambda r: r.get("CRIATIVO"),
    "canal_aquisicao": _canal_aquisicao,
}


def _atendimentos_por_entrada(
    comercial_rows: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    escritorio_id: int,
) -> List[Dict[str, Any]]:
    """Uma linha por atendimento do escritório (o join com demandas repete o atendimento)."""
    vistos: Set[Any] = set()
    saida: List[Dict[str, Any]] = []
    for row in _somente_escritorio(comercial_rows, escritorio_id):
        id_action = row.get("ID_ACTION")
        if id_action is None or id_action in vistos:
            continue
        if not _no_periodo(row, "DATA_ENTRADA", from_date, to_date, exigir_data=True):
            continue
        vistos.add(id_action)
        saida.append(row)
    return saida


def _group_por(
    rows: List[Dict[str, Any]],
    extrator: Callable[[Dict[str, Any]], Optional[str]],
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for row in rows:
        chave = str(extrator(row) or "").strip() or "(Em branco)"
        counts[chave] = counts.get(chave, 0) + 1
    itens = _to_chart(counts)
    return itens[:top_n] if top_n else itens


def get_analise_aquisicao(
    comercial_rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    selection_pairs: Optional[List[Tuple[str, str]]] = None,
    escritorio_id: int = ESCRITORIO_NGAM,
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """Stats e gráficos da Seção 05. `selection_pairs` = drill-down da página (só as dims da seção valem)."""
    trackeamento = apply_selection_filters(
        _atendimentos_por_entrada(comercial_rows, from_date, to_date, escritorio_id),
        selection_pairs or [],
        _FIELD_MAP_AQUISICAO,
        escritorio_id,
    )
    fechados = [r for r in trackeamento if _is_assinado(r)]

    stats = {
        "marketing_lexpre_ng_total_trackeamento": len(trackeamento),
        "marketing_lexpre_ng_processos_assinados": len(fechados),
    }
    charts: Dict[str, List[Dict[str, Any]]] = {}
    for prefixo, rows in (("trackeamento", trackeamento), ("fechamento", fechados)):
        charts[f"marketing_lexpre_ng_{prefixo}_categoria"] = _group_por(rows, _categoria_criativo)
        charts[f"marketing_lexpre_ng_{prefixo}_posicionamento"] = _group_por(rows, _posicionamento_padronizado)
        charts[f"marketing_lexpre_ng_{prefixo}_canal_aquisicao"] = _group_por(rows, _canal_aquisicao)
        charts[f"marketing_lexpre_ng_{prefixo}_campanha"] = _group_por(
            rows, lambda r: r.get("NOME_CAMPANHA"), top_n=10
        )

    # Ind. Performance de MKT (Seção 06): mesmo rastreio, só o canal campanha (anúncio).
    campanha = _somente_campanha_comercial(trackeamento)
    charts["marketing_lexpre_ng_ind_campanha"] = _group_por(campanha, lambda r: r.get("NOME_CAMPANHA"), top_n=10)
    charts["marketing_lexpre_ng_ind_posicionamento"] = _group_por(campanha, _posicionamento_padronizado)
    charts["marketing_lexpre_ng_ind_conjunto"] = _group_por(campanha, lambda r: r.get("NOME_CONJUNTO"), top_n=10)
    charts["marketing_lexpre_ng_ind_criativo"] = _group_por(campanha, lambda r: r.get("CRIATIVO"), top_n=10)
    charts["marketing_lexpre_ng_ind_categoria"] = _group_por(campanha, _categoria_criativo)
    return stats, charts


# ─── Ind. Orgânico de MKT (Seção 07) ─────────────────────────────────────────
# Mesmos 4 canais do marketing_NG (Facebook, Instagram, Site, Google) + o valor
# genérico "Orgânico", que é o único que existe no lexpre hoje (29/09/2026: 33
# leads NGAM, sem plataforma/campanha) — entra só no total, como o Comercial
# LexPre já faz ao contar "Orgânico" em Redes Sociais. Retorno e indicação têm
# tipo_trafego "Orgânico" mas não são canal orgânico (igual ao legado).
# Regras iguais às da Seção 04/06: leads por DATA_ENTRADA, contratos assinados
# por DATA_ASSINATURA, ações do Comercial LexPre, protocolado via log de setor.

CANAIS_ORGANICO: Tuple[str, ...] = ("FACEBOOK", "INSTAGRAM", "SITE", "GOOGLE")
_CANAL_ORGANICO_GENERICO = "ORGANICO"


def _e_organico(row: Dict[str, Any]) -> bool:
    canal = _canal_comercial(row)
    return canal in CANAIS_ORGANICO or canal == _CANAL_ORGANICO_GENERICO


def _ids_leads_por_entrada(
    rows: List[Dict[str, Any]],
    predicado: Callable[[Dict[str, Any]], bool],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Set[Any]:
    return _ids_distintos(
        rows,
        lambda r: predicado(r) and _no_periodo(r, "DATA_ENTRADA", from_date, to_date, exigir_data=True),
    )


def get_organico(
    comercial_rows: List[Dict[str, Any]],
    log_setor_rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[Any, List[str]]] = None,
    selection_pairs: Optional[List[Tuple[str, str]]] = None,
    escritorio_id: int = ESCRITORIO_NGAM,
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """Stats e gráficos da Seção 07."""
    pares = selection_pairs or []
    rows = _escritorio_por_rubrica(
        comercial_rows, [v for d, v in pares if d == "rubrica"], mapa_reunidas, escritorio_id
    )
    organico = [r for r in rows if _e_organico(r)]

    leads_canal = {
        canal: len(_ids_leads_por_entrada(organico, lambda r, c=canal: _canal_comercial(r) == c, from_date, to_date))
        for canal in CANAIS_ORGANICO
    }
    total_leads = len(_ids_leads_por_entrada(organico, lambda _r: True, from_date, to_date))
    contratos = len(_ids_distintos(
        organico,
        lambda r: _is_assinado(r) and _no_periodo(r, "DATA_ASSINATURA", from_date, to_date, exigir_data=True),
    ))
    acoes = get_acoes_fechadas(organico, from_date, to_date, mapa_reunidas)

    ids_organico = {r.get("ID_DEMANDA") for r in organico if r.get("ID_DEMANDA") is not None}
    saidas = [
        s for s in _saidas_protocoladas_periodo(log_setor_rows, from_date, to_date, escritorio_id)
        if s.get("ID_DEMANDA") in ids_organico
    ]

    stats: Dict[str, Any] = {
        f"marketing_lexpre_ng_org_leads_{canal.lower()}": leads_canal[canal] for canal in CANAIS_ORGANICO
    }
    stats.update({
        "marketing_lexpre_ng_org_total_leads": total_leads,
        "marketing_lexpre_ng_org_contratos": contratos,
        "marketing_lexpre_ng_org_acoes": acoes,
        "marketing_lexpre_ng_org_aproveitamento": round(acoes / contratos, 2) if contratos else 0.0,
        "marketing_lexpre_ng_org_taxa_fechamento": round(contratos / total_leads * 100, 2) if total_leads else 0.0,
        "marketing_lexpre_ng_org_valor_causa": get_valor_causa_protocolado(saidas),
        "marketing_lexpre_ng_org_ticket_medio": get_ticket_medio_protocolado(saidas),
    })

    # Rubricas (ações fechadas) — total e por canal, para o seletor do gráfico.
    charts: Dict[str, List[Dict[str, Any]]] = {
        "marketing_lexpre_ng_org_rubricas_total": get_acoes_fechadas_por_rubrica(
            organico, None, from_date, to_date, mapa_reunidas
        ),
    }
    for canal in CANAIS_ORGANICO:
        charts[f"marketing_lexpre_ng_org_rubricas_{canal.lower()}"] = get_acoes_fechadas_por_rubrica(
            [r for r in organico if _canal_comercial(r) == canal], None, from_date, to_date, mapa_reunidas
        )

    # Rastreio dos leads orgânicos (mesma base da Seção 05), com o drill-down da página.
    trackeamento = apply_selection_filters(
        [r for r in _atendimentos_por_entrada(comercial_rows, from_date, to_date, escritorio_id) if _e_organico(r)],
        pares,
        _FIELD_MAP_AQUISICAO,
        escritorio_id,
    )
    charts["marketing_lexpre_ng_org_campanha"] = _group_por(trackeamento, lambda r: r.get("NOME_CAMPANHA"), top_n=10)
    charts["marketing_lexpre_ng_org_posicionamento"] = _group_por(trackeamento, _posicionamento_padronizado)
    charts["marketing_lexpre_ng_org_conjunto"] = _group_por(trackeamento, lambda r: r.get("NOME_CONJUNTO"), top_n=10)
    charts["marketing_lexpre_ng_org_criativo"] = _group_por(trackeamento, lambda r: r.get("CRIATIVO"), top_n=10)
    charts["marketing_lexpre_ng_org_categoria"] = _group_por(trackeamento, _categoria_criativo)
    return stats, charts


# ─── Exportar relatório ──────────────────────────────────────────────────────
# Uma linha por lead (atendimento) do escritório com DATA_ENTRADA no período —
# mesma base das Seções 05 a 07. Os campos de perfil vêm de perfil_clientes_lexpre
# (só existe para assinados, mesma base das Seções 01/02). As demandas do lead são
# resumidas na linha; "protocolado" segue o dashboard Protocolo LexPre (log de
# setor, status 13), sem recorte de data — é o status atual da demanda.
# O drill-down ativo na página vale aqui também: perfil, rastreio e rubrica.

CAMPOS_EXPORT: Dict[str, str] = {
    "id_action": "ID do Atendimento",
    "cliente": "Nome do Cliente",
    "atendente": "Atendente",
    "uf": "UF",
    "data_entrada": "Data de Entrada",
    "status": "Status do Atendimento",
    "assinado": "Assinado",
    "data_assinatura": "Data de Assinatura",
    "canal_aquisicao": "Canal de Aquisição",
    "tipo_trafego": "Tipo de Tráfego",
    "prospeccao": "Prospecção",
    "campanha": "Campanha",
    "conjunto": "Conjunto",
    "criativo": "Criativo",
    "posicionamento": "Posicionamento (original)",
    "plataforma_anuncio": "Posicionamento",
    "categoria": "Categoria",
    "idade": "Idade",
    "faixa_etaria": "Faixa Etária",
    "genero": "Gênero",
    "ocupacao": "Ocupação",
    "media_salarial": "Média Salarial Mensal",
    "tipo_residencia": "Tipo de Residência",
    "pessoas_dependentes": "Pessoas Dependentes",
    "triado": "Respondeu a Triagem",
    "qtd_demandas": "Qtd. Demandas",
    "rubricas": "Rubricas",
    "qtd_protocolados": "Qtd. Protocolados",
    "valor_causa_protocolado": "Valor de Causa Protocolado (R$)",
}


def _perfil_por_atendimento(perfil_rows: List[Dict[str, Any]], escritorio_id: int) -> Dict[Any, Dict[str, Any]]:
    return {
        r.get("ATENDIMENTO"): r
        for r in _somente_escritorio(perfil_rows, escritorio_id)
        if r.get("ATENDIMENTO") is not None
    }


def get_linhas_export(
    comercial_rows: List[Dict[str, Any]],
    perfil_rows: List[Dict[str, Any]],
    log_setor_rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[Any, List[str]]] = None,
    selection_pairs: Optional[List[Tuple[str, str]]] = None,
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Linhas do relatório (dict por slug de `CAMPOS_EXPORT`), ordenadas por data de entrada."""
    pares = selection_pairs or []
    perfil = _perfil_por_atendimento(perfil_rows, escritorio_id)

    # Lead + campos de perfil na mesma linha, para o drill-down de perfil e de rastreio.
    leads = []
    for row in _atendimentos_por_entrada(comercial_rows, from_date, to_date, escritorio_id):
        p = perfil.get(row.get("ID_ACTION")) or {}
        leads.append({
            **row,
            "NASCIMENTO": p.get("NASCIMENTO"),
            "GENERO": p.get("GENERO"),
            **{campo: p.get(campo) for campo in _CAMPOS_PESQUISA},
            "_TEM_PERFIL": bool(p),
        })
    leads = apply_selection_filters(
        leads, [(d, v) for d, v in pares if d != "rubrica"], {**_FIELD_MAP_CLIENTES, **_FIELD_MAP_AQUISICAO}, escritorio_id
    )

    rubricas_filtro = [v for d, v in pares if d == "rubrica"]
    if rubricas_filtro:
        ids_com_rubrica = {
            r.get("ID_ACTION") for r in _escritorio_por_rubrica(comercial_rows, rubricas_filtro, mapa_reunidas, escritorio_id)
        }
        leads = [r for r in leads if r.get("ID_ACTION") in ids_com_rubrica]

    # Demandas por atendimento (não canceladas, de cliente assinado — regra do Protocolo
    # LexPre), com os componentes de rubrica reunida.
    ids_leads = {r.get("ID_ACTION") for r in leads}
    demandas: Dict[Any, Dict[Any, Dict[str, Any]]] = {}
    rubricas: Dict[Any, List[str]] = {}
    for row in _somente_escritorio(comercial_rows, escritorio_id):
        id_action, id_demanda = row.get("ID_ACTION"), row.get("ID_DEMANDA")
        if id_action not in ids_leads or id_demanda is None or not _demanda_valida(row):
            continue
        if id_demanda in demandas.setdefault(id_action, {}):
            continue
        demandas[id_action][id_demanda] = row
        nomes = rubricas.setdefault(id_action, [])
        for _sub_id, nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            if nome not in nomes:
                nomes.append(nome)

    # Protocolado = status atual da demanda no log do Protocolo (sem recorte de data).
    saidas_por_demanda = {
        s.get("ID_DEMANDA"): s for s in _saidas_protocoladas_periodo(log_setor_rows, None, None, escritorio_id)
    }

    linhas: List[Dict[str, Any]] = []
    for row in sorted(leads, key=lambda r: _como_data(r.get("DATA_ENTRADA")) or date.min):
        id_action = row.get("ID_ACTION")
        dem = demandas.get(id_action, {})
        saidas = [saidas_por_demanda[d] for d in dem if d in saidas_por_demanda]
        idade = _calc_idade(row.get("NASCIMENTO"))
        tem_perfil = row.get("_TEM_PERFIL")
        linhas.append({
            "id_action": id_action,
            "cliente": row.get("CLIENTE"),
            "atendente": row.get("ATENDENTE"),
            "uf": row.get("UF"),
            "data_entrada": _como_data(row.get("DATA_ENTRADA")),
            "status": row.get("STATUS"),
            "assinado": _is_assinado(row),
            "data_assinatura": _como_data(row.get("DATA_ASSINATURA")),
            "canal_aquisicao": row.get("CANAL_AQUISICAO"),
            "tipo_trafego": row.get("TIPO_TRAFEGO"),
            "prospeccao": row.get("PROSPECCAO"),
            "campanha": row.get("NOME_CAMPANHA"),
            "conjunto": row.get("NOME_CONJUNTO"),
            "criativo": row.get("CRIATIVO"),
            "posicionamento": row.get("POSICIONAMENTO"),
            "plataforma_anuncio": _posicionamento_padronizado(row),
            "categoria": _categoria_criativo(row),
            "idade": idade,
            "faixa_etaria": _faixa_etaria(idade) if idade is not None else None,
            "genero": row.get("GENERO"),
            "ocupacao": row.get("PS_OCUPACAO"),
            "media_salarial": row.get("PS_MEDIA_GANHO_MENSAL"),
            "tipo_residencia": row.get("PS_RESIDENCIA"),
            "pessoas_dependentes": row.get("PS_TOTAL_DEPENDENTES"),
            "triado": _respondeu_pesquisa(row) if tem_perfil else None,
            "qtd_demandas": len(dem),
            "rubricas": ", ".join(rubricas.get(id_action, [])),
            "qtd_protocolados": get_protocolados_total(saidas),
            "valor_causa_protocolado": get_valor_causa_protocolado(saidas),
        })
    return linhas


# ─── Exportar relatório: aba Facebook Ads ────────────────────────────────────
# Campos selecionáveis da query facebook_ads (metrics_ads.facebook_ads, diária).
# Os campos de DIMENSÃO escolhidos definem o detalhamento: o relatório agrupa
# pelas dimensões selecionadas e soma as MÉTRICAS em cada grupo (com Data, uma
# linha por dia; só Campanha, uma linha por campanha; nenhuma dimensão, só o total).
# Leads/assinados do lexpre cruzam pelo ad_id do atendimento (mesma coorte de
# entrada da aba de leads) — e pelo dia de entrada quando Data está selecionada —,
# o que dá CPL e CAC no mesmo detalhamento. `facebook_ads_rows` já vem recortado
# por período e escritório.

# slug -> (rótulo, coluna da query)
DIMENSOES_EXPORT_FACEBOOK: Dict[str, Tuple[str, str]] = {
    "data": ("Data", "date"),
    "conta": ("Conta", "nome_conta"),
    "id_conta": ("ID da Conta", "id_conta"),
    "campanha": ("Campanha", "campaign"),
    "campaign_id": ("ID da Campanha", "campaign_id"),
    "conjunto": ("Conjunto", "adset"),
    "adset_id": ("ID do Conjunto", "adset_id"),
    "anuncio": ("Anúncio", "ad"),
    "ad_id": ("ID do Anúncio", "ad_id"),
}

# slug -> (rótulo, coluna da query ou None p/ calculada)
METRICAS_EXPORT_FACEBOOK: Dict[str, Tuple[str, Optional[str]]] = {
    "primeiro_dia": ("Primeiro Dia", None),
    "ultimo_dia": ("Último Dia", None),
    "valor_gasto": ("Valor Gasto (R$)", "valor_gasto"),
    "alcance": ("Alcance (soma diária)", "alcance"),
    "impressoes": ("Impressões", "impressoes"),
    "cliques": ("Cliques no Link", "cliques_no_link"),
    "pageview": ("Pageview", "landing_page_view"),
    "leads_facebook": ("Leads (Facebook)", "leads"),
    "cadastros": ("Cadastros", "cadastros"),
    "leads_lexpre": ("Leads (LexPre)", None),
    "assinados_lexpre": ("Clientes Assinados (LexPre)", None),
    "cpl": ("CPL (R$)", None),
    "cac": ("CAC (R$)", None),
}

CAMPOS_EXPORT_FACEBOOK: Dict[str, str] = {
    **{slug: rotulo for slug, (rotulo, _col) in DIMENSOES_EXPORT_FACEBOOK.items()},
    **{slug: rotulo for slug, (rotulo, _col) in METRICAS_EXPORT_FACEBOOK.items()},
}

# Seleção padrão: o detalhamento por anúncio.
CAMPOS_EXPORT_FACEBOOK_PADRAO: List[str] = [
    "conta", "campanha", "conjunto", "anuncio", "ad_id", "primeiro_dia", "ultimo_dia",
    "valor_gasto", "impressoes", "cliques", "pageview", "leads_facebook",
    "leads_lexpre", "assinados_lexpre", "cpl", "cac",
]


def get_linhas_facebook_ads_export(
    facebook_ads_rows: List[Dict[str, Any]],
    comercial_rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    escritorio_id: int = ESCRITORIO_NGAM,
    campos: Optional[List[str]] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """(slugs na ordem de `CAMPOS_EXPORT_FACEBOOK`, linhas por slug) — com linha TOTAL se houver mais de um grupo."""
    escolhidos = set(campos or CAMPOS_EXPORT_FACEBOOK_PADRAO)
    slugs = [s for s in CAMPOS_EXPORT_FACEBOOK if s in escolhidos] or list(CAMPOS_EXPORT_FACEBOOK_PADRAO)
    dims = [s for s in slugs if s in DIMENSOES_EXPORT_FACEBOOK]
    por_dia = "data" in dims

    # Leads do lexpre por anúncio (e por dia de entrada, se Data estiver no detalhamento).
    leads_lexpre: Dict[Tuple[str, Optional[date]], int] = {}
    assinados_lexpre: Dict[Tuple[str, Optional[date]], int] = {}
    for row in _atendimentos_por_entrada(comercial_rows, from_date, to_date, escritorio_id):
        ad_id = str(row.get("AD_ID") or "").strip()
        if not ad_id:
            continue
        chave = (ad_id, _como_data(row.get("DATA_ENTRADA")) if por_dia else None)
        leads_lexpre[chave] = leads_lexpre.get(chave, 0) + 1
        if _is_assinado(row):
            assinados_lexpre[chave] = assinados_lexpre.get(chave, 0) + 1

    grupos: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for row in facebook_ads_rows:
        dia = _como_data(row.get("date"))
        valores_dim = {
            s: (dia if s == "data" else row.get(DIMENSOES_EXPORT_FACEBOOK[s][1]))
            for s in dims
        }
        g = grupos.setdefault(tuple(valores_dim[s] for s in dims), {
            **valores_dim,
            "primeiro_dia": dia,
            "ultimo_dia": dia,
            "_anuncios": set(),
            **{s: 0.0 for s, (_r, col) in METRICAS_EXPORT_FACEBOOK.items() if col},
        })
        if dia:
            g["primeiro_dia"] = min(d for d in (g["primeiro_dia"], dia) if d)
            g["ultimo_dia"] = max(d for d in (g["ultimo_dia"], dia) if d)
        for s, (_r, col) in METRICAS_EXPORT_FACEBOOK.items():
            if col:
                g[s] += _parse_numero(row.get(col)) or 0.0
        g["_anuncios"].add((str(row.get("ad_id") or "").strip(), dia if por_dia else None))

    # Com Data no detalhamento, ordem cronológica; senão, do maior gasto para o menor.
    if por_dia:
        linhas = sorted(grupos.values(), key=lambda g: (g["data"] or date.min, -g["valor_gasto"]))
    else:
        linhas = sorted(grupos.values(), key=lambda g: g["valor_gasto"], reverse=True)
    for g in linhas:
        g["leads_lexpre"] = sum(leads_lexpre.get(a, 0) for a in g["_anuncios"])
        g["assinados_lexpre"] = sum(assinados_lexpre.get(a, 0) for a in g["_anuncios"])

    if len(linhas) > 1:
        total: Dict[str, Any] = {dims[0]: "TOTAL"} if dims else {}
        total["primeiro_dia"] = min((g["primeiro_dia"] for g in linhas if g["primeiro_dia"]), default=None)
        total["ultimo_dia"] = max((g["ultimo_dia"] for g in linhas if g["ultimo_dia"]), default=None)
        for s, (_r, col) in METRICAS_EXPORT_FACEBOOK.items():
            if col or s in ("leads_lexpre", "assinados_lexpre"):
                total[s] = sum(g[s] for g in linhas)
        linhas.append(total)

    for g in linhas:
        g["cpl"] = round(_divide(g["valor_gasto"], g["leads_lexpre"]), 2)
        g["cac"] = round(_divide(g["valor_gasto"], g["assinados_lexpre"]), 2)
        g["valor_gasto"] = round(g["valor_gasto"], 2)
        for s, (_r, col) in METRICAS_EXPORT_FACEBOOK.items():
            if col and s != "valor_gasto":
                g[s] = int(round(g[s]))
    return slugs, linhas
