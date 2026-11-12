"""Comissão Comercial (banco NG) — mesmo cálculo da v1 do Comercial (banco NG).

Na v1 a página Comissão Comercial NG não tem endpoint próprio: chama GET /comercial (o mesmo do
Comercial NG, sem escopo próprio) e mostra a parte de comissão. Na V2: o mesmo módulo do comercial.py
com a key do catálogo.
"""

from dataclasses import replace

from app.dashboards import comercial

MODULE = replace(comercial.MODULE, key="comissao")
