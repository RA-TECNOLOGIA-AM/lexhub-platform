# -*- coding: utf-8 -*-
"""TCC Previsão Individualizada (Fase 6) - dado ESTÁTICO, não consulta o LexFlow.

Serve o lookup de previsões do XGBoost-AFT (treinado/validado nas Fases 4-5 do
TCC) e as métricas de validação (C-index com IC bootstrap, Brier Score,
calibração) já calculadas offline. O arquivo `data/tcc_previsao_individual.json`
é gerado a partir da pasta de pesquisa do TCC (fora deste repositório) e
versionado aqui como um snapshot read-only - não há recomputo nem acesso a
banco neste módulo.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_DATA_PATH = Path(__file__).parent / "data" / "tcc_previsao_individual.json"


@lru_cache(maxsize=1)
def _carregar(_mtime_ns: int) -> Dict[str, Any]:
    with _DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def montar_payload_tcc_previsao_individual() -> Dict[str, Any]:
    # mtime na chave do cache: um JSON regerado é servido sem reiniciar a API
    # (o --reload do uvicorn só observa .py).
    return _carregar(_DATA_PATH.stat().st_mtime_ns)
