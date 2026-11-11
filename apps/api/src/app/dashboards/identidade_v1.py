"""Equivalentes V2 das funções de identidade da v1 (app/auth.py), para o código copiado da v1 rodar sem mudança.

Na v1 o corpo recebe `usuario_logado` (header) e pergunta:
    is_gestor_ou_desenvolvedor(usuario_logado)   -> quem vê todo mundo
    await get_atendente_vinculado(usuario_logado) -> nome do atendente da pessoa na fonte
Aqui `usuario_logado` é o próprio DashboardContext, e as respostas vêm da casca:
    gere a unidade (owner/admin; gestor/controller na unidade) -> ctx.can_see_commission
    vínculo pessoa -> fonte (app.member_source_refs)            -> ctx.own_ref
"""

from app.dashboards.base import DashboardContext


def is_gestor_ou_desenvolvedor(usuario: DashboardContext | None) -> bool:
    return usuario is not None and usuario.can_see_commission


async def get_atendente_vinculado(usuario: DashboardContext | None) -> str | None:
    return None if usuario is None else usuario.own_ref
