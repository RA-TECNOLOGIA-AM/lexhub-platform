"""Exportação do Protocolo, Peticionamento, Org. de Documentos e Pendências (banco legado) da v1 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (cópia de 26/11/2026; linha na v1 ao lado de cada bloco).
O gerar_generico.py copia só as rotas do dashboard; as rotas /export da v1 usam também estes campos, rótulos e
funções. As funções de linhas leem as mesmas buscas e filtros das cópias do dashboard
(v1_dashboard_generico_ng.py para NG/RJ, v1_dashboard_generico_la.py para a LA). Quem monta o arquivo na V2 é
app/dashboards/export.py; quem escolhe a unidade é app/dashboards/legado_export.py.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Union

from app.analyses.v1_dashboard_generico_la import (
    _normalizar_funcionarios_query as _normalizar_funcionarios_query_la,
    _resolve_date_range as _resolve_date_range_la,
    fetch_org_doc_LA,
    fetch_pendencias_LA,
    fetch_peticionamento_LA,
    fetch_protocolo_LA,
    filter_comercial_geral_por_area_atuacao as filter_comercial_geral_por_area_atuacao_la,
    filter_data as filter_data_la,
    filter_org_doc_LA_por_funcionarios,
    filter_org_doc_LA_por_materia,
    filter_org_doc_LA_por_uf,
    filter_pendencia_LA_por_funcionarios,
    filter_pendencia_LA_por_uf,
    filter_peticionamento_LA_por_funcionarios,
    filter_peticionamento_LA_por_materia,
    filter_peticionamento_LA_por_uf,
    filter_protocolo_LA_por_funcionarios,
    filter_protocolo_LA_por_materia,
    filter_protocolo_LA_por_sistema,
)
from app.analyses.v1_dashboard_generico_ng import (
    _filtrar_dados_ng_por_uf,
    _normalizar_funcionarios_query,
    _resolve_date_range,
    fetch_org_doc,
    fetch_pendencias,
    fetch_peticionamento,
    fetch_protocolos,
    filter_comercial_geral_por_area_atuacao,
    filter_data,
    filter_org_doc_por_funcionarios,
    filter_org_doc_por_materia,
    filter_org_doc_por_uf,
    filter_pendencia_por_funcionarios,
    filter_pendencia_por_uf,
    filter_peticionamento_por_funcionarios,
    filter_peticionamento_por_materia,
    filter_peticionamento_por_uf,
    filter_protocolo_por_funcionarios,
    filter_protocolo_por_materia,
    filter_protocolo_por_sistema,
    filter_protocolo_por_uf,
)

# ─── Protocolo (NG e RJ) ──────────────────────────────────────────────────────

# v1: dashboard_routes.py:18185
_CAMPOS_EXPORT_PROTOCOLO_NG: Dict[str, str] = {
    "nome": "NOME",
    "atendente": "ATENDENTE",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "status": "STATUS",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "sistema": "SISTEMA",
    "campanha": "CAMPANHA",
    "id_action": "ID_ACTION",
    "id_processo": "ID_PROCESSO",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "valor_da_causa": "VALOR_DA_CAUSA",
    "dano_moral": "DANO_MORAL",
    "dano_material": "DANO_MATERIAL",
    "reajuizamento": "REAJUIZAMENTO",
    "area_atuacao_id": "AREA_ATUACAO_ID",
}

# v1: dashboard_routes.py:18207
_LABELS_EXPORT_PROTOCOLO_NG: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "status": "Status",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "sistema": "Sistema",
    "campanha": "Campanha",
    "id_action": "ID da Ação",
    "id_processo": "ID do Processo",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "valor_da_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "dano_material": "Dano Material (R$)",
    "reajuizamento": "Reajuizamento",
    "area_atuacao_id": "Área de Atuação (ID)",
}


# v1: dashboard_routes.py:18230
async def _rows_protocolo_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]],
    funcionario: Optional[List[str]],
    sistema: Optional[str],
    uf_protocolo: Optional[List[str]],
    area_atuacao_id: Optional[Union[int, List[int]]],
    *,
    excluir_rj: bool = True,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/protocolo` (ou `/protocolo_RJ`, com
    ``excluir_rj=False``), para exportação linha a linha — mesma query, sem campos
    adicionais."""
    raw: Dict[str, List] = {"protocolos": await fetch_protocolos()}
    raw = _filtrar_dados_ng_por_uf(raw, "RJ", excluir=excluir_rj)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtered = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in raw.items()
    }
    funcs = _normalizar_funcionarios_query(funcionario)
    uf_filtro = (
        [str(u).strip().upper() for u in uf_protocolo if str(u).strip()]
        if uf_protocolo
        else None
    )
    rows = filter_protocolo_por_uf(
        filter_protocolo_por_sistema(
            filter_protocolo_por_funcionarios(
                filter_protocolo_por_materia(filtered.get("protocolos", []), materia),
                funcs,
            ),
            sistema,
        ),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao(rows, area_atuacao_id)
    return rows


# ─── Peticionamento (NG e RJ) ─────────────────────────────────────────────────

# v1: dashboard_routes.py:18467
_CAMPOS_EXPORT_PETICIONAMENTO_NG: Dict[str, str] = {
    "nome": "NOME",
    "atendente_comercial": "ATENDENTE_COMERCIAL",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "status": "STATUS",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "sistema": "SISTEMA",
    "id_action": "ID_ACTION",
    "id_processo": "ID_PROCESSO",
    "id_peticao": "ID_PETICAO",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "data_confeccao": "DATA_CONFECCAO",
    "valor_da_causa": "VALOR_DA_CAUSA",
    "dano_material": "DANO_MATERIAL",
    "dano_moral": "DANO_MORAL",
    "reajuizamento": "REAJUIZAMENTO",
    "pet_auto": "PET_AUTO",
    "area_atuacao_id": "AREA_ATUACAO_ID",
}

# v1: dashboard_routes.py:18490
_LABELS_EXPORT_PETICIONAMENTO_NG: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente_comercial": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "status": "Status",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "sistema": "Sistema",
    "id_action": "ID da Ação",
    "id_processo": "ID do Processo",
    "id_peticao": "ID da Petição",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "data_confeccao": "Data de Confecção",
    "valor_da_causa": "Valor de Causa (R$)",
    "dano_material": "Dano Material (R$)",
    "dano_moral": "Dano Moral (R$)",
    "reajuizamento": "Reajuizamento",
    "pet_auto": "Petição Automática",
    "area_atuacao_id": "Área de Atuação (ID)",
}


# v1: dashboard_routes.py:18514
async def _rows_peticionamento_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]],
    funcionario: Optional[List[str]],
    uf_peticionamento: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
    *,
    excluir_rj: bool = True,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/peticionamento` (ou `/peticionamento_RJ`, com
    ``excluir_rj=False``), para exportação linha a linha — mesma query, sem campos
    adicionais."""
    raw: Dict[str, List] = {"peticionamento": await fetch_peticionamento()}
    raw = _filtrar_dados_ng_por_uf(raw, "RJ", excluir=excluir_rj)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtered = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in raw.items()
    }
    funcs = _normalizar_funcionarios_query(funcionario)
    uf_filtro = (
        str(uf_peticionamento).strip().upper()
        if uf_peticionamento and str(uf_peticionamento).strip()
        else None
    )
    rows = filter_peticionamento_por_uf(
        filter_peticionamento_por_funcionarios(
            filter_peticionamento_por_materia(filtered.get("peticionamento", []), materia),
            funcs,
        ),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao(rows, area_atuacao_id)
    return rows


# ─── Org. de Documentos (NG e RJ) ─────────────────────────────────────────────

# v1: dashboard_routes.py:18745
_CAMPOS_EXPORT_ORG_DOC_NG: Dict[str, str] = {
    "nome": "NOME",
    "atendente_comercial": "ATENDENTE_COMERCIAL",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "origem": "ORIGEM",
    "status": "STATUS",
    "materia": "MATERIA",
    "id_action": "ID_ACTION",
    "id_processo": "ID_PROCESSO",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "valor_da_causa": "VALOR_DA_CAUSA",
    "dano_moral": "DANO_MORAL",
    "reajuizamento": "REAJUIZAMENTO",
    "area_atuacao_id": "AREA_ATUACAO_ID",
}

# v1: dashboard_routes.py:18764
_LABELS_EXPORT_ORG_DOC_NG: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente_comercial": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "origem": "Origem",
    "status": "Status",
    "materia": "Matéria",
    "id_action": "ID da Ação",
    "id_processo": "ID do Processo",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "valor_da_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "reajuizamento": "Reajuizamento",
    "area_atuacao_id": "Área de Atuação (ID)",
}


# v1: dashboard_routes.py:18863
async def _rows_org_doc_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]],
    funcionario: Optional[List[str]],
    uf_org_doc: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
    *,
    excluir_rj: bool = True,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/org-documentos` (ou `/org_doc_RJ`, com
    ``excluir_rj=False``), para exportação linha a linha — mesma query, sem campos
    adicionais."""
    raw: Dict[str, List] = {"org_doc": await fetch_org_doc()}
    raw = _filtrar_dados_ng_por_uf(raw, "RJ", excluir=excluir_rj)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtered = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in raw.items()
    }
    funcs = _normalizar_funcionarios_query(funcionario)
    uf_filtro = str(uf_org_doc).strip().upper() if uf_org_doc and str(uf_org_doc).strip() else None
    rows = filter_org_doc_por_uf(
        filter_org_doc_por_funcionarios(
            filter_org_doc_por_materia(filtered.get("org_doc", []), materia),
            funcs,
        ),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao(rows, area_atuacao_id)
    return rows


# ─── Pendências (NG e RJ) ─────────────────────────────────────────────────────

# v1: dashboard_routes.py:19084
_CAMPOS_EXPORT_PENDENCIAS_NG: Dict[str, str] = {
    "nome": "NOME",
    "atendente": "ATENDENTE",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "status": "STATUS",
    "origem": "ORIGEM",
    "tipo_pendencia": "TIPO_PENDENCIA",
    "motivo_cancelamento": "MOTIVO_CANCELAMENTO",
    "id_action": "ID_ACTION",
    "id_processo": "ID_PROCESSO",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "reajuizamento": "REAJUIZAMENTO",
    "area_atuacao_id": "AREA_ATUACAO_ID",
}

# v1: dashboard_routes.py:19102
_LABELS_EXPORT_PENDENCIAS_NG: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "status": "Status",
    "origem": "Origem",
    "tipo_pendencia": "Tipo de Pendência",
    "motivo_cancelamento": "Motivo de Cancelamento",
    "id_action": "ID da Ação",
    "id_processo": "ID do Processo",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "reajuizamento": "Reajuizamento",
    "area_atuacao_id": "Área de Atuação (ID)",
}


# v1: dashboard_routes.py:19121
async def _rows_pendencias_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    funcionario: Optional[List[str]],
    uf_pendencias: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
    *,
    excluir_rj: bool = True,
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/pendencias` (ou `/pendencias_RJ`, com
    ``excluir_rj=False``), para exportação linha a linha — mesma query, sem campos
    adicionais."""
    raw: Dict[str, List] = {"pendencias": await fetch_pendencias()}
    raw = _filtrar_dados_ng_por_uf(raw, "RJ", excluir=excluir_rj)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    filtered = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in raw.items()
    }
    funcs = _normalizar_funcionarios_query(funcionario)
    uf_filtro = (
        str(uf_pendencias).strip().upper()
        if uf_pendencias and str(uf_pendencias).strip()
        else None
    )
    rows = filter_pendencia_por_uf(
        filter_pendencia_por_funcionarios(filtered.get("pendencias", []), funcs),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao(rows, area_atuacao_id)
    return rows


# ─── Org. de Documentos (LA) ──────────────────────────────────────────────────

# v1: dashboard_routes.py:21752
_CAMPOS_EXPORT_ORG_DOC_LA: Dict[str, str] = {
    "nome": "NOME",
    "atendente_comercial": "ATENDENTE_COMERCIAL",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "setor_origem": "SETOR_ORIGEM",
    "status": "STATUS",
    "materia": "MATERIA",
    "action_id": "ACTION_ID",
    "processo_id": "PROCESSO_ID",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "valor_causa": "VALOR_CAUSA",
    "dano_moral": "DANO_MORAL",
    "reajuizamento": "REAJUIZAMENTO",
    "pet_auto": "PET_AUTO",
    "area_atuacao": "AREA_ATUACAO",
}

# v1: dashboard_routes.py:21772
_LABELS_EXPORT_ORG_DOC_LA: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente_comercial": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "setor_origem": "Setor de Origem",
    "status": "Status",
    "materia": "Matéria",
    "action_id": "ID da Ação",
    "processo_id": "ID do Processo",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "valor_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "reajuizamento": "Reajuizamento",
    "pet_auto": "Petição Automática",
    "area_atuacao": "Área de Atuação",
}


# v1: dashboard_routes.py:21793
async def _rows_org_doc_la_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]],
    funcionario: Optional[List[str]],
    uf_org_doc_la: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/org_doc_LA`, para exportação linha a linha —
    mesma query, sem campos adicionais."""
    all_rows = await fetch_org_doc_LA()
    from_date, to_date = _resolve_date_range_la(from_date, to_date)
    rows = filter_data_la("org_doc_LA", all_rows, from_date, to_date)
    funcs = _normalizar_funcionarios_query_la(funcionario)
    uf_filtro = str(uf_org_doc_la).strip().upper() if uf_org_doc_la and str(uf_org_doc_la).strip() else None
    rows = filter_org_doc_LA_por_uf(
        filter_org_doc_LA_por_funcionarios(
            filter_org_doc_LA_por_materia(rows, materia),
            funcs,
        ),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao_la(rows, area_atuacao_id)
    return rows


# ─── Protocolo (LA) ───────────────────────────────────────────────────────────

# v1: dashboard_routes.py:26559
_CAMPOS_EXPORT_PROTOCOLO_LA: Dict[str, str] = {
    "nome": "NOME",
    "atendente": "ATENDENTE",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "status": "STATUS",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "sistema": "SISTEMA",
    "action_id": "ACTION_ID",
    "processo_id": "PROCESSO_ID",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "valor_causa": "VALOR_CAUSA",
    "dano_moral": "DANO_MORAL",
    "dano_material": "DANO_MATERIAL",
    "reajuizamento": "REAJUIZAMENTO",
    "area_atuacao": "AREA_ATUACAO",
}

# v1: dashboard_routes.py:26580
_LABELS_EXPORT_PROTOCOLO_LA: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "status": "Status",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "sistema": "Sistema",
    "action_id": "ID da Ação",
    "processo_id": "ID do Processo",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "valor_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "dano_material": "Dano Material (R$)",
    "reajuizamento": "Reajuizamento",
    "area_atuacao": "Área de Atuação",
}


# v1: dashboard_routes.py:26602
async def _rows_protocolo_la_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]],
    funcionario: Optional[List[str]],
    sistema: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/protocolo_LA`, para exportação linha a linha
    — mesma query, sem campos adicionais."""
    all_rows = await fetch_protocolo_LA()
    from_date, to_date = _resolve_date_range_la(from_date, to_date)
    rows = filter_data_la("protocolo_LA", all_rows, from_date, to_date)
    funcs = _normalizar_funcionarios_query_la(funcionario)
    rows = filter_protocolo_LA_por_sistema(
        filter_protocolo_LA_por_funcionarios(
            filter_protocolo_LA_por_materia(rows, materia),
            funcs,
        ),
        sistema,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao_la(rows, area_atuacao_id)
    return rows


# ─── Peticionamento (LA) ──────────────────────────────────────────────────────

# v1: dashboard_routes.py:26736
_CAMPOS_EXPORT_PETICIONAMENTO_LA: Dict[str, str] = {
    "nome": "NOME",
    "atendente": "ATENDENTE",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "status": "STATUS",
    "materia": "MATERIA",
    "parte_adversa": "PARTE_ADVERSA",
    "sistema": "SISTEMA",
    "action_id": "ACTION_ID",
    "processo_id": "PROCESSO_ID",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "data_entrada_pet": "DATA_ENTRADA_PET",
    "data_saida_pet": "DATA_SAIDA_PET",
    "data_entrada_protocolo": "DATA_ENTRADA_PROTOCOLO",
    "data_saida_protocolo": "DATA_SAIDA_PROTOCOLO",
    "valor_causa": "VALOR_CAUSA",
    "dano_moral": "DANO_MORAL",
    "dano_material": "DANO_MATERIAL",
    "reajuizamento": "REAJUIZAMENTO",
    "pet_auto": "PET_AUTO",
    "area_atuacao": "AREA_ATUACAO",
}

# v1: dashboard_routes.py:26761
_LABELS_EXPORT_PETICIONAMENTO_LA: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "status": "Status",
    "materia": "Matéria",
    "parte_adversa": "Parte Adversa",
    "sistema": "Sistema",
    "action_id": "ID da Ação",
    "processo_id": "ID do Processo",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "data_entrada_pet": "Data de Entrada (Peticionamento)",
    "data_saida_pet": "Data de Saída (Peticionamento)",
    "data_entrada_protocolo": "Data de Entrada (Protocolo)",
    "data_saida_protocolo": "Data de Saída (Protocolo)",
    "valor_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "dano_material": "Dano Material (R$)",
    "reajuizamento": "Reajuizamento",
    "pet_auto": "Petição Automática",
    "area_atuacao": "Área de Atuação",
}


# v1: dashboard_routes.py:26787
async def _rows_peticionamento_la_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    materia: Optional[Union[str, List[str]]],
    funcionario: Optional[List[str]],
    uf_peticionamento_la: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/peticionamento_LA`, para exportação linha a
    linha — mesma query, sem campos adicionais."""
    all_rows = await fetch_peticionamento_LA()
    from_date, to_date = _resolve_date_range_la(from_date, to_date)
    rows = filter_data_la("peticionamento_LA", all_rows, from_date, to_date)
    funcs = _normalizar_funcionarios_query_la(funcionario)
    uf_filtro = (
        str(uf_peticionamento_la).strip().upper()
        if uf_peticionamento_la and str(uf_peticionamento_la).strip()
        else None
    )
    rows = filter_peticionamento_LA_por_uf(
        filter_peticionamento_LA_por_funcionarios(
            filter_peticionamento_LA_por_materia(rows, materia),
            funcs,
        ),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao_la(rows, area_atuacao_id)
    return rows


# ─── Pendências (LA) ──────────────────────────────────────────────────────────

# v1: dashboard_routes.py:27134
_CAMPOS_EXPORT_PENDENCIAS_LA: Dict[str, str] = {
    "nome": "NOME",
    "atendente": "ATENDENTE",
    "funcionario": "FUNCIONARIO",
    "uf": "UF",
    "status": "STATUS",
    "setor_origem": "SETOR_ORIGEM",
    "tipo_pendencia": "TIPO_PENDENCIA",
    "motivo_cancelamento": "MOTIVO_CANCELAMENTO",
    "action_id": "ACTION_ID",
    "processo_id": "PROCESSO_ID",
    "data_contratacao": "DATA_CONTRATACAO",
    "entrada": "ENTRADA",
    "saida": "SAIDA",
    "reajuizamento": "REAJUIZAMENTO",
    "area_atuacao": "AREA_ATUACAO",
}

# v1: dashboard_routes.py:27152
_LABELS_EXPORT_PENDENCIAS_LA: Dict[str, str] = {
    "nome": "Nome do Cliente",
    "atendente": "Atendente Comercial",
    "funcionario": "Funcionário Responsável",
    "uf": "UF",
    "status": "Status",
    "setor_origem": "Setor de Origem",
    "tipo_pendencia": "Tipo de Pendência",
    "motivo_cancelamento": "Motivo de Cancelamento",
    "action_id": "ID da Ação",
    "processo_id": "ID do Processo",
    "data_contratacao": "Data de Contratação",
    "entrada": "Data de Entrada",
    "saida": "Data de Saída",
    "reajuizamento": "Reajuizamento",
    "area_atuacao": "Área de Atuação",
}


# v1: dashboard_routes.py:27171
async def _rows_pendencias_la_filtradas(
    from_date: Optional[date],
    to_date: Optional[date],
    funcionario: Optional[List[str]],
    uf_pendencia_la: Optional[str],
    area_atuacao_id: Optional[Union[int, List[int]]],
) -> List[Dict[str, Any]]:
    """Réplica os filtros do dashboard `/pendencia_LA`, para exportação linha a linha
    — mesma query, sem campos adicionais."""
    all_rows = await fetch_pendencias_LA()
    from_date, to_date = _resolve_date_range_la(from_date, to_date)
    rows = filter_data_la("pendencia_LA", all_rows, from_date, to_date)
    funcs = _normalizar_funcionarios_query_la(funcionario)
    uf_filtro = (
        str(uf_pendencia_la).strip().upper()
        if uf_pendencia_la and str(uf_pendencia_la).strip()
        else None
    )
    rows = filter_pendencia_LA_por_uf(
        filter_pendencia_LA_por_funcionarios(rows, funcs),
        uf_filtro,
    )
    if area_atuacao_id is not None:
        rows = filter_comercial_geral_por_area_atuacao_la(rows, area_atuacao_id)
    return rows
