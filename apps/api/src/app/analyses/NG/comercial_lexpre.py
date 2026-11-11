# Análises e processamento de dados de COMERCIAL NG (banco lexpre)
#
# Fonte: query "comercial_lexpre_NG" (queries.py) — public.atendimento + public.demandas
# do banco `lexpre`. É o mesmo domínio de negócio do antigo "comercial_geral_NG"
# (banco `ng`), mas em um schema novo:
#   - "ID_ACTION" (antigo) == atendimento.id (o lead/atendimento comercial)
#   - "ID_PROCESSO"/processo (antigo) == demandas (1 atendimento pode ter 0..N demandas)
#
# O lexpre ainda não tem os campos de comissão por rubrica (VALOR_AM), REAJUIZAMENTO
# nem área de atuação usados no dashboard antigo — por ora só as métricas que dá para
# calcular com o que existe hoje no banco.

from typing import Any, Dict, List, Optional, Union
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from app.utils import parse_date_from_db, resolver_periodo_comparativo, normalizar_filtro_ids, normalizar_filtro_textos

# "Assinado" em public.status (lexpre) — atualizado assim que o contrato é assinado,
# antes mesmo do atendimento ser formalmente encerrado. Ver `_is_assinado`: motivo_id
# não entra no critério de "assinou" (só descreve como o atendimento foi encerrado
# depois, às vezes por automação — não invalida uma assinatura já registrada).
STATUS_ASSINADO_ID = 6

# public.escritorio (lexpre): 1 = NGAM, 2 = LAAM, 3 = LARJ.
ESCRITORIO_NGAM = 1
ESCRITORIO_LAAM = 2
ESCRITORIO_LARJ = 3

# "Cancelado" em public.status (lexpre) — mesma tabela de status compartilhada
# entre atendimento.status_id e demandas.status.
STATUS_DEMANDA_CANCELADO_ID = 10

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]


# -----------------------------------------------------------------------------
# Rubricas "reunidas" (pacotes) — expansão para contagem de ações
# -----------------------------------------------------------------------------
#
# Uma demanda cuja rubrica é "reunida" (``rubricas.reunida = true`` — ex.:
# RUBRICAS_BRADESCO, RUBRICAS_REUNIDAS_IRDR) é, na prática, um pacote com várias
# rubricas componentes (``public.rubricas_reunidas``, ``rubrica_id`` = pacote →
# ``rubrica_associada`` = componente). Para contagem de "ações fechadas" (total,
# ranking por atendente, distribuição por rubrica), cada componente ativo conta
# como uma ação — mesmo critério do dashboard Comercial NG legado, que fazia essa
# expansão via LATERAL JOIN em ``processo_rubricas_reunidas`` direto na query SQL.
#
# Importante: essa expansão é só para CONTAGEM (nº de ações). Não se aplica a somas
# em R$ (valor de causa, ticket médio, meta por atendente) — ``valor_causa`` é um
# atributo da demanda/pacote como um todo, não teria sentido repetir o mesmo valor
# por componente.

def build_mapa_rubricas_reunidas(demanda_rubrica_reunida: List[Dict[str, Any]]) -> Dict[Any, List[str]]:
    """
    Monta o mapa ``demanda_id -> [nome_associada, ...]`` a partir de
    ``public.demanda_rubrica_reunida`` (query "demanda_rubrica_reunida_lexpre_NG") — os
    componentes REALMENTE configurados para cada demanda de rubrica "reunida" (pacote),
    não a lista genérica de tudo que já foi associado ao tipo de pacote alguma vez (essa
    lista genérica vive em ``public.rubricas_reunidas`` e não deve ser usada aqui — ver
    o comentário na query, ela chegou a inflar uma única demanda em até 24 "ações").
    """
    mapa: Dict[Any, List[str]] = defaultdict(list)
    for row in demanda_rubrica_reunida or []:
        demanda_id = row.get("DEMANDA_ID")
        nome = row.get("RUBRICA_ASSOCIADA_NOME")
        if demanda_id is None or not nome:
            continue
        mapa[demanda_id].append(str(nome))
    return dict(mapa)


def build_mapa_valor_rubrica_associada(demanda_rubrica_reunida: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Monta o mapa ``nome_associada -> VALOR_AM da própria associada`` a partir de
    ``public.demanda_rubrica_reunida`` (query "demanda_rubrica_reunida_lexpre_NG").

    Usado para o cálculo de comissão (VALOR_AM) por componente de rubrica
    "reunida": o pacote em si normalmente não tem valor cadastrado (quem carrega
    a comissão são os componentes) — ver `_valor_am_por_componente`. O VALOR_AM é
    um atributo da rubrica associada em si (não muda por demanda), então repetir o
    nome em várias demandas apenas sobrescreve com o mesmo valor.
    """
    mapa: Dict[str, float] = {}
    for row in demanda_rubrica_reunida or []:
        nome = row.get("RUBRICA_ASSOCIADA_NOME")
        if not nome:
            continue
        mapa[str(nome)] = _converter_valor(row.get("RUBRICA_ASSOCIADA_VALOR_AM"))
    return mapa


def _valor_am_por_componente(
    row: Dict[str, Any],
    nome_componente: str,
    mapa_valor_associada: Optional[Dict[str, float]],
) -> float:
    """
    VALOR_AM (comissão) de um componente expandido de `_expandir_ids_para_contagem`.

    Quando o componente É a própria rubrica da linha (sem expansão real —
    rubrica normal, ou pacote sem associadas cadastradas), usa ``row["VALOR_AM"]``
    diretamente. Quando o componente é uma associada de um pacote "reunido" (ex.:
    "SEGURO" dentro do pacote "RUBRICAS_BRADESCO"), usa o VALOR_AM da PRÓPRIA
    associada — o pacote normalmente não tem valor cadastrado, e usar o dele
    (NULL/0) para todo componente sub-contaria a comissão.
    """
    if nome_componente == str(row.get("RUBRICA") or "Sem rubrica"):
        return _converter_valor(row.get("VALOR_AM"))
    if mapa_valor_associada and nome_componente in mapa_valor_associada:
        return mapa_valor_associada[nome_componente]
    return _converter_valor(row.get("VALOR_AM"))


def _expandir_ids_para_contagem(
    row: Dict[str, Any],
    mapa_reunidas: Optional[Dict[Any, List[str]]],
) -> List[tuple]:
    """
    Sub-identificadores e nomes de rubrica que uma demanda representa, para fins de
    contagem de "ações fechadas". Demanda com rubrica "reunida" e componentes
    configurados para ELA especificamente (``mapa_reunidas`` chaveado por
    ``ID_DEMANDA``, a partir de ``public.demanda_rubrica_reunida``) gera um par
    ``(sub_id, nome_componente)` por componente; caso contrário (rubrica normal, ou
    pacote sem componentes configurados ainda para essa demanda) gera só um par —
    nunca zera a contagem por falta de cadastro.
    """
    id_demanda = row.get("ID_DEMANDA")
    rubrica_nome = str(row.get("RUBRICA") or "Sem rubrica")
    if not mapa_reunidas or not row.get("RUBRICA_REUNIDA"):
        return [(id_demanda, rubrica_nome)]
    associadas = mapa_reunidas.get(id_demanda) or []
    if not associadas:
        return [(id_demanda, rubrica_nome)]
    return [(f"{id_demanda}::{i}", nome) for i, nome in enumerate(associadas)]


def filter_comercial_lexpre_por_escritorio(
    comercial_lexpre: List[Dict[str, Any]],
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Restringe ao escritório informado — a query traz todos (NGAM/LAAM/LARJ) sem filtro."""
    return [
        row for row in comercial_lexpre or []
        if row.get("ESCRITORIO_ID") == escritorio_id
    ]


# -----------------------------------------------------------------------------
# Filtros da página (atendente / segmento) — aplicados no dispatcher do endpoint,
# antes de qualquer função de estatística, para que a página toda reaja.
# -----------------------------------------------------------------------------

def list_atendentes_comerciais(comercial_lexpre: List[Dict[str, Any]]) -> List[str]:
    """Lista única de atendentes (primeiro nome) presentes no recorte atual, ordenada alfabeticamente."""
    vistos: set = set()
    saida: List[str] = []
    for row in comercial_lexpre or []:
        nome = row.get("ATENDENTE")
        if nome is None or not str(nome).strip():
            continue
        fmt = _formatar_nome_atendente(nome)
        if not fmt or fmt == "Sem atendente" or fmt in vistos:
            continue
        vistos.add(fmt)
        saida.append(fmt)
    return sorted(saida, key=lambda x: x.lower())


def filter_comercial_lexpre_por_atendentes(
    comercial_lexpre: List[Dict[str, Any]],
    atendentes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe aos registros de um ou mais atendentes (união — OR). Aplica-se a leads e
    clientes igualmente (não exige assinatura) — mesmo critério do dashboard Comercial
    NG legado. ``atendentes`` pode ser o nome completo ou o primeiro nome já formatado.
    """
    if not atendentes:
        return list(comercial_lexpre)
    alvos = {_formatar_nome_atendente(a) for a in atendentes if a is not None and str(a).strip()}
    if not alvos:
        return list(comercial_lexpre)
    return [r for r in comercial_lexpre if _formatar_nome_atendente(r.get("ATENDENTE")) in alvos]


def normalizar_segmento_comercial_lexpre(raw: str) -> str:
    """Normaliza texto da UI ou query string para um slug de `CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS`."""
    slug = str(raw).strip().upper().replace(" ", "_")
    if slug in CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS:
        return slug
    raise ValueError(
        "segmento_comercial inválido: {!r}. Valores: {}".format(
            raw, ", ".join(CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS)
        )
    )


def filter_comercial_lexpre_por_segmento(
    comercial_lexpre: List[Dict[str, Any]],
    segmento: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe ao canal de origem informado (mesmos slugs da Seção 02 — Campanha, Redes
    Sociais, Retorno, Resgate, Indicação, Site, Parceiros, Externos). Como o canal só
    existe no universo de clientes assinados, restringe a página inteira a esse
    universo quando o filtro está ativo — mesmo comportamento do dashboard legado.
    """
    if segmento is None or not str(segmento).strip():
        return list(comercial_lexpre)
    slug = normalizar_segmento_comercial_lexpre(str(segmento))
    return [r for r in comercial_lexpre if _row_pertence_canal(r, slug)]


def list_areas_atuacao_comerciais(comercial_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lista única de "áreas de atuação" de verdade (``public.area_atuacao``, via
    ``public.operacao.area_atuacao_id``) presentes no recorte atual.

    Corrigido em 17/09/2026: antes agrupava por ``rubricas.operacao_id``/``public.operacao``
    diretamente — no lexpre, ``operacao`` é mais um código de escritório/operação
    (NGAM/NGPB/NGPA/CONSUMIDOR/ADMINISTRATIVO), não a área de atuação jurídica em si. A
    área de atuação real é ``public.area_atuacao`` (CONSUMIDOR, CIVIL, TRABALHISTA,
    PENAL, ADMINISTRATIVO, AMBIENTAL, PREVIDENCIÁRIO), relacionada via
    ``operacao.area_atuacao_id`` — hoje toda rubrica cadastrada usa uma operação com
    area_atuacao_id=1 (CONSUMIDOR); outras operações (ex.: "NGAM ADM", associada a
    area_atuacao_id=5/ADMINISTRATIVO) ainda vão ser criadas.

    Formato: ``[{"id": area_atuacao_id, "nome": area_atuacao_nome}, ...]``, ordenado por nome.
    """
    vistas: Dict[int, str] = {}
    for row in comercial_lexpre or []:
        area_atuacao_id = row.get("AREA_ATUACAO_ID")
        if area_atuacao_id is None:
            continue
        nome = row.get("AREA_ATUACAO_NOME")
        if area_atuacao_id not in vistas:
            vistas[area_atuacao_id] = str(nome) if nome else f"Área {area_atuacao_id}"
    return sorted(
        ({"id": area_atuacao_id, "nome": nome} for area_atuacao_id, nome in vistas.items()),
        key=lambda item: item["nome"].lower(),
    )


def filter_comercial_lexpre_por_area_atuacao(
    comercial_lexpre: List[Dict[str, Any]],
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe às demandas da "área de atuação" (``public.area_atuacao``, via
    ``operacao.area_atuacao_id`` — ver `list_areas_atuacao_comerciais`) informada.
    ``None`` = sem filtro. Como só demandas têm operação/área de atuação, restringe a
    página ao universo de atendimentos com demanda nessa área quando o filtro está ativo.
    """
    alvos = normalizar_filtro_ids(area_atuacao_id)
    if not alvos:
        return list(comercial_lexpre)
    return [r for r in comercial_lexpre if r.get("AREA_ATUACAO_ID") in alvos]


def filter_comercial_lexpre_por_area_atuacao_nome(
    comercial_lexpre: List[Dict[str, Any]],
    area_atuacao_nome: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe pelo NOME da área de atuação (``AREA_ATUACAO_NOME``), em vez do
    ID usado por `filter_comercial_lexpre_por_area_atuacao`.

    O Estratégico Geral combina esta fonte (banco ``lexpre``, área de atuação
    em ``public.area_atuacao``) com o legado (bancos ``ng``/``laadv``, área de
    atuação em ``juridico.area_atuacao``/``"área_atuação"``) — bancos
    diferentes, sem FK entre eles, então o mesmo ID numérico não tem garantia
    de significar a mesma área nos dois. Comparar pelo nome (ex.: "CONSUMIDOR")
    evita essa coincidência acidental de ID.
    """
    alvos = normalizar_filtro_textos(area_atuacao_nome)
    if not alvos:
        return list(comercial_lexpre)
    return [
        r for r in comercial_lexpre
        if str(r.get("AREA_ATUACAO_NOME") or "").strip().upper() in alvos
    ]


def _normalizar_uf(raw: Any) -> str:
    return str(raw or "").strip().upper()


def list_ufs_comerciais(comercial_lexpre: List[Dict[str, Any]]) -> List[str]:
    """
    Lista única de UFs (``customer.uf``) presentes no recorte atual, ordenada
    alfabeticamente — mesmo critério de `list_areas_atuacao_comerciais`, reaproveitado
    como catálogo compartilhado do filtro de UF em todos os dashboards lexpre (ver
    endpoint "GET /comercial-lexpre/ufs").
    """
    vistas: set = set()
    for row in comercial_lexpre or []:
        uf = _normalizar_uf(row.get("UF"))
        if uf:
            vistas.add(uf)
    return sorted(vistas)


def filter_comercial_lexpre_por_uf(
    comercial_lexpre: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos atendimentos cujo cliente (``customer.uf``) é da UF informada. ``None`` = sem filtro."""
    alvos = normalizar_filtro_textos(uf)
    if not alvos:
        return list(comercial_lexpre)
    return [r for r in comercial_lexpre if _normalizar_uf(r.get("UF")) in alvos]


def _normalizar_rubrica(raw: Any) -> str:
    return str(raw or "").strip().upper()


def filter_comercial_lexpre_por_rubrica(
    comercial_lexpre: List[Dict[str, Any]],
    rubrica: Optional[str] = None,
    mapa_reunidas: Optional[Dict[Any, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe às demandas da rubrica informada — o nome exibido na fatia do gráfico
    "Distribuição por Rubrica". Clique na fatia filtra a página inteira.

    Compara sem diferenciar maiúsculas/minúsculas. Para rubricas reunidas, também
    casa com os componentes ativos em ``mapa_reunidas`` (mesmo recorte da pizza).
    ``None`` = sem filtro.
    """
    if rubrica is None or not str(rubrica).strip():
        return list(comercial_lexpre)
    alvo = _normalizar_rubrica(rubrica)

    def _row_tem_rubrica(row: Dict[str, Any]) -> bool:
        for _sub_id, nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            if _normalizar_rubrica(nome) == alvo:
                return True
        return False

    return [r for r in comercial_lexpre if _row_tem_rubrica(r)]


def _is_assinado(row: Dict[str, Any]) -> bool:
    """
    Cliente assinou: ``status_id == 6`` (Assinado) e ``data_assinatura`` preenchida
    (é essa data que localiza o cliente no período, nos cards da Seção 02).

    ``motivo_id`` NÃO entra no critério — ele só descreve como o atendimento foi
    encerrado depois (passo administrativo separado, às vezes automático — ex.:
    motivo_id 13 "Fechado pela automação - sem interação"), e não invalida uma
    assinatura já registrada. Antes esta função exigia ``motivo_id`` nulo ou == 4
    ("Atendimento finalizado - assinado"), o que excluía clientes que realmente
    assinaram mas cujo atendimento foi encerrado por outro motivo — confirmado com
    o usuário em 04/09/2026 (caso real: 2 de 7 clientes fechados de uma atendente
    ficavam de fora por causa desse filtro).
    """
    if row.get("STATUS_ID") != STATUS_ASSINADO_ID:
        return False
    return bool(row.get("DATA_ASSINATURA"))


def _converter_valor(valor_raw: Any) -> float:
    """Converte um valor monetário (string ou numérico) para float."""
    if valor_raw is None:
        return 0.0

    if isinstance(valor_raw, (int, float, Decimal)):
        return float(valor_raw)

    valor_str = str(valor_raw).strip()
    if not valor_str:
        return 0.0

    valor_str = (
        valor_str.replace("R$", "")
        .replace(" ", "")  # NBSP
        .replace(" ", "")
        .strip()
    )

    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str and "." not in valor_str:
        valor_str = valor_str.replace(",", ".")

    try:
        return float(valor_str)
    except (ValueError, TypeError):
        return 0.0


def _to_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    parsed = parse_date_from_db(raw)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def get_total_leads(comercial_lexpre: List[Dict[str, Any]]) -> int:
    """Total de atendimentos (leads) distintos no recorte atual."""
    return len({
        row.get("ID_ACTION") for row in comercial_lexpre or []
        if row.get("ID_ACTION") is not None
    })


def get_clientes_fechados(comercial_lexpre: List[Dict[str, Any]]) -> int:
    """Total de atendimentos distintos com contrato assinado — ver `_is_assinado`."""
    return len({
        row.get("ID_ACTION") for row in comercial_lexpre or []
        if row.get("ID_ACTION") is not None and _is_assinado(row)
    })


def get_valor_causa_protocolado(
    comercial_lexpre: List[Dict[str, Any]],
    ano: Optional[int] = None,
) -> float:
    """
    Soma o valor de causa das demandas já protocoladas (``data_protocolo`` preenchida).

    Deduplicado por ``ID_DEMANDA`` (uma linha por demanda, já que o join com
    rubrica é 1:1). Se ``ano`` for informado, restringe às demandas protocoladas
    naquele ano civil (base do card "Meta Anual").
    """
    vistos: set = set()
    total = 0.0
    for row in comercial_lexpre or []:
        data_protocolo = _to_date(row.get("DATA_PROTOCOLO"))
        if not data_protocolo:
            continue
        if ano is not None and data_protocolo.year != ano:
            continue

        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in vistos:
            continue
        vistos.add(id_demanda)

        total += _converter_valor(row.get("VALOR_CAUSA"))

    return round(total, 2)


# -----------------------------------------------------------------------------
# Captação por Origem (Seção 02)
# -----------------------------------------------------------------------------
#
# `canal_aquisicao` ainda não é um vocabulário fechado no lexpre — é texto livre
# e a maior parte dos canais abaixo (Redes Sociais, Resgate, Site, Parceiros,
# Externos) não tem nenhum registro real ainda. As regras abaixo cobrem o que já
# existe hoje; os valores esperados para os canais "vazios" ficam documentados
# para ativar assim que o dado passar a existir — ver `_row_pertence_canal`.
#
# Campanha: `canal_aquisicao == "anúncio"` — canal único, sem distinguir RA/NG
# (a Campanha RA está sendo descontinuada e não faz mais sentido separar).

CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS: tuple[str, ...] = (
    "CAMPANHA",
    "REDES_SOCIAIS",
    "RETORNO",
    "RESGATE",
    "INDICACAO",
    "SITE",
    "PARCEIROS",
    "EXTERNOS",
)

# "Orgânico" (tráfego orgânico sem canal específico) conta como Redes Sociais.
_REDES_SOCIAIS_VALUES = frozenset({
    "REDES SOCIAIS", "INSTAGRAM", "FACEBOOK", "YOUTUBE", "GOOGLE",
    "ORGÂNICO", "ORGANICO",
    # Valores de transição vistos em contratos reais já assinados — confirmado
    # pelo usuário que Meta (Facebook) vira canal_aquisicao="facebook" (já
    # coberto acima); "Meta Ads"/"Google Ads" são o rótulo usado até lá.
    "META ADS", "GOOGLE ADS",
})


def _canal_aquisicao_norm(row: Dict[str, Any]) -> str:
    return str(row.get("CANAL_AQUISICAO") or "").strip().upper()


def _prospeccao_norm(row: Dict[str, Any]) -> str:
    return str(row.get("PROSPECCAO") or "").strip().upper()


def _canal_aquisicao_bate(row: Dict[str, Any], canal: str) -> bool:
    """Predicado de canal por ``CANAL_AQUISICAO`` — sem exigir assinatura (usado por leads)."""
    canal_aq = _canal_aquisicao_norm(row)
    if canal == "CAMPANHA":
        return canal_aq == "ANÚNCIO"
    if canal == "REDES_SOCIAIS":
        return canal_aq in _REDES_SOCIAIS_VALUES
    if canal == "RETORNO":
        return canal_aq == "RETORNO"
    if canal == "RESGATE":
        return canal_aq == "RESGATE"
    if canal == "INDICACAO":
        return canal_aq.startswith("INDICA")
    if canal == "SITE":
        return canal_aq == "SITE"
    if canal == "PARCEIROS":
        return canal_aq.startswith("PARCEIRO")
    if canal == "EXTERNOS":
        return canal_aq.startswith("EXTERNO")
    return False


def _row_pertence_canal(row: Dict[str, Any], canal: str) -> bool:
    """Predicado de classificação de canal para clientes — só considera atendimentos assinados."""
    return _is_assinado(row) and _canal_aquisicao_bate(row, canal)


def _row_pertence_algum_canal(row: Dict[str, Any]) -> bool:
    return any(_row_pertence_canal(row, canal) for canal in CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS)


def _distinct_id_actions_no_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    pertence_fn,
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    ids: set = set()
    for row in comercial_lexpre or []:
        if not pertence_fn(row):
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is not None:
            ids.add(id_action)
    return len(ids)


def group_clientes_todos_por_mes(comercial_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa Contratos Fechados (clientes assinados — mesmo critério de
    `get_clientes_todos`) por mês, pra alimentar o gráfico de tendência
    "Contratos por mês" no Estratégico Geral. Sem filtro de período — usa toda
    a história disponível, um mês por ponto (mesmo padrão do legado
    `group_contratos_fechados_por_mes`).
    """
    nomes_mes: Dict[str, str] = {}
    ids_por_mes: Dict[str, set] = defaultdict(set)
    for row in comercial_lexpre or []:
        if not _row_pertence_algum_canal(row):
            continue
        data = _to_date(row.get("DATA_ASSINATURA"))
        if not data:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is None:
            continue
        month_key = f"{data.year}-{data.month:02d}"
        nomes_mes.setdefault(month_key, f"{_MONTH_NAMES[data.month - 1]} {data.year}")
        ids_por_mes[month_key].add(id_action)
    return [
        {"name": nomes_mes[k], "value": len(v)}
        for k, v in sorted(ids_por_mes.items())
    ]


def group_clientes_todos_por_dia(comercial_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mesmo critério de `group_clientes_todos_por_mes`, granularidade diária (drilldown)."""
    ids_por_dia: Dict[str, set] = defaultdict(set)
    for row in comercial_lexpre or []:
        if not _row_pertence_algum_canal(row):
            continue
        data = _to_date(row.get("DATA_ASSINATURA"))
        if not data:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is None:
            continue
        ids_por_dia[data.strftime("%Y-%m-%d")].add(id_action)
    return [
        {"name": k, "value": len(v)}
        for k, v in sorted(ids_por_dia.items())
    ]


def get_clientes_por_canal(
    comercial_lexpre: List[Dict[str, Any]],
    canal: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Clientes (atendimentos distintos) assinados no canal, filtrados por ``DATA_ASSINATURA``."""
    return _distinct_id_actions_no_periodo(
        comercial_lexpre, lambda r: _row_pertence_canal(r, canal), from_date, to_date
    )


def get_clientes_todos(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de clientes assinados classificados em algum canal (soma das origens)."""
    return _distinct_id_actions_no_periodo(
        comercial_lexpre, _row_pertence_algum_canal, from_date, to_date
    )


def _comparativo_variacao_percentual(
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
    """Variação percentual de ``metrica_fn(inicio, fim)`` no período vs. o mesmo recorte um mês civil antes."""
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    valor_atual = metrica_fn(data_inicio_atual, data_fim_atual)
    valor_anterior = metrica_fn(data_inicio_anterior, data_fim_anterior)
    if valor_anterior == 0:
        # Sem base no período anterior (ex.: LA, que só começou a usar o lexpre em
        # 22/09/2026): crescimento a partir do zero é exibido como +100%.
        return 100.0 if valor_atual > 0 else 0.0
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 2)


def get_comparativo_canal(
    comercial_lexpre: List[Dict[str, Any]],
    canal: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    """Variação percentual do canal (ou do total, se ``canal`` for ``None``) no período vs. mês anterior."""
    metrica = (
        (lambda a, b: get_clientes_todos(comercial_lexpre, a, b))
        if canal is None
        else (lambda a, b: get_clientes_por_canal(comercial_lexpre, canal, a, b))
    )
    return _comparativo_variacao_percentual(from_date, to_date, metrica)


def get_clientes_todos_periodo_anterior(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """
    Total de clientes assinados no MESMO recorte do "mês anterior" resolvido
    por ``resolver_periodo_comparativo`` — valor ABSOLUTO (não percentual),
    para o chamador combinar com outras fontes (ex.: legado ng/laadv) e só
    então calcular um único comparativo, em vez de somar percentuais de
    fontes diferentes (que dá resultado errado).
    """
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return get_clientes_todos(comercial_lexpre, data_inicio_anterior, data_fim_anterior)


def get_acoes_fechadas_periodo_anterior(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> int:
    """Mesmo critério de `get_clientes_todos_periodo_anterior`, para ações fechadas."""
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return get_acoes_fechadas(comercial_lexpre, data_inicio_anterior, data_fim_anterior, mapa_reunidas)


def get_acoes_fechadas_por_rubrica(
    comercial_lexpre: List[Dict[str, Any]],
    canal: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Ações fechadas (demandas não canceladas de clientes assinados) agrupadas por
    rubrica, no período — opcionalmente restritas a um canal de origem (mesmos
    valores de `CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS`; ``None`` = todos os canais).

    Demandas de rubrica "reunida" contam uma ação por componente ativo (ver
    `_expandir_ids_para_contagem`) — cada componente aparece com seu próprio nome
    no agrupamento, em vez do nome do pacote.

    Base da Seção 04 (Total de Rubricas — gráfico de pizza "Distribuição por Rubrica").
    """
    vistos: set = set()
    contagem: Dict[str, int] = defaultdict(int)
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        if canal is not None and not _row_pertence_canal(row, canal):
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue

        for sub_id, nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            if sub_id in vistos:
                continue
            vistos.add(sub_id)
            contagem[nome] += 1

    resultado = [{"name": nome, "value": valor} for nome, valor in contagem.items()]
    return sorted(resultado, key=lambda item: item["value"], reverse=True)


# -----------------------------------------------------------------------------
# Cancelados, Ações Fechadas e Aproveitamento (Seção 02)
# -----------------------------------------------------------------------------
#
# Cancelados conta DEMANDAS canceladas (status "Cancelado"), não atendimentos —
# cada demanda é uma ação/rubrica dentro do atendimento. Ações Fechadas conta as
# demandas de atendimentos assinados que NÃO foram canceladas (o lexpre ainda não
# tem um campo de reajuizamento para excluir, diferente do dashboard antigo).
# Aproveitamento é a razão ações_fechadas / clientes_todos (não é percentual —
# mesma fórmula do dashboard Comercial NG legado).
#
# Igual aos canais: só considera demandas de atendimentos assinados (`_is_assinado`),
# bucketizadas pela DATA_ASSINATURA do atendimento (demandas não têm data própria).

def _distinct_id_demandas_no_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    pertence_fn,
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> int:
    """
    ``mapa_reunidas`` opcional: quando informado, demandas de rubrica "reunida" contam
    uma vez por componente ativo (ver `_expandir_ids_para_contagem`) em vez de 1 —
    usado só por `get_acoes_fechadas` (e o que deriva dela). Sem ``mapa_reunidas``,
    conta 1 por demanda — comportamento de `get_demandas_canceladas` e
    `get_rubricas_reunidas_fechadas`, que contam "pacotes", não componentes.
    """
    ids: set = set()
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if not pertence_fn(row):
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        if mapa_reunidas is not None:
            for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
                ids.add(sub_id)
        else:
            ids.add(row.get("ID_DEMANDA"))
    return len(ids)


def group_acoes_fechadas_por_mes(
    comercial_lexpre: List[Dict[str, Any]],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Agrupa Ações Fechadas (mesmo critério de `get_acoes_fechadas`) por mês, pra
    alimentar o gráfico de tendência "Ações por mês" no Estratégico Geral. Sem
    filtro de período — usa toda a história disponível (mesmo padrão do
    legado `group_processos_fechados_por_mes`).
    """
    nomes_mes: Dict[str, str] = {}
    ids_por_mes: Dict[str, set] = defaultdict(set)
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        data = _to_date(row.get("DATA_ASSINATURA"))
        if not data:
            continue
        month_key = f"{data.year}-{data.month:02d}"
        nomes_mes.setdefault(month_key, f"{_MONTH_NAMES[data.month - 1]} {data.year}")
        if mapa_reunidas is not None:
            for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
                ids_por_mes[month_key].add(sub_id)
        else:
            ids_por_mes[month_key].add(row.get("ID_DEMANDA"))
    return [
        {"name": nomes_mes[k], "value": len(v)}
        for k, v in sorted(ids_por_mes.items())
    ]


def group_acoes_fechadas_por_dia(
    comercial_lexpre: List[Dict[str, Any]],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Mesmo critério de `group_acoes_fechadas_por_mes`, granularidade diária (drilldown)."""
    ids_por_dia: Dict[str, set] = defaultdict(set)
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        data = _to_date(row.get("DATA_ASSINATURA"))
        if not data:
            continue
        dia_key = data.strftime("%Y-%m-%d")
        if mapa_reunidas is not None:
            for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
                ids_por_dia[dia_key].add(sub_id)
        else:
            ids_por_dia[dia_key].add(row.get("ID_DEMANDA"))
    return [
        {"name": k, "value": len(v)}
        for k, v in sorted(ids_por_dia.items())
    ]


def get_demandas_canceladas(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Demandas canceladas (status "Cancelado") de atendimentos assinados no período."""
    return _distinct_id_demandas_no_periodo(
        comercial_lexpre,
        lambda r: r.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID,
        from_date,
        to_date,
    )


def get_acoes_fechadas(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> int:
    """
    Demandas de atendimentos assinados no período, excluindo as canceladas.

    Com ``mapa_reunidas`` (ver `build_mapa_rubricas_reunidas`), demandas de rubrica
    "reunida" contam uma ação por componente ativo, não 1 por pacote.
    """
    return _distinct_id_demandas_no_periodo(
        comercial_lexpre,
        lambda r: r.get("STATUS_DEMANDA_ID") != STATUS_DEMANDA_CANCELADO_ID,
        from_date,
        to_date,
        mapa_reunidas=mapa_reunidas,
    )


def get_rubricas_reunidas_fechadas(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Subconjunto de `get_acoes_fechadas`: demandas cuja rubrica é do tipo "reunida"
    (``rubricas.reunida = true`` — ex.: RUBRICAS_BRADESCO, RUBRICAS_REUNIDAS_IRDR).

    Equivalente ao antigo `get_rubricas_reunidas_fechadas` (banco `ng`), que usava uma
    lista fixa de IDs de rubrica (79, 85) — no lexpre a rubrica já tem essa marcação
    própria (`reunida`), então não precisa de lista hardcoded.
    """
    return _distinct_id_demandas_no_periodo(
        comercial_lexpre,
        lambda r: r.get("STATUS_DEMANDA_ID") != STATUS_DEMANDA_CANCELADO_ID and bool(r.get("RUBRICA_REUNIDA")),
        from_date,
        to_date,
    )


def get_taxa_aproveitamento(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    """Ações fechadas por cliente assinado no período — razão, não percentual."""
    clientes = get_clientes_todos(comercial_lexpre, from_date, to_date)
    if clientes == 0:
        return 0.0
    return round(get_acoes_fechadas(comercial_lexpre, from_date, to_date, mapa_reunidas) / clientes, 2)


def get_comparativo_demandas_canceladas(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_demandas_canceladas(comercial_lexpre, a, b)
    )


def get_comparativo_acoes_fechadas(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_acoes_fechadas(comercial_lexpre, a, b, mapa_reunidas)
    )


def get_comparativo_taxa_aproveitamento(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_taxa_aproveitamento(comercial_lexpre, a, b, mapa_reunidas)
    )


# -----------------------------------------------------------------------------
# Leads, ranking e atividade diária (Seção 02 · Performance)
# -----------------------------------------------------------------------------
#
# Leads usam DATA_ENTRADA (quando o atendimento entrou), não DATA_ASSINATURA —
# um lead pode nunca assinar. "Taxa de leads" cruza os dois: clientes assinados
# no período (DATA_ASSINATURA) sobre leads que entraram no período (DATA_ENTRADA).
# "Leads Campanha" substitui o antigo "Leads Anúncio NG" — mesma fusão RA/NG do
# card "Campanha" da Seção 02 anterior, já que não haverá mais leads de RA.

def _formatar_nome_atendente(nome_completo: Any) -> str:
    """Primeiro nome do atendente — mesmo critério dos rankings de outros dashboards comerciais."""
    if not nome_completo or not str(nome_completo).strip():
        return "Sem atendente"
    return str(nome_completo).strip().split()[0]


def _distinct_id_actions_por_entrada_no_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    pertence_fn,
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    ids: set = set()
    for row in comercial_lexpre or []:
        if not pertence_fn(row):
            continue
        data_entrada = _to_date(row.get("DATA_ENTRADA"))
        if not data_entrada:
            continue
        if from_date and data_entrada < from_date:
            continue
        if to_date and data_entrada > to_date:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is not None:
            ids.add(id_action)
    return len(ids)


def get_total_leads_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Atendimentos distintos que entraram no período (``DATA_ENTRADA``), independente de terem assinado."""
    return _distinct_id_actions_por_entrada_no_periodo(
        comercial_lexpre, lambda _r: True, from_date, to_date
    )


def get_leads_por_canal_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    canal: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Leads do canal (por ``CANAL_AQUISICAO``, sem exigir assinatura) que entraram no período."""
    return _distinct_id_actions_por_entrada_no_periodo(
        comercial_lexpre, lambda r: _canal_aquisicao_bate(r, canal), from_date, to_date
    )


def get_leads_campanha_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Leads de campanha (canal_aquisicao == "anúncio") que entraram no período."""
    return get_leads_por_canal_periodo(comercial_lexpre, "CAMPANHA", from_date, to_date)


def _leads_do_periodo_que_assinaram_no_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    pertence_fn,
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """
    Numerador das taxas de leads: atendimentos que ENTRARAM no período (``DATA_ENTRADA``)
    e também ASSINARAM dentro dele (``DATA_ASSINATURA``). Ajuste de 13/10/2026: antes o
    numerador contava qualquer cliente assinado no período, inclusive leads que entraram
    antes dele — a taxa não era "dos leads do período" e podia passar de 100%.
    """
    ids: set = set()
    for row in comercial_lexpre or []:
        if not pertence_fn(row):
            continue
        entrada = _to_date(row.get("DATA_ENTRADA"))
        assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not entrada or not assinatura:
            continue
        if from_date and (entrada < from_date or assinatura < from_date):
            continue
        if to_date and (entrada > to_date or assinatura > to_date):
            continue
        id_action = row.get("ID_ACTION")
        if id_action is not None:
            ids.add(id_action)
    return len(ids)


def get_taxa_leads_geral(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """% dos leads que entraram no período e assinaram contrato dentro do mesmo período."""
    leads = get_total_leads_periodo(comercial_lexpre, from_date, to_date)
    if leads == 0:
        return 0.0
    clientes = _leads_do_periodo_que_assinaram_no_periodo(
        comercial_lexpre, _row_pertence_algum_canal, from_date, to_date
    )
    return round((clientes / leads) * 100, 2)


def get_taxa_leads_campanha(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """% dos leads de campanha que entraram no período e assinaram via campanha dentro do mesmo período."""
    leads = get_leads_campanha_periodo(comercial_lexpre, from_date, to_date)
    if leads == 0:
        return 0.0
    clientes = _leads_do_periodo_que_assinaram_no_periodo(
        comercial_lexpre, lambda r: _row_pertence_canal(r, "CAMPANHA"), from_date, to_date
    )
    return round((clientes / leads) * 100, 2)


def get_comparativo_total_leads(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_total_leads_periodo(comercial_lexpre, a, b)
    )


def get_comparativo_leads_campanha(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_leads_campanha_periodo(comercial_lexpre, a, b)
    )


def get_comparativo_taxa_leads_geral(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_taxa_leads_geral(comercial_lexpre, a, b)
    )


def get_comparativo_taxa_leads_campanha(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_taxa_leads_campanha(comercial_lexpre, a, b)
    )


def get_ranking_acoes_fechadas_por_atendente(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limite: Optional[int] = 5,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Top atendentes por ações fechadas (demandas não canceladas) de clientes assinados no período.

    Demandas de rubrica "reunida" contam uma ação por componente ativo (ver
    `_expandir_ids_para_contagem`), não 1 por pacote. ``limite=None`` retorna todos
    os atendentes, sem cortar o ranking.
    """
    vistos: set = set()
    contagem: Dict[str, int] = defaultdict(int)
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        nome_atendente = _formatar_nome_atendente(row.get("ATENDENTE"))
        for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            if sub_id in vistos:
                continue
            vistos.add(sub_id)
            contagem[nome_atendente] += 1

    ranking = sorted(
        ({"name": nome, "value": valor} for nome, valor in contagem.items()),
        key=lambda item: item["value"],
        reverse=True,
    )
    return ranking[:limite]


def get_acoes_fechadas_hoje_por_atendente(
    comercial_lexpre: List[Dict[str, Any]],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Ações (demandas) fechadas hoje, agrupadas por atendente."""
    hoje = date.today()
    return get_ranking_acoes_fechadas_por_atendente(
        comercial_lexpre, hoje, hoje, limite=None, mapa_reunidas=mapa_reunidas
    )


def get_contratos_fechados_hoje_por_atendente(
    comercial_lexpre: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Contratos assinados hoje, agrupados por atendente."""
    hoje = date.today()
    vistos: set = set()
    contagem: Dict[str, int] = defaultdict(int)
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        id_action = row.get("ID_ACTION")
        if id_action is None or id_action in vistos:
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if data_assinatura != hoje:
            continue
        vistos.add(id_action)
        contagem[_formatar_nome_atendente(row.get("ATENDENTE"))] += 1

    return sorted(
        ({"name": nome, "value": valor} for nome, valor in contagem.items()),
        key=lambda item: item["value"],
        reverse=True,
    )


# -----------------------------------------------------------------------------
# Acompanhamento por Atendente (Seção 05)
# -----------------------------------------------------------------------------
#
# Leads/clientes/taxa de fechamento gerais e por canal, uma linha por atendente.
# Sem o corte ativa/passiva por canal do dashboard Comercial NG legado (indicação,
# retorno e resgate ativos/passivos) — essa distinção não existe no modelo de
# canais do lexpre hoje.

def _leads_por_atendente_no_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    pertence_fn,
    from_date: Optional[date],
    to_date: Optional[date],
) -> Dict[str, int]:
    """Leads (atendimentos distintos, por DATA_ENTRADA) que casam ``pertence_fn``, por atendente."""
    ids_por_atendente: Dict[str, set] = defaultdict(set)
    for row in comercial_lexpre or []:
        if not pertence_fn(row):
            continue
        data_entrada = _to_date(row.get("DATA_ENTRADA"))
        if not data_entrada:
            continue
        if from_date and data_entrada < from_date:
            continue
        if to_date and data_entrada > to_date:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is None:
            continue
        ids_por_atendente[_formatar_nome_atendente(row.get("ATENDENTE"))].add(id_action)
    return {nome: len(ids) for nome, ids in ids_por_atendente.items()}


def _clientes_por_atendente_no_periodo(
    comercial_lexpre: List[Dict[str, Any]],
    pertence_fn,
    from_date: Optional[date],
    to_date: Optional[date],
) -> Dict[str, int]:
    """Clientes assinados (atendimentos distintos, por DATA_ASSINATURA) que casam ``pertence_fn``, por atendente."""
    ids_por_atendente: Dict[str, set] = defaultdict(set)
    for row in comercial_lexpre or []:
        if not _is_assinado(row):
            continue
        if not pertence_fn(row):
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is None:
            continue
        ids_por_atendente[_formatar_nome_atendente(row.get("ATENDENTE"))].add(id_action)
    return {nome: len(ids) for nome, ids in ids_por_atendente.items()}


def _taxa_fechamento(leads: int, clientes: int) -> float:
    return round((clientes / leads) * 100, 2) if leads > 0 else 0.0


# Canais com corte ativa/passiva (via ``atendimento.prospeccao``) na tabela por
# atendente — mesmo corte do dashboard Comercial NG legado (Indicação, Retorno e
# Resgate ativos/passivos). Os demais canais (Campanha, Redes Sociais, Site,
# Parceiros, Externos) não têm esse corte.
CANAIS_ATIVA_PASSIVA_ORDENADOS: tuple[str, ...] = ("INDICACAO", "RETORNO", "RESGATE")


def _colunas_tabela_por_atendente():
    """
    Colunas da tabela por atendente: ``(slug, predicado_leads, predicado_clientes)``.

    Para canais em `CANAIS_ATIVA_PASSIVA_ORDENADOS`, gera duas colunas (``<slug>_ativa``
    e ``<slug>_passiva``, via ``prospeccao``); para os demais, uma só coluna ``<slug>``.
    """
    colunas = []
    for canal in CANAIS_COMERCIAL_LEXPRE_NG_ORDENADOS:
        slug = canal.lower()
        if canal in CANAIS_ATIVA_PASSIVA_ORDENADOS:
            for sufixo, prospeccao_valor in (("ativa", "ATIVA"), ("passiva", "PASSIVA")):
                colunas.append((
                    f"{slug}_{sufixo}",
                    (lambda r, canal=canal, p=prospeccao_valor: _canal_aquisicao_bate(r, canal) and _prospeccao_norm(r) == p),
                    (lambda r, canal=canal, p=prospeccao_valor: _row_pertence_canal(r, canal) and _prospeccao_norm(r) == p),
                ))
        else:
            colunas.append((
                slug,
                (lambda r, canal=canal: _canal_aquisicao_bate(r, canal)),
                (lambda r, canal=canal: _row_pertence_canal(r, canal)),
            ))
    return colunas


def get_tabela_por_atendente(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Uma linha por atendente: leads, clientes e taxa de fechamento gerais e por coluna
    de origem, no período. Ordenado por ``leads_geral`` decrescente (o front reordena
    localmente conforme o critério escolhido no dropdown).

    Formato de cada linha: ``{"atendente": str, "leads_geral": int, "clientes_geral": int,
    "taxa_geral": float, "leads_<slug>": int, "clientes_<slug>": int, "taxa_<slug>": float, ...}``
    — ver `_colunas_tabela_por_atendente` para a lista de ``slug``.
    """
    leads_geral = _leads_por_atendente_no_periodo(comercial_lexpre, lambda _r: True, from_date, to_date)
    clientes_geral = _clientes_por_atendente_no_periodo(comercial_lexpre, _row_pertence_algum_canal, from_date, to_date)

    colunas = _colunas_tabela_por_atendente()
    por_coluna: Dict[str, tuple] = {}
    todos_atendentes = set(leads_geral) | set(clientes_geral)
    for slug, leads_fn, clientes_fn in colunas:
        leads_c = _leads_por_atendente_no_periodo(comercial_lexpre, leads_fn, from_date, to_date)
        clientes_c = _clientes_por_atendente_no_periodo(comercial_lexpre, clientes_fn, from_date, to_date)
        por_coluna[slug] = (leads_c, clientes_c)
        todos_atendentes |= set(leads_c) | set(clientes_c)

    linhas: List[Dict[str, Any]] = []
    for nome in todos_atendentes:
        l_geral = leads_geral.get(nome, 0)
        c_geral = clientes_geral.get(nome, 0)
        linha: Dict[str, Any] = {
            "atendente": nome,
            "leads_geral": l_geral,
            "clientes_geral": c_geral,
            "taxa_geral": _taxa_fechamento(l_geral, c_geral),
        }
        for slug, _leads_fn, _clientes_fn in colunas:
            leads_c, clientes_c = por_coluna[slug]
            l = leads_c.get(nome, 0)
            c = clientes_c.get(nome, 0)
            linha[f"leads_{slug}"] = l
            linha[f"clientes_{slug}"] = c
            linha[f"taxa_{slug}"] = _taxa_fechamento(l, c)
        linhas.append(linha)

    return sorted(linhas, key=lambda r: r["leads_geral"], reverse=True)


def get_totais_tabela_por_atendente(
    comercial_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Linha "Total" da tabela por atendente — mesmas colunas de `get_tabela_por_atendente`."""
    leads_geral = get_total_leads_periodo(comercial_lexpre, from_date, to_date)
    clientes_geral = get_clientes_todos(comercial_lexpre, from_date, to_date)
    total: Dict[str, Any] = {
        "atendente": "Total",
        "leads_geral": leads_geral,
        "clientes_geral": clientes_geral,
        "taxa_geral": _taxa_fechamento(leads_geral, clientes_geral),
    }
    for slug, leads_fn, clientes_fn in _colunas_tabela_por_atendente():
        leads_c = _distinct_id_actions_por_entrada_no_periodo(comercial_lexpre, leads_fn, from_date, to_date)
        clientes_c = _distinct_id_actions_no_periodo(comercial_lexpre, clientes_fn, from_date, to_date)
        total[f"leads_{slug}"] = leads_c
        total[f"clientes_{slug}"] = clientes_c
        total[f"taxa_{slug}"] = _taxa_fechamento(leads_c, clientes_c)
    return total
