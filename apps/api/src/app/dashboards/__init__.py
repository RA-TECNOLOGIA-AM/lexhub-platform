"""Dashboards com dados na V2: key -> módulo. Dashboard novo = um módulo + uma linha aqui."""

from app.dashboards import (
    acordos,
    comercial,
    comercial_lexpre,
    comissao,
    comissao_lexpre,
    execucao,
    marketing,
    org_documentos,
    org_documentos_lexpre,
    pendencias,
    pendencias_lexpre,
    peticionamento,
    peticionamento_lexpre,
    protocolo,
    protocolo_lexpre,
    recursal,
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
        execucao.MODULE,
        acordos.MODULE,
        recursal.MODULE,
        protocolo.MODULE,
        pendencias.MODULE,
        org_documentos.MODULE,
        peticionamento.MODULE,
        comercial.MODULE,
        comissao.MODULE,
        marketing.MODULE,
    )
}
