"""O relatório "campos em branco" da faixa "Atenção" (V2, não existe na v1): Julgados Acórdãos e Sentenças.

O modal da faixa lista {numero_processo, campo}; este relatório baixa a mesma lista em XLSX, uma aba por
informação faltando, com matéria, comarca e UF do processo para achá-lo no LexFlow. As linhas são as da própria
faixa (a função da v1 get_julgados_*_dados_faltando_<unidade>, histórico todo, com os filtros da página).
A Execução tem o seu em execucao_campos.py (a base e os campos são outros).
"""

from collections.abc import Awaitable, Callable
from typing import Any

from app.dashboards.base import DashboardContext, ExportSpec

# ?relatorio= da exportação (o mesmo da Execução; o front usa este nome)
RELATORIO = "campos-faltando"

# As informações da v1 com nome maior que os 31 caracteres de uma aba do Excel.
ABAS = {
    "Data do acórdão (mérito lançado)": "Sem data do acórdão",
    "Mérito do acórdão (data lançada)": "Sem mérito do acórdão",
    "Data da sentença (mérito lançado)": "Sem data da sentença",
    "Mérito da sentença (data lançada)": "Sem mérito da sentença",
}


def _texto(v: Any) -> str:
    return "" if v is None else str(v).strip()


def enriquecer(
    itens: list[dict[str, Any]], processos: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Cada item da faixa com a matéria, a comarca e a UF do processo (a primeira linha com aquele número)."""
    por_numero: dict[str, dict[str, Any]] = {}
    for row in processos:
        numero = _texto(row.get("NUMERO_PROCESSO") or row.get("numero_processo"))
        if numero:
            por_numero.setdefault(numero, row)
    out = []
    for item in itens:
        numero = _texto(item.get("numero_processo"))
        row = por_numero.get(numero, {})
        out.append(
            {
                "numero_processo": numero,
                "materia": _texto(row.get("MATERIA")),
                "comarca": _texto(row.get("COMARCA")),
                "uf": _texto(row.get("UF")).upper(),
                "campo": _texto(item.get("campo")),
            }
        )
    return out


def relatorio(
    ordem: tuple[str, ...],
    rows: Callable[[DashboardContext], Awaitable[list[dict[str, Any]]]],
) -> ExportSpec:
    """O ExportSpec do relatório: XLSX com uma aba por campo (na ordem da faixa da v1)."""
    return ExportSpec(
        title="Campos em branco",
        fields={
            "processo": "numero_processo",
            "materia": "materia",
            "comarca": "comarca",
            "uf": "uf",
            "campo": "campo",
        },
        labels={
            "processo": "Nº Processo",
            "materia": "Matéria",
            "comarca": "Comarca",
            "uf": "UF",
            "campo": "Informação faltando",
        },
        sheet_name="Campos em branco",
        rows=rows,
        sheet_by="campo",
        sheet_order=ordem,
        sheet_titles=ABAS,
    )
