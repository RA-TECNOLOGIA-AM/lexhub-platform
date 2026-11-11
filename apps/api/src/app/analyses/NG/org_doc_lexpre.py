# Análises e processamento de dados de ORGANIZAÇÃO DE DOCUMENTOS NG (banco lexpre)
#
# Fonte: query "org_doc_lexpre_NG" (queries.py) — public.log_setor_demanda (join
# demandas/rubricas/funcionario) do banco `lexpre`. Mesmo domínio de negócio do
# antigo "org_doc" (banco `ng`, tabela setor_org_doc — uma linha por processo, com
# colunas ENTRADA/SAIDA/STATUS/FUNCIONARIO/MATERIA), mas em um schema orientado a
# EVENTOS: cada linha aqui é um evento de entrada OU saída de uma demanda em um
# setor (log_setor_demanda), não um processo.
#
# Setor "Organização de Documentos" = public.setores.id = 3. Uma movimentação de
# setor grava duas linhas com o mesmo movimentacao_id: a saída do setor antigo e a
# entrada no novo — ver `_indexar_movimentacoes`.
#
# Mapeamento das colunas do dashboard antigo (NG, banco `ng`) para o novo (lexpre):
#   - SAIDA (data em que o processo saiu do setor)      -> evento TIPO="saida", SETOR_ID=3,
#     cujo DESTINO (a entrada pareada pelo mesmo movimentacao_id) é Peticionamento
#     (id=4) OU Protocolo (id=5) — os mesmos dois destinos valem tanto para
#     peças manuais quanto automáticas (pet_auto não decide o destino) — ver
#     `_saidas_org_doc` e `_filtrar_resolvidos_reais`. No sistema, uma demanda
#     pode sair da Organização de Documentos para QUALQUER setor: uma saída para
#     Pendências é a demanda sendo DEVOLVIDA (algo precisa ser resolvido antes de
#     prosseguir), não uma resolução — ver "Devolvido para Pendência" abaixo.
#   - ENTRADA (data em que o processo entrou no setor)  -> evento TIPO="entrada", SETOR_ID=3
#   - MATERIA (rubrica, com sufixo livre "X - banco")    -> rubricas.nome (já normalizado)
#   - FUNCIONARIO responsável pela resolução             -> responsável (setor_func) no
#     momento da ENTRADA no setor, propagado para a saída correspondente (ver
#     `_funcionario_resolucao`) — as saídas observadas no banco não carregam
#     responsavel_id preenchido.
#   - STATUS "Resolvido" / "Protocolar" (manual/auto)    -> demandas.pet_auto
#     (False = organizado manualmente, True = organizado e peticionado automaticamente)
#   - STATUS "Cancelado"                                  -> demandas.status ==
#     STATUS_DEMANDA_CANCELADO_ID (10), mesma tabela/constante de comercial_lexpre.py
#     e protocolo_lexpre.py.
#   - REAJUIZAMENTO                                       -> não existe no lexpre ainda;
#     o card "Resolvidos Reajuizamento" do dashboard antigo não tem equivalente aqui.
#   - "Retorno Pendência" / "Retorno Pet" (entrada no setor vinda de outro setor —
#     a demanda voltou a ficar represada aqui) -> entrada no setor 3 cuja
#     movimentação pareada (mesmo movimentacao_id) tem saída do setor Pendências
#     (id=2) ou Peticionamento (id=4) — ver `_setor_origem`.
#   - "Devolvido para Pendência" (saída do setor para Pendências — a demanda saiu
#     daqui, mas não foi resolvida) -> evento de saída do setor 3 cujo destino
#     (movimentação pareada) é Pendências (id=2) — ver `_setor_destino` e
#     `get_devolvido_pendencia`. Direção OPOSTA de "Retorno Pendência" acima.
#   - "Represados" (processos parados no setor, sem filtro de período)
#     -> demandas (não canceladas) cujo setor_id ATUAL (demandas.setor_id, não o
#     evento de log) é 3.
#   - Comissionamento (R$0,60 × qtd protocolados × Σvalor_causa_protocolado/1.000.000)
#     -> mesma fórmula do dashboard antigo (org_doc.py, banco `ng`), mas com uma
#     diferença deliberada de 04/09/2026: TANTO a quantidade quanto o valor de
#     causa somados na fórmula só contam demandas que de fato chegaram a ser
#     PROTOCOLADAS (status atual == "Aguardando Despacho Inicial", id=13 — mesmo
#     critério de protocolo_setor_lexpre.py) — não qualquer demanda "resolvida"
#     pelo Org Doc (que só exige ter saído rumo a Peticionamento/Protocolo, sem
#     garantia de que o processo chegue a ser protocolado de fato). Ver
#     `get_protocolados_por_funcionario` / `get_valor_causa_protocolado_por_funcionario`
#     / `_is_protocolado` e a memória "Org Doc NG — Comissão vs Protocolado"
#     (simulação equivalente para o banco `ng`, feita em 03/09/2026, que motivou
#     este ajuste — lá só o valor de causa mudou, aqui a quantidade também).

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
# dashboard lexpre até agora (NGAM=1, LAAM=2, LARJ=3) — a atribuição de escritório
# de uma linha vem SEMPRE da coluna ESCRITORIO_ID (já filtrada antes via
# `filter_org_doc_lexpre_por_escritorio`), nunca do valor de SETOR_ID/SETOR_ATUAL_ID
# em si; esses ids só identificam QUAL setor, e comparar por pertencimento (in)
# cobre também casos de "cruzamento" onde uma demanda de um escritório é
# processada sob o setor_id de outro (confirmado com o usuário em 24/09/2026 pro
# caso de Organização de Documentos: 12 demandas com escritorio_id=2 registradas
# sob o setor_id do NGAM, id=3 — contam como LAAM mesmo assim). Existe um 3º bloco
# de ids (102-109, escritorio_id=11, operação "Penal") ainda não tratado aqui — não
# é o mesmo bloco do LARJ (operacao_id=33, setores 155-162), adicionado em 14/10/2026.
#   Setor                         NGAM   LAAM   LARJ
#   Comercial                       1    154    162
#   Pendências                      2     10    161
#   Organização de Documentos       3     11    155
#   Peticionamento                  4     12    157
#   Protocolo                       5     13    158
#   Triagem                         6      9    156
SETOR_COMERCIAL_IDS = {1, 154, 162}
SETOR_PENDENCIAS_IDS = {2, 10, 161}
SETOR_ORG_DOC_IDS = {3, 11, 155}
SETOR_PETICIONAMENTO_IDS = {4, 12, 157}
SETOR_PROTOCOLO_IDS = {5, 13, 158}
SETOR_TRIAGEM_IDS = {6, 9, 156}

# "Cancelado" em public.status (lexpre) — mesma constante de comercial_lexpre.py / protocolo_lexpre.py.
STATUS_DEMANDA_CANCELADO_ID = 10

# "Aguardando Despacho Inicial" em public.status (lexpre) — mesmo critério de "protocolado"
# usado em protocolo_setor_lexpre.py (`_is_protocolado`). Usado aqui só para o comissionamento
# (ver `_is_protocolado` / `get_valor_causa_protocolado_por_funcionario`) — decisão de 04/09/2026
# de só contar valor de causa de demandas que de fato chegaram a ser protocoladas, não de
# qualquer demanda resolvida pelo Org Doc (réplica lexpre da regra simulada para o banco `ng`
# em 03/09/2026, ver memória "Org Doc NG — Comissão vs Protocolado").
STATUS_AG_DESPACHO_INICIAL_ID = 13


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

def filter_org_doc_lexpre_por_escritorio(
    org_doc_lexpre: List[Dict[str, Any]],
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Restringe ao escritório informado — a query traz todos (NGAM/LAAM/LARJ) sem filtro."""
    return [row for row in org_doc_lexpre or [] if row.get("ESCRITORIO_ID") == escritorio_id]


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
    """Primeiro e segundo nome do funcionário — mesmo critério de org_doc.py (banco `ng`)."""
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
    Inicial") — critério mais estrito que "resolvido" (que só exige ter saído do
    Org Doc rumo a Peticionamento/Protocolo). Usado só no comissionamento: uma
    demanda pode ter "saído resolvida" do Org Doc e nunca chegar a ser protocolada
    de fato (parada em Peticionamento, cancelada depois, etc.).
    """
    return row.get("STATUS_DEMANDA_ID") == STATUS_AG_DESPACHO_INICIAL_ID


def _indexar_movimentacoes(org_doc_lexpre: List[Dict[str, Any]]) -> Dict[Any, Dict[str, Dict[str, Any]]]:
    """
    ``movimentacao_id -> {"entrada": linha, "saida": linha}``, a partir do universo
    COMPLETO de eventos (todos os setores, não só Organização de Documentos) — é isso
    que permite descobrir de/para qual setor uma demanda veio/foi, a partir de um
    evento isolado no setor 3.

    A primeira movimentação de uma demanda (criação) só tem a linha de entrada, sem
    saída pareada — nesse caso o índice fica só com a chave "entrada".
    """
    idx: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in org_doc_lexpre or []:
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


def _entradas_org_doc(org_doc_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        row for row in org_doc_lexpre or []
        if row.get("SETOR_ID") in SETOR_ORG_DOC_IDS and row.get("TIPO") == "entrada"
    ]


def _saidas_org_doc(org_doc_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Última saída do setor, uma por demanda.

    Uma demanda pode sair do setor mais de uma vez (ex.: vai para Peticionamento e
    depois retorna via "retorno confecção", ficando represada de novo, até
    finalmente sair outra vez) — cada ida gera seu próprio evento de saída em
    ``log_setor_demanda``. Sem essa deduplicação, uma mesma demanda contaria como
    "resolvida" uma vez por saída, inflando resolvidos/comissionamento.

    Demandas cujo setor ATUAL (``SETOR_ATUAL_ID``, valor vivo de ``demandas``) é de
    novo o setor 3 são excluídas por completo: a última saída registrada não foi
    final — a demanda voltou e está represada outra vez (contabilizada só em
    `get_represados`, nunca simultaneamente como resolvida).
    """
    ultima_por_demanda: Dict[Any, Dict[str, Any]] = {}
    for row in org_doc_lexpre or []:
        if row.get("SETOR_ID") not in SETOR_ORG_DOC_IDS or row.get("TIPO") != "saida":
            continue
        if row.get("SETOR_ATUAL_ID") in SETOR_ORG_DOC_IDS:
            continue
        demanda_id = row.get("ID_DEMANDA")
        atual = ultima_por_demanda.get(demanda_id)
        data_row = _to_datetime(row.get("DATA")) or datetime.min
        data_atual = _to_datetime(atual.get("DATA")) if atual else None
        if atual is None or data_row > (data_atual or datetime.min):
            ultima_por_demanda[demanda_id] = row
    return list(ultima_por_demanda.values())


def _filtrar_resolvidos_reais(
    saidas: List[Dict[str, Any]],
    idx: Dict[Any, Dict[str, Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    De ``_saidas_org_doc`` (última saída por demanda), mantém só as que de fato
    resolveram a demanda — destino Peticionamento OU Protocolo. Os mesmos dois
    destinos valem tanto para peças manuais quanto automáticas (pet_auto não
    determina o destino; qualquer saída para um desses dois setores conta como
    resolvida, seja manual ou automática).

    No sistema, uma saída da Organização de Documentos pode ir para QUALQUER
    setor: uma saída para Pendências é a demanda sendo DEVOLVIDA (algo precisa
    ser resolvido antes de prosseguir), não uma resolução concluída. Sem esse
    filtro, uma devolução contaria erroneamente como "resolvida" — ver
    `get_devolvido_pendencia` para essas devoluções.
    """
    return [row for row in saidas if _setor_destino(row, idx) in (SETOR_PETICIONAMENTO_IDS | SETOR_PROTOCOLO_IDS)]


def _entradas_org_doc_por_demanda(entradas: List[Dict[str, Any]]) -> Dict[Any, List[Dict[str, Any]]]:
    """Entradas no setor 3, agrupadas por demanda e ordenadas por data (mais antiga primeiro)."""
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
    """Última entrada da demanda no setor 3 até (e incluindo) o instante de referência."""
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


def _funcionario_resolucao(
    saida_row: Dict[str, Any],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> str:
    """
    Funcionário responsável pela resolução de uma saída do setor 3 — o próprio
    evento de saída normalmente não carrega responsável (ver cabeçalho do módulo),
    então usamos o responsável registrado na última entrada da mesma demanda no
    setor, antes da saída.
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
    DATA_PROTOCOLO em vez de DATA (saída da Organização de Documentos) — base de
    todo indicador de "Protocolados" (quantidade e valor, ver
    `get_protocolados_total`/`get_valor_causa_protocolado_por_funcionario`/
    `get_comissionamento_por_funcionario`), que deve refletir demandas cuja
    DATA_PROTOCOLO (não a saída do setor) caiu no período selecionado — mesmo
    padrão de peticionamento_lexpre.py (ajuste de 01/10/2026 na comissão),
    estendido em 07/10/2026 pro próprio card "Protocolados" (antes ancorado em
    DATA/saída, inflando/esvaziando o número conforme o status atual da demanda
    mudava com o tempo, independente do período escolhido — pedido do usuário).
    Recebe `saidas` (resoluções reais, de qualquer data de saída), não
    `saidas_periodo`, pra não perder demandas que saíram do setor fora do
    período mas protocolaram dentro dele.
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

def filter_org_doc_lexpre_por_materia(
    org_doc_lexpre: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(org_doc_lexpre)
    return [row for row in org_doc_lexpre if _normalizar_materia(row.get("MATERIA")) in alvos]


def filter_org_doc_lexpre_por_area_atuacao(
    org_doc_lexpre: List[Dict[str, Any]],
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe pela área de atuação real (``public.area_atuacao``, via ``operacao.area_atuacao_id``) — ver comercial_lexpre.filter_comercial_lexpre_por_area_atuacao."""
    alvos = normalizar_filtro_ids(area_atuacao_id)
    if not alvos:
        return list(org_doc_lexpre)
    return [row for row in org_doc_lexpre if row.get("AREA_ATUACAO_ID") in alvos]


def filter_org_doc_lexpre_por_area_atuacao_nome(
    org_doc_lexpre: List[Dict[str, Any]],
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
        return list(org_doc_lexpre)
    return [
        row for row in org_doc_lexpre
        if str(row.get("AREA_ATUACAO_NOME") or "").strip().upper() in alvos
    ]


def filter_org_doc_lexpre_por_uf(
    org_doc_lexpre: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe às demandas cujo cliente (``customer.uf``) é da UF informada. ``None`` = sem filtro. Catálogo de UFs compartilhado — ver `comercial_lexpre.list_ufs_comerciais`."""
    alvos = normalizar_filtro_textos(uf)
    if not alvos:
        return list(org_doc_lexpre)
    return [row for row in org_doc_lexpre if str(row.get("UF") or "").strip().upper() in alvos]


def list_funcionarios_org_doc_lexpre(org_doc_lexpre: List[Dict[str, Any]]) -> List[str]:
    """Funcionários que aparecem como responsáveis por uma entrada no setor 3, no recorte atual."""
    vistos: set = set()
    saida: List[str] = []
    for row in _entradas_org_doc(org_doc_lexpre):
        nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        if nome == "Sem funcionário" or nome in vistos:
            continue
        vistos.add(nome)
        saida.append(nome)
    return sorted(saida, key=lambda x: x.lower())


def filter_org_doc_lexpre_por_funcionarios(
    org_doc_lexpre: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
    idx: Optional[Dict[Any, Dict[str, Dict[str, Any]]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe às demandas cujo responsável (na última entrada no setor 3) é um dos
    funcionários informados (união — OR). Filtra por DEMANDA, não por evento
    isolado, para que a saída de uma demanda continue associada ao funcionário
    correto mesmo quando o próprio evento de saída não carrega responsável.
    """
    if not funcionarios:
        return list(org_doc_lexpre)
    alvos = {_formatar_nome_funcionario(f) for f in funcionarios if f is not None and str(f).strip()}
    if not alvos:
        return list(org_doc_lexpre)

    indice = idx if idx is not None else _indexar_movimentacoes(org_doc_lexpre)
    entradas_por_demanda = _entradas_org_doc_por_demanda(_entradas_org_doc(org_doc_lexpre))

    demandas_alvo: set = set()
    for row in org_doc_lexpre:
        if row.get("SETOR_ID") not in SETOR_ORG_DOC_IDS:
            continue
        if row.get("TIPO") == "entrada":
            nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        else:
            nome = _funcionario_resolucao(row, entradas_por_demanda)
        if nome in alvos:
            demandas_alvo.add(row.get("ID_DEMANDA"))

    return [row for row in org_doc_lexpre if row.get("ID_DEMANDA") in demandas_alvo]


# -----------------------------------------------------------------------------
# 3 - KPIs do período (base: saídas do setor 3, por DATA da saída)
# -----------------------------------------------------------------------------

def get_resolvidos_total(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if not _is_cancelado(row)])


def get_organizados_manualmente(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if not _is_cancelado(row) and row.get("PET_AUTO") is False])


def get_organizados_e_peticionados_automaticamente(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if not _is_cancelado(row) and row.get("PET_AUTO") is True])


def get_cancelados(saidas_periodo: List[Dict[str, Any]]) -> int:
    return len([row for row in saidas_periodo if _is_cancelado(row)])


def get_protocolados_total(saidas_protocoladas_periodo: List[Dict[str, Any]]) -> int:
    """
    Quantas demandas resolvidas pela Organização de Documentos de fato
    protocolaram DENTRO do período selecionado — critério: DATA_PROTOCOLO
    preenchida e dentro do período (ver `_filter_saidas_by_protocolo_date_range`,
    já aplicado em ``saidas_protocoladas_periodo``) e status atual "Aguardando
    Despacho Inicial" (`_is_protocolado`).

    Ajuste de 07/10/2026 (pedido do usuário): antes contava, entre as que
    SAÍRAM do setor no período, quantas JÁ ESTÃO protocoladas hoje — número que
    só cresce (ou oscila) com o tempo, sem relação com o período escolhido. Uma
    demanda que saiu em setembro mas só protocolou em outubro não entra mais no
    "Protocolados" de setembro; entra no de outubro.
    """
    return len([row for row in saidas_protocoladas_periodo if not _is_cancelado(row) and _is_protocolado(row)])


def get_represados(org_doc_lexpre: List[Dict[str, Any]]) -> int:
    """
    Demandas (não canceladas) atualmente no setor 3 — valor sempre total, sem
    filtro de período, mesmo critério de "Represados" no dashboard antigo.
    Deduplicado por ID_DEMANDA (linhas de log repetem a demanda a cada evento).

    Diferente do dashboard Comercial (LexPre), aqui uma demanda de rubrica
    "reunida" conta como 1, não expandida por componente — nos setores de
    pré-protocolo (Organização de Documentos, Peticionamento, Protocolo) o que se
    move é o documento/demanda física, não a comissão por rubrica associada.
    Confirmado com o usuário em 04/09/2026 (não reverter para expandir de novo).
    """
    vistos: set = set()
    for row in org_doc_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_ORG_DOC_IDS:
            continue
        if _is_cancelado(row):
            continue
        vistos.add(demanda_id)
    return len(vistos)


def _retornos(org_doc_lexpre: List[Dict[str, Any]], setores_origem_alvo: set) -> int:
    """Entradas no setor 3 cuja movimentação pareada saiu de algum dos setores informados — valor sempre total."""
    idx = _indexar_movimentacoes(org_doc_lexpre)
    return len([
        row for row in _entradas_org_doc(org_doc_lexpre)
        if _setor_origem(row, idx) in setores_origem_alvo
    ])


def get_retorno_pendencia(org_doc_lexpre: List[Dict[str, Any]]) -> int:
    """Entradas no setor vindas de Pendências — equivalente a "Retorno" no dashboard antigo."""
    return _retornos(org_doc_lexpre, SETOR_PENDENCIAS_IDS)


def get_retorno_pet(org_doc_lexpre: List[Dict[str, Any]]) -> int:
    """Entradas no setor vindas de Peticionamento — equivalente a "Retorno Pet" no dashboard antigo."""
    return _retornos(org_doc_lexpre, SETOR_PETICIONAMENTO_IDS)


def get_devolvido_pendencia(
    org_doc_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Demandas devolvidas da Organização de Documentos para Pendências — a
    resolução foi interrompida porque surgiu uma pendência a resolver antes de
    prosseguir. Direção OPOSTA de `get_retorno_pendencia` (que conta entradas
    vindas de Pendências, não saídas para lá). Conta eventos de saída (não
    deduplicados: cada devolução conta). Sem datas = valor sempre total (o que
    o card exibe); com datas = só as devoluções cuja DATA cai no intervalo
    (base do comparativo, ver `get_comparativo_devolvido_pendencia`).
    """
    idx = _indexar_movimentacoes(org_doc_lexpre)
    saidas_brutas = [
        row for row in org_doc_lexpre or []
        if row.get("SETOR_ID") in SETOR_ORG_DOC_IDS and row.get("TIPO") == "saida"
    ]
    if from_date and to_date:
        saidas_brutas = _filter_saidas_by_date_range(saidas_brutas, from_date, to_date)
    return len([row for row in saidas_brutas if _setor_destino(row, idx) in SETOR_PENDENCIAS_IDS])


# -----------------------------------------------------------------------------
# 4 - Tempo de resolução (entrada -> saída no setor 3)
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


def get_media_tempo_resolvidos(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> float:
    """Média de dias entre entrada e saída no setor, para saídas do período (não canceladas)."""
    duracoes_horas = _extrair_duracoes_horas(saidas_periodo, entradas_por_demanda)
    if not duracoes_horas:
        return 0.0
    return round((sum(duracoes_horas) / len(duracoes_horas)) / 24, 2)


def get_mediana_tempo_resolvidos(
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


def _saidas_reais_para_comparativo(org_doc_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """``_saidas_org_doc`` já filtrada para destino Peticionamento/Protocolo — mesma base usada nos stats do período (ver `_filtrar_resolvidos_reais`)."""
    idx = _indexar_movimentacoes(org_doc_lexpre)
    saidas = _saidas_org_doc(org_doc_lexpre)
    return _filtrar_resolvidos_reais(saidas, idx)


def get_comparativo_resolvidos_total(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(org_doc_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_resolvidos_total(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_protocolados_total(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(org_doc_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_protocolados_total(_filter_saidas_by_protocolo_date_range(saidas, a, b))
    )


def get_comparativo_organizados_manualmente(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(org_doc_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_organizados_manualmente(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_organizados_automaticamente(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(org_doc_lexpre)
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_organizados_e_peticionados_automaticamente(_filter_saidas_by_date_range(saidas, a, b)),
    )


def get_comparativo_cancelados(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    # Cancelamento não tem entrada pareada em outro setor (destino sempre None),
    # então usa as saídas SEM o filtro de destino de `_saidas_reais_para_comparativo`
    # — senão todo cancelamento seria descartado antes mesmo de ser contado.
    saidas = _saidas_org_doc(org_doc_lexpre)
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_cancelados(_filter_saidas_by_date_range(saidas, a, b))
    )


def get_comparativo_devolvido_pendencia(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    """Devoluções p/ Pendências no período selecionado vs mesmo recorte do mês anterior (o card em si segue total)."""
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_devolvido_pendencia(org_doc_lexpre, a, b)
    )


def get_comparativo_tempo_medio_resolvidos(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(org_doc_lexpre)
    entradas_por_demanda = _entradas_org_doc_por_demanda(_entradas_org_doc(org_doc_lexpre))
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_media_tempo_resolvidos(_filter_saidas_by_date_range(saidas, a, b), entradas_por_demanda),
    )



def get_comparativo_mediana_tempo_resolvidos(
    org_doc_lexpre: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    saidas = _saidas_reais_para_comparativo(org_doc_lexpre)
    entradas_por_demanda = _entradas_org_doc_por_demanda(_entradas_org_doc(org_doc_lexpre))
    return _comparativo_variacao_percentual(
        from_date,
        to_date,
        lambda a, b: get_mediana_tempo_resolvidos(_filter_saidas_by_date_range(saidas, a, b), entradas_por_demanda),
    )


# -----------------------------------------------------------------------------
# 6 - Agrupamentos (matéria, mês, dia, funcionário)
# -----------------------------------------------------------------------------

_MONTH_NAMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def group_resolvidos_total_por_materia(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_protocolados_total_por_materia(saidas_protocoladas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Por matéria, quantas demandas de fato protocolaram DENTRO do período
    selecionado (``saidas_protocoladas_periodo``, ancorado em DATA_PROTOCOLO —
    ver `_filter_saidas_by_protocolo_date_range`), não a resolvida/saída do
    setor. Alimenta o toggle "No Setor" / "Protocolados" do gráfico "Top 10 –
    Resolvidos por Matéria" (mesmo padrão do Peticionamento LexPre, ver
    `peticionamento_lexpre.group_protocolados_por_materia`). Ajuste de
    07/10/2026 (pedido do usuário) — antes usava ``saidas_periodo`` (DATA de
    saída) + status atual, igual ao bug do card "Protocolados" (ver
    `get_protocolados_total`); por isso o resultado NÃO é mais necessariamente
    ≤ `group_resolvidos_total_por_materia` do mesmo período (uma demanda pode
    ter saído do setor num mês e protocolado em outro).
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


def group_nao_organizados_total_por_materia(org_doc_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados (setor atual = 3, não cancelados) agrupados por matéria — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    vistos: set = set()
    for row in org_doc_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_ORG_DOC_IDS or _is_cancelado(row):
            continue
        vistos.add(demanda_id)
        grouped[_normalizar_materia(row.get("MATERIA"))] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_resolvidos_total_por_mes(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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


def group_nao_resolvidos_total_por_mes(org_doc_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados agrupados pelo mês da última entrada no setor — equivalente ao "por mês (via ENTRADA)" antigo."""
    grouped: Dict[str, Dict[str, Any]] = {}
    entradas_por_demanda = _entradas_org_doc_por_demanda(_entradas_org_doc(org_doc_lexpre))
    vistos: set = set()
    for row in org_doc_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_ORG_DOC_IDS or _is_cancelado(row):
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


def group_resolvidos_por_dia(saidas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        d = _to_date(row.get("DATA"))
        if not d:
            continue
        grouped[d.strftime("%Y-%m-%d")] += 1
    return [{"name": dia, "value": count} for dia, count in sorted(grouped.items())]


def get_resolvidos_por_dia_por_funcionario(
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
        funcionario = _funcionario_resolucao(row, entradas_por_demanda)
        grouped[d.strftime("%Y-%m-%d")][funcionario] += 1
    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted({f for dia_data in grouped.values() for f in dia_data.keys()})
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {
        func: [{"name": dia, "value": grouped[dia].get(func, 0)} for dia in dias_ordenados]
        for func in funcionarios
    }
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}


def group_resolvidos_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        grouped[_funcionario_resolucao(row, entradas_por_demanda)] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def group_nao_organizados_por_funcionario(org_doc_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Represados por funcionário responsável (última entrada no setor) — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    entradas_por_demanda = _entradas_org_doc_por_demanda(_entradas_org_doc(org_doc_lexpre))
    vistos: set = set()
    for row in org_doc_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_ORG_DOC_IDS or _is_cancelado(row):
            continue
        vistos.add(demanda_id)
        entradas = entradas_por_demanda.get(demanda_id) or []
        nome = _formatar_nome_funcionario(entradas[-1].get("FUNCIONARIO")) if entradas else "Sem funcionário"
        grouped[nome] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_media_resolvidos_por_funcionario(
    saidas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in saidas_periodo:
        if _is_cancelado(row):
            continue
        funcionario = _funcionario_resolucao(row, entradas_por_demanda)
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
    """Valor de causa por funcionário (das saídas resolvidas). Para matéria ANP usa DANO_MORAL."""
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
        funcionario = _funcionario_resolucao(row, entradas_por_demanda)
        grouped[funcionario] += valor
    result = [{"name": nome, "value": round(valor, 2)} for nome, valor in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_valor_causa_protocolado_por_funcionario(
    saidas_protocoladas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Valor de causa por funcionário, restrito às demandas que de fato
    protocolaram DENTRO do período selecionado (``saidas_protocoladas_periodo``,
    ancorado em DATA_PROTOCOLO — ver `_filter_saidas_by_protocolo_date_range`) —
    usado no gráfico "Valor de Causa por Funcionário" (fatia protocolada) e no
    comissionamento (ver `get_comissionamento_por_funcionario`).

    Diferente de `get_valor_causa_por_funcionario` (todas as resolvidas, usado no
    gráfico "Valor de Causa por Funcionário"): uma demanda pode sair "resolvida"
    do Org Doc rumo a Peticionamento/Protocolo e nunca chegar a ser protocolada de
    fato, ou só protocolar fora do período — decisão de 04/09/2026 de não
    comissionar sobre valor de causa de demandas que podem nunca ser
    protocoladas (réplica lexpre da regra simulada para o banco `ng` em
    03/09/2026), estendida em 07/10/2026 pra também exigir que a protocolada
    tenha DATA_PROTOCOLO dentro do período (pedido do usuário).
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
        funcionario = _funcionario_resolucao(row, entradas_por_demanda)
        grouped[funcionario] += valor
    result = [{"name": nome, "value": round(valor, 2)} for nome, valor in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_protocolados_por_funcionario(
    saidas_protocoladas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Quantidade de demandas que de fato protocolaram DENTRO do período
    selecionado (``saidas_protocoladas_periodo``, ancorado em DATA_PROTOCOLO —
    ver `_filter_saidas_by_protocolo_date_range`), por funcionário — usado no
    comissionamento (ver `get_comissionamento_por_funcionario`).

    Diferente de `group_resolvidos_por_funcionario` (todas as resolvidas,
    protocoladas ou não, por data de saída, usado no gráfico "Demandas por
    Funcionário"): decisão de 04/09/2026 de a comissão só contar demandas de
    fato protocoladas, tanto na quantidade quanto no valor de causa (mesmo
    critério de `get_valor_causa_protocolado_por_funcionario`); estendida em
    07/10/2026 pra também exigir DATA_PROTOCOLO dentro do período (pedido do
    usuário) — antes bastava status atual protocolado, sem olhar quando.
    """
    grouped: Dict[str, int] = defaultdict(int)
    for row in saidas_protocoladas_periodo:
        if _is_cancelado(row):
            continue
        if not _is_protocolado(row):
            continue
        grouped[_funcionario_resolucao(row, entradas_por_demanda)] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# R$ 0,60 por protocolado, proporcional ao valor de causa protocolado, expresso em
# milhões — mesma fórmula de org_doc.py (banco `ng`), com o ajuste de 04/09/2026 de
# só contar demandas de fato protocoladas, tanto na quantidade quanto no valor de
# causa (ver `get_protocolados_por_funcionario` / `get_valor_causa_protocolado_por_funcionario`).
_COMISSAO_POR_RESOLVIDO_MILHAO = Decimal("0.60")
_MILHAO = Decimal("1000000")


def get_comissionamento_por_funcionario(
    saidas_protocoladas_periodo: List[Dict[str, Any]],
    entradas_por_demanda: Dict[Any, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    por_qtd = {
        r["name"]: int(r["value"])
        for r in get_protocolados_por_funcionario(saidas_protocoladas_periodo, entradas_por_demanda)
    }
    por_valor = {
        r["name"]: float(r["value"])
        for r in get_valor_causa_protocolado_por_funcionario(saidas_protocoladas_periodo, entradas_por_demanda)
    }
    nomes = sorted(set(por_qtd) | set(por_valor))

    linhas: List[Dict[str, Any]] = []
    for nome in nomes:
        qtd = por_qtd.get(nome, 0)
        valor_causa = por_valor.get(nome, 0.0)
        comissao = _COMISSAO_POR_RESOLVIDO_MILHAO * Decimal(qtd) * (Decimal(str(valor_causa)) / _MILHAO)
        linhas.append({
            "funcionario": nome,
            "qtd_protocolados": qtd,
            "valor_causa_protocolado": round(valor_causa, 2),
            "valor_comissao": float(comissao.quantize(Decimal("0.01"))),
        })
    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# -----------------------------------------------------------------------------
# 8 - Exportação (relatório) — uma linha por demanda
# -----------------------------------------------------------------------------

_SITUACAO_RESOLVIDO_MANUAL = "Resolvido (manual)"
_SITUACAO_RESOLVIDO_AUTOMATICO = "Resolvido (automático)"
_SITUACAO_REPRESADO = "Represado"
_SITUACAO_CANCELADO = "Cancelado"

_EXPORT_DESTINO_NOMES = {
    **{sid: "Pendências" for sid in SETOR_PENDENCIAS_IDS},
    **{sid: "Peticionamento" for sid in SETOR_PETICIONAMENTO_IDS},
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
        situacao = _SITUACAO_RESOLVIDO_AUTOMATICO
    else:
        situacao = _SITUACAO_RESOLVIDO_MANUAL
    return {
        "ID_DEMANDA": demanda_id,
        "NUMERO_PROCESSO": row.get("NUMERO_PROCESSO"),
        "CLIENTE_NOME": row.get("CLIENTE_NOME"),
        "MATERIA": _normalizar_materia(row.get("MATERIA")),
        "FUNCIONARIO": _funcionario_resolucao(row, entradas_por_demanda),
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
    org_doc_lexpre: List[Dict[str, Any]],
    from_date: date,
    to_date: date,
) -> List[Dict[str, Any]]:
    """
    Uma linha por demanda, para o relatório exportável: as que saíram do setor
    (resolvidas manual/automaticamente ou canceladas) OU que protocolaram
    dentro do período selecionado (``DATA_SAIDA`` ou ``DATA_PROTOCOLO`` — nunca
    as duas juntas para a mesma demanda), mais o backlog atual (represadas
    ainda no setor), sempre total.

    Uma demanda pode sair do setor num mês e só protocolar no seguinte — sem o
    critério por ``DATA_PROTOCOLO`` ela não apareceria em NENHUM relatório
    mensal, mesmo contando no comissionamento do mês em que protocolou de fato
    (ajuste de 28/10/2026, pedido do usuário, depois de uma 1ª tentativa com
    aba separada — o usuário preferiu os dois critérios numa linha só, com a
    coluna "Data de Protocolo" explícita, a duas abas parcialmente duplicadas;
    caso real: demanda 957/SILVIO MENEZES DIAS, MORA, saiu 30/09, protocolou
    02/10 — sumia dos relatórios de setembro E outubro).
    """
    idx = _indexar_movimentacoes(org_doc_lexpre)
    entradas_por_demanda = _entradas_org_doc_por_demanda(_entradas_org_doc(org_doc_lexpre))
    saidas = _saidas_org_doc(org_doc_lexpre)
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

    for row in org_doc_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_ORG_DOC_IDS:
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
