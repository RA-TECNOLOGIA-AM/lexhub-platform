"""Execução Acordos: os processos em acordo agora com campo do cadastro em branco (V2, não existe na v1).

A mesma faixa "Atenção" da Execução Condenação (execucao_campos.py), com os dados do acordo: a base é o total em
Execução de Acordos agora (fase ACORDO, ID_FASE == 30: o critério "total" da exportação da v1, o mesmo do card
"Total em execução"), com os filtros da página e sem o filtro de período. Cada campo de CAMPOS vazio vira um item
{numero_processo, campo}: o letreiro conta por campo, o modal lista, e o relatório `campos-faltando` sai em XLSX
com uma aba por campo para a equipe preencher no LexFlow. Inclui o "valor de alçada final" do aviso da v1.

Só campos que todo acordo em andamento deveria ter. Os que só se preenchem com um evento posterior (homologação,
pagamento, alvará, TED) e os da negociação (proposta e contraproposta, que nem todo acordo tem) ficam de fora.
"""

from dataclasses import replace
from typing import Any

from app.dashboards import execucao_campos, execucao_export
from app.dashboards.base import DashboardContext, ExportSpec

# (informação faltando, coluna da query execucao_acordos_{NG,LA,RJ}), na ordem das abas do relatório.
CAMPOS: tuple[tuple[str, str], ...] = (
    ("Valor de alçada final", "VALOR_ALCADA_FINAL"),
    ("Data do acordo fechado", "DATA_ACORDO_FECHADO"),
    ("Data da execução", "DATA_EXECUCAO"),
    ("Data de distribuição", "DATA_DISTRIBUICAO"),
    ("Matéria", "MATERIA"),
    ("Comarca", "COMARCA"),
    ("Competência", "COMPETENCIA"),
    ("Vara", "VARA"),
    ("UF", "UF"),
    ("Subfase", "SUBFASE"),
)

CHAVE = execucao_campos.CHAVE  # o campo da resposta do dashboard (o mesmo da Execução)
RELATORIO = (
    execucao_campos.RELATORIO
)  # ?relatorio= da exportação (o mesmo da Execução e dos Julgados)


async def _linhas(ctx: DashboardContext) -> list[dict[str, Any]]:
    """O total em Execução de Acordos agora (critério "total" da exportação da v1), com os filtros da página."""
    total = replace(ctx, export_options={**ctx.export_options, "criterio": "total"})
    return execucao_campos.itens(await execucao_export._linhas_acordos(total), CAMPOS)


async def lista(ctx: DashboardContext) -> list[dict[str, Any]]:
    """O que vai na resposta do dashboard: só número e campo (o modal não usa o resto)."""
    return [
        {"numero_processo": i["numero_processo"], "campo": i["campo"]} for i in await _linhas(ctx)
    ]


# O mesmo relatório da Execução (colunas, uma aba por campo), com as linhas e a ordem das abas dos Acordos.
RELATORIO_SPEC: ExportSpec = replace(
    execucao_campos.RELATORIO_SPEC,
    rows=_linhas,
    sheet_order=tuple(nome for nome, _ in CAMPOS),
)
