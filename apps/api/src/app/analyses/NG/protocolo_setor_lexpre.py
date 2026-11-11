# Análises e processamento de dados de PROTOCOLO NG (banco lexpre) — visão de SETOR
#
# Fonte: query "log_setor_demanda_lexpre_NG" (queries.py) — o mesmo log cru de
# entradas/saídas de setor usado por org_doc_lexpre.py e peticionamento_lexpre.py,
# aqui recortado para o setor "Protocolo" (public.setores.id = 5). Mesmo domínio
# de negócio do antigo "protocolo" (banco `ng`, tabela protocolo — uma linha por
# processo), mas orientado a EVENTOS: cada linha do log é uma entrada OU saída de
# uma demanda em um setor, não um processo.
#
# Este módulo é a visão OPERACIONAL do setor (represados, tempo no setor) —
# complementar, não duplicado, ao módulo `protocolo_lexpre.py` (usado pela
# página Comercial (LexPre), Seção 03), que já cobre a visão COMERCIAL de
# protocolamento a partir de ``demandas.data_protocolo`` (sem depender do log
# de movimentação de setor).
#
# Diferença-chave em relação a org_doc_lexpre.py / peticionamento_lexpre.py: o
# critério de "resolvido" aqui NÃO é o setor de destino da saída — é o STATUS
# que a demanda atinge (``demandas.status`` chegar a "Aguardando Despacho
# Inicial", public.status.id = 13). "Represados" cobre qualquer demanda ainda
# no setor, não resolvida (ver abaixo); "Devolvido p/ X" cobre as que SAÍRAM do
# Protocolo sem ter sido resolvidas, devolvidas para qualquer setor anterior
# (Peticionamento, Organização de Documentos ou Pendências) — mesmo mecanismo
# de `get_devolvido_pendencia` em org_doc_lexpre.py.
#
# Mapeamento das colunas do dashboard antigo (NG, banco `ng`) para o novo (lexpre):
#   - SAIDA (data em que o processo saiu do setor)      -> evento TIPO="saida", SETOR_ID=5,
#     cujo STATUS DA DEMANDA (``demandas.status``, valor vivo) é "Aguardando
#     Despacho Inicial" (id=13) — ver `_is_protocolado` e `_saidas_setor`.
#   - ENTRADA (data em que o processo entrou no setor)  -> evento TIPO="entrada", SETOR_ID=5
#   - MATERIA (rubrica, com sufixo livre "X - banco")    -> rubricas.nome (já normalizado)
#   - FUNCIONARIO responsável pelo protocolo             -> responsável (setor_func) no
#     momento da ENTRADA no setor, propagado para a saída correspondente (mesmo
#     critério de org_doc_lexpre.py/peticionamento_lexpre.py).
#   - STATUS "Cancelado"                                  -> demandas.status ==
#     STATUS_DEMANDA_CANCELADO_ID (10), mesma constante de comercial_lexpre.py —
#     usado só para EXCLUIR canceladas de "Represados" (sem card dedicado).
#   - REAJUIZAMENTO                                       -> não existe no lexpre ainda;
#     os cards "Protocolados de Reajuizamento" / "Represados de Reajuizamento"
#     do dashboard antigo ficam como placeholder (valor 0) na UI.
#   - Comissionamento por meta anual (fator multiplicador AM/PA/PB)
#     -> não existe no lexpre ainda: depende de metas comerciais anuais e do
#     pool de comissão da Comercial (comissao_lexpre.py), que ainda não tem
#     VALOR_AM cadastrado por rubrica no lexpre. Sem equivalente aqui por ora.
#   - "Represados" / "Não Protocolados" (processos parados no setor, sem filtro
#     de período) -> demandas (não canceladas, ainda sem status "Aguardando
#     Despacho Inicial") cujo setor_id ATUAL (demandas.setor_id, não o evento
#     de log) é 5 — ou seja, ainda estão "no Protocolo", não resolvidas.
#   - "Devolvido p/ Peticionamento" / "Devolvido p/ Org Doc" / "Devolvido p/
#     Pendência" (saída do setor para um setor anterior, sem status "Aguardando
#     Despacho Inicial" — a demanda foi devolvida antes de ser resolvida) ->
#     evento de saída do setor 5 cujo destino (movimentação pareada) é
#     Peticionamento (id=4), Organização de Documentos (id=3) ou Pendências
#     (id=2) — ver `_setor_destino` e `get_devolvido_peticionamento` /
#     `get_devolvido_org_doc` / `get_devolvido_pendencia`.

from typing import Any, Dict, List, Optional, Union
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from app.utils import parse_date_from_db, parse_datetime_from_db, resolver_periodo_comparativo, normalizar_filtro_ids, normalizar_filtro_textos

# public.escritorio (lexpre): 1 = NGAM, 2 = LAAM, 3 = LARJ — mesma constante de comercial_lexpre.py.
ESCRITORIO_NGAM = 1
ESCRITORIO_LAAM = 2
ESCRITORIO_LARJ = 3

# public.setores (lexpre) — cada escritório tem seu próprio bloco de ids pro mesmo
# setor lógico (link real: setores.operacao_id -> operacao.escritorio_id). Cada
# constante abaixo é a UNIÃO dos ids desse setor em todos os escritórios com
# dashboard lexpre até agora (NGAM=1, LAAM=2, LARJ=3 — ver o mesmo ajuste em
# org_doc_lexpre.py/pendencia_setor_lexpre.py, 24/09/2026; LARJ adicionado em
# 14/10/2026, operacao_id=33). A atribuição de escritório de uma linha vem SEMPRE
# da coluna ESCRITORIO_ID, nunca do valor de SETOR_ID/SETOR_ATUAL_ID em si — por
# isso a comparação é por pertencimento (in).
#   Setor                         NGAM   LAAM   LARJ
#   Pendências                      2     10    161
#   Organização de Documentos       3     11    155
#   Peticionamento                  4     12    157
#   Protocolo                       5     13    158
SETOR_PENDENCIAS_IDS = {2, 10, 161}
SETOR_ORG_DOC_IDS = {3, 11, 155}
SETOR_PETICIONAMENTO_IDS = {4, 12, 157}
SETOR_PROTOCOLO_IDS = {5, 13, 158}

# public.status (lexpre).
STATUS_DEMANDA_CANCELADO_ID = 10
STATUS_AG_DESPACHO_INICIAL_ID = 13


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

def filter_protocolo_lexpre_por_escritorio(
    protocolo_lexpre: List[Dict[str, Any]],
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Restringe ao escritório informado — a query traz todos (NGAM/LAAM/LARJ) sem filtro."""
    return [row for row in protocolo_lexpre or [] if row.get("ESCRITORIO_ID") == escritorio_id]


def _to_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    parsed = parse_date_from_db(raw)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def _to_datetime(raw: Any) -> Optional[datetime]:
    if not raw:
        return None
    return parse_datetime_from_db(raw)


def _converter_valor(valor_raw: Any) -> float:
    """Converte um valor monetário (string ou numérico) para float — mesma lógica de comercial_lexpre.py."""
    if valor_raw is None:
        return 0.0
    if isinstance(valor_raw, (int, float, Decimal)):
        return float(valor_raw)
    valor_str = str(valor_raw).strip()
    if not valor_str:
        return 0.0
    valor_str = valor_str.replace("R$", "").replace(" ", "").replace(" ", "").strip()
    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str and "." not in valor_str:
        valor_str = valor_str.replace(",", ".")
    try:
        return float(valor_str)
    except (ValueError, TypeError):
        return 0.0


def _formatar_nome_funcionario(nome_completo: Any) -> str:
    """Primeiro e segundo nome do funcionário — mesmo critério de org_doc_lexpre.py."""
    if not nome_completo or not str(nome_completo).strip():
        return "Sem funcionário"
    partes = str(nome_completo).strip().split()
    if len(partes) == 1:
        return partes[0]
    return " ".join(partes[:2])


def _normalizar_materia(raw: Any) -> str:
    """Rubrica já vem normalizada do lexpre (sem o sufixo livre do banco `ng`)."""
    s = str(raw or "").strip()
    return s if s else "Sem matéria"


def _is_cancelado(row: Dict[str, Any]) -> bool:
    return row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID


def _is_protocolado(row: Dict[str, Any]) -> bool:
    """Demanda atingiu o status "Aguardando Despacho Inicial" — critério de conclusão do Protocolo."""
    return row.get("STATUS_DEMANDA_ID") == STATUS_AG_DESPACHO_INICIAL_ID


def _indexar_movimentacoes(protocolo_lexpre: List[Dict[str, Any]]) -> Dict[Any, Dict[str, Dict[str, Any]]]:
    """
    ``movimentacao_id -> {"entrada": linha, "saida": linha}``, a partir do universo
    COMPLETO de eventos (todos os setores, não só Protocolo) — mesmo mecanismo de
    org_doc_lexpre.py/peticionamento_lexpre.py, usado aqui para descobrir para
    qual setor uma demanda foi devolvida a partir de um evento de saída do setor 5.
    """
    idx: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in protocolo_lexpre or []:
        mov_id = row.get("MOVIMENTACAO_ID")
        tipo = row.get("TIPO")
        if mov_id is None or tipo not in ("entrada", "saida"):
            continue
        idx[mov_id][tipo] = row
    return idx


def _setor_destino(saida_row: Dict[str, Any], idx: Dict[Any, Dict[str, Dict[str, Any]]]) -> Optional[int]:
    """Setor para o qual a demanda foi, para um evento de ``saida`` — ``None`` se não houver entrada pareada (ex.: cancelamento)."""
    par = idx.get(saida_row.get("MOVIMENTACAO_ID"), {})
    entrada_par = par.get("entrada")
    return entrada_par.get("SETOR_ID") if entrada_par else None


def _entradas_setor(protocolo_lexpre: List[Dict[str, Any]], setor_ids: set) -> List[Dict[str, Any]]:
    return [
        row for row in protocolo_lexpre or []
        if row.get("SETOR_ID") in setor_ids and row.get("TIPO") == "entrada"
    ]


def _saidas_setor(protocolo_lexpre: List[Dict[str, Any]], setor_ids: set) -> List[Dict[str, Any]]:
    """
    Última saída do setor, uma por demanda.

    Uma demanda pode sair do setor mais de uma vez (ex.: é devolvida para
    Peticionamento e depois retorna, ficando represada de novo, até finalmente
    sair outra vez) — cada ida gera seu próprio evento de saída em
    ``log_setor_demanda``. Sem essa deduplicação, uma mesma demanda contaria
    como "protocolada" uma vez por saída. Mesma lógica de org_doc_lexpre.py.

    Demandas cujo setor ATUAL (``SETOR_ATUAL_ID``, valor vivo de ``demandas``) é
    de novo o setor informado são excluídas por completo: a última saída
    registrada não foi final — a demanda voltou e está represada outra vez
    (contabilizada só em `get_represados`, nunca simultaneamente como protocolada).
    """
    ultima_por_demanda: Dict[Any, Dict[str, Any]] = {}
    for row in protocolo_lexpre or []:
        if row.get("SETOR_ID") not in setor_ids or row.get("TIPO") != "saida":
            continue
        if row.get("SETOR_ATUAL_ID") in setor_ids:
            continue
        demanda_id = row.get("ID_DEMANDA")
        atual = ultima_por_demanda.get(demanda_id)
        data_row = _to_datetime(row.get("DATA")) or datetime.min
        data_atual = _to_datetime(atual.get("DATA")) if atual else None
        if atual is None or data_row > (data_atual or datetime.min):
            ultima_por_demanda[demanda_id] = row
    return list(ultima_por_demanda.values())


def _filtrar_protocolados_reais(saidas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    De ``_saidas_setor`` (última saída por demanda), mantém só as que de fato
    protocolaram a demanda — status "Aguardando Despacho Inicial". Sem esse
    filtro, uma saída para outro setor sem esse status (a demanda ainda não foi
    resolvida) contaria erroneamente como "protocolada".
    """
    return [row for row in saidas if _is_protocolado(row)]


def _entradas_por_demanda(entradas: List[Dict[str, Any]]) -> Dict[Any, List[Dict[str, Any]]]:
    """Entradas no setor, agrupadas por demanda e ordenadas por data (mais antiga primeiro)."""
    por_demanda: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for row in entradas:
        por_demanda[row.get("ID_DEMANDA")].append(row)
    for lista in por_demanda.values():
        lista.sort(key=lambda r: _to_datetime(r.get("DATA")) or datetime.min)
    return dict(por_demanda)


def _ultima_entrada_antes_de(
    demanda_id: Any,
    referencia: Optional[datetime],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """Última entrada da demanda no setor até (e incluindo) o instante de referência."""
    candidatas = entradas_por_demanda.get(demanda_id) or []
    if not candidatas:
        return None
    if referencia is None:
        return candidatas[-1]
    escolhida = None
    for row in candidatas:
        data_entrada = _to_datetime(row.get("DATA"))
        if data_entrada is not None and data_entrada <= referencia:
            escolhida = row
        else:
            break
    return escolhida or candidatas[0]


def _funcionario_responsavel(
    saida_row: Dict[str, Any],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> str:
    """
    Funcionário responsável por uma saída do setor — o próprio evento de saída
    normalmente não carrega responsável (ver cabeçalho do módulo), então usamos o
    responsável registrado na última entrada da mesma demanda no setor, antes da
    saída.
    """
    if saida_row.get("FUNCIONARIO"):
        return _formatar_nome_funcionario(saida_row.get("FUNCIONARIO"))
    entrada = _ultima_entrada_antes_de(
        saida_row.get("ID_DEMANDA"), _to_datetime(saida_row.get("DATA")), entradas_por_demanda
    )
    return _formatar_nome_funcionario(entrada.get("FUNCIONARIO") if entrada else None)


def _filter_saidas_by_date_range(saidas: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    filtered = []
    for row in saidas:
        d = _to_date(row.get("DATA"))
        if d and from_date <= d <= to_date:
            filtered.append(row)
    return filtered


# -----------------------------------------------------------------------------
# 2 - Filtros da página (matéria / funcionário / área de atuação)
# -----------------------------------------------------------------------------

def filter_protocolo_lexpre_por_materia(
    protocolo_lexpre: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(protocolo_lexpre)
    return [row for row in protocolo_lexpre if _normalizar_materia(row.get("MATERIA")) in alvos]


def filter_protocolo_lexpre_por_area_atuacao(
    protocolo_lexpre: List[Dict[str, Any]],
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe pela área de atuação real (``public.area_atuacao``, via ``operacao.area_atuacao_id``) — ver comercial_lexpre.filter_comercial_lexpre_por_area_atuacao."""
    alvos = normalizar_filtro_ids(area_atuacao_id)
    if not alvos:
        return list(protocolo_lexpre)
    return [row for row in protocolo_lexpre if row.get("AREA_ATUACAO_ID") in alvos]


def filter_protocolo_lexpre_por_area_atuacao_nome(
    protocolo_lexpre: List[Dict[str, Any]],
    area_atuacao_nome: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe pelo NOME da área de atuação (``AREA_ATUACAO_NOME``), em vez do
    ID — usado pelo Estratégico Geral, que casa por nome com o legado
    (bancos/tabelas de área de atuação diferentes, sem relação entre os IDs;
    ver comercial_lexpre.filter_comercial_lexpre_por_area_atuacao_nome).
    """
    alvos = normalizar_filtro_textos(area_atuacao_nome)
    if not alvos:
        return list(protocolo_lexpre)
    return [
        row for row in protocolo_lexpre
        if str(row.get("AREA_ATUACAO_NOME") or "").strip().upper() in alvos
    ]


def filter_protocolo_lexpre_por_uf(
    protocolo_lexpre: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe às demandas cujo cliente (``customer.uf``) é da UF informada. ``None`` = sem filtro. Catálogo de UFs compartilhado — ver `comercial_lexpre.list_ufs_comerciais`."""
    alvos = normalizar_filtro_textos(uf)
    if not alvos:
        return list(protocolo_lexpre)
    return [row for row in protocolo_lexpre if str(row.get("UF") or "").strip().upper() in alvos]


def list_funcionarios_protocolo_lexpre(protocolo_lexpre: List[Dict[str, Any]]) -> List[str]:
    """Funcionários que aparecem como responsáveis por uma entrada no setor, no recorte atual."""
    vistos: set = set()
    saida: List[str] = []
    for row in _entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS):
        nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        if nome == "Sem funcionário" or nome in vistos:
            continue
        vistos.add(nome)
        saida.append(nome)
    return sorted(saida, key=lambda x: x.lower())


def filter_protocolo_lexpre_por_funcionarios(
    protocolo_lexpre: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe às demandas cujo responsável (na última entrada no setor) é um dos
    funcionários informados (união — OR). Filtra por DEMANDA, não por evento
    isolado — mesmo critério de org_doc_lexpre.py.
    """
    if not funcionarios:
        return list(protocolo_lexpre)
    alvos = {_formatar_nome_funcionario(f) for f in funcionarios if f is not None and str(f).strip()}
    if not alvos:
        return list(protocolo_lexpre)

    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS))

    demandas_alvo: set = set()
    for row in protocolo_lexpre:
        if row.get("SETOR_ID") not in SETOR_PROTOCOLO_IDS:
            continue
        if row.get("TIPO") == "entrada":
            nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        else:
            nome = _funcionario_responsavel(row, entradas_por_demanda)
        if nome in alvos:
            demandas_alvo.add(row.get("ID_DEMANDA"))

    return [row for row in protocolo_lexpre if row.get("ID_DEMANDA") in demandas_alvo]


# -----------------------------------------------------------------------------
# 3 - KPIs do período (base: saídas do setor 5, por DATA da saída)
# -----------------------------------------------------------------------------

def get_protocolados_total(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if _is_protocolado(row)])


def get_represados(protocolo_lexpre: List[Dict[str, Any]]) -> int:
    """
    Demandas (não canceladas, ainda não protocoladas) atualmente no setor de
    Protocolo — ou seja, ainda com status diferente de "Aguardando Despacho
    Inicial", pois ainda não foram resolvidas. Valor sempre total, sem filtro
    de período, mesmo critério de "Não Protocolados" no dashboard antigo.
    Deduplicado por ID_DEMANDA.
    """
    vistos: set = set()
    for row in protocolo_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PROTOCOLO_IDS:
            continue
        if _is_cancelado(row) or _is_protocolado(row):
            continue
        vistos.add(demanda_id)
    return len(vistos)


def _devolvidos(
    protocolo_lexpre: List[Dict[str, Any]],
    setores_destino_alvo: set,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Demandas devolvidas do Protocolo para o setor informado — saída do setor 5
    cujo destino (movimentação pareada) é o setor alvo, sem ter atingido o
    status "Aguardando Despacho Inicial". Conta eventos de saída (não
    deduplicados: cada devolução conta), valor sempre total, independente do
    período — mesmo critério de `get_devolvido_pendencia` em org_doc_lexpre.py.
    """
    idx = _indexar_movimentacoes(protocolo_lexpre)
    saidas_brutas = [
        row for row in protocolo_lexpre or []
        if row.get("SETOR_ID") in SETOR_PROTOCOLO_IDS and row.get("TIPO") == "saida"
    ]
    # Sem datas = total (o card); com datas = só devoluções do intervalo (comparativo).
    if from_date and to_date:
        saidas_brutas = _filter_saidas_by_date_range(saidas_brutas, from_date, to_date)
    return len([row for row in saidas_brutas if _setor_destino(row, idx) in setores_destino_alvo])


def get_devolvido_peticionamento(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Demandas devolvidas do Protocolo para Peticionamento — equivalente a "Devolvido p/ Peticionamento"."""
    return _devolvidos(protocolo_lexpre, SETOR_PETICIONAMENTO_IDS, from_date, to_date)


def get_devolvido_org_doc(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Demandas devolvidas do Protocolo para Organização de Documentos — equivalente a "Devolvido p/ Org Doc"."""
    return _devolvidos(protocolo_lexpre, SETOR_ORG_DOC_IDS, from_date, to_date)


def get_devolvido_pendencia(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Demandas devolvidas do Protocolo para Pendências — equivalente a "Devolvido p/ Pendência"."""
    return _devolvidos(protocolo_lexpre, SETOR_PENDENCIAS_IDS, from_date, to_date)


def get_valor_causa_protocolado(saidas_periodo: List[Dict[str, Any]]) -> float:
    """Soma do valor de causa das demandas protocoladas (não canceladas) no período."""
    total = 0.0
    for row in saidas_periodo:
        materia = _normalizar_materia(row.get("MATERIA")).upper()
        valor_raw = row.get("DANO_MORAL") if materia == "ANP" else row.get("VALOR_CAUSA")
        valor = _converter_valor(valor_raw)
        if valor > 0:
            total += valor
    return round(total, 2)


def get_ticket_medio_protocolado(saidas_periodo: List[Dict[str, Any]]) -> float:
    """Valor de causa protocolado médio por demanda no período."""
    qtd = get_protocolados_total(saidas_periodo)
    if qtd == 0:
        return 0.0
    return round(get_valor_causa_protocolado(saidas_periodo) / qtd, 2)


# -----------------------------------------------------------------------------
# 4 - Tempo no setor (entrada -> saída no setor 5)
# -----------------------------------------------------------------------------

def _extrair_duracoes_horas(
    saidas: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[float]:
    duracoes: List[float] = []
    for row in saidas:
        saida_dt = _to_datetime(row.get("DATA"))
        entrada = _ultima_entrada_antes_de(row.get("ID_DEMANDA"), saida_dt, entradas_por_demanda)
        entrada_dt = _to_datetime(entrada.get("DATA")) if entrada else None
        if not saida_dt or not entrada_dt:
            continue
        horas = (saida_dt - entrada_dt).total_seconds() / 3600
        if horas > 0:
            duracoes.append(horas)
    return duracoes


def get_media_tempo_protocolado(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> float:
    """Média de dias entre entrada e saída no setor, para demandas protocoladas no período."""
    duracoes_horas = _extrair_duracoes_horas(saidas_periodo, entradas_por_demanda)
    if not duracoes_horas:
        return 0.0
    return round((sum(duracoes_horas) / len(duracoes_horas)) / 24, 2)


def get_mediana_tempo_protocolado(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> float:
    duracoes_horas = _extrair_duracoes_horas(saidas_periodo, entradas_por_demanda)
    if not duracoes_horas:
        return 0.0
    duracoes_horas.sort()
    n = len(duracoes_horas)
    mediana_horas = (
        duracoes_horas[n // 2]
        if n % 2 == 1
        else (duracoes_horas[n // 2 - 1] + duracoes_horas[n // 2]) / 2.0
    )
    return round(mediana_horas / 24, 2)


# -----------------------------------------------------------------------------
# 5 - Comparativo (período atual vs. mesmo recorte um mês civil antes)
# -----------------------------------------------------------------------------

def _comparativo_variacao_percentual(
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
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


def _saidas_protocoladas_para_comparativo(protocolo_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """``_saidas_setor`` já filtrada para status "Aguardando Despacho Inicial" — mesma base usada nos stats do período."""
    saidas = _saidas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS)
    return _filtrar_protocolados_reais(saidas)


def get_comparativo_protocolados_total(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_protocoladas_para_comparativo(protocolo_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_protocolados_total(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_valor_causa_protocolado(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_protocoladas_para_comparativo(protocolo_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_valor_causa_protocolado(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_ticket_medio_protocolado(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_protocoladas_para_comparativo(protocolo_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_ticket_medio_protocolado(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_devolvido_peticionamento(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    """Devoluções p/ Peticionamento no período selecionado vs mesmo recorte do mês anterior (o card em si segue total)."""
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_devolvido_peticionamento(protocolo_lexpre, a, b)
    )


def get_comparativo_devolvido_org_doc(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    """Devoluções p/ Org Doc no período selecionado vs mesmo recorte do mês anterior (o card em si segue total)."""
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_devolvido_org_doc(protocolo_lexpre, a, b)
    )


def get_comparativo_devolvido_pendencia(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    """Devoluções p/ Pendências no período selecionado vs mesmo recorte do mês anterior (o card em si segue total)."""
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_devolvido_pendencia(protocolo_lexpre, a, b)
    )


def get_comparativo_tempo_medio_protocolado(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_protocoladas_para_comparativo(protocolo_lexpre)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS))
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_media_tempo_protocolado(_filter_saidas_by_date_range(saidas, a, b), entradas_por_demanda),
    )



def get_comparativo_mediana_tempo_protocolado(
    protocolo_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_protocoladas_para_comparativo(protocolo_lexpre)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS))
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_mediana_tempo_protocolado(_filter_saidas_by_date_range(saidas, a, b), entradas_por_demanda),
    )


# -----------------------------------------------------------------------------
# 6 - Agrupamentos (matéria, mês, dia, funcionário)
# -----------------------------------------------------------------------------

_MONTH_NAMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def group_protocolados_por_materia(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_represados_por_materia(protocolo_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados (setor atual = Protocolo, não cancelados/protocolados) agrupados por matéria — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    vistos: set = set()
    for row in protocolo_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PROTOCOLO_IDS or _is_cancelado(row) or _is_protocolado(row):
            continue
        vistos.add(demanda_id)
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_protocolados_por_mes(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in saidas_periodo:
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        month_key = f"{d.year}-{d.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {"name": f"{_MONTH_NAMES[d.month - 1]} {d.year}", "value": 0}
        grouped[month_key]["value"] += 1
    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_represados_por_mes(protocolo_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados agrupados pelo mês da última entrada no setor."""
    grouped: Dict[str, Dict[str, Any]] = {}
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS))
    vistos: set = set()
    for row in protocolo_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PROTOCOLO_IDS or _is_cancelado(row) or _is_protocolado(row):
            continue
        vistos.add(demanda_id)
        entradas = entradas_por_demanda.get(demanda_id) or []
        if not entradas:
            continue
        d = _to_date(entradas[-1].get("DATA"))
        if not d:
            continue
        month_key = f"{d.year}-{d.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {"name": f"{_MONTH_NAMES[d.month - 1]} {d.year}", "value": 0}
        grouped[month_key]["value"] += 1
    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_protocolados_por_dia(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        grouped[d.strftime("%Y-%m-%d")] += 1
    return [{"name": dia, "value": count} for dia, count in sorted(grouped.items())]


def get_protocolados_por_dia_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in saidas_periodo:
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        funcionario = _funcionario_responsavel(row, entradas_por_demanda)
        grouped[d.strftime("%Y-%m-%d")][funcionario] += 1
    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted({f for dia_data in grouped.values() for f in dia_data.keys()})
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {
        func: [{"name": dia, "value": grouped[dia].get(func, 0)} for dia in dias_ordenados]
        for func in funcionarios
    }
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}


def group_protocolados_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        grouped[_funcionario_responsavel(row, entradas_por_demanda)] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_represados_por_funcionario(protocolo_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados por funcionário responsável (última entrada no setor) — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS))
    vistos: set = set()
    for row in protocolo_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PROTOCOLO_IDS or _is_cancelado(row) or _is_protocolado(row):
            continue
        vistos.add(demanda_id)
        entradas = entradas_por_demanda.get(demanda_id) or []
        nome = _formatar_nome_funcionario(entradas[-1].get("FUNCIONARIO")) if entradas else "Sem funcionário"
        grouped[nome] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_media_protocolados_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in saidas_periodo:
        funcionario = _funcionario_responsavel(row, entradas_por_demanda)
        grouped[funcionario]["total"] += 1
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        if from_date and to_date:
            if from_date <= d <= to_date:
                grouped[funcionario]["dias"].add(d)
        else:
            grouped[funcionario]["dias"].add(d)

    result = []
    for funcionario, stats in grouped.items():
        dias = len(stats["dias"])
        if dias > 0:
            result.append({"name": funcionario, "value": round(stats["total"] / dias, 2)})
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_valor_causa_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Valor de causa por funcionário (das demandas protocoladas). Para matéria ANP usa DANO_MORAL."""
    grouped: Dict[str, float] = defaultdict(float)
    vistos: set = set()
    for row in saidas_periodo:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id in vistos:
            continue
        vistos.add(demanda_id)
        materia = _normalizar_materia(row.get("MATERIA")).upper()
        valor_raw = row.get("DANO_MORAL") if materia == "ANP" else row.get("VALOR_CAUSA")
        valor = _converter_valor(valor_raw)
        if valor <= 0:
            continue
        funcionario = _funcionario_responsavel(row, entradas_por_demanda)
        grouped[funcionario] += valor
    result = [{"name": nome, "value": round(valor, 2)} for nome, valor in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# -----------------------------------------------------------------------------
# 7 - Comissionamento (R$1,00 por protocolado — taxa fixa, sem valor de causa)
# -----------------------------------------------------------------------------

# R$ 1,00 por processo protocolado — mesma fórmula de protocolo.py (banco `ng`).
# Taxa fixa: o valor de causa não entra no cálculo (diferente de Org Doc, que usa
# R$0,60 × qtd × valor_causa/1M). "Protocolado" = mesmo critério de
# `_is_protocolado` (status Aguardando Despacho Inicial) — o banco `ng` usa
# STATUS em ("DISTRIBUÍDO", "PROTOCOLADO") e exclui reajuizamento; o lexpre não
# modela reajuizamento ainda, então não há essa exclusão aqui.
_VALOR_COMISSAO_POR_PROTOCOLADO = Decimal("1.00")


def get_comissionamento_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Comissão = R$ 1,00 × quantidade de demandas protocoladas no período, por
    funcionário responsável — mesma fórmula do dashboard antigo (protocolo.py,
    banco `ng`). `saidas_periodo` já deve vir filtrado para só as protocoladas
    (ver `_filtrar_protocolados_reais` + `_filter_saidas_by_date_range`), mesmo
    recorte usado no card "Protocolados" e no gráfico "Demandas por Funcionário".
    """
    linhas: List[Dict[str, Any]] = []
    for r in group_protocolados_por_funcionario(saidas_periodo, entradas_por_demanda):
        nome = r["name"]
        qtd = int(r["value"])
        comissao = (_VALOR_COMISSAO_POR_PROTOCOLADO * Decimal(qtd)).quantize(Decimal("0.01"))
        linhas.append({
            "funcionario": nome,
            "qtd_protocolados": qtd,
            "valor_comissao": float(comissao),
        })
    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# -----------------------------------------------------------------------------
# 8 - Exportação (relatório) — uma linha por demanda
# -----------------------------------------------------------------------------

_SITUACAO_PROTOCOLADO = "Protocolado"
_SITUACAO_REPRESADO = "Represado"
_SITUACAO_CANCELADO = "Cancelado"


def list_export_rows(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: date,
    to_date: date,
) -> List[Dict[str, Any]]:
    """
    Uma linha por demanda, para o relatório exportável: as protocoladas
    (status Aguardando Despacho Inicial) dentro do período selecionado, mais o
    backlog atual (represadas/canceladas ainda no setor), sempre total — mesmo
    recorte já usado nos cards do dashboard.
    """
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS))
    saidas = _saidas_setor(protocolo_lexpre, SETOR_PROTOCOLO_IDS)
    protocolados = _filtrar_protocolados_reais(saidas)
    protocolados_periodo = _filter_saidas_by_date_range(protocolados, from_date, to_date)

    linhas: List[Dict[str, Any]] = []
    vistos: set = set()
    for row in protocolados_periodo:
        demanda_id = row.get("ID_DEMANDA")
        vistos.add(demanda_id)
        entrada = _ultima_entrada_antes_de(demanda_id, _to_datetime(row.get("DATA")), entradas_por_demanda)
        linhas.append({
            "ID_DEMANDA": demanda_id,
            "NUMERO_PROCESSO": row.get("NUMERO_PROCESSO"),
            "CLIENTE_NOME": row.get("CLIENTE_NOME"),
            "MATERIA": _normalizar_materia(row.get("MATERIA")),
            "FUNCIONARIO": _funcionario_responsavel(row, entradas_por_demanda),
            "SITUACAO": _SITUACAO_PROTOCOLADO,
            "STATUS_DEMANDA": row.get("STATUS_DEMANDA") or "—",
            "SETOR_ATUAL_NOME": row.get("SETOR_ATUAL_NOME") or "—",
            "DATA_ENTRADA": _to_date(entrada.get("DATA")) if entrada else None,
            "DATA_SAIDA": _to_date(row.get("DATA")),
            "VALOR_CAUSA": _converter_valor(row.get("VALOR_CAUSA")),
            "DANO_MORAL": _converter_valor(row.get("DANO_MORAL")),
            "AREA_ATUACAO": row.get("AREA_ATUACAO_NOME"),
        })

    for row in protocolo_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PROTOCOLO_IDS:
            continue
        vistos.add(demanda_id)
        entradas = entradas_por_demanda.get(demanda_id) or []
        entrada = entradas[-1] if entradas else None
        linhas.append({
            "ID_DEMANDA": demanda_id,
            "NUMERO_PROCESSO": row.get("NUMERO_PROCESSO"),
            "CLIENTE_NOME": row.get("CLIENTE_NOME"),
            "MATERIA": _normalizar_materia(row.get("MATERIA")),
            "FUNCIONARIO": _formatar_nome_funcionario(entrada.get("FUNCIONARIO")) if entrada else "Sem funcionário",
            "SITUACAO": _SITUACAO_CANCELADO if _is_cancelado(row) else _SITUACAO_REPRESADO,
            "STATUS_DEMANDA": row.get("STATUS_DEMANDA") or "—",
            "SETOR_ATUAL_NOME": row.get("SETOR_ATUAL_NOME") or "—",
            "DATA_ENTRADA": _to_date(entrada.get("DATA")) if entrada else None,
            "DATA_SAIDA": None,
            "VALOR_CAUSA": _converter_valor(row.get("VALOR_CAUSA")),
            "DANO_MORAL": _converter_valor(row.get("DANO_MORAL")),
            "AREA_ATUACAO": row.get("AREA_ATUACAO_NOME"),
        })

    return linhas
