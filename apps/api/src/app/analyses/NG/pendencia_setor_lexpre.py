# Análises e processamento de dados de PENDÊNCIAS NG (banco lexpre) — visão de SETOR
#
# Fonte: query "log_setor_demanda_lexpre_NG" (queries.py) — o mesmo log cru de
# entradas/saídas de setor usado por org_doc_lexpre.py, peticionamento_lexpre.py
# e protocolo_setor_lexpre.py, aqui recortado para o setor "Pendências"
# (public.setores.id = 2). Mesmo domínio de negócio do antigo "pendencia"
# (banco `ng`, tabela pendencia — uma linha por instância de pendência, com
# colunas ENTRADA/SAIDA/STATUS/ORIGEM/ATENDENTE/FUNCIONARIO), mas em um schema
# orientado a EVENTOS: cada linha aqui é um evento de entrada OU saída de uma
# demanda em um setor, não uma instância de pendência já pronta.
#
# Diferença-chave em relação aos outros três módulos: uma demanda pode visitar
# Pendências VÁRIAS VEZES ao longo da vida (ela sai de outro setor, cai em
# Pendências para resolver algo, volta, e pode cair em Pendências de novo mais
# tarde por outro motivo). `_construir_visitas` reconstrói TODAS as visitas (par
# entrada/saída) por demanda, em ordem cronológica, e marca qual delas é a ÚLTIMA
# (``ultima=True``) — necessário porque cancelamento é sempre terminal (a demanda
# não se move mais depois de cancelada), então só a última visita pode ser
# classificada como cancelada a partir do status vivo de `demandas` — ver
# `_is_cancelada`.
#
# Ajuste de 18/09/2026: as métricas "do período" (Total, Resolvidas, Canceladas,
# taxas, comissão, produção diária/mensal) só consideram a ÚLTIMA visita de cada
# demanda — ver `_visitas_periodo`. Antes disso, cada visita contava como uma
# "pendência resolvida" separada (réplica literal do dashboard antigo, onde cada
# linha da tabela `pendencia` já era uma instância pronta); na prática isso inflava
# os números quando uma demanda saía e voltava a cair em Pendências mais de uma vez
# no mesmo recorte. Agora o critério é o mesmo de "última saída por demanda"
# (`_saidas_setor`) já usado nos outros três módulos — uma visita intermediária
# (não a última) nunca aparece em nenhuma métrica de período, mesmo que sua
# entrada caia no intervalo selecionado.
#
# O "período" filtra pela data de ENTRADA da visita (quando a pendência foi
# aberta), não pela saída — isso é o que permite uma visita "ainda aberta"
# (sem saída) aparecer no total do período (ver `_visitas_periodo`), igual ao
# dashboard antigo (onde total/resolvidas/canceladas/taxas do período sempre
# vêm do mesmo recorte). "Não Resolvidas" (o card de backlog) e "Não Resolvidas
# > 5 dias", por outro lado, são sempre acumulados (todas as visitas em aberto,
# não só as do período) — mesmo critério de "Represados" dos outros módulos; como
# uma visita aberta é sempre a última da sua demanda (não dá pra reentrar no setor
# sem antes fechar a visita atual), o filtro de "última visita" não muda esse card.
#
# Mapeamento das colunas do dashboard antigo (NG, banco `ng`) para o novo (lexpre):
#   - ENTRADA / SAIDA                                     -> par de eventos TIPO="entrada"/"saida",
#     SETOR_ID=2, reconstruído em visitas — ver `_construir_visitas`.
#   - STATUS "Resolvido"                                   -> visita fechada (tem saída) e não é a
#     última visita cancelada da demanda — ver `_is_resolvida`.
#   - STATUS "Em andamento" / "Pendência" (não resolvida)   -> visita em aberto (sem saída) — ver `_is_aberta`.
#   - STATUS "Cancelado"                                    -> última visita da demanda, com
#     demandas.status == STATUS_DEMANDA_CANCELADO_ID (10) — ver `_is_cancelada`.
#     Ajuste de 04/09/2026: só conta como cancelamento "da Pendência" se quem executou o evento
#     (log_setor_demanda.actor_id) pertence de fato ao setor Pendências (`setor_func`, via
#     `build_funcionarios_do_setor` + `_construir_visitas(..., funcionarios_setor_ids=...)`) — um
#     cancelamento feito por alguém de outro setor/área não é responsabilidade da Pendência e não
#     deve contar na taxa de cancelamento nem no card "Pendências Canceladas" desse setor. Sem
#     `funcionarios_setor_ids` informado, o comportamento antigo é mantido (qualquer cancelamento conta).
#     Ajuste de 02/10/2026: também exige que `demandas.motivo_cancelamento_id` esteja em
#     `MOTIVOS_CANCELAMENTO_PENDENCIA_IDS` (1 "Cliente desistiu", 2 "Cliente de outro estado" —
#     catálogo public.motivo_encerramento) — motivos como "Inexistência processual" ou "Erro na
#     geração de contrato" não contam mais como cancelamento desta Pendência, mesmo com o ator
#     correto; a demanda cai em "Resolvida" nesse caso (mesmo efeito que o cancelamento fora do
#     setor já tinha). Pedido do usuário após eu explicar o critério de cancelamento existente.
#   - ORIGEM (de onde veio a pendência)                     -> setor da saída pareada pelo mesmo
#     movimentacao_id da entrada na visita — ver `_setor_origem_nome`.
#   - FUNCIONARIO responsável pela resolução                -> responsável (setor_func) no momento
#     da ENTRADA da visita, propagado para a saída correspondente — ver `_funcionario_visita`.
#   - TRIAGEM (clientes que não responderam a Triagem)       -> não tem equivalente direto no
#     lexpre ainda: Triagem lá é outro setor (id=6), não um sub-estado de Pendências. Fica como
#     placeholder (valor 0) na UI.
#   - REAJUIZAMENTO                                          -> não existe no lexpre ainda; os
#     cards "Não Resolvidas/Resolvidas - Reajuizamento" do dashboard antigo ficam como
#     placeholder (valor 0) na UI.
#   - ATENDENTE (comercial) / "Não Resolvidas por Atendente" -> não mapeado: esse campo vem do
#     atendimento comercial original, não do responsável pela pendência em si, e não é usado em
#     nenhum gráfico renderizado na página atual — sem equivalente aqui.
#   - Comissionamento (R$3 se taxa_resolvido>=97% e taxa_cancelamento<5%; R$1 se >=85%; senão R$0)
#     -> mesma fórmula, aplicada por funcionário sobre as visitas do período — ver
#     `get_pendencias_comissionamento_por_funcionario`.

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
# `filter_pendencia_lexpre_por_escritorio`), nunca do valor de SETOR_ID em si;
# esses ids só identificam QUAL setor, e comparar por pertencimento (in) cobre
# também eventuais casos de "cruzamento" entre escritórios (ver o mesmo ajuste em
# org_doc_lexpre.py, 24/09/2026; LARJ adicionado em 14/10/2026, operacao_id=33).
# Existe um 3º bloco de ids (102-109, escritorio_id=11, operação "Penal") ainda
# não tratado aqui — não é o mesmo bloco do LARJ.
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

# "Cancelado" em public.status (lexpre) — mesma constante dos outros módulos lexpre.
STATUS_DEMANDA_CANCELADO_ID = 10

# Motivos de cancelamento que contam como "cancelamento da Pendência" (ajuste de
# 02/10/2026, pedido do usuário) — catálogo em public.motivo_encerramento (não
# existe uma tabela motivo_cancelamento separada; demandas.motivo_cancelamento_id
# referencia esse mesmo catálogo, compartilhado com encerramento):
#   1 = "Cliente desistiu"
#   2 = "Cliente de outro estado"
# Qualquer outro motivo (ex.: 15 "Erro na geração de contrato", 16 "Inexistência
# processual") NÃO conta mais como cancelamento desta Pendência — ver
# `_tem_motivo_cancelamento_valido`/`_is_cancelada`. Antes desse ajuste, todo
# cancelamento contava (sem filtro de motivo).
MOTIVOS_CANCELAMENTO_PENDENCIA_IDS = {1, 2}

# Prazo (dias) para uma pendência em aberto ser considerada atrasada — mesmo critério do antigo pendencia.py.
_DIAS_ATRASO = 5


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

def filter_pendencia_lexpre_por_escritorio(
    pendencia_lexpre: List[Dict[str, Any]],
    escritorio_id: int = ESCRITORIO_NGAM,
) -> List[Dict[str, Any]]:
    """Restringe ao escritório informado — a query traz todos (NGAM/LAAM/LARJ) sem filtro."""
    return [row for row in pendencia_lexpre or [] if row.get("ESCRITORIO_ID") == escritorio_id]


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
    """Converte um valor monetário (string ou numérico) para float — mesma lógica dos outros módulos lexpre."""
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
    """Primeiro e segundo nome do funcionário — mesmo critério dos outros módulos lexpre."""
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


def _is_cancelado_status(row: Dict[str, Any]) -> bool:
    return row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID


def _tem_motivo_cancelamento_valido(row: Dict[str, Any]) -> bool:
    """`demandas.motivo_cancelamento_id` está em `MOTIVOS_CANCELAMENTO_PENDENCIA_IDS` — ver constante."""
    return row.get("MOTIVO_CANCELAMENTO_ID") in MOTIVOS_CANCELAMENTO_PENDENCIA_IDS


def _indexar_movimentacoes(pendencia_lexpre: List[Dict[str, Any]]) -> Dict[Any, Dict[str, Dict[str, Any]]]:
    """``movimentacao_id -> {"entrada": linha, "saida": linha}`` — mesmo critério de org_doc_lexpre.py."""
    idx: Dict[Any, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in pendencia_lexpre or []:
        mov_id = row.get("MOVIMENTACAO_ID")
        tipo = row.get("TIPO")
        if mov_id is None or tipo not in ("entrada", "saida"):
            continue
        idx[mov_id][tipo] = row
    return idx


def _setor_origem_nome(entrada_row: Dict[str, Any], idx: Dict[Any, Dict[str, Dict[str, Any]]]) -> str:
    """Nome do setor de onde a demanda veio, para um evento de ``entrada`` — a saída pareada pelo mesmo movimentacao_id."""
    par = idx.get(entrada_row.get("MOVIMENTACAO_ID"), {})
    saida_par = par.get("saida")
    if not saida_par:
        return "Origem desconhecida"
    return str(saida_par.get("SETOR_NOME") or "Origem desconhecida")


def _entradas_setor(pendencia_lexpre: List[Dict[str, Any]], setor_ids: set) -> List[Dict[str, Any]]:
    return [
        row for row in pendencia_lexpre or []
        if row.get("SETOR_ID") in setor_ids and row.get("TIPO") == "entrada"
    ]


# -----------------------------------------------------------------------------
# 2 - Reconstrução de visitas (par entrada/saída por demanda, em ordem cronológica)
# -----------------------------------------------------------------------------

def build_funcionarios_do_setor(setor_func_lexpre: List[Dict[str, Any]], setor_ids: set) -> set:
    """
    Conjunto de ``funcionario_id`` formalmente alocados no setor informado
    (query "setor_func_lexpre_NG") — usado para validar se quem executou um
    cancelamento (``ACTOR_ID``) pertence de fato ao setor Pendências antes de
    contar o evento como "cancelamento da Pendência" (ver `_is_cancelada`).

    ``setor_ids`` é um conjunto (ex: `SETOR_PENDENCIAS_IDS`), não um id único —
    cada escritório tem seu próprio id de setor (ver comentário da constante).
    """
    return {
        row.get("FUNCIONARIO_ID")
        for row in setor_func_lexpre or []
        if row.get("SETOR_ID") in setor_ids and row.get("FUNCIONARIO_ID") is not None
    }


def _construir_visitas(
    pendencia_lexpre: List[Dict[str, Any]],
    setor_ids: set,
    funcionarios_setor_ids: Optional[set] = None,
) -> List[Dict[str, Any]]:
    """
    Reconstrói cada visita (par entrada + saída, quando houver) da demanda ao
    setor, em ordem cronológica. Uma demanda pode visitar o setor várias vezes;
    cada visita vira um item próprio, marcado com ``ultima=True`` só na última
    visita cronológica daquela demanda (usado por `_is_cancelada`, já que
    cancelamento é sempre terminal). Uma visita sem saída (``saida=None``)
    ainda está em aberto (represada).

    ``funcionarios_setor_ids`` (opcional, ver `build_funcionarios_do_setor`):
    quando informado, cada visita ganha o campo ``ator_do_setor`` — se quem
    executou o evento de referência (a saída, ou a entrada quando ainda não
    há saída) pertence ao setor — consumido por `_is_cancelada` pra só validar
    cancelamentos feitos por alguém do próprio setor Pendências. Sem esse
    argumento, ``ator_do_setor`` fica sempre ``True`` (comportamento antigo,
    sem essa checagem).
    """
    eventos_por_demanda: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for row in pendencia_lexpre or []:
        if row.get("SETOR_ID") not in setor_ids or row.get("TIPO") not in ("entrada", "saida"):
            continue
        eventos_por_demanda[row.get("ID_DEMANDA")].append(row)

    visitas: List[Dict[str, Any]] = []
    for eventos in eventos_por_demanda.values():
        eventos.sort(key=lambda r: _to_datetime(r.get("DATA")) or datetime.min)
        fechadas: List[Dict[str, Any]] = []
        entrada_pendente: Optional[Dict[str, Any]] = None
        for ev in eventos:
            if ev.get("TIPO") == "entrada":
                if entrada_pendente is not None:
                    fechadas.append({"entrada": entrada_pendente, "saida": None})
                entrada_pendente = ev
            else:
                fechadas.append({"entrada": entrada_pendente, "saida": ev})
                entrada_pendente = None
        if entrada_pendente is not None:
            fechadas.append({"entrada": entrada_pendente, "saida": None})
        for v in fechadas:
            v["ultima"] = False
            if funcionarios_setor_ids is not None:
                referencia = v.get("saida") or v.get("entrada")
                v["ator_do_setor"] = bool(
                    referencia and referencia.get("ACTOR_ID") in funcionarios_setor_ids
                )
            else:
                v["ator_do_setor"] = True
        if fechadas:
            fechadas[-1]["ultima"] = True
        visitas.extend(fechadas)
    return visitas


def _is_cancelada(visita: Dict[str, Any]) -> bool:
    """
    Cancelamento é sempre terminal — só a última visita da demanda pode ter
    sido a cancelada — e só conta se: (1) quem executou o evento pertence ao
    setor Pendências (``ator_do_setor``, ver `_construir_visitas`/
    `build_funcionarios_do_setor`; ``True`` por padrão quando essa checagem não
    foi habilitada), E (2) o motivo do cancelamento está em
    `MOTIVOS_CANCELAMENTO_PENDENCIA_IDS` (ajuste de 02/10/2026 — ver a
    constante). Uma demanda cancelada por outro motivo (ou por alguém de outro
    setor) não conta como "cancelada" aqui — como a visita já tem saída, ela
    cai em `_is_resolvida` (mesmo efeito que o cancelamento fora do setor já
    tinha antes desse ajuste).
    """
    if not visita.get("ultima"):
        return False
    referencia = visita.get("saida") or visita.get("entrada")
    if not (referencia and _is_cancelado_status(referencia)):
        return False
    if not _tem_motivo_cancelamento_valido(referencia):
        return False
    return visita.get("ator_do_setor", True)


def _is_aberta(visita: Dict[str, Any]) -> bool:
    """
    Ainda represada — sem saída do setor E ainda não cancelada. Uma demanda
    pode ser cancelada sem nunca ter gerado um evento de saída do setor (ela
    estava parada aqui quando foi cancelada); sem o segundo critério, essa
    visita contaria ao mesmo tempo como "em aberto" (backlog) e "cancelada".
    """
    return visita.get("saida") is None and not _is_cancelada(visita)


def _is_resolvida(visita: Dict[str, Any]) -> bool:
    return not _is_aberta(visita) and not _is_cancelada(visita)


def _visitas_periodo(visitas: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """
    Visitas cuja ENTRADA caiu no período — permite que uma visita ainda aberta conte
    no total do período.

    Só considera a ÚLTIMA visita de cada demanda ao setor (``ultima=True``, ver
    `_construir_visitas`) — ajuste de 18/09/2026: uma demanda pode sair de Pendências
    mais de uma vez (ela é devolvida, resolve algo, mas depois volta a cair em
    Pendências por outro motivo); antes disso, cada uma dessas idas contava como uma
    "pendência resolvida" separada, inflando Total/Resolvidas/taxas/comissão. Agora
    só a saída mais recente da demanda representa o desfecho real dela nas métricas
    "do período" — mesmo critério de "última saída por demanda" já usado nos outros
    três módulos lexpre (`_saidas_setor`). Visitas intermediárias (não a última) não
    aparecem em nenhuma métrica de período, mesmo que a entrada delas caia no
    intervalo selecionado — isso é intencional: elas não são o desfecho final da
    demanda no setor.
    """
    result = []
    for v in visitas:
        if not v.get("ultima"):
            continue
        entrada = v.get("entrada")
        if not entrada:
            continue
        d = _to_date(entrada.get("DATA"))
        if d and from_date <= d <= to_date:
            result.append(v)
    return result


def _funcionario_visita(visita: Dict[str, Any]) -> str:
    """
    Funcionário responsável pela visita — o evento de saída normalmente não
    carrega responsável, então usamos o da entrada da própria visita (par já
    resolvido por `_construir_visitas`, sem precisar buscar entradas anteriores).
    """
    saida = visita.get("saida")
    if saida and saida.get("FUNCIONARIO"):
        return _formatar_nome_funcionario(saida.get("FUNCIONARIO"))
    entrada = visita.get("entrada")
    return _formatar_nome_funcionario(entrada.get("FUNCIONARIO") if entrada else None)


# -----------------------------------------------------------------------------
# 3 - Filtros da página (funcionário / área de atuação)
# -----------------------------------------------------------------------------

def filter_pendencia_lexpre_por_area_atuacao(
    pendencia_lexpre: List[Dict[str, Any]],
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe pela área de atuação real (``public.area_atuacao``, via ``operacao.area_atuacao_id``) — ver comercial_lexpre.filter_comercial_lexpre_por_area_atuacao."""
    alvos = normalizar_filtro_ids(area_atuacao_id)
    if not alvos:
        return list(pendencia_lexpre)
    return [row for row in pendencia_lexpre if row.get("AREA_ATUACAO_ID") in alvos]


def filter_pendencia_lexpre_por_area_atuacao_nome(
    pendencia_lexpre: List[Dict[str, Any]],
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
        return list(pendencia_lexpre)
    return [
        row for row in pendencia_lexpre
        if str(row.get("AREA_ATUACAO_NOME") or "").strip().upper() in alvos
    ]


def filter_pendencia_lexpre_por_uf(
    pendencia_lexpre: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe às demandas cujo cliente (``customer.uf``) é da UF informada. ``None`` = sem filtro. Catálogo de UFs compartilhado — ver `comercial_lexpre.list_ufs_comerciais`."""
    alvos = normalizar_filtro_textos(uf)
    if not alvos:
        return list(pendencia_lexpre)
    return [row for row in pendencia_lexpre if str(row.get("UF") or "").strip().upper() in alvos]


def list_funcionarios_pendencia_lexpre(pendencia_lexpre: List[Dict[str, Any]]) -> List[str]:
    """Funcionários que aparecem como responsáveis por uma entrada no setor 2, no recorte atual."""
    vistos: set = set()
    saida: List[str] = []
    for row in _entradas_setor(pendencia_lexpre, SETOR_PENDENCIAS_IDS):
        nome = _formatar_nome_funcionario(row.get("FUNCIONARIO"))
        if nome == "Sem funcionário" or nome in vistos:
            continue
        vistos.add(nome)
        saida.append(nome)
    return sorted(saida, key=lambda x: x.lower())


def filter_pendencia_lexpre_por_funcionarios(
    pendencia_lexpre: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe às demandas cujo responsável em alguma visita ao setor é um dos funcionários informados (união — OR)."""
    if not funcionarios:
        return list(pendencia_lexpre)
    alvos = {_formatar_nome_funcionario(f) for f in funcionarios if f is not None and str(f).strip()}
    if not alvos:
        return list(pendencia_lexpre)

    visitas = _construir_visitas(pendencia_lexpre, SETOR_PENDENCIAS_IDS)
    demandas_alvo: set = set()
    for v in visitas:
        entrada = v.get("entrada")
        if entrada and _funcionario_visita(v) in alvos:
            demandas_alvo.add(entrada.get("ID_DEMANDA"))

    return [row for row in pendencia_lexpre if row.get("ID_DEMANDA") in demandas_alvo]


# -----------------------------------------------------------------------------
# 4 - KPIs do período (base: visitas cuja ENTRADA caiu no período)
# -----------------------------------------------------------------------------

def get_pendencias_total(visitas_periodo: List[Dict[str, Any]]) -> int:
    return len(visitas_periodo)


def get_pendencias_resolvidas(visitas_periodo: List[Dict[str, Any]]) -> int:
    return len([v for v in visitas_periodo if _is_resolvida(v)])


def get_pendencias_canceladas(visitas_periodo: List[Dict[str, Any]]) -> int:
    return len([v for v in visitas_periodo if _is_cancelada(v)])


def get_pendencias_taxa_resolvidos(visitas_periodo: List[Dict[str, Any]]) -> float:
    total = get_pendencias_total(visitas_periodo)
    if total == 0:
        return 0.0
    return round(get_pendencias_resolvidas(visitas_periodo) / total * 100, 2)


def get_pendencias_taxa_nao_resolvidos(visitas_periodo: List[Dict[str, Any]]) -> float:
    total = get_pendencias_total(visitas_periodo)
    if total == 0:
        return 0.0
    abertas = len([v for v in visitas_periodo if _is_aberta(v)])
    return round(abertas / total * 100, 2)


def get_pendencias_taxa_canceladas(visitas_periodo: List[Dict[str, Any]]) -> float:
    total = get_pendencias_total(visitas_periodo)
    if total == 0:
        return 0.0
    return round(get_pendencias_canceladas(visitas_periodo) / total * 100, 2)


# -----------------------------------------------------------------------------
# 5 - Backlog acumulado (sem filtro de período)
# -----------------------------------------------------------------------------

def get_pendencias_nao_resolvidas(visitas_todas: List[Dict[str, Any]]) -> int:
    """Visitas ainda em aberto — valor sempre total, mesmo critério de "Represados" dos outros módulos."""
    return len([v for v in visitas_todas if _is_aberta(v)])


def get_pendencias_nao_resolvidas_com_atraso(
    visitas_todas: List[Dict[str, Any]], hoje: Optional[date] = None
) -> int:
    """Visitas em aberto cuja entrada foi há mais de 5 dias — valor sempre total."""
    referencia = hoje or date.today()
    count = 0
    for v in visitas_todas:
        if not _is_aberta(v):
            continue
        entrada = v.get("entrada")
        d = _to_date(entrada.get("DATA")) if entrada else None
        if d and (referencia - d).days > _DIAS_ATRASO:
            count += 1
    return count


def get_pendencias_triagem(pendencia_lexpre: List[Dict[str, Any]]) -> int:
    """
    Quantas demandas estão atualmente no setor Triagem (``SETOR_ATUAL_ID``), foto
    do estado agora — sem filtro de período, mesmo critério de "Não Resolvidas"
    (backlog atual). Adicionado em 24/09/2026: Triagem é outro setor no lexpre
    (setor_id 6 NGAM / 9 LAAM — ver `SETOR_TRIAGEM_IDS`), não um sub-estado de
    Pendências, mas como a query de origem já traz eventos de TODOS os setores do
    escritório (não só Pendências), dá pra contar direto pela localização atual
    da demanda em ``pendencia_lexpre`` sem precisar buscar dados extras — mesmo
    padrão de `get_represados` em org_doc_lexpre.py.
    """
    vistos: set = set()
    for row in pendencia_lexpre or []:
        demanda_id = row.get("ID_DEMANDA")
        if demanda_id is None or demanda_id in vistos:
            continue
        if row.get("SETOR_ATUAL_ID") not in SETOR_TRIAGEM_IDS:
            continue
        if _is_cancelado_status(row):
            continue
        vistos.add(demanda_id)
    return len(vistos)


def group_nao_resolvidas_por_origem(
    visitas_todas: List[Dict[str, Any]], idx: Dict[Any, Dict[str, Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Visitas em aberto, agrupadas pelo setor de origem — acumulado, sem filtro de período."""
    grouped: Dict[str, int] = defaultdict(int)
    for v in visitas_todas:
        if not _is_aberta(v):
            continue
        entrada = v.get("entrada")
        if not entrada:
            continue
        grouped[_setor_origem_nome(entrada, idx)] += 1
    result = [{"name": nome, "value": int(qtd)} for nome, qtd in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# -----------------------------------------------------------------------------
# 6 - Tempo de resolução (entrada -> saída da visita, em dias)
# -----------------------------------------------------------------------------

def _duracoes_dias(visitas: List[Dict[str, Any]]) -> List[float]:
    duracoes: List[float] = []
    for v in visitas:
        if not _is_resolvida(v):
            continue
        entrada_dt = _to_datetime(v["entrada"].get("DATA")) if v.get("entrada") else None
        saida_dt = _to_datetime(v["saida"].get("DATA")) if v.get("saida") else None
        if not entrada_dt or not saida_dt:
            continue
        dias = (saida_dt - entrada_dt).total_seconds() / 86400
        if dias > 0:
            duracoes.append(dias)
    return duracoes


def get_media_tempo_resolvidos(visitas_periodo: List[Dict[str, Any]]) -> float:
    duracoes = _duracoes_dias(visitas_periodo)
    if not duracoes:
        return 0.0
    return round(sum(duracoes) / len(duracoes), 2)


def get_mediana_tempo_resolvidos(visitas_periodo: List[Dict[str, Any]]) -> float:
    duracoes = sorted(_duracoes_dias(visitas_periodo))
    if not duracoes:
        return 0.0
    n = len(duracoes)
    mediana = duracoes[n // 2] if n % 2 == 1 else (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0
    return round(mediana, 2)


# -----------------------------------------------------------------------------
# 7 - Comparativo (período atual vs. mesmo recorte um mês civil antes)
# -----------------------------------------------------------------------------
#
# Réplica do padrão já usado em org_doc_lexpre.py/peticionamento_lexpre.py/
# protocolo_setor_lexpre.py (`_comparativo_variacao_percentual` + `resolver_periodo_comparativo`),
# adaptada ao modelo de "visitas" de Pendências: em vez de refiltrar uma lista de
# saídas por `DATA_ASSINATURA`/`DATA`, refiltra a lista de visitas por `_visitas_periodo`
# (que já usa a data de ENTRADA da visita, mesmo recorte dos KPIs "do período").

def _comparativo_variacao_percentual(
    visitas: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    valor_atual = metrica_fn(_visitas_periodo(visitas, data_inicio_atual, data_fim_atual))
    valor_anterior = metrica_fn(_visitas_periodo(visitas, data_inicio_anterior, data_fim_anterior))
    if valor_anterior == 0:
        # Sem base no período anterior (ex.: LA, que só começou a usar o lexpre em
        # 22/09/2026): crescimento a partir do zero é exibido como +100%.
        return 100.0 if valor_atual > 0 else 0.0
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 2)


def get_comparativo_pendencias_resolvidas(
    visitas: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    return _comparativo_variacao_percentual(visitas, from_date, to_date, get_pendencias_resolvidas)


def get_comparativo_tempo_medio_resolvidos(
    visitas: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    return _comparativo_variacao_percentual(visitas, from_date, to_date, get_media_tempo_resolvidos)



def get_comparativo_mediana_tempo_resolvidos(
    visitas: List[Dict[str, Any]], from_date: Optional[date], to_date: Optional[date]
) -> float:
    return _comparativo_variacao_percentual(visitas, from_date, to_date, get_mediana_tempo_resolvidos)


# -----------------------------------------------------------------------------
# 8 - Agrupamentos (dia, mês, funcionário)
# -----------------------------------------------------------------------------

_MONTH_NAMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def group_resolvidas_por_dia(visitas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for v in visitas_periodo:
        if not _is_resolvida(v):
            continue
        d = _to_date(v["saida"].get("DATA"))
        if not d:
            continue
        grouped[d.strftime("%Y-%m-%d")] += 1
    return [{"name": dia, "value": count} for dia, count in sorted(grouped.items())]


def get_resolvidas_por_dia_por_funcionario(visitas_periodo: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for v in visitas_periodo:
        if not _is_resolvida(v):
            continue
        d = _to_date(v["saida"].get("DATA"))
        if not d:
            continue
        grouped[d.strftime("%Y-%m-%d")][_funcionario_visita(v)] += 1
    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted({f for dia_data in grouped.values() for f in dia_data.keys()})
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {
        func: [{"name": dia, "value": grouped[dia].get(func, 0)} for dia in dias_ordenados]
        for func in funcionarios
    }
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}


def group_resolvidas_por_mes(visitas_todas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Resolvidas por mês — acumulado, sem filtro de período (mesmo critério do dashboard antigo para essa série)."""
    grouped: Dict[str, Dict[str, Any]] = {}
    for v in visitas_todas:
        if not _is_resolvida(v):
            continue
        d = _to_date(v["saida"].get("DATA"))
        if not d:
            continue
        month_key = f"{d.year}-{d.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {"name": f"{_MONTH_NAMES[d.month - 1]} {d.year}", "value": 0}
        grouped[month_key]["value"] += 1
    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def get_media_resolvidas_por_funcionario(visitas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for v in visitas_periodo:
        if not _is_resolvida(v):
            continue
        funcionario = _funcionario_visita(v)
        grouped[funcionario]["total"] += 1
        d = _to_date(v["saida"].get("DATA"))
        if d:
            grouped[funcionario]["dias"].add(d)

    result = []
    for funcionario, stats in grouped.items():
        dias = len(stats["dias"])
        if dias > 0:
            result.append({"name": funcionario, "value": round(stats["total"] / dias, 2)})
    return sorted(result, key=lambda x: x["value"], reverse=True)


# -----------------------------------------------------------------------------
# 9 - Comissionamento (R$3/demanda se taxa_resolvido>=97% e taxa_cancelamento<5%; R$1 se >=85%; senão R$0)
# -----------------------------------------------------------------------------

_TAXA_RESOLVIDO_ALTA = 97.0
_TAXA_RESOLVIDO_BAIXA = 85.0
_TAXA_CANCELAMENTO_MAX = 5.0
_PRECO_ALTO = Decimal("3.00")
_PRECO_BAIXO = Decimal("1.00")
_PRECO_NENHUM = Decimal("0")


def _preco_unitario_pendencia(taxa_resolvido: float, taxa_cancelamento: float) -> Decimal:
    if taxa_resolvido >= _TAXA_RESOLVIDO_ALTA and taxa_cancelamento < _TAXA_CANCELAMENTO_MAX:
        return _PRECO_ALTO
    if taxa_resolvido >= _TAXA_RESOLVIDO_BAIXA:
        return _PRECO_BAIXO
    return _PRECO_NENHUM


def get_pendencias_comissionamento_por_funcionario(visitas_periodo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Comissão por funcionário sobre as visitas do período: taxa_resolvido e
    taxa_cancelamento são calculadas sobre as visitas FECHADAS (resolvidas +
    canceladas) atribuídas ao funcionário — visitas ainda abertas não entram
    no denominador, pois ainda não têm desfecho.
    """
    grouped = defaultdict(lambda: {"resolvido": 0, "cancelado": 0})
    for v in visitas_periodo:
        if _is_aberta(v):
            continue
        funcionario = _funcionario_visita(v)
        if _is_resolvida(v):
            grouped[funcionario]["resolvido"] += 1
        elif _is_cancelada(v):
            grouped[funcionario]["cancelado"] += 1

    linhas: List[Dict[str, Any]] = []
    for funcionario, stats in grouped.items():
        total = stats["resolvido"] + stats["cancelado"]
        if total == 0:
            continue
        taxa_resolvido = round(stats["resolvido"] / total * 100, 2)
        taxa_cancelamento = round(stats["cancelado"] / total * 100, 2)
        preco = _preco_unitario_pendencia(taxa_resolvido, taxa_cancelamento)
        qtd_x_valor = Decimal(stats["resolvido"]) * preco
        linhas.append({
            "funcionario": funcionario,
            "taxa_resolvido": taxa_resolvido,
            "taxa_cancelamento": taxa_cancelamento,
            "qtd_resolvido": stats["resolvido"],
            "valor": float(preco),
            "qtd_x_valor": float(qtd_x_valor),
            "comissao": float(qtd_x_valor.quantize(Decimal("0.01"))),
        })
    linhas.sort(key=lambda x: (-x["comissao"], x["funcionario"]))
    return linhas


# -----------------------------------------------------------------------------
# 10 - Exportação (relatório) — uma linha por visita
# -----------------------------------------------------------------------------

_SITUACAO_RESOLVIDA = "Resolvida"
_SITUACAO_NAO_RESOLVIDA = "Não Resolvida"
_SITUACAO_CANCELADA = "Cancelada"


def _linha_export_pendencia(
    entrada: Optional[Dict[str, Any]],
    saida: Optional[Dict[str, Any]],
    situacao: str,
    idx: Dict[Any, Dict[str, Dict[str, Any]]],
) -> Dict[str, Any]:
    referencia = saida or entrada or {}
    return {
        "ID_DEMANDA": referencia.get("ID_DEMANDA"),
        "NUMERO_PROCESSO": referencia.get("NUMERO_PROCESSO"),
        "CLIENTE_NOME": referencia.get("CLIENTE_NOME"),
        "MATERIA": _normalizar_materia(referencia.get("MATERIA")),
        "FUNCIONARIO": _funcionario_visita({"entrada": entrada, "saida": saida}),
        "SITUACAO": situacao,
        "STATUS_DEMANDA": referencia.get("STATUS_DEMANDA") or "—",
        "SETOR_ATUAL_NOME": referencia.get("SETOR_ATUAL_NOME") or "—",
        "ORIGEM": _setor_origem_nome(entrada, idx) if entrada else "Origem desconhecida",
        "DATA_ENTRADA": _to_date(entrada.get("DATA")) if entrada else None,
        "DATA_SAIDA": _to_date(saida.get("DATA")) if saida else None,
        "VALOR_CAUSA": _converter_valor(referencia.get("VALOR_CAUSA")),
        "DANO_MORAL": _converter_valor(referencia.get("DANO_MORAL")),
        "AREA_ATUACAO": referencia.get("AREA_ATUACAO_NOME"),
    }


def list_export_rows(
    pendencia_lexpre: List[Dict[str, Any]],
    idx: Dict[Any, Dict[str, Dict[str, Any]]],
    from_date: date,
    to_date: date,
    funcionarios_setor_ids: Optional[set] = None,
) -> List[Dict[str, Any]]:
    """
    Uma linha por visita ao setor, para o relatório exportável: as resolvidas
    ou canceladas cuja entrada caiu no período selecionado, mais o backlog
    atual (visitas ainda em aberto), sempre total — mesmo recorte já usado nos
    cards do dashboard. ``funcionarios_setor_ids``: ver `_construir_visitas`/
    `build_funcionarios_do_setor` — mantém a coluna SITUACAO consistente com o
    dashboard (só conta "Cancelada" se o ator pertence ao setor Pendências).
    """
    visitas = _construir_visitas(pendencia_lexpre, SETOR_PENDENCIAS_IDS, funcionarios_setor_ids)
    visitas_periodo = _visitas_periodo(visitas, from_date, to_date)

    linhas: List[Dict[str, Any]] = []
    for v in visitas_periodo:
        if _is_aberta(v):
            continue
        situacao = _SITUACAO_CANCELADA if _is_cancelada(v) else _SITUACAO_RESOLVIDA
        linhas.append(_linha_export_pendencia(v.get("entrada"), v.get("saida"), situacao, idx))

    for v in visitas:
        if not _is_aberta(v):
            continue
        linhas.append(_linha_export_pendencia(v.get("entrada"), None, _SITUACAO_NAO_RESOLVIDA, idx))

    return linhas
