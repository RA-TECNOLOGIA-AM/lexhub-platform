"""Dashboards com dados na V2: key -> módulo. Dashboard novo = um módulo + uma linha aqui."""

from app.dashboards import pendencias_lexpre, protocolo_lexpre
from app.dashboards.base import DashboardModule

DASHBOARDS: dict[str, DashboardModule] = {
    m.key: m for m in (protocolo_lexpre.MODULE, pendencias_lexpre.MODULE)
}
