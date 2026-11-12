"""Molde dos dashboards "genéricos" da v1 que leem o banco NG (Protocolo, Peticionamento, Org. de
Documentos, Pendências, Comercial, Comissão e Marketing).

É o mesmo molde do LexFlow (generico_v1.py), só com a cópia da v1 do banco NG
(app/analyses/v1_dashboard_generico_ng.py, gerada por scripts/copiar_v1/gerar_generico.py).
Unidade -> ref no NG (app.unit_source_refs, source = 'ng'): "NG" e "RJ". Na v1 os dois saem do mesmo
banco NG: a rota da NG tira o RJ e a do RJ fica só com ele (_filtrar_dados_ng_por_uf). A LA tem as suas
rotas (_LA) no banco LAADV: fica fora destes módulos.
"""

from app.analyses import v1_dashboard_generico_ng as copia_ng
from app.dashboards import generico_v1
from app.dashboards.base import DashboardModule


def modulo(key: str, v1_por_unidade: dict[str, str], descricao_falta: str) -> DashboardModule:
    """DashboardModule de um dashboard genérico da v1 no banco NG. `v1_por_unidade`: ref -> nome na v1."""
    return generico_v1.modulo(
        key=key,
        v1_por_unidade=v1_por_unidade,
        descricao_falta=descricao_falta,
        copia=copia_ng,
        source_db="ng",
        source_label="NG",
    )
