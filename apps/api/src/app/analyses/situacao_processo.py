"""Filtro de situação do processo (LexFlow: ATIVO / ARQUIVADO / SUSPENSO-SOBRESTADO).

Aplicado de forma transversal a todos os dashboards que leem o banco ``lexflow``:

- ``SituacaoProcessoMiddleware`` lê o parâmetro ``situacao_processo`` (repetível) de
  QUALQUER requisição e guarda a seleção num ``ContextVar`` — assim endpoint
  principal, sub-endpoints (cards, rankings, listas) e exports respeitam o filtro
  sem precisar mudar a assinatura de cada rota.
- ``fetch_data_with_cache`` chama ``aplicar_filtro_situacao_processo`` no retorno:
  o cache (L1/Redis) continua guardando a fonte completa; o recorte é feito por
  requisição, devolvendo uma lista nova (nunca muta o cache).

Sem seleção, cada query volta ao recorte histórico dela (``SITUACOES_PADRAO_POR_QUERY``),
então os números dos dashboards não mudam até o usuário escolher uma situação.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from typing import Any, Dict, FrozenSet, Iterable, List, Optional
from urllib.parse import parse_qs

SITUACAO_ATIVO_ID = 1
SITUACAO_ARQUIVADO_ID = 2
SITUACAO_SUSPENSO_ID = 6

SITUACAO_LABEL_POR_ID: Dict[int, str] = {
    SITUACAO_ATIVO_ID: "ATIVO",
    SITUACAO_ARQUIVADO_ID: "ARQUIVADO",
    SITUACAO_SUSPENSO_ID: "SUSPENSO/SOBRESTADO",
}

_ID_POR_CHAVE: Dict[str, int] = {
    "ATIVO": SITUACAO_ATIVO_ID,
    "ARQUIVADO": SITUACAO_ARQUIVADO_ID,
    "SUSPENSO/SOBRESTADO": SITUACAO_SUSPENSO_ID,
    "SUSPENSO": SITUACAO_SUSPENSO_ID,
    "SOBRESTADO": SITUACAO_SUSPENSO_ID,
    "1": SITUACAO_ATIVO_ID,
    "2": SITUACAO_ARQUIVADO_ID,
    "6": SITUACAO_SUSPENSO_ID,
}

PARAM_SITUACAO_PROCESSO = "situacao_processo"

_TODAS: Optional[FrozenSet[int]] = None
_SO_ATIVO = frozenset({SITUACAO_ATIVO_ID})

# query (queries.py) -> situações devolvidas quando o usuário NÃO escolhe nenhuma.
# ``None`` = sem recorte (a query já trazia todas as situações antes do filtro).
# As queries com WHERE fixo de situação foram ampliadas para trazer as demais
# situações; o padrão aqui reproduz exatamente o WHERE antigo.
SITUACOES_PADRAO_POR_QUERY: Dict[str, Optional[FrozenSet[int]]] = {
    # Recursal — antes: id_situacao = 1 (ampliada p/ IN (1, 2, 6))
    "setor_recurso": _SO_ATIVO,
    "setor_recurso_LA_RJ": _SO_ATIVO,
    "setor_recurso_NG": _SO_ATIVO,
    # Julgados — sem WHERE de situação
    "julgados": _TODAS,
    # Publicações — sem WHERE de situação
    "publicacoes_LA": _TODAS,
    "publicacoes_LA_RJ": _TODAS,
    "publicacoes_NG": _TODAS,
    # Agendamentos (vw_dashboard_agendamentos_detalhados) — sem WHERE de situação
    "agendamentos_setor_recursos_LA": _TODAS,
    "agendamentos_setor_recursos_LA_RJ": _TODAS,
    "agendamentos_setor_recursos_NG": _TODAS,
    "agendamentos_setor_intermediarias_LA": _TODAS,
    "agendamentos_setor_intermediarias_NG": _TODAS,
    "agendamentos_setor_intermediarias_LA_RJ": _TODAS,
    "agendamentos_setor_emendas_manifestacoes_LA": _TODAS,
    "agendamentos_setor_emendas_manifestacoes_LA_RJ": _TODAS,
    "agendamentos_setor_emendas_manifestacoes_NG": _TODAS,
    "agendamentos_setor_replicas_LA": _TODAS,
    "processos_status_1g_replicas_LA": _TODAS,
    "agendamentos_setor_replicas_NG": _TODAS,
    "processos_status_1g_replicas_NG": _TODAS,
    "agendamentos_setor_reajuizamento_LA": _TODAS,
    "processos_extincao_reajuizamento_LA": _TODAS,
    "processos_dados_reajuizamento_LA": _TODAS,
    "agendamentos_dilacao_prazo_intermediarias_LA": _TODAS,
    "agendamentos_dilacao_prazo_intermediarias_NG": _TODAS,
    "agendamentos_dilacao_prazo_intermediarias_LA_RJ": _TODAS,
    "agendamentos_todos_setores_LA": _TODAS,
    "agendamentos_todos_setores_LA_RJ": _TODAS,
    "agendamentos_todos_setores_NG": _TODAS,
}

_situacoes_processo_ctx: ContextVar[Optional[FrozenSet[int]]] = ContextVar(
    "situacoes_processo", default=None
)


def parse_situacoes_processo(valores: Iterable[str]) -> Optional[FrozenSet[int]]:
    """Converte rótulos/ids (``ATIVO``, ``arquivado``, ``6``...) em ids. Vazio → ``None``."""
    ids: set[int] = set()
    for raw in valores:
        chave = str(raw or "").strip().upper()
        if not chave:
            continue
        if chave not in _ID_POR_CHAVE:
            raise ValueError(
                f"Situação do processo inválida: '{raw}'. "
                f"Valores: {sorted(SITUACAO_LABEL_POR_ID.values())}"
            )
        ids.add(_ID_POR_CHAVE[chave])
    return frozenset(ids) if ids else None


def situacoes_processo_selecionadas() -> Optional[FrozenSet[int]]:
    return _situacoes_processo_ctx.get()


def aplicar_filtro_situacao_processo(
    query_name: str, rows: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Recorta ``rows`` pela situação escolhida (ou pelo padrão histórico da query).

    Queries fora de ``SITUACOES_PADRAO_POR_QUERY`` (outros bancos, catálogos) passam
    intactas. Linhas sem processo vinculado (``ID_SITUACAO`` nulo) só ficam quando
    não há recorte.
    """
    if query_name not in SITUACOES_PADRAO_POR_QUERY:
        return rows
    alvo = _situacoes_processo_ctx.get() or SITUACOES_PADRAO_POR_QUERY[query_name]
    if alvo is None:
        return rows
    return [r for r in rows if r.get("ID_SITUACAO") in alvo]


class SituacaoProcessoMiddleware:
    """ASGI: publica ``situacao_processo`` da query string no ``ContextVar`` da requisição."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
        try:
            selecao = parse_situacoes_processo(qs.get(PARAM_SITUACAO_PROCESSO, []))
        except ValueError as exc:
            body = json.dumps({"detail": str(exc)}).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({"type": "http.response.body", "body": body})
            return
        token = _situacoes_processo_ctx.set(selecao)
        try:
            await self.app(scope, receive, send)
        finally:
            _situacoes_processo_ctx.reset(token)
