"""Execução Condenação: os processos em execução com campo do cadastro em branco (V2, não existe na v1).

A faixa "Atenção" dos Julgados aplicada à Execução: a base é o total em execução agora (ID_FASE == 12, o mesmo
recorte do card "Total em execução" e da exportação "Total em execução agora" da v1), com os filtros da página e
sem o filtro de período. Para cada processo, cada campo de CAMPOS que estiver vazio vira um item
{numero_processo, campo}: o letreiro conta por campo, o modal lista, e o relatório `campos-faltando` sai em XLSX
com uma aba por campo para a equipe preencher no LexFlow.

Só campos que todo processo em execução deveria ter. Os que só se preenchem com um evento posterior (alvará, TED,
honorários, encerramento, saída) ficam de fora: vazio neles é o normal.
"""

from dataclasses import replace
from typing import Any

from app.dashboards import execucao_export
from app.dashboards.base import DashboardContext, ExportSpec

# (informação faltando, coluna da query execucao_LA / execucao_RJ), na ordem das abas do relatório.
CAMPOS: tuple[tuple[str, str], ...] = (
    ("Valor da execução", "VALOR_EXECUCAO"),
    ("Data da execução", "DATA_EXECUCAO"),
    ("Data do trânsito em julgado", "DATA_TRANSITO_JULGADO"),
    ("Data de distribuição", "DATA_DISTRIBUICAO"),
    ("Valor da causa", "VALOR_CAUSA"),
    ("Matéria", "MATERIA"),
    ("Comarca", "COMARCA"),
    ("Competência", "COMPETENCIA"),
    ("Vara", "VARA"),
    ("UF", "UF"),
    ("Subfase", "SUBFASE"),
)

CHAVE = "campos_faltando"  # o campo da resposta do dashboard
RELATORIO = "campos-faltando"  # ?relatorio= da exportação (o mesmo dos Julgados)


def _vazio(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _texto(v: Any) -> str:
    return "" if _vazio(v) else str(v).strip()


def itens(
    rows: list[dict[str, Any]], campos: tuple[tuple[str, str], ...] = CAMPOS
) -> list[dict[str, Any]]:
    """Um item por (processo, campo vazio), com o contexto que ajuda a achar o processo na planilha.

    `campos`: (informação faltando, coluna) — os da Execução Condenação por padrão; os Acordos têm os seus
    (acordos_campos.py)."""
    out: list[dict[str, Any]] = []
    for row in rows:
        numero = _texto(row.get("NUMERO_PROCESSO")) or _texto(row.get("id") or row.get("ID"))
        contexto = {
            "numero_processo": numero,
            "materia": _texto(row.get("MATERIA")),
            "comarca": _texto(row.get("COMARCA")),
            "uf": _texto(row.get("UF")),
            "subfase": _texto(row.get("SUBFASE")),
        }
        for nome, coluna in campos:
            if _vazio(row.get(coluna)):
                out.append({**contexto, "campo": nome})
    return out


async def _linhas(ctx: DashboardContext) -> list[dict[str, Any]]:
    """O total em execução agora (critério "total" da exportação da v1), com os filtros da página."""
    total = replace(ctx, export_options={**ctx.export_options, "criterio": "total"})
    return itens(await execucao_export._linhas_execucao(total))


async def lista(ctx: DashboardContext) -> list[dict[str, Any]]:
    """O que vai na resposta do dashboard: só número e campo (o modal não usa o resto)."""
    return [
        {"numero_processo": i["numero_processo"], "campo": i["campo"]} for i in await _linhas(ctx)
    ]


RELATORIO_SPEC = ExportSpec(
    title="Campos em branco",
    fields={
        "processo": "numero_processo",
        "materia": "materia",
        "comarca": "comarca",
        "uf": "uf",
        "subfase": "subfase",
        "campo": "campo",
    },
    labels={
        "processo": "Nº Processo",
        "materia": "Matéria",
        "comarca": "Comarca",
        "uf": "UF",
        "subfase": "Subfase",
        "campo": "Informação faltando",
    },
    sheet_name="Campos em branco",
    rows=_linhas,
    sheet_by="campo",
    sheet_order=tuple(nome for nome, _ in CAMPOS),
)
