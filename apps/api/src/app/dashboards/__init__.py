"""Dashboards com dados na V2: key -> módulo. Dashboard novo = um módulo + uma linha aqui."""

from app.dashboards import (
    comercial_lexpre,
    comissao_lexpre,
    org_documentos_lexpre,
    pendencias_lexpre,
    peticionamento_lexpre,
    protocolo_lexpre,
)
from app.dashboards.base import DashboardModule

DASHBOARDS: dict[str, DashboardModule] = {
    m.key: m
    for m in (
        protocolo_lexpre.MODULE,
        pendencias_lexpre.MODULE,
        org_documentos_lexpre.MODULE,
        peticionamento_lexpre.MODULE,
        comercial_lexpre.MODULE,
        comissao_lexpre.MODULE,
    )
}
