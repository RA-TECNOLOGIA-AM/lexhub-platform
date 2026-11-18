"""Previsão Individualizada (TCC, Fase 6) — a página da v1 GERAL/TccPrevisaoIndividualizada.tsx.

v1: GET /tcc_previsao_individual. Dado ESTÁTICO: o lookup de previsões do XGBoost-AFT e as métricas de validação,
calculados offline pelo pipeline em modelo-machine-learning/ (scripts/fase6_exportar_bundle_api.py grava o JSON em
app/analyses/GERAL/data/tcc_previsao_individual.json). Não consulta o LexFlow; o módulo da v1 foi copiado sem
mudança em app/analyses/GERAL/tcc_previsao_individual.py.

Regra de negócio da V2 (18/11/2026): cada unidade vê só o próprio escritório (a NG vê a NG e o LA vê o LA). As
tabelas por combinação (previsões, histórico de acordo, procedência, pesos do treino) têm o escritório na 5ª posição
da chave e vêm recortadas aqui; as métricas do modelo e o Kaplan-Meier por matéria são do estudo inteiro.
"""

from typing import Any

from app.analyses.GERAL.tcc_previsao_individual import montar_payload_tcc_previsao_individual
from app.dashboards.base import DashboardContext, DashboardModule, NotReady
from app.dashboards.sobrevivencia_processual import ESCRITORIO_DA_UNIDADE

# Tabelas cujas chaves são "A|B|C|D|ESCRITORIO|FAIXA" (o escritório é sempre a 5ª parte).
TABELAS_POR_COMBINACAO = ("previsoes", "historico_acordo_pre", "procedencia", "pesos_treino")
POS_ESCRITORIO = 4


def recortar(payload: dict[str, Any], sigla: str) -> dict[str, Any]:
    """O bundle só com o escritório `sigla` (sem mudar o dict em cache)."""
    out = dict(payload)
    for nome in TABELAS_POR_COMBINACAO:
        tabela = payload.get(nome)
        if isinstance(tabela, dict):
            out[nome] = {k: v for k, v in tabela.items() if k.split("|")[POS_ESCRITORIO] == sigla}
    if isinstance(ref := payload.get("referencia_acordo_pre"), dict):
        out["referencia_acordo_pre"] = {k: v for k, v in ref.items() if k == sigla}
    if isinstance(opcoes := payload.get("opcoes"), dict):
        out["opcoes"] = {**opcoes, "escritorios": [sigla]}
    return out


async def build(ctx: DashboardContext) -> dict:
    # A ref da unidade no LexFlow ("NG" / "LA") é a própria sigla do escritório nas chaves do JSON.
    if ctx.unit_ref not in ESCRITORIO_DA_UNIDADE:
        raise NotReady("A Previsão Individualizada (estudo do TCC) existe só para a NG e o LA/AM")
    return recortar(montar_payload_tcc_previsao_individual(), ctx.unit_ref)


MODULE = DashboardModule(
    key="previsao-individualizada",
    source_db="lexflow",
    source_label="Modelo XGBoost-AFT (TCC)",
    build=build,
)
