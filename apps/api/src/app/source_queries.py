"""Queries dos bancos de origem, copiadas da v1 (api_dashboards/src/app/queries.py) SEM mudar o texto.

Mesmo formato da v1: nome -> {"database": "lexpre" | "lexflow" | "ng" | "laadv", "query": "..."}.
O dev de dados cola aqui só as que os dashboards da V2 usam (ex.: "log_setor_demanda_lexpre_NG").
"""

QUERIES: dict[str, dict] = {}
