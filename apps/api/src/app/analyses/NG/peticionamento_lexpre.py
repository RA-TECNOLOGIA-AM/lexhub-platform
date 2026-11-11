# Análises e processamento de dados de PETICIONAMENTO NG (banco lexpre)
#
# Fonte: query "log_setor_demanda_lexpre_NG" (queries.py) — o mesmo log cru de
# entradas/saídas de setor usado por org_doc_lexpre.py, aqui recortado para o
# setor "Peticionamento" (public.setores.id = 4). Mesmo domínio de negócio do
# antigo "peticionamento" (banco `ng`, tabela peticionamento.peticionamento —
# uma linha por processo, com colunas ENTRADA/DATA_CONFECCAO/STATUS/FUNCIONARIO/
# MATERIA), mas orientado a EVENTOS: cada linha do log é uma entrada OU saída de
# uma demanda em um setor, não um processo.
#
# Mapeamento das colunas do dashboard antigo (NG, banco `ng`) para o novo (lexpre):
#   - DATA_CONFECCAO (data em que o processo foi confeccionado/saiu do setor)
#     -> evento TIPO="saida", SETOR_ID=4, cujo DESTINO (a entrada pareada pelo
#     mesmo movimentacao_id) é o Protocolo (setor 5) — ver `_saidas_setor` e
#     `_filtrar_peticionados_reais`. No sistema, uma demanda pode sair do
#     Peticionamento para QUALQUER setor, não só para o Protocolo: uma saída
#     para Pendências ou Organização de Documentos é a demanda sendo DEVOLVIDA
#     (algo precisa ser resolvido antes de prosseguir), não uma confecção
#     concluída — por isso só a saída com destino Protocolo conta como
#     "peticionado" (ver "Retorno Org Doc"/"Retorno Pendência" abaixo).
#   - ENTRADA (data em que o processo entrou no setor)   -> evento TIPO="entrada", SETOR_ID=4
#   - MATERIA (rubrica, com sufixo livre "X - banco")     -> rubricas.nome (já normalizado)
#   - FUNCIONARIO responsável pela confecção              -> responsável (setor_func) no
#     momento da ENTRADA no setor, propagado para a saída correspondente (mesmo
#     critério de org_doc_lexpre.py — as saídas observadas não carregam
#     responsavel_id preenchido).
#   - STATUS "PROTOCOLAR" (manual/automático)             -> demandas.pet_auto
#     (False = confeccionado manualmente, True = peticionado automaticamente)
#   - STATUS "REVISÃO"                                    -> não existe no lexpre ainda;
#     o card "Revisão" do dashboard antigo não tem equivalente aqui (mantido na UI
#     como placeholder zerado, a definir).
#   - REAJUIZAMENTO                                        -> não existe no lexpre ainda;
#     os cards "Resolvidos/Não Resolvidos Reajuizamento" não têm equivalente aqui.
#   - "Retorno Org Doc" (devolução do setor para Organização de Documentos)
#     -> evento de saída do setor 4 cujo destino (movimentação pareada) é
#     Organização de Documentos (id=3) — ver `get_retorno_org_doc`.
#   - "Retorno Pendência" (devolução do setor para Pendências)
#     -> evento de saída do setor 4 cujo destino (movimentação pareada) é
#     Pendências (id=2) — ver `get_retorno_pendencia`.
#   - "Não Peticionados" (represados, sem filtro de período)
#     -> demandas (não canceladas) cujo setor_id ATUAL (demandas.setor_id, não o
#     evento de log) é 4.
#
# Comissionamento: mesma fórmula por faixas do dashboard antigo (peticionamento.py,
# banco `ng`) — ações de Massa (R$0,50/1,50/3,00) e ESPECÍFICA (R$7/13/20) por
# faixa de "taxa de resolução" do funcionário (peticionados / (peticionados +
# represados) no recorte GERAL, sem filtro de matéria). ESPECÍFICA é identificada
# pela rubrica "ESPECÍFICA" ou pela operação (rubricas.operacao_id) "Administrativo"
# (public.operacao.id = 2 no lexpre) — mesmo critério usado em comercial_lexpre.py.
# Ajuste de 04/09/2026 (mesmo critério de org_doc_lexpre.py): o numerador da taxa
# de resolução só conta demandas que de fato chegaram a ser protocoladas (status
# Aguardando Despacho Inicial), não qualquer demanda "peticionada" (destino
# Protocolo, sem garantia de que chegou a ser protocolada de fato) — ver
# `_is_protocolado`.
# Ajuste de 01/10/2026 (pedido do usuário): a quantidade PAGA (Qtd Massa/
# Específica, base do "Qtd x Valor") também passou a exigir protocolado de fato
# (antes contava qualquer confecção manual não cancelada, independente de ter
# protocolado) — e o PERÍODO que determina em qual relatório essa quantidade
# entra passou a ser a DATA_PROTOCOLO, não mais a data de saída do
# Peticionamento (ver `_filter_saidas_by_protocolo_date_range`). A TAXA de
# resolução (que define a faixa de preço) continua ancorada na data de saída,
# sem mudança.

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

# "Cancelado" em public.status (lexpre) — mesma constante de comercial_lexpre.py / protocolo_lexpre.py.
STATUS_DEMANDA_CANCELADO_ID = 10

# "Aguardando Despacho Inicial" em public.status (lexpre) — mesmo critério de "protocolado"
# usado em org_doc_lexpre.py / protocolo_setor_lexpre.py. Usado aqui só na taxa de
# resolução do comissionamento (ver `_is_protocolado` / `get_comissionamento_por_funcionario`) —
# decisão de 04/09/2026 de a taxa só contar demandas que passaram pelo Peticionamento e de
# fato chegaram a ser protocoladas, não qualquer demanda "peticionada" (que só exige ter
# saído rumo ao Protocolo, sem garantia de que o processo chegue a ser protocolado de fato).
STATUS_AG_DESPACHO_INICIAL_ID = 13

# "Administrativo" em public.operacao (lexpre) — rubricas dessa operação usam a
# tabela de comissão ESPECÍFICA, mesmo critério de peticionamento.py (banco `ng`).
OPERACAO_ADMINISTRATIVO_ID = 2


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

def filter_peticionamento_lexpre_por_escritorio(
    peticionamento_lexpre: List[Dict[str, Any]],
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Restringe ao escritório informado — a query traz todos (NGAM/LAAM/LARJ) sem filtro."""
    return [row for row in peticionamento_lexpre or [] if row.get("ESCRITORIO_ID") == escritorio_id]


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
    """
    Demanda de fato chegou a ser protocolada (status atual == "Aguardando Despacho
    Inicial") — critério mais estrito que "peticionado" (que só exige ter saído do
    Peticionamento rumo ao Protocolo). Usado só na taxa de resolução do
    comissionamento: uma demanda pode "sair peticionada" do setor e nunca chegar a
    ser protocolada de fato (parada no Protocolo, cancelada depois, etc.).
    """
    return row.get("STATUS_DEMANDA_ID") == STATUS_AG_DESPACHO_INICIAL_ID


def _indexar_movimentacoes(peticionamento_lexpre: List[Dict[str, Any]]) -> Dict[Any, Dict[str, Dict[str, Any]]]:
    """
    ``movimentacao_id -> {"entrada": linha, "saida": linha}``, a partir do universo
    COMPLETO de eventos (todos os setores) — permite descobrir de/para qual setor
    uma demanda veio/foi a partir de um evento isolado no setor 4. Mesmo mecanismo
    de org_doc_lexpre.py.
    """
    idx: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in peticionamento_lexpre or []:
        mov_id = row.get("MOVIMENTACAO_ID")
        tipo = row.get("TIPO")
        if mov_id is None or tipo not in ("entrada", "saida"):
            continue
        idx[mov_id][tipo] = row
    return idx


def _setor_origem(entrada_row: Dict[str, Any], idx: Dict[Any, Dict[str, Dict[str, Any]]]) -> Optional[int]:
    """Setor do qual a demanda veio, para um evento de ``entrada`` — ``None`` se for a primeira movimentação."""
    par = idx.get(entrada_row.get("MOVIMENTACAO_ID"), {})
    saida_par = par.get("saida")
    return saida_par.get("SETOR_ID") if saida_par else None


def _setor_destino(saida_row: Dict[str, Any], idx: Dict[Any, Dict[str, Dict[str, Any]]]) -> Optional[int]:
    """Setor para o qual a demanda foi, para um evento de ``saida`` — ``None`` se não houver entrada pareada (ex.: cancelamento)."""
    par = idx.get(saida_row.get("MOVIMENTACAO_ID"), {})
    entrada_par = par.get("entrada")
    return entrada_par.get("SETOR_ID") if entrada_par else None


def _entradas_setor(peticionamento_lexpre: List[Dict[str, Any]], setor_ids: set) -> List[Dict[str, Any]]:
    return [
        row for row in peticionamento_lexpre or []
        if row.get("SETOR_ID") in setor_ids and row.get("TIPO") == "entrada"
    ]


def _saidas_setor(peticionamento_lexpre: List[Dict[str, Any]], setor_ids: set) -> List[Dict[str, Any]]:
    """
    Última saída do setor, uma por demanda.

    Uma demanda pode sair do setor mais de uma vez (ex.: vai para Pendências e
    depois retorna, ficando represada de novo, até finalmente sair outra vez) —
    cada ida gera seu próprio evento de saída em ``log_setor_demanda``. Sem essa
    deduplicação, uma mesma demanda contaria como "peticionada" uma vez por saída,
    inflando o volume e o comissionamento. Mesma lógica de org_doc_lexpre.py.

    Demandas cujo setor ATUAL (``SETOR_ATUAL_ID``, valor vivo de ``demandas``) é de
    novo o setor informado são excluídas por completo: a última saída registrada
    não foi final — a demanda voltou e está represada outra vez (contabilizada só
    em `get_represados`, nunca simultaneamente como peticionada).
    """
    ultima_por_demanda: Dict[Any, Dict[str, Any]] = {}
    for row in peticionamento_lexpre or []:
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


def _filtrar_peticionados_reais(
    saidas: List[Dict[str, Any]],
    idx: Dict[Any, Dict[str, Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    De ``_saidas_setor`` (última saída por demanda), mantém só as que de fato
    confeccionaram a demanda — destino Protocolo (setor 5).

    No sistema, uma saída do Peticionamento pode ir para QUALQUER setor: uma
    saída para Pendências ou Organização de Documentos é a demanda sendo
    DEVOLVIDA (algo precisa ser resolvido antes de prosseguir), não uma
    confecção concluída. Sem esse filtro, uma devolução contaria erroneamente
    como "peticionada" — ver `get_retorno_org_doc` / `get_retorno_pendencia`
    para essas devoluções.
    """
    return [row for row in saidas if _setor_destino(row, idx) in SETOR_PROTOCOLO_IDS]


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


def _filter_saidas_by_protocolo_date_range(
    saidas: List[Dict[str, Any]], from_date: date, to_date: date
) -> List[Dict[str, Any]]:
    """
    Mesmo princípio de `_filter_saidas_by_date_range`, mas ancorado em
    DATA_PROTOCOLO em vez de DATA (saída/peticionamento) — usado só pra base de
    pagamento da comissão (ver `get_comissionamento_por_funcionario`), que paga
    pela quantidade PROTOCOLADA no período, não pela peticionada. Isso evita que
    uma ação peticionada perto do fim de um período, que só protocola depois,
    fique sem nunca entrar em nenhum relatório de comissão (ajuste de
    01/10/2026, pedido do usuário). Os outros cards do dashboard (Total
    Peticionados, Cancelados, Produção Diária, etc.) continuam usando
    `_filter_saidas_by_date_range` (ancorado em DATA) — essa função é exclusiva
    da base de pagamento.
    """
    filtered = []
    for row in saidas:
        d = _to_date(row.get("DATA_PROTOCOLO"))
        if d and from_date <= d <= to_date:
            filtered.append(row)
    return filtered


# -----------------------------------------------------------------------------
# 2 - Filtros da página (matéria / funcionário / área de atuação)
# -----------------------------------------------------------------------------

def filter_peticionamento_lexpre_por_materia(
    peticionamento_lexpre: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(peticionamento_lexpre)
    return [row for row in peticionamento_lexpre if _normalizar_materia(row.get("MATERIA")) in alvos]


def filter_peticionamento_lexpre_por_area_atuacao(
    peticionamento_lexpre: List[Dict[str, Any]],
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe pela área de atuação real (``public.area_atuacao``, via ``operacao.area_atuacao_id``) — ver comercial_lexpre.filter_comercial_lexpre_por_area_atuacao."""
    alvos = normalizar_filtro_ids(area_atuacao_id)
    if not alvos:
        return list(peticionamento_lexpre)
    return [row for row in peticionamento_lexpre if row.get("AREA_ATUACAO_ID") in alvos]


def filter_peticionamento_lexpre_por_area_atuacao_nome(
    peticionamento_lexpre: List[Dict[str, Any]],
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
        return list(peticionamento_lexpre)
    return [
        row for row in peticionamento_lexpre
        if str(row.get("AREA_ATUACAO_NOME") or "").strip().upper() in alvos
    ]


def filter_peticionamento_lexpre_por_uf(
    peticionamento_lexpre: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe às demandas cujo cliente (``customer.uf``) é da UF informada. ``None`` = sem filtro. Catálogo de UFs compartilhado — ver `comercial_lexpre.list_ufs_comerciais`."""
    alvos = normalizar_filtro_textos(uf)
    if not alvos:
        return list(peticionamento_lexpre)
    return [row for row in peticionamento_lexpre if str(row.get("UF") or "").strip().upper() in alvos]


def list_funcionarios_peticionamento_lexpre(peticionamento_lexpre: List[Dict[str, Any]]) -> List[str]:
    """Funcionários que aparecem como responsáveis por uma entrada no setor, no recorte atual."""
    vistos: set = set()
    saida: List[str] = []
    for row in _entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS):
        nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        if nome == "Sem funcionário" or nome in vistos:
            continue
        vistos.add(nome)
        saida.append(nome)
    return sorted(saida, key=lambda x: x.lower())


def filter_peticionamento_lexpre_por_funcionarios(
    peticionamento_lexpre: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe às demandas cujo responsável (na última entrada no setor) é um dos
    funcionários informados (união — OR). Filtra por DEMANDA, não por evento
    isolado — mesmo critério de org_doc_lexpre.py.
    """
    if not funcionarios:
        return list(peticionamento_lexpre)
    alvos = {_formatar_nome_funcionario(f) for f in funcionarios if f is not None and str(f).strip()}
    if not alvos:
        return list(peticionamento_lexpre)

    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS))

    demandas_alvo: set = set()
    for row in peticionamento_lexpre:
        if row.get("SETOR_ID") not in SETOR_PETICIONAMENTO_IDS:
            continue
        if row.get("TIPO") == "entrada":
            nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        else:
            nome = _funcionario_responsavel(row, entradas_por_demanda)
        if nome in alvos:
            demandas_alvo.add(row.get("ID_DEMANDA"))

    return [row for row in peticionamento_lexpre if row.get("ID_DEMANDA") in demandas_alvo]


# -----------------------------------------------------------------------------
# 3 - KPIs do período (base: saídas do setor 4, por DATA da saída)
# -----------------------------------------------------------------------------

def get_total_peticionados(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if not _is_cancelado(row)])


def get_peticionados_manualmente(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if not _is_cancelado(row) and row.get("PET_AUTO") is False])


def get_peticionados_automaticamente(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if not _is_cancelado(row) and row.get("PET_AUTO") is True])


def get_cancelados(saidas_todas_periodo: List[Dict[str, Any]]) -> int:
    """
    Demandas canceladas que saíram do setor no período. Usa `saidas_todas_periodo`
    (sem o filtro de destino Protocolo), não `saidas_periodo`: uma demanda
    cancelada não tem destino pareado (`_setor_destino` retorna None) e seria
    descartada por `_filtrar_peticionados_reais` antes mesmo de ser contada.
    """
    return len([row for row in saidas_todas_periodo if _is_cancelado(row)])


def get_protocolados_total(saidas_protocoladas_periodo: List[Dict[str, Any]]) -> int:
    """
    Quantas demandas que passaram pelo Peticionamento de fato protocolaram
    DENTRO do período selecionado — critério: DATA_PROTOCOLO preenchida e
    dentro do período (``saidas_protocoladas_periodo``, ver
    `_filter_saidas_by_protocolo_date_range`) e status atual "Aguardando
    Despacho Inicial" (`_is_protocolado`). Mesmo critério usado na comissão
    (ver `get_comissionamento_por_funcionario`).

    Ajuste de 07/10/2026 (pedido do usuário, mesma correção de
    `org_doc_lexpre.get_protocolados_total`): antes contava, entre as
    confeccionadas no período (``saidas_periodo``, por DATA de saída), quantas
    JÁ ESTÃO protocoladas hoje — número que só cresce (ou oscila) com o tempo,
    sem relação com o período escolhido.
    """
    return len([row for row in saidas_protocoladas_periodo if not _is_cancelado(row) and _is_protocolado(row)])


def get_represados(peticionamento_lexpre: List[Dict[str, Any]]) -> int:
    """
    Demandas (não canceladas) atualmente no setor de Peticionamento — valor
    sempre total, sem filtro de período, mesmo critério de "Não Peticionados" no
    dashboard antigo. Deduplicado por ID_DEMANDA.
    """
    vistos: set = set()
    for row in peticionamento_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PETICIONAMENTO_IDS:
            continue
        if _is_cancelado(row):
            continue
        vistos.add(demanda_id)
    return len(vistos)


def get_retorno_org_doc(
    peticionamento_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Demandas devolvidas do Peticionamento para Organização de Documentos — a
    confecção foi interrompida porque a documentação precisava ser reorganizada.
    Conta eventos de saída (não deduplicados: cada devolução conta como um
    evento), sem datas = valor sempre total (o que o card exibe);
    com datas = só devoluções cuja DATA cai no intervalo (base do comparativo).
    """
    idx = _indexar_movimentacoes(peticionamento_lexpre)
    saidas_brutas = [
        row for row in peticionamento_lexpre or []
        if row.get("SETOR_ID") in SETOR_PETICIONAMENTO_IDS and row.get("TIPO") == "saida"
    ]
    if from_date and to_date:
        saidas_brutas = _filter_saidas_by_date_range(saidas_brutas, from_date, to_date)
    return len([row for row in saidas_brutas if _setor_destino(row, idx) in SETOR_ORG_DOC_IDS])


def get_retorno_pendencia(
    peticionamento_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Demandas devolvidas do Peticionamento para Pendências — surgiu uma
    pendência a resolver antes de a confecção prosseguir. Conta eventos de
    saída (não deduplicados), sem datas = valor sempre total (o que o card exibe);
    com datas = só devoluções cuja DATA cai no intervalo (base do comparativo).
    """
    idx = _indexar_movimentacoes(peticionamento_lexpre)
    saidas_brutas = [
        row for row in peticionamento_lexpre or []
        if row.get("SETOR_ID") in SETOR_PETICIONAMENTO_IDS and row.get("TIPO") == "saida"
    ]
    if from_date and to_date:
        saidas_brutas = _filter_saidas_by_date_range(saidas_brutas, from_date, to_date)
    return len([row for row in saidas_brutas if _setor_destino(row, idx) in SETOR_PENDENCIAS_IDS])


def get_valor_causa_confeccionado(saidas_periodo: List[Dict[str, Any]]) -> float:
    """Soma do valor de causa das demandas confeccionadas (peticionadas, não canceladas) no período."""
    total = 0.0
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        materia = _normalizar_materia(row.get("MATERIA")).upper()
        valor_raw = row.get("DANO_MORAL") if materia == "ANP" else row.get("VALOR_CAUSA")
        valor = _converter_valor(valor_raw)
        if valor > 0:
            total += valor
    return round(total, 2)


def get_ticket_medio_confeccionado(saidas_periodo: List[Dict[str, Any]]) -> float:
    """Valor de causa confeccionado médio por demanda peticionada no período."""
    qtd = get_total_peticionados(saidas_periodo)
    if qtd == 0:
        return 0.0
    return round(get_valor_causa_confeccionado(saidas_periodo) / qtd, 2)


# -----------------------------------------------------------------------------
# 4 - Tempo de confecção (entrada -> saída no setor 4)
# -----------------------------------------------------------------------------

def _extrair_duracoes_horas(
    saidas: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[float]:
    duracoes: List[float] = []
    for row in saidas:
        if _is_cancelado(row):
            continue
        saida_dt = _to_datetime(row.get("DATA"))
        entrada = _ultima_entrada_antes_de(row.get("ID_DEMANDA"), saida_dt, entradas_por_demanda)
        entrada_dt = _to_datetime(entrada.get("DATA")) if entrada else None
        if not saida_dt or not entrada_dt:
            continue
        horas = (saida_dt - entrada_dt).total_seconds() / 3600
        if horas > 0:
            duracoes.append(horas)
    return duracoes


def get_media_tempo_peticionado(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> float:
    """Média de dias entre entrada e saída no setor, para saídas do período (não canceladas)."""
    duracoes_horas = _extrair_duracoes_horas(saidas_periodo, entradas_por_demanda)
    if not duracoes_horas:
        return 0.0
    return round((sum(duracoes_horas) / len(duracoes_horas)) / 24, 2)


def get_mediana_tempo_peticionado(
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


def _saidas_reais_para_comparativo(peticionamento_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """``_saidas_setor`` já filtrada para destino Protocolo — mesma base usada nos stats do período (ver `_filtrar_peticionados_reais`)."""
    idx = _indexar_movimentacoes(peticionamento_lexpre)
    saidas = _saidas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS)
    return _filtrar_peticionados_reais(saidas, idx)


def get_comparativo_total_peticionados(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_total_peticionados(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_peticionados_manualmente(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_peticionados_manualmente(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_peticionados_automaticamente(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_peticionados_automaticamente(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_cancelados(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    # Cancelamento não tem entrada pareada em outro setor (destino sempre None),
    # então usa as saídas SEM o filtro de destino de `_saidas_reais_para_comparativo`
    # — senão todo cancelamento seria descartado antes mesmo de ser contado.
    saidas = _saidas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_cancelados(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_protocolados_total(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_protocolados_total(_filter_saidas_by_protocolo_date_range(saidas, a, b))
    )


def get_comparativo_valor_causa_confeccionado(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_valor_causa_confeccionado(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_ticket_medio_confeccionado(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_ticket_medio_confeccionado(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_retorno_org_doc(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    """Devoluções p/ Org Doc no período selecionado vs mesmo recorte do mês anterior (o card em si segue total)."""
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_retorno_org_doc(peticionamento_lexpre, a, b)
    )


def get_comparativo_retorno_pendencia(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    """Devoluções p/ Pendências no período selecionado vs mesmo recorte do mês anterior (o card em si segue total)."""
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_retorno_pendencia(peticionamento_lexpre, a, b)
    )


def get_comparativo_tempo_medio_peticionado(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS))
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_media_tempo_peticionado(_filter_saidas_by_date_range(saidas, a, b), entradas_por_demanda),
    )



def get_comparativo_mediana_tempo_peticionado(
    peticionamento_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(peticionamento_lexpre)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS))
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_mediana_tempo_peticionado(_filter_saidas_by_date_range(saidas, a, b), entradas_por_demanda),
    )


# -----------------------------------------------------------------------------
# 6 - Agrupamentos (matéria, mês, dia, funcionário)
# -----------------------------------------------------------------------------

_MONTH_NAMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def group_peticionados_por_materia(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_protocolados_por_materia(saidas_protocoladas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Por matéria, das demandas que passaram pelo Peticionamento, quantas de fato
    protocolaram DENTRO do período selecionado (``saidas_protocoladas_periodo``,
    ancorado em DATA_PROTOCOLO — ver `_filter_saidas_by_protocolo_date_range`).
    Exibido ao lado de "Peticionados por Matéria" no gráfico "Top 10 –
    Peticionados por Matéria" (visão de funil/conversão por matéria).

    Ajuste de 07/10/2026 (pedido do usuário): antes usava ``saidas_periodo``
    (DATA de peticionamento) + status atual, sem olhar DATA_PROTOCOLO — mesmo
    critério simples que `get_protocolados_por_funcionario` usava ANTES do
    ajuste de 01/10/2026. Agora usa o mesmo critério estrito da comissão (ver
    `get_comissionamento_por_funcionario`); por isso o resultado NÃO é mais
    necessariamente ≤ `group_peticionados_por_materia` do mesmo período (uma
    demanda pode ter peticionado num mês e protocolado em outro).
    """
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_protocoladas_periodo:
        if _is_cancelado(row):
            continue
        if not _is_protocolado(row):
            continue
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_represados_por_materia(peticionamento_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados (setor atual = Peticionamento, não cancelados) agrupados por matéria — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    vistos: set = set()
    for row in peticionamento_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PETICIONAMENTO_IDS or _is_cancelado(row):
            continue
        vistos.add(demanda_id)
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_peticionados_por_mes(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        month_key = f"{d.year}-{d.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {"name": f"{_MONTH_NAMES[d.month - 1]} {d.year}", "value": 0}
        grouped[month_key]["value"] += 1
    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_represados_por_mes(peticionamento_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados agrupados pelo mês da última entrada no setor."""
    grouped: Dict[str, Dict[str, Any]] = {}
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS))
    vistos: set = set()
    for row in peticionamento_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PETICIONAMENTO_IDS or _is_cancelado(row):
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


def group_peticionados_por_dia(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        grouped[d.strftime("%Y-%m-%d")] += 1
    return [{"name": dia, "value": count} for dia, count in sorted(grouped.items())]


def get_peticionados_por_dia_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
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


def group_peticionados_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        grouped[_funcionario_responsavel(row, entradas_por_demanda)] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_protocolados_por_funcionario(
    saidas_protocoladas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Quantidade, por funcionário, de ações MANUAIS que de fato protocolaram
    dentro do período selecionado (por DATA_PROTOCOLO) — usado no gráfico
    "Demandas por Funcionário" e na página de comissionamento.

    Ajuste de 01/10/2026 (pedido do usuário): antes contava qualquer ação
    (manual OU automática) peticionada no período cujo status ATUAL já fosse
    terminal, sem olhar a data de protocolo — por isso divergia do relatório
    de comissão (que só paga ações manuais protocoladas dentro do período).
    Agora usa EXATAMENTE o mesmo critério da comissão (`saidas_protocoladas_periodo`,
    ver `_filter_saidas_by_protocolo_date_range`, mais `PET_AUTO is False`), pra
    os dois números baterem. Isso quebra a garantia de que esse valor é sempre
    ≤ `group_peticionados_por_funcionario` do mesmo período (que ainda conta
    manual+automático por data de peticionamento) — o frontend já usa
    ``Math.max(0, ...)`` ao empilhar os dois no gráfico, então o caso raro de
    "mais protocolado que peticionado no mesmo recorte" só zera a fatia
    "Peticionados" do funcionário em vez de dar um valor negativo.
    """
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_protocoladas_periodo:
        if _is_cancelado(row):
            continue
        if row.get("PET_AUTO") is not False:
            continue
        if not _is_protocolado(row):
            continue
        grouped[_funcionario_responsavel(row, entradas_por_demanda)] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_represados_por_funcionario(peticionamento_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados por funcionário responsável (última entrada no setor) — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS))
    vistos: set = set()
    for row in peticionamento_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PETICIONAMENTO_IDS or _is_cancelado(row):
            continue
        vistos.add(demanda_id)
        entradas = entradas_por_demanda.get(demanda_id) or []
        nome = _formatar_nome_funcionario(entradas[-1].get("FUNCIONARIO")) if entradas else "Sem funcionário"
        grouped[nome] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_media_peticionado_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
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
    """Valor de causa por funcionário (das saídas confeccionadas). Para matéria ANP usa DANO_MORAL."""
    grouped: Dict[str, float] = defaultdict(float)
    vistos: set = set()
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
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


def get_valor_causa_protocolado_por_funcionario(
    saidas_protocoladas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Valor de causa por funcionário (mesmo recorte de `get_valor_causa_por_funcionario`),
    restrito às demandas que de fato protocolaram DENTRO do período selecionado
    (``saidas_protocoladas_periodo``, ancorado em DATA_PROTOCOLO — ver
    `_filter_saidas_by_protocolo_date_range`) e status atual "Aguardando
    Despacho Inicial" (`_is_protocolado`). Usado no gráfico "Valor de Causa por
    Funcionário" (junto com `get_valor_causa_por_funcionario`, para separar a
    fatia protocolada da não protocolada em layout empilhado) e no
    comissionamento.

    Ajuste de 07/10/2026 (pedido do usuário): antes recebia ``saidas_periodo``
    (DATA de peticionamento), sem exigir que a DATA_PROTOCOLO também caísse no
    período — inconsistente com `get_protocolados_por_funcionario` (já corrigido
    em 01/10/2026), que é exatamente o equivalente em quantidade.
    """
    grouped: Dict[str, float] = defaultdict(float)
    vistos: set = set()
    for row in saidas_protocoladas_periodo:
        if _is_cancelado(row):
            continue
        if not _is_protocolado(row):
            continue
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
# 7 - Comissionamento (apenas confecções manuais concluídas)
# -----------------------------------------------------------------------------

def _materia_e_especifica(materia_raw: Any) -> bool:
    """True quando a matéria é ESPECÍFICA (aceita com ou sem acento)."""
    s = str(materia_raw or "").strip().upper()
    return s in ("ESPECIFICA", "ESPECÍFICA")


def _elegivel_tabela_especifica(row: Dict[str, Any]) -> bool:
    """
    True quando a peça deve usar a tabela de comissão ESPECÍFICA (R$7/13/20):
    rubrica ESPECÍFICA, ou rubrica cuja operação é "Administrativo" (ex.:
    progressões e gratificações de servidor público) — mesma lógica do dashboard
    antigo (peticionamento.py, banco `ng`).
    """
    if _materia_e_especifica(row.get("MATERIA")):
        return True
    return row.get("OPERACAO_ID") == OPERACAO_ADMINISTRATIVO_ID


def get_taxa_resolvidos(qtd_peticionados: int, qtd_represados: int) -> Optional[float]:
    """% de demandas peticionadas em relação ao total (peticionadas + represadas) — não é filtrado por matéria."""
    total = qtd_peticionados + qtd_represados
    if total == 0:
        return None
    return round((qtd_peticionados / total) * 100, 2)


_PRECO_MASSA_FAIXAS: tuple[tuple[float, Decimal], ...] = (
    (98, Decimal("3.00")),
    (85, Decimal("1.50")),
    (70, Decimal("0.50")),
)
_PRECO_ESPECIFICA_FAIXAS: tuple[tuple[float, Decimal], ...] = (
    (95, Decimal("20.00")),
    (85, Decimal("13.00")),
    (50, Decimal("7.00")),
)


def _preco_unitario(taxa: Optional[float], faixas: tuple[tuple[float, Decimal], ...]) -> Decimal:
    if taxa is None:
        return Decimal("0")
    for limiar, preco in faixas:
        if taxa >= limiar:
            return preco
    return Decimal("0")


def get_comissionamento_por_funcionario(
    saidas_protocoladas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
    saidas_periodo_geral: List[Dict[str, Any]],
    entradas_por_demanda_geral: Dict[Any, List[Dict[str, Any]]],
    represados_por_funcionario_geral: Dict[str, int],
) -> List[Dict[str, Any]]:
    """
    Comissão só sobre confecções manuais (não canceladas, pet_auto=falso) que de
    fato PROTOCOLARAM.

    Ajuste de 01/10/2026 (pedido do usuário): o valor pago (Qtd Massa/Específica
    × preço unitário) agora é calculado sobre ``saidas_protocoladas_periodo`` —
    ações cuja DATA_PROTOCOLO caiu no período selecionado (ver
    `_filter_saidas_by_protocolo_date_range`), não mais sobre qualquer ação
    peticionada no período independente de ter protocolado. Uma ação peticionada
    num mês mas só protocolada no mês seguinte passa a ser paga no mês em que ela
    REALMENTE protocolou — antes disso, ela era paga no mês em que foi só
    peticionada, mesmo sem garantia de que chegaria a protocolar de fato.

    Por funcionário: conta ações de Massa vs ESPECÍFICA (respeitando o filtro de
    matéria da página) e aplica o valor unitário conforme a faixa de
    `get_taxa_resolvidos` do funcionário — mas essa taxa é sempre calculada no
    recorte GERAL (``saidas_periodo_geral``, ``represados_por_funcionario_geral``,
    sem filtro de matéria, AINDA ancorado em DATA/peticionamento — não mudou),
    pelo mesmo motivo do dashboard antigo: a faixa de comissão reflete a
    produtividade geral do funcionário, não só a fatia filtrada.

    Decisão de 04/09/2026 (mesmo critério de org_doc_lexpre.py): a taxa de
    resolução só conta, no numerador, demandas que passaram pelo Peticionamento
    E de fato chegaram a ser protocoladas (status Aguardando Despacho Inicial) —
    não qualquer demanda "peticionada" (que só exige ter saído rumo ao
    Protocolo). Essa parte (a TAXA, que define a faixa de preço) não mudou no
    ajuste de 01/10/2026 — só a quantidade paga (``contagem``) passou a exigir
    protocolado também.

    Massa: R$ 0,50 / 1,50 / 3,00 nas faixas 70% / 85% / 98%.
    ESPECÍFICA: R$ 7 / 13 / 20 nas faixas 50% / 85% / 95%.
    """
    manual = [
        row for row in saidas_protocoladas_periodo
        if not _is_cancelado(row) and row.get("PET_AUTO") is False and _is_protocolado(row)
    ]

    contagem: Dict[str, Dict[str, int]] = defaultdict(lambda: {"massa": 0, "especifica": 0})
    for row in manual:
        nome = _funcionario_responsavel(row, entradas_por_demanda)
        if _elegivel_tabela_especifica(row):
            contagem[nome]["especifica"] += 1
        else:
            contagem[nome]["massa"] += 1

    # Numerador da taxa: só demandas que passaram pelo Peticionamento e de fato
    # chegaram a ser protocoladas (ver docstring acima).
    peticionados_geral_por_funcionario: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo_geral:
        if _is_cancelado(row):
            continue
        if not _is_protocolado(row):
            continue
        nome = _funcionario_responsavel(row, entradas_por_demanda_geral)
        peticionados_geral_por_funcionario[nome] += 1

    linhas: List[Dict[str, Any]] = []
    for nome in sorted(contagem.keys()):
        massa = contagem[nome]["massa"]
        especifica = contagem[nome]["especifica"]
        if massa == 0 and especifica == 0:
            continue

        taxa = get_taxa_resolvidos(
            peticionados_geral_por_funcionario.get(nome, 0),
            represados_por_funcionario_geral.get(nome, 0),
        )
        preco_massa = _preco_unitario(taxa, _PRECO_MASSA_FAIXAS)
        preco_especifica = _preco_unitario(taxa, _PRECO_ESPECIFICA_FAIXAS)
        sub_massa = (Decimal(massa) * preco_massa).quantize(Decimal("0.01"))
        sub_especifica = (Decimal(especifica) * preco_especifica).quantize(Decimal("0.01"))
        total = (sub_massa + sub_especifica).quantize(Decimal("0.01"))

        linhas.append({
            "funcionario": nome,
            "qtd_acoes_massa": massa,
            "valor_acoes_massa": float(preco_massa),
            "qtd_x_valor_massa": float(sub_massa),
            "qtd_acoes_especificas": especifica,
            "valor_acoes_especificas": float(preco_especifica),
            "qtd_x_valor_especificas": float(sub_especifica),
            "taxa_resolvidos": taxa,
            "valor_comissao": float(total),
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# -----------------------------------------------------------------------------
# 8 - Exportação (relatório) — uma linha por demanda
# -----------------------------------------------------------------------------

_SITUACAO_CONFECCIONADO_MANUAL = "Confeccionado (manual)"
_SITUACAO_CONFECCIONADO_AUTOMATICO = "Confeccionado (automático)"
_SITUACAO_REPRESADO = "Represado"
_SITUACAO_CANCELADO = "Cancelado"

_EXPORT_DESTINO_NOMES = {
    **{sid: "Organização de Documentos" for sid in SETOR_ORG_DOC_IDS},
    **{sid: "Pendências" for sid in SETOR_PENDENCIAS_IDS},
    **{sid: "Protocolo" for sid in SETOR_PROTOCOLO_IDS},
}


def _linha_export_saida(
    row: Dict[str, Any],
    idx: Dict[Any, Dict[str, Dict[str, Any]]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    demanda_id = row.get("ID_DEMANDA")
    entrada = _ultima_entrada_antes_de(demanda_id, _to_datetime(row.get("DATA")), entradas_por_demanda)
    if _is_cancelado(row):
        situacao = _SITUACAO_CANCELADO
    elif row.get("PET_AUTO") is True:
        situacao = _SITUACAO_CONFECCIONADO_AUTOMATICO
    else:
        situacao = _SITUACAO_CONFECCIONADO_MANUAL
    return {
        "ID_DEMANDA": demanda_id,
        "NUMERO_PROCESSO": row.get("NUMERO_PROCESSO"),
        "CLIENTE_NOME": row.get("CLIENTE_NOME"),
        "MATERIA": _normalizar_materia(row.get("MATERIA")),
        "FUNCIONARIO": _funcionario_responsavel(row, entradas_por_demanda),
        "SITUACAO": situacao,
        "STATUS_DEMANDA": row.get("STATUS_DEMANDA") or "—",
        "SETOR_ATUAL_NOME": row.get("SETOR_ATUAL_NOME") or "—",
        "DESTINO": _EXPORT_DESTINO_NOMES.get(_setor_destino(row, idx), "—"),
        "DATA_ENTRADA": _to_date(entrada.get("DATA")) if entrada else None,
        "DATA_SAIDA": _to_date(row.get("DATA")),
        "DATA_PROTOCOLO": _to_date(row.get("DATA_PROTOCOLO")),
        "VALOR_CAUSA": _converter_valor(row.get("VALOR_CAUSA")),
        "DANO_MORAL": _converter_valor(row.get("DANO_MORAL")),
        "AREA_ATUACAO": row.get("AREA_ATUACAO_NOME"),
    }


def list_export_rows(
    peticionamento_lexpre: List[Dict[str, Any]],
    from_date: date,
    to_date: date,
) -> List[Dict[str, Any]]:
    """
    Uma linha por demanda, para o relatório exportável: as que saíram do setor
    (confeccionadas manual/automaticamente ou canceladas) OU que protocolaram
    dentro do período selecionado (``DATA_SAIDA`` ou ``DATA_PROTOCOLO`` — nunca
    as duas juntas para a mesma demanda), mais o backlog atual (represadas
    ainda no setor), sempre total.

    Uma demanda pode ser peticionada num mês e só protocolar no seguinte — sem
    o critério por ``DATA_PROTOCOLO`` ela não apareceria em NENHUM relatório
    mensal, mesmo contando no comissionamento do mês em que protocolou de fato
    (ajuste de 28/10/2026, pedido do usuário — mesmo caso do Org Doc, ver
    `org_doc_lexpre.list_export_rows`; o usuário preferiu os dois critérios
    numa linha só, com a coluna "Data de Protocolo" explícita, a uma 2ª aba
    parcialmente duplicada).
    """
    idx = _indexar_movimentacoes(peticionamento_lexpre)
    entradas_por_demanda = _entradas_por_demanda(_entradas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS))
    saidas = _saidas_setor(peticionamento_lexpre, SETOR_PETICIONAMENTO_IDS)
    saidas_periodo = _filter_saidas_by_date_range(saidas, from_date, to_date)

    linhas: List[Dict[str, Any]] = []
    vistos: set = set()
    for row in saidas_periodo:
        vistos.add(row.get("ID_DEMANDA"))
        linhas.append(_linha_export_saida(row, idx, entradas_por_demanda))

    for row in _filter_saidas_by_protocolo_date_range(saidas, from_date, to_date):
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id in vistos:
            continue
        vistos.add(demanda_id)
        linhas.append(_linha_export_saida(row, idx, entradas_por_demanda))

    for row in peticionamento_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_PETICIONAMENTO_IDS:
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
            "DESTINO": "—",
            "DATA_ENTRADA": _to_date(entrada.get("DATA")) if entrada else None,
            "DATA_SAIDA": None,
            "DATA_PROTOCOLO": None,
            "VALOR_CAUSA": _converter_valor(row.get("VALOR_CAUSA")),
            "DANO_MORAL": _converter_valor(row.get("DANO_MORAL")),
            "AREA_ATUACAO": row.get("AREA_ATUACAO_NOME"),
        })

    return linhas
