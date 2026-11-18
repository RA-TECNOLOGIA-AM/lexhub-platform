"""Sobrevivência Processual (TCC) — payload colunar pro dashboard do LexHub.

Antes (até 14/10/2026) esse payload era gerado por cron na máquina do pesquisador
(`TCC - Luiz/scripts/atualizar_dashboard_tcc.py`) e importado como JSON estático no
front — produção só atualizava com commit+deploy do JSON. Agora a API monta o mesmo
formato a partir da query `tcc_sobrevivencia_processual` (queries.py), com cache.

O cálculo estatístico (Kaplan-Meier, log-rank) NÃO roda aqui: o front recalcula no
navegador sob qualquer combinação de filtros (`src/lib/kaplanMeier.ts` no LexHub).
Aqui só codifica a coorte linha a linha em colunas + dicionário de categorias, o que
mantém a resposta pequena (~40k processos).
"""
from collections import Counter
from datetime import date
from typing import Any, Dict, List, Optional

# id_escritorio_assinante confirmado via tabela escritorio_assinante
# (ver coorte_sobrevivencia_2_estagios.sql no projeto do TCC)
# Só NG e LA/AM desde 09/11/2026 (a query já filtra; RJ fora do estudo).
ESCRITORIO_POR_ID = {20: "NG", 21: "LA"}

TIPO_EVENTO_E1_DICT = [
    "CENSURADO",
    "ACORDO",
    "MERITO_FAVORAVEL_COM_PROVEITO",
    "MERITO_SEM_PROVEITO_OU_DESFAVORAVEL",
]
TIPO_EVENTO_E2_DICT = ["PAGO", "CENSURADO_PAGAMENTO"]
TIPO_ACORDO_DICT = ["PRE_SENTENCA", "POS_SENTENCA"]

# Colunas categóricas: (chave no payload, coluna da query)
_CATEGORICAS = (
    ("tipo_acao", "tipo_acao"),
    ("materia", "materia"),
    ("comarca", "comarca"),
    ("competencia", "competencia"),
    # Exploratórias apenas (estado atual/pós-desfecho do processo) — no dashboard
    # saem só como ranking, nunca como covariável do Cox/Fine-Gray.
    ("fase", "fase"),
    ("subfase", "subfase"),
    ("juiz_1g", "juiz_1g"),
    ("relator_2g", "relator_2g"),
)


def _dicionario(valores: List[Any]) -> List[Any]:
    """Categorias únicas ordenadas por frequência (mais comuns primeiro).

    Empate mantém a ordem de primeira aparição, igual ao `value_counts()` do pandas
    usado pelo script original.
    """
    return [v for v, _ in Counter(v for v in valores if v is not None).most_common()]


def _codificar(valores: List[Any], dicionario: List[Any]) -> List[Optional[int]]:
    codigo = {v: i for i, v in enumerate(dicionario)}
    return [codigo.get(v) if v is not None else None for v in valores]


def montar_payload_tcc_sobrevivencia(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Converte a coorte (1 linha/processo) no formato colunar consumido pelo front."""
    escritorios = [ESCRITORIO_POR_ID.get(r.get("id_escritorio_assinante")) for r in rows]
    tipo_evento_e1 = [r.get("tipo_evento_e1") for r in rows]
    tipo_evento_e2 = [r.get("tipo_evento_e2") for r in rows]
    tipo_acordo = [r.get("tipo_acordo") for r in rows]

    escritorio_dict = _dicionario(escritorios)
    payload: Dict[str, Any] = {
        "gerado_em": date.today().isoformat(),
        "escritorio_dict": escritorio_dict,
        "tipo_evento_e1_dict": TIPO_EVENTO_E1_DICT,
        "tipo_evento_e2_dict": TIPO_EVENTO_E2_DICT,
        "tipo_acordo_dict": TIPO_ACORDO_DICT,
    }

    registros: Dict[str, List[Any]] = {
        "escritorio": _codificar(escritorios, escritorio_dict),
        "duracao_e1": [int(r["duracao_dias_e1"]) for r in rows],
        "evento_e1": [0 if t == "CENSURADO" else 1 for t in tipo_evento_e1],
        "tipo_evento_e1": _codificar(tipo_evento_e1, TIPO_EVENTO_E1_DICT),
        # Todo processo com data de acordo fechado (11/11/2026 - independente do evento do
        # Estagio 1): PRE_SENTENCA (antes da 1a decisao de merito) ou POS_SENTENCA (depois,
        # inclusive na execucao). duracao_acordo = distribuicao -> acordo, em dias.
        "tipo_acordo": _codificar(tipo_acordo, TIPO_ACORDO_DICT),
        "duracao_acordo": [
            int(r["duracao_dias_acordo"]) if r.get("duracao_dias_acordo") is not None else None
            for r in rows
        ],
    }
    for chave, coluna in _CATEGORICAS:
        valores = [r.get(coluna) for r in rows]
        dicionario = _dicionario(valores)
        payload[f"{chave}_dict"] = dicionario
        registros[chave] = _codificar(valores, dicionario)

    registros["tipo_evento_e2"] = _codificar(tipo_evento_e2, TIPO_EVENTO_E2_DICT)
    registros["duracao_e2"] = [
        int(r["duracao_dias_e2"]) if r.get("duracao_dias_e2") is not None else None
        for r in rows
    ]

    # Estagio 1 quebrado em 2 sub-marcos (mesmo t=0 = distribuicao): distribuicao -> sentenca
    # (1G) e distribuicao -> acordao de merito (2G). Ver nota na query (queries.py) sobre o
    # tratamento de ACORDO como censura (sem riscos competitivos nativos, mesma simplificacao
    # ja documentada nas Fases 3-5 do TCC). A mediana/curva conta QUALQUER sentenca/acordao
    # como evento; *_favoravel e um campo a parte, usado so pela % de favoravel com proveito.
    registros["evento_sentenca"] = [0 if r.get("tipo_evento_sentenca") != "SENTENCA" else 1 for r in rows]
    registros["sentenca_favoravel"] = [1 if r.get("sentenca_favoravel") else 0 for r in rows]
    # improcedencia (merito 5/6) e extincao (7) - mesma regra dos Julgados (11/11/2026)
    registros["sentenca_improcedente"] = [1 if r.get("sentenca_improcedente") else 0 for r in rows]
    registros["sentenca_extinta"] = [1 if r.get("sentenca_extinta") else 0 for r in rows]
    registros["duracao_sentenca"] = [
        int(r["duracao_dias_sentenca"]) if r.get("duracao_dias_sentenca") is not None else None
        for r in rows
    ]
    registros["evento_acordao"] = [0 if r.get("tipo_evento_acordao") != "ACORDAO_MERITO" else 1 for r in rows]
    registros["acordao_favoravel"] = [1 if r.get("acordao_favoravel") else 0 for r in rows]
    registros["acordao_improcedente"] = [1 if r.get("acordao_improcedente") else 0 for r in rows]
    registros["acordao_extinto"] = [1 if r.get("acordao_extinto") else 0 for r in rows]
    registros["duracao_acordao"] = [
        int(r["duracao_dias_acordao"]) if r.get("duracao_dias_acordao") is not None else None
        for r in rows
    ]

    payload["registros"] = registros
    return payload
